# Company profile (for tender-scout)

**status:** active  
**last-review-date:** 2026-08-12  
**source:** adapted from `ndt-buisness-proc/docs/company/profile.md`  
**product entity:** ООО СВАРКА (tenders / rostender)

---

## In one paragraph

Two related NDT labs in Russia: **НДТ-Консалтинг** (federal / large customers, heavy radiography) and **ООО СВАРКА** (Moscow + region, mid/small, one-off jobs; welding is secondary). Strength: **radiation NDT** (X-ray, gamma, digital radiography) plus **ВИК** and **ПВК**. Digital priority: process transparency. Site: [ndt-consulting.ru](https://ndt-consulting.ru).

This repo’s product monitors tenders for **ООО СВАРКА**.

---

## Legal entities

| | НДТ-Консалтинг | ООО СВАРКА |
| --- | --- | --- |
| Geography | All Russia | Moscow + region |
| Customers | Very large | Mid / small |
| Typical deal | Frameworks, long projects, millions ₽ | Often one-off ~10⁵ ₽ |
| Positioning | Top-tier RF lab | Full permits, different market |

No external NDT subcontractors — they go to sites themselves. Customers may hire them as NDT subcontractor.

### Digital contours (relevant here)

| Contour | Note for this repo |
| --- | --- |
| **Bitrix24 (box)** | Single portal on **ООО СВАРКА**; НДТ-Консалтинг = обособленное подразделение. Future: tenders → CRM leads — [bitrix-and-leads.md](./bitrix-and-leads.md) |
| **Employees** | [employees.md](./employees.md) (roles for lead ownership; no secrets) |
| **NAS / LNA / budget** | **Out of scope** of this repository |

---

## Industries

Oil & gas, energy, construction, defense, aviation.

---

## NDT methods

See [ndt-methods.md](./ndt-methods.md). Do not confuse УЗТ with “толщинометрия” via ЦР.

**Lab attestation:** ЛНК-075А0291 (to 2028-08-18). **ИИИ license:** 74.50.11.002.Л.000014.12.17 (2017-12-27).

---

## Sales & tenders

- Channels: tenders, frameworks, platforms, referrals.
- Weak seasonality; slightly busier in summer.
- Large framework examples (careful with public naming): SINOPEC 10 / SINOPEC 4 (SEG subsidiaries).

**Scout product:** rostender UI scrape → L1/L2/L3 fit → operator UI → later Bitrix leads for fit tiers.

---

## Team (orientation)

| Contour | Size |
| --- | --- |
| Back office | 5–7 |
| Defectoscopists + supervisors | ~10 |

Process / Bitrix owner (director): Ильенко Виктор Викторович.  
Digital development (this product owner): Уманец Павел.

Ops reality: Excel-heavy protocols; Bitrix low adoption; goal = clearer processes and more revenue same direction. **Not in focus:** commercial training / EdTech.

---

## Tone

- Materials in this repo docs: **RU** for operator-facing copy; agent skills **EN**.
- Сварка: practical, fast, regional.
