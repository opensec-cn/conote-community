#!/usr/bin/env bash

chown www-data:www-data -R .
chown www-data:www-data -R /data/conote/media
chown www-data:www-data -R /data/conote/static
chown www-data:www-data -R /data/conote/sandbox

source env/bin/activate

./manage.py migrate --no-input && ./manage.py collectstatic --no-input

exec /home/conote/env/bin/gunicorn -w 2 -k gevent -b 127.0.0.1:8076 -u www-data -g www-data "$@" conote.wsgi:application