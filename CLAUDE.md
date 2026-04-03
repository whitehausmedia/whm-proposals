
# CLAUDE.md — White Haus Media Proposal Generator

> This file defines how Claude generates client-facing proposal pages. Every proposal deployed to whitehausmedia.com/proposals/[company-slug] must follow this exact structure, styling, and quality standard.

---

## Model Routing

- **Sonnet 4.6 extended** handles: website scraping/analysis (structured JSON), opportunity scoring, opportunity card generation, deliverables list, email draft
- **Opus 4.6extended** handles: the final client-facing proposal HTML file and the spec site mockup. These are premium, interactive sales documents — they must be flawless. Never ship Sonnet-quality design output to a prospect.

---

## Proposal Generation Flow

When Rico says "New proposal for [Business Name] at [URL]":

### Step 1: Scrape & Analyze (Sonnet)
- Fetch the homepage HTML
- Extract all internal navigation links from the nav/menu and fetch every subpage (about, contact, services, team, programs, gallery, etc.)
- Search for Google reviews (rating and count)
- Pull US Census Bureau ACS 5-Year Estimate data for the business's zip code — specifically median household income
- Research competitors in the area to understand the local market
- Always check who built the prospect's current website. Look for meta generator tags, footer credits, CMS signatures, or whois data. Note the incumbent vendor name, their tech stack, and any weaknesses in their work. This intel helps position during outreach. Add incumbent vendor info to HubSpot deal notes.
- Analyze across these dimensions and return structured JSON:

```json
{
  "businessName": "",
  "ownerName": "",
  "industry": "",
  "city": "",
  "state": "",
  "zipCode": "",
  "phone": "",
  "email": "",
  "currentSiteUrl": "",
  "summary": "2-3 sentence overview of the business and what makes them notable",
  "scores": {
    "design": 0-100,
    "mobile": 0-100,
    "seo": 0-100,
    "content": 0-100,
    "overall": 0-100
  },
  "opportunityLabel": "Hot | Warm | Moderate | Cold",
  "strengths": ["what they do well — cite specific evidence"],
  "gaps": ["specific digital weaknesses — directly observable from site HTML or reviews only"],
  "googleReviews": { "rating": 0, "count": 0 },
  "competitors": ["nearby competitor names if found"],
  "locationTier": "affluent | middle | modest",
  "medianHouseholdIncome": "$XX,XXX (from Census ACS data)",
  "estimatedRevenue": "",
  "addonPotential": 0-100,
  "recommendedBuildFee": "calculated from pricing formula below",
  "pricingRationale": "1-2 sentence explanation of why this price was recommended"
}
```

### Pricing Recommendation Formula
The recommended build fee is calculated from multiple factors, not any single one:

**Factor 1 — Area Affluence (from census data):**
- Affluent (median household income $90K+): supports higher pricing
- Middle ($55K–$90K): supports mid-range pricing
- Modest (below $55K): supports accessible pricing

**Factor 2 — Current Site Quality (from analysis scores):**
- Very poor site (overall score below 35): higher value to prospect, supports higher pricing
- Poor site (35-55): moderate value proposition
- Decent site (55+): harder sell, may need lower price to compete

**Factor 3 — Business Establishment & Reputation:**
- Strong Google reviews (4.0+ stars, 50+ reviews): established business, has revenue, can invest
- Moderate reviews (3.5-4.0, 20-50 reviews): growing business
- Few/no reviews: newer or smaller operation, price-sensitive

**Factor 4 — Industry Norms:**
- Professional services (legal, finance, healthcare): expect to pay more for quality
- Childcare/education: value-conscious but understand trust signaling
- Restaurants/retail: tighter margins, more price-sensitive
- Contractors/trades: ROI-focused, willing to pay if you show the math

**Factor 5 — Scope of Work:**
- Simple brochure site (4-5 pages): lower end
- Full site with forms, booking, gallery: mid-range
- Complex functionality (e-commerce, portals, integrations): higher end

**Factor 6 — Competitive Pressure:**
- If competitors have strong sites: prospect feels urgency, supports pricing
- If competitors also have weak sites: less urgency but good market opportunity

