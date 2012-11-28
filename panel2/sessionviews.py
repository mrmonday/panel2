#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from panel2 import app
from panel2.models import User
from flask import session, redirect, url_for, escape, request, render_template

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

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('uid', None)
    return redirect(url_for('index'))
