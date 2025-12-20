# FYI Social ∞ - Quick Start Guide

## 🚀 Get Started in 3 Steps

### 1. Install Prerequisites

**Install Rust** (required for Tauri):
```bash
# Windows (PowerShell)
winget install --id=Rustlang.Rustup -e

# Or download from: https://rustup.rs/
```

**Install Node.js 18+**:
```bash
# Windows
winget install OpenJS.NodeJS

# Or download from: https://nodejs.org/
```

### 2. Development Mode

```bash
# Navigate to desktop folder
cd desktop

# Install dependencies (first time only)
npm install

# Start development server
npm run tauri:dev
```

**Development server will open automatically at http://localhost:5173**

### 3. Build Production App

```bash
# Windows
build_desktop.bat

# Linux/macOS
chmod +x build_desktop.sh
./build_desktop.sh
```

**Installers will be created in:**
- Windows MSI: `desktop/src-tauri/target/release/bundle/msi/`
- Windows NSIS: `desktop/src-tauri/target/release/bundle/nsis/`
- Linux AppImage: `desktop/src-tauri/target/release/bundle/appimage/`
- macOS DMG: `desktop/src-tauri/target/release/bundle/dmg/`

---

## 🎨 Component Overview

### Navigation
- **Dashboard**: Analytics overview with charts
- **Upload**: Video upload and AI processing
- **Clips**: Gallery of generated clips
- **Scheduler**: Multi-platform post scheduling
- **Growth**: AI insights and predictions
- **Agency**: Client management dashboard

### Keyboard Shortcuts
- `Ctrl/Cmd + K`: Quick search (coming soon)
- `Ctrl/Cmd + ,`: Settings
- `Ctrl/Cmd + N`: New post

---

## 🐛 Troubleshooting

### "Rust not found" error
```bash
# Install Rust toolchain
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### "npm install" fails
```bash
# Clear cache and retry
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

### Build fails on Windows
```bash
# Install Visual Studio Build Tools
# Download from: https://visualstudio.microsoft.com/downloads/
# Select "Desktop development with C++"
```

### Hot reload not working
```bash
# Kill all Node processes and restart
taskkill /F /IM node.exe    # Windows
killall node                # Linux/macOS

npm run tauri:dev
```

---

## 📚 Learn More

- **Full Documentation**: See `desktop/README.md`
- **Tauri Docs**: https://tauri.app/v1/guides/
- **React 19 Docs**: https://react.dev/
- **Framer Motion**: https://www.framer.com/motion/

---

**Need Help?** Check `PHASE_3_COMPLETION_REPORT.md` for detailed information.

**Built with ❤️ using Tauri 2 + React 19**
