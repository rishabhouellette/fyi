#!/bin/bash

echo "===================================="
echo "Building FYI Social Infinity Desktop"
echo "===================================="
echo ""

cd desktop || exit 1

echo "[1/4] Installing dependencies..."
npm install
if [ $? -ne 0 ]; then
    echo "ERROR: npm install failed"
    exit 1
fi

echo ""
echo "[2/4] Building React frontend..."
npm run build
if [ $? -ne 0 ]; then
    echo "ERROR: Frontend build failed"
    exit 1
fi

echo ""
echo "[3/4] Building Tauri desktop app..."
npm run tauri build
if [ $? -ne 0 ]; then
    echo "ERROR: Tauri build failed"
    exit 1
fi

echo ""
echo "[4/4] Build complete!"
echo ""
echo "Your installers are in: desktop/src-tauri/target/release/bundle/"
echo "- Linux AppImage: desktop/src-tauri/target/release/bundle/appimage/"
echo "- macOS DMG: desktop/src-tauri/target/release/bundle/dmg/"
echo ""
