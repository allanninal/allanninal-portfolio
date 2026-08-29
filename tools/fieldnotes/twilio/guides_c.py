#!/usr/bin/env python3
"""/twilio/ field notes, batch C — the registration paperwork.

Four notes about the A2P and toll-free registration state machines, where the
failure is never in your code and never in your logs: it is a status field and
an errors array on a resource nobody polls. Every check here is a GET with an
API Key that has read access, and every repair is printed rather than run,
because these scripts hold a credential to an account that can send messages and
spend money.
"""

CITE_USA2P = ("UsAppToPerson resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/usapptoperson-resource")
CITE_BRAND = ("BrandRegistration resource — Twilio Docs",
              "https://www.twilio.com/docs/messaging/api/brand-registration-resource")
CITE_TF = ("Tollfree Verification resource — Twilio Docs",
           "https://www.twilio.com/docs/messaging/api/tollfree-verification-resource")
CITE_30034 = ("Error 30034: message from an unregistered number — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30034")
CITE_30032 = ("Error 30032: toll-free number has not been verified — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30032")
CITE_30909 = ("Error 30909: campaign message flow is incomplete — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/30909")
CITE_FIX_CAMPAIGNS = (
    "Troubleshooting and rectifying A2P campaigns — Twilio Docs",
    "https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/troubleshooting-a2p-brands/troubleshooting-and-rectifying-a2p-campaigns")
CITE_FIX_BRANDS = (
    "Troubleshooting and rectifying Standard and LVS brands — Twilio Docs",
    "https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/troubleshooting-a2p-brands/troubleshooting-and-rectifying-a2p-standardlvs-brands")
CITE_SERVICE = ("Messaging Service resource — Twilio Docs",
                "https://www.twilio.com/docs/messaging/api/service-resource")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")

GUIDES = [

{
"slug": "a2p-campaign-vetting-failed",
"title": "A2P campaign is FAILED and errors[] names the rejected field",
"description": "campaign_status is FAILED and every US send returns 30034. The errors[] array names the exact attribute that was rejected, and nobody reads it.",
"h1": "a2p campaign is FAILED and errors[] names the rejected field",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio campaign_status failed", "a2p campaign rejected",
             "twilio 30886 30893", "us_app_to_person errors",
             "10dlc campaign vetting failed"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The campaign was rejected in March. Somebody resubmitted the same description in April and it was rejected again. The reason was in the response both times: <code>errors[]</code> on the campaign carries a code, a sentence of English and the exact <code>fields</code> that triggered it &mdash; and the dashboard the team built reads <code>campaign_status</code> and stops there.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/Compliance/Usa2p</code>. When <code>campaign_status</code> is <code>FAILED</code>, the answer is in <code>errors[]</code>: each entry carries the code, a <code>description</code>, a docs <code>url</code> and <code>fields</code>, which names the campaign attributes that caused it.</p>
<p>Sort the codes before you resubmit anything. <code>30886</code>, <code>30890</code>, <code>30892</code>, <code>30893</code>, <code>30895</code> and <code>30909</code> are edits to the campaign copy. <code>30898</code> is a brand problem wearing a campaign error. <code>30883</code>, <code>30884</code> and <code>30885</code> are content rejections that no edit will clear.</p>""",
"problem": """<p>A failed campaign produces exactly one visible symptom: US messages come back <code>30034</code>, the same code you get from a service that was never registered at all. So the failure looks like an absence, and the instinct is to register again. The campaign is resubmitted with the same description, the same message samples and the same undeclared attribute, and three weeks later it fails for the same reason.</p>
<p>The information needed to avoid that round trip was in the API from the moment the vetting finished. <code>errors[]</code> is not a summary or a status string; it is a list of objects, each naming a code and the campaign attribute that produced it. A team that reads only <code>campaign_status</code> has thrown away the entire diagnosis and is left guessing which paragraph the reviewer disliked.</p>""",
"why": """<p><strong>The status field looks like the whole answer.</strong> <code>campaign_status</code> is a single word, it appears in the console in red, and it reads like a verdict rather than a pointer. Nothing about <code>FAILED</code> suggests there is a structured explanation sitting next to it in the same response.</p>
<p><strong>The old fields taught people the wrong habit.</strong> Brands used to expose <code>failure_reason</code> and <code>brand_feedback</code>, both prose, both now deprecated. Code written against those reads a string, finds nothing useful, and concludes the API does not explain rejections. <code>errors[]</code> is the replacement and it is considerably better than what it replaced.</p>
<p><strong>Not every code is fixable, and the report has to say which.</strong> <code>30893</code> means the samples do not match the use case, which is an afternoon of editing. <code>30884</code> means the content was judged a spam risk, which no amount of rewriting the description will clear. Treating them as one bucket wastes weeks on the second kind.</p>
<p><strong>Resubmitting is not free.</strong> The vetting fee is charged once per campaign, so editing in place is cheaper than delete-and-recreate &mdash; but only if you know which fields to edit. Without <code>errors[]</code> the safe-feeling move is to recreate the campaign, which pays again for the same rejection.</p>""",
"steps": [
 {"h": "Fetch the campaign, not just the service flag",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/Compliance/Usa2p</code> returns the campaign objects under <code>compliance</code>. The Messaging Service's <code>us_app_to_person_registered</code> boolean tells you a campaign exists; only this resource tells you what state it is in and why.</p>"""},
 {"h": "Read every entry in errors[], not the first one",
  "body": """<p>A campaign can fail on several codes at once &mdash; a vague description and an undeclared link shortener are two findings, not one. Each object has <code>error_code</code>, <code>description</code>, <code>fields</code> and <code>url</code>. Collect all of them before deciding what to change.</p>"""},
 {"h": "Split the codes by what actually clears them",
  "body": """<p><code>30886</code> is <code>description</code>. <code>30890</code> is the help message. <code>30892</code> and <code>30893</code> are the samples. <code>30895</code> is the <code>direct_lending</code> attribute. <code>30909</code> is the message flow. <code>30898</code> is the EIN, which lives on the brand. <code>30883</code>, <code>30884</code> and <code>30885</code> are content rejections and are not remediable by editing.</p>"""},
 {"h": "Treat FAILED with an empty errors[] as its own finding",
  "body": """<p>It happens, and it is worth reporting separately rather than silently rendering as "failed, reason unknown". Re-fetch the resource before you act: there is nothing else in the API that explains the rejection, so a resubmission at that point is a guess.</p>"""},
 {"h": "Edit in place, then poll until VERIFIED",
  "body": """<p><code>POST /v1/Services/{ServiceSid}/Compliance/Usa2p/{QESid}</code> with the corrected <code>Description</code>, <code>MessageFlow</code>, <code>MessageSamples</code>, <code>HelpMessage</code>, <code>HasEmbeddedLinks</code> or <code>DirectLending</code>. Then keep reading <code>campaign_status</code>: the edit puts the campaign back into vetting, it does not approve it.</p>"""},
],
"verify": """<p>Re-run the script. Every campaign should report <code>verified</code>, and no service should be sitting on a <code>FAILED</code> campaign.</p>
<pre><code class="language-bash">python3 twilio_a2p_campaign_vetting_audit.py
# 4 service(s), 0 with a failed campaign</code></pre>""",
"code_intro": "One paginated GET for the services and one per service for its campaign &mdash; reads only, with an API Key that has read access and nothing more. The classifier is pure and takes the campaign object alone, because the whole value of this note is the code table: which <code>errors[]</code> entries are an edit, which are a brand problem and which are the end of the road.",
"py_file": "twilio_a2p_campaign_vetting_audit.py",
"py": '''"""Report A2P 10DLC campaigns that failed vetting, and name the field that did it.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_a2p_campaign_vetting_audit")

MSG = "https://messaging.twilio.com/v1"

# The 308xx/309xx codes that turn up in errors[] on a FAILED campaign, split by
# what actually clears them. A report that only says FAILED sends people round
# the same three week loop; the split is the entire point of this script.
EDITABLE = {
    "30886": ("description", "the use case description is too vague"),
    "30890": ("help_message", "the help message names no brand or support contact"),
    "30892": ("message_samples", "a public URL shortener appears in the samples"),
    "30893": ("message_samples", "the samples do not match the stated use case"),
    "30895": ("direct_lending", "direct lending is not declared"),
    "30909": ("message_flow", "the message flow or call to action is incomplete"),
}
UPSTREAM = {
    "30898": ("brand", "the EIN is already attached to too many brands"),
}
STRUCTURAL = {
    "30883": ("content", "content violation"),
    "30884": ("content", "spam risk"),
    "30885": ("content", "fraud or phishing risk"),
}


def error_code(err):
    """Read the code off one errors[] entry, as a string.

    The campaign resource spells the key error_code and the brand resource
    spells it code. Reading both is cheaper than being wrong on one of them, and
    normalising to a string means the tables above can be keyed on one type.
    """
    for k in ("error_code", "code"):
        v = err.get(k)
        if v not in (None, ""):
            return str(v)
    return ""


def classify_error(err):
    """Sort one errors[] entry by what will clear it. Pure.

    Returns (bucket, field, why); bucket is editable, upstream, structural or
    unknown.
    """
    code = error_code(err)
    for bucket, table in (("editable", EDITABLE), ("upstream", UPSTREAM),
                          ("structural", STRUCTURAL)):
        if code in table:
            field, why = table[code]
            return (bucket, field, "%s: %s" % (code, why))
    return ("unknown", "",
            "%s: %s" % (code or "no code",
                        err.get("description") or "no description"))


def named_fields(errors):
    """Every campaign attribute the errors point at, in order, without repeats.

    Prefers what the API said in `fields` and falls back to the code table, so a
    code this script has never seen still reports whatever the reviewer named.
    """
    out = []
    for err in errors:
        fields = [str(f).strip() for f in (err.get("fields") or []) if str(f).strip()]
        if not fields:
            _bucket, field, _why = classify_error(err)
            fields = [field] if field else []
        for f in fields:
            if f not in out:
                out.append(f)
    return out


def verdict(campaign):
    """Classify one UsAppToPerson campaign. Pure, so the code table can be
    tested without a network.

    Returns (state, detail).
    """
    if not campaign:
        return ("no-campaign",
                "no A2P campaign on this Messaging Service at all.")

    status = str(campaign.get("campaign_status") or "").upper()
    errors = campaign.get("errors") or []
    buckets = [classify_error(e) for e in errors]
    reasons = "; ".join(w for _b, _f, w in buckets)
    fields = ", ".join(named_fields(errors)) or "nothing named"

    if status == "FAILED":
        if not errors:
            return ("failed-unexplained",
                    "campaign_status is FAILED and errors[] is empty. Nothing "
                    "else in the API explains the rejection, so a resubmission "
                    "now is a guess.")
        if any(b == "structural" for b, _f, _w in buckets):
            return ("failed-structural",
                    "FAILED on a content rejection that editing will not clear "
                    "(%s)." % reasons)
        if any(b == "upstream" for b, _f, _w in buckets):
            return ("failed-at-the-brand",
                    "FAILED on a brand level code (%s). Editing the campaign "
                    "changes nothing until the brand is fixed." % reasons)
        return ("failed-editable",
                "FAILED on %s. Edit %s and resubmit the same campaign."
                % (reasons, fields))

    if status == "SUSPENDED":
        return ("suspended",
                "campaign_status is SUSPENDED, which sends exactly like FAILED. "
                "Check the brand above it before touching the campaign.")

    if status in ("PENDING", "IN_PROGRESS"):
        if errors:
            return ("pending-with-errors",
                    "still %s, but errors[] is already populated (%s): the "
                    "vetting result has arrived and the status has not caught "
                    "up." % (status, reasons))
        return ("pending",
                "still %s: not live, not failed, nothing to edit yet." % status)

    if status == "VERIFIED":
        return ("verified",
                "campaign %s is VERIFIED" % (campaign.get("sid") or "?"))

    return ("unknown-status",
            "campaign_status is %s, which this script does not recognise."
            % (status or "unset"))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_v1(session, url, key, limit=1000):
    """Page a messaging.twilio.com list. meta.next_page_url is absolute."""
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-services", type=int, default=200)
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    session = requests.Session()
    session.auth = (key, secret)

    services = list_v1(session, MSG + "/Services", "services", args.max_services)
    if not services:
        log.info("no Messaging Services on this account")
        return 0

    bad = 0
    for svc in services:
        campaigns = list_v1(session,
                            "%s/Services/%s/Compliance/Usa2p" % (MSG, svc["sid"]),
                            "compliance")
        campaign = campaigns[0] if campaigns else None
        state, detail = verdict(campaign)
        name = svc.get("friendly_name") or svc["sid"]
        line = "%-19s %s  %s" % (state, name, detail)
        if state in ("verified", "pending"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        for err in (campaign or {}).get("errors") or []:
            if err.get("url"):
                log.warning("  %s -> %s", error_code(err), err["url"])
        if state == "failed-editable":
            log.warning("  repair: POST %s/Services/%s/Compliance/Usa2p/%s with the "
                        "corrected Description, MessageFlow, MessageSamples or "
                        "HelpMessage", MSG, svc["sid"], campaign.get("sid", "QE..."))
        elif state == "failed-at-the-brand":
            log.warning("  repair: fix the brand first; the campaign edit will not "
                        "take while the brand carries the same error")
        elif state == "failed-structural":
            log.warning("  repair: none by API. The content itself was rejected, so "
                        "the use case has to change before resubmitting")

    log.info("%d service(s), %d with a failed campaign", len(services), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-a2p-campaign-vetting-audit.mjs",
"js": '''/**
 * Report A2P 10DLC campaigns that failed vetting, and name the field that did it.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MSG = 'https://messaging.twilio.com/v1';

// The 308xx/309xx codes that turn up in errors[] on a FAILED campaign, split by
// what actually clears them.
const EDITABLE = {
  30886: ['description', 'the use case description is too vague'],
  30890: ['help_message', 'the help message names no brand or support contact'],
  30892: ['message_samples', 'a public URL shortener appears in the samples'],
  30893: ['message_samples', 'the samples do not match the stated use case'],
  30895: ['direct_lending', 'direct lending is not declared'],
  30909: ['message_flow', 'the message flow or call to action is incomplete'],
};
const UPSTREAM = {
  30898: ['brand', 'the EIN is already attached to too many brands'],
};
const STRUCTURAL = {
  30883: ['content', 'content violation'],
  30884: ['content', 'spam risk'],
  30885: ['content', 'fraud or phishing risk'],
};

/**
 * Read the code off one errors[] entry, as a string. The campaign resource
 * spells the key error_code and the brand resource spells it code.
 */
