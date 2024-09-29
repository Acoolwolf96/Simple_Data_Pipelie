import time
import psycopg2
from config import config

def connect():
    connection = None
    retries = 5
    while retries > 0:
        try:
            params = config()
            print('Connecting to database...')
            connection = psycopg2.connect(**params)
            crsr = connection.cursor()
            crsr.execute('SELECT version()')
            db_version = crsr.fetchone()
            print(f"Database version: {db_version}")
            crsr.close()
            break 
        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error connecting to database: {error}")
            retries -= 1
            print(f"Retrying... ({retries} retries left)")
            time.sleep(5)
        finally:
            if connection is not None: 
                connection.close()
                print('Database Connection Terminated!')

def create_table():
    connection = None
    try:
        params = config()
        print("Connecting to Database...")
        connection = psycopg2.connect(**params)
        crsr = connection.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS weather_data (
            id SERIAL PRIMARY KEY,
            city VARCHAR(255),
            temperature FLOAT,
            humidity INTEGER,
            wind REAL,
            pressure INT,
            description VARCHAR(255),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        crsr.execute(create_table_query)
        connection.commit()
        print("Table has been created!")

        # Check if the table exists
        crsr.execute("SELECT EXISTS(SELECT FROM information_schema.tables WHERE table_name = 'weather_data');")
        if crsr.fetchone()[0]:
            print("Table 'weather_data' exists.")
        else:
            print("Table 'weather_data' does not exist.")

        # Fetch data from the table (if any)
        crsr.execute("SELECT * FROM weather_data")
        rows = crsr.fetchall()  # Fetch the data
        if rows:
            print("Weather data:", rows)
        else:
            print("No data found in the 'weather_data' table.")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f'Error while creating table\n{error}')

    finally:
        if connection is not None:
            connection.close()
            print('Database connection is closed.')
