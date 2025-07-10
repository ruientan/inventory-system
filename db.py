import mysql.connector
import pymysql
pymysql.install_as_MySQLdb()

def get_connection():
    return mysql.connector.connect(
        host='localhost',  
        user="root",
        password="JacksonYee1128",
        database="inventory_db"
    )



    