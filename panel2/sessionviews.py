#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

import sys
import hashlib

from panel2 import app
from panel2.models import User, get_session_user
from panel2.utils import is_email_valid
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

@app.template_filter('gravatar')
def user_gravatar_url(email, size=24):
    return "https://www.gravatar.com/avatar/" + hashlib.md5(email.lower()).hexdigest() + ("?s=%d" % size)

@app.template_filter('time_ago')
def pretty_date(time=False):
    """
    Get a datetime object or a int() Epoch timestamp and return a
    pretty string like 'an hour ago', 'Yesterday', '3 months ago',
    'just now', etc.  Pretty much ganked this from Atheme and rewrote
    it in python.
    """
    from datetime import datetime
    now = datetime.now()
    if type(time) is long:
        time = int(time)
    if type(time) is int:
        diff = now - datetime.fromtimestamp(time)
    elif isinstance(time,datetime):
        diff = now - time 
    elif not time:
        diff = now - now
    second_diff = diff.seconds
    day_diff = diff.days

    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(second_diff) + " seconds ago"
        if second_diff < 120:
            return  "a minute ago"
        if second_diff < 3600:
            return str( second_diff / 60 ) + " minutes ago"
        if second_diff < 7200:
            return "an hour ago"
        if second_diff < 86400:
            return str( second_diff / 3600 ) + " hours ago"
    if day_diff == 1:
        return "Yesterday"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(day_diff/7) + " weeks ago"
    if day_diff < 365:
        return str(day_diff/30) + " months ago"
    return str(day_diff/365) + " years ago"
