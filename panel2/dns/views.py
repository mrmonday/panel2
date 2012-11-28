#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from flask import render_template
from panel2.models import User, get_session_user
from panel2.dns import dns

@dns.route('/')
@dns.route('/zones')
def list():
    user = get_session_user()
    return render_template('dns/zones.html', zones=user.domains)
