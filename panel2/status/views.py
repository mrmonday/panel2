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

import re

from flask import render_template, Markup, redirect, url_for, request, abort
from jinja2 import escape

from panel2.user import User, get_session_user, login_required, admin_required
from panel2.utils import strip_unprintable
from panel2.status.models import Incident, IncidentReply
from panel2.status import status
from panel2 import app, db

_paragraph_re = re.compile(r'(?:\r\n|\r|\n){2,}')

@app.template_filter()
def nl2br(value):
    esc_value = escape(value)
    result = u'\n\n'.join(u'<p>%s</p>' % p.replace('\n', '\n') \
        for p in _paragraph_re.split(esc_value))
    return Markup(result)

@status.route('/')
@status.route('/incidents')
def list():
    incidents = Incident.query.order_by(Incident.opened_at.desc()).all()
    return render_template('status/incidentlist.html', incidents=incidents)

@status.route('/incident/<incident_id>', methods=['GET', 'POST'])
def view(incident_id):
    user = get_session_user()
    incident = Incident.query.filter_by(id=incident_id).first_or_404()
    if request.method == 'POST' and user.is_admin == True:
        reply = strip_unprintable(request.form['message'])
        incident.add_reply(get_session_user(), reply)
        return redirect(url_for('.view', incident_id=incident_id))

    return render_template('status/incidentview.html', incident=incident)

@status.route('/incident/<incident_id>/close')
@admin_required
def close(incident_id):
    incident = Incident.query.filter_by(id=incident_id).first_or_404()
    incident.close()

    return redirect(url_for('.list'))

@status.route('/incident/new', methods=['GET', 'POST'])
@admin_required
def new():
    if request.method == 'POST':
        subject = strip_unprintable(request.form['subject'])
        message = strip_unprintable(request.form['message'])
        department = strip_unprintable(request.form['department'])

        if len(subject) == 0:
            abort(500)
        if len(message) == 0:
            abort(500)
        if len(department) == 0:
            abort(500)

        incident = Incident(get_session_user(), subject, message, 0, department)
        return redirect(url_for('.view', incident_id=incident.id))

    return render_template('status/incidentnew.html')

@status.route('/atom.xml')
def syndicate():
    incidents = Incident.query.order_by(Incident.opened_at.desc()).all()
    return render_template('status/incidentlist.xml', incidents=incidents)
