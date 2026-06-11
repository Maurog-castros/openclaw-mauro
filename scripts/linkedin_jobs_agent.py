"""
Agente OpenClaw: búsqueda y postulación en LinkedIn con registro en CSV.

Requiere sesión humana inicial (login manual una vez). Por defecto corre en dry_run.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote_plus, urlparse

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

CSV_COLUMNS = [
    "applied_at",
    "job_id",
    "job_title",
    "company",
    "location",
    "job_url",
    "easy_apply",
    "cv_used",
    "application_status",
    "match_rule",
    "search_keywords",
    "notes",
    "error_message",
]

DEFAULT_SEARCH_CONFIG = {
    "keywords": "python developer",
    "location": "Chile",
    "easy_apply_only": True,
    "max_jobs_to_scan": 15,
    "max_applications_per_run": 5,
    "dry_run": True,
    "pause_between_applications_sec": 8,
}

DEFAULT_CV_MAP = {
    "default_cv": "cv_general.pdf",
    "rules": [
        {
            "name": "backend",
            "keywords_any": ["python", "backend", "django", "fastapi"],
            "cv": "cv_backend.pdf",
        },
        {
            "name": "data",
            "keywords_any": ["data", "analytics", "sql", "etl"],
            "cv": "cv_data.pdf",
        },
    ],
}

# Perfiles separados: distinta config, CSV, sesion LinkedIn y carpeta de CVs.
PROFILES: Dict[str, Dict[str, str]] = {
    "tech": {
        "search_config": "config/linkedin_jobs/search.json",
        "cv_map": "config/linkedin_jobs/cv_map.json",
        "cvs_dir": "cvs",
        "output": "data/linkedin_applications.csv",
        "state": "data/linkedin_processed_jobs.json",
        "storage_state": "secrets/linkedin_storage_state.json",
    },
    "soldador": {
        "search_config": "config/linkedin_jobs_soldador/search.json",
        "cv_map": "config/linkedin_jobs_soldador/cv_map.json",
        "cvs_dir": "cvs/soldador",
        "output": "data/soldador/linkedin_applications.csv",
        "state": "data/soldador/linkedin_processed_jobs.json",
        "storage_state": "secrets/linkedin_soldador_storage_state.json",
    },
}


def apply_profile(args: argparse.Namespace) -> None:
    profile = getattr(args, "profile", None)
    if not profile:
        return
    if profile not in PROFILES:
        raise SystemExit(f"Perfil desconocido: {profile}. Opciones: {', '.join(PROFILES)}")
    for key, value in PROFILES[profile].items():
        setattr(args, key, value)


def load_json(path: Path, default: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(default, ensure_ascii=False, indent=2), encoding="utf-8")
        return dict(default)
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return dict(default)


def load_state(state_file: Path) -> Dict[str, bool]:
    if not state_file.exists():
        return {}
    try:
        return json.loads(state_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_state(state_file: Path, state: Dict[str, bool]) -> None:
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def ensure_csv(csv_file: Path) -> None:
    csv_file.parent.mkdir(parents=True, exist_ok=True)
    if csv_file.exists():
        return
    with csv_file.open("w", newline="", encoding="utf-8") as f:
        csv.DictWriter(f, fieldnames=CSV_COLUMNS).writeheader()


def append_csv(csv_file: Path, row: Dict[str, str]) -> None:
    with csv_file.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writerow({k: row.get(k, "") for k in CSV_COLUMNS})


def job_id_from_url(url: str) -> str:
    m = re.search(r"currentJobId=(\d+)", url)
    if m:
        return m.group(1)
    m = re.search(r"/jobs/view/(\d+)", url)
    if m:
        return m.group(1)
    return urlparse(url).path or url


def build_search_url(cfg: Dict[str, Any]) -> str:
    params = [f"keywords={quote_plus(cfg.get('keywords', ''))}"]
    location = cfg.get("location", "").strip()
    if location:
        params.append(f"location={quote_plus(location)}")
    if cfg.get("easy_apply_only", True):
        params.append("f_AL=true")
    return "https://www.linkedin.com/jobs/search/?" + "&".join(params)


def pick_cv(job_title: str, company: str, cv_map: Dict[str, Any], cvs_dir: Path) -> Tuple[str, str]:
    blob = f"{job_title} {company}".lower()
    for rule in cv_map.get("rules", []):
        keywords = [k.lower() for k in rule.get("keywords_any", [])]
        if any(k in blob for k in keywords):
            cv_name = rule.get("cv", "")
            if (cvs_dir / cv_name).exists():
                return cv_name, rule.get("name", "rule")
    default_cv = cv_map.get("default_cv", "")
    if default_cv and (cvs_dir / default_cv).exists():
        return default_cv, "default"
    available = sorted(p.name for p in cvs_dir.glob("*.pdf"))
    if available:
        return available[0], "fallback_first_pdf"
    return "", "no_cv_found"


def read_applications(csv_file: Path) -> List[Dict[str, str]]:
    if not csv_file.exists():
        return []
    with csv_file.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def filter_by_period(rows: List[Dict[str, str]], period: str) -> List[Dict[str, str]]:
    if period == "all":
        return rows
    now = datetime.now()
    if period == "day":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == "week":
        start = now - timedelta(days=now.weekday())
        start = start.replace(hour=0, minute=0, second=0, microsecond=0)
    else:
        return rows
    out = []
    for row in rows:
        raw = row.get("applied_at", "")
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            continue
        if dt >= start:
            out.append(row)
    return out


def format_summary(rows: List[Dict[str, str]], period_label: str) -> str:
    if not rows:
        return f"No hay postulaciones registradas en el periodo: {period_label}."
    applied = [r for r in rows if r.get("application_status") == "applied"]
    dry = [r for r in rows if r.get("application_status") == "dry_run"]
    failed = [r for r in rows if r.get("application_status") == "failed"]
    lines = [
        f"Resumen ({period_label}): {len(rows)} registros",
        f"- Postuladas: {len(applied)}",
        f"- Simulacion (dry_run): {len(dry)}",
        f"- Fallidas: {len(failed)}",
        "",
        "Detalle:",
    ]
    for r in rows:
        lines.append(
            f"• {r.get('applied_at', '')} | {r.get('job_title', '')} @ {r.get('company', '')} "
            f"| CV: {r.get('cv_used', '')} | estado: {r.get('application_status', '')}"
        )
    return "\n".join(lines)


def openclaw_client() -> OpenAI:
    base_url = os.getenv("OPENCLAW_PRIMARY_URL", "https://ia.iamiko.cl/v1")
    api_key = os.getenv("LITELLM_MASTER_KEY", "sk-openclaw-local")
    return OpenAI(base_url=base_url, api_key=api_key)


def ask_about_applications(
    question: str,
    rows: List[Dict[str, str]],
    model: str,
) -> str:
    context = json.dumps(rows, ensure_ascii=False, indent=2)
    client = openclaw_client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Eres un asistente de carrera. Respondes solo con datos del JSON de postulaciones. "
                    "Si no hay datos suficientes, dilo claramente. Responde en español."
                ),
            },
            {
                "role": "user",
                "content": f"Pregunta: {question}\n\nPostulaciones:\n{context}",
            },
        ],
        temperature=0.2,
    )
    return response.choices[0].message.content or ""


def ensure_logged_in(page, storage_state: Path, login_wait_sec: int) -> None:
    page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
    time.sleep(2)
    if "login" in page.url or "checkpoint" in page.url:
        print("Inicia sesion en LinkedIn en el navegador abierto.")
        print(f"Esperando hasta {login_wait_sec}s para completar login...")
        deadline = time.time() + login_wait_sec
        while time.time() < deadline:
            page.goto("https://www.linkedin.com/feed/", wait_until="domcontentloaded", timeout=60000)
            time.sleep(2)
            if "feed" in page.url:
                break
        if "feed" not in page.url:
            raise RuntimeError("No se detecto sesion activa de LinkedIn.")
    storage_state.parent.mkdir(parents=True, exist_ok=True)
    page.context.storage_state(path=str(storage_state))
    print(f"Sesion guardada en: {storage_state}")


def collect_job_cards(page, max_jobs: int) -> List[Dict[str, str]]:
    jobs: List[Dict[str, str]] = []
    cards = page.locator("div.job-card-container, li.jobs-search-results__list-item")
    count = cards.count()
    for i in range(min(count, max_jobs)):
        card = cards.nth(i)
        title = ""
        company = ""
        location = ""
        url = ""
        try:
            title = card.locator("a.job-card-list__title, a.job-card-container__link").first.inner_text(
                timeout=3000
            ).strip()
        except Exception:
            pass
        try:
            company = card.locator(
                "span.job-card-container__primary-description, "
                "a.hidden-nested-link, "
                "span.artdeco-entity-lockup__subtitle"
            ).first.inner_text(timeout=2000).strip()
        except Exception:
            pass
        try:
            location = card.locator(
                "span.job-card-container__metadata-item, "
                "li.job-card-container__metadata-item"
            ).first.inner_text(timeout=2000).strip()
        except Exception:
            pass
        try:
            href = card.locator("a.job-card-list__title, a.job-card-container__link").first.get_attribute(
                "href"
            )
            if href:
                url = href if href.startswith("http") else f"https://www.linkedin.com{href}"
        except Exception:
            pass
        if title and url:
            jobs.append(
                {
                    "job_title": title,
                    "company": company,
                    "location": location,
                    "job_url": url.split("?")[0],
                }
            )
    return jobs


def try_easy_apply(
    page,
    cv_path: Path,
    dry_run: bool,
) -> Tuple[str, str]:
    """Devuelve (status, error_message)."""
    easy_btn = page.locator(
        "button.jobs-apply-button, button.jobs-s-apply button, button:has-text('Solicitud sencilla'), "
        "button:has-text('Easy Apply')"
    )
    if easy_btn.count() == 0:
        return "skipped_no_easy_apply", "No se encontro boton Easy Apply"
    if dry_run:
        return "dry_run", ""
    easy_btn.first.click(timeout=8000)
    time.sleep(2)
    # Subir CV si aparece input file
    file_input = page.locator("input[type='file']")
    if file_input.count() > 0 and cv_path.exists():
        file_input.first.set_input_files(str(cv_path))
        time.sleep(1)
    # Avanzar pasos del modal
    for _ in range(6):
        submit = page.locator(
            "button[aria-label='Submit application'], "
            "button[aria-label='Enviar solicitud'], "
            "button:has-text('Submit application'), "
            "button:has-text('Enviar solicitud')"
        )
        if submit.count() > 0:
            submit.first.click(timeout=5000)
            time.sleep(2)
            return "applied", ""
        nxt = page.locator(
            "button[aria-label='Continue to next step'], "
            "button[aria-label='Review your application'], "
            "button[aria-label='Continuar'], "
            "button:has-text('Next'), "
            "button:has-text('Siguiente'), "
            "button:has-text('Review')"
        )
        if nxt.count() > 0:
            nxt.first.click(timeout=5000)
            time.sleep(1.5)
            continue
        break
    return "failed", "No se pudo completar el flujo Easy Apply"


def run_apply_cycle(
    search_cfg: Dict[str, Any],
    cv_map: Dict[str, Any],
    csv_file: Path,
    state_file: Path,
    storage_state: Path,
    cvs_dir: Path,
    headed: bool,
    login_wait_sec: int,
) -> int:
    state = load_state(state_file)
    ensure_csv(csv_file)
    processed = 0
    max_apply = int(search_cfg.get("max_applications_per_run", 5))
    max_scan = int(search_cfg.get("max_jobs_to_scan", 15))
    dry_run = bool(search_cfg.get("dry_run", True))
    pause_sec = int(search_cfg.get("pause_between_applications_sec", 8))

    from playwright.sync_api import Browser, BrowserContext, sync_playwright

    with sync_playwright() as p:
        browser: Browser = p.chromium.launch(headless=not headed)
        context_kwargs: Dict[str, Any] = {}
        if storage_state.exists():
            context_kwargs["storage_state"] = str(storage_state)
        context: BrowserContext = browser.new_context(**context_kwargs)
        page = context.new_page()
        ensure_logged_in(page, storage_state, login_wait_sec)

        search_url = build_search_url(search_cfg)
        print(f"Buscando empleos: {search_url}")
        page.goto(search_url, wait_until="domcontentloaded", timeout=60000)
        time.sleep(3)
        jobs = collect_job_cards(page, max_scan)
        print(f"Vacantes detectadas en listado: {len(jobs)}")

        for job in jobs:
            if processed >= max_apply:
                break
            jid = job_id_from_url(job["job_url"])
            if state.get(jid):
                continue

            cv_name, match_rule = pick_cv(job["job_title"], job["company"], cv_map, cvs_dir)
            cv_path = cvs_dir / cv_name if cv_name else Path()
            row = {
                "applied_at": datetime.now().isoformat(timespec="seconds"),
                "job_id": jid,
                "job_title": job["job_title"],
                "company": job["company"],
                "location": job["location"],
                "job_url": job["job_url"],
                "easy_apply": "",
                "cv_used": cv_name,
                "application_status": "",
                "match_rule": match_rule,
                "search_keywords": search_cfg.get("keywords", ""),
                "notes": "dry_run" if dry_run else "live",
                "error_message": "",
            }

            if not cv_name:
                row["application_status"] = "skipped_no_cv"
                row["error_message"] = f"No hay CV en {cvs_dir}"
                append_csv(csv_file, row)
                state[jid] = True
                processed += 1
                continue

            try:
                page.goto(job["job_url"], wait_until="domcontentloaded", timeout=60000)
                time.sleep(2)
                status, err = try_easy_apply(page, cv_path, dry_run=dry_run)
                row["application_status"] = status
                row["error_message"] = err
                row["easy_apply"] = "yes" if status in ("applied", "dry_run") else "no"
            except Exception as exc:
                row["application_status"] = "failed"
                row["error_message"] = str(exc)

            append_csv(csv_file, row)
            state[jid] = True
            processed += 1
            print(
                f"[{row['application_status']}] {row['job_title']} @ {row['company']} "
                f"(CV: {row['cv_used']})"
            )
            time.sleep(pause_sec)

        context.storage_state(path=str(storage_state))
        browser.close()

    save_state(state_file, state)
    return processed


def cmd_run(args: argparse.Namespace) -> None:
    search_cfg = load_json(Path(args.search_config), DEFAULT_SEARCH_CONFIG)
    cv_map = load_json(Path(args.cv_map), DEFAULT_CV_MAP)
    if args.live:
        search_cfg["dry_run"] = False
    count = run_apply_cycle(
        search_cfg=search_cfg,
        cv_map=cv_map,
        csv_file=Path(args.output),
        state_file=Path(args.state),
        storage_state=Path(args.storage_state),
        cvs_dir=Path(args.cvs_dir),
        headed=args.headed,
        login_wait_sec=args.login_wait_sec,
    )
    print(f"Registros procesados en esta corrida: {count}")
    print(f"CSV: {args.output}")


def cmd_query(args: argparse.Namespace) -> None:
    rows = filter_by_period(read_applications(Path(args.output)), args.period)
    print(format_summary(rows, args.period))


def cmd_ask(args: argparse.Namespace) -> None:
    rows = filter_by_period(read_applications(Path(args.output)), args.period)
    answer = ask_about_applications(args.question, rows, args.model)
    print(answer)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Agente LinkedIn OpenClaw: buscar, postular (Easy Apply) y registrar en CSV."
    )
    parser.add_argument(
        "--profile",
        choices=sorted(PROFILES.keys()),
        default=None,
        help="tech: tu perfil. soldador: soldadura/construccion/reparaciones (cuenta y CSV aparte).",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    run_p = sub.add_parser("run", help="Buscar vacantes y postular segun configuracion")
    run_p.add_argument("--search-config", default="config/linkedin_jobs/search.json")
    run_p.add_argument("--cv-map", default="config/linkedin_jobs/cv_map.json")
    run_p.add_argument("--cvs-dir", default="cvs")
    run_p.add_argument("--output", default="data/linkedin_applications.csv")
    run_p.add_argument("--state", default="data/linkedin_processed_jobs.json")
    run_p.add_argument("--storage-state", default="secrets/linkedin_storage_state.json")
    run_p.add_argument("--headed", action="store_true", help="Mostrar navegador")
    run_p.add_argument("--live", action="store_true", help="Postular de verdad (sin dry_run)")
    run_p.add_argument("--login-wait-sec", type=int, default=180)
    run_p.set_defaults(func=cmd_run)

    query_p = sub.add_parser("query", help="Resumen de postulaciones del dia o semana")
    query_p.add_argument("--output", default="data/linkedin_applications.csv")
    query_p.add_argument("--period", choices=["day", "week", "all"], default="day")
    query_p.set_defaults(func=cmd_query)

    ask_p = sub.add_parser("ask", help="Preguntar sobre postulaciones usando modelo OpenClaw")
    ask_p.add_argument("question")
    ask_p.add_argument("--output", default="data/linkedin_applications.csv")
    ask_p.add_argument("--period", choices=["day", "week", "all"], default="week")
    ask_p.add_argument("--model", default=os.getenv("OPENCLAW_LINKEDIN_MODEL", ""))
    ask_p.set_defaults(func=cmd_ask)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    apply_profile(args)
    if args.command == "ask" and not args.model:
        print(
            "Error: define --model o la variable OPENCLAW_LINKEDIN_MODEL con un modelo disponible.",
            file=sys.stderr,
        )
        sys.exit(1)
    args.func(args)


if __name__ == "__main__":
    main()
