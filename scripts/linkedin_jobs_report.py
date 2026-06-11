"""Informe diario/semanal de postulaciones LinkedIn desde CSV."""

import argparse
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from linkedin_jobs_agent import PROFILES, filter_by_period, format_summary, read_applications


def build_markdown(rows: list, title: str) -> str:
    if not rows:
        return f"# {title}\n\nSin registros en el periodo.\n"

    by_status = Counter(r.get("application_status", "unknown") for r in rows)
    by_company = Counter(r.get("company", "") for r in rows if r.get("company"))
    by_cv = Counter(r.get("cv_used", "") for r in rows if r.get("cv_used"))

    lines = [
        f"# {title}",
        "",
        f"Generado: {datetime.now().isoformat(timespec='seconds')}",
        f"Total registros: {len(rows)}",
        "",
        "## Por estado",
    ]
    for status, count in by_status.most_common():
        lines.append(f"- {status}: {count}")

    lines.extend(["", "## Por empresa (top 10)"])
    for company, count in by_company.most_common(10):
        lines.append(f"- {company}: {count}")

    lines.extend(["", "## Por CV usado"])
    for cv, count in by_cv.most_common():
        lines.append(f"- {cv}: {count}")

    lines.extend(["", "## Detalle", ""])
    for r in rows:
        lines.append(
            f"- `{r.get('applied_at', '')}` | **{r.get('job_title', '')}** @ "
            f"{r.get('company', '')} | CV `{r.get('cv_used', '')}` | "
            f"estado `{r.get('application_status', '')}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Reporte de postulaciones LinkedIn")
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES.keys()),
        default=None,
        help="soldador: data/soldador/... | tech: data/linkedin_applications.csv",
    )
    parser.add_argument("--input", default="data/linkedin_applications.csv")
    parser.add_argument("--period", choices=["day", "week"], default="day")
    parser.add_argument("--output", default="")
    args = parser.parse_args()

    if args.profile:
        args.input = PROFILES[args.profile]["output"]
        if not args.output:
            args.output = f"reports/linkedin_{args.profile}_{args.period}.md"

    rows = read_applications(Path(args.input))
    filtered = filter_by_period(rows, args.period)
    profile_label = f" ({args.profile})" if args.profile else ""
    title = f"Postulaciones LinkedIn{profile_label} ({args.period})"
    md = build_markdown(filtered, title)

    if args.output:
        out = Path(args.output)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"Reporte guardado: {out}")
    else:
        print(md)
    print()
    print(format_summary(filtered, args.period))


if __name__ == "__main__":
    main()
