# Cloudware

Copyright (c) 2012, 2013, 2014 TortoiseLabs LLC.

Many components of this software are free but copyrighted.
See COPYING.md for exact terms and conditions.

## What is it?

Cloudware is a modular framework for building and facilitating customer management and
interactions.

The open-source release includes the following modules:

* DNS management
* High-level VPS management (using the TortoiseLabs Edia framework)
* Account lifecycle management
* Invoicing (including generic recurring services and crediting)
* Technical support
* Service status
* Generic bootstrap-based branding module

Additional modules and custom integrations are available, with a fast turn-around time.
Contact our sales team for more information.

## Installation

1. Copy panel2_environment.example.py to panel2_environment.py and edit it.
2. Run create-all.py.
3. Modify start-uwsgi.sh to fit your needs, or use panel2_environment.py as a config file
   for Apache mod_wsgi.  Specific deployment instructions are not covered here.
4. Create an account on the application instance after it is deployed on your webserver.
5. Run promote-to-admin.py <username> to give them admin access.
6. Add cron.py to your crontab like so:

```
*       *       *       *       *       (cd /home/cloudware/panel2; python cron.py minutely) &>/dev/null
*       *       *       *       *       (cd /home/cloudware/panel2; python cron.py monitoring) &>/dev/null
0       *       *       *       *       (cd /home/cloudware/panel2; python cron.py hourly) &>/dev/null
0       0       *       *       *       (cd /home/cloudware/panel2; python cron.py daily) &>/dev/null
```

At this point your installation is complete.  Individual modules may need manual configuration
(such as setting up the DNS servers and replication for the DNS module).

## Running the Jobserver

Cloudware has a Jobserver for running tasks using the Edia framework.  We simply recommend running the
Jobserver in `screen`, like so:

```
$ screen python jobserver.py
```

This will provide a screen session where you may monitor the performance of the Jobserver.
