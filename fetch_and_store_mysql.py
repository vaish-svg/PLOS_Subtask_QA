import requests
import json
import time
import mysql.connector
from mysql.connector import Error

# MySQL Database connection details
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'root',
    'database': 'plos_keytask_ready'
}

# Connect to MySQL
def create_connection():
    try:
        connection = mysql.connector.connect(**db_config)
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

# Create table if not exists
def create_table_if_not_exists(connection):
    try:
        cursor = connection.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS plos_key_tasks (
                id INT AUTO_INCREMENT PRIMARY KEY,
                taskName VARCHAR(100),
                shortCode VARCHAR(100),
                receivedAt DATETIME,
                doi VARCHAR(255),
                data LONGTEXT,
                fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                proofDeliveryStatus VARCHAR(100),
                submittedBy VARCHAR(100),
                submittedDate DATETIME
            )
        ''')
        connection.commit()
    except Error as e:
        print(f"Error creating table: {e}")

# API Details
url = "https://pubsub.newgen.co/reportsmicro/reports/approved_queries/getploskeytasksready"

payload = json.dumps({
    "where": {
        "receiveddate": "2025-04-17 04:00:00"
    }
})

headers = {
    'email': 'vijayachandran.c@newgen.co',
    'token': 'afaa7b95fa0d6ea5a1cbad45181b0bf9-53d61c9f5860b321636130f695c18f9f',
    'Content-Type': 'application/json'
}

# Fetch data and insert into MySQL
def fetch_and_store(connection):
    try:
        response = requests.post(url, headers=headers, data=payload)
        if response.status_code == 200:
            records = response.json()
            cursor = connection.cursor()

            for record in records:
                cursor.execute('''
                    INSERT INTO plos_key_tasks (
                        taskName, shortCode, receivedAt, doi,
                        data, proofDeliveryStatus, submittedBy, submittedDate
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    record.get('taskName'),
                    record.get('shortCode'),
                    record.get('receivedAt'),
                    record.get('doi'),
                    json.dumps(record),
                    record.get('proofDeliveryStatus'),
                    record.get('submittedBy'),
                    record.get('submittedDate')
                ))

            connection.commit()
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {len(records)} records inserted successfully.")
        else:
            print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Failed to fetch data. Status code: {response.status_code}")
    except Exception as e:
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error: {e}")

# Main loop: every 30 minutes
if __name__ == "__main__":
    connection = create_connection()
    if connection:
        create_table_if_not_exists(connection)
        print("Starting fetch and store service... (runs every 30 minutes)")
        while True:
            fetch_and_store(connection)
            time.sleep(1800)  # 30 minutes
