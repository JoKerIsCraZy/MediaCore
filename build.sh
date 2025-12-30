#!/bin/bash
# Build script for JokerList

echo "Building frontend..."
cd frontend
npm run build

echo "Copying to backend/static..."
cd ..
rm -rf backend/static
mkdir -p backend/static
cp -r frontend/dist/* backend/static/

echo "Done! You can now start the backend with: cd backend && python main.py"
