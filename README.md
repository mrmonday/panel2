# panel2

Copyright (c) 2012, 2013 TortoiseLabs LLC.

This software is free but copyrighted.  See COPYING.md for exact terms and conditions.

## what is it?

This is the highest level component of our platform.  Various other components are also
open-source.  We are working on open-sourcing the remainder, as they are written or vetted
to be release-able.

Specifically, panel2 is the code which runs on the user-facing part of manage.tortois.es.

It covers:

* DNS management
* High-level VPS management
* Account lifecycle management
* Technical support

It can be plugged with support for other products by splicing into the application using
a wrapper.  It is therefore well-behaved (as far as these sorts of apps go).

There are other components in the platform, such as:

* Edia, which is the virtualization management agent running on each host.
* ApplianceKit, which is used to build new installation images.
* PowerDNS, which is used to serve DNS entries.  This is not original code, however, and you
  may find it at powerdns.org.

## why?

We decided that there is basically no value in hiding our development.  So we're developing
our new platform right out there in the open.  Also, by making the code available it allows us
to later pay people outside the company to develop on the code with them already being familiar
with it.  Really, there's a lot of reasons to do it this way, but the main one is that there's
really no good reason *not* to do it this way.

The panel is not really useful to competitors because you still have to assemble the platform
yourself, and the average hosting provider does not know enough about Python and RabbitMQ and
other such nonsense to do it.

