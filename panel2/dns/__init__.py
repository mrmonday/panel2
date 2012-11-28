#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from flask import Blueprint

dns = Blueprint('dns', __name__, template_folder='templates')

import panel2.dns.models
import panel2.dns.views
