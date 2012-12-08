#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from flask import render_template

from panel2 import app, db
from panel2.models import User
from panel2.support.models import Ticket, Reply, ticket_create_signal, ticket_reply_signal

@ticket_create_signal.connect_via(app)
def send_ticket_create_message(*args, **kwargs):
    ticket = kwargs.pop('ticket', None)
    reply = kwargs.pop('reply', None)

    subject = "[#%d] %s" % (ticket.id, ticket.subject)

    # First send a message to the user.
    ticket.user.send_email(subject, 'support/email/ticket-new.txt', ticket=ticket, reply=reply)

    # Then to any admins.
    admins = User.query.filter_by(is_admin=True)
    for admin in admins:
         if admin != ticket.user:
             admin.send_email(subject, 'support/email/ticket-new.txt', ticket=ticket, reply=reply)

@ticket_reply_signal.connect_via(app)
def send_ticket_reply_message(*args, **kwargs):
    ticket = kwargs.pop('ticket', None)
    reply = kwargs.pop('reply', None)

    subject = "[#%d] %s" % (ticket.id, ticket.subject)

    # First send a message to the user.
    ticket.user.send_email(subject, 'support/email/ticket-body.txt', ticket=ticket, reply=reply)

    # Then to any admins.
    admins = User.query.filter_by(is_admin=True)
    for admin in admins:
         if admin != ticket.user:
             admin.send_email(subject, 'support/email/ticket-body.txt', ticket=ticket, reply=reply)

