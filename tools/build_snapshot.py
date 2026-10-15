"""Turn Power BI query results (data/raw/*.csv) into data/snapshot.json for Rolly.

The CSVs come from DAX queries run against the "Sales Analysis" model
(see GAPS.md). data/ is git-ignored: it holds real customer data.

    python -I tools/build_snapshot.py
"""
import csv, json, pathlib, re
from datetime import date, datetime

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
OUT = ROOT / "data" / "snapshot.json"


def rows(name):
    with open(RAW / name, encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = [re.sub(r"^.*\[|\]$", "", h) for h in next(reader)]
        return [dict(zip(header, r)) for r in reader]


def num(s):
    try:
        return float(s) if s not in ("", None) else 0.0
    except ValueError:
        return 0.0


def nz_date(s):
    """Power BI CSV dates are d/m/yyyy (en-NZ)."""
    if not s:
        return None
    return datetime.strptime(s.split(" ")[0], "%d/%m/%Y").date()


def us_date(s):
    """Sales plan contract dates arrive as m/d/yyyy text."""
    try:
        d = datetime.strptime(s, "%m/%d/%Y").date()
        return d if d.year > 1990 else None
    except ValueError:
        return None


NOT_A_PERSON = re.compile(r"^(e-?mail|no email|contact|\*|cash sale)", re.I)


def contact_name(raw):
    raw = (raw or "").strip()
    m = re.match(r"^e-?mail\s*-?\s*(.+)$", raw, re.I)
    if m and m.group(1).strip():
        raw = m.group(1).strip()
    elif NOT_A_PERSON.match(raw):
        return ""
    return raw.strip(" -")


def main():
    accounts = rows("accounts.csv")
    as_of = max(nz_date(a["lastInv"]) for a in accounts if a["lastInv"])
    cutoff = date(as_of.year - 1, as_of.month, as_of.day)

    # 12 month slots ending with as_of's month
    months = []
    y, m = as_of.year, as_of.month
    for _ in range(12):
        months.append((y, m))
        m -= 1
        if m == 0:
            y, m = y - 1, 12
    months.reverse()

    monthly = {}
    for r in rows("monthly.csv"):
        d = nz_date(r["DocMnthStart"])
        monthly.setdefault(r["CardCode"], {})[(d.year, d.month)] = (num(r["t"]), num(r["v"]))

    out_acc = []
    for a in accounts:
        last = nz_date(a["lastInv"])
        series = monthly.get(a["code"], {})
        out_acc.append({
            "id": a["code"],
            "name": a["name"],
            "seg": a["seg"],
            "island": a["island"] if a["island"] not in ("", "NA") else "",
            "city": a["city"],
            "territory": a["territory"],
            "owner": "" if a["owner"].startswith("-No Sales") else a["owner"],
            "parent": a["parent"] if a["parent"] != a["name"] else "",
            "contact": contact_name(a["contact"]),
            "phone": a["phone"],
            "status": "Customer" if last and last >= cutoff else "Lapsed",
            "lastInv": last.isoformat() if last else None,
            "t12": round(num(a["t12"]), 1),
            "v12": round(num(a["v12"])),
            "inv12": int(num(a["inv12"])),
            "unpaid": round(num(a["open"])),
            "months": [round(series.get(k, (0, 0))[0], 1) for k in months],
        })
    out_acc.sort(key=lambda x: -x["v12"])

    stock = []
    for s in rows("stock.csv"):
        on, com = num(s["onHand"]), num(s["committed"])
        weekly = num(s["sold12w"]) / 12
        stock.append({
            "code": s["code"], "name": s["name"], "group": s["group"], "unit": s["unit"] or "",
            "onHand": on, "committed": com, "available": round(on - com, 1),
            "weeksCover": round((on - com) / weekly, 1) if weekly > 0 else None,
        })

    prices = []
    for p in rows("prices.csv"):
        if not p["ItemCode"]:
            continue
        prices.append({
            "code": p["ItemCode"], "name": p["ItemNameInv"], "lines": int(num(p["lines"])),
            "qty": num(p["qty"]), "tonnes": num(p["tonnes"]), "value": round(num(p["value"])),
            "perUnit": num(p["perUnit"]) or None, "perTonne": num(p["perTonne"]) or None,
        })
    prices.sort(key=lambda x: -x["value"])

    plan = []
    for p in rows("plan.csv"):
        start, end = us_date(p["Contract Start"]), us_date(p["Contract End"])
        plan.append({
            "client": p["Client"], "relationship": p["Relationship"],
            "start": start.isoformat() if start else None, "end": end.isoformat() if end else None,
            "vol12": num(p["vol12"]), "rev12": round(num(p["rev12"])), "price": num(p["price"]) or None,
        })

    contracts = build_contracts() if (RAW / "contracts.csv").exists() else []
    portal = build_portal(out_acc) if (RAW / "ar_balances.csv").exists() else None

    active = [a for a in out_acc if a["status"] == "Customer"]
    t12 = sum(a["t12"] for a in out_acc)
    v12 = sum(a["v12"] for a in out_acc)
    snapshot = {
        "meta": {
            "source": "Power BI · Sales Analysis (SAP Business One via dataflow; sales plan from SharePoint)",
            "asOf": as_of.isoformat(),
            "generated": date.today().isoformat(),
            "months": [f"{y}-{m:02d}" for y, m in months],
        },
        "kpis": {
            "customers12": len(active), "accounts": len(out_acc),
            "t12": round(t12), "v12": round(v12),
            "perTonne": round(v12 / t12) if t12 else None,
        },
        "accounts": out_acc, "stock": stock, "prices": prices, "plan": plan,
        "contracts": contracts,
        "portal": portal,
    }
    OUT.write_text(json.dumps(snapshot, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(out_acc)} accounts ({len(active)} active), "
          f"{len(stock)} stock items, {len(prices)} prices, {len(plan)} plan rows, "
          f"{len(contracts)} contracts, as of {as_of}")


def build_portal(accounts):
    """Per-customer portal pages: payment position and recent orders.

    Sources (data/raw):
      ar_balances.csv     Financial result · JDT1 per business partner: balance, last payment, paid/invoiced 90 days
      invoices_12m.csv    Financial result · OINV invoices from the last 12 months
      invoices_open.csv   Financial result · OINV invoices since 2023 with PaidSys < DocTotal
      order_lines_90d.csv Sales Analysis   · invoiced product lines, last 90 days

    Chain stores (Mitre 10, Bunnings, ...) are billed to a head-office account, so the
    balance lives on the parent. Open items are found by allocating the account's
    balance to its most recent invoices (oldest invoices are taken as paid first).
    """
    ar = {r["ShortName"]: r for r in rows("ar_balances.csv")}
    as_of = max(nz_date(r["lastActivity"]) for r in ar.values() if r["lastActivity"])

    invoices = {}
    for name in ("invoices_open.csv", "invoices_12m.csv"):
        if not (RAW / name).exists():
            continue
        for r in rows(name):
            invoices[r["docNum"]] = {
                "code": r["code"], "no": r["docNum"], "date": nz_date(r["date"]), "due": nz_date(r["due"]),
                "total": num(r["total"]), "paidSys": num(r["paid"]), "ref": r["ref"].strip(),
            }

    names = {a["id"]: a["name"] for a in accounts}
    parent_of = {a["id"]: a["parent"] for a in accounts if a["parent"]}

    def bill_to(code):
        p = parent_of.get(code)
        if p and p in ar and (code not in ar or num(ar[code]["balance"]) == 0 and num(ar[p]["balance"]) != 0):
            return p
        return code

    # allocate each billing account's balance over its group's invoices, newest first
    open_amt = {}
    groups = {}
    for inv in invoices.values():
        groups.setdefault(bill_to(inv["code"]), []).append(inv)
    for acct, invs in groups.items():
        remaining = num(ar.get(acct, {}).get("balance", "0"))
        for inv in sorted(invs, key=lambda i: (i["date"], i["no"]), reverse=True):
            if remaining <= 0.005:
                break
            if inv["total"] <= 0:  # rebates / credits are not open items
                continue
            amt = min(inv["total"], remaining)
            open_amt[inv["no"]] = round(amt, 2)
            remaining -= amt

    def ageing(acct):
        buckets = {"current": 0.0, "d1_30": 0.0, "d31_60": 0.0, "d61_90": 0.0, "d90": 0.0}
        for inv in groups.get(acct, []):
            amt = open_amt.get(inv["no"], 0)
            if not amt:
                continue
            late = (as_of - inv["due"]).days if inv["due"] else 0
            key = "current" if late <= 0 else "d1_30" if late <= 30 else "d31_60" if late <= 60 else "d61_90" if late <= 90 else "d90"
            buckets[key] += amt
        return {k: round(v, 2) for k, v in buckets.items()}

    orders = {}
    for r in rows("order_lines_90d.csv") if (RAW / "order_lines_90d.csv").exists() else []:
        o = orders.setdefault(r["DocNum"], {"code": r["CardCode"], "no": r["DocNum"], "date": nz_date(r["DocDate"]), "lines": []})
        o["lines"].append({"item": r["ItemNameInv"], "qty": num(r["qty"]), "t": num(r["tonnes"]), "v": num(r["value"])})

    out = {}
    for a in accounts:
        code = a["id"]
        acct = bill_to(code)
        bal = ar.get(acct)
        own = sorted([i for i in invoices.values() if i["code"] == code], key=lambda i: (i["date"], i["no"]), reverse=True)
        inv_list = []
        for i in own[:15]:
            o = open_amt.get(i["no"], 0)
            status = "Paid" if not o else ("Overdue" if i["due"] and i["due"] < as_of else "Open")
            inv_list.append({"no": i["no"], "date": i["date"].isoformat(), "due": i["due"].isoformat() if i["due"] else None,
                             "total": round(i["total"], 2), "open": o, "status": status, "ref": i["ref"]})
        ords = sorted([o for o in orders.values() if o["code"] == code], key=lambda o: (o["date"], o["no"]), reverse=True)
        refs = {i["no"]: i["ref"] for i in own}
        out[code] = {
            "billTo": acct, "billToName": names.get(acct, acct) if acct != code else "",
            "balance": round(num(bal["balance"]), 2) if bal else 0.0,
            "lastPay": nz_date(bal["lastPay"]).isoformat() if bal and bal["lastPay"] else None,
            "paid90": round(num(bal["paid90"]), 2) if bal else 0.0,
            "invoiced90": round(num(bal["invoiced90"]), 2) if bal else 0.0,
            "ageing": ageing(acct),
            "ownOpen": round(sum(open_amt.get(i["no"], 0) for i in own), 2),
            "invoices": inv_list,
            "orders": [{"no": o["no"], "date": o["date"].isoformat(), "ref": refs.get(o["no"], ""), "lines": o["lines"]} for o in ords[:12]],
        }
    print(f"portal: {len(out)} customers, AR as of {as_of}, {len(invoices)} invoices, {len(orders)} orders (90 days)")
    return {"asOf": as_of.isoformat(), "customers": out}


def build_contracts():
    """Key Contracts Register (SharePoint Excel via Power BI), one entry per contract.

    The register has one row per rate line; lines sharing a contract number (or,
    when the number is blank, the same company and services) are grouped.
    """
    def contract_key(no, company, services):
        return re.sub(r"[^A-Za-z0-9_-]+", "-", no or f"{company}-{services}")[:80].strip("-")

    # "Contract Link" from the register: a SharePoint URL, or sometimes just a file name
    links = {}
    if (RAW / "contract_links.csv").exists():
        for r in rows("contract_links.csv"):
            link = r["Contract Link"].strip()
            if not link or not r["Company"].strip():
                continue
            k = contract_key(r["Contract #"].strip(), r["Company"].strip(), r["Services Contracted"].strip())
            if link.startswith("https://") and not links.get(k, "").startswith("https://"):
                links[k] = link
            links.setdefault(k, link)

    by_key = {}
    for r in rows("contracts.csv"):
        company = r["Company"].strip()
        if not company:
            continue
        no = r["Contract #"].strip()
        key = contract_key(no, company, r["Services Contracted"].strip())
        start, end = nz_date(r["StartsDate1"]), nz_date(r["ExpiryDate1"])
        c = by_key.setdefault(key, {
            "key": key, "no": no, "status": r["Status"], "type": r["Contract Type (dropdown)"],
            "company": company, "start": start.isoformat() if start else None,
            "end": end.isoformat() if end and end.year < 3000 else None,
            "term": num(r["Term (Yrs.)"]) or None,
            "adjust": r["Adjust Rate"].strip(), "anniversary": r["Adjust anniver"].strip(),
            "volume": num(r["Volume (annum)"]) or None, "volUom": r["Vol UOM"].strip(),
            "comments": re.sub(r"\s{2,}", " ", r["Comments"]).strip(), "lines": [],
            "link": links.get(key, "") if links.get(key, "").startswith("https://") else "",
            "linkNote": "" if links.get(key, "").startswith("https://") else links.get(key, ""),
        })
        # keep the latest expiry when lines differ by a day
        if c["end"] and end and end.year < 3000 and end.isoformat() > c["end"]:
            c["end"] = end.isoformat()
        c["lines"].append({
            "services": r["Services Contracted"].strip(), "item": r["Rate Item"].strip(),
            "rate": num(r["rate"]) or None, "uom": r["Rate UOM"].strip(),
        })
    return sorted(by_key.values(), key=lambda c: (c["end"] or "9999", c["company"]))


if __name__ == "__main__":
    main()
