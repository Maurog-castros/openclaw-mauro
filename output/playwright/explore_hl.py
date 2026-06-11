"""Explora módulos H-L antiguo y dev para comparación."""
import json
import re
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    import subprocess

    subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "-q"])
    subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    from playwright.sync_api import sync_playwright

OUT = Path(__file__).parent
USER, PASS = "mauro", "mauro1234"

OLD_PAGES = [
    "panel",
    "users",
    "client_users",
    "claves_permissions",
    "claves",
    "clients",
    "ingresoBL",
    "planilla",
    "buques",
    "navieras",
    "transportistas",
    "choferes",
    "generator",
    "ports",
    "remesa_form",
    "remesa_cliente",
    "remesa",
]


def scrape_page(page, label: str) -> dict:
    page.wait_for_load_state("networkidle", timeout=15000)
    title = page.title()
    headings = page.eval_on_selector_all(
        "h1, h2, h3, .page-title, .titulo, [class*='title']",
        "els => els.slice(0,8).map(e => (e.innerText||'').trim()).filter(Boolean)",
    )
    links = page.eval_on_selector_all(
        "a[href]",
        """els => [...new Set(els.slice(0,120).map(e => ({
            text: (e.innerText||'').trim().slice(0,80),
            href: e.getAttribute('href')||''
        })).filter(x => x.text && x.href && !x.href.startsWith('javascript')))]
        """,
    )
    buttons = page.eval_on_selector_all(
        "button, input[type=submit], .btn, [role=button]",
        "els => [...new Set(els.slice(0,40).map(e => (e.innerText||e.value||e.getAttribute('aria-label')||'').trim()).filter(Boolean))]",
    )
    tables = page.locator("table").count()
    forms = page.locator("form").count()
    inputs = page.locator("input, select, textarea").count()
    nav_text = page.eval_on_selector(
        "nav, .sidebar, .menu, #menu, .nav, [class*='sidebar'], [class*='menu']",
        "el => el ? el.innerText.slice(0,2000) : ''",
    ) if page.locator("nav, .sidebar, .menu, #menu").count() else ""

    return {
        "label": label,
        "url": page.url,
        "title": title,
        "headings": headings[:8],
        "tables": tables,
        "forms": forms,
        "inputs": inputs,
        "buttons_sample": buttons[:25],
        "links_sample": links[:30],
        "nav_snippet": (nav_text or "")[:1500],
    }


def login_old(page):
    page.goto("https://h-l.cl/", wait_until="domcontentloaded")
    page.get_by_role("textbox", name="Nombre de usuario").fill(USER)
    page.locator('input[type="password"]').fill(PASS)
    page.get_by_role("button", name="Entrar").click()
    page.wait_for_load_state("networkidle", timeout=25000)
    if "page=panel" not in page.url and "panel" not in page.title().lower():
        raise RuntimeError(f"Login antiguo falló: {page.url} | {page.title()}")


def login_dev(page):
    page.goto("https://dev.h-l.cl/inicio", wait_until="networkidle")
    # Flujo multi-paso: identificador -> contraseña
    id_field = page.get_by_placeholder(re.compile("identificador|usuario|rut|email", re.I))
    if id_field.count() == 0:
        id_field = page.locator("input").first
    id_field.fill(USER)
    next_btn = page.get_by_role("button", name=re.compile("Siguiente|Continuar|INGRESAR", re.I))
    if next_btn.count():
        next_btn.first.click()
        page.wait_for_timeout(1500)
    pwd = page.get_by_placeholder(re.compile("contraseña|clave|password", re.I))
    if pwd.count() == 0:
        pwd = page.locator('input[type="password"]')
    if pwd.count():
        pwd.first.fill(PASS)
    ingresar = page.get_by_role("button", name=re.compile("INGRESAR|Entrar|Iniciar", re.I))
    if ingresar.count():
        ingresar.first.click()
    page.wait_for_load_state("networkidle", timeout=25000)


def collect_nav(page) -> list:
    return page.eval_on_selector_all(
        "a[href]",
        """els => {
            const skip = /logout|salir|google|recover|javascript:void/i;
            return [...new Map(els.map(e => {
                const t = (e.innerText||'').replace(/\\s+/g,' ').trim();
                const h = e.href||'';
                if (!t || t.length>60 || skip.test(h) || skip.test(t)) return null;
                return [h, {text: t, href: h}];
            }).filter(Boolean)).values()];
        }""",
    )


def explore_dev_after_login(page) -> dict:
    base = scrape_page(page, "dashboard")
    nav = collect_nav(page)
    visited = {page.url}
    modules = [base]
    # Explorar enlaces internos del menú principal (máx 40)
    for item in nav[:45]:
        href = item.get("href", "")
        if not href or "dev.h-l.cl" not in href or href in visited:
            continue
        if any(x in href.lower() for x in ("logout", "salir", "google", "olvide", "recover")):
            continue
        try:
            page.goto(href, wait_until="networkidle", timeout=20000)
            visited.add(page.url)
            modules.append(scrape_page(page, item.get("text", href)))
        except Exception as ex:
            modules.append({"label": item.get("text"), "url": href, "error": str(ex)})
    return {"dashboard_nav": nav, "modules": modules}


def main():
    result = {"old": [], "dev": {}}
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        ctx = browser.new_context(locale="es-CL", viewport={"width": 1400, "height": 900})

        # OLD
        page = ctx.new_page()
        login_old(page)
        old_nav = collect_nav(page)
        for pg in OLD_PAGES:
            try:
                page.goto(f"https://h-l.cl/?page={pg}", wait_until="networkidle", timeout=20000)
                result["old"].append(scrape_page(page, pg))
            except Exception as ex:
                result["old"].append({"label": pg, "error": str(ex)})
        result["old_nav"] = old_nav

        # DEV
        page2 = ctx.new_page()
        try:
            login_dev(page2)
            result["dev"] = explore_dev_after_login(page2)
        except Exception as ex:
            result["dev"] = {"login_error": str(ex), "snapshot": page2.content()[:3000]}
        browser.close()

    out_file = OUT / "hl_comparison.json"
    out_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_file}")
    print(f"Old modules: {len(result['old'])}")
    dev_mods = result.get("dev", {}).get("modules", [])
    print(f"Dev modules explored: {len(dev_mods)}")


if __name__ == "__main__":
    main()
