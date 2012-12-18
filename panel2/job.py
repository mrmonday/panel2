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
import time

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_ts = db.Column(db.Integer)
    entry_ts = db.Column(db.Integer)
    end_ts = db.Column(db.Integer)
    target_ip = db.Column(db.String(255))
    target_port = db.Column(db.Integer)
    request_envelope = db.Column(db.Text)
    response_envelope = db.Column(db.Text)

    def __init__(self, request_envelope, target_ip, target_port=5959):
        self.request_envelope = request_envelope
        self.target_ip = target_ip
        self.target_port = target_port
        self.entry_ts = int(time.time())

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Job {}>".format(self.id)

    def is_finished(self):
        return self.end_ts is not None

    def is_running(self):
        return self.start_ts is not None and self.is_finished() is False

    def is_failed(self):
        return self.is_finished() is True and self.response_envelope is None

    def is_success(self):
        return self.is_finished() is True and self.response_envelope is not None

    def checkout(self):
        self.start_ts = int(time.time())
        db.session.add(self)
        db.session.commit()

    def checkin(self, response_envelope=None):
        self.end_ts = int(time.time())
        self.response_envelope = response_envelope
        db.session.add(self)
        db.session.commit()

from ediarpc import rpc_message, rpc_client

class QueueingProxy(rpc_client.ServerProxy):
    def _call(self, name, **kwargs):
        envelope = rpc_message.encode(self._secret, name, iterations=self._iterations, **kwargs) + '\r\n'
        return Job(envelope, self._host, self._port)

    def __del__(self):
        pass

