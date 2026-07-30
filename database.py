import mysql.connector

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="jayasurya*04",
        database="knowledge_trading_erp"
    )