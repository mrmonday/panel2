#!/bin/sh

echo "HOME is ${HOME}"
(sleep 2; chmod 777 ${HOME}/panel2-edge-uwsgi.sock) &
/usr/bin/env uwsgi --workers 4 --plugin-dir /usr/lib/uwsgi --plugin python -s ${HOME}/panel2-edge-uwsgi.sock -w panel2:app
