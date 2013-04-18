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

import rrdtool, os, time, subprocess, socket
from flask import render_template
from panel2 import app, db, cron
from panel2.vps.models import Node, XenVPS
from panel2.cron import MONITORING
from panel2.utils import send_simple_email
from ediarpc.rpc_client import ServerProxy
from panel2.vps.monitorengine import *


