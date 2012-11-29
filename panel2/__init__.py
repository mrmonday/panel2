#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config.from_pyfile('panel2.conf')

db = SQLAlchemy(app)

import panel2.models
import panel2.views
import panel2.sessionviews

# plugins!
from panel2.dns import dns
from panel2.support import support

app.register_blueprint(dns, url_prefix='/dns')
app.register_blueprint(support, url_prefix='/support')
