import csv
from db import get_connection

def import_products_from_csv(csv_file_path):
    conn = get_connection()
    cursor = conn.cursor()

    
    with open(csv_file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            product_name = row['product_name']
            supplier_name = row['supplier_name']
            category = row['category']
            unit_price = float(row['unit_price']) if row['unit_price'] else 0.0
            reorder_level = 0  # Default value

            cursor.execute("""
                INSERT INTO products (product_name, supplier_name, category, unit_price, reorder_level)
                VALUES (%s, %s, %s, %s, %s)
            """, (product_name, supplier_name, category, unit_price, reorder_level))

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ Import complete!")

# Run the function
if __name__ == '__main__':
    import_products_from_csv('hq_products.csv')