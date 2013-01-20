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
from panel2.job import QueueingProxy, Job

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

    def available_node(self, memory, disk):
        for node in self.nodes:
            if len(node.available_ips()) > 0:
                return node

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

    def api(self, constructor=QueueingProxy, refid=None):
        if not refid:
            refid = self.id
        if constructor is not QueueingProxy:
            return constructor(self.ipaddr, 5959, self.secret, iterations=15)
        return constructor(self.ipaddr, 5959, self.secret, iterations=15, refid=refid)

    def available_ips(self):
        return [ip for iprange in self.ipranges for ip in iprange.available_ips()]

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

    def api(self, constructor=QueueingProxy):
        return self.node.api(constructor, self.id)

    def suspend(self):
        self.destroy()
        Service.suspend(self)

    def jobs(self):
        return Job.query.filter_by(refid=self.id)

    def delete(self):
        self.api().vps_destroy(domname=self.name)
        Service.delete(self)

    def create(self):
        return self.api().create(domname=self.name, memory=self.memory, ips=[ipaddr.ip for ipaddr in self.ips])

    def format(self):
        return self.api().vps_format(domname=self.name)

    def init(self):
        return self.api().vps_create(domname=self.name, size=self.disk, swap=self.swap, is_hvm=False)

    def image(self, template):
        eth0 = {
           'address': self.ips[0].ip,
           'netmask': str(self.ips[0].ipnet.ipnet().netmask),
           'broadcast': str(self.ips[0].ipnet.broadcast()),
           'gateway': str(self.ips[0].ipnet.gateway()),
        }
        return self.api().vps_image(domname=self.name, eth0=eth0, image=template)

    # XXX: presently MD5 Crypt is still the lowest common denominator...
    def rootpass(self, rootpass):
        from passlib.hash import md5_crypt
        return self.api().vps_rootpass(domname=self.name, newpasshash=md5_crypt.encrypt(rootpass))

    def shutdown(self):
        return self.api().shutdown(domname=self.name)

    def destroy(self):
        return self.api().destroy(domname=self.name)

    def pause(self):
        return self.api().pause(domname=self.name)

    def unpause(self):
        return self.api().unpause(domname=self.name)

    def reimage(self, template, password):
        self.destroy()
        self.format()
        self.image(template)
        self.rootpass(password)

    def __repr__(self):
        return "<XenVPS: '%s' on '%s'>" % (self.name, self.node.name)

    def _make_path(self, type):
        return app.config['RRDPATH'] + '/' + self.node.name + '-' + self.name + '-' + type + '.rrd'

    def get_cpu_stats(self, start=600, step=60):
        now = int(time.time())
        path = self._make_path('cpu')

        if step != 60:
            cf = 'AVERAGE'
            step = 1440
        else:
            cf = 'LAST'
            step = 60

        start_ts = now - (now % step)
        negated = -(start - (start % step))

        rdata = None
        try:
            rdata = rrdtool.fetch(str(path), cf, '-s', str(negated), '-e', str(start_ts), '-r', str(step))
        except:
            return {}

        data = rdata[2]

        step = rdata[0][2]
	begin_ts = rdata[0][0]
        set = []
        for i in data:
            if i[0] is None: continue
            set.append([begin_ts * 1000, i[0] / 10])
            begin_ts += step

        return {'label': 'CPU usage (%)', 'data': set, 'color': "#336633"}

    def get_net_stats(self, start=600, step=60):
        now = int(time.time())
        path = self._make_path('net')

        if step != 60:
            cf = 'AVERAGE'
            step = 1440
        else:
            cf = 'LAST'
            step = 60

        start_ts = now - (now % step)
        negated = -(start - (start % step))

        rdata = None
        try:
            rdata = rrdtool.fetch(str(path), cf, '-s', str(negated), '-e', str(start_ts), '-r', str(step))
        except:
            return {}

	data = rdata[2]
        step = rdata[0][2]

	begin_ts = rdata[0][0]
        set = []
        for i in data:
            if i[0] is None: continue
            set.append([begin_ts * 1000, i[0]])
            begin_ts += step

        rxbytes = {'label': 'Bytes received', 'data': set, 'color': "#336633"}

	begin_ts = rdata[0][0]
        set = []
        for i in data:
            if i[0] is None: continue
            set.append([begin_ts * 1000, i[1]])
            begin_ts += step

        txbytes = {'label': 'Bytes sent', 'data': set, 'color': "#333366"}

        return [rxbytes, txbytes]

    def get_vbd_stats(self, start=600, step=60):
        now = int(time.time())
        path = self._make_path('vbd')

        if step != 60:
            cf = 'AVERAGE'
            step = 1440
        else:
            cf = 'LAST'
            step = 60

        start_ts = now - (now % step)
        negated = -(start - (start % step))

        rdata = None
        try:
            rdata = rrdtool.fetch(str(path), cf, '-s', str(negated), '-e', str(start_ts), '-r', str(step))
        except:
            return {}

	data = rdata[2]
        step = rdata[0][2]

        begin_ts = rdata[0][0]
        set = []
        for i in data:
            if i[0] is None: continue
            set.append([begin_ts * 1000, i[0]])
            begin_ts += step

        rxbytes = {'label': 'Read requests', 'data': set, 'color': "#336633"}

        begin_ts = rdata[0][0]
        set = []
        for i in data:
            if i[0] is None: continue
            set.append([begin_ts * 1000, i[1]])
            begin_ts += step

        txbytes = {'label': 'Write requests', 'data': set, 'color': "#333366"}

        begin_ts = rdata[0][0]
        set = []
        for i in data:
            if i[0] is None: continue
            set.append([begin_ts * 1000, i[2]])
            begin_ts += step

        oobytes = {'label': 'Rescheduled requests', 'data': set, 'color': "#663333"}

        return [rxbytes, txbytes, oobytes]

class ResourcePlan(db.Model):
    __tablename__ = 'vps_resource_plan'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    memory = db.Column(db.Integer)
    disk = db.Column(db.Integer)
    swap = db.Column(db.Integer)
    price = db.Column(db.Float)

    def __init__(self, name, memory, swap, disk, price):
        self.name = name
        self.memory = memory
        self.disk = disk
        self.swap = swap
        self.price = price

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<ResourcePlan: {}>".format(self.name)

    def create_vps(self, user, region, name):
        node = region.available_node(self.memory, self.disk)
        vps = XenVPS(name, self.memory, self.swap, self.disk, self.price, node, user)
        iprs = filter(lambda x: len(x.available_ips()) > 0, node.ipranges)
        if not iprs or len(iprs) == 0:
            return vps
        iprs[0].assign_first_available(user, vps)
        vps.init()
        return vps
