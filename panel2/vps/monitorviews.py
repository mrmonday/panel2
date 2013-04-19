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

import rrdtool, os, time, subprocess, socket
from flask import render_template, request, url_for, redirect
from panel2 import app, db, cron
from panel2.vps import vps
from panel2.vps.models import Node, XenVPS
from panel2.cron import MONITORING
from panel2.utils import send_simple_email, render_template_or_json
from ediarpc.rpc_client import ServerProxy
from panel2.vps.monitorengine import *
from panel2.user import login_required, admin_required, get_session_user, User, Session
from panel2.vps.views import can_access_vps

@vps.route('/<vps>/monitors')
@login_required
def monitor_list(vps):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    return render_template_or_json('vps/monitoring-base.html', service=vps)

@vps.route('/<vps>/monitor/<monitor>')
@login_required
def monitor_rules(vps, monitor):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    monitor = MonitorProbe.query.filter_by(id=monitor).first_or_404()
    if monitor not in vps.probes:
        abort(403)
    return render_template_or_json('vps/monitoring-details.html', service=vps, monitor=monitor)

@vps.route('/<vps>/monitor/<monitor>/enable')
@login_required
def monitor_enable(vps, monitor):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    monitor = MonitorProbe.query.filter_by(id=monitor).first_or_404()
    if monitor not in vps.probes:
        abort(403)
    monitor.set_active(True)
    return redirect(url_for('.monitor_rules', vps=vps.id, monitor=monitor.id))

@vps.route('/<vps>/monitor/<monitor>/disable')
@login_required
def monitor_disable(vps, monitor):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    monitor = MonitorProbe.query.filter_by(id=monitor).first_or_404()
    if monitor not in vps.probes:
        abort(403)
    monitor.set_active(False)
    return redirect(url_for('.monitor_rules', vps=vps.id, monitor=monitor.id))

montypes = {
    'ping': lambda vps: PingProbe(request.form['nickname'], vps, request.form['ip']),
    'tcp':  lambda vps: TCPConnectProbe(request.form['nickname'], vps, request.form['ip'], request.form['port'], request.form['content'] if len(request.form['content']) > 0 else None),
    'uri':  lambda vps: HTTPProbe(request.form['nickname'], vps, request.form['uri'], request.form['content'] if len(request.form['content']) > 0 else None),
};

@vps.route('/<vps>/monitor/new', methods=['GET', 'POST'])
@login_required
def monitor_new(vps):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    if request.method == 'POST':
        probe = montypes[request.form['type']](vps)
        probe.verify()
        return redirect(url_for('.monitor_rules', vps=vps.id, monitor=probe.id))
    return render_template_or_json('vps/monitoring-new.html', service=vps)

trigtypes = {
    'reboot': lambda monitor: RebootServiceTrigger(monitor),
    'email':  lambda monitor: EMailTrigger(monitor, request.form['email'] if len(request.form['email']) > 0 else None),
}

@vps.route('/<vps>/monitor/<monitor>/trigger/new', methods=['GET', 'POST'])
@login_required
def monitor_new_trigger(vps, monitor):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    monitor = MonitorProbe.query.filter_by(id=monitor).first_or_404()
    if monitor not in vps.probes:
        abort(403)
    if request.method == 'POST':
        trigger = trigtypes[request.form['type']](monitor)
        return redirect(url_for('.monitor_rules', vps=vps.id, monitor=monitor.id))
    return render_template_or_json('vps/monitoring-trigger-new.html', service=vps, monitor=monitor)

@vps.route('/<vps>/monitor/<monitor>/trigger/<trigger>/delete')
@login_required
def monitor_del_trigger(vps, monitor, trigger):
    vps = XenVPS.query.filter_by(id=vps).first_or_404()
    if can_access_vps(vps) is False:
        abort(403)
    monitor = MonitorProbe.query.filter_by(id=monitor).first_or_404()
    if monitor not in vps.probes:
        abort(403)
    trigger = MonitorTrigger.query.filter_by(id=trigger).first_or_404()
    if trigger not in monitor.triggers:
        abort(403)
    db.session.delete(trigger)
    db.session.commit()
    return redirect(url_for('.monitor_rules', vps=vps.id, monitor=monitor.id))
