$ErrorActionPreference = 'Stop'
$token = ssh mauro@192.168.1.12 "grep '^OPENCLAW_GATEWAY_TOKEN=' /home/mauro/openclaw-mauro/openclaw/.env | cut -d= -f2-"
Start-Process "http://192.168.1.12:18789/main/chat?session=agent%3Amain%3Adashboard%3A804fa987-fed6-4cdd-86e2-14a2cc7f0877#token=$token"
