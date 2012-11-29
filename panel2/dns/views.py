#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from flask import render_template, Markup, redirect, url_for, request
from panel2.models import User, get_session_user
from panel2.dns.models import Domain, Record
from panel2.dns import dns
from panel2 import db

@dns.route('/')
@dns.route('/zones')
def list():
    user = get_session_user()
    return render_template('dns/zones.html', zones=user.domains)

@dns.route('/zone/<zone>')
def view_zone(zone):
    domain = Domain.query.filter_by(id=zone).first()
    return render_template('dns/view-zone.html', zone=domain)

@dns.route('/zone/<zone>/record/<record>', methods=['GET', 'POST'])
def edit_record(zone, record):
    record_obj = Record.query.filter_by(domain_id=zone, id=record).first()
    if request.method == 'POST':
        record_obj.set_name(request.form['subdomain'] + '.' + record_obj.domain.name)
        record_obj.set_content(request.form['content'])
        return redirect(url_for('.view_zone', zone=request_obj.id))

    return render_template('dns/edit-record.html', zone=record_obj.domain, record=record_obj)

@dns.route('/zone/new', methods=['GET', 'POST'])
def new_domain():
    if request.method == 'POST':
        user = get_session_user()
        domain = Domain(user, request.form['domain_name'])
        return redirect(url_for('.view_zone', zone=domain.id))

    return render_template('dns/new-domain.html')

@dns.route('/zone/<zone_id>/record/new', methods=['GET', 'POST'])
def new_record(zone_id):
    domain = Domain.query.filter_by(id=zone_id).first()
    if request.method == 'POST':
        domain.add_record(request.form['subdomain'] + '.' + domain.name,
                          request.form['content'], request.form['type'],
                          request.form['prio'], request.form['ttl'])
        return redirect(url_for('.view_zone', zone=domain.id))

    return render_template('dns/new-record.html', zone=domain)

@dns.route('/zone/<zone_id>/record/<record_id>/delete')
def delete_record(zone_id, record_id):
    Record.query.filter_by(domain_id=zone_id, id=record_id).delete()
    db.session.commit()

    return redirect(url_for('.view_zone', zone=zone_id))
