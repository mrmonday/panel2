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

from functools import wraps
from flask import session, redirect, url_for, abort, render_template

from panel2 import app, db
from panel2.pbkdf2 import pbkdf2_hex
from panel2.utils import send_simple_email

import hashlib, os
import blinker

createuser_signal = blinker.Signal('A signal which is fired when a user is created')

class User(db.Model):
    extend_existing=True
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(128))
    email = db.Column(db.String(255))
    address1 = db.Column(db.String(255))
    address2 = db.Column(db.String(255))
    city = db.Column(db.String(255))
    state = db.Column(db.String(255))
    country = db.Column(db.String(255))
    phone = db.Column(db.String(255))
    zip = db.Column(db.String(255))
    salt = db.Column(db.String(32))
    is_admin = db.Column(db.Boolean)

    def __init__(self, username, password, email):
        self.username = username
        self.email = email
        self.assign_password(password.encode('utf-8'))

        createuser_signal.send(app, user=self)

    def __repr__(self):
        return "<User '%s'>%s" % (self.username, (" {admin}" if self.is_admin is True else ""))

    def _get_pbkdf2_hash(self, password):
        return pbkdf2_hex(password, self.salt, 1000, 64, hashlib.sha512)

    def validate_password(self, password):
        "Validate password against the user's password."
        if self._get_pbkdf2_hash(password.encode('utf-8')) == self.password:
            return True
        return False

    def assign_password(self, new_password):
        self.salt = os.urandom(16).encode('hex')
        self.password = self._get_pbkdf2_hash(new_password)

        db.session.add(self)
        db.session.commit()

    def assign_email(self, new_email):
        self.email = new_email

        db.session.add(self)
        db.session.commit()

    def send_email(self, subject, template, **kwargs):
        message = render_template(template, user=self, **kwargs)
        send_simple_email(recipient=self.email, subject=subject, message=message)

def get_session_user():
    if session.has_key('uid'):
        return User.query.filter_by(id=session['uid']).first()

    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if get_session_user() is None:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_session_user()
        if user is None:
            return redirect(url_for('login'))
        if user.is_admin is not True:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function
