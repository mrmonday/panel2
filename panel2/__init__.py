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

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.mail import Mail
from flask.ext.sslify import SSLify

app = Flask(__name__)
app.config.from_pyfile('panel2.conf')

db = SQLAlchemy(app)
mail = Mail(app)
ssl = SSLify(app)

import panel2.user
import panel2.views
import panel2.session
import panel2.auth_hooks
import panel2.preferences
import panel2.service
import panel2.filters
import panel2.job

# plugins!
from panel2.dns import dns
from panel2.support import support
from panel2.vps import vps

app.register_blueprint(dns, url_prefix='/dns')
app.register_blueprint(support, url_prefix='/support')
app.register_blueprint(vps, url_prefix='/vps')
