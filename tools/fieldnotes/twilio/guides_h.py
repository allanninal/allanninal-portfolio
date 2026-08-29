#!/usr/bin/env python3
"""/twilio/ field notes, batch H — the writing.

Four Verify and Lookup failures. Two of them are fraud arriving (a country whose
conversion rate falls off a cliff, a Service with no rate limits to stop it), one
is the defence overreacting (Fraud Guard blocking a prefix your real users live
on), and one is a destination that was never going to receive an SMS at all.

Read-only throughout: an API Key with read access, never the account auth token,
and the repair is printed for a human to run. Verify spends money on every
attempt, which is exactly why a credential pointed at it should not be able to
start one.
"""

CITE_SUMMARY = ("Verification Attempts Summary resource — Twilio Docs",
                "https://www.twilio.com/docs/verify/api/verification-attempts-summary")
CITE_TOLLFRAUD = ("Preventing toll fraud and SMS pumping — Twilio Docs",
                  "https://www.twilio.com/docs/verify/preventing-toll-fraud")
CITE_RATELIMITS = ("Verify Service Rate Limits — Twilio Docs",
                   "https://www.twilio.com/docs/verify/api/service-rate-limits")
CITE_BUCKETS = ("Verify Rate Limit Buckets — Twilio Docs",
                "https://www.twilio.com/docs/verify/api/service-rate-limit-buckets")
CITE_VSERVICE = ("Verify Service resource — Twilio Docs",
                 "https://www.twilio.com/docs/verify/api/service")
CITE_60410 = ("Error 60410: verification delivery attempt blocked — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/60410")
CITE_60205 = ("Error 60205: SMS is not supported by landline phone number — Twilio Docs",
              "https://www.twilio.com/docs/api/errors/60205")
CITE_PUMPRISK = ("Lookup v2 SMS Pumping Risk — Twilio Docs",
                 "https://www.twilio.com/docs/lookup/v2-api/sms-pumping-risk")
CITE_LTI = ("Lookup v2 Line Type Intelligence — Twilio Docs",
            "https://www.twilio.com/docs/lookup/v2-api/line-type-intelligence")
CITE_KEYS = ("API keys — Twilio Docs", "https://www.twilio.com/docs/iam/api-keys")

GUIDES = [

{
"slug": "verify-conversion-rate-collapse",
"title": "Verify conversion collapses in one country: SMS pumping",
"description": "Verify spend jumps, mostly to one country, and almost none of those codes are ever entered. No error code: the sends succeed and are billed.",
"h1": "Verify conversion collapses in one country: SMS pumping",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio verify sms pumping", "verify conversion rate drop",
             "artificially inflated traffic twilio", "verify attempts summary",
             "twilio otp fraud spend"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The Verify bill for the month is five times last month's. Nothing is failing: no <code>4xx</code>, no error code, no delivery problem, no support tickets. The sends are being accepted, delivered and charged exactly as designed. The only thing that changed is that in one country almost nobody types the code in any more &mdash; and that single number is the difference between a growth spurt and somebody quietly farming your signup form.",
"short_answer": """<p>Read <code>GET https://verify.twilio.com/v2/Attempts/Summary?VerifyServiceSid={VA...}&amp;DateCreatedAfter={ISO8601}</code> once with no country filter to get the service baseline, then once per country with <code>&amp;Country={ISO2}</code>. Compare each country's <code>conversion_rate_percentage</code> against that baseline on non-trivial <code>total_attempts</code>.</p>
<p>A country sitting far below the baseline while its volume climbs is SMS pumping in progress: the OTP is delivered and billed, and nobody was ever going to enter it. Drill in with <code>GET https://verify.twilio.com/v2/Attempts?Status=unconverted&amp;Country={ISO2}</code> and read <code>channel_data.to</code> and <code>price</code>.</p>""",
"problem": """<p>SMS pumping, or artificially inflated traffic, works because your signup form is a free trigger for a paid event. A fraudster with access to revenue share on a set of carrier ranges drives your public OTP endpoint with numbers on those ranges. Twilio sends the message, the carrier delivers it, the carrier's share of the termination fee is collected, and you are invoiced. Every step is a success. There is no error code anywhere in this, because nothing went wrong.</p>
<p>What that means practically is that every alert you have is pointed at the wrong signal. Delivery rate: healthy. Error counts: unchanged. Latency: fine. The volume graph goes up, which in most companies is the graph that makes people happy. The only place the attack is visible is in the ratio between codes sent and codes entered, and that ratio lives in a summary endpoint most accounts have never called.</p>
<p>The other reason it survives is that the account-wide number barely moves. Ten thousand genuine verifications at 65% conversion plus two thousand pumped ones at 1% still averages out near 54% &mdash; a slide you can talk yourself out of. Split by country, the same data says one prefix converts at 1% on rising volume, which is not a number anybody talks themselves out of.</p>""",
"why": """<p><strong>The sends succeed, so error-based monitoring is blind.</strong> There is no <code>error_code</code> for a message somebody chose not to read. The verification is created, delivered, priced and left <code>pending</code> until it expires. Anything that watches for failures will watch this happen for a month without a word.</p>
<p><strong>Conversion rate is the only signal, and it is only useful split by country.</strong> Verify exposes <code>conversion_rate_percentage</code> alongside <code>total_attempts</code>, <code>total_converted</code> and <code>total_unconverted</code>. Aggregated over the account it is a slow-moving average that hides the attack; filtered by <code>Country</code>, the attacked prefix separates from everything else immediately.</p>
<p><strong>The comparison has to be relative, not a fixed threshold.</strong> A service doing web signups may convert at 70%, one bolted onto a lapsed re-engagement flow at 25%. Alerting on "below 40%" fires constantly on the second and never on the first. Comparing each country against that service's own baseline works for both.</p>
<p><strong>Small samples are noise, not evidence.</strong> Three attempts and one conversion is 33%, and it means nothing. Without a volume floor the report is dominated by countries where four people signed up, and the finding that matters is buried under them.</p>
<p><strong>The bill arrives a month after the traffic.</strong> Pumping is priced per attempt at international OTP rates, and it is discovered at invoice time by default. A conversion check running daily turns a five-figure surprise into an afternoon.</p>""",
"steps": [
 {"h": "Fetch the service baseline first",
  "body": """<p><code>GET https://verify.twilio.com/v2/Attempts/Summary?VerifyServiceSid={VA...}&amp;DateCreatedAfter={ISO8601}</code> with no <code>Country</code>. That response is the yardstick: <code>conversion_rate_percentage</code> over the whole window. Choose a window long enough to be stable &mdash; seven to thirty days &mdash; because a baseline computed over a bad afternoon judges everything against the attack.</p>"""},
 {"h": "Repeat the summary per country",
  "body": """<p>Add <code>&amp;Country={ISO2}</code> and read the same four fields. Countries you already serve are the obvious set; the interesting ones are the countries that only appeared this week, which you can enumerate from <code>GET https://verify.twilio.com/v2/Attempts?Status=unconverted&amp;DateCreatedAfter={ISO8601}</code>.</p>"""},
 {"h": "Judge against the baseline, with a volume floor",
  "body": """<p>Flag a country whose conversion rate is a small fraction of the baseline on more than a few dozen attempts. The fraction is the diagnosis: at a fifth of baseline the messages are being delivered to people who are not signing up, and the only question left is who is paying for them.</p>"""},
 {"h": "Drill into the unconverted attempts",
  "body": """<p><code>GET https://verify.twilio.com/v2/Attempts?Status=unconverted&amp;Country={ISO2}&amp;DateCreatedAfter={ISO8601}</code> gives you <code>channel_data.to</code> and <code>price</code> per attempt. Group the numbers by their leading digits. Pumping concentrates on a handful of prefixes inside a country, and those prefixes are what you feed into the repair.</p>"""},
 {"h": "Cut off the trigger, then re-run",
  "body": """<p>Enable Fraud Guard on the Service's SMS channel in the Console, restrict Geo Permissions to the countries you actually serve, and add Service Rate Limits keyed on IP or user so one client cannot start a thousand verifications. Re-run the summary the next day: the flagged country's conversion rate should climb back toward baseline as the pumped traffic stops.</p>"""},
],
"verify": """<p>Re-run the script. Every country should come back at or near the service baseline, and the collapse count should be zero.</p>
<pre><code class="language-bash">python3 twilio_verify_conversion_audit.py --days 7
# baseline 64.1% over 9,204 attempts
# 6 country(s) checked, 0 collapsed</code></pre>""",
"code_intro": "The script reads the summary once for the baseline and once per country, plus one page of unconverted attempts to find which countries are worth asking about &mdash; all GETs, so an API Key with read access is enough. The comparison itself is a pure function: a country is judged against the service's own baseline rather than a fixed threshold, and only above a volume floor, because those two rules are the whole difference between a useful report and a page of noise.",
"py_file": "twilio_verify_conversion_audit.py",
"py": '''"""Find Verify countries whose conversion rate has collapsed against the baseline.

A collapse in one country on rising volume is SMS pumping in progress: the OTP
is delivered and billed, and nobody was ever going to enter it.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed,
because this script holds a credential to an account that can start billable
verifications.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_verify_conversion_audit")

VERIFY = "https://verify.twilio.com/v2"

# A country is only judged once it has this many attempts in the window. Three
# attempts and one conversion is 33%, and it means nothing at all.
MIN_ATTEMPTS = 40

# Fractions of the service baseline, not absolute rates. A service doing web
# signups converts near 70%; one attached to a re-engagement flow near 25%. Any
# fixed threshold is wrong for one of them.
COLLAPSE_RATIO = 0.35
WATCH_RATIO = 0.70


def conversion_rate(row):
    """Conversion rate for one summary row, as a percentage or None.

    Prefers conversion_rate_percentage as returned, and falls back to the counts
    so the function still works on a row assembled from total_converted and
    total_attempts alone.
    """
    pct = row.get("conversion_rate_percentage")
    if pct is not None:
        return float(pct)
    total = int(row.get("total_attempts") or 0)
    if total <= 0:
        return None
    return 100.0 * float(row.get("total_converted") or 0) / total


def verdict(row, baseline, min_attempts=MIN_ATTEMPTS):
    """Classify one country's summary against the service baseline.

    Pure, so the two rules that matter -- relative to baseline, and only above a
    volume floor -- can be tested without a network.

    Returns (state, detail).
    """
    attempts = int(row.get("total_attempts") or 0)
    country = row.get("country") or "??"

    if attempts <= 0:
        return ("no-traffic", "no attempts in the window")

    if baseline is None or baseline <= 0:
        return ("no-baseline",
                "the service baseline is zero or missing, so nothing can be "
                "compared against it: widen the window before reading this run")

    rate = conversion_rate(row)
    if rate is None:
        return ("no-baseline", "no conversion rate on the row")

    ratio = rate / baseline
    shape = ("%s: %.1f%% conversion against a %.1f%% baseline on %d attempts"
             % (country, rate, baseline, attempts))

    if attempts < min_attempts:
        return ("thin",
                "%s, below the %d attempt floor: too few to read as anything"
                % (shape, min_attempts))

    if ratio <= COLLAPSE_RATIO:
        return ("collapse",
                "%s (%.0f%% of baseline). The sends succeeded and were billed, "
                "and nobody entered the code: that is the shape of SMS pumping, "
                "not a broken integration." % (shape, ratio * 100))

    if ratio <= WATCH_RATIO:
        return ("watch",
                "%s (%.0f%% of baseline). Below the service, not yet at collapse: "
                "worth a second window before acting." % (shape, ratio * 100))

    return ("healthy", "%s (%.0f%% of baseline)" % (shape, ratio * 100))


def prefix_of(number, digits=6):
    """Leading digits of an E.164 number. Pumping concentrates on a few ranges
    inside a country, and the prefix is what the repair is written against.
    """
    n = "".join(c for c in str(number or "") if c.isdigit())
    return ("+" + n[:digits]) if n else "?"


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def summary(session, service, since, country=None):
    params = {"VerifyServiceSid": service, "DateCreatedAfter": since}
    if country:
        params["Country"] = country
    return get(session, VERIFY + "/Attempts/Summary", **params)


def unconverted(session, service, since, limit=1000):
    """One bounded sweep of unconverted attempts, used for two things: which
    countries are worth asking the summary about, and which prefixes inside them
    are carrying the traffic.
    """
    url = VERIFY + "/Attempts"
    params = {"VerifyServiceSid": service, "Status": "unconverted",
              "DateCreatedAfter": since, "PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("attempts", []))
        nxt = (page.get("meta") or {}).get("next_page_url")
        url, params = nxt, {}
    return out[:limit]


def countries_seen(attempts):
    """Countries in the unconverted sweep, most recent traffic first."""
    seen = {}
    for a in attempts:
        code = a.get("country")
        if not code:
            continue
        seen[code] = seen.get(code, 0) + 1
    return [c for c, _ in sorted(seen.items(), key=lambda kv: -kv[1])]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--service", required=True, help="Verify Service SID (VA...)")
    ap.add_argument("--days", type=int, default=7, help="window to summarise")
    ap.add_argument("--country", action="append", default=[],
                    help="ISO 3166-1 alpha-2 code; repeatable. Default: the "
                         "countries seen in unconverted attempts")
    ap.add_argument("--min-attempts", type=int, default=MIN_ATTEMPTS,
                    help="volume floor below which a rate is not read")
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

    since = (dt.datetime.now(dt.timezone.utc)
             - dt.timedelta(days=args.days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    base_row = summary(session, args.service, since)
    baseline = conversion_rate(base_row)
    log.info("baseline %.1f%% over %s attempts",
             baseline or 0.0, base_row.get("total_attempts", 0))

    attempts = unconverted(session, args.service, since)
    countries = args.country or countries_seen(attempts)
    if not countries:
        log.info("no countries to check in the last %d day(s)", args.days)
        return 0

    bad = 0
    for code in countries:
        row = summary(session, args.service, since, country=code)
        row.setdefault("country", code)
        state, detail = verdict(row, baseline, args.min_attempts)
        line = "%-10s %s" % (state, detail)
        if state in ("collapse", "watch"):
            bad += state == "collapse"
            log.warning(line)
            hot = {}
            for a in attempts:
                if a.get("country") == code:
                    p = prefix_of((a.get("channel_data") or {}).get("to"))
                    hot[p] = hot.get(p, 0) + 1
            for p, n in sorted(hot.items(), key=lambda kv: -kv[1])[:3]:
                log.warning("  %s x%d unconverted", p, n)
            log.warning("  repair: Console > Verify > Services > %s > SMS: "
                        "enable Fraud Guard, restrict Geo Permissions to the "
                        "countries you serve, and add an IP-keyed Service Rate "
                        "Limit", args.service)
        else:
            log.info(line)

    log.info("%d country(s) checked, %d collapsed", len(countries), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-verify-conversion-audit.mjs",
"js": '''/**
 * Find Verify countries whose conversion rate has collapsed against the baseline.
 *
 * A collapse in one country on rising volume is SMS pumping in progress: the OTP
 * is delivered and billed, and nobody was ever going to enter it.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const VERIFY = 'https://verify.twilio.com/v2';

// A country is only judged once it has this many attempts in the window.
export const MIN_ATTEMPTS = 40;

// Fractions of the service baseline, not absolute rates: any fixed threshold is
// wrong for either a 70% signup service or a 25% re-engagement one.
const COLLAPSE_RATIO = 0.35;
const WATCH_RATIO = 0.70;

/**
 * Conversion rate for one summary row, as a percentage or null. Falls back to
 * the counts so a row assembled from total_converted and total_attempts works.
 */
export function conversionRate(row) {
  const pct = row.conversion_rate_percentage;
  if (pct !== undefined && pct !== null) return Number(pct);
  const total = Number(row.total_attempts ?? 0);
  if (total <= 0) return null;
  return (100 * Number(row.total_converted ?? 0)) / total;
}

/**
 * Classify one country's summary against the service baseline. Pure, so the two
 * rules that matter -- relative to baseline, and only above a volume floor --
 * can be tested without a network. Returns [state, detail].
 */
export function verdict(row, baseline, minAttempts = MIN_ATTEMPTS) {
  const attempts = Number(row.total_attempts ?? 0);
  const country = row.country ?? '??';

  if (attempts <= 0) return ['no-traffic', 'no attempts in the window'];

  if (baseline === null || baseline === undefined || baseline <= 0) {
    return ['no-baseline',
      'the service baseline is zero or missing, so nothing can be compared ' +
      'against it: widen the window before reading this run'];
  }

  const rate = conversionRate(row);
  if (rate === null) return ['no-baseline', 'no conversion rate on the row'];

  const ratio = rate / baseline;
  const shape = `${country}: ${rate.toFixed(1)}% conversion against a ` +
                `${baseline.toFixed(1)}% baseline on ${attempts} attempts`;

  if (attempts < minAttempts) {
    return ['thin',
      `${shape}, below the ${minAttempts} attempt floor: too few to read as ` +
      'anything'];
  }

  if (ratio <= COLLAPSE_RATIO) {
    return ['collapse',
      `${shape} (${Math.round(ratio * 100)}% of baseline). The sends succeeded ` +
      'and were billed, and nobody entered the code: that is the shape of SMS ' +
      'pumping, not a broken integration.'];
  }

  if (ratio <= WATCH_RATIO) {
    return ['watch',
      `${shape} (${Math.round(ratio * 100)}% of baseline). Below the service, ` +
      'not yet at collapse: worth a second window before acting.'];
  }

  return ['healthy', `${shape} (${Math.round(ratio * 100)}% of baseline)`];
}

/** Leading digits of an E.164 number: pumping concentrates on a few ranges. */
export function prefixOf(number, digits = 6) {
  const n = String(number ?? '').replace(/\\D/g, '');
  return n ? `+${n.slice(0, digits)}` : '?';
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

async function summary(auth, service, since, country) {
  const params = { VerifyServiceSid: service, DateCreatedAfter: since };
  if (country) params.Country = country;
  return get(auth, `${VERIFY}/Attempts/Summary`, params);
}

async function unconverted(auth, service, since, limit = 1000) {
  let url = `${VERIFY}/Attempts`;
  let params = { VerifyServiceSid: service, Status: 'unconverted',
                 DateCreatedAfter: since, PageSize: 100 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.attempts ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

/** Countries in the unconverted sweep, busiest first. */
export function countriesSeen(attempts) {
  const seen = new Map();
  for (const a of attempts) {
    if (!a.country) continue;
    seen.set(a.country, (seen.get(a.country) ?? 0) + 1);
  }
  return [...seen.entries()].sort((x, y) => y[1] - x[1]).map(([c]) => c);
}

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i === -1 ? fallback : process.argv[i + 1];
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
  const service = arg('--service');
  if (!service) {
    console.error('pass --service VA...');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);
  const days = Number(arg('--days', '7'));
  const since = new Date(Date.now() - days * 86400000).toISOString()
    .replace(/\\.\\d+Z$/, 'Z');

  const baseRow = await summary(auth, service, since);
  const baseline = conversionRate(baseRow);
  console.log(`baseline ${(baseline ?? 0).toFixed(1)}% over ` +
              `${baseRow.total_attempts ?? 0} attempts`);

  const attempts = await unconverted(auth, service, since);
  const countries = countriesSeen(attempts);
  if (countries.length === 0) {
    console.log(`no countries to check in the last ${days} day(s)`);
    return;
  }

  let bad = 0;
  for (const code of countries) {
    const row = await summary(auth, service, since, code);
    if (!row.country) row.country = code;
    const [state, detail] = verdict(row, baseline);
    const line = `${state.padEnd(10)} ${detail}`;
    if (state === 'collapse' || state === 'watch') {
      if (state === 'collapse') bad += 1;
      console.warn(line);
      const hot = new Map();
      for (const a of attempts) {
        if (a.country !== code) continue;
        const p = prefixOf(a.channel_data?.to);
        hot.set(p, (hot.get(p) ?? 0) + 1);
      }
      for (const [p, n] of [...hot.entries()].sort((x, y) => y[1] - x[1]).slice(0, 3)) {
        console.warn(`  ${p} x${n} unconverted`);
      }
      console.warn(`  repair: Console > Verify > Services > ${service} > SMS: ` +
                   'enable Fraud Guard, restrict Geo Permissions to the countries ' +
                   'you serve, and add an IP-keyed Service Rate Limit');
    } else {
      console.log(line);
    }
  }

  console.log(`${countries.length} country(s) checked, ${bad} collapsed`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones that separate a real collapse from a number that merely looks bad: the same 4% conversion is a finding on eight hundred attempts and nothing at all on nine, and a country at 9% is healthy on a service whose own baseline is 11%. The last test is the one that stops the report from being a list of every country where four people signed up.",
"test_py_file": "test_twilio_verify_conversion_audit.py",
"test_py": '''from twilio_verify_conversion_audit import conversion_rate, prefix_of, verdict


def test_country_far_below_baseline_on_volume_is_a_collapse():
    row = {"country": "ID", "total_attempts": 812, "total_converted": 25,
           "conversion_rate_percentage": 3.1}
    state, detail = verdict(row, 64.0)
    assert state == "collapse"
    assert "pumping" in detail


def test_same_rate_on_nine_attempts_is_too_thin_to_read():
    # The volume floor is what keeps the report free of countries where four
    # people signed up this week.
    row = {"country": "MT", "total_attempts": 9, "total_converted": 0,
           "conversion_rate_percentage": 0.0}
    state, detail = verdict(row, 64.0)
    assert state == "thin"
    assert "floor" in detail


def test_judgement_is_relative_so_a_low_baseline_service_still_works():
    # 9% would trip any fixed threshold, and on this service it is normal.
    row = {"country": "BR", "total_attempts": 400, "total_converted": 36,
           "conversion_rate_percentage": 9.0}
    assert verdict(row, 11.0)[0] == "healthy"
    # Same service, a country at a fifth of that baseline.
    hit = {"country": "PK", "total_attempts": 400, "total_converted": 8,
           "conversion_rate_percentage": 2.0}
    assert verdict(hit, 11.0)[0] == "collapse"


def test_middling_country_is_watch_not_collapse():
    row = {"country": "PL", "total_attempts": 300, "total_converted": 120,
           "conversion_rate_percentage": 40.0}
    assert verdict(row, 64.0)[0] == "watch"


def test_rate_is_derived_from_the_counts_when_the_percentage_is_absent():
    assert conversion_rate({"total_attempts": 200, "total_converted": 50}) == 25.0
    assert conversion_rate({"total_attempts": 0, "total_converted": 0}) is None


def test_missing_baseline_refuses_to_judge():
    row = {"country": "US", "total_attempts": 500, "conversion_rate_percentage": 2.0}
    state, detail = verdict(row, None)
    assert state == "no-baseline"
    assert "widen the window" in detail


def test_prefix_keeps_the_leading_digits_only():
    assert prefix_of("+62 812-3456-7890") == "+628123"
    assert prefix_of(None) == "?"
''',
"test_js_file": "twilio-verify-conversion-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { conversionRate, prefixOf, verdict } from './twilio-verify-conversion-audit.mjs';

test('country far below baseline on volume is a collapse', () => {
  const [state, detail] = verdict(
    { country: 'ID', total_attempts: 812, total_converted: 25,
      conversion_rate_percentage: 3.1 }, 64.0);
  assert.equal(state, 'collapse');
  assert.match(detail, /pumping/);
});

test('same rate on nine attempts is too thin to read', () => {
  const [state, detail] = verdict(
    { country: 'MT', total_attempts: 9, total_converted: 0,
      conversion_rate_percentage: 0 }, 64.0);
  assert.equal(state, 'thin');
  assert.match(detail, /floor/);
});

test('judgement is relative so a low baseline service still works', () => {
  assert.equal(verdict(
    { country: 'BR', total_attempts: 400, total_converted: 36,
      conversion_rate_percentage: 9.0 }, 11.0)[0], 'healthy');
  assert.equal(verdict(
    { country: 'PK', total_attempts: 400, total_converted: 8,
      conversion_rate_percentage: 2.0 }, 11.0)[0], 'collapse');
});

test('middling country is watch not collapse', () => {
  assert.equal(verdict(
    { country: 'PL', total_attempts: 300, total_converted: 120,
      conversion_rate_percentage: 40.0 }, 64.0)[0], 'watch');
});

test('rate is derived from the counts when the percentage is absent', () => {
  assert.equal(conversionRate({ total_attempts: 200, total_converted: 50 }), 25);
  assert.equal(conversionRate({ total_attempts: 0, total_converted: 0 }), null);
});

test('missing baseline refuses to judge', () => {
  const [state, detail] = verdict(
    { country: 'US', total_attempts: 500, conversion_rate_percentage: 2.0 }, null);
  assert.equal(state, 'no-baseline');
  assert.match(detail, /widen the window/);
});

test('prefix keeps the leading digits only', () => {
  assert.equal(prefixOf('+62 812-3456-7890'), '+628123');
  assert.equal(prefixOf(null), '?');
});
''',
"faq": [
 ("There is no error code, so what exactly am I detecting?",
  "The absence of a second event. Every pumped verification is a successful, billed send whose code is never checked. Verify records that as an unconverted attempt, and the Attempts Summary turns it into conversion_rate_percentage. That ratio is the only signal, because nothing in the send path failed."),
 ("Why compare against the service baseline instead of a fixed percentage?",
  "Because conversion rate is a property of your funnel, not of the platform. A web signup flow sits near 70%, a reactivation flow near 25%. A fixed threshold either alarms constantly on the second or never fires on the first. Each country measured against its own service's baseline behaves correctly on both."),
 ("Could a collapse be a broken integration rather than fraud?",
  "It can, and the country split is what separates them. A broken check endpoint, an OTP field that eats the code, an expired deep link: those depress conversion everywhere at once. Pumping depresses it in one or two countries while the rest of the service stays exactly where it was."),
 ("Why a volume floor of forty attempts?",
  "Because below it the rate is a coin toss. One conversion out of three is 33% and carries no information. Forty is low enough to catch an attack in its first hours and high enough that the report is not dominated by countries with a handful of genuine signups."),
 ("Can the script turn on Fraud Guard once it finds this?",
  "No, and not only because it is read-only: Fraud Guard's enable state has no read or write API at all. It is a Console setting on the Service's SMS channel. The script prints where to go and what else to add alongside it, which is Geo Permissions and a rate limit keyed on something you control."),
],
"related": [
 ("/twilio/verify-no-rate-limits/", "A Verify Service with no rate limits at all"),
 ("/twilio/fraud-guard-blocking-prefix/", "Fraud Guard blocking a prefix your users live on"),
 ("/twilio/sms-pumping-protection-30450/", "SMS Pumping Protection blocking legitimate OTPs"),
],
"citations": [CITE_SUMMARY, CITE_TOLLFRAUD, CITE_RATELIMITS, CITE_KEYS],
},

{
"slug": "verify-no-rate-limits",
"title": "A Verify Service with zero rate limits configured",
"description": "Verify's built-in protection is per phone number only. With no Service Rate Limits, one script rotating destinations from one IP is entirely unthrottled.",
"h1": "a Verify Service with zero rate limits configured",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio verify rate limits", "verify service rate limit buckets",
             "twilio 60212", "twilio 20429 verify",
             "unbounded verification spend"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Verify looks protected. There is a limit on how often one phone number can be sent a code, and you have seen <code>60212</code> in the logs, so something is clearly throttling something. Then a scripted signup endpoint sends ten thousand verifications to ten thousand different numbers from a single host, hits no limit at all, and the invoice explains why: the protection you were relying on is keyed on the destination, and the attacker changes the destination every time.",
"short_answer": """<p>Read <code>GET https://verify.twilio.com/v2/Services/{ServiceSid}/RateLimits</code> and flag an empty <code>rate_limits[]</code>. Then, for each <code>RK...</code> that exists, read <code>GET https://verify.twilio.com/v2/Services/{ServiceSid}/RateLimits/{RateLimitSid}/Buckets</code> and flag an empty <code>buckets[]</code> &mdash; a Rate Limit with no buckets enforces nothing.</p>
<p>Verify's built-in platform protections are per phone number. Service Rate Limits are keyed on <em>your</em> identifier &mdash; IP, user ID, number prefix &mdash; and they are opt-in, so an attacker rotating destinations from one client is unthrottled until you create one.</p>""",
"problem": """<p>The dangerous part of this failure is that the account is not unprotected, it is protected against the wrong thing. Twilio does throttle repeated verifications to the same phone number, and that limit is real: it stops the retry loop, the impatient user hammering "resend", the double-firing form. What it does not stop, and was never meant to stop, is one client walking through a list of numbers it has never used before.</p>
<p>That is the exact shape of both attacks people run against a Verify endpoint. SMS pumping needs many distinct destinations, one message each. Enumeration and account probing need many distinct destinations, one message each. Neither one triggers a per-destination limit, because neither one repeats a destination.</p>
<p>And because the limits are opt-in, the configuration that leaves you exposed is the configuration you get by default. Nothing in the Console is red. The Service works. Verifications start, codes arrive, users log in. The finding is the absence of a resource, which is the one thing no dashboard shows you.</p>""",
"why": """<p><strong>Platform protection and Service Rate Limits solve different problems.</strong> The built-in guard is per phone number and always on. Service Rate Limits are per key of your choosing and off until you create them. Reading the first as coverage for the second is the mistake this note exists to catch.</p>
<p><strong>A Rate Limit with no buckets is inert.</strong> The <code>RateLimit</code> resource is a named key; the <code>Bucket</code> underneath is the actual <code>max</code> per <code>interval</code>. Creating the key and stopping there is a common half-finished state, and it reads as configured in a listing: the name is there, the SID is there, and nothing is enforced.</p>
<p><strong>Passing the key on send is the other half.</strong> A limit keyed on <code>end_user_ip</code> only applies when the verification start includes <code>RateLimits={"end_user_ip": "..."}</code>. The resource can be perfect and every request can bypass it because the field was never sent.</p>
<p><strong>Generous buckets look like limits and are not.</strong> A bucket of a thousand starts per minute per IP is a resource, a SID and a number, and it will never stop anything a script does. The audit has to read the arithmetic, not the existence.</p>
<p><strong>The cost of missing this is uncapped.</strong> Every verification is a billed message at international rates. There is no natural ceiling on the number of destinations in the world, so an unthrottled start endpoint is a wire from your card to whoever finds it first.</p>""",
"steps": [
 {"h": "List the Services, then the Rate Limits on each",
  "body": """<p><code>GET https://verify.twilio.com/v2/Services</code> for the inventory, then <code>GET https://verify.twilio.com/v2/Services/{ServiceSid}/RateLimits</code> per Service. An empty <code>rate_limits[]</code> is the headline finding: nothing beyond the per-destination platform guard applies to that Service.</p>"""},
 {"h": "Read the buckets under every limit",
  "body": """<p><code>GET https://verify.twilio.com/v2/Services/{ServiceSid}/RateLimits/{RateLimitSid}/Buckets</code>. Each bucket carries <code>max</code> and <code>interval</code>. No buckets means the limit exists in name only. This is the check that separates a Service that is configured from one that merely has resources in it.</p>"""},
 {"h": "Convert every bucket to starts per minute",
  "body": """<p><code>max / interval * 60</code> makes buckets comparable and makes generous ones obvious. Five per sixty seconds is five a minute. A thousand per sixty seconds is a resource that exists to be pointed at in a review. The tightest bucket across all limits is the one that actually binds.</p>"""},
 {"h": "Check that the key is being sent",
  "body": """<p>The audit cannot see this from the API, and it is where most half-working setups fail: the <code>RateLimits</code> parameter has to be passed on every verification start for the limit to apply. Grep the code that calls Verify for the unique name the Service defines. A limit nobody keys is the same as no limit.</p>"""},
 {"h": "Create the limit and its buckets, then re-run",
  "body": """<p>Create a limit with a <code>UniqueName</code> such as <code>end_user_ip</code>, then two buckets under it: a short one for bursts and a long one for the day's total. Re-run the audit and every Service should report a tightest bucket in starts per minute rather than <code>unlimited</code>.</p>"""},
],
"verify": """<p>Re-run the script. Every Service should report a bucket, and the unlimited count should be zero.</p>
<pre><code class="language-bash">python3 twilio_verify_rate_limit_audit.py
# 3 service(s), 0 with no effective limit</code></pre>""",
"code_intro": "One GET for the Services, one per Service for its limits, and one per limit for its buckets &mdash; read-only throughout, so give it an API Key with read access. The classifier is pure and takes the shape the API returns: it separates a Service with no limits from one whose limit has no buckets, because those look identical in a Console listing and only the second one has somebody halfway through the job.",
"py_file": "twilio_verify_rate_limit_audit.py",
"py": '''"""Report Verify Services with no effective rate limit on verification starts.

Verify's built-in protections are per destination phone number. Service Rate
Limits are keyed on your own identifier and are opt-in, so a script rotating
destinations from one IP is unthrottled until one exists.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_verify_rate_limit_audit")

VERIFY = "https://verify.twilio.com/v2"

# Above this, a bucket is a resource rather than a brake: no human signup flow
# needs thirty verification starts a minute from one key.
LOOSE_PER_MINUTE = 30.0


def starts_per_minute(bucket):
    """Normalise one bucket to starts per minute, or None if it is unreadable.

    Buckets are written in whatever interval suited the author -- 5 per 60s, 25
    per 3600s -- and cannot be compared until they are in the same unit.
    """
    try:
        max_ = float(bucket.get("max"))
        interval = float(bucket.get("interval"))
    except (TypeError, ValueError):
        return None
    if interval <= 0:
        return None
    return max_ * 60.0 / interval


def verdict(limits, loose_per_minute=LOOSE_PER_MINUTE):
    """Classify one Verify Service from its rate limits and their buckets.

    `limits` is a list of {"unique_name": str, "buckets": [{"max", "interval"}]},
    which is the two API responses joined. Pure, so the difference between no
    limits and a limit with no buckets can be tested without a network.

    Returns (state, detail).
    """
    if not limits:
        return ("unlimited",
                "no Service Rate Limits at all. The only protection is Twilio's "
                "per destination number guard, which does nothing against one "
                "client rotating through numbers it has not used before.")

    inert = [str(l.get("unique_name") or l.get("sid") or "?")
             for l in limits if not l.get("buckets")]
    live = [(l, b) for l in limits for b in (l.get("buckets") or [])]

    if not live:
        return ("inert",
                "%d rate limit(s) with no buckets: %s. The limit resource is a "
                "named key; the bucket underneath is the max per interval, so a "
                "limit without one enforces nothing."
                % (len(inert), ", ".join(inert)))

    rated = [(starts_per_minute(b), l, b) for l, b in live]
    rated = [r for r in rated if r[0] is not None]
    if not rated:
        return ("inert",
                "buckets present but none has a readable max and interval")

    rate, limit, bucket = min(rated, key=lambda r: r[0])
    tightest = ("tightest bucket is %s: %s per %ss (%.1f/min)"
                % (limit.get("unique_name") or limit.get("sid") or "?",
                   bucket.get("max"), bucket.get("interval"), rate))
    if inert:
        tightest += "; no buckets on " + ", ".join(inert)

    if rate > loose_per_minute:
        return ("loose",
                "%s, above %.0f/min. That is a resource, not a brake: a script "
                "will sit under it all day." % (tightest, loose_per_minute))

    return ("limited", tightest)


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def page(session, url, field, **params):
    """Walk a Verify v2 list. Paging lives in meta.next_page_url."""
    out = []
    while url:
        body = get(session, url, **params)
        out.extend(body.get(field, []))
        url, params = (body.get("meta") or {}).get("next_page_url"), {}
    return out


def limits_with_buckets(session, service_sid):
    """Join RateLimits to their Buckets: one GET per limit, and the join is the
    only way to tell a configured Service from one with an empty named key.
    """
    base = "%s/Services/%s/RateLimits" % (VERIFY, service_sid)
    out = []
    for limit in page(session, base, "rate_limits", PageSize=50):
        buckets = page(session, "%s/%s/Buckets" % (base, limit.get("sid")),
                       "buckets", PageSize=50)
        out.append({"sid": limit.get("sid"),
                    "unique_name": limit.get("unique_name"),
                    "buckets": buckets})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--service", action="append", default=[],
                    help="Verify Service SID; repeatable. Default: every service")
    ap.add_argument("--loose-per-minute", type=float, default=LOOSE_PER_MINUTE,
                    help="starts per minute above which a bucket is not a brake")
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

    if args.service:
        services = [{"sid": s, "friendly_name": s} for s in args.service]
    else:
        services = page(session, VERIFY + "/Services", "services", PageSize=50)
    if not services:
        log.info("no Verify services on this account")
        return 0

    bad = 0
    for svc in services:
        sid = svc.get("sid")
        limits = limits_with_buckets(session, sid)
        state, detail = verdict(limits, args.loose_per_minute)
        line = "%-9s %s (%s)  %s" % (state, svc.get("friendly_name", "?"), sid, detail)
        if state == "limited":
            log.info(line)
            continue
        bad += 1
        log.warning(line)
        log.warning("  repair: create %s/Services/%s/RateLimits with "
                    "UniqueName=end_user_ip, then a bucket Max=5 Interval=60 and "
                    "a second Max=25 Interval=3600", VERIFY, sid)
        log.warning("  then pass RateLimits={\\"end_user_ip\\": \\"<ip>\\"} on every "
                    "verification start, or the limit never applies")

    log.info("%d service(s), %d with no effective limit", len(services), bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-verify-rate-limit-audit.mjs",
"js": '''/**
 * Report Verify Services with no effective rate limit on verification starts.
 *
 * Verify's built-in protections are per destination phone number. Service Rate
 * Limits are keyed on your own identifier and are opt-in, so a script rotating
 * destinations from one IP is unthrottled until one exists.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const VERIFY = 'https://verify.twilio.com/v2';

// Above this, a bucket is a resource rather than a brake.
export const LOOSE_PER_MINUTE = 30;

/**
 * Normalise one bucket to starts per minute, or null if it is unreadable.
 * Buckets are written in whatever interval suited the author and cannot be
 * compared until they are in the same unit.
 */
export function startsPerMinute(bucket) {
  // Number(null) is 0, not NaN, so a missing max has to be rejected before the
  // arithmetic rather than after it.
  if (bucket?.max === null || bucket?.max === undefined) return null;
  if (bucket?.interval === null || bucket?.interval === undefined) return null;
  const max = Number(bucket.max);
  const interval = Number(bucket.interval);
  if (!Number.isFinite(max) || !Number.isFinite(interval) || interval <= 0) return null;
  return (max * 60) / interval;
}

/**
 * Classify one Verify Service from its rate limits and their buckets. `limits`
 * is the two API responses joined. Pure, so the difference between no limits and
 * a limit with no buckets can be tested without a network.
 * Returns [state, detail].
 */
export function verdict(limits, loosePerMinute = LOOSE_PER_MINUTE) {
  if (!limits || limits.length === 0) {
    return ['unlimited',
      'no Service Rate Limits at all. The only protection is Twilio\\'s per ' +
      'destination number guard, which does nothing against one client ' +
      'rotating through numbers it has not used before.'];
  }

  const inert = limits.filter((l) => !(l.buckets ?? []).length)
    .map((l) => l.unique_name ?? l.sid ?? '?');
  const live = limits.flatMap((l) => (l.buckets ?? []).map((b) => [l, b]));

  if (live.length === 0) {
    return ['inert',
      `${inert.length} rate limit(s) with no buckets: ${inert.join(', ')}. The ` +
      'limit resource is a named key; the bucket underneath is the max per ' +
      'interval, so a limit without one enforces nothing.'];
  }

  const rated = live.map(([l, b]) => [startsPerMinute(b), l, b])
    .filter(([r]) => r !== null);
  if (rated.length === 0) {
    return ['inert', 'buckets present but none has a readable max and interval'];
  }

  const [rate, limit, bucket] = rated.reduce((a, b) => (b[0] < a[0] ? b : a));
  let tightest = `tightest bucket is ${limit.unique_name ?? limit.sid ?? '?'}: ` +
                 `${bucket.max} per ${bucket.interval}s (${rate.toFixed(1)}/min)`;
  if (inert.length) tightest += `; no buckets on ${inert.join(', ')}`;

  if (rate > loosePerMinute) {
    return ['loose',
      `${tightest}, above ${loosePerMinute}/min. That is a resource, not a ` +
      'brake: a script will sit under it all day.'];
  }

  return ['limited', tightest];
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

/** Walk a Verify v2 list. Paging lives in meta.next_page_url. */
async function page(auth, url, field, params = {}) {
  const out = [];
  let next = url;
  let p = params;
  while (next) {
    const body = await get(auth, next, p);
    out.push(...(body[field] ?? []));
    next = body.meta?.next_page_url ?? null;
    p = {};
  }
  return out;
}

export async function limitsWithBuckets(auth, serviceSid) {
  const base = `${VERIFY}/Services/${serviceSid}/RateLimits`;
  const out = [];
  for (const limit of await page(auth, base, 'rate_limits', { PageSize: 50 })) {
    const buckets = await page(auth, `${base}/${limit.sid}/Buckets`, 'buckets',
                               { PageSize: 50 });
    out.push({ sid: limit.sid, unique_name: limit.unique_name, buckets });
  }
  return out;
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

  const services = await page(auth, `${VERIFY}/Services`, 'services', { PageSize: 50 });
  if (services.length === 0) {
    console.log('no Verify services on this account');
    return;
  }

  let bad = 0;
  for (const svc of services) {
    const limits = await limitsWithBuckets(auth, svc.sid);
    const [state, detail] = verdict(limits);
    const line = `${state.padEnd(9)} ${svc.friendly_name ?? '?'} (${svc.sid})  ${detail}`;
    if (state === 'limited') { console.log(line); continue; }
    bad += 1;
    console.warn(line);
    console.warn(`  repair: create ${VERIFY}/Services/${svc.sid}/RateLimits with ` +
                 'UniqueName=end_user_ip, then a bucket Max=5 Interval=60 and a ' +
                 'second Max=25 Interval=3600');
    console.warn('  then pass RateLimits={"end_user_ip": "<ip>"} on every ' +
                 'verification start, or the limit never applies');
  }

  console.log(`${services.length} service(s), ${bad} with no effective limit`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three states have to stay distinct, because in a Console listing they look the same: no limits, a limit whose bucket list is empty, and a bucket so generous that nothing will ever hit it. The last two tests cover the case that decides whether the report is trustworthy &mdash; a Service with one real bucket and one abandoned key is limited, and the abandoned key still gets named.",
"test_py_file": "test_twilio_verify_rate_limit_audit.py",
"test_py": '''from twilio_verify_rate_limit_audit import starts_per_minute, verdict


def test_no_rate_limits_at_all_is_the_headline_finding():
    state, detail = verdict([])
    assert state == "unlimited"
    assert "per destination number guard" in detail


def test_limit_with_no_buckets_enforces_nothing():
    state, detail = verdict([{"unique_name": "end_user_ip", "buckets": []}])
    assert state == "inert"
    assert "end_user_ip" in detail


def test_five_per_minute_is_a_real_brake():
    state, detail = verdict([{"unique_name": "end_user_ip",
                              "buckets": [{"max": 5, "interval": 60}]}])
    assert state == "limited"
    assert "5.0/min" in detail


def test_a_thousand_a_minute_is_a_resource_not_a_brake():
    state, detail = verdict([{"unique_name": "end_user_ip",
                              "buckets": [{"max": 1000, "interval": 60}]}])
    assert state == "loose"
    assert "all day" in detail


def test_tightest_bucket_across_limits_is_the_one_that_binds():
    state, detail = verdict([
        {"unique_name": "user_id", "buckets": [{"max": 600, "interval": 60}]},
        {"unique_name": "end_user_ip", "buckets": [{"max": 5, "interval": 60}]},
    ])
    assert state == "limited"
    assert "end_user_ip" in detail


def test_an_abandoned_key_is_named_even_when_another_limit_works():
    state, detail = verdict([
        {"unique_name": "end_user_ip", "buckets": [{"max": 5, "interval": 60}]},
        {"unique_name": "prefix", "buckets": []},
    ])
    assert state == "limited"
    assert "no buckets on prefix" in detail


def test_buckets_are_normalised_to_starts_per_minute():
    assert starts_per_minute({"max": 25, "interval": 3600}) == 25 * 60 / 3600
    assert starts_per_minute({"max": 5, "interval": 0}) is None
    assert starts_per_minute({"max": None, "interval": 60}) is None
''',
"test_js_file": "twilio-verify-rate-limit-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { startsPerMinute, verdict } from './twilio-verify-rate-limit-audit.mjs';

test('no rate limits at all is the headline finding', () => {
  const [state, detail] = verdict([]);
  assert.equal(state, 'unlimited');
  assert.match(detail, /per destination number guard/);
});

test('limit with no buckets enforces nothing', () => {
  const [state, detail] = verdict([{ unique_name: 'end_user_ip', buckets: [] }]);
  assert.equal(state, 'inert');
  assert.match(detail, /end_user_ip/);
});

test('five per minute is a real brake', () => {
  const [state, detail] = verdict([
    { unique_name: 'end_user_ip', buckets: [{ max: 5, interval: 60 }] }]);
  assert.equal(state, 'limited');
  assert.match(detail, /5\\.0\\/min/);
});

test('a thousand a minute is a resource not a brake', () => {
  const [state, detail] = verdict([
    { unique_name: 'end_user_ip', buckets: [{ max: 1000, interval: 60 }] }]);
  assert.equal(state, 'loose');
  assert.match(detail, /all day/);
});

test('tightest bucket across limits is the one that binds', () => {
  const [state, detail] = verdict([
    { unique_name: 'user_id', buckets: [{ max: 600, interval: 60 }] },
    { unique_name: 'end_user_ip', buckets: [{ max: 5, interval: 60 }] },
  ]);
  assert.equal(state, 'limited');
  assert.match(detail, /end_user_ip/);
});

test('an abandoned key is named even when another limit works', () => {
  const [state, detail] = verdict([
    { unique_name: 'end_user_ip', buckets: [{ max: 5, interval: 60 }] },
    { unique_name: 'prefix', buckets: [] },
  ]);
  assert.equal(state, 'limited');
  assert.match(detail, /no buckets on prefix/);
});

test('buckets are normalised to starts per minute', () => {
  assert.equal(startsPerMinute({ max: 25, interval: 3600 }), (25 * 60) / 3600);
  assert.equal(startsPerMinute({ max: 5, interval: 0 }), null);
  assert.equal(startsPerMinute({ max: null, interval: 60 }), null);
});
''',
"faq": [
 ("Twilio already rate limits verifications. Why do I need my own?",
  "Because the built-in protection is keyed on the destination phone number, and both attacks that matter use each destination once. Pumping needs many numbers, one message each; enumeration needs many numbers, one message each. Neither repeats a destination, so neither meets the per-number limit."),
 ("What is the difference between a Rate Limit and a Bucket?",
  "The Rate Limit is the named key you throttle on, such as end_user_ip or user_id. The Bucket underneath is the enforcement: max starts per interval seconds. A limit with no buckets is a name with nothing behind it, and it is the state a half-finished setup leaves behind."),
 ("Does creating the limit make it apply automatically?",
  "No. The verification start has to pass a value for the key, as RateLimits with your unique name and the caller's IP or user id. The resource and the request are two halves of the same control, and an audit can only see one of them, which is why the note tells you to grep your own code for the unique name."),
 ("What should the buckets actually be?",
  "Two per key works well: a short window that stops bursts, such as five per sixty seconds, and a longer one that caps the day, such as twenty-five per hour. The short one blocks a script; the long one blocks a script that has learned to wait."),
 ("Why flag a bucket that exists but is generous?",
  "Because it passes every review that checks for existence. A thousand starts per minute per IP is a number no human flow will ever reach, and a script will sit comfortably underneath it forever. Normalising every bucket to starts per minute is what makes that visible in one column."),
],
"related": [
 ("/twilio/verify-conversion-rate-collapse/", "Verify conversion collapsing in one country"),
 ("/twilio/fraud-guard-blocking-prefix/", "Fraud Guard blocking a prefix your users live on"),
 ("/twilio/sms-pumping-protection-30450/", "SMS Pumping Protection blocking legitimate OTPs"),
],
"citations": [CITE_RATELIMITS, CITE_BUCKETS, CITE_TOLLFRAUD, CITE_KEYS],
},

{
"slug": "fraud-guard-blocking-prefix",
"title": "Fraud Guard blocked the prefix, so real users get 60410",
"description": "One country cannot sign up for twelve hours. Fraud Guard saw pumping-shaped traffic on a prefix and blocked it, and legitimate users share that prefix.",
"h1": "Fraud Guard blocked the prefix, so real users get 60410",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 60410", "fraud guard blocked prefix",
             "verification delivery attempt blocked", "sms_pumping_risk lookup",
             "twilio number_blocked"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Support has four tickets from one country, all saying the same thing: the code never arrives. Your logs show <code>60410</code>, <em>verification delivery attempt blocked</em>. Nothing in the account changed, no carrier is down, and the numbers are ordinary mobiles. Fraud Guard is doing exactly what you asked it to do &mdash; it found pumping-shaped traffic on a number prefix and stopped sending there for twelve hours &mdash; and your real users happen to live on that prefix too.",
"short_answer": """<p>Sweep <code>GET https://verify.twilio.com/v2/Attempts?Status=unconverted&amp;DateCreatedAfter={ISO8601}</code> and group the attempts by <code>country</code> and by the leading digits of <code>channel_data.to</code>. Then confirm a sample number per prefix with <code>GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=sms_pumping_risk</code> and read <code>sms_pumping_risk.number_blocked</code>, <code>number_blocked_date</code>, <code>number_blocked_last_3_months</code>, <code>carrier_risk_category</code> and <code>sms_pumping_risk_score</code>.</p>
<p><code>number_blocked</code> <code>true</code> is the answer: the block is live, it lasts twelve hours, and it re-arms in twelve hour increments while the suspicious traffic continues. There is no API to lift it. The repair is to stop the traffic that caused it.</p>""",
"problem": """<p>This is the failure mode of a defence rather than of a bug, and it is uncomfortable in a specific way: the platform is right and your users are still locked out. Fraud Guard watched a prefix, saw the signature of artificially inflated traffic, and imposed a temporary block on SMS to that prefix. Prefixes are shared. The fraudster's numbers and your customers' numbers sit in the same carrier range, so the block that stops one stops the other.</p>
<p>From inside your application it presents as a hard stop with a code you cannot act on. <code>60410</code> is not a retry-later condition in any useful sense: retrying inside the window fails identically, and each retry is more traffic on the prefix that is being judged. The instinct to hammer the send until it works is the one behaviour that extends the block.</p>
<p>The other half of the difficulty is that Fraud Guard's state is not readable. There is no endpoint that reports "this prefix is currently blocked", no field on the Service, nothing in the Console API. Its enable state has no read API either. Everything you can learn about it read-only has to come from two other surfaces: the attempts that failed, and Lookup's view of the numbers involved.</p>""",
"why": """<p><strong>The block is on the prefix, not on the account or the user.</strong> That is why it looks so arbitrary from the application's side: one user in that range fails, another in the next range succeeds, and nothing about either account differs. Grouping failures by prefix is the step that turns a scatter of tickets into a single fact.</p>
<p><strong>Twelve hours, re-arming.</strong> The block expires on its own, and it is reapplied in further twelve hour increments as long as the pattern continues. An investigation that starts the morning after finds everything working, which is how this gets logged as a mystery and closed.</p>
<p><strong>There is no unblock API.</strong> Nothing you can call clears it. The only levers are stopping the source traffic, gating signup on the pumping risk score, and lowering the protection level in the Console if the block really is a false positive. A script that finds the cause is worth more here than usual, because it is the only lever that can be pulled quickly.</p>
<p><strong>Lookup is the only read-only window into the risk.</strong> <code>sms_pumping_risk</code> gives you <code>number_blocked</code> right now, <code>number_blocked_last_3_months</code> for the history, <code>carrier_risk_category</code> for the range, and a <code>sms_pumping_risk_score</code> you can gate on. It is a billed Lookup field, so the audit samples one number per prefix rather than asking about all of them.</p>
<p><strong>Blocked and blocked-before need different responses.</strong> A live block is an incident: your users cannot sign up now. A prefix blocked twice in three months with no block today is a source problem: it will happen again this week unless the traffic driving it is cut off.</p>""",
"steps": [
 {"h": "Sweep unconverted attempts over a bounded window",
  "body": """<p><code>GET https://verify.twilio.com/v2/Attempts?Status=unconverted&amp;DateCreatedAfter={ISO8601}</code>, following <code>meta.next_page_url</code>, with a hard cap. Unconverted is the right filter because a blocked delivery can never convert &mdash; the message was refused before it reached anyone.</p>"""},
 {"h": "Group by country and by number prefix",
  "body": """<p>Take <code>country</code> and the first six digits of <code>channel_data.to</code>. Fraud Guard acts on ranges, so a real block shows up as a cluster: dozens of unconverted attempts sharing leading digits, appearing inside a few hours rather than spread across the window.</p>"""},
 {"h": "Confirm one number per prefix through Lookup",
  "body": """<p><code>GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=sms_pumping_risk</code>. One number is enough to characterise the range, and the field is billed per lookup, so sampling is the design rather than a shortcut. Read <code>number_blocked</code>, <code>number_blocked_last_3_months</code> and <code>sms_pumping_risk_score</code>.</p>"""},
 {"h": "Separate the live block from the repeat offender",
  "body": """<p><code>number_blocked</code> <code>true</code> means signups from that range are failing right now, and the only thing that shortens it is the traffic stopping. <code>number_blocked_last_3_months</code> above zero with no current block means the range has been here before and will be again.</p>"""},
 {"h": "Cut off the source, then gate the front door",
  "body": """<p>Add Service Rate Limits keyed on IP or user so one client cannot drive the endpoint. Gate signup on the score: block at 90 and above, add friction between 60 and 75. If the block really is a false positive on your traffic, lower the protection level at Console &rarr; Verify &rarr; Services &rarr; SMS. Then re-run and watch <code>number_blocked</code> go false.</p>"""},
],
"verify": """<p>Re-run the script once the source traffic has stopped. No prefix should report a live block.</p>
<pre><code class="language-bash">python3 twilio_fraud_guard_block_audit.py --service VA00000000000000000000000000000000 --days 2
# 7 prefix group(s), 0 currently blocked</code></pre>""",
"code_intro": "The script pages unconverted attempts, groups them by country and prefix, and spends one billed Lookup per group rather than per number &mdash; all GETs, and an API Key with read access is enough. The classifier is pure and deliberately keeps five states apart, because <em>blocked now</em>, <em>blocked twice last quarter</em> and <em>scoring 94 and about to be</em> call for three different responses on three different timescales.",
"py_file": "twilio_fraud_guard_block_audit.py",
"py": '''"""Find number prefixes Fraud Guard has blocked, which fail real users with 60410.

Fraud Guard blocks SMS to a prefix for twelve hours when it sees pumping-shaped
traffic, and re-arms while the pattern continues. There is no unblock API: the
block ends when the traffic causing it stops.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_fraud_guard_block_audit")

VERIFY = "https://verify.twilio.com/v2"
LOOKUPS = "https://lookups.twilio.com/v2"

# Twilio's own guidance for gating a signup on the score: block at 90 and above,
# add friction in the middle band.
BLOCK_SCORE = 90
FRICTION_SCORE = 60

# Below this many unconverted attempts a prefix is not a cluster, it is a few
# people whose phones were off.
MIN_ATTEMPTS = 5


def prefix_of(number, digits=6):
    """Leading digits of an E.164 number. Fraud Guard acts on ranges, so the
    prefix is the unit of both the block and the report.
    """
    n = "".join(c for c in str(number or "") if c.isdigit())
    return ("+" + n[:digits]) if n else "?"


def group_attempts(attempts, digits=6):
    """Bucket unconverted attempts by (country, prefix). Pure, so the grouping
    can be tested without a network.
    """
    groups = {}
    for a in attempts:
        to = (a.get("channel_data") or {}).get("to")
        keyed = (a.get("country") or "??", prefix_of(to, digits))
        g = groups.setdefault(keyed, {"country": keyed[0], "prefix": keyed[1],
                                      "attempts": 0, "sample": None})
        g["attempts"] += 1
        if g["sample"] is None and to:
            g["sample"] = to
    return sorted(groups.values(), key=lambda g: -g["attempts"])


def verdict(group, risk, min_attempts=MIN_ATTEMPTS):
    """Classify one (country, prefix) group against Lookup's pumping risk.

    `risk` is the sms_pumping_risk object from Lookup, or None when the field was
    not returned. Pure, so the five states can be tested without a network.

    Returns (state, detail).
    """
    attempts = int(group.get("attempts") or 0)
    where = "%s %s" % (group.get("country", "??"), group.get("prefix", "?"))

    if attempts < min_attempts:
        return ("thin",
                "%s: %d unconverted attempt(s), below the %d cluster floor"
                % (where, attempts, min_attempts))

    if not risk:
        return ("no-risk-data",
                "%s: %d unconverted, and Lookup returned no sms_pumping_risk. "
                "That field is billed and entitlement-gated: confirm the add-on "
                "before reading this as clear." % (where, attempts))

    score = risk.get("sms_pumping_risk_score")
    score_txt = "score %s" % ("?" if score is None else score)
    carrier = risk.get("carrier_risk_category") or "unknown"

    if risk.get("number_blocked"):
        return ("blocked",
                "%s: Fraud Guard block is live (since %s, %s, carrier risk %s) "
                "on %d unconverted attempts. Every real user on this prefix gets "
                "60410 for twelve hours, and it re-arms while the traffic "
                "continues. There is no unblock API."
                % (where, risk.get("number_blocked_date") or "unknown date",
                   score_txt, carrier, attempts))

    recent = int(risk.get("number_blocked_last_3_months") or 0)
    if recent > 0:
        return ("blocked-recently",
                "%s: not blocked now, but blocked %d time(s) in three months "
                "(%s, carrier risk %s). The source traffic is still arriving, so "
                "this range will block again." % (where, recent, score_txt, carrier))

    if score is not None and score >= BLOCK_SCORE:
        return ("high-risk",
                "%s: %s on %d unconverted attempts. This is the traffic Fraud "
                "Guard blocks; gate signup on the score before it does."
                % (where, score_txt, attempts))

    if score is not None and score >= FRICTION_SCORE:
        return ("watch",
                "%s: %s, in the band where friction belongs rather than a hard "
                "block (carrier risk %s)." % (where, score_txt, carrier))

    return ("clear",
            "%s: %s, no block on record. The %d unconverted attempts here are "
            "something else." % (where, score_txt, attempts))


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def unconverted(session, service, since, limit=2000):
    url = VERIFY + "/Attempts"
    params = {"VerifyServiceSid": service, "Status": "unconverted",
              "DateCreatedAfter": since, "PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("attempts", []))
        url, params = (page.get("meta") or {}).get("next_page_url"), {}
    return out[:limit]


def pumping_risk(session, e164):
    """One billed Lookup per prefix group, not per number."""
    body = get(session, "%s/PhoneNumbers/%s" % (LOOKUPS, e164),
               Fields="sms_pumping_risk")
    return body.get("sms_pumping_risk")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--service", required=True, help="Verify Service SID (VA...)")
    ap.add_argument("--days", type=int, default=2, help="window to sweep")
    ap.add_argument("--prefix-digits", type=int, default=6,
                    help="leading digits that define a range")
    ap.add_argument("--max-lookups", type=int, default=20,
                    help="cap on billed Lookup calls")
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

    since = (dt.datetime.now(dt.timezone.utc)
             - dt.timedelta(days=args.days)).strftime("%Y-%m-%dT%H:%M:%SZ")

    groups = group_attempts(unconverted(session, args.service, since),
                            args.prefix_digits)
    if not groups:
        log.info("no unconverted attempts in the last %d day(s)", args.days)
        return 0

    blocked = 0
    for i, g in enumerate(groups):
        risk = None
        if g["sample"] and i < args.max_lookups and g["attempts"] >= MIN_ATTEMPTS:
            risk = pumping_risk(session, g["sample"])
        state, detail = verdict(g, risk)
        line = "%-16s %s" % (state, detail)
        if state in ("blocked", "blocked-recently", "high-risk"):
            blocked += state == "blocked"
            log.warning(line)
            log.warning("  repair: no API lifts this. Add an IP-keyed Service "
                        "Rate Limit on %s, gate signup on "
                        "sms_pumping_risk_score (block at %d, friction from %d), "
                        "and lower the level at Console > Verify > Services > "
                        "SMS if this is a false positive on your own traffic",
                        args.service, BLOCK_SCORE, FRICTION_SCORE)
        else:
            log.info(line)

    log.info("%d prefix group(s), %d currently blocked", len(groups), blocked)
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-fraud-guard-block-audit.mjs",
"js": '''/**
 * Find number prefixes Fraud Guard has blocked, which fail real users with 60410.
 *
 * Fraud Guard blocks SMS to a prefix for twelve hours when it sees pumping-shaped
 * traffic, and re-arms while the pattern continues. There is no unblock API: the
 * block ends when the traffic causing it stops.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const VERIFY = 'https://verify.twilio.com/v2';
const LOOKUPS = 'https://lookups.twilio.com/v2';

// Twilio's own guidance for gating a signup on the score.
export const BLOCK_SCORE = 90;
export const FRICTION_SCORE = 60;

// Below this many unconverted attempts a prefix is not a cluster.
export const MIN_ATTEMPTS = 5;

/** Leading digits of an E.164 number: Fraud Guard acts on ranges. */
export function prefixOf(number, digits = 6) {
  const n = String(number ?? '').replace(/\\D/g, '');
  return n ? `+${n.slice(0, digits)}` : '?';
}

/**
 * Bucket unconverted attempts by (country, prefix). Pure, so the grouping can be
 * tested without a network.
 */
export function groupAttempts(attempts, digits = 6) {
  const groups = new Map();
  for (const a of attempts) {
    const to = a.channel_data?.to;
    const country = a.country ?? '??';
    const prefix = prefixOf(to, digits);
    const key = `${country} ${prefix}`;
    if (!groups.has(key)) {
      groups.set(key, { country, prefix, attempts: 0, sample: null });
    }
    const g = groups.get(key);
    g.attempts += 1;
    if (g.sample === null && to) g.sample = to;
  }
  return [...groups.values()].sort((x, y) => y.attempts - x.attempts);
}

/**
 * Classify one (country, prefix) group against Lookup's pumping risk. `risk` is
 * the sms_pumping_risk object, or null when the field was not returned. Pure, so
 * the five states can be tested without a network. Returns [state, detail].
 */
export function verdict(group, risk, minAttempts = MIN_ATTEMPTS) {
  const attempts = Number(group.attempts ?? 0);
  const where = `${group.country ?? '??'} ${group.prefix ?? '?'}`;

  if (attempts < minAttempts) {
    return ['thin',
      `${where}: ${attempts} unconverted attempt(s), below the ${minAttempts} ` +
      'cluster floor'];
  }

  if (!risk) {
    return ['no-risk-data',
      `${where}: ${attempts} unconverted, and Lookup returned no ` +
      'sms_pumping_risk. That field is billed and entitlement-gated: confirm ' +
      'the add-on before reading this as clear.'];
  }

  const score = risk.sms_pumping_risk_score;
  const scoreTxt = `score ${score ?? '?'}`;
  const carrier = risk.carrier_risk_category ?? 'unknown';

  if (risk.number_blocked) {
    return ['blocked',
      `${where}: Fraud Guard block is live (since ` +
      `${risk.number_blocked_date ?? 'unknown date'}, ${scoreTxt}, carrier ` +
      `risk ${carrier}) on ${attempts} unconverted attempts. Every real user ` +
      'on this prefix gets 60410 for twelve hours, and it re-arms while the ' +
      'traffic continues. There is no unblock API.'];
  }

  const recent = Number(risk.number_blocked_last_3_months ?? 0);
  if (recent > 0) {
    return ['blocked-recently',
      `${where}: not blocked now, but blocked ${recent} time(s) in three ` +
      `months (${scoreTxt}, carrier risk ${carrier}). The source traffic is ` +
      'still arriving, so this range will block again.'];
  }

  if (score !== undefined && score !== null && score >= BLOCK_SCORE) {
    return ['high-risk',
      `${where}: ${scoreTxt} on ${attempts} unconverted attempts. This is the ` +
      'traffic Fraud Guard blocks; gate signup on the score before it does.'];
  }

  if (score !== undefined && score !== null && score >= FRICTION_SCORE) {
    return ['watch',
      `${where}: ${scoreTxt}, in the band where friction belongs rather than a ` +
      `hard block (carrier risk ${carrier}).`];
  }

  return ['clear',
    `${where}: ${scoreTxt}, no block on record. The ${attempts} unconverted ` +
    'attempts here are something else.'];
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

async function unconverted(auth, service, since, limit = 2000) {
  let url = `${VERIFY}/Attempts`;
  let params = { VerifyServiceSid: service, Status: 'unconverted',
                 DateCreatedAfter: since, PageSize: 100 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.attempts ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

/** One billed Lookup per prefix group, not per number. */
async function pumpingRisk(auth, e164) {
  const body = await get(auth, `${LOOKUPS}/PhoneNumbers/${e164}`,
                         { Fields: 'sms_pumping_risk' });
  return body.sms_pumping_risk ?? null;
}

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i === -1 ? fallback : process.argv[i + 1];
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
  const service = arg('--service');
  if (!service) {
    console.error('pass --service VA...');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);
  const days = Number(arg('--days', '2'));
  const maxLookups = Number(arg('--max-lookups', '20'));
  const since = new Date(Date.now() - days * 86400000).toISOString()
    .replace(/\\.\\d+Z$/, 'Z');

  const groups = groupAttempts(await unconverted(auth, service, since));
  if (groups.length === 0) {
    console.log(`no unconverted attempts in the last ${days} day(s)`);
    return;
  }

  let blocked = 0;
  for (const [i, g] of groups.entries()) {
    let risk = null;
    if (g.sample && i < maxLookups && g.attempts >= MIN_ATTEMPTS) {
      risk = await pumpingRisk(auth, g.sample);
    }
    const [state, detail] = verdict(g, risk);
    const line = `${state.padEnd(16)} ${detail}`;
    if (state === 'blocked' || state === 'blocked-recently' || state === 'high-risk') {
      if (state === 'blocked') blocked += 1;
      console.warn(line);
      console.warn('  repair: no API lifts this. Add an IP-keyed Service Rate ' +
                   `Limit on ${service}, gate signup on sms_pumping_risk_score ` +
                   `(block at ${BLOCK_SCORE}, friction from ${FRICTION_SCORE}), ` +
                   'and lower the level at Console > Verify > Services > SMS if ' +
                   'this is a false positive on your own traffic');
    } else {
      console.log(line);
    }
  }

  console.log(`${groups.length} prefix group(s), ${blocked} currently blocked`);
  process.exitCode = blocked ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The states that have to stay apart are the ones people conflate: a live block, a range that was blocked twice last quarter, and a range scoring 94 that has not been blocked yet. The test that matters most is the last one &mdash; when Lookup returns no <code>sms_pumping_risk</code> at all the group must not be reported as clear, because an unentitled field and a clean number look identical in the response.",
"test_py_file": "test_twilio_fraud_guard_block_audit.py",
"test_py": '''from twilio_fraud_guard_block_audit import group_attempts, prefix_of, verdict

GROUP = {"country": "GB", "prefix": "+447700", "attempts": 44, "sample": "+447700900123"}


def test_live_block_is_the_incident():
    state, detail = verdict(GROUP, {"number_blocked": True,
                                    "number_blocked_date": "2026-08-29",
                                    "sms_pumping_risk_score": 97,
                                    "carrier_risk_category": "high"})
    assert state == "blocked"
    assert "60410" in detail
    assert "no unblock API" in detail


def test_blocked_before_but_not_now_is_a_source_problem():
    state, detail = verdict(GROUP, {"number_blocked": False,
                                    "number_blocked_last_3_months": 2,
                                    "sms_pumping_risk_score": 71})
    assert state == "blocked-recently"
    assert "block again" in detail


def test_high_score_with_no_block_yet_is_its_own_state():
    state, detail = verdict(GROUP, {"number_blocked": False,
                                    "number_blocked_last_3_months": 0,
                                    "sms_pumping_risk_score": 94})
    assert state == "high-risk"
    assert "before it does" in detail


def test_middle_band_asks_for_friction_not_a_block():
    state, _ = verdict(GROUP, {"number_blocked": False,
                               "number_blocked_last_3_months": 0,
                               "sms_pumping_risk_score": 66})
    assert state == "watch"


def test_missing_pumping_risk_is_never_reported_as_clear():
    # An unentitled field and a clean number look the same in the response.
    state, detail = verdict(GROUP, None)
    assert state == "no-risk-data"
    assert "entitlement-gated" in detail


def test_a_handful_of_attempts_is_not_a_cluster():
    state, _ = verdict({"country": "GB", "prefix": "+447700", "attempts": 2},
                       {"number_blocked": True})
    assert state == "thin"


def test_attempts_group_by_country_and_prefix_keeping_a_sample():
    groups = group_attempts([
        {"country": "GB", "channel_data": {"to": "+447700900123"}},
        {"country": "GB", "channel_data": {"to": "+447700900456"}},
        {"country": "FR", "channel_data": {"to": "+33612345678"}},
    ])
    assert groups[0]["prefix"] == "+447700"
    assert groups[0]["attempts"] == 2
    assert groups[0]["sample"] == "+447700900123"
    assert prefix_of("+33 6 12 34 56 78") == "+336123"
''',
"test_js_file": "twilio-fraud-guard-block-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { groupAttempts, prefixOf, verdict } from './twilio-fraud-guard-block-audit.mjs';

const GROUP = { country: 'GB', prefix: '+447700', attempts: 44, sample: '+447700900123' };

test('live block is the incident', () => {
  const [state, detail] = verdict(GROUP, {
    number_blocked: true, number_blocked_date: '2026-08-29',
    sms_pumping_risk_score: 97, carrier_risk_category: 'high' });
  assert.equal(state, 'blocked');
  assert.match(detail, /60410/);
  assert.match(detail, /no unblock API/);
});

test('blocked before but not now is a source problem', () => {
  const [state, detail] = verdict(GROUP, {
    number_blocked: false, number_blocked_last_3_months: 2,
    sms_pumping_risk_score: 71 });
  assert.equal(state, 'blocked-recently');
  assert.match(detail, /block again/);
});

test('high score with no block yet is its own state', () => {
  const [state, detail] = verdict(GROUP, {
    number_blocked: false, number_blocked_last_3_months: 0,
    sms_pumping_risk_score: 94 });
  assert.equal(state, 'high-risk');
  assert.match(detail, /before it does/);
});

test('middle band asks for friction not a block', () => {
  assert.equal(verdict(GROUP, {
    number_blocked: false, number_blocked_last_3_months: 0,
    sms_pumping_risk_score: 66 })[0], 'watch');
});

test('missing pumping risk is never reported as clear', () => {
  const [state, detail] = verdict(GROUP, null);
  assert.equal(state, 'no-risk-data');
  assert.match(detail, /entitlement-gated/);
});

test('a handful of attempts is not a cluster', () => {
  assert.equal(
    verdict({ country: 'GB', prefix: '+447700', attempts: 2 },
            { number_blocked: true })[0], 'thin');
});

test('attempts group by country and prefix keeping a sample', () => {
  const groups = groupAttempts([
    { country: 'GB', channel_data: { to: '+447700900123' } },
    { country: 'GB', channel_data: { to: '+447700900456' } },
    { country: 'FR', channel_data: { to: '+33612345678' } },
  ]);
  assert.equal(groups[0].prefix, '+447700');
  assert.equal(groups[0].attempts, 2);
  assert.equal(groups[0].sample, '+447700900123');
  assert.equal(prefixOf('+33 6 12 34 56 78'), '+336123');
});
''',
"faq": [
 ("Can I ask Twilio's API whether a prefix is blocked?",
  "Not directly. Fraud Guard has no read API for its state and none for whether it is even enabled. What you can read is the consequence: unconverted verification attempts clustered on a prefix, and Lookup's sms_pumping_risk.number_blocked on a number in that range. Those two together are the diagnosis."),
 ("How long does the block last?",
  "Twelve hours, and it re-arms in twelve-hour increments while the suspicious traffic keeps arriving. That is why retrying is counterproductive: each retry adds to the pattern being judged, and the window restarts rather than expiring."),
 ("My users are legitimate. Is this a false positive?",
  "Possibly, and it is worth separating two things. Fraud Guard blocked a prefix, not your users; if fraudulent traffic is hitting your endpoint from numbers in that range, the block is correct and the fix is upstream. If your own traffic genuinely resembles pumping, lower the protection level in the Console for that Service's SMS channel."),
 ("Why sample one number per prefix instead of looking up every failure?",
  "Because sms_pumping_risk is a billed Lookup field and the block applies to the range rather than to the individual number. One number characterises the range, so the audit spends one lookup per group and stays cheap enough to run on a schedule."),
 ("What do I do while the block is live?",
  "Give the affected users another channel. Verify supports a voice call for the same verification, which is not subject to the SMS block, and it is the difference between a signup that is delayed and one that is abandoned. In parallel, cut off whatever traffic triggered it so the window stops re-arming."),
],
"related": [
 ("/twilio/verify-conversion-rate-collapse/", "Verify conversion collapsing in one country"),
 ("/twilio/verify-no-rate-limits/", "A Verify Service with no rate limits at all"),
 ("/twilio/sms-pumping-protection-30450/", "SMS Pumping Protection blocking legitimate OTPs"),
],
"citations": [CITE_60410, CITE_PUMPRISK, CITE_TOLLFRAUD, CITE_KEYS],
},

{
"slug": "verify-sms-to-landline",
"title": "Verify sends SMS to a landline: 60205, or just silence",
"description": "A slice of users never receive their code. The destination is a landline or fixed VoIP range that cannot receive SMS, and Verify bills the attempt anyway.",
"h1": "Verify sends SMS to a landline: 60205, or just silence",
"category": "Twilio",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["twilio error 60205", "verify sms landline",
             "skip_sms_to_landlines", "line_type_intelligence lookup",
             "verify pending never converts"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "A small, stubborn fraction of your signups never complete. They are not bots, they do not retry three times and give up, and support cannot reproduce any of it. The numbers look fine: right length, right country, valid E.164. They are landlines. An SMS to a landline either comes back <code>60205</code> or, if Lookup is off, disappears into a verification that stays <code>pending</code> until it expires &mdash; billed, delivered nowhere.",
"short_answer": """<p>Pre-flight the destination with <code>GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=line_type_intelligence</code> and read <code>line_type_intelligence.type</code>. <code>landline</code>, <code>fixedVoip</code>, <code>pager</code>, <code>voicemail</code> and <code>unknown</code> are the types that cannot be relied on to receive an SMS.</p>
<p>Retrospectively, sweep <code>GET https://verify.twilio.com/v2/Attempts?Status=unconverted&amp;DateCreatedAfter={ISO8601}</code> and bucket <code>channel_data.to</code> by line type. Then check the Service itself: <code>skip_sms_to_landlines</code> only works when <code>lookup_enabled</code> is <code>true</code>, so the pair set the wrong way round is a setting that does nothing.</p>""",
"problem": """<p>Signup forms accept digits. A user typing their desk number, a small business entering its main line, a form that helpfully offers the phone number already on file from an older record &mdash; all three produce a valid E.164 string pointed at something that has no SMS inbox. Verify does not refuse it by default. It sends, it is billed, and the message stops at a carrier that has nowhere to put it.</p>
<p>The two shapes this takes are both bad, in different ways. With Lookup enabled on the Service you get a <code>403</code> and <code>60205</code>, which at least appears in your logs. With Lookup disabled &mdash; the default &mdash; Verify cannot classify the line at all, sends anyway, and leaves you a verification that sits <code>pending</code> until it expires. The second one costs the same and tells you nothing.</p>
<p>What makes it durable is the size. This is never everybody. It is two or three percent of signups, sitting inside the same bucket as typos and abandoned forms, and no funnel dashboard has a line item for <em>users whose phone cannot receive text messages</em>. It has to be looked for deliberately, using the line type as the key.</p>""",
"why": """<p><strong>A landline is not a delivery failure, it is a category error.</strong> No amount of retrying, no carrier escalation and no change of sender will make an SMS arrive at a number with no SMS capability. The only fixes are upstream: do not send, or send to a different channel.</p>
<p><strong>Lookup is off by default, and the landline guard depends on it.</strong> <code>skip_sms_to_landlines</code> can only work if Verify performs a Lookup at start time, which is what <code>lookup_enabled</code> controls. Setting the skip while leaving lookup off produces a configuration that reads as protected and enforces nothing.</p>
<p><strong>Silence is the worse outcome and it is the default one.</strong> Without lookup there is no <code>60205</code> to grep for; there is just an unconverted attempt among all your other unconverted attempts. That is why the retrospective sweep buckets by line type rather than by error code.</p>
<p><strong><code>fixedVoip</code> is the interesting middle.</strong> Some fixed VoIP numbers receive SMS and some do not, depending entirely on the provider. Treating them as landlines rejects real users; treating them as mobiles produces intermittent, unreproducible failures. They deserve their own state and a voice fallback rather than a rejection.</p>
<p><strong>Line type is a billed lookup, so where you spend it matters.</strong> One lookup at signup, cached against the user, is cheap and prevents the whole class. One lookup per failed verification, forever, is a running cost with no ceiling. The audit samples; the signup form is where the check belongs permanently.</p>""",
"steps": [
 {"h": "Read the Service's two settings together",
  "body": """<p><code>GET https://verify.twilio.com/v2/Services/{ServiceSid}</code> and read <code>lookup_enabled</code> and <code>skip_sms_to_landlines</code> as a pair. Skip <code>true</code> with lookup <code>false</code> is the no-op combination, and it is the one that convinces a team it is already handled.</p>"""},
 {"h": "Sweep the unconverted attempts",
  "body": """<p><code>GET https://verify.twilio.com/v2/Attempts?Status=unconverted&amp;DateCreatedAfter={ISO8601}</code>, following <code>meta.next_page_url</code>. These are the verifications nobody completed. Take <code>channel_data.to</code> from each and deduplicate: the same number appearing four times is one user trying four times, not four findings.</p>"""},
 {"h": "Classify each distinct number by line type",
  "body": """<p><code>GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=line_type_intelligence</code>. Cap the number of lookups: the field is billed, and a sample is enough to tell you whether landlines are one percent of your unconverted attempts or forty.</p>"""},
 {"h": "Separate cannot from might-not",
  "body": """<p><code>landline</code>, <code>pager</code> and <code>voicemail</code> cannot receive an SMS at all. <code>fixedVoip</code> and <code>unknown</code> might, depending on the provider. The first group is a hard finding; the second is the group to route through a voice call rather than reject.</p>"""},
 {"h": "Fix it in two places, then re-run",
  "body": """<p>On the Service, enable <code>LookupEnabled</code> and <code>SkipSmsToLandlines</code> so Verify stops paying to text landlines. On the signup form, check the line type before you accept the number and offer <code>Channel=call</code> when it is not a mobile. Re-run the sweep; the landline share of unconverted attempts should fall to roughly nothing.</p>"""},
],
"verify": """<p>Re-run the script. The Service should report both settings on, and no unconverted attempt should be sitting on a landline.</p>
<pre><code class="language-bash">python3 twilio_verify_landline_audit.py --service VA00000000000000000000000000000000
# service guard: guarded
# 60 number(s) sampled, 0 that cannot receive SMS</code></pre>""",
"code_intro": "Two pure functions carry the diagnosis and both are tested offline: one turns a Lookup response into a verdict for the channel you are actually sending on, and one reads the Service's two settings as the pair they really are. Around them the script does GETs only &mdash; the Service, a page of unconverted attempts, and a capped number of billed lookups &mdash; and prints the repair rather than applying it.",
"py_file": "twilio_verify_landline_audit.py",
"py": '''"""Find Verify traffic aimed at numbers that cannot receive an SMS.

A landline destination is not a delivery failure, it is a category error: it
returns 60205 when Lookup is on, and silently expires as an unconverted
verification when Lookup is off, which is the default.

Read only. GET requests and nothing else: give this an API Key with read access
rather than the account auth token. The repair is printed, never performed.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("twilio_verify_landline_audit")

VERIFY = "https://verify.twilio.com/v2"
LOOKUPS = "https://lookups.twilio.com/v2"

# No SMS inbox exists behind these, whatever the carrier or the sender.
NO_SMS = {"landline", "pager", "voicemail"}

# These may or may not receive an SMS depending on the provider, which is worse
# than a clean no: the failures are intermittent and unreproducible.
UNRELIABLE = {"fixedvoip", "uan", "unknown"}


def line_type(lookup):
    """Lowercased line_type_intelligence.type, or None if the field is absent.

    The API returns camelCase values such as fixedVoip; lowercasing once here
    keeps every comparison below in one case.
    """
    lti = (lookup or {}).get("line_type_intelligence") or {}
    t = lti.get("type")
    return str(t).strip().lower() if t else None


def verdict(lookup, channel="sms"):
    """Classify one Lookup response for the channel you intend to use.

    Pure, so the rules can be tested without a network. Returns (state, detail).
    """
    if lookup is not None and lookup.get("valid") is False:
        return ("invalid",
                "Lookup says the number is not valid: it will fail on any channel")

    t = line_type(lookup)
    if t is None:
        return ("no-line-type",
                "no line_type_intelligence on the response. Either the field was "
                "not requested (Fields=line_type_intelligence) or the account is "
                "not entitled to it: do not read this as a mobile.")

    if t in NO_SMS:
        if channel == "call":
            return ("voice-ok",
                    "%s, and this verification is on the call channel: a voice "
                    "code reaches it fine" % t)
        return ("no-sms",
                "%s: there is no SMS inbox behind this number. Verify returns "
                "60205 when lookup_enabled is true, and bills a verification "
                "that expires unconverted when it is false." % t)

    if t in UNRELIABLE:
        return ("unreliable",
                "%s: SMS delivery depends entirely on the provider, so these "
                "fail intermittently and never reproduce. Offer a voice call "
                "rather than rejecting the number." % t)

    return ("mobile", "%s: can receive SMS" % t)


def guard_state(service):
    """Read lookup_enabled and skip_sms_to_landlines as the pair they are.

    Pure. The no-op combination -- skip on, lookup off -- is the one that
    convinces a team the problem is already handled.
    """
    lookup_on = bool((service or {}).get("lookup_enabled"))
    skip_on = bool((service or {}).get("skip_sms_to_landlines"))

    if skip_on and not lookup_on:
        return ("no-op",
                "skip_sms_to_landlines is true but lookup_enabled is false. The "
                "skip needs the Lookup to classify the line, so this setting "
                "does nothing at all.")
    if not lookup_on:
        return ("unguarded",
                "lookup_enabled is false: Verify cannot classify the line type, "
                "so landlines are sent to and billed in silence.")
    if not skip_on:
        return ("lookup-only",
                "lookup_enabled is true but skip_sms_to_landlines is false: you "
                "get 60205 in the logs instead of a skipped send.")
    return ("guarded", "lookup_enabled and skip_sms_to_landlines are both on")


def get(session, url, **params):
    r = session.get(url, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise SystemExit("%d from Twilio: check TWILIO_ACCOUNT_SID and that the "
                         "API key belongs to that account with read access"
                         % r.status_code)
    r.raise_for_status()
    return r.json()


def unconverted(session, service, since, limit=1000):
    url = VERIFY + "/Attempts"
    params = {"VerifyServiceSid": service, "Status": "unconverted",
              "DateCreatedAfter": since, "PageSize": 100}
    out = []
    while url and len(out) < limit:
        page = get(session, url, **params)
        out.extend(page.get("attempts", []))
        url, params = (page.get("meta") or {}).get("next_page_url"), {}
    return out[:limit]


def distinct_destinations(attempts):
    """One entry per number, with the channel it was tried on. The same number
    four times is one user trying four times, not four findings.
    """
    seen = {}
    for a in attempts:
        data = a.get("channel_data") or {}
        to = data.get("to")
        if to and to not in seen:
            seen[to] = (a.get("channel") or "sms").lower()
    return list(seen.items())


def line_type_lookup(session, e164):
    return get(session, "%s/PhoneNumbers/%s" % (LOOKUPS, e164),
               Fields="line_type_intelligence")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--service", required=True, help="Verify Service SID (VA...)")
    ap.add_argument("--days", type=int, default=7, help="window to sweep")
    ap.add_argument("--max-lookups", type=int, default=60,
                    help="cap on billed Lookup calls")
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

    service = get(session, "%s/Services/%s" % (VERIFY, args.service))
    gstate, gdetail = guard_state(service)
    log.info("service guard: %s  %s", gstate, gdetail)
    if gstate != "guarded":
        log.warning("  repair: set LookupEnabled=true and SkipSmsToLandlines=true "
                    "on %s/Services/%s", VERIFY, args.service)

    since = (dt.datetime.now(dt.timezone.utc)
             - dt.timedelta(days=args.days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    numbers = distinct_destinations(unconverted(session, args.service, since))
    if not numbers:
        log.info("no unconverted attempts in the last %d day(s)", args.days)
        return 1 if gstate != "guarded" else 0

    bad = 0
    for e164, channel in numbers[:args.max_lookups]:
        state, detail = verdict(line_type_lookup(session, e164), channel)
        line = "%-13s %s  %s" % (state, e164, detail)
        if state in ("no-sms", "invalid"):
            bad += 1
            log.warning(line)
        elif state in ("unreliable", "no-line-type"):
            log.warning(line)
        else:
            log.info(line)

    if bad:
        log.warning("  repair: gate signup on line_type_intelligence.type == "
                    "\\"mobile\\" and start these verifications with Channel=call "
                    "instead")

    log.info("%d number(s) sampled, %d that cannot receive SMS",
             min(len(numbers), args.max_lookups), bad)
    return 1 if (bad or gstate != "guarded") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "twilio-verify-landline-audit.mjs",
"js": '''/**
 * Find Verify traffic aimed at numbers that cannot receive an SMS.
 *
 * A landline destination is not a delivery failure, it is a category error: it
 * returns 60205 when Lookup is on, and silently expires as an unconverted
 * verification when Lookup is off, which is the default.
 *
 * Read only. GET requests and nothing else: give this an API Key with read
 * access rather than the account auth token. The repair is printed, never
 * performed.
 */
const VERIFY = 'https://verify.twilio.com/v2';
const LOOKUPS = 'https://lookups.twilio.com/v2';

// No SMS inbox exists behind these, whatever the carrier or the sender.
const NO_SMS = new Set(['landline', 'pager', 'voicemail']);

// These may or may not receive an SMS depending on the provider, which is worse
// than a clean no: the failures are intermittent and unreproducible.
const UNRELIABLE = new Set(['fixedvoip', 'uan', 'unknown']);

/**
 * Lowercased line_type_intelligence.type, or null if the field is absent. The
 * API returns camelCase values such as fixedVoip; lowercasing once here keeps
 * every comparison below in one case.
 */
export function lineType(lookup) {
  const t = lookup?.line_type_intelligence?.type;
  return t ? String(t).trim().toLowerCase() : null;
}

/**
 * Classify one Lookup response for the channel you intend to use. Pure, so the
 * rules can be tested without a network. Returns [state, detail].
 */
export function verdict(lookup, channel = 'sms') {
  if (lookup && lookup.valid === false) {
    return ['invalid',
      'Lookup says the number is not valid: it will fail on any channel'];
  }

  const t = lineType(lookup);
  if (t === null) {
    return ['no-line-type',
      'no line_type_intelligence on the response. Either the field was not ' +
      'requested (Fields=line_type_intelligence) or the account is not ' +
      'entitled to it: do not read this as a mobile.'];
  }

  if (NO_SMS.has(t)) {
    if (channel === 'call') {
      return ['voice-ok',
        `${t}, and this verification is on the call channel: a voice code ` +
        'reaches it fine'];
    }
    return ['no-sms',
      `${t}: there is no SMS inbox behind this number. Verify returns 60205 ` +
      'when lookup_enabled is true, and bills a verification that expires ' +
      'unconverted when it is false.'];
  }

  if (UNRELIABLE.has(t)) {
    return ['unreliable',
      `${t}: SMS delivery depends entirely on the provider, so these fail ` +
      'intermittently and never reproduce. Offer a voice call rather than ' +
      'rejecting the number.'];
  }

  return ['mobile', `${t}: can receive SMS`];
}

/**
 * Read lookup_enabled and skip_sms_to_landlines as the pair they are. Pure. The
 * no-op combination -- skip on, lookup off -- is the one that convinces a team
 * the problem is already handled. Returns [state, detail].
 */
export function guardState(service) {
  const lookupOn = Boolean(service?.lookup_enabled);
  const skipOn = Boolean(service?.skip_sms_to_landlines);

  if (skipOn && !lookupOn) {
    return ['no-op',
      'skip_sms_to_landlines is true but lookup_enabled is false. The skip ' +
      'needs the Lookup to classify the line, so this setting does nothing at all.'];
  }
  if (!lookupOn) {
    return ['unguarded',
      'lookup_enabled is false: Verify cannot classify the line type, so ' +
      'landlines are sent to and billed in silence.'];
  }
  if (!skipOn) {
    return ['lookup-only',
      'lookup_enabled is true but skip_sms_to_landlines is false: you get ' +
      '60205 in the logs instead of a skipped send.'];
  }
  return ['guarded', 'lookup_enabled and skip_sms_to_landlines are both on'];
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

async function unconverted(auth, service, since, limit = 1000) {
  let url = `${VERIFY}/Attempts`;
  let params = { VerifyServiceSid: service, Status: 'unconverted',
                 DateCreatedAfter: since, PageSize: 100 };
  const out = [];
  while (url && out.length < limit) {
    const page = await get(auth, url, params);
    out.push(...(page.attempts ?? []));
    url = page.meta?.next_page_url ?? null;
    params = {};
  }
  return out.slice(0, limit);
}

/** One entry per number: the same number four times is one user, not four findings. */
export function distinctDestinations(attempts) {
  const seen = new Map();
  for (const a of attempts) {
    const to = a.channel_data?.to;
    if (to && !seen.has(to)) seen.set(to, String(a.channel ?? 'sms').toLowerCase());
  }
  return [...seen.entries()];
}

function arg(name, fallback) {
  const i = process.argv.indexOf(name);
  return i === -1 ? fallback : process.argv[i + 1];
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
  const serviceSid = arg('--service');
  if (!serviceSid) {
    console.error('pass --service VA...');
    process.exitCode = 2;
    return;
  }
  const auth = authHeader(key, secret);
  const days = Number(arg('--days', '7'));
  const maxLookups = Number(arg('--max-lookups', '60'));

  const service = await get(auth, `${VERIFY}/Services/${serviceSid}`);
  const [gstate, gdetail] = guardState(service);
  console.log(`service guard: ${gstate}  ${gdetail}`);
  if (gstate !== 'guarded') {
    console.warn('  repair: set LookupEnabled=true and SkipSmsToLandlines=true ' +
                 `on ${VERIFY}/Services/${serviceSid}`);
  }

  const since = new Date(Date.now() - days * 86400000).toISOString()
    .replace(/\\.\\d+Z$/, 'Z');
  const numbers = distinctDestinations(await unconverted(auth, serviceSid, since));
  if (numbers.length === 0) {
    console.log(`no unconverted attempts in the last ${days} day(s)`);
    process.exitCode = gstate === 'guarded' ? 0 : 1;
    return;
  }

  let bad = 0;
  for (const [e164, channel] of numbers.slice(0, maxLookups)) {
    const lookup = await get(auth, `${LOOKUPS}/PhoneNumbers/${e164}`,
                             { Fields: 'line_type_intelligence' });
    const [state, detail] = verdict(lookup, channel);
    const line = `${state.padEnd(13)} ${e164}  ${detail}`;
    if (state === 'no-sms' || state === 'invalid') { bad += 1; console.warn(line); }
    else if (state === 'unreliable' || state === 'no-line-type') console.warn(line);
    else console.log(line);
  }

  if (bad) {
    console.warn('  repair: gate signup on line_type_intelligence.type === ' +
                 '"mobile" and start these verifications with Channel=call instead');
  }

  console.log(`${Math.min(numbers.length, maxLookups)} number(s) sampled, ` +
              `${bad} that cannot receive SMS`);
  process.exitCode = (bad || gstate !== 'guarded') ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing credentials and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Four things have to hold: a landline is a finding on SMS and not on a voice call, <code>fixedVoip</code> is neither a pass nor a rejection, a response with no line type is never treated as a mobile, and the Service's two settings are read together so the no-op combination is named as one. That last case is the one worth the test &mdash; it is the configuration that looks correct in the Console.",
"test_py_file": "test_twilio_verify_landline_audit.py",
"test_py": '''from twilio_verify_landline_audit import guard_state, line_type, verdict


def test_landline_on_the_sms_channel_is_the_finding():
    state, detail = verdict({"line_type_intelligence": {"type": "landline"}})
    assert state == "no-sms"
    assert "60205" in detail


def test_the_same_landline_on_a_voice_verification_is_fine():
    state, _ = verdict({"line_type_intelligence": {"type": "landline"}},
                       channel="call")
    assert state == "voice-ok"


def test_fixed_voip_is_neither_a_pass_nor_a_rejection():
    # Camel case from the API, matched case-insensitively.
    state, detail = verdict({"line_type_intelligence": {"type": "fixedVoip"}})
    assert state == "unreliable"
    assert "voice call" in detail


def test_a_response_with_no_line_type_is_not_a_mobile():
    state, detail = verdict({"valid": True})
    assert state == "no-line-type"
    assert "Fields=line_type_intelligence" in detail


def test_mobile_passes():
    assert verdict({"line_type_intelligence": {"type": "mobile"}})[0] == "mobile"
    assert line_type({"line_type_intelligence": {"type": "  Mobile "}}) == "mobile"


def test_skip_without_lookup_is_a_setting_that_does_nothing():
    state, detail = guard_state({"lookup_enabled": False,
                                 "skip_sms_to_landlines": True})
    assert state == "no-op"
    assert "does nothing" in detail


def test_both_settings_on_is_the_only_guarded_state():
    assert guard_state({"lookup_enabled": True,
                        "skip_sms_to_landlines": True})[0] == "guarded"
    assert guard_state({"lookup_enabled": True,
                        "skip_sms_to_landlines": False})[0] == "lookup-only"
    assert guard_state({})[0] == "unguarded"
''',
"test_js_file": "twilio-verify-landline-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { guardState, lineType, verdict } from './twilio-verify-landline-audit.mjs';

test('landline on the sms channel is the finding', () => {
  const [state, detail] = verdict({ line_type_intelligence: { type: 'landline' } });
  assert.equal(state, 'no-sms');
  assert.match(detail, /60205/);
});

test('the same landline on a voice verification is fine', () => {
  assert.equal(
    verdict({ line_type_intelligence: { type: 'landline' } }, 'call')[0],
    'voice-ok');
});

test('fixed voip is neither a pass nor a rejection', () => {
  const [state, detail] = verdict({ line_type_intelligence: { type: 'fixedVoip' } });
  assert.equal(state, 'unreliable');
  assert.match(detail, /voice call/);
});

test('a response with no line type is not a mobile', () => {
  const [state, detail] = verdict({ valid: true });
  assert.equal(state, 'no-line-type');
  assert.match(detail, /Fields=line_type_intelligence/);
});

test('mobile passes', () => {
  assert.equal(verdict({ line_type_intelligence: { type: 'mobile' } })[0], 'mobile');
  assert.equal(lineType({ line_type_intelligence: { type: '  Mobile ' } }), 'mobile');
});

test('skip without lookup is a setting that does nothing', () => {
  const [state, detail] = guardState({ lookup_enabled: false,
                                       skip_sms_to_landlines: true });
  assert.equal(state, 'no-op');
  assert.match(detail, /does nothing/);
});

test('both settings on is the only guarded state', () => {
  assert.equal(guardState({ lookup_enabled: true,
                            skip_sms_to_landlines: true })[0], 'guarded');
  assert.equal(guardState({ lookup_enabled: true,
                            skip_sms_to_landlines: false })[0], 'lookup-only');
  assert.equal(guardState({})[0], 'unguarded');
});
''',
"faq": [
 ("Why would a verification just stay pending instead of erroring?",
  "Because with lookup_enabled false, Verify never classifies the destination. It hands the message to the carrier, the carrier has nowhere to deliver it, and the verification sits pending until its ten-minute TTL expires. You are billed for the attempt and there is no error code anywhere to find it by."),
 ("Is skip_sms_to_landlines enough on its own?",
  "No, and this is the trap. The skip depends on Verify performing a Lookup at start time, which is what lookup_enabled controls. Set the skip while lookup is off and you have a setting that reads as protection in the Console and does nothing at all in production."),
 ("What about fixedVoip numbers? Plenty of my users have them.",
  "Some receive SMS and some do not, entirely depending on the provider, so blanket-rejecting them loses real users and blanket-accepting them produces intermittent failures nobody can reproduce. Treat them as their own case: try SMS, and offer a voice call as the fallback rather than an error."),
 ("Should I check the line type at signup or after the failure?",
  "At signup. One billed lookup, cached against the user, prevents the whole class before any money is spent on a message. The retrospective sweep in this note exists to tell you how large the problem already is, not to be the permanent control."),
 ("Can these users verify at all?",
  "Yes, over the voice channel. Verify will call the number and read the code out, which works on a landline exactly as it does on a mobile. Routing non-mobile numbers to Channel=call turns a silent signup failure into a slightly different signup flow."),
],
"related": [
 ("/twilio/landline-destination-30006/", "Sending SMS to landlines that can never receive it"),
 ("/twilio/from-number-not-sms-capable/", "A from number with no SMS capability"),
 ("/twilio/verify-conversion-rate-collapse/", "Verify conversion collapsing in one country"),
],
"citations": [CITE_60205, CITE_LTI, CITE_VSERVICE, CITE_KEYS],
},

]
