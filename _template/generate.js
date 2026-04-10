#!/usr/bin/env node
/**
 * WHM Proposal Generator
 * Reads prospect data, applies master template, outputs index.html per proposal.
 * Preserves existing preview.html files untouched.
 *
 * Usage: node generate.js [--slug slug-name]  (omit slug to regenerate all)
 */

const fs = require('fs');
const path = require('path');

const TEMPLATE_PATH = path.join(__dirname, 'proposal-template.html');
const PROPOSALS_DIR = path.join(__dirname, '..', 'proposals');
const BOOKING_URL = 'https://whitehausmedia.com/consultation/';
const DEFAULT_DATE = 'April 2026';

// ── Default daycare content ──────────────────────────────────────────────
const DAYCARE_DEFAULTS = {
  heroHeadline: 'A digital home as <em>welcoming</em> as the one you\'ve built for families.',
  heroBody: 'Parents searching for childcare don\'t just want a program — they want to feel confident in their choice before they ever visit. A dedicated website gives your center that first impression, 24 hours a day.',
  letterP1: 'We took some time to look at your center\'s current digital footprint — your social media, your directory listings, your reviews — and what stood out immediately is that the quality of care you provide speaks for itself. Families trust you with their children, and that\'s the strongest foundation any business can have.',
  letterP2: 'What\'s missing is a dedicated online home that communicates that same level of care to parents who haven\'t found you yet. Right now, families searching for childcare in your area are comparing providers side by side — and the centers with polished, professional websites are making a stronger first impression before a single tour is booked.',
  letterP3: 'So instead of just writing up a proposal, we built a working concept of what your website could look like. Not a template — a fully designed, interactive preview built specifically around your center, your programs, and the families you serve. It\'s embedded below so you can scroll through it right here.',
  oppHeadline: 'Your center deserves more than a directory listing.',
  oppSub: 'After reviewing your current online presence, we identified four areas where a dedicated website would directly impact how families discover and choose your center.',
  opp1Title: 'No Dedicated Website',
  opp1Body: 'Your center\'s entire online presence currently lives on directory sites, social media, and review platforms. Parents searching for childcare are comparing you against providers who have their own professional websites. A custom site gives you a home base that you control — not a third-party platform that could change its layout or policies at any time.',
  opp2Title: 'Program Details Are Hard to Find',
  opp2Body: 'Your age groups, curriculum approach, daily schedule, and tuition information should be the easiest things for a parent to find online. Right now, that information is either scattered across multiple platforms or missing entirely. A website puts your programs front and center — exactly where a searching parent needs them.',
  opp3Title: 'No Online Tour or Enrollment Path',
  opp3Body: 'When a parent decides they\'re interested, there should be a clear next step — schedule a tour, request information, or start enrollment. Without a website, that path doesn\'t exist. A simple inquiry form on your own site converts interest into action.',
  opp4Title: 'Your Reputation Isn\'t Working for You Online',
  opp4Body: 'Families already love your center — your reviews and word-of-mouth prove it. But without a website to anchor those testimonials and showcase your facility, that reputation isn\'t reaching the parents who are actively searching. A website turns your existing trust into new enrollments.',
  del1: 'Custom single-page website designed for childcare enrollment',
  del2: 'Program sections organized by age group with curriculum highlights',
  del3: 'Tour scheduling and enrollment inquiry forms',
  del4: 'About section highlighting staff credentials and center philosophy',
  del5: 'Parent testimonials and trust-building content',
  del6: 'Photo gallery showcasing your facility and classrooms',
  del7: 'Mobile-first responsive build optimized for parent browsing',
  del8: 'SEO foundation — meta tags, Open Graph, schema markup',
};

