import time
import psycopg2
from app.config import config, config_render

def connect():
    connection = None
    retries = 5
    while retries > 0:
        try:
            # Try to connect using database.ini
            params = config()
            print('Connecting to database using database.ini...')
            connection = psycopg2.connect(**params)
            crsr = connection.cursor()
            crsr.execute('SELECT version()')
            db_version = crsr.fetchone()
            print(f"Database version: {db_version}")
            crsr.close()
            break  

        except (Exception, psycopg2.DatabaseError) as error:
            print(f"Error connecting to database using database.ini: {error}")
            retries -= 1
            print(f"Retrying... ({retries} retries left)")
            time.sleep(5)

            if retries == 0: #After retries
                print("Falling back to environment variables (Render)...")
                try:
                    params = config_render()
                    connection = psycopg2.connect(**params)
                    crsr = connection.cursor()
                    crsr.execute('SELECT version()')
                    db_version = crsr.fetchone()
                    print(f"Database version (Render): {db_version}")
                    crsr.close()
                    break  
                except (Exception, psycopg2.DatabaseError) as render_error:
                    print(f"Error connecting using Render environment variables: {render_error}")
                    time.sleep(5)
                    break  

        finally:
            if connection is not None:
                connection.close()
                print('Database Connection Terminated!')


def create_table():
    connection = None
    try:
        try:
            # Try to connect using database.ini
            params = config()
            print("Connecting to Database using database.ini...")
            connection = psycopg2.connect(**params)
        except (Exception, psycopg2.DatabaseError) as ini_error:
            print(f"Error using database.ini: {ini_error}")
            print("Falling back to Render environment variables...")
            params = config_render()
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

    except (Exception, psycopg2.DatabaseError) as error:
        print(f'Error while creating table\n{error}')

    finally:
        if connection is not None:
            connection.close()
            print('Database connection is closed.')



def create_cache_table():
    connection = None
    try:
        try:
            # Try to connect using database.ini
            params = config()
            print("Connecting to Database using database.ini...")
            connection = psycopg2.connect(**params)
        except (Exception, psycopg2.DatabaseError) as ini_error:
            print(f"Error using database.ini: {ini_error}")
            print("Falling back to Render environment variables...")
            params = config_render()
            connection = psycopg2.connect(**params)

        crsr = connection.cursor()

        create_table_query = """
        CREATE TABLE IF NOT EXISTS geocoding_cache (
            city VARCHAR(255) PRIMARY KEY,
            lat DOUBLE PRECISION,
            lng DOUBLE PRECISION,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        crsr.execute(create_table_query)
        connection.commit()
        print("Geocoding cache table has been created!")

    except (Exception, psycopg2.DatabaseError) as error:
        print(f'Error while creating geocoding cache table\n{error}')

    finally:
        if connection is not None:
            connection.close()
            print('Database connection is closed.')


