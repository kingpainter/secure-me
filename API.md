# Secure Me — Alarm Control API Contract

> **Version:** 2.2.0
> **Formål:** Formel, versioneret beskrivelse af hvordan eksterne forbrugere
> (Lovelace-kort, automations, scripts) skal styre og aflæse Secure Me's
> alarm-entitet. Opdateret i v2.2.0 med NFC tag-understøttelse og service-dokumentation.
>
> Dette dokument beskriver:
> 1. `alarm_control_panel`-entiteten og arm/disarm-veje
> 2. NFC tag WebSocket endpoints (v2.1.0+)
> 3. Registered HA services (`secure_me.*`)
>
> Websocket-API'et for panel-konfiguration (sensorer, moduler, floorplan osv.)
> er internt mellem `secure-me-panel.js` og backend og er ikke en del af denne kontrakt.

---

## 1. Alarm-tilstande (States)

Secure Me's interne tilstande (se `const.py`, `STATE_ALARM_*`):

| Secure Me state    | HA `AlarmControlPanelState` (entity.state) | Standard? |
|--------------------|---------------------------------------------|-----------|
| `disarmed`         | `disarmed`                                   | Ja |
| `arming`           | `arming`                                     | Ja |
| `pending`          | `pending`                                    | Ja |
| `armed_away`       | `armed_away`                                 | Ja |
| `armed_home`       | `armed_home`                                 | Ja |
| `armed_night`      | `armed_night`                                | Ja |
| `armed_vacation`   | `armed_vacation`                             | Ja |
| `armed_home_alone` | `armed_home_alone` (rå streng, ikke et HA-enum-medlem) | **Nej — se §2** |
| `triggered`        | `triggered`                                  | Ja |

**Regel:** Brug aldrig `entity.state` alene til at afgøre om alarmen er i
Home Alone-mode i generisk HA-tooling (voice assistants, det indbyggede
alarm-kort) — de kender ikke strengen `armed_home_alone` og vil vise
"Unknown". Secure Me's egne kort læser `entity.state` direkte og har en
eksplicit `armed_home_alone`-gren, så det er trygt der. Attributten
`secure_me_mode` (§5) indeholder altid den samme værdi som `entity.state`
og er den foretrukne kilde for nyt kode, uanset hvilken vej fremtidige
HA-ændringer måtte tage.

---

## 2. Home Alone — den ene bevidst undtagelse

HA's `AlarmControlPanelState`-enum har intet begreb der svarer til "hjemme,
men alene", og har kun én "custom"-plads (`ARMED_CUSTOM_BYPASS`) — der er
ingen anden ledig plads at låne. Derfor:

- Entiteten rapporterer den rå streng `"armed_home_alone"` direkte som
  `state` — **ikke** `ARMED_CUSTOM_BYPASS`. Dette blev reverteret i
  v1.5.0 efter at `ARMED_CUSTOM_BYPASS`-mapningen brød
  `secure_me_alarm_tab_card.js` (kunne ikke skelne Alene fra en almindelig
  bypass).
- Konsekvens: HA's *indbyggede* standard alarm-kort og evt.
  voice-assistant-eksponering (Google Home/Alexa) vil vise "Unknown" i
  Home Alone-tilstand. Accepteret tradeoff — Secure Me styres udelukkende
  via egne kort som alle læser `entity.state` direkte.
- Den ægte tilstand er også tilgængelig via attributten `secure_me_mode`.
- Arming sker via `secure_me.arm_home_alone` service eller websocket-kommando
  `secure_me/arm_home_alone`.

---

## 3. Arm/disarm-veje — hvilken skal jeg bruge?

