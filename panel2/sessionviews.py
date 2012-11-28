#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

import sys
import hashlib

from panel2 import app
from panel2.models import User
from flask import session, redirect, url_for, escape, request, render_template
from sqlalchemy.exc import IntegrityError

def validate_login(username, password):
    u = User.query.filter_by(username=username).first()
    if u is None:
        return None
    if u.validate_password(password) is False:
        return None
    return u

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = validate_login(request.form['username'], request.form['password'])
        if user is not None:
            session['uid'] = user.id
            return redirect(url_for('index'))
        else:
            session.pop('uid', None)
            return render_template('login.html', error='Invalid username or password')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('uid', None)
    return redirect(url_for('index'))

@app.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        try:
            user = User(request.form['username'], request.form['password'], request.form['email'])
        except IntegrityError:
            return render_template('create.html', error='Username is already taken')
            
        if user is not None:
            session['uid'] = user.id
            return redirect(url_for('index'))

    return render_template('create.html')

@app.context_processor
def user_information_from_session():
    """A decorated function to give the templates a user object if we're logged in."""
    if session.has_key('uid'):
        _user = User.query.filter_by(id=session['uid']).first()
        return dict(user=_user)

    return dict()

@app.template_filter('gravatar')
def user_gravatar_url(email):
    return "https://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + "?s=18"
