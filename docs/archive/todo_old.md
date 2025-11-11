# todo.md

> Doel van dit document:  
> Jij (Claude, AI coding editor) gaat eerst **onderzoek doen naar de data** in deze repo, zodat we daarna gerichte opdrachten kunnen geven voor ETL, ingestie en Elysia-integratie.

Gebruik waar nodig Python-scripts / notebooks in de repo of nieuwe files in `notebooks/` of `scripts/`. Geef je antwoorden bij voorkeur terug in de vorm van **markdown-bestanden in de repo** (bijv. `docs/data/telemetry_schema.md`, etc.).

---

## 1. Timeseries / Telemetry (parquet)

### 1.1 Vind en beschrijf alle relevante bestanden

1. Zoek in de repo naar alle **parquet files** met telemetry:
   - Identificeer:
     - Bestandsnamen,
     - Paden,
     - Eventuele naming conventies (bijv. `*_cleaned.parquet`, `*_with_flags.parquet`).
2. Maak een kort overzicht in een nieuw markdown-bestand, bijv.  
   `docs/data/telemetry_files.md` met:
   - Tabel: `filename` | `path` | `description` (als er iets uit de context/naam duidelijk is).

### 1.2 Schema-analyse

Voor **elke** relevante parquet (in ieder geval voor de “cleaned with flags” variant):

1. Lees de parquet in (Python) en beschrijf de **schema** in `docs/data/telemetry_schema.md`:
   - Kolomnaam,
   - Dtype,
   - Eventuele obvious betekenis (als die herleidbaar is uit naam of bestaande EDA-code).

2. Geef per kolom:
   - `min`, `max`, `mean` (voor numerieke),
   - Aantal unieke waarden (voor categorische/bool),
   - Percentage missing values.

3. Identificeer expliciet:
   - Tijdsas:
     - Welke kolom is de timestamp?
     - Is de data per asset gescheiden (heeft elke rij een asset-id)? Zo ja, hoe heet die kolom?
   - Flags:
     - Welke `_flag_*` kolommen zijn er?
     - Wat is hun type en waarde-distributie?

### 1.3 Semantiek van belangrijke kolommen

We hebben al een vermoeden, maar we willen dat jij het **precies bevestigt** op basis van de echte data:

1. Probeer de volgende kolommen (of equivalenten) te vinden en te beschrijven:
   - Sensoren:
     - `sGekoeldeRuimte` of equivalent,
     - `sHeetgasLeiding`,
     - `sVloeistofleiding`,
     - `sZuigleiding`,
     - `sOmgeving`.
   - Status:
     - `sDeurcontact`,
     - `sRSSI`, `sBattery`.
   - Flags:
     - `_flag_main_temp_high`,
     - `_flag_secondary_error_code`,
     - Overige `_flag_*` kolommen.

2. Beschrijf in `telemetry_schema.md` per kolom:
   - Waarschijnlijk fysische betekenis (bv. “temperatuur in koelcel (°C)”),
   - Waarde-range die in de data voorkomt (bijv. `-40` tot `+10`),
   - Voor flags: in welke situaties staan ze meestal op `True`? (bijvoorbeeld: als `sGekoeldeRuimte` > X).

### 1.4 Basisfeature-voorstellen (nog niet implementeren, wél opschrijven)

Op basis van de schema-analyse:

1. Stel in `docs/data/telemetry_features.md` een lijst voor van **WorldState-features** die we later willen berekenen, bijvoorbeeld:

   - Actuele waarden:
     - `current_room_temp`,
     - `current_ambient_temp`,
     - `current_door_open` (bool),
   - Historische trends (laatste N minuten/uren):
     - `room_temp_min_last_2h`,
     - `room_temp_max_last_2h`,
     - `door_open_ratio_last_2h`,
   - Incidentfeatures:
     - `is_temp_high` (op basis van flag of threshold),
     - `is_ambient_high`,
     - `has_recent_errors` (flags afgelopen X uur).

2. Je hoeft ze **nog niet te implementeren**, alleen goed uit te schrijven met:
   - Naam,
   - Beschrijving,
   - Benodigde kolommen,
   - Tijdvenster (bijv. laatste 30 min / 2 uur / 24 uur).

---

## 2. Manuals (parsed PDFs via Landing AI)

### 2.1 Vind en beschrijf de parsed manual-bestanden

1. Zoek in de repo naar de parsed versies van de 3 manuals (via Landing AI):
   - Dit kunnen JSON, YAML, Markdown of andere gestructureerde formaten zijn.
   - Noteer in `docs/data/manuals_files.md`:
     - `filename`,
     - `path`,
     - Formaat (JSON/MD/etc.),
     - Korte omschrijving (welk manual is het?).

### 2.2 Structuur en key-velden

Voor elk parsed manual-bestand:

1. Inspecteer de structuur en documenteer in `docs/data/manuals_structure.md`:
   - Welke keys komen voor? (`title`, `content`, `page`, `bbox`, `section_id`, etc.),
   - Hoe zijn paragrafen/secties georganiseerd (per pagina, per blok, per heading?).

2. Probeer logische **sectie-grenzen** te identificeren:
   - Bijvoorbeeld:
     - SMIDO-hoofdstuk,
     - Subsecties (Melding / Technisch / Installatie Vertrouwd / De 3 P’s / Ketens & Onderdelen uitsluiten),
     - Specifieke cases zoals “Ingevroren verdamper”,
     - Uitleg “Het koelproces uit balans”,
     - Tabeldata (storings- en diagnosetabellen),
     - Flowcharts (kunnen als tekst of als imagecaptions voorkomen).

### 2.3 Voorstel voor Weaviate-schema `ManualSections`

