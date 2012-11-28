#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from panel2 import app, db

import time

class Domain(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True)
    master = db.Column(db.String(128))
    type = db.Column(db.String(6), default='NATIVE')
    last_check = db.Column(db.Integer)
    notified_serial = db.Column(db.Integer)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='domains')

    def __init__(self, user, name):
        self.name = name
        self.user_id = user.id

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Domain: '%s'>" % (self.name)

    def add_record(self, name, content, type='A', prio=0, ttl=300):
        return Record(name, type, prio, content, ttl, self.id)

class Record(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    type = db.Column(db.String(20))
    prio = db.Column(db.Integer)
    ttl = db.Column(db.Integer)
    content = db.Column(db.String(255))
    change_date = db.Column(db.Integer)
    domain_id = db.Column(db.Integer, db.ForeignKey('domain.id'))
    domain = db.relationship('Domain', backref='records')

    def __init__(self, name, type, prio, content, ttl, domain_id):
        self.name = name
        self.type = type
        self.prio = prio
        self.content = content
        self.ttl = ttl
        self.domain_id = domain_id
        self.change_date = int(time.time())

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Record: '%s' -> '%s' (%s)>" % (self.name, self.content, self.type)
