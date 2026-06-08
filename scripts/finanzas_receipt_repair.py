"""Repara boletas mal OCR + elimina screenshots bancarios del CSV."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

_SCRIPTS_DIR = Path(__file__).resolve().parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from finanzas_common import (
    DEFAULT_UNIFIED_CSV,
    DEFAULT_VISION_CSV,
    VISION_CSV_COLUMNS,
    ensure_csv_headers,
    merge_all_sources,
    parse_clp,
    read_csv_rows,
    resolve_data_path,
    write_unified_csv,
)
from finanzas_receipt_caption import enrich_receipt_from_caption, extract_caption_products, is_generic_product

# Captions conocidos del hilo WhatsApp 07-06-2026
KNOWN_CAPTIONS: Dict[str, str] = {
    "235844": "Diclofenaco + 2 tapsin noche + pan + vodka + snaks + primavera verduras congeladas",
    "221452": "aqua y 2 jaleas",
    "162991769144": "Italiano y Coca-Cola express",
}

PURGE_REFERENCE_IDS = frozenset({"db207f7f6965"})
PURGE_IMAGE_FRAGMENTS = frozenset({"ff93b763-cff2-44aa-a082-ae6b1ccb0163"})


def row_should_purge(row: Dict[str, str]) -> bool:
    ref = (row.get("reference_id") or row.get("source_ref") or "").strip()
    if ref in PURGE_REFERENCE_IDS:
        return True
    raw = (row.get("raw_source_file") or row.get("image_path") or "")
    return any(frag in raw for frag in PURGE_IMAGE_FRAGMENTS)


def rebuild_receipt_from_vision_rows(rows: List[Dict[str, str]]) -> Dict[str, Any]:
    first = rows[0]
    items = []
    for row in rows:
        items.append(
            {
                "product": row.get("product") or "",
                "amount": parse_clp(row.get("line_amount")),
                "category": row.get("category") or "",
            }
        )
    return {
        "store": first.get("store") or "",
        "store_branch": first.get("store_branch") or "",
        "merchant_rut": first.get("merchant_rut") or "",
        "receipt_number": first.get("receipt_number") or "",
        "purchase_date": first.get("purchase_date") or "",
        "purchase_time": first.get("purchase_time") or "",
        "purchase_datetime": first.get("purchase_datetime") or "",
        "payment_method": first.get("payment_method") or "",
        "ticket_total": parse_clp(first.get("ticket_total")),
        "items": items,
    }


def apply_caption_to_vision_rows(rows: List[Dict[str, str]], caption: str) -> List[Dict[str, str]]:
    receipt = rebuild_receipt_from_vision_rows(rows)
    enriched = enrich_receipt_from_caption(receipt, caption)
    first = rows[0]
    out: List[Dict[str, str]] = []
    for item in enriched.get("items") or []:
        out.append(
            {
                **first,
                "product": item.get("product") or "",
                "category": item.get("category") or "",
                "line_amount": str(item.get("amount") or ""),
            }
        )
    return out


def repair_vision_csv(vision_path: Path) -> Dict[str, Any]:
    rows = read_csv_rows(vision_path)
    kept: List[Dict[str, str]] = []
    purged = 0
    fixed = 0
    by_receipt: Dict[str, List[Dict[str, str]]] = {}

    for row in rows:
        if row_should_purge(row):
            purged += 1
            continue
        doc = (row.get("receipt_number") or "").strip()
        by_receipt.setdefault(doc or row.get("image_hash") or "?", []).append(row)

    for key, group in by_receipt.items():
        doc = (group[0].get("receipt_number") or "").strip()
        caption = KNOWN_CAPTIONS.get(doc, "")
        generic = all(is_generic_product(r.get("product") or "") for r in group)
        if caption and generic:
            group = apply_caption_to_vision_rows(group, caption)
            fixed += 1
        kept.extend(group)

    ensure_csv_headers(vision_path, VISION_CSV_COLUMNS)
    with vision_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=VISION_CSV_COLUMNS)
        writer.writeheader()
        for row in kept:
            writer.writerow({col: row.get(col, "") for col in VISION_CSV_COLUMNS})

    return {"vision_purged": purged, "vision_fixed": fixed, "vision_rows": len(kept)}


def repair_unified_csv(unified_path: Path) -> Dict[str, Any]:
    rows = read_csv_rows(unified_path)
    kept = [r for r in rows if not row_should_purge(r)]
    purged = len(rows) - len(kept)

    fixed = 0
    by_doc: Dict[str, List[Dict[str, str]]] = {}
    for row in kept:
        if (row.get("movement_type") or "") != "gasto":
            continue
        doc = (row.get("document_number") or "").strip()
        if doc in KNOWN_CAPTIONS:
            by_doc.setdefault(doc, []).append(row)

    for doc, group in by_doc.items():
        caption = KNOWN_CAPTIONS[doc]
        products = extract_caption_products(caption)
        if not products:
            continue
        if len(products) == 1 and len(group) == 1 and is_generic_product(group[0].get("description") or ""):
            group[0]["description"] = products[0]
            fixed += 1
        elif len(products) > 1 and all(is_generic_product(r.get("description") or "") for r in group):
            ticket = parse_clp(group[0].get("ticket_total")) or 0
            per = ticket // len(products) if ticket else 0
            if len(group) == len(products):
                for idx, row in enumerate(group):
                    row["description"] = products[idx]
                    if per:
                        row["amount_clp"] = str(per if idx < len(products) - 1 else ticket - per * (len(products) - 1))
                fixed += 1
            elif len(group) == 1:
                group[0]["description"] = caption
                fixed += 1

    write_unified_csv(unified_path, kept)
    return {"unified_purged": purged, "unified_fixed": fixed, "unified_rows": len(kept)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Repara boletas OCR + purga screenshots bancarios.")
    parser.add_argument("--unified", default=DEFAULT_UNIFIED_CSV)
    parser.add_argument("--vision", default=DEFAULT_VISION_CSV)
    parser.add_argument("--remerge", action="store_true", default=True)
    parser.add_argument("--no-remerge", action="store_false", dest="remerge")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    unified_path = resolve_data_path(args.unified)
    vision_path = resolve_data_path(args.vision)
    stats: Dict[str, Any] = {"status": "ok"}

    if vision_path.exists():
        stats.update(repair_vision_csv(vision_path))

    if args.remerge and vision_path.exists() and unified_path.parent.exists():
        merge_stats = merge_all_sources(
            unified_csv=unified_path,
            lider_csv=resolve_data_path("data/lider_receipts.csv"),
            vision_csv=vision_path,
            transferencias_csv=resolve_data_path("data/transferencias.csv"),
            registry_file=resolve_data_path("data/receipts_registry.json"),
        )
        stats["merge"] = merge_stats
        stats.update(repair_unified_csv(unified_path))
    elif unified_path.exists():
        stats.update(repair_unified_csv(unified_path))

    if args.json:
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(stats, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