| Mode              | Standard HA-service                          | secure_me.*-service | Websocket |
|-------------------|-----------------------------------------------|----------------------|-----------|
| Away              | `alarm_control_panel.alarm_arm_away`          | `secure_me.arm_away` | `secure_me/arm_away` |
| Home              | `alarm_control_panel.alarm_arm_home`          | `secure_me.arm_home` | `secure_me/arm_home` |
| Night             | `alarm_control_panel.alarm_arm_night`         | `secure_me.arm_night` | `secure_me/arm_night` |
| Vacation          | `alarm_control_panel.alarm_arm_vacation`      | `secure_me.arm_vacation` | `secure_me/arm_vacation` |
| **Home Alone**    | *(findes ikke — se §2)*                       | `secure_me.arm_home_alone` | `secure_me/arm_home_alone` |
| Disarm            | `alarm_control_panel.alarm_disarm`            | `secure_me.disarm` | `secure_me/disarm` |

**Alle arm-services accepterer disse valgfri parametre:**
- `code` (string): PIN-kode til arm. Valideres via bcrypt ThreadPoolExecutor.
- `skip_delay` (boolean): Hop exit-delay over (default: false)
- `force` (boolean): Arm selv hvis sensorer er åbne (default: false)

**Anbefaling:**
- Automations/scripts uden for panel-konteksten bør bruge `secure_me.*`-services,
  da disse er rigtige, registrerede HA-services med schema-validering.
- Lovelace-kort skal bruge standard `alarm_control_panel.*`-services for
  away/home/night/vacation/disarm, og websocket kun for home_alone.

---

## 4. Registrerede HA-Services (v1.5.0+)

Alle disse services er tilgængelige i automations/scripts via
`service: secure_me.<service_name>`:

| Service | Parameters | Beskrivelse |
|---------|------------|-------------|
| `arm_away` | `code`, `skip_delay`, `force` | Arm i away-mode (alle zoner aktive) |
| `arm_home` | `code`, `skip_delay`, `force` | Arm i home-mode (perimeter kun) |
| `arm_night` | `code`, `skip_delay`, `force` | Arm i night-mode |
| `arm_vacation` | `code`, `skip_delay`, `force` | Arm i vacation-mode |
| `arm_home_alone` | `code`, `skip_delay`, `force` | Arm i Home Alone-mode |
| `disarm` | `code` (required) | Disarm alarmen |
| `trigger` | `source` (optional) | Udløs alarm manuelt |
| `run_test` | `test_type` (quick/standard/full) | Kør systemtest |
| `enable_module` | `module_id` (string) | Aktivér modul (admin kun) |
| `disable_module` | `module_id` (string) | Deaktivér modul (admin kun) |

---

## 5. Attribut-kontrakt (alarm_control_panel-entiteten)

| Attribut            | Type                  | Til stede når                          | Beskrivelse |
|---------------------|-----------------------|------------------------------------------|-------------|
| `secure_me_mode`    | string                | Altid                                    | Den ægte Secure Me-tilstand (identisk med `entity.state`). |
| `changed_by`        | string \| null        | Altid                                    | Brugernavn der sidst armerede/disarmede. |
| `triggered_by`      | string \| null        | Efter trigger, overlever restart         | Sensor-navn eller bruger der udløste alarm. |
| `last_triggered`    | ISO-timestamp \| null | Efter mindst én trigger, overlever restart | Tidspunkt for sidste trigger. |
| `countdown`         | int                   | Kun under `arming`/`pending`             | Sekunder tilbage af delay. |
| `target_mode`       | string                | Kun under `arming`                       | Hvilken `armed_*`-tilstand vi er på vej til. |
| `bypassed_sensors`  | list[string]          | Når sensorer er auto-bypassed            | Tomt array hvis ingen. |
| `code_arm_required` | bool                  | Altid                                    | Altid `true` — koden valideres via bcrypt. |

---

## 6. NFC Tag Integration (v2.1.0+)

NFC tags kan registreres per bruger for PIN-less authentication. Home Assistant
`tag_scanned` events udløser alarm-handlinger.

### WebSocket Endpoints (Frontend → Backend)

#### `get_nfc_tags` — Hent brugerens NFC tags

**Request:**
```json
{
  "type": "secure_me/get_nfc_tags",
  "user_id": "user_123"
}
```

**Response:**
```json
{
  "type": "secure_me/get_nfc_tags",
  "success": true,
  "tags": [
    {
      "tag_id": "nfc_abc123",
      "user_id": "user_123",
      "name": "iPhone",
      "created_at": "2026-10-03T10:30:00Z"
    }
  ]
}
```

