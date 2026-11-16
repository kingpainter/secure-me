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

Bemærk: `alarm_control_panel.alarm_trigger` kræver en gyldig kode, ligesom arm og disarm. Uden kode afvises kaldet, og eventet `secure_me_invalid_code` udsendes.

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
| `open_sensors`      | list[string]          | Når der er åbne sensorer                 | Sensorer der er åbne lige nu. |

---

## 6. NFC Tag Integration (v2.1.0+)

NFC tags kan registreres per bruger for PIN-less authentication. Home Assistant
`tag_scanned` events udløser alarm-handlinger.

### WebSocket Endpoints (Frontend → Backend)

#### `get_nfc_tags` — Hent alle registrerede NFC tags

**Request:**
```json
{
  "id": 1,
  "type": "secure_me/get_nfc_tags"
}
```

Kræver ikke admin. Returnerer alle tags, ikke kun den aktuelle brugers.

**Response:**
```json
{
  "id": 1,
  "type": "result",
  "success": true,
  "result": {
    "nfc_tags": {
      "04FA123456789ABC": {
        "user_id": "user_123",
        "action": "disarm",
        "name": "iPhone",
        "requires_pin": false,
        "created_at": 1790000000.0
      }
    }
  }
}
```

`nfc_tags` er et dict nøglet på `tag_id`. `created_at` er et Unix-tidsstempel (sekunder), ikke ISO-tekst.

#### `register_nfc_tag` — Registrer nyt NFC tag (kræver admin)

**Request:**
```json
{
  "id": 2,
  "type": "secure_me/register_nfc_tag",
  "tag_id": "HA_TAG_ID_FROM_SCAN",
  "user_id": "user_123",
  "action": "disarm",
  "name": "iPhone",
  "requires_pin": false
}
```

- `tag_id`, `user_id`, `action` (`disarm` eller `arm_away`) og `name` er påkrævet.
- `requires_pin` er valgfri (standard `false`). Se bemærkningen om schema nedenfor.

**Response:**
```json
{
  "id": 2,
  "type": "result",
  "success": true,
  "result": {
    "success": true
  }
}
```

Svaret indeholder ikke tag-objektet. Læs det via `get_nfc_tags`.

#### `delete_nfc_tag` — Slet NFC tag (kræver admin)

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

#### `get_ha_nfc_tags` — Hent tags kendt af Home Assistant

Returnerer en liste af tag-ID'er fra HA's tag-register (eller `.storage/tag` som fallback). Bruges af panelet til at importere tags. Kræver ikke admin.

#### `import_nfc_tag` — Importer et HA-tag til Secure Me (kræver admin)

```json
{
  "id": 3,
  "type": "secure_me/import_nfc_tag",
  "tag_id": "04FA123456789ABC",
  "action": "disarm",
  "name": "Hoveddør"
}
```

Taget gemmes uden brugerbinding (`user_id` = `null`).

### Home Assistant Event Integration

Secure Me lytter selv på HA's `tag_scanned`-event, når et tag er registreret. Der skal **ikke** oprettes en separat automation for registrerede tags. En sådan automation ville køre sammen med den indbyggede håndtering og give dobbelte kald.

For tags med `requires_pin: true` skal PIN'en leveres i eventets `code`-felt. Et tag uden PIN handler på scanningen alene.

Tags uden PIN virker dermed uden kode, også når en global kode er sat op. Det er bevidst: tagget er legitimationen.

> **Bemærk:** I v2.2.0 læser koden `requires_pin` i `register_nfc_tag` og `import_nfc_tag` uden at feltet står i schemaet. Verificér, at PIN-kravet faktisk gemmes, efter du registrerer et tag.

```yaml
# Ingen automation nødvendig for registrerede tags (se ovenfor).
# Hvis du alligevel vil lave en egen automation, skal den bruge en
# pladsholder-kode, ikke en hardcoded kode i YAML. Eksempel:
#   service: secure_me.disarm
#   data:
#     code: !secret secure_me_disarm_code
```

---

## 7. Events (Secure Me-genererede)

| Event | Data | Beskrivelse |
|-------|------|-------------|
| `secure_me_armed` | `mode` (str), `armed_by` (str), `armed_by_id` (str \| null) | Alarmen blev armeret |
| `secure_me_disarmed` | `disarmed_by` (str), `disarmed_by_id` (str \| null) | Alarmen blev disarmeret |
| `secure_me_triggered` | `triggered_by` (str) | Alarmen blev udløst |
| `secure_me_arm_failed` | `command` (str), `open_sensors` (list), `bypassed_sensors` (list) | Arm mislykkedes grundet åbne sensorer |
| `secure_me_module_error` | `module` (str), `action` (str), `error` (str) | Modul fejlede under udførelse |
| `secure_me_tag_scanned` | `tag_id`, `tag_name`, `action`, `success`, `error`, `alarm_state`, `pin_required`, `pin_verified` | Et registreret NFC tag blev scannet. `pin_verified` er `null` når tagget ikke kræver PIN. PIN-koden logges eller sendes aldrig i eventet. |
| `secure_me_code_locked` | `lockout_seconds` (int) | Kodeindtastning er låst efter gentagne fejl (5 fejl på 10 min, låst i 10 min) |
| `secure_me_invalid_code` | `command`, `entity_id` (valgfri) | Forkert kode ved arm, disarm eller trigger |
| `secure_me_command_rejected` | `command`, `current_state` | Tilstandsmaskinen afviste kommandoen (fx disarm når allerede disarmed) |
| `secure_me_module_enabled` / `secure_me_module_disabled` | `module` | Et modul blev slået til/fra |
| `secure_me_home_empty` | — | Auto Actions: alle sporede brugere er væk |
| `secure_me_person_home` | `entity_id` | Auto Actions: en sporet bruger er kommet hjem |
| `secure_me_auto_action_done` | `action`, `result`, `success` | Auto Actions: en handling (lock, alarm, camera) er færdig |
| `secure_me_fake_presence_changed` | `active` (bool) | Fake Presence blev slået til eller fra |

---

## 8. Attribut-kontrakt — Versionering

Dette dokument opdateres ved enhver ændring i state-mapping, arm/disarm-veje,
attributter eller services. Se `CHANGELOG.md` for hvornår en given feature
blev introduceret.

### Versionshistorik af API-dokumentation

| Version | Dato | Vigtigste ændringer |
|---------|------|---------------------|
| 2.2.0 | 2026-10-24 | NFC per-tag PIN håndhævet i backend (`requires_pin`), kode-lockout, `secure_me_tag_scanned` med PIN-felter. NFC-endpoints og events dokumenteret i denne version. |
| 2.1.0 | 2026-10-03 | Tilføjet NFC tag integration (endpoints, `secure_me_tag_scanned`-listener) |
| 1.5.0 | 2026-07-19 | Formaliseret alarm entity contract, service-definitioner |

---

## 9. Eksempler

### NFC tag-baseret disarm

Ingen automation er nødvendig. Registrér tagget i panelet (Users → NFC), så håndterer Secure Me `tag_scanned` selv. Se afsnittet om events ovenfor.

### Automation: Arm away når ingen hjemme

```yaml
automation:
  alias: "Secure Me - Auto arm away"
  triggers:
    - trigger: state
      entity_id: binary_sensor.secure_me_anyone_home
      to: "off"
  conditions:
    - condition: state
      entity_id: alarm_control_panel.secure_me
      state: "disarmed"
  actions:
    - action: secure_me.arm_away
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

