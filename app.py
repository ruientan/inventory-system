from flask import Flask, jsonify, render_template, request, redirect, url_for, session, send_from_directory, send_file, render_template_string
from db import get_connection
from functools import wraps
import csv
from io import StringIO
from flask import Response, g, flash
from werkzeug.security import check_password_hash
from invoice_generator import generate_invoice
import os
import pandas as pd
from io import BytesIO
import uuid
from flask_cors import CORS 
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from datetime import datetime
from dateutil import parser
from pytz import timezone
import pytz 
from sqlalchemy import create_engine

app = Flask(__name__)
CORS(app)

load_dotenv()
app.secret_key = os.getenv('SECRET_KEY')

conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT"),
    cursor_factory=RealDictCursor
)
cursor = conn.cursor()

@app.before_request
def require_login():
    # endpoints that don't need login
    public = {'login', 'static'}  

    if request.endpoint not in public and 'username' not in session:
        flash('Please log in first.', 'warning')
        return redirect(url_for('login'))

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ────────── Analytics helper functions ──────────
def to_sgt(utc_dt):
    sgt = timezone('Asia/Singapore')
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=pytz.utc)
    return utc_dt.astimezone(sgt)

def log_audit_action(username, action, product_name=None, location=None, quantity=None,
                     product_id=None, location_id=None, session_id=None, ip=None,
                     invoice_number=None, purpose=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO audit_log (username, action, product_name, location, quantity,
                               product_id, location_id, session_id, ip, invoice_number, purpose, timestamp)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    cursor.execute(query, (
        username, action, product_name, location, quantity,
        product_id, location_id, session_id, ip, invoice_number, purpose,
        datetime.now()
    ))

    conn.commit()
    cursor.close()
    conn.close()



def get_all_product_names(cursor):
    cursor.execute("SELECT DISTINCT product_name FROM products ORDER BY product_name")
    return [row['product_name'] for row in cursor.fetchall()]

def get_inventory_summary(cursor, location=None):
    params = []
    location_clause = ""

    if location:
        location_clause = "WHERE l.name = %s"
        params = [location]

    # Total SKUs
    cursor.execute("""
        SELECT COUNT(DISTINCT i.product_id) AS skus
        FROM inventory i
        JOIN locations l ON i.location_id = l.location_id
        """ + location_clause,
        params
    )
    total_skus = cursor.fetchone()['skus'] or 0

    # Total Quantity
    cursor.execute("""
        SELECT SUM(i.quantity) AS total_qty
        FROM inventory i
        JOIN locations l ON i.location_id = l.location_id
        """ + location_clause,
        params
    )
    total_qty = cursor.fetchone()['total_qty'] or 0

    # Low Stock Items
    query = """
        SELECT COUNT(*) AS low
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN locations l ON i.location_id = l.location_id
        WHERE ((i.quantity <= p.reorder_level AND p.reorder_level > 0) OR i.quantity <= 1)
    """
    low_stock_params = []
    if location:
        query += " AND l.name = %s"
        low_stock_params.append(location)

    cursor.execute(query, low_stock_params)
    low_stock = cursor.fetchone()['low'] or 0

    return {
        'total_skus': total_skus,
        'total_quantity': total_qty,
        'low_stock_items': low_stock
    }



def get_stock_by_location(cursor):
    """
    Returns rows of the form
    [{'location':'HQ','product':'Shampoo','qty':12}, …]
    """
    cursor.execute("""
        SELECT l.name AS location, p.product_name AS product, i.quantity AS qty
        FROM inventory i
        JOIN products  p ON i.product_id  = p.product_id
        JOIN locations l ON i.location_id = l.location_id
        ORDER BY l.name, p.product_name
    """)
    return cursor.fetchall()



def get_recent_movements(cursor, limit=20, location=None):
    if location:
        query = """
            SELECT sm.movement_id AS id, p.product_name, fl.name AS from_loc, tl.name AS to_loc, 
                   sm.quantity, sm.moved_by, sm.date_moved
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.product_id
            JOIN locations fl ON sm.from_location = fl.location_id
            JOIN locations tl ON sm.to_location = tl.location_id
            WHERE fl.name = %s OR tl.name = %s
            ORDER BY sm.date_moved DESC
            LIMIT %s
        """
        cursor.execute(query, (location, location, limit))
    else:
        query = """
            SELECT sm.movement_id AS id, p.product_name, fl.name AS from_loc, tl.name AS to_loc, 
                   sm.quantity, sm.moved_by, sm.date_moved
            FROM stock_movements sm
            JOIN products p ON sm.product_id = p.product_id
            JOIN locations fl ON sm.from_location = fl.location_id
            JOIN locations tl ON sm.to_location = tl.location_id
            ORDER BY sm.date_moved DESC
            LIMIT %s
        """
        cursor.execute(query, (limit,))
    
    return cursor.fetchall()

# ───────────────────── Dashboard ─────────────────────

@app.route('/')
def dashboard():
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    role = session['role']

    hq_summary        = get_inventory_summary(cursor, location='HQ')
    mbella_summary    = get_inventory_summary(cursor, location='Mbella')
    citibella_summary = get_inventory_summary(cursor, location='Citibella')
    if role == 'HQ':
        summary = get_inventory_summary(cursor)  # all locations
    else:
        summary = get_inventory_summary(cursor, location=role)  # only their own location
    stock_by_location = get_stock_by_location(cursor)
    if role == 'HQ':
        recent_movements = get_recent_movements(cursor, limit=20)
    else:
        recent_movements = get_recent_movements(cursor, limit=20, location=role)

    product_names     = get_all_product_names(cursor)

    if role == 'HQ':
        cursor.execute("""
            SELECT 
                p.product_name,
                l.name AS location_name,
                i.quantity,
                p.reorder_level,
                CASE 
                    WHEN (i.quantity <= p.reorder_level AND p.reorder_level > 0) OR i.quantity <= 1 THEN TRUE
                    ELSE FALSE 
                END AS is_low_stock
            FROM inventory i
            JOIN products p ON i.product_id = p.product_id
            JOIN locations l ON i.location_id = l.location_id
            ORDER BY l.name, p.product_name
        """)
        all_inventory = cursor.fetchall()

        hq_stock = [row for row in all_inventory if row['location_name'] == 'HQ']
        mbella_stock = [row for row in all_inventory if row['location_name'] == 'Mbella']
        citibella_stock = [row for row in all_inventory if row['location_name'] == 'Citibella']

        cursor.close()
        conn.close()

        return render_template(
            'dashboard.html',
            role=role,
            hq_stock=hq_stock,
            mbella_stock=mbella_stock,
            citibella_stock=citibella_stock,
            summary=summary,
            hq_summary=hq_summary,
            mbella_summary=mbella_summary,
            citibella_summary=citibella_summary,
            stock_by_location=stock_by_location,
            recent_movements=recent_movements,
            product_names=product_names
        )
    else:
        cursor.execute("""
            SELECT 
                p.product_name,
                l.name AS location_name,
                i.quantity,
                p.reorder_level,
                CASE 
                    WHEN i.quantity <= p.reorder_level THEN TRUE 
                    ELSE FALSE 
                END AS is_low_stock
            FROM inventory i
            JOIN products p ON i.product_id = p.product_id
            JOIN locations l ON i.location_id = l.location_id
            WHERE l.name = %s
            ORDER BY p.product_name
        """, (role,))
        inventory = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template(
            'dashboard.html',
            role=role,
            inventory=inventory,
            summary=summary,
            stock_by_location=stock_by_location,
            recent_movements=recent_movements,
            product_names=product_names
        )

# ─────────────────── Initiate Transfer ───────────────────
@app.route('/initiate_transfer', methods=['GET', 'POST'])
@login_required
def initiate_transfer():
    if session.get('role') != 'HQ':
        return redirect(url_for('dashboard'))

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Fetch product and branch location options
    cursor.execute("SELECT product_id, product_name FROM products ORDER BY product_name")
    products = cursor.fetchall()

    cursor.execute("SELECT location_id, name FROM locations WHERE name != 'HQ'")
    branches = cursor.fetchall()

    if request.method == 'POST':
        to_location = int(request.form['to_location'])
        moved_by = session.get('username') or request.form.get('moved_by', 'HQ User')
        product_ids = request.form.getlist('product_id[]')
        quantities = request.form.getlist('quantity[]')

        # Generate invoice number
        suffix = 'M' if to_location == 2 else 'C'
        today_str = datetime.now().strftime('%d%m%y')
        invoice_number = f"HQ-{suffix}-{today_str}"

        # Insert stock transaction
        cursor.execute("""
            INSERT INTO stock_transactions (invoice_number, from_location_id, to_location_id, status, initiated_by)
            VALUES (%s, %s, %s, 'Preparing', %s)
            RETURNING transaction_id
        """, (invoice_number, 1, to_location, moved_by))  # 1 = HQ
        
        transaction_id = cursor.fetchone()['transaction_id']

        transferred_items = []

        for pid, qty in zip(product_ids, quantities):
            cursor.execute("""
                INSERT INTO transaction_items (transaction_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (transaction_id, pid, qty))

            product_name = next((p['product_name'] for p in products if str(p['product_id']) == pid), 'Unknown')
            transferred_items.append((product_name, int(qty)))

        conn.commit()

        # Generate printable invoice
        location_name = 'Mbella' if to_location == 2 else 'Citibella'
        invoice_path = generate_invoice(items=transferred_items, to_location=location_name, moved_by=moved_by)

        flash("✅ Stock transfer initiated. Printable invoice generated.", "success")
        return redirect(url_for('view_invoice', filename=os.path.basename(invoice_path)))

    return render_template('initiate_transfer.html', products=products, branches=branches)

@app.route('/view_invoice/<filename>')
def view_invoice(filename):
    return send_from_directory('static/invoices', filename, as_attachment=True)

# ─────────────────── Stock Transfer ───────────────────
@app.route('/transfer', methods=['GET', 'POST'])
@login_required
def transfer_stock():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT product_id, product_name FROM products")
    products = cursor.fetchall()
    cursor.execute("SELECT location_id, name FROM locations")
    locations = cursor.fetchall()

    success = None
    invoice_number = None
    invoice_filename = None
    purpose = "Transfer"

    if request.method == 'POST':
        if session.get('role') not in ['HQ', 'Admin']:
            flash("❌ Only HQ/Admin can initiate transfers.", "danger")
            return redirect(url_for('dashboard'))

        product_names = request.form.getlist('product_name[]')
        quantities = request.form.getlist('quantity[]')
        from_location = int(request.form['from_location'])
        to_location = int(request.form['to_location'])
        moved_by = session.get('username') or request.form['moved_by']
        session_id = session.get('session_id') or request.cookies.get('session')

        if from_location == 1 and to_location in [2, 3]:
            suffix = 'M' if to_location == 2 else 'C'
            timestamp_str = datetime.now().strftime('%d%m%y-%H%M%S')
            invoice_number = f"HQ-{suffix}-{timestamp_str}"

        cursor.execute("""
            INSERT INTO stock_transactions (invoice_number, from_location_id, to_location_id, status, initiated_by)
            VALUES (%s, %s, %s, 'Preparing', %s)
            RETURNING transaction_id
        """, (invoice_number, from_location, to_location, moved_by))
        
        transaction_id = cursor.fetchone()['transaction_id']

        transferred_items = []

        for name, qty in zip(product_names, quantities):
            if not name.strip() or not qty.strip():
                continue  # Skip if product name or quantity is empty

            quantity = int(qty)
            product = next((p for p in products if p['product_name'].lower() == name.lower()), None)
            if not product:
                flash(f"❌ Product '{name}' not found in inventory.", "danger")
                cursor.close()
                conn.close()
                return render_template('transfer.html', products=products, locations=locations)

            product_id = product['product_id']

            # Check available HQ stock
            cursor.execute("""
                SELECT quantity FROM inventory
                WHERE product_id = %s AND location_id = %s
            """, (product_id, from_location))
            hq_stock = cursor.fetchone()

            if not hq_stock or hq_stock['quantity'] < quantity:
                flash(f"❌ Not enough stock for {name}. Requested: {quantity}, Available: {hq_stock['quantity'] if hq_stock else 0}", "danger")
                cursor.close()
                conn.close()
                return render_template('transfer.html', products=products, locations=locations)

            # Insert transaction item
            cursor.execute("""
                INSERT INTO transaction_items (transaction_id, product_id, quantity)
                VALUES (%s, %s, %s)
            """, (transaction_id, product_id, quantity))

            transferred_items.append((name, quantity))

            log_audit_action(
                username=moved_by,
                action="Initiated Transfer",
                product_name=name,
                product_id=product_id,
                location=f"{from_location} → {to_location}",
                location_id=to_location,
                quantity=quantity,
                session_id=session_id,
                ip=request.remote_addr,
                invoice_number=invoice_number,
                purpose=purpose
            )

        conn.commit()

        if invoice_number:
            location_name = 'Mbella' if to_location == 2 else 'Citibella'
            invoice_filename = generate_invoice(
                items=transferred_items,
                to_location=location_name,
                moved_by=moved_by
            )

        success = "✅ Transfer recorded. Awaiting delivery confirmation before inventory is updated."

    cursor.close()
    conn.close()

    if invoice_filename:
        return redirect(url_for('view_invoice', filename=os.path.basename(invoice_filename)))
    else:
        return render_template(
            'transfer.html',
            products=products,
            locations=locations,
            success=success
        )


# ─────────────────── Confirm Transfer ───────────────────
@app.route('/confirm_transfer', methods=['GET', 'POST'])
@login_required
def confirm_transfer():
    if session.get('role') not in ['Mbella', 'Citibella']:
        return redirect(url_for('dashboard'))

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    location_name = session.get('role')

    # Get location_id from locations table
    cursor.execute("SELECT location_id FROM locations WHERE name = %s", (location_name,))
    location = cursor.fetchone()
    if not location:
        cursor.close()
        conn.close()
        return "❌ Invalid location", 400

    location_id = location['location_id']

    # Show all "Pending" or "Sent Out" transfers to this location
    cursor.execute("""
        SELECT st.transaction_id, st.invoice_number, st.created_at, u.username AS sender
        FROM stock_transactions st
        JOIN users u ON st.initiated_by = u.username
        WHERE st.to_location_id = %s AND st.status IN ('Pending', 'Sent Out')
        ORDER BY st.created_at DESC
    """, (location_id,))
    pending_transfers = cursor.fetchall()

    print("✅ POST request received for confirm_transfer")

    if request.method == 'POST':
        transaction_id = int(request.form['transaction_id'])
        print("➡️ Transaction ID:", transaction_id)
        received_by = session.get('username')
        session_id = session.get('session_id') or request.cookies.get('session')

        # Get items in that transaction
        cursor.execute("""
            SELECT product_id, quantity
            FROM transaction_items
            WHERE transaction_id = %s
        """, (transaction_id,))
        items = cursor.fetchall()
        print("📦 Items to confirm:", items)

        # Update inventory and log movement
        for item in items:
            pid = item['product_id']
            qty = item['quantity']

            # SAFETY CHECK: Ensure HQ has enough quantity
            cursor.execute("""
                SELECT quantity FROM inventory
                WHERE product_id = %s AND location_id = 1
            """, (pid,))
            hq_stock = cursor.fetchone()

            print("📊 Checking HQ stock for product:", pid, "| Required:", qty, "| HQ has:", hq_stock)


            if not hq_stock or hq_stock['quantity'] < qty:
                flash(f"❌ HQ does not have enough stock of Product ID {pid}.", "danger")
                conn.rollback()
                return redirect(url_for('confirm_transfer'))

            # Subtract from HQ inventory
            cursor.execute("""
                UPDATE inventory
                SET quantity = quantity - %s
                WHERE product_id = %s AND location_id = 1
            """, (qty, pid))

            # Add to branch inventory
            cursor.execute("""
                INSERT INTO inventory (product_id, location_id, quantity)
                VALUES (%s, %s, %s)
                ON CONFLICT (product_id, location_id)
                DO UPDATE SET quantity = inventory.quantity + EXCLUDED.quantity
            """, (pid, location_id, qty))

            # Log movement
            cursor.execute("""
                INSERT INTO stock_movements (product_id, from_location, to_location, quantity, moved_by, purpose)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (pid, 1, location_id, qty, received_by, "Confirmed Receipt"))

            # Log audit
            cursor.execute("SELECT product_name FROM products WHERE product_id = %s", (pid,))
            pname = cursor.fetchone()['product_name']

            log_audit_action(
                username=received_by,
                action="Confirmed Transfer",
                product_name=pname,
                product_id=pid,
                location=f"HQ → {location_name}",
                location_id=location_id,
                quantity=qty,
                session_id=session_id,
                ip=request.remote_addr,
                invoice_number=None,
                purpose="Confirmed Receipt"
            )

        # Update transaction status
        cursor.execute("""
            UPDATE stock_transactions
            SET status = 'Received'
            WHERE transaction_id = %s
        """, (transaction_id,))

        conn.commit()
        flash("✅ Stock successfully confirmed and inventory updated!", "success")
        return redirect(url_for('confirm_transfer'))

    cursor.close()
    conn.close()
    return render_template('confirm_transfer.html', transfers=pending_transfers)


# ─────────────────── Download Invoice ───────────────────
@app.route('/download_invoice/<filename>')
def download_invoice(filename):
    return send_from_directory('invoices', filename, as_attachment=False)

# ─────────────────── HQ Mark Sent Out───────────────────
@app.route('/mark_sent_out/<int:transaction_id>', methods=['POST'])
def mark_sent_out(transaction_id):
    if session['role'] != 'HQ':
        return "Unauthorized", 403

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE stock_transactions SET status = 'Sent Out' WHERE transaction_id = %s", (transaction_id,))
    conn.commit()
    cursor.close()
    conn.close()

    flash('Transaction marked as Sent Out.', 'success')
    return redirect(url_for('transaction_history'))





# ─────────────────── Transaction History ───────────────────
@app.route('/transaction_history')
@login_required
def transaction_history():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    role = session.get('role')
    username = session.get('username')

    # Get location_id for current user
    cursor.execute("SELECT location_id FROM locations WHERE name = %s", (role,))
    loc = cursor.fetchone()
    if not loc:
        return "❌ Invalid location", 400
    location_id = loc['location_id']

    # Show transactions where this user is sender or recipient
    cursor.execute("""
        SELECT 
            st.transaction_id,
            st.invoice_number,
            fl.name AS from_location,
            tl.name AS to_location,
            st.status,
            st.initiated_by,
            st.created_at,
            STRING_AGG(p.product_name || ' (x' || ti.quantity || ')', E'\n') AS items
        FROM stock_transactions st
        JOIN locations fl ON st.from_location_id = fl.location_id
        JOIN locations tl ON st.to_location_id = tl.location_id
        JOIN transaction_items ti ON st.transaction_id = ti.transaction_id
        JOIN products p ON ti.product_id = p.product_id
        WHERE st.from_location_id = %s OR st.to_location_id = %s
        GROUP BY st.transaction_id, fl.name, tl.name, st.status, st.initiated_by, st.created_at
        ORDER BY st.created_at DESC
    """, (location_id, location_id))

    transactions = cursor.fetchall()


    for t in transactions:
        if isinstance(t['created_at'], str):
            try:
                t['created_at'] = datetime.strptime(t['created_at'], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                t['created_at'] = parser.parse(t['created_at'])

        t['created_at'] = to_sgt(t['created_at'])

   
    cursor.close()
    conn.close()

    return render_template("transaction_history.html", transactions=transactions)

@app.route('/transaction_history/export')
@login_required
def export_transaction_history():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("""
        SELECT 
            st.invoice_number,
            fl.name AS from_location,
            tl.name AS to_location,
            STRING_AGG(p.product_name || ' (x' || ti.quantity || ')', ', ') AS items,
            st.status,
            st.initiated_by,
            st.created_at
        FROM stock_transactions st
        JOIN locations fl ON st.from_location_id = fl.location_id
        JOIN locations tl ON st.to_location_id = tl.location_id
        JOIN transaction_items ti ON st.transaction_id = ti.transaction_id
        JOIN products p ON ti.product_id = p.product_id
        GROUP BY st.transaction_id, fl.name, tl.name, st.invoice_number, st.status, st.initiated_by, st.created_at
        ORDER BY st.created_at DESC
    """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    df = pd.DataFrame(rows)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Transaction History')

    output.seek(0)
    return send_file(
        output,
        download_name="transaction_history.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
# ─────────────────── Movement ───────────────────

@app.route('/movements')
def view_movements():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get filters from query parameters
    product_search = request.args.get('product_search', '')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # Build base query
    query = """
        SELECT 
            sm.movement_id AS id, 
            p.product_name, 
            fl.name AS from_location, 
            tl.name AS to_location, 
            sm.quantity, 
            sm.moved_by, 
            sm.date_moved AS timestamp
        FROM stock_movements sm
        JOIN products p ON sm.product_id = p.product_id
        JOIN locations fl ON sm.from_location = fl.location_id
        JOIN locations tl ON sm.to_location = tl.location_id
        WHERE 1 = 1
    """
    params = []

    # Add filters dynamically
    if product_search:
        query += " AND p.product_name LIKE %s"
        params.append(f"%{product_search}%")

    if start_date:
        query += " AND sm.date_moved >= %s"
        params.append(start_date)

    if end_date:
        query += " AND sm.date_moved <= %s"
        params.append(end_date)

    query += " ORDER BY sm.date_moved DESC"

    cursor.execute(query, params)
    movements = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('movements.html', movements=movements, product_search=product_search, start_date=start_date, end_date=end_date)


@app.route('/movements/export')
def export_movements():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Get filters from query params
    product_search = request.args.get('product_search', '')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = """
        SELECT 
            sm.movement_id AS id, 
            p.product_name, 
            fl.name AS from_location, 
            tl.name AS to_location, 
            sm.quantity, 
            sm.moved_by, 
            sm.date_moved AS timestamp
        FROM stock_movements sm
        JOIN products p ON sm.product_id = p.product_id
        JOIN locations fl ON sm.from_location = fl.location_id
        JOIN locations tl ON sm.to_location = tl.location_id
        WHERE 1 = 1
    """
    params = []

    if product_search:
        query += " AND p.product_name LIKE %s"
        params.append(f"%{product_search}%")

    if start_date:
        query += " AND sm.date_moved >= %s"
        params.append(start_date)

    if end_date:
        query += " AND sm.date_moved <= %s"
        params.append(end_date)

    query += " ORDER BY sm.date_moved DESC"

    cursor.execute(query, params)
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    # CSV creation
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['ID', 'Product', 'From', 'To', 'Quantity', 'Moved By', 'Timestamp'])

    for row in rows:
        if isinstance(row['timestamp'], str):
            try:
                row['timestamp'] = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S.%f")
            except ValueError:
                row['timestamp'] = datetime.strptime(row['timestamp'], "%Y-%m-%d %H:%M:%S")

    for row in rows:
        cw.writerow([
            row['id'], row['product_name'], row['from_location'],
            row['to_location'], row['quantity'], row['moved_by'],
            row['timestamp'].strftime('%d/%m/%Y %H:%M') if row['timestamp'] else ''
        ])

    output = si.getvalue()
    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=stock_movements.csv"}
    )

# ─────────────────── Product UI ───────────────────
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    success = None
    if request.method == 'POST':
        product_name = request.form['product_name']
        supplier_name = request.form['supplier_name']
        category = request.form['category']
        unit_price = request.form.get('unit_price') or 0.00
        reorder_level = int(request.form.get('reorder_level', 0))
        quantity = int(request.form['quantity'])
        moved_by = request.form['moved_by']
        hq_location_id = 1  # Adjust if your HQ location_id is different

        session_id = session.get('session_id') or request.cookies.get('session')
        invoice_number = None  # Not relevant for new product entry

        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)

        # Check if product already exists
        cursor.execute("SELECT * FROM products WHERE product_name = %s", (product_name,))
        if cursor.fetchone():
            error = f"⚠️ Product '{product_name}' already exists."
            return render_template('add_product.html', error=error)

        # 1. Insert product and get product_id (PostgreSQL way)
        cursor.execute("""
            INSERT INTO products (product_name, supplier_name, category, unit_price, reorder_level)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING product_id
        """, (product_name, supplier_name, category, unit_price, reorder_level))
        product_id = cursor.fetchone()['product_id']

        # 2. Add initial inventory to HQ
        cursor.execute("""
            INSERT INTO inventory (product_id, location_id, quantity)
            VALUES (%s, %s, %s)
        """, (product_id, hq_location_id, quantity))

        # 3. Log movement (from NULL to HQ) with purpose
        cursor.execute("""
            INSERT INTO stock_movements (product_id, from_location, to_location, quantity, moved_by, purpose, invoice_number)
            VALUES (%s, NULL, %s, %s, %s, %s, %s)
        """, (product_id, hq_location_id, quantity, moved_by, 'New Product', invoice_number))

        conn.commit()

        # 4. Audit log
        log_audit_action(
            username=moved_by,
            action="Added New Product",
            product_name=product_name,
            product_id=product_id,
            location="→ HQ",
            location_id=hq_location_id,
            quantity=quantity,
            session_id=session_id,
            ip=request.remote_addr,
            invoice_number=invoice_number
        )

        cursor.close()
        conn.close()
        success = "✅ Product successfully added to HQ!"

    return render_template('add_product.html', success=success)



# ─────────────────── Restock ───────────────────
@app.route('/restock', methods=['GET', 'POST'])
def restock():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Fetch product and location options
    cursor.execute("SELECT product_id, product_name FROM products")
    products = cursor.fetchall()

    cursor.execute("SELECT location_id, name FROM locations")
    locations = cursor.fetchall()

    success = None

    if request.method == 'POST':
        product_id = request.form['product_id']
        location_id = int(request.form['location_id'])
        quantity = int(request.form['quantity'])
        moved_by = request.form['moved_by']
        session_id = session.get('session_id') or request.cookies.get('session')
        invoice_number = None  # Not applicable for restock

        # 1. Update inventory (add quantity to location)
        cursor.execute("""
            INSERT INTO inventory (product_id, location_id, quantity)
            VALUES (%s, %s, %s)
            ON CONFLICT (product_id, location_id) DO UPDATE
            SET quantity = quantity + EXCLUDED.quantity
        """, (product_id, location_id, quantity))

        # 2. Log movement (from NULL to location) with purpose
        cursor.execute("""
            INSERT INTO stock_movements (product_id, from_location, to_location, quantity, moved_by, purpose, invoice_number)
            VALUES (%s, NULL, %s, %s, %s, %s, %s)
        """, (product_id, location_id, quantity, moved_by, 'Restock', invoice_number))

        conn.commit()

        # 3. Get product and location names
        product_name = next((p['product_name'] for p in products if str(p['product_id']) == str(product_id)), None)
        location_name = next((l['name'] for l in locations if str(l['location_id']) == str(location_id)), None)

        # 4. Log audit
        log_audit_action(
            username=moved_by,
            action="Restocked Product",
            product_name=product_name,
            product_id=product_id,
            location=f"→ {location_name}",
            location_id=location_id,
            quantity=quantity,
            session_id=session_id,
            ip=request.remote_addr,
            invoice_number=invoice_number
        )

        success = "✅ Inventory successfully restocked!"

    cursor.close()
    conn.close()
    return render_template('restock.html', products=products, locations=locations, success=success)

# ─────────────────── Login ───────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            session['session_id'] = str(uuid.uuid4())

            # ✅ Log successful login
            log_audit_action(
                username=username,
                action="Login Success",
                session_id=session['session_id'],
                ip=request.remote_addr
            )

            return redirect(url_for('dashboard'))
        else:
            error = 'Invalid username or password.'
            log_audit_action(
                username=username,
                action="Login Failed",
                session_id=str(uuid.uuid4()),
                ip=request.remote_addr
            )
           

    return render_template('login.html', error=error)
 
 # ─────────────────── Log out───────────────────
@app.route('/logout', methods=['POST'])
def logout():
    username = session.get('username')
    session_id = session.get('session_id')
    ip = request.remote_addr

    # Log the logout event
    log_audit_action(
        username=username,
        action="Logout",
        session_id=session_id,
        ip=ip
    )

    session.clear()
    return redirect(url_for('login'))



@app.route('/user')
@login_required
def user_profile():
    return render_template('user.html')

 # ───────────────────  Manage Products (HQ Only) ───────────────────
@app.route("/use_product", methods=["GET", "POST"])
@login_required
def use_product():
    role = session['role']

    if role not in ['HQ', 'Mbella', 'Citibella']:
        return "❌ Access Denied", 403

    success_msg = None

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    # Load product list
    cursor.execute("SELECT * FROM products ORDER BY product_name")
    products = cursor.fetchall()

    if request.method == 'POST' and role in ['Mbella', 'Citibella']:
        product_id = int(request.form['product_id'])
        quantity = int(request.form['quantity'])
        purpose = request.form['purpose']
        used_by = session['username']
        session_id = session.get('session_id') or request.cookies.get('session')
        invoice_number = None  # No invoice for usage
        location_name = role

        # Get this user's location_id
        cursor.execute("SELECT location_id FROM locations WHERE name = %s", (location_name,))
        location_id = cursor.fetchone()['location_id']

        # Deduct from inventory
        cursor.execute("""
            UPDATE inventory
            SET quantity = quantity - %s
            WHERE product_id = %s AND location_id = %s
        """, (quantity, product_id, location_id))

        # Insert into stock_movements (from current location → NULL)
        cursor.execute("""
            INSERT INTO stock_movements (product_id, from_location, to_location, quantity, moved_by, purpose, invoice_number)
            VALUES (%s, %s, NULL, %s, %s, %s, %s)
        """, (product_id, location_id, quantity, used_by, purpose, invoice_number))

        # Log audit
        product_name = next((p['product_name'] for p in products if p['product_id'] == product_id), "Unknown")
        log_audit_action(
            username=used_by,
            action=f"Used Product ({purpose})",
            product_name=product_name,
            product_id=product_id,
            location=location_name,
            location_id=location_id,
            quantity=quantity,
            session_id=session_id,
            ip=request.remote_addr,
            invoice_number=invoice_number
        )

        # Log into usage_log table too
        cursor.execute("""
            INSERT INTO usage_log (product_id, quantity, purpose, used_by, location)
            VALUES (%s, %s, %s, %s, %s)
        """, (product_id, quantity, purpose, used_by, location_name))

        conn.commit()
        success_msg = f"✅ {quantity} x {product_name} logged as {purpose}"

    # Fetch logs
    if role == 'HQ':
        cursor.execute("""
            SELECT u.id, p.product_name, u.quantity, u.purpose, u.used_by, u.location, u.date_used
            FROM usage_log u
            JOIN products p ON u.product_id = p.product_id
            WHERE u.location = 'Mbella'
            ORDER BY u.date_used DESC
        """)
        mbella_logs = cursor.fetchall()

        cursor.execute("""
            SELECT u.id, p.product_name, u.quantity, u.purpose, u.used_by, u.location, u.date_used
            FROM usage_log u
            JOIN products p ON u.product_id = p.product_id
            WHERE u.location = 'Citibella'
            ORDER BY u.date_used DESC
        """)
        citibella_logs = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template("use_product.html",
                               role=role,
                               products=products,
                               mbella_usage=mbella_logs,
                               citibella_usage=citibella_logs,
                               success=success_msg)
    else:
        cursor.execute("""
            SELECT u.id, p.product_name, u.quantity, u.purpose, u.used_by, u.location, u.date_used
            FROM usage_log u
            JOIN products p ON u.product_id = p.product_id
            WHERE u.location = %s
            ORDER BY u.date_used DESC
        """, (role,))
        usage_logs = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template("use_product.html",
                               role=role,
                               products=products,
                               usage_logs=usage_logs,
                               success=success_msg)


@app.route("/manage_products")
@login_required
def manage_products():
    if session.get('role') != 'HQ':
        return redirect(url_for('dashboard'))

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM products ORDER BY product_name")
    products = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template("manage_products.html", products=products)

 # ───────────────────  Edit Product ───────────────────
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if session.get('role') != 'HQ':
        return redirect(url_for('dashboard'))

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
    product = cursor.fetchone()

    # Get HQ inventory quantity for this product
    cursor.execute("""
        SELECT quantity FROM inventory
        WHERE product_id = %s AND location_id = (
            SELECT location_id FROM locations WHERE name = 'HQ'
        )
    """, (product_id,))
    inventory_row = cursor.fetchone()
    product['quantity'] = inventory_row['quantity'] if inventory_row else 0

    if not product:
        cursor.close()
        conn.close()
        return "❌ Product not found.", 404

    if request.method == 'POST':
        product_name = request.form['product_name']
        supplier_name = request.form['supplier_name']
        category = request.form['category']
        unit_price = float(request.form['unit_price'])
        reorder_level = int(request.form['reorder_level'])
        quantity = int(request.form['quantity'])

        # Update product info
        cursor.execute("""
            UPDATE products
            SET product_name = %s,
                supplier_name = %s,
                category = %s,
                unit_price = %s,
                reorder_level = %s
            WHERE product_id = %s
        """, (product_name, supplier_name, category, unit_price, reorder_level, product_id))

        # Update HQ inventory quantity
        cursor.execute("""
            UPDATE inventory
            SET quantity = %s
            WHERE product_id = %s AND location_id = (
                SELECT location_id FROM locations WHERE name = 'HQ'
            )
        """, (quantity, product_id))

        conn.commit()
        cursor.close()
        conn.close()

        return redirect(url_for('manage_products'))

    cursor.close()
    conn.close()
    return render_template('edit_product.html', product=product)


# ─────────────────── Delete Product ───────────────────
@app.route('/delete_product/<int:product_id>', methods=['POST'])
@login_required
def delete_product(product_id):
    if session.get('role') != 'HQ':
        return redirect(url_for('dashboard'))

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # Get product name before deletion
        cursor.execute("SELECT product_name FROM products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        product_name = product[0] if product else "Unknown"

        # Delete associated inventory and stock movements
        cursor.execute("DELETE FROM inventory WHERE product_id = %s", (product_id,))
        cursor.execute("DELETE FROM stock_movements WHERE product_id = %s", (product_id,))
        cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
        conn.commit()

        # Log the deletion in audit log
        log_audit_action(
            username=moved_by,
            action="Deleted Product",
            product_name=name,
            product_id=product_id,
            location=f"{from_location} → {to_location}",
            location_id=to_location,
            quantity=quantity,
            session_id=session_id,
            ip=request.remote_addr,
            invoice_number=invoice_number
        )

    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return f"❌ Failed to delete: {str(e)}", 400

    cursor.close()
    conn.close()
    return redirect(url_for('manage_products'))


# ─────────────────── Invoice───────────────────
#@app.route('/view_invoice/<filename>')
#@login_required
#def view_invoice(filename):
#    return render_template('view_invoice.html', filename=filename)

# ─────────────────── Full inventory ───────────────────
@app.route('/export/inventory')
def export_inventory():
    engine = create_engine("postgresql://inventory_system_gtol_user:aYf9pFVCC8siUGiTuPmya42MqT1WK3Os@ddpg-d1nn8vadbo4c73eq882g-a.singapore-postgres.render.com:5432/inventory_system_gtol")
    df = pd.read_sql("""
        SELECT 
            p.product_name, 
            l.name AS location, 
            i.quantity, 
            p.reorder_level 
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN locations l ON i.location_id = l.location_id
        ORDER BY l.name, p.product_name
    """, engine)

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    output.seek(0)
    filename = f"inventory_{datetime.now().strftime('%d%m%y')}.xlsx"
    return send_file(
        output,
        as_attachment=True,
        download_name=filename,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/export/movements')
def export_movements_excel():
    # Use SQLAlchemy engine for compatibility with Pandas
    engine = create_engine("postgresql://inventory_system_gtol_user:aYf9pFVCC8siUGiTuPmya42MqT1WK3Os@ddpg-d1nn8vadbo4c73eq882g-a.singapore-postgres.render.com:5432/inventory_system_gtol")
    df = pd.read_sql("""
        SELECT 
            sm.movement_id AS ID,
            p.product_name AS "Product Name", 
            fl.name AS "From Location", 
            tl.name AS "To Location", 
            sm.quantity AS Quantity,
            sm.moved_by AS "Moved By", 
            sm.date_moved AS "Date Moved"
        FROM stock_movements sm
        JOIN products p ON sm.product_id = p.product_id
        JOIN locations fl ON sm.from_location = fl.location_id
        JOIN locations tl ON sm.to_location = tl.location_id
        ORDER BY sm.date_moved DESC
    """, engine)

    # Optional: Format datetime column
    df["Date Moved"] = pd.to_datetime(df["Date Moved"]).dt.strftime('%d-%m-%Y %I:%M %p')

    # Write to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Movement History')

    output.seek(0)
    filename = f"movement_history_{datetime.now().strftime('%d%m%y')}.xlsx"

    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


@app.route('/export/low_stock')
def export_low_stock():
    engine = create_engine("postgresql://inventory_system_gtol_user:aYf9pFVCC8siUGiTuPmya42MqT1WK3Os@ddpg-d1nn8vadbo4c73eq882g-a.singapore-postgres.render.com:5432/inventory_system_gtol")
    query = """
        SELECT 
            p.product_name, 
            l.name AS location, 
            i.quantity, 
            p.reorder_level
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN locations l ON i.location_id = l.location_id
        WHERE (i.quantity <= p.reorder_level AND p.reorder_level > 0) OR i.quantity <= 1
        ORDER BY l.name, p.product_name
    """

    df = pd.read_sql(query, engine)

    # Export to Excel
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Low Stock')

    output.seek(0)
    filename = f"low_stock_items_{datetime.now().strftime('%d%m%y')}.xlsx"
    return Response(
        output.getvalue(),
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

# ─────────────────── Export Products ───────────────────
@app.route("/export/products")
def export_products():
    conn = get_connection()  # your DB connection function
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    headers = [desc[0] for desc in cursor.description]

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(headers)
    writer.writerows(rows)

    output = '\ufeff' + si.getvalue()
    si.close()

    filename = f"products_{datetime.now().strftime('%d%m%y')}.csv"

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )

# ─────────────────── Export Audit Log ───────────────────
@app.route('/export/audit_log_secret')
def export_audit_log():
    # Simple shared secret method
    secret_key = request.args.get('key')
    if secret_key != '1431431@mfld':
        return "❌ Unauthorized", 403

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    cursor.execute("SELECT * FROM audit_log ORDER BY timestamp DESC")
    logs = cursor.fetchall()
    df = pd.DataFrame(logs)
    cursor.close()
    conn.close()

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    output.seek(0)
    return send_file(
        output,
        download_name="audit_log.xlsx",
        as_attachment=True,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# http://localhost:5001/export/audit_log_secret?key=supersecret123

@app.route("/api/dashboard_metrics")
def dashboard_metrics():
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    cursor.execute("SELECT COUNT(*) AS total_skus FROM products")
    total_skus = cursor.fetchone()['total_skus']

    cursor.execute("""
        SELECT COUNT(*) AS low_stock 
        FROM inventory i 
        JOIN products p ON i.product_id = p.product_id
        WHERE i.quantity <= p.reorder_level OR i.quantity <= 1
    """)
    low_stock = cursor.fetchone()['low_stock']

    conn.close()
    return jsonify({
        "total_skus": total_skus,
        "low_stock": low_stock,
        "branches": ["Mbella", "Citibella"]
    })

# ─────────────────── Run the server ───────────────────
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  
