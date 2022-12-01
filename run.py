
import sys

import flask
from flask_migrate import Migrate
from sys import exit
from decouple import config
import mariadb
from apps.config import config_dict
from apps import create_app, db

# WARNING: Don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

# Connect to MariaDB Platform
try:
    conn = mariadb.connect(
        user="root",
        password="invlab",
        host="127.0.0.1",
        port=3306,
        database="invlab"

    )
    print(f'Connected to Mariadb: {conn.database}')

    # Get Cursor
    cur = conn.cursor()

except mariadb.Error as e:
    print(f"Error connecting to MariaDB Platform: {e}")
    sys.exit(1)


try:

    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]

except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = create_app(app_config)

@app.context_processor
def inject_stage_and_region():
    ip_address = flask.request.remote_addr
    return dict(stage="alpha", region="NA",server_address=ip_address+':5000')
Migrate(app, db)

if DEBUG:
    app.logger.info('DEBUG       = ' + str(DEBUG))
    app.logger.info('Environment = ' + get_config_mode)
    app.logger.info('DBMS        = ' + app_config.SQLALCHEMY_DATABASE_URI)

if __name__ == "__main__":
    app.run()
