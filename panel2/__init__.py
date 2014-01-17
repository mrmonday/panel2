#!/usr/bin/env python
"""
Copyright (c) 2012, 2013, 2014 Centarra Networks, Inc.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice, this permission notice and all necessary source code
to recompile the software are included or otherwise available in all
distributions.

This software is provided 'as is' and without any warranty, express or
implied.  In no event shall the authors be liable for any damages arising
from the use of this software.
"""

from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.sendmail import Mail
from flask.ext.sslify import SSLify

class LocalSSLify(SSLify):
    def redirect_to_ssl(self):
        if 'btc-notify' not in request.url:
            super(LocalSSLify, self).redirect_to_ssl()

app = Flask(__name__)
app.config.from_pyfile('panel2.conf')

db = SQLAlchemy(app)
mail = Mail(app)
ssl = LocalSSLify(app)

if app.config['SEND_DEBUG_EMAILS'] is True:
    import logging
    from logging.handlers import SMTPHandler
    mail_handler = SMTPHandler((app.config['MAIL_SERVER'], app.config['MAIL_PORT']),
                               app.config['NOREPLY_MAIL'],
                               app.config['DEBUG_EMAIL_TARGETS'], __name__ + ' failed')
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter('''
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:

%(message)s
'''))
    app.logger.addHandler(mail_handler)

# add round()
app.jinja_env.globals.update(sum=sum)
app.jinja_env.globals.update(round=round)

# cron system
import panel2.cron
cron = panel2.cron.CronManager()

# navigation system
import panel2.navigation
nav = panel2.navigation.NavigationManager()
app.jinja_env.globals.update(nav=nav)

# base components
import panel2.user
import panel2.views
import panel2.session
import panel2.auth_hooks
import panel2.preferences
import panel2.service
import panel2.filters
import panel2.job
import panel2.job_hooks
import panel2.invoice
