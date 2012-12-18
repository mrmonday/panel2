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

from flask import render_template, redirect, url_for
from panel2.vps import vps
from panel2.vps.models import XenVPS
from panel2.user import login_required

@vps.route('/')
@vps.route('/list')
@login_required
def list():
    return render_template('vps/list.html')

@vps.route('/<vps>')
def view(vps):
    vps = XenVPS.query.filter_by(id=vps).first()
    return render_template('vps/view.html', service=vps)

