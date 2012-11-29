#!/bin/sh

/usr/bin/env uwsgi --plugin-dir /usr/lib/uwsgi --plugin python --http-socket 0.0.0.0:5000 -w panel2:app
