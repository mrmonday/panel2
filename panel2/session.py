#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs LLC

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice, this permission notice and all necessary source code
to recompile the software are included or otherwise available in all
distributions.

This software is provided 'as is' and without any warranty, express or
implied.  In no event shall the authors be liable for any damages arising
from the use of this software.
"""

import sys
import hashlib
import blinker

from panel2 import app
from panel2.user import User, get_session_user
from panel2.utils import is_email_valid
from flask import session, redirect, url_for, escape, request, render_template
from sqlalchemy.exc import IntegrityError

login_signal = blinker.Signal('A signal sent when the user logs in')
logout_signal = blinker.Signal('A signal sent when the user logs out')
authfail_signal = blinker.Signal('A signal sent when the user fails authentication')

@login_signal.connect_via(app)
def handle_session_login(*args, **kwargs):
    user = kwargs.pop('user', None)
    session['uid'] = user.id

@logout_signal.connect_via(app)
def handle_session_logout(*args, **kwargs):
    session.pop('uid', None)

def validate_login(username, password):
    u = User.query.filter_by(username=username).first()
    if u is None:
        authfail_signal.send(app, user=u, reason='Invalid username')
        return False
    if u.validate_password(password) is False:
        authfail_signal.send(app, user=u, reason='Invalid password')
        return False

    # Password validation was successful, fire the login event.
    login_signal.send(app, user=u)
    return True

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = validate_login(request.form['username'], request.form['password'])
        if user is not False:
            return redirect(url_for('index'))
        else:
            session.pop('uid', None)
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/logout')
def logout():
    _user = get_session_user()
    if _user is not None:
        logout_signal.send(app, user=_user)

    return redirect(url_for('index'))

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        try:
            username = request.form['username'].strip().rstrip()
            password = request.form['password'].strip().rstrip()
            email = request.form['email'].strip().rstrip()
            if len(username) == 0:
                return render_template('create.html', error='No username provided') 
            if len(password) == 0:
                return render_template('create.html', error='No password provided') 
            if len(email) == 0:
                return render_template('create.html', error='No email provided') 
            user = User(username, password, email)
        except:
            return render_template('create.html', error='Username is already taken')
            
        if user is not None:
            session['uid'] = user.id
            return redirect(url_for('index'))

    return render_template('create.html')

@app.context_processor
def user_information_from_session():
    """A decorated function to give the templates a user object if we're logged in."""
    _user = get_session_user()
    if _user is not None:
        return dict(user=_user)

    return dict()