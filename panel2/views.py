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
from flask import render_template, session, redirect, url_for

@app.route('/')
def index():
    if session.has_key("uid"):
        # For right now, lets just redirect to VPS.
        # return render_template('frontpage.html')
        return redirect(url_for('vps.list'))

    return redirect(url_for('login'))

@app.errorhandler(403)
def error_forbidden(e):
    return render_template('error-forbidden.html'), 403

@app.errorhandler(404)
def error_forbidden(e):
    return render_template('error-notfound.html'), 404
