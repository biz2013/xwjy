#!/bin/bash

source /home/osboxes/workspace/xwjy/stakingsvc/dj2env/bin/activate
cd /home/osboxes/workspace/xwjy/stakingsvc/
python manage.py runserver 0.0.0.0:8080 --settings=stakingsvc.settings.virtualbox
