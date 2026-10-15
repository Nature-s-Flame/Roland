# Rolly · Nature's Flame CRM

Rolly is a CRM for Nature's Flame (NZ wood-pellet manufacturer, Taupō) with a customer portal.
This folder holds the clickable mock-up while the real build is planned.
Git: https://github.com/Nature-s-Flame/Rolly (branch `main`) — this repo is PUBLIC, so never commit real data.
`data/`, `artifact/` and `*.zip` are ignored.

## Layout

| Path | What it is |
|---|---|
| `rolly/index.html` | Staff CRM mock (source). Standalone HTML + vanilla JS, no build step. |
| `rolly/portal.html` | Customer portal mock (source). Linked from Rolly's sidebar and back. |
| `rolly/fonts/` | Brand fonts (Open Sans, Open Sans Condensed) used by both pages. |
| `artifact/` | Generated publish copy (fonts inlined). Don't edit; rebuild it. |
| `tools/build_artifact.py` | Builds `artifact/` from `rolly/`: `python -I tools/build_artifact.py` |
| `tools/theme_tokens.py` | One-off that added the dark palette. Already applied; don't rerun. |
| `mock-original/` | Original Claude Design source (`*.dc.html`). Reference only; needs the Design runtime to render. |
| `brand/` | Nature's Flame Style Guide (Nov 2022) PDF and font files. |
| `*.zip` | The original downloads the above were extracted from. |

## Preview and publish

- Local preview: serve the folder (`python -m http.server 5173 --bind 127.0.0.1`) and open `/rolly/index.html`.
- Published artifact (private): https://claude.ai/artifact/BWRAZEBpcQifdwJ3uwRFMj
  To update: run the build script, then publish `artifact/rolly.html` with `portal.html` as a supporting file to that URL.
- An earlier Claude Design canvas of the original mock: https://claude.ai/artifact/QHNL9hgEysohtsQztZ2eT7

## Brand rules (from the Style Guide)

- Primary: 377C green `#82A519`, 575C olive `#66783C`. Secondary: sage `#CDDCB9`, sand `#CDC896`, forest `#1D332F`.
- Type: Open Sans (body), Open Sans Condensed (headings, uppercase labels).
- Flame "swoosh" as the graphic device. Colours are CSS tokens on `:root` with a dark palette; style through tokens, not literals.
- The logo in the pages is a redrawing. Swap in the official RGB logo files when available.

## Data: current state and plan

- Sample data is hard-coded in each page's script. That is what the published artifact shows.
- Real data snapshot (local only): `data/snapshot.json`, built by `python -I tools/build_snapshot.py` from DAX query
  results in `data/raw/*.csv` (accounts, monthly, stock, prices, plan), queried from the "Sales Analysis" PBIP
  (`Downloads\Sales Analysis.pbip`) open in Power BI Desktop via the powerbi-modeling MCP. Rolly fetches
  `../data/snapshot.json` on load and switches accounts, SAP panel, stock, realised prices and the pipeline
  (from the sales plan) to real data; activities, comms, chat and the portal stay samples.
- `GAPS.md` maps each Rolly screen/field to what the semantic model has or lacks.
- Contracts: `data/raw/contracts.csv` comes from the "Key Contracts Register" PBIP (`Downloads\Key Contracts Register.pbip`,
  SharePoint Excel `Key Contract Register.xlsx`). Rolly's "Contracts & price reviews" view alerts on expired / ≤90-day
  expiry and prompts price reviews 60 days before each "Adjust anniver" date until someone confirms. Confirmations live
  in the artifact db collection `reviews` (doc id `<contractKey>__<cycle date>`); locally in localStorage `rolly.reviews`.
  The artifact declares capabilities `{db: {}, user: {scopes: ["profile"]}}` — keep them on republish (omit `capabilities`).
  (The "email" user scope is refused for this organization; the welcome uses the profile name.)
