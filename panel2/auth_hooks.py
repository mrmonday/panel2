#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from panel2 import app
from panel2.sessionviews import login_signal, authfail_signal
from flask import request

@login_signal.connect_via(app)
def send_login_notice(*args, **kwargs):
    user = kwargs.pop('user', none)
    user.send_email('Authentication successful for %s from %s' % (user.name, request.environ['REMOTE_ADDR']), 'email/auth-message.txt')

@authfail_signal.connect_via(app)
def send_authfail_notice(*args, **kwargs):
    user = kwargs.pop('user', none)
    user.send_email('Authentication failed for %s from %s' % (user.name, request.environ['REMOTE_ADDR']), 'email/authfail-message.txt')

