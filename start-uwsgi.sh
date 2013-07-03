#!/bin/sh

echo "HOME is ${HOME}"
(sleep 2; chmod 777 ${HOME}/panel2-uwsgi.sock) &
/usr/bin/env uwsgi --workers 8 --plugin-dir /usr/lib/uwsgi --plugin python -s ${HOME}/panel2-uwsgi.sock -w panel2:app