Schrijf in `docs/data/manuals_weaviate_design.md` een **schema-voorstel** voor een Weaviate-collectie `ManualSections`, o.b.v. wat er in de parsed files echt aanwezig is.

Beantwoord daarbij:

1. Welke properties kunnen we minimaal vullen, gegeven de huidige parsed data? Bijvoorbeeld:

   - `manual_id` (TEXT),
   - `section_id` (TEXT),
   - `title` (TEXT),
   - `body_text` (TEXT),
   - `page_range` (ARRAY/STRING),
   - `smido_step` (TEXT; bijvoorbeeld `melding`, `technisch`, `installatie_vertrouwd`, `3P`, `ketens_onderdelen`, `koelproces_uit_balans`, `overig`),
   - `failure_mode` (TEXT; bv. `ingevroren_verdamper`, `te_hoge_temperatuur`, etc.),
   - `component` (TEXT),
   - `content_type` (TEXT; `uitleg`, `stappenplan`, `flowchart`, `tabel`, `voorbeeldcase`).

2. Welke velden moeten we later **semi-automatisch labelen** via LLM (bijv. failure_mode, smido_step), en welke zijn al direct af te leiden uit de structuur?

3. Welke tekstvelden zijn geschikt voor vectorisatie (Weaviate text2vec), en welke moeten we als gewone metadata gebruiken?

---

## 3. Vlogs (service engineer video’s)

> Let op: het is mogelijk dat de ruwe vlogs nog niet in deze repo staan, of alleen referenties/paden.

### 3.1 Inventarisatie

1. Zoek naar een map of bestandsnamen die wijzen op vlogs:
   - Bijvoorbeeld folders `vlogs/`, `videos/`, `media/`, of JSON/MD met metadata.
2. Documenteer in `docs/data/vlogs_files.md`:
   - Welke vlogs/metadata-bestanden je vindt (naam, pad, formaat),
   - Of er al transcripties of notities bestaan.

Als er **geen vlogs aanwezig** zijn:

- Noteer expliciet dat de vlogs nog ontbreken.
- We gaan dan werken met een “verwacht formaat” i.p.v. bestaande data.

### 3.2 Voorstel voor JSON/tekst-structuur (verwacht formaat)

Maak in `docs/data/vlogs_structure.md` een voorstel voor het **doel-formaat** dat we later door Gemini 2.5 Pro willen laten produceren per vlog.

Bijvoorbeeld per vlog:

- `vlog_id` (TEXT),
- `title` (TEXT),
- `raw_transcript` (TEXT),
- `steps` (ARRAY of TEXT; elk element een stap in de troubleshooting),
- `failure_mode` (TEXT),
- `component` (TEXT),
- `world_state_pattern` (TEXT; beschrijving van typische sensordata situatie),
- `smido_path` (TEXT of ARRAY; bijv. `["melding", "technisch", "3P", "ketens_onderdelen"]`),
- `skill_level` (TEXT; `junior`, `medior`, `senior`),
- Eventueel links:
  - `video_path` of `video_url`.

Leg uit:

- Welke velden verplicht zijn,
- Welke optioneel,
- Welke later in Weaviate als properties gebruikt zullen worden.

---

## 4. Samenvattende vragen die je expliciet moet beantwoorden

In elk van de bovenstaande docs verwachten we dat je de volgende vragen **expliciet beantwoordt**:

1. **Telemetry**
   - Wat is de exacte schema (alle kolommen + types)?
   - Welke kolommen corresponderen hoogstwaarschijnlijk met:
     - Gekoelde ruimte temperatuur,
     - Omgevingstemperatuur,
     - Deurstatus,
     - Relevante flags voor temperatuur/incidenten?
   - Zijn er meerdere assets/installaties of één?
   - Zijn er duidelijke tijdsintervallen (bijv. per minuut, per 5 minuten)?

2. **Manuals**
   - Hoe zijn de parsed manuals precies gestructureerd (keys, nesting, splitsing)?
   - Kunnen we de SMIDO-stappen redelijk afleiden uit de structuur (headings/teksten)?
   - Waar zitten de voorbeeldcases zoals “Ingevroren verdamper” en “Koelproces uit balans” in de data?
   - Hoeveel logische secties verwacht je dat we uiteindelijk in `ManualSections` zullen hebben (ruwe schatting)?

3. **Vlogs**
   - Zijn er al vlogs of metadata aanwezig in de repo?
   - Zo ja: in welk formaat?
   - Zo nee: welk JSON/tekst-formaat stel je voor als eindproduct van de Gemini 2.5 Pro preprocessing?

4. **Weaviate-voorbereiding**
   - Gegeven de echte data, zijn de voorgestelde collections:
     - `ManualSections`,
     - `Incidents`,
     - `ServiceVlogs`,
     
     nog steeds logisch, of stel je alternatieven/aanpassingen voor?

   - Zijn er extra collections nodig (bijv. `RawTelemetryWindows`, `WorldStateSnapshots`)?

---

## 5. Wat je *nog niet* hoeft te doen

In deze fase:

- **Nog geen** ETL-code schrijven om data werkelijk naar Weaviate te pushen.
- **Nog geen** Elysia tools/decision tree implementeren.
- **Nog geen** definitieve schema’s in code maken.

We willen eerst:

1. 100% helderheid over:
   - Wat er precies in de data zit,
   - Hoe het nu is gestructureerd,
   - Welke velden we kunnen en willen gebruiken.
2. Duidelijke design-notities in `docs/data/*.md`.

Zodra deze vragen beantwoord zijn en de docs bestaan, gaan we je vragen:

- ETL-scripts te schrijven,
- Weaviate-schema’s in code te definieren,
- En daarna de Elysia-integratie op te zetten.