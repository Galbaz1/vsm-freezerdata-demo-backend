# SMIDO Methodology - Visual Diagrams

This document contains mermaid diagrams illustrating the SMIDO troubleshooting methodology for cooling systems.

---

## 1. SMIDO Overview Flowchart

The main SMIDO troubleshooting workflow:

```mermaid
flowchart TD
    Start([Storing Gemeld<br/>Fault Reported]) --> M
    
    M[M - MELDING<br/>Report/Symptoms<br/>Wat is het probleem?]
    M --> M1{Symptomen<br/>begrijpelijk?}
    M1 -->|Nee| M2[Aanvullende<br/>vragen stellen]
    M2 --> M
    M1 -->|Ja| T
    
    T[T - TECHNISCH<br/>Quick Technical Check<br/>Waarneembaar defect?]
    T --> T1{Direct zichtbaar<br/>defect?}
    T1 -->|Ja| Fix1[Repareer<br/>direct]
    Fix1 --> End
    T1 -->|Nee| I
    
    I[I - INSTALLATIE VERTROUWD<br/>Installation Familiarity<br/>Ken je het systeem?]
    I --> I1{Schema's &<br/>componenten<br/>bekend?}
    I1 -->|Nee| I2[Bestudeer<br/>documentatie]
    I2 --> I
    I1 -->|Ja| D
    
    D[D - DIAGNOSE: De 3 P's<br/>Systematic Diagnosis]
    D --> P1[P1: POWER<br/>Voeding/Spanning]
    P1 --> P1Check{Spanning<br/>OK?}
    P1Check -->|Nee| Fix2[Controleer<br/>voeding]
    Fix2 --> End
    P1Check -->|Ja| P2
    
    P2[P2: PROCESINSTELLINGEN<br/>Process Settings<br/>Parameters/Setpoints]
    P2 --> P2Check{Instellingen<br/>correct?}
    P2Check -->|Nee| Fix3[Corrigeer<br/>instellingen]
    Fix3 --> End
    P2Check -->|Ja| P3
    
    P3[P3: PROCESPARAMETERS<br/>Process Measurements<br/>Drukken/Temperaturen]
    P3 --> P3Check{Metingen<br/>normaal?}
    P3Check -->|Nee| P4
    P3Check -->|Ja| O
    
    P4[P4: PRODUCTINPUT<br/>Environmental Conditions<br/>Belading/Condities]
    P4 --> P4Check{Condities<br/>normaal?}
    P4Check -->|Nee| Fix4[Corrigeer<br/>condities]
    Fix4 --> End
    P4Check -->|Ja| O
    
    O[O - ONDERDELEN UITSLUITEN<br/>Component Isolation<br/>Welk onderdeel faalt?]
    O --> O1[Test ketens &<br/>signaalgevers]
    O1 --> O2{Defect<br/>onderdeel<br/>gevonden?}
    O2 -->|Ja| Fix5[Vervang/repareer<br/>onderdeel]
    Fix5 --> End
    O2 -->|Nee| Balance
    
    Balance[Koelproces<br/>Uit Balans?]
    Balance --> BalCheck{Verdamper/<br/>Condensor<br/>problemen?}
    BalCheck -->|Ja| Fix6[Herstel balans<br/>Clean/Defrost]
    Fix6 --> End
    BalCheck -->|Nee| Escalate
    
    Escalate[Escaleer naar<br/>specialist]
    Escalate --> End
    
    End([Storing Verholpen<br/>Fault Resolved])
    
    style M fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    style T fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    style I fill:#f3e5f5,stroke:#4a148c,stroke-width:3px
    style D fill:#e8f5e9,stroke:#1b5e20,stroke-width:3px
    style P1 fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style P2 fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style P3 fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style P4 fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style O fill:#ffe0b2,stroke:#e65100,stroke-width:3px
    style Balance fill:#ffccbc,stroke:#bf360c,stroke-width:2px
    style Start fill:#b2dfdb,stroke:#004d40,stroke-width:3px
    style End fill:#c5cae9,stroke:#1a237e,stroke-width:3px
```

---

## 2. SMIDO Detailed Breakdown

### 2.1 Melding (M) - Report Phase