// ── Prospect Data ────────────────────────────────────────────────────────
// Each entry can override any default field. Only slug, companyName, and price are required.
const PROSPECTS = [
  { slug: 'appletree-day-care', companyName: 'Appletree Day Care', price: '600', preparedFor: 'Appletree Day Care', previewDomain: 'appletreedaycare.com' },
  { slug: 'ashebridge-academy', companyName: 'AsheBridge Academy', price: '600', preparedFor: 'AsheBridge Academy', previewDomain: 'ashebridgeacademy.com' },
  { slug: 'aversboro-road-child-care-center', companyName: 'Aversboro Road Child Care Center', price: '600', preparedFor: 'Aversboro Road Child Care', previewDomain: 'aversborochildcare.com' },
  { slug: 'bright-beginnings', companyName: 'Bright Beginnings Child Development Center', price: '600', preparedFor: 'Bright Beginnings', previewDomain: 'brightbeginningscdc.com' },
  { slug: 'bright-starz-learning-center', companyName: 'Bright Starz Learning Center', price: '600', preparedFor: 'Bright Starz', previewDomain: 'brightstarzlearning.com' },
  { slug: 'chapel-hill-day-care-center', companyName: 'Chapel Hill Day Care Center', price: '797', preparedFor: 'Chapel Hill Day Care', previewDomain: 'chapelhilldaycare.com' },
  { slug: 'childcare-matters', companyName: 'Childcare Matters', price: '797', preparedFor: 'Childcare Matters', previewDomain: 'childcarematters.com' },
  { slug: 'childrens-campus', companyName: "Children's Campus", price: '600', preparedFor: "Children's Campus", previewDomain: 'childrenscampus.com' },
  { slug: 'community-school-people-under-six', companyName: 'Community School for People Under Six', price: '600', preparedFor: 'Community School', previewDomain: 'communityschoolundersix.com' },
  { slug: 'creative-kidz-academy', companyName: 'Creative Kidz Academy', price: '600', preparedFor: 'Creative Kidz Academy', previewDomain: 'creativekidzacademy.com' },
  { slug: 'discovery-child-development', companyName: 'Discovery Child Development Center', price: '600', preparedFor: 'Discovery Child Development', previewDomain: 'discoverychilddevelopment.com' },
  { slug: 'fairview-childrens-center', companyName: "Fairview Children's Center", price: '600', preparedFor: "Fairview Children's Center", previewDomain: 'fairviewchildrenscenter.com' },
  { slug: 'gifted-stars', companyName: 'Gifted Stars Early Learning Academy', price: '897', preparedFor: 'Gifted Stars', previewDomain: 'giftedstars.com' },
  { slug: 'giggles-and-smiles', companyName: 'Giggles and Smiles Playschool', price: '600', preparedFor: 'Giggles and Smiles', previewDomain: 'gigglesandsmiles.com' },
  { slug: 'grey-stone-preschool', companyName: 'Grey Stone Preschool & Kindergarten', price: '600', preparedFor: 'Grey Stone Preschool', previewDomain: 'greystonepreschool.com' },
  { slug: 'heavenly-haven-cdc', companyName: 'Heavenly Haven CDC', price: '600', preparedFor: 'Heavenly Haven', previewDomain: 'heavenlyhavencdc.com' },
  { slug: 'higher-calling-childcare', companyName: 'Higher Calling Childcare Center', price: '600', preparedFor: 'Higher Calling Childcare', previewDomain: 'highercallingchildcare.com' },
  { slug: 'holly-springs-learning-center', companyName: 'Holly Springs Learning Center', price: '600', preparedFor: 'Holly Springs Learning', previewDomain: 'hollyspringslearningcenter.com' },
  { slug: 'huckleberrys-friends', companyName: "Huckleberry's Friends", price: '897', preparedFor: "Huckleberry's Friends", previewDomain: 'huckleberrysfriends.com' },
  { slug: 'indigo-montessori', companyName: 'Indigo Montessori School', price: '697', preparedFor: 'Indigo Montessori', previewDomain: 'indigomontessori.com' },
  { slug: 'kids-country-day-care', companyName: 'Kids Country Day Care', price: '600', preparedFor: 'Kids Country Day Care', previewDomain: 'kidscountrydaycare.com' },
  { slug: 'knowledge-kickers', companyName: 'Knowledge Kickers', price: '600', preparedFor: 'Knowledge Kickers', previewDomain: 'knowledgekickers.com' },
  { slug: 'little-believers-academy', companyName: "Little Believer's Academy", price: '600', preparedFor: "Little Believer's Academy", previewDomain: 'littlebelieversacademy.com' },
  { slug: 'little-thinkers', companyName: 'Little Thinkers', price: '600', preparedFor: 'Little Thinkers', previewDomain: 'littlethinkers.com' },
  { slug: 'mi-escuelita', companyName: 'Mi Escuelita Spanish Immersion Preschool', price: '897', preparedFor: 'Mi Escuelita', previewDomain: 'miescuelita.com' },
  { slug: 'preschool-at-woodland', companyName: 'Preschool at Woodland', price: '600', preparedFor: 'Preschool at Woodland', previewDomain: 'preschoolatwoodland.com' },
  { slug: 'preston-childrens-academy', companyName: "Preston Children's Academy", price: '600', preparedFor: "Preston Children's Academy", previewDomain: 'prestonchildrensacademy.com' },
  { slug: 'primary-beginnings', companyName: 'Primary Beginnings', price: '600', preparedFor: 'Primary Beginnings', previewDomain: 'primarybeginnings.com' },
  { slug: 'sunny-side-child-development', companyName: 'Sunny Side Child Development Center', price: '600', preparedFor: 'Sunny Side', previewDomain: 'sunnysidechilddevelopment.com' },
  { slug: 'wee-care-preschool', companyName: 'Wee Care Preschool', price: '600', preparedFor: 'Wee Care Preschool', previewDomain: 'weecarepreschool.com' },
];