export function errorCode(err) {
  for (const k of ['error_code', 'code']) {
    const v = err[k];
    if (v !== undefined && v !== null && v !== '') return String(v);
  }
  return '';
}

/**
 * Sort one errors[] entry by what will clear it. Pure. Returns
 * [bucket, field, why] with bucket editable, upstream, structural or unknown.
 */
export function classifyError(err) {
  const code = errorCode(err);
  for (const [bucket, table] of [['editable', EDITABLE], ['upstream', UPSTREAM],
                                 ['structural', STRUCTURAL]]) {
    if (Object.prototype.hasOwnProperty.call(table, code)) {
      const [field, why] = table[code];
      return [bucket, field, `${code}: ${why}`];
    }
  }
  return ['unknown', '',
          `${code || 'no code'}: ${err.description ?? 'no description'}`];
}

/** Every campaign attribute the errors point at, in order, without repeats. */
export function namedFields(errors) {
  const out = [];
  for (const err of errors) {
    let fields = (err.fields ?? []).map((f) => String(f).trim()).filter(Boolean);
    if (fields.length === 0) {
      const [, field] = classifyError(err);
      fields = field ? [field] : [];
    }
    for (const f of fields) if (!out.includes(f)) out.push(f);
  }
  return out;
}

/**
 * Classify one UsAppToPerson campaign. Pure, so the code table can be tested
 * without a network. Returns [state, detail].
 */
