# Technické zabezpečení a soukromí

Jak Metricord chrání vaše data na infrastrukturní úrovni.

## 1. Autentizace a Autorizace

- **Discord OAuth2:** Přihlašování probíhá výhradně přes oficiální bránu Discordu. Metricord nikdy neukládá vaše heslo.
- **Stateful Sessions:** Sezení jsou uložena v Redisu s expirací 24 hodin a jsou podepsána kryptografickým klíčem `SECRET_KEY`.
- **Role-Based Access (RBAC):** Přístup k datům serveru je povolen pouze uživatelům s oprávněním `Manage Server`.

## 2. Životní cyklus dat

| Typ dat | Uložení | Expirace |
| :--- | :--- | :--- |
| **Session Tokeny** | Redis (Keys) | 24 Hodin |
| **Uživatelské Info** | Redis (Hash) | 7 Dní |
| **Analytické eventy** | Redis (Sorted Sets) | Neomezeně / Do smazání |

## 3. Ochrana proti útokům

- **Rate Limiting:** Bot i API mají vestavěné omezovače požadavků.
- **CORS:** Dashboard omezuje požadavky pouze na povolené domény.
- **XSS Protection:** Všechny uživatelské vstupy v dashboardu jsou escapovány.

## 4. Infrastruktura

Aplikace běží v oddělených Docker kontejnerech. Redis není přístupný z vnější sítě a komunikuje pouze s interními službami bota a dashboardu.

## 5. Modelování hrozeb a Mitigace

- **SQL Injection:** Nulové riziko (systém nepoužívá SQL).
- **Token Theft:** Session tokeny jsou chráněny příznaky `HttpOnly` a `SameSite=Lax`.
- **Data Isolation:** Data každého serveru jsou v Redisu oddělena prefixy klíčů. API striktně kontroluje oprávnění k přístupu k danému prefixu.

## 6. Šifrování

Veškerá komunikace mezi botem, dashboardem a Discord API probíhá přes **TLS 1.3**. Citlivá data v `.env` jsou při běhu v Dockeru uložena v paměti RAM a nejsou zapisována do logů.
