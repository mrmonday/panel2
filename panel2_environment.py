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

from panel2 import app as application
from panel2 import nav

# plugins!
from panel2.dns import dns
from panel2.support import support
from panel2.vps import vps
from panel2.mod_invoice import invoice
from panel2.status import status
from panel2.profile import profile

# branding module
from panel2.mod_branding_tortoiselabs import branding

# register the branding module as a blueprint
application.register_blueprint(branding, subdomain='manage', url_prefix='/branding')

application.add_url_rule('/static/<path:filename>',
			endpoint='static',
			subdomain='manage',
			view_func=application.send_static_file)

application.register_blueprint(dns, subdomain='manage', url_prefix='/dns')
application.register_blueprint(support, subdomain='manage', url_prefix='/support')
application.register_blueprint(vps, subdomain='manage', url_prefix='/vps')
application.register_blueprint(invoice, subdomain='manage', url_prefix='/invoice')

application.register_blueprint(status, subdomain='manage', url_prefix='/status')
application.register_blueprint(profile, subdomain='manage', url_prefix='/account')

nav.register('DNS', 'icon-globe', 'dns.list')
nav.register('vServers', 'icon-cloud', 'vps.list')
nav.register('Support', 'icon-phone', 'support.list')
nav.register('Status', 'icon-wrench', 'status.list')
nav.register('Billing', 'icon-usd', 'invoice.index')
nav.register('Admin', 'icon-dashboard', 'profile.list', True)
