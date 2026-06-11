#!/bin/bash
set -euo pipefail
CONF=/etc/samba/smb.conf
if [[ -z "${PASS:-}" ]]; then
  echo "PASS no definida" >&2
  exit 1
fi
sudo_cmd() { printf '%s\n' "$PASS" | sudo -S "$@"; }
sudo_cmd cp -a "$CONF" "${CONF}.bak.$(date +%Y%m%d%H%M%S)"
sudo_cmd sed -i '/^\[ubuntu-root\]/,/^\[/ s/read only = yes/read only = no/' "$CONF"
sudo_cmd sed -i '/^\[ubuntu-root\]/,/^\[/ s/(read-only)/(read\/write)/' "$CONF"
if ! sudo_cmd grep -A20 '^\[ubuntu-root\]' "$CONF" | grep -q 'force user'; then
  sudo_cmd sed -i '/^\[ubuntu-root\]/,/^\[/{
    /valid users = mauro/a\
   writable = yes\
   create mask = 0664\
   directory mask = 0775\
   force user = mauro\
   force group = mauro
  }' "$CONF"
fi
sudo_cmd testparm -s >/dev/null
sudo_cmd systemctl restart smbd
echo "=== [ubuntu-root] ==="
grep -A14 '^\[ubuntu-root\]' "$CONF"
echo SAMBA_OK
