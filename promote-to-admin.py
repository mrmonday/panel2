#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from panel2 import db
from panel2.models import User

import sys

if len(sys.argv) > 1:
    username = sys.argv[1]
    print username, "will be promoted to admin"

    user = User.query.filter_by(username=username).first()
    user.is_admin = True

    db.session.add(user)
    db.session.commit()

    print username, "privilege level:", ("Admin" if user.is_admin else "User")
