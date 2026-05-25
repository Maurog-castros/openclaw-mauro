$ErrorActionPreference = 'Stop'
$token = ssh mauro@192.168.1.12 "grep '^OPENCLAW_GATEWAY_TOKEN=' /home/mauro/openclaw-mauro/openclaw/.env | cut -d= -f2-"
Start-Process "http://192.168.1.12:18789/#token=$token"