**Recommended range: $597 to $1,100.** Present a specific number with a 1-2 sentence rationale so Rico can quickly approve or adjust. Example: "Recommended $997 — affluent area (median income $112K), terrible current site (score 34), strong reputation (4.6 stars, 89 reviews), established business that can invest."

**Minimum build fee: $600 (negotiation floor).** If the formula calculates a price below $697, round up to $697. This gives room to negotiate down to the $600 floor if needed. The listed price on a proposal should never be below $697.

Rico always reviews and approves or adjusts the recommended price before the proposal is built. Never auto-generate a proposal without pricing confirmation.

### Step 2: Score & Label
Extract from the analysis JSON. Score 75+ = Hot, 50-74 = Warm, 25-49 = Moderate, <25 = Cold.

### Step 3: Generate Opportunity Cards (Sonnet)
Produce exactly 4 opportunity cards based on the analysis.

CRITICAL — EVIDENCE-BASED ONLY:
- Every claim must be directly observable from the website HTML or confirmed in Google reviews
- NEVER assume customer frustration or pain points without evidence
- If the site lacks something, state it factually: "No online booking form" — NOT "customers are frustrated by the lack of booking"
- If Google reviews mention a specific issue, cite it: "Google reviews mention difficulty finding hours"
- Strengths should also reference specific evidence: review quotes, awards, program names found on the site

Each card must:
- Have a short, specific title (e.g., "No mobile optimization" not "Mobile issues")
- Have a 2-3 sentence body explaining the business impact
- Reference specific findings from the analysis

### Step 4: Generate Deliverables List (Sonnet)
Based on the industry and analysis, produce 6-8 specific deliverables tailored to this business. Examples:
- "Custom responsive homepage with hero imagery and clear value proposition"
- "Dedicated programs/services page with individual descriptions"
- "Contact form with [industry-specific fields]"
- "Google Business integration and local SEO foundation"
- "Mobile-first design optimized for on-the-go browsing"

Note: booking calendars, enrollment forms, and intake systems are INCLUDED in the core website build — do NOT list them as add-on services.

### Step 5: Build the Spec Site (OPUS)
Generate the spec site mockup first. Save as preview.html. See "Spec Site Generation" section below.

### Step 6: Build the Proposal Page (OPUS)
Generate the proposal page referencing preview.html. Save as index.html. See "Proposal Page Structure" section below.

---

## Contact Name Handling

- If owner/director name is found: use FIRST NAME ONLY throughout the proposal (greeting, letter, personalized headlines)
- If no contact name is found: use "Hey there" as the greeting
- Never use full name (first + last) in the proposal body — first name keeps it warm and personal
- The metadata grid can show full name if available under "Prepared for"

---

## Proposal Page Structure (exact section order)

