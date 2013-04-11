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

from flask import Flask, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail
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
    mail_handler = SMTPHandler('127.0.0.1',
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

# cron system
import panel2.cron
cron = panel2.cron.CronManager()

# base components
import panel2.user
import panel2.views
import panel2.session
import panel2.auth_hooks
import panel2.preferences
import panel2.service
import panel2.filters
import panel2.job
import panel2.invoice

# plugins!
from panel2.dns import dns
from panel2.support import support
from panel2.vps import vps
from panel2.mod_invoice import invoice
from panel2.squid import squid
from panel2.status import status
from panel2.profile import profile

app.add_url_rule('/static/<path:filename>',
                 endpoint='static',
                 subdomain='manage.edge',
                 view_func=app.send_static_file)

app.register_blueprint(dns, subdomain='manage.edge', url_prefix='/dns')
app.register_blueprint(support, subdomain='manage.edge', url_prefix='/support')
app.register_blueprint(vps, subdomain='manage.edge', url_prefix='/vps')
app.register_blueprint(invoice, subdomain='manage.edge', url_prefix='/invoice')

app.register_blueprint(status, subdomain='status')
app.register_blueprint(profile, subdomain='manage.edge', url_prefix='/account')

app.add_url_rule('/static/<path:filename>',
                 endpoint='static',
                 subdomain='status',
                 view_func=app.send_static_file)
