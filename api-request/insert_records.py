# Using psycopg2 to connect to PostgreSQL and insert records
import psycopg2
# Import functions from api_request module# Import functions from api_request module
from api_request import mock_fetch_data, fetch_data 

def connect_to_db():
    print("Connecting to the PostgreSQL database...")
    try:
        conn = psycopg2.connect(
            host="db",
            port=5432,
            dbname="db",
            user="db_user",
            password="db_password"
        )
        return conn
    except psycopg2.Error as e:
        print(f"An error occurred while connecting to the database: {e}")
        raise

def create_table(conn):
    print("Creating table if it does not exist...")
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE SCHEMA IF NOT EXISTS dev;
            CREATE TABLE IF NOT EXISTS dev.raw_weather_data (
                id SERIAL PRIMARY KEY,
                city TEXT,
                temperature FLOAT,
                weather_descriptions TEXT,
                wind_speed FLOAT, 
                time TIMESTAMP,
                inserted_at TIMESTAMP DEFAULT NOW(),
                utc_offset TEXT
            );
        """)
        conn.commit()
        print("Table was created.")
    except psycopg2.Error as e:
        print(f'Failed to create table: {e}')
        raise

# Function to insert a record into the database, will be used to insert the API response
def insert_record(conn, data):
    print("Inserting record into the database...")
    try: 
        weather = data['current']
        location = data['location']
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO dev.raw_weather_data (
                city,
                temperature,
                weather_descriptions,
                wind_speed,
                time,
                inserted_at,
                utc_offset
            )
            VALUES (%s, %s, %s, %s, %s, NOW(), %s) 
        """, (
            location['name'],
            weather['temperature'],
            weather['weather_descriptions'][0],
            weather['wind_speed'],
            location['localtime'],
            location['utc_offset']
        )) # Using %s placeholders to prevent SQL injection
        conn.commit()
        print('Data successfully inserted')
    except psycopg2.Error as e:
        print(f'Error inserting data into the database: {e}')
        raise

# Packaging everything together into the main function 
def main():
    try:
        #data = mock_fetch_data()  # Use mock data for testing
        conn = connect_to_db()
        create_table(conn)
        data = fetch_data()  # Replace with mock_fetch_data() to test
        insert_record(conn, data)
    except Exception as e:
        print(f"An error occurred during execution: {e}")
    finally: # Ensure the connection is closed independently of success or failure
        if 'conn' in locals(): # Verify if conn variable exists before closing
            conn.close()
            print("Database connection closed.")