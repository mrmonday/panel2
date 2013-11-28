#!/usr/bin/env python
"""
Copyright (c) 2013 TortoiseLabs LLC

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
    def __init__(self, title, icon, endpoint, requires_admin=False):
        self.title = title
        self.icon = icon
        self.endpoint = endpoint
        self.requires_admin = requires_admin

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
        if is_admin:
            return self.__navitems__
        return filter(lambda x: x.requires_admin == False, self.__navitems__)

    def register(self, title, icon, endpoint, requires_admin=False):
        self.__navitems__.append(NavigationObject(title, icon, endpoint, requires_admin))

