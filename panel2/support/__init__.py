#!/usr/bin/env python
"""
Copyright (c) 2012, 2013  TortoiseLabs, LLC.

All rights reserved.
"""

from flask import Blueprint

support = Blueprint('support', __name__, template_folder='templates')

import panel2.support.models
import panel2.support.views
import panel2.support.email_hooks
