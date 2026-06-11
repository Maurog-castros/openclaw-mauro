#!/bin/bash
# Habilita lectura/escritura en [ubuntu-root] — ejecutar en Ubuntu: bash ~/fix-ubuntu-root-samba-write.sh
set -euo pipefail
CONF=/etc/samba/smb.conf
sudo cp -a "$CONF" "${CONF}.bak.$(date +%Y%m%d%H%M%S)"

sudo sed -i '/^\[ubuntu-root\]/,/^\[/{
  s/read only = yes/read only = no/
  s/Ubuntu Root (read-only)/Ubuntu Root (read\/write)/
}' "$CONF"

# Asegurar que Samba escribe como tu usuario Linux (no como invitado/root anónimo)
if ! sudo grep -A20 '^\[ubuntu-root\]' "$CONF" | grep -q 'force user'; then
  sudo sed -i '/^\[ubuntu-root\]/,/^\[/{
    /valid users = mauro/a\
   writable = yes\
   create mask = 0664\
   directory mask = 0775\
   force user = mauro\
   force group = mauro
  }' "$CONF"
fi

sudo testparm -s >/dev/null
echo "=== [ubuntu-root] ==="
sudo testparm -s 2>/dev/null | sed -n '/\[ubuntu-root\]/,/^$/p'
sudo systemctl restart smbd
echo "Samba reiniciado. En Windows: net use Y: /delete & net use Y: \\\\192.168.1.12\\ubuntu-root /user:mauro /persistent:yes"
