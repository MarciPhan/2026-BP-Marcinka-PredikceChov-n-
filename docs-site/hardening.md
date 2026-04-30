# Zabezpečení infrastruktury (Hardening)

Aplikace Metricord je bezpečná již na úrovni kódu, ale pro provoz v produkci musíte zajistit ochranu na úrovni operačního systému, sítě a kontejnerů. Tento průvodce vás provede kroky pro minimalizaci útočné plochy vašeho serveru.

## Konfigurace síťového firewallu (UFW)

Povolte pouze porty nezbytné pro provoz. Veškerou ostatní komunikaci zablokujte.

> [!CAUTION]
> **Port 6379 (Redis) nesmí být nikdy přístupný z internetu.** V rámci Dockeru komunikuje Redis pouze přes interní virtuální síť.

Pro nastavení firewallu na systémech Ubuntu/Debian použijte nástroj UFW:

```bash
# Nastavení výchozích pravidel
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Povolení služeb
sudo ufw allow 22/tcp    # SSH přístup
sudo ufw allow 80/tcp    # HTTP pro Certbot
sudo ufw allow 443/tcp   # HTTPS pro dashboard

# Aktivace firewallu
sudo ufw enable
```

## Zabezpečení databáze Redis

### Nastavení silného hesla
V souboru `redis.conf` aktivujte parametrem `requirepass` silné heslo. Stejné heslo pak zadejte do proměnné `REDIS_URL` v souboru `.env`:

```text
REDIS_URL=redis://:vase_silne_heslo@localhost:6379/0
```

### Řízení přístupu pomocí ACL (Redis 6.0+)
Místo jednoho generálního hesla vytvořte oddělené uživatelské účty s minimálními oprávněními (Principle of Least Privilege):

```text
# Účet pro bota (zápis eventů a čtení statistik)
user bot on >heslo ~events:* ~stats:* ~hll:* +@all -@admin

# Účet pro dashboard (pouze čtení statistik)
user dashboard on >heslo ~stats:* ~hll:* +get +hget +zrange +pfcount
```

## Zabezpečení SSH přístupu

Upravte konfigurační soubor `/etc/ssh/sshd_config` pro zamezení útokům hrubou silou:

1.  Zakažte přihlášení uživatele root: `PermitRootLogin no`.
2.  Zakažte přihlášení heslem a vyžadujte SSH klíče: `PasswordAuthentication no`.
3.  Omezte přihlášení pouze na konkrétního uživatele: `AllowUsers metricord`.
4.  Restartujte službu: `sudo systemctl restart ssh`.

## Zabezpečení kontejnerů (Docker Hardening)

Pro maximální izolaci aplikací v produkci využijte tyto pokročilé techniky:

-   **Neprivilegovaný uživatel:** V Dockerfile definujte `USER 1000`. Aplikace nesmí běžet pod rootem uvnitř kontejneru.
-   **Souborový systém pouze pro čtení:** V `docker-compose.yml` nastavte `read_only: true`. Pro dočasné soubory využijte `tmpfs`.
-   **Omezení systémových volání (Seccomp):** Vytvořte Seccomp profil pro omezení povolených syscallů (např. `read`, `write`, `socket`).

### Ukázka konfigurace v `docker-compose.yml`:

```yaml
services:
  discord-bot-primary:
    security_opt:
      - seccomp:seccomp-profile.json
    read_only: true
    tmpfs:
      - /tmp
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '1.0'
```

> [!WARNING]
> Před nasazením Seccomp profilu v ostrém provozu důkladně otestujte stabilitu bota. Příliš restriktivní profil může způsobit pád aplikace při legitimním systémovém volání.

## Soulad s předpisy a ochrana soukromí

Metricord implementuje principy **Privacy by Design** pro soulad s nařízením GDPR:

1.  **Minimalizace dat:** Neukládáme obsah zpráv, pouze metadata potřebná pro analytiku (čas, délka, metadata autora).
2.  **Právo na zapomnění:** Příkaz `/gdpr delete` okamžitě a nevratně odstraní všechny záznamy o uživateli ze všech Redis struktur (`Sorted Sets`, `Hashes`).
3.  **Šifrování komunikace:** Veškerý provoz mezi prohlížečem a dashboardem musí být šifrován pomocí TLS/SSL (HTTPS).

## Kontrolní seznam (Production Readiness)

| Oblast | Doporučení | Stav |
| :--- | :--- | :--- |
| **Síť** | Firewall (UFW) blokuje vše kromě 22, 80, 443. | - |
| **Databáze** | Redis vyžaduje silné heslo a používá ACL profily. | - |
| **Server** | SSH hesla jsou vypnutá, používají se pouze klíče. | - |
| **Docker** | Kontejnery běží bez root oprávnění s limity RAM. | - |
| **SSL** | Dashboard používá platný certifikát Let's Encrypt. | - |

