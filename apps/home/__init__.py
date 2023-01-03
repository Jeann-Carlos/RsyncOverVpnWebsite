# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import threading
import time

import serverprocess
from flask import Blueprint

blueprint = Blueprint(
    'home_blueprint',
    __name__,
    url_prefix=''
)

def serverprocess_thread():
    while True:
        serverprocess.main()
        time.sleep(180)


thread = threading.Thread(target=serverprocess_thread)
thread.start()