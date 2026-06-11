#!/bin/bash
# Ejecutar EN el servidor Ubuntu (SSH mauro@192.168.1.12) con sudo.
# Habilita escritura en el share Samba [ubuntu-root] (path = /)

set -euo pipefail

CONF=/etc/samba/smb.conf
BACKUP="${CONF}.bak.$(date +%Y%m%d%H%M%S)"

sudo cp -a "$CONF" "$BACKUP"
echo "Backup: $BACKUP"

# Reemplazar bloque [ubuntu-root] por versión lectura/escritura
sudo tee /tmp/ubuntu-root-share.conf >/dev/null <<'EOF'

[ubuntu-root]
   comment = Ubuntu Root (read/write)
   path = /
   browseable = yes
   read only = no
   writable = yes
   guest ok = no
   valid users = mauro
   create mask = 0664
   directory mask = 0775
   force user = mauro
   force group = mauro
EOF

# Eliminar bloque antiguo [ubuntu-root] y añadir el nuevo al final
sudo python3 <<'PY'
import re
from pathlib import Path
p = Path("/etc/samba/smb.conf")
text = p.read_text()
text = re.sub(r"\n\[ubuntu-root\][^\[]*", "\n", text, flags=re.DOTALL)
new = Path("/tmp/ubuntu-root-share.conf").read_text()
p.write_text(text.rstrip() + new + "\n")
PY

sudo testparm -s >/dev/null
echo "testparm OK"

# Contraseña Samba (si aún no existe): descomenta la siguiente línea
# sudo smbpasswd -a mauro

sudo systemctl restart smbd
sudo systemctl status smbd --no-pager -l | head -5
echo "Listo. Desde Windows: .\\scripts\\map-ubuntu-root-U.ps1"
