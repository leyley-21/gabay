#!/bin/sh
set -eu
python manage.py initialize-database
exec python serve.py
