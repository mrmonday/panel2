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

from jinja2 import environmentfunction

from panel2 import app, db
from panel2.status.models import Incident

def incident_count(all=False):
    if not all:
        return Incident.query.filter_by(is_open=True).count()
    return Incident.query.count()

print "UPDATE SHIT"
app.jinja_env.globals.update(incident_count=incident_count)