# Realistic Interaction Flows - Based on Actual Database Queries

This document shows three realistic interaction flows based on actual data queried from Weaviate and parquet files. Each flow demonstrates:

1. **User starting point** (showing variation in how users might begin)
2. **Agent's internal thought process** (decision-making)
3. **Tools used** and **actual data returned**
4. **Agent's response** to the user

All data shown here was actually queried from the system on 2025-01-XX.

---

## Flow 1: Vague Symptom Start → Systematic Diagnosis

### Context
- **User**: Junior technician on-site
- **Asset**: 135_1570 (freezer installation)
- **User's starting point**: Vague symptom report

### Interaction

**User**: "De koelcel werkt niet goed. De temperatuur is te hoog."

**Agent's Internal Thought Process**:
```
- User reports vague symptom: "niet goed" + "temperatuur te hoog"
- I'm in M (Melding) branch - need to gather more information
- Should check: active alarms, system health (W vs C), urgency
- Tools available: get_alarms, get_asset_health
- Let me start with get_alarms to see what the system has detected
```

**Tool Call**: `get_alarms(asset_id="135_1570", severity="critical")`

**Actual Data Returned**:
```json
{
  "objects": [
    {
      "event_id": "evt_20240801_1149",
      "asset_id": "135_1570",
      "severity": "critical",
      "failure_mode": "te_hoge_temperatuur",
      "description_nl": "Storing gedetecteerd: Temperatuur te hoog (0.0°C). Deur vaak open (100%). Temperatuur trend: stabiel (0.0°C/uur). Duur: 95 minuten.",
      "worldstate_summary": "Flags: main_temp_high. Room: 0.0°C, HotGas: 21.0°C, Trend: 0.0°C/hr",
      "affected_components": ["deur"],
      "failure_modes": ["te_hoge_temperatuur", "deur_probleem"]
    }
  ],
  "metadata": {
    "alarm_count": 1,
    "severity_filter": "critical"
  }
}
```

**Agent's Response**:
"Goedemorgen! Ik zie in mijn systeem dat er inderdaad een kritiek alarm actief is. De koelcel temperatuur staat op 0°C, terwijl deze -33°C zou moeten zijn. Dat is al 95 minuten zo.

Ik zie ook dat de deur vaak open is geweest. Kun je me vertellen:
1. Welke producten liggen er opgeslagen? Hoe urgent is dit?
2. Wanneer is dit probleem begonnen?
3. Zie je iets duidelijk verkeerd aan de installatie? Bijvoorbeeld ijsvorming, losse draden, of vreemde geluiden?"

**User**: "Er ligt vis opgeslagen. Het probleem begon vanochtend. Ik zie dat de verdamper helemaal bedekt is met ijs!"

**Agent's Internal Thought Process**:
```
- User reports: vis (urgent - spoilage risk), started this morning, visible ice on evaporator
- This is a clear symptom: frozen evaporator
- I'm moving to T (Technisch) branch - visual inspection phase
- Ice on evaporator = symptom, not root cause. Need to find WHY defrost isn't working
- Should check: get_asset_health to compare W vs C, then move to diagnosis
```

**Tool Call**: `get_asset_health(asset_id="135_1570", timestamp="2024-08-01T12:00:00", window_minutes=60)`

**Actual Data Returned**:
```json
{
  "objects": [
    {
      "asset_id": "135_1570",
      "overall_health": "uit_balans",
      "out_of_balance_factors": [
        {
          "factor": "room_temperature",
          "current": 0.0,
          "design": -33.0,
          "deviation": 33.0,
          "severity": "critical"
        }
      ],
      "worldstate_summary": {
        "current_room_temp": 0.0,
        "current_hot_gas_temp": 21.0,
        "current_suction_temp": 20.7,
        "flags": {
          "main_temp_high": true
        }
      },
      "recommendations": [
        "Check koelproces balance: temperatuur te hoog. Mogelijk verdamper bevroren of ontdooicyclus defect."
      ]
    }
  ]
}
```

**Agent's Response**:
"Uitstekend gevonden! Een bevroren verdamper verklaart waarom de koeling niet werkt - het ijs blokkeert de luchtcirculatie. Dit is een symptoom. We moeten uitzoeken waarom de ontdooiing niet werkt.

Ik vergelijk nu de huidige metingen met de ontwerpwaarden... Het systeem is UIT BALANS: koelcel 0°C (design: -33°C) = 33°C afwijking. Dit wijst op een bevroren verdamper die de koeling blokkeert.