// ── Template engine ──────────────────────────────────────────────────────
function generate(prospect) {
  let template = fs.readFileSync(TEMPLATE_PATH, 'utf8');

  const d = { ...DAYCARE_DEFAULTS, ...prospect };

  const vars = {
    '{{COMPANY_NAME}}': d.companyName,
    '{{SLUG}}': d.slug,
    '{{PREPARED_FOR}}': d.preparedFor || d.companyName,
    '{{DATE}}': d.date || DEFAULT_DATE,
    '{{PRICE}}': d.price,
    '{{BOOKING_URL}}': d.bookingUrl || BOOKING_URL,
    '{{PREVIEW_DOMAIN}}': d.previewDomain || d.slug.replace(/-/g, '') + '.com',
    '{{HERO_HEADLINE}}': d.heroHeadline,
    '{{HERO_BODY}}': d.heroBody,
    '{{LETTER_GREETING}}': d.letterGreeting || 'Hello there,',
    '{{LETTER_P1}}': d.letterP1,
    '{{LETTER_P2}}': d.letterP2,
    '{{LETTER_P3}}': d.letterP3,
    '{{OPP_HEADLINE}}': d.oppHeadline,
    '{{OPP_SUB}}': d.oppSub,
    '{{OPP_1_TITLE}}': d.opp1Title,
    '{{OPP_1_BODY}}': d.opp1Body,
    '{{OPP_2_TITLE}}': d.opp2Title,
    '{{OPP_2_BODY}}': d.opp2Body,
    '{{OPP_3_TITLE}}': d.opp3Title,
    '{{OPP_3_BODY}}': d.opp3Body,
    '{{OPP_4_TITLE}}': d.opp4Title,
    '{{OPP_4_BODY}}': d.opp4Body,
    '{{DEL_1}}': d.del1,
    '{{DEL_2}}': d.del2,
    '{{DEL_3}}': d.del3,
    '{{DEL_4}}': d.del4,
    '{{DEL_5}}': d.del5,
    '{{DEL_6}}': d.del6,
    '{{DEL_7}}': d.del7,
    '{{DEL_8}}': d.del8,
  };

  for (const [key, value] of Object.entries(vars)) {
    // Use split/join for global replace (no regex escaping needed)
    template = template.split(key).join(value);
  }

  return template;
}

// ── Main ─────────────────────────────────────────────────────────────────
function main() {
  const args = process.argv.slice(2);
  let targetSlug = null;

  if (args.includes('--slug') && args[args.indexOf('--slug') + 1]) {
    targetSlug = args[args.indexOf('--slug') + 1];
  }

  const prospects = targetSlug
    ? PROSPECTS.filter(p => p.slug === targetSlug)
    : PROSPECTS;

  if (prospects.length === 0) {
    console.error(`No prospect found for slug: ${targetSlug}`);
    process.exit(1);
  }

  let generated = 0;
  let skipped = 0;

  for (const prospect of prospects) {
    const dir = path.join(PROPOSALS_DIR, prospect.slug);

    // Create directory if it doesn't exist
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }

    // Generate and write index.html
    const html = generate(prospect);
    const outPath = path.join(dir, 'index.html');
    fs.writeFileSync(outPath, html, 'utf8');
    generated++;

    // Check if preview.html exists
    const previewPath = path.join(dir, 'preview.html');
    if (!fs.existsSync(previewPath)) {
      console.warn(`  ⚠ No preview.html for ${prospect.slug}`);
    }

    console.log(`  ✓ ${prospect.slug} → index.html (${(html.length / 1024).toFixed(1)}KB)`);
  }

  console.log(`\nDone: ${generated} proposals generated, ${skipped} skipped.`);
}

main();
