# Secure Me — Alarm Control API Contract

> **Version:** 1.5.0
> **Formål:** Formel, versioneret beskrivelse af hvordan eksterne forbrugere
> (Lovelace-kort, automations, scripts) skal styre og aflæse Secure Me's
> alarm-entitet. Skrevet efter en API-audit i v1.5.0 hvor det viste sig at
> flere dele af kontrakten kun levede som kodekommentarer.
>
> Dette dokument beskriver **kun** `alarm_control_panel`-entiteten og de
> tilhørende arm/disarm-veje. Websocket-API'et for panel-konfiguration
> (sensorer, moduler, floorplan osv.) er internt mellem `secure-me-panel.js`
> og backend og er ikke en del af denne kontrakt.

---

## 1. Alarm-tilstande

Secure Me's interne tilstande (se `const.py`, `STATE_ALARM_*`):

| Secure Me state    | HA `AlarmControlPanelState` (entity.state) | Standard? |
|--------------------|---------------------------------------------|-----------|
| `disarmed`         | `disarmed`                                   | Ja |
| `arming`           | `arming`                                     | Ja |
| `pending`          | `pending`                                    | Ja |
| `armed_away`       | `armed_away`                                 | Ja |
| `armed_home`       | `armed_home`                                 | Ja |
| `armed_night`      | `armed_night`                                | Ja |
| `armed_vacation`   | `armed_vacation`                              | Ja (first-class HA-feature siden v1.4.3) |
| `armed_home_alone` | `armed_home_alone` (rå streng, ikke et HA-enum-medlem) | **Nej — se §2** |
| `triggered`        | `triggered`                                  | Ja |

**Regel:** Brug aldrig `entity.state` alene til at afgøre om alarmen er i
Home Alone-mode i generisk HA-tooling (voice assistants, det indbyggede
alarm-kort) — de kender ikke strengen `armed_home_alone` og vil vise
"Unknown". Secure Me's egne kort læser `entity.state` direkte og har en
eksplicit `armed_home_alone`-gren, så det er trygt der. Attributten
`secure_me_mode` (§4) indeholder altid den samme værdi som `entity.state`
og er den foretrukne kilde for nyt kode, uanset hvilken vej fremtidige
HA-ændringer måtte tage.

## 2. Home Alone — den ene bevidste undtagelse

HA's `AlarmControlPanelState`-enum har intet begreb der svarer til "hjemme,
men alene", og har kun én "custom"-plads (`ARMED_CUSTOM_BYPASS`) — der er
ingen anden ledig plads at låne. Derfor:

- Entiteten rapporterer den rå streng `"armed_home_alone"` direkte som
  `state` — **ikke** `ARMED_CUSTOM_BYPASS`. Dette er bevidst reverteret i
  v1.5.0 efter at `ARMED_CUSTOM_BYPASS`-mapningen brød
  `secure_me_alarm_tab_card.js` (kunne ikke skelne Alene fra en almindelig
  bypass) og gav risiko for fremtidig kollision, hvis noget andet nogensinde
  brugte samme bypass-slot.
- Konsekvens: HA's *indbyggede* standard alarm-kort og evt.
  voice-assistant-eksponering (Google Home/Alexa) vil vise "Unknown" i
  Home Alone-tilstand, da strengen ikke er et gyldigt enum-medlem. Accepteret
  tradeoff — Secure Me styres udelukkende via egne kort
  (`secure-me-panel.js`, `secure-me-alarm-card.js`,
  `secure_me_alarm_tab_card.js`), som alle læser `entity.state` direkte og
  har en eksplicit `armed_home_alone`-gren.
- Den ægte tilstand er også tilgængelig via attributten `secure_me_mode`, som nu
  er identisk med `entity.state` for home_alone (men beholdt som stabil
  kontrakt uafhængigt af fremtidige HA-ændringer).
- Arming sker **ikke** via en standard `alarm_control_panel`-service (HA's
  entity-interface har ingen `arm_home_alone`-kommando), men via:
  - `secure_me.arm_home_alone` — HA-service, dokumenteret i `services.yaml`,
    anbefalet vej for automations/scripts (tilføjet i v1.5.0-API-oprydningen).
  - `secure_me/arm_home_alone` — websocket-kommando, brugt af
    `secure-me-alarm-card.js`.

