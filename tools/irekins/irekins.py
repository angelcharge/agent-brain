#!/usr/bin/env python3
"""Ielādē biedrības "Riekstu 11" rēķinu uzskaiti no i-rekins.lv un pārvērš md failos.

Lietošana:
    python irekins.py fetch --from 2019-09 --to 2026-08 [--refresh]
    python irekins.py convert
    python irekins.py run --from 2026-09 --to 2026-09
"""
import argparse
import os
import sys
import time
from pathlib import Path

import requests

REPO_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = REPO_ROOT / "temp" / "irekins" / "raw"
OUT_DIR = REPO_ROOT / "r11" / "rekini"

BASE_URL = "https://i-rekins.lv/admin.php"
REQUEST_PAUSE_S = 1.0


def load_env(path: Path) -> None:
    """Nolasa KEY=VALUE rindas no .env; jau iestatītie vides mainīgie ir prioritāri."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def parse_month_arg(value: str) -> tuple[int, int]:
    try:
        year, month = (int(x) for x in value.split("-"))
    except ValueError:
        raise argparse.ArgumentTypeError(f"mēnesis jānorāda formātā GGGG-MM, nevis '{value}'")
    if not 1 <= month <= 12:
        raise argparse.ArgumentTypeError(f"nederīgs mēnesis: '{value}'")
    return year, month


def month_range(start: tuple[int, int], end: tuple[int, int]):
    year, month = start
    while (year, month) <= end:
        yield year, month
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)


def is_login_page(html: str) -> bool:
    return "name='auth'" in html or 'name="auth"' in html


def login(session: requests.Session) -> None:
    user = os.environ.get("IREKINS_LOGIN")
    password = os.environ.get("IREKINS_PASSWORD")
    if not user or not password:
        sys.exit("Kļūda: .env failā jānorāda IREKINS_LOGIN un IREKINS_PASSWORD.")
    resp = session.post(
        BASE_URL,
        data={"login": user, "password": password, "check": "Pieteikšanās"},
        timeout=30,
    )
    resp.raise_for_status()
    if is_login_page(resp.text):
        sys.exit("Kļūda: i-rekins.lv pieteikšanās neizdevās (pārbaudi login/paroli).")
    # Bez izvēlēta projekta (mājas) rēķinu saraksts ir tukšs
    resp = session.get(
        BASE_URL,
        params={"act": "set_pr_id", "id": os.environ.get("IREKINS_PROJECT_ID", "23")},
        timeout=30,
    )
    resp.raise_for_status()


def month_params(year: int, month: int, page: int = 1) -> dict:
    return {
        "act": "control",
        "key": "15",
        "type": "",
        "sort": "",
        "value": "",
        "p": str(page),
        "max": "200",
        "month_s": str(month),
        "year_s": str(year),
        "personal_count_f": "",
        "type_of_private_post": "0",
        "object_name_field": os.environ.get("IREKINS_OBJECT_ID", "1161"),
        "counts_type_id": "1",
        "submitted": "Meklēšana",
        "printview": "1",
    }


def fetch_month(session: requests.Session, year: int, month: int) -> str:
    resp = session.get(BASE_URL, params=month_params(year, month), timeout=60)
    resp.raise_for_status()
    resp.encoding = "utf-8"
    if is_login_page(resp.text):
        sys.exit("Kļūda: sesija beigusies — i-rekins.lv atgrieza pieteikšanās lapu.")
    return resp.text


def cmd_fetch(start, end, refresh: bool) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers["User-Agent"] = "riekstu11-irekins-export/1.0"
    logged_in = False
    for year, month in month_range(start, end):
        target = RAW_DIR / f"{year:04d}-{month:02d}.html"
        if target.exists() and not refresh:
            print(f"{target.name}: jau ielādēts, izlaižu")
            continue
        if not logged_in:
            login(session)
            logged_in = True
        html = fetch_month(session, year, month)
        target.write_text(html, encoding="utf-8")
        print(f"{target.name}: saglabāts ({len(html)} baiti)")
        time.sleep(REQUEST_PAUSE_S)


# Fiksētās kolonnas rēķinu sarakstā; viss starp tām ir mēneša pakalpojumi
LEAD_COLS = ["Rēķina numurs", "Dzīvoklis", "Vārds Uzvārds / Firma", "Pers. konts"]
TAIL_COLS = ["Summa bez PVN", "Aprēķins", "Parāds/ pārmaksa", "Sods", "Samaksai"]
SUMMARY_COLS = ["Aprēķins", "Parāds/ pārmaksa", "Sods", "Samaksai"]
MONTH_NAMES = ["janvāris", "februāris", "marts", "aprīlis", "maijs", "jūnijs", "jūlijs",
               "augusts", "septembris", "oktobris", "novembris", "decembris"]


def cell_texts(tr) -> list[str]:
    return [" ".join(c.get_text(" ", strip=True).split()) for c in tr.find_all(["th", "td"])]


def to_number(text: str) -> float:
    return float(text.replace(",", ".").replace("\xa0", "").replace(" ", "") or 0)


def parse_month(html: str) -> dict:
    """Atgriež {'services': [...], 'rows': [...], 'totals': {...}}; rows ir tukšs, ja mēnesī nav rēķinu."""
    from bs4 import BeautifulSoup

    table = BeautifulSoup(html, "html.parser").find("table", class_="table_printview_con")
    if table is None:
        raise ValueError("lapā nav rēķinu tabulas (table_printview_con)")
    trs = table.find_all("tr")
    header = cell_texts(trs[0])
    missing = [c for c in TAIL_COLS if c not in header]
    if header[:1] != LEAD_COLS[:1] or missing:
        raise ValueError(f"negaidīta tabulas galvene (trūkst {missing}): {header}")
    # Pakalpojumi ir starp fiksētajām sākuma kolonnām un "Summa bez PVN"; aiz tās var būt PVN kolonnas
    amount_cols = header[len(LEAD_COLS):]
    services = amount_cols[:amount_cols.index("Summa bez PVN")]
    columns = LEAD_COLS + amount_cols

    rows, totals = [], {}
    for tr in trs[1:]:
        cells = cell_texts(tr)
        if cells and cells[0].startswith("Kopā"):
            totals = {col: to_number(v) for col, v in zip(amount_cols, cells[1:])}
            continue
        if len(cells) != len(columns):
            continue
        row = dict(zip(columns, cells))
        row["Dzīvoklis"] = row["Dzīvoklis"].split("-")[-1].strip()
        for col in amount_cols:
            row[col] = to_number(row[col])
        rows.append(row)
    return {"services": services, "rows": rows, "totals": totals}


def fmt(value: float) -> str:
    return f"{value:.2f}".replace(".", ",")


def apartment_sort_key(apt: str):
    digits = "".join(ch for ch in apt if ch.isdigit())
    return (int(digits) if digits else 0, apt)


def render_month_md(data: dict, year: int, month: int) -> str:
    rows = sorted(data["rows"], key=lambda r: apartment_sort_key(r["Dzīvoklis"]))
    services, totals = data["services"], data["totals"]
    title = f"{MONTH_NAMES[month - 1]} {year}"
    lines = [
        f"# Rēķini — {title}",
        "",
        f"> Avots: i-rekins.lv, Biedrība Riekstu 11 → Uzskaite → Rēķini → Saraksts ({title}), "
        f"rēķinu veids \"Komunālie\". Ielādēts {time.strftime('%d.%m.%Y.')} Summas EUR.",
        "",
        "## Kopsavilkums",
        "",
        "| Rādītājs | EUR |",
        "|---|---|",
    ]
    lines += [f"| {col} | {fmt(totals.get(col, 0))} |" for col in SUMMARY_COLS]
    lines += [
        "",
        "## Rēķini pa dzīvokļiem",
        "",
        "| Dz. | Īpašnieks | Rēķina Nr. | Aprēķins | Parāds/ pārmaksa | Sods | Samaksai |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['Dzīvoklis']} | {r['Vārds Uzvārds / Firma']} | {r['Rēķina numurs']} | "
            + " | ".join(fmt(r[c]) for c in SUMMARY_COLS) + " |"
        )
    lines.append("| **Kopā** | | | " + " | ".join(f"**{fmt(totals.get(c, 0))}**" for c in SUMMARY_COLS) + " |")
    lines += [
        "",
        "## Pakalpojumi pa dzīvokļiem",
        "",
        "| Dz. | " + " | ".join(services) + " |",
        "|---|" + "---|" * len(services),
    ]
    for r in rows:
        lines.append(f"| {r['Dzīvoklis']} | " + " | ".join(fmt(r[s]) for s in services) + " |")
    lines.append("| **Kopā** | " + " | ".join(f"**{fmt(totals.get(s, 0))}**" for s in services) + " |")
    lines += [
        "",
        "Parāds/ pārmaksa: pozitīva summa — parāds no iepriekšējiem periodiem, negatīva — pārmaksa. "
        "Samaksai = Aprēķins + Parāds/ pārmaksa + Sods.",
        "",
    ]
    return "\n".join(lines)


def render_index(months: list[tuple[int, int, dict]]) -> str:
    lines = [
        "# Rēķinu uzskaite pa mēnešiem",
        "",
        "Mēnešu kopsummas no i-rekins.lv (rēķinu veids \"Komunālie\"). Detalizēti rēķini pa dzīvokļiem "
        "un pakalpojumiem — mēneša failā `GGGG-MM.md`. Summas EUR.",
        "",
        "| Mēnesis | Rēķini | Aprēķins | Parāds/ pārmaksa | Sods | Samaksai | Fails |",
        "|---|---|---|---|---|---|---|",
    ]
    for year, month, data in sorted(months, key=lambda m: (m[0], m[1]), reverse=True):
        t = data["totals"]
        lines.append(
            f"| {year}-{month:02d} | {len(data['rows'])} | "
            + " | ".join(fmt(t.get(c, 0)) for c in SUMMARY_COLS)
            + f" | `{year:04d}-{month:02d}.md` |"
        )
    lines.append("")
    return "\n".join(lines)


def cmd_convert() -> None:
    raw_files = sorted(RAW_DIR.glob("*.html"))
    if not raw_files:
        sys.exit(f"Nav ielādētu failu mapē {RAW_DIR}. Vispirms palaid 'fetch'.")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    months = []
    for path in raw_files:
        year, month = parse_month_arg(path.stem)
        data = parse_month(path.read_text(encoding="utf-8"))
        target = OUT_DIR / f"{path.stem}.md"
        if not data["rows"]:
            print(f"{path.stem}: rēķinu nav, izlaižu")
            target.unlink(missing_ok=True)
            continue
        target.write_text(render_month_md(data, year, month), encoding="utf-8")
        months.append((year, month, data))
        print(f"{target.name}: {len(data['rows'])} rēķini, samaksai {fmt(data['totals'].get('Samaksai', 0))} EUR")
    (OUT_DIR / "00_saraksts.md").write_text(render_index(months), encoding="utf-8")


def main() -> None:
    load_env(REPO_ROOT / ".env")
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("fetch", "run"):
        p = sub.add_parser(name)
        p.add_argument("--from", dest="start", type=parse_month_arg, required=True, help="GGGG-MM")
        p.add_argument("--to", dest="end", type=parse_month_arg, required=True, help="GGGG-MM")
        p.add_argument("--refresh", action="store_true", help="ielādēt vēlreiz arī jau saglabātos mēnešus")
    sub.add_parser("convert")
    args = parser.parse_args()

    if args.command in ("fetch", "run"):
        if args.start > args.end:
            parser.error("--from nevar būt vēlāks par --to")
        cmd_fetch(args.start, args.end, args.refresh)
    if args.command in ("convert", "run"):
        cmd_convert()


if __name__ == "__main__":
    main()
