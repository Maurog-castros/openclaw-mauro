# Graph Report - .  (2026-06-03)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 627 nodes · 1088 edges · 82 communities (34 shown, 48 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 31 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `650b22cf`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- [[_COMMUNITY_Community 0|Community 0]]
- [[_COMMUNITY_Community 1|Community 1]]
- [[_COMMUNITY_Community 2|Community 2]]
- [[_COMMUNITY_Community 3|Community 3]]
- [[_COMMUNITY_Community 4|Community 4]]
- [[_COMMUNITY_Community 5|Community 5]]
- [[_COMMUNITY_Community 6|Community 6]]
- [[_COMMUNITY_Community 7|Community 7]]
- [[_COMMUNITY_Community 8|Community 8]]
- [[_COMMUNITY_Community 9|Community 9]]
- [[_COMMUNITY_Community 10|Community 10]]
- [[_COMMUNITY_Community 11|Community 11]]
- [[_COMMUNITY_Community 12|Community 12]]
- [[_COMMUNITY_Community 13|Community 13]]
- [[_COMMUNITY_Community 14|Community 14]]
- [[_COMMUNITY_Community 15|Community 15]]
- [[_COMMUNITY_Community 16|Community 16]]
- [[_COMMUNITY_Community 17|Community 17]]
- [[_COMMUNITY_Community 18|Community 18]]
- [[_COMMUNITY_Community 19|Community 19]]
- [[_COMMUNITY_Community 20|Community 20]]
- [[_COMMUNITY_Community 21|Community 21]]
- [[_COMMUNITY_Community 22|Community 22]]
- [[_COMMUNITY_Community 23|Community 23]]
- [[_COMMUNITY_Community 24|Community 24]]
- [[_COMMUNITY_Community 25|Community 25]]
- [[_COMMUNITY_Community 26|Community 26]]
- [[_COMMUNITY_Community 27|Community 27]]
- [[_COMMUNITY_Community 28|Community 28]]
- [[_COMMUNITY_Community 29|Community 29]]
- [[_COMMUNITY_Community 30|Community 30]]
- [[_COMMUNITY_Community 31|Community 31]]
- [[_COMMUNITY_Community 32|Community 32]]
- [[_COMMUNITY_Community 33|Community 33]]
- [[_COMMUNITY_Community 34|Community 34]]
- [[_COMMUNITY_Community 35|Community 35]]
- [[_COMMUNITY_Community 36|Community 36]]
- [[_COMMUNITY_Community 37|Community 37]]
- [[_COMMUNITY_Community 38|Community 38]]
- [[_COMMUNITY_Community 39|Community 39]]
- [[_COMMUNITY_Community 40|Community 40]]
- [[_COMMUNITY_Community 41|Community 41]]
- [[_COMMUNITY_Community 42|Community 42]]
- [[_COMMUNITY_Community 43|Community 43]]
- [[_COMMUNITY_Community 44|Community 44]]
- [[_COMMUNITY_Community 45|Community 45]]
- [[_COMMUNITY_Community 46|Community 46]]
- [[_COMMUNITY_Community 47|Community 47]]
- [[_COMMUNITY_Community 48|Community 48]]
- [[_COMMUNITY_Community 49|Community 49]]
- [[_COMMUNITY_Community 50|Community 50]]
- [[_COMMUNITY_Community 51|Community 51]]
- [[_COMMUNITY_Community 52|Community 52]]
- [[_COMMUNITY_Community 53|Community 53]]
- [[_COMMUNITY_Community 54|Community 54]]
- [[_COMMUNITY_Community 55|Community 55]]
- [[_COMMUNITY_Community 56|Community 56]]
- [[_COMMUNITY_Community 57|Community 57]]
- [[_COMMUNITY_Community 58|Community 58]]
- [[_COMMUNITY_Community 59|Community 59]]
- [[_COMMUNITY_Community 60|Community 60]]
- [[_COMMUNITY_Community 61|Community 61]]
- [[_COMMUNITY_Community 62|Community 62]]
- [[_COMMUNITY_Community 63|Community 63]]
- [[_COMMUNITY_Community 64|Community 64]]
- [[_COMMUNITY_Community 65|Community 65]]
- [[_COMMUNITY_Community 66|Community 66]]
- [[_COMMUNITY_Community 67|Community 67]]
- [[_COMMUNITY_Community 68|Community 68]]
- [[_COMMUNITY_Community 69|Community 69]]
- [[_COMMUNITY_Community 70|Community 70]]
- [[_COMMUNITY_Community 71|Community 71]]
- [[_COMMUNITY_Community 72|Community 72]]
- [[_COMMUNITY_Community 73|Community 73]]
- [[_COMMUNITY_Community 74|Community 74]]
- [[_COMMUNITY_Community 75|Community 75]]

