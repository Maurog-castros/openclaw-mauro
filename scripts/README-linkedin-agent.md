# Agente LinkedIn (OpenClaw)

Automatiza búsqueda de empleos en LinkedIn, selección de CV según reglas, registro en CSV y consultas del día/semana vía CLI o modelo OpenClaw.

## Advertencia importante

- LinkedIn limita automatización; el DOM cambia seguido y puede bloquear cuentas con uso agresivo.
- **Por defecto corre en `dry_run`** (simula sin enviar postulaciones).
- Usa pausas amplias y pocos envíos por corrida (`max_applications_per_run`).
- Revisa los [Términos de LinkedIn](https://www.linkedin.com/legal/user-agreement) antes de usar `--live`.

## 1) Instalar dependencias

```bash
python -m pip install -r scripts/requirements-linkedin-agent.txt
python -m playwright install chromium
```

## 2) Preparar CVs

Coloca PDFs en `cvs/` con los nombres definidos en `config/linkedin_jobs/cv_map.json`:

```text
cvs/cv_general.pdf
cvs/cv_backend.pdf
cvs/cv_data.pdf
```

## 3) Configurar búsqueda

Edita `config/linkedin_jobs/search.json`:

- `keywords`, `location`
- `max_applications_per_run`
- `dry_run`: `true` hasta validar el flujo

## 4) Primera ejecución (login + simulación)

```bash
python scripts/linkedin_jobs_agent.py run --headed
```

1. Se abre Chromium.
2. Inicia sesión manualmente en LinkedIn si te lo pide.
3. La sesión queda en `secrets/linkedin_storage_state.json`.
4. Registra vacantes en `data/linkedin_applications.csv` con estado `dry_run`.

## 5) Postulación real (opcional)

Cuando el flujo te convenza:

```bash
python scripts/linkedin_jobs_agent.py run --headed --live
```

Y en `search.json` pon `"dry_run": false`.

## 6) Consultar postulaciones

Resumen texto:

```bash
python scripts/linkedin_jobs_agent.py query --period day
python scripts/linkedin_jobs_agent.py query --period week
```

Pregunta en lenguaje natural (usa API OpenClaw):

```bash
set OPENCLAW_LINKEDIN_MODEL=tu-modelo-disponible
python scripts/linkedin_jobs_agent.py ask "¿A cuántas empresas postulé esta semana y con qué CV?" --period week
```

## 7) Reporte diario (Markdown)

```bash
python scripts/linkedin_jobs_report.py --period day --output reports/linkedin_daily.md
```

## 8) Programar en Windows (Task Scheduler)

- Cada mañana: `run --headed` (o sin headed si la sesión ya está guardada).
- Cada noche: `linkedin_jobs_report.py --period day`.

Action:

- Program: `python.exe`
- Arguments: `scripts/linkedin_jobs_agent.py run --headed`
- Start in: `C:\DEV\openclaw-mauro`

## Archivos generados

| Archivo | Uso |
|---------|-----|
| `data/linkedin_applications.csv` | Registro de postulaciones |
| `data/linkedin_processed_jobs.json` | IDs ya procesados (evita duplicados) |
| `secrets/linkedin_storage_state.json` | Cookies/sesión Playwright |

## Columnas del CSV

`applied_at`, `job_id`, `job_title`, `company`, `location`, `job_url`, `easy_apply`, `cv_used`, `application_status`, `match_rule`, `search_keywords`, `notes`, `error_message`

Estados típicos: `applied`, `dry_run`, `failed`, `skipped_no_easy_apply`, `skipped_no_cv`.

## Perfil soldador (amigo: construcción / reparaciones)

Segundo perfil con cuenta LinkedIn, CSV y CVs separados. Ver:

`scripts/README-linkedin-soldador-agent.md`

```bash
python scripts/linkedin_jobs_soldador.py run --headed
```

## Variables de entorno

Mismas que el dashboard OpenClaw (`app.py`):

- `OPENCLAW_PRIMARY_URL`
- `LITELLM_MASTER_KEY`
- `OPENCLAW_LINKEDIN_MODEL` (para subcomando `ask`)
