# Sincroniza scan LinkedIn hecho en Windows hacia el servidor Ubuntu
$ErrorActionPreference = "Stop"
$Root = "C:\DEV\openclaw-mauro"
$Date = Get-Date -Format "yyyy-MM-dd"
$Remote = "mauro@192.168.1.12"
$Base = "/home/mauro/openclaw-mauro"

Write-Host "Scan local..."
& "$Root\.venv-linkedin-intel\Scripts\python" "$Root\scripts\linkedin_intel_scout.py" scan --json | Out-Null

Write-Host "Sync al servidor..."
scp "$Root\data\workspace\marketing\intel\data\linkedin_signals_$Date.json" "${Remote}:${Base}/data/workspace/marketing/intel/data/"
scp "$Root\data\workspace\marketing\intel\reports\${Date}-linkedin-intel.md" "${Remote}:${Base}/data/workspace/marketing/intel/reports/"
scp "$Root\data\workspace\marketing\content\drafts\linkedin\${Date}-linkedin-drafts.md" "${Remote}:${Base}/data/workspace/marketing/content/drafts/linkedin/"
scp "$Root\secrets\linkedin_innovacionradical_storage_state.json" "${Remote}:${Base}/secrets/"

Write-Host "Listo. Prueba WhatsApp: /intel linkedin tendencias"
