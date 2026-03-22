# Secure Me - Brands Submission Checklist

## Pre-Submission Verification ✅

### File Requirements
- [ ] `icon.png` - 256x256 pixels ✓
- [ ] `icon@2x.png` - 512x512 pixels ✓
- [ ] `logo.png` - 256x256 pixels ✓
- [ ] `logo@2x.png` - 512x512 pixels ✓
- [ ] `dark_icon.png` - 256x256 pixels ✓
- [ ] `dark_icon@2x.png` - 512x512 pixels ✓
- [ ] `dark_logo.png` - 256x256 pixels ✓
- [ ] `dark_logo@2x.png` - 512x512 pixels ✓

### Quality Checks
- [ ] All images are PNG format ✓
- [ ] All images have transparency ✓
- [ ] All images are trimmed (minimal empty space) ✓
- [ ] Icons are 1:1 square aspect ratio ✓
- [ ] File sizes are optimized ✓
- [ ] Images look good on light background ✓
- [ ] Images look good on dark background ✓

### Technical Checks
- [ ] Domain in manifest.json matches directory name: `secure_me` ✓
- [ ] Integration is a custom integration ✓
- [ ] No Home Assistant branded elements used ✓
- [ ] All trademark considerations met ✓

## Submission Steps

### Step 1: Fork Repository
```bash
# On GitHub, fork:
https://github.com/home-assistant/brands

# Note your fork URL:
https://github.com/YOUR_USERNAME/brands
```

- [ ] Repository forked
- [ ] Fork URL noted: _______________________

### Step 2: Clone Fork Locally
```bash
git clone https://github.com/YOUR_USERNAME/brands.git
cd brands
```

- [ ] Repository cloned locally
- [ ] Changed to brands directory

### Step 3: Create Branch (Optional but Recommended)
```bash
git checkout -b add-secure-me-branding
```

- [ ] New branch created

### Step 4: Create Directory Structure
```bash
mkdir -p custom_integrations/secure_me
```

- [ ] Directory created: `custom_integrations/secure_me/`

### Step 5: Copy Files
```bash
# Copy all 8 branding files:
cp /path/to/secure_me_brands/icon.png custom_integrations/secure_me/
cp /path/to/secure_me_brands/icon@2x.png custom_integrations/secure_me/
cp /path/to/secure_me_brands/logo.png custom_integrations/secure_me/
cp /path/to/secure_me_brands/logo@2x.png custom_integrations/secure_me/
cp /path/to/secure_me_brands/dark_icon.png custom_integrations/secure_me/
cp /path/to/secure_me_brands/dark_icon@2x.png custom_integrations/secure_me/
cp /path/to/secure_me_brands/dark_logo.png custom_integrations/secure_me/
cp /path/to/secure_me_brands/dark_logo@2x.png custom_integrations/secure_me/
```

- [ ] All 8 files copied to correct location

### Step 6: Verify Files
```bash
# Check directory contents:
ls -lh custom_integrations/secure_me/

# Expected output:
# icon.png
# icon@2x.png
# logo.png
# logo@2x.png
# dark_icon.png
# dark_icon@2x.png
# dark_logo.png
# dark_logo@2x.png
```

- [ ] All files present in directory
- [ ] File sizes look reasonable (< 100KB each)

### Step 7: Git Add and Commit
```bash
# Stage files:
git add custom_integrations/secure_me/

# Check what will be committed:
git status

# Commit:
git commit -m "Add Secure Me custom integration branding

- Added icon.png and icon@2x.png
- Added logo.png and logo@2x.png
- Added dark mode variants
- Square 1:1 aspect ratio
- Optimized PNG format
- Meets all HA brands requirements"
```

- [ ] Files staged
- [ ] Changes committed

### Step 8: Push to Your Fork
```bash
# Push to your fork:
git push origin add-secure-me-branding

# Or if you didn't create a branch:
git push origin master
```

- [ ] Changes pushed to GitHub fork

### Step 9: Create Pull Request
On GitHub:

1. **Go to your fork:**
   - https://github.com/YOUR_USERNAME/brands

2. **Click "Pull Request"** or "Compare & pull request"

3. **Fill in PR details:**

**Title:**
```
Add Secure Me custom integration branding
```

**Description:**
```
Adding branding for Secure Me - a comprehensive home alarm system integration for Home Assistant.

**Integration Details:**
- Domain: `secure_me`
- Type: Custom integration
- Repository: https://github.com/kingpainter/secure-me

**Files Added:**
- Standard icons/logos (256x256 and 512x512)
- Dark mode variants for both icon and logo
- Total: 8 PNG files

**Compliance:**
✅ All files meet HA brands requirements:
- Square 1:1 aspect ratio for icons
- Proper sizes (256x256, 512x512)
- PNG format with transparency
- Trimmed with minimal empty space
- Optimized file sizes
- Both light and dark theme support

**Design:**
Professional våbenskjold (coat of arms) theme featuring:
- Lock symbol (security)
- House symbol (home automation)
- Camera symbol (surveillance)
- Bell symbol (notifications)

**Testing:**
Files have been verified to display correctly on both light and dark backgrounds.
```

4. **Submit Pull Request**

- [ ] Pull request created
- [ ] PR number noted: #_______
- [ ] Description complete

### Step 10: Monitor PR
- [ ] PR submitted successfully
- [ ] No automated check failures
- [ ] Respond to any reviewer feedback
- [ ] PR merged

## Post-Submission

### After Merge
Once your PR is merged:

1. **Wait for deployment** (usually within 24 hours)

2. **Verify images are accessible:**
   ```
   https://brands.home-assistant.io/_/secure_me/icon.png
   https://brands.home-assistant.io/_/secure_me/dark_icon.png
   ```

3. **Test in Home Assistant:**
   - Install/update Secure Me integration
   - Check that icons appear correctly
   - Verify dark mode variants work

4. **Update integration documentation:**
   - Add note about official branding
   - Update screenshots if needed

- [ ] Images verified on brands website
- [ ] Images display correctly in Home Assistant
- [ ] Documentation updated

## Troubleshooting

### Common Issues

**Issue:** PR fails automated checks
**Solution:** Check that:
- All files are in correct directory
- File names match exactly (case-sensitive)
- Files are PNG format
- Sizes are correct

**Issue:** Images don't appear after merge
**Solution:** 
- Wait 24-48 hours for CDN propagation
- Clear Home Assistant cache
- Restart Home Assistant

**Issue:** Dark mode variants don't work
**Solution:**
- Ensure files are named with `dark_` prefix
- Check that theme detection is working in HA

## Timeline

- [ ] Pre-submission prep: _____ (date)
- [ ] PR submitted: _____ (date)
- [ ] PR reviewed: _____ (date)
- [ ] PR merged: _____ (date)
- [ ] Images live: _____ (date)
- [ ] Verified in HA: _____ (date)

## Notes

Use this section for any additional notes during the submission process:

```
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
_______________________________________________________________
```

---

**Created:** 2026-02-08  
**Integration:** Secure Me v0.2.0  
**Developer:** KingPainter  
**Status:** Ready for submission ✅
