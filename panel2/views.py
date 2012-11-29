#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from panel2 import app
from flask import render_template, session

@app.route('/')
def index():
    if session.has_key("uid"):
        return render_template('frontpage.html')

    return render_template('login.html')

@app.errorhandler(403)
def error_forbidden():
    return render_template('error-forbidden.html')

