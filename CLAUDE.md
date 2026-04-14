# WHM Proposals — Project Instructions

This repo houses White Haus Media's client proposal system. Static HTML proposals deployed on Vercel at whm-proposals.vercel.app. Every proposal is generated from a master template — never built from scratch.

## STRUCTURE
```
_template/
  proposal-template.html   ← MASTER TEMPLATE — source of truth for all proposals
  generate.js              ← Manual batch script for specific verticals (e.g. daycare)
proposals/
  company-slug/
    index.html             ← Generated proposal, filled from master template
```

## PROPOSAL URL FORMAT
`https://whm-proposals.vercel.app/proposals/[company-slug]/index.html`

Slug rules: lowercase, hyphens only, match company name closely.
Example: "Aversboro Road Child Care Center" → `aversboro-road-child-care-center`

## MASTER TEMPLATE SYSTEM
The template at `_template/proposal-template.html` uses `{{PLACEHOLDER}}` variables. **Always fetch this file via GitHub API and fill placeholders — never generate proposal HTML from scratch.**

### Key Placeholders
| Placeholder | What it is |
|---|---|
| `{{COMPANY_NAME}}` | Client company name |
| `{{CONTACT_NAME}}` | Primary contact first name |
| `{{INDUSTRY}}` | Industry label |
| `{{AUDIENCE}}` | Industry-specific audience term (see below) |
| `{{CITY}}` | City |
| `{{HEADLINE}}` | Hero headline |
| `{{SUBHEAD}}` | Hero subheadline |
| `{{OPP_INTRO}}` | Opportunity section intro paragraph |
| `{{OPP_1_TITLE}}` through `{{OPP_4_TITLE}}` | Opportunity card titles |
| `{{OPP_1_BODY}}` through `{{OPP_4_BODY}}` | Opportunity card body copy |
| `{{DEL_1}}` through `{{DEL_8}}` | Deliverable names (solution section + pricing list) |
| `{{DEL_1_DESC}}` through `{{DEL_8_DESC}}` | Deliverable descriptions |
| `{{PREVIEW_URL}}` | URL used in the preview iframe |
| `{{BUILD_FEE}}` | One-time build price (e.g. "1,997") |
| `{{CARE_PLAN}}` | Care plan name (e.g. "Growth Plan") |
| `{{CARE_MONTHLY}}` | Monthly care plan price (e.g. "197") |
| `{{BOOKING_URL}}` | Calendly or booking link (defaults to #contact if none) |
| `{{LETTER_BODY}}` | Personalized letter body copy |

### {{AUDIENCE}} by Industry
| Industry | Audience Term |
|---|---|
| childcare / daycare | families |
| healthcare | patients |
| restaurant / food | guests |
| church / faith | members |
| medspa / aesthetics | clients |
| legal / law | clients |
| fitness / gym | members |
| real estate | buyers and sellers |
| retail | customers |
| nonprofit | supporters |
| education | students and families |
| default | clients |

## INTERNAL DATA RULES
- **Scores (opp_score, site_score, etc.) are NEVER shown to clients** — use them internally to write qualitative copy only
- No scorecard sections in delivered proposals
- No percentages, grades, or numerical ratings visible to prospects

## GENERATE.JS USAGE
The manual batch script is for bulk-generating proposals for a specific vertical. To use:
```bash
node _template/generate.js
```
Edit `DAYCARE_DEFAULTS` and the company array at the top of the file to match the target companies. Always push the generated files to GitHub — Vercel auto-deploys.

## AUTO-GENERATOR (Scheduled Task)
The `auto-proposal-generator` Cowork task runs 3x/day and handles proposals automatically for prospects with opp_score ≥ 60. It:
1. Fetches the master template via GitHub API
2. Fills placeholders using prospect/company data
3. Pushes `proposals/[slug]/index.html` to this repo
4. Creates a Supabase proposal record
5. Updates prospect status to 'Proposal Generated'
6. Auto-sends if build_fee < $800, otherwise queues 'Ready for Review' in The Haus

## DESIGN REFERENCE
- Background: #080808 (near-black)
- Gold: #C6A44C
- Cream: #F4EFE6
- Fonts: Cormorant Garamond (display) + Plus Jakarta Sans (body)
- Icons: thin-stroke gold SVGs — never emoji
