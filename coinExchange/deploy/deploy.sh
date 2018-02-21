#!/bin/sh
# Deploy latest code.

source ./../../dj2env/bin/activate
export DJANGO_SETTINGS_MODULE=coinExchange.settings.production
git pull
pip install -r requirements/prod.txt

# Update database, static files.
manage.py syncdb --noinput
manage.py migrate
# Need to take care of permission of static path.
manage.py collectstatic --noinput

# restart wsgi
touch coinExchange/wsgi.py


