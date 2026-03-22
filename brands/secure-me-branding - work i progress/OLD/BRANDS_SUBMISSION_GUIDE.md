# 🎨 Secure Me - Brands Repository Submission Guide

## 📦 Dine Brand Billeder er Klar!

Du har modtaget 4 billeder klar til upload:

| Fil | Størrelse | Formål |
|-----|-----------|--------|
| `icon.png` | 256×256 | Standard icon |
| `icon@2x.png` | 512×512 | hDPI icon |
| `logo.png` | 256×256 | Standard logo |
| `logo@2x.png` | 512×512 | hDPI logo |

**Note:** Da dit våbenskjold er square (1:1 aspect ratio), bruges samme billede for både icon og logo.

---

## 🚀 Submit til Home Assistant Brands Repository

### Step 1: Fork Repository

1. Gå til: https://github.com/home-assistant/brands
2. Click **"Fork"** (øverst til højre)
3. Click **"Create fork"**
4. Vent til fork er klar

---

### Step 2: Opret Folder Struktur

**I dit forked repository:**

1. Click **"Add file"** → **"Create new file"**
2. I "Name your file" feltet, skriv:
   ```
   custom_integrations/secure_me/icon.png
   ```
3. Før du uploader, skal GitHub folder strukturen oprettes

**ELLER brug GitHub Desktop:**

1. Clone dit forked repo:
   ```bash
   git clone https://github.com/kingpainter/brands.git
   cd brands
   ```

2. Opret folder:
   ```bash
   mkdir -p custom_integrations/secure_me
   ```

---

### Step 3: Upload Billeder

**Via GitHub Web Interface:**

1. Gå til: `custom_integrations/secure_me/` i dit fork
2. Click **"Add file"** → **"Upload files"**
3. **Drag and drop** alle 4 filer:
   - icon.png
   - icon@2x.png
   - logo.png
   - logo@2x.png
4. Commit message: `Add Secure Me custom integration`
5. Click **"Commit changes"**

**Via GitHub Desktop:**

1. Kopier de 4 filer til:
   ```
   brands/custom_integrations/secure_me/
   ```

2. Commit:
   ```
   Commit message: Add Secure Me custom integration
   Description: Adding brand images for Secure Me alarm system integration
   ```

3. Push til GitHub

---

### Step 4: Create Pull Request

1. Gå til dit forked repository på GitHub
2. Du vil se en banner: **"This branch is 1 commit ahead of home-assistant:master"**
3. Click **"Contribute"** → **"Open pull request"**

**Pull Request Template:**

**Title:**
```
Add Secure Me custom integration
```

**Description:**
```markdown
## Description
Adding brand images for Secure Me - a professional Home Assistant alarm system integration.

## Integration Details
- **Domain:** secure_me
- **Repository:** https://github.com/kingpainter/secure-me
- **Type:** Custom integration
- **Status:** Active development (v0.2.0)

## Images Included
- ✅ icon.png (256×256)
- ✅ icon@2x.png (512×512)
- ✅ logo.png (256×256)
- ✅ logo@2x.png (512×512)

## Checklist
- [x] Images are in correct format (PNG)
- [x] Images meet size requirements
- [x] Aspect ratio is 1:1 (square logo)
- [x] Images are optimized
- [x] No Home Assistant branded images used
- [x] Domain matches integration manifest.json

## Additional Notes
Secure Me is a custom alarm system integration featuring multi-zone support, 6 smart modules, and a modern configuration dashboard. The våbenskjold (coat of arms) design represents security and protection.
```

4. Click **"Create pull request"**

---

### Step 5: Vent på Review

**Hvad sker der nu:**

1. **Automated checks** kører (minutter)
   - Verificer fil størrelser
   - Check image format
   - Validate folder structure

2. **Maintainer review** (dage/uger)
   - Menneske reviewer PR
   - Kan bede om ændringer
   - Eller approve direkte

3. **Merge** (efter approval)
   - Billeder bliver merged
   - Deployed til brands.home-assistant.io
   - Tilgængelig for alle HA installationer!

**Timeline:**
- ⚡ Automated checks: 1-5 minutter
- 👀 Human review: 3-14 dage (typisk 1 uge)
- 🚀 Deployment: Automatisk ved merge

---

## 🎯 Efter Merge - Opdater Integration

**Når PR er merged**, opdater din manifest.json:

### Option A: Explicit Logo Reference (Anbefalet)

