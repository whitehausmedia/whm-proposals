"""
WHM Proposal Sequence Runner
Runs daily — checks proposals table, sends Day 1/4/7/monthly emails via Resend.
Sequence tracking stored in proposals.notes as JSON.

Usage: python proposal_sequence_runner.py [--dry-run]
"""

import json
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone, timedelta

# ─── Config ────────────────────────────────────────────────────────────────────
# Load secrets from environment — set these before running:
#   export WHM_SUPABASE_KEY="eyJ..."
#   export WHM_RESEND_KEY="re_..."
SUPABASE_URL  = "https://lpdbffncosplssshclqh.supabase.co"
SUPABASE_KEY  = os.environ.get("WHM_SUPABASE_KEY", "")
RESEND_KEY    = os.environ.get("WHM_RESEND_KEY", "")
FROM_EMAIL    = "hello@send.whitehausmedia.com"
REPLY_TO      = "hello@whitehausmedia.com"
CALENDLY_URL  = "https://calendly.com/whitehausmedia"

DRY_RUN = "--dry-run" in sys.argv

# ─── Supabase helpers ──────────────────────────────────────────────────────────
def sb_get(path, params=""):
    url = f"{SUPABASE_URL}/rest/v1/{path}?{params}"
    req = urllib.request.Request(url, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    })
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def sb_patch(path, row_id, data):
    url = f"{SUPABASE_URL}/rest/v1/{path}?id=eq.{row_id}"
    payload = json.dumps(data).encode()
    req = urllib.request.Request(url, data=payload, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }, method="PATCH")
    with urllib.request.urlopen(req) as r:
        return r.status


def sb_log_communication(company_id, contact_id, subject, html_body):
    """Log every outbound sequence email to the communications table."""
    if DRY_RUN:
        return
    payload = json.dumps({
        "company_id": company_id,
        "contact_id": contact_id,
        "type": "email",
        "direction": "outbound",
        "subject": subject,
        "body": html_body[:800],  # truncate for storage
    }).encode()
    url = f"{SUPABASE_URL}/rest/v1/communications"
    req = urllib.request.Request(url, data=payload, headers={
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }, method="POST")
    try:
        with urllib.request.urlopen(req) as r:
            pass  # 201 = created
    except urllib.error.HTTPError as e:
        print(f"  WARN: failed to log communication: {e.code} {e.read().decode()[:100]}")


