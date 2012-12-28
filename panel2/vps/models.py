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

import time
import rrdtool

from panel2 import app, db
from panel2.service import Service, IPRange
from panel2.job import QueueingProxy

from collections import OrderedDict

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

    def api(self, constructor=QueueingProxy):
        return constructor(self.ipaddr, 5959, self.secret, iterations=15, refid=self.id)

class NodeIPRange(IPRange):
    __mapper_args__ = {'polymorphic_identity': 'node'}
    node_id = db.Column(db.Integer, db.ForeignKey('node.id'))
    node = db.relationship('Node', backref='ipranges')

    def __init__(self, network, node):
        self.node = node
        self.node_id = node.id
        self.network = network

        db.session.add(self)
        db.session.commit()

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

    def create(self):
        return self.node.api().create(domname=self.name, memory=self.memory, ips=[ipaddr.ip for ipaddr in self.ips])

    def shutdown(self):
        return self.node.api().shutdown(domname=self.name)

    def destroy(self):
        return self.node.api().destroy(domname=self.name)

    def pause(self):
        return self.node.api().pause(domname=self.name)

    def unpause(self):
        return self.node.api().unpause(domname=self.name)

    def __repr__(self):
        return "<XenVPS: '%s' on '%s'>" % (self.name, self.node.name)

    def _make_path(self, type):
        return app.config['RRDPATH'] + '/' + self.node.name + '-' + self.name + '-' + type + '.rrd'

    def get_cpu_stats(self, start=600, step=60):
        now = int(time.time())
        start_ts = now - (now % step)
        negated = -start
        path = self._make_path('cpu')

	data = rrdtool.fetch(str(path), 'LAST', '-s', str(negated), '-e', str(start_ts))[2]
	begin_ts = start_ts - start
        set = []
        for i in data:
            if i[0] is None: continue
            set.append([begin_ts * 1000, i[0] / 10])
            begin_ts += step

        return {'label': 'CPU usage (%)', 'data': set, 'color': "#336633"}

    def get_net_stats(self, start=600, step=60):
        now = int(time.time())
        start_ts = now - (now % step)
        negated = -start
        path = self._make_path('net')

	data = rrdtool.fetch(str(path), 'LAST', '-s', str(negated), '-e', str(start_ts))[2]

	begin_ts = start_ts - start
        set = []
        for i in data:
            if i[0] is None: continue
            set.append([begin_ts * 1000, i[0]])
            begin_ts += step

        rxbytes = {'label': 'Bytes received', 'data': set, 'color': "#336633"}

	begin_ts = start_ts - start
        set = []
        for i in data:
            if i[0] is None: continue
            set.append([begin_ts * 1000, i[1]])
            begin_ts += step

        txbytes = {'label': 'Bytes sent', 'data': set, 'color': "#333366"}

        return [rxbytes, txbytes]

    def get_vbd_stats(self, start=600, step=60):
        now = int(time.time())
        start_ts = now - (now % step)
        negated = -start
        path = self._make_path('vbd')

	data = rrdtool.fetch(str(path), 'LAST', '-s', str(negated), '-e', str(start_ts))[2]

	begin_ts = start_ts - start
        set = []
        for i in data:
            if i[0] is None: continue
            set.append([begin_ts * 1000, i[0]])
            begin_ts += step

        rxbytes = {'label': 'Read requests', 'data': set, 'color': "#336633"}

	begin_ts = start_ts - start
        set = []
        for i in data:
            if i[0] is None: continue
            set.append([begin_ts * 1000, i[1]])
            begin_ts += step

        txbytes = {'label': 'Write requests', 'data': set, 'color': "#333366"}

	begin_ts = start_ts - start
        set = []
        for i in data:
            if i[0] is None: continue
            set.append([begin_ts * 1000, i[2]])
            begin_ts += step

        oobytes = {'label': 'Rescheduled requests', 'data': set, 'color': "#663333"}

        return [rxbytes, txbytes, oobytes]
