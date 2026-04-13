# Security Hardening (Zabezpečení infrastruktury)

Metricord je bezpečný na aplikační úrovni, ale produkční server vyžaduje dodatečné zabezpečení na úrovni OS, sítě a kontejnerů.

## 1. Firewall (UFW / firewalld)

Povolte pouze nezbytné porty. **Redis nesmí být nikdy přístupný zvenčí.**

```bash
# Ubuntu / Debian (UFW)
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

::: danger Kritické
Port `6379` (Redis) nesmí být přístupný z internetu. V Dockeru komunikuje Redis pouze přes interní síť.
:::

## 2. Redis zabezpečení

### 2.1 Heslo (requirepass)
V `redis.conf` nastavte `requirepass` a stejné heslo v `.env`:
`REDIS_URL=redis://:heslo@localhost:6379/0`

### 2.2 ACL (Redis 6.0+)
Vytvořte oddělené účty s minimálními oprávněními:
```text
user bot on >heslo ~events:* ~stats:* ~hll:* +@all -@admin
user dashboard on >heslo ~stats:* ~hll:* +get +hget +zrange +pfcount
```

## 3. Docker zabezpečení

- **Non-root user:** Spouštějte kontejnery pod neprivilegovaným uživatelem.
- **Read-only filesystem:** Nastavte `read_only: true` v docker-compose.
- **Resource limits:** Omezte paměť a CPU pro každý kontejner (např. `memory: 512M`).

## 4. SSH zabezpečení

V `/etc/ssh/sshd_config` nastavte:
- `PermitRootLogin no`
- `PasswordAuthentication no` (používejte klíče)
- `AllowUsers metricord`

## 5. Fail2Ban

Ochrana proti bruteforce útokům:
```bash
sudo apt install fail2ban
```
Aktivujte maily pro `sshd` a `nginx-http-auth`.

## 6. Bezpečnostní checklist

- [ ] Redis port 6379 není přístupný z internetu
- [ ] Redis má nastaveno silné heslo
- [ ] `.env` má oprávnění `600`
- [ ] SSH nepovoluje root login ani heslo
- [ ] Firewall povoluje pouze 22, 80, 443
- [ ] Fail2Ban aktivní
- [ ] SSL certifikát aktivní (Certbot)

::: info Audit
Pravidelně kontrolujte přístupy přes `redis-cli ACL LIST` a logy Fail2Ban přes `sudo fail2ban-client status sshd`.
:::
