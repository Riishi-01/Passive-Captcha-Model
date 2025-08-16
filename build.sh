#!/bin/bash
set -e

echo "Building frontend..."
cd frontend
npm ci
npm run build
cd ..

echo "Installing Python dependencies..."
pip install -r backend/requirements.txt

echo "Build completed successfully!"