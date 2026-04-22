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
        "from": f"Rico at White Haus Media <{FROM_EMAIL}>",
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


# ─── Email templates ───────────────────────────────────────────────────────────
def email_day1(first_name, company_name, proposal_url):
    subject = f"Your proposal from White Haus Media — {company_name}"
    html = f"""
<div style="font-family:'Helvetica Neue',Arial,sans-serif;max-width:600px;margin:0 auto;color:#242528;line-height:1.7">
  <div style="border-top:3px solid #102A43;padding:40px 0 0">
    <p style="font-size:14px;color:#6889A6;letter-spacing:.08em;text-transform:uppercase;margin:0 0 28px">White Haus Media</p>
    <p style="font-size:16px;margin:0 0 20px">Hey {first_name},</p>
    <p style="font-size:16px;margin:0 0 20px">We put together a custom proposal for {company_name}. It covers what we found on your current site, what we'd build instead, and what that could mean for your business.</p>
    <p style="font-size:16px;margin:0 0 32px">Take a look when you get a minute:</p>
    <div style="margin:0 0 32px">
      <a href="{proposal_url}" style="display:inline-block;background:#102A43;color:#F8F7F3;text-decoration:none;padding:14px 28px;font-size:14px;font-weight:600;letter-spacing:.04em;border-radius:6px">View Your Proposal</a>
    </div>
    <p style="font-size:16px;margin:0 0 20px">If anything in there sparks a question or you want to talk through the scope, you can grab 20 minutes on my calendar: <a href="{CALENDLY_URL}" style="color:#102A43;font-weight:600">{CALENDLY_URL}</a></p>
    <p style="font-size:16px;margin:0 0 8px">Rico</p>
    <p style="font-size:14px;color:#6889A6;margin:0">White Haus Media · Wake Forest, NC</p>
    <hr style="border:none;border-top:1px solid #EEE9E1;margin:32px 0">
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
    <p style="font-size:16px;margin:0 0 32px">If you have any questions about what's included or want to talk through the project, just reply here or grab time on my calendar:</p>
    <div style="margin:0 0 32px">
      <a href="{CALENDLY_URL}" style="display:inline-block;background:#102A43;color:#F8F7F3;text-decoration:none;padding:14px 28px;font-size:14px;font-weight:600;letter-spacing:.04em;border-radius:6px">Schedule a Call</a>
      &nbsp;
      <a href="{proposal_url}" style="display:inline-block;color:#102A43;text-decoration:none;padding:14px 20px;font-size:14px;font-weight:600;letter-spacing:.04em;border:1px solid #102A43;border-radius:6px">View Proposal</a>
    </div>
    <p style="font-size:16px;margin:0 0 8px">Rico</p>
    <p style="font-size:14px;color:#6889A6;margin:0">White Haus Media · Wake Forest, NC</p>
    <hr style="border:none;border-top:1px solid #EEE9E1;margin:32px 0">
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
    <p style="font-size:16px;margin:0 0 20px">If this isn't a priority right now, no problem — I'll follow up in a couple months. If you're ready to move forward or want to talk through any of it, the fastest way is to grab 20 minutes:</p>
    <div style="margin:0 0 32px">
      <a href="{CALENDLY_URL}" style="display:inline-block;background:#102A43;color:#F8F7F3;text-decoration:none;padding:14px 28px;font-size:14px;font-weight:600;letter-spacing:.04em;border-radius:6px">Book a 20-Minute Call</a>
    </div>
    <p style="font-size:16px;margin:0 0 8px">Rico</p>
    <p style="font-size:14px;color:#6889A6;margin:0">White Haus Media · Wake Forest, NC</p>
    <hr style="border:none;border-top:1px solid #EEE9E1;margin:32px 0">
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
    <p style="font-size:16px;margin:0 0 20px">We've been doing a lot of work with businesses in the Triangle recently — happy to share what's been working if it's helpful. Or if you're ready to revisit the project, the proposal is still live:</p>
    <div style="margin:0 0 32px">
      <a href="{proposal_url}" style="display:inline-block;background:#102A43;color:#F8F7F3;text-decoration:none;padding:14px 28px;font-size:14px;font-weight:600;letter-spacing:.04em;border-radius:6px">View Your Proposal</a>
    </div>
    <p style="font-size:16px;margin:0 0 8px">Rico</p>
    <p style="font-size:14px;color:#6889A6;margin:0">White Haus Media · Wake Forest, NC</p>
    <hr style="border:none;border-top:1px solid #EEE9E1;margin:32px 0">
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
