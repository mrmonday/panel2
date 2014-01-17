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

from panel2 import app as application

# plugins!
from panel2.dns import dns
from panel2.support import support
from panel2.vps import vps
from panel2.mod_invoice import invoice
from panel2.status import status
from panel2.profile import profile

# branding module
from panel2.mod_branding_simple import branding

# register the branding module as a blueprint
application.register_blueprint(branding, url_prefix='/branding')
application.register_blueprint(dns, url_prefix='/dns')
application.register_blueprint(support, url_prefix='/support')
application.register_blueprint(vps, url_prefix='/vps')
application.register_blueprint(invoice, url_prefix='/invoice')
application.register_blueprint(status, url_prefix='/status')
application.register_blueprint(profile, url_prefix='/account')