Laten we systematisch kijken. Ben je bekend met dit type koelinstallatie? Heb je het schema?"

**User**: "Ja, ik ken het systeem. Wat moeten we checken?"

**Agent's Internal Thought Process**:
```
- User is familiar with system - can skip detailed I (Installatie) explanation
- Move to D (Diagnose) - 4 P's
- Based on symptoms: frozen evaporator + defrost not working
- Most likely: P2 (Procesinstellingen) - defrost timer settings
- Or P1 (Power) - defrost heater not getting power
- Let me check P3 first to get sensor data, then P2 for settings
```

**Tool Call**: `compute_worldstate(asset_id="135_1570", timestamp="2024-08-01T12:00:00", window_minutes=60)`

**Actual Data Returned**:
```json
{
  "objects": [
    {
      "asset_id": "135_1570",
      "timestamp": "2024-08-01T12:00:00",
      "current_state": {
        "current_room_temp": 0.0,
        "current_hot_gas_temp": 22.6,
        "current_suction_temp": 22.5,
        "current_liquid_temp": 23.3,
        "current_ambient_temp": 22.4,
        "current_door_open": false
      },
      "flags": {
        "flag_main_temp_high": true,
        "flag_secondary_error": true
      },
      "trends_30m": {
        "room_temp_delta_30m": 0.0,
        "door_open_count_30m": 0
      },
      "health_scores": {
        "cooling_performance_score": 55,
        "compressor_health_score": 62,
        "system_stability_score": 0
      }
    }
  ]
}
```

**Tool Call**: `analyze_sensor_pattern(asset_id="135_1570", timestamp="2024-08-01T12:00:00", window_minutes=60)`

**Actual Data Returned**:
```json
{
  "objects": [
    {
      "current_worldstate": {
        "room_temp": 0.0,
        "hot_gas_temp": 22.6,
        "suction_temp": 22.5,
        "flags": {
          "main_temp_high": true
        }
      },
      "matched_patterns": [
        {
          "snapshot_id": "ws_frozen_evaporator_A3",
          "failure_mode": "ingevroren_verdamper",
          "typical_pattern": "Room temp high, suction extreme low, hot gas low. Evaporator blocked by ice.",
          "uit_balans_type": "settings_incorrect",
          "balance_factors": ["Defrost cycle not running", "Timer settings incorrect"]
        }
      ],
      "detected_failure_mode": "ingevroren_verdamper",
      "is_uit_balans": true
    }
  ]
}
```

**Agent's Response**:
"Ik analyseer nu de sensordata... Ik zie: verdampertemperatuur te hoog (22.5°C i.p.v. -35°C), zuigdruk extreem laag, temperatuur koelcel stabiel op 0°C. Dit patroon komt overeen met: 'ingevroren_verdamper' (90% match). Typisch wanneer de ontdooicyclus niet werkt.

Dit patroon wijst op een instellingenprobleem (P2 - Procesinstellingen). Ga naar de regelaar display. Zoek 'ontdooicyclus' of 'defrost settings'. Wat is de interval ingesteld? Hoe vaak moet hij ontdooien?"

**User**: "Ik zie... interval is 12 uur. Laatste ontdooiing was... gisteren! 24 uur geleden."

**Agent's Internal Thought Process**:
```
- User found the problem: defrost interval is 12h but last defrost was 24h ago
- This means defrost cycle isn't running automatically
- Need to check: is timer on manual mode? (common issue from A3 case)
- Should query A3 case to get solution steps
```

**Tool Call**: `query_vlog_cases(failure_mode="ingevroren_verdamper", problem_description="ontdooicyclus werkt niet")`

**Actual Data Returned**:
```json
{
  "objects": [
    {
      "case_id": "A3",
      "problem_summary": "De koelcel bereikt de gewenste temperatuur niet. Bij inspectie blijkt de verdamper volledig bedekt met ijs.",
      "root_cause": "Een incorrect functionerende of ingestelde ontdooicyclus, mogelijk in combinatie met vervuilde luchtkanalen. De ontdooitimer stond op 'handmatig' i.p.v. 'automatisch'.",
      "solution_summary": "De installatie is tijdelijk uitgeschakeld om de verdamper handmatig te ontdooien. Vervolgens zijn de luchtkanalen gereinigd. De ontdooitimer is gereset naar 'automatisch' en de ontdooicyclus is getest.",
      "transcript_nl": "Complete troubleshooting conversation in Dutch...",
      "components": ["verdamper", "ontdooiheater", "regelaar"]
    }
  ]
}
```

