import re
from playwright.sync_api import sync_playwright

USER, PASS = "mauro", "mauro1234"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto("https://dev.h-l.cl/inicio")
    page.locator("input").first.fill(USER)
    page.get_by_role("button", name=re.compile("Siguiente|INGRESAR", re.I)).first.click()
    page.wait_for_timeout(1200)
    pwd = page.locator('input[type="password"]')
    if pwd.count():
        pwd.first.fill(PASS)
    page.get_by_role("button", name=re.compile("INGRESAR|Entrar", re.I)).first.click()
    page.wait_for_load_state("networkidle")
    page.goto("https://dev.h-l.cl/planilla", wait_until="networkidle")
    text = page.inner_text("body")
    keywords = [
        "remesa", "Remesa", "endose", "Endose", "garantía", "Garantía",
        "Tracking", "Generar", "PDF", "XLS", "aforo", "MSC",
    ]
    found = {k: (k.lower() in text.lower()) for k in keywords}
    links = page.eval_on_selector_all(
        "a",
        "els => [...new Set(els.map(e => (e.innerText||'').trim()).filter(t => /remesa|endose|garant|pdf|tracking|xls|aforo/i.test(t)))].slice(0,30)",
    )
    print("Keywords in planilla body:", {k: v for k, v in found.items() if v})
    print("Action links:", links)
    browser.close()