- Customer portal (`rolly/portal.html`): a demo sign-in dropdown picks any of the 303 customers and shows their
  recent invoiced orders (90 days), payment position and invoices. Sources in `data/raw`: `ar_balances.csv`,
  `invoices_12m.csv`, `invoices_open.csv` from the "Financial result" PBIP (JDT1 balances, OINV); `order_lines_90d.csv`
  from "Sales Analysis". Chain stores are billed to the parent (e.g. Mitre10HO), so balance/ageing use the billing
  account; open items = balance allocated to the newest invoices. Open (undelivered) sales orders need ORDR/RDR1.
  `build_artifact.py --with-data` embeds a portal subset as `window.ROLLY_PORTAL`.
- Prospects (agreed design, 15 Oct 2026): every deal is a multi-year supply agreement. Pipeline stages: Enquiry,
  Feasibility, Proposal, Investment decision, Negotiation, Signed (awaiting commissioning), Supplying.
  Prospects are stored in the artifact db collections `leads` (one doc per prospect, `agreements` array inside) and
  `activities` (one doc per logged activity, `lead` = prospect id); locally in localStorage `rolly.leads` /
  `rolly.activities`. Rules: required = company, product, annual volume, contact name, phone or email; a prospect
  goes Cold automatically 365 days after `coldReset` (created or revived) unless signed, with a 30-day warning;
  anyone can mark Lost (reason recorded); Cold/Lost can be revived (clock restarts); becomes Customer when its
  `sapCode` has invoices in the snapshot. Signing prepares a Key Contracts Register row to copy into the SharePoint
  workbook; the "Not yet in register" badge clears when the contract number comes through the Power BI model.
  Email/Teams capture needs Microsoft Graph (not in the artifact); activities are logged by hand meanwhile.
- Quotes: db `quotes` (Draft → Awaiting approval → Issued → Accepted/Declined; Expired derived from validUntil;
  revisions keep the number, Rev B…), `approvals/{quoteId}` and `settings/quoteTerms` writable by Editors only
  (db rules), `counters/quotes-YYYY` (number via acquire lease, format Q-YYYY-NNN), per-person
  `data/users/<id>/profile` (title, mobile, email for "Prepared by"). GM (John Goodwin) approval needed when the
  price is >10% under the product's 12-month realised price or the product has no sales history; John needs Editor
  access, salespeople Contributor. UPDATE 15 Oct 2026: EVERY quote now needs John's approval (APPROVER constant);
  approving also issues it (number, validity, frozen terms) and stamps `approval` on the quote; the creator's
  "Prepared by" details are frozen at submit (John can't read their private profile). Statuses shown: Draft →
  Awaiting approval → (Sent back) → Approved → Accepted/Declined/Expired. Signature = "John Goodwin" in the Google
  font "Homemade Apple" (CSS on screen; drawn to a canvas PNG for the PDF) — swap `signatureImage()` for a scanned
  image when John's signature arrives. PDF via jsPDF 2.5.1 (cdnjs) with brand fonts fetched from `fonts/` (published as
  artifact files). Email draft = .eml with `X-Unsent: 1` (opens as a draft in classic Outlook); in the artifact it is
  wrapped in a .zip because the download allowlist excludes .eml. Standard terms are a proposed draft pending review.
  Artifact capabilities now: `{db: {rules: [approvals write admin, settings write admin]}, user: {scopes: ["profile"]},
  downloads: {}, sample: {}}` — omit `capabilities` on republish to keep them.
- Quote form rendering (fixed 15 Oct 2026): typing in the Quote form used to call the global `render()` on every
  keystroke (needed so the live preview pane updates as you type), which destroys and recreates every `<input>`,
  including the one being typed into — this silently reversed typed text in `type="email"` fields (no
  `selectionStart`/`setSelectionRange` support to restore the caret) and dropped already-typed day/month when
  starting the year in the `type="date"` field (focus resets to the first segment on a freshly-created date
  input, with no way to restore which segment was active). Fixed at the root: `qf` input/textarea keystrokes now
  call `renderQuoteLive()` (updates only `#q-preview` and `#q-check`, never the fields) instead of `render()`;
  only `<select>`-backed `qf` fields (e.g. `qf-pricing`, which shows/hides the freight fields) still call the
  full `render()`, since selects aren't typed into character-by-character. Don't reintroduce a full `render()`
  on `qf` input/textarea keystrokes — same destructive-rebuild bug will resurface for whatever field types it.