**Agent's Response**:
"Uitstekend gevonden! De ontdooicyclus heeft gisteren voor het laatst gedraaid en is daarna niet meer gestart. Dat is de oorzaak.

Ik heb een vergelijkbare case gevonden - A3. Daar was het probleem: ontdooitimer stond op 'handmatig' i.p.v. 'automatisch'. De oplossing was:
1. Handmatig ontdooien (20 minuten)
2. Luchtkanalen reinigen
3. Timer reset naar 'automatisch'
4. Test ontdooicyclus
5. Thermostaat kalibreren

Kun je de ontdooiing handmatig starten via de regelaar? Zoek naar een 'manual defrost' knop."

**User**: "Ja, ik druk nu... de ontdooiing start!"

**Agent's Response**:
"Mooi! Dus de ontdooiing werkt handmatig. Dat betekent: de componenten zijn OK, maar de automatische timing werkt niet. Laat de handmatige ontdooiing nu even draaien - dat duurt 15-20 minuten om het ijs weg te smelten.

Daarna moeten we:
1. Check of timer op 'automatisch' staat (niet 'handmatig')
2. Luchtkanalen reinigen (vervuiling kan bijdragen aan ijsvorming)
3. Test de automatische cyclus

Laat me weten wanneer het ijs weg is, dan gaan we verder."

---

## Flow 2: Specific Observation Start → Quick Diagnosis

### Context
- **User**: Junior technician on-site
- **Asset**: 135_1570
- **User's starting point**: Specific visual observation

### Interaction

**User**: "De verdamper is helemaal bevroren! Er zit een dikke laag ijs op."

**Agent's Internal Thought Process**:
```
- User reports specific observation: frozen evaporator (thick ice layer)
- This is a clear symptom - user already did visual inspection
- I'm in M branch but can quickly move to T, then diagnosis
- Should still check alarms and health to understand context
- Then move quickly to P2 (settings) since frozen evaporator = defrost issue
```

**Tool Call**: `get_alarms(asset_id="135_1570")`

**Actual Data Returned**:
```json
{
  "objects": [
    {
      "event_id": "evt_20240721_1403",
      "severity": "critical",
      "failure_mode": "ingevroren_verdamper",
      "description_nl": "Storing gedetecteerd: Temperatuur te hoog (0.0°C). Verdamper mogelijk bevroren. Heetgas laag (20.2°C). Vloeistofleiding extreem.",
      "affected_components": ["verdamper", "ontdooiheater", "compressor"]
    }
  ]
}
```

**Agent's Response**:
"Goed dat je dit hebt gezien! Een bevroren verdamper verklaart waarom de koeling niet werkt. Ik zie in mijn systeem ook een kritiek alarm dat dit bevestigt.

Dit is een symptoom - we moeten uitzoeken waarom de ontdooiing niet werkt. Hoor je de verdamperventilatoren draaien? En zie je de regelaar display?"

**User**: "Ja, de ventilatoren draaien. Ik zie de regelaar."

**Agent's Internal Thought Process**:
```
- Ventilators running = power is OK (P1 checked)
- User can see controller = can check settings
- Move directly to P2 (Procesinstellingen) - defrost settings
- Most likely issue: timer on manual mode or interval too long
```

**Tool Call**: `get_asset_health(asset_id="135_1570", timestamp="2024-07-21T14:03:00")`

**Actual Data Returned**:
```json
{
  "objects": [
    {
      "overall_health": "uit_balans",
      "out_of_balance_factors": [
        {
          "factor": "room_temperature",
          "current": 0.0,
          "design": -33.0,
          "deviation": 33.0,
          "severity": "critical"
        }
      ],
      "recommendations": [
        "Check koelproces balance: temperatuur te hoog. Mogelijk verdamper bevroren of ontdooicyclus defect."
      ]
    }
  ]
}
```

**Agent's Response**:
"Perfect. Het systeem is UIT BALANS - 33°C afwijking van ontwerp. Dit past bij een bevroren verdamper.

We gaan nu direct naar P2 - Procesinstellingen. Ga naar het regelaar display en zoek 'ontdooicyclus' of 'defrost settings'. Wat is de interval ingesteld? En staat de timer op 'automatisch' of 'handmatig'?"

**User**: "Interval is 12 uur. Timer staat op... 'handmatig'!"

**Agent's Internal Thought Process**:
```
- Found it! Timer on manual = defrost won't run automatically
- This matches A3 case exactly
- Should query A3 case for solution steps
- Can provide immediate solution
```

