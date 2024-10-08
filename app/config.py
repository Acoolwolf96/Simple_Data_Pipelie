from configparser import ConfigParser
import os
import urllib.parse as urlparse


def config(filename="database.ini", section="postgresql"):
    #create a parser
    parser = ConfigParser()
    #read config file 
    parser.read(filename)

    db = {}

    if parser.has_section(section):
        params = parser.items(section)
        for param in params:
            db[param[0]] = param[1]
    else:
        raise Exception(
            f'Section {section} not found in the {filename} file'
        )    
    return db    

def config_render():
    # Get the DATABASE_URL environment variable
    database_url = os.getenv('DATABASE_URL')
    
    # Parse the URL into components
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    # Use urlparse to break down the URL
    url = urlparse.urlparse(database_url)
    
    # Construct parameters dictionary
    db_config = {
        'host': url.hostname,
        'database': url.path[1:],  # Remove the leading '/'
        'port': url.port,
        'user': url.username,
        'password': url.password
    }

    # Print out the configuration for debugging
    print("Database configuration from DATABASE_URL:")
    for key, value in db_config.items():
        print(f"{key}: {value}")

    return db_config

