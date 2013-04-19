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
from flask import render_template
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

