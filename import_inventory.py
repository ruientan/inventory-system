# import_inventory.py

import csv
from db import get_connection

def import_inventory_from_csv(csv_file_path):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            product_name = row['product_name'].strip()
            location_name = row['location_name'].strip()
            quantity = int(row['quantity'])

            # Get product_id
            cursor.execute("SELECT product_id FROM products WHERE product_name = %s", (product_name,))
            product_result = cursor.fetchone()
            if not product_result:
                print(f"❌ Product not found: {product_name}")
                continue
            product_id = product_result['product_id']

            # Get location_id
            cursor.execute("SELECT location_id FROM locations WHERE name = %s", (location_name,))
            location_result = cursor.fetchone()
            if not location_result:
                print(f"❌ Location not found: {location_name}")
                continue
            location_id = location_result['location_id']

            # Check if already exists
            cursor.execute(
                "SELECT * FROM inventory WHERE product_id = %s AND location_id = %s",
                (product_id, location_id)
            )
            if cursor.fetchone():
                print(f"⚠️ Inventory already exists: {product_name} @ {location_name}")
                continue

            # Insert into inventory
            cursor.execute("""
                INSERT INTO inventory (product_id, location_id, quantity)
                VALUES (%s, %s, %s)
            """, (product_id, location_id, quantity))
            print(f"✅ Added: {product_name} @ {location_name} = {quantity}")

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Import complete!")

# Run it
if __name__ == '__main__':
    import_inventory_from_csv('inventory.csv')
