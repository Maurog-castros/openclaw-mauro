# Hermes Agent

## Windows local (PC de desarrollo)

Instalado con el script oficial en `%LOCALAPPDATA%\hermes\` (`HERMES_HOME`).

### Modelos (Iamiko / OpenClaw)

Endpoint: `https://ia.iamiko.cl/v1` — lista: [ia.iamiko.cl/v1/models](https://ia.iamiko.cl/v1/models)

| Modelo | Uso sugerido en Hermes |
|--------|------------------------|
| `qwen3-coder-next` | Default — código y agente |
| `qwen3-vl-30b-a3b-instruct` | Visión / imágenes (`hermes model`) |
| `text-embedding-nomic-embed-text-v1.5` | Embeddings (memoria; no es chat) |

### Archivos de config

| Ruta | Uso |
|------|-----|
| `%LOCALAPPDATA%\hermes\config.yaml` | `model.provider: custom`, `base_url`, `default` |
| `%LOCALAPPDATA%\hermes\.env` | `OPENAI_API_KEY`, `OPENAI_BASE_URL` |
| `%LOCALAPPDATA%\hermes\hermes-agent\` | Código y venv |

Clave por defecto (misma que OpenClaw local): `sk-openclaw-local`. Si tu proxy exige otra, edita `.env`.

### Comandos

```powershell
# Tras instalar, abre una terminal nueva (PATH) o:
$env:Path = "$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts;" + $env:Path
$env:HERMES_HOME = "$env:LOCALAPPDATA\hermes"

hermes doctor
hermes                    # chat interactivo
hermes model              # cambiar modelo
hermes dashboard --host 127.0.0.1 --port 9119
```

Dashboard local: **http://127.0.0.1:9119**

### Reinstalar / actualizar

```powershell
iex (irm https://raw.githubusercontent.com/NousResearch/hermes-agent/main/scripts/install.ps1)
hermes update
```

---

## Dashboard web (servidor Ubuntu)

Instalado en `mauro@192.168.1.12` (ZenBook). **Misma config que Windows**: endpoint directo Iamiko, modelo `qwen3-coder-next`.

| Setting | Valor |
|---------|--------|
| `model.provider` | `custom` |
| `model.base_url` | `https://ia.iamiko.cl/v1` |
| `model.default` | `qwen3-coder-next` |
| `model.api_key` | `sk-openclaw-local` (obligatorio en `config.yaml` para Iamiko; el dashboard no usa solo `.env`) |
| `.env` | `OPENAI_API_KEY` + `OPENAI_BASE_URL` → Iamiko (CLI / herramientas auxiliares) |

Servicio **siempre activo** (user systemd):

```bash
systemctl --user status hermes-dashboard   # debe estar active
systemctl --user enable hermes-dashboard   # ya habilitado al boot (con linger)
```

## Acceso desde tu PC (LAN)

El dashboard escucha en **todas las interfaces** (`0.0.0.0:9119`, flag `--insecure`).

Desde cualquier equipo en la misma red:

**http://192.168.1.12:9119**

Sin autenticación propia: solo en red de confianza. Si la IP del servidor cambia, sustituye en la URL.

### Alternativa más segura (solo localhost + túnel SSH)

```powershell
ssh -L 9119:127.0.0.1:9119 mauro@192.168.1.12
```

Navegador: **http://127.0.0.1:9119**

## Estado del servicio (en el servidor)

```bash
systemctl --user status hermes-dashboard
systemctl --user restart hermes-dashboard
journalctl --user -u hermes-dashboard -f
```

## Rutas importantes

| Ruta | Uso |
|------|-----|
| `~/.hermes/venv/` | Python 3.12 + Hermes (git main, v0.15.1) |
| `~/.hermes/config.yaml` | `custom` → `https://ia.iamiko.cl/v1`, default `qwen3-coder-next` |
| `~/.hermes/.env` | `OPENAI_API_KEY` + `OPENAI_BASE_URL=https://ia.iamiko.cl/v1` |
| `~/.hermes/skills/` | Skills de `npx skills` (chrome-extensions, etc.) |
| `~/hermes-agent-src/hermes_cli/web_dist/` | UI web compilada |

## CLI manual

```bash
export PATH="$HOME/.local/bin:$PATH"
hermes --version
hermes doctor
hermes skills list
hermes dashboard --no-open --host 127.0.0.1 --port 9119 --tui --skip-build
```

## Chat en el dashboard (`/chat`)

Requiere el TUI compilado. Si ves `[session ended]` y no puedes escribir:

```bash
cd ~/hermes-agent-src/ui-tui && npm install && npm run build
# El servicio usa HERMES_TUI_DIR=/home/mauro/hermes-agent-src/ui-tui
systemctl --user restart hermes-dashboard
```

También necesitas `model.api_key` en `config.yaml` (no basta solo `.env` para Iamiko).

## Actualizar frontend (si cambia la UI)

```bash
cd ~/hermes-agent-src && git pull
cd web && npm ci && npm run build
cp -a ../hermes_cli/web_dist ~/.hermes/venv/lib/python3.12/site-packages/hermes_cli/web_dist
cd ../ui-tui && npm install && npm run build
systemctl --user restart hermes-dashboard
```

## Actualizar Hermes

```bash
source ~/.local/bin/env
uv pip install --python ~/.hermes/venv/bin/python "hermes-agent[web,pty,all] @ git+https://github.com/NousResearch/hermes-agent.git"
```

## Seguridad

- LAN activa (`--host 0.0.0.0 --insecure`): cualquiera en la red puede ver config y claves en el dashboard.
- Para Internet o redes compartidas: volver a `127.0.0.1` o poner un reverse proxy con auth delante del 9119.
