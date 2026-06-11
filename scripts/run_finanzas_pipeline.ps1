# Pipeline finanzas: Gmail Lider + Santander + inbox fotos + CSV unificado
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "== Lider Gmail =="
python scripts/lider_receipts_agent.py

Write-Host "== Transferencias Santander =="
python scripts/transferencias_agent.py

Write-Host "== Cartolas Santander =="
python scripts/santander_cartola_agent.py

Write-Host "== Boletas foto (inbox) =="
python scripts/receipt_vision_agent.py --inbox data/inbox/boletas --merge --source telegram_foto

Write-Host "== Merge CSV unificado =="
python scripts/finanzas_merge.py

Write-Host "Listo: data/finanzas_movimientos.csv"
