import time

import flask
from flask_migrate import Migrate
from sys import exit
from decouple import config
import threading
import serverprocess
from apps.config import config_dict
from apps import create_app, db


# WARNING: Don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

# The configuration
get_config_mode = 'Debug' if DEBUG else 'Production'

try:

    # Load the configuration using the default values
    app_config = config_dict[get_config_mode.capitalize()]

except KeyError:
    exit('Error: Invalid <config_mode>. Expected values [Debug, Production] ')

app = create_app(app_config)

def serverprocess_thread():
    while True:
        serverprocess.main()
        time.sleep(180)
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
    thread = threading.Thread(target=serverprocess_thread)
    thread.start()
    app.run()






