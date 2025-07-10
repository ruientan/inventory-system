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
from datetime import datetime
import uuid
from flask_cors import CORS 

app = Flask(__name__)
CORS(app)
app.secret_key = 'Citibella123'

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
def log_audit_action(user, action, product_name=None, location=None, quantity=None,
                     product_id=None, location_id=None, session_id=None, ip=None,
                     invoice_number=None, purpose=None):
    conn = get_connection()
    cursor = conn.cursor()

    query = """
        INSERT INTO audit_log (user, action, product_name, location, quantity,
                               product_id, location_id, session_id, ip, invoice_number, purpose, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (
        user, action, product_name, location, quantity,
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
    location_filter = ""

    if location:
        location_filter = "WHERE l.name = ?"
        params = [location]

    # Total SKUs
    query1 = """
        SELECT COUNT(DISTINCT i.product_id) AS skus
        FROM inventory i
        JOIN locations l ON i.location_id = l.location_id
        """ + location_filter
    cursor.execute(query1, params)
    total_skus = cursor.fetchone()['skus'] or 0

    # Total quantity
    query2 = """
        SELECT SUM(i.quantity) AS total_qty
        FROM inventory i
        JOIN locations l ON i.location_id = l.location_id
        """ + location_filter
    cursor.execute(query2, params)
    total_qty = cursor.fetchone()['total_qty'] or 0

    # Low stock items
    low_stock_query = """
        SELECT COUNT(*) AS low
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN locations l ON i.location_id = l.location_id
        WHERE ((i.quantity <= p.reorder_level AND p.reorder_level > 0) OR i.quantity <= 1)
    """
    low_stock_params = []
    if location:
        low_stock_query += " AND l.name = ?"
        low_stock_params = [location]

    cursor.execute(low_stock_query, low_stock_params)
    low_stock = cursor.fetchone()['low'] or 0

    return dict(
        total_skus=total_skus,
        total_quantity=total_qty,
        low_stock_items=low_stock
    )




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
            WHERE fl.name = ? OR tl.name = ?
            ORDER BY sm.date_moved DESC
            LIMIT ?
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
            LIMIT ?
        """
        cursor.execute(query, (limit,))
    
    return cursor.fetchall()

# ───────────────────── Dashboard ─────────────────────

from datetime import datetime

