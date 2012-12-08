#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

import re

from flask import render_template, Markup, redirect, url_for, request, abort
from jinja2 import evalcontextfilter, escape

from panel2.models import User, get_session_user, login_required, admin_required
from panel2.utils import strip_unprintable
from panel2.support.models import Ticket, Reply
from panel2.support import support
from panel2 import db

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@app.template_filter()
@evalcontextfilter
def nl2br(eval_ctx, value):
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '<br>\n') \
        for p in _paragraph_re.split(escape(value)))
    if eval_ctx.autoescape:
        result = Markup(result)
    return result

def user_can_access_ticket(ticket, user=None):
    if user is None:
        user = get_session_user()
    if user.is_admin is True:
        return True
    if ticket.user != user:
        return False
    return True

@support.route('/')
@support.route('/tickets')
@login_required
def list():
    user = get_session_user()
    open_tickets = []
    closed_tickets = []
    for ticket in user.tickets:
        if ticket.is_open is not True:
            closed_tickets.append(ticket)
        else:
            open_tickets.append(ticket)

    return render_template('support/ticketlist.html', open_tickets=open_tickets, closed_tickets=closed_tickets,
                           open_tickets_count=len(open_tickets), closed_tickets_count=len(closed_tickets))

@support.route('/tickets/all')
@admin_required
def list_all():
    open_tickets = Ticket.query.filter_by(is_open=True)
    closed_tickets = Ticket.query.filter_by(is_open=False)

    return render_template('support/ticketlist.html', open_tickets=open_tickets, closed_tickets=closed_tickets,
                           open_tickets_count=open_tickets.count(), closed_tickets_count=closed_tickets.count())

@support.route('/ticket/<ticket_id>', methods=['GET', 'POST'])
@login_required
def view(ticket_id):
    ticket = Ticket.query.filter_by(id=ticket_id).first_or_404()
    if user_can_access_ticket(ticket) is not True:
        abort(403)
    if request.method == 'POST':
        reply = strip_unprintable(request.form['message'])
        ticket.add_reply(get_session_user(), reply)
        return redirect(url_for('.view', ticket_id=ticket_id))

    return render_template('support/ticketview.html', ticket=ticket)

@support.route('/ticket/<ticket_id>/close')
@login_required
def close(ticket_id):
    ticket = Ticket.query.filter_by(id=ticket_id).first_or_404()
    if user_can_access_ticket(ticket) is not True:
        abort(403)
    ticket.close()

    return redirect(url_for('.list'))

@support.route('/ticket/new', methods=['GET', 'POST'])
@login_required
def new():
    if request.method == 'POST':
        subject = strip_unprintable(request.form['subject'])
        message = strip_unprintable(request.form['message'])

        if len(subject) == 0:
            abort(500)
        if len(message) == 0:
            abort(500)

        ticket = Ticket(get_session_user(), subject, message)
        return redirect(url_for('.view', ticket_id=ticket.id))

    return render_template('support/ticketnew.html')
