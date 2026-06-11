# Agente LinkedIn — perfil soldador / construcción / reparaciones

Segundo perfil para un amigo con especialidad en **soldadura**, **obra/construcción** y **reparaciones/mantención**. Usa el mismo motor que el agente tech, pero con:

- Búsqueda y reglas de CV propias
- CSV y estado en `data/soldador/`
- **Sesión LinkedIn separada** (debe iniciar sesión con **su** cuenta, no la tuya)

## Instalación

Misma que el agente principal (si ya la hiciste, no repitas):

```bash
python -m pip install -r scripts/requirements-linkedin-agent.txt
python -m playwright install chromium
```

## CVs de tu amigo

Coloca PDFs en `cvs/soldador/`:

| Archivo | Cuándo se usa |
|---------|----------------|
| `cv_obrero_general.pdf` | Por defecto |
| `cv_soldador.pdf` | Soldadura, MIG/TIG, estructuras metálicas |
| `cv_construccion.pdf` | Obra, faena, maestro, terminaciones |
| `cv_reparaciones.pdf` | Reparaciones, mantención, taller |
| `cv_industrial.pdf` | Planta, minería, equipos |

Ajusta nombres y palabras clave en `config/linkedin_jobs_soldador/cv_map.json`.

## Búsqueda

Edita `config/linkedin_jobs_soldador/search.json`:

- `keywords`: términos de ofertas (ej. soldador, construcción, mantención)
- `location`: ciudad o región (ej. `Santiago`, `Antofagasta`, `Chile`)
- `dry_run`: dejar `true` hasta probar el flujo

## Comandos (atajo recomendado)

```bash
# Primera vez: login con cuenta de tu amigo + simulación
python scripts/linkedin_jobs_soldador.py run --headed

# Resumen del día
python scripts/linkedin_jobs_soldador.py query --period day

# Pregunta con modelo OpenClaw
set OPENCLAW_LINKEDIN_MODEL=tu-modelo
python scripts/linkedin_jobs_soldador.py ask "¿A qué faenas postuló esta semana?" --period week

# Postulación real (cuando esté validado)
python scripts/linkedin_jobs_soldador.py run --headed --live
```

Equivalente con perfil explícito:

```bash
python scripts/linkedin_jobs_agent.py --profile soldador run --headed
```

## Reporte diario

```bash
python scripts/linkedin_jobs_report.py --profile soldador --period day --output reports/soldador_daily.md
```

## Archivos del perfil soldador

| Archivo | Uso |
|---------|-----|
| `data/soldador/linkedin_applications.csv` | Postulaciones registradas |
| `data/soldador/linkedin_processed_jobs.json` | Vacantes ya vistas |
| `secrets/linkedin_soldador_storage_state.json` | Sesión LinkedIn del amigo |

## No mezclar cuentas

- Perfil **tech** → `secrets/linkedin_storage_state.json` → tu LinkedIn  
- Perfil **soldador** → `secrets/linkedin_soldador_storage_state.json` → LinkedIn de tu amigo  

Si corres ambos en la misma PC, usa `--headed` la primera vez de cada perfil para confirmar que entró la cuenta correcta.

## Programar (Task Scheduler)

Mañana:

```text
python scripts/linkedin_jobs_soldador.py run --headed
```

Noche:

```text
python scripts/linkedin_jobs_report.py --profile soldador --period day --output reports/soldador_daily.md
```

Start in: `C:\DEV\openclaw-mauro`
