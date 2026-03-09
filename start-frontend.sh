#!/bin/sh
set -e

cd "$(dirname "$0")/frontend"

if [ ! -d "node_modules" ]; then
  echo "Installing npm dependencies..."
  npm install
fi

echo "Starting Vite on http://localhost:5173 ..."
npm run dev
