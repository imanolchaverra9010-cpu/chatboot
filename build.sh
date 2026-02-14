#!/usr/bin/env bash
# Build script para Render - instala dependencias y ejecuta migraciones
set -o errexit

pip install -r requirements.txt
python manage.py migrate --noinput
