# Engagement Score

## Principy

1. **Fakta místo verdiktů.** Aktivita, odpovědi a reakce jsou podklady; vhodnost pro roli určuje člověk.
2. **Korelace není příčina.** Událost před odchodem se popisuje jako časová posloupnost.
3. **Modularita.** Analýza žádostí o pomoc je vypnutá, dokud správce neurčí relevantní kanály.
4. **Minimalizace dat.** Obsah zpráv není uložen.

## Redis struktury

Systém ukládá data strukturovaně, převážně pomocí map (hash) pro data a množin (zset/set) pro indexaci a časové dotazy.

### Entity a metadata (Hashe)
- `health:message:{guild}:{message}` – metadata zprávy (reakce, typ);
- `health:help:{guild}:{message}` – detailní stav žádosti o pomoc;
- `health:mod_event:{guild}:{event}` – kontext auditní události (ban, kick...);
- `health:mod_pair:{guild}:{target}:{moderator}` – historie interakcí konkrétní dvojice;
- `health:departure:{guild}:{departure}` – časový a datový kontext odchodu člena;
- `health:event:{guild}:{event}` – definice plánované události;
- `health:role_review:{guild}:{user}` – ruční stanovisko a poznámky týmu;
- `cfg:health:{guild}` – konfigurace health modulů.

### Indexy a časové řady (Sorted Sety a Sety)
- `health:user_messages:{guild}:{user}` – časová osa ID zpráv uživatele;
- `health:mod_events:moderator:{guild}:{user}` – časová osa zásahů moderátora;
- `health:mod_events:target:{guild}:{user}` – časová osa incidentů uživatele;
- `health:help:all:{guild}` – index všech help tiketů pro časové dotazy;
- `health:departures:{guild}` – index odchodů pro procházení v čase;
- `health:events:{guild}` – seznam všech sledovaných událostí na serveru;
- `health:event:interested:{guild}:{event}` – uživatelé se zájmem o událost;
- `health:event:attended:{guild}:{event}` – uživatelé potvrzení u události.

### API struktury
- `api:key:{digest}` – detaily o vydaném API klíči (oprávnění, stav);
- `api:keys:guild:{guild}` – seznam API klíčů pro daný server;
- `api:rate:{digest}:{bucket}` – rate-limiting pro veřejné API.
## Omezení

- Discord neposkytuje spolehlivou informaci, zda uživatel skutečně četl kanál.
- Fyzickou účast na akci nelze zjistit automaticky; implementace měří hlasovou účast u Discord Scheduled Events.
- Reakce na dotaz znamená pouze potvrzení, nikoli vyřešení.
- Historický odchod členů nelze zpětně rekonstruovat bez dříve uložených member-remove událostí.
