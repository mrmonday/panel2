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

from panel2.service import IPRange, IPAddress
import sys

ipr = IPRange.query.filter_by(id=sys.argv[1]).all()
for ip in ipr:
	print "Range: {}".format(ip.network)
	print "================================================"
	print "| {} - {}".format(ip.ipnet().network_address, "Network")
	for ip_adr in ip.ipnet().iterhosts():
		if str(ip_adr) == ip.gateway():
			print "| {} - {}".format(ip.gateway(), "Gateway")
		else:
			ip_obj = IPAddress.query.filter_by(ip=str(ip_adr)).first()
			if ip_obj is None or ip_obj.service is None:
				print "| {} - Free".format(str(ip_adr))
			else:
				print "| {} - Assigned to {} '{}'".format(str(ip_adr), ip_obj.service.type, ip_obj.service.name)
	print "| {} - {}".format(ip.ipnet().broadcast_address, "Broadcast")
	print "================================================"
