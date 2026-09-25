# 🧠 Roberts AI – Agent Brain (Zināšanu Bāze)

Šis repozitorijs ir **Roberts AI Aģenta** ([`angelcharge/agent`](https://github.com/angelcharge/agent)) padziļinātā zināšanu bāze (*External Domain Knowledge Base*). 

Šeit tiek glabāta uzņēmumu specifiskā dokumentācija, tehniskās specifikācijas, receptūras, likumdošanas/PVD prasības, cenu lapas un piegādātāju noteikumi, kurus aģents automātiski ielādē savā kontekstā kā **primāro patiesības avotu**.

---

## 📁 Repozitorija struktūra

Failu struktūra ir organizēta pēc uzņēmumu identifikatoriem (**`slug`**). Katram biznesa profilam atbilst atsevišķa mape:

```text
agent-brain/
├── README.md                  # Šis apraksta fails
│
├── r11/                       # Uzņēmuma/projekta 'r11' zināšanu bāze
│   ├── profile.md             # Uzņēmuma misija, zīmola balss, pamatdati
│   ├── recipes.md             # Receptūras, izejvielu proporcijas, tehnoloģiskā karte
│   ├── pvd_regulations.md     # PVD un higiēnas prasības, telpu standarti, marķējums
│   ├── suppliers.md           # Piegādātāji, iepirkuma cenas, loģistikas noteikumi
│   └── templates.md           # Oficiālās sarakstes sagataves un stils
│
├── cat_food/                  # Kaķu barības un gardumu uzņēmums (SIA T3)
│   ├── profile.md
│   └── ...
│
└── fit_food/                  # Veselīgo uzkodu uzņēmums (FitFood SIA)
    ├── profile.md
    └── ...
```

---

## 📝 Vadlīnijas failu veidošanai (cilvēkiem un citiem AI asistentiem)

Veidojot vai papildinot saturu šajā repozitorijā:

1. **Failu formāts:**
   * Tiek nolasīti visi faili ar paplašinājumu **`.md`** vai **`.markdown`**.
   * Drīkst brīvi izmantot standarta CommonMark Markdown: virsrakstus (`#`, `##`, `###`), tabulas (`| a | b |`), sarakstus, treknrakstu un koda blokus.

2. **Ieteicamie standarta failu nosaukumi:**
   * `profile.md` — uzņēmuma fons, darbības jomas, galvenie mērķi un tonis.
   * `recipes.md` vai `specifications.md` — tehnoloģiskās kartes, formulas, proporcijas, sastāvdaļu saraksti un aprēķini.
   * `pvd_regulations.md` vai `regulations.md` — PVD prasības, higiēnas normas, uzraudzības un marķējuma noteikumi.
   * `suppliers.md` vai `pricing.md` — izejvielu piegādātāji, bāzes cenas, pasūtījumu apjomi un piegādes termiņi.
   * `templates.md` — uzņēmuma specifiskās atbilžu un iesniegumu struktūras.

3. **Satura stils:**
   * Rakstiet faktiski, skaidri un precīzi. Izvairieties no liekvārdības.
   * Skaitļus, proporcijas un procentus norādiet nepārprotami (piemēram: `Liellopu gaļa: 45% (45 kg uz 100 kg partiju)`).
   * Šī informācija tieši ietekmē AI ģenerētos aprēķinus un oficiālos e-pastus iestādēm.

---

## ⚡ Kā aģents izmanto šo repozitoriju?

1. **Automātiska ielāde kontekstā:**
   * Kad aģents strādā ar konkrētu uzņēmumu (piemēram, aktīvs profils `r11`), tas caur GitHub Contents API automātiski ielādē visus šīs mapes `.md` failus.
   * Viss saturs tiek ievietots tieši Gemini modeļa sistēmas uzvedības promptā kā uzņēmuma patiesības avots.

2. **Kešatmiņa un ātrdarbība:**
   * Aģents uztur lokālu kešatmiņu ar 15 minūšu TTL, lai ikdienas sarakstē neradītu tīkla aizturi un netērētu GitHub API limitus.

3. **Telegram komandas tūlītējai pārvaldībai:**
   * **`/brain`** — parāda sarakstu ar šobrīd aktīvajam uzņēmumam ielādētajiem failiem, to apjomiem un sinhronizācijas statusu.
   * **`/sync_brain`** (arī `sinhronizē brain`) — tūlītēji nolasa jaunākās izmaiņas no `main` zara bez gaidīšanas.

---

## 🤝 Paplašināšana un jaunu uzņēmumu pievienošana

Lai pievienotu jaunu uzņēmumu zināšanu bāzei:
1. Pārliecinieties par uzņēmuma koda nosaukumu (`slug`), kas reģistrēts aģenta sistēmā (to var apskatīt ar `/contexts`).
2. Izveidojiet jaunu mapi ar šo pašu koda nosaukumu: `/<jaunais_slug>/`.
3. Pievienojiet nepieciešamos `.md` failus un iecommitējiet `main` zarā.
4. Telegram čatā izpildiet `/sync_brain`.
