#!/usr/bin/env python
"""
Copyright (c) 2012, 2013, 2014 Centarra Networks, Inc.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice, this permission notice and all necessary source code
to recompile the software are included or otherwise available in all
distributions.

This software is provided 'as is' and without any warranty, express or
implied.  In no event shall the authors be liable for any damages arising
from the use of this software.
"""

from panel2 import app, db, cron
from panel2.cron import DAILY, HOURLY
from panel2.invoice import InvoiceItem, ServiceCreditItem, invoice_item_paid_signal

from sqlalchemy import func

import math
import ipaddress
import time
import random

class Service(db.Model):
    __tablename__ = 'services'

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(255))
    type = db.Column(db.String(50))
    created = db.Column(db.Integer)
    expiry = db.Column(db.Integer)
    price = db.Column(db.Float)
    is_entitled = db.Column(db.Boolean, default=False)
    disable_renew = db.Column(db.Boolean, default=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User', backref='services')

    __mapper_args__ = {'polymorphic_on': type}

    def delete(self, do_refund=True):
        if do_refund:
            refund_amt = self.refund_amount()
            if refund_amt > 0:
                ServiceCreditItem(self.user, refund_amt, 'Deletion - {}'.format(self.name))

        for a in InvoiceItem.query.filter_by(service_id=self.id).all():
            if a.invoice.payment_ts is None:  # if the invoice has not been paid
                a.invoice.delete()
            else:  # if the invoice *has* been paid, we should keep it around.
                a.service = None
                a.service_id = None

        db.session.commit()

        for ip in self.ips:
            ip.service_id = None
            ip.service = None

            ip.user_id = None
            ip.user = None

            db.session.add(ip)

        db.session.delete(self)
        db.session.commit()

    def create(self):
        pass

    def suspend(self, disable_renew=False, template='email/service-suspended.txt'):
        self.is_entitled = False
        self.disable_renew = disable_renew

        delete_ts = self.expiry + (86400 * 7)
        self.user.send_email('SUSPENSION: {}'.format(self.name), template, service=self, delete_ts=delete_ts)

        db.session.add(self)
        db.session.commit()

    def invoice(self, invoice):
        if self.disable_renew:
            return None

        return InvoiceItem(self, invoice, self.price)

    def attach_ip(self, ip, ipnet=None):
        return IPAddressRef(ip, ipnet, self.user, self)

    def entitle(self):
        if not self.is_entitled:
            self.user.send_email('ACTIVATION: {}'.format(self.name), 'email/service-activated.txt', service=self)

        self.is_entitled = True
        self.disable_renew = False

        db.session.add(self)
        db.session.commit()

    # XXX: update this when yearly is added --nenolod
    def update_expiry(self):
        if self.disable_renew:
            return

        current_expiry = list(time.gmtime(self.expiry))
        current_expiry[1] += 1
        self.expiry = time.mktime(tuple(current_expiry))
        self.entitle()

    def last_renewed(self):
        current_expiry = list(time.gmtime(self.expiry))
        current_expiry[1] -= 1
        return time.mktime(tuple(current_expiry))

    def reservation_length(self, unit=1):
        return (self.expiry - self.last_renewed()) / unit

    def reservation_remaining(self, unit=1):
        return (self.expiry - time.time()) / unit

    def hourly_rate(self):
        return round(self.price / (self.reservation_length(unit=3600)), 4)

    def refund_amount(self):
        if not self.expiry:
            return 0
        if not self.is_entitled:
            return 0
        if self.expiry < time.time():
            return 0
        return round(self.hourly_rate() * (math.floor(self.reservation_remaining(unit=3600))), 2)

@invoice_item_paid_signal.connect_via(app)
def service_update_expiry(*args, **kwargs):
    service = kwargs.get('service', None)
    if service:
        service.update_expiry()

@cron.task(DAILY)
def expiry_nag():
    ctx = app.test_request_context()
    ctx.push()

    delinquent = Service.query.filter(Service.expiry < time.time())

    for svc in delinquent:
        print "{} has expired".format(svc.name)
        expiry_ts = svc.expiry + (86400 * 3)
        delete_ts = svc.expiry + (86400 * 7)
        svc.user.send_email('URGENT: Service {} has expired'.format(svc.name), 'email/service-expired.txt', service=svc, expiry_ts=expiry_ts, delete_ts=delete_ts)

    ctx.pop()

@cron.task(DAILY)
def expiry_suspend():
    ctx = app.test_request_context()
    ctx.push()
    ts = time.time()

    delinquent = Service.query.filter_by(is_entitled=True).filter(Service.expiry < time.time())

    for svc in delinquent:
        expiry_ts = svc.expiry + (86400 * 3)
        if expiry_ts < ts:
            svc.suspend()

    ctx.pop()

@cron.task(DAILY)
def expiry_autodelete():
    ctx = app.test_request_context()
    ctx.push()
    ts = time.time()

    delinquent = Service.query.filter_by(is_entitled=False).filter(Service.expiry < time.time())

    for svc in delinquent:
        delete_ts = svc.expiry + (86400 * 7)
        if delete_ts < ts:
            svc.delete()

    ctx.pop()

@cron.task(HOURLY)
def expire_reservations():
    deadline = int(time.time() - (3600 * 3))
    delinquent = Service.query.filter_by(is_entitled=False).filter_by(expiry=None).filter(Service.created < deadline)
    [svs.delete() for svs in delinquent]

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

    reserved = db.Column(db.Boolean, default=False)

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

    def update_ipnet(self, ipnet):
        if self.ipnet == ipnet:
            return

        if ipnet:
            self.ipnet_id = ipnet.id
            self.ipnet = ipnet
        else:
            self.ipnet_id = None
            self.ipnet = None

        db.session.add(self)
        db.session.commit()

    def update_service(self, service):
        if self.service == service:
            return

        if service:
            self.service_id = service.id
            self.service = service
        else:
            self.service_id = None
            self.service = None

        db.session.add(self)
        db.session.commit()

    def update_user(self, user):
        if self.user == user:
            return

        if user:
            self.user_id = user.id
            self.user = user
        else:
            self.user_id = None
            self.user = None

        db.session.add(self)
        db.session.commit()

    def ptr_name(self, ipv4_dns_base=None):
        if self.ipnet.is_ipv6():
            ip = ipaddress.IPv6Address(self.ip)
            nibbles = list(("%32x" % ip._ip))
            nibbles.reverse()
            return '{}.ip6.arpa'.format('.'.join(nibbles))

        ip = ipaddress.IPv4Address(self.ip)
        ip_int = int(ip._ip)

        octets = []
        for octet in xrange(4):
            octets.insert(0, str(ip_int & 0xFF))
            ip_int >>= 8
        octets.reverse()

        if not ipv4_dns_base:
            return '{}.in-addr.arpa'.format('.'.join(octets))

        return '{0}.{1}'.format(octets[0], ipv4_dns_base)

    def update_rdns(self, rdns):
        from panel2.dns.models import Record

        if not self.ipnet.rdns_zone:
            return False

        dom = self.ipnet.rdns_zone
        recname = self.ptr_name(ipv4_dns_base=dom.name)

        rec = Record.query.filter_by(domain_id=dom.id).filter_by(name=recname).first()
        if not rec:
            dom.add_record(recname, rdns, 'PTR', ttl=43200)
            return True

        rec.update_content(rdns)
        return True

    def lookup_rdns(self):
        from panel2.dns.models import Record

        if not self.ipnet.rdns_zone:
            return None

        dom = self.ipnet.rdns_zone
        recname = self.ptr_name(ipv4_dns_base=dom.name)

        rec = Record.query.filter_by(domain_id=dom.id).filter_by(name=recname).first()
        if not rec:
            return None

        return rec.content

    def _serialize(self):
        return dict(id=self.id, ip=self.ip, ipnet=self.ipnet._serialize())

def IPAddressRef(ip, ipnet=None, user=None, service=None):
    '''A wrapper around the IPAddress constructor which handles lookup as well as
       creation of IP address records.'''
    ip_obj = IPAddress.query.filter_by(ip=ip).first()
    if ip_obj is not None:
        if ipnet is not None:
            ip_obj.update_ipnet(ipnet)
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

    rdns_zone_id = db.Column(db.Integer, db.ForeignKey('domains.id'))
    rdns_zone = db.relationship('Domain')

    __mapper_args__ = {'polymorphic_on': type}

    def __repr__(self):
        return "<IPRange: {}>".format(self.network)

    def delete(self):
        db.session.delete(self)
        db.session.commit()

    def ipnet(self):
        return ipaddress.ip_network(self.network)

    def is_ipv6(self):
        return self.ipnet().version == 6

    def gateway(self):
        return str(self.ipnet().network_address + 1)

    def broadcast(self):
        return str(self.ipnet().broadcast_address)

    def usable_size(self):
        if self.ipnet().version == 6:
            return 2**16
        gateway = int(self.ipnet().network_address) + 1
        broadcast = int(self.ipnet().broadcast_address) - 1
        return broadcast - gateway

    def count_free_ips(self):
        if self.ipnet().version == 6:
            return 32
        used_ips = db.session.query(func.count(IPAddress.id)).filter_by(ipnet_id=self.id).filter(IPAddress.service_id).first()[0]
        reserved_ips = db.session.query(func.count(IPAddress.id)).filter_by(ipnet_id=self.id).filter_by(reserved=True).first()[0]
        return self.usable_size() - used_ips - reserved_ips

    def rdns_zone_name(self):
        network_addr = self.ipnet().network_address
        network_addr_int = int(network_addr._ip)

        octets = []
        for octet in xrange(4):
            octets.insert(0, str(network_addr_int & 0xFF))
            network_addr_int >>= 8
        octets.reverse()

        return '{0}.in-addr.arpa'.format('.'.join(octets[1:4]))

    def rdns_discover(self):
        from panel2.dns.models import Domain

        zone = self.rdns_zone_name()
        dom = Domain.query.filter_by(name=zone).first()
        if not dom:
            return

        self.rdns_zone_id = dom.id
        db.session.add(self)
        db.session.commit()

    def available_ips(self):
        iplist = []
        if self.ipnet().version == 4:
            for host in self.ipnet().iterhosts():
                if str(host) == self.gateway():
                   continue
                ip_obj = IPAddress.query.filter_by(ip=str(host)).first()
                if ip_obj is None:
                    iplist.append(str(host))
                elif ip_obj.service is None and not ip_obj.reserved:
                    iplist.append(str(host))
        else:
            for i in xrange(32):
                host = ipaddress.IPv6Address(str(self.ipnet().network_address)) + int(random.getrandbits(32))
                if str(host) == self.gateway():
                    continue
                ip_obj = IPAddress.query.filter_by(ip=str(host)).first()
                if ip_obj is None:
                    iplist.append(str(host))
                elif ip_obj.service is None and not ip_obj.reserved:
                    iplist.append(str(host))
        return iplist

    def assign_first_available(self, user=None, service=None):
        iplist = self.available_ips()
        if len(iplist) < 1:
            return None
        return IPAddressRef(iplist[0], self, user, service)
 
    def _serialize(self):
        return dict(network=self.network, version=self.ipnet().version,
                    gateway=self.gateway(), broadcast=self.broadcast(),
                    netmask=str(self.ipnet().netmask))

class ServiceIPRange(IPRange):
    __mapper_args__ = {'polymorphic_identity': 'service'}
    service_id = db.Column(db.Integer, db.ForeignKey('services.id'))
    service = db.relationship('Service', backref='ipranges')

    def __init__(self, network, service):
        self.service = service
        self.service_id = service.id
        self.network = network

        db.session.add(self)
        db.session.commit()

        self.associate_child_ips()
        self.rdns_discover()

    def associate_child_ips(self):
        if not self.is_ipv6():
            for ip in self.available_ips():
                IPAddressRef(ip, self, self.service.user, self.service)

    def disassociate_child_ips(self):
        for ip in self.assigned_ips:
            ip.update_ipnet(None)
            ip.update_user(None)
            ip.update_service(None)

    def delete(self):
        self.disassociate_child_ips()
        IPRange.delete(self)
