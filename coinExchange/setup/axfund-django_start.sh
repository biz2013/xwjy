#!/bin/bash

cd /home/ubuntu/workspace/xwjy/coinExchange/     # Working dir
source dj2env/bin/activate
sudo dj2env/bin/python manage.py runserver --settings=coinExchange.settings.dev 0.0.0.0:80
