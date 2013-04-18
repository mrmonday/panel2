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

import rrdtool, os, time
from panel2 import app, db, cron
from panel2.vps.models import Node, XenVPS
from panel2.cron import MONITORING
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

    def run(self, check):
        print '{0}: check failed, rebooting {1}'.format(self.probe.nickname, self.probe.vps.name)
        check.vps.destroy()
        check.vps.create()

class DebugTrigger(MonitorTrigger):
    __mapper_args__ = {'polymorphic_identity': 'debug'}

    def __init__(self, probe):
        self.type = 'reboot'
        self.active = True

        self.probe_id = probe.id
        self.probe = probe

        db.session.add(self)
        db.session.commit()

    def run(self, check):
        print '{0}: check failed'.format(self.probe.nickname)

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

    def describe(self):
        return 'There is no description for probe type: {1}'.format(self.type)

    def check(self):
        print '{0}: check for probe type {1} is unimplemented'.format(self.nickname, self.type)
        return True

    def verify(self):
        result = self.check()

        if not result and not self.failed:
            [trigger.run(self) for trigger in self.triggers]
            self.failed = True
        elif result:
            self.failed = False

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

    def check(self):
        if not self.failed:
            return False

        return True

@cron.task(MONITORING)
def monitor_task():
    print 'running monitoring probes'
    for probe in MonitorProbe.query.filter_by(active=True):
        probe.verify()