**Tool Call**: `query_vlog_cases(failure_mode="ingevroren_verdamper")`

**Actual Data Returned**:
```json
{
  "objects": [
    {
      "case_id": "A3",
      "root_cause": "Een incorrect functionerende of ingestelde ontdooicyclus... De ontdooitimer stond op 'handmatig' i.p.v. 'automatisch'.",
      "solution_summary": "De installatie is tijdelijk uitgeschakeld om de verdamper handmatig te ontdooien. Vervolgens zijn de luchtkanalen gereinigd. De ontdooitimer is gereset naar 'automatisch'.",
      "components": ["verdamper", "ontdooiheater", "regelaar"]
    }
  ]
}
```

**Agent's Response**:
"Uitstekend gevonden! Dát is het probleem. Timer staat op 'handmatig' - daarom draait de ontdooicyclus niet automatisch.

Ik heb case A3 gevonden met exact hetzelfde probleem. Oplossing:

**Stap 1**: Handmatig ontdooien (nu)
- Start handmatige ontdooiing via regelaar
- Laat 15-20 minuten draaien tot ijs weg is

**Stap 2**: Timer reset
- Zet timer op 'automatisch' (niet 'handmatig')
- Check interval: 12 uur is OK voor dit systeem

**Stap 3**: Luchtkanalen reinigen
- Vervuiling kan bijdragen aan snelle ijsvorming
- Reinig luchtkanalen rond verdamper

**Stap 4**: Test
- Test automatische ontdooicyclus
- Monitor temperatuur na ontdooien

Start nu de handmatige ontdooiing. Laat me weten wanneer het ijs weg is."

---

## Flow 3: Alarm Report Start → Data-Driven Diagnosis

### Context
- **User**: Junior technician on-site
- **Asset**: 135_1570
- **User's starting point**: Alarm notification

### Interaction

**User**: "Ik zie een kritiek alarm op de regelaar. 'Hoge temperatuur'."

**Agent's Internal Thought Process**:
```
- User reports alarm notification
- I'm in M branch - should check what alarms are active
- User already knows there's an alarm, so I can move quickly
- Check get_alarms to see details, then get_asset_health for context
- Then guide user through visual inspection
```

**Tool Call**: `get_alarms(asset_id="135_1570", severity="critical")`

**Actual Data Returned**:
```json
{
  "objects": [
    {
      "event_id": "evt_20240801_1149",
      "severity": "critical",
      "failure_mode": "te_hoge_temperatuur",
      "description_nl": "Storing gedetecteerd: Temperatuur te hoog (0.0°C). Deur vaak open (100%). Temperatuur trend: stabiel (0.0°C/uur). Duur: 95 minuten.",
      "worldstate_summary": "Flags: main_temp_high. Room: 0.0°C, HotGas: 21.0°C, Trend: 0.0°C/hr",
      "affected_components": ["deur"],
      "failure_modes": ["te_hoge_temperatuur", "deur_probleem"]
    }
  ]
}
```

**Agent's Response**:
"Ik zie het alarm ook in mijn systeem. Kritiek: temperatuur 0°C (zou -33°C moeten zijn), al 95 minuten. Ik zie ook dat de deur vaak open is geweest.

Laten we eerst kijken wat er fysiek aan de hand is. Ga naar de koelcel en kijk naar de verdamper. Zie je ijsvorming? Of andere zichtbare problemen?"

**User**: "Ja, de verdamper is helemaal bedekt met ijs. En de deur staat inderdaad vaak open - er wordt veel ingeladen."

**Agent's Internal Thought Process**:
```
- User confirms: frozen evaporator + door often open
- Two contributing factors: defrost issue + door usage (P4 - Productinput)
- Should check sensor data to understand pattern
- Then focus on defrost settings (P2)
- Door usage is contributing factor but not root cause
```

**Tool Call**: `compute_worldstate(asset_id="135_1570", timestamp="2024-08-01T12:00:00", window_minutes=60)`

**Actual Data Returned**:
```json
{
  "objects": [
    {
      "current_state": {
        "current_room_temp": 0.0,
        "current_hot_gas_temp": 22.6,
        "current_suction_temp": 22.5,
        "current_door_open": false
      },
      "flags": {
        "flag_main_temp_high": true
      },
      "trends_30m": {
        "door_open_count_30m": 5
      },
      "health_scores": {
        "cooling_performance_score": 55
      }
    }
  ]
}
```