## God Nodes (most connected - your core abstractions)
1. `entries` - 44 edges
2. `str` - 37 edges
3. `process_image_file()` - 22 edges
4. `process_messages()` - 19 edges
5. `Any` - 18 edges
6. `parse_clp()` - 17 edges
7. `str` - 17 edges
8. `run_apply_cycle()` - 17 edges
9. `Path` - 16 edges
10. `main()` - 15 edges

## Surprising Connections (you probably didn't know these)
- `main()` --calls--> `resolve_data_path()`  [INFERRED]
  scripts/finanzas_merchant_report.py → scripts/finanzas_common.py
- `main()` --calls--> `resolve_data_path()`  [INFERRED]
  scripts/finanzas_monthly_report.py → scripts/finanzas_common.py
- `main()` --calls--> `load_merchant_aliases()`  [INFERRED]
  scripts/finanzas_merchant_report.py → scripts/finanzas_common.py
- `summarize_alias()` --calls--> `alias_patterns()`  [INFERRED]
  scripts/finanzas_merchant_report.py → scripts/finanzas_common.py
- `main()` --calls--> `row_matches_alias()`  [INFERRED]
  scripts/finanzas_merchant_report.py → scripts/finanzas_common.py

## Import Cycles
- 1-file cycle: `app.py -> app.py`
- 1-file cycle: `scripts/linkedin_jobs_agent.py -> scripts/linkedin_jobs_agent.py`
- 1-file cycle: `scripts/receipt_vision_agent.py -> scripts/receipt_vision_agent.py`

## Communities (82 total, 48 thin omitted)

### Community 0 - "Community 0"
Cohesion: 0.14
Nodes (49): alias_patterns(), category_for_product(), _category_from_cartola_description(), dedupe_gastos_by_receipt(), dedupe_rows(), ensure_csv_headers(), extract_json_object(), file_sha256() (+41 more)

### Community 1 - "Community 1"
Cohesion: 0.04
Nodes (46): agents, defaults, list, bindings, channels, commands, native, nativeSkills (+38 more)

### Community 2 - "Community 2"
Cohesion: 0.13
Nodes (37): ArgumentParser, Namespace, append_csv(), apply_profile(), ask_about_applications(), build_parser(), build_search_url(), cmd_ask() (+29 more)

### Community 3 - "Community 3"
Cohesion: 0.19
Nodes (27): float, append_rows(), category_for_product(), decode_pdf_content(), ensure_csv_headers(), extract_parts(), get_gmail_service(), is_valid_receipt_attachment() (+19 more)

### Community 4 - "Community 4"
Cohesion: 0.25
Nodes (26): date, build_detail_mobile(), build_detail_summary(), build_detail_table(), filter_rows(), fmt_clp(), fmt_date_dd_mm_yy(), fmt_time_24h() (+18 more)

### Community 5 - "Community 5"
Cohesion: 0.07
Nodes (27): config, enabled, agents, dreaming, enabled, logging, promptStyle, queryMode (+19 more)

### Community 6 - "Community 6"
Cohesion: 0.19
Nodes (25): ensure_csv_headers(), extract_html_from_message(), extract_parts(), extract_section(), field_after_label(), first_email(), get_gmail_service(), get_header_value() (+17 more)

### Community 7 - "Community 7"
Cohesion: 0.25
Nodes (24): append_vision_rows(), call_vision_model(), extract_receipt_from_image(), finalize_skipped_image(), find_latest_inbound_image(), format_receipt_summary(), image_to_data_url(), infer_inbound_source() (+16 more)

### Community 8 - "Community 8"
Cohesion: 0.21
Nodes (22): append_rows(), classify_movement(), _ddmmyyyy_to_iso(), ensure_csv_headers(), infer_movement_date(), is_cartola_pdf(), is_movement_amount(), main() (+14 more)

### Community 9 - "Community 9"
Cohesion: 0.09
Nodes (21): 10) Troubleshooting, 1) Instalar dependencias, 2) Esquema CSV unificado, 4) Pipeline completo (Task Scheduler), 5) Config OpenClaw — agente finanzas, 6) Config OpenClaw — Telegram → finanzas, 6b) WhatsApp → finanzas (numero dedicado), 8) Probar vision contra Iamiko (+13 more)

### Community 10 - "Community 10"
Cohesion: 0.22
Nodes (20): backup(), ensure_channel_binding(), ensure_finanzas_docker_mounts(), ensure_host_symlinks_for_container(), ensure_merchant_aliases_seed(), load_whatsapp_allow_from(), main(), normalize_e164() (+12 more)

### Community 11 - "Community 11"
Cohesion: 0.12
Nodes (16): document, photo, agents, list, channels, telegram, _comment, models (+8 more)

