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

from panel2 import app
from panel2.session import login_signal, authfail_signal
from flask import request

@login_signal.connect_via(app)
def send_login_notice(*args, **kwargs):
    user = kwargs.pop('user', None)
    user.send_email('Authentication successful for %s from %s' % (user.username, request.environ['REMOTE_ADDR']), 'email/auth-message.txt')

@authfail_signal.connect_via(app)
def send_authfail_notice(*args, **kwargs):
    user = kwargs.pop('user', None)
    user.send_email('Authentication failed for %s from %s' % (user.username, request.environ['REMOTE_ADDR']), 'email/authfail-message.txt')