@app.route('/')
def dashboard():
    if 'role' not in session:
        return redirect(url_for('login'))

    conn = get_connection()
    cursor = conn.cursor()

    role = session['role']

    hq_summary        = get_inventory_summary(cursor, location='HQ')
    mbella_summary    = get_inventory_summary(cursor, location='Mbella')
    citibella_summary = get_inventory_summary(cursor, location='Citibella')

    if role == 'HQ':
        summary = get_inventory_summary(cursor)  # all locations
        recent_movements = get_recent_movements(cursor, limit=20)
    else:
        summary = get_inventory_summary(cursor, location=role)
        recent_movements = get_recent_movements(cursor, limit=20, location=role)

    # 🔧 Convert date_moved string → datetime object
    for mv in recent_movements:
        if isinstance(mv['date_moved'], str):
            try:
                mv['date_moved'] = datetime.strptime(mv['date_moved'], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

    stock_by_location = get_stock_by_location(cursor)
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
            WHERE l.name = ?
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
    cursor = conn.cursor()

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

    if not product_ids or not quantities or len(product_ids) != len(quantities):
        flash("⚠️ Invalid product or quantity selection.", "danger")
        return redirect(url_for('initiate_transfer'))

    for pid, qty in zip(product_ids, quantities):
        try:
            qty_int = int(qty)
            if qty_int <= 0:
                raise ValueError
        except ValueError:
            flash(f"⚠️ Invalid quantity for product ID {pid}.", "danger")
            return redirect(url_for('initiate_transfer'))

        # Generate invoice number
        suffix = 'M' if to_location == 2 else 'C'
        today_str = datetime.now().strftime('%d%m%y')
        invoice_number = f"HQ-{suffix}-{today_str}"

        # Insert stock transaction
        cursor.execute("""
            INSERT INTO stock_transactions (invoice_number, from_location_id, to_location_id, status, initiated_by)
            VALUES (?, ?, ?, 'Preparing', ?)
        """, (invoice_number, 1, to_location, moved_by))  # 1 = HQ
        transaction_id = cursor.lastrowid

        transferred_items = []

        for pid, qty in zip(product_ids, quantities):
            cursor.execute("""
                INSERT INTO transaction_items (transaction_id, product_id, quantity)
                VALUES (?, ?, ?)
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
    cursor = conn.cursor()

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

        # ✅ Validate basic input
        if not product_names or not quantities or len(product_names) != len(quantities):
            flash("⚠️ Please ensure all products and quantities are selected correctly.", "danger")
            return redirect(url_for('transfer_stock'))

        # ✅ Validate each quantity is a positive integer
        for name, qty in zip(product_names, quantities):
            try:
                if int(qty) <= 0:
                    flash(f"⚠️ Quantity for '{name}' must be a positive number.", "danger")
                    return redirect(url_for('transfer_stock'))
            except ValueError:
                flash(f"⚠️ Invalid quantity entered for '{name}'.", "danger")
                return redirect(url_for('transfer_stock'))

        if from_location == 1 and to_location in [2, 3]:
            suffix = 'M' if to_location == 2 else 'C'
            today_str = datetime.now().strftime('%d%m%y')
            invoice_number = f"HQ-{suffix}-{today_str}"

        cursor.execute("""
            INSERT INTO stock_transactions (invoice_number, from_location_id, to_location_id, status, initiated_by)
            VALUES (?, ?, ?, 'Preparing', ?)
        """, (invoice_number, from_location, to_location, moved_by))
        transaction_id = cursor.lastrowid

        transferred_items = []

        for name, qty in zip(product_names, quantities):
            quantity = int(qty)
            product = next((p for p in products if p['product_name'].lower() == name.lower()), None)
            if not product:
                flash(f"❌ Product '{name}' not found in system.", "danger")
                continue

            product_id = product['product_id']

            cursor.execute("""
                INSERT INTO transaction_items (transaction_id, product_id, quantity)
                VALUES (?, ?, ?)
            """, (transaction_id, product_id, quantity))

            transferred_items.append((name, quantity))

            log_audit_action(
                user=moved_by,
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
    cursor = conn.cursor()
    location_name = session.get('role')

    # Get location_id
    cursor.execute("SELECT location_id FROM locations WHERE name = ?", (location_name,))
    location = cursor.fetchone()
    if not location:
        cursor.close()
        conn.close()
        return "❌ Invalid location", 400

    location_id = location['location_id']

    # Show pending transfers
    cursor.execute("""
        SELECT st.transaction_id, st.invoice_number, st.created_at, st.initiated_by AS sender
        FROM stock_transactions st
        WHERE st.to_location_id = ? AND st.status IN ('Pending', 'Sent Out')
        ORDER BY st.created_at DESC
    """, (location_id,))
    pending_transfers = cursor.fetchall()

    if request.method == 'POST':
        transaction_id = int(request.form['transaction_id'])
        received_by = session.get('username')
        session_id = session.get('session_id') or request.cookies.get('session')
        ip = request.remote_addr or 'N/A'

        # Fetch items in the transfer
        cursor.execute("""
            SELECT product_id, quantity
            FROM transaction_items
            WHERE transaction_id = ?
        """, (transaction_id,))
        items = cursor.fetchall()

        for item in items:
            pid = item['product_id']
            qty = item['quantity']

            # SAFETY CHECK: Ensure HQ has enough quantity
            cursor.execute("""
                SELECT quantity FROM inventory
                WHERE product_id = ? AND location_id = 1
            """, (pid,))
            hq_stock = cursor.fetchone()

            if not hq_stock or hq_stock['quantity'] < qty:
                flash(f"❌ HQ does not have enough stock of Product ID {pid}.", "danger")
                conn.rollback()
                return redirect(url_for('confirm_transfer'))

            # Subtract from HQ
            cursor.execute("""
                UPDATE inventory
                SET quantity = quantity - ?
                WHERE product_id = ? AND location_id = 1
            """, (qty, pid))

            # Add to receiving branch (SQLite UPSERT)
            cursor.execute("""
                INSERT INTO inventory (product_id, location_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(product_id, location_id)
                DO UPDATE SET quantity = quantity + excluded.quantity
            """, (pid, location_id, qty))

            # Movement log
            cursor.execute("""
                INSERT INTO stock_movements (product_id, from_location, to_location, quantity, moved_by, purpose)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (pid, 1, location_id, qty, received_by, "Confirmed Receipt"))

            # Audit log
            cursor.execute("SELECT product_name FROM products WHERE product_id = ?", (pid,))
            pname = cursor.fetchone()['product_name']

            log_audit_action(
                user=received_by,
                action="Confirmed Transfer",
                product_name=pname,
                product_id=pid,
                location=f"HQ → {location_name}",
                location_id=location_id,
                quantity=qty,
                session_id=session_id,
                ip=ip,
                invoice_number=None,
                purpose="Confirmed Receipt"
            )

        # Update status
        cursor.execute("""
            UPDATE stock_transactions
            SET status = 'Received'
            WHERE transaction_id = ?
        """, (transaction_id,))

        conn.commit()
        flash("✅ Stock successfully confirmed and inventory updated!", "success")
        return redirect(url_for('confirm_transfer'))

    cursor.close()
    conn.close()
    return render_template('confirm_transfer.html', transfers=pending_transfers)

# ─────────────────── Download Invoice ───────────────────
@app.route('/download_invoice/<filename>')
@login_required
def download_invoice(filename):
    try:
        return send_from_directory(
            directory='static/invoices',  # Ensure this matches your folder structure
            filename=filename,
            as_attachment=False  # Set to True if you want to prompt download
        )
    except FileNotFoundError:
        flash("❌ Invoice file not found.", "danger")
        return redirect(url_for('dashboard'))

# ─────────────────── HQ Mark Sent Out───────────────────
@app.route('/mark_sent_out/<int:transaction_id>', methods=['POST'])
@login_required
def mark_sent_out(transaction_id):
    # Only HQ staff should be allowed to mark as 'Sent Out'
    if session.get('role') != 'HQ':
        flash("❌ You are not authorized to perform this action.", "danger")
        return redirect(url_for('dashboard'))

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            UPDATE stock_transactions
            SET status = 'Sent Out',
                updated_at = CURRENT_TIMESTAMP
            WHERE transaction_id = ?
        """, (transaction_id,))
        
        conn.commit()
        flash("✅ Transaction marked as 'Sent Out'.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"❌ Failed to mark as 'Sent Out': {str(e)}", "danger")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('transaction_history'))


# ─────────────────── Mark Delivered ───────────────────
@app.route('/mark_delivered/<int:transaction_id>', methods=['POST'])
@login_required
def mark_delivered(transaction_id):
    # Only branch staff should mark a transaction as delivered
    role = session.get('role')
    if role not in ['Mbella', 'Citibella']:
        flash("❌ You are not authorized to perform this action.", "danger")
        return redirect(url_for('dashboard'))

    try:
        conn = get_connection()
        cursor = conn.cursor()

        # Update status and timestamp
        cursor.execute("""
            UPDATE stock_transactions
            SET status = 'Delivered',
                updated_at = CURRENT_TIMESTAMP
            WHERE transaction_id = ?
        """, (transaction_id,))
        
        conn.commit()
        flash("✅ Transaction marked as 'Delivered'.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"❌ Failed to update status: {str(e)}", "danger")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('transaction_history'))



# ─────────────────── Transaction History ───────────────────
@app.route('/transaction_history')
@login_required
def transaction_history():
    conn = get_connection()
    cursor = conn.cursor()

    role = session.get('role')
    username = session.get('username')

    # Get location_id for current user
    cursor.execute("SELECT location_id FROM locations WHERE name = ?", (role,))
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
            GROUP_CONCAT(CONCAT(p.product_name, ' (x', ti.quantity, ')') SEPARATOR '<br>') AS items
        FROM stock_transactions st
        JOIN locations fl ON st.from_location_id = fl.location_id
        JOIN locations tl ON st.to_location_id = tl.location_id
        JOIN transaction_items ti ON st.transaction_id = ti.transaction_id
        JOIN products p ON ti.product_id = p.product_id
        WHERE st.from_location_id = ? OR st.to_location_id = ?
        GROUP BY st.transaction_id
        ORDER BY st.created_at DESC
    """, (location_id, location_id))

    transactions = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("transaction_history.html", transactions=transactions)

@app.route('/transaction_history/export')
@login_required
def export_transaction_history():
    conn = get_connection()
    cursor = conn.cursor()

    role = session.get('role')

    if role in ['Mbella', 'Citibella']:
        # Only show transactions related to their own location
        cursor.execute("""
            SELECT 
                st.invoice_number,
                fl.name AS from_location,
                tl.name AS to_location,
                GROUP_CONCAT(CONCAT(p.product_name, ' (', ti.quantity, ')') SEPARATOR ', ') AS items,
                st.status,
                st.initiated_by,
                st.created_at
            FROM stock_transactions st
            JOIN locations fl ON st.from_location_id = fl.location_id
            JOIN locations tl ON st.to_location_id = tl.location_id
            JOIN transaction_items ti ON st.transaction_id = ti.transaction_id
            JOIN products p ON ti.product_id = p.product_id
            WHERE fl.name = ? OR tl.name = ?
            GROUP BY st.transaction_id
            ORDER BY st.created_at DESC
        """, (role, role))
    else:
        # HQ sees all
        cursor.execute("""
            SELECT 
                st.invoice_number,
                fl.name AS from_location,
                tl.name AS to_location,
                GROUP_CONCAT(CONCAT(p.product_name, ' (', ti.quantity, ')') SEPARATOR ', ') AS items,
                st.status,
                st.initiated_by,
                st.created_at
            FROM stock_transactions st
            JOIN locations fl ON st.from_location_id = fl.location_id
            JOIN locations tl ON st.to_location_id = tl.location_id
            JOIN transaction_items ti ON st.transaction_id = ti.transaction_id
            JOIN products p ON ti.product_id = p.product_id
            GROUP BY st.transaction_id
            ORDER BY st.created_at DESC
        """)

    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    df = pd.DataFrame(rows)

    # Rename columns for Excel
    df.rename(columns={
        'invoice_number': 'Invoice Number',
        'from_location': 'From',
        'to_location': 'To',
        'items': 'Items',
        'status': 'Status',
        'initiated_by': 'Initiated By',
        'created_at': 'Date'
    }, inplace=True)

    # Format date column nicely
    if 'Date' in df.columns:
        df['Date'] = pd.to_datetime(df['Date']).dt.strftime('%d %b %Y, %I:%M %p')

    # Export to Excel
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
    cursor = conn.cursor()

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
        query += " AND p.product_name LIKE ?"
        params.append(f"%{product_search}%")

    if start_date:
        query += " AND sm.date_moved >= ?"
        params.append(start_date)

    if end_date:
        query += " AND sm.date_moved <= ?"
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
    cursor = conn.cursor()

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
        query += " AND p.product_name LIKE ?"
        params.append(f"%{product_search}%")

    if start_date:
        query += " AND sm.date_moved >= ?"
        params.append(start_date)

    if end_date:
        query += " AND sm.date_moved <= ?"
        params.append(end_date)

    # Restrict view for non-HQ roles
    if role not in ['HQ', 'Admin']:
        query += " AND (fl.name = ? OR tl.name = ?)"
        params.extend([role, role])

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
        cw.writerow([
            row['movement_id'], row['product_name'], row['from_location'],
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
@login_required
def add_product():
    success = None
    error = None

    if request.method == 'POST':
        product_name   = request.form.get('product_name', '').strip()
        supplier_name  = request.form.get('supplier_name', '').strip()
        category       = request.form.get('category', '').strip()
        moved_by       = request.form.get('moved_by', '').strip()
        unit_price     = request.form.get('unit_price', '0').strip()
        reorder_level  = request.form.get('reorder_level', '0').strip()
        quantity       = request.form.get('quantity', '0').strip()
        hq_location_id = 1
        invoice_number = None  # For audit

        # Basic validation
        if not product_name or not moved_by or not quantity.isdigit():
            error = "⚠️ Product name, quantity, and staff name are required."
            return render_template('add_product.html', error=error)

        try:
            quantity = int(quantity)
            reorder_level = int(reorder_level or 0)
            unit_price = float(unit_price or 0.00)
            if quantity < 0 or unit_price < 0:
                raise ValueError
        except ValueError:
            error = "⚠️ Please enter valid numeric values for quantity and price."
            return render_template('add_product.html', error=error)

        conn = get_connection()
        cursor = conn.cursor()

        # Check for duplicates
        cursor.execute("SELECT * FROM products WHERE product_name = ?", (product_name,))
        if cursor.fetchone():
            error = f"⚠️ Product '{product_name}' already exists."
            cursor.close()
            conn.close()
            return render_template('add_product.html', error=error)

        # Insert into products
        cursor.execute("""
            INSERT INTO products (product_name, supplier_name, category, unit_price, reorder_level)
            VALUES (?, ?, ?, ?, ?)
        """, (product_name, supplier_name, category, unit_price, reorder_level))

        product_id = cursor.lastrowid  # SQLite-compatible

        # Insert into inventory (HQ)
        cursor.execute("""
            INSERT INTO inventory (product_id, location_id, quantity)
            VALUES (?, ?, ?)
        """, (product_id, hq_location_id, quantity))

        # Insert into stock_movements
        cursor.execute("""
            INSERT INTO stock_movements (product_id, from_location, to_location, quantity, moved_by, purpose, invoice_number)
            VALUES (?, NULL, ?, ?, ?, ?, ?)
        """, (product_id, hq_location_id, quantity, moved_by, 'New Product', invoice_number))

        # Audit log
        session_id = session.get('session_id') or request.cookies.get('session')
        log_audit_action(
            user=moved_by,
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

        conn.commit()
        cursor.close()
        conn.close()

        success = "✅ Product successfully added to HQ!"

    return render_template('add_product.html', success=success, error=error)


# ─────────────────── Restock ───────────────────
@app.route('/restock', methods=['GET', 'POST'])
@login_required
def restock():
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch products and locations
    cursor.execute("SELECT product_id, product_name FROM products")
    products = cursor.fetchall()

    cursor.execute("SELECT location_id, name FROM locations")
    locations = cursor.fetchall()

    success = None
    error = None

    if request.method == 'POST':
        product_id   = request.form.get('product_id')
        location_id  = request.form.get('location_id')
        quantity     = request.form.get('quantity', '0')
        moved_by     = session.get('username') or request.form.get('moved_by', '').strip()
        session_id   = session.get('session_id') or request.cookies.get('session')
        invoice_number = None

        # Basic validation
        if not product_id or not location_id or not quantity or not moved_by:
            error = "⚠️ All fields are required."
        else:
            try:
                location_id = int(location_id)
                quantity = int(quantity)
                if quantity <= 0:
                    raise ValueError("Quantity must be positive.")
            except ValueError:
                error = "⚠️ Quantity must be a positive number."

        if not error:
            # 1. Update or insert inventory
            cursor.execute("""
                INSERT INTO inventory (product_id, location_id, quantity)
                VALUES (?, ?, ?)
                ON CONFLICT(product_id, location_id)
                DO UPDATE SET quantity = quantity + excluded.quantity
            """, (product_id, location_id, quantity))

            # 2. Log stock movement
            cursor.execute("""
                INSERT INTO stock_movements (product_id, from_location, to_location, quantity, moved_by, purpose, invoice_number)
                VALUES (?, NULL, ?, ?, ?, ?, ?)
            """, (product_id, location_id, quantity, moved_by, 'Restock', invoice_number))

            # 3. Get readable names
            product_name = next((p['product_name'] for p in products if str(p['product_id']) == str(product_id)), 'Unknown')
            location_name = next((l['name'] for l in locations if str(l['location_id']) == str(location_id)), 'Unknown')

            # 4. Log audit
            log_audit_action(
                user=moved_by,
                action="Restocked Product",
                product_name=product_name,
                product_id=product_id,
                location=f"→ {location_name}",
                location_id=location_id,
                quantity=quantity,
                session_id=session_id,
                ip=request.remote_addr,
                invoice_number=invoice_number,
                purpose="Restock"
            )

            conn.commit()
            success = f"✅ {product_name} successfully restocked at {location_name}!"

    cursor.close()
    conn.close()

    return render_template(
        'restock.html',
        products=products,
        locations=locations,
        success=success,
        error=error
    )

# ─────────────────── Login ───────────────────
@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            error = "⚠️ Please enter both username and password."
            return render_template('login.html', error=error)

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        cursor.close()
        conn.close()

        session_id = str(uuid.uuid4())

        if user and check_password_hash(user['password_hash'], password):
            session['username'] = user['username']
            session['role'] = user['role']
            session['session_id'] = session_id

            # ✅ Log successful login
            log_audit_action(
                user=username,
                action="Login Success",
                session_id=session_id,
                ip=request.remote_addr
            )

            return redirect(url_for('dashboard'))
        else:
            error = "❌ Invalid username or password."

            # ❗ Log failed login attempt
            log_audit_action(
                user=username,
                action="Login Failed",
                session_id=session_id,
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
    if username:
        log_audit_action(
            user=username,
            action="Logout",
            session_id=session_id,
            ip=ip
        )

    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))




@app.route('/user')
@login_required
def user_profile():
    username = session.get('username')
    role = session.get('role')
    return render_template('user.html', username=username, role=role)


 # ───────────────────  Manage Products (HQ Only) ───────────────────
@app.route("/use_product", methods=["GET", "POST"])
@login_required
def use_product():
    role = session['role']
    if role not in ['HQ', 'Mbella', 'Citibella']:
        return "❌ Access Denied", 403

    success_msg = None
    error_msg = None

    conn = get_connection()
    cursor = conn.cursor()

    # Load products
    cursor.execute("SELECT * FROM products ORDER BY product_name")
    products = cursor.fetchall()

    if request.method == 'POST' and role in ['Mbella', 'Citibella']:
        try:
            product_id = int(request.form['product_id'])
            quantity = int(request.form['quantity'])
            purpose = request.form['purpose'].strip()
            used_by = session['username']
            session_id = session.get('session_id') or request.cookies.get('session')
            invoice_number = None
            location_name = role

            # Validate inputs
            if quantity <= 0:
                raise ValueError("Quantity must be a positive number.")

            if not purpose:
                raise ValueError("Purpose is required.")

            # Get location ID
            cursor.execute("SELECT location_id FROM locations WHERE name = ?", (location_name,))
            result = cursor.fetchone()
            if not result:
                raise ValueError("Invalid location.")
            location_id = result['location_id']

            # Check current inventory
            cursor.execute("""
                SELECT quantity FROM inventory
                WHERE product_id = ? AND location_id = ?
            """, (product_id, location_id))
            inv = cursor.fetchone()

            if not inv or inv['quantity'] < quantity:
                raise ValueError("Not enough stock available.")

            # Deduct from inventory
            cursor.execute("""
                UPDATE inventory
                SET quantity = quantity - ?
                WHERE product_id = ? AND location_id = ?
            """, (quantity, product_id, location_id))

            # Log movement
            cursor.execute("""
                INSERT INTO stock_movements (product_id, from_location, to_location, quantity, moved_by, purpose, invoice_number)
                VALUES (?, ?, NULL, ?, ?, ?, ?)
            """, (product_id, location_id, quantity, used_by, purpose, invoice_number))

            # Log audit
            product_name = next((p['product_name'] for p in products if p['product_id'] == product_id), "Unknown")
            log_audit_action(
                user=used_by,
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

            # Log usage
            cursor.execute("""
                INSERT INTO usage_log (product_id, quantity, purpose, used_by, location)
                VALUES (?, ?, ?, ?, ?)
            """, (product_id, quantity, purpose, used_by, location_name))

            conn.commit()
            success_msg = f"✅ {quantity} x {product_name} used for '{purpose}'."
        except ValueError as ve:
            conn.rollback()
            error_msg = f"⚠️ {ve}"
        except Exception as e:
            conn.rollback()
            error_msg = "❌ An unexpected error occurred. Please try again."

    # Usage logs
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
                               success=success_msg,
                               error=error_msg)

    else:
        cursor.execute("""
            SELECT u.id, p.product_name, u.quantity, u.purpose, u.used_by, u.location, u.date_used
            FROM usage_log u
            JOIN products p ON u.product_id = p.product_id
            WHERE u.location = ?
            ORDER BY u.date_used DESC
        """, (role,))
        usage_logs = cursor.fetchall()

        cursor.close()
        conn.close()

        return render_template("use_product.html",
                               role=role,
                               products=products,
                               usage_logs=usage_logs,
                               success=success_msg,
                               error=error_msg)


@app.route("/manage_products")
@login_required
def manage_products():
    if session.get('role') != 'HQ':
        return redirect(url_for('dashboard'))

    search = request.args.get('search', '').strip()

    conn = get_connection()
    cursor = conn.cursor()

    if search:
        cursor.execute("""
            SELECT * FROM products
            WHERE product_name LIKE ?
            ORDER BY product_name
        """, (f"%{search}%",))
    else:
        cursor.execute("SELECT * FROM products ORDER BY product_name")

    products = cursor.fetchall()
    cursor.close()
    conn.close()

    # Optional: Audit logging
    log_audit_action(
        user=session.get('username'),
        action="Viewed Product List",
        session_id=session.get('session_id'),
        ip=request.remote_addr
    )

    return render_template("manage_products.html", products=products, search=search)

 # ───────────────────  Edit Product ───────────────────
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    if session.get('role') != 'HQ':
        return redirect(url_for('dashboard'))

    conn = get_connection()
    cursor = conn.cursor()

    # Fetch product first
    cursor.execute("SELECT * FROM products WHERE product_id = ?", (product_id,))
    product = cursor.fetchone()

    if not product:
        cursor.close()
        conn.close()
        return "❌ Product not found.", 404

    # Then fetch HQ quantity
    cursor.execute("""
        SELECT quantity FROM inventory
        WHERE product_id = ? AND location_id = (
            SELECT location_id FROM locations WHERE name = 'HQ'
        )
    """, (product_id,))
    inventory_row = cursor.fetchone()
    product['quantity'] = inventory_row['quantity'] if inventory_row else 0

    if request.method == 'POST':
        try:
            product_name = request.form['product_name']
            supplier_name = request.form['supplier_name']
            category = request.form['category']
            unit_price = float(request.form['unit_price'])
            reorder_level = int(request.form['reorder_level'])
            quantity = int(request.form['quantity'])

            # Update product info
            cursor.execute("""
                UPDATE products
                SET product_name = ?,
                    supplier_name = ?,
                    category = ?,
                    unit_price = ?,
                    reorder_level = ?
                WHERE product_id = ?
            """, (product_name, supplier_name, category, unit_price, reorder_level, product_id))

            # Update inventory quantity in HQ
            cursor.execute("""
                UPDATE inventory
                SET quantity = ?
                WHERE product_id = ? AND location_id = (
                    SELECT location_id FROM locations WHERE name = 'HQ'
                )
            """, (quantity, product_id))

            conn.commit()

            flash("✅ Product updated successfully!", "success")
            return redirect(url_for('manage_products'))

        except Exception as e:
            conn.rollback()
            flash(f"❌ Error updating product: {str(e)}", "danger")

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
        # Get product info before deletion
        cursor.execute("SELECT product_name FROM products WHERE product_id = ?", (product_id,))
        product = cursor.fetchone()
        product_name = product['product_name'] if product else "Unknown"

        # Delete inventory and stock movements (if desired)
        cursor.execute("DELETE FROM inventory WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM stock_movements WHERE product_id = ?", (product_id,))
        cursor.execute("DELETE FROM products WHERE product_id = ?", (product_id,))
        conn.commit()

        # Log audit
        log_audit_action(
            user=session.get('username'),
            action="Deleted Product",
            product_name=product_name,
            product_id=product_id,
            location="HQ",
            location_id=1,  # HQ
            quantity=0,
            session_id=session.get('session_id'),
            ip=request.remote_addr,
            invoice_number=None
        )

        flash(f"🗑️ Product '{product_name}' deleted successfully.", "success")

    except Exception as e:
        conn.rollback()
        flash(f"❌ Failed to delete product: {str(e)}", "danger")

    finally:
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
    conn = get_connection()
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
    """, conn)
    conn.close()

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)

    output.seek(0)
    return send_file(
        output,
        as_attachment=True,
        download_name="inventory.xlsx",
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

@app.route('/export/movements')
def export_movements_excel():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT 
            sm.movement_id AS ID,
            p.product_name AS Product, 
            fl.name AS From_Location, 
            tl.name AS To_Location, 
            sm.quantity AS Quantity, 
            sm.moved_by AS Moved_By, 
            sm.date_moved AS Timestamp
        FROM stock_movements sm
        JOIN products p ON sm.product_id = p.product_id
        JOIN locations fl ON sm.from_location = fl.location_id
        JOIN locations tl ON sm.to_location = tl.location_id
        ORDER BY sm.date_moved DESC
    """, conn)
    conn.close()

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Movements')

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name='movement_history.xlsx'
    )


@app.route('/export/low_stock')
def export_low_stock():
    conn = get_connection()
    df = pd.read_sql("""
        SELECT 
            p.product_name AS Product, 
            l.name AS Location, 
            i.quantity AS Quantity, 
            p.reorder_level AS Reorder_Level
        FROM inventory i
        JOIN products p ON i.product_id = p.product_id
        JOIN locations l ON i.location_id = l.location_id
        WHERE i.quantity <= p.reorder_level OR i.quantity <= 1
        ORDER BY l.name, p.product_name
    """, conn)
    conn.close()

    filename = f"low_stock_items_{datetime.now().strftime('%d%m%y')}.xlsx"
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Low Stock')

    output.seek(0)
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )


