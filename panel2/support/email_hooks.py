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
from panel2.user import User
from panel2.support.models import Ticket, Reply, ticket_create_signal, ticket_reply_signal

@ticket_create_signal.connect_via(app)
def send_ticket_create_message(*args, **kwargs):
    ticket = kwargs.pop('ticket', None)
    reply = kwargs.pop('reply', None)
    notify_admins = kwargs.pop('notify_admins', True)

    subject = "[#%d] %s" % (ticket.id, ticket.subject)

    # First send a message to the user.
    ticket.user.send_email(subject, 'support/email/ticket-new.txt', ticket=ticket, reply=reply)

    if not notify_admins:
        return

    # Then to any admins.
    admins = User.query.filter_by(is_admin=True)
    for admin in admins:
         if admin != ticket.user:
             admin.send_email(subject, 'support/email/ticket-new.txt', ticket=ticket, reply=reply)

@ticket_reply_signal.connect_via(app)
def send_ticket_reply_message(*args, **kwargs):
    ticket = kwargs.pop('ticket', None)
    reply = kwargs.pop('reply', None)
    notify_admins = kwargs.pop('notify_admins', True)

    subject = "[#%d] %s" % (ticket.id, ticket.subject)

    # First send a message to the user.
    ticket.user.send_email(subject, 'support/email/ticket-body.txt', ticket=ticket, reply=reply)

    if not notify_admins:
        return

    # Then to any admins.
    admins = User.query.filter_by(is_admin=True)
    for admin in admins:
         if admin != ticket.user:
             admin.send_email(subject, 'support/email/ticket-body.txt', ticket=ticket, reply=reply)

