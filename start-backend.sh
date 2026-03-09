#!/bin/sh
set -e

cd "$(dirname "$0")/backend"

if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python3 -m venv .venv
fi

. .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt -q

echo "Running migrations..."
python manage.py makemigrations accounts music --no-input 2>/dev/null || true
python manage.py migrate --no-input

echo "Starting Django on http://localhost:8000 ..."
python manage.py runserver 8000