#### `register_nfc_tag` — Registrer nyt NFC tag

**Request:**
```json
{
  "type": "secure_me/register_nfc_tag",
  "user_id": "user_123",
  "tag_id": "HA_TAG_ID_FROM_SCAN",
  "name": "iPhone"
}
```

**Response:**
```json
{
  "type": "secure_me/register_nfc_tag",
  "success": true,
  "tag": {
    "tag_id": "HA_TAG_ID_FROM_SCAN",
    "user_id": "user_123",
    "name": "iPhone",
    "created_at": "2026-10-03T10:30:00Z"
  }
}
```

#### `delete_nfc_tag` — Slet NFC tag

**Request:**
```json
{
  "type": "secure_me/delete_nfc_tag",
  "tag_id": "nfc_abc123"
}
```

**Response:**
```json
{
  "type": "secure_me/delete_nfc_tag",
  "success": true
}
```

### Home Assistant Event Integration

Når en registreret NFC tag scannes, affyrer Home Assistant en `tag_scanned`
event med tag-IDet. Secure Me lytter på disse events og kan udløse arm/disarm
baseret på tag-brugerbinding:

```yaml
# Example automation (user-created, ikke Secure Me-genereret)
automation:
  alias: "Disarm on NFC scan"
  trigger:
    platform: event
    event_type: tag_scanned
    event_data:
      tag_id: "04FA123456789ABC"
  action:
    service: secure_me.disarm
    data:
      code: "1234"  # or trigger without code for known users
```

---

## 7. Events (Secure Me-genererede)

| Event | Data | Beskrivelse |
|-------|------|-------------|
| `secure_me_alarm_armed` | `mode` (str), `armed_by` (str) | Alarmen blev armeret |
| `secure_me_alarm_disarmed` | `disarmed_by` (str) | Alarmen blev disarmeret |
| `secure_me_alarm_triggered` | `triggered_by` (str) | Alarmen blev udløst |
| `secure_me_arm_failed` | `command` (str), `open_sensors` (list), `bypassed_sensors` (list) | Arm mislykkedes grundet åbne sensorer |
| `secure_me_module_error` | `module` (str), `action` (str), `error` (str) | Modul fejlede under udførelse |
| `secure_me_nfc_scanned` | `tag_id` (str), `user_id` (str) | NFC tag blev scannet og registreret (v2.1.0+) |

---

## 8. Attribut-kontrakt — Versionering

Dette dokument opdateres ved enhver ændring i state-mapping, arm/disarm-veje,
attributter eller services. Se `CHANGELOG.md` for hvornår en given feature
blev introduceret.

### Versionshistorik af API-dokumentation

| Version | Dato | Vigtigste ændringer |
|---------|------|---------------------|
| 2.2.0 | 2026-10-03 | Tilføjet NFC tag endpoints, komplette service-definitioner |
| 2.1.0 | 2026-10-03 | Tilføjet NFC tag integration |
| 1.5.0 | 2026-07-19 | Formaliseret alarm entity contract, service-definitioner |

---

## 9. Eksempler

### Automation: NFC tag-baseret disarm

```yaml
automation:
  alias: "Secure Me - Disarm on NFC"
  trigger:
    platform: event
    event_type: tag_scanned
    event_data:
      tag_id: "04FA123456789ABC"
  action:
    service: secure_me.disarm
    data:
      code: "1234"
```

### Automation: Arm away når ingen hjemme

```yaml
automation:
  alias: "Secure Me - Auto arm away"
  trigger:
    platform: state
    entity_id: binary_sensor.secure_me_anyone_home
    to: "off"
  condition:
    condition: state
    entity_id: alarm_control_panel.secure_me
    state: "disarmed"
  action:
    service: secure_me.arm_away
    data:
      skip_delay: false
```

### Script: Force arm regardless of open sensors

```yaml
script:
  secure_me_force_arm:
    sequence:
      - service: secure_me.arm_away
        data:
          code: "1234"
          force: true
```