```mermaid
flowchart LR
    M[M - MELDING] --> Questions
    
    Questions[Key Questions to Ask]
    Questions --> Q1[Wat is het<br/>symptoom?]
    Questions --> Q2[Wanneer begon<br/>het probleem?]
    Questions --> Q3[Is het<br/>continu of<br/>intermitterend?]
    Questions --> Q4[Zijn er<br/>alarmen<br/>afgegaan?]
    Questions --> Q5[Wat is er<br/>recent<br/>veranderd?]
    
    Q1 --> Symptoms[Common Symptoms]
    Symptoms --> S1[Te hoge<br/>temperatuur]
    Symptoms --> S2[Compressor<br/>draait niet]
    Symptoms --> S3[Lawaai/<br/>trillingen]
    Symptoms --> S4[IJsvorming]
    Symptoms --> S5[Lekkage]
    
    style M fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    style Questions fill:#bbdefb,stroke:#0277bd,stroke-width:2px
    style Symptoms fill:#90caf9,stroke:#0288d1,stroke-width:2px
```

### 2.2 Technisch (T) - Quick Technical Check

```mermaid
flowchart TD
    T[T - TECHNISCH<br/>Quick Visual/Auditory Checks] --> Checks
    
    Checks[Visual Inspection]
    Checks --> C1{Deur goed<br/>gesloten?}
    Checks --> C2{Zichtbare<br/>schade/lekkage?}
    Checks --> C3{Ongebruikelijke<br/>geluiden?}
    Checks --> C4{Displays/<br/>indicatoren<br/>actief?}
    
    C1 -->|Problem| Fix1[Sluit deur<br/>correct]
    C2 -->|Problem| Fix2[Repareer<br/>lekkage]
    C3 -->|Problem| Investigate[Onderzoek<br/>geluidsbron]
    C4 -->|Problem| CheckPower[Controleer<br/>voeding]
    
    C1 -->|OK| Next[Ga door naar<br/>Installatie]
    C2 -->|OK| Next
    C3 -->|OK| Next
    C4 -->|OK| Next
    
    style T fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    style Checks fill:#fff59d,stroke:#f9a825,stroke-width:2px
```

### 2.3 Installatie Vertrouwd (I) - Familiarity Check

```mermaid
flowchart LR
    I[I - INSTALLATIE<br/>VERTROUWD] --> Knowledge
    
    Knowledge[Required Knowledge]
    Knowledge --> K1[Systeem<br/>schema]
    Knowledge --> K2[Component<br/>locaties]
    Knowledge --> K3[Normale<br/>waarden]
    Knowledge --> K4[Recente<br/>historie]
    
    K1 --> Docs[Documentation]
    Docs --> D1[P&ID<br/>Drawings]
    Docs --> D2[Electrical<br/>Schematics]
    Docs --> D3[Specificaties]
    
    K3 --> Baseline[Baseline Data]
    Baseline --> B1[Normale<br/>temperaturen]
    Baseline --> B2[Normale<br/>drukken]
    Baseline --> B3[Normale<br/>stromen]
    
    style I fill:#f3e5f5,stroke:#4a148c,stroke-width:3px
    style Knowledge fill:#e1bee7,stroke:#6a1b9a,stroke-width:2px
    style Docs fill:#ce93d8,stroke:#7b1fa2,stroke-width:2px
    style Baseline fill:#ce93d8,stroke:#7b1fa2,stroke-width:2px
```

### 2.4 Diagnose (D) - The 3 P's (+ Product Input)

```mermaid
flowchart TD
    D[D - DIAGNOSE<br/>De 3 P's + Product Input] --> P1
    
    P1[P1: POWER<br/>Voeding/Spanning]
    P1 --> P1a[Spanning aanwezig?]
    P1 --> P1b[Zekeringen intact?]
    P1 --> P1c[Vermogensschakelaars OK?]
    P1 --> P1d[Motor/compressor<br/>stroomopname?]
    
    P1 --> P2
    
    P2[P2: PROCESINSTELLINGEN<br/>Parameters/Setpoints]
    P2 --> P2a[Thermostaat<br/>instellingen]
    P2 --> P2b[Pressostaat<br/>waarden]
    P2 --> P2c[Tijdschakelaars]
    P2 --> P2d[Regelaar<br/>configuratie]
    
    P2 --> P3
    
    P3[P3: PROCESPARAMETERS<br/>Metingen]
    P3 --> P3a[Zuigdruk]
    P3 --> P3b[Persdruk]
    P3 --> P3c[Verdamptemperatuur]
    P3 --> P3d[Condenstemperatuur]
    P3 --> P3e[Oververhitting]
    P3 --> P3f[Onderkoeling]
    
    P3 --> P4
    
    P4[P4: PRODUCTINPUT<br/>Omgevingscondities]
    P4 --> P4a[Productbelading]
    P4 --> P4b[Omgevingstemperatuur]
    P4 --> P4c[Luchtstroom]
    P4 --> P4d[Deur frequentie]
    
    style D fill:#e8f5e9,stroke:#1b5e20,stroke-width:3px
    style P1 fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style P2 fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style P3 fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style P4 fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
```