# ─────────────────── Export Products ───────────────────
@app.route("/export/products")
def export_products():
    import csv
    from io import StringIO
    from flask import Response

    conn = get_connection()  # your DB connection function
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM products")
    rows = cursor.fetchall()
    headers = [desc[0] for desc in cursor.description]

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(headers)
    writer.writerows(rows)

    output = si.getvalue()
    si.close()

    return Response(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=products.csv"}
    )

# ─────────────────── Export Audit Log ───────────────────
@app.route('/export/audit_log_secret')
def export_audit_log():
    # Simple shared secret method
    secret_key = request.args.get('key')
    if secret_key != '1431431@mfld':
        return "❌ Unauthorized", 403

    conn = get_connection()
    cursor = conn.cursor()
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
@login_required  # Optional: Only allow logged-in users to fetch metrics
def dashboard_metrics():
    conn = get_connection()
    cursor = conn.cursor()

    # Total SKUs
    cursor.execute("SELECT COUNT(*) AS total_skus FROM products")
    total_skus = cursor.fetchone()['total_skus']

    # Low stock products
    cursor.execute("""
        SELECT COUNT(*) AS low_stock 
        FROM inventory i 
        JOIN products p ON i.product_id = p.product_id
        WHERE i.quantity <= p.reorder_level OR i.quantity <= 1
    """)
    low_stock = cursor.fetchone()['low_stock']

    # (Optional) Count total quantity across locations
    cursor.execute("SELECT SUM(quantity) AS total_quantity FROM inventory")
    total_quantity = cursor.fetchone()['total_quantity'] or 0

    conn.close()
    return jsonify({
        "total_skus": total_skus,
        "low_stock": low_stock,
        "total_quantity": total_quantity,
        "branches": ["Mbella", "Citibella"]
    })


# ─────────────────── Run the server ───────────────────
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
