#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from flask import render_template, Markup, redirect, url_for, request, abort
from panel2.models import User, get_session_user, login_required
from panel2.dns.models import Domain, Record
from panel2.dns import dns
from panel2 import db

@dns.route('/')
@dns.route('/zones')
@login_required
def list():
    user = get_session_user()
    return render_template('dns/zones.html', zones=user.domains)

@dns.route('/zone/<zone_id>')
@login_required
def view_domain(zone_id):
    domain = Domain.query.filter_by(id=zone_id).first()
    if domain.user != get_session_user():
        abort(403)
    return render_template('dns/view-zone.html', zone=domain)

@dns.route('/zone/<zone_id>/record/<record_id>', methods=['GET', 'POST'])
@login_required
def edit_record(zone_id, record_id):
    domain = Domain.query.filter_by(id=zone_id).first()
    if domain.user != get_session_user():
        abort(403)
    record_obj = Record.query.filter_by(domain_id=domain.id, id=record_id).first()
    if request.method == 'POST':
        record_obj.update_name(record_obj.domain.full_name(request.form['subdomain']))
        record_obj.update_content(request.form['content'])
        return redirect(url_for('.view_domain', zone_id=request_obj.id))

    return render_template('dns/edit-record.html', zone=record_obj.domain, record=record_obj)

@dns.route('/zone/new', methods=['GET', 'POST'])
@login_required
def new_domain():
    if request.method == 'POST':
        user = get_session_user()
        domain = Domain(user, request.form['domain_name'])
        return redirect(url_for('.view_domain', zone_id=domain.id))

    return render_template('dns/new-domain.html')

@dns.route('/zone/<zone_id>/record/new', methods=['GET', 'POST'])
@login_required
def new_record(zone_id):
    domain = Domain.query.filter_by(id=zone_id).first()
    if domain.user != get_session_user():
        abort(403)
    if request.method == 'POST':
        domain.add_record(domain.full_name(request.form['subdomain']),
                          request.form['content'], request.form['type'],
                          request.form['prio'], request.form['ttl'])
        return redirect(url_for('.view_domain', zone_id=domain.id))

    return render_template('dns/new-record.html', zone=domain)

@dns.route('/zone/<zone_id>/record/<record_id>/delete')
@login_required
def delete_record(zone_id, record_id):
    domain = Domain.query.filter_by(id=zone_id).first()
    if domain.user != get_session_user():
        abort(403)
    Record.query.filter_by(domain_id=domain.id, id=record_id).delete()
    db.session.commit()

    return redirect(url_for('.view_domain', zone_id=zone_id))

@dns.route('/zone/<zone_id>/delete')
@login_required
def delete_domain(zone_id):
    domain = Domain.query.filter_by(id=zone_id).first()
    if domain.user != get_session_user():
        abort(403)

    # Surprise, surprise!  The SQLAlchemy documentation lies.
    # Remove all dependent records in a separate transaction before
    # removing the parent.  This way we can avoid MySQL derping.
    for record in domain.records:
        db.session.delete(record)

    db.session.commit()

    db.session.delete(domain)
    db.session.commit()

    return redirect(url_for('.list'))
