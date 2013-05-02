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
import hashlib

from panel2 import app, db
from panel2.service import Service, IPRange
from panel2.invoice import ExchangeRate
from panel2.job import QueueingProxy, Job
from ediarpc.rpc_client import ServerProxy

from collections import OrderedDict

class HVMISOImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    file = db.Column(db.String(255))

    def __init__(self, name, file):
        self.name = name
        self.file = file

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<HVMISOImage: '{0}' ['{1}']>".format(self.name, self.file)

class KernelProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))

    def __init__(self, name):
        self.name = name

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<KernelProfile: '%s'>" % self.name

    def render_config(self, domain):
        keys = {
            'domname': domain.name,
            'domid': domain.id,
            'eth0_ip': domain.ips[0].ip,
            'eth0_gateway': domain.ips[0].ipnet.gateway(),
            'eth0_netmask': domain.ips[0].ipnet.ipnet().netmask,
            'eth0_broadcast': domain.ips[0].ipnet.broadcast(),
        }
        return {s.key: s.value.format(**keys) for s in self.arguments}

class KernelProfileArgument(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    key = db.Column(db.String(255))
    value = db.Column(db.String(255))

    profile_id = db.Column(db.Integer, db.ForeignKey('kernel_profile.id'))
    profile = db.relationship('KernelProfile', backref='arguments')

    def __init__(self, profile, key, value):
        self.key = key
        self.value = value

        self.profile_id = profile.id
        self.profile = profile

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<KernelProfileArgument: '%s'='%s' ('%s')>" % (self.key, self.value, self.profile.name)

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
        return filter(lambda node: node.allocatable(memory, disk, 1) and node.locked == False, self.nodes)[0]

class Node(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    ipaddr = db.Column(db.String(255))
    secret = db.Column(db.String(255))
    locked = db.Column(db.Boolean, default=False)
    memorycap = db.Column(db.Integer)
    diskcap = db.Column(db.Integer)

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

    def available_ips(self, ipv4_only=False):
        if ipv4_only:
            return [ip for iprange in filter(lambda x: x.is_ipv6() == False, self.ipranges) for ip in iprange.available_ips()]

        return [ip for iprange in self.ipranges for ip in iprange.available_ips()]

    def disk_allocated(self):
        return sum([(x.swap / 1024) for x in self.vps]) + sum([x.disk for x in self.vps])

    def memory_allocated(self):
        return sum([x.memory for x in self.vps])

    def allocatable(self, memory, disk, ips):
        memory_free = self.memorycap - self.memory_allocated()
        disk_free = self.diskcap - self.disk_allocated()
        ips_free = len(self.available_ips(ipv4_only=True))

        return (memory <= memory_free and disk <= disk_free and ips <= ips_free)

    def gen_keypair(self):
        api = self.api(ServerProxy)
        res = api.tmp_keypair_gen()
        data = res['pubkey'].split(' ')[0:2]
        return ' '.join(data)

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

    profile_id = db.Column(db.Integer, db.ForeignKey('kernel_profile.id'))
    profile = db.relationship('KernelProfile')

    watchdog = db.Column(db.Boolean)

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

        self.profile = KernelProfile.query.first()
        self.profile_id = self.profile.id

        self.watchdog = False

        db.session.add(self)
        db.session.commit()

    def _serialize(self):
        return dict(id=self.id, name=self.name, memory=self.memory, swap=self.swap, disk=self.disk, node=self.node.name,
                    user=self.user.username, ips=[ip._serialize() for ip in self.ips])

    def set_profile(self, profile):
        self.profile_id = profile.id
        self.profile = profile

        db.session.add(self)
        db.session.commit()

    def api(self, constructor=QueueingProxy):
        return self.node.api(constructor, self.id)

    def console_key(self):
        payload = '{0}:{1}'.format(self.name, self.node.secret)
        return hashlib.sha512(payload).hexdigest()

    def suspend(self):
        self.destroy()
        Service.suspend(self)

    def jobs(self):
        return Job.query.filter_by(refid=self.id)

    def delete(self):
        self.api().vps_destroy(domname=self.name)
        Service.delete(self)

    def create(self, profile=None):
        if not profile:
            profile = self.profile
        bootargs = profile.render_config(self)
        return self.api().create(domname=self.name, memory=self.memory, ips=[ipaddr.ip for ipaddr in self.ips], **bootargs)

    def format(self):
        return self.api().vps_format(domname=self.name)

    def init(self):
        return self.api().vps_create(domname=self.name, size=self.disk, swap=self.swap, is_hvm=False)

    def image(self, template, arch='x86_64'):
        eth0 = {
           'address': self.ips[0].ip,
           'netmask': str(self.ips[0].ipnet.ipnet().netmask),
           'broadcast': str(self.ips[0].ipnet.broadcast()),
           'gateway': str(self.ips[0].ipnet.gateway()),
        }
        return self.api().vps_image(domname=self.name, eth0=eth0, image=template, arch=arch)

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

    def reimage(self, template, password, create=False, arch='x86_64'):
        self.destroy()
        self.format()
        self.image(template, arch=arch)
        self.rootpass(password)
        if create:
            self.create()

    def clone(self, template, targetip, create=False):
        eth0 = {
           'address': self.ips[0].ip,
           'netmask': str(self.ips[0].ipnet.ipnet().netmask),
           'broadcast': str(self.ips[0].ipnet.broadcast()),
           'gateway': str(self.ips[0].ipnet.gateway()),
        }
        self.destroy()
        self.format()
        self.api().vps_clone(domname=self.name, eth0=eth0, image=template, targetip=targetip)
        if create:
            self.create()

    def __repr__(self):
        return "<XenVPS: '%s' on '%s'>" % (self.name, self.node.name)

    def _make_path(self, type):
        return app.config['RRDPATH'] + '/' + self.node.name + '-' + self.name + '-' + type + '.rrd'

    def get_cpu_stats(self, start=600, step=60):
        now = int(time.time())
        path = self._make_path('cpu')

        if step >= 1440:
            cf = 'AVERAGE'
            step = 1440
        else:
            cf = 'LAST'

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

        if step >= 1440:
            cf = 'AVERAGE'
            step = 1440
        else:
            cf = 'LAST'

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

        if step >= 1440:
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

    def bitcoin_cost(self):
        btc = ExchangeRate.query.filter_by(currency_name='BTC').first()
        return btc.convert_to(self.price)

    def create_vps(self, user, region, name):
        node = region.available_node(self.memory, self.disk)
        vps = XenVPS(name, self.memory, self.swap, self.disk, self.price, node, user)
        ipv4_rs = filter(lambda x: len(x.available_ips()) > 0 and x.is_ipv6() == False, node.ipranges)
        if not ipv4_rs or len(ipv4_rs) == 0:
            return vps
        ipv4_rs[0].assign_first_available(user, vps)
        vps.init()
        ipv6_rs = filter(lambda x: len(x.available_ips()) > 0 and x.is_ipv6() == True, node.ipranges)
        if not ipv6_rs or len(ipv6_rs) == 0:
            return vps
        ipv6_rs[0].assign_first_available(user, vps)
        return vps
