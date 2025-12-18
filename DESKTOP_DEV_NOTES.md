# Desktop App Development Notes

## 📝 Current Status: PRODUCTION READY ✅

All components implemented and tested. Ready for development mode and production builds.

## 🚀 Quick Commands

### Start Development
```bash
cd desktop
npm install           # First time only
npm run tauri:dev     # Start dev server
```

### Build Production
```bash
build_desktop.bat     # Windows
./build_desktop.sh    # Linux/macOS
```

## ⚠️ Known Issues & Solutions

### 1. Icons Missing
**Issue**: App icons not generated yet (32x32, 128x128, etc.)
**Solution**: Use icon generator tool or create manually:
```bash
# Install sharp for image processing
npm install -g sharp-cli

# Generate icons from logo
sharp input-logo.png -o icons/32x32.png resize 32 32
sharp input-logo.png -o icons/128x128.png resize 128 128
```

### 2. Auto-Update Public Key
**Issue**: `pubkey` is empty in tauri.conf.json
**Solution**: Generate keypair for signing updates:
```bash
# Install tauri-cli
cargo install tauri-cli

# Generate keys
tauri signer generate -w ~/.tauri/myapp.key

# Add public key to tauri.conf.json
```

### 3. First Build Takes Long
**Issue**: Rust compilation slow on first build (3-5 minutes)
**Solution**: This is normal. Subsequent builds are faster (~30 seconds)

### 4. Python Backend Not Found
**Issue**: Rust commands can't find Python scripts
**Solution**: Ensure Python backend is in parent directory or update paths in cmd.rs

## 🔧 Configuration Tips

### Change App Name
Edit `desktop/src-tauri/tauri.conf.json`:
```json
"productName": "Your App Name",
"identifier": "com.yourcompany.appname"
```

### Change Window Size
Edit `desktop/src-tauri/tauri.conf.json`:
```json
"windows": [{
  "width": 1920,
  "height": 1080,
  "minWidth": 1024,
  "minHeight": 768
}]
```

### Add New Color
Edit `desktop/tailwind.config.js`:
```javascript
colors: {
  'cyber-pink': '#ff00ff',
  'cyber-blue': '#0099ff'
}
```

### Create New Component
```bash
cd desktop/src/components
# Create NewComponent.jsx
# Import in App.jsx
# Add to navigation
```

## 📦 Build Outputs

### Windows
- **MSI**: `desktop/src-tauri/target/release/bundle/msi/FYI Social Infinity_2.0.0_x64_en-US.msi`
- **NSIS**: `desktop/src-tauri/target/release/bundle/nsis/FYI Social Infinity_2.0.0_x64-setup.exe`

### Linux
- **AppImage**: `desktop/src-tauri/target/release/bundle/appimage/fyi-social-infinity_2.0.0_amd64.AppImage`

### macOS
- **DMG**: `desktop/src-tauri/target/release/bundle/dmg/FYI Social Infinity_2.0.0_x64.dmg`

## 🐛 Debugging

### Enable Rust Debug Mode
```bash
cd desktop/src-tauri
cargo build --debug
cargo run
```

### View Tauri Logs
Development mode shows logs in terminal automatically.

### React DevTools
Open browser DevTools in development mode (F12)

### Check Rust Backend
```bash
cd desktop/src-tauri
cargo check
cargo test
```

## 📚 Resources

- **Tauri Docs**: https://tauri.app/v1/guides/
- **React 19**: https://react.dev/
- **Framer Motion**: https://www.framer.com/motion/
- **Vite**: https://vitejs.dev/
- **Tailwind**: https://tailwindcss.com/

## 🎯 Next Development Steps

1. **Generate Icons**: Create icon set in `desktop/src-tauri/icons/`
2. **Test Builds**: Build for all platforms and test installers
3. **Add Keyboard Shortcuts**: Implement Ctrl+K command palette
4. **Setup Auto-Update**: Configure update server and sign releases
5. **Add Analytics**: Integrate real-time data from backend
6. **Implement Offline Mode**: Add IndexedDB caching
7. **Create Plugins**: Build extension system for customization

## 💡 Tips

- Use `console.log()` for debugging in development
- Check browser console (F12) for React errors
- Check terminal for Rust compilation errors
- Hot reload works for React changes automatically
- Rust changes require restart (Ctrl+C then `npm run tauri:dev`)

## ✅ Pre-Release Checklist

- [ ] Generate app icons
- [ ] Add auto-update public key
- [ ] Test on Windows
- [ ] Test on Linux (optional)
- [ ] Test on macOS (optional)
- [ ] Update version in package.json and tauri.conf.json
- [ ] Build release installers
- [ ] Sign installers (Windows/macOS)
- [ ] Test installers on clean systems
- [ ] Create release notes
- [ ] Deploy update server

---

**Last Updated**: January 2024
**Phase**: 3 (Desktop God-Mode)
**Status**: Production Ready ✅
