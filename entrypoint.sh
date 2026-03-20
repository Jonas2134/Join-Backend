#!/bin/bash
set -e

echo "Warte auf PostgreSQL..."
while ! python -c "
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
try:
    s.connect(('${DB_HOST:-db}', ${DB_PORT:-5432}))
    s.close()
    exit(0)
except:
    exit(1)
" 2>/dev/null; do
    echo "PostgreSQL ist noch nicht erreichbar - warte..."
    sleep 1
done
echo "PostgreSQL ist erreichbar!"

echo "Migrationen ausfuehren..."
python manage.py migrate --noinput

echo "Static Files sammeln..."
python manage.py collectstatic --noinput

echo "Starte Gunicorn..."
exec gunicorn core.wsgi:application --bind 0.0.0.0:8000 --workers 3
