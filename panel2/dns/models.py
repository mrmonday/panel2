#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from panel2 import app, db

import time

class Domain(db.Model):
    __tablename__ = 'domains'

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

        self.add_record(self.name, 'dns.tortois.es ' + user.email + ' 0', 'SOA')
        self.add_record(self.name, 'ns1.tortois.es', 'NS')
        self.add_record(self.name, 'ns2.tortois.es', 'NS')

    def __repr__(self):
        return "<Domain: '%s'>" % (self.name)

    def add_record(self, name, content, type='A', prio=0, ttl=300):
        return Record(name, type, prio, content, ttl, self.id)

    def full_name(self, subdomain):
        if subdomain != '':
            return subdomain + '.' + self.name

        return self.name

class Record(db.Model):
    __tablename__ = 'records'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    type = db.Column(db.String(20))
    prio = db.Column(db.Integer)
    ttl = db.Column(db.Integer)
    content = db.Column(db.String(255))
    change_date = db.Column(db.Integer)
    domain_id = db.Column(db.Integer, db.ForeignKey('domains.id'))
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

    def update_name(self, name):
        self.name = name
        self.change_date = int(time.time())

        db.session.add(self)
        db.session.commit()

    def update_content(self, content):
        self.content = content
        self.change_date = int(time.time())

        db.session.add(self)
        db.session.commit()

    def subdomain(self):
        return self.name.rstrip(self.domain.name).rstrip('.')

class Supermaster(db.Model):
    """A class which reflects the PowerDNS supermasters table.  Presently
       unused, but we need this model to ensure it is in the schema, otherwise
       PowerDNS may crash."""
    __tablename__ = 'supermasters'

    id = db.Column(db.Integer, primary_key=True)
    nameserver = db.Column(db.String(255), nullable=False)
    account = db.Column(db.String(40))

    def __init__(self, nameserver, account):
        self.nameserver = nameserver
        self.account = account

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Supermaster: '%s'>" % self.nameserver

