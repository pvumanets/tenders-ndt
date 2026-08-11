"""P4: write tenders.csv, tenders.md, priority-fit.md from scored-list."""
from __future__ import annotations

import csv
import re
from collections import Counter
from pathlib import Path

COLUMNS = [
    "rank",
    "score",
    "tier",
    "fit_reason",
    "tender_id",
    "title",
    "url",
    "status",
    "price_rub",
    "location",
    "customer_name",
    "customer_inn",
    "customer_kpp",
    "deadline_msk",
    "source_etp",
    "methods",
    "contact_name",
    "contact_phone",
    "contact_email",
    "docs_path",
    "notes",
    "card_error",
]


def _clean_loc(s: str | None) -> str:
    if not s:
        return ""
    s = re.sub(r"\s+", " ", s).strip()
    s = re.sub(r",?\s*Russia,?\s*RU\.?$", "", s, flags=re.I).strip().rstrip(",")
    return s


def _md_escape(s: str) -> str:
    return (s or "").replace("|", "\\|").replace("\n", " ")


def write_artifacts(out_dir: Path, rows: list[dict]) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    summary = dict(Counter(r.get("tier") or "pool" for r in rows))
    for k in ("L1", "L2", "L3", "noise", "pool"):
        summary.setdefault(k, 0)

    # CSV
    csv_path = out_dir / "tenders.csv"
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            row = {c: r.get(c, "") for c in COLUMNS}
            row["location"] = _clean_loc(str(row.get("location") or ""))
            if not row.get("notes") and r.get("card_error"):
                row["notes"] = f"card_error:{r['card_error']}"
            w.writerow(row)

    # tenders.md — compact table (top by rank already sorted by score)
    md_path = out_dir / "tenders.md"
    lines = [
        f"# Тендеры — прогон {out_dir.name}",
        "",
        f"**всего:** {len(rows)} · **L1:** {summary['L1']} · **L2:** {summary['L2']} · "
        f"**L3:** {summary['L3']} · **noise:** {summary['noise']} · **pool:** {summary['pool']}",
        "",
        "| rank | score | tier | title | price | location | deadline |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rows[:200]:
        title = _md_escape(str(r.get("title") or "")[:80])
        url = r.get("url") or ""
        title_cell = f"[{title}]({url})" if url else title
        lines.append(
            "| {rank} | {score} | {tier} | {title} | {price} | {loc} | {dl} |".format(
                rank=r.get("rank", ""),
                score=r.get("score", ""),
                tier=r.get("tier", ""),
                title=title_cell,
                price=_md_escape(str(r.get("price_rub") or "")[:24]),
                loc=_md_escape(_clean_loc(str(r.get("location") or ""))[:40]),
                dl=_md_escape(str(r.get("deadline_msk") or "")[:16]),
            )
        )
    if len(rows) > 200:
        lines.append("")
        lines.append(f"_… ещё {len(rows) - 200} строк в `tenders.csv`_")
    lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    # priority-fit.md
    fit_path = out_dir / "priority-fit.md"
    fit_lines = [
        f"# Приоритетные тендеры (fit)",
        "",
        f"**прогон:** {out_dir.name}",
        f"**из пула:** {len(rows)}",
        f"**L1 / L2 / L3:** {summary['L1']} / {summary['L2']} / {summary['L3']}",
        "",
    ]
    for tier in ("L1", "L2", "L3"):
        subset = [r for r in rows if r.get("tier") == tier]
        fit_lines.append(f"## {tier}")
        fit_lines.append("")
        if not subset:
            fit_lines.append("_пусто_")
            fit_lines.append("")
            continue
        fit_lines.append("| # | score | methods | title | price | location | deadline | url |")
        fit_lines.append("| --- | --- | --- | --- | --- | --- | --- | --- |")
        for i, r in enumerate(subset, start=1):
            title = _md_escape(str(r.get("title") or "")[:100])
            fit_lines.append(
                "| {i} | {score} | {methods} | {title} | {price} | {loc} | {dl} | {url} |".format(
                    i=i,
                    score=r.get("score", ""),
                    methods=_md_escape(str(r.get("methods") or "")[:40]),
                    title=title,
                    price=_md_escape(str(r.get("price_rub") or "")[:24]),
                    loc=_md_escape(_clean_loc(str(r.get("location") or ""))[:40]),
                    dl=_md_escape(str(r.get("deadline_msk") or "")[:16]),
                    url=r.get("url") or "",
                )
            )
        fit_lines.append("")
        fit_lines.append("### Карточки")
        fit_lines.append("")
        for i, r in enumerate(subset[:50], start=1):
            fit_lines.append(f"### {i}. {_md_escape(str(r.get('title') or '')[:120])}")
            fit_lines.append(f"- **id / url:** {r.get('tender_id')} · {r.get('url')}")
            fit_lines.append(f"- **почему:** {_md_escape(str(r.get('fit_reason') or ''))}")
            fit_lines.append(f"- **заказчик:** {_md_escape(str(r.get('customer_name') or ''))} ИНН {r.get('customer_inn') or '—'}")
            fit_lines.append(f"- **методы:** {r.get('methods') or '—'}")
            fit_lines.append(f"- **статус / срок:** {r.get('status') or '—'} / {r.get('deadline_msk') or '—'}")
            fit_lines.append(
                f"- **контакт:** {r.get('contact_name') or '—'}; {r.get('contact_phone') or ''}; {r.get('contact_email') or ''}"
            )
            if r.get("card_error"):
                fit_lines.append(f"- **card_error:** {r['card_error']}")
            fit_lines.append("")
        if len(subset) > 50:
            fit_lines.append(f"_… ещё {len(subset) - 50} в таблице выше / CSV_")
            fit_lines.append("")

    fit_path.write_text("\n".join(fit_lines), encoding="utf-8")
    return summary
