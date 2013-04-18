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

from functools import wraps

MINUTELY   = 'minutely'
MONITORING = 'monitoring'
HOURLY     = 'hourly'
DAILY      = 'daily'
WEEKLY     = 'weekly'
MONTHLY    = 'monthly'

class CronManager(object):
    """
    Controller class for handling dispatch of cron operations.

    Typical usage:

        mgr = CronManager()

        @mgr.task(HOURLY)
        def cron_task():
            print 'hourly event'
    """
    taskqueues = {
        MINUTELY:   list(),
        MONITORING: list(),
        HOURLY:     list(),
        DAILY:      list(),
        WEEKLY:     list(),
        MONTHLY:    list()
    }

    def task(self, queue):
        """
        Decorator factory which returns a new decorator that
        is used to add a task to a taskqueue.

        :param queue: queue to add the function to.
        :returns decorator
        """
        if not self.taskqueues.has_key(queue):
            raise NameError(queue)

        def wrapped_fn(func):
            self.taskqueues[queue].append(func)
        return wrapped_fn

    def dispatch(self, queue):
        """
        Dispatch a specific taskqueue.

        :param queue: queue to dispatch
        """
        if not self.taskqueues.has_key(queue):
            raise NameError(queue)

        return [func() for func in self.taskqueues[queue]]