- Quote form Company field (16 Oct 2026): `qf-company` is a text input with `list="qf-company-list"` (native
  searchable dropdown, like the existing SAP-code `datalist` fields) instead of free text. Options come from
  `companyDirectory()`: real SAP customers (`ACC` entries with `.real`, i.e. actual Power BI sales data — not
  the sample/demo `ACC` rows) plus open prospects (`LEADS` not Cold/Lost/Customer; a prospect that has become a
  Customer is left out since its SAP account entry already covers it). Typing an exact match (or picking from
  the dropdown) calls `applyCompanyToQuote()`, which overwrites contact name/role/email/phone/address/city from
  that record — all still plain inputs, so the preparer can type over any of them for a different contact at
  the same company. `quoteFromLead`/`quoteFromAccount` now call the same helper, so the three entry points
  (generic "+ Create quote", and the per-prospect/per-account "Create quote" buttons) stay in sync. Saving
  re-resolves the typed company against `companyDirectory()` and blocks with a "pick an existing customer or
  prospect, or add it as a new prospect first" error if it doesn't match — this is what forces a brand-new
  company through "+ New prospect" before it can be quoted, matching the guardrail Danie asked for. The
  "no match" hint under the field links straight to a pre-filled New Prospect form (`data-qnew-prospect`).
- Ask Rolly (chat): in the artifact it uses the `sample` capability, so questions run on each VIEWER's own Claude
  account (first use asks them to allow it). Claude gets a rules turn (who's asking, today, headline KPIs, answer
  style) plus seven page tools: find_accounts, get_account (incl. payment position, orders, contracts, quotes),
  top_customers (sales/tonnes/overdue/balance), get_contracts, get_pipeline, get_quotes, get_stock_and_prices.
  Locally (no `window.claude`) or if the viewer declines, the old scripted answers remain.
- Later (live data): add Microsoft's remote Power BI MCP server (`https://api.fabric.microsoft.com/v1/mcp/powerbi`)
  as a claude.ai custom connector named `Power BI`. Needs the tenant setting
  "Users can use the Power BI Model Context Protocol server endpoint (preview)" and an Entra app registration
  (redirect `https://claude.ai/api/mcp/auth_callback`, delegated `Dataset.Read.All`, `Workspace.Read.All`).
- Production route: a backend calling the Power BI `executeQueries` REST API with a service principal or user sign-in.

## Renamed Roland → Rolly (16 Oct 2026)

The tool was renamed from "Roland" to "Rolly": GitHub repo (`Nature-s-Flame/Roland` → `Nature-s-Flame/Rolly`,
old URL redirects), the `roland/` source folder → `rolly/`, the built `artifact/roland.html` → `artifact/rolly.html`,
and the `window.ROLAND_SNAPSHOT`/`ROLAND_PORTAL` globals → `ROLLY_SNAPSHOT`/`ROLLY_PORTAL`. The `roland.*`
localStorage keys (quotes, leads, activities, reviews, profile, portal customer choice) are now written as
`rolly.*`, but every reader falls back to the old `roland.*` key when the new one is empty, so nobody's
already-saved local data (from before this rename) goes missing — don't remove that fallback without checking
whether it's still needed. The published private artifact keeps its existing URL
(https://claude.ai/artifact/BWRAZEBpcQifdwJ3uwRFMj); only its content and displayed title changed.

## Guardrails

- Real customer contacts and pricing must not be committed: `data/` is in `.gitignore`.
- The artifact embeds real data when built with `--with-data` (the owner chose this on 15 Oct 2026, private artifact).
  Build without the flag for anything shared outside Nature's Flame.
- SAP stays the system of record; Rolly only reads SAP data (via Power BI).
