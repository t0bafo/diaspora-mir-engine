# Amapiano Genre Classification Criteria
*MIR Dataset v1 — Updated May 2026*
*Sourced from: Splice, EDMProd, Roland, Wikipedia, OkayAfrica, Rolling Stone Africa + academic sources*

---

## Core Definition

Amapiano is a South African electronic genre from Gauteng townships (Pretoria/Johannesburg),
emerging mid-2010s. It blends deep house, jazz, and lounge music — unified by a synthesized
log drum and a specific syncopated rhythmic grid. The name means "the pianos" in Zulu.

---

## Non-Negotiable Sonic Markers (3 of 4 Required)

| # | Marker | Specification |
|---|---|---|
| 1 | **BPM** | 108–118 (core: 108–115). Outside this = not Amapiano |
| 2 | **Log Drum** | FM-synthesized percussive bass (Fruity DX10 "Log Drum" preset or equivalent). Woody attack, syncopated lead role — NOT just a kick substitute |
| 3 | **Electric Piano** | Rhodes/Wurlitzer or synth equivalent, jazzy 7th/9th chord voicings. May be absent in Sgija subgenre (flag accordingly) |
| 4 | **Track Structure** | Build-and-layer arrangement, typically 5–8 minutes, DJ-oriented. Absence of this = Afropiano hybrid, not core |

---

## Genre Classification Decision Tree

### Step 1 — BPM Check
- **108–118 BPM** → Continue to Step 2
- **120–130 BPM** → Likely Afro-house/Afro-tech. Skip unless log drum + piano lead both present → tag `afropiano`
- **Under 105 BPM** → Kwaito or Afropop → `exclude`

### Step 2 — Harmonic Check
- **Electric piano or jazzy synth present** → Continue to Step 3
- **No piano** → Continue, but flag as `sgija` subgenre variant

### Step 3 — Log Drum Check
- **Syncopated FM log drum present as lead/melodic voice** → Continue to Step 4
- **No log drum** → `exclude` (Afro-house or Deep House)

### Step 4 — Structure Check
- **5:00+ minutes, build-and-layer, instrumental sections** → Tag: `amapiano`
- **Under 4:00, verse-chorus, radio-ready** → Tag: `afropiano` (hybrid — include with subgenre flag, not as core Amapiano)

---

## Genre Tags (Use Exactly These in the CSV)

| Tag | Meaning |
|---|---|
| `amapiano` | Core — passes all 4 steps |
| `afropiano` | Hybrid — Amapiano production + pop/Afrobeats vocal structure (Tyla, Asake crossovers) |
| `afrobeats` | Nigerian/West African pop with or without piano elements |
| `afro-house` | African + house, four-on-the-floor kick, typically 118–130 BPM |
| `afropop` | Mainstream pop crossover (Fireboy, Tems ballads) |
| `alte` | Nigerian alternative/experimental |
| `exclude` | Gqom, Kwaito, Afro-tech, DJ mixes, snippets |

---

## Subgenre Internal Taxonomy

When tagging `amapiano`, add a `sub_style` column using these values:

| Sub-style | Characteristics | Pioneer |
|---|---|---|
| `private_school` | Polished, jazz/R&B forward, live instruments (sax, guitar, violin), smooth production | Kelvin Momo |
| `sgija` | Log drum-heavy, minimal harmonics, raw/aggressive, dancefloor-focused | Mellow & Sleazy, Mr JazziQ |
| `mozambique` | Sgija variant — undulated log drum sound, hypnotic | Mellow & Sleazy |
| `bacardi` | Heavier kicks, raw/dusty textures, street vocal chants | Pretoria origin |
| `tech_amapiano` | 120–128 BPM, four-on-the-floor kicks, techy synth arpeggios — borderline Afro-tech | International-oriented |
| `vocal` | Vocal-forward traditional structure, still long-form | Various |
| `instrumental` | DJ/producer sets, no lead vocals | Various |

---

## Boundary Rules

