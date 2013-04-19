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

import rrdtool, os, time, subprocess, socket, requests, json
from flask import render_template
from panel2 import app, db, cron
from panel2.vps.models import Node, XenVPS
from panel2.cron import MONITORING
from panel2.utils import send_simple_email
from ediarpc.rpc_client import ServerProxy

class MonitorTrigger(db.Model):
    __tablename__ = 'monitortriggers'

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(255))
    type = db.Column(db.String(50))
    active = db.Column(db.Boolean)

    probe_id = db.Column(db.Integer, db.ForeignKey('monitorprobes.id'))
    probe = db.relationship('MonitorProbe', backref='triggers')

    __mapper_args__ = {'polymorphic_on': type}

    def __repr__(self):
        return '<MonitorTrigger: {0} {1}>'.format(self.type, repr(self.probe))

    def describe(self):
        return 'Do nothing'

    def run(self, check):
        print '{0}: trigger for probe type {1} is unimplemented'.format(self.nickname, self.type)

class RebootServiceTrigger(MonitorTrigger):
    __mapper_args__ = {'polymorphic_identity': 'reboot'}

    def __init__(self, probe):
        self.type = 'reboot'
        self.active = True

        self.probe_id = probe.id
        self.probe = probe

        db.session.add(self)
        db.session.commit()

    def describe(self):
        return 'Reboot the VPS on failure'

    def run(self, check):
        if not check.failed:
            return
        print '{0}: check failed, rebooting {1}'.format(self.probe.nickname, self.probe.vps.name)
        check.vps.destroy()
        check.vps.create()

class DebugTrigger(MonitorTrigger):
    __mapper_args__ = {'polymorphic_identity': 'debug'}

    def __init__(self, probe):
        self.type = 'debug'
        self.active = True

        self.probe_id = probe.id
        self.probe = probe

        db.session.add(self)
        db.session.commit()

    def describe(self):
        return 'Log a debug message'

    def run(self, check):
        print '{0}: check {1}'.format(self.probe.nickname, 'failed' if check.failed else 'recovered')

class EMailTrigger(MonitorTrigger):
    __tablename__ = 'monitor_emailtrigger'
    __mapper_args__ = {'polymorphic_identity': 'email'}

    id = db.Column(db.Integer, primary_key=True)
    trigger_id = db.Column(db.Integer, db.ForeignKey('monitortriggers.id'))

    email = db.Column(db.String(255))

    def __init__(self, probe, email=None):
        self.type = 'email'
        self.active = True

        self.probe_id = probe.id
        self.probe = probe

        if not email:
            self.email = probe.vps.user.email
        else:
            self.email = email

        db.session.add(self)
        db.session.commit()

    def describe(self):
        return 'Send an e-mail to {}'.format(self.email)

    def run(self, check):
        subject = None
        message = None

        if check.failed:
            subject = '*** FAILED: {0} on {1} ***'.format(self.probe.nickname, self.probe.vps.name)
            message = render_template('vps/email/monitoring-failed.txt', user=self.probe.vps.user, service=self.probe.vps, check=self.probe)
        else:
            subject = '*** RECOVERY: {0} on {1} ***'.format(self.probe.nickname, self.probe.vps.name)
            message = render_template('vps/email/monitoring-recovered.txt', user=self.probe.vps.user, service=self.probe.vps, check=self.probe)

        send_simple_email(recipient=self.email, subject=subject, message=message)

class WebHookTrigger(MonitorTrigger):
    __tablename__ = 'monitor_webhooktrigger'
    __mapper_args__ = {'polymorphic_identity': 'webhook'}

    id = db.Column(db.Integer, primary_key=True)
    trigger_id = db.Column(db.Integer, db.ForeignKey('monitortriggers.id'))

    uri = db.Column(db.String(255))

    def __init__(self, probe, uri):
        self.type = 'webhook'
        self.active = True

        self.probe_id = probe.id
        self.probe = probe

        self.uri = uri

        db.session.add(self)
        db.session.commit()

    def describe(self):
        return 'Post a JSON structure to {} describing the event'.format(self.uri)

    def run(self, check):
        payload = {
            'name': self.probe.nickname,
            'status': 'ok' if not self.failed else 'down',
            'time': time.time() * 1000,
            'resource': self.probe.resource_dict(),
            'description': self.probe.describe(),
        }
        message = json.dumps(payload)
        try:
            requests.post(self.uri, message, timeout=2.0)
        except:
            pass

class MonitorProbe(db.Model):
    __tablename__ = 'monitorprobes'

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(255))
    type = db.Column(db.String(50))
    active = db.Column(db.Boolean)
    failed = db.Column(db.Boolean)

    vps_id = db.Column(db.Integer, db.ForeignKey('xenvps.vps_id'))
    vps = db.relationship('XenVPS', backref='probes')

    __mapper_args__ = {'polymorphic_on': type}

    def __repr__(self):
        return '<MonitorProbe: {0} [{1}]>'.format(self.type, self.vps.name)

    def set_active(self, active):
        self.active = active

        db.session.add(self)
        db.session.commit()

    def resource_dict(self):
        return dict(type=self.type)

    def describe(self):
        return 'Do nothing'

    def check(self):
        print '{0}: check for probe type {1} is unimplemented'.format(self.nickname, self.type)
        return True

    def verify(self):
        result = self.check()

        if not result and not self.failed:
            self.failed = True
            [trigger.run(self) for trigger in self.triggers]
        elif result and self.failed:
            self.failed = False
            [trigger.run(self) for trigger in self.triggers]

        db.session.add(self)
        db.session.commit()

        return result

