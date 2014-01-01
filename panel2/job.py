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

from panel2 import app, db, cron
from panel2.cron import MINUTELY

import time
import blinker

job_checkin_signal = blinker.Signal('A signal which is fired when a job is checked in with a result')
job_checkout_signal = blinker.Signal('A signal which is fired when a job is checked out')

class Job(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    refid = db.Column(db.Integer)
    start_ts = db.Column(db.Integer)
    entry_ts = db.Column(db.Integer)
    end_ts = db.Column(db.Integer)
    target_ip = db.Column(db.String(255))
    target_port = db.Column(db.Integer)
    request_envelope = db.Column(db.Text)
    response_envelope = db.Column(db.Text)

    def __init__(self, request_envelope, target_ip, target_port=5959, refid=None):
        self.request_envelope = request_envelope
        self.target_ip = target_ip
        self.target_port = target_port
        self.entry_ts = int(time.time())
        self.refid = refid

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

        job_checkout_signal.send(app, job=self)

    def backout(self):
        self.start_ts = None
        self.end_ts = None
        self.response_envelope = None
        db.session.add(self)
        db.session.commit()

    def checkin(self, response_envelope=None):
        self.end_ts = int(time.time())
        self.response_envelope = response_envelope
        db.session.add(self)
        db.session.commit()

        job_checkin_signal.send(app, job=self)

from ediarpc import rpc_message, rpc_client

class QueueingProxy(rpc_client.ServerProxy):
    def __init__(self, *args, **kwargs):
        self._refid = kwargs.pop('refid', None)
        super(QueueingProxy, self).__init__(*args, **kwargs)

    def _call(self, name, **kwargs):
        envelope = rpc_message.encode(self._secret, name, iterations=self._iterations, **kwargs) + '\r\n'
        return Job(envelope, self._host, self._port, self._refid)

    def __del__(self):
        pass

class DeferredJob(db.Model):
    """
    A deferred job is a job which will be queued to execute a specified length of time after a parent job
    is completed.

    This can be used to implement complex logic such as "reset the boot device on my server after starting
    an installation process."
    """
    id = db.Column(db.Integer, primary_key=True)

    parent_job_id = db.Column(db.Integer, db.ForeignKey('job.id'))
    parent_job = db.relationship('Job')

    refid = db.Column(db.Integer)
    target_ip = db.Column(db.String(255))
    target_port = db.Column(db.Integer)
    request_envelope = db.Column(db.Text)

    deadline = db.Column(db.Integer)

    def __init__(self, parent_job, request_envelope, target_ip, target_port=5959, refid=None, deadline=300):
        self.parent_job_id = parent_job.id
        self.request_envelope = request_envelope
        self.target_ip = target_ip
        self.target_port = target_port
        self.refid = refid
        self.deadline = deadline

        db.session.add(self)
        db.session.commit()

    def deadline_met(self):
        """
        Determine whether or not a deferred task's deadline has yet been met.  The criteria for this is:

        1. The parent job must be in 'completed' state.
        2. The parent job end_ts + our deadline length must have come before the current timestamp.
        """
        if not self.parent_job or not self.parent_job.end_ts:
            return False
        return (self.parent_job.end_ts + self.deadline) < int(time.time())

    def enqueue(self):
        """
        Move the task to the real job queue for execution.

        Side effect: the DeferredJob object is dropped from the database.
        """
        j = Job(self.request_envelope, self.target_ip, self.target_port, self.refid)
        db.session.delete(self)
        db.session.commit()
        return j

    def maybe_enqueue(self):
        """
        If the job's deadline conditions are met, move the task to the real job queue for execution.
        This basically ties DeferredJob.deadline_met() and DeferredJob.enqueue() together nicely.

        Side effect: If the job is moved, then this object will become invalidated and should not be
        used anymore.
        """
        if not self.deadline_met():
            return None
        return self.enqueue()

class InvalidParentJobException(Exception):
    pass

class DeferredQueueingProxy(rpc_client.ServerProxy):
    def __init__(self, *args, **kwargs):
        self._refid = kwargs.pop('refid', None)
        self._deadline = kwargs.pop('deadline', 300)
        self._parent = kwargs.pop('parent', None)
        if not self._parent:
            raise InvalidParentJobException()
        super(DeferredQueueingProxy, self).__init__(*args, **kwargs)

    def _call(self, name, **kwargs):
        envelope = rpc_message.encode(self._secret, name, iterations=self._iterations, **kwargs) + '\r\n'
        return DeferredJob(envelope, self._parent, self._host, self._port, self._refid, self._deadline)

    def __del__(self):
        pass

@cron.task(MINUTELY)
def schedule_deferred_jobs():
    """
    Schedule any deferred jobs that we can.

    To do this, we simply iterate over the deferred job table, and enqueue the ones we can.  We operate on a copy
    of the results to ensure that our iteration is safe.
    """
    deferred_list = DeferredJob.query.all()
    [deferred_job.maybe_enqueue() for deferred_job in deferred_list]