### 2.5 Onderdelen Uitsluiten (O) - Component Isolation

```mermaid
flowchart TD
    O[O - ONDERDELEN<br/>UITSLUITEN] --> Chains
    
    Chains[Test Component Chains]
    Chains --> Chain1[Koudemiddelketen]
    Chains --> Chain2[Elektrische keten]
    Chains --> Chain3[Regelsysteem]
    
    Chain1 --> C1[Compressor]
    Chain1 --> C2[Verdamper]
    Chain1 --> C3[Condensor]
    Chain1 --> C4[Expansieventiel]
    Chain1 --> C5[Filter/droger]
    
    Chain2 --> E1[Voeding]
    Chain2 --> E2[Relais/contactors]
    Chain2 --> E3[Ventilator motors]
    Chain2 --> E4[Compressor motor]
    
    Chain3 --> R1[Temperatuursensoren]
    Chain3 --> R2[Druksensoren]
    Chain3 --> R3[Regelaar]
    Chain3 --> R4[Pressostaten]
    
    C1 --> Test1{Test uitvoeren}
    C2 --> Test1
    C3 --> Test1
    C4 --> Test1
    C5 --> Test1
    E1 --> Test1
    E2 --> Test1
    E3 --> Test1
    E4 --> Test1
    R1 --> Test1
    R2 --> Test1
    R3 --> Test1
    R4 --> Test1
    
    Test1 -->|Defect gevonden| Replace[Vervang/repareer<br/>onderdeel]
    Test1 -->|Alle OK| Balance[Check koelproces<br/>balans]
    
    style O fill:#ffe0b2,stroke:#e65100,stroke-width:3px
    style Chains fill:#ffcc80,stroke:#ef6c00,stroke-width:2px
    style Chain1 fill:#ffb74d,stroke:#f57c00,stroke-width:2px
    style Chain2 fill:#ffb74d,stroke:#f57c00,stroke-width:2px
    style Chain3 fill:#ffb74d,stroke:#f57c00,stroke-width:2px
```

---

## 3. Common Failure Modes Mapped to SMIDO

```mermaid
flowchart LR
    Failures[Common Failures] --> F1
    Failures --> F2
    Failures --> F3
    Failures --> F4
    Failures --> F5
    Failures --> F6
    
    F1[Te hoge<br/>temperatuur]
    F2[Ingevroren<br/>verdamper]
    F3[Compressor<br/>draait niet]
    F4[Ventilator<br/>defect]
    F5[Expansieventiel<br/>defect]
    F6[Regelaar<br/>probleem]
    
    F1 --> D1[SMIDO: M→T→I→D→O]
    F2 --> D2[SMIDO: M→T→D→Balance]
    F3 --> D3[SMIDO: M→T→D-Power]
    F4 --> D4[SMIDO: M→T→D-Power→O]
    F5 --> D5[SMIDO: M→I→D-Params→O]
    F6 --> D6[SMIDO: M→I→D-Settings→O]
    
    D1 --> Telem1[Flags:<br/>main_temp_high]
    D2 --> Telem2[Flags:<br/>suction_extreme]
    D3 --> Telem3[Flags:<br/>main_temp_high]
    D4 --> Telem4[Flags:<br/>hot_gas_low]
    D5 --> Telem5[Flags:<br/>liquid_extreme]
    D6 --> Telem6[Flags:<br/>main_temp_high]
    
    style Failures fill:#ffebee,stroke:#c62828,stroke-width:2px
    style F1 fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    style F2 fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    style F3 fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    style F4 fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    style F5 fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
    style F6 fill:#ffcdd2,stroke:#d32f2f,stroke-width:2px
```