### Amapiano vs Afro-house
- Afro-house: straight four-on-the-floor kick, 118–125+ BPM, tribal/organic percussion leads
- Amapiano: syncopated shuffled kick, 108–118 BPM, log drum is the lead voice
- **Rule:** Log drum present but BPM > 120 and straight kick pattern → `afro-house`

### Amapiano vs Afrobeats (The "Afropiano" Problem)
- Nigerian artists adopting log drum over pop structure = **Afropiano**, not core Amapiano
- **Rule:** If track is under 4:00 with standard verse-chorus → `afropiano`
- **Rule:** If track is SA production with Nigerian vocalist but full Amapiano structure → `amapiano` (tag `region=NG`)

### The Rhythmic Anchor Rule (for genuinely ambiguous tracks)
> "If the core pulse is 112 BPM with a syncopated log drum, it is Amapiano regardless of the vocalist's nationality. If it is a 3-minute pop song with a 105 BPM Afropop groove and a log drum added for flavor, it remains Afrobeats."

---

## Canonical Artists — Ground Truth

### Core SA Amapiano (unambiguous — HIGH confidence by default)
- **Kabza De Small** — "King of Amapiano," defines the structural and melodic balance
- **DJ Maphorisa** — bridges SA Amapiano with global Afrobeats while maintaining SA sonics
- **MDU aka TRP** — credited with creating/popularizing the log drum sound
- **Kelvin Momo** — defines Private School Piano
- **Mellow & Sleazy** — defines Sgija and Mozambique
- **Mr JazziQ** — Piano Hub style, Sgija movement
- **Focalistic** — Amapiano-Hip-hop fusion
- **Major League DJz** — high-energy club Amapiano
- **Uncle Waffles** — modern club-centric standard
- **Vigro Deep** — deep, experimental, closer to house roots
- **De Mthuda** — soulful, township-rooted harmonic depth
- **Josiah De Disciple** — early pioneer, jazzy/soulful transition
- **Tyler ICU** — large melodic anthems at 112 BPM
- **Young Stunna** — vocal Amapiano
- **Daliwonga** — vocal Amapiano
- **DBN Gogo** — DJ/high-energy
- **Ami Faku** — vocal/melodic crossover
- **Mas Musiq** — established producer

### Nigerian/Cross-National (mostly Afropiano — verify per track)
- **Asake** — select tracks with SA production qualify; most = Afropiano
- **Kcee** — Ojapiano-era tracks; verify structure
- **Oxlade** — Afropiano hybrid
- **Zinoleesky** — Afropiano hybrid
- **Seyi Vibez** — select tracks; verify BPM and structure

---

## Test Case Validation

| Track | Artist | Tag | Reasoning |
|---|---|---|---|
| Sponono | Kabza De Small ft. Wizkid, Burna Boy | `amapiano` | 112 BPM, 6:00+ min, SA production, log drum lead — regardless of Nigerian features |
| Tshwala Bam | TitoM & Yuppe | `amapiano` | Full SA structure, syncopated log drum lead, Zulu lyrics — often wrongly tagged Afrobeats on UK/NG charts |
| Water | Tyla | `afropiano` | Log drum present but 3:20 radio structure, R&B vocal format — lacks DJ-oriented build |
| Jerusalema | Master KG | `afro-house` | Straight four-on-the-floor, 120+ BPM, no log drum |
| Bheba | Shaunmusiq & Ftears | `amapiano` (Sgija) | 112 BPM, raw log drum lead, minimal piano — absence of piano doesn't exclude it |
| Ojapiano | Kcee | `afropiano` | Nigerian artist, Amapiano-influenced production, pop structure |

---

## Edge Cases Log
*Add ambiguous tracks here during tagging rather than guessing*

| Track | Artist | Reason for Ambiguity | Decision |
|---|---|---|---|
| *(add here)* | | | |

---

## What This Is Not For
This criteria is for **this dataset only** and is deliberately opinionated for consistency.
It is not a universal definition of Amapiano. The goal is consistency within one research corpus,
not settling a genre debate.

All decisions should be traceable to one of the rules above. If a track can't be resolved
by the decision tree, add it to the Edge Cases Log.
