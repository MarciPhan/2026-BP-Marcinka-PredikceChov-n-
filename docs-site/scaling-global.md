# Global Scaling & High Availability

Průvodce škálováním Metricord pro velké komunity (50k+ členů) a zajištění vysoké dostupnosti pro produkční nasazení.

## 1. Redis Sentinel (High Availability)

Pro zajištění běhu i při výpadku hlavního databázového uzlu využijte Redis Sentinel. Ten automaticky zvolí nového Mastera, pokud hlavní uzel selže.

```yaml
# sentinel.conf
sentinel monitor mymaster 127.0.0.1 6379 2
sentinel down-after-milliseconds mymaster 5000
sentinel failover-timeout mymaster 60000
sentinel parallel-syncs mymaster 1
```

### Topologie

| Node | Role | Data |
| :--- | :--- | :--- |
| **redis-master** | Master (read/write) | Bot zapisuje sem |
| **redis-replica-1** | Replica (read-only) | Dashboard čte odtud |
| **redis-replica-2** | Replica (read-only) | Záloha pro failover |
| **sentinel-1,2,3** | Monitor | Sledují master, failover |

## 2. Redis Cluster (Sharding)

Pro servery s miliony eventů:
- Data jsou rozdělena do **16,384 hash slotů**.
- Klíče s guild ID jako prefixem zajišťují, že data jednoho serveru jsou na stejném uzlu (hash tagy: `{guild_id}`).
- Doporučení: 3+ master nodes, každý s 1 replikou.

```bash
# Vytvoření clusteru
redis-cli --cluster create \
    node1:6379 node2:6379 node3:6379 \
    node4:6379 node5:6379 node6:6379 \
    --cluster-replicas 1
```

## 3. Read/Write Splitting

Oddělte zapisující a čtecí klienty:
- **Bot (Write):** Připojuje se k Masteru.
- **Dashboard (Read):** Připojuje se k Replikám.
Tím zajistíte nulový dopad analytiky na výkon bota.

## 4. Event Thinning

Pro servery s extrémní aktivitou:
- **Voice sampling:** Změna frekvence trackingu z 1 minuty na 5 minut.
- **Message aggregation:** Agregace zpráv do 5minutových bucketů.
- **TTL na events:** Expirace starých Sorted Setů po 90 dnech.

```bash
redis-cli EXPIRE "events:msg:guild_id:user_id" 7776000  # 90 dní
```

## 5. Multi-Node Deployment

| Region | Komponenty | Účel |
| :--- | :--- | :--- |
| **EU-Central** | Redis Master + Bot Primary + Dashboard | Hlavní uzel |
| **US-East** | Redis Replica + Dashboard Read-Only | Nižší latence pro USA |

::: info Architektonický tip
Pro globální škálování je klíčová latence k Redisu. Bot i Redis musí být v rámci stejného regionu. Dashboard repliky mohou být geograficky distribuované.
:::

## 6. Monitoring velkých instalací

```bash
# Sledování Redis metrik v reálném čase
redis-cli --stat

# Sledování pomalých příkazů
redis-cli SLOWLOG GET 10
```
