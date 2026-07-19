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
| `armed_home_alone` | `armed_custom_bypass`                         | **Nej — se §2** |
| `triggered`        | `triggered`                                  | Ja |

**Regel:** Brug aldrig `entity.state` alene til at afgøre om alarmen er i
Home Alone-mode. Brug altid attributten `secure_me_mode` (§4), som altid
indeholder den ægte Secure Me-tilstand.

## 2. Home Alone — den ene bevidste undtagelse

HA's `AlarmControlPanelState`-enum har intet begreb der svarer til "hjemme,
men alene". Der findes ikke og vil formentlig aldrig komme et standard
alternativ til dette. Derfor:

- Entiteten rapporterer `armed_custom_bypass` som `state`, så HA's egne UI's
  og integrationer ikke går i stykker på en ukendt streng.
- Den ægte tilstand `armed_home_alone` eksponeres via attributten
  `secure_me_mode`.
- Arming sker **ikke** via en standard `alarm_control_panel`-service (HA's
  entity-interface har ingen `arm_home_alone`-kommando), men via:
  - `secure_me.arm_home_alone` — HA-service, dokumenteret i `services.yaml`,
    anbefalet vej for automations/scripts (tilføjet i v1.5.0-API-oprydningen).
  - `secure_me/arm_home_alone` — websocket-kommando, brugt af
    `secure-me-alarm-card.js`.

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
| `secure_me_mode`     | string                | Altid                                     | Den ægte Secure Me-tilstand — brug denne, ikke `state`, for at skelne `armed_home_alone` fra `armed_custom_bypass`. |
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
