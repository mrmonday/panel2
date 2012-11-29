#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from panel2 import db
from panel2.models import User

import sys

users = User.query
for user in users:
    print user.username, user.is_admin