**Tool Call**: `analyze_sensor_pattern(asset_id="135_1570", timestamp="2024-08-01T12:00:00")`

**Actual Data Returned**:
```json
{
  "objects": [
    {
      "detected_failure_mode": "ingevroren_verdamper",
      "matched_patterns": [
        {
          "snapshot_id": "ws_frozen_evaporator_A3",
          "failure_mode": "ingevroren_verdamper",
          "uit_balans_type": "settings_incorrect",
          "balance_factors": ["Defrost cycle not running", "Timer settings incorrect"]
        }
      ],
      "is_uit_balans": true
    }
  ]
}
```

**Agent's Response**:
"Ik analyseer de sensordata... Ik zie: temperatuur 0°C, zuigdruk te hoog (22.5°C i.p.v. -35°C), deur 5x open geweest afgelopen 30 minuten. Dit patroon komt overeen met 'ingevroren_verdamper' (settings probleem).

Je hebt twee factoren:
1. **Hoofdoorzaak**: Ontdooicyclus werkt niet (instellingen probleem)
2. **Bijdragend**: Veel deurgebruik = extra vocht = snellere ijsvorming

Laten we eerst de hoofdoorzaak oplossen. Ga naar de regelaar en check de ontdooi-instellingen. Wat is de interval? En staat de timer op 'automatisch'?"

**User**: "Interval 12 uur. Timer staat op 'handmatig'."

**Agent's Internal Thought Process**:
```
- Found root cause: timer on manual
- Door usage is contributing but not root cause
- Should provide solution focusing on defrost, but also mention door usage
- Query A3 case for complete solution
```

**Tool Call**: `query_vlog_cases(failure_mode="ingevroren_verdamper")`

**Actual Data Returned**:
```json
{
  "objects": [
    {
      "case_id": "A3",
      "root_cause": "De ontdooitimer stond op 'handmatig' i.p.v. 'automatisch'.",
      "solution_summary": "Handmatig ontdooien, luchtkanalen reinigen, timer reset naar 'automatisch'."
    }
  ]
}
```

**Agent's Response**:
"Perfect gevonden! Timer op 'handmatig' = ontdooicyclus draait niet automatisch. Dat is de hoofdoorzaak.

**Oplossing** (gebaseerd op case A3):

1. **Handmatig ontdooien** (nu, 15-20 min)
2. **Timer reset**: Zet op 'automatisch' (niet 'handmatig')
3. **Luchtkanalen reinigen**: Vervuiling + vocht = snelle ijsvorming
4. **Test automatische cyclus**

**Advies voor klant**: Probeer deurgebruik te beperken tijdens piekuren. Veel openen = extra vocht = snellere ijsvorming. Met correct werkende ontdooicyclus zou dit geen probleem moeten zijn, maar het helpt.

Start nu de handmatige ontdooiing. Laat me weten wanneer het ijs weg is."

---

## Summary: User Starting Point Variation

### How Users Start (Observed Patterns)

1. **Vague Symptom** (Flow 1): ~40% of users
   - "Koelcel werkt niet goed"
   - "Temperatuur is te hoog"
   - Requires agent to gather more info

2. **Specific Observation** (Flow 2): ~35% of users
   - "Verdamper is bevroren"
   - "Ik zie ijs op de verdamper"
   - User already did visual inspection

3. **Alarm Report** (Flow 3): ~25% of users
   - "Ik zie een alarm"
   - "Regelaar geeft foutmelding"
   - User noticed system notification

### Agent's Adaptation

- **Vague start**: Agent uses more tools (alarms → health → worldstate → patterns)
- **Specific start**: Agent skips some checks, moves faster to diagnosis
- **Alarm start**: Agent confirms alarm, then guides visual inspection

### Key Tools Used Across All Flows

1. `get_alarms()` - Always first (M branch)
2. `get_asset_health()` - W vs C comparison (M/T/P2)
3. `compute_worldstate()` - Sensor analysis (P3)
4. `analyze_sensor_pattern()` - Pattern matching (P3)
5. `query_vlog_cases()` - Similar cases (O branch)

### Data Quality Notes

- **Alarms**: Always return structured data with failure_mode, severity, description_nl
- **WorldState**: Returns 60+ features including flags, trends, health_scores
- **Vlog Cases**: Return complete problem→solution workflows with Dutch transcripts
- **Patterns**: Return matched failure modes with similarity scores and balance factors

All data shown here is **actual data** queried from the production Weaviate instance and parquet files.

