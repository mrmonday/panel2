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
from panel2.service import Service

class Region(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

    def __init__(self, name):
        self.name = name

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Region: '%s'>" % self.name

class Node(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    ipaddr = db.Column(db.String(255))
    secret = db.Column(db.String(255))

    region_id = db.Column(db.Integer, db.ForeignKey('region.id'))
    region = db.relationship('Region', backref='nodes')

    def __init__(self, name, ipaddr, secret, region):
        self.name = name

        self.ipaddr = ipaddr
        self.secret = secret

        self.region_id = region.id
        self.region = region

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Node: '%s' [%s]>" % (self.name, self.ipaddr)

class XenVPS(Service):
    __tablename__ = 'xenvps'
    __mapper_args__ = {'polymorphic_identity': 'xenvps'}
    vps_id = db.Column(db.Integer, primary_key=True)
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))

    memory = db.Column(db.Integer)
    swap = db.Column(db.Integer)
    disk = db.Column(db.Integer)

    node_id = db.Column(db.Integer, db.ForeignKey('node.id'))
    node = db.relationship('Node', backref='vps')

    name = db.Column(db.String(255))

    def __init__(self, name, memory, swap, disk, price, node, user):
        self.name = name

        self.memory = memory
        self.swap = swap
        self.disk = disk
        self.price = price

        self.node_id = node.id
        self.node = node

        self.user_id = user.id
        self.user = user

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<XenVPS: '%s' on '%s'>" % (self.name, self.node.name)

