#!/bin/sh

set -e

whoami

#python manage.py wait_for_db
python manage.py makemigrations mainapp  --noinput #|| true --noinput
python manage.py migrate mainapp --no-input
python manage.py runserver 0.0.0.0:8004
#python manage.py collectstatic