export function verdict(campaign) {
  if (!campaign) {
    return ['no-campaign', 'no A2P campaign on this Messaging Service at all.'];
  }

  const status = String(campaign.campaign_status ?? '').toUpperCase();
  const errors = campaign.errors ?? [];
  const buckets = errors.map(classifyError);
  const reasons = buckets.map(([, , why]) => why).join('; ');
  const fields = namedFields(errors).join(', ') || 'nothing named';

  if (status === 'FAILED') {
    if (errors.length === 0) {
      return ['failed-unexplained',
        'campaign_status is FAILED and errors[] is empty. Nothing else in the ' +
        'API explains the rejection, so a resubmission now is a guess.'];
    }
    if (buckets.some(([b]) => b === 'structural')) {
      return ['failed-structural',
        `FAILED on a content rejection that editing will not clear (${reasons}).`];
    }
    if (buckets.some(([b]) => b === 'upstream')) {
      return ['failed-at-the-brand',
        `FAILED on a brand level code (${reasons}). Editing the campaign ` +
        'changes nothing until the brand is fixed.'];
    }
    return ['failed-editable',
      `FAILED on ${reasons}. Edit ${fields} and resubmit the same campaign.`];
  }

  if (status === 'SUSPENDED') {
    return ['suspended',
      'campaign_status is SUSPENDED, which sends exactly like FAILED. Check ' +
      'the brand above it before touching the campaign.'];
  }

  if (status === 'PENDING' || status === 'IN_PROGRESS') {
    if (errors.length) {
      return ['pending-with-errors',
        `still ${status}, but errors[] is already populated (${reasons}): the ` +
        'vetting result has arrived and the status has not caught up.'];
    }
    return ['pending', `still ${status}: not live, not failed, nothing to edit yet.`];
  }

  if (status === 'VERIFIED') {
    return ['verified', `campaign ${campaign.sid ?? '?'} is VERIFIED`];
  }

  return ['unknown-status',
    `campaign_status is ${status || 'unset'}, which this script does not recognise.`];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

async function get(auth, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  const res = await fetch(u, { headers: { Authorization: auth } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Twilio: check TWILIO_ACCOUNT_SID and ` +
                    'that the API key belongs to that account with read access');
  }
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return res.json();
}

export async function listV1(auth, url, key, limit = 1000) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const page = await get(auth, next, { PageSize: 50 });
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
  }
  return out.slice(0, limit);
}

async function main() {
  const account = process.env.TWILIO_ACCOUNT_SID;
  const key = process.env.TWILIO_API_KEY;
  const secret = process.env.TWILIO_API_SECRET;
  if (!account || !key || !secret) {
    console.error('set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET ' +
                  '(an API Key with read access, not the auth token)');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);

  const services = await listV1(auth, `${MSG}/Services`, 'services');
  if (services.length === 0) {
    console.log('no Messaging Services on this account');
    return;
  }

  let bad = 0;
  for (const svc of services) {
    const campaigns = await listV1(auth, `${MSG}/Services/${svc.sid}/Compliance/Usa2p`,
                                   'compliance');
    const campaign = campaigns[0] ?? null;
    const [state, detail] = verdict(campaign);
    const name = svc.friendly_name ?? svc.sid;
    const line = `${state.padEnd(19)} ${name}  ${detail}`;
    if (state === 'verified' || state === 'pending') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    for (const err of campaign?.errors ?? []) {
      if (err.url) console.warn(`  ${errorCode(err)} -> ${err.url}`);
    }
    if (state === 'failed-editable') {
      console.warn(`  repair: POST ${MSG}/Services/${svc.sid}/Compliance/Usa2p/` +
                   `${campaign.sid ?? 'QE...'} with the corrected Description, ` +
                   'MessageFlow, MessageSamples or HelpMessage');
    } else if (state === 'failed-at-the-brand') {
      console.warn('  repair: fix the brand first; the campaign edit will not take ' +
                   'while the brand carries the same error');
    } else if (state === 'failed-structural') {
      console.warn('  repair: none by API. The content itself was rejected, so the ' +
                   'use case has to change before resubmitting');
    }
  }

  console.log(`${services.length} service(s), ${bad} with a failed campaign`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases that matter are the ones where <code>FAILED</code> means three different things: an edit, a brand problem and a dead end. The other one worth pinning is an <code>errors[]</code> entry that spells the key <code>code</code> rather than <code>error_code</code> &mdash; the two resources differ, and a classifier that reads only one of them silently reports every rejection as unknown.",
"test_py_file": "test_twilio_a2p_campaign_vetting_audit.py",
"test_py": '''from twilio_a2p_campaign_vetting_audit import (classify_error, named_fields,
                                                  verdict)

FAILED = {"sid": "QE0123456789", "campaign_status": "FAILED"}


def test_failed_on_an_editable_code_names_the_field_to_change():
    state, detail = verdict(dict(FAILED, errors=[{"error_code": 30893,
                                                  "fields": ["message_samples"]}]))
    assert state == "failed-editable"
    assert "message_samples" in detail


def test_content_rejection_is_not_an_edit():
    # 30884 is a spam risk judgement. Rewriting the description does not clear it,
    # and reporting it in the same bucket costs weeks.
    state, detail = verdict(dict(FAILED, errors=[{"error_code": "30884"}]))
    assert state == "failed-structural"
    assert "will not clear" in detail


def test_ein_code_points_at_the_brand_not_the_campaign():
    state, _ = verdict(dict(FAILED, errors=[{"error_code": 30898}]))
    assert state == "failed-at-the-brand"


def test_failed_with_an_empty_errors_array_is_its_own_state():
    state, detail = verdict(dict(FAILED, errors=[]))
    assert state == "failed-unexplained"
    assert "guess" in detail


def test_an_error_object_spelled_code_is_still_read():
    # The campaign resource says error_code and the brand resource says code.
    bucket, field, _why = classify_error({"code": "30886"})
    assert (bucket, field) == ("editable", "description")


def test_fields_from_the_api_win_over_the_table():
    assert named_fields([{"error_code": 30886, "fields": ["message_flow"]}]) == \\
        ["message_flow"]


def test_in_progress_with_errors_is_not_reported_as_waiting():
    state, _ = verdict({"campaign_status": "IN_PROGRESS",
                        "errors": [{"error_code": 30909}]})
    assert state == "pending-with-errors"


def test_verified_campaign_is_clean():
    state, detail = verdict({"campaign_status": "VERIFIED", "sid": "QE0123456789"})
    assert state == "verified"
    assert "QE0123456789" in detail
''',
"test_js_file": "twilio-a2p-campaign-vetting-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { classifyError, namedFields, verdict }
  from './twilio-a2p-campaign-vetting-audit.mjs';

const FAILED = { sid: 'QE0123456789', campaign_status: 'FAILED' };

test('failed on an editable code names the field to change', () => {
  const [state, detail] = verdict({ ...FAILED,
    errors: [{ error_code: 30893, fields: ['message_samples'] }] });
  assert.equal(state, 'failed-editable');
  assert.match(detail, /message_samples/);
});

test('content rejection is not an edit', () => {
  const [state, detail] = verdict({ ...FAILED, errors: [{ error_code: '30884' }] });
  assert.equal(state, 'failed-structural');
  assert.match(detail, /will not clear/);
});

test('ein code points at the brand, not the campaign', () => {
  assert.equal(verdict({ ...FAILED, errors: [{ error_code: 30898 }] })[0],
               'failed-at-the-brand');
});

test('failed with an empty errors array is its own state', () => {
  const [state, detail] = verdict({ ...FAILED, errors: [] });
  assert.equal(state, 'failed-unexplained');
  assert.match(detail, /guess/);
});

test('an error object spelled code is still read', () => {
  const [bucket, field] = classifyError({ code: '30886' });
  assert.deepEqual([bucket, field], ['editable', 'description']);
});

test('fields from the api win over the table', () => {
  assert.deepEqual(namedFields([{ error_code: 30886, fields: ['message_flow'] }]),
                   ['message_flow']);
});

test('in progress with errors is not reported as waiting', () => {
  assert.equal(
    verdict({ campaign_status: 'IN_PROGRESS', errors: [{ error_code: 30909 }] })[0],
    'pending-with-errors');
});

test('verified campaign is clean', () => {
  const [state, detail] = verdict({ campaign_status: 'VERIFIED', sid: 'QE0123456789' });
  assert.equal(state, 'verified');
  assert.match(detail, /QE0123456789/);
});
''',
"faq": [
 ("Where exactly is the rejection reason?",
  "In errors[] on the campaign, returned by GET /v1/Services/{ServiceSid}/Compliance/Usa2p. Each entry has an error_code, a description in English, a fields array naming the campaign attributes that triggered it, and a url to the docs page for that code. campaign_status only tells you that something was rejected."),
 ("Why do sends fail with 30034 rather than a campaign-specific code?",
  "Because from the carrier's point of view an unapproved campaign and no campaign are the same thing: the sending number is not registered. That is why the send-side error is useless for diagnosis and the campaign resource is the only place the reason exists."),
 ("Which codes can I actually fix by editing?",
  "30886, 30890, 30892, 30893, 30895 and 30909 are all edits to the campaign copy or its declared attributes. 30898 is the EIN being attached to too many brands, which is fixed on the brand. 30883, 30884 and 30885 are content rejections, and no rewrite of the description clears those."),
 ("Should I edit the campaign or delete it and start again?",
  "Edit it. The vetting fee is charged once per campaign, so recreating pays a second time for the same review. Delete-and-recreate is only right when the use case itself was wrong, because the use case is not editable in place."),
 ("Does the script resubmit for me?",
  "No. It prints the POST with the campaign SID and the fields to change. A script that rewrites a compliance registration on a schedule can resubmit the same rejected copy and burn the review queue, and it holds a credential to an account that can send messages."),
],
"related": [
 ("/twilio/a2p-brand-registration-failed/", "An A2P brand stuck at FAILED blocks every campaign"),
 ("/twilio/a2p-campaign-stuck-in-progress/", "A campaign parked at IN_PROGRESS is not live"),
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign"),
],
"citations": [CITE_USA2P, CITE_FIX_CAMPAIGNS, CITE_30909, CITE_30034],
},

{
"slug": "a2p-brand-registration-failed",
"title": "An A2P brand stuck at FAILED blocks every campaign under it",
"description": "BrandRegistration.status is FAILED, so no campaign can attach and every US send is 30034. The reason is in errors[], not in the deprecated prose fields.",
"h1": "an A2P brand stuck at FAILED blocks every campaign under it",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio brand registration failed", "a2p brand status failed",
             "brandregistration errors", "twilio 30034 brand",
             "10dlc brand not approved"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Campaign creation keeps getting rejected and every US message comes back <code>30034</code>, so the team keeps looking at the campaign. The campaign is not the problem: the brand above it is <code>FAILED</code>, nothing can attach to a failed brand, and the reason it failed has been sitting in <code>errors[]</code> on the brand resource since the day it was reviewed.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations</code> and flag every item where <code>status</code> is <code>FAILED</code>. Then read <code>errors[]</code> on that item: each entry carries a code, a <code>description</code>, the <code>fields</code> it objects to and a docs <code>url</code>.</p>
<p>Do not read <code>failure_reason</code> or <code>brand_feedback</code>. Both are deprecated in favour of <code>errors[]</code>, and code written against them reports "no reason given" on a brand that explained itself perfectly. <code>tcr_id</code> is <code>null</code> until the brand is approved, which is a useful second opinion on the status field.</p>""",
"problem": """<p>A2P has two registration objects and only one of them is visible from where the failure appears. Your sends fail with <code>30034</code>. You look at the Messaging Service, which is fine. You look at the campaign, which cannot be created &mdash; and the error you get from trying to create it talks about the campaign, not about why the brand behind it is unusable. The layer that actually failed is one level up and nothing in the send path names it.</p>
<p>Meanwhile the brand sits at <code>FAILED</code> indefinitely. There is no expiry, no retry, no alert. Everything downstream is blocked: no campaign, therefore no registered numbers, therefore no US 10DLC traffic at all. Teams routinely spend a fortnight on campaign paperwork for a brand that was rejected before any of it could matter.</p>""",
"why": """<p><strong>Failure cascades downward and diagnosis does not.</strong> A failed brand takes the whole account's US messaging with it, but the error surfaces per message as <code>30034</code>, the most generic code in 10DLC. Nothing in that code distinguishes a missing campaign from a rejected brand from a number outside the pool.</p>
<p><strong>The fields most people read are deprecated.</strong> <code>failure_reason</code> and <code>brand_feedback</code> were the old prose explanations. They are superseded by <code>errors[]</code>, and integrations written before the change now read fields that may be empty on a brand that has a perfectly explicit list of objections.</p>
<p><strong>Resubmissions are limited and quiet about it.</strong> Three resubmissions are free; a fourth is rejected with <code>21724</code>. So blind retries are not merely slow, they are finite, and each one spent on a guess is one you do not have when you know the answer.</p>
<p><strong>Nothing polls.</strong> Most integrations wire a status callback at registration time and never read the resource again. A callback that is missed, or a webhook deployed after the brand was submitted, leaves the brand parked at <code>FAILED</code> with nobody looking at it. Reading the list is one GET.</p>""",
"steps": [
 {"h": "List the brands on the account",
  "body": """<p><code>GET https://messaging.twilio.com/v1/a2p/BrandRegistrations</code>. This resource returns its items under <code>data</code> rather than a resource-named key like the rest of messaging v1, which is a small thing that costs an afternoon if you assume otherwise.</p>"""},
 {"h": "Read status, and read tcr_id next to it",
  "body": """<p><code>status</code> moves <code>PENDING</code> to <code>IN_REVIEW</code> to <code>APPROVED</code> or <code>FAILED</code>, with <code>SUSPENDED</code>, <code>DELETION_PENDING</code> and <code>DELETION_FAILED</code> also possible. <code>tcr_id</code> stays <code>null</code> until the registry accepts the brand, so an <code>APPROVED</code> brand with no <code>tcr_id</code> is worth reporting rather than trusting.</p>"""},
 {"h": "Take the reason from errors[], not from the prose fields",
  "body": """<p>Each entry in <code>errors[]</code> names a code, a description, the <code>fields</code> it objects to and a docs URL. <code>30799</code> is the common one: the tax ID does not match the legal name on public record. Report the fields, because those are what somebody has to go and edit.</p>"""},
 {"h": "Say so when only the deprecated fields have anything in them",
  "body": """<p>If <code>errors[]</code> is empty and <code>failure_reason</code> or <code>brand_feedback</code> is populated, the script should print that prose and flag where it came from. It is still the only explanation available, and knowing it arrived from a deprecated field tells you not to build on it.</p>"""},
 {"h": "Fix the Customer Profile, then resubmit once",
  "body": """<p>The brand is assembled from the Trust Hub Customer Profile bundle named in <code>customer_profile_bundle_sid</code>. Correct the business details there so legal name, address and registration identifier match the public record, then <code>POST /v1/a2p/BrandRegistrations/{BrandSid}</code> to resubmit. Do not create a second brand on the same EIN.</p>"""},
],
"verify": """<p>Re-run the script. Every brand should report <code>approved</code> with a <code>tcr_id</code>, and no brand should be sitting at <code>FAILED</code>.</p>
<pre><code class="language-bash">python3 twilio_a2p_brand_audit.py
# 2 brand(s), 0 blocking campaign registration</code></pre>""",
"code_intro": "One paginated GET over the brands, and nothing else &mdash; an API Key with read access is enough. The classifier is pure and takes the brand object, because the interesting decision is where the explanation comes from: <code>errors[]</code> first, the deprecated prose fields only as a labelled fallback, and a distinct state when neither has anything to say.",
"py_file": "twilio_a2p_brand_audit.py",
"py": '''"""Report A2P 10DLC brands that block every campaign underneath them.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_a2p_brand_audit")

MSG = "https://messaging.twilio.com/v1"

DELETING = ("DELETION_PENDING", "DELETION_FAILED")
WAITING = ("PENDING", "IN_REVIEW")

# Superseded by errors[]. Read only as a labelled fallback, because an
# integration written against them reports "no reason given" on a brand that
# explained itself in full.
DEPRECATED = ("failure_reason", "brand_feedback")


def error_code(err):
    """Read the code off one errors[] entry, as a string.

    The brand resource spells the key code and the campaign resource spells it
    error_code. Reading both costs one loop and removes a whole class of silent
    misreport.
    """
    for k in ("error_code", "code"):
        v = err.get(k)
        if v not in (None, ""):
            return str(v)
    return ""


def failure_lines(brand):
    """The reasons a brand gives for its state, and where they came from. Pure.

    Returns (source, lines). source is "errors" when errors[] carried them,
    "deprecated" when only the old prose fields did, and "none" when the brand
    offers no explanation at all.
    """
    lines = []
    for err in brand.get("errors") or []:
        fields = ", ".join(str(f).strip() for f in (err.get("fields") or [])
                           if str(f).strip())
        text = "%s: %s" % (error_code(err) or "no code",
                           err.get("description") or "no description")
        lines.append("%s (%s)" % (text, fields) if fields else text)
    if lines:
        return ("errors", lines)

    for key in DEPRECATED:
        value = str(brand.get(key) or "").strip()
        if value:
            lines.append("%s: %s" % (key, value))
    if lines:
        return ("deprecated", lines)

    return ("none", [])


def verdict(brand):
    """Classify one BrandRegistration. Pure, so the states can be tested without
    a network.

    Returns (state, detail).
    """
    status = str(brand.get("status") or "").upper()
    tcr = str(brand.get("tcr_id") or "").strip()
    source, lines = failure_lines(brand)
    reasons = "; ".join(lines)

    if status == "FAILED":
        if source == "errors":
            return ("failed",
                    "brand is FAILED: %s. No campaign can attach while it stays "
                    "here, so every US send is 30034." % reasons)
        if source == "deprecated":
            return ("failed-deprecated-reason",
                    "brand is FAILED and errors[] is empty; the only text "
                    "available is from a deprecated field (%s)." % reasons)
        return ("failed-unexplained",
                "brand is FAILED with an empty errors[] and no legacy text. "
                "Re-fetch before resubmitting: there are only three free "
                "resubmissions and a fourth returns 21724.")

    if status == "SUSPENDED":
        return ("suspended",
                "brand is SUSPENDED, which suspends every campaign under it. "
                "%s" % (reasons or "No reason on the resource; this is a "
                        "support conversation, not an API repair."))

    if status in DELETING:
        return ("deleting",
                "brand is %s: it is on its way out and cannot carry a campaign."
                % status)

    if status in WAITING:
        return ("in-review",
                "brand is %s and tcr_id is %s. Not failed, just not usable yet."
                % (status, tcr or "null"))

    if status == "APPROVED":
        if not tcr:
            return ("approved-no-tcr-id",
                    "status is APPROVED but tcr_id is null, which is what an "
                    "unapproved brand looks like. Report the disagreement "
                    "rather than picking a side.")
        return ("approved", "brand is APPROVED with tcr_id %s" % tcr)

    return ("unknown-status",
            "status is %s, which this script does not recognise."
            % (status or "unset"))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_brands(session, limit=500):
    """Page the brand list.

    This resource returns its items under `data`, not under a resource-named key
    like the rest of messaging v1. meta.next_page_url is absolute.
    """
    url = MSG + "/a2p/BrandRegistrations"
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        out.extend(page.get("data", []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-brands", type=int, default=500)
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    session = requests.Session()
    session.auth = (key, secret)

    brands = list_brands(session, args.max_brands)
    if not brands:
        log.info("no A2P brand registrations on this account")
        return 0

    bad = 0
    for brand in brands:
        state, detail = verdict(brand)
        sid = brand.get("sid", "?")
        line = "%-24s %s  %s" % (state, sid, detail)
        if state in ("approved", "in-review"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        for err in brand.get("errors") or []:
            if err.get("url"):
                log.warning("  %s -> %s", error_code(err), err["url"])
        if state in ("failed", "failed-deprecated-reason", "failed-unexplained"):
            log.warning("  repair: correct the Customer Profile bundle %s in Trust "
                        "Hub, then POST %s/a2p/BrandRegistrations/%s to resubmit",
                        brand.get("customer_profile_bundle_sid", "BU..."), MSG, sid)
        elif state == "suspended":
            log.warning("  repair: none by API. Resolve the suspension with Twilio "
                        "Support; do not move the traffic to a new brand")

    log.info("%d brand(s), %d blocking campaign registration", len(brands), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-a2p-brand-audit.mjs",
"js": '''/**
 * Report A2P 10DLC brands that block every campaign underneath them.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const MSG = 'https://messaging.twilio.com/v1';

const DELETING = ['DELETION_PENDING', 'DELETION_FAILED'];
const WAITING = ['PENDING', 'IN_REVIEW'];

// Superseded by errors[]. Read only as a labelled fallback.
const DEPRECATED = ['failure_reason', 'brand_feedback'];

/**
 * Read the code off one errors[] entry, as a string. The brand resource spells
 * the key code and the campaign resource spells it error_code.
 */
export function errorCode(err) {
  for (const k of ['error_code', 'code']) {
    const v = err[k];
    if (v !== undefined && v !== null && v !== '') return String(v);
  }
  return '';
}

/**
 * The reasons a brand gives for its state, and where they came from. Pure.
 * Returns [source, lines] with source errors, deprecated or none.
 */
export function failureLines(brand) {
  const lines = [];
  for (const err of brand.errors ?? []) {
    const fields = (err.fields ?? []).map((f) => String(f).trim())
      .filter(Boolean).join(', ');
    const text = `${errorCode(err) || 'no code'}: ${err.description ?? 'no description'}`;
    lines.push(fields ? `${text} (${fields})` : text);
  }
  if (lines.length) return ['errors', lines];

  for (const key of DEPRECATED) {
    const value = String(brand[key] ?? '').trim();
    if (value) lines.push(`${key}: ${value}`);
  }
  if (lines.length) return ['deprecated', lines];

  return ['none', []];
}

/**
 * Classify one BrandRegistration. Pure, so the states can be tested without a
 * network. Returns [state, detail].
 */
export function verdict(brand) {
  const status = String(brand.status ?? '').toUpperCase();
  const tcr = String(brand.tcr_id ?? '').trim();
  const [source, lines] = failureLines(brand);
  const reasons = lines.join('; ');

  if (status === 'FAILED') {
    if (source === 'errors') {
      return ['failed',
        `brand is FAILED: ${reasons}. No campaign can attach while it stays ` +
        'here, so every US send is 30034.'];
    }
    if (source === 'deprecated') {
      return ['failed-deprecated-reason',
        'brand is FAILED and errors[] is empty; the only text available is ' +
        `from a deprecated field (${reasons}).`];
    }
    return ['failed-unexplained',
      'brand is FAILED with an empty errors[] and no legacy text. Re-fetch ' +
      'before resubmitting: there are only three free resubmissions and a ' +
      'fourth returns 21724.'];
  }

  if (status === 'SUSPENDED') {
    return ['suspended',
      'brand is SUSPENDED, which suspends every campaign under it. ' +
      (reasons || 'No reason on the resource; this is a support conversation, ' +
       'not an API repair.')];
  }

  if (DELETING.includes(status)) {
    return ['deleting',
      `brand is ${status}: it is on its way out and cannot carry a campaign.`];
  }

  if (WAITING.includes(status)) {
    return ['in-review',
      `brand is ${status} and tcr_id is ${tcr || 'null'}. Not failed, just not ` +
      'usable yet.'];
  }

  if (status === 'APPROVED') {
    if (!tcr) {
      return ['approved-no-tcr-id',
        'status is APPROVED but tcr_id is null, which is what an unapproved ' +
        'brand looks like. Report the disagreement rather than picking a side.'];
    }
    return ['approved', `brand is APPROVED with tcr_id ${tcr}`];
  }

  return ['unknown-status',
    `status is ${status || 'unset'}, which this script does not recognise.`];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

async function get(auth, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  const res = await fetch(u, { headers: { Authorization: auth } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Twilio: check TWILIO_ACCOUNT_SID and ` +
                    'that the API key belongs to that account with read access');
  }
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return res.json();
}

/**
 * Page the brand list. This resource returns its items under `data`, not under
 * a resource-named key like the rest of messaging v1.
 */
export async function listBrands(auth, limit = 500) {
  const out = [];
  let next = `${MSG}/a2p/BrandRegistrations`;
  while (next && out.length < limit) {
    const page = await get(auth, next, { PageSize: 50 });
    out.push(...(page.data ?? []));
    next = page.meta?.next_page_url ?? null;
  }
  return out.slice(0, limit);
}

async function main() {
  const account = process.env.TWILIO_ACCOUNT_SID;
  const key = process.env.TWILIO_API_KEY;
  const secret = process.env.TWILIO_API_SECRET;
  if (!account || !key || !secret) {
    console.error('set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET ' +
                  '(an API Key with read access, not the auth token)');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);

  const brands = await listBrands(auth);
  if (brands.length === 0) {
    console.log('no A2P brand registrations on this account');
    return;
  }

  let bad = 0;
  for (const brand of brands) {
    const [state, detail] = verdict(brand);
    const sid = brand.sid ?? '?';
    const line = `${state.padEnd(24)} ${sid}  ${detail}`;
    if (state === 'approved' || state === 'in-review') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    for (const err of brand.errors ?? []) {
      if (err.url) console.warn(`  ${errorCode(err)} -> ${err.url}`);
    }
    if (state.startsWith('failed')) {
      console.warn(`  repair: correct the Customer Profile bundle ` +
                   `${brand.customer_profile_bundle_sid ?? 'BU...'} in Trust Hub, ` +
                   `then POST ${MSG}/a2p/BrandRegistrations/${sid} to resubmit`);
    } else if (state === 'suspended') {
      console.warn('  repair: none by API. Resolve the suspension with Twilio ' +
                   'Support; do not move the traffic to a new brand');
    }
  }

  console.log(`${brands.length} brand(s), ${bad} blocking campaign registration`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three cases carry this one. A <code>FAILED</code> brand that explains itself in <code>errors[]</code>, a <code>FAILED</code> brand where only the deprecated prose field has anything in it, and an <code>APPROVED</code> brand with a <code>null</code> <code>tcr_id</code> &mdash; the last because a status field and the registry disagreeing is worth reporting rather than resolving in favour of whichever you happened to read.",
"test_py_file": "test_twilio_a2p_brand_audit.py",
"test_py": '''from twilio_a2p_brand_audit import failure_lines, verdict


def test_failed_brand_reports_the_code_and_the_fields():
    state, detail = verdict({
        "status": "FAILED",
        "errors": [{"code": 30799, "description": "Unable to verify registration "
                    "details", "fields": ["business_registration_identifier"]}],
    })
    assert state == "failed"
    assert "30799" in detail
    assert "business_registration_identifier" in detail


def test_deprecated_prose_is_used_but_labelled():
    # failure_reason and brand_feedback are superseded by errors[]. If they are
    # all that is populated, say so rather than presenting them as the answer.
    state, detail = verdict({"status": "FAILED", "errors": [],
                             "failure_reason": "EIN does not match"})
    assert state == "failed-deprecated-reason"
    assert "deprecated" in detail


def test_errors_win_over_the_deprecated_fields():
    source, lines = failure_lines({"errors": [{"code": "30799"}],
                                   "brand_feedback": "old text"})
    assert source == "errors"
    assert len(lines) == 1


def test_failed_with_nothing_at_all_mentions_the_resubmission_limit():
    state, detail = verdict({"status": "FAILED"})
    assert state == "failed-unexplained"
    assert "21724" in detail


def test_approved_without_a_tcr_id_is_a_disagreement():
    state, _ = verdict({"status": "APPROVED", "tcr_id": None})
    assert state == "approved-no-tcr-id"


def test_approved_with_a_tcr_id_is_clean():
    state, detail = verdict({"status": "APPROVED", "tcr_id": "BRAND1234"})
    assert state == "approved"
    assert "BRAND1234" in detail


def test_suspended_is_not_folded_into_failed():
    state, detail = verdict({"status": "SUSPENDED"})
    assert state == "suspended"
    assert "every campaign" in detail


def test_in_review_is_not_a_finding():
    state, _ = verdict({"status": "IN_REVIEW", "tcr_id": None})
    assert state == "in-review"
''',
"test_js_file": "twilio-a2p-brand-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { failureLines, verdict } from './twilio-a2p-brand-audit.mjs';

test('failed brand reports the code and the fields', () => {
  const [state, detail] = verdict({
    status: 'FAILED',
    errors: [{ code: 30799, description: 'Unable to verify registration details',
               fields: ['business_registration_identifier'] }],
  });
  assert.equal(state, 'failed');
  assert.match(detail, /30799/);
  assert.match(detail, /business_registration_identifier/);
});

test('deprecated prose is used but labelled', () => {
  const [state, detail] = verdict({ status: 'FAILED', errors: [],
                                    failure_reason: 'EIN does not match' });
  assert.equal(state, 'failed-deprecated-reason');
  assert.match(detail, /deprecated/);
});

test('errors win over the deprecated fields', () => {
  const [source, lines] = failureLines({ errors: [{ code: '30799' }],
                                         brand_feedback: 'old text' });
  assert.equal(source, 'errors');
  assert.equal(lines.length, 1);
});

test('failed with nothing at all mentions the resubmission limit', () => {
  const [state, detail] = verdict({ status: 'FAILED' });
  assert.equal(state, 'failed-unexplained');
  assert.match(detail, /21724/);
});

test('approved without a tcr id is a disagreement', () => {
  assert.equal(verdict({ status: 'APPROVED', tcr_id: null })[0],
               'approved-no-tcr-id');
});

test('approved with a tcr id is clean', () => {
  const [state, detail] = verdict({ status: 'APPROVED', tcr_id: 'BRAND1234' });
  assert.equal(state, 'approved');
  assert.match(detail, /BRAND1234/);
});

test('suspended is not folded into failed', () => {
  const [state, detail] = verdict({ status: 'SUSPENDED' });
  assert.equal(state, 'suspended');
  assert.match(detail, /every campaign/);
});

test('in review is not a finding', () => {
  assert.equal(verdict({ status: 'IN_REVIEW', tcr_id: null })[0], 'in-review');
});
''',
"faq": [
 ("Why do the sends fail with 30034 when the problem is the brand?",
  "Because 30034 means the sending number is not registered, and a number cannot be registered without a campaign, and a campaign cannot exist without an approved brand. Every one of those failures collapses into the same send-side code, which is why the brand resource has to be read directly."),
 ("Should I read failure_reason or brand_feedback?",
  "Only as a labelled fallback. Both are deprecated in favour of errors[], which is structured: a code, a description, the fields it objects to and a docs URL. Code that reads only the old fields will report a fully explained rejection as having no reason given."),
 ("How many times can I resubmit a brand?",
  "Three resubmissions are free; the fourth returns 21724. That is why blind retries are worse than they look. Read errors[], fix the Customer Profile the brand was built from, and spend one of the three deliberately."),
 ("The brand is APPROVED but tcr_id is null. Which do I believe?",
  "Neither, yet. tcr_id is populated when The Campaign Registry accepts the brand, so an approved brand without one is a disagreement between two fields on the same object. The script reports it as its own state rather than resolving it, because the right next step is to look rather than to assume."),
 ("Can I just create a second brand?",
  "No. Duplicate brands on one EIN cause their own rejection, and a campaign that fails on 30898 is exactly that problem. Fix the brand you have."),
],
"related": [
 ("/twilio/a2p-campaign-vetting-failed/", "A campaign is FAILED and errors[] names the field"),
 ("/twilio/a2p-campaign-stuck-in-progress/", "A campaign parked at IN_PROGRESS is not live"),
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign"),
],
"citations": [CITE_BRAND, CITE_FIX_BRANDS, CITE_30034, CITE_KEYS],
},

{
"slug": "a2p-campaign-stuck-in-progress",
"title": "An A2P campaign parked at IN_PROGRESS is not a live campaign",
"description": "campaign_status sits at IN_PROGRESS for weeks, campaign_id is null, and the launch ships anyway. Nothing errors, and every US send returns 30034.",
"h1": "an a2p campaign parked at IN_PROGRESS is not a live campaign",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio campaign_status in_progress", "a2p campaign pending approval",
             "10dlc campaign not verified", "twilio campaign_id null",
             "a2p registration taking weeks"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Registration was submitted, the console went quiet, and three weeks later the launch shipped on the assumption that quiet meant done. It did not. <code>campaign_status</code> still reads <code>IN_PROGRESS</code>, <code>campaign_id</code> is still <code>null</code>, and every US message is coming back <code>30034</code>. Nothing is broken. It simply was never approved.",
"short_answer": """<p>Read <code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/Compliance/Usa2p</code> and flag any campaign whose <code>campaign_status</code> is <code>PENDING</code> or <code>IN_PROGRESS</code> and whose <code>date_created</code> is older than your launch SLA. Corroborate with <code>campaign_id</code>, which stays <code>null</code> until the registry issues one.</p>
<p>Two variants are worth separating from plain waiting: a campaign still <code>IN_PROGRESS</code> whose <code>errors[]</code> is already populated, which means the vetting result has landed and the status has not caught up, and one that has a <code>campaign_id</code> while the status still says it is in progress.</p>""",
"problem": """<p>Every other registration failure gives you something to read. This one gives you an empty <code>errors[]</code> and a status word that sounds like progress. There is no rejection, no code, no callback that says stop &mdash; and because nothing has gone wrong, nothing in your monitoring will ever mention it. The campaign is simply not finished, and TCR review has run to three weeks during backlogs.</p>
<p>What turns that into an outage is the deploy. A rollout gated on "we submitted the registration" rather than on <code>campaign_status == "VERIFIED"</code> goes out into a state where numbers in the sender pool cannot reach <code>REGISTERED</code>, so every US message fails <code>30034</code> on launch day. The registration was fine. The gate was wrong.</p>""",
"why": """<p><strong>Waiting and failing look identical from the send side.</strong> Both produce <code>30034</code> on every US message. The only thing that distinguishes "not approved yet" from "rejected" is the campaign resource, and if nobody reads it, the two are the same event with different fixes.</p>
<p><strong>Callbacks are fire and forget.</strong> Most integrations register a status callback at submission time and never poll again. A callback missed during a deploy, or an endpoint that 500s once, leaves the campaign parked with no second chance to notice. Polling is one GET and does not depend on your own uptime.</p>
<p><strong>The review has no SLA you can plan against.</strong> Sometimes hours, sometimes three weeks. That variance is exactly what makes "it has probably gone through by now" so tempting and so unreliable, and it is why the check has to be a scheduled read rather than a memory.</p>
<p><strong>The status field can lag the outcome.</strong> A campaign can carry entries in <code>errors[]</code> while <code>campaign_status</code> still says <code>IN_PROGRESS</code>. Reading only the status there means waiting out a review that has already returned an answer.</p>""",
"steps": [
 {"h": "Read the campaign on every service, on a schedule",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Services/{ServiceSid}/Compliance/Usa2p</code>, campaigns under <code>compliance</code>. This belongs in cron rather than in a runbook, because the whole failure mode is that nobody looked again after submitting.</p>"""},
 {"h": "Age the campaign against a launch SLA you actually chose",
  "body": """<p><code>date_created</code> comes back as ISO 8601 with a trailing <code>Z</code>, which <code>datetime.fromisoformat</code> would not accept before Python 3.11. Compare the age against a number you picked &mdash; seven days is a reasonable "somebody should look", twenty-one is the point Twilio Support becomes the next step.</p>"""},
 {"h": "Corroborate with campaign_id",
  "body": """<p><code>campaign_id</code> is <code>null</code> until the registry issues one, so a campaign that is <code>IN_PROGRESS</code> with no <code>campaign_id</code> is genuinely still in review. One that has a <code>campaign_id</code> while the status has not moved is a disagreement, and worth reporting as such rather than picking whichever field you read first.</p>"""},
 {"h": "Check errors[] even while the status says in progress",
  "body": """<p>An empty <code>errors[]</code> is part of what confirms a campaign is still waiting. A populated one under an <code>IN_PROGRESS</code> status means the vetting result has arrived and the status is behind it, so there is something to read and act on now rather than more waiting to do.</p>"""},
 {"h": "Gate the rollout on VERIFIED, and have an interim sender",
  "body": """<p>There is no API action that speeds this up. What you control is the release gate: check <code>campaign_status == "VERIFIED"</code> before enabling US sends, and route the interim traffic through a verified toll-free number or Twilio Verify. Escalate to Support past about three weeks, quoting the campaign SID.</p>"""},
],
"verify": """<p>Re-run the script. Every campaign should report <code>verified</code>, and nothing should be sitting past the SLA.</p>
<pre><code class="language-bash">python3 twilio_a2p_campaign_wait_audit.py --sla-days 7
# 4 service(s), 0 campaign(s) still waiting past 7 days</code></pre>""",
"code_intro": "One paginated GET for the services and one per service for its campaign, reads only, with an API Key that has read access. The clock is kept out of the classifier: <code>verdict()</code> takes an age in days, so the interesting decisions &mdash; waiting, overdue, escalate, and the two states where the fields disagree &mdash; can be tested without freezing time.",
"py_file": "twilio_a2p_campaign_wait_audit.py",
"py": '''"""Report A2P 10DLC campaigns still waiting for approval past a launch SLA.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. Nothing here can speed up a review; the
script exists so a rollout is gated on VERIFIED rather than on a memory of
having submitted the registration.
"""
import argparse
import datetime
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_a2p_campaign_wait_audit")

MSG = "https://messaging.twilio.com/v1"

WAITING = ("PENDING", "IN_PROGRESS")


def parse_time(value):
    """Parse a messaging v1 timestamp. Pure.

    These come back as ISO 8601 with a trailing Z, which
    datetime.fromisoformat did not accept before Python 3.11.
    """
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        return datetime.datetime.fromisoformat(text)
    except ValueError:
        return None


def age_days(date_created, now):
    """Age of a campaign in days, or None when the timestamp is unreadable."""
    created = parse_time(date_created)
    if created is None or now is None:
        return None
    return (now - created).total_seconds() / 86400.0


def verdict(campaign, age, sla_days=7, escalate_days=21):
    """Classify one UsAppToPerson campaign that may still be in review.

    `age` is the campaign's age in days, or None. Taking it as an argument keeps
    the clock out of the classifier, so every state below is testable without
    freezing time. Returns (state, detail).
    """
    if not campaign:
        return ("no-campaign", "no A2P campaign on this Messaging Service.")

    status = str(campaign.get("campaign_status") or "").upper()
    campaign_id = str(campaign.get("campaign_id") or "").strip()
    errors = campaign.get("errors") or []

    if status == "VERIFIED":
        if not campaign_id:
            return ("verified-no-campaign-id",
                    "campaign_status is VERIFIED but campaign_id is null, which "
                    "is what an unfinished registration looks like.")
        return ("verified", "VERIFIED with campaign_id %s" % campaign_id)

    if status in ("FAILED", "SUSPENDED"):
        return ("not-waiting",
                "campaign_status is %s: this is a rejection, not a queue. Read "
                "errors[] rather than waiting any longer." % status)

    if status not in WAITING:
        return ("unknown-status",
                "campaign_status is %s, which this script does not recognise."
                % (status or "unset"))

    if errors:
        return ("waiting-with-errors",
                "still %s, but errors[] already has %d entr%s: the vetting "
                "result has arrived and the status is behind it."
                % (status, len(errors), "y" if len(errors) == 1 else "ies"))

    if campaign_id:
        return ("waiting-with-campaign-id",
                "still %s, but campaign_id is %s. The registry has issued an "
                "id while the status says the review is running."
                % (status, campaign_id))

    if age is None:
        return ("waiting-unknown-age",
                "still %s and date_created could not be read, so this cannot be "
                "aged against the SLA." % status)

    if age >= escalate_days:
        return ("escalate",
                "still %s after %.0f days. Past about three weeks this is a "
                "support ticket quoting the campaign SID, not more waiting."
                % (status, age))

    if age >= sla_days:
        return ("overdue",
                "still %s after %.0f days, past the %d day SLA. US sends will "
                "keep returning 30034 until it is VERIFIED."
                % (status, age, sla_days))

    return ("waiting",
            "still %s after %.0f days, inside the %d day SLA. Not live yet: do "
            "not enable US sends." % (status, age, sla_days))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_v1(session, url, key, limit=1000):
    """Page a messaging.twilio.com list. meta.next_page_url is absolute."""
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        out.extend(page.get(key, []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sla-days", type=int, default=7,
                    help="how long a campaign may sit in review before it is a finding")
    ap.add_argument("--escalate-days", type=int, default=21,
                    help="age past which this becomes a support ticket")
    ap.add_argument("--max-services", type=int, default=200)
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    session = requests.Session()
    session.auth = (key, secret)
    now = datetime.datetime.now(datetime.timezone.utc)

    services = list_v1(session, MSG + "/Services", "services", args.max_services)
    if not services:
        log.info("no Messaging Services on this account")
        return 0

    bad = 0
    for svc in services:
        campaigns = list_v1(session,
                            "%s/Services/%s/Compliance/Usa2p" % (MSG, svc["sid"]),
                            "compliance")
        campaign = campaigns[0] if campaigns else None
        age = age_days((campaign or {}).get("date_created"), now)
        state, detail = verdict(campaign, age, args.sla_days, args.escalate_days)
        name = svc.get("friendly_name") or svc["sid"]
        line = "%-24s %s  %s" % (state, name, detail)
        if state in ("verified", "waiting"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state in ("overdue", "escalate", "waiting-unknown-age"):
            log.warning("  repair: none by API. Gate the rollout on "
                        "campaign_status == VERIFIED and send the interim traffic "
                        "from a verified toll-free number or Twilio Verify")
        elif state == "waiting-with-errors":
            log.warning("  repair: read errors[] on %s now; it has already been "
                        "reviewed", campaign.get("sid", "the campaign"))

    log.info("%d service(s), %d campaign(s) still waiting past %d days",
             len(services), bad, args.sla_days)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-a2p-campaign-wait-audit.mjs",
"js": '''/**
 * Report A2P 10DLC campaigns still waiting for approval past a launch SLA.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. Nothing here can speed up a
 * review; the script exists so a rollout is gated on VERIFIED.
 */
const MSG = 'https://messaging.twilio.com/v1';

const WAITING = ['PENDING', 'IN_PROGRESS'];

/** Parse a messaging v1 ISO 8601 timestamp. Pure. Returns a Date or null. */
export function parseTime(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const t = Date.parse(text);
  return Number.isNaN(t) ? null : new Date(t);
}

/** Age of a campaign in days, or null when the timestamp is unreadable. */
export function ageDays(dateCreated, now) {
  const created = parseTime(dateCreated);
  if (created === null || !now) return null;
  return (now.getTime() - created.getTime()) / 86400000;
}

/**
 * Classify one UsAppToPerson campaign that may still be in review. `age` is in
 * days, or null; taking it as an argument keeps the clock out of the
 * classifier. Pure. Returns [state, detail].
 */
export function verdict(campaign, age, slaDays = 7, escalateDays = 21) {
  if (!campaign) return ['no-campaign', 'no A2P campaign on this Messaging Service.'];

  const status = String(campaign.campaign_status ?? '').toUpperCase();
  const campaignId = String(campaign.campaign_id ?? '').trim();
  const errors = campaign.errors ?? [];

  if (status === 'VERIFIED') {
    if (!campaignId) {
      return ['verified-no-campaign-id',
        'campaign_status is VERIFIED but campaign_id is null, which is what an ' +
        'unfinished registration looks like.'];
    }
    return ['verified', `VERIFIED with campaign_id ${campaignId}`];
  }

  if (status === 'FAILED' || status === 'SUSPENDED') {
    return ['not-waiting',
      `campaign_status is ${status}: this is a rejection, not a queue. Read ` +
      'errors[] rather than waiting any longer.'];
  }

  if (!WAITING.includes(status)) {
    return ['unknown-status',
      `campaign_status is ${status || 'unset'}, which this script does not recognise.`];
  }

  if (errors.length) {
    return ['waiting-with-errors',
      `still ${status}, but errors[] already has ${errors.length} ` +
      `entr${errors.length === 1 ? 'y' : 'ies'}: the vetting result has ` +
      'arrived and the status is behind it.'];
  }

  if (campaignId) {
    return ['waiting-with-campaign-id',
      `still ${status}, but campaign_id is ${campaignId}. The registry has ` +
      'issued an id while the status says the review is running.'];
  }

  if (age === null) {
    return ['waiting-unknown-age',
      `still ${status} and date_created could not be read, so this cannot be ` +
      'aged against the SLA.'];
  }

  if (age >= escalateDays) {
    return ['escalate',
      `still ${status} after ${age.toFixed(0)} days. Past about three weeks ` +
      'this is a support ticket quoting the campaign SID, not more waiting.'];
  }

  if (age >= slaDays) {
    return ['overdue',
      `still ${status} after ${age.toFixed(0)} days, past the ${slaDays} day ` +
      'SLA. US sends will keep returning 30034 until it is VERIFIED.'];
  }

  return ['waiting',
    `still ${status} after ${age.toFixed(0)} days, inside the ${slaDays} day ` +
    'SLA. Not live yet: do not enable US sends.'];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

async function get(auth, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  const res = await fetch(u, { headers: { Authorization: auth } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Twilio: check TWILIO_ACCOUNT_SID and ` +
                    'that the API key belongs to that account with read access');
  }
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return res.json();
}

export async function listV1(auth, url, key, limit = 1000) {
  const out = [];
  let next = url;
  while (next && out.length < limit) {
    const page = await get(auth, next, { PageSize: 50 });
    out.push(...(page[key] ?? []));
    next = page.meta?.next_page_url ?? null;
  }
  return out.slice(0, limit);
}

async function main() {
  const account = process.env.TWILIO_ACCOUNT_SID;
  const key = process.env.TWILIO_API_KEY;
  const secret = process.env.TWILIO_API_SECRET;
  if (!account || !key || !secret) {
    console.error('set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET ' +
                  '(an API Key with read access, not the auth token)');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);
  const slaFlag = process.argv.indexOf('--sla-days');
  const slaDays = slaFlag >= 0 ? Number(process.argv[slaFlag + 1]) : 7;
  const now = new Date();

  const services = await listV1(auth, `${MSG}/Services`, 'services');
  if (services.length === 0) {
    console.log('no Messaging Services on this account');
    return;
  }

  let bad = 0;
  for (const svc of services) {
    const campaigns = await listV1(auth, `${MSG}/Services/${svc.sid}/Compliance/Usa2p`,
                                   'compliance');
    const campaign = campaigns[0] ?? null;
    const age = ageDays(campaign?.date_created, now);
    const [state, detail] = verdict(campaign, age, slaDays);
    const name = svc.friendly_name ?? svc.sid;
    const line = `${state.padEnd(24)} ${name}  ${detail}`;
    if (state === 'verified' || state === 'waiting') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'overdue' || state === 'escalate' || state === 'waiting-unknown-age') {
      console.warn('  repair: none by API. Gate the rollout on campaign_status == ' +
                   'VERIFIED and send the interim traffic from a verified toll-free ' +
                   'number or Twilio Verify');
    } else if (state === 'waiting-with-errors') {
      console.warn(`  repair: read errors[] on ${campaign.sid ?? 'the campaign'} ` +
                   'now; it has already been reviewed');
    }
  }

  console.log(`${services.length} service(s), ${bad} campaign(s) still waiting past ` +
              `${slaDays} days`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Because the age is an argument rather than a clock read inside the function, the boundary cases are ordinary tests: one day inside the SLA, one day past it, and past the escalation point. The two that earn their place are the disagreements &mdash; <code>IN_PROGRESS</code> with a populated <code>errors[]</code>, and <code>VERIFIED</code> with a null <code>campaign_id</code> &mdash; because both read as fine if you only look at the status word.",
"test_py_file": "test_twilio_a2p_campaign_wait_audit.py",
"test_py": '''import datetime

from twilio_a2p_campaign_wait_audit import age_days, verdict

IN_PROGRESS = {"sid": "QE0123456789", "campaign_status": "IN_PROGRESS"}
NOW = datetime.datetime(2026, 8, 30, tzinfo=datetime.timezone.utc)


def test_inside_the_sla_is_waiting_not_a_finding():
    state, detail = verdict(IN_PROGRESS, 3.0, sla_days=7)
    assert state == "waiting"
    assert "do not enable US sends" in detail


def test_past_the_sla_is_overdue():
    state, detail = verdict(IN_PROGRESS, 9.0, sla_days=7)
    assert state == "overdue"
    assert "30034" in detail


def test_past_three_weeks_is_a_support_ticket():
    state, _ = verdict(IN_PROGRESS, 25.0, sla_days=7, escalate_days=21)
    assert state == "escalate"


def test_in_progress_with_errors_is_already_decided():
    # The status lags the outcome. Waiting longer here achieves nothing.
    state, detail = verdict(dict(IN_PROGRESS, errors=[{"error_code": 30886}]), 2.0)
    assert state == "waiting-with-errors"
    assert "1 entry" in detail


def test_a_campaign_id_while_still_in_progress_is_a_disagreement():
    state, _ = verdict(dict(IN_PROGRESS, campaign_id="CX123"), 2.0)
    assert state == "waiting-with-campaign-id"


def test_verified_without_a_campaign_id_is_not_reported_as_live():
    state, _ = verdict({"campaign_status": "VERIFIED", "campaign_id": None}, 30.0)
    assert state == "verified-no-campaign-id"


def test_failed_is_a_rejection_not_a_queue():
    state, detail = verdict({"campaign_status": "FAILED"}, 30.0)
    assert state == "not-waiting"
    assert "errors[]" in detail


def test_age_days_reads_the_trailing_z_timestamp():
    assert round(age_days("2026-08-23T00:00:00Z", NOW)) == 7
    assert age_days("not a date", NOW) is None
''',
"test_js_file": "twilio-a2p-campaign-wait-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { ageDays, verdict } from './twilio-a2p-campaign-wait-audit.mjs';

const IN_PROGRESS = { sid: 'QE0123456789', campaign_status: 'IN_PROGRESS' };
const NOW = new Date('2026-08-30T00:00:00Z');

test('inside the sla is waiting, not a finding', () => {
  const [state, detail] = verdict(IN_PROGRESS, 3.0, 7);
  assert.equal(state, 'waiting');
  assert.match(detail, /do not enable US sends/);
});

test('past the sla is overdue', () => {
  const [state, detail] = verdict(IN_PROGRESS, 9.0, 7);
  assert.equal(state, 'overdue');
  assert.match(detail, /30034/);
});

test('past three weeks is a support ticket', () => {
  assert.equal(verdict(IN_PROGRESS, 25.0, 7, 21)[0], 'escalate');
});

test('in progress with errors is already decided', () => {
  const [state, detail] = verdict({ ...IN_PROGRESS, errors: [{ error_code: 30886 }] },
                                  2.0);
  assert.equal(state, 'waiting-with-errors');
  assert.match(detail, /1 entry/);
});

test('a campaign id while still in progress is a disagreement', () => {
  assert.equal(verdict({ ...IN_PROGRESS, campaign_id: 'CX123' }, 2.0)[0],
               'waiting-with-campaign-id');
});

test('verified without a campaign id is not reported as live', () => {
  assert.equal(verdict({ campaign_status: 'VERIFIED', campaign_id: null }, 30.0)[0],
               'verified-no-campaign-id');
});

test('failed is a rejection, not a queue', () => {
  const [state, detail] = verdict({ campaign_status: 'FAILED' }, 30.0);
  assert.equal(state, 'not-waiting');
  assert.match(detail, /errors/);
});

test('ageDays reads the trailing z timestamp', () => {
  assert.equal(Math.round(ageDays('2026-08-23T00:00:00Z', NOW)), 7);
  assert.equal(ageDays('not a date', NOW), null);
});
''',
"faq": [
 ("How long should a campaign take to reach VERIFIED?",
  "Sometimes hours, sometimes three weeks during a registry backlog. There is no SLA you can plan a launch around, which is why the release has to be gated on the status rather than on elapsed time or on somebody's recollection of having submitted it."),
 ("Is there any way to speed up the review?",
  "No API action exists. Past about three weeks it is worth a Twilio Support ticket quoting the campaign SID, but before that there is nothing to do except not ship the US traffic yet. Deleting and resubmitting puts you at the back of the same queue and pays the vetting fee again."),
 ("Why is campaign_id worth reading if I already have campaign_status?",
  "Because it is issued by the registry rather than set alongside the status, so the two can disagree. A VERIFIED campaign with a null campaign_id, or an IN_PROGRESS one that already has an id, is a state worth looking at rather than trusting."),
 ("What can we send in the meantime?",
  "A verified toll-free number, or Twilio Verify for one-time passcodes. Both are separate registration paths from 10DLC, so neither is blocked by this campaign. What you cannot do is send from an unregistered long code and hope."),
 ("Does the script poll for me?",
  "It performs one read per Messaging Service, so putting it in cron with a sensible SLA is the intended use. It never writes: a script that resubmits a compliance registration on a timer can burn the review queue and the vetting fee at the same time."),
],
"related": [
 ("/twilio/a2p-campaign-vetting-failed/", "A campaign is FAILED and errors[] names the field"),
 ("/twilio/a2p-brand-registration-failed/", "An A2P brand stuck at FAILED blocks every campaign"),
 ("/twilio/tollfree-number-not-verified/", "An unverified toll-free number is blocked outright"),
],
"citations": [CITE_USA2P, CITE_FIX_CAMPAIGNS, CITE_30034, CITE_SERVICE],
},

{
"slug": "tollfree-number-not-verified",
"title": "An unverified toll-free number is blocked, not throttled",
"description": "Every US and CA message from an unverified +1 8XX number fails 30032, and you are billed for the attempts. Pending review is a blocked state too.",
"h1": "an unverified toll-free number is blocked, not throttled",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio 30032", "toll-free not verified", "tollfree verification pending",
             "twilio toll free sms blocked", "tollfree_phone_number_sid"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Toll-free was the easy option: no brand, no campaign, no EIN, buy the number and send. That stopped being true on 31 January 2024. Unverified toll-free traffic to US and Canadian mobiles is now blocked outright rather than throttled, every message comes back <code>30032</code>, and you are still billed for the attempts.",
"short_answer": """<p>List the toll-free numbers with <code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/TollFree.json</code>, then list the verifications with <code>GET https://messaging.twilio.com/v1/Tollfree/Verifications</code> and join them on <code>tollfree_phone_number_sid</code>.</p>
<p>Flag two things, not one: a toll-free number with no verification record at all, and a record whose <code>status</code> is <code>PENDING_REVIEW</code> or <code>IN_REVIEW</code>. Both are blocked states. Only <code>TWILIO_APPROVED</code> can send, and a <code>TWILIO_REJECTED</code> record carries its reasons in <code>rejection_reasons[]</code> alongside <code>edit_allowed</code> and <code>edit_expiration</code>.</p>""",
"problem": """<p>The whole appeal of a toll-free number was that it skipped the 10DLC paperwork. That reputation outlived the policy by years, so teams still reach for toll-free as the quick path, buy the number, wire it up, test it internally and discover at launch that toll-free has its own mandatory verification with no unverified allowance at all.</p>
<p>Two details make it worse than a plain outage. The first is that <em>pending</em> is blocked: filing the verification is not the same as passing it, and a number sitting in review sends exactly like one that was never filed. The second is that you pay for the blocked attempts, so a retry loop against <code>30032</code> spends money at full speed while delivering nothing.</p>""",
"why": """<p><strong>The rule changed and the folklore did not.</strong> Before 31 January 2024 unverified toll-free traffic was throttled, which meant a test message usually got through. Now it is blocked. Anyone whose mental model predates that date will test, see failure, and assume a configuration mistake rather than a policy.</p>
<p><strong>Filing is not passing.</strong> <code>PENDING_REVIEW</code> and <code>IN_REVIEW</code> both look like progress and both block every message. A check that treats "there is a verification record" as success reports a number that cannot send as healthy, which is the single most common way this is missed.</p>
<p><strong>The two objects live in different APIs.</strong> The numbers are on the 2010-04-01 account API and the verifications are on <code>messaging.twilio.com/v1</code>, keyed by <code>tollfree_phone_number_sid</code>. Neither response knows about the other, so the finding only exists in the join.</p>
<p><strong>The rejection reasons are structured and nobody reads them.</strong> A <code>TWILIO_REJECTED</code> record has <code>rejection_reasons[]</code>, an <code>error_code</code> and an <code>edit_expiration</code>. Resubmitting identical data gets rejected identically, and the edit window closes while that is happening.</p>""",
"steps": [
 {"h": "List the toll-free numbers from the dedicated endpoint",
  "body": """<p><code>GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/TollFree.json?PageSize=1000</code>, paging on <code>next_page_uri</code>. Filtering the full number list on the <code>8XX</code> prefixes yourself works, but this endpoint is the one Twilio maintains and it will not drift when a new toll-free code is allocated.</p>"""},
 {"h": "Skip the numbers that cannot send SMS anyway",
  "body": """<p>Read <code>capabilities.sms</code>. A toll-free number bought for voice has nothing to verify, and putting it in the report trains people to skim the report. The finding should be numbers that are expected to send and cannot.</p>"""},
 {"h": "Join on tollfree_phone_number_sid, and pick a record deliberately",
  "body": """<p><code>GET https://messaging.twilio.com/v1/Tollfree/Verifications</code>. A number can carry more than one record &mdash; an old rejection and a newer approval, for instance &mdash; so prefer <code>TWILIO_APPROVED</code> and otherwise take the most recently updated. A plain set-membership check reports whichever the API happened to return first.</p>"""},
 {"h": "Treat review states as blocked, because they are",
  "body": """<p><code>PENDING_REVIEW</code> and <code>IN_REVIEW</code> belong in the same report as no record at all. Since 31 January 2024 traffic in those states is blocked rather than throttled, so the practical difference between "filed last week" and "never filed" is nothing.</p>"""},
 {"h": "For a rejection, read the reasons before the edit window closes",
  "body": """<p><code>rejection_reasons[]</code> and <code>error_code</code> say what was wrong; <code>edit_allowed</code> and <code>edit_expiration</code> say how long the cheap fix is available. Correcting the named fields in place beats a fresh submission, which goes to the back of the review queue.</p>"""},
],
"verify": """<p>Re-run the script. Every SMS-capable toll-free number should report <code>verified</code>.</p>
<pre><code class="language-bash">python3 twilio_tollfree_verification_audit.py
# 3 toll-free number(s), 0 blocked from US and CA SMS</code></pre>""",
"code_intro": "Two paginated GETs and a join &mdash; the toll-free numbers from the account API, the verifications from messaging v1 &mdash; read with an API Key that has read access and nothing more. Both interesting decisions are pure functions: which verification record governs a number when it has several, and why a given record does or does not let it send.",
"py_file": "twilio_tollfree_verification_audit.py",
"py": '''"""Report toll-free numbers that cannot send US or CA SMS for want of verification.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The submission is printed, never performed,
because this script holds a credential to an account that can send messages and
spend money.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_tollfree_verification_audit")

HOST = "https://api.twilio.com"
BASE = HOST + "/2010-04-01"
MSG = "https://messaging.twilio.com/v1"

# Since 31 January 2024 these are blocked, not throttled. They belong in the
# same report as a number with no verification record at all.
BLOCKED_REVIEW = ("PENDING_REVIEW", "IN_REVIEW")


def pick_verification(records):
    """Choose the record that governs a number. Pure.

    A number can carry more than one: an old rejection and a newer approval, for
    instance. A plain set-membership check reports whichever the API returned
    first, so prefer TWILIO_APPROVED and otherwise take the most recently
    updated.
    """
    if not records:
        return None
    approved = [r for r in records
                if str(r.get("status") or "").upper() == "TWILIO_APPROVED"]
    pool = approved or list(records)
    return max(pool, key=lambda r: str(r.get("date_updated")
                                       or r.get("date_created") or ""))


def rejection_lines(verification):
    """Why a verification was rejected, from the structured fields first. Pure.

    rejection_reasons[] is the list nobody reads; error_code and the
    rejection_reason prose are the fallbacks when it is absent.
    """
    lines = []
    for reason in verification.get("rejection_reasons") or []:
        code = reason.get("code") or reason.get("error_code") or "no code"
        lines.append("%s: %s" % (code, reason.get("description")
                                 or "no description"))
    if lines:
        return lines
    code = verification.get("error_code")
    prose = str(verification.get("rejection_reason") or "").strip()
    if code or prose:
        lines.append("%s: %s" % (code or "no code", prose or "no description"))
    return lines


def verdict(number, verification):
    """Decide whether one toll-free number can send US or CA SMS. Pure, so the
    blocked states can be tested without a network.

    Returns (state, detail).
    """
    if not (number.get("capabilities") or {}).get("sms"):
        return ("voice-only",
                "toll-free number with no SMS capability: nothing to verify.")

    if not verification:
        return ("unverified",
                "no toll-free verification record at all. Every US or CA SMS "
                "from this number fails 30032, and the attempts are billed.")

    status = str(verification.get("status") or "").upper()

    if status == "TWILIO_APPROVED":
        return ("verified", "verification %s is TWILIO_APPROVED"
                % (verification.get("sid") or "?"))

    if status in BLOCKED_REVIEW:
        return ("blocked-in-review",
                "verification is %s. Filing is not passing: since 31 January "
                "2024 traffic in a review state is blocked outright rather than "
                "throttled." % status)

    if status == "TWILIO_REJECTED":
        reasons = "; ".join(rejection_lines(verification)) or "no reason on the record"
        if verification.get("edit_allowed"):
            return ("rejected-editable",
                    "rejected (%s). edit_allowed is true until %s, so the named "
                    "fields can still be corrected in place."
                    % (reasons, verification.get("edit_expiration") or "an "
                       "unstated date"))
        return ("rejected-final",
                "rejected (%s) and edit_allowed is false: a fresh submission is "
                "the only path, at the back of the review queue." % reasons)

    return ("unknown-status",
            "verification status is %s, which this script does not recognise."
            % (status or "unset"))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def list_tollfree(session, account, limit=1000):
    """Page the toll-free numbers. next_page_uri is a path, not an absolute URL."""
    url = "%s/Accounts/%s/IncomingPhoneNumbers/TollFree.json" % (BASE, account)
    params = {"PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("incoming_phone_numbers", []))
        nxt = page.get("next_page_uri")
        url, params = (HOST + nxt) if nxt else None, {}
    return out[:limit]


def list_verifications(session, limit=1000):
    """Page the toll-free verifications. meta.next_page_url is absolute."""
    url = MSG + "/Tollfree/Verifications"
    out = []
    while url and len(out) < limit:
        page = get(session, url, PageSize=50)
        out.extend(page.get("verifications", []))
        url = (page.get("meta") or {}).get("next_page_url")
    return out[:limit]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-numbers", type=int, default=1000)
    args = ap.parse_args()

    account = os.environ.get("TWILIO_ACCOUNT_SID")
    key = os.environ.get("TWILIO_API_KEY")
    secret = os.environ.get("TWILIO_API_SECRET")
    if not (account and key and secret):
        log.error("set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET "
                  "(an API Key with read access, not the auth token)")
        return 2

    session = requests.Session()
    session.auth = (key, secret)

    numbers = list_tollfree(session, account, args.max_numbers)
    if not numbers:
        log.info("no toll-free numbers on this account")
        return 0

    by_sid = {}
    for record in list_verifications(session):
        by_sid.setdefault(record.get("tollfree_phone_number_sid"), []).append(record)

    bad = 0
    for n in numbers:
        verification = pick_verification(by_sid.get(n.get("sid")) or [])
        state, detail = verdict(n, verification)
        line = "%-18s %s  %s" % (state, n.get("phone_number", "?"), detail)
        if state in ("verified", "voice-only"):
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        if state == "unverified":
            log.warning("  repair: POST %s/Tollfree/Verifications with BusinessName, "
                        "BusinessWebsite, NotificationEmail, UseCaseCategories, "
                        "UseCaseSummary, ProductionMessageSample, OptInType, "
                        "OptInImageUrls, MessageVolume and "
                        "TollfreePhoneNumberSid=%s", MSG, n.get("sid", "PN..."))
        elif state == "rejected-editable":
            log.warning("  repair: POST %s/Tollfree/Verifications/%s correcting the "
                        "named fields before edit_expiration", MSG,
                        verification.get("sid", "HH..."))
        elif state == "blocked-in-review":
            log.warning("  repair: none by API. Wait for TWILIO_APPROVED and do not "
                        "route production traffic through this number meanwhile")

    log.info("%d toll-free number(s), %d blocked from US and CA SMS",
             len(numbers), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-tollfree-verification-audit.mjs",
"js": '''/**
 * Report toll-free numbers that cannot send US or CA SMS for want of verification.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The submission is printed, never
 * performed.
 */
const HOST = 'https://api.twilio.com';
const BASE = `${HOST}/2010-04-01`;
const MSG = 'https://messaging.twilio.com/v1';

// Since 31 January 2024 these are blocked, not throttled.
const BLOCKED_REVIEW = ['PENDING_REVIEW', 'IN_REVIEW'];

/**
 * Choose the record that governs a number. Pure. A number can carry more than
 * one, so prefer TWILIO_APPROVED and otherwise take the most recently updated.
 */
export function pickVerification(records) {
  if (!records || records.length === 0) return null;
  const approved = records.filter(
    (r) => String(r.status ?? '').toUpperCase() === 'TWILIO_APPROVED');
  const pool = approved.length ? approved : records;
  const stamp = (r) => String(r.date_updated ?? r.date_created ?? '');
  return pool.reduce((best, r) => (stamp(r) > stamp(best) ? r : best), pool[0]);
}

/** Why a verification was rejected, from the structured fields first. Pure. */
export function rejectionLines(verification) {
  const lines = [];
  for (const reason of verification.rejection_reasons ?? []) {
    const code = reason.code ?? reason.error_code ?? 'no code';
    lines.push(`${code}: ${reason.description ?? 'no description'}`);
  }
  if (lines.length) return lines;
  const code = verification.error_code;
  const prose = String(verification.rejection_reason ?? '').trim();
  if (code || prose) lines.push(`${code ?? 'no code'}: ${prose || 'no description'}`);
  return lines;
}

/**
 * Decide whether one toll-free number can send US or CA SMS. Pure, so the
 * blocked states can be tested without a network. Returns [state, detail].
 */
export function verdict(number, verification) {
  if (!(number.capabilities ?? {}).sms) {
    return ['voice-only', 'toll-free number with no SMS capability: nothing to verify.'];
  }

  if (!verification) {
    return ['unverified',
      'no toll-free verification record at all. Every US or CA SMS from this ' +
      'number fails 30032, and the attempts are billed.'];
  }

  const status = String(verification.status ?? '').toUpperCase();

  if (status === 'TWILIO_APPROVED') {
    return ['verified', `verification ${verification.sid ?? '?'} is TWILIO_APPROVED`];
  }

  if (BLOCKED_REVIEW.includes(status)) {
    return ['blocked-in-review',
      `verification is ${status}. Filing is not passing: since 31 January 2024 ` +
      'traffic in a review state is blocked outright rather than throttled.'];
  }

  if (status === 'TWILIO_REJECTED') {
    const reasons = rejectionLines(verification).join('; ') || 'no reason on the record';
    if (verification.edit_allowed) {
      return ['rejected-editable',
        `rejected (${reasons}). edit_allowed is true until ` +
        `${verification.edit_expiration ?? 'an unstated date'}, so the named ` +
        'fields can still be corrected in place.'];
    }
    return ['rejected-final',
      `rejected (${reasons}) and edit_allowed is false: a fresh submission is ` +
      'the only path, at the back of the review queue.'];
  }

  return ['unknown-status',
    `verification status is ${status || 'unset'}, which this script does not recognise.`];
}

function authHeader(key, secret) {
  return `Basic ${Buffer.from(`${key}:${secret}`).toString('base64')}`;
}

async function get(auth, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  const res = await fetch(u, { headers: { Authorization: auth } });
  if (res.status === 401 || res.status === 403) {
    throw new Error(`${res.status} from Twilio: check TWILIO_ACCOUNT_SID and ` +
                    'that the API key belongs to that account with read access');
  }
  if (!res.ok) throw new Error(`${res.status} from ${u.pathname}`);
  return res.json();
}

export async function listTollfree(auth, account, limit = 1000) {
  let url = `${BASE}/Accounts/${account}/IncomingPhoneNumbers/TollFree.json`;
  let params = { PageSize: 100 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.incoming_phone_numbers ?? []));
    url = page.next_page_uri ? HOST + page.next_page_uri : null;
    params = {};
  }
  return out.slice(0, limit);
}

export async function listVerifications(auth, limit = 1000) {
  const out = [];
  let next = `${MSG}/Tollfree/Verifications`;
  while (next && out.length < limit) {
    const page = await get(auth, next, { PageSize: 50 });
    out.push(...(page.verifications ?? []));
    next = page.meta?.next_page_url ?? null;
  }
  return out.slice(0, limit);
}

async function main() {
  const account = process.env.TWILIO_ACCOUNT_SID;
  const key = process.env.TWILIO_API_KEY;
  const secret = process.env.TWILIO_API_SECRET;
  if (!account || !key || !secret) {
    console.error('set TWILIO_ACCOUNT_SID, TWILIO_API_KEY and TWILIO_API_SECRET ' +
                  '(an API Key with read access, not the auth token)');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);

  const numbers = await listTollfree(auth, account);
  if (numbers.length === 0) {
    console.log('no toll-free numbers on this account');
    return;
  }

  const bySid = new Map();
  for (const record of await listVerifications(auth)) {
    const sid = record.tollfree_phone_number_sid;
    if (!bySid.has(sid)) bySid.set(sid, []);
    bySid.get(sid).push(record);
  }

  let bad = 0;
  for (const n of numbers) {
    const verification = pickVerification(bySid.get(n.sid) ?? []);
    const [state, detail] = verdict(n, verification);
    const line = `${state.padEnd(18)} ${n.phone_number ?? '?'}  ${detail}`;
    if (state === 'verified' || state === 'voice-only') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    if (state === 'unverified') {
      console.warn(`  repair: POST ${MSG}/Tollfree/Verifications with BusinessName, ` +
                   'BusinessWebsite, NotificationEmail, UseCaseCategories, ' +
                   'UseCaseSummary, ProductionMessageSample, OptInType, ' +
                   `OptInImageUrls, MessageVolume and TollfreePhoneNumberSid=${n.sid}`);
    } else if (state === 'rejected-editable') {
      console.warn(`  repair: POST ${MSG}/Tollfree/Verifications/` +
                   `${verification.sid ?? 'HH...'} correcting the named fields ` +
                   'before edit_expiration');
    } else if (state === 'blocked-in-review') {
      console.warn('  repair: none by API. Wait for TWILIO_APPROVED and do not route ' +
                   'production traffic through this number meanwhile');
    }
  }

  console.log(`${numbers.length} toll-free number(s), ${bad} blocked from US and CA SMS`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that carries this note is the one where a verification record exists and the number still cannot send: <code>PENDING_REVIEW</code> is a blocked state, and a check that treats the presence of a record as success reports a dead number as healthy. The other one worth pinning is a number with two records, because preferring the approved one over the newest is the difference between a true and a false alarm.",
"test_py_file": "test_twilio_tollfree_verification_audit.py",
"test_py": '''from twilio_tollfree_verification_audit import pick_verification, verdict

SMS = {"sid": "PN0123456789", "phone_number": "+18885551234",
       "capabilities": {"sms": True, "voice": True}}


def test_no_verification_record_is_the_headline_finding():
    state, detail = verdict(SMS, None)
    assert state == "unverified"
    assert "30032" in detail


def test_pending_review_is_blocked_not_progress():
    # The point of the note: filing is not passing.
    state, detail = verdict(SMS, {"status": "PENDING_REVIEW"})
    assert state == "blocked-in-review"
    assert "blocked outright" in detail


def test_approved_is_the_only_state_that_can_send():
    state, detail = verdict(SMS, {"status": "TWILIO_APPROVED", "sid": "HH0123456789"})
    assert state == "verified"
    assert "HH0123456789" in detail


def test_rejection_reasons_are_read_from_the_array():
    state, detail = verdict(SMS, {
        "status": "TWILIO_REJECTED", "edit_allowed": True,
        "edit_expiration": "2026-09-05T00:00:00Z",
        "rejection_reasons": [{"code": 30469,
                               "description": "Illegal substances or articles"}]})
    assert state == "rejected-editable"
    assert "30469" in detail
    assert "2026-09-05" in detail


def test_rejection_falls_back_to_the_prose_field():
    state, detail = verdict(SMS, {"status": "TWILIO_REJECTED", "edit_allowed": False,
                                  "rejection_reason": "opt-in evidence missing"})
    assert state == "rejected-final"
    assert "opt-in evidence missing" in detail


def test_a_voice_only_toll_free_number_is_not_a_finding():
    state, _ = verdict({"capabilities": {"sms": False, "voice": True}}, None)
    assert state == "voice-only"


def test_an_approved_record_wins_over_a_newer_rejection():
    records = [{"status": "TWILIO_APPROVED", "date_updated": "2026-01-01T00:00:00Z"},
               {"status": "TWILIO_REJECTED", "date_updated": "2026-06-01T00:00:00Z"}]
    assert pick_verification(records)["status"] == "TWILIO_APPROVED"


def test_without_an_approval_the_newest_record_governs():
    records = [{"status": "TWILIO_REJECTED", "date_updated": "2026-01-01T00:00:00Z"},
               {"status": "PENDING_REVIEW", "date_updated": "2026-06-01T00:00:00Z"}]
    assert pick_verification(records)["status"] == "PENDING_REVIEW"
    assert pick_verification([]) is None
''',
"test_js_file": "twilio-tollfree-verification-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { pickVerification, verdict } from './twilio-tollfree-verification-audit.mjs';

const SMS = { sid: 'PN0123456789', phone_number: '+18885551234',
              capabilities: { sms: true, voice: true } };

test('no verification record is the headline finding', () => {
  const [state, detail] = verdict(SMS, null);
  assert.equal(state, 'unverified');
  assert.match(detail, /30032/);
});

test('pending review is blocked, not progress', () => {
  const [state, detail] = verdict(SMS, { status: 'PENDING_REVIEW' });
  assert.equal(state, 'blocked-in-review');
  assert.match(detail, /blocked outright/);
});

test('approved is the only state that can send', () => {
  const [state, detail] = verdict(SMS, { status: 'TWILIO_APPROVED',
                                         sid: 'HH0123456789' });
  assert.equal(state, 'verified');
  assert.match(detail, /HH0123456789/);
});

test('rejection reasons are read from the array', () => {
  const [state, detail] = verdict(SMS, {
    status: 'TWILIO_REJECTED', edit_allowed: true,
    edit_expiration: '2026-09-05T00:00:00Z',
    rejection_reasons: [{ code: 30469, description: 'Illegal substances or articles' }],
  });
  assert.equal(state, 'rejected-editable');
  assert.match(detail, /30469/);
  assert.match(detail, /2026-09-05/);
});

test('rejection falls back to the prose field', () => {
  const [state, detail] = verdict(SMS, { status: 'TWILIO_REJECTED',
                                         edit_allowed: false,
                                         rejection_reason: 'opt-in evidence missing' });
  assert.equal(state, 'rejected-final');
  assert.match(detail, /opt-in evidence missing/);
});

test('a voice only toll free number is not a finding', () => {
  assert.equal(verdict({ capabilities: { sms: false, voice: true } }, null)[0],
               'voice-only');
});

test('an approved record wins over a newer rejection', () => {
  const records = [{ status: 'TWILIO_APPROVED', date_updated: '2026-01-01T00:00:00Z' },
                   { status: 'TWILIO_REJECTED', date_updated: '2026-06-01T00:00:00Z' }];
  assert.equal(pickVerification(records).status, 'TWILIO_APPROVED');
});

test('without an approval the newest record governs', () => {
  const records = [{ status: 'TWILIO_REJECTED', date_updated: '2026-01-01T00:00:00Z' },
                   { status: 'PENDING_REVIEW', date_updated: '2026-06-01T00:00:00Z' }];
  assert.equal(pickVerification(records).status, 'PENDING_REVIEW');
  assert.equal(pickVerification([]), null);
});
''',
"faq": [
 ("Is an unverified toll-free number throttled or blocked?",
  "Blocked. Before 31 January 2024 unverified toll-free traffic to US and Canadian mobiles was throttled, which is why so many teams remember getting test messages through. Since then it is blocked outright, and every attempt returns 30032 while still being billed."),
 ("We filed the verification. Why is it still failing?",
  "Because PENDING_REVIEW and IN_REVIEW are blocked states, exactly like having filed nothing. Only TWILIO_APPROVED can send. That is the single most common way this check goes wrong: treating the existence of a verification record as success."),
 ("Is toll-free still easier than 10DLC?",
  "It is a different registration, not the absence of one. There is no brand, no campaign and no EIN, but there is a mandatory verification with its own review and its own rejection codes. What toll-free still gives you is higher throughput and no per-campaign vetting fee."),
 ("What if the verification was rejected?",
  "Read rejection_reasons[] and error_code before touching anything, then check edit_allowed and edit_expiration. If editing is still allowed, correcting the named fields in place is far faster than a fresh submission. Some categories are rejected structurally and no edit will pass."),
 ("Why join two APIs instead of reading one field on the number?",
  "Because the number resource carries no verification state. The numbers live on the 2010-04-01 account API, the verifications on messaging.twilio.com/v1 keyed by tollfree_phone_number_sid, and the finding only exists where the two meet."),
],
"related": [
 ("/twilio/a2p-campaign-stuck-in-progress/", "A campaign parked at IN_PROGRESS is not live"),
 ("/twilio/a2p-campaign-vetting-failed/", "A campaign is FAILED and errors[] names the field"),
 ("/twilio/messaging-service-not-a2p-registered/", "A Messaging Service with no A2P campaign"),
],
"citations": [CITE_TF, CITE_30032, CITE_SERVICE, CITE_KEYS],
},

]
