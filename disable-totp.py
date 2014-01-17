#!/usr/bin/env python
"""
Copyright (c) 2014 Centarra Networks, Inc.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice, this permission notice and all necessary source code
to recompile the software are included or otherwise available in all
distributions.

This software is provided 'as is' and without any warranty, express or
implied.  In no event shall the authors be liable for any damages arising
from the use of this software.
"""

import panel2_environment

from panel2 import db
from panel2.user import User

import sys

if len(sys.argv) > 1:
    username = sys.argv[1]

    user = User.query.filter_by(username=username).first()
    user.require_totp = False

    db.session.add(user)
    db.session.commit()

    print "disabled totp requirement for", user.username