**Bagudkompatibilitet:** Entiteter der blev gemt af en ældre Secure
Me-build (hvor `state` genuinely var `armed_custom_bypass`) genkendes
stadig korrekt ved HA-genstart — `coordinator.py`'s
`async_restore_state()` reverse-mapper `armed_custom_bypass →
armed_home_alone` som en legacy-fallback.

Dette er den eneste bevidst non-standard del af kontrakten. Alt andet
(away/home/night/vacation/disarm) går gennem HA's standard
`alarm_control_panel.*`-services.

## 3. Arm/disarm-veje — hvilken skal jeg bruge?

| Mode              | Standard HA-service                          | secure_me.*-service (automations) | Websocket (kort) |
|-------------------|-----------------------------------------------|-------------------------------------|-------------------|
| Away              | `alarm_control_panel.alarm_arm_away`          | `secure_me.arm_away`                | `secure_me/arm_away` |
| Home              | `alarm_control_panel.alarm_arm_home`          | `secure_me.arm_home`                | `secure_me/arm_home` |
| Night             | `alarm_control_panel.alarm_arm_night`         | `secure_me.arm_night`               | `secure_me/arm_night` |
| Vacation          | `alarm_control_panel.alarm_arm_vacation`      | `secure_me.arm_vacation`            | `secure_me/arm_vacation` |
| **Home Alone**    | *(findes ikke — se §2)*                       | `secure_me.arm_home_alone`          | `secure_me/arm_home_alone` |
| Disarm            | `alarm_control_panel.alarm_disarm`            | `secure_me.disarm`                  | `secure_me/disarm` |

**Anbefaling:**
- **Lovelace-kort** i secure_me-repoet skal bruge standard
  `alarm_control_panel.*`-services for away/home/night/vacation/disarm, og
  websocket kun for home_alone. (`secure-me-alarm-card.js` blev rettet til
  dette i v1.5.0 — vacation gik tidligere fejlagtigt gennem websocket.)
- **Automations/scripts** uden for panel-konteksten bør bruge
  `secure_me.*`-services (§3-kolonne 2), da disse nu er rigtige, registrerede
  HA-services med schema-validering — ikke websocket-kald der kræver en
  frontend-forbindelse.

> **Historik:** Før v1.5.0 var `services.yaml` dokumentation uden
> tilhørende `hass.services.async_register()`-kald — et kald til
> `secure_me.arm_away` fejlede med "service not found". Dette er rettet i
> `services.py`.

## 4. Attribut-kontrakt (alarm_control_panel-entiteten)

| Attribut            | Type                  | Til stede når                          | Beskrivelse |
|----------------------|-----------------------|------------------------------------------|-------------|
| `secure_me_mode`     | string                | Altid                                     | Den ægte Secure Me-tilstand. Identisk med `entity.state` siden v1.5.0-revert af `armed_home_alone`; beholdes som stabil, HA-uafhængig kontrakt for kode der ikke vil parse `entity.state` direkte. |
| `changed_by`         | string \| null        | Altid                                     | Navnet på brugeren der sidst armerede/disarmede. **Bemærk:** hedder `changed_by`, ikke `armed_by`. |
| `countdown`          | int                   | Kun under `arming`/`pending`              | Sekunder tilbage af exit-/entry-delay. |
| `target_mode`        | string                | Kun under `arming`                        | Hvilken `armed_*`-state alarmen er på vej ind i. |
| `bypassed_sensors`   | list[string]          | Når sensorer er auto-bypassed ved arm      | Tomt array hvis ingen. |
| `last_triggered`     | ISO-timestamp \| null | Efter mindst én trigger, overlever restart | |
| `code_arm_required`  | bool                  | Altid                                     | Altid `true` — koden valideres internt via bcrypt. |

**Ikke eksisterende (men let at antage findes):** der er intet
heartbeat/staleness-felt (fx `last_updated`) der fortæller om
integrationen reelt er "i live" versus blot viser sidst kendte state. Et
kort bør i stedet bruge `hass.connected` til at afgøre om
websocket-forbindelsen til HA overhovedet er oppe. En eventuel
`last_updated`-attribut er på idé-listen til v1.6.0, ikke implementeret endnu.

## 5. Versionering af denne kontrakt

Dette dokument opdateres ved enhver ændring i state-mapping,
arm/disarm-veje eller attributter. Se `CHANGELOG.md` for hvornår en given
attribut/service blev introduceret.