### Community 12 - "Community 12"
Cohesion: 0.12
Nodes (16): Acceso desde tu PC (LAN), Actualizar frontend (si cambia la UI), Actualizar Hermes, Alternativa más segura (solo localhost + túnel SSH), Archivos de config, Chat en el dashboard (`/chat`), CLI manual, Comandos (+8 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (14): 1) Instalar dependencias, 2) Preparar CVs, 3) Configurar búsqueda, 4) Primera ejecución (login + simulación), 5) Postulación real (opcional), 6) Consultar postulaciones, 7) Reporte diario (Markdown), 8) Programar en Windows (Task Scheduler) (+6 more)

### Community 14 - "Community 14"
Cohesion: 0.31
Nodes (14): cartola_entries(), finanzas_entries(), in_range(), main(), match_entries(), merchant_hint(), month_range(), normalize_desc() (+6 more)

### Community 15 - "Community 15"
Cohesion: 0.14
Nodes (14): mode, password, trustedProxy, allowedOrigins, allowInsecureAuth, dangerouslyDisableDeviceAuth, gateway, auth (+6 more)

### Community 16 - "Community 16"
Cohesion: 0.15
Nodes (13): systemPrompt, poll, sendMessage, telegram, 8503943962, actions, allowFrom, direct (+5 more)

### Community 17 - "Community 17"
Cohesion: 0.17
Nodes (12): ask, commandHighlighting, host, security, strictInlineEval, maxResults, provider, timeoutSeconds (+4 more)

### Community 18 - "Community 18"
Cohesion: 0.18
Nodes (11): enabled, enabled, enabled, 1password, bear-notes, camsnap, peekaboo, trello (+3 more)

### Community 19 - "Community 19"
Cohesion: 0.20
Nodes (9): Agente LinkedIn — perfil soldador / construcción / reparaciones, Archivos del perfil soldador, Búsqueda, Comandos (atajo recomendado), CVs de tu amigo, Instalación, No mezclar cuentas, Programar (Task Scheduler) (+1 more)

### Community 20 - "Community 20"
Cohesion: 0.42
Nodes (8): str, collect_nav(), explore_dev_after_login(), login_dev(), login_old(), main(), Explora módulos H-L antiguo y dev para comparación., scrape_page()

### Community 21 - "Community 21"
Cohesion: 0.22
Nodes (8): 1) Instalar dependencias, 2) Configurar OAuth Gmail, 3) Ejecutar agente (manual), 4) Programar cada 30 minutos (Windows Task Scheduler), 5) Generar informe mensual, 6) Extraccion de transferencias (Santander), 7) Finanzas unificado (boletas foto + merge), Agente boletas Lider (Gmail)

### Community 22 - "Community 22"
Cohesion: 0.50
Nodes (7): classify_task(), get_client(), get_models(), OpenAI, str, resolve_models(), stream_with_fallback()

### Community 23 - "Community 23"
Cohesion: 0.25
Nodes (7): dry_run, easy_apply_only, keywords, location, max_applications_per_run, max_jobs_to_scan, pause_between_applications_sec

### Community 24 - "Community 24"
Cohesion: 0.25
Nodes (7): dry_run, easy_apply_only, keywords, location, max_applications_per_run, max_jobs_to_scan, pause_between_applications_sec

### Community 25 - "Community 25"
Cohesion: 0.43
Nodes (6): load_rows(), main(), Path, str, Reporte mensual desde finanzas_movimientos.csv., summarize()

### Community 26 - "Community 26"
Cohesion: 0.33
Nodes (5): dev, dashboard_nav, modules, old, old_nav

### Community 27 - "Community 27"
Cohesion: 0.60
Nodes (4): build_monthly_report(), main(), Path, str

## Knowledge Gaps
- **223 isolated node(s):** `allow`, `aliases`, `_comment`, `list`, `enabled` (+218 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **48 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `entries` connect `Community 18` to `Community 1`, `Community 37`, `Community 38`, `Community 39`, `Community 40`, `Community 41`, `Community 42`, `Community 43`, `Community 44`, `Community 45`, `Community 46`, `Community 47`, `Community 48`, `Community 49`, `Community 50`, `Community 51`, `Community 52`, `Community 53`, `Community 54`, `Community 55`, `Community 56`, `Community 57`, `Community 58`, `Community 59`, `Community 60`, `Community 61`, `Community 62`, `Community 63`, `Community 64`, `Community 65`, `Community 66`, `Community 67`, `Community 68`, `Community 69`, `Community 70`, `Community 71`, `Community 72`, `Community 73`, `Community 74`?**
  _High betweenness centrality (0.068) - this node is a cross-community bridge._
- **Why does `skills` connect `Community 1` to `Community 18`?**
  _High betweenness centrality (0.051) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `process_image_file()` (e.g. with `file_sha256()` and `find_receipt_duplicate()`) actually correct?**
  _`process_image_file()` has 9 INFERRED edges - model-reasoned connections that need verification._
- **What connects `allow`, `aliases`, `_comment` to the rest of the system?**
  _242 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.13568627450980392 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.0425531914893617 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.13360323886639677 - nodes in this community are weakly interconnected._