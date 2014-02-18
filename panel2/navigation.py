#!/usr/bin/env python
"""
Copyright (c) 2013, 2014 Centarra Networks, Inc.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice, this permission notice and all necessary source code
to recompile the software are included or otherwise available in all
distributions.

This software is provided 'as is' and without any warranty, express or
implied.  In no event shall the authors be liable for any damages arising
from the use of this software.
"""

from panel2.user import get_session_user

class NavigationObject(object):
    """
    Navigation object for navbar.
    """
    def __init__(self, title, icon, endpoint, requires_admin=False, requires_permission=None):
        self.title = title
        self.icon = icon
        self.endpoint = endpoint
        self.requires_admin = requires_admin
        self.requires_permission = requires_permission

class NavigationManager(object):
    """
    Controller class for navigation links.

    Typical usage:

        nav = NavigationManager()
        nav.register('vServers', 'icon-cloud', 'vps.list')
    """
    __navitems__ = []

    def items(self, is_admin=False):
        u = get_session_user()
        if not is_admin and u is not None:
            is_admin = u.is_admin
        lst = self.__navitems__
        if not is_admin:
            lst = filter(lambda x: x.requires_admin == False, lst)
        return filter(lambda x: u.has_permission(x.requires_permission), lst)

    def register(self, title, icon, endpoint, requires_admin=False, requires_permission=None):
        self.__navitems__.append(NavigationObject(title, icon, endpoint, requires_admin, requires_permission))

