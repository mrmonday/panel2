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
import ipaddress

class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(255))
    type = db.Column(db.String(50))
    expiry = db.Column(db.Integer)
    price = db.Column(db.Float)
    is_entitled = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='services')

    __mapper_args__ = {'polymorphic_on': type}

    def delete(self):
        for ip in self.ips:
            ip.service_id = None
            ip.service = None

            ip.user_id = None
            ip.user = None

            db.session.add(ip)

        db.session.delete(self)
        db.session.commit()
        del self

    def create(self):
        pass

    def suspend(self):
        pass

    def invoice(self, invoice):
        pass

    def attach_ip(self, ip, ipnet=None):
        return IPAddressRef(ip, ipnet, self.user, self)

    def entitle(self):
        self.is_entitled = True

        db.session.add(self)
        db.session.commit()

class IPAddress(db.Model):
    __tablename__ = 'ips'
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(255))

    ipnet_id = db.Column(db.Integer, db.ForeignKey('ip_range.id'))
    ipnet = db.relationship('IPRange', backref='assigned_ips')

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='ips')

    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    service = db.relationship('Service', backref='ips')

    def __init__(self, ip, user=None, service=None, ipnet=None):
        self.ip = ip
        self.ipnet = ipnet
        self.ipnet_id = ipnet.id

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

def IPAddressRef(ip, ipnet=None, user=None, service=None):
    '''A wrapper around the IPAddress constructor which handles lookup as well as
       creation of IP address records.'''
    ip_obj = IPAddress.query.filter_by(ip=ip).first()
    if ip_obj is not None:
        if user is not None:
            ip_obj.update_user(user)
        if service is not None:
            ip_obj.update_service(service)
        return ip_obj

    return IPAddress(ip, user, service, ipnet)

class IPRange(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50))
    network = db.Column(db.String(255))

    __mapper_args__ = {'polymorphic_on': type}

    def __repr__(self):
        return "<IPRange: {}>".format(self.network)

    def ipnet(self):
        return ipaddress.ip_network(self.network)

    def is_ipv6(self):
        return self.ipnet().version == 6

    def gateway(self):
        return str(self.ipnet().network_address + 1)

    def broadcast(self):
        return str(self.ipnet().broadcast_address)

    def available_ips(self):
        iplist = []
        for host in self.ipnet().iterhosts():
            if str(host) == self.gateway():
                continue
            ip_obj = IPAddress.query.filter_by(ip=str(host)).first()
            if ip_obj is None:
                iplist.append(str(host))
            elif ip_obj.service is None:
                iplist.append(str(host))
        return iplist

    def assign_first_available(self, user=None, service=None):
        iplist = self.available_ips()
        if len(iplist) < 1:
            return None
        return IPAddressRef(iplist[0], self, user, service)
