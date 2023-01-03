# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""
import threading

from flask import render_template, redirect, request, url_for
import re
from flask_login import (
    current_user,
    login_user,
    logout_user
)

import serverprocess
from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users

from apps.authentication.util import verify_pass


@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))


# Login & Registration

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    def serverprocess_thread():
        serverprocess.main()

    thread = threading.Thread(target=serverprocess_thread)
    thread.start()
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        USERNAME = request.form['username']
        PASSWORD = request.form['password']

        # Locate user
        user = Users.query.filter_by(USERNAME=USERNAME).first()

        # Check the PASSWORD
        if user and verify_pass(PASSWORD, user.PASSWORD):

            login_user(user)
            return redirect(url_for('authentication_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html',
                               msg='Wrong user or PASSWORD',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.index'))


# for validating an EMAIL

@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    def check(EMAIL):
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if (re.fullmatch(regex, EMAIL)):
            return True
        else:
            return False


    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        USERNAME = request.form['username']
        EMAIL = request.form['email']

        # Check usename exists
        user = Users.query.filter_by(USERNAME=USERNAME).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='USERNAME already registered',
                                   success=False,
                                   form=create_account_form)

        # Check EMAIL exists
        user = Users.query.filter_by(EMAIL=EMAIL).first()
        if user or not check(EMAIL):
            return render_template('accounts/register.html',
                                   msg='EMAIL already registered or invalid EMAIL',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        user = Users(**request.form)
        db.session.add(user)
        db.session.commit()
     #   cur.execute(f"insert into usuarios(USERNAME, EMAIL, PASSWORD, client_id) value ('{USERNAME}','{EMAIL}','{ user.PASSWORD.decode('UTF-8')}',4)")
     #   conn.commit()

        return render_template('accounts/register.html',
                               msg='User created please <a href="/login">login</a>',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login'))


# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500
