#!/usr/bin/env python3
"""
Atajo: agente LinkedIn para perfil soldador / construcción / reparaciones.

Equivalente a: linkedin_jobs_agent.py --profile soldador <comando> ...
Usa la cuenta LinkedIn de tu amigo (sesión aparte en secrets/).
"""

from __future__ import annotations

import sys
from pathlib import Path

_SCRIPT = Path(__file__).resolve().parent / "linkedin_jobs_agent.py"


def main() -> None:
    argv = list(sys.argv)
    # linkedin_jobs_soldador.py run --headed  ->  agent.py --profile soldador run --headed
    if len(argv) == 1:
        argv.append("run")
    if "--profile" not in argv:
        argv[1:1] = ["--profile", "soldador"]
    sys.argv = [str(_SCRIPT.parent / "linkedin_jobs_agent.py")] + argv[1:]
    import linkedin_jobs_agent

    linkedin_jobs_agent.main()


if __name__ == "__main__":
    main()
