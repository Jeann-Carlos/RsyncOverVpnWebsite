# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from flask_login import UserMixin

from apps import db, login_manager

from apps.authentication.util import hash_pass

class Users(db.Model, UserMixin):

    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True)
    USERNAME = db.Column(db.String(64), unique=True)
    EMAIL = db.Column(db.String(64), unique=True)
    PASSWORD = db.Column(db.String(300))
    CLIENT_ID =  db.Column(db.Integer,db.ForeignKey('clientes.CLIENT_ID'),default=10)

    def __init__(self, **kwargs):
        for property, value in kwargs.items():
            # depending on whether value is an iterable or not, we must
            # unpack it's value (when **kwargs is request.form, some values
            # will be a 1-element list)
            if hasattr(value, '__iter__') and not isinstance(value, str):
                # the ,= unpack of a singleton fails PEP8 (travis flake8 test)
                value = value[0]

            if property == 'password':
                value = hash_pass(value)  # we need bytes here (not plain str)

            setattr(self, property.upper(), value)

    def __repr__(self):
        return str(self.USERNAME)


class clientes(db.Model, UserMixin):
    __tablename__ = 'clientes'
    CLIENT_ID = db.Column(db.Integer, primary_key=True)
    IP_VPN = db.Column(db.String(64))


class host(db.Model, UserMixin):
    __tablename__ = 'host'
    HOST_ID = db.Column(db.Integer, primary_key=True)
    HOST_IP = db.Column(db.String(64))
    CLIENT_ID = db.Column(db.Integer,db.ForeignKey('clientes.CLIENT_ID'))


class logs_servicios(db.Model, UserMixin):
    __tablename__ = 'logs_servicios'
    SERVICIOS_ID = db.Column(db.Integer,db.ForeignKey('servicios.SERVICIOS_ID'), primary_key=True,)
    STATUS = db.Column(db.String(64))
    NOMBRE = db.Column(db.String(64))
    TIMESTAMP = db.Column(db.String(300), primary_key=True)
class logs(db.Model, UserMixin):
    __tablename__ = 'logs'
    LOG_ID = db.Column(db.Integer, primary_key=True)
    HOST_ID = db.Column(db.Integer,db.ForeignKey('host.HOST_ID'))
    STATUS = db.Column(db.String(300))
    HADDRS = db.Column(db.String(300))
    TIMESTAMP = db.Column(db.String(300))

class servicios(db.Model, UserMixin):
    __tablename__ = 'servicios'
    SERVICIOS_ID = db.Column(db.Integer, primary_key=True)
    PORT = db.Column(db.String(64))
    PROTOCOL = db.Column(db.String(64))
    HOST_ID = db.Column(db.Integer,db.ForeignKey('host.HOST_ID'))
@login_manager.user_loader
def user_loader(id):
    return Users.query.filter_by(id=id).first()


@login_manager.request_loader
def request_loader(request):
    username = request.form.get('username')
    user = Users.query.filter_by(USERNAME=username).first()
    return user if user else None
