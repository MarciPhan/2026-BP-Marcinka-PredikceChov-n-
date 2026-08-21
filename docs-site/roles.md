# XP systém a automatické role

Systém přiděluje zkušenostní body (XP) za aktivitu na serveru. Body se kumulují a určují úroveň uživatele, na jejímž základě bot automaticky přiřazuje Discord role.

## Výpočet XP

Každá akce prochází filtrem kvality. Systém neodměňuje pouhou přítomnost, ale smysluplnou interakci.

| Typ akce | XP | Podmínky |
| :--- | :--- | :--- |
| Krátká zpráva (< 15 znaků) | 1 | Jednoslovné reakce, emoji. |
| Standardní zpráva (15–100 znaků) | 5 | Běžná konverzace. |
| Dlouhý příspěvek (> 100 znaků) | 15–50 | Lineární nárůst s délkou, maximum 50 XP. |
| Odpověď (Reply) | +10 | Bonus za použití funkce Reply. |
| Voice aktivita | 5 / min | Mikrofon musí být aktivní (ne mute). |

### Náhodná složka (Variable Ratio Reinforcement)

Systém přidává náhodnou odchylku ±15 % ke každému XP zisku. Tato metoda zvyšuje angažovanost uživatelů a ztěžuje automatizované farmení.

## Anti-spam ochrana

| Mechanismus | Pravidlo |
| :--- | :--- |
| **Message Cooldown** | Maximálně 1 XP-profitující zpráva za 60 sekund. |
| **Duplicate Check** | Opakované odeslání stejné zprávy přiděluje 0 XP. |
| **Noční korekce** | Mezi 2:00 a 6:00 jsou body násobeny koeficientem 0,5. |

## Výpočet úrovně

Úroveň $L$ se vypočítá z celkových XP $X$ podle kvadratické funkce:

$$X(L) = 50 \cdot L^2 + 200 \cdot L + 100$$

Příklady požadovaného XP pro vybrané úrovně:

| Úroveň | Požadované XP | Odhad doby dosažení |
| :--- | :--- | :--- |
| 2 | 700 | 1–2 dny aktivní konverzace |
| 10 | 7 100 | cca 2 týdny |
| 25 | 36 350 | cca 2 měsíce |
| 50 | 135 100 | cca 6 měsíců |

## Konfigurace automatických rolí

V dashboardu propojte Discord role s konkrétními úrovněmi. Bot role přiděluje:

1. Okamžitě při dosažení nové úrovně.
2. Pravidelnou synchronizací každých 24 hodin.
3. Ručně příkazem `/activity sync_names`.

::: tip Doporučení
Nastavte 4–6 rolí na milnících (úrovně 5, 10, 25, 50, 100). Příliš mnoho rolí snižuje jejich prestiž.
:::

## Úprava vah za běhu

Váhy XP akcí lze měnit bez restartu bota:

```bash
# Přes redis-cli
redis-cli HSET config:xp:weights msg_short 1 msg_medium 5 msg_long 15

# Přes REST API
curl -X POST http://localhost:8092/admin/config/weights \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"msg_short": 1, "msg_medium": 5}'
```

Po změně vah je nutné zvýšit verzi konfigurace, aby se denní statistiky přepočítaly:

```bash
redis-cli INCR config:weights_version
```
