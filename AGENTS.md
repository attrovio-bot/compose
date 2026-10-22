# Dev-Local Stack Notes

## Stack
- **Compose file**: `compose-dev-local.yaml` (branch `mario-local`)
- **Tailscale IP**: `100.87.231.127`
- **No Cloudflare/HTTPS/.uk domains** – tutto via HTTP su Tailscale IP

## Immagini Custom
- `gateway-iam-patched:latest` — built da `docker-builds/gateway-iam/Dockerfile`
  - Patches `application-dev.yaml`: `issuer-uri`, `redirect-uri` → `http://100.87.231.127:8081/realms/measurestream-dev`
  - Patches `HomeController.class` bytecode: `https://dev.christiandellisanti.uk` e `https://www.christiandellisanti.uk` → `http://100.87.231.127:8080`
- `frontend-patched:latest` — built da `docker-builds/frontend/Dockerfile`
  - Patches JS bundle: URL sostituzioni + fix `realm_access` safety

## Fix Fatti

### 1. Gateway IAM — JAR patching
- `docker-builds/gateway-iam/patch-jar.py`: modifica YAML e bytecode via Python
- `docker-builds/gateway-iam/Dockerfile`: multi-stage build (python:3-alpine per patch, JRE base per run)
- **Risultato**: login OIDC funzionante su `http://100.87.231.127:8080`

### 2. Frontend — realm_access safety
- `docker-builds/frontend/patch-js.py`: trasforma `*.principal.claims.realm_access.roles.includes("app-admin")` in `*.principal.claims?.realm_access?.roles?.includes("app-admin")??false` usando regex (gestisce nomi variabili che cambiano tra build)
- **Perché**: se il token ID non ha `realm_access.roles`, il JS crashava silenziosamente e l'app rimaneva sulla landing page
- **Risultato**: anche se `claims.realm_access` è `undefined`, il ruolo diventa `"USER"` invece di crashare

### 3. Calibrator-manager — issuer-uri
- Aggiunto env var in `compose-dev-local.yaml`:
  `SPRING_SECURITY_OAUTH2_RESOURCESERVER_JWT_ISSUER_URI: "http://100.87.231.127:8081/realms/measurestream-dev"`
- **Prima**: hardcoded `https://auth.christiandellisanti.uk/realms/measurestream` nel JAR → 530
- **Risultato**: servizio risolve correttamente OpenID configuration

### 4. Sensor-manager — issuer-uri
- Stesso fix: aggiunto `SPRING_SECURITY_OAUTH2_RESOURCESERVER_JWT_ISSUER_URI` a sensor-manager
- **Prima**: hardcoded `https://auth.christiandellisanti.uk/realms/measurestream-dev` → 530

### 5. Sensor-manager — template path e template mancante
- **Problema**: `GET /API/controlunits` → 500 `java.lang.IllegalArgumentException: Template for humidity_hpp845e not found`
- **Causa**: volume mount in `compose-dev-local.yaml` puntava a `/home/mattrovio/templates/sensor-templates` (vuoto). I template veri erano in `./templates/sensor-templates/`.
- **Fix**:
  - Modificato volume mount da `/home/mattrovio/templates/sensor-templates:/app/templates:ro` a `./templates/sensor-templates:/app/templates:ro` (`compose-dev-local.yaml:65`)
  - Creati template mancanti in `templates/sensor-templates/`:
    - `humidity_hpp845e.json` — sensore umidità HPP845E
    - `pressure_ms5837.json` — sensore pressione MS5837
    - `accelerometer_lsm6dsm.json` — accelerometro LSM6DSM
  - **Nota**: i file devono avere estensione `.json` (il codice cerca `<modelName>.json`)

### 6. DCC Service — chiavi di firma mancanti
- **Problema**: sign/verify return 200 ma PDF e XML rimangono `valid: false`, nessun download. Nei log: `[ERROR] Signing/Verification failed: /app/keys/private_key.pem — java.nio.file.NoSuchFileException`
- **Causa**: volume mount `~/keys:/app/keys:ro` puntava a `/home/mario/keys/` che era **vuoto**. Le chiavi reali sono in `/home/mario/backend/sign/keys/` (generate da `generate_keys.py` e `create_cert.py`).
- **Fix**: cambiato volume mount in `compose-dev-local.yaml:188` da `~/keys:/app/keys:ro` a `/home/mario/backend/sign/keys:/app/keys:ro`
- **File richiesti**: `private_key.pem` (RSA 2048-bit PKCS#8), `certificate.pem` (X.509 self-signed)
- **Per rigenerare**: `cd /home/mario/backend/sign && python generate_keys.py && python create_cert.py`

### 7. DCC Service — `/dcc-service/api/status` → 404
- **Causa**: il gateway inoltra `/dcc-service/api/status` → `StripPrefix=1` → `/api/status` su dcc-service, ma il dcc-service non espone un endpoint `/api/status`
- **Nota**: gli endpoint pubblici del dcc-service sono sotto `/api/public/` (route senza TokenRelay nel gateway). Se serve uno status check, usare `/api/public/health` (ma via gateway richiede auth perché passa dalla route `dcc-service-proxy` con TokenRelay)
- **Fix temporaneo**: N/A — dipende dal frontend se questo endpoint è necessario

## Keycloak Setup
- **Realm**: `measurestream-dev`
- **Client**: `gateway-dev` (secret: `0DoNSj76OjIZEE5ISq6bah1bbMznOQDT`)
- **Ruolo**: `app-admin` (assegnato a `admin`)
- **Protocol Mapper**: `realm-roles-realm-access` sul client `gateway-dev`
  - Aggiunge `realm_access.roles` a ID token, access token, userinfo
- `directAccessGrantsEnabled`: `false` (disabilitato dopo test)

## Routing (gateway-iam, profile `dev`)
| Path | Backend | IP |
|---|---|---|
| `/API/nodes/**`, `/API/measurementunits/**`, `/API/controlunits/**` | sensor-manager | `172.20.0.10:8080` |
| `/API/measures/**` | measure-manager | `172.20.0.11:8080` |
| `/API/calibrator/**` | calibrator-manager | `172.20.0.15:8080` |
| `/api/dcc/**`, `/api/mus/**` | dcc-service | `172.20.0.14:8080` |
| `/ui/**` | frontend | (nginx:80) |

## Comandi Utili
```bash
# Build gateway-iam patched
docker build -t gateway-iam-patched -f docker-builds/gateway-iam/Dockerfile docker-builds/gateway-iam/

# Build frontend patched
docker build -t frontend-patched -f docker-builds/frontend/Dockerfile docker-builds/frontend/

# Restart stack
docker compose -f compose-dev-local.yaml up -d

# Check logs
docker compose -f compose-dev-local.yaml logs --tail=50 <service>
```
