#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from panel2 import app, db

import time

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

    def __init__(self, user, subject, message, priority=0, department='Support'):
        self.user = user
        self.user_id = user.id

        self.subject = subject
        self.priority = priority
        self.department = department

        self.is_open = True
        self.opened_at = time.time()

        db.session.add(self)
        db.session.commit()

        self.add_reply(self.user, message)

    def __repr__(self):
        return "<Ticket: %d - '%s'>" % (self.id, self.subject)

    def add_reply(self, from_user, message):
        return Reply(self, from_user, message)

    def close(self):
        self.closed_at = time.time()
        self.is_open = False

        db.session.add(self)
        db.session.commit()

class Reply(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticket_id = db.Column(db.Integer, db.ForeignKey('ticket.id'))
    from_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    replied_at = db.Column(db.Integer)
    message = db.Column(db.Text)

    ticket = db.relationship('Ticket', backref='replies')
    from_user = db.relationship('User')

    def __init__(self, ticket, from_user, message):
        self.ticket = ticket
        self.ticket_id = ticket.id

        self.from_user = from_user
        self.from_id = from_user.id

        self.message = message

        self.replied_at = time.time()

        db.session.add(self)
        db.session.commit()

    def __repr__(self):
        return "<Reply for Ticket %d, '%s...'>" % (self.ticket.id, self.message[0:50])
