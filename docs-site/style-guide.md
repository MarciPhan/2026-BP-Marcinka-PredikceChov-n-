# Metricord Style Guide (Standardy kódu)

Pokud chcete přispět do jádra Metricord, dodržujte tyto technické a estetické standardy.

## 1. Python Backend (PEP8 + Async)

- **Typování:** Každá funkce musí mít `type hints`.
- **Docstrings:** Používejte Google styl dokumentace.
- **Asynchronita:** Nikdy nepoužívejte blokující `time.sleep()` nebo `requests`. Vždy `asyncio.sleep()` a `httpx`.

## 2. Frontend (Glassmorphism CSS)

Nepoužívejte ad-hoc barvy. Vždy využívejte definované CSS proměnné:

```css
.my-new-card {
  background: var(--bg-secondary);
  backdrop-filter: blur(10px);
  border: 1px solid var(--glass-border);
}
```

## 3. Redis Naming

Klíče v Redisu musí následovat vzor `[domain]:[subdomain]:[guild_id]:[key]`.

- **Špatně:** `user123_stats`
- **Správně:** `stats:user:123456789:msg_count`

## 4. UI Component Library

### Standardní Karta (Card)
```html
<div class="glass-card">
  <h4>Titulek</h4>
  <p>Obsah karty...</p>
</div>
```

### Primární Tlačítko (Button)
```html
<button class="btn-primary">Klikni zde</button>
```

### Datová Tabulka (Table)
```html
<table class="docs-table">
  <thead>...</thead>
  <tbody>...</tbody>
</table>
```
