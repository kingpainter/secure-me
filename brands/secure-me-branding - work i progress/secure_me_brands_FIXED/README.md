# Secure Me - Home Assistant Brands Package

This package contains all required branding files for the Secure Me integration to be submitted to the Home Assistant brands repository.

## Package Contents

### Standard Icons/Logos (Light Background)
- `icon.png` - 256x256 pixels (standard resolution)
- `icon@2x.png` - 512x512 pixels (high DPI)
- `logo.png` - 256x256 pixels (standard resolution)
- `logo@2x.png` - 512x512 pixels (high DPI)

### Dark Mode Variants (Dark Background)
- `dark_icon.png` - 256x256 pixels (standard resolution)
- `dark_icon@2x.png` - 512x512 pixels (high DPI)
- `dark_logo.png` - 256x256 pixels (standard resolution)
- `dark_logo@2x.png` - 512x512 pixels (high DPI)

## Specifications

All files meet Home Assistant brands requirements:

✅ **Icon Requirements:**
- Aspect ratio: 1:1 (square)
- Standard size: 256x256 pixels
- hDPI size: 512x512 pixels
- Format: PNG with transparency
- Trimmed (minimal empty space)

✅ **Logo Requirements:**
- Same as icon (square shield design)
- Standard size: 256x256 pixels
- hDPI size: 512x512 pixels
- Format: PNG with transparency
- Trimmed (minimal empty space)

✅ **Dark Mode Support:**
- Optimized versions for dark backgrounds
- Prefixed with `dark_` as per HA standards

## Design Elements

**Theme:** Våbenskjold (coat of arms) with security elements

**Shield Design:** Divided into 4 quadrants containing:
- 🔒 Lock (top left) - Security
- 🏠 House (top right) - Home automation
- 📷 Camera (bottom left) - Surveillance
- 🔔 Bell (bottom right) - Notifications

**Color Scheme:**
- Gold/bronze metallic icons
- Black/dark gray shield interior
- Silver/gray shield frame
- Professional and modern appearance

## Submission Instructions

### 1. Fork Repository
```bash
# Visit GitHub and fork:
https://github.com/home-assistant/brands

# Clone your fork:
git clone https://github.com/YOUR_USERNAME/brands.git
cd brands
```

### 2. Create Integration Directory
```bash
# Create directory structure:
mkdir -p custom_integrations/secure_me
```

### 3. Copy Files
```bash
# Copy all 8 PNG files to the new directory:
cp icon.png custom_integrations/secure_me/
cp icon@2x.png custom_integrations/secure_me/
cp logo.png custom_integrations/secure_me/
cp logo@2x.png custom_integrations/secure_me/
cp dark_icon.png custom_integrations/secure_me/
cp dark_icon@2x.png custom_integrations/secure_me/
cp dark_logo.png custom_integrations/secure_me/
cp dark_logo@2x.png custom_integrations/secure_me/
```

### 4. Commit and Push
```bash
# Add files:
git add custom_integrations/secure_me/

# Commit:
git commit -m "Add Secure Me custom integration branding"

# Push:
git push origin master
```

### 5. Create Pull Request
1. Go to your forked repository on GitHub
2. Click "Pull Request"
3. Title: "Add Secure Me custom integration branding"
4. Description:
   ```
   Adding branding for Secure Me - a comprehensive home alarm system integration.
   
   Integration domain: secure_me
   Integration type: Custom integration
   
   Files included:
   - Standard icons/logos (256x256 and 512x512)
   - Dark mode variants
   
   All files meet HA brands requirements:
   - Square 1:1 aspect ratio
   - Proper sizes (256x256, 512x512)
   - PNG format with transparency
   - Trimmed (minimal empty space)
   - Optimized for both light and dark themes
   ```
5. Submit pull request

## Verification

After submission and approval, the branding will be available at:

```
https://brands.home-assistant.io/_/secure_me/icon.png
https://brands.home-assistant.io/_/secure_me/icon@2x.png
https://brands.home-assistant.io/_/secure_me/logo.png
https://brands.home-assistant.io/_/secure_me/logo@2x.png
https://brands.home-assistant.io/_/secure_me/dark_icon.png
https://brands.home-assistant.io/_/secure_me/dark_icon@2x.png
https://brands.home-assistant.io/_/secure_me/dark_logo.png
https://brands.home-assistant.io/_/secure_me/dark_logo@2x.png
```

## Integration Manifest

Ensure your `manifest.json` has the correct domain:

```json
{
  "domain": "secure_me",
  ...
}
```

The domain name must match the directory name in the brands repository.

## Credits

**Design:** Professional våbenskjold theme with security elements  
**Created:** February 2026  
**Integration:** Secure Me v0.2.0  
**Developer:** KingPainter  
**License:** MIT

## Support

For issues with the branding package:
- GitHub: https://github.com/kingpainter/secure-me
- Home Assistant Community: Search for "Secure Me"

---

**Last Updated:** 2026-02-08  
**Package Version:** 1.0.0  
**Status:** Ready for submission ✅