---

## 4. SMIDO + Data Sources Integration

```mermaid
flowchart TD
    Start([Fault Reported]) --> Agent[VSM Agent]
    
    Agent --> SMIDO[SMIDO Methodology]
    
    SMIDO --> M[M - Melding]
    SMIDO --> T[T - Technisch]
    SMIDO --> I[I - Installatie]
    SMIDO --> D[D - Diagnose 3P's]
    SMIDO --> O[O - Onderdelen]
    
    M --> Data1[Data Sources]
    T --> Data1
    I --> Data1
    D --> Data1
    O --> Data1
    
    Data1 --> Telemetry[Telemetry<br/>785K datapoints<br/>15 columns]
    Data1 --> Manuals[Manuals<br/>3 documents<br/>922 chunks]
    Data1 --> Vlogs[Video Logs<br/>15 clips<br/>5 cases]
    
    Telemetry --> Features[WorldState<br/>Features<br/>60+ metrics]
    Features --> Current[Current state]
    Features --> Trends[Trends 30m-24h]
    Features --> Health[Health scores]
    Features --> Flags[Boolean flags]
    
    Manuals --> Sections[Manual Sections<br/>~200 sections]
    Sections --> SMIDO_Docs[SMIDO steps]
    Sections --> Cases[Case studies]
    Sections --> Tables[Diagnostic tables]
    Sections --> Photos[Photos/diagrams]
    
    Vlogs --> Metadata[Vlog Metadata<br/>5 cases + 15 clips]
    Metadata --> Problems[Problem phase]
    Metadata --> Triage[Triage phase]
    Metadata --> Solutions[Solution phase]
    
    Current --> Tools[Agent Tools]
    Trends --> Tools
    Health --> Tools
    Flags --> Tools
    SMIDO_Docs --> Tools
    Cases --> Tools
    Tables --> Tools
    Problems --> Tools
    Triage --> Tools
    Solutions --> Tools
    
    Tools --> Weaviate[Weaviate Vector DB]
    Weaviate --> Query[Semantic Search]
    Query --> Response[Troubleshooting<br/>Guidance]
    
    Response --> Technician[Junior Technician]
    
    style Agent fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    style SMIDO fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    style Telemetry fill:#e8f5e9,stroke:#2e7d32,stroke-width:2px
    style Manuals fill:#f3e5f5,stroke:#6a1b9a,stroke-width:2px
    style Vlogs fill:#ffe0b2,stroke:#e65100,stroke-width:2px
    style Weaviate fill:#e0f2f1,stroke:#00695c,stroke-width:3px
    style Technician fill:#c5cae9,stroke:#1a237e,stroke-width:3px
```

---

## 5. Example: Frozen Evaporator Troubleshooting Flow

