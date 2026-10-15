# Rolly ↔ Power BI "Sales Analysis" — what's there, what's missing

Source: `Downloads\Sales Analysis.pbip` (Import model; SAP Business One tables via a Power BI dataflow,
plus a SharePoint Excel sales plan). Read on 15 Oct 2026 from the live model in Power BI Desktop.

## What the model holds

| Table | SAP B1 source | Rows / range | Useful columns |
|---|---|---|---|
| Customers - OCRD | Business partners | 2,218 (1,669 customers, rest suppliers) | CardCode, CardName, GroupName (segment), SlpName (rep), U_Territory, City, Island, ParentCustomer, CntctPrsn, Phone1/2, Address |
| SalesHeaders - OINV | A/R invoices | 11,619 · 23 Apr 2021 – 12 Oct 2026 | DocNum, DocDate, DocDueDate, CardCode, totals, GST, Freight, PaidSys |
| SalesLines - INV1 | Invoice lines | 24,871 | ItemCode, Quantity, Weight(T), Price/UOM, line value, WhsName, ShipDate; calc: SalesValue, SalesVolume (t), DeliveryCost |
| Items - OITM | Items | 347 columns | ItemName, ItmsGrpNam, SalUnitMsr, OnHand, IsCommited, OnOrder |
| SALES PLAN (PBI) | SharePoint Excel | 1,048 rows · Oct 2023 – Sep 2027 | Client, Relationship, Contract Start/End, Month, Volume, Price |
| Daily Production targets | — | daily | DailyPlantOutputTarget, Capacity, MaintenanceDay |
| OrderPerformance | Plant MES | — | production run data (not sales) |
| Date, FinPeriod - OFPR, GLAccounts - OACT | — | — | NZ financial year/month (FinnYR, FinMnth) |

Measures worth reusing: `AveSalesPrice` ($/t, excl. delivery), `AveDeliveryCost`, `Revenue` (plan), `StorageReq` / `NetStorageReq`.
Report pages: Pellet Sales Analysis, Pellet Sales Trends, Biomass Sales Analysis, Biomass Sales Trends, Sales Forecast, Top 5.

Last 12 months by segment (tonnes · NZ$ excl. GST): Commercial/Industrial 106,492 t · $30.1m; Export 78,528 t · $24.0m;
Wholesale/Retail 8,924 t · $5.6m; Biomass $1.2m; Residential $42k.

## Rolly screen by screen

| Rolly screen / field | Status | Source in model | Notes |
|---|---|---|---|
| Accounts list: name, segment, region, owner | ✅ Have | OCRD CardName, GroupName, Island/City/U_Territory, SlpName | Filter CardType = "C"; exclude "Customers DO NOT USE" |
| Accounts: status (Customer / Prospect / Lead / Lost) | ⚠️ Partial | Derive "Customer" from invoices in last 12 months | Prospects, leads and lost are CRM data, not SAP |
| Accounts: est. tonnes/yr | ⚠️ Partial | Actual t last 12 months from INV1 | "Estimated" potential is CRM data |
| Contacts: name, title, role | ❌ Missing | Only OCRD CntctPrsn + Phone1 (one person) | Need SAP contact persons **OCPR** (name, position, email, phone) in the dataflow |
| Contact email | ❌ Missing | — | OCRD E_Mail / OCPR E_MailL not loaded |
| From SAP panel: customer no. | ✅ Have | OCRD CardCode | |
| From SAP: sales last 12 months (t, $) | ✅ Have | INV1 SalesVolume, SalesValue | |
| From SAP: monthly tonnes chart | ✅ Have | INV1 by Date[MnthYr] | |
| From SAP: current orders | ❌ Missing | — | Model has invoices only. Need sales orders **ORDR/RDR1** (open qty, due date) |
| From SAP: credit status | ❌ Missing | OINV PaidSys only | Need OCRD Balance / CreditLine, or open invoices |
| Sales, stock & orders: stock on hand | ✅ Have | OITM OnHand | Sell items only; units vary (t, bags) |
| Stock: on open orders / available | ✅ Have | OITM IsCommited; available = OnHand − IsCommited | |
| Stock: weeks of cover | ⚠️ Derive | OnHand ÷ avg weekly sales from INV1 | |
| Current orders table | ❌ Missing | — | Needs ORDR/RDR1 |
| Price list | ⚠️ Partial | Realised prices (AveSalesPrice by item) | List prices need SAP price lists **ITM1/OPLN** |
| Dashboard: won this quarter, stalled deals | ❌ Not SAP | — | Pipeline data lives in Rolly itself |
| Supply agreements (Stage 2) | ✅ Have (plan) | SALES PLAN: Client, Contract Start/End, monthly Volume, Price | Join to invoices by customer for planned vs delivered |
| Forecast (Stage 2) | ✅ Have | SALES PLAN Revenue + plant capacity | |
| Pipeline, deals, activities, comms | ❌ Not SAP | — | Rolly's own data (and Outlook/Teams via Graph) |
| Customer portal: invoices | ✅ Have | OINV DocNum, DocDate, DocDueDate, total, PaidSys | Status = paid if PaidSys ≥ total |
| Customer portal: orders, deliveries, quotes | ❌ Missing | — | Need ORDR, ODLN, OQUT |

## Data issues spotted

- **SALES PLAN Client ↔ customer**: plan uses free-text client names, not CardCode, so it can't join to customers reliably. Add CardCode to the sheet.
- **Negative tonnes** on some items (e.g. one pallet SKU nets to −434 t): credit notes or returns mixed into invoices. Check before showing run rates.
- **1,772 invoice lines with no item code** (service/GL lines). Exclude from product views.
- **Units differ by item**: Price/UOM is per bag for 15 kg export lines, per pallet or per tonne elsewhere. Use $/t (AveSalesPrice) for comparisons.
- Sawdust, shavings and chip have zero tonnes (Weight(T) is blank for them); they are sold in other units.
- A future ship date (Aug 2028) on a sawdust line.
- The M query hard-codes one weight correction (2025.54 → 30.69).
- 28 auto date tables (Auto date/time is on) and two bi-directional relationships; fine for now, worth tidying.

## To ask IT / the dataflow owner

1. Add **OCPR** (contact persons) and OCRD E_Mail.
2. Add **ORDR/RDR1** (open sales orders), and ideally **ODLN** (deliveries) and **OQUT** (quotes) for the portal.
3. Add **ITM1/OPLN** (price lists) and OCRD Balance/CreditLine.
4. Add CardCode to the SharePoint sales plan.
