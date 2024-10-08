from configparser import ConfigParser
import os


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
    db = {
        'host': os.getenv('DB_HOST'),
        'database': os.getenv('DB_NAME'),
        'port': os.getenv('DB_PORT'),
        'user': os.getenv('DB_USER'),
        'password': os.getenv('DB_PASSWORD')
    }
    return db

