# 📦 Inventory Management System

A lightweight, role-based inventory tracking system for managing stock transfers, restocks, and product usage across multiple branches like **HQ**, **Mbella**, and **Citibella**. Built using **Flask**, **SQLite**, and **Bootstrap**, this system is simple to deploy and extend.

---

## 🌟 Features

- 🔐 **Login system** with role-based access (HQ, Mbella, Citibella)
- 🧾 **Auto-generated invoices** for stock transfers
- 🔄 **Stock transfer status tracking**: Preparing → Sent Out → Delivered → Received
- 📉 **Low stock alerts** for items with quantity ≤ 1
- 🧮 **Inventory dashboard**: Total SKUs, Low Stock Items, Branches
- 🕓 **Transaction & Movement history** with Excel export
- 🧑‍💻 **Separate interfaces** for HQ and branch users
- 💅 Clean and responsive **Bootstrap UI**
- ⚛️ Optional React frontend in `frontend/` folder (WIP)

---

## 🗂️ Project Structure

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

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/your-username/inventory-system.git
cd inventory-system
2. Create a virtual environment and activate it
bash
Copy
Edit
python3 -m venv venv
source venv/bin/activate
3. Install the dependencies
bash
Copy
Edit
pip install -r requirements.txt
If you don’t have requirements.txt yet:

bash
Copy
Edit
pip freeze > requirements.txt
4. Run the app
bash
Copy
Edit
python app.py
The server will start at http://localhost:5001

🧾 Sample Invoice Naming
Invoices are automatically generated upon transfer with the format:

bash
Copy
Edit
HQ-M-06/07/2025.pdf      # HQ to Mbella
HQ-C-06/07/2025.pdf      # HQ to Citibella
Saved in: static/invoices/

🧠 Usage Overview
User Role	Can View	Can Edit	Can Confirm
HQ	All branches	All stock	Can mark “Sent Out” and “Received”
Mbella	Own branch	Own stock	Can mark “Delivered”
Citibella	Own branch	Own stock	Can mark “Delivered”

Status Flow:
Preparing → (HQ) → Sent Out

Sent Out → (Branch) → Delivered

Delivered → (HQ) → Received

📈 Dashboard Highlights
Total SKUs: Count of unique products

Low Stock Items: Items with quantity ≤ 1

Branches: Detected from your database

📤 Exporting Data
Go to Transaction History and click on 📥 Export to Excel. The .xlsx file will be downloaded for offline reporting.

🛠️ Technologies Used
Backend: Flask, SQLite, Jinja2

Frontend: HTML, CSS, Bootstrap 5

PDF Generation: ReportLab

Data Export: Pandas + OpenPyXL

Role Management: Flask Sessions

CORS (for future React integration): flask_cors

🧑‍💻 Contribution
Want to improve this project?

Fork the repo

Create your feature branch: git checkout -b feature-name

Commit your changes: git commit -m 'Add some feature'

Push to the branch: git push origin feature-name

Open a pull request!

🧭 Future Plans
 Fully integrated React frontend

 Add user registration and secure password storage

 Real-time alerts for stock below threshold

 Inventory analytics and charting

 Mobile-friendly layout improvements

📄 License
MIT License – feel free to use, improve and adapt!

🙋‍♀️ Author
Made with 💖 by Raine Tan