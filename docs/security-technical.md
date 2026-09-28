# Technické zabezpečení a soukromí

Jak CommunityMetrics chrání vaše data na infrastrukturní úrovni.

## 1. Autentizace a Autorizace

- **Discord OAuth2:** Přihlašování probíhá výhradně přes oficiální bránu Discordu. Generuje se unikátní stavový parametr (State) pro zamezení CSRF útoků při přihlašování.
- **Cookie-based Sessions:** Sezení jsou uložena v podepsaných cookie pomocí `itsdangerous` (`SameSite=Lax`). V produkci se nastavuje `https_only=True`. Expirace je konfigurována přes `SESSION_EXPIRY_HOURS`.
- **CSRF Ochrana:** Všechny stavotvorné požadavky API (`POST`, `DELETE`) vyžadují předložení kryptograficky bezpečného CSRF tokenu, který je kontrolován proti timing útokům pomocí `secrets.compare_digest` v `web/backend/security.py`. Token se předává v hlavičce `X-CSRF-Token` nebo jako pole `csrf_token` ve formuláři.
- **X-API-Key Autentizace:** Pro externí klienty existuje autentizace pomocí API klíčů (prefix `mtr_`), validovaných přes SHA-256 digest.
- **Role-Based Access (RBAC):** Backend rozlišuje dvě úrovně: globálního systémového administrátora (`require_admin`, používá se jen pro `/api/logs` a změnu globálního bot tokenu) a per-komunitní oprávnění (`view_stats`, `manage_settings`, `export_data`, ...), které mají automaticky administrátoři daného Discord serveru a jinak jen team memberové, kterým bylo oprávnění výslovně uděleno v Nastavení → Tým.

## 2. Životní cyklus dat

| Typ dat | Uložení | Expirace |
| :--- | :--- | :--- |
| **Session data** | Podepsané cookie (`itsdangerous`) | `SESSION_EXPIRY_HOURS` (výchozí 24h) |
| **Uživatelské Info** | Redis (Hash `user:info:{uid}`) | 7 Dní |
| **Analytické eventy** | Redis (Sorted Sets) | Konfigurovatelné (výchozí 90 dní, `EVENT_RETENTION_DAYS`) |

## 3. Ochrana proti útokům

- **Rate Limiting:** Aplikován omezený tok pro citlivé endpointy a omezovače Discord API.
- **CORS:** Omezení hlaviček na povolené domény v produkční konfiguraci.
- **Ochrana SSRF (Server-Side Request Forgery):** Jak při PŘIDÁVÁNÍ integrace Discourse, tak při KAŽDÉM běhu periodické synchronizace na pozadí (`scripts/discourse_sync.py`, každých 300 s) se přes sdílenou funkci `assert_safe_discourse_url` (`shared/net_security.py`) provádí striktní filtrace IP adres s cílem blokovat `localhost`, privátní IP, link-local adresy a metadata služby (např. `169.254.169.254`). Díky opakované validaci při každém požadavku je pokrytý i útok typu DNS Rebinding (změna DNS záznamu domény po přidání instance).

## 4. Infrastruktura

Aplikace běží v oddělených Docker kontejnerech. Redis není přístupný z vnější sítě a komunikuje pouze s interními službami bota a dashboardu.

## 5. Modelování hrozeb a mitigace

- **Injection útoky:** Datový model spoléhá výhradně na Redis struktury a ORM rozhraní. Aplikace nepoužívá klasické relační databáze s přímými SQL dotazy.
- **Konfigurace a tajné klíče:** Proměnné prostředí jsou parsovány s využitím `pydantic-settings` do aplikační logiky, nesdílejí se v běžných logovacích zprávách.
- **Data Isolation:** Data serverů jsou v Redis striktně oddělena prefixy klíčů (např. `events:msg:{guild_id}:*`).

## 6. Šifrování a komunikace

Veškerá produkční komunikace s klienty a Discord API je určena pro provoz za reverzní proxy podepsanou certifikátem pro TLS 1.2/1.3. Citlivé klíče a secrety v `.env` se do aplikace předávají jako environment variables, nejsou ukládány do kódu (hardcoding). `docker-compose.prod.yml` předává do kontejneru `web-dashboard` všechny proměnné potřebné pro OAuth2 přihlášení (`DISCORD_CLIENT_ID`, `DISCORD_CLIENT_SECRET`, `DISCORD_REDIRECT_URI`, `DASHBOARD_SECRET_KEY`, `DASHBOARD_ACCESS_TOKEN`, `BOT_TOKEN`, `EVENT_RETENTION_DAYS`), viz [Nasazení do produkce](/deployment).
