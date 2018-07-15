#!/bin/bash

source /home/osboxes/xwjy/stakingsvc/dj2env/bin/activate
python manage.py runserver 0.0.0.0:8080 --settings=stakingsvc.settings.virtualbox