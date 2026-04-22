import base64, json, os, time
import urllib.request, urllib.error, urllib.parse

# Load secrets from environment — set WHM_GITHUB_TOKEN and WHM_SUPABASE_KEY before running
# e.g.:  export WHM_GITHUB_TOKEN="ghp_..."  export WHM_SUPABASE_KEY="eyJ..."
GITHUB_TOKEN = os.environ.get("WHM_GITHUB_TOKEN", "")
REPO = "White-Haus-Media/whm-proposals"

# ─── Supabase config ──────────────────────────────────────────────────────────
SUPABASE_URL = "https://lpdbffncosplssshclqh.supabase.co"
SUPABASE_KEY = os.environ.get("WHM_SUPABASE_KEY", "")

def sb_upsert_proposal(slug, title, price):
    """
    After pushing a proposal to GitHub, ensure a Supabase proposals record exists.
    - If record found by URL: bump updated_at so The Haus shows fresh build time
    - If not found: create Draft record (company_id/deal_id left null; link manually)
    """
    proposal_url = f"https://www.whitehausmedia.com/proposals/{slug}/"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }

    # Look up existing record by URL
    lookup_url = f"{SUPABASE_URL}/rest/v1/proposals?url=eq.{urllib.parse.quote(proposal_url)}&select=id,status"
    req = urllib.request.Request(lookup_url, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            rows = json.loads(r.read())
    except Exception as e:
        print(f"    Supabase lookup error: {e}")
        return

    if rows:
        # Record exists — just log it (we don't stomp on status or tracked fields)
        print(f"    Supabase: record exists (id={rows[0]['id']}, status={rows[0]['status']})")
    else:
        # Create a new Draft record
        payload = json.dumps({
            "title": title,
            "url": proposal_url,
            "status": "Draft",
        }).encode()
        create_url = f"{SUPABASE_URL}/rest/v1/proposals"
        req2 = urllib.request.Request(create_url, data=payload, headers={
            **headers, "Prefer": "return=representation"
        }, method="POST")
        try:
            with urllib.request.urlopen(req2) as r:
                created = json.loads(r.read())
                pid = created[0].get("id") if isinstance(created, list) else created.get("id")
                print(f"    Supabase: created Draft record (id={pid}) — link company_id manually in The Haus")
        except urllib.error.HTTPError as e:
            print(f"    Supabase create error: {e.code} {e.read().decode()}")

def gh_push(path, content, message):
    url = f"https://api.github.com/repos/{REPO}/contents/{path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}", "Content-Type": "application/json"}
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as r:
            sha = json.loads(r.read())["sha"]
    except:
        sha = None
    b64 = base64.b64encode(content.encode()).decode()
    payload = {"message": message, "content": b64}
    if sha: payload["sha"] = sha
    data = json.dumps(payload).encode()
    req2 = urllib.request.Request(url, data=data, headers=headers, method="PUT")
    with urllib.request.urlopen(req2) as r:
        result = json.loads(r.read())
        return result.get("content", {}).get("name", "ERROR")


FONTS = "https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400;1,8..60,600&family=Manrope:wght@400;500;600;700;800&display=swap"

def build_roi_js(industry):
    """Return inline JS for the ROI calculator based on industry."""
    if industry == 'dental':
        return '''
    function calcROI() {
      var p = parseInt(document.getElementById('roi1').value) || 0;
      var v = parseInt(document.getElementById('roi2').value) || 0;
      var result = p * v;
      document.getElementById('roi-result').textContent = '$' + result.toLocaleString();
      document.getElementById('roi-annual').textContent = '$' + (result * 12).toLocaleString() + '/yr';
    }
    document.getElementById('roi1').addEventListener('input', calcROI);
    document.getElementById('roi2').addEventListener('input', calcROI);
    calcROI();'''
    elif industry == 'legal':
        return '''
    function calcROI() {
      var c = parseInt(document.getElementById('roi1').value) || 0;
      var v = parseInt(document.getElementById('roi2').value) || 0;
      var result = c * v;
      document.getElementById('roi-result').textContent = '$' + result.toLocaleString();
      document.getElementById('roi-annual').textContent = '$' + (result * 12).toLocaleString() + '/yr';
    }
    document.getElementById('roi1').addEventListener('input', calcROI);
    document.getElementById('roi2').addEventListener('input', calcROI);
    calcROI();'''
    elif industry == 'realty':
        return '''
    function calcROI() {
      var t = parseInt(document.getElementById('roi1').value) || 0;
      var c = parseInt(document.getElementById('roi2').value) || 0;
      var annual = t * c;
      var monthly = Math.round(annual / 12);
      document.getElementById('roi-result').textContent = '$' + monthly.toLocaleString();
      document.getElementById('roi-annual').textContent = '$' + annual.toLocaleString() + '/yr';
    }
    document.getElementById('roi1').addEventListener('input', calcROI);
    document.getElementById('roi2').addEventListener('input', calcROI);
    calcROI();'''
    elif industry == 'fitness':
        return '''
    function calcROI() {
      var m = parseInt(document.getElementById('roi1').value) || 0;
      var f = parseInt(document.getElementById('roi2').value) || 0;
      var result = m * f;
      document.getElementById('roi-result').textContent = '$' + result.toLocaleString();
      document.getElementById('roi-annual').textContent = '$' + (result * 12).toLocaleString() + '/yr';
    }
    document.getElementById('roi1').addEventListener('input', calcROI);
    document.getElementById('roi2').addEventListener('input', calcROI);
    calcROI();'''
    return ''


def build_proposal(slug, title, prepared_for, prepared_by, date_str,
                   hook_h1, hook_sub, letter_body,
                   issues, deliverables, price, includes,
                   revenue_title, revenue_body, revenue_stat,
                   roi_industry, roi_label, roi1_label, roi1_default,
                   roi2_label, roi2_default, roi_output_label,
                   sample_domain=""):

    issues_html = ""
    for i, (num, title_i, body_i) in enumerate(issues, 1):
        issues_html += f'''
        <div class="opp-card reveal">
          <div class="opp-num">0{i}</div>
          <h3>{title_i}</h3>
          <p>{body_i}</p>
        </div>'''

    del_html = ""
    for d in deliverables:
        del_html += f'<div class="del-item"><span class="del-star">✦</span><span>{d}</span></div>\n'

    includes_html = ""
    for inc in includes:
        includes_html += f'<div class="p-item"><span class="p-check">✓</span><span>{inc}</span></div>\n'

    letter_paras = "".join(f"<p>{p}</p>" for p in letter_body)
    roi_js = build_roi_js(roi_industry)

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Website Proposal | White Haus Media</title>
<meta name="robots" content="noindex, nofollow">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{FONTS}" rel="stylesheet">
<style>
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --midnight:#102A43;
  --midnight-mid:#1B3D5C;
  --slate:#6889A6;
  --gold:#CEC195;
  --gold-dim:rgba(206,193,149,.12);
  --gold-border:rgba(206,193,149,.28);
  --offwhite:#F8F7F3;
  --offwhite-dark:#EEE9E1;
  --charcoal:#242528;
  --charcoal-mid:#4A4C50;
  --graphite:#202938;
  --soft-border:rgba(36,37,40,.1);
  --text-primary:#242528;
  --text-secondary:#4A4C50;
  --text-muted:#8A8C90;
  --on-dark:rgba(248,247,243,.88);
  --on-dark-muted:rgba(248,247,243,.5);
  --on-dark-border:rgba(248,247,243,.12);
}}
html{{scroll-behavior:smooth}}
body{{font-family:'Manrope',-apple-system,sans-serif;background:var(--offwhite);color:var(--text-primary);-webkit-font-smoothing:antialiased;line-height:1.6}}
a{{text-decoration:none;color:inherit;transition:all .2s}}

.progress{{position:fixed;top:0;left:0;height:2px;background:var(--gold);z-index:1000;width:0%;transition:width .1s linear}}

/* NAV — Midnight Blue, permanent */
.nav{{position:fixed;top:2px;left:0;right:0;z-index:100;padding:0 24px;background:var(--midnight);border-bottom:1px solid rgba(16,42,67,.4)}}
.nav-inner{{display:flex;align-items:center;justify-content:space-between;max-width:1040px;margin:0 auto;padding:16px 0}}
.nav-logo-text{{font-family:'Source Serif 4',Georgia,serif;font-size:.95rem;font-weight:600;color:var(--offwhite);letter-spacing:-.01em}}
.nav-logo-text em{{font-style:italic;color:var(--gold)}}
.nav-links{{display:flex;align-items:center;gap:24px;list-style:none}}
.nav-links a{{font-size:.82rem;font-weight:500;color:var(--on-dark-muted);transition:color .2s;letter-spacing:.01em}}
.nav-links a:hover{{color:var(--on-dark)}}
.nav-pill{{background:var(--gold);color:var(--midnight);padding:8px 20px;border-radius:100px;font-size:.82rem;font-weight:700;transition:all .2s;letter-spacing:.02em}}
.nav-pill:hover{{background:#D8CDA8;transform:translateY(-1px)}}

.reveal{{opacity:0;transform:translateY(20px);transition:opacity .65s ease,transform .65s ease}}
.reveal.visible{{opacity:1;transform:translateY(0)}}

/* HERO */
.hero{{min-height:100vh;display:flex;align-items:center;justify-content:center;text-align:center;padding:140px 24px 100px;position:relative;overflow:hidden;background:var(--offwhite)}}
.hero::before{{content:'';position:absolute;top:10%;left:50%;transform:translateX(-50%);width:640px;height:640px;border-radius:50%;background:radial-gradient(circle,rgba(104,137,166,.08) 0%,transparent 70%);pointer-events:none}}
.hero-pill{{display:inline-flex;align-items:center;gap:8px;background:rgba(16,42,67,.06);border:1px solid rgba(16,42,67,.12);color:var(--slate);padding:8px 20px;border-radius:100px;font-size:.75rem;font-weight:600;letter-spacing:.08em;text-transform:uppercase;margin-bottom:32px}}
.hero h1{{font-family:'Source Serif 4',Georgia,serif;font-size:clamp(2.4rem,5vw,3.6rem);font-weight:600;line-height:1.1;color:var(--midnight);max-width:720px;margin:0 auto 24px;letter-spacing:-.02em}}
.hero h1 em{{font-style:italic;color:var(--slate)}}
.hero-body{{font-size:1.05rem;color:var(--text-secondary);max-width:520px;margin:0 auto 48px;line-height:1.7;font-weight:400}}
.hero-meta{{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--soft-border);border:1px solid var(--soft-border);border-radius:12px;overflow:hidden;max-width:640px;margin:0 auto}}
.hero-meta-item{{background:var(--offwhite);padding:20px 16px;text-align:center}}
.hero-meta-label{{font-size:.68rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:var(--text-muted);margin-bottom:4px}}
.hero-meta-value{{font-size:.88rem;font-weight:600;color:var(--midnight)}}

/* LETTER */
.letter{{padding:100px 24px;background:var(--offwhite-dark)}}
.letter-card{{max-width:680px;margin:0 auto}}
.letter-greeting{{font-family:'Source Serif 4',Georgia,serif;font-size:1.8rem;color:var(--midnight);margin-bottom:8px;font-weight:600}}
.letter-rule{{width:40px;height:1.5px;background:rgba(16,42,67,.15);margin:20px 0 28px;border-radius:2px}}
.letter p{{font-size:.95rem;color:var(--text-secondary);line-height:1.85;margin-bottom:20px}}
.letter-sig{{display:flex;align-items:center;gap:14px;margin-top:36px;padding-top:28px;border-top:1px solid var(--soft-border)}}
.letter-sig-text{{font-size:.82rem;color:var(--text-muted);line-height:1.5}}
.letter-sig-text strong{{color:var(--midnight);display:block;font-weight:600}}

/* OPPORTUNITY */
.opp{{padding:100px 24px;background:var(--offwhite)}}
.opp .wrap-wide{{max-width:1040px;margin:0 auto}}
.section-eyebrow{{font-size:.72rem;font-weight:600;text-transform:uppercase;letter-spacing:.12em;color:var(--slate);margin-bottom:14px}}
.section-eyebrow.light{{color:var(--gold)}}
.section-rule{{width:48px;height:1.5px;background:var(--slate);margin-bottom:32px;border-radius:2px;opacity:.4}}
.section-rule.light{{background:var(--gold);opacity:.6}}
.opp h2{{font-family:'Source Serif 4',Georgia,serif;font-size:clamp(1.8rem,4vw,2.4rem);font-weight:600;color:var(--midnight);margin-bottom:12px;letter-spacing:-.02em}}
.opp .sub{{font-size:1rem;color:var(--text-secondary);line-height:1.7;margin-bottom:48px;max-width:600px}}
.opp-grid{{display:grid;grid-template-columns:1fr 1fr;gap:16px}}
.opp-card{{background:#fff;border:1px solid var(--soft-border);border-left:3px solid var(--midnight);border-radius:0 12px 12px 0;padding:28px 24px;transition:all .3s}}
.opp-card:hover{{border-left-color:var(--slate);box-shadow:0 4px 20px rgba(36,37,40,.06)}}
.opp-num{{font-size:.68rem;font-weight:700;color:var(--slate);letter-spacing:.1em;text-transform:uppercase;margin-bottom:12px}}
.opp-card h3{{font-size:1rem;font-weight:700;color:var(--midnight);margin-bottom:8px}}
.opp-card p{{font-size:.88rem;color:var(--text-secondary);line-height:1.65}}

/* SOLUTION */
.solution{{padding:100px 24px;background:var(--offwhite-dark)}}
.solution .wrap-wide{{max-width:1040px;margin:0 auto}}
.solution h2{{font-family:'Source Serif 4',Georgia,serif;font-size:clamp(1.8rem,4vw,2.4rem);font-weight:600;color:var(--midnight);margin-bottom:12px;letter-spacing:-.02em}}
.solution .sub{{font-size:1rem;color:var(--text-secondary);line-height:1.7;margin-bottom:48px;max-width:600px}}
.del-list{{display:flex;flex-direction:column;gap:0;max-width:680px}}
.del-item{{display:flex;align-items:center;gap:14px;padding:18px 0;border-bottom:1px solid var(--soft-border)}}
.del-item:first-child{{border-top:1px solid var(--soft-border)}}
.del-star{{color:var(--midnight);font-size:.9rem;flex-shrink:0;opacity:.5}}
.del-item span{{font-size:.95rem;color:var(--text-primary);font-weight:500}}

/* REVENUE IDEA — Graphite dark */
.revenue{{padding:100px 24px;background:var(--graphite)}}
.revenue .wrap-wide{{max-width:1040px;margin:0 auto}}
.revenue .section-eyebrow{{color:var(--gold)}}
.revenue h2{{font-family:'Source Serif 4',Georgia,serif;font-size:clamp(1.8rem,4vw,2.4rem);font-weight:600;color:var(--offwhite);margin-bottom:12px;letter-spacing:-.02em}}
.revenue-card{{background:rgba(248,247,243,.04);border:1px solid var(--on-dark-border);border-radius:16px;padding:48px 40px;margin-top:40px;position:relative;overflow:hidden}}
.revenue-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--gold),transparent)}}
.revenue-card h3{{font-family:'Source Serif 4',Georgia,serif;font-size:1.5rem;font-weight:600;color:var(--offwhite);margin-bottom:16px}}
.revenue-card p{{font-size:.95rem;color:var(--on-dark);line-height:1.85;margin-bottom:24px}}
.revenue-stat{{display:inline-flex;align-items:center;gap:10px;background:rgba(206,193,149,.1);border:1px solid rgba(206,193,149,.25);border-radius:100px;padding:10px 24px}}
.revenue-stat-value{{font-size:1.1rem;font-weight:700;color:var(--gold)}}
.revenue-stat-label{{font-size:.82rem;color:var(--on-dark-muted)}}

