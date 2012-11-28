#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from panel2 import db

class CommitableMixIn:
    def commit(self):
        db.session.add(self)
        db.commit()