```json
{
  "domain": "secure_me",
  "name": "Secure Me",
  "codeowners": ["@kingpainter"],
  "config_flow": true,
  "dependencies": ["frontend", "http", "websocket_api"],
  "documentation": "https://github.com/kingpainter/secure-me",
  "integration_type": "hub",
  "iot_class": "local_polling",
  "issue_tracker": "https://github.com/kingpainter/secure-me/issues",
  "requirements": [],
  "version": "0.2.0"
}
```

**Fjern `"icon"` linjen helt** - HA henter automatisk fra brands!

### Option B: Keep Icon as Fallback

```json
{
  ...
  "icon": "mdi:shield-home",
  ...
}
```

Icon vises indtil brands er deployed, derefter skifter HA automatisk til dit logo.

---

## 📊 Verification

**Efter merge, verificer at logo virker:**

1. **Check brands URL:**
   ```
   https://brands.home-assistant.io/secure_me/icon.png
   https://brands.home-assistant.io/secure_me/logo.png
   ```

2. **Clear cache + reload HA:**
   - Settings → System → Restart
   - Clear browser cache (Ctrl+Shift+R)
   - Gå til Settings → Devices & Services
   - Dit våbenskjold skulle nu vises! 🛡️

3. **Cache timing:**
   - Browser cache: 7 dage
   - Cloudflare CDN: 24 timer
   - Kan tage tid før alle ser dit logo

---

## 🐛 Troubleshooting

### PR Rejected / Changes Requested

**Common issues:**

1. **Forkert størrelse:**
   - Verificer 256×256 og 512×512
   - Brug "file" command for at tjekke

2. **Forkert format:**
   - Skal være PNG
   - Ikke JPG, SVG, eller andre formater

3. **Forkert placering:**
   - Skal være i `custom_integrations/secure_me/`
   - IKKE i `core_integrations/`

4. **Domæne mismatch:**
   - Folder navn SKAL matche manifest.json domain
   - secure_me = secure_me

### Logo vises ikke efter merge

1. **Vent 24-48 timer:**
   - CDN cache skal refreshe
   - Browser cache skal expire

2. **Force refresh:**
   ```
   Ctrl + Shift + R (hard refresh)
   ```

3. **Check URL direkte:**
   ```
   https://brands.home-assistant.io/secure_me/icon.png
   ```

4. **Verificer manifest.json:**
   - Fjern `"logo"` linje hvis den findes
   - Reload integration

---

## 📝 Alternative: Vent med Brands Submission

**Hvis du ikke vil submitte NU:**

1. **Brug MDI icon** i stedet:
   ```json
   "icon": "mdi:shield-home"
   ```

2. **Submit til brands senere** når:
   - Integration er mere moden (v0.3.0 eller v1.0.0)
   - Flere brugere
   - Stabil codebase

3. **Fordele ved at vente:**
   - Færre support spørgsmål
   - Bedre documentation
   - Mere poleret produkt

**Ulemper:**
- Ingen custom logo i HA (kun MDI icon)
- Men logo fungerer perfekt på GitHub!

---

## ✅ Checklist - Før Submit

- [ ] Alle 4 billeder downloaded
- [ ] Fork brands repository
- [ ] Folder struktur oprettet: `custom_integrations/secure_me/`
- [ ] Alle 4 filer uploaded korrekt
- [ ] Pull request oprettet med god beskrivelse
- [ ] Link til dit GitHub repo inkluderet
- [ ] Domain matcher manifest.json

---

## 🎉 Efter Successful Merge

1. **Update README.md:**
   ```markdown
   ![Secure Me](https://brands.home-assistant.io/secure_me/logo.png)
   ```

2. **Update manifest.json:**
   - Fjern `"icon"` eller `"logo"` linjer
   - HA finder automatisk via brands

3. **Tag new release:**
   ```bash
   git tag -a v0.2.1 -m "Add brands repository support"
   git push origin v0.2.1
   ```

4. **Announce på forum:**
   - Home Assistant Community
   - Reddit r/homeassistant

---

## 📞 Brug for Hjælp?

**Resources:**

- **Brands Repository:** https://github.com/home-assistant/brands
- **Documentation:** https://developers.home-assistant.io/blog/2020/05/08/logos-custom-integrations/
- **Example PR:** Find andre custom integration PRs i brands repo

**Hvis stuck:**
- Check andre PRs for examples
- Spørg i HA Developer Discord
- Eller spørg mig (Claude)!

---

**Filer klar til upload:** ✅  
**Guide komplet:** ✅  
**Klar til at submitte:** 🚀

**God fornøjelse med din brands submission!** 🛡️