```mermaid
flowchart TD
    Start([Melding:<br/>Koelcel bereikt<br/>temperatuur niet]) --> M
    
    M[M - MELDING<br/>Symptomen verzamelen]
    M --> M_Data[Temperatuur te hoog<br/>IJsvorming waargenomen<br/>Alarm actief]
    
    M_Data --> T[T - TECHNISCH<br/>Visuele inspectie]
    T --> T_Find[Verdamper volledig<br/>bevroren<br/>Dikke ijslaag]
    
    T_Find --> I[I - INSTALLATIE<br/>Schema raadplegen]
    I --> I_Check[Ontdooicyclus<br/>instellingen bekijken<br/>Luchtkanalen bekijken]
    
    I_Check --> D[D - DIAGNOSE<br/>3 P's checken]
    D --> P3[P3: Procesparameters]
    P3 --> P3_Measure[Zuigleiding extreem koud<br/>Verdampdruk te laag<br/>Oververhitting te hoog]
    
    P3_Measure --> O[O - ONDERDELEN<br/>Oorzaak isoleren]
    O --> O_Find[Ontdooitimer defect<br/>Luchtkanalen vervuild<br/>Thermostaat verkeerd]
    
    O_Find --> Solution[OPLOSSING]
    Solution --> S1[1. Handmatig ontdooien]
    Solution --> S2[2. Luchtkanalen reinigen]
    Solution --> S3[3. Thermostaat kalibreren]
    Solution --> S4[4. Ontdooitimer vervangen]
    
    S1 --> Verify[Verificatie]
    S2 --> Verify
    S3 --> Verify
    S4 --> Verify
    
    Verify --> Check{IJsvorming<br/>verdwenen?<br/>Temperatuur<br/>normaal?}
    Check -->|Ja| End([Storing verholpen])
    Check -->|Nee| Escalate[Escaleer naar<br/>specialist]
    
    subgraph Data_Sources[Data Sources Used]
        Tel[Telemetry:<br/>_flag_main_temp_high<br/>_flag_suction_extreme]
        Man[Manual:<br/>Page 7 - Frozen evaporator case<br/>Koelproces uit balans]
        Vlog[Vlog A3:<br/>Problem-Triage-Solution<br/>Complete workflow]
    end
    
    style Start fill:#ffebee,stroke:#c62828,stroke-width:3px
    style M fill:#e1f5ff,stroke:#01579b,stroke-width:3px
    style T fill:#fff9c4,stroke:#f57f17,stroke-width:3px
    style I fill:#f3e5f5,stroke:#4a148c,stroke-width:3px
    style D fill:#e8f5e9,stroke:#1b5e20,stroke-width:3px
    style O fill:#ffe0b2,stroke:#e65100,stroke-width:3px
    style Solution fill:#c8e6c9,stroke:#2e7d32,stroke-width:3px
    style End fill:#c5cae9,stroke:#1a237e,stroke-width:3px
    style Data_Sources fill:#e0f2f1,stroke:#00695c,stroke-width:2px
```

---

## 6. Component Reference Diagram

```mermaid
graph TB
    subgraph Cooling_System[Koelsysteem Componenten]
        Compressor[Compressor<br/>Drukverhogend]
        Condensor[Condensor<br/>Warmteafvoer]
        Expansion[Expansieventiel<br/>Drukverlaging]
        Evaporator[Verdamper<br/>Warmteopname]
        
        Compressor -->|Hoge druk<br/>Hoge temp| Condensor
        Condensor -->|Vloeibaar<br/>Onderkoeld| Expansion
        Expansion -->|Lage druk<br/>Twee fasen| Evaporator
        Evaporator -->|Gas<br/>Oververhit| Compressor
    end
    
    subgraph Control_System[Regelsysteem]
        Thermostat[Thermostaat]
        Pressostat[Pressostaat]
        Controller[Regelaar]
        Sensors[Sensoren]
    end
    
    subgraph Support_Components[Ondersteunende Componenten]
        Fan_Evap[Verdamper ventilator]
        Fan_Cond[Condensor ventilator]
        Filter[Filter/Droger]
        Receiver[Vloeistofvat]
        Valve[Magneetklep]
    end
    
    Controller --> Compressor
    Controller --> Fan_Evap
    Controller --> Fan_Cond
    Controller --> Valve
    
    Thermostat --> Controller
    Pressostat --> Controller
    Sensors --> Controller
    
    Fan_Evap -.-> Evaporator
    Fan_Cond -.-> Condensor
    Filter -.-> Expansion
    Receiver -.-> Expansion
    
    style Compressor fill:#ffcdd2,stroke:#c62828,stroke-width:2px
    style Condensor fill:#fff9c4,stroke:#f57f17,stroke-width:2px
    style Expansion fill:#c8e6c9,stroke:#2e7d32,stroke-width:2px
    style Evaporator fill:#bbdefb,stroke:#1565c0,stroke-width:2px
    style Controller fill:#e1bee7,stroke:#6a1b9a,stroke-width:2px
```

---

## Legend

| Color | SMIDO Phase |
|-------|-------------|
| 🔵 Blue | M - Melding (Report) |
| 🟡 Yellow | T - Technisch (Technical Quick Check) |
| 🟣 Purple | I - Installatie Vertrouwd (Familiarity) |
| 🟢 Green | D - Diagnose (3 P's + Product Input) |
| 🟠 Orange | O - Onderdelen Uitsluiten (Component Isolation) |
| 🔴 Red | Failure Modes / Problems |
| 🔵 Indigo | Resolution / End State |
| 🟢 Teal | Data Sources / Tools |