### 1. Nav
- White Haus Media logo (CDN: https://WhiteHaus.b-cdn.net/WhiteHause%20Logo%20.png)
- Logo text: "White Haus Media" (Haus in italic gold)
- Nav links: Opportunity | Solution | Preview | Investment | Let's Talk (gold pill button)
- Frosted glass on scroll (blur + dark background)

### 2. Cover / Hero
- Eyebrow pill: "Prepared exclusively for [Business Name]"
- Headline: Personalized, warm, specific to their business. Serif italic on the emotional word. Example: "A website built around everything you've earned."
- Body: 1-2 sentences positioning the proposal. References their city and what the partnership would achieve.
- Metadata grid: Prepared for [First Name or Business Name] | Prepared by White Haus Media | Date [auto] | Delivery Under 2 weeks
- Subtle animated background glows (gold-tinted radial gradients)

### 3. Letter Section
- Eyebrow: "A note from White Haus Media"
- Greeting: "Dear [First Name]," or "Hey there," if no name found
- Gold divider rule
- 3 paragraphs:
  1. What impressed us about their business + the opportunity we see
  2. "I built a working concept of what your website could look like..." — the show-don't-tell pitch
  3. "Everything is outlined below: what I see as the opportunity, exactly what we would build, how we work together, and what it costs. No pressure — just an honest look at what is possible."
- Signature: WHM logo + "White Haus Media" + "Boutique Web Design & Digital Media"
- Signature says "from our team" — never from Rico personally

### 4. Opportunity Section
- Eyebrow: "Where the opportunity lives"
- Headline: "Your online presence has room to work harder for you."
- Body: "After reviewing your current website, we identified four areas where a stronger digital presence would directly impact how many new customers choose [Business Name]."
- 4 Opportunity Cards in a 2x2 grid:
  - Each card: number (01-04), title, body paragraph
  - Dark panel background, subtle gold top-border on hover
  - Cards animate in with reveal class
  - ALL content must be evidence-based per Step 3 rules

### 5. Solution Section
- Eyebrow: "What we would build"
- Headline: "A complete digital home for [Business Name]."
- Body: "Every site we create is built from scratch around your specific business. Here is exactly what is included — delivered in under two weeks."
- Deliverables list: checkmark/star icon (✦) + title for each item
- Clean vertical layout, no grid

### 6. Preview Section (Spec Site Embed)
- Eyebrow: "See it for yourself"
- Headline: "We already built you a working concept."
- Body: "Rather than mockups, we built a fully interactive preview. Every button and form works."
- Browser-frame container:
  - Top bar with dots (red/yellow/green) + URL text: "[Business Name] — Concept Preview by White Haus Media"
  - "Open full screen" link pointing to preview.html
  - Iframe with src="preview.html"
  - Caption: "Fully working prototype — not a mockup."

### 7. Process Section
- Eyebrow: "How we work together"
- Headline: "Four steps. Under two weeks."
- 4-step horizontal grid:
  1. Discovery Call — "We talk about your goals, your customers, and what success looks like."
  2. Design & Build — "We create your site from scratch — no templates, no shortcuts."
  3. Review & Refine — "You see everything before it goes live. We adjust until it's right."
  4. Launch & Support — "We handle deployment, and your site keeps working for your business long after launch."
- Each step: number, title, description
- Connected by subtle gold arrows between steps

### 8. Pricing Section
- Eyebrow: "Preliminary pricing"
- Headline: "An investment in where your business is headed."

**Build Fee Card (primary):**
- Badge: "Recommended"
- Large price display: $[amount]
- Label: "One-time investment"
- Payment split display below (50/50, upfront, or 3 payments depending on what Rico chose)
- Checkmark list of what's included

**Care Plans (two cards side by side):**
- Core Care: $47/month — software updates, 2 content edits/month, hosting coordination
- Full Care: $97/month — everything in Core + security monitoring, uptime monitoring, monthly performance report
- Gold border on the Full Care card (recommended)
- Note: "Your site keeps working for you long after launch. Both plans are month-to-month with no commitments."

**Add-On Services (if applicable):**
- Cards for Email Marketing ($297/mo), Social Media ($497/mo), Paid Ads ($597/mo + spend)
- Shown as "available" or "coming soon" depending on readiness

### 9. CTA Section
- Dark panel with gold glow
- Headline: "Ready to see what's possible?"
- Body: "Everything above is a recommendation based on what we found. Book a free consultation and we'll walk through the concept together, answer every question, and make sure the scope fits exactly where your business is headed."
- Primary button: "Book a Free Consultation" — links to HubSpot booking page
- Secondary button: "hello@whitehausmedia.com" mailto link

### 10. Footer
- WHM logo + text
- "© 2026 White Haus Media"
- Clean, minimal

---

## Styling Specification

Core palette:
--cream: #F4EFE6
--black: #080808
--gold: #C9A84C (proposal uses slightly warmer gold)
--gold-light: #D4BA6A
--gold-border: rgba(201,168,76,.25)
--gold-dim: rgba(201,168,76,.06)
--panel: rgba(255,255,255,.03)
--soft-border: rgba(255,255,255,.06)
--text-primary: rgba(255,255,255,.88)
--text-secondary: rgba(255,255,255,.5)
--text-muted: rgba(255,255,255,.28)

Typography:
- Body: Plus Jakarta Sans, -apple-system, sans-serif
- Headlines: Cormorant Garamond, Georgia, serif (for hero h1 and section headlines)

Key patterns:
- Section padding: ~100px vertical
- Max content width: ~680px for text, ~1040px for full width
- Border radius: 20px for cards, 100px for pills/buttons
- Scroll-triggered reveal animations (opacity 0 to 1, translateY 24px to 0)
- Background: solid #080808, NO images, subtle radial gold glows in hero only
- Progress bar at top of page (gold, tied to scroll position)

---

## Spec Site Generation (OPUS)

The spec site is a complete, functional website mockup for the prospect's business. It must:

- Be a single self-contained HTML file (all CSS/JS inline)
- Use real content from the analysis (business name, services, location, phone)
- Use CSS-only decorative elements (no external images unless on Bunny CDN)
- Include working navigation, forms, and interactive elements
- Be mobile responsive
- Use typography and design appropriate to the PROSPECT'S industry (NOT the WHM brand — this is THEIR site)
- Include a subtle "Site by White Haus Media" credit in the footer with link to whitehausmedia.com
- Load Google Fonts appropriate to the industry
- Extract actual images from the prospect's current website and use them in the spec site. Never use placeholder text like "Hero photography of children." If the current site has photos, use those image URLs. If no usable photos exist, use CSS-only abstract visuals, or stock images that are related to the business that are premium — never placeholder text.
- Extract the prospect's brand colors from their current site and use them in the redesign. Not generic pastels or invented colors. Match what they already have.
- No floating pill badges or stat bubbles. Integrate stats and trust signals naturally into the layout.
- Design must look premium and custom, not template-like. No cookie-cutter card layouts. Each spec site should feel like it was designed specifically for that business.

### How the spec site connects to the proposal

The spec site is saved as a separate file (preview.html) in the same directory as the proposal (index.html). The proposal embeds it via a simple relative-path iframe:

```html
<iframe class="preview-iframe" src="preview.html" title="[Business Name] Website Concept"></iframe>
```

No base64 encoding, no Blob URLs, no atob() — just two HTML files in the same folder. Vercel serves both. The client sees one seamless experience.

This also gives a standalone preview link:
whitehausmedia.com/proposals/[company-slug]/preview.html
Useful for walk-in outreach — pull up just the preview on your phone without the full proposal.

### Build Order
1. Generate the spec site FIRST — save as preview.html
2. Generate the proposal page SECOND (it references preview.html in the iframe) — save as index.html
3. Commit and push both files together

---

## File Output

Each proposal generates two files in the same directory:
```
proposals/[company-slug]/
    index.html      — the branded proposal page (what the client sees at the URL)
    preview.html    — the spec site mockup (embedded in proposal + standalone link)
```

Where [company-slug] is the lowercase, hyphenated business name (e.g., little-stepping-stones, apex-roofing, mesa-modern-kitchen).

After writing both files, commit and push:
```
git add proposals/[company-slug]/index.html proposals/[company-slug]/preview.html
git commit -m "Add proposal for [Business Name]"
git push origin main
```

Vercel auto-deploys. Proposal is live at:
- Full proposal: whitehausmedia.com/proposals/[company-slug]
- Spec site only: whitehausmedia.com/proposals/[company-slug]/preview.html

---

## HubSpot Auto-Creation

After generating the proposal, create via HubSpot MCP:

**Contact:**
- Business name, owner name (if found), phone, email (if found), website URL, industry, city
- All whm_ scored properties from analysis
- If no contact name or email found: create the contact with business name only and create a HubSpot TASK alerting Rico to find contact info (check LinkedIn, call, or use contact form)

**Deal:**
- Name: "[Business Name] — Website Build"
- Stage: "Proposal Sent"
- Amount: build fee
- whm_proposal_url: the live proposal link
- whm_opp_score, whm_score_label, whm_location_tier, whm_digital_gaps, whm_strengths
- All other whm_ analysis properties

---

## Volume Prospecting Workflow

When running a batch daycare prospecting campaign:

1. **Find 25 daycares** — Search Google Maps for "[city] daycare" or "[city] childcare." Pull the first 25 unique results. Log business name, website URL, and Google Business Profile link.

1b. **VERIFY OPEN STATUS** — Verify EVERY business is currently open and operating. Check Google Business Profile for 'permanently closed' or 'temporarily closed' status. If closed, skip and find a replacement. Never analyze a closed business.

2. **Score all 25** — Run the Step 1 scrape and analysis on each. Score 75+ = Hot, 50-74 = Warm, 25-49 = Moderate, <25 = Cold.

3. **Rank by score** — Sort all 25 by overall opportunity score, highest first.

4. **Select the Top 10** — The 10 highest-scoring prospects get full proposals: spec site + proposal page + HubSpot deal + email outreach.

5. **Build proposals for Top 10** — Follow the full proposal generation flow for each (Steps 1–6, HubSpot creation, email draft). The bottom 15 get email-only outreach — no full proposal built. See **Bottom 15 — No Email Fallback** below.

5b. **VERIFY PROPOSAL LIVE** — NEVER draft or send an email for a prospect that doesn't have a live proposal on whitehausmedia.com. Verify the proposal URL returns 200 before creating any email. If the build or push failed, skip that prospect's email and flag it in the summary.

---

## Contact Enrichment Order

When searching for a prospect's contact info, follow this order — do not skip ahead:

1. **Website scrape** — During Step 1 analysis, check every page thoroughly: About, Contact, Staff, Team, footer, privacy policy. Look for owner/director name, email address, and phone number.
2. **Google Business Profile** — Check the GBP listing for owner name and phone number.
3. **Apollo** — Only if steps 1 and 2 found no email, use Apollo to search for the decision maker at this business.
4. **No result** — If Apollo also returns nothing, create a HubSpot task: "No contact found for [Business Name] — manual research needed."

This saves Apollo credits for prospects where we truly can't find contact info any other way.

---

## Bottom 15 — No Email Fallback

If a bottom 15 prospect has no email address after completing the full enrichment order (website scrape → Google Business → Apollo):

1. **Contact form exists** — Submit the outreach message through their contact form. Include the proposal link. Log in `volume-outreach-log.md` as "contact form submitted" with date.

2. **No contact form, but social presence exists** — Log their Facebook or Instagram profile URL in `volume-outreach-log.md` and flag for manual DM: "No email or contact form. Social profile: [URL]. Manual DM needed."

3. **No email, no contact form, no social** — Mark as "unreachable" in `volume-outreach-log.md` and move on.

The proposal still gets built and pushed live either way. If they ever Google themselves and find it, or if contact info surfaces later, the proposal is ready.

---

## Email Generation

After the proposal is live, draft an outreach email:
- From: hello@whitehausmedia.com
- To: prospect email if found, otherwise flag for manual outreach
- Use first name only in greeting
- Subject: specific, not generic, under 8 words
- Body: 3-4 short paragraphs max
- Include the proposal link
- Sign off as "Rico, White Haus Media"
- No exclamation marks
- No AI or technology references
- Sound like a local founder who genuinely did research on their business
- If no email address found: draft the message anyway for use in contact form submission or DM, and create a HubSpot task for manual outreach

---

## Quality Checklist (before deploying)

- Both files exist: index.html (proposal) and preview.html (spec site)
- Proposal iframe uses src="preview.html" (relative path, not base64/blob)
- All instances say "White Haus Media" (never "Digital")
- Logo loads from CDN URL
- Email references hello@whitehausmedia.com
- First name used throughout (or "Hey there" if no name)
- Business name is correct throughout
- City/location references are accurate
- Opportunity cards reference actual findings only (no assumptions, no fabricated pain points)
- Spec site renders correctly in the proposal preview iframe
- Spec site renders correctly as standalone at preview.html
- Pricing section says "Preliminary pricing" and "Recommended" badge
- CTA says "Book a Free Consultation" with advisory framing
- Care plan tiers show $47 and $97
- Both files are mobile responsive (check at 375px width)
- No AI/automation/Claude language anywhere in either file
- HTML is valid in both files (balanced tags, no broken nesting)
- Both files load without external dependency failures
- Spec site footer includes "Site by White Haus Media" credit
