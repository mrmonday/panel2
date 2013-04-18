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
    __tablename__ = 'monitorprobes'

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(255))
    type = db.Column(db.String(50))
    active = db.Column(db.Boolean)

    probe_id = db.Column(db.Integer, db.ForeignKey('monitorprobes.id'))
    probe = db.relationship('MonitorProbe', backref='triggers')

    __mapper_args__ = {'polymorphic_on': type}

    def run(self, check):
        print '{0}: trigger for probe type {1} is unimplemented'.format(self.nickname, self.type)

class MonitorProbe(db.Model):
    __tablename__ = 'monitorprobes'

    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(255))
    type = db.Column(db.String(50))
    active = db.Column(db.Boolean)

    vps_id = db.Column(db.Integer, db.ForeignKey('xenvps.id'))
    vps = db.relationship('XenVPS', backref='probes')

    __mapper_args__ = {'polymorphic_on': type}

    def check(self):
        print '{0}: check for probe type {1} is unimplemented'.format(self.nickname, self.type)
        return True

    def verify(self):
        result = self.check()
        if not result:
            [trigger.run(self) for trigger in self.triggers]
        return result

@cron.task(MONITORING)
def monitor_task():
    print 'running monitoring probes'
    for probe in MonitorProbe.query.filter_by(active=True):
        probe.verify()
