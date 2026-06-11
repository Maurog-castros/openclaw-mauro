#!/usr/bin/env bash
set -euo pipefail
REPO="${1:-/home/mauro/agentes-ai-on-clouds}"
cd "$REPO"

mkdir -p \
  apps/openclaw \
  apps/litellm \
  apps/open-webui \
  apps/memory-services \
  infra/terraform/gke \
  infra/terraform/eks \
  infra/terraform/aks \
  infra/k8s/base \
  infra/k8s/overlays/dev \
  infra/k8s/overlays/prod \
  cicd/jenkins \
  docs \
  scripts \
  secrets.example

cat > secrets.example/.env.example <<'EOF'
OPENAI_API_KEY=replace-me
LITELLM_MASTER_KEY=replace-me
POSTGRES_USER=agent_user
POSTGRES_PASSWORD=replace-me
REDIS_PASSWORD=replace-me
EOF

cat > .gitignore <<'EOF'
.env
.env.*
!.env.example
*.tfstate
*.tfstate.*
.terraform/
secrets/
*.pem
*.key
kubeconfig*
_inventory/
__pycache__/
*.pyc
.venv/
.venv-*/
*.csv
!*.csv.example
*.jsonl
*.bak
*.bak-*
EOF

if [[ ! -d .git ]]; then
  git init
  git add .
  git commit -m "chore: initial repo structure for multi-cloud agent platform"
else
  git add .
  if git diff --cached --quiet; then
    echo "Sin cambios nuevos para commit."
  else
    git commit -m "chore: phase 1 repo structure and secrets.example"
  fi
fi

git status -sb
echo "Fase 1 OK: $REPO"
