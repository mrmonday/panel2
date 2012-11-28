#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from panel2 import app, db
from panel2.pbkdf2 import pbkdf2_hex

import hashlib, os

class User(db.Model):
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
        self.assign_password(password)

    def __repr__(self):
        return "<User '%s'>%s" % (self.username, (" {admin}" if self.is_admin is True else ""))

    def _get_pbkdf2_hash(self, password):
        return pbkdf2_hex(password, self.salt, 1000, 64, hashlib.sha512)

    def validate_password(self, password):
        "Validate password against the user's password."
        if self._get_pbkdf2_hash(password) == self.password:
            return True
        return False

    def assign_password(self, new_password):
        self.salt = os.urandom(16).encode('hex')
        self.password = self._get_pbkdf2_hash(new_password)

        db.session.add(self)
        db.session.commit()