/* PROCESS */
.process{{padding:100px 24px;background:var(--offwhite)}}
.process .wrap-wide{{max-width:1040px;margin:0 auto}}
.process h2{{font-family:'Source Serif 4',Georgia,serif;font-size:clamp(1.8rem,4vw,2.4rem);font-weight:600;color:var(--midnight);margin-bottom:12px;letter-spacing:-.02em}}
.process .sub{{font-size:1rem;color:var(--text-secondary);line-height:1.7;margin-bottom:48px}}
.step-grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:20px}}
.step{{background:#fff;border:1px solid var(--soft-border);border-radius:12px;padding:28px 24px;text-align:center;position:relative}}
.step-num{{font-size:.68rem;font-weight:700;color:var(--slate);letter-spacing:.1em;text-transform:uppercase;margin-bottom:12px}}
.step h4{{font-size:1rem;font-weight:700;color:var(--midnight);margin-bottom:8px}}
.step p{{font-size:.85rem;color:var(--text-secondary);line-height:1.6}}
.step-arrow{{position:absolute;right:-14px;top:50%;transform:translateY(-50%);color:var(--soft-border);font-size:1.2rem}}

/* ROI CALCULATOR — Graphite dark */
.roi{{padding:100px 24px;background:var(--graphite)}}
.roi .wrap-wide{{max-width:1040px;margin:0 auto}}
.roi .section-eyebrow{{color:var(--gold)}}
.roi h2{{font-family:'Source Serif 4',Georgia,serif;font-size:clamp(1.8rem,4vw,2.4rem);font-weight:600;color:var(--offwhite);margin-bottom:12px;letter-spacing:-.02em}}
.roi .sub{{font-size:1rem;color:var(--on-dark);line-height:1.7;margin-bottom:48px;max-width:600px}}
.roi-card{{background:rgba(248,247,243,.05);border:1px solid var(--on-dark-border);border-radius:16px;padding:48px 40px;max-width:680px}}
.roi-card::before{{content:'';display:block;height:1.5px;background:linear-gradient(90deg,var(--gold),transparent);margin-bottom:36px;border-radius:2px}}
.roi-label{{font-size:.68rem;font-weight:600;text-transform:uppercase;letter-spacing:.1em;color:var(--on-dark-muted);margin-bottom:8px}}
.roi-row{{display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-bottom:24px}}
.roi-field input{{width:100%;background:rgba(248,247,243,.07);border:1px solid var(--on-dark-border);border-radius:8px;padding:14px 16px;font-size:1rem;font-weight:600;color:var(--offwhite);font-family:'Manrope',inherit;outline:none;transition:border-color .2s;-webkit-appearance:none}}
.roi-field input:focus{{border-color:rgba(206,193,149,.4)}}
.roi-field input::-webkit-inner-spin-button{{opacity:.4}}
.roi-output{{background:rgba(206,193,149,.08);border:1px solid rgba(206,193,149,.2);border-radius:12px;padding:28px 32px;display:flex;align-items:center;justify-content:space-between;gap:24px;flex-wrap:wrap;margin-top:8px}}
.roi-output-label{{font-size:.82rem;color:var(--on-dark-muted)}}
.roi-output-number{{font-family:'Source Serif 4',Georgia,serif;font-size:2.6rem;font-weight:600;color:var(--gold);line-height:1}}
.roi-output-sub{{font-size:.8rem;color:var(--on-dark-muted);margin-top:4px}}
.roi-disclaimer{{font-size:.72rem;color:var(--on-dark-muted);margin-top:20px;line-height:1.6}}

/* PRICING */
.pricing{{padding:100px 24px;background:var(--offwhite-dark)}}
.pricing-head{{text-align:center;margin-bottom:48px}}
.pricing-head h2{{font-family:'Source Serif 4',Georgia,serif;font-size:clamp(1.8rem,4vw,2.4rem);font-weight:600;color:var(--midnight);margin-bottom:4px;letter-spacing:-.02em}}
.pricing-cards{{display:grid;grid-template-columns:1fr;gap:20px;max-width:540px;margin:0 auto}}
.p-card{{background:#fff;border:1px solid rgba(16,42,67,.15);border-radius:16px;padding:48px 36px;text-align:center;position:relative;overflow:hidden}}
.p-card::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--midnight)}}
.p-badge{{display:inline-flex;align-items:center;gap:6px;background:rgba(16,42,67,.07);border:1px solid rgba(16,42,67,.12);color:var(--midnight);padding:5px 14px;border-radius:100px;font-size:.7rem;font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin-bottom:20px}}
.p-headline{{font-size:1.2rem;font-weight:700;color:var(--midnight);margin-bottom:28px}}
.p-amount{{font-size:3.6rem;font-weight:800;color:var(--midnight);letter-spacing:-.03em;line-height:1}}
.p-amount sup{{font-size:1.4rem;vertical-align:super;margin-right:2px}}
.p-label{{font-size:.85rem;color:var(--text-muted);margin-top:6px;margin-bottom:28px}}
.p-list{{text-align:left;margin-bottom:32px}}
.p-item{{display:flex;align-items:flex-start;gap:10px;padding:10px 0;border-bottom:1px solid var(--soft-border)}}
.p-item:last-child{{border:none}}
.p-check{{color:var(--slate);flex-shrink:0;margin-top:2px;font-size:.85rem}}
.p-item span{{font-size:.88rem;color:var(--text-secondary)}}
.p-cta{{display:inline-flex;align-items:center;gap:10px;background:var(--midnight);color:var(--offwhite);padding:16px 36px;border-radius:100px;font-size:.95rem;font-weight:700;font-family:inherit;transition:all .25s;text-decoration:none;letter-spacing:.01em}}
.p-cta:hover{{background:var(--midnight-mid);transform:translateY(-1px);box-shadow:0 8px 24px rgba(16,42,67,.25)}}
.p-note{{font-size:.78rem;color:var(--text-muted);margin-top:16px}}

.care-plans{{display:grid;grid-template-columns:1fr 1fr;gap:16px;max-width:540px;margin:24px auto 0}}
.care-card{{background:#fff;border:1px solid var(--soft-border);border-radius:12px;padding:28px 22px;text-align:center}}
.care-card.rec{{border-color:rgba(16,42,67,.2);position:relative;overflow:hidden}}
.care-card.rec::before{{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:var(--slate)}}
.care-name{{font-size:.92rem;font-weight:700;color:var(--midnight);margin-bottom:4px}}
.care-price{{font-size:1.6rem;font-weight:800;color:var(--midnight)}}
.care-price span{{font-size:.82rem;font-weight:500;color:var(--text-muted)}}
.care-desc{{font-size:.78rem;color:var(--text-secondary);margin-top:8px;line-height:1.6}}
.care-note{{text-align:center;max-width:540px;margin:16px auto 0;font-size:.78rem;color:var(--text-muted)}}

/* WEBSITE PREVIEW EMBED */
.preview-section{{padding:100px 24px;background:var(--offwhite)}}
.preview-section .wrap-wide{{max-width:1040px;margin:0 auto}}
.preview-section h2{{font-family:'Source Serif 4',Georgia,serif;font-size:clamp(1.8rem,4vw,2.4rem);font-weight:600;color:var(--midnight);margin-bottom:12px;letter-spacing:-.02em}}
.preview-sub{{font-size:.95rem;color:var(--text-secondary);line-height:1.7;max-width:580px;margin-bottom:40px}}
.preview-wrap{{border-radius:14px;overflow:hidden;box-shadow:0 8px 48px rgba(16,42,67,.12);border:1px solid var(--soft-border)}}
.browser-chrome{{background:#E4E0D8;padding:10px 16px;display:flex;align-items:center;gap:10px}}
.browser-dots{{display:flex;gap:5px;flex-shrink:0}}
.browser-dot{{width:11px;height:11px;border-radius:50%}}
.dot-r{{background:#FF5F57}}
.dot-y{{background:#FFBD2E}}
.dot-g{{background:#28C840}}
.browser-bar{{flex:1;background:rgba(255,255,255,.75);border-radius:4px;padding:5px 12px;font-size:.72rem;color:var(--text-muted);font-family:'Manrope',inherit;overflow:hidden;white-space:nowrap;text-overflow:ellipsis}}
.browser-expand{{font-size:.72rem;font-weight:700;color:var(--midnight);background:rgba(16,42,67,.08);border:1px solid rgba(16,42,67,.15);padding:5px 14px;border-radius:100px;white-space:nowrap;text-decoration:none;flex-shrink:0;transition:all .2s}}
.browser-expand:hover{{background:rgba(16,42,67,.14)}}
.preview-frame{{position:relative;background:var(--offwhite);overflow:hidden}}
.preview-frame iframe{{width:100%;height:620px;border:none;display:block;pointer-events:none}}
.preview-gradient{{position:absolute;bottom:0;left:0;right:0;height:180px;background:linear-gradient(to bottom,transparent 0%,rgba(248,247,243,.97) 65%,var(--offwhite) 100%);display:flex;align-items:flex-end;justify-content:center;padding-bottom:28px}}
.expand-cta{{display:inline-flex;align-items:center;gap:9px;background:var(--midnight);color:var(--offwhite);padding:14px 32px;border-radius:100px;font-size:.9rem;font-weight:700;font-family:'Manrope',inherit;letter-spacing:.01em;transition:all .25s;text-decoration:none;box-shadow:0 4px 24px rgba(16,42,67,.28)}}
.expand-cta:hover{{background:var(--midnight-mid);transform:translateY(-2px);box-shadow:0 8px 32px rgba(16,42,67,.35)}}
.expand-cta svg{{width:15px;height:15px;stroke:currentColor;stroke-width:2;fill:none}}

/* CTA — Midnight Blue */
.cta-section{{padding:100px 24px;background:var(--midnight)}}
.cta-box{{max-width:680px;margin:0 auto;text-align:center}}
.cta-box h2{{font-family:'Source Serif 4',Georgia,serif;font-size:2.4rem;font-weight:600;color:var(--offwhite);margin-bottom:16px;letter-spacing:-.02em}}
.cta-box p{{font-size:.95rem;color:var(--on-dark);line-height:1.7;max-width:480px;margin:0 auto 40px}}
.cta-btns{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}}
.cta-primary{{display:inline-flex;align-items:center;gap:8px;background:var(--gold);color:var(--midnight);padding:16px 32px;border-radius:100px;font-size:.95rem;font-weight:700;transition:all .25s;letter-spacing:.01em}}
.cta-primary:hover{{background:#D8CDA8;transform:translateY(-1px);box-shadow:0 8px 24px rgba(206,193,149,.25)}}
.cta-secondary{{display:inline-flex;align-items:center;gap:8px;color:var(--on-dark-muted);padding:16px 24px;border-radius:100px;font-size:.9rem;font-weight:500;border:1px solid var(--on-dark-border);transition:all .2s}}
.cta-secondary:hover{{border-color:rgba(206,193,149,.3);color:var(--gold)}}

.footer{{padding:40px 24px;text-align:center;border-top:1px solid var(--soft-border);background:var(--offwhite)}}
.footer-text{{font-size:.82rem;color:var(--text-muted)}}
.footer-text strong{{color:var(--text-secondary)}}

@media(max-width:768px){{
  .opp-grid{{grid-template-columns:1fr}}
  .step-grid{{grid-template-columns:1fr 1fr}}
  .care-plans{{grid-template-columns:1fr}}
  .hero-meta{{grid-template-columns:1fr 1fr}}
  .nav-links{{display:none}}
  .roi-row{{grid-template-columns:1fr}}
  .roi-output{{flex-direction:column;gap:8px}}
  .revenue-card{{padding:32px 24px}}
  .roi-card{{padding:32px 24px}}
}}
</style>
</head>
<body>
<div class="progress" id="progress"></div>

<nav class="nav" id="nav">
  <div class="nav-inner">
    <div class="nav-logo-text">White Haus <em>Media</em></div>
    <ul class="nav-links">
      <li><a href="#opportunity">Opportunity</a></li>
      <li><a href="#solution">Solution</a></li>
      <li><a href="#preview">Preview</a></li>
      <li><a href="#roi">ROI</a></li>
      <li><a href="#investment">Investment</a></li>
    </ul>
    <a href="https://calendly.com/whitehausmedia" target="_blank" class="nav-pill">Book a Call</a>
  </div>
</nav>

<!-- HERO -->
<section class="hero">
  <div>
    <div class="hero-pill reveal">Prepared exclusively for {title}</div>
    <h1 class="reveal">{hook_h1}</h1>
    <p class="hero-body reveal">{hook_sub}</p>
    <div class="hero-meta reveal">
      <div class="hero-meta-item">
        <div class="hero-meta-label">Prepared for</div>
        <div class="hero-meta-value">{prepared_for}</div>
      </div>
      <div class="hero-meta-item">
        <div class="hero-meta-label">Prepared by</div>
        <div class="hero-meta-value">White Haus Media</div>
      </div>
      <div class="hero-meta-item">
        <div class="hero-meta-label">Date</div>
        <div class="hero-meta-value">{date_str}</div>
      </div>
      <div class="hero-meta-item">
        <div class="hero-meta-label">Delivery</div>
        <div class="hero-meta-value">Under 2 Weeks</div>
      </div>
    </div>
  </div>
</section>

<!-- LETTER -->
<section class="letter">
  <div class="letter-card">
    <div class="letter-greeting reveal">Hey {prepared_for},</div>
    <div class="letter-rule reveal"></div>
    <div class="reveal">
      {letter_paras}
    </div>
    <div class="letter-sig reveal">
      <div class="letter-sig-text">
        <strong>Rico White</strong>
        White Haus Media &middot; Wake Forest, NC
      </div>
    </div>
  </div>
</section>

<!-- OPPORTUNITY -->
<section class="opp" id="opportunity">
  <div class="wrap-wide">
    <div class="reveal"><div class="section-eyebrow">Where the opportunity lives</div></div>
    <h2 class="reveal">What we found on your site</h2>
    <div class="section-rule reveal"></div>
    <div class="opp-grid">
      {issues_html}
    </div>
  </div>
</section>

<!-- SOLUTION -->
<section class="solution" id="solution">
  <div class="wrap-wide">
    <div class="reveal"><div class="section-eyebrow">What we build</div></div>
    <h2 class="reveal">Everything included, delivered in under two weeks</h2>
    <div class="section-rule reveal"></div>
    <div class="del-list">
      {del_html}
    </div>
  </div>
</section>

<!-- REVENUE IDEA -->
<section class="revenue">
  <div class="wrap-wide">
    <div class="reveal"><div class="section-eyebrow light">Revenue opportunity</div></div>
    <h2 class="reveal">One idea worth adding to the roadmap</h2>
    <div class="section-rule light reveal"></div>
    <div class="revenue-card reveal">
      <h3>{revenue_title}</h3>
      <p>{revenue_body}</p>
      <div class="revenue-stat">
        <span class="revenue-stat-value">{revenue_stat}</span>
        <span class="revenue-stat-label">potential additional revenue</span>
      </div>
    </div>
  </div>
</section>

<!-- PROCESS -->
<section class="process">
  <div class="wrap-wide">
    <div class="reveal"><div class="section-eyebrow">How we work together</div></div>
    <h2 class="reveal">Four steps. Under two weeks.</h2>
    <div class="section-rule reveal"></div>
    <div class="step-grid">
      <div class="step reveal">
        <div class="step-num">01</div>
        <h4>Discovery Call</h4>
        <p>We talk through your goals, your clients, and what you want your site to communicate.</p>
        <div class="step-arrow">&#8250;</div>
      </div>
      <div class="step reveal">
        <div class="step-num">02</div>
        <h4>Design &amp; Build</h4>
        <p>We build from scratch around your brand — your photos, your voice, your services.</p>
        <div class="step-arrow">&#8250;</div>
      </div>
      <div class="step reveal">
        <div class="step-num">03</div>
        <h4>Review &amp; Refine</h4>
        <p>You see everything before it goes live. We adjust until it&#8217;s exactly right.</p>
        <div class="step-arrow">&#8250;</div>
      </div>
      <div class="step reveal">
        <div class="step-num">04</div>
        <h4>Launch &amp; Support</h4>
        <p>We handle deployment and domain setup. You get 30 days of post-launch support.</p>
      </div>
    </div>
  </div>
</section>

<!-- WEBSITE PREVIEW EMBED -->
<section class="preview-section" id="preview">
  <div class="wrap-wide">
    <div class="reveal"><div class="section-eyebrow">Your new site</div></div>
    <h2 class="reveal">Here&#8217;s what it could look like</h2>
    <div class="section-rule reveal"></div>
    <p class="preview-sub reveal">This is a sample homepage built specifically for {title}. Real content, real layout, production-ready design. Scroll through the embedded preview below or open it full screen.</p>
    <div class="preview-wrap reveal">
      <div class="browser-chrome">
        <div class="browser-dots">
          <div class="browser-dot dot-r"></div>
          <div class="browser-dot dot-y"></div>
          <div class="browser-dot dot-g"></div>
        </div>
        <div class="browser-bar">{sample_domain}</div>
        <a href="preview.html" target="_blank" class="browser-expand">&#8599; Full Screen</a>
      </div>
      <div class="preview-frame">
        <iframe src="preview.html" title="Sample website preview for {title}" loading="lazy" scrolling="no"></iframe>
        <div class="preview-gradient">
          <a href="preview.html" target="_blank" class="expand-cta">
            <svg viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
            View Full Screen
          </a>
        </div>
      </div>
    </div>
  </div>
</section>

<!-- ROI CALCULATOR -->
<section class="roi" id="roi">
  <div class="wrap-wide">
    <div class="reveal"><div class="section-eyebrow light">What a better site is worth</div></div>
    <h2 class="reveal">{roi_label}</h2>
    <div class="section-rule light reveal"></div>
    <div class="roi-card reveal">
      <div class="roi-row">
        <div class="roi-field">
          <div class="roi-label">{roi1_label}</div>
          <input type="number" id="roi1" value="{roi1_default}" min="0">
        </div>
        <div class="roi-field">
          <div class="roi-label">{roi2_label}</div>
          <input type="number" id="roi2" value="{roi2_default}" min="0">
        </div>
      </div>
      <div class="roi-output">
        <div>
          <div class="roi-output-label">{roi_output_label}</div>
          <div class="roi-output-number" id="roi-result">—</div>
          <div class="roi-output-sub" id="roi-annual"></div>
        </div>
      </div>
      <div class="roi-disclaimer">Estimates are illustrative. Actual results depend on traffic, conversion rates, and market conditions. This calculator is meant to frame the conversation, not guarantee outcomes.</div>
    </div>
  </div>
</section>

<!-- PRICING -->
<section class="pricing" id="investment">
  <div class="pricing-head">
    <div class="section-eyebrow reveal">Investment</div>
    <h2 class="reveal">One flat fee. No surprises.</h2>
  </div>
  <div class="pricing-cards">
    <div class="p-card reveal">
      <div class="p-badge">&#10003; Recommended</div>
      <div class="p-headline">Custom Website Build</div>
      <div class="p-amount"><sup>$</sup>{price}</div>
      <div class="p-label">one-time investment</div>
      <div class="p-list">
        {includes_html}
      </div>
      <a href="https://calendly.com/whitehausmedia" target="_blank" class="p-cta">Book a Free Consultation</a>
      <div class="p-note">No obligation — we&#8217;ll walk through everything together.</div>
    </div>
  </div>
  <div class="care-plans">
    <div class="care-card">
      <div class="care-name">Core Care</div>
      <div class="care-price">$47<span>/mo</span></div>
      <div class="care-desc">Software updates, 2 content edits/month, hosting coordination.</div>
    </div>
    <div class="care-card rec">
      <div class="care-name">Full Care</div>
      <div class="care-price">$97<span>/mo</span></div>
      <div class="care-desc">Everything in Core + security monitoring, uptime checks, monthly performance report.</div>
    </div>
  </div>
  <div class="care-note">Both plans are month-to-month. No commitments.</div>
</section>

<!-- CTA -->
<section class="cta-section">
  <div class="cta-box reveal">
    <h2>Ready to see what&#8217;s possible?</h2>
    <p>Everything above is based on what we found. Book a free call and we&#8217;ll walk through it together — no pressure, just clarity on the scope.</p>
    <div class="cta-btns">
      <a href="https://calendly.com/whitehausmedia" target="_blank" class="cta-primary">Book a Free Consultation</a>
      <a href="mailto:hello@whitehausmedia.com" class="cta-secondary">hello@whitehausmedia.com</a>
    </div>
  </div>
</section>

<footer class="footer">
  <div class="footer-text">&copy; 2026 <strong>White Haus Media</strong> &middot; Wake Forest, NC</div>
</footer>

<script>
(function(){{
  var prog=document.getElementById('progress');
  window.addEventListener('scroll',function(){{
    var h=document.documentElement.scrollHeight-window.innerHeight;
    var s=window.scrollY;
    if(h>0) prog.style.width=(s/h*100)+'%';
  }});
  var obs=new IntersectionObserver(function(entries){{
    entries.forEach(function(e){{
      if(e.isIntersecting){{e.target.classList.add('visible');obs.unobserve(e.target);}}
    }});
  }},{{threshold:.12,rootMargin:'0px 0px -40px 0px'}});
  document.querySelectorAll('.reveal').forEach(function(el){{obs.observe(el);}});
  document.querySelectorAll('a[href^="#"]').forEach(function(a){{
    a.addEventListener('click',function(e){{
      var t=document.querySelector(this.getAttribute('href'));
      if(t){{e.preventDefault();t.scrollIntoView({{behavior:'smooth',block:'start'}});}}
    }});
  }});
  // ROI Calculator
  {roi_js}
}})();
</script>
</body>
</html>'''


def build_sample_site(slug, title, domain,
                      primary, primary_mid, accent, accent_dim, accent_border,
                      hero_eyebrow, hero_h1, hero_sub, hero_cta,
                      services, stats,
                      testimonial_quote, testimonial_name, testimonial_role,
                      footer_tagline,
                      design_style='default',
                      font_url=None,
                      heading_font=None,
                      body_font=None,
                      services_heading='Our Services',
                      services_sub='Built around one goal — making it easier for the right clients to find you and choose you.'):
    """Generate a full homepage mockup — industry-specific design, fonts, and layout per client."""

    _default_font_url = "https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;0,8..60,700;1,8..60,400;1,8..60,600&family=Manrope:wght@400;500;600;700;800&display=swap"
    _font_url = font_url or _default_font_url
    _hf = heading_font or "'Source Serif 4',Georgia,serif"
    _bf = body_font or "'Manrope',-apple-system,sans-serif"

    # ── Style-specific CSS overrides ──────────────────────────────────────────
    # Built via string concatenation (no f-strings) so CSS braces don't conflict
    # with the outer f-string template. These get embedded as a plain variable.

    if design_style == 'law':
        # Playfair Display + DM Sans. Left-aligned split hero. Gold-bordered cards.
        style_css = (
            "body{font-family:" + _bf + "}"
            ".hero{background:var(--bg);padding:120px 28px 100px}"
            ".hero-inner{max-width:1060px;margin:0 auto;display:grid;grid-template-columns:1.1fr 0.9fr;gap:64px;align-items:center}"
            ".hero-deco{background:linear-gradient(150deg," + primary + " 0%," + primary_mid + " 100%);border-radius:20px;height:380px;display:flex;align-items:center;justify-content:center;overflow:hidden}"
            ".hero-deco-inner{font-family:" + _hf + ";font-size:5.5rem;font-weight:700;color:rgba(248,247,243,.07);line-height:.9;text-align:center;font-style:italic;padding:24px;user-select:none}"
            ".hero-eyebrow{color:var(--ink3);justify-content:flex-start;margin-bottom:0}"
            ".hero-eyebrow::before,.hero-eyebrow::after{background:var(--ink3);opacity:.4}"
            ".hero-rule{width:40px;height:2px;background:" + accent + ";margin:18px 0 24px}"
            ".hero h1{font-family:" + _hf + ";font-size:clamp(2.2rem,4vw,3.4rem);text-align:left;letter-spacing:-.025em;line-height:1.08;color:" + primary + ";margin:0 0 20px;max-width:none}"
            ".hero h1 em{font-style:italic;color:" + accent + "}"
            ".hero-sub{text-align:left;margin:0 0 36px;color:var(--ink2);font-size:.92rem;max-width:none;line-height:1.75}"
            ".hero-btns{justify-content:flex-start}"
            ".hero-btn-primary{background:" + primary + ";color:#F8F7F3;border-radius:6px}"
            ".hero-btn-primary:hover{background:" + primary_mid + ";transform:translateY(-1px)}"
            ".hero-btn-secondary{background:transparent;border:1px solid rgba(36,37,40,.18);color:var(--ink2);border-radius:6px}"
            ".stat-num{font-family:" + _hf + ";font-size:2rem;font-weight:600}"
            ".section-h2{font-family:" + _hf + ";font-weight:600}"
            ".svc-card{border-radius:0 12px 12px 0;border-left:3px solid " + accent + ";border-top:none;border-right:1px solid var(--border);border-bottom:1px solid var(--border)}"
            ".svc-card:hover{border-left-color:" + primary + ";box-shadow:0 4px 20px rgba(36,37,40,.06);transform:none}"
            ".svc-icon{background:transparent;width:auto;height:auto;border-radius:0;margin-bottom:10px}"
            ".svc-card h3{font-family:" + _hf + ";font-weight:600;font-size:1rem}"
            ".testimonial blockquote{font-family:" + _hf + ";font-style:italic;font-weight:400}"
            ".cta-section h2{font-family:" + _hf + ";font-weight:600}"
            ".sitenav-brand{font-family:" + _hf + ";font-weight:600;letter-spacing:-.01em}"
            ".sitenav-brand em{font-style:italic}"
            "@media(max-width:768px){.hero-inner{grid-template-columns:1fr}.hero-deco{display:none}}"
        )

    elif design_style == 'fitness':
        # Barlow Condensed + Barlow. Bold uppercase. Athletic dark intensity.
        style_css = (
            "body{font-family:" + _bf + "}"
            ".hero-eyebrow{font-size:.72rem;letter-spacing:.18em;font-weight:700}"
            ".hero h1{font-family:" + _hf + ";font-size:clamp(3rem,9vw,6rem);font-weight:800;text-transform:uppercase;letter-spacing:-.025em;line-height:.9;margin-bottom:24px}"
            ".hero h1 em{font-style:normal;font-weight:800;color:" + accent + "}"
            ".hero-sub{font-family:" + _bf + ";font-size:.95rem;font-weight:400;letter-spacing:0;max-width:480px;margin-left:auto;margin-right:auto}"
            ".hero-btn-primary{border-radius:4px;font-weight:700;letter-spacing:.06em;text-transform:uppercase;font-size:.76rem;padding:15px 28px}"
            ".hero-btn-secondary{border-radius:4px;font-weight:600;letter-spacing:.06em;text-transform:uppercase;font-size:.74rem}"
            ".stats-bar{background:#F0EDEA}"
            ".stat-num{font-family:" + _hf + ";font-size:3.4rem;font-weight:800;letter-spacing:-.03em;color:" + primary + ";line-height:1}"
            ".stat-label{font-weight:700;letter-spacing:.12em;font-size:.62rem}"
            ".section-eyebrow{letter-spacing:.15em;font-weight:700}"
            ".section-h2{font-family:" + _hf + ";font-size:clamp(2rem,5vw,3.4rem);font-weight:800;text-transform:uppercase;letter-spacing:-.025em}"
            ".section-sub{font-family:" + _bf + ";font-size:.88rem;font-weight:400}"
            ".svc-grid{gap:10px}"
            ".svc-card{border-radius:4px;border:none;border-top:3px solid " + accent + ";overflow:hidden;position:relative;background:#fff}"
            ".svc-card::after{content:attr(data-num);position:absolute;bottom:-10px;right:14px;font-family:" + _hf + ";font-size:5.5rem;font-weight:800;color:rgba(36,37,40,.04);line-height:1;pointer-events:none}"
            ".svc-card:hover{transform:translateY(-3px);box-shadow:0 8px 32px rgba(36,37,40,.1)}"
            ".svc-card h3{font-family:" + _hf + ";font-size:1.15rem;font-weight:800;text-transform:uppercase;letter-spacing:.02em;margin-bottom:8px}"
            ".svc-icon{background:" + accent_dim + ";border-radius:4px}"
            ".testimonial blockquote{font-family:" + _hf + ";font-size:clamp(1.6rem,3.5vw,2.6rem);font-weight:800;text-transform:uppercase;font-style:normal;letter-spacing:-.025em;line-height:1.0}"
            ".cta-section h2{font-family:" + _hf + ";font-weight:800;text-transform:uppercase;letter-spacing:-.02em}"
            ".sitenav-brand{font-family:" + _hf + ";font-size:1.3rem;font-weight:800;text-transform:uppercase;letter-spacing:.01em}"
            ".sitenav-brand em{font-style:italic}"
        )

    elif design_style == 'dental':
        # DM Sans lightweight. Minimal. Clinical calm. Spa-like breathing room.
        style_css = (
            "body{font-family:" + _bf + ";font-weight:300}"
            ".sitenav{box-shadow:0 1px 0 var(--border)}"
            ".sitenav-brand{font-family:" + _hf + ";font-weight:500;letter-spacing:-.01em;font-size:1.05rem}"
            ".sitenav-brand em{font-style:normal;font-weight:600;color:" + accent + "}"
            ".sitenav-links a{font-weight:400}"
            ".sitenav-cta{font-weight:500;border-radius:8px}"
            ".hero{padding:130px 28px 120px}"
            ".hero h1{font-family:" + _hf + ";font-size:clamp(2rem,4.5vw,3.2rem);font-weight:300;letter-spacing:-.025em;line-height:1.2;margin-bottom:20px}"
            ".hero h1 em{font-style:normal;font-weight:600;color:" + accent + "}"
            ".hero-eyebrow{font-weight:400;letter-spacing:.1em;opacity:.6}"
            ".hero-sub{font-weight:300;font-size:.95rem;line-height:1.9;color:rgba(248,247,243,.52);max-width:440px}"
            ".hero-btn-primary{background:" + accent + ";color:" + primary + ";font-weight:500;border-radius:8px;padding:14px 30px}"
            ".hero-btn-primary:hover{opacity:.9;transform:translateY(-1px);box-shadow:none}"
            ".hero-btn-secondary{border-radius:8px;font-weight:400;background:rgba(248,247,243,.06);border:1px solid rgba(248,247,243,.15)}"
            ".stats-bar{padding:44px 28px}"
            ".stat-num{font-family:" + _hf + ";font-size:2rem;font-weight:400;letter-spacing:-.025em}"
            ".stat-label{font-weight:400;letter-spacing:.06em;font-size:.7rem}"
            ".section-h2{font-family:" + _hf + ";font-size:clamp(1.6rem,3.5vw,2.2rem);font-weight:400;letter-spacing:-.02em}"
            ".section-sub{font-weight:300;line-height:1.9;font-size:.9rem}"
            ".svc-grid{gap:24px}"
            ".svc-card{border:none;border-radius:16px;box-shadow:0 2px 28px rgba(36,37,40,.04);border-bottom:2px solid transparent;transition:border-color .3s,box-shadow .3s;padding:36px 28px}"
            ".svc-card:hover{border-bottom-color:" + accent + ";box-shadow:0 6px 36px rgba(36,37,40,.07);transform:none}"
            ".svc-icon{background:" + accent_dim + ";border-radius:50%}"
            ".svc-card h3{font-family:" + _hf + ";font-weight:500;letter-spacing:-.01em;font-size:.95rem}"
            ".svc-card p{font-weight:300;line-height:1.8;font-size:.82rem}"
            ".testimonial blockquote{font-family:" + _hf + ";font-weight:300;font-style:italic;font-size:clamp(1.1rem,2.5vw,1.55rem);line-height:1.75}"
            ".testimonial-name{font-weight:500}"
            ".cta-section{padding:90px 28px}"
            ".cta-section h2{font-family:" + _hf + ";font-weight:400;letter-spacing:-.025em}"
            ".cta-section p{font-weight:300;line-height:1.9}"
            ".cta-btn{border-radius:8px;font-weight:500;letter-spacing:.01em}"
        )

    elif design_style == 'realty':
        # Nunito Sans + Source Serif 4. Left-aligned hero. Modern, neighborhood feel.
        style_css = (
            "body{font-family:" + _bf + "}"
            ".hero{padding:100px 28px 88px;text-align:left}"
            ".hero-eyebrow{justify-content:flex-start;color:" + accent + "}"
            ".hero-eyebrow::before,.hero-eyebrow::after{background:" + accent + "}"
            ".hero h1{font-family:" + _hf + ";font-size:clamp(2.2rem,4.5vw,3.6rem);font-weight:700;letter-spacing:-.025em;max-width:640px;text-align:left;line-height:1.08;margin-left:0;margin-right:0}"
            ".hero h1 em{font-style:italic;color:" + accent + ";font-weight:700}"
            ".hero-sub{text-align:left;margin:0 0 36px;max-width:460px;font-size:.92rem;font-weight:400;color:rgba(248,247,243,.65)}"
            ".hero-btns{justify-content:flex-start}"
            ".hero-btn-primary{border-radius:6px;font-weight:700;background:" + accent + ";color:" + primary + "}"
            ".hero-btn-primary:hover{opacity:.9}"
            ".hero-btn-secondary{border-radius:6px;font-weight:500;background:rgba(248,247,243,.08);border:1px solid rgba(248,247,243,.2)}"
            ".stat-num{font-family:" + _hf + ";font-size:2.2rem;font-weight:700;letter-spacing:-.025em}"
            ".section-h2{font-family:" + _hf + ";font-weight:700;letter-spacing:-.02em}"
            ".svc-card{border-radius:8px}"
            ".svc-card h3{font-family:" + _hf + ";font-weight:700;font-size:.95rem}"
            ".svc-card:hover{border-color:" + primary + ";box-shadow:0 4px 24px rgba(36,37,40,.08)}"
            ".testimonial blockquote{font-family:" + _hf + ";font-style:italic;font-weight:600;font-size:clamp(1.1rem,2.5vw,1.6rem)}"
            ".cta-section h2{font-family:" + _hf + ";font-weight:700}"
            ".sitenav-brand{font-family:" + _hf + ";font-weight:700}"
            ".sitenav-brand em{font-style:italic}"
        )

    elif design_style == 'heritage_law':
        # EB Garamond + Inter. Centered editorial hero. Traditional institution feel.
        style_css = (
            "body{font-family:" + _bf + "}"
            ".hero{background:var(--bg);padding:120px 28px 100px;text-align:center}"
            ".hero-eyebrow{color:var(--ink3);letter-spacing:.15em;font-size:.64rem}"
            ".hero-eyebrow::before,.hero-eyebrow::after{background:var(--ink3);opacity:.35}"
            ".hero-badge{display:inline-flex;align-items:center;gap:16px;margin:16px auto 28px;font-family:" + _hf + ";font-size:.7rem;font-weight:400;letter-spacing:.12em;text-transform:uppercase;color:" + primary + ";font-style:normal}"
            ".hero-badge::before,.hero-badge::after{content:'';display:block;width:28px;height:1px;background:" + accent + "}"
            ".hero h1{font-family:" + _hf + ";font-size:clamp(2.2rem,4.5vw,3.8rem);font-weight:500;color:" + primary + ";letter-spacing:-.02em;line-height:1.1;font-style:italic;max-width:720px;margin-left:auto;margin-right:auto}"
            ".hero h1 em{font-style:normal;font-weight:600}"
            ".hero-sub{color:var(--ink2);font-size:.9rem;font-weight:400;line-height:1.88;max-width:520px;margin-left:auto;margin-right:auto}"
            ".hero-btn-primary{background:" + primary + ";color:#F8F7F3;border-radius:0;font-weight:400;letter-spacing:.06em;text-transform:uppercase;font-size:.76rem;padding:15px 36px}"
            ".hero-btn-primary:hover{background:" + primary_mid + "}"
            ".hero-btn-secondary{border-radius:0;font-weight:400;border:1px solid rgba(36,37,40,.18);color:var(--ink2);font-size:.76rem;text-transform:uppercase;letter-spacing:.06em}"
            ".stats-bar{background:var(--bg2)}"
            ".stat-num{font-family:" + _hf + ";font-size:2.2rem;font-weight:500;font-style:italic;color:" + primary + "}"
            ".section-h2{font-family:" + _hf + ";font-weight:500;font-style:italic;letter-spacing:-.01em}"
            ".services{background:var(--bg2)}"
            ".svc-card{border-radius:0;border:none;border-top:2px solid " + accent + ";background:#FFFFFF;transition:box-shadow .3s}"
            ".svc-card:hover{box-shadow:0 4px 24px rgba(36,37,40,.07);transform:none}"
            ".svc-icon{background:transparent;border-radius:0;width:auto;height:auto;margin-bottom:8px}"
            ".svc-card h3{font-family:" + _hf + ";font-weight:500;font-style:italic;font-size:1.08rem}"
            ".testimonial blockquote{font-family:" + _hf + ";font-size:clamp(1.1rem,2.5vw,1.7rem);font-weight:400;font-style:italic;line-height:1.68}"
            ".cta-section{background:#EEE9E1}"
            ".cta-section h2{font-family:" + _hf + ";font-weight:500;font-style:italic;color:" + primary + "}"
            ".cta-section p{color:var(--ink2);font-size:.9rem}"
            ".cta-btn{background:" + primary + ";color:#F8F7F3;border-radius:0;font-size:.76rem;letter-spacing:.06em;text-transform:uppercase;font-weight:400;padding:15px 36px}"
            ".cta-btn:hover{background:" + primary_mid + ";box-shadow:none}"
            ".sitenav-brand{font-family:" + _hf + ";font-weight:500;font-size:1.1rem;letter-spacing:-.01em}"
            ".sitenav-brand em{font-style:italic;color:" + accent + "}"
        )

    else:
        style_css = ""

    # ── Services HTML ────────────────────────────────────────────────────────
    services_html = ""
    for i, (icon_path, svc_title, svc_body) in enumerate(services, 1):
        num_str = f"0{i}" if i < 10 else str(i)
        services_html += f'''
      <div class="svc-card" data-num="{num_str}">
        <div class="svc-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="{accent}" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">{icon_path}</svg>
        </div>
        <h3>{svc_title}</h3>
        <p>{svc_body}</p>
      </div>'''

    stats_html = ""
    for num, label in stats:
        stats_html += f'''
      <div class="stat-item">
        <div class="stat-num">{num}</div>
        <div class="stat-label">{label}</div>
      </div>'''

    # ── Style-specific hero HTML ────────────────────────────────────────────
    if design_style == 'law':
        hero_html = f'''<!-- HERO -->
<section class="hero">
  <div class="hero-inner">
    <div class="hero-content">
      <div class="hero-eyebrow">{hero_eyebrow}</div>
      <div class="hero-rule"></div>
      <h1>{hero_h1}</h1>
      <p class="hero-sub">{hero_sub}</p>
      <div class="hero-btns">
        <a href="#contact" class="hero-btn-primary">{hero_cta}</a>
        <a href="#services" class="hero-btn-secondary">Practice Areas</a>
      </div>
    </div>
    <div class="hero-deco">
      <div class="hero-deco-inner">Law<br>&amp;<br>Counsel</div>
    </div>
  </div>
</section>'''

    elif design_style == 'heritage_law':
        hero_html = f'''<!-- HERO -->
<section class="hero">
  <div class="wrap">
    <div class="hero-eyebrow">{hero_eyebrow}</div>
    <div class="hero-badge">Established 1974</div>
    <h1>{hero_h1}</h1>
    <p class="hero-sub">{hero_sub}</p>
    <div class="hero-btns">
      <a href="#contact" class="hero-btn-primary">{hero_cta}</a>
      <a href="#services" class="hero-btn-secondary">Practice Areas</a>
    </div>
  </div>
</section>'''

    else:
        hero_html = f'''<!-- HERO -->
<section class="hero">
  <div class="wrap">
    <div class="hero-eyebrow">{hero_eyebrow}</div>
    <h1>{hero_h1}</h1>
    <p class="hero-sub">{hero_sub}</p>
    <div class="hero-btns">
      <a href="#contact" class="hero-btn-primary">{hero_cta}</a>
      <a href="#services" class="hero-btn-secondary">See Our Services</a>
    </div>
  </div>
</section>'''

    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} — Sample Website</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="{_font_url}" rel="stylesheet">
<style>
*,*::before,*::after{{margin:0;padding:0;box-sizing:border-box}}
:root{{
  --p:{primary};
  --p2:{primary_mid};
  --a:{accent};
  --ad:{accent_dim};
  --ab:{accent_border};
  --bg:#F8F7F3;
  --bg2:#EEE9E1;
  --ink:#242528;
  --ink2:#4A4C50;
  --ink3:#8A8C90;
  --border:rgba(36,37,40,.1);
}}
html{{scroll-behavior:smooth}}
body{{background:var(--bg);color:var(--ink);-webkit-font-smoothing:antialiased;line-height:1.6}}
a{{text-decoration:none;color:inherit}}
.wrap{{max-width:1060px;margin:0 auto;padding:0 28px}}

/* SAMPLE BANNER */
.sample-banner{{background:var(--p);padding:10px 28px;display:flex;align-items:center;justify-content:space-between;gap:16px;position:sticky;top:0;z-index:200}}
.sample-banner-left{{display:flex;align-items:center;gap:10px}}
.sample-dot{{width:8px;height:8px;border-radius:50%;background:var(--a);flex-shrink:0}}
.sample-banner-text{{font-size:.7rem;font-weight:600;color:rgba(248,247,243,.7);letter-spacing:.06em;text-transform:uppercase}}
.sample-banner-text strong{{color:var(--a)}}
.sample-banner-link{{font-size:.7rem;font-weight:700;color:var(--a);letter-spacing:.06em;text-transform:uppercase;padding:6px 16px;border:1px solid var(--ab);border-radius:100px;white-space:nowrap;transition:all .2s}}
.sample-banner-link:hover{{background:var(--ad)}}

/* NAV */
.sitenav{{background:var(--p);padding:0 28px}}
.sitenav-inner{{max-width:1060px;margin:0 auto;display:flex;align-items:center;justify-content:space-between;padding:18px 0}}
.sitenav-brand{{font-size:1.1rem;font-weight:600;color:#F8F7F3;letter-spacing:-.01em}}
.sitenav-links{{display:flex;align-items:center;gap:28px;list-style:none}}
.sitenav-links a{{font-size:.82rem;font-weight:500;color:rgba(248,247,243,.55);transition:color .2s}}
.sitenav-links a:hover{{color:#F8F7F3}}
.sitenav-cta{{background:var(--a);color:var(--p);padding:9px 22px;border-radius:100px;font-size:.82rem;font-weight:700;letter-spacing:.02em;transition:all .2s}}
.sitenav-cta:hover{{opacity:.9;transform:translateY(-1px)}}

/* HERO base */
.hero{{background:var(--p);padding:100px 28px 90px;text-align:center;position:relative;overflow:hidden}}
.hero::before{{content:'';position:absolute;top:-80px;left:50%;transform:translateX(-50%);width:800px;height:800px;border-radius:50%;background:radial-gradient(circle,rgba(255,255,255,.035) 0%,transparent 65%);pointer-events:none}}
.hero-eyebrow{{display:inline-flex;align-items:center;gap:8px;color:var(--a);font-size:.72rem;font-weight:700;letter-spacing:.12em;text-transform:uppercase;margin-bottom:28px}}
.hero-eyebrow::before{{content:'';width:20px;height:1px;background:var(--a)}}
.hero-eyebrow::after{{content:'';width:20px;height:1px;background:var(--a)}}
.hero h1{{font-size:clamp(2.2rem,5vw,3.4rem);font-weight:600;line-height:1.1;color:#F8F7F3;max-width:660px;margin:0 auto 20px;letter-spacing:-.02em}}
.hero h1 em{{font-style:italic;color:var(--a)}}
.hero-sub{{font-size:1rem;color:rgba(248,247,243,.62);max-width:500px;margin:0 auto 44px;line-height:1.72}}
.hero-btns{{display:flex;gap:14px;justify-content:center;flex-wrap:wrap}}
.hero-btn-primary{{background:var(--a);color:var(--p);padding:14px 32px;border-radius:100px;font-size:.9rem;font-weight:700;letter-spacing:.01em;transition:all .2s}}
.hero-btn-primary:hover{{opacity:.9;transform:translateY(-1px)}}
.hero-btn-secondary{{background:rgba(248,247,243,.08);border:1px solid rgba(248,247,243,.2);color:rgba(248,247,243,.8);padding:14px 28px;border-radius:100px;font-size:.88rem;font-weight:500;transition:all .2s}}
.hero-btn-secondary:hover{{background:rgba(248,247,243,.13);color:#F8F7F3}}

/* STATS BAR */
.stats-bar{{background:#F8F7F3;border-bottom:1px solid var(--border);padding:32px 28px}}
.stats-inner{{max-width:1060px;margin:0 auto;display:flex;justify-content:center;gap:0;flex-wrap:wrap}}
.stat-item{{flex:1;min-width:150px;text-align:center;padding:16px 20px;border-right:1px solid var(--border)}}
.stat-item:last-child{{border-right:none}}
.stat-num{{font-size:2rem;font-weight:600;color:var(--p);line-height:1;margin-bottom:4px}}
.stat-label{{font-size:.72rem;font-weight:500;color:var(--ink3);letter-spacing:.05em;text-transform:uppercase}}

/* SERVICES */
.services{{padding:90px 28px;background:#F8F7F3}}
.section-eyebrow{{font-size:.68rem;font-weight:700;text-transform:uppercase;letter-spacing:.12em;color:var(--ink3);margin-bottom:12px}}
.section-h2{{font-size:clamp(1.7rem,4vw,2.2rem);font-weight:600;color:var(--p);margin-bottom:12px;letter-spacing:-.02em}}
.section-sub{{font-size:.9rem;color:var(--ink2);line-height:1.72;max-width:520px;margin-bottom:52px}}
.svc-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}}
.svc-card{{background:#fff;border:1px solid var(--border);border-radius:12px;padding:32px 26px;transition:all .3s}}
.svc-card:hover{{box-shadow:0 4px 24px rgba(36,37,40,.07);transform:translateY(-2px)}}
.svc-icon{{width:44px;height:44px;background:var(--ad);border-radius:10px;display:flex;align-items:center;justify-content:center;margin-bottom:18px}}
.svc-card h3{{font-size:1rem;font-weight:700;color:var(--p);margin-bottom:8px}}
.svc-card p{{font-size:.85rem;color:var(--ink2);line-height:1.65}}

/* TESTIMONIAL */
.testimonial{{padding:90px 28px;background:var(--p)}}
.testimonial-inner{{max-width:700px;margin:0 auto;text-align:center}}
.quote-mark{{font-size:4rem;color:var(--a);line-height:.8;margin-bottom:16px;opacity:.5}}
.testimonial blockquote{{font-size:clamp(1.2rem,3vw,1.6rem);font-weight:400;font-style:italic;color:#F8F7F3;line-height:1.55;margin-bottom:32px;letter-spacing:-.01em}}
.testimonial-name{{font-size:.82rem;font-weight:700;color:var(--a);letter-spacing:.05em;text-transform:uppercase}}
.testimonial-role{{font-size:.76rem;color:rgba(248,247,243,.45);margin-top:4px}}

/* CTA */
.cta-section{{padding:90px 28px;background:#EEE9E1;text-align:center}}
.cta-section h2{{font-size:clamp(1.7rem,4vw,2.2rem);font-weight:600;color:var(--p);margin-bottom:14px;letter-spacing:-.02em}}
.cta-section p{{font-size:.92rem;color:var(--ink2);max-width:480px;margin:0 auto 36px;line-height:1.72}}
.cta-btn{{display:inline-flex;align-items:center;gap:8px;background:var(--p);color:#F8F7F3;padding:15px 34px;border-radius:100px;font-size:.92rem;font-weight:700;letter-spacing:.01em;transition:all .25s}}
.cta-btn:hover{{background:var(--p2);transform:translateY(-1px);box-shadow:0 8px 24px rgba(36,37,40,.15)}}
.cta-sub{{font-size:.76rem;color:var(--ink3);margin-top:14px}}

/* FOOTER */
.sitefooter{{background:var(--p);padding:40px 28px;display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:16px}}
.sitefooter-brand{{font-size:.95rem;font-weight:600;color:#F8F7F3}}
.sitefooter-brand em{{color:var(--a);font-style:italic}}
.sitefooter-text{{font-size:.72rem;color:rgba(248,247,243,.38)}}
.sitefooter-links{{display:flex;gap:20px}}
.sitefooter-links a{{font-size:.72rem;color:rgba(248,247,243,.38);transition:color .2s}}
.sitefooter-links a:hover{{color:rgba(248,247,243,.75)}}

@media(max-width:720px){{
  .svc-grid{{grid-template-columns:1fr}}
  .sitenav-links{{display:none}}
  .stats-inner{{gap:0}}
  .stat-item{{min-width:50%;border-bottom:1px solid var(--border)}}
  .stat-item:nth-child(even){{border-right:none}}
  .sample-banner{{flex-direction:column;gap:8px;text-align:center}}
  .sitefooter{{flex-direction:column;text-align:center}}
  .sitefooter-links{{justify-content:center}}
}}

/* ── DESIGN STYLE OVERRIDES ──────────────────────────────── */
{style_css}
</style>
</head>
<body>

<!-- SAMPLE BANNER -->
<div class="sample-banner">
  <div class="sample-banner-left">
    <div class="sample-dot"></div>
    <div class="sample-banner-text">Sample website — designed by <strong>White Haus Media</strong> for {title}</div>
  </div>
  <a href="index.html" class="sample-banner-link">View Proposal &#8250;</a>
</div>

<!-- NAV -->
<nav class="sitenav">
  <div class="sitenav-inner">
    <div class="sitenav-brand">{title.split()[0]} <em>{" ".join(title.split()[1:3]) if len(title.split()) > 1 else ""}</em></div>
    <ul class="sitenav-links">
      <li><a href="#services">Services</a></li>
      <li><a href="#">About</a></li>
      <li><a href="#contact">Contact</a></li>
    </ul>
    <a href="#contact" class="sitenav-cta">{hero_cta}</a>
  </div>
</nav>

{hero_html}

<!-- STATS -->
<div class="stats-bar">
  <div class="stats-inner">
    {stats_html}
  </div>
</div>

<!-- SERVICES -->
<section class="services" id="services">
  <div class="wrap">
    <div class="section-eyebrow">What We Do</div>
    <h2 class="section-h2">{services_heading}</h2>
    <p class="section-sub">{services_sub}</p>
    <div class="svc-grid">
      {services_html}
    </div>
  </div>
</section>

<!-- TESTIMONIAL -->
<section class="testimonial">
  <div class="testimonial-inner">
    <div class="quote-mark">&#8220;</div>
    <blockquote>{testimonial_quote}</blockquote>
    <div class="testimonial-name">{testimonial_name}</div>
    <div class="testimonial-role">{testimonial_role}</div>
  </div>
</section>

<!-- CTA -->
<section class="cta-section" id="contact">
  <div class="wrap">
    <h2>Ready to get started?</h2>
    <p>{footer_tagline}</p>
    <a href="#" class="cta-btn">{hero_cta}</a>
    <div class="cta-sub">{domain}</div>
  </div>
</section>

<!-- FOOTER -->
<footer class="sitefooter">
  <div class="sitefooter-brand">{title.split()[0]} <em>{" ".join(title.split()[1:3]) if len(title.split()) > 1 else ""}</em></div>
  <div class="sitefooter-links">
    <a href="#">Services</a>
    <a href="#">About</a>
    <a href="#contact">Contact</a>
  </div>
  <div class="sitefooter-text">Sample site designed by White Haus Media &middot; whitehausmedia.com</div>
</footer>

<script>
(function(){{
  var obs=new IntersectionObserver(function(e){{e.forEach(function(x){{if(x.isIntersecting){{x.target.style.opacity='1';x.target.style.transform='translateY(0)';obs.unobserve(x.target);}}}});}},{{threshold:.1,rootMargin:'0px 0px -30px 0px'}});
  document.querySelectorAll('.svc-card,.stat-item').forEach(function(el){{el.style.opacity='0';el.style.transform='translateY(16px)';el.style.transition='opacity .6s ease,transform .6s ease';obs.observe(el);}});
}})();
</script>
</body>
</html>'''


# ── PROPOSALS ─────────────────────────────────────────────────────────────────

proposals = [

  dict(
    slug="law-offices-john-k-cook",
    title="Law Offices of John K. Cook, P.A.",
    prepared_for="John",
    date_str="April 20, 2026",
    hook_h1='Your website links to <em>Google+.</em><br>Google shut it down in 2019.',
    hook_sub="lawofjkc.com is still running on an early-2000s Thryv template with a dead social link and content that hasn't been touched in years. In Wake Forest's growing market, that's costing you cases before anyone picks up the phone.",
    letter_body=[
      "We came across lawofjkc.com while researching law firms in the Wake Forest area. You have 28+ years of practice here — that's a real differentiator. What stood out wasn't the work itself, it was the gap between the quality of that practice and what someone sees when they find you online.",
      "The site still has a link to Google+, which Google shut down in 2019. It's running on an old Thryv directory template. There's no mobile optimization, no blog, no Google Business integration. A client searching for an attorney in Wake Forest in 2026 is going to compare you to firms with modern, professional sites — and the first impression matters.",
      "We put together a proposal for what we'd build instead. It's a flat fee, no monthly contracts unless you want ongoing support, and we deliver in under two weeks. Take a look.",
    ],
    issues=[
      ("01", "Google+ link on a platform that closed in 2019", "The footer of lawofjkc.com still links to a Google+ profile. Google shut down Google+ in April 2019. It's a small detail that signals to every visitor — and to Google's crawlers — that this site hasn't been maintained in years."),
      ("02", "Early-2000s Thryv directory template", "The site is built on a Thryv directory template that reads as a placeholder, not a professional law firm presence. There's no custom design, no real photography, and no visual identity that communicates the caliber of a 28-year practice."),
      ("03", "No mobile optimization — 60%+ of searches are on mobile", "lawofjkc.com is not responsive. On a phone, the layout breaks and the text is nearly unreadable. Most people searching for a local attorney do it on their phone, often in a moment of urgency. A site that doesn't work on mobile loses those clients immediately."),
      ("04", "No blog, no content, near-zero SEO", "There is no blog, no articles, no resources — nothing for Google to index beyond a few static pages. A law firm in a growing market like Wake Forest should be ranking for dozens of local legal search terms. Right now, that visibility doesn't exist."),
    ],
    deliverables=[
      "Custom responsive website — built from scratch, not a template",
      "Mobile-first design optimized for readability and trust",
      "Practice area pages (up to 5) with proper SEO structure",
      "Attorney bio with professional photography guidance",
      "Blog foundation — first 2 posts written and published",
      "Google Business integration and local SEO setup",
      "Contact form + consultation booking capability",
      "SSL, hosting coordination, and launch support",
    ],
    price=797,
    price_label="Custom Website Package",
    includes=[
      "Custom design and development — no templates",
      "Mobile-first responsive build",
      "Practice area pages (up to 5)",
      "Attorney bio and firm history section",
      "Blog with 2 starter posts",
      "Google Business integration and local SEO",
      "Contact form with consultation scheduling",
      "SSL setup, hosting coordination, and launch",
      "30 days post-launch support",
    ],
    # Revenue idea
    revenue_title="Fixed-Fee Document Packages",
    revenue_body="Wake Forest's residential growth is producing a steady stream of clients who need wills, powers of attorney, and simple real estate documents — but don't want to pay hourly rates for straightforward paperwork. A tiered fixed-fee document service (Estate Starter: $297, Full Package: $597) marketed directly from the site could add a predictable revenue stream without taking time from complex litigation work. It also builds the client pipeline early, before the complicated matters arise.",
    revenue_stat="$1,500–$3,000/mo",
    # ROI Calculator
    roi_industry="legal",
    roi_label="What one new client per month is worth to your practice",
    roi1_label="New consultations from the site (per month)",
    roi1_default=3,
    roi2_label="Average case or document value ($)",
    roi2_default=2500,
    roi_output_label="Estimated monthly revenue from site-driven clients",
    # Preview
    # Sample site
    sample_domain="lawofjkc.com",
    sample_primary="#0F2440", sample_primary_mid="#1A3A5C",
    sample_accent="#C8B97A", sample_accent_dim="rgba(200,185,122,.1)", sample_accent_border="rgba(200,185,122,.28)",
    sample_hero_eyebrow="Wake Forest, NC · Since 1996",
    sample_hero_h1="Trusted Legal Counsel<br>for <em>28 Years</em>",
    sample_hero_sub="From estate planning to real estate closings, we give Wake Forest families and businesses the legal clarity they deserve.",
    sample_hero_cta="Schedule a Consultation",
    sample_services=[
      ('<path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>', "Estate Planning", "Wills, powers of attorney, healthcare directives, and trust administration — built around your family's specific situation."),
      ('<path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>', "Real Estate Law", "Closings, title review, deed preparation, and contract review for buyers, sellers, and investors across the Triangle."),
      ('<path d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>', "Business Law", "Entity formation, contracts, employment agreements, and general counsel for businesses at every stage of growth."),
    ],
    sample_stats=[("28+", "Years serving Wake Forest"), ("500+", "Estates planned"), ("2,000+", "Closings completed"), ("5★", "Client rating")],
    sample_testimonial_quote="John Cook has handled our family's legal needs for over 15 years. He's the kind of attorney who actually explains things — you leave every meeting knowing exactly where you stand.",
    sample_testimonial_name="Margaret T.",
    sample_testimonial_role="Estate planning client, Wake Forest NC",
    sample_footer_tagline="Schedule a free 20-minute consultation and find out exactly what you need — no pressure, no obligation.",
    sample_design_style='law',
    sample_font_url='https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;0,700;1,500;1,600&family=DM+Sans:ital,opsz,wght@0,9..40,400;0,9..40,500;0,9..40,600&display=swap',
    sample_heading_font="'Playfair Display',Georgia,serif",
    sample_body_font="'DM Sans',-apple-system,sans-serif",
    sample_services_heading='Practice Areas',
    sample_services_sub="28 years across Wake Forest's most important legal needs — estate planning, property, and business.",
  ),

  dict(
    slug="freedom-realty-firm",
    title="Freedom Realty Firm",
    prepared_for="Rich",
    date_str="April 20, 2026",
    hook_h1='Every buyer who searches your listings<br>hits <em>an error page.</em>',
    hook_sub="The 'Search Triangle Homes' feature on freedomrealtyfirm.com points to a broken subdomain. Your core product — the thing buyers come to a real estate site for — returns an error. That's not a minor issue.",
    letter_body=[
      "We reviewed freedomrealtyfirm.com while researching real estate brokers in the Holly Springs area. The site has some real problems that are directly costing you leads, and we wanted to put together something concrete rather than just flag the issues.",
      "The most significant one: the property search function routes to a subdomain that returns a broken error page. Buyers who come to your site looking to browse listings hit a dead end. That's your primary conversion point, and it's not working.",
      "There's also raw JavaScript code rendering as visible text on parts of the site — a symptom of a Joomla CMS issue that's been there a while. And the top credential featured on the site is 'Broker of the Year 2010.' That's 16 years ago in a market that's changed completely since then.",
      "We can fix all of it. Take a look at what we'd build.",
    ],
    issues=[
      ("01", "Broken property search — your core product doesn't work", "The 'Search Triangle Homes' button routes to homesearch.freedomrealtyfirm.com, which returns an error page. Any buyer who comes to your site to browse listings hits a dead end. This is the single most important feature on a real estate website, and it's broken."),
      ("02", "Raw JavaScript code visible as text on the page", "Parts of freedomrealtyfirm.com render raw JS code as readable text instead of executing it. This is a Joomla rendering issue and it's been there long enough that it's indexed. It signals to visitors — and to Google — that the site is unmaintained."),
      ("03", "Top credential is 'Broker of the Year 2010'", "The most prominent trust signal on your homepage is an award from 2010 — 16 years ago, before the Triangle market became what it is today. In a competitive real estate market, your credentials need to reflect the current practice, not where you were a decade and a half ago."),
      ("04", "No Google Business integration, no mobile optimization", "There's no connection between the site and your Google Business profile, no schema markup for local real estate search, and the layout doesn't adapt cleanly to mobile. Buyers browsing listings on their phones — which is most buyers — get a degraded experience."),
    ],
    deliverables=[
      "Custom responsive website rebuilt from scratch",
      "Working MLS/IDX property search integration",
      "Agent bio and credentials section — current and compelling",
      "Neighborhood and market pages for Holly Springs and Triangle area",
      "Lead capture forms and consultation scheduling",
      "Google Business integration and local real estate SEO",
      "Mobile-first build optimized for property browsing",
      "SSL, hosting coordination, and launch support",
    ],
    price=797,
    price_label="Custom Website Package",
    includes=[
      "Custom design and development",
      "Working IDX/MLS property search",
      "Agent bio and updated credentials showcase",
      "Neighborhood and area pages",
      "Lead capture and consultation booking",
      "Google Business integration and local SEO",
      "Mobile-first responsive build",
      "SSL, hosting, and launch",
      "30 days post-launch support",
    ],
    # Revenue idea
    revenue_title="Relocation Guide Lead Funnel",
    revenue_body="The Triangle sees consistent corporate relocation — RTP, healthcare systems, and finance firms bring buyers from out of state who don't know the area. A downloadable 'Holly Springs & Triangle Relocation Guide' (PDF + email sequence) positioned as a free resource would capture out-of-state buyer emails weeks before they're ready to search. Most competing agents aren't doing this. The guide builds trust early, keeps Freedom Realty top of mind, and creates a warm referral pipeline with HR departments and relocation companies.",
    revenue_stat="2–4 additional closings/yr",
    # ROI Calculator
    roi_industry="realty",
    roi_label="What additional closings are worth to your business",
    roi1_label="Additional closings from the site (per year)",
    roi1_default=3,
    roi2_label="Average commission per closing ($)",
    roi2_default=8500,
    roi_output_label="Estimated monthly revenue from new closings",
    # Preview
    # Sample site
    sample_domain="freedomrealtyfirm.com",
    sample_primary="#1C3557", sample_primary_mid="#264B76",
    sample_accent="#C8A96E", sample_accent_dim="rgba(200,169,110,.1)", sample_accent_border="rgba(200,169,110,.28)",
    sample_hero_eyebrow="Holly Springs · Cary · Apex · Raleigh",
    sample_hero_h1="Find Your Triangle Home<br>with an Agent Who <em>Knows the Market</em>",
    sample_hero_sub="Transparent representation, no double-dipping, and a broker who's been closing in the Triangle for over 25 years.",
    sample_hero_cta="Search Homes",
    sample_services=[
      ('<path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>', "Buy a Home", "Expert buyer representation across Holly Springs, Apex, Cary, and the greater Triangle. No conflicts, no pressure — just clear guidance."),
      ('<path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>', "Sell Your Home", "Strategic pricing, professional photography, and a marketing plan that gets your home in front of the right buyers fast."),
      ('<path d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"/>', "Neighborhood Guides", "Detailed relocation guides for every Triangle neighborhood — schools, commute times, parks, and what life actually looks like."),
    ],
    sample_stats=[("25+", "Years in Triangle real estate"), ("$180M+", "In closed transactions"), ("98%", "Client satisfaction"), ("4.9★", "Average review")],
    sample_testimonial_quote="Rich didn't just find us a house — he found us the right neighborhood. He knew every street in Holly Springs and never once pushed us toward something that wasn't right for our family.",
    sample_testimonial_name="David & Sarah K.",
    sample_testimonial_role="Home buyers, Holly Springs NC",
    sample_footer_tagline="Whether you're buying, selling, or just exploring — reach out and let's talk about what makes sense for you.",
    sample_design_style='realty',
    sample_font_url='https://fonts.googleapis.com/css2?family=Nunito+Sans:ital,opsz,wght@0,6..12,400;0,6..12,500;0,6..12,600;0,6..12,700;0,6..12,800&family=Source+Serif+4:ital,opsz,wght@0,8..60,600;0,8..60,700;1,8..60,600&display=swap',
    sample_heading_font="'Source Serif 4',Georgia,serif",
    sample_body_font="'Nunito Sans',-apple-system,sans-serif",
    sample_services_heading='How We Work',
    sample_services_sub="Buying, selling, or relocating — we give you clear guidance from first call to closing, with no conflicts and no pressure.",
  ),

  dict(
    slug="warren-shackleford-thomas",
    title="Warren Shackleford Thomas Attorneys",
    prepared_for="the WST team",
    date_str="April 20, 2026",
    hook_h1='50 years of Wake Forest legal expertise.<br><em>None of it searchable online.</em>',
    hook_sub="wakeforestattorneys.com has no blog, no articles, no resources — nothing for Google to index beyond a few static pages. Half a century of legal knowledge, completely invisible to the people searching for it.",
    letter_body=[
      "We were researching law firms in Wake Forest and came across wakeforestattorneys.com. A firm practicing since 1974 — that's 50 years serving this community. That's a meaningful story, and a real differentiator in a market full of newer practices.",
      "What stood out is that none of that history is online in any usable way. There's no blog, no legal resources, no articles. The Facebook link in the footer is broken. The site has a URL that reads '/services/elementor-490/' — which is a leftover Elementor block ID, not a real page path. These are signs that the site was built and then left.",
      "A firm with this much history should be the first result when someone in Wake Forest searches for legal help. Right now, that visibility isn't there. We can change that.",
    ],
    issues=[
      ("01", "No blog, no articles, no searchable content", "wakeforestattorneys.com has zero published content beyond static service pages. No blog, no resources, no FAQ, no case studies. Google has almost nothing to index, which means the firm is invisible for the dozens of legal search queries Wake Forest residents run every day."),
      ("02", "No online scheduling — clients can only call", "There's no way to book a consultation online. In 2026, many prospective clients — especially younger ones facing their first legal issue — expect to be able to schedule directly from a website. A contact form with no confirmation and no scheduling capability loses those clients to firms that make it easier."),
      ("03", "Broken Facebook link and leftover builder URLs", "The footer links to a Facebook page that no longer resolves. And the site has internal URLs like '/services/elementor-490/' — raw Elementor block IDs that got published as page paths. Both signal a site that was set up and forgotten, not maintained."),
    ],
    deliverables=[
      "Custom responsive website rebuilt with proper page architecture",
      "Blog foundation with first 3 articles written and published",
      "Practice area pages optimized for local search",
      "Online consultation scheduling capability",
      "Attorney bios with professional photography guidance",
      "Google Business integration and Wake Forest local SEO",
      "Fixed navigation, clean URLs, and working social links",
      "SSL, hosting coordination, and launch support",
    ],
    price=597,
    price_label="Custom Website Package",
    includes=[
      "Custom design and development",
      "Blog with 3 starter articles",
      "Practice area pages (up to 5) with local SEO",
      "Online consultation booking",
      "Attorney bios section",
      "Google Business integration",
      "Clean URL structure and fixed navigation",
      "SSL, hosting, and launch",
      "30 days post-launch support",
    ],
    # Revenue idea
    revenue_title="Small Business Legal Membership ($97/mo)",
    revenue_body="Wake Forest's business district is growing, and small businesses — contractors, retailers, service providers — consistently need routine legal guidance: contract reviews, employment questions, lease renewals. A flat-fee legal membership ($97/month) offering monthly Q&A access, one contract review, and a quarterly check-in would create predictable recurring revenue for the firm and genuine ongoing value for clients. With 50 years in this community, WST has the credibility to make this offer compelling to businesses that can't afford retainer-level fees.",
    revenue_stat="$970/mo per 10 members",
    # ROI Calculator
    roi_industry="legal",
    roi_label="What consistent online visibility means for new client intake",
    roi1_label="New consultations from the site (per month)",
    roi1_default=4,
    roi2_label="Average case value ($)",
    roi2_default=1800,
    roi_output_label="Estimated monthly revenue from site-driven clients",
    # Preview
    # Sample site
    sample_domain="wakeforestattorneys.com",
    sample_primary="#243320", sample_primary_mid="#344A2E",
    sample_accent="#C8A96E", sample_accent_dim="rgba(200,169,110,.1)", sample_accent_border="rgba(200,169,110,.28)",
    sample_hero_eyebrow="Wake Forest, NC · Established 1974",
    sample_hero_h1="50 Years of Legal Service<br>to <em>Wake Forest</em>",
    sample_hero_sub="Three generations of trusted counsel. From real estate closings to estate planning, we've been protecting Wake Forest families since 1974.",
    sample_hero_cta="Schedule a Consultation",
    sample_services=[
      ('<path d="M3 9l9-7 9 7v11a2 2 0 01-2 2H5a2 2 0 01-2-2z"/><polyline points="9 22 9 12 15 12 15 22"/>', "Real Estate & Title", "Closings, deed preparation, title examination, and 1031 exchanges — handled with the precision that real estate transactions require."),
      ('<path d="M9 12l2 2 4-4M7.835 4.697a3.42 3.42 0 001.946-.806 3.42 3.42 0 014.438 0 3.42 3.42 0 001.946.806 3.42 3.42 0 013.138 3.138 3.42 3.42 0 00.806 1.946 3.42 3.42 0 010 4.438 3.42 3.42 0 00-.806 1.946 3.42 3.42 0 01-3.138 3.138 3.42 3.42 0 00-1.946.806 3.42 3.42 0 01-4.438 0 3.42 3.42 0 00-1.946-.806 3.42 3.42 0 01-3.138-3.138 3.42 3.42 0 00-.806-1.946 3.42 3.42 0 010-4.438 3.42 3.42 0 00.806-1.946 3.42 3.42 0 013.138-3.138z"/>', "Estate Planning & Probate", "Wills, trusts, powers of attorney, and estate administration — plain-language guidance for every stage of life."),
      ('<path d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"/>', "Business & Civil Litigation", "Entity formation, contract disputes, and civil litigation — representing Wake Forest businesses with the experience that 50 years builds."),
    ],
    sample_stats=[("50+", "Years in Wake Forest"), ("3", "Generations of attorneys"), ("10,000+", "Clients served"), ("5★", "Community reputation")],
    sample_testimonial_quote="This firm has handled every legal matter our family has had for thirty years. They know our names, our history, and what we need. That kind of relationship doesn't exist at most law firms.",
    sample_testimonial_name="Robert H.",
    sample_testimonial_role="Long-time client, Wake Forest NC",
    sample_footer_tagline="Call or book online for a straightforward consultation. We'll tell you exactly what you need — and what you don't.",
    sample_design_style='heritage_law',
    sample_font_url='https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@400;500;600&display=swap',
    sample_heading_font="'EB Garamond',Georgia,serif",
    sample_body_font="'Inter',-apple-system,sans-serif",
    sample_services_heading='Practice Areas',
    sample_services_sub="Fifty years of counsel for Wake Forest families and businesses — the depth of experience that matters most when it counts.",
  ),

  dict(
    slug="woodalls-fitness",
    title="Woodall's Fitness",
    prepared_for="the Woodall's team",
    date_str="April 20, 2026",
    hook_h1='20 years of fitness content.<br><em>All of it on Constant Contact.</em>',
    hook_sub="Every Strength Report article on woodallsfitness.com links out to conta.cc — Constant Contact's domain. Your content is building someone else's traffic. Every article, every tip, every piece of expertise belongs to a third-party platform instead of your site.",
    letter_body=[
      "We looked at woodallsfitness.com while researching fitness studios in the Clayton area. Twenty years is a long time to build a community, and it's clear the expertise is real. What caught our attention was where that expertise actually lives online.",
      "Every article in the Strength Report section links to conta.cc — Constant Contact's platform. When a member or prospective client reads one of those articles, they're on Constant Contact's domain, not yours. Google credits Constant Contact, not Woodall's Fitness, for that content. All the SEO value from two decades of fitness knowledge is going to a third-party email tool.",
      "There's also no online booking — just a contact form. And the page title on the homepage reads 'Fueling Your Fitness' which is great branding but tells Google nothing about who or where you are.",
      "We can bring all of that on-site and fix what's holding the site back.",
    ],
    issues=[
      ("01", "All Strength Report content lives on Constant Contact's domain", "Every article linked from woodallsfitness.com routes to conta.cc — Constant Contact's platform. Readers leave your site, and Google credits that content to Constant Contact's domain, not yours. Two decades of fitness expertise should be building your domain authority, not theirs."),
      ("02", "No online booking — a contact form is not a membership flow", "Someone ready to join Woodall's fills out a contact form and waits for a callback. Every hour between that submission and your response is an opportunity for them to sign up somewhere else. Real-time booking or a direct membership sign-up eliminates that friction entirely."),
      ("03", "Page title is a tagline, not a search term", "The browser tab on the homepage reads 'Fueling Your Fitness.' That's strong brand copy — but it tells Google nothing about what Woodall's is, where it is, or who it serves. People searching for a gym in Clayton aren't finding woodallsfitness.com because the site isn't optimized for those searches."),
    ],
    deliverables=[
      "Custom responsive website built around Woodall's brand",
      "On-site blog — migrate Strength Report content to woodallsfitness.com",
      "Membership sign-up or direct booking flow",
      "Class schedule display — easy to update",
      "Local SEO foundation: proper titles, meta tags, Google Business integration",
      "Social media integration with live feeds",
      "Mobile-first build with fast load times",
      "SSL, hosting coordination, and launch support",
    ],
    price=597,
    price_label="Custom Website Package",
    includes=[
      "Custom design and development",
      "On-site blog with content migration from Constant Contact",
      "Membership sign-up or booking flow",
      "Class schedule page",
      "Local SEO: titles, meta tags, Google Business",
      "Social integration",
      "Mobile-first responsive build",
      "SSL, hosting, and launch",
      "30 days post-launch support",
    ],
    # Revenue idea
    revenue_title="Online Training Membership ($47/mo)",
    revenue_body="Woodall's has 20 years of programming knowledge and an established member community. A digital membership — workout programs, nutrition guides, video content — would let the brand serve clients who've moved away, prospects outside of Clayton, and members who want more than their in-person sessions. At $47/month with just 30 subscribers, that's $1,400/month in revenue that doesn't require a single additional square foot of gym space. The existing Strength Report content library is the foundation — it just needs to live on woodallsfitness.com and sit behind a paywall.",
    revenue_stat="$1,400+/mo at 30 members",
    # ROI Calculator
    roi_industry="fitness",
    roi_label="What removing booking friction is worth per month",
    roi1_label="New members from online sign-up (per month)",
    roi1_default=8,
    roi2_label="Monthly membership fee ($)",
    roi2_default=55,
    roi_output_label="Estimated monthly recurring revenue from new members",
    # Preview
    # Sample site
    sample_domain="woodallsfitness.com",
    sample_primary="#1A1F2E", sample_primary_mid="#252C40",
    sample_accent="#D4A843", sample_accent_dim="rgba(212,168,67,.1)", sample_accent_border="rgba(212,168,67,.28)",
    sample_hero_eyebrow="Clayton, NC · Training Since 2004",
    sample_hero_h1="Train Harder.<br>Recover Smarter.<br><em>Perform Better.</em>",
    sample_hero_sub="20 years of results-driven coaching in Clayton, NC. Whether you're just starting or competing — Woodall's builds athletes.",
    sample_hero_cta="Start Your Free Trial",
    sample_services=[
      ('<path d="M13 10V3L4 14h7v7l9-11h-7z"/>', "Personal Training", "One-on-one coaching built around your goals, your schedule, and where you are today. Real programming, real accountability."),
      ('<path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/>', "Group Classes", "High-energy group training sessions for all fitness levels. Strength, conditioning, and mobility — scheduled throughout the week."),
      ('<path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"/>', "Performance Programs", "Sport-specific programming for athletes looking to improve speed, strength, and competitive performance. Evidence-based, results-measured."),
    ],
    sample_stats=[("20+", "Years coaching in Clayton"), ("500+", "Members trained"), ("3", "Program tracks"), ("4.9★", "Google rating")],
    sample_testimonial_quote="I've been training at Woodall's for six years. The programming is serious, the coaches actually know what they're doing, and the community keeps you coming back. Best decision I made for my health.",
    sample_testimonial_name="Marcus L.",
    sample_testimonial_role="Member since 2018, Clayton NC",
    sample_footer_tagline="Sign up online in 60 seconds. Your first week is on us — no pressure, no commitment.",
    sample_design_style='fitness',
    sample_font_url='https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,700;0,800;1,700&family=Barlow:wght@400;500;600&display=swap',
    sample_heading_font="'Barlow Condensed',Impact,sans-serif",
    sample_body_font="'Barlow',-apple-system,sans-serif",
    sample_services_heading='Training Programs',
    sample_services_sub="20 years of building athletes in Clayton. Every program is built around measurable performance — show up and put in the work.",
  ),

  dict(
    slug="zen-triangle-dentistry",
    title="Zen Triangle Dentistry",
    prepared_for="the Zen Triangle team",
    date_str="April 20, 2026",
    hook_h1='Patients are ready to book.<br><em>Your site makes them wait.</em>',
    hook_sub="zentriangledentistry.com has a 'Book an Appointment' button — but it leads to a static contact form. No real-time availability, no instant confirmation. In a market where patients expect to book like they'd book anything else, that friction sends them to the next practice.",
    letter_body=[
      "We were reviewing dental practices in the Cary area and spent some time on zentriangledentistry.com. The site is clean and the service list is strong — 30+ procedures including cosmetic, restorative, and IV sedation. That's a comprehensive practice.",
      "A few things stood out that are worth addressing. The 'Book an Appointment' call to action leads to a static contact form, not a real-time scheduler. For a prospective patient ready to commit, that's friction at exactly the wrong moment.",
      "There's also a testimonials section with no testimonials — it's visually present but empty, which actually reads worse than no testimonials section at all. And the site has no schema markup, which means Google can't identify it as a dental practice or surface the star ratings, hours, and 'dentist near me' results that drive local patient acquisition.",
      "We put together a proposal for what we'd fix and build.",
    ],
    issues=[
      ("01", "Booking button leads to a static form, not a scheduler", "The 'Book an Appointment' CTA on zentriangledentistry.com leads to a contact form. Patients fill it out and wait. Real-time scheduling lets them see availability, pick a time, and get an instant confirmation — removing the single biggest friction point in converting a visitor to a booked patient."),
      ("02", "Testimonials section is empty", "The site has a dedicated testimonials section, but there are no reviews, no names, no patient quotes — just a heading and white space. For a healthcare practice, an empty testimonials section is worse than no section at all. It signals that no one has vouched for the practice, which creates doubt at exactly the wrong moment."),
      ("03", "No schema markup — invisible in local dental searches", "Google uses structured data (schema) to identify dental practices, display star ratings, and surface 'dentist near me' results. zentriangledentistry.com has no schema markup, which means Google has to guess what kind of business it is. Cary is a fast-growing market and competitors with proper schema are capturing local visibility this practice should own."),
    ],
    deliverables=[
      "Custom responsive website with clean, clinical aesthetic",
      "Real-time appointment booking integration",
      "Live reviews feed pulling from Google and other verified sources",
      "Service pages (up to 8) optimized for local dental search",
      "Dental practice schema markup and local SEO foundation",
      "Google Business integration",
      "Patient resources section (FAQ, insurance info, new patient forms)",
      "SSL, hosting coordination, and launch support",
    ],
    price=797,
    price_label="Custom Website Package — Dental",
    includes=[
      "Custom design and development",
      "Real-time appointment booking integration",
      "Live reviews / testimonials feed",
      "Service pages (up to 8)",
      "Dental schema markup and local SEO",
      "Google Business integration",
      "New patient resources section",
      "SSL, hosting, and launch",
      "30 days post-launch support",
    ],
    # Revenue idea
    revenue_title="Whitening Membership Club ($79/mo)",
    revenue_body="Cary's demographics skew toward professionals who prioritize their appearance and are comfortable with subscription services. A teeth-whitening membership — monthly in-office treatment or take-home kit, plus 15% off any cosmetic procedure — converts cosmetic-curious patients into recurring revenue. At $79/month it's approachable for patients, and it creates a natural upsell path to veneers, bonding, and other high-margin services. The membership page and sign-up flow would live directly on the new site, capturing patients who are already browsing the services page.",
    revenue_stat="$1,975+/mo at 25 members",
    # ROI Calculator
    roi_industry="dental",
    roi_label="What real-time booking means for your patient acquisition",
    roi1_label="New patients from the site (per month)",
    roi1_default=5,
    roi2_label="Average new patient value ($)",
    roi2_default=450,
    roi_output_label="Estimated monthly revenue from new patients",
    # Preview
    # Sample site
    sample_domain="zentriangledentistry.com",
    sample_primary="#163544", sample_primary_mid="#1F4A5E",
    sample_accent="#7BBAC8", sample_accent_dim="rgba(123,186,200,.1)", sample_accent_border="rgba(123,186,200,.28)",
    sample_hero_eyebrow="Cary, NC · Family & Cosmetic Dentistry",
    sample_hero_h1="A Dental Experience<br>That Feels <em>Different</em>",
    sample_hero_sub="Comprehensive care for the whole family — from routine cleanings to full-smile transformations. Book online in under a minute.",
    sample_hero_cta="Book an Appointment",
    sample_services=[
      ('<path d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"/>', "Preventive Care", "Cleanings, exams, X-rays, and fluoride treatments — the foundation of long-term oral health for every member of your family."),
      ('<circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/>', "Cosmetic Dentistry", "Teeth whitening, veneers, bonding, and full smile makeovers — designed to give you confidence in every conversation."),
      ('<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>', "Restorative Dentistry", "Crowns, bridges, implants, and root canals performed with precision and comfort — restoring function and appearance at the same time."),
    ],
    sample_stats=[("5,000+", "Patients treated"), ("30+", "Procedures offered"), ("IV Sedation", "Available"), ("4.9★", "Google reviews")],
    sample_testimonial_quote="I used to dread going to the dentist. Zen Triangle changed that completely. The whole team is calm, the office is beautiful, and they actually explain what they're doing. I don't stress about appointments anymore.",
    sample_testimonial_name="Priya M.",
    sample_testimonial_role="Patient, Cary NC",
    sample_footer_tagline="Booking takes less than a minute. Pick a time that works for you and we'll take care of the rest.",
    sample_design_style='dental',
    sample_font_url='https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap',
    sample_heading_font="'DM Sans',-apple-system,sans-serif",
    sample_body_font="'DM Sans',-apple-system,sans-serif",
    sample_services_heading='Our Services',
    sample_services_sub="From your first cleaning to a complete smile transformation — comprehensive care for every member of your family.",
  ),

]

# Build and push all proposals
for p in proposals:
    slug = p["slug"]
    print(f"\n--- Building {slug} ---")

    # 1. Build the standalone sample site (preview.html)
    preview_html = build_sample_site(
        slug=slug, title=p["title"], domain=p["sample_domain"],
        primary=p["sample_primary"], primary_mid=p["sample_primary_mid"],
        accent=p["sample_accent"], accent_dim=p["sample_accent_dim"],
        accent_border=p["sample_accent_border"],
        hero_eyebrow=p["sample_hero_eyebrow"], hero_h1=p["sample_hero_h1"],
        hero_sub=p["sample_hero_sub"], hero_cta=p["sample_hero_cta"],
        services=p["sample_services"], stats=p["sample_stats"],
        testimonial_quote=p["sample_testimonial_quote"],
        testimonial_name=p["sample_testimonial_name"],
        testimonial_role=p["sample_testimonial_role"],
        footer_tagline=p["sample_footer_tagline"],
        design_style=p.get("sample_design_style", "default"),
        font_url=p.get("sample_font_url"),
        heading_font=p.get("sample_heading_font"),
        body_font=p.get("sample_body_font"),
        services_heading=p.get("sample_services_heading", "Our Services"),
        services_sub=p.get("sample_services_sub", "Built around one goal — making it easier for the right clients to find you and choose you."),
    )

    # 2. Build the proposal (index.html) — embeds preview.html via iframe
    index_html = build_proposal(
        slug=slug, title=p["title"], prepared_for=p["prepared_for"],
        prepared_by="White Haus Media", date_str=p["date_str"],
        hook_h1=p["hook_h1"], hook_sub=p["hook_sub"],
        letter_body=p["letter_body"],
        issues=p["issues"], deliverables=p["deliverables"],
        price=p["price"], includes=p["includes"],
        revenue_title=p["revenue_title"], revenue_body=p["revenue_body"],
        revenue_stat=p["revenue_stat"],
        roi_industry=p["roi_industry"], roi_label=p["roi_label"],
        roi1_label=p["roi1_label"], roi1_default=p["roi1_default"],
        roi2_label=p["roi2_label"], roi2_default=p["roi2_default"],
        roi_output_label=p["roi_output_label"],
        sample_domain=p["sample_domain"]
    )

    # Push preview.html first (so iframe src resolves when index loads)
    print(f"  Pushing preview.html...", end=" ", flush=True)
    r = gh_push(f"proposals/{slug}/preview.html", preview_html, f"Rebuild {slug}: sample site homepage mockup")
    print(r)
    time.sleep(0.5)

    # Push index.html
    print(f"  Pushing index.html...", end=" ", flush=True)
    r = gh_push(f"proposals/{slug}/index.html", index_html, f"Rebuild {slug}: embedded sample site preview + fullscreen expand")
    print(r)
    time.sleep(0.5)

    # Sync to Supabase (create if new, log if existing)
    sb_upsert_proposal(slug, p["title"] + " — Website Proposal", p["price"])

print("\n✓ All 5 proposals rebuilt and pushed.")
