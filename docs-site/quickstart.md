# Průvodce rychlým startem

S Metricordem získáte první analytické přehledy během 5 minut. Tento průvodce vás provede nezbytnými kroky od autorizace až po první predikce.

::: tip Předpoklady
- Discord účet s oprávněním **Manage Server** na cílovém serveru.
- Bot vytvořený v [Discord Developer Portalu](https://discord.com/developers/applications) s vygenerovaným tokenem.
:::

## 1. Vytvoření bota v Discord Portalu

Pokud ještě nemáte bota, vytvořte si jej:

1.  Přejděte na [Discord Developer Portal](https://discord.com/developers/applications).
2.  Klikněte na **New Application** a pojmenujte ji (např. „Metricord").
3.  V sekci **Bot** klikněte na **Add Bot** a zkopírujte si `BOT_TOKEN`.
4.  V sekci **OAuth2 → URL Generator** zaškrtněte scope `bot` a `applications.commands`.

> [!IMPORTANT]
> V sekci **Bot → Privileged Gateway Intents** musíte zapnout:
> - **Presence Intent:** Pro sledování online stavu členů.
> - **Server Members Intent:** Pro sledování příchodů, odchodů a synchronizaci profilů.
> - **Message Content Intent:** Pro výpočet délky zpráv a aktivity.

## 2. Pozvání bota na server

Pomocí vygenerované OAuth2 URL pozvěte bota na váš Discord server. Doporučená oprávnění:

| Oprávnění | Důvod |
| :--- | :--- |
| **View Channels & Read Messages** | Analýza textové aktivity. |
| **Read Message History** | Nutné pro zpětný import dat (Backfill). |
| **Connect** | Sledování účasti v hlasových kanálech. |
| **Use Application Commands** | Registrace slash příkazů. |
| **Manage Roles** *(volitelné)* | Automatické přidělování rolí za aktivitu. |

## 3. Instalace a spuštění

Metricord můžete spustit lokálně nebo přes Docker. Vyberte si cestu, která vám vyhovuje:

::: code-group

```bash [Lokální spuštění (doporučeno pro vývoj)]
# 1. Klonování
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-
cd 2026-BP-Marcinka-PredikceChov-n-

# 2. Konfigurace
cp .env.example .env
# Otevřete .env a vyplňte BOT_TOKEN a další proměnné

# 3. Spuštění (bot + dashboard + docs jedním příkazem)
chmod +x start.sh
./start.sh
```

```bash [Docker Compose (doporučeno pro produkci)]
# 1. Klonování
git clone https://github.com/MarciPhan/2026-BP-Marcinka-PredikceChov-n-
cd 2026-BP-Marcinka-PredikceChov-n-

# 2. Konfigurace
cp .env.example .env
# Otevřete .env a vyplňte BOT_TOKEN a další proměnné

# 3. Vytvoření Docker sítě (pouze poprvé)
docker network create botnet

# 4. Spuštění celého stacku
docker-compose up -d --build
```

:::

### Ověření úspěšného spuštění

Po spuštění by měly běžet tři služby:

| Služba | URL / Kontrola | Co dělá |
| :--- | :--- | :--- |
| **Bot** | `redis-cli GET bot:heartbeat` | Sběr událostí z Discordu |
| **Dashboard** | `http://localhost:8092` | Webové rozhraní s grafy |
| **Dokumentace** | `http://localhost:5173` | Tato dokumentace (VitePress) |

> [!TIP]
> Pokud bot neodpovídá na příkazy, spusťte v Discord chatu `*sync` pro registraci slash příkazů.

## 4. Přihlášení k dashboardu

1.  Přejděte na `http://localhost:8092` (nebo vaši produkční doménu).
2.  Klikněte na **Login** a autorizujte se přes Discord OAuth2.
3.  Metricord automaticky zobrazí servery, kde máte právo **Manage Server**.
4.  Vyberte cílový server z postranního panelu.

## 5. První synchronizace dat (Backfill)

Bot standardně sbírá data od momentu svého připojení. Pokud chcete vidět historické trendy okamžitě, proveďte zpětný import:

```
/activity backfill days:30
```

Bot začne indexovat historii zpráv a audit log. Proces probíhá asynchronně na pozadí a nezpomaluje ostatní funkce bota.

> [!WARNING]
> Backfill je náročný na Discord API. U velkých serverů (10 000+ zpráv) může trvat i desítky minut. Podrobnosti viz [Backfill historických dat](/backfill).

## 6. Kalibrace XP systému

Přizpůsobte metriky dynamice své komunity v dashboardu (sekce **Settings**) nebo přímo přes Redis:

| Parametr | Výchozí | Popis |
| :--- | :--- | :--- |
| **Base XP** | 5 | Počet bodů za jednu standardní zprávu. |
| **Voice Multiplier** | 5/min | XP za minutu strávenou ve voice kanálu. |
| **Length Bonus** | 15–50 | XP navýšení za dlouhé a komplexní zprávy. |
| **Cooldown** | 60 s | Časové okno pro anti-spam ochranu. |

```bash
# Příklad úpravy vah přes redis-cli
redis-cli HSET config:xp:weights msg_short 1 msg_medium 5 msg_long 15
redis-cli INCR config:weights_version
```

## Časový plán sběru dat

Analytika Metricord pracuje v několika cyklech. Očekávejte tyto milníky:

| Časový horizont | Co uvidíte | Účel |
| :--- | :--- | :--- |
| **Ihned** | Real-time Heatmapa | Okamžitý přehled o špičce aktivity. |
| **24 hodin** | DAU (Denní aktivita) | Porovnání dnešní aktivity s předchozím dnem. |
| **7 dní** | Churn Predictions | První odhady pravděpodobnosti odchodu členů. |
| **30 dní** | Kaplan-Meier | Kompletní křivky přežití a dlouhodobá retence. |

## Co dál?

::: info Doporučený postup po instalaci
1. **[Uživatelská příručka](/user-guide)** — Naučte se základní příkazy a XP systém.
2. **[Průvodce pro moderátory](/moderators)** — Interpretujte metriky a pracujte s predikcemi.
3. **[Osvědčené postupy](/best-practices)** — 30denní plán pro maximální využití analytiky.
4. **[Architektura systému](/architecture)** — Pochopte, jak Metricord funguje pod kapotou.
:::