class DebugProbe(MonitorProbe):
    __mapper_args__ = {'polymorphic_identity': 'debug'}

    def __init__(self, nickname, vps):
        self.nickname = nickname
        self.type = 'debug'
        self.active = True

        self.vps_id = vps.vps_id
        self.vps = vps

        db.session.add(self)
        db.session.commit()

    def describe(self):
        return 'Negate the status of the last check'

    def check(self):
        if not self.failed:
            return False

        return True

class PingProbe(MonitorProbe):
    __tablename__ = 'monitor_pingprobe'
    __mapper_args__ = {'polymorphic_identity': 'ping'}

    id = db.Column(db.Integer, primary_key=True)
    probe_id = db.Column(db.Integer, db.ForeignKey('monitorprobes.id'))

    ip = db.Column(db.String(255))

    def __init__(self, nickname, vps, ip):
        self.nickname = nickname
        self.type = 'ping'
        self.active = True

        self.vps_id = vps.vps_id
        self.vps = vps

        self.ip = ip

        db.session.add(self)
        db.session.commit()

    def resource_dict(self):
        return dict(type=self.type, ip=self.ip)

    def describe(self):
        return 'Send an ICMP ping to {} and wait 2 seconds for a response'.format(self.ip)

    def check(self):
        return subprocess.call(['ping', '-c', '1', '-W', '2', self.ip]) == 0

class TCPConnectProbe(MonitorProbe):
    __tablename__ = 'monitor_tcpprobe'
    __mapper_args__ = {'polymorphic_identity': 'tcp'}

    id = db.Column(db.Integer, primary_key=True)
    probe_id = db.Column(db.Integer, db.ForeignKey('monitorprobes.id'))

    ip = db.Column(db.String(255))
    port = db.Column(db.Integer)
    banner = db.Column(db.String(255))

    def __repr__(self):
        return '<MonitorProbe: {0} ({1}/{2}) [{3}]>'.format(self.type, self.ip, self.port, self.vps.name)

    def __init__(self, nickname, vps, ip, port, banner=None):
        self.nickname = nickname
        self.type = 'tcp'
        self.active = True

        self.vps_id = vps.vps_id
        self.vps = vps

        self.ip = ip
        self.port = port
        self.banner = banner

        db.session.add(self)
        db.session.commit()

    def resource_dict(self):
        return dict(type=self.type, ip=self.ip, port=self.port, banner=self.banner)

    def describe(self):
        if self.banner:
            return 'Connect to {0} port {1} and look for {2} in the returned data'.format(self.ip, self.port, self.banner)

        return 'Connect to {0} port {1}'.format(self.ip, self.port)

    def check(self):
        try:
            sock = socket.create_connection((str(self.ip), int(self.port)), timeout=2.0)
            if not self.banner:
                return True
            sock.settimeout(2.0)
            sock.send('\r\n')
            data = sock.recv(2048)
            if self.banner in data:
                return True
        except:
            pass

        return False

class HTTPProbe(MonitorProbe):
    __tablename__ = 'monitor_httpprobe'
    __mapper_args__ = {'polymorphic_identity': 'http'}

    id = db.Column(db.Integer, primary_key=True)
    probe_id = db.Column(db.Integer, db.ForeignKey('monitorprobes.id'))

    uri = db.Column(db.String(255))
    banner = db.Column(db.String(255))

    def __repr__(self):
        return '<MonitorProbe: {0} ({1}) [{2}]>'.format(self.type, self.uri, self.vps.name)

    def __init__(self, nickname, vps, uri, banner=None):
        self.nickname = nickname
        self.type = 'http'
        self.active = True

        self.vps_id = vps.vps_id
        self.vps = vps

        self.uri = uri
        self.banner = banner

        db.session.add(self)
        db.session.commit()

    def resource_dict(self):
        return dict(type=self.type, uri=self.uri, banner=self.banner)

    def describe(self):
        if self.banner:
            return 'Fetch {0} and look for {1} in the returned data'.format(self.uri, self.banner)

        return 'Fetch {0}'.format(self.uri)

    def check(self):
        try:
            r = requests.get(self.uri, timeout=2.0)
            if not self.banner:
                return True
            if self.banner in r.text:
                return True
        except:
            pass

        return False

@cron.task(MONITORING)
def monitor_task():
    ctx = app.test_request_context()
    ctx.push()

    print 'running monitoring probes'
    for probe in MonitorProbe.query.filter_by(active=True):
        probe.verify()

    ctx.pop()
