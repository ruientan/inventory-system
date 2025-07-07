# 📦 Inventory Management System

A lightweight Flask-based inventory system designed for small businesses (e.g. beauty salons) to track stock across branches like HQ, Mbella, and Citibella.

---

## ✨ Features

- 🔐 **Login system** with role-based access (HQ, Mbella, Citibella)
- 🧾 **Auto-generated invoices** for stock transfers
- 🔄 **Stock transfer status tracking**: Preparing → Sent Out → Delivered → Received
- 🚨 **Low stock alerts** for items with quantity ≤ 1
- 📊 **Inventory dashboard**: Total SKUs, Low Stock Items, Branches
- 📁 **Transaction & Movement history** with Excel export
- 🧑‍💻 **Separate interfaces** for HQ and branch users
- 🎨 **Clean Bootstrap UI** (HTML + CSS)
- 🧪 Optional React frontend (`/frontend/`) — work in progress

---

## 🗂️ Project Structure

<pre>
📁 inventory-system/
├── app.py                # Flask backend logic
├── db.py                 # Database connection and helpers
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── .gitignore            # Git ignore list
├── inventory.csv         # Sample inventory data
├── invoice_generator.py  # PDF invoice generator
├── import_inventory.py   # Inventory import script
├── import_products.py    # Product import script
├── hq_products.csv       # HQ inventory data
│
├── templates/            # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── login.html
│   └── ... other HTML pages ...
│
├── static/
│   ├── style.css         # Optional custom styles
│   └── invoices/         # Auto-generated PDF invoices
│
├── frontend/             # (Optional) React UI (WIP)
│   ├── src/
│   ├── public/
│   └── package.json
│
└── venv/                 # Python virtual environment
</pre>

🚀 Getting Started
1. Clone the repository
git clone https://github.com/your-username/inventory-system.git
cd inventory-system

2. Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

3. Install dependencies
pip install -r requirements.txt
If requirements.txt doesn’t exist yet:
pip freeze > requirements.txt

4. Run the app
python app.py
Visit: http://localhost:5001

🧾 Invoice Naming Convention
Invoices are generated automatically with this format:
HQ-M-06/07/2025.pdf      # HQ to Mbella
HQ-C-06/07/2025.pdf      # HQ to Citibella
Saved in: static/invoices/

Stock Status Flow:
Preparing → (HQ) → Sent Out → (Branch) → Delivered → (HQ) → Received

📈 Dashboard Metrics
Total SKUs – Count of unique products
Low Stock Items – Items with quantity ≤ 1
Branches – Detected from inventory data

📤 Exporting Data
Go to Transaction History and click on 📥 Export to Excel.
A .xlsx file will be downloaded for offline reporting.

🛠️ Technologies Used
Backend: Flask, SQLite, Jinja2

Frontend: HTML, CSS, Bootstrap 5

PDF Generation: ReportLab

Data Export: pandas + openpyxl

User Sessions: Flask session

Cross-Origin Support: flask_cors (for future React UI)


🧭 Future Plans
✅ Fully integrated React frontend

✅ User registration and secure password storage

✅ Real-time stock alert notifications

✅ Inventory analytics and charts

✅ Mobile-responsive layout

📄 License
MIT License – feel free to use, improve, and adapt!

🙋‍♀️ Author
Made with 💖 by Raine Tan


---