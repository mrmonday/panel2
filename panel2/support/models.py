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
import blinker

ticket_create_signal = blinker.Signal('A signal which is fired when a ticket is created')
ticket_reply_signal = blinker.Signal('A signal which is fired when a reply is added')

class Ticket(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    subject = db.Column(db.String(255), default='(no subject)')
    priority = db.Column(db.Integer)
    department = db.Column(db.String(255))

    is_open = db.Column(db.Boolean, default=True)

    opened_at = db.Column(db.Integer)
    closed_at = db.Column(db.Integer)
    
    user = db.relationship('User', backref='tickets')

    def __init__(self, user, subject, message=None, priority=0, department='Support'):
        self.user = user
        self.user_id = user.id

        self.subject = subject
        self.priority = priority
        self.department = department

        self.is_open = True
        self.opened_at = time.time()

        db.session.add(self)
        db.session.commit()

        if message:
            reply = self.add_reply(self.user, message, False)
            ticket_create_signal.send(app, ticket=self, reply=reply)

    def __repr__(self):
        return "<Ticket: %d - '%s'>" % (self.id, self.subject)

    def add_reply(self, from_user, message, fire_reply_signal=True, reopen=True):
        if reopen:
            self.reopen()

        return Reply(self, from_user, message, fire_reply_signal)

    def reopen(self):
        self.closed_at = None
        self.is_open = True

        db.session.add(self)
        db.session.commit()

    def close(self):
        self.closed_at = time.time()
        self.is_open = False

        db.session.add(self)
        db.session.commit()

    def _serialize(self):
        return dict(ticket=self.id, subject=self.subject, user=self.user.username, priority=self.priority,
                    department=self.department, is_open=self.is_open, opened_at=self.opened_at,
                    closed_at=self.closed_at, replies=[reply._serialize() for reply in self.replies])

def send_message(user, from_user, subject, message, close=False):
    ticket = Ticket(user, subject)
    reply = ticket.add_reply(from_user, message, False)

    if close:
        ticket.close()

    ticket_create_signal.send(app, ticket=ticket, reply=reply)
    return ticket

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'))
    from_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    replied_at = db.Column(db.Integer)
    message = db.Column(db.Text)

    ticket = db.relationship('Ticket', backref='replies')
    from_user = db.relationship('User')

    def __init__(self, ticket, from_user, message, fire_reply_signal=True):
        self.ticket = ticket
        self.ticket_id = ticket.id

        self.from_user = from_user
        self.from_id = from_user.id

        self.message = message

        self.replied_at = time.time()

        db.session.add(self)
        db.session.commit()

        if fire_reply_signal is True:
            ticket_reply_signal.send(app, ticket=self.ticket, reply=self)

    def __repr__(self):
        return "<Reply for Ticket %d, '%s...'>" % (self.ticket.id, self.message[0:50])

    def _serialize(self):
        return dict(ticket=self.ticket_id, user=self.from_user.username, message=self.message,
                    replied_at=self.replied_at)
