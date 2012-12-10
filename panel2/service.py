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

from panel2 import app, db

class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(255))
    type = db.Column(db.String(50))
    expiry = db.Column(db.Integer)
    price = db.Column(db.Float)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='services')

    __mapper_args__ = {'polymorphic_on': type}

    def create(self):
        pass

    def suspend(self):
        pass

    def destroy(self):
        pass

    def invoice(self, invoice):
        pass

    def attach_ip(self, ip):
        return IPAddressRef(ip, self.user, self)

class IPAddress(db.Model):
    __tablename__ = 'ips'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(255))

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='ips')

    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    service = db.relationship('Service', backref='ips')

    def __init__(self, ip, user=None, service=None):
        self.ip = ip

        if user is not None:
            self.update_user(user)

        if service is not None:
            self.update_service(service)

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        base = "<IP: %s" % self.ip

        if self.service is not None:
            base = base + " [%s]" % repr(self.service)

        if self.user is not None:
            base = base + " {%s}" % repr(self.user)

        base = base + ">"
        return base

    def update_service(self, service):
        if self.service == service:
            return

        self.service_id = service.id
        self.service = service

        db.session.add(self)
        db.session.commit()

    def update_user(self, user):
        if self.user == user:
            return

        self.user_id = user.id
        self.user = user

        db.session.add(self)
        db.session.commit()

def IPAddressRef(ip, user=None, service=None):
    '''A wrapper around the IPAddress constructor which handles lookup as well as
       creation of IP address records.'''
    ip_obj = IPAddress.query.filter_by(ip=ip).first()
    if ip_obj is not None:
        if user is not None:
            ip_obj.update_user(user)
        if service is not None:
            ip_obj.update_service(service)
        return ip_obj

    return IPAddress(ip, user, service)