# ─── Resend helper ─────────────────────────────────────────────────────────────
def send_email(to_email, subject, html_body):
    if DRY_RUN:
        print(f"  [DRY RUN] Would send to {to_email}: {subject}")
        return True
    payload = json.dumps({
        "from": f"Colton at White Haus Media <{FROM_EMAIL}>",
        "reply_to": REPLY_TO,
        "to": [to_email],
        "subject": subject,
        "html": html_body,
    }).encode()
    req = urllib.request.Request(
        "https://api.resend.com/emails",
        data=payload,
        headers={"Authorization": f"Bearer {RESEND_KEY}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as r:
            result = json.loads(r.read())
            print(f"  Sent [{result.get('id', '?')}] → {to_email}")
            return True
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        print(f"  ERROR sending to {to_email}: {e.code} {err}")
        return False


# ─── Shared email components ───────────────────────────────────────────────────
def _signature_block():
    """Colton Palmer branded business card signature — email-safe HTML."""
    return """
  <!-- Signature -->
  <table cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:400px;margin:0 0 8px">
    <tr>
      <td style="border-left:3px solid #CEC195;padding:0 0 0 16px">
        <p style="margin:0 0 2px;font-size:15px;font-weight:700;color:#102A43;font-family:'Helvetica Neue',Arial,sans-serif;line-height:1.3">Colton Palmer</p>
        <p style="margin:0 0 10px;font-size:11px;color:#6889A6;font-family:'Helvetica Neue',Arial,sans-serif;letter-spacing:.08em;text-transform:uppercase;font-weight:600">Co-Founder &amp; Creative Director</p>
        <p style="margin:0 0 3px;font-size:13px;color:#242528;font-family:'Helvetica Neue',Arial,sans-serif">
          <a href="mailto:hello@whitehausmedia.com" style="color:#242528;text-decoration:none">hello@whitehausmedia.com</a>
        </p>
        <p style="margin:0 0 3px;font-size:13px;font-family:'Helvetica Neue',Arial,sans-serif">
          <a href="https://whitehausmedia.com" style="color:#102A43;text-decoration:none;font-weight:600">whitehausmedia.com</a>
          &nbsp;&middot;&nbsp;
          <a href="https://calendly.com/whitehausmedia" style="color:#102A43;text-decoration:none">Book a call</a>
        </p>
        <p style="margin:0;font-size:12px;color:#6889A6;font-family:'Helvetica Neue',Arial,sans-serif">Wake Forest, NC</p>
      </td>
    </tr>
  </table>"""


def _proposal_preview_card(company_name, proposal_url):
    """Rich branded proposal preview card — replaces plain URL in Day 1 email."""
    # Extract slug for display URL
    slug = proposal_url.rstrip("/").split("/")[-1] if proposal_url else ""
    display_url = f"whitehausmedia.com/proposals/{slug}" if slug else "whitehausmedia.com"
    return f"""
  <!-- Proposal Preview Card -->
  <table cellpadding="0" cellspacing="0" border="0" style="width:100%;max-width:540px;border-radius:10px;overflow:hidden;border:1px solid #1a3a58;margin:0 0 32px">
    <tr>
      <td style="background:#102A43;padding:28px 32px 24px">
        <!-- Label -->
        <p style="font-size:10px;color:#CEC195;letter-spacing:.12em;text-transform:uppercase;margin:0 0 16px;font-family:'Helvetica Neue',Arial,sans-serif;font-weight:700">Custom Website Proposal</p>
        <!-- Company name -->
        <h2 style="font-size:20px;color:#F8F7F3;margin:0 0 10px;font-family:'Helvetica Neue',Arial,sans-serif;font-weight:600;line-height:1.3">{company_name}</h2>
        <!-- Description -->
        <p style="font-size:14px;color:rgba(248,247,243,0.65);margin:0 0 22px;font-family:'Helvetica Neue',Arial,sans-serif;line-height:1.6">A custom concept built for your business — new design, clearer messaging, and a site that converts.</p>
        <!-- Divider -->
        <div style="height:1px;background:rgba(248,247,243,0.1);margin:0 0 22px"></div>
        <!-- Display URL -->
        <p style="font-size:11px;color:#6889A6;margin:0 0 18px;font-family:'Helvetica Neue',Arial,sans-serif;letter-spacing:.03em">{display_url}</p>
        <!-- CTA -->
        <a href="{proposal_url}" style="display:inline-block;background:#CEC195;color:#102A43;text-decoration:none;padding:11px 22px;font-size:12px;font-weight:700;letter-spacing:.06em;border-radius:5px;font-family:'Helvetica Neue',Arial,sans-serif;text-transform:uppercase">View Your Proposal &rarr;</a>
      </td>
    </tr>
    <tr>
      <td style="background:#0d2235;padding:10px 32px">
        <p style="font-size:11px;color:#6889A6;margin:0;font-family:'Helvetica Neue',Arial,sans-serif">White Haus Media &middot; Custom Web Design &middot; Wake Forest, NC</p>
      </td>
    </tr>
  </table>"""


# ─── Email templates ───────────────────────────────────────────────────────────
def email_day1(first_name, company_name, proposal_url):
    subject = f"Your proposal from White Haus Media — {company_name}"
    html = f"""
<div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:600px;margin:0 auto;color:#242528;line-height:1.7">
  <div style="border-top:3px solid #102A43;padding:40px 0 0">
    <p style="font-size:14px;color:#6889A6;letter-spacing:.08em;text-transform:uppercase;margin:0 0 28px">White Haus Media</p>
    <p style="font-size:16px;margin:0 0 20px">Hey {first_name},</p>
    <p style="font-size:16px;margin:0 0 20px">We put together a custom proposal for {company_name}. It covers what we found on your current site, what we'd build instead, and what that could mean for your business.</p>
    <p style="font-size:16px;margin:0 0 28px">Take a look:</p>

    {_proposal_preview_card(company_name, proposal_url)}

    <p style="font-size:16px;margin:0 0 28px">If anything in there sparks a question, or you want to talk through the scope, you can grab 20 minutes on my calendar: <a href="{CALENDLY_URL}" style="color:#102A43;font-weight:600">{CALENDLY_URL}</a></p>

    {_signature_block()}

    <hr style="border:none;border-top:1px solid #EEE9E1;margin:28px 0">
    <p style="font-size:12px;color:#8A8C90;margin:0">You're receiving this because we researched {company_name} and built a custom proposal. Reply to opt out.</p>
  </div>
</div>"""
    return subject, html


def email_day4(first_name, company_name, proposal_url):
    subject = f"Quick check-in — {company_name}"
    html = f"""
<div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:600px;margin:0 auto;color:#242528;line-height:1.7">
  <div style="border-top:3px solid #102A43;padding:40px 0 0">
    <p style="font-size:14px;color:#6889A6;letter-spacing:.08em;text-transform:uppercase;margin:0 0 28px">White Haus Media</p>
    <p style="font-size:16px;margin:0 0 20px">Hey {first_name},</p>
    <p style="font-size:16px;margin:0 0 20px">Just wanted to see if you had a chance to look at the proposal for {company_name}. No pressure — I know it can get buried.</p>
    <p style="font-size:16px;margin:0 0 28px">If you have any questions or want to talk through the project, just reply here or grab time on my calendar. The proposal link is below if you need it:</p>
    <div style="margin:0 0 28px">
      <a href="{CALENDLY_URL}" style="display:inline-block;background:#102A43;color:#F8F7F3;text-decoration:none;padding:13px 26px;font-size:13px;font-weight:700;letter-spacing:.04em;border-radius:5px;margin:0 8px 0 0;font-family:'Helvetica Neue',Arial,sans-serif">Schedule a Call</a>
      <a href="{proposal_url}" style="display:inline-block;color:#102A43;text-decoration:none;padding:13px 20px;font-size:13px;font-weight:600;letter-spacing:.04em;border:1px solid #102A43;border-radius:5px;font-family:'Helvetica Neue',Arial,sans-serif">View Proposal</a>
    </div>

    {_signature_block()}

    <hr style="border:none;border-top:1px solid #EEE9E1;margin:28px 0">
    <p style="font-size:12px;color:#8A8C90;margin:0">Reply to opt out of future messages.</p>
  </div>
</div>"""
    return subject, html


def email_day7(first_name, company_name, proposal_url):
    subject = f"Last note on this — {company_name}"
    html = f"""
<div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:600px;margin:0 auto;color:#242528;line-height:1.7">
  <div style="border-top:3px solid #102A43;padding:40px 0 0">
    <p style="font-size:14px;color:#6889A6;letter-spacing:.08em;text-transform:uppercase;margin:0 0 28px">White Haus Media</p>
    <p style="font-size:16px;margin:0 0 20px">Hey {first_name},</p>
    <p style="font-size:16px;margin:0 0 20px">One last check-in on the proposal for {company_name}. I don't want to keep filling your inbox if the timing isn't right.</p>
    <p style="font-size:16px;margin:0 0 28px">If this isn't a priority right now, no problem — I'll follow up in a couple months. If you're ready to move forward or want to talk through any of it, the fastest way is to grab 20 minutes:</p>
    <div style="margin:0 0 28px">
      <a href="{CALENDLY_URL}" style="display:inline-block;background:#102A43;color:#F8F7F3;text-decoration:none;padding:13px 26px;font-size:13px;font-weight:700;letter-spacing:.04em;border-radius:5px;font-family:'Helvetica Neue',Arial,sans-serif">Book a 20-Minute Call</a>
    </div>

    {_signature_block()}

    <hr style="border:none;border-top:1px solid #EEE9E1;margin:28px 0">
    <p style="font-size:12px;color:#8A8C90;margin:0">Reply to opt out — you won't hear from us again on this proposal.</p>
  </div>
</div>"""
    return subject, html


def email_nurture(first_name, company_name, proposal_url):
    subject = f"Checking in from White Haus Media — {company_name}"
    html = f"""
<div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:600px;margin:0 auto;color:#242528;line-height:1.7">
  <div style="border-top:3px solid #102A43;padding:40px 0 0">
    <p style="font-size:14px;color:#6889A6;letter-spacing:.08em;text-transform:uppercase;margin:0 0 28px">White Haus Media</p>
    <p style="font-size:16px;margin:0 0 20px">Hey {first_name},</p>
    <p style="font-size:16px;margin:0 0 20px">Just checking back in. We still have the proposal for {company_name} ready to go whenever the timing makes sense.</p>
    <p style="font-size:16px;margin:0 0 28px">We've been doing a lot of work with businesses in the Triangle recently — happy to share what's been working if it's helpful. Or if you're ready to revisit, the proposal is still live:</p>
    <div style="margin:0 0 28px">
      <a href="{proposal_url}" style="display:inline-block;background:#102A43;color:#F8F7F3;text-decoration:none;padding:13px 26px;font-size:13px;font-weight:700;letter-spacing:.04em;border-radius:5px;font-family:'Helvetica Neue',Arial,sans-serif">View Your Proposal</a>
    </div>

    {_signature_block()}

    <hr style="border:none;border-top:1px solid #EEE9E1;margin:28px 0">
    <p style="font-size:12px;color:#8A8C90;margin:0">Reply to opt out of future check-ins.</p>
  </div>
</div>"""
    return subject, html


# ─── Date helpers ──────────────────────────────────────────────────────────────
def parse_iso(s):
    """Parse ISO 8601 datetime string to UTC datetime."""
    if not s:
        return None
    # Handle both with and without timezone
    s = s.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(s)
    except Exception:
        return None


def now_utc():
    return datetime.now(timezone.utc)


def days_since(dt):
    if dt is None:
        return None
    delta = now_utc() - dt
    return delta.days


# ─── Main ──────────────────────────────────────────────────────────────────────
def run():
    print(f"\n{'[DRY RUN] ' if DRY_RUN else ''}WHM Proposal Sequence Runner — {now_utc().strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)

    # Fetch all proposals that are Approved or Sent (not Draft, Won, Lost)
    proposals = sb_get(
        "proposals",
        "status=in.(Approved,Sent)&select=id,company_id,deal_id,title,status,url,sent_date,notes"
    )
    print(f"Found {len(proposals)} proposal(s) in sequence\n")

    for prop in proposals:
        prop_id    = prop["id"]
        company_id = prop["company_id"]
        title      = prop["title"]
        status     = prop.get("status", "")
        url        = prop.get("url", "")
        sent_date  = prop.get("sent_date")  # DATE field (YYYY-MM-DD)

        # Parse sequence tracking from notes JSON
        raw_notes = prop.get("notes") or ""
        try:
            tracking = json.loads(raw_notes) if raw_notes.strip().startswith("{") else {}
        except Exception:
            tracking = {}

        sent_at          = parse_iso(tracking.get("sent_at"))
        followup1_sent   = parse_iso(tracking.get("followup1_sent_at"))
        followup2_sent   = parse_iso(tracking.get("followup2_sent_at"))
        nurture_active   = tracking.get("nurture_active", False)
        nurture_last     = parse_iso(tracking.get("nurture_last_sent_at"))

        print(f"  → {title} (proposal #{prop_id})")
        print(f"     URL:       {url}")
        print(f"     Tracking:  sent={bool(sent_at)} | f1={bool(followup1_sent)} | f2={bool(followup2_sent)} | nurture={nurture_active}")

        # Fetch primary contact for this company
        contacts = sb_get(
            "contacts",
            f"company_id=eq.{company_id}&select=id,first_name,last_name,email&limit=1"
        )
        if not contacts:
            print(f"     SKIP: no contact found for company_id={company_id}")
            continue

        contact    = contacts[0]
        first_name = contact.get("first_name") or "there"
        last_name  = contact.get("last_name") or ""
        email      = contact.get("email")

        if not email:
            print(f"     SKIP: no email for contact {first_name} {last_name}")
            continue

        print(f"     Contact:   {first_name} {last_name} <{email}>")

        company_name = title  # use proposal title as company name in emails
        contact_id = contact.get("id")

        updated = False

        # ── Day 1 — Initial send (Approved → Sent) ───────────────────────────
        if status == "Approved" and sent_at is None:
            print(f"     ACTION: Sending Day 1 (initial) — Approved → Sent")
            subj, html = email_day1(first_name, company_name, url)
            ok = send_email(email, subj, html)
            if ok:
                tracking["sent_at"] = now_utc().isoformat()
                updated = True
                sb_log_communication(company_id, contact_id, subj, html)
                # Update status to Sent
                if not DRY_RUN:
                    sb_patch("proposals", prop_id, {"status": "Sent", "sent_date": now_utc().date().isoformat()})
                else:
                    print(f"     [DRY RUN] Would set status=Sent, sent_date={now_utc().date().isoformat()}")

        # ── Day 4 — Soft bump ────────────────────────────────────────────────
        elif status == "Sent" and followup1_sent is None and days_since(sent_at) >= 4:
            print(f"     ACTION: Sending Day 4 follow-up (day {days_since(sent_at)} since initial)")
            subj, html = email_day4(first_name, company_name, url)
            ok = send_email(email, subj, html)
            if ok:
                tracking["followup1_sent_at"] = now_utc().isoformat()
                updated = True
                sb_log_communication(company_id, contact_id, subj, html)

        # ── Day 7 — Final close ──────────────────────────────────────────────
        elif status == "Sent" and followup2_sent is None and days_since(sent_at) >= 7:
            print(f"     ACTION: Sending Day 7 close (day {days_since(sent_at)} since initial)")
            subj, html = email_day7(first_name, company_name, url)
            ok = send_email(email, subj, html)
            if ok:
                tracking["followup2_sent_at"] = now_utc().isoformat()
                tracking["nurture_active"]    = True  # Move to nurture after Day 7
                updated = True
                sb_log_communication(company_id, contact_id, subj, html)

        # ── Monthly nurture ──────────────────────────────────────────────────
        elif status == "Sent" and nurture_active:
            days_since_nurture = days_since(nurture_last) if nurture_last else 999
            if days_since_nurture >= 30:
                print(f"     ACTION: Sending monthly nurture (day {days_since_nurture} since last nurture)")
                subj, html = email_nurture(first_name, company_name, url)
                ok = send_email(email, subj, html)
                if ok:
                    tracking["nurture_last_sent_at"] = now_utc().isoformat()
                    updated = True
                    sb_log_communication(company_id, contact_id, subj, html)
            else:
                print(f"     SKIP: nurture active, {days_since_nurture} days since last send (need 30)")

        elif status == "Approved":
            print(f"     INFO: Approved but sent_at already set — possible duplicate. Skipping.")
        else:
            print(f"     SKIP: sequence complete, nurture not active yet")

        # Persist updated tracking to notes
        if updated and not DRY_RUN:
            new_notes = json.dumps(tracking)
            status = sb_patch("proposals", prop_id, {"notes": new_notes})
            print(f"     Supabase updated (HTTP {status})")
        elif updated and DRY_RUN:
            print(f"     [DRY RUN] Would update notes: {json.dumps(tracking)}")

        print()

    print("Done.\n")


if __name__ == "__main__":
    run()
