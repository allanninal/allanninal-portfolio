#!/usr/bin/env python3
"""/github/ field notes, batch K — the writing.

Four notes about a GitHub App that cannot get in, and four different doors.

The first is a clock. GitHub reads the iat claim against its own time, so a host
running a minute fast has already lost before the request leaves it. The
instrument is the Date header on any response, sampled a few times with the
round trip recorded, which turns "the clock is probably fine" into an offset
with an error bar. The JWT is never opened here: the arithmetic on iat and exp
belongs to a note that already owns it, and this one is about the machine.

The second is a key. The same 401 arrives when the private key is not the one
registered on the App named in iss, and no amount of clock discipline helps.
The instrument is the PEM itself - its label, its shape and a fingerprint that
identifies the file without revealing it - followed by one GET /app that says
which App you actually authenticated as. No clocks, no claim arithmetic.

The third is a lifetime. An installation access token lasts exactly one hour,
and a process that mints one at startup and holds it outlives its own
credential in the most confusing way available: an hour of green followed by
uniform 401s. The finding is a schedule rather than a header, so the script
compares a refresh interval against the lifetime and prints the wall-clock
moment the cliff arrives.

The fourth is an absence. A 404 on a repository that plainly exists usually
means the App was never installed on it, and GitHub answers 404 rather than 403
so as not to confirm the repository is there. The instrument is
GET /repos/{owner}/{repo}/installation under the App JWT, which asks the
per-repository presence question directly and gets a yes or a no.

Read only throughout. The mint endpoint is a write and none of these call it.
"""

CITE_JWT = ("Generating a JSON Web Token (JWT) for a GitHub App — GitHub Docs",
            "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app")
CITE_APP_AUTH = ("Authenticating as a GitHub App — GitHub Docs",
                 "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app")
CITE_APP_INSTALL_AUTH = ("Authenticating as a GitHub App installation — GitHub Docs",
                         "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation")
CITE_APPS_REST = ("Apps — GitHub REST API",
                  "https://docs.github.com/en/rest/apps/apps")
CITE_INSTALLATIONS_REST = ("App installations — GitHub REST API",
                           "https://docs.github.com/en/rest/apps/installations")
CITE_PRIVATE_KEYS = ("Managing private keys for GitHub Apps — GitHub Docs",
                     "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/managing-private-keys-for-github-apps")
CITE_BEST_PRACTICES = ("Best practices for creating a GitHub App — GitHub Docs",
                       "https://docs.github.com/en/apps/creating-github-apps/setting-up-a-github-app/best-practices-for-creating-a-github-app")
CITE_INSTALLING = ("Installing your own GitHub App — GitHub Docs",
                   "https://docs.github.com/en/apps/using-github-apps/installing-your-own-github-app")
CITE_RATE_LIMITS = ("Rate limits for the REST API — GitHub Docs",
                    "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")
CITE_HTTP_DATE = ("HTTP Semantics, the Date field — RFC 9110",
                  "https://www.rfc-editor.org/rfc/rfc9110#field.date")
CITE_JWS = ("JSON Web Signature (JWS) — RFC 7515",
            "https://www.rfc-editor.org/rfc/rfc7515")
CITE_PKCS1 = ("PKCS #1: RSA Cryptography Specifications Version 2.2 — RFC 8017",
              "https://www.rfc-editor.org/rfc/rfc8017")

GUIDES = [

{
"slug": "jwt-clock-drift-iat",
"title": "Clock drift puts the JWT iat claim in GitHub's future",
"description": "GitHub refuses a JWT whose iat has not happened yet by its clock. Measure the offset against the Date header, then backdate iat past the drift.",
"h1": "clock drift puts the JWT iat claim in GitHub's future",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app jwt issued at claim iat must be an integer",
             "github app jwt 401 iat in the future",
             "github app jwt clock skew", "github app jwt works locally fails in docker",
             "backdate iat github app jwt"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The same code, the same key, the same App. On a laptop it works every time. In the container it returns <code>401 {\"message\": \"'Issued at' claim ('iat') must be an Integer representing the time that the assertion was issued\"}</code>, and on the third host it works again until Tuesday. Nothing about the JWT changed between those runs. What changed is which machine did the signing.",
"short_answer": """<p><code>iat</code> is a moment your host writes down and GitHub reads back against <em>its</em> clock. If your host is ahead, the moment you claim to have signed at has not happened yet as far as GitHub is concerned, and the JWT is refused before its signature matters. Containers with no time sync, suspended virtual machines and runners that boot with a cold clock all produce it, and they produce it intermittently, which is why it survives so many rounds of debugging.</p>
<p>You can measure the offset without any credential. Every GitHub response carries a <code>Date</code> header, so time the request from both ends and the skew falls out with an error bar attached: <code>local midpoint - server time</code>, plus or minus half the round trip. Then set <code>iat</code> to sixty seconds in the past, which is GitHub's own documented advice rather than a workaround, and fix the host's time sync so the number stays small.</p>""",
"problem": """<p>It fails on the wrong axis. Everything a person reaches for during a 401 is a property of the credential, and every one of those properties is identical across the machine where it works and the machine where it does not. The key is the same file. The App is the same App. The library is pinned. So the search goes around the credential twice before anybody thinks to look at the clock, because the clock is not part of the request as far as the code is concerned.</p>
<p>Then the message misdirects. <em>Must be an Integer representing the time that the assertion was issued</em> reads like a type error, and the first reaction is to check whether milliseconds went in where seconds were expected, or whether a date string slipped through. Those are real defects and they are not this one: the value is an integer, it is in seconds, and it is simply too large by the amount your host is ahead.</p>
<p>Worst of all it is intermittent by construction. A clock a second or two fast fails only when the network is quick enough for the request to arrive before GitHub's own second ticks over, so the same deployment returns 401 for one call in five. That looks like an upstream flap, gets a retry loop wrapped around it, and the retry loop makes it invisible for another six months.</p>""",
"why": """<p><strong>The claim is evaluated against a clock you do not own.</strong> <code>iat</code> means <em>issued at</em>, and a token issued in the future is a contradiction, so GitHub rejects it rather than waiting. The comparison is made on GitHub's clock, which is disciplined; yours may not be. Nothing in the JWT records which machine signed it, so the error can only describe the symptom.</p>
<p><strong>The reference clock is free and unauthenticated.</strong> Every HTTP response carries a <code>Date</code> header in the format RFC 9110 fixes, and <code>GET /rate_limit</code> answers without a credential and without consuming quota. That makes the measurement cheap enough to run on a schedule on every host that signs, rather than during an incident on the one host somebody suspects.</p>
<p><strong>A single reading is not a measurement.</strong> The <code>Date</code> value is truncated to the second and the response spent an unknown share of the round trip in each direction, so a naive comparison can be a second or two wrong in either direction. Recording the local time on both sides of the request and comparing the midpoint gives an offset with an uncertainty attached, and taking the exchange with the shortest round trip out of several is the same trick a time daemon uses: the fastest exchange had the least room to be asymmetric.</p>
<p><strong>Offset and drift are different diseases.</strong> A host that is forty seconds ahead and staying there was set wrong once, probably at boot. A host whose offset grows while you watch has no discipline at all and will be wrong again next week whatever you set it to today. Telling those apart needs two readings a decent interval apart, and the script refuses to guess a rate from samples taken seconds apart rather than report a number it cannot support.</p>
<p><strong>Whole hours are not drift.</strong> An offset that lands within a minute or two of a whole number of hours, or of a half hour, is a timezone conversion rather than a clock fault: something built <code>iat</code> from a naive local datetime and treated it as UTC. Backdating will not save that, and the script says so instead of recommending sixty seconds against a five-hour error.</p>
<p><strong>This note does not open the JWT.</strong> The lifetime arithmetic on <code>iat</code> and <code>exp</code> belongs to <a href="/github/jwt-exp-too-far-future/">the note on a JWT that expires in an hour</a>, which decodes the payload locally and never needs a network. Here the payload is irrelevant: a perfectly legal ten-minute JWT is refused just the same if the host that signed it is ahead.</p>""",
"steps": [
 {"h": "Measure on the host that signs, not on your laptop",
  "body": """<p>The number is a property of one machine. Run the check inside the container, on the runner, in the pod that mints the JWT, and run it there even when the same code works elsewhere, because the whole finding is the difference between those two places. A measurement taken on a developer machine with working time sync proves nothing about a production host that has none.</p>"""},
 {"h": "Take several samples and keep the fastest",
  "body": """<p>One request gives an offset contaminated by half an unknown round trip. Three or five, spread a couple of seconds apart, let you keep the exchange with the shortest round trip and report the rest as uncertainty. If the uncertainty is larger than the offset, the honest answer is that the path is too slow to resolve a skew this small, and the script says that rather than inventing precision.</p>"""},
 {"h": "Read the direction before the magnitude",
  "body": """<p>Ahead of GitHub is the dangerous direction: it is the one that puts <code>iat</code> in the future and produces the 401. Behind GitHub is a different and quieter problem, because the JWT arrives having already spent part of its life, so a ten-minute token signed on a host five minutes slow is half gone when it lands.</p>"""},
 {"h": "Check the offset against the backdate you already apply",
  "body": """<p>If your signing code sets <code>iat</code> to <code>now - 60</code>, an offset of ten seconds is absorbed and there is nothing to fix here. If it sets <code>iat</code> to <code>now</code>, any positive offset at all is a live failure waiting for a fast network. Pass the backdate you actually use and the report becomes a margin rather than a number.</p>"""},
 {"h": "Backdate by sixty seconds, then fix the host clock anyway",
  "body": """<p>Backdating is GitHub's documented recommendation and it costs nothing, so do it first. It is still not a repair: a host whose clock is wrong enough to break a JWT is producing misordered logs, wrong certificate validity windows and confusing metrics on the same afternoon. Install time sync, or run the container on a host that has it.</p>"""},
],
"verify": """<p>Re-run on the same host after the clock is disciplined. The state moves from <code>iat-lands-in-the-future</code> to <code>clock-in-sync</code>, and the confirming request, if you give it a JWT, stops naming <code>iat</code>.</p>
<pre><code class="language-bash">python3 github_clock_skew.py --samples 5 --backdate 60
# best of 5 samples: skew=+2.4s uncertainty=1.2s round_trip=0.31s
# clock-in-sync: this host and GitHub agree to within the measurement error.
# drift over 128s: offset-is-static at 3.1 ppm
# GET /app returned 200
# accepted: GitHub did not complain about iat.</code></pre>""",
"code_intro": "The measurement is the whole script and it needs no credential: <code>GET /rate_limit</code> answers unauthenticated, does not consume quota, and carries the <code>Date</code> header that is the only thing being read. Everything that turns samples into a verdict is pure &mdash; parsing the header, computing an offset with its uncertainty, picking the fastest exchange, classifying direction against the backdate you already apply, and refusing to state a drift rate from samples too close together. The optional confirming <code>GET /app</code> sends a JWT you already hold; it is never decoded, stored or printed, and the report contains nothing but seconds.",
"py_file": "github_clock_skew.py",
"py": '''"""Measure the clock on the machine that signs GitHub App JWTs.

Read only, and the part that matters needs no credential at all. Every GitHub
response carries a Date header, so the reference clock is free: send a request,
note the local time on both sides of it, and the offset between this host and
GitHub falls out with an error bar attached.

GET /rate_limit is used for the samples because it answers unauthenticated and
does not consume quota. Nothing here is written, minted or changed.

This script does not open your JWT. The arithmetic on iat and exp belongs to a
different note; the question here is whether the machine writing iat agrees
with the machine reading it. A host running fast puts iat in GitHub's future
and the JWT is refused however carefully the claim was computed.

Sign convention throughout: skew is local minus server, so a positive number
means this host is ahead of GitHub, which is the direction that breaks a JWT.
"""
import argparse
import json
import logging
import math
import os
import sys
import time
from datetime import timezone
from email.utils import parsedate_to_datetime

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_clock_skew")

API = "https://api.github.com"
UA = "github-clock-skew/1.0"

# The Date header is truncated to the second, so the true server time is
# somewhere inside a one second window. That floor is added to every
# uncertainty rather than pretended away.
DATE_RESOLUTION = 1.0

# Below this the two clocks are close enough that nothing is actionable.
GRACE = 5

# GitHub's own documented advice for the signing code.
RECOMMENDED_BACKDATE = 60

# A drift rate computed over a shorter span than this is noise, given that
# every sample is quantised to a whole second.
MIN_DRIFT_SPAN = 60

# Roughly the discipline a working time daemon holds. Above it the clock is
# free running and will be wrong again whatever you set it to today.
FREE_RUNNING_PPM = 100


def parse_http_date(value):
    """Parse an RFC 9110 Date header into epoch seconds. Pure.

    Returns None rather than raising: a response without a usable Date is a
    sample to discard, not an exception to propagate out of a measurement.
    """
    if not value:
        return None
    try:
        moment = parsedate_to_datetime(str(value))
    except (TypeError, ValueError):
        return None
    if moment is None:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.timestamp()


def sample_skew(server_epoch, sent, received):
    """One exchange reduced to an offset with an error bar. Pure.

    The request left at `sent` and the response landed at `received`, so the
    server read its clock somewhere in between. Comparing the midpoint of that
    window against the server time gives the offset; half the round trip, plus
    the one second the Date header is quantised to, bounds how wrong it can be.
    """
    if server_epoch is None:
        return None
    round_trip = max(float(received) - float(sent), 0.0)
    midpoint = (float(sent) + float(received)) / 2.0
    return {"skew": round(midpoint - float(server_epoch), 3),
            "uncertainty": round(round_trip / 2.0 + DATE_RESOLUTION, 3),
            "round_trip": round(round_trip, 3),
            "at": round(float(received), 3)}


def best_sample(samples):
    """The exchange with the shortest round trip. Pure.

    Not the mean and not the median. The fastest exchange is the one with the
    least room to be asymmetric between the two directions, which is the same
    reason a time daemon prefers it.
    """
    usable = [s for s in samples if s]
    if not usable:
        return None
    return min(usable, key=lambda s: s["round_trip"])


def timezone_suspect(skew):
    """Hours of offset when the skew looks like a timezone rather than drift. Pure.

    An offset within a minute and a half of a whole or half hour is almost
    never a clock: it is a naive local datetime that was treated as UTC. Saying
    so matters, because backdating sixty seconds does nothing about five hours.
    """
    if skew is None:
        return None
    magnitude = abs(float(skew))
    if magnitude < 1500:
        return None
    slots = round(magnitude / 1800.0)
    if slots == 0:
        return None
    if abs(magnitude - slots * 1800) <= 90:
        hours = slots / 2.0
        return hours if skew > 0 else -hours
    return None


def backdate_needed(skew, uncertainty):
    """How far to backdate iat so this offset cannot reach GitHub's future. Pure."""
    need = float(skew) + float(uncertainty) + GRACE
    if need <= RECOMMENDED_BACKDATE:
        return RECOMMENDED_BACKDATE
    return int(math.ceil(need / 30.0)) * 30


def classify(skew, uncertainty, backdate):
    """Turn one measured offset into a finding. Pure.

    Direction first, because it decides which failure you have. A host ahead of
    GitHub breaks iat; a host behind it burns the JWT lifetime early, which is
    a quieter problem with a different repair.
    """
    if skew is None:
        return ("unmeasurable",
                "no response carried a usable Date header, so there is no "
                "reference clock to compare against. Check that something is "
                "not stripping response headers in front of this host.")

    hours = timezone_suspect(skew)
    if hours is not None:
        return ("timezone-not-drift",
                "the offset is %+.1f hours, which is a timezone conversion "
                "rather than a clock fault. Something built the timestamp from "
                "a naive local datetime and treated it as UTC. Backdating will "
                "not help; the conversion has to be fixed." % hours)

    if skew > 0:
        margin = float(backdate) - (float(skew) + float(uncertainty))
        if margin < 0:
            return ("iat-lands-in-the-future",
                    "this host is %.1fs ahead of GitHub and iat is backdated "
                    "by %ds, so the claim lands %.1fs into GitHub's future and "
                    "the JWT is refused. Backdate by %ds and fix the host clock."
                    % (skew, backdate, -margin, backdate_needed(skew, uncertainty)))
        if margin < GRACE:
            return ("backdate-has-no-headroom",
                    "this host is %.1fs ahead of GitHub and the %ds backdate "
                    "absorbs it with only %.1fs to spare, which is close enough "
                    "to fail on a fast network. Backdate by %ds."
                    % (skew, backdate, margin, backdate_needed(skew, uncertainty)))
        if abs(skew) <= max(uncertainty, GRACE):
            return ("clock-in-sync",
                    "this host and GitHub agree to within the measurement "
                    "error of %.1fs." % uncertainty)
        return ("drift-absorbed-by-backdate",
                "this host is %.1fs ahead of GitHub, and the %ds backdate "
                "covers it with %.1fs to spare. The JWT is safe; the clock is "
                "still wrong and worth fixing." % (skew, backdate, margin))

    if abs(skew) <= max(uncertainty, GRACE):
        return ("clock-in-sync",
                "this host and GitHub agree to within the measurement error "
                "of %.1fs." % uncertainty)
    return ("clock-behind-github",
            "this host is %.1fs behind GitHub. iat is safe, but every JWT "
            "arrives having already spent %.1fs of its life, so a short "
            "lifetime can expire on the way." % (-skew, -skew))


def drift_rate(readings, min_span=MIN_DRIFT_SPAN):
    """Parts per million of drift between the first and last reading. Pure.

    readings: [(local_time, skew), ...]. Returns None when the samples are too
    close together to support a rate, which they usually are: every sample is
    quantised to a whole second, so a few seconds of span can only produce a
    number that looks authoritative and is not.
    """
    usable = [r for r in readings if r and r[1] is not None]
    if len(usable) < 2:
        return None
    span = float(usable[-1][0]) - float(usable[0][0])
    if span < min_span:
        return None
    return round((float(usable[-1][1]) - float(usable[0][1])) / span * 1e6, 1)


def classify_rate(ppm):
    """Say whether the offset is standing still or growing. Pure."""
    if ppm is None:
        return ("rate-not-measurable",
                "the samples do not span %ds, which is the least this "
                "measurement can support. Re-run with a longer interval if you "
                "want a rate rather than an offset." % MIN_DRIFT_SPAN)
    if abs(ppm) <= FREE_RUNNING_PPM:
        return ("offset-is-static",
                "the offset is holding at %.1f ppm, so the clock is "
                "disciplined and was simply set wrong once." % ppm)
    return ("clock-is-running-free",
            "the offset is moving at %.1f ppm, which is about %.1f seconds a "
            "day. Nothing is disciplining this clock, so setting it by hand "
            "buys only a few days." % (ppm, ppm * 0.0864))


def interpret(status, message):
    """Map a confirming GET /app response to the defect it names. Pure.

    Only the iat family is this note's business. The other messages are named
    so the report can point at the right neighbour rather than absorbing them.
    """
    if status == 200:
        return ("accepted", "GitHub did not complain about iat.")
    text = str(message or "").lower()
    if "issued at" in text or "'iat'" in text:
        return ("github-refused-iat",
                "GitHub says iat is not a time that has happened, which is "
                "this host being ahead of it.")
    if "too far in the future" in text:
        return ("lifetime-not-drift",
                "GitHub is complaining about exp rather than iat, so the "
                "requested lifetime is over the ceiling and the clock is not "
                "the problem.")
    if "could not be decoded" in text:
        return ("key-or-encoding",
                "GitHub could not decode the JWT at all, which is a signing "
                "key or encoding fault rather than a clock one.")
    if "integration not found" in text:
        return ("issuer-does-not-resolve",
                "the iss claim does not name an App GitHub can find, which is "
                "a key and issuer problem rather than a clock one.")
    return ("unrelated",
            "the response does not mention a claim, so this failure has "
            "another cause.")


def take_samples(count, interval):
    """Time `count` exchanges against GitHub. The only network in this script."""
    out = []
    for i in range(count):
        if i:
            time.sleep(interval)
        sent = time.time()
        try:
            r = requests.get(API + "/rate_limit", timeout=30, headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": UA,
            })
        except requests.RequestException as err:
            log.warning("sample %d failed: %s", i + 1, err)
            continue
        received = time.time()
        served = parse_http_date(r.headers.get("Date"))
        if served is None:
            log.warning("sample %d carried no usable Date header", i + 1)
            continue
        out.append(sample_skew(served, sent, received))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--samples", type=int, default=3,
                    help="how many exchanges to time (default 3)")
    ap.add_argument("--interval", type=float, default=2.0,
                    help="seconds between samples; use 30 or more if you want "
                         "a drift rate as well as an offset (default 2)")
    ap.add_argument("--backdate", type=int, default=0,
                    help="the seconds your signing code already subtracts from "
                         "iat (default 0, which is the common case)")
    ap.add_argument("--confirm", action="store_true",
                    help="also send GITHUB_APP_JWT to GET /app and report what "
                         "GitHub says about the claim")
    args = ap.parse_args()

    samples = take_samples(max(args.samples, 1), max(args.interval, 0.0))
    best = best_sample(samples)
    if best is None:
        log.error("no sample produced a reading; nothing can be said about "
                  "this clock")
        return 2

    log.info("best of %d sample(s): skew=%+.1fs uncertainty=%.1fs "
             "round_trip=%.2fs", len(samples), best["skew"],
             best["uncertainty"], best["round_trip"])

    state, detail = classify(best["skew"], best["uncertainty"], args.backdate)
    log.info("%s: %s", state, detail)

    readings = [(s["at"], s["skew"]) for s in samples if s]
    ppm = drift_rate(readings)
    rate_state, rate_detail = classify_rate(ppm)
    log.info("%s: %s", rate_state, rate_detail)

    if args.confirm:
        jwt = os.environ.get("GITHUB_APP_JWT")
        if not jwt:
            log.warning("--confirm needs GITHUB_APP_JWT set to the JWT your "
                        "own signing code produces")
        else:
            # The JWT is sent and nothing else. It is not decoded, stored or
            # logged, in whole or in part.
            r = requests.get(API + "/app", timeout=30, headers={
                "Authorization": "Bearer " + jwt,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": UA,
            })
            try:
                body = r.json()
            except ValueError:
                body = None
            message = body.get("message") if isinstance(body, dict) else None
            log.info("GET /app returned %d", r.status_code)
            live_state, live_detail = interpret(r.status_code, message)
            log.info("%s: %s", live_state, live_detail)

    if state in ("iat-lands-in-the-future", "backdate-has-no-headroom"):
        log.info("repair: set iat to now minus %ds when minting, then "
                 "install time sync on this host so the offset stops moving",
                 backdate_needed(best["skew"], best["uncertainty"]))

    print(json.dumps({"skew_seconds": best["skew"],
                      "uncertainty_seconds": best["uncertainty"],
                      "round_trip_seconds": best["round_trip"],
                      "samples": len(samples), "backdate_seconds": args.backdate,
                      "drift_ppm": ppm, "state": state}, indent=2))
    return 0 if state in ("clock-in-sync", "drift-absorbed-by-backdate") else 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-clock-skew.mjs",
"js": '''/**
 * Measure the clock on the machine that signs GitHub App JWTs.
 *
 * Read only, and the part that matters needs no credential. Every GitHub
 * response carries a Date header, so the reference clock is free: time a
 * request from both ends and the offset falls out with an error bar attached.
 *
 * GET /rate_limit is used for the samples because it answers unauthenticated
 * and does not consume quota.
 *
 * This script does not open your JWT. The question is whether the machine
 * writing iat agrees with the machine reading it.
 *
 * Sign convention: skew is local minus server, so positive means this host is
 * ahead of GitHub, which is the direction that breaks a JWT.
 */
const API = 'https://api.github.com';
const UA = 'github-clock-skew/1.0';

/** The Date header is quantised to a whole second, so every reading carries this floor. */
export const DATE_RESOLUTION = 1.0;

/** Below this the two clocks are close enough that nothing is actionable. */
export const GRACE = 5;

/** GitHub's own documented advice for the signing code. */
export const RECOMMENDED_BACKDATE = 60;

/** A rate computed over a shorter span than this is noise. */
export const MIN_DRIFT_SPAN = 60;

/** Roughly the discipline a working time daemon holds. */
export const FREE_RUNNING_PPM = 100;

/** Parse an RFC 9110 Date header into epoch seconds. Pure. null on anything odd. */
export function parseHttpDate(value) {
  if (!value) return null;
  const ms = Date.parse(String(value));
  return Number.isNaN(ms) ? null : ms / 1000;
}

/**
 * One exchange reduced to an offset with an error bar. Pure.
 * The server read its clock somewhere between sent and received, so the
 * midpoint is the fairest local comparison and half the round trip, plus the
 * one second of quantisation, bounds how wrong it can be.
 */
export function sampleSkew(serverEpoch, sent, received) {
  if (serverEpoch === null || serverEpoch === undefined) return null;
  const roundTrip = Math.max(Number(received) - Number(sent), 0);
  const midpoint = (Number(sent) + Number(received)) / 2;
  const round3 = (n) => Math.round(n * 1000) / 1000;
  return {
    skew: round3(midpoint - Number(serverEpoch)),
    uncertainty: round3(roundTrip / 2 + DATE_RESOLUTION),
    round_trip: round3(roundTrip),
    at: round3(Number(received)),
  };
}

/**
 * The exchange with the shortest round trip. Pure.
 * Not the mean and not the median: the fastest exchange had the least room to
 * be asymmetric, which is the same reason a time daemon prefers it.
 */
export function bestSample(samples) {
  const usable = (samples || []).filter(Boolean);
  if (!usable.length) return null;
  return usable.reduce((a, b) => (b.round_trip < a.round_trip ? b : a));
}

/**
 * Hours of offset when the skew looks like a timezone rather than drift. Pure.
 * Backdating sixty seconds does nothing about five hours, so this is worth
 * naming separately.
 */
export function timezoneSuspect(skew) {
  if (skew === null || skew === undefined) return null;
  const magnitude = Math.abs(Number(skew));
  if (magnitude < 1500) return null;
  const slots = Math.round(magnitude / 1800);
  if (slots === 0) return null;
  if (Math.abs(magnitude - slots * 1800) <= 90) {
    const hours = slots / 2;
    return skew > 0 ? hours : -hours;
  }
  return null;
}

/** How far to backdate iat so this offset cannot reach GitHub's future. Pure. */
export function backdateNeeded(skew, uncertainty) {
  const need = Number(skew) + Number(uncertainty) + GRACE;
  if (need <= RECOMMENDED_BACKDATE) return RECOMMENDED_BACKDATE;
  return Math.ceil(need / 30) * 30;
}

/**
 * Turn one measured offset into a finding. Pure.
 * Direction first: ahead of GitHub breaks iat, behind it burns the lifetime.
 */
export function classify(skew, uncertainty, backdate) {
  if (skew === null || skew === undefined) {
    return ['unmeasurable',
      'no response carried a usable Date header, so there is no reference ' +
      'clock to compare against. Check that something is not stripping ' +
      'response headers in front of this host.'];
  }
  const hours = timezoneSuspect(skew);
  if (hours !== null) {
    return ['timezone-not-drift',
      `the offset is ${hours > 0 ? '+' : ''}${hours.toFixed(1)} hours, which ` +
      'is a timezone conversion rather than a clock fault. Something built ' +
      'the timestamp from a naive local datetime and treated it as UTC. ' +
      'Backdating will not help; the conversion has to be fixed.'];
  }
  if (skew > 0) {
    const margin = Number(backdate) - (Number(skew) + Number(uncertainty));
    if (margin < 0) {
      return ['iat-lands-in-the-future',
        `this host is ${skew.toFixed(1)}s ahead of GitHub and iat is ` +
        `backdated by ${backdate}s, so the claim lands ${(-margin).toFixed(1)}s ` +
        'into GitHub\\'s future and the JWT is refused. Backdate by ' +
        `${backdateNeeded(skew, uncertainty)}s and fix the host clock.`];
    }
    if (margin < GRACE) {
      return ['backdate-has-no-headroom',
        `this host is ${skew.toFixed(1)}s ahead of GitHub and the ${backdate}s ` +
        `backdate absorbs it with only ${margin.toFixed(1)}s to spare, which ` +
        'is close enough to fail on a fast network. Backdate by ' +
        `${backdateNeeded(skew, uncertainty)}s.`];
    }
    if (Math.abs(skew) <= Math.max(uncertainty, GRACE)) {
      return ['clock-in-sync',
        `this host and GitHub agree to within the measurement error of ` +
        `${Number(uncertainty).toFixed(1)}s.`];
    }
    return ['drift-absorbed-by-backdate',
      `this host is ${skew.toFixed(1)}s ahead of GitHub, and the ${backdate}s ` +
      `backdate covers it with ${margin.toFixed(1)}s to spare. The JWT is ` +
      'safe; the clock is still wrong and worth fixing.'];
  }
  if (Math.abs(skew) <= Math.max(uncertainty, GRACE)) {
    return ['clock-in-sync',
      `this host and GitHub agree to within the measurement error of ` +
      `${Number(uncertainty).toFixed(1)}s.`];
  }
  return ['clock-behind-github',
    `this host is ${(-skew).toFixed(1)}s behind GitHub. iat is safe, but ` +
    `every JWT arrives having already spent ${(-skew).toFixed(1)}s of its ` +
    'life, so a short lifetime can expire on the way.'];
}

/**
 * Parts per million of drift between the first and last reading. Pure.
 * readings: [[localTime, skew], ...]. null when the span is too short to
 * support a rate, which is most of the time.
 */
export function driftRate(readings, minSpan = MIN_DRIFT_SPAN) {
  const usable = (readings || []).filter((r) => r && r[1] !== null && r[1] !== undefined);
  if (usable.length < 2) return null;
  const span = Number(usable[usable.length - 1][0]) - Number(usable[0][0]);
  if (span < minSpan) return null;
  const delta = Number(usable[usable.length - 1][1]) - Number(usable[0][1]);
  return Math.round((delta / span) * 1e6 * 10) / 10;
}

/** Say whether the offset is standing still or growing. Pure. */
export function classifyRate(ppm) {
  if (ppm === null || ppm === undefined) {
    return ['rate-not-measurable',
      `the samples do not span ${MIN_DRIFT_SPAN}s, which is the least this ` +
      'measurement can support. Re-run with a longer interval if you want a ' +
      'rate rather than an offset.'];
  }
  if (Math.abs(ppm) <= FREE_RUNNING_PPM) {
    return ['offset-is-static',
      `the offset is holding at ${ppm.toFixed(1)} ppm, so the clock is ` +
      'disciplined and was simply set wrong once.'];
  }
  return ['clock-is-running-free',
    `the offset is moving at ${ppm.toFixed(1)} ppm, which is about ` +
    `${(ppm * 0.0864).toFixed(1)} seconds a day. Nothing is disciplining this ` +
    'clock, so setting it by hand buys only a few days.'];
}

/** Map a confirming GET /app response to the defect it names. Pure. */
export function interpret(status, message) {
  if (status === 200) return ['accepted', 'GitHub did not complain about iat.'];
  const text = String(message ?? '').toLowerCase();
  if (text.includes('issued at') || text.includes("'iat'")) {
    return ['github-refused-iat',
      'GitHub says iat is not a time that has happened, which is this host ' +
      'being ahead of it.'];
  }
  if (text.includes('too far in the future')) {
    return ['lifetime-not-drift',
      'GitHub is complaining about exp rather than iat, so the requested ' +
      'lifetime is over the ceiling and the clock is not the problem.'];
  }
  if (text.includes('could not be decoded')) {
    return ['key-or-encoding',
      'GitHub could not decode the JWT at all, which is a signing key or ' +
      'encoding fault rather than a clock one.'];
  }
  if (text.includes('integration not found')) {
    return ['issuer-does-not-resolve',
      'the iss claim does not name an App GitHub can find, which is a key ' +
      'and issuer problem rather than a clock one.'];
  }
  return ['unrelated',
    'the response does not mention a claim, so this failure has another cause.'];
}

const wait = (seconds) => new Promise((r) => setTimeout(r, seconds * 1000));

async function takeSamples(count, interval) {
  const out = [];
  for (let i = 0; i < count; i += 1) {
    if (i) await wait(interval);
    const sent = Date.now() / 1000;
    let res;
    try {
      res = await fetch(`${API}/rate_limit`, {
        headers: {
          Accept: 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent': UA,
        },
      });
    } catch (err) {
      console.error(`sample ${i + 1} failed: ${err.message}`);
      continue;
    }
    const received = Date.now() / 1000;
    const served = parseHttpDate(res.headers.get('date'));
    if (served === null) {
      console.error(`sample ${i + 1} carried no usable Date header`);
      continue;
    }
    out.push(sampleSkew(served, sent, received));
  }
  return out;
}

function flag(name, fallback) {
  const at = process.argv.indexOf(name);
  if (at === -1 || at === process.argv.length - 1) return fallback;
  const value = Number(process.argv[at + 1]);
  return Number.isFinite(value) ? value : fallback;
}

async function main() {
  const count = Math.max(flag('--samples', 3), 1);
  const interval = Math.max(flag('--interval', 2), 0);
  const backdate = flag('--backdate', 0);
  const samples = await takeSamples(count, interval);
  const best = bestSample(samples);
  if (!best) {
    console.error('no sample produced a reading; nothing can be said about this clock');
    process.exitCode = 2;
    return;
  }

  console.log(`best of ${samples.length} sample(s): skew=${best.skew >= 0 ? '+' : ''}` +
    `${best.skew.toFixed(1)}s uncertainty=${best.uncertainty.toFixed(1)}s ` +
    `round_trip=${best.round_trip.toFixed(2)}s`);

  const [state, detail] = classify(best.skew, best.uncertainty, backdate);
  console.log(`${state}: ${detail}`);

  const ppm = driftRate(samples.filter(Boolean).map((s) => [s.at, s.skew]));
  const [rateState, rateDetail] = classifyRate(ppm);
  console.log(`${rateState}: ${rateDetail}`);

  if (process.argv.includes('--confirm')) {
    const jwt = process.env.GITHUB_APP_JWT;
    if (!jwt) {
      console.error('--confirm needs GITHUB_APP_JWT set to the JWT your own ' +
        'signing code produces');
    } else {
      // The JWT is sent and nothing else. Never decoded, stored or logged.
      const res = await fetch(`${API}/app`, {
        headers: {
          Authorization: `Bearer ${jwt}`,
          Accept: 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent': UA,
        },
      });
      let body = null;
      try { body = await res.json(); } catch { body = null; }
      const message = body && typeof body === 'object' ? body.message : null;
      console.log(`GET /app returned ${res.status}`);
      const [liveState, liveDetail] = interpret(res.status, message);
      console.log(`${liveState}: ${liveDetail}`);
    }
  }

  if (state === 'iat-lands-in-the-future' || state === 'backdate-has-no-headroom') {
    console.log(`repair: set iat to now minus ` +
      `${backdateNeeded(best.skew, best.uncertainty)}s when minting, then ` +
      'install time sync on this host so the offset stops moving');
  }

  console.log(JSON.stringify({
    skew_seconds: best.skew,
    uncertainty_seconds: best.uncertainty,
    round_trip_seconds: best.round_trip,
    samples: samples.length,
    backdate_seconds: backdate,
    drift_ppm: ppm,
    state,
  }, null, 2));
  process.exitCode = (state === 'clock-in-sync' || state === 'drift-absorbed-by-backdate') ? 0 : 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and set an exit code that fails a passing suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "There is no credential anywhere in these tests, because there is none in the measurement either. Every case is three numbers &mdash; a server time and the two local times either side of the request &mdash; so a host forty seconds fast, a host five hours out by timezone and a network too slow to resolve either are all one line each. The two rules worth pinning are that the fastest exchange wins rather than the average, and that a drift rate over a four second span is refused rather than reported.",
"test_py_file": "test_github_clock_skew.py",
"test_py": '''from github_clock_skew import (
    GRACE, backdate_needed, best_sample, classify, classify_rate, drift_rate,
    interpret, parse_http_date, sample_skew, timezone_suspect,
)

NOW = 1_772_000_000.0


def test_a_date_header_parses_to_epoch_seconds():
    assert parse_http_date("Thu, 01 Jan 1970 00:00:10 GMT") == 10.0
    assert parse_http_date("not a date") is None
    assert parse_http_date("") is None
    assert parse_http_date(None) is None


def test_one_exchange_becomes_an_offset_with_an_error_bar():
    s = sample_skew(NOW, NOW + 40.0, NOW + 40.4)
    assert s["skew"] == 40.2
    assert s["uncertainty"] == 1.2
    assert s["round_trip"] == 0.4


def test_a_response_without_a_date_produces_no_sample():
    assert sample_skew(None, NOW, NOW + 0.2) is None


def test_the_fastest_exchange_wins_rather_than_the_average():
    slow = sample_skew(NOW, NOW + 40.0, NOW + 44.0)
    quick = sample_skew(NOW, NOW + 40.0, NOW + 40.1)
    assert best_sample([slow, quick, None])["round_trip"] == 0.1
    assert best_sample([]) is None
    assert best_sample([None]) is None


def test_a_host_running_fast_with_no_backdate_is_the_headline_finding():
    state, detail = classify(40.0, 1.0, 0)
    assert state == "iat-lands-in-the-future"
    assert "41.0s into GitHub" in detail


def test_the_same_offset_is_harmless_once_iat_is_backdated():
    state, detail = classify(40.0, 1.0, 60)
    assert state == "drift-absorbed-by-backdate"
    assert "19.0s to spare" in detail


def test_a_backdate_that_only_just_covers_the_drift_is_still_flagged():
    assert classify(58.0, 1.0, 60)[0] == "backdate-has-no-headroom"


def test_a_slow_path_cannot_resolve_a_small_offset():
    # Three seconds of skew measured over a six second round trip is inside
    # the error bar, so the honest answer is that the clocks agree.
    assert classify(3.0, 4.0, 60)[0] == "clock-in-sync"


def test_a_clock_behind_github_is_its_own_state_and_its_own_consequence():
    state, detail = classify(-45.0, 1.0, 60)
    assert state == "clock-behind-github"
    assert "already spent 45.0s" in detail


def test_whole_hours_are_a_timezone_and_not_drift():
    assert timezone_suspect(-18000.0) == -5.0
    assert timezone_suspect(19800.0) == 5.5
    assert timezone_suspect(41.0) is None
    assert timezone_suspect(2400.0) is None
    state, detail = classify(18000.0, 1.0, 60)
    assert state == "timezone-not-drift"
    assert "naive local datetime" in detail


def test_the_backdate_recommendation_covers_the_offset_and_its_error_bar():
    assert backdate_needed(5.0, 1.0) == 60
    assert backdate_needed(200.0, 2.0) == 210
    assert backdate_needed(-30.0, 1.0) == 60


def test_a_rate_is_refused_when_the_samples_are_too_close_together():
    readings = [(NOW, 10.0), (NOW + 4, 10.4)]
    assert drift_rate(readings) is None
    state, detail = classify_rate(None)
    assert state == "rate-not-measurable"
    assert "60s" in detail


def test_a_growing_offset_is_reported_as_a_free_running_clock():
    readings = [(NOW, 10.0), (NOW + 100, 10.05)]
    ppm = drift_rate(readings)
    assert ppm == 500.0
    state, detail = classify_rate(ppm)
    assert state == "clock-is-running-free"
    assert "43.2 seconds a day" in detail


def test_a_static_offset_says_the_clock_was_set_wrong_once():
    readings = [(NOW, 40.0), (NOW + 600, 40.0)]
    assert classify_rate(drift_rate(readings))[0] == "offset-is-static"


def test_an_unmeasurable_clock_says_so_rather_than_guessing():
    state, _ = classify(None, 1.0, 60)
    assert state == "unmeasurable"


def test_the_live_messages_separate_iat_from_its_neighbours():
    assert interpret(200, None)[0] == "accepted"
    assert interpret(401, "'Issued at' claim ('iat') must be an Integer "
                          "representing the time that the assertion was "
                          "issued")[0] == "github-refused-iat"
    assert interpret(401, "'Expiration time' claim ('exp') is too far in the "
                          "future")[0] == "lifetime-not-drift"
    assert interpret(401, "A JSON web token could not be "
                          "decoded")[0] == "key-or-encoding"
    assert interpret(404, "Integration not found")[0] == "issuer-does-not-resolve"
    assert interpret(403, "Resource not accessible by integration")[0] == "unrelated"


def test_the_grace_band_is_the_one_place_a_number_is_shared():
    assert GRACE == 5
''',
"test_js_file": "github-clock-skew.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  GRACE, backdateNeeded, bestSample, classify, classifyRate, driftRate,
  interpret, parseHttpDate, sampleSkew, timezoneSuspect,
} from './github-clock-skew.mjs';

const NOW = 1772000000;

test('a date header parses to epoch seconds', () => {
  assert.equal(parseHttpDate('Thu, 01 Jan 1970 00:00:10 GMT'), 10);
  assert.equal(parseHttpDate('not a date'), null);
  assert.equal(parseHttpDate(''), null);
  assert.equal(parseHttpDate(null), null);
});

test('one exchange becomes an offset with an error bar', () => {
  const s = sampleSkew(NOW, NOW + 40.0, NOW + 40.4);
  assert.equal(s.skew, 40.2);
  assert.equal(s.uncertainty, 1.2);
  assert.equal(s.round_trip, 0.4);
});

test('a response without a date produces no sample', () => {
  assert.equal(sampleSkew(null, NOW, NOW + 0.2), null);
});

test('the fastest exchange wins rather than the average', () => {
  const slow = sampleSkew(NOW, NOW + 40.0, NOW + 44.0);
  const quick = sampleSkew(NOW, NOW + 40.0, NOW + 40.1);
  assert.equal(bestSample([slow, quick, null]).round_trip, 0.1);
  assert.equal(bestSample([]), null);
  assert.equal(bestSample([null]), null);
});

test('a host running fast with no backdate is the headline finding', () => {
  const [state, detail] = classify(40.0, 1.0, 0);
  assert.equal(state, 'iat-lands-in-the-future');
  assert.match(detail, /41.0s into GitHub/);
});

test('the same offset is harmless once iat is backdated', () => {
  const [state, detail] = classify(40.0, 1.0, 60);
  assert.equal(state, 'drift-absorbed-by-backdate');
  assert.match(detail, /19.0s to spare/);
});

test('a backdate that only just covers the drift is still flagged', () => {
  assert.equal(classify(58.0, 1.0, 60)[0], 'backdate-has-no-headroom');
});

test('a slow path cannot resolve a small offset', () => {
  assert.equal(classify(3.0, 4.0, 60)[0], 'clock-in-sync');
});

test('a clock behind github is its own state and its own consequence', () => {
  const [state, detail] = classify(-45.0, 1.0, 60);
  assert.equal(state, 'clock-behind-github');
  assert.match(detail, /already spent 45.0s/);
});

test('whole hours are a timezone and not drift', () => {
  assert.equal(timezoneSuspect(-18000), -5);
  assert.equal(timezoneSuspect(19800), 5.5);
  assert.equal(timezoneSuspect(41), null);
  assert.equal(timezoneSuspect(2400), null);
  const [state, detail] = classify(18000, 1.0, 60);
  assert.equal(state, 'timezone-not-drift');
  assert.match(detail, /naive local datetime/);
});

test('the backdate recommendation covers the offset and its error bar', () => {
  assert.equal(backdateNeeded(5, 1), 60);
  assert.equal(backdateNeeded(200, 2), 210);
  assert.equal(backdateNeeded(-30, 1), 60);
});

test('a rate is refused when the samples are too close together', () => {
  assert.equal(driftRate([[NOW, 10.0], [NOW + 4, 10.4]]), null);
  const [state, detail] = classifyRate(null);
  assert.equal(state, 'rate-not-measurable');
  assert.match(detail, /60s/);
});

test('a growing offset is reported as a free running clock', () => {
  const ppm = driftRate([[NOW, 10.0], [NOW + 100, 10.05]]);
  assert.equal(ppm, 500);
  const [state, detail] = classifyRate(ppm);
  assert.equal(state, 'clock-is-running-free');
  assert.match(detail, /43.2 seconds a day/);
});

test('a static offset says the clock was set wrong once', () => {
  assert.equal(classifyRate(driftRate([[NOW, 40], [NOW + 600, 40]]))[0], 'offset-is-static');
});

test('an unmeasurable clock says so rather than guessing', () => {
  assert.equal(classify(null, 1.0, 60)[0], 'unmeasurable');
});

test('the live messages separate iat from its neighbours', () => {
  assert.equal(interpret(200, null)[0], 'accepted');
  assert.equal(interpret(401,
    "'Issued at' claim ('iat') must be an Integer representing the time that the assertion was issued")[0],
  'github-refused-iat');
  assert.equal(interpret(401, "'Expiration time' claim ('exp') is too far in the future")[0],
    'lifetime-not-drift');
  assert.equal(interpret(401, 'A JSON web token could not be decoded')[0], 'key-or-encoding');
  assert.equal(interpret(404, 'Integration not found')[0], 'issuer-does-not-resolve');
  assert.equal(interpret(403, 'Resource not accessible by integration')[0], 'unrelated');
});

test('the grace band is the one place a number is shared', () => {
  assert.equal(GRACE, 5);
});
''',
"faq": [
 ("How far ahead does the clock have to be before GitHub refuses the JWT?",
  "In practice, any amount at all, because there is no published tolerance to rely on and the comparison is against a moment that has to have already happened. A host a second fast fails only when the request arrives before GitHub's own second ticks over, so it fails intermittently rather than never, which is worse. That is the whole reason the documented advice is to set iat sixty seconds in the past: it is not a tolerance you are given, it is one you build yourself, and it costs nothing because the JWT is discarded after the exchange anyway."),
 ("Why measure against the Date header rather than an NTP server?",
  "Because the clock that matters is GitHub's, and the Date header is GitHub's clock stated directly. An NTP server tells you your offset from a reference that GitHub is also tracking, which is nearly always the same answer, but it needs UDP 123 open outbound and it does not run from inside a locked-down build container. A GET you are already able to make does, and GET /rate_limit answers unauthenticated without consuming quota, so the check can run as a startup probe on every host that signs."),
 ("The offset it reports is about two seconds and my clock is fine. Is that real?",
  "Probably not, and the uncertainty figure is there to tell you. The Date header is truncated to the whole second, so a reading can be up to a second off before the network is considered at all, and half the round trip is added on top of that. When the offset is smaller than the uncertainty the script says the clocks agree rather than reporting the number as a finding. If you want a tighter measurement, take more samples from a host with a quiet path and let it keep the fastest exchange."),
 ("Should I fix the container's clock or the host's?",
  "The host's, because a container does not have one. Containers share the kernel's clock, so a container cannot be fast relative to the machine it runs on; what you are seeing is the machine being fast, and it will be fast for every container on it. Virtual machines are where this usually comes from: a suspended and resumed VM wakes up with the time it went to sleep with, and a hypervisor without guest time sync leaves it there. Fix time sync on the node and the whole fleet moves at once."),
 ("Can I just retry until the JWT is accepted?",
  "It will appear to work and it will hide the fault for a year. A retry loop against a clock a few seconds fast succeeds roughly whenever the network is slow enough for GitHub's second to tick over first, so the failure rate drops to something that looks like ordinary upstream noise and the real offset keeps growing underneath. It also spends real time on every token exchange in a hot path. Backdating iat fixes it in one line and costs nothing, which is why the retry loop is not worth writing."),
],
"related": [
 ("/github/jwt-exp-too-far-future/", "A JWT that asks to live for an hour"),
 ("/github/jwt-wrong-key-or-algorithm/", "A JWT signed with the wrong key"),
 ("/github/bad-credentials-401/", "401 Bad credentials on every endpoint"),
],
"citations": [CITE_JWT, CITE_APP_AUTH, CITE_HTTP_DATE, CITE_RATE_LIMITS],
},

{
"slug": "jwt-wrong-key-or-algorithm",
"title": "The App JWT is signed with the wrong key or algorithm",
"description": "A JSON web token could not be decoded means the key is not the one registered on that App. Fingerprint the PEM, then ask GET /app which App you are.",
"h1": "the App JWT is signed with the wrong key or algorithm",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["a json web token could not be decoded github app",
             "github app integration not found jwt",
             "github app private key newlines environment variable",
             "github app jwt rs256", "github app wrong private key"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "It worked until the key was rotated. Now every call is <code>401 {\"message\": \"A JSON web token could not be decoded\"}</code>, or occasionally <code>404 {\"message\": \"Integration not found\"}</code>, and the two arrive from what looks like the same deployment. The key is in the environment. The App exists. Somebody has already pasted the PEM into three different terminals to check it looks right.",
"short_answer": """<p>GitHub verified nothing, because it could not. That message means the JWT did not survive verification against any key currently registered on the App named in <code>iss</code> &mdash; a key from a different App, a key that was revoked when a new one was generated, an <code>HS256</code> default in the signing library, or, most often, a PEM whose newlines were destroyed on the way into an environment variable. <em>Integration not found</em> is the neighbouring case: <code>iss</code> does not name an App at all.</p>
<p>Look at the key before you look at the request. Its PEM label says whether it is even an RSA private key; its line count says whether the newlines survived; the SHA-256 of its DER body is a fingerprint you can compare between a laptop and a container without either of them printing a secret. Then one <code>GET /app</code> under the JWT settles the rest, because a 200 there returns the App you actually authenticated as &mdash; which is not always the App you meant.</p>""",
"problem": """<p>The message is a dead end on purpose. GitHub will not say which part of the verification failed, because telling an unauthenticated caller <em>the algorithm was wrong</em> rather than <em>the signature was wrong</em> is a small oracle it has no reason to hand out. So one sentence covers a wrong key, a revoked key, a key from the staging App, an unexpected algorithm and a mangled PEM, and none of those five is visibly different from the others.</p>
<p>The environment variable is the usual culprit and it is invisible in exactly the way that wastes the most time. A PEM is meaningful only because of its line breaks, and every layer between a settings page and a running process is capable of turning those into the two characters backslash and n: a <code>.env</code> file, a CI secret editor, a Kubernetes manifest quoted one way instead of another, a shell that helpfully collapsed the value. The variable is set. Its length looks about right. It is not a key any more.</p>
<p>And the successful case is not proof either. Teams that run a staging App and a production App keep both keys in the same shape of variable with the same name, and a JWT signed with the staging key against the staging App succeeds. Everything works, against the wrong installation set, on the wrong account, and nothing in a 200 announces that. That is why the script asks which App answered rather than only whether one did.</p>""",
"why": """<p><strong>The key has to be registered on the App named in <code>iss</code>.</strong> Those two facts travel separately: <code>iss</code> is a claim your code wrote, and the key is a file your deployment shipped. Nothing checks that they belong together until GitHub does, and when they do not match the failure is the generic decode message rather than anything that names either half.</p>
<p><strong>Generating a new key does not retire the old one, but deleting it does.</strong> An App can hold several private keys at once, which is what makes rotation safe: add the new one, deploy, then remove the old. Rotations that skip the middle step produce exactly this 401 on every host that has not been redeployed yet, and a rotation done in the wrong order produces it on all of them.</p>
<p><strong>Only <code>RS256</code> is accepted.</strong> A JWT library whose default is <code>HS256</code> will happily sign with the PEM's bytes treated as a shared secret and produce a token that is well formed and unverifiable. Pinning the algorithm explicitly costs one argument and removes a class of failure that otherwise looks identical to a wrong key.</p>
<p><strong>A fingerprint is safe to print and a key is not.</strong> The SHA-256 of the DER body identifies a key file without revealing anything about it, which is what makes it the right thing to log: you can compare the fingerprint on a developer machine against the one in a container and settle whether they are the same file, in a channel where nobody would paste a key.</p>
<p><strong>What a read-only script cannot see.</strong> GitHub does not publish an App's registered public keys, so nothing here can prove a key is registered except by using it. That is the blind spot, and it is the reason the live half of this check is a single <code>GET /app</code>: a 200 is the proof, and a 401 narrows the cause to the list above without picking one. The claim arithmetic that produces its own 401s belongs to <a href="/github/jwt-exp-too-far-future/">the note on a JWT that lives too long</a> and to <a href="/github/jwt-clock-drift-iat/">the note on clock drift</a>, and this script names those messages when it sees them rather than absorbing them.</p>""",
"steps": [
 {"h": "Read the PEM's label before anything else",
  "body": """<p><code>BEGIN RSA PRIVATE KEY</code> is what GitHub hands you. <code>BEGIN PRIVATE KEY</code> is the same key in a PKCS#8 wrapper and every sensible library accepts it. <code>BEGIN OPENSSH PRIVATE KEY</code> means somebody ran <code>ssh-keygen</code>, <code>BEGIN PUBLIC KEY</code> means the wrong half of the pair got deployed, and <code>BEGIN EC PRIVATE KEY</code> means a key that cannot sign <code>RS256</code> at all. Four of those never work and are visible in one line.</p>"""},
 {"h": "Count the lines",
  "body": """<p>A real PEM is many short lines. One line means the newlines are gone, and the two characters backslash and n appearing anywhere in the value means they were escaped rather than embedded. Both are the same deployment fault with the same repair: base64-encode the whole PEM for transport and decode it in the process, so no layer in between ever has an opinion about newlines.</p>"""},
 {"h": "Fingerprint it and compare the fingerprint, not the key",
  "body": """<p>Take the SHA-256 of the decoded DER body and print the first sixteen hex characters. That is enough to tell two keys apart and useless to anybody who intercepts it. Run the script on the machine that works and the machine that does not; if the fingerprints differ you have already found the problem and nobody had to paste a key anywhere.</p>"""},
 {"h": "Send one GET /app and read which App answered",
  "body": """<p>A 200 returns the App: its numeric <code>id</code>, its <code>client_id</code>, its <code>slug</code> and its owner. Compare that against the App you meant, by name or by id. This is the step that catches a working credential for the wrong environment, which is the only failure in this note that produces no error at all.</p>"""},
 {"h": "Pin the algorithm and set iss to the client ID",
  "body": """<p>Pass <code>RS256</code> explicitly rather than accepting a library default. Use the App's client ID as <code>iss</code>, which is the current recommendation; the numeric App ID still works. Anything else &mdash; a slug, an installation ID, an owner name &mdash; produces <em>Integration not found</em>, which at least tells you the claim rather than the key is wrong.</p>"""},
],
"verify": """<p>Re-run after the key is deployed with its newlines intact. The PEM state moves from <code>escaped-newlines</code> to <code>pkcs1-rsa-key</code>, and the live check names the App you expected.</p>
<pre><code class="language-bash">python3 github_app_key_identity.py --expect acme-deploy-bot
# key: label=RSA PRIVATE KEY fingerprint=3f9a1c04e7b25d18 der=1192B lines=28
# pkcs1-rsa-key: this is the PKCS#1 RSA private key GitHub issues.
# GET /app returned 200
# key-accepted: the JWT verified against a key registered on this App.
# identity-matches: GET /app answered as acme-deploy-bot (id 123456).</code></pre>""",
"code_intro": "Two halves that never touch a secret in the output. The first is structural and offline: a PEM is a label, a run of base64 and an end line, so the label lookup, the line count, the base64 decode and the SHA-256 fingerprint are all pure functions over a string, and every one of them can fail in a way worth naming. The second is a single <code>GET /app</code>, whose only job is to say which App the JWT authenticated as. The key is read from the environment, never written to a file and never printed; what the report contains is a label, a line count, a byte count and sixteen hex characters.",
"py_file": "github_app_key_identity.py",
"py": '''"""Say which GitHub App a private key belongs to, without printing the key.

Read only. One request, GET /app, sent with a JWT you already hold. Nothing is
minted, rotated, registered or changed, and the script never signs anything
itself: it inspects the key file and asks GitHub who answered.

The output contains a PEM label, a line count, a byte count and a truncated
SHA-256 fingerprint. It never contains the key, any part of the key, or the
JWT. A fingerprint is the right thing to compare across machines precisely
because it can be pasted into a chat window without consequence.

The blind spot is stated rather than worked around: GitHub does not publish the
public keys registered on an App, so nothing here can prove a key is registered
except by using it. A 200 from GET /app is that proof. A 401 narrows the cause
to a short list without choosing between its entries.
"""
import argparse
import base64
import hashlib
import json
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_app_key_identity")

API = "https://api.github.com"
UA = "github-app-key-identity/1.0"

# The two characters backslash and n, which is what an environment variable
# holds when a PEM's newlines were escaped rather than embedded. This is the
# single most common way a working key stops being a key.
ESCAPED_NEWLINE = "\\\\n"

# A 2048-bit RSA private key is around 1200 bytes of DER. Anything much under
# this is a different kind of key or a truncated one.
MIN_RSA_DER = 500

# The labels GitHub's own key downloads carry, and the one PKCS#8 alternative
# that every library still accepts.
USABLE_LABELS = {"RSA PRIVATE KEY": "pkcs1-rsa-key", "PRIVATE KEY": "pkcs8-key"}

REPAIRS = {
    "no-key-present":
        "set GITHUB_APP_PRIVATE_KEY to the PEM downloaded from the App's "
        "settings page. Nothing can be said about a key that is not there.",
    "escaped-newlines":
        "the value contains the two characters backslash and n where line "
        "breaks belong, so some layer between the settings page and this "
        "process escaped them. Base64-encode the whole PEM for transport and "
        "decode it in the process; then no layer in between has an opinion.",
    "single-line-pem":
        "the PEM has lost its line breaks entirely. Same repair: carry it "
        "base64-encoded rather than raw.",
    "not-a-pem":
        "there is no BEGIN line, so this is not a PEM at all. Check what the "
        "secret store actually returned.",
    "truncated-pem":
        "there is a BEGIN line and no matching END line, so the value was cut "
        "short. Secret stores with a length limit do this quietly.",
    "encrypted-key":
        "this key is passphrase-protected. GitHub does not issue encrypted "
        "keys, so this one was re-encrypted locally; decrypt it or download a "
        "fresh key from the App.",
    "openssh-format":
        "this is an OpenSSH key, which is what ssh-keygen produces. It is not "
        "the key GitHub issued for the App. Download the App's private key "
        "from its settings page.",
    "public-key-not-private":
        "this is the public half of a pair. The public key cannot sign, so no "
        "JWT made with it will ever verify.",
    "certificate-not-key":
        "this is a certificate rather than a key. Something is reading the "
        "wrong entry out of the secret store.",
    "not-an-rsa-key":
        "GitHub App JWTs must be signed RS256, which needs an RSA key. This "
        "key uses a different algorithm family and cannot sign one.",
    "unknown-pem-label":
        "the PEM label is not one this check recognises, which usually means "
        "the wrong file entirely.",
    "body-not-base64":
        "the body between the BEGIN and END lines is not valid base64, so the "
        "PEM was corrupted in transit or edited by hand.",
    "too-small-for-rsa":
        "the decoded body is too small to be an RSA private key of any usable "
        "size, so this is either truncated or a different kind of key.",
    "pkcs1-rsa-key":
        "this is the PKCS#1 RSA private key GitHub issues.",
    "pkcs8-key":
        "this is a PKCS#8 wrapper, which every sensible JWT library accepts.",
}


def unwrap(text):
    """Undo base64 transport if the value is a wrapped PEM. Pure.

    Carrying a PEM base64-encoded is the recommended way to survive an
    environment variable, so a value with no BEGIN line that decodes to one is
    not an error. Returns the PEM and whether it was wrapped.
    """
    raw = str(text or "").strip()
    if not raw or "BEGIN" in raw:
        return raw, False
    try:
        decoded = base64.b64decode(raw, validate=True).decode("utf-8")
    except Exception:
        return raw, False
    if "BEGIN" in decoded:
        return decoded, True
    return raw, False


def inspect_pem(text):
    """Reduce a PEM to a label, a shape and a fingerprint. Pure.

    Never returns any part of the key. The fingerprint is the SHA-256 of the
    decoded DER body, truncated, which identifies the file without revealing
    it and is therefore safe to compare in a chat window.
    """
    raw = str(text or "")
    out = {"state": None, "label": None, "fingerprint": None,
           "der_bytes": None, "lines": 0}
    if not raw.strip():
        out["state"] = "no-key-present"
        return out
    out["lines"] = len(raw.strip().splitlines())
    if ESCAPED_NEWLINE in raw:
        out["state"] = "escaped-newlines"
        return out

    found = re.search(r"-----BEGIN ([A-Z0-9 ]+)-----", raw)
    if not found:
        out["state"] = "not-a-pem"
        return out
    label = found.group(1).strip()
    out["label"] = label

    if label == "ENCRYPTED PRIVATE KEY" or "Proc-Type: 4,ENCRYPTED" in raw:
        out["state"] = "encrypted-key"
        return out
    if label == "OPENSSH PRIVATE KEY":
        out["state"] = "openssh-format"
        return out
    if label.endswith("PUBLIC KEY"):
        out["state"] = "public-key-not-private"
        return out
    if label == "CERTIFICATE":
        out["state"] = "certificate-not-key"
        return out
    if label in ("EC PRIVATE KEY", "DSA PRIVATE KEY"):
        out["state"] = "not-an-rsa-key"
        return out
    if label not in USABLE_LABELS:
        out["state"] = "unknown-pem-label"
        return out
    if ("-----END " + label + "-----") not in raw:
        out["state"] = "truncated-pem"
        return out
    if out["lines"] < 3:
        out["state"] = "single-line-pem"
        return out

    body = "".join(line.strip() for line in raw.splitlines()
                   if line.strip() and not line.strip().startswith("-----"))
    try:
        der = base64.b64decode(body, validate=True)
    except Exception:
        out["state"] = "body-not-base64"
        return out
    out["der_bytes"] = len(der)
    out["fingerprint"] = hashlib.sha256(der).hexdigest()[:16]
    if len(der) < MIN_RSA_DER:
        out["state"] = "too-small-for-rsa"
        return out
    out["state"] = USABLE_LABELS[label]
    return out


def usable(state):
    """Whether a key in this state could sign an RS256 JWT at all. Pure."""
    return state in ("pkcs1-rsa-key", "pkcs8-key")


def repair_for(state):
    """The one sentence worth printing under a PEM state. Pure."""
    return REPAIRS.get(state, "this state has no stock repair; read the label.")


def issuer_form(value):
    """Classify what was put in the iss claim. Pure.

    iss must be the App's client ID or its numeric App ID. A slug, an owner
    name or an installation ID all produce Integration not found, which is a
    different failure from a key that does not verify.
    """
    text = str(value or "").strip()
    if not text:
        return "no-issuer"
    if text.isdigit():
        return "app-id"
    if text.startswith("Iv1.") or text.startswith("Iv23"):
        return "client-id"
    return "unusable-issuer"


def interpret(status, message):
    """Map a GET /app response to the defect it names. Pure.

    GitHub deliberately will not say which part of verification failed, so the
    decode message covers five causes at once and this function says so rather
    than picking one. The claim messages are named only to hand them off.
    """
    if status == 200:
        return ("key-accepted",
                "the JWT verified against a key registered on this App.")
    text = str(message or "").lower()
    if "could not be decoded" in text:
        return ("signature-rejected",
                "GitHub could not verify the JWT. That one message covers a "
                "key from another App, a key deleted during rotation, an "
                "algorithm other than RS256, and a PEM whose newlines were "
                "destroyed. Compare the fingerprint against a machine that "
                "works to split the list.")
    if "integration not found" in text:
        return ("issuer-does-not-resolve",
                "iss does not name an App GitHub can find, so the claim is "
                "wrong rather than the key. It must be the client ID or the "
                "numeric App ID.")
    if "issued at" in text or "'iat'" in text:
        return ("clock-problem-not-key",
                "GitHub is complaining about iat, which is clock drift on the "
                "signing host and a different repair entirely.")
    if "too far in the future" in text:
        return ("lifetime-problem-not-key",
                "GitHub is complaining about exp, so the requested lifetime is "
                "over the ceiling and the key is fine.")
    if "bad credentials" in text:
        return ("not-a-jwt",
                "GitHub parsed the credential and refused it outright, which "
                "is what happens when an installation access token is sent to "
                "a route that wants the App JWT.")
    return ("unrelated",
            "the response does not name a key or a claim, so this failure has "
            "another cause.")


def reconcile(app, expected):
    """Say whether GET /app answered as the App you meant. Pure.

    The failure this catches makes no noise at all: a staging key against a
    staging App works perfectly, on the wrong account, with the wrong
    installations, and returns 200 the whole time.
    """
    if not isinstance(app, dict):
        return ("no-app-body",
                "GET /app returned nothing that could be read as an App.")
    label = "%s (id %s, client_id %s)" % (app.get("slug") or app.get("name"),
                                          app.get("id"), app.get("client_id"))
    known = {str(app.get(field) or "").lower()
             for field in ("id", "client_id", "slug", "name")}
    known.discard("")
    want = str(expected or "").strip().lower()
    if not want:
        return ("no-expectation-given",
                "GET /app answered as %s. Pass --expect to have that checked "
                "rather than reported." % label)
    if want in known:
        return ("identity-matches", "GET /app answered as %s." % label)
    return ("authenticated-as-another-app",
            "you expected %s and the key authenticated as %s. The credential "
            "works; it belongs to a different App, which is how a staging key "
            "reaches production without anything failing." % (expected, label))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--expect", default=None,
                    help="the App you believe this key belongs to, as a slug, "
                         "a name, a numeric id or a client id")
    ap.add_argument("--iss", default=None,
                    help="the value your signing code puts in the iss claim, "
                         "checked for shape only")
    ap.add_argument("--offline", action="store_true",
                    help="inspect the key and skip the confirming GET /app")
    args = ap.parse_args()

    pem, wrapped = unwrap(os.environ.get("GITHUB_APP_PRIVATE_KEY"))
    if wrapped:
        log.info("the key was carried base64-encoded, which is the shape that "
                 "survives an environment variable")
    key = inspect_pem(pem)
    log.info("key: label=%s fingerprint=%s der=%sB lines=%d",
             key["label"] or "none", key["fingerprint"] or "none",
             key["der_bytes"] if key["der_bytes"] is not None else "?",
             key["lines"])
    log.info("%s: %s", key["state"], repair_for(key["state"]))

    if args.iss is not None:
        form = issuer_form(args.iss)
        log.info("iss form: %s", form)
        if form == "unusable-issuer":
            log.info("repair: iss must be the App's client ID or its numeric "
                     "App ID. Anything else returns Integration not found.")

    live_state = None
    identity_state = None
    if not args.offline:
        jwt = os.environ.get("GITHUB_APP_JWT")
        if not jwt:
            log.warning("set GITHUB_APP_JWT to the JWT your signing code "
                        "produces, or pass --offline to inspect the key only")
        else:
            # The JWT is sent and nothing else. It is not decoded, stored or
            # logged, in whole or in part.
            r = requests.get(API + "/app", timeout=30, headers={
                "Authorization": "Bearer " + jwt,
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": UA,
            })
            try:
                body = r.json()
            except ValueError:
                body = None
            message = body.get("message") if isinstance(body, dict) else None
            log.info("GET /app returned %d", r.status_code)
            live_state, live_detail = interpret(r.status_code, message)
            log.info("%s: %s", live_state, live_detail)
            if r.status_code == 200:
                identity_state, identity_detail = reconcile(body, args.expect)
                log.info("%s: %s", identity_state, identity_detail)

    print(json.dumps({"label": key["label"], "fingerprint": key["fingerprint"],
                      "der_bytes": key["der_bytes"], "lines": key["lines"],
                      "key_state": key["state"], "live_state": live_state,
                      "identity_state": identity_state}, indent=2))
    ok = usable(key["state"]) and live_state in (None, "key-accepted") \\
        and identity_state != "authenticated-as-another-app"
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-app-key-identity.mjs",
"js": '''/**
 * Say which GitHub App a private key belongs to, without printing the key.
 *
 * Read only. One request, GET /app, sent with a JWT you already hold. The
 * script never signs anything itself: it inspects the key file and asks
 * GitHub who answered.
 *
 * The output contains a PEM label, a line count, a byte count and a truncated
 * SHA-256 fingerprint. It never contains the key or the JWT.
 *
 * The blind spot is stated rather than worked around: GitHub does not publish
 * the public keys registered on an App, so nothing here can prove a key is
 * registered except by using it.
 */
import { createHash } from 'node:crypto';

const API = 'https://api.github.com';
const UA = 'github-app-key-identity/1.0';

/** The two characters backslash and n, which is what an escaped PEM holds. */
export const ESCAPED_NEWLINE = '\\\\n';

/** A 2048-bit RSA private key is around 1200 bytes of DER. */
export const MIN_RSA_DER = 500;

/** The labels GitHub issues, and the PKCS#8 alternative libraries accept. */
export const USABLE_LABELS = {
  'RSA PRIVATE KEY': 'pkcs1-rsa-key',
  'PRIVATE KEY': 'pkcs8-key',
};

const REPAIRS = {
  'no-key-present':
    'set GITHUB_APP_PRIVATE_KEY to the PEM downloaded from the App\\'s ' +
    'settings page. Nothing can be said about a key that is not there.',
  'escaped-newlines':
    'the value contains the two characters backslash and n where line breaks ' +
    'belong, so some layer between the settings page and this process escaped ' +
    'them. Base64-encode the whole PEM for transport and decode it in the ' +
    'process; then no layer in between has an opinion.',
  'single-line-pem':
    'the PEM has lost its line breaks entirely. Same repair: carry it ' +
    'base64-encoded rather than raw.',
  'not-a-pem':
    'there is no BEGIN line, so this is not a PEM at all. Check what the ' +
    'secret store actually returned.',
  'truncated-pem':
    'there is a BEGIN line and no matching END line, so the value was cut ' +
    'short. Secret stores with a length limit do this quietly.',
  'encrypted-key':
    'this key is passphrase-protected. GitHub does not issue encrypted keys, ' +
    'so this one was re-encrypted locally; decrypt it or download a fresh key.',
  'openssh-format':
    'this is an OpenSSH key, which is what ssh-keygen produces. It is not the ' +
    'key GitHub issued for the App.',
  'public-key-not-private':
    'this is the public half of a pair. The public key cannot sign, so no JWT ' +
    'made with it will ever verify.',
  'certificate-not-key':
    'this is a certificate rather than a key. Something is reading the wrong ' +
    'entry out of the secret store.',
  'not-an-rsa-key':
    'GitHub App JWTs must be signed RS256, which needs an RSA key. This key ' +
    'uses a different algorithm family and cannot sign one.',
  'unknown-pem-label':
    'the PEM label is not one this check recognises, which usually means the ' +
    'wrong file entirely.',
  'body-not-base64':
    'the body between the BEGIN and END lines is not valid base64, so the PEM ' +
    'was corrupted in transit or edited by hand.',
  'too-small-for-rsa':
    'the decoded body is too small to be an RSA private key of any usable ' +
    'size, so this is either truncated or a different kind of key.',
  'pkcs1-rsa-key': 'this is the PKCS#1 RSA private key GitHub issues.',
  'pkcs8-key': 'this is a PKCS#8 wrapper, which every sensible JWT library accepts.',
};

/**
 * Undo base64 transport if the value is a wrapped PEM. Pure.
 * Returns [pem, wasWrapped].
 */
export function unwrap(text) {
  const raw = String(text ?? '').trim();
  if (!raw || raw.includes('BEGIN')) return [raw, false];
  try {
    const decoded = Buffer.from(raw, 'base64').toString('utf8');
    if (decoded.includes('BEGIN')) return [decoded, true];
  } catch {
    return [raw, false];
  }
  return [raw, false];
}

const isBase64 = (text) => /^[A-Za-z0-9+/]*={0,2}$/.test(text) && text.length % 4 === 0;

/**
 * Reduce a PEM to a label, a shape and a fingerprint. Pure.
 * Never returns any part of the key.
 */
export function inspectPem(text) {
  const raw = String(text ?? '');
  const out = { state: null, label: null, fingerprint: null, der_bytes: null, lines: 0 };
  if (!raw.trim()) {
    out.state = 'no-key-present';
    return out;
  }
  out.lines = raw.trim().split('\\n').length;
  if (raw.includes(ESCAPED_NEWLINE)) {
    out.state = 'escaped-newlines';
    return out;
  }
  const found = /-----BEGIN ([A-Z0-9 ]+)-----/.exec(raw);
  if (!found) {
    out.state = 'not-a-pem';
    return out;
  }
  const label = found[1].trim();
  out.label = label;

  if (label === 'ENCRYPTED PRIVATE KEY' || raw.includes('Proc-Type: 4,ENCRYPTED')) {
    out.state = 'encrypted-key';
    return out;
  }
  if (label === 'OPENSSH PRIVATE KEY') { out.state = 'openssh-format'; return out; }
  if (label.endsWith('PUBLIC KEY')) { out.state = 'public-key-not-private'; return out; }
  if (label === 'CERTIFICATE') { out.state = 'certificate-not-key'; return out; }
  if (label === 'EC PRIVATE KEY' || label === 'DSA PRIVATE KEY') {
    out.state = 'not-an-rsa-key';
    return out;
  }
  if (!(label in USABLE_LABELS)) { out.state = 'unknown-pem-label'; return out; }
  if (!raw.includes(`-----END ${label}-----`)) { out.state = 'truncated-pem'; return out; }
  if (out.lines < 3) { out.state = 'single-line-pem'; return out; }

  const body = raw.split('\\n').map((l) => l.trim())
    .filter((l) => l && !l.startsWith('-----')).join('');
  if (!isBase64(body)) { out.state = 'body-not-base64'; return out; }
  const der = Buffer.from(body, 'base64');
  out.der_bytes = der.length;
  out.fingerprint = createHash('sha256').update(der).digest('hex').slice(0, 16);
  if (der.length < MIN_RSA_DER) { out.state = 'too-small-for-rsa'; return out; }
  out.state = USABLE_LABELS[label];
  return out;
}

/** Whether a key in this state could sign an RS256 JWT at all. Pure. */
export function usable(state) {
  return state === 'pkcs1-rsa-key' || state === 'pkcs8-key';
}

/** The one sentence worth printing under a PEM state. Pure. */
export function repairFor(state) {
  return REPAIRS[state] ?? 'this state has no stock repair; read the label.';
}

/**
 * Classify what was put in the iss claim. Pure.
 * It must be the client ID or the numeric App ID; anything else returns
 * Integration not found, which is a different failure from a bad key.
 */
export function issuerForm(value) {
  const text = String(value ?? '').trim();
  if (!text) return 'no-issuer';
  if (/^\\d+$/.test(text)) return 'app-id';
  if (text.startsWith('Iv1.') || text.startsWith('Iv23')) return 'client-id';
  return 'unusable-issuer';
}

/** Map a GET /app response to the defect it names. Pure. */
export function interpret(status, message) {
  if (status === 200) {
    return ['key-accepted', 'the JWT verified against a key registered on this App.'];
  }
  const text = String(message ?? '').toLowerCase();
  if (text.includes('could not be decoded')) {
    return ['signature-rejected',
      'GitHub could not verify the JWT. That one message covers a key from ' +
      'another App, a key deleted during rotation, an algorithm other than ' +
      'RS256, and a PEM whose newlines were destroyed. Compare the ' +
      'fingerprint against a machine that works to split the list.'];
  }
  if (text.includes('integration not found')) {
    return ['issuer-does-not-resolve',
      'iss does not name an App GitHub can find, so the claim is wrong rather ' +
      'than the key. It must be the client ID or the numeric App ID.'];
  }
  if (text.includes('issued at') || text.includes("'iat'")) {
    return ['clock-problem-not-key',
      'GitHub is complaining about iat, which is clock drift on the signing ' +
      'host and a different repair entirely.'];
  }
  if (text.includes('too far in the future')) {
    return ['lifetime-problem-not-key',
      'GitHub is complaining about exp, so the requested lifetime is over the ' +
      'ceiling and the key is fine.'];
  }
  if (text.includes('bad credentials')) {
    return ['not-a-jwt',
      'GitHub parsed the credential and refused it outright, which is what ' +
      'happens when an installation access token is sent to a route that ' +
      'wants the App JWT.'];
  }
  return ['unrelated',
    'the response does not name a key or a claim, so this failure has another cause.'];
}

/** Say whether GET /app answered as the App you meant. Pure. */
export function reconcile(app, expected) {
  if (!app || typeof app !== 'object' || Array.isArray(app)) {
    return ['no-app-body', 'GET /app returned nothing that could be read as an App.'];
  }
  const label = `${app.slug ?? app.name} (id ${app.id}, client_id ${app.client_id})`;
  const known = new Set(['id', 'client_id', 'slug', 'name']
    .map((field) => String(app[field] ?? '').toLowerCase())
    .filter(Boolean));
  const want = String(expected ?? '').trim().toLowerCase();
  if (!want) {
    return ['no-expectation-given',
      `GET /app answered as ${label}. Pass --expect to have that checked ` +
      'rather than reported.'];
  }
  if (known.has(want)) return ['identity-matches', `GET /app answered as ${label}.`];
  return ['authenticated-as-another-app',
    `you expected ${expected} and the key authenticated as ${label}. The ` +
    'credential works; it belongs to a different App, which is how a staging ' +
    'key reaches production without anything failing.'];
}

function flag(name) {
  const at = process.argv.indexOf(name);
  return (at === -1 || at === process.argv.length - 1) ? null : process.argv[at + 1];
}

async function main() {
  const [pem, wrapped] = unwrap(process.env.GITHUB_APP_PRIVATE_KEY);
  if (wrapped) {
    console.log('the key was carried base64-encoded, which is the shape that ' +
      'survives an environment variable');
  }
  const key = inspectPem(pem);
  console.log(`key: label=${key.label ?? 'none'} ` +
    `fingerprint=${key.fingerprint ?? 'none'} ` +
    `der=${key.der_bytes ?? '?'}B lines=${key.lines}`);
  console.log(`${key.state}: ${repairFor(key.state)}`);

  const iss = flag('--iss');
  if (iss !== null) {
    const form = issuerForm(iss);
    console.log(`iss form: ${form}`);
    if (form === 'unusable-issuer') {
      console.log('repair: iss must be the App\\'s client ID or its numeric ' +
        'App ID. Anything else returns Integration not found.');
    }
  }

  let liveState = null;
  let identityState = null;
  if (!process.argv.includes('--offline')) {
    const jwt = process.env.GITHUB_APP_JWT;
    if (!jwt) {
      console.error('set GITHUB_APP_JWT to the JWT your signing code produces, ' +
        'or pass --offline to inspect the key only');
    } else {
      // The JWT is sent and nothing else. Never decoded, stored or logged.
      const res = await fetch(`${API}/app`, {
        headers: {
          Authorization: `Bearer ${jwt}`,
          Accept: 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent': UA,
        },
      });
      let body = null;
      try { body = await res.json(); } catch { body = null; }
      const message = body && typeof body === 'object' ? body.message : null;
      console.log(`GET /app returned ${res.status}`);
      const [state, detail] = interpret(res.status, message);
      liveState = state;
      console.log(`${state}: ${detail}`);
      if (res.status === 200) {
        const [idState, idDetail] = reconcile(body, flag('--expect'));
        identityState = idState;
        console.log(`${idState}: ${idDetail}`);
      }
    }
  }

  console.log(JSON.stringify({
    label: key.label,
    fingerprint: key.fingerprint,
    der_bytes: key.der_bytes,
    lines: key.lines,
    key_state: key.state,
    live_state: liveState,
    identity_state: identityState,
  }, null, 2));
  const ok = usable(key.state)
    && (liveState === null || liveState === 'key-accepted')
    && identityState !== 'authenticated-as-another-app';
  process.exitCode = ok ? 0 : 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and set an exit code that fails a passing suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The fixtures are PEMs and none of them is a key: the body is a run of filler bytes long enough to pass the size check, so every case &mdash; an OpenSSH key, a public key, a certificate, a PEM whose newlines were escaped, one that was cut short &mdash; is three lines and carries no secret. The fingerprint is asserted to be stable and to differ between two different bodies, which is the only property it needs to have. Nothing signs, nothing verifies, and no test touches the network.",
"test_py_file": "test_github_app_key_identity.py",
"test_js_file": "github-app-key-identity.test.mjs",
"test_py": '''import base64

from github_app_key_identity import (
    ESCAPED_NEWLINE, inspect_pem, interpret, issuer_form, reconcile, repair_for,
    unwrap, usable,
)

FILLER = base64.b64encode(b"x" * 1200).decode()


def pem(label, body=None):
    """An obviously fake PEM: a real label and a run of filler bytes."""
    chunk = body if body is not None else FILLER
    rows = [chunk[i:i + 64] for i in range(0, len(chunk), 64)]
    return "-----BEGIN %s-----\\n%s\\n-----END %s-----\\n" % (
        label, "\\n".join(rows), label)


def test_the_key_github_issues_is_recognised_and_fingerprinted():
    out = inspect_pem(pem("RSA PRIVATE KEY"))
    assert out["state"] == "pkcs1-rsa-key"
    assert out["label"] == "RSA PRIVATE KEY"
    assert len(out["fingerprint"]) == 16
    assert out["der_bytes"] >= 500
    assert usable(out["state"])


def test_a_pkcs8_wrapper_is_the_same_key_and_is_accepted():
    assert inspect_pem(pem("PRIVATE KEY"))["state"] == "pkcs8-key"


def test_the_fingerprint_identifies_the_file_and_nothing_else():
    one = inspect_pem(pem("RSA PRIVATE KEY"))["fingerprint"]
    again = inspect_pem(pem("RSA PRIVATE KEY"))["fingerprint"]
    other = inspect_pem(pem("RSA PRIVATE KEY",
                            base64.b64encode(b"y" * 1200).decode()))["fingerprint"]
    assert one == again
    assert one != other


def test_escaped_newlines_are_the_headline_deployment_fault():
    flattened = pem("RSA PRIVATE KEY").replace("\\n", ESCAPED_NEWLINE)
    out = inspect_pem(flattened)
    assert out["state"] == "escaped-newlines"
    assert "backslash and n" in repair_for(out["state"])


def test_a_pem_collapsed_onto_one_line_is_told_apart_from_an_escaped_one():
    collapsed = pem("RSA PRIVATE KEY").replace("\\n", " ")
    assert inspect_pem(collapsed)["state"] == "single-line-pem"


def test_the_wrong_kind_of_key_is_named_rather_than_guessed_at():
    assert inspect_pem(pem("OPENSSH PRIVATE KEY"))["state"] == "openssh-format"
    assert inspect_pem(pem("PUBLIC KEY"))["state"] == "public-key-not-private"
    assert inspect_pem(pem("EC PRIVATE KEY"))["state"] == "not-an-rsa-key"
    assert inspect_pem(pem("CERTIFICATE"))["state"] == "certificate-not-key"
    assert inspect_pem(pem("ENCRYPTED PRIVATE KEY"))["state"] == "encrypted-key"
    assert inspect_pem(pem("DH PARAMETERS"))["state"] == "unknown-pem-label"
    for state in ("openssh-format", "public-key-not-private", "not-an-rsa-key"):
        assert not usable(state)


def test_a_truncated_pem_is_caught_before_its_body_is_read():
    cut = pem("RSA PRIVATE KEY").split("-----END")[0]
    assert inspect_pem(cut)["state"] == "truncated-pem"


def test_a_body_that_is_not_base64_says_so():
    assert inspect_pem(pem("RSA PRIVATE KEY", "not base64 at all"))["state"] \\
        in ("body-not-base64", "too-small-for-rsa")


def test_something_far_too_small_to_be_an_rsa_key_is_rejected():
    small = base64.b64encode(b"z" * 64).decode()
    out = inspect_pem(pem("RSA PRIVATE KEY", small))
    assert out["state"] == "too-small-for-rsa"
    assert out["fingerprint"] is not None


def test_an_absent_key_is_a_state_and_not_a_crash():
    assert inspect_pem("")["state"] == "no-key-present"
    assert inspect_pem(None)["state"] == "no-key-present"
    assert inspect_pem("just some text")["state"] == "not-a-pem"


def test_a_base64_wrapped_pem_is_unwrapped_rather_than_rejected():
    raw = pem("RSA PRIVATE KEY")
    wrapped = base64.b64encode(raw.encode()).decode()
    text, was_wrapped = unwrap(wrapped)
    assert was_wrapped is True
    assert inspect_pem(text)["state"] == "pkcs1-rsa-key"
    assert unwrap(raw) == (raw.strip(), False)


def test_the_issuer_claim_is_checked_for_shape_only():
    assert issuer_form("123456") == "app-id"
    assert issuer_form("Iv23liABCDEfghij") == "client-id"
    assert issuer_form("acme-deploy-bot") == "unusable-issuer"
    assert issuer_form("") == "no-issuer"


def test_one_decode_message_covers_five_causes_and_says_so():
    state, detail = interpret(401, "A JSON web token could not be decoded")
    assert state == "signature-rejected"
    assert "another App" in detail
    assert "RS256" in detail


def test_the_neighbouring_failures_are_handed_off_rather_than_absorbed():
    assert interpret(200, None)[0] == "key-accepted"
    assert interpret(404, "Integration not found")[0] == "issuer-does-not-resolve"
    assert interpret(401, "'Issued at' claim ('iat') is in the "
                          "future")[0] == "clock-problem-not-key"
    assert interpret(401, "'Expiration time' claim ('exp') is too far in the "
                          "future")[0] == "lifetime-problem-not-key"
    assert interpret(401, "Bad credentials")[0] == "not-a-jwt"
    assert interpret(403, "Resource not accessible by integration")[0] == "unrelated"


def test_a_working_key_for_the_wrong_app_is_the_finding_with_no_error():
    app = {"id": 654321, "client_id": "Iv23liZZZZ", "slug": "acme-staging-bot",
           "name": "Acme Staging Bot"}
    state, detail = reconcile(app, "acme-deploy-bot")
    assert state == "authenticated-as-another-app"
    assert "staging key reaches production" in detail
    assert reconcile(app, "acme-staging-bot")[0] == "identity-matches"
    assert reconcile(app, "654321")[0] == "identity-matches"
    assert reconcile(app, "Iv23liZZZZ")[0] == "identity-matches"
    assert reconcile(app, None)[0] == "no-expectation-given"
    assert reconcile(None, "acme")[0] == "no-app-body"
''',
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  ESCAPED_NEWLINE, inspectPem, interpret, issuerForm, reconcile, repairFor,
  unwrap, usable,
} from './github-app-key-identity.mjs';

const FILLER = Buffer.from('x'.repeat(1200)).toString('base64');

/** An obviously fake PEM: a real label and a run of filler bytes. */
function pem(label, body = FILLER) {
  const rows = [];
  for (let i = 0; i < body.length; i += 64) {
    rows.push(body.slice(i, i + 64));
  }
  return `-----BEGIN ${label}-----\\n${rows.join('\\n')}\\n-----END ${label}-----\\n`;
}

test('the key github issues is recognised and fingerprinted', () => {
  const out = inspectPem(pem('RSA PRIVATE KEY'));
  assert.equal(out.state, 'pkcs1-rsa-key');
  assert.equal(out.label, 'RSA PRIVATE KEY');
  assert.equal(out.fingerprint.length, 16);
  assert.ok(out.der_bytes >= 500);
  assert.ok(usable(out.state));
});

test('a pkcs8 wrapper is the same key and is accepted', () => {
  assert.equal(inspectPem(pem('PRIVATE KEY')).state, 'pkcs8-key');
});

test('the fingerprint identifies the file and nothing else', () => {
  const one = inspectPem(pem('RSA PRIVATE KEY')).fingerprint;
  const again = inspectPem(pem('RSA PRIVATE KEY')).fingerprint;
  const other = inspectPem(pem('RSA PRIVATE KEY',
    Buffer.from('y'.repeat(1200)).toString('base64'))).fingerprint;
  assert.equal(one, again);
  assert.notEqual(one, other);
});

test('escaped newlines are the headline deployment fault', () => {
  const flattened = pem('RSA PRIVATE KEY').split('\\n').join(ESCAPED_NEWLINE);
  const out = inspectPem(flattened);
  assert.equal(out.state, 'escaped-newlines');
  assert.match(repairFor(out.state), /backslash and n/);
});

test('a pem collapsed onto one line is told apart from an escaped one', () => {
  const collapsed = pem('RSA PRIVATE KEY').split('\\n').join(' ');
  assert.equal(inspectPem(collapsed).state, 'single-line-pem');
});

test('the wrong kind of key is named rather than guessed at', () => {
  assert.equal(inspectPem(pem('OPENSSH PRIVATE KEY')).state, 'openssh-format');
  assert.equal(inspectPem(pem('PUBLIC KEY')).state, 'public-key-not-private');
  assert.equal(inspectPem(pem('EC PRIVATE KEY')).state, 'not-an-rsa-key');
  assert.equal(inspectPem(pem('CERTIFICATE')).state, 'certificate-not-key');
  assert.equal(inspectPem(pem('ENCRYPTED PRIVATE KEY')).state, 'encrypted-key');
  assert.equal(inspectPem(pem('DH PARAMETERS')).state, 'unknown-pem-label');
  for (const state of ['openssh-format', 'public-key-not-private', 'not-an-rsa-key']) {
    assert.ok(!usable(state));
  }
});

test('a truncated pem is caught before its body is read', () => {
  const cut = pem('RSA PRIVATE KEY').split('-----END')[0];
  assert.equal(inspectPem(cut).state, 'truncated-pem');
});

test('a body that is not base64 says so', () => {
  assert.ok(['body-not-base64', 'too-small-for-rsa']
    .includes(inspectPem(pem('RSA PRIVATE KEY', 'not base64 at all')).state));
});

test('something far too small to be an rsa key is rejected', () => {
  const small = Buffer.from('z'.repeat(64)).toString('base64');
  const out = inspectPem(pem('RSA PRIVATE KEY', small));
  assert.equal(out.state, 'too-small-for-rsa');
  assert.notEqual(out.fingerprint, null);
});

test('an absent key is a state and not a crash', () => {
  assert.equal(inspectPem('').state, 'no-key-present');
  assert.equal(inspectPem(null).state, 'no-key-present');
  assert.equal(inspectPem('just some text').state, 'not-a-pem');
});

test('a base64 wrapped pem is unwrapped rather than rejected', () => {
  const raw = pem('RSA PRIVATE KEY');
  const wrapped = Buffer.from(raw).toString('base64');
  const [text, wasWrapped] = unwrap(wrapped);
  assert.equal(wasWrapped, true);
  assert.equal(inspectPem(text).state, 'pkcs1-rsa-key');
  assert.deepEqual(unwrap(raw), [raw.trim(), false]);
});

test('the issuer claim is checked for shape only', () => {
  assert.equal(issuerForm('123456'), 'app-id');
  assert.equal(issuerForm('Iv23liABCDEfghij'), 'client-id');
  assert.equal(issuerForm('acme-deploy-bot'), 'unusable-issuer');
  assert.equal(issuerForm(''), 'no-issuer');
});

test('one decode message covers five causes and says so', () => {
  const [state, detail] = interpret(401, 'A JSON web token could not be decoded');
  assert.equal(state, 'signature-rejected');
  assert.match(detail, /another App/);
  assert.match(detail, /RS256/);
});

test('the neighbouring failures are handed off rather than absorbed', () => {
  assert.equal(interpret(200, null)[0], 'key-accepted');
  assert.equal(interpret(404, 'Integration not found')[0], 'issuer-does-not-resolve');
  assert.equal(interpret(401, "'Issued at' claim ('iat') is in the future")[0],
    'clock-problem-not-key');
  assert.equal(interpret(401, "'Expiration time' claim ('exp') is too far in the future")[0],
    'lifetime-problem-not-key');
  assert.equal(interpret(401, 'Bad credentials')[0], 'not-a-jwt');
  assert.equal(interpret(403, 'Resource not accessible by integration')[0], 'unrelated');
});

test('a working key for the wrong app is the finding with no error', () => {
  const app = {
    id: 654321, client_id: 'Iv23liZZZZ', slug: 'acme-staging-bot',
    name: 'Acme Staging Bot',
  };
  const [state, detail] = reconcile(app, 'acme-deploy-bot');
  assert.equal(state, 'authenticated-as-another-app');
  assert.match(detail, /staging key reaches production/);
  assert.equal(reconcile(app, 'acme-staging-bot')[0], 'identity-matches');
  assert.equal(reconcile(app, '654321')[0], 'identity-matches');
  assert.equal(reconcile(app, 'Iv23liZZZZ')[0], 'identity-matches');
  assert.equal(reconcile(app, null)[0], 'no-expectation-given');
  assert.equal(reconcile(null, 'acme')[0], 'no-app-body');
});
''',
"faq": [
 ("Does GitHub ever say which of the five causes it was?",
  "No, and that is deliberate rather than an oversight. Distinguishing wrong algorithm from wrong key for an unauthenticated caller would hand out information about a credential nobody has proved they own, so the same sentence covers all of it. That is exactly why the useful work happens before the request: the PEM's label, its line count and its fingerprint are all things you can read locally, and between them they eliminate four of the five without asking GitHub anything."),
 ("Why does the PEM keep losing its newlines?",
  "Because a PEM is one of the few secrets whose meaning depends on whitespace, and almost nothing in a deployment pipeline is built to preserve it. A .env parser, a CI secret field, a YAML block scalar quoted the wrong way and a shell that collapsed the value can each turn line breaks into the two characters backslash and n, and none of them reports having done it. Carrying the PEM base64-encoded ends the argument: every layer sees one long token with no whitespace to have an opinion about, and the process decodes it once at startup."),
 ("Is it safe to log the fingerprint?",
  "Yes, and that is most of the point. It is a truncated SHA-256 of the key's DER body, so it cannot be reversed and it carries no information about the key beyond identity. What it gives you is the ability to answer the only question that matters during an incident, which is whether the machine that works and the machine that does not are holding the same file, without either of them printing a key into a terminal that somebody is screen-sharing."),
 ("Can an App have more than one private key at a time?",
  "Yes, and using that is how a rotation avoids this failure entirely. Generate the new key while the old one is still registered, deploy it everywhere, confirm every host is signing with the new fingerprint, and only then delete the old key from the App. Rotations that delete first produce this 401 on every host at once, and rotations that never delete leave a key in circulation that somebody downloaded onto a laptop two years ago."),
 ("The JWT is accepted but my calls still fail. Is the key wrong?",
  "No. If GET /app returns 200 the key is registered on the App named in iss and this note is finished. What follows is a different layer: the JWT authenticates the App itself and cannot read repository data, so it has to be exchanged for an installation access token first, and that token then has its own permissions and its own repository coverage. A 403 mentioning permissions, a 404 on a repository, and a route that refuses installation tokens outright are three separate notes, and none of them is about the key."),
],
"related": [
 ("/github/jwt-clock-drift-iat/", "Clock drift puts iat in GitHub's future"),
 ("/github/jwt-exp-too-far-future/", "A JWT that asks to live for an hour"),
 ("/github/installation-token-rejected-by-endpoint/", "Endpoints that refuse an installation token"),
],
"citations": [CITE_JWT, CITE_PRIVATE_KEYS, CITE_JWS, CITE_PKCS1],
},

{
"slug": "installation-token-expired",
"title": "The installation token expired an hour into the job",
"description": "Installation access tokens last exactly one hour. A worker that mints one at startup runs green for 60 minutes and then 401s on everything at once.",
"h1": "the installation token expired an hour into the job",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app installation access token expires after 1 hour",
             "github installation token 401 bad credentials after an hour",
             "github app token refresh long running process",
             "installation access token expires_at", "github app daemon token expiry"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The migration ran for fifty-eight minutes and processed eleven thousand repositories. Then every request started returning <code>401 Bad credentials</code> &mdash; not some of them, all of them, from one second to the next. Restarting the job fixes it, which is the detail that sends everybody looking for a memory leak. It is not a leak. The process outlived its own credential.",
"short_answer": """<p>An installation access token lasts exactly one hour from the moment it was minted, and nothing warns you. Code that fetches a token during startup and holds it in a variable is fine for the length of a request-response cycle and wrong for anything longer: a queue worker, a nightly migration, a daemon, a long backfill. The cliff arrives at sixty minutes of process life and takes every in-flight call with it.</p>
<p>The check is arithmetic, not a lookup. Take the moment the token was minted &mdash; your own code knows it, because your own code asked for it &mdash; add 3600, and compare against now. Then compare your refresh interval against the same 3600: an interval of an hour is not a refresh, it is a coin flip. Re-mint at fifty minutes, and re-mint on any 401 as well, so a slow batch cannot walk off the end of a token it is still using.</p>""",
"problem": """<p>Everything about the shape of the failure argues against the real cause. It is sudden, it is total, and it is fixed by a restart, which is the signature of a resource leak rather than an expiry. So the first hour goes on heap graphs and connection pools, and the fact that it happens at almost exactly sixty minutes gets noticed late because nobody is looking at the clock, they are looking at the memory.</p>
<p>The message is no help either. <code>401 Bad credentials</code> is what GitHub says about a token that expired, a token that was revoked, a token that was truncated on the way into the process and a token that was never valid. It is the same sentence in all four cases, so the response cannot tell you that the credential used to work, which is the single most useful fact about this failure.</p>
<p>And it hides in the small. A web service that mints a token per request never sees it, so the same codebase can carry the defect for years while only the batch jobs fail. When it finally shows up it shows up in the worst place: the long-running thing, halfway through, having already done fifty minutes of work that now has to be repeated.</p>""",
"why": """<p><strong>One hour, fixed, from mint rather than from first use.</strong> The lifetime is not extended by activity and there is no refresh handshake. A token minted at startup and first used forty minutes later has twenty minutes left, which is why the burn-down has to be measured from the mint and not from anything the process did afterwards.</p>
<p><strong>The mint is a write, so this check cannot make one.</strong> Tokens come from a POST to the App installation endpoint, and nothing in this section writes. That is a real constraint and it shapes the script: the moment of minting has to come from your own record of it, or from the expiry GitHub states on a response to the token you already hold. The script says which of the two it used rather than pretending it minted anything.</p>
<p><strong>A refresh interval is only a refresh if it is shorter than the lifetime.</strong> An hourly timer against an hourly token means the window closes at the same moment it is meant to reopen, and whichever loses the race that day decides whether the job survives. Fifty minutes leaves ten minutes of margin for a slow mint, a retry and a batch that overran.</p>
<p><strong>The two clocks can disagree about which token you hold.</strong> If your recorded mint time says forty minutes remain and the expiry GitHub reports says four, you are not holding the token you think you are &mdash; something cached an older one, or two workers are sharing a variable. That disagreement is worth more than either number alone, and it is the reason the script reads both.</p>
<p><strong>This is the hour-scale question, not the day-scale one.</strong> Whether a credential expires next Tuesday, and what to do about the ones that carry no expiry at all, belongs to <a href="/github/token-expiring-soon/">the note on a token expiring soon</a>. Here the expiry is certain, it is an hour away, and the finding is whether your refresh schedule beats it. Nothing needs watching; something needs a timer.</p>""",
"steps": [
 {"h": "Record the moment you minted, and keep it next to the token",
  "body": """<p>Whatever holds the token should hold the timestamp too. It is the only number from which the burn-down can be computed without another request, and it is free: the code that asked for the token was there when the answer came back. A token in a variable with no mint time attached is a credential nobody can reason about.</p>"""},
 {"h": "Compute how much of the hour is left, not how long the process has run",
  "body": """<p>Uptime is a proxy and it lies as soon as anything re-mints. Subtract the mint time from now, take that off 3600, and you have the remaining life of the credential you are actually holding. Under five minutes is the band where a long batch will cross the line mid-flight.</p>"""},
 {"h": "Compare your refresh interval against the lifetime",
  "body": """<p>No interval at all means you minted once at startup and the cliff is at sixty minutes. An interval of an hour or more means the refresh cannot win. Anything over fifty minutes has no room for a retry. This is the part of the check that finds the bug before it fires, on a healthy process, in the middle of the afternoon.</p>"""},
 {"h": "Cross-check your record against what GitHub says",
  "body": """<p>An authenticated response for a credential with an expiry carries GitHub's own view of when it ends. Read it and compare. Agreement is reassurance; a large disagreement means the process is holding a different token from the one it recorded, which is a sharing or caching bug and not an expiry one.</p>"""},
 {"h": "Re-mint on a timer and on any 401",
  "body": """<p>Fifty minutes on a timer covers the ordinary case. Re-minting on a 401 covers the rest: a paused container, a clock correction, a batch that took longer than anyone modelled. Octokit's App authentication strategy does both for you, and a hand-rolled client has to do both explicitly, because doing only the first still fails on the day something stalls.</p>"""},
],
"verify": """<p>Re-run against the process once it refreshes on a timer. The state moves from <code>minted-once-at-startup</code> to <code>refresh-healthy</code>, and the remaining life stops falling towards zero between runs.</p>
<pre><code class="language-bash">python3 github_installation_token_age.py --refresh-interval 3000
# GET /installation/repositories returned 200
# minted 640s ago, 2960s of the hour remain
# fresh: 2960s remain of the 3600s lifetime.
# refresh-healthy: re-minting every 3000s leaves 600s of margin.
# record-agrees: GitHub's expiry and your recorded mint time are 2s apart.</code></pre>""",
"code_intro": "One GET, against the route only an installation access token can answer, and everything else is arithmetic over timestamps. The pure half is the interesting half: parsing the two different time formats GitHub uses, turning a mint time into a remaining life, turning a remaining life into a band, and turning a refresh interval into a verdict about a schedule that has not failed yet. The token is read from the environment and never printed. The mint endpoint is a write and this script does not call it, so where the numbers come from is stated explicitly in the output rather than assumed.",
"py_file": "github_installation_token_age.py",
"py": '''"""Say how much of its hour a GitHub App installation token has left.

Read only. One request, GET /installation/repositories, which is the route an
installation access token can answer and almost nothing else can. Nothing is
minted, refreshed or changed.

Minting is a write - it is a POST to the App installation endpoint - so this
script never does it. The mint moment comes from your own record of it, or the
expiry comes from the header GitHub attaches to a response for a credential
that has one. The report says which source it used rather than implying it
learned the number from a fresh mint.

The token is read from the environment and never printed, in whole or in part.
What the report contains is seconds.
"""
import argparse
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_installation_token_age")

API = "https://api.github.com"
UA = "github-installation-token-age/1.0"

# Fixed, from the moment of minting, and not extended by use.
LIFETIME = 3600

# Re-mint with this much of the hour still unspent, so a slow mint, a retry and
# an overrunning batch all fit inside the margin.
SAFE_MARGIN = 600
RECOMMENDED_INTERVAL = LIFETIME - SAFE_MARGIN

# Under this, a long batch will cross the line while it is still working.
DANGER_BAND = 300

# Two records of the same token should agree to about this. More than this and
# they are records of different tokens.
RECONCILE_TOLERANCE = 60


def parse_moment(value):
    """Parse an epoch or an ISO-8601 timestamp into epoch seconds. Pure.

    Accepts what a program is likely to have written down: the integer it got
    from time(), or the string GitHub uses in expires_at. Returns None rather
    than raising, because an unparseable record is a finding of its own.
    """
    text = str(value or "").strip()
    if not text:
        return None
    if re.fullmatch(r"\\d{9,11}", text):
        return float(text)
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.timestamp()


def parse_expiry_header(value):
    """Parse the expiry GitHub puts on a response. Pure.

    It is not ISO-8601: the format is a space-separated date and time followed
    by a zone name, so it needs its own small normalisation before the general
    parser can take it.
    """
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith(" UTC"):
        text = text[:-4].strip().replace(" ", "T") + "+00:00"
    return parse_moment(text)


def remaining(minted_at, expires_at, now):
    """Seconds of life left in the token, and where that number came from. Pure.

    GitHub's own expiry wins when both are available, because your record is a
    record of a mint and GitHub's is a statement about the credential in your
    hand. They should agree; when they do not, that is the finding.
    """
    if expires_at is not None:
        return int(expires_at - now), "github"
    if minted_at is not None:
        return int(minted_at + LIFETIME - now), "record"
    return None, "nothing"


def classify(left):
    """Turn a remaining life into a band. Pure."""
    if left is None:
        return ("no-record",
                "there is no mint time recorded and no expiry on the response, "
                "so nothing can be said about how much of the hour is left. "
                "Record the moment you mint, next to the token.")
    if left <= 0:
        return ("expired",
                "this token ran out %ds ago. Every call made with it returns "
                "401 Bad credentials, all at once, which is why a restart "
                "appears to fix it." % -left)
    if left < DANGER_BAND:
        return ("inside-the-danger-band",
                "%ds remain of the %ds lifetime. A batch that runs longer than "
                "that will cross the line while it is still working."
                % (left, LIFETIME))
    if left < SAFE_MARGIN:
        return ("past-the-safe-margin",
                "%ds remain, which is inside the %ds margin a refresh needs to "
                "cover a slow mint and a retry." % (left, SAFE_MARGIN))
    return ("fresh", "%ds remain of the %ds lifetime." % (left, LIFETIME))


def refresh_verdict(interval):
    """Judge a refresh schedule against the fixed lifetime. Pure.

    This is the half of the check that finds the bug on a healthy process,
    before it has ever fired.
    """
    if not interval or interval <= 0:
        return ("minted-once-at-startup",
                "no refresh interval, so this process mints once and holds. "
                "The first 401 arrives %d minutes after start, on everything "
                "at once." % (LIFETIME // 60))
    if interval >= LIFETIME:
        return ("refresh-slower-than-lifetime",
                "re-minting every %ds against a %ds lifetime is not a refresh, "
                "it is a race. Some days the token is replaced first and some "
                "days it is not." % (interval, LIFETIME))
    if interval > LIFETIME - SAFE_MARGIN:
        return ("refresh-without-margin",
                "re-minting every %ds leaves only %ds of margin, which one "
                "slow mint or one retry uses up." % (interval, LIFETIME - interval))
    return ("refresh-healthy",
            "re-minting every %ds leaves %ds of margin."
            % (interval, LIFETIME - interval))


def cliff_at(minted_at):
    """The epoch second at which 401s begin, or None. Pure."""
    if minted_at is None:
        return None
    return int(minted_at) + LIFETIME


def reconcile(header_expiry, record_expiry):
    """Compare GitHub's expiry against your own record of the mint. Pure.

    A disagreement is not a rounding problem. It means the process is holding a
    different token from the one it wrote down, which is a caching or sharing
    bug wearing an expiry costume.
    """
    if header_expiry is None:
        return ("no-header",
                "the response carried no expiry, so GitHub's view is "
                "unavailable and only your record is in play.")
    if record_expiry is None:
        return ("header-only",
                "there is no recorded mint time to check GitHub's expiry "
                "against. Record one; it costs nothing and it is the only way "
                "to notice a stale token.")
    gap = int(abs(header_expiry - record_expiry))
    if gap <= RECONCILE_TOLERANCE:
        return ("record-agrees",
                "GitHub's expiry and your recorded mint time are %ds apart." % gap)
    return ("record-disagrees",
            "GitHub's expiry and your recorded mint time are %ds apart, so "
            "this process is not holding the token it recorded. Look for a "
            "cached token or two workers sharing one variable." % gap)


def interpret(status, message, left):
    """Map the live response to a cause, using the remaining life. Pure.

    401 Bad credentials is the same sentence for an expired token, a revoked
    one and a truncated one, so the burn-down is what separates them. With no
    record to lean on, the honest answer is that they cannot be separated.
    """
    if status == 200:
        return ("token-live",
                "the token answered the installation route, so it is valid "
                "right now.")
    text = str(message or "").lower()
    if status == 401 and "bad credentials" in text:
        if left is not None and left <= 0:
            return ("expired-as-predicted",
                    "the token is past its hour and GitHub refused it, which "
                    "is exactly the arithmetic above.")
        if left is not None and left > DANGER_BAND:
            return ("not-an-expiry-problem",
                    "%ds of the lifetime remain and GitHub still refused the "
                    "token, so it was revoked, truncated or never valid. That "
                    "is a different investigation." % left)
        return ("expired-or-revoked-cannot-tell",
                "GitHub refused the token and there is no reliable record of "
                "when it was minted, so expiry and revocation look identical "
                "from here.")
    if status == 403 and "not accessible by integration" in text:
        return ("wrong-credential-class",
                "this route accepted the credential and refused the action, "
                "which means what is being held is not an installation access "
                "token at all.")
    if status == 404:
        return ("route-not-answered",
                "a 404 on the installation route usually means the credential "
                "is not an installation access token.")
    return ("unrelated",
            "the response does not look like an expiry, so this failure has "
            "another cause.")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--refresh-interval", type=int, default=0,
                    help="the seconds between re-mints in your code; 0 means "
                         "the token is minted once at startup")
    ap.add_argument("--minted-at", default=None,
                    help="when this token was minted, as an epoch second or an "
                         "ISO-8601 timestamp. Defaults to GITHUB_TOKEN_MINTED_AT")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_INSTALLATION_TOKEN")
    if not token:
        log.error("set GITHUB_INSTALLATION_TOKEN to the installation access "
                  "token the process is holding")
        return 2

    minted_at = parse_moment(args.minted_at
                             or os.environ.get("GITHUB_TOKEN_MINTED_AT"))
    now = time.time()

    r = requests.get(API + "/installation/repositories", timeout=30,
                     params={"per_page": 1}, headers={
                         "Authorization": "Bearer " + token,
                         "Accept": "application/vnd.github+json",
                         "X-GitHub-Api-Version": "2022-11-28",
                         "User-Agent": UA,
                     })
    try:
        body = r.json()
    except ValueError:
        body = None
    message = body.get("message") if isinstance(body, dict) else None
    header_expiry = parse_expiry_header(
        r.headers.get("github-authentication-token-expiration"))
    log.info("GET /installation/repositories returned %d", r.status_code)

    left, source = remaining(minted_at, header_expiry, now)
    if minted_at is not None:
        log.info("minted %ds ago", int(now - minted_at))
    if left is not None:
        log.info("%ds left, according to the %s", left, source)

    state, detail = classify(left)
    log.info("%s: %s", state, detail)

    plan_state, plan_detail = refresh_verdict(args.refresh_interval)
    log.info("%s: %s", plan_state, plan_detail)

    record_expiry = None if minted_at is None else minted_at + LIFETIME
    match_state, match_detail = reconcile(header_expiry, record_expiry)
    log.info("%s: %s", match_state, match_detail)

    live_state, live_detail = interpret(r.status_code, message, left)
    log.info("%s: %s", live_state, live_detail)

    if plan_state != "refresh-healthy" or state in ("expired",
                                                    "inside-the-danger-band"):
        log.info("repair: re-mint every %ds, and re-mint again on any 401. A "
                 "timer alone still fails on the day something stalls.",
                 RECOMMENDED_INTERVAL)

    print(json.dumps({"seconds_left": left, "source": source,
                      "cliff_at": cliff_at(minted_at),
                      "refresh_interval": args.refresh_interval,
                      "state": state, "refresh_state": plan_state,
                      "reconcile_state": match_state,
                      "live_state": live_state}, indent=2))
    return 0 if state == "fresh" and plan_state == "refresh-healthy" else 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-installation-token-age.mjs",
"js": '''/**
 * Say how much of its hour a GitHub App installation token has left.
 *
 * Read only. One request, GET /installation/repositories, which is the route
 * an installation access token can answer and almost nothing else can.
 *
 * Minting is a write, so this script never does it. The mint moment comes from
 * your own record of it, or the expiry comes from the header GitHub attaches
 * to a response for a credential that has one. The report says which source it
 * used.
 *
 * The token is read from the environment and never printed.
 */
const API = 'https://api.github.com';
const UA = 'github-installation-token-age/1.0';

/** Fixed, from the moment of minting, and not extended by use. */
export const LIFETIME = 3600;

/** Re-mint with this much of the hour still unspent. */
export const SAFE_MARGIN = 600;
export const RECOMMENDED_INTERVAL = LIFETIME - SAFE_MARGIN;

/** Under this, a long batch will cross the line while it is still working. */
export const DANGER_BAND = 300;

/** Two records of the same token should agree to about this. */
export const RECONCILE_TOLERANCE = 60;

/** Parse an epoch or an ISO-8601 timestamp into epoch seconds. Pure. */
export function parseMoment(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  if (/^\\d{9,11}$/.test(text)) return Number(text);
  const ms = Date.parse(text);
  return Number.isNaN(ms) ? null : ms / 1000;
}

/**
 * Parse the expiry GitHub puts on a response. Pure.
 * It is not ISO-8601: a space-separated date and time followed by a zone name.
 */
export function parseExpiryHeader(value) {
  let text = String(value ?? '').trim();
  if (!text) return null;
  if (text.endsWith(' UTC')) {
    text = `${text.slice(0, -4).trim().replace(' ', 'T')}+00:00`;
  }
  return parseMoment(text);
}

/**
 * Seconds of life left, and where the number came from. Pure.
 * GitHub's expiry wins when both exist: yours is a record of a mint, GitHub's
 * is a statement about the credential in your hand.
 */
export function remaining(mintedAt, expiresAt, now) {
  if (expiresAt !== null && expiresAt !== undefined) {
    return [Math.trunc(expiresAt - now), 'github'];
  }
  if (mintedAt !== null && mintedAt !== undefined) {
    return [Math.trunc(mintedAt + LIFETIME - now), 'record'];
  }
  return [null, 'nothing'];
}

/** Turn a remaining life into a band. Pure. */
export function classify(left) {
  if (left === null || left === undefined) {
    return ['no-record',
      'there is no mint time recorded and no expiry on the response, so ' +
      'nothing can be said about how much of the hour is left. Record the ' +
      'moment you mint, next to the token.'];
  }
  if (left <= 0) {
    return ['expired',
      `this token ran out ${-left}s ago. Every call made with it returns 401 ` +
      'Bad credentials, all at once, which is why a restart appears to fix it.'];
  }
  if (left < DANGER_BAND) {
    return ['inside-the-danger-band',
      `${left}s remain of the ${LIFETIME}s lifetime. A batch that runs longer ` +
      'than that will cross the line while it is still working.'];
  }
  if (left < SAFE_MARGIN) {
    return ['past-the-safe-margin',
      `${left}s remain, which is inside the ${SAFE_MARGIN}s margin a refresh ` +
      'needs to cover a slow mint and a retry.'];
  }
  return ['fresh', `${left}s remain of the ${LIFETIME}s lifetime.`];
}

/** Judge a refresh schedule against the fixed lifetime. Pure. */
export function refreshVerdict(interval) {
  if (!interval || interval <= 0) {
    return ['minted-once-at-startup',
      'no refresh interval, so this process mints once and holds. The first ' +
      `401 arrives ${LIFETIME / 60} minutes after start, on everything at once.`];
  }
  if (interval >= LIFETIME) {
    return ['refresh-slower-than-lifetime',
      `re-minting every ${interval}s against a ${LIFETIME}s lifetime is not a ` +
      'refresh, it is a race. Some days the token is replaced first and some ' +
      'days it is not.'];
  }
  if (interval > LIFETIME - SAFE_MARGIN) {
    return ['refresh-without-margin',
      `re-minting every ${interval}s leaves only ${LIFETIME - interval}s of ` +
      'margin, which one slow mint or one retry uses up.'];
  }
  return ['refresh-healthy',
    `re-minting every ${interval}s leaves ${LIFETIME - interval}s of margin.`];
}

/** The epoch second at which 401s begin, or null. Pure. */
export function cliffAt(mintedAt) {
  if (mintedAt === null || mintedAt === undefined) return null;
  return Math.trunc(mintedAt) + LIFETIME;
}

/** Compare GitHub's expiry against your own record of the mint. Pure. */
export function reconcile(headerExpiry, recordExpiry) {
  if (headerExpiry === null || headerExpiry === undefined) {
    return ['no-header',
      'the response carried no expiry, so GitHub\\'s view is unavailable and ' +
      'only your record is in play.'];
  }
  if (recordExpiry === null || recordExpiry === undefined) {
    return ['header-only',
      'there is no recorded mint time to check GitHub\\'s expiry against. ' +
      'Record one; it costs nothing and it is the only way to notice a stale ' +
      'token.'];
  }
  const gap = Math.trunc(Math.abs(headerExpiry - recordExpiry));
  if (gap <= RECONCILE_TOLERANCE) {
    return ['record-agrees',
      `GitHub's expiry and your recorded mint time are ${gap}s apart.`];
  }
  return ['record-disagrees',
    `GitHub's expiry and your recorded mint time are ${gap}s apart, so this ` +
    'process is not holding the token it recorded. Look for a cached token or ' +
    'two workers sharing one variable.'];
}

/** Map the live response to a cause, using the remaining life. Pure. */
export function interpret(status, message, left) {
  if (status === 200) {
    return ['token-live',
      'the token answered the installation route, so it is valid right now.'];
  }
  const text = String(message ?? '').toLowerCase();
  if (status === 401 && text.includes('bad credentials')) {
    if (left !== null && left !== undefined && left <= 0) {
      return ['expired-as-predicted',
        'the token is past its hour and GitHub refused it, which is exactly ' +
        'the arithmetic above.'];
    }
    if (left !== null && left !== undefined && left > DANGER_BAND) {
      return ['not-an-expiry-problem',
        `${left}s of the lifetime remain and GitHub still refused the token, ` +
        'so it was revoked, truncated or never valid. That is a different ' +
        'investigation.'];
    }
    return ['expired-or-revoked-cannot-tell',
      'GitHub refused the token and there is no reliable record of when it ' +
      'was minted, so expiry and revocation look identical from here.'];
  }
  if (status === 403 && text.includes('not accessible by integration')) {
    return ['wrong-credential-class',
      'this route accepted the credential and refused the action, which means ' +
      'what is being held is not an installation access token at all.'];
  }
  if (status === 404) {
    return ['route-not-answered',
      'a 404 on the installation route usually means the credential is not an ' +
      'installation access token.'];
  }
  return ['unrelated',
    'the response does not look like an expiry, so this failure has another cause.'];
}

function flag(name, fallback) {
  const at = process.argv.indexOf(name);
  if (at === -1 || at === process.argv.length - 1) return fallback;
  return process.argv[at + 1];
}

async function main() {
  const token = process.env.GITHUB_INSTALLATION_TOKEN;
  if (!token) {
    console.error('set GITHUB_INSTALLATION_TOKEN to the installation access ' +
      'token the process is holding');
    process.exitCode = 2;
    return;
  }
  const interval = Number(flag('--refresh-interval', 0)) || 0;
  const mintedAt = parseMoment(flag('--minted-at', null)
    ?? process.env.GITHUB_TOKEN_MINTED_AT);
  const now = Date.now() / 1000;

  const res = await fetch(`${API}/installation/repositories?per_page=1`, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  const message = body && typeof body === 'object' ? body.message : null;
  const headerExpiry = parseExpiryHeader(
    res.headers.get('github-authentication-token-expiration'));
  console.log(`GET /installation/repositories returned ${res.status}`);

  const [left, source] = remaining(mintedAt, headerExpiry, now);
  if (mintedAt !== null) console.log(`minted ${Math.trunc(now - mintedAt)}s ago`);
  if (left !== null) console.log(`${left}s left, according to the ${source}`);

  const [state, detail] = classify(left);
  console.log(`${state}: ${detail}`);

  const [planState, planDetail] = refreshVerdict(interval);
  console.log(`${planState}: ${planDetail}`);

  const recordExpiry = mintedAt === null ? null : mintedAt + LIFETIME;
  const [matchState, matchDetail] = reconcile(headerExpiry, recordExpiry);
  console.log(`${matchState}: ${matchDetail}`);

  const [liveState, liveDetail] = interpret(res.status, message, left);
  console.log(`${liveState}: ${liveDetail}`);

  if (planState !== 'refresh-healthy' || state === 'expired'
      || state === 'inside-the-danger-band') {
    console.log(`repair: re-mint every ${RECOMMENDED_INTERVAL}s, and re-mint ` +
      'again on any 401. A timer alone still fails on the day something stalls.');
  }

  console.log(JSON.stringify({
    seconds_left: left,
    source,
    cliff_at: cliffAt(mintedAt),
    refresh_interval: interval,
    state,
    refresh_state: planState,
    reconcile_state: matchState,
    live_state: liveState,
  }, null, 2));
  process.exitCode = (state === 'fresh' && planState === 'refresh-healthy') ? 0 : 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and set an exit code that fails a passing suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Every case is a pair of timestamps and an integer, so the whole hour can be replayed in a line: a token minted an hour and a minute ago, a refresh timer set to exactly the lifetime, a recorded mint time that disagrees with GitHub's expiry by twenty minutes. The one fake token in here is the string <code>tok</code>, which is short enough and silly enough that nobody will mistake it for a credential. The rule worth pinning is the last one: a 401 with plenty of life left is explicitly <em>not</em> this note's problem, and the script says so rather than claiming the win.",
"test_py_file": "test_github_installation_token_age.py",
"test_py": '''from github_installation_token_age import (
    DANGER_BAND, LIFETIME, cliff_at, classify, interpret, parse_expiry_header,
    parse_moment, reconcile, refresh_verdict, remaining,
)

NOW = 1_772_000_000.0

# Obviously not a credential.
FAKE = "tok"


def test_a_recorded_mint_time_parses_in_either_shape():
    assert parse_moment("1772000000") == NOW
    assert parse_moment("2026-02-25T08:33:20Z") == parse_moment("1772008400")
    assert parse_moment("") is None
    assert parse_moment(None) is None
    assert parse_moment("some time last tuesday") is None


def test_the_expiry_github_states_is_not_iso_8601():
    assert parse_expiry_header("2026-02-25 08:33:20 UTC") == parse_moment("1772008400")
    assert parse_expiry_header("") is None
    assert parse_expiry_header(None) is None


def test_the_remaining_life_names_the_source_it_came_from():
    left, source = remaining(NOW - 600, None, NOW)
    assert (left, source) == (3000, "record")
    left, source = remaining(NOW - 600, NOW + 120, NOW)
    assert (left, source) == (120, "github")
    assert remaining(None, None, NOW) == (None, "nothing")


def test_an_hour_old_token_is_the_headline_finding():
    state, detail = classify(-60)
    assert state == "expired"
    assert "60s ago" in detail
    assert "all at once" in detail


def test_the_bands_below_an_hour_are_named_separately():
    assert classify(3000)[0] == "fresh"
    assert classify(599)[0] == "past-the-safe-margin"
    assert classify(DANGER_BAND - 1)[0] == "inside-the-danger-band"
    assert classify(0)[0] == "expired"


def test_nothing_recorded_is_a_state_and_not_a_guess():
    state, detail = classify(None)
    assert state == "no-record"
    assert "Record the moment you mint" in detail


def test_minting_once_at_startup_is_found_before_it_fires():
    state, detail = refresh_verdict(0)
    assert state == "minted-once-at-startup"
    assert "60 minutes after start" in detail
    assert refresh_verdict(None)[0] == "minted-once-at-startup"


def test_an_hourly_timer_against_an_hourly_token_is_a_race():
    state, detail = refresh_verdict(LIFETIME)
    assert state == "refresh-slower-than-lifetime"
    assert "it is a race" in detail
    assert refresh_verdict(7200)[0] == "refresh-slower-than-lifetime"


def test_a_refresh_with_no_room_for_a_retry_is_still_flagged():
    assert refresh_verdict(3400)[0] == "refresh-without-margin"


def test_fifty_minutes_is_the_schedule_that_passes():
    state, detail = refresh_verdict(3000)
    assert state == "refresh-healthy"
    assert "600s of margin" in detail


def test_the_cliff_is_an_hour_after_the_mint():
    assert cliff_at(NOW) == int(NOW) + LIFETIME
    assert cliff_at(None) is None


def test_two_records_of_different_tokens_are_caught():
    state, detail = reconcile(NOW + 240, NOW + 1440)
    assert state == "record-disagrees"
    assert "1200s apart" in detail
    assert reconcile(NOW + 240, NOW + 250)[0] == "record-agrees"
    assert reconcile(None, NOW + 240)[0] == "no-header"
    assert reconcile(NOW + 240, None)[0] == "header-only"


def test_a_401_at_the_end_of_the_hour_is_the_expiry():
    state, detail = interpret(401, "Bad credentials", -30)
    assert state == "expired-as-predicted"
    assert "the arithmetic above" in detail


def test_a_401_with_most_of_the_hour_left_is_explicitly_not_this_problem():
    state, detail = interpret(401, "Bad credentials", 2400)
    assert state == "not-an-expiry-problem"
    assert "revoked, truncated or never valid" in detail


def test_a_401_with_no_record_refuses_to_choose():
    assert interpret(401, "Bad credentials", None)[0] == "expired-or-revoked-cannot-tell"


def test_the_other_responses_point_somewhere_else():
    assert interpret(200, None, 3000)[0] == "token-live"
    assert interpret(403, "Resource not accessible by integration",
                     3000)[0] == "wrong-credential-class"
    assert interpret(404, "Not Found", 3000)[0] == "route-not-answered"
    assert interpret(500, "Server Error", 3000)[0] == "unrelated"


def test_the_fixture_token_is_obviously_not_a_credential():
    assert len(FAKE) < 20
''',
"test_js_file": "github-installation-token-age.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  DANGER_BAND, LIFETIME, classify, cliffAt, interpret, parseExpiryHeader,
  parseMoment, reconcile, refreshVerdict, remaining,
} from './github-installation-token-age.mjs';

const NOW = 1772000000;

/** Obviously not a credential. */
const FAKE = 'tok';

test('a recorded mint time parses in either shape', () => {
  assert.equal(parseMoment('1772000000'), NOW);
  assert.equal(parseMoment('2026-02-25T08:33:20Z'), parseMoment('1772008400'));
  assert.equal(parseMoment(''), null);
  assert.equal(parseMoment(null), null);
  assert.equal(parseMoment('some time last tuesday'), null);
});

test('the expiry github states is not iso 8601', () => {
  assert.equal(parseExpiryHeader('2026-02-25 08:33:20 UTC'), parseMoment('1772008400'));
  assert.equal(parseExpiryHeader(''), null);
  assert.equal(parseExpiryHeader(null), null);
});

test('the remaining life names the source it came from', () => {
  assert.deepEqual(remaining(NOW - 600, null, NOW), [3000, 'record']);
  assert.deepEqual(remaining(NOW - 600, NOW + 120, NOW), [120, 'github']);
  assert.deepEqual(remaining(null, null, NOW), [null, 'nothing']);
});

test('an hour old token is the headline finding', () => {
  const [state, detail] = classify(-60);
  assert.equal(state, 'expired');
  assert.match(detail, /60s ago/);
  assert.match(detail, /all at once/);
});

test('the bands below an hour are named separately', () => {
  assert.equal(classify(3000)[0], 'fresh');
  assert.equal(classify(599)[0], 'past-the-safe-margin');
  assert.equal(classify(DANGER_BAND - 1)[0], 'inside-the-danger-band');
  assert.equal(classify(0)[0], 'expired');
});

test('nothing recorded is a state and not a guess', () => {
  const [state, detail] = classify(null);
  assert.equal(state, 'no-record');
  assert.match(detail, /Record the moment you mint/);
});

test('minting once at startup is found before it fires', () => {
  const [state, detail] = refreshVerdict(0);
  assert.equal(state, 'minted-once-at-startup');
  assert.match(detail, /60 minutes after start/);
  assert.equal(refreshVerdict(null)[0], 'minted-once-at-startup');
});

test('an hourly timer against an hourly token is a race', () => {
  const [state, detail] = refreshVerdict(LIFETIME);
  assert.equal(state, 'refresh-slower-than-lifetime');
  assert.match(detail, /it is a race/);
  assert.equal(refreshVerdict(7200)[0], 'refresh-slower-than-lifetime');
});

test('a refresh with no room for a retry is still flagged', () => {
  assert.equal(refreshVerdict(3400)[0], 'refresh-without-margin');
});

test('fifty minutes is the schedule that passes', () => {
  const [state, detail] = refreshVerdict(3000);
  assert.equal(state, 'refresh-healthy');
  assert.match(detail, /600s of margin/);
});

test('the cliff is an hour after the mint', () => {
  assert.equal(cliffAt(NOW), NOW + LIFETIME);
  assert.equal(cliffAt(null), null);
});

test('two records of different tokens are caught', () => {
  const [state, detail] = reconcile(NOW + 240, NOW + 1440);
  assert.equal(state, 'record-disagrees');
  assert.match(detail, /1200s apart/);
  assert.equal(reconcile(NOW + 240, NOW + 250)[0], 'record-agrees');
  assert.equal(reconcile(null, NOW + 240)[0], 'no-header');
  assert.equal(reconcile(NOW + 240, null)[0], 'header-only');
});

test('a 401 at the end of the hour is the expiry', () => {
  const [state, detail] = interpret(401, 'Bad credentials', -30);
  assert.equal(state, 'expired-as-predicted');
  assert.match(detail, /the arithmetic above/);
});

test('a 401 with most of the hour left is explicitly not this problem', () => {
  const [state, detail] = interpret(401, 'Bad credentials', 2400);
  assert.equal(state, 'not-an-expiry-problem');
  assert.match(detail, /revoked, truncated or never valid/);
});

test('a 401 with no record refuses to choose', () => {
  assert.equal(interpret(401, 'Bad credentials', null)[0],
    'expired-or-revoked-cannot-tell');
});

test('the other responses point somewhere else', () => {
  assert.equal(interpret(200, null, 3000)[0], 'token-live');
  assert.equal(interpret(403, 'Resource not accessible by integration', 3000)[0],
    'wrong-credential-class');
  assert.equal(interpret(404, 'Not Found', 3000)[0], 'route-not-answered');
  assert.equal(interpret(500, 'Server Error', 3000)[0], 'unrelated');
});

test('the fixture token is obviously not a credential', () => {
  assert.ok(FAKE.length < 20);
});
''',
"faq": [
 ("Can I make the installation token last longer than an hour?",
  "No, and there is no parameter for it. The hour is the point: an installation access token carries the App's permissions across a whole account, so a leaked one is worth having, and a short fixed lifetime bounds how long it is worth anything. What you can do is stop treating it as a startup constant. Minting is one request and it is fast, so a token per unit of work, or a token on a fifty-minute timer, costs almost nothing and removes the failure entirely."),
 ("Why does restarting fix it if the token is the problem?",
  "Because a restart mints a new token, which is exactly the repair, applied by accident. That coincidence is what makes this bug expensive: the fix that works is the one that also resets the heap, the connection pool and every other suspect, so the evidence points at all of them equally. The tell is the timing. If the failure lands at close to sixty minutes of process life every time, and lands on every call at once rather than on a growing fraction of them, it is not a leak."),
 ("Should I re-mint on a timer or when I get a 401?",
  "Both, because they cover different failures. A timer handles the ordinary case and keeps the credential fresh even when the process is idle. Re-minting on a 401 handles everything the timer cannot model: a container paused by the scheduler, a clock stepped by an hour, a single batch that took twice as long as any batch before it. A timer alone fails on the unusual day, and a 401 handler alone means every unusual day starts with a burst of failed requests."),
 ("How do I get expires_at without minting a token?",
  "You do not, and that is why this script does not pretend to. The mint response is where expires_at comes from and minting is a write, which nothing in this section does. What is available read-only is the expiry GitHub attaches to a response for a credential that has one, and your own record of when you minted. The script uses whichever exists, says which one it used, and reports the disagreement when both exist and differ, because that disagreement means you are holding a token you did not record."),
 ("Does an installation token expire early when the App's permissions change?",
  "It can stop working before its hour is up for reasons that are not expiry, which is exactly why the script separates them. Suspending the installation, uninstalling the App, or revoking the token all end it immediately, and all of them produce the same 401 Bad credentials as the hour running out. The remaining life is what tells them apart: a 401 with forty minutes still on the clock is not an expiry, and the script says so rather than recommending a shorter refresh interval that would not have helped."),
],
"related": [
 ("/github/token-expiring-soon/", "A token that expires in days with nobody watching"),
 ("/github/bad-credentials-401/", "401 Bad credentials on every endpoint"),
 ("/github/installation-token-rejected-by-endpoint/", "Endpoints that refuse an installation token"),
],
"citations": [CITE_APP_INSTALL_AUTH, CITE_INSTALLATIONS_REST, CITE_BEST_PRACTICES, CITE_APP_AUTH],
},

{
"slug": "app-not-installed-on-repo",
"title": "A 404 that means the App is not installed on that repo",
"description": "An App gets 404, not 403, on a repository its installation does not cover. GET /repos/{owner}/{repo}/installation under the JWT answers yes or no.",
"h1": "a 404 that means the App is not installed on that repo",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app 404 on repository that exists",
             "github app not installed on repository",
             "get repos owner repo installation 404",
             "github app selected repositories new repo missing",
             "github app installation 404 public repo"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The repository is public. You can open it in a browser without logging in. The App reads eleven other repositories in the same organization with the same token, and this one comes back <code>404 Not Found</code>. So the search starts with permissions, and permissions are not the problem, because the App was never installed here at all.",
"short_answer": """<p>An installation access token can only see the repositories inside its installation. Anything else is not forbidden, it is invisible: GitHub answers 404 rather than 403 so that a caller cannot use error codes to enumerate resources it has no business knowing about. A public repository looks exactly like a private one it cannot reach, and both look exactly like one that does not exist.</p>
<p>Ask the question that has a yes-or-no answer. <code>GET /repos/{owner}/{repo}/installation</code>, sent with the App's JWT rather than an installation token, returns the installation object when your App is installed on that repository and 404 when it is not. Then ask the same about the account with <code>GET /orgs/{org}/installation</code>. Installed on the account but not the repository is one repair; not installed on the account at all is a different one.</p>""",
"problem": """<p>404 is the least informative answer GitHub has, and it is the correct one. Returning 403 would confirm the repository exists, which is a small leak that matters a great deal for private repositories, so the API declines to distinguish <em>you may not</em> from <em>there is nothing here</em>. The cost is paid by everyone debugging the honest case, where the repository plainly exists and the code still cannot see it.</p>
<p>The presence of other working repositories makes it worse. Eleven successes and one failure looks like a property of the twelfth repository &mdash; archived, renamed, moved, private in some new way &mdash; rather than a property of the installation. So the investigation goes into the repository's settings, which are fine, instead of into the App's installation, which is where the missing entry is.</p>
<p>And the commonest cause is invisible by design. An installation set to <em>selected repositories</em> does not gain new ones. A repository created this morning is not in an installation configured last year, so an integration that has worked for eleven months starts 404ing on exactly the repositories that are newest and most active, and nobody changed anything.</p>""",
"why": """<p><strong>The installation is the boundary, not the permission.</strong> Permissions say what an App may do with a repository it can reach. The installation says which repositories those are. A missing permission produces a 403 that names what it wanted; a missing installation produces a 404 that names nothing, because as far as that credential is concerned there is no resource to talk about.</p>
<p><strong>There is an endpoint that answers this directly.</strong> <code>GET /repos/{owner}/{repo}/installation</code> is asked with the App's JWT and returns the installation covering that repository, or 404. It is the only call in this note that gives a yes or a no rather than an inference, which is why it is the one the script leans on.</p>
<p><strong>Account and repository are two separate questions.</strong> An App can be installed on an organization and still not cover a given repository, so the account-level route has to be asked too. Installed on the account is a good state to be in: the repair is adding one repository. Not installed at all means somebody has to accept an installation, which is a different conversation with a different person.</p>
<p><strong>Creation dates turn a guess into a sentence.</strong> When the selection is <em>selected</em> and the repository was created after the installation, the cause is not a mistake anybody made, it is the default behaviour of a selection that does not grow. Comparing the two timestamps lets the report say that instead of listing possibilities, and it points at the durable repair rather than the immediate one.</p>
<p><strong>What this cannot tell you.</strong> If the unauthenticated read also 404s, the repository is either private or absent and no read-only check can separate those two: that is the same masking, one level out. And the size of the gap between what the installation covers and what the account holds is a different measurement, kept in <a href="/github/installation-repository-selection-partial/">the note on partial repository selection</a>. This note is about one repository and whether the App is there at all.</p>""",
"steps": [
 {"h": "Confirm the repository exists without any credential",
  "body": """<p>An unauthenticated <code>GET /repos/{owner}/{repo}</code> settles whether there is a public repository at that path. A 200 makes the rest of the investigation about your App, which is a much smaller search. A 404 leaves two possibilities that no read-only check can separate, and the report should say so rather than picking one.</p>"""},
 {"h": "Ask the per-repository question with the App JWT",
  "body": """<p><code>GET /repos/{owner}/{repo}/installation</code> is the direct question and it is answered with the App's JWT, not with an installation token. A 200 returns the installation, its id, its <code>repository_selection</code> and the account it sits on. A 404 is the finding: your App is not installed on that repository.</p>"""},
 {"h": "Ask the same about the account",
  "body": """<p><code>GET /orgs/{org}/installation</code>, or <code>/users/{username}/installation</code> for a personal account, says whether the App is installed anywhere on that owner. This is the step that turns one 404 into two different repairs, and it takes one request.</p>"""},
 {"h": "Compare the creation dates when the selection is partial",
  "body": """<p>If the installation covers <em>selected</em> repositories and the repository was created after the installation, you have found a recurring problem rather than a one-off. It will happen again with the next repository, and again after that, and adding this one by hand does nothing about the next.</p>"""},
 {"h": "Add the repository, or switch the installation to all repositories",
  "body": """<p>Adding one repository is done from the installation's configuration page and fixes today. Switching the installation to all repositories fixes every future one, at the cost of a broader grant that somebody has to be comfortable with. Which of those is right is a policy question; the script prints both and names the one that matches what it found.</p>"""},
],
"verify": """<p>Re-run after the repository is added to the installation. The state moves from <code>installed-on-account-not-repo</code> to <code>installed-on-this-repo</code>, with no permission changed and no token re-minted.</p>
<pre><code class="language-bash">python3 github_app_installation_presence.py --repo acme/reporting
# public-repo: acme/reporting exists and is publicly readable
# GET /repos/acme/reporting/installation returned 200
# installed-on-this-repo: installation 42891842 covers this repository.
# selection-covers-everything: repository_selection is all, so new
# repositories are covered automatically.</code></pre>""",
"code_intro": "Three GETs, and the first one deliberately carries no credential at all: whether the repository is publicly readable is a fact about the world rather than about your App, and separating it out keeps the rest of the report honest. The other two are the same question asked at two scopes, repository and account, under the App's JWT. Everything that turns those three status codes into a verdict is pure, including the repository-reference parser, which has to reduce a URL, an <code>owner/name</code> pair and a clone path to the same two strings, and the creation-date comparison that names a recurring cause rather than a one-off.",
"py_file": "github_app_installation_presence.py",
"py": '''"""Say whether a GitHub App is installed on one specific repository.

Read only. Three GETs: one unauthenticated existence check, and two presence
questions asked with the App's JWT, at repository scope and at account scope.
Nothing is installed, added, changed or minted.

An installation access token cannot see outside its installation, and GitHub
answers 404 rather than 403 for anything outside it, so a public repository the
App was never installed on is indistinguishable from one that does not exist.
GET /repos/{owner}/{repo}/installation is the call that answers directly.

The JWT is read from the environment and never printed. The output is three
status codes, two timestamps and a verdict.
"""
import argparse
import json
import logging
import os
import re
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_app_installation_presence")

API = "https://api.github.com"
UA = "github-app-installation-presence/1.0"

# Owner and repository names GitHub will actually issue.
NAME = re.compile(r"[A-Za-z0-9._-]+")

# Every way a repository reference tends to arrive in a bug report.
PREFIXES = ("https://github.com/", "http://github.com/",
            "https://api.github.com/repos/", "git@github.com:")


def split_repo(value):
    """Reduce any repository reference to (owner, name). Pure.

    A browser URL, an API URL, a clone path and a plain owner/name pair all
    describe the same repository, and a bug report will contain whichever one
    the reporter had on their clipboard. Returns None when it is not a
    repository reference at all.
    """
    text = str(value or "").strip().rstrip("/")
    for prefix in PREFIXES:
        if text.startswith(prefix):
            text = text[len(prefix):]
            break
    if text.endswith(".git"):
        text = text[:-4]
    parts = [p for p in text.split("/") if p]
    if len(parts) < 2:
        return None
    owner, name = parts[0], parts[1]
    if not NAME.fullmatch(owner) or not NAME.fullmatch(name):
        return None
    return (owner, name)


def account_route(owner, owner_type):
    """The account-scope installation route for this kind of owner. Pure.

    Organizations and user accounts have separate routes and the wrong one
    404s for reasons that have nothing to do with the App, which would be a
    very annoying way to get a false finding.
    """
    if str(owner_type or "").lower() == "user":
        return "/users/%s/installation" % owner
    return "/orgs/%s/installation" % owner


def parse_iso(value):
    """Parse an ISO-8601 timestamp into epoch seconds. Pure. None if unusable."""
    text = str(value or "").strip()
    if not text:
        return None
    try:
        moment = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=timezone.utc)
    return moment.timestamp()


def visibility(status):
    """What the unauthenticated read proved about the repository. Pure."""
    if status == 200:
        return ("public-repo",
                "the repository exists and is publicly readable, so whatever "
                "is wrong is on your side of the request.")
    if status == 404:
        return ("not-public-or-absent",
                "an unauthenticated read also returns 404, which means the "
                "repository is private or does not exist. A read-only check "
                "cannot separate those two, and neither can anyone else "
                "without access.")
    return ("visibility-unknown",
            "the unauthenticated read returned something other than 200 or "
            "404, so nothing was established about the repository itself.")


def classify(repo_status, account_status):
    """Turn two presence questions into one verdict. Pure.

    Repository scope is asked first because a 200 there ends the matter. The
    account-scope answer only matters when the repository-scope answer is no,
    and it is what splits one 404 into two different repairs.
    """
    if repo_status in (401, 403) or account_status in (401, 403):
        return ("jwt-not-accepted",
                "the App JWT was refused, so nothing was learned about any "
                "installation. Fix the JWT first; a signing or clock fault "
                "looks like an absent installation from here.")
    if repo_status == 200:
        return ("installed-on-this-repo",
                "the App is installed on this repository, so a 404 from your "
                "integration is about something else: a permission, a wrong "
                "path, or a credential that is not this App's.")
    if repo_status == 404 and account_status == 200:
        return ("installed-on-account-not-repo",
                "the App is installed on the account and this repository is "
                "not in the installation. The installation is set to selected "
                "repositories and this one was never selected.")
    if repo_status == 404 and account_status == 404:
        return ("not-installed-on-account",
                "the App is not installed anywhere on this account. Somebody "
                "with admin rights on the account has to install it; no "
                "permission or token change will do anything until they do.")
    return ("inconclusive",
            "the two presence checks did not return a pair this check "
            "recognises, so no verdict is safe.")


def creation_order(repo_created, installation_created, selection):
    """Say whether the repository is simply newer than the installation. Pure.

    This is the difference between a mistake and a recurring condition. A
    selection that does not grow will keep producing this finding for every
    repository created after it, and adding this one by hand fixes only today.
    """
    if str(selection or "").lower() == "all":
        return ("selection-covers-everything",
                "repository_selection is all, so new repositories are covered "
                "automatically and creation order is irrelevant.")
    if not selection:
        return ("selection-unknown",
                "no repository_selection was returned, so nothing can be said "
                "about how the installation grows.")
    if repo_created is None or installation_created is None:
        return ("creation-order-unknown",
                "one of the two creation dates is missing, so the order "
                "cannot be established.")
    if repo_created > installation_created:
        days = int((repo_created - installation_created) // 86400)
        return ("repo-created-after-installation",
                "this repository was created %d day(s) after the installation, "
                "and a selected-repositories installation does not gain new "
                "ones. Every repository created from now on will land in the "
                "same state." % days)
    return ("repo-predates-installation",
            "the repository already existed when the installation was "
            "configured, so it was left out deliberately or by oversight "
            "rather than by the passage of time.")


def repair_for(state, selection):
    """The sentence worth printing under a verdict. Pure."""
    if state == "installed-on-account-not-repo":
        if str(selection or "").lower() == "selected":
            return ("add this repository to the installation, or switch the "
                    "installation to all repositories so future ones are "
                    "covered without anybody remembering to.")
        return ("open the installation's configuration and add this "
                "repository to it.")
    if state == "not-installed-on-account":
        return ("install the App on this account. This needs somebody with "
                "admin rights on the account, and it is not something a token "
                "change can substitute for.")
    if state == "installed-on-this-repo":
        return ("nothing to repair here. If calls still fail, read the status "
                "code and the message rather than assuming coverage.")
    if state == "jwt-not-accepted":
        return ("fix the App JWT before reading anything above; an unusable "
                "JWT and an absent installation look the same from here.")
    return "no repair applies to this state."


def get(path, token=None):
    """One GET. Returns (status, body). The only network in this script."""
    headers = {"Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28", "User-Agent": UA}
    if token:
        headers["Authorization"] = "Bearer " + token
    r = requests.get(API + path, timeout=30, headers=headers)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True,
                    help="the repository, as owner/name or as any GitHub URL "
                         "for it")
    args = ap.parse_args()

    target = split_repo(args.repo)
    if target is None:
        log.error("could not read %r as a repository reference", args.repo)
        return 2
    owner, name = target

    jwt = os.environ.get("GITHUB_APP_JWT")
    if not jwt:
        log.error("set GITHUB_APP_JWT to the App JWT. The per-repository "
                  "installation route is answered with the JWT, not with an "
                  "installation access token")
        return 2

    # No credential on this one on purpose: whether the repository is publicly
    # readable is a fact about the world, not about the App.
    public_status, public_body = get("/repos/%s/%s" % (owner, name))
    vis_state, vis_detail = visibility(public_status)
    log.info("%s: %s", vis_state, vis_detail)
    owner_type = None
    repo_created = None
    if isinstance(public_body, dict):
        owner_type = (public_body.get("owner") or {}).get("type")
        repo_created = parse_iso(public_body.get("created_at"))

    repo_status, repo_body = get("/repos/%s/%s/installation" % (owner, name), jwt)
    log.info("GET /repos/%s/%s/installation returned %d", owner, name, repo_status)

    route = account_route(owner, owner_type)
    account_status, account_body = get(route, jwt)
    log.info("GET %s returned %d", route, account_status)

    state, detail = classify(repo_status, account_status)
    log.info("%s: %s", state, detail)

    installation = repo_body if repo_status == 200 else account_body
    selection = None
    installation_created = None
    installation_id = None
    if isinstance(installation, dict):
        selection = installation.get("repository_selection")
        installation_created = parse_iso(installation.get("created_at"))
        installation_id = installation.get("id")
    if installation_id is not None:
        log.info("installation %s, repository_selection=%s",
                 installation_id, selection or "unknown")

    order_state, order_detail = creation_order(repo_created,
                                               installation_created, selection)
    log.info("%s: %s", order_state, order_detail)
    log.info("repair: %s", repair_for(state, selection))

    print(json.dumps({"owner": owner, "repo": name,
                      "public_status": public_status,
                      "repo_installation_status": repo_status,
                      "account_installation_status": account_status,
                      "account_route": route,
                      "repository_selection": selection,
                      "installation_id": installation_id,
                      "visibility": vis_state, "order": order_state,
                      "state": state}, indent=2))
    return 0 if state == "installed-on-this-repo" else 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-app-installation-presence.mjs",
"js": '''/**
 * Say whether a GitHub App is installed on one specific repository.
 *
 * Read only. Three GETs: one unauthenticated existence check, and two
 * presence questions asked with the App's JWT, at repository scope and at
 * account scope. Nothing is installed, added, changed or minted.
 *
 * An installation access token cannot see outside its installation, and
 * GitHub answers 404 rather than 403 for anything outside it, so a public
 * repository the App was never installed on is indistinguishable from one
 * that does not exist. GET /repos/{owner}/{repo}/installation answers
 * directly.
 *
 * The JWT is read from the environment and never printed.
 */
const API = 'https://api.github.com';
const UA = 'github-app-installation-presence/1.0';

/** Owner and repository names GitHub will actually issue. */
const NAME = /^[A-Za-z0-9._-]+$/;

/** Every way a repository reference tends to arrive in a bug report. */
const PREFIXES = ['https://github.com/', 'http://github.com/',
  'https://api.github.com/repos/', 'git@github.com:'];

/**
 * Reduce any repository reference to [owner, name]. Pure.
 * null when it is not a repository reference at all.
 */
export function splitRepo(value) {
  let text = String(value ?? '').trim().replace(/\\/+$/, '');
  for (const prefix of PREFIXES) {
    if (text.startsWith(prefix)) {
      text = text.slice(prefix.length);
      break;
    }
  }
  if (text.endsWith('.git')) text = text.slice(0, -4);
  const parts = text.split('/').filter(Boolean);
  if (parts.length < 2) return null;
  const [owner, name] = parts;
  if (!NAME.test(owner) || !NAME.test(name)) return null;
  return [owner, name];
}

/**
 * The account-scope installation route for this kind of owner. Pure.
 * The wrong one 404s for reasons that have nothing to do with the App.
 */
export function accountRoute(owner, ownerType) {
  if (String(ownerType ?? '').toLowerCase() === 'user') {
    return `/users/${owner}/installation`;
  }
  return `/orgs/${owner}/installation`;
}

/** Parse an ISO-8601 timestamp into epoch seconds. Pure. null if unusable. */
export function parseIso(value) {
  const text = String(value ?? '').trim();
  if (!text) return null;
  const ms = Date.parse(text);
  return Number.isNaN(ms) ? null : ms / 1000;
}

/** What the unauthenticated read proved about the repository. Pure. */
export function visibility(status) {
  if (status === 200) {
    return ['public-repo',
      'the repository exists and is publicly readable, so whatever is wrong ' +
      'is on your side of the request.'];
  }
  if (status === 404) {
    return ['not-public-or-absent',
      'an unauthenticated read also returns 404, which means the repository ' +
      'is private or does not exist. A read-only check cannot separate those ' +
      'two, and neither can anyone else without access.'];
  }
  return ['visibility-unknown',
    'the unauthenticated read returned something other than 200 or 404, so ' +
    'nothing was established about the repository itself.'];
}

/**
 * Turn two presence questions into one verdict. Pure.
 * Repository scope first: a 200 there ends the matter. The account answer is
 * what splits one 404 into two different repairs.
 */
export function classify(repoStatus, accountStatus) {
  if ([401, 403].includes(repoStatus) || [401, 403].includes(accountStatus)) {
    return ['jwt-not-accepted',
      'the App JWT was refused, so nothing was learned about any ' +
      'installation. Fix the JWT first; a signing or clock fault looks like ' +
      'an absent installation from here.'];
  }
  if (repoStatus === 200) {
    return ['installed-on-this-repo',
      'the App is installed on this repository, so a 404 from your ' +
      'integration is about something else: a permission, a wrong path, or a ' +
      'credential that is not this App\\'s.'];
  }
  if (repoStatus === 404 && accountStatus === 200) {
    return ['installed-on-account-not-repo',
      'the App is installed on the account and this repository is not in the ' +
      'installation. The installation is set to selected repositories and ' +
      'this one was never selected.'];
  }
  if (repoStatus === 404 && accountStatus === 404) {
    return ['not-installed-on-account',
      'the App is not installed anywhere on this account. Somebody with ' +
      'admin rights on the account has to install it; no permission or token ' +
      'change will do anything until they do.'];
  }
  return ['inconclusive',
    'the two presence checks did not return a pair this check recognises, so ' +
    'no verdict is safe.'];
}

/**
 * Say whether the repository is simply newer than the installation. Pure.
 * This is the difference between a mistake and a recurring condition.
 */
export function creationOrder(repoCreated, installationCreated, selection) {
  if (String(selection ?? '').toLowerCase() === 'all') {
    return ['selection-covers-everything',
      'repository_selection is all, so new repositories are covered ' +
      'automatically and creation order is irrelevant.'];
  }
  if (!selection) {
    return ['selection-unknown',
      'no repository_selection was returned, so nothing can be said about ' +
      'how the installation grows.'];
  }
  if (repoCreated === null || repoCreated === undefined
      || installationCreated === null || installationCreated === undefined) {
    return ['creation-order-unknown',
      'one of the two creation dates is missing, so the order cannot be ' +
      'established.'];
  }
  if (repoCreated > installationCreated) {
    const days = Math.trunc((repoCreated - installationCreated) / 86400);
    return ['repo-created-after-installation',
      `this repository was created ${days} day(s) after the installation, and ` +
      'a selected-repositories installation does not gain new ones. Every ' +
      'repository created from now on will land in the same state.'];
  }
  return ['repo-predates-installation',
    'the repository already existed when the installation was configured, so ' +
    'it was left out deliberately or by oversight rather than by the passage ' +
    'of time.'];
}

/** The sentence worth printing under a verdict. Pure. */
export function repairFor(state, selection) {
  if (state === 'installed-on-account-not-repo') {
    if (String(selection ?? '').toLowerCase() === 'selected') {
      return 'add this repository to the installation, or switch the ' +
        'installation to all repositories so future ones are covered without ' +
        'anybody remembering to.';
    }
    return 'open the installation\\'s configuration and add this repository to it.';
  }
  if (state === 'not-installed-on-account') {
    return 'install the App on this account. This needs somebody with admin ' +
      'rights on the account, and it is not something a token change can ' +
      'substitute for.';
  }
  if (state === 'installed-on-this-repo') {
    return 'nothing to repair here. If calls still fail, read the status code ' +
      'and the message rather than assuming coverage.';
  }
  if (state === 'jwt-not-accepted') {
    return 'fix the App JWT before reading anything above; an unusable JWT ' +
      'and an absent installation look the same from here.';
  }
  return 'no repair applies to this state.';
}

async function get(path, token) {
  const headers = {
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  const res = await fetch(API + path, { headers });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return [res.status, body];
}

function flag(name) {
  const at = process.argv.indexOf(name);
  return (at === -1 || at === process.argv.length - 1) ? null : process.argv[at + 1];
}

async function main() {
  const target = splitRepo(flag('--repo'));
  if (!target) {
    console.error('pass --repo owner/name, or any GitHub URL for the repository');
    process.exitCode = 2;
    return;
  }
  const [owner, name] = target;

  const jwt = process.env.GITHUB_APP_JWT;
  if (!jwt) {
    console.error('set GITHUB_APP_JWT to the App JWT. The per-repository ' +
      'installation route is answered with the JWT, not with an installation ' +
      'access token');
    process.exitCode = 2;
    return;
  }

  // No credential on this one on purpose: whether the repository is publicly
  // readable is a fact about the world, not about the App.
  const [publicStatus, publicBody] = await get(`/repos/${owner}/${name}`);
  const [visState, visDetail] = visibility(publicStatus);
  console.log(`${visState}: ${visDetail}`);
  const ownerType = publicBody && publicBody.owner ? publicBody.owner.type : null;
  const repoCreated = publicBody ? parseIso(publicBody.created_at) : null;

  const [repoStatus, repoBody] = await get(`/repos/${owner}/${name}/installation`, jwt);
  console.log(`GET /repos/${owner}/${name}/installation returned ${repoStatus}`);

  const route = accountRoute(owner, ownerType);
  const [accountStatus, accountBody] = await get(route, jwt);
  console.log(`GET ${route} returned ${accountStatus}`);

  const [state, detail] = classify(repoStatus, accountStatus);
  console.log(`${state}: ${detail}`);

  const installation = repoStatus === 200 ? repoBody : accountBody;
  const selection = installation ? installation.repository_selection : null;
  const installationCreated = installation ? parseIso(installation.created_at) : null;
  const installationId = installation ? installation.id : null;
  if (installationId !== null && installationId !== undefined) {
    console.log(`installation ${installationId}, ` +
      `repository_selection=${selection ?? 'unknown'}`);
  }

  const [orderState, orderDetail] = creationOrder(repoCreated, installationCreated, selection);
  console.log(`${orderState}: ${orderDetail}`);
  console.log(`repair: ${repairFor(state, selection)}`);

  console.log(JSON.stringify({
    owner,
    repo: name,
    public_status: publicStatus,
    repo_installation_status: repoStatus,
    account_installation_status: accountStatus,
    account_route: route,
    repository_selection: selection ?? null,
    installation_id: installationId ?? null,
    visibility: visState,
    order: orderState,
    state,
  }, null, 2));
  process.exitCode = state === 'installed-on-this-repo' ? 0 : 1;
}

// Only run when invoked directly, so importing this module from the test file
// does not execute main() and set an exit code that fails a passing suite.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "There is nothing to fake here but two status codes, which is the point: the whole verdict is a lookup over the pair of answers the two presence routes gave, so every case is one line. The reference parser gets its own group of tests because a bug report will contain a browser URL as often as an <code>owner/name</code> pair, and a parser that quietly disagreed with itself would produce a confident 404 about a repository nobody asked about. The creation-date comparison is tested for the case that matters most: a repository younger than the installation that will never be covered by it.",
"test_py_file": "test_github_app_installation_presence.py",
"test_py": '''from github_app_installation_presence import (
    account_route, classify, creation_order, parse_iso, repair_for, split_repo,
    visibility,
)

JAN = parse_iso("2026-01-01T00:00:00Z")
MAR = parse_iso("2026-03-02T00:00:00Z")


def test_every_shape_of_repository_reference_lands_on_the_same_pair():
    assert split_repo("acme/reporting") == ("acme", "reporting")
    assert split_repo("https://github.com/acme/reporting") == ("acme", "reporting")
    assert split_repo("https://github.com/acme/reporting/") == ("acme", "reporting")
    assert split_repo("https://github.com/acme/reporting/pulls/12") == ("acme", "reporting")
    assert split_repo("https://api.github.com/repos/acme/reporting") == ("acme", "reporting")
    assert split_repo("git@github.com:acme/reporting.git") == ("acme", "reporting")


def test_something_that_is_not_a_repository_reference_is_refused():
    assert split_repo("acme") is None
    assert split_repo("") is None
    assert split_repo(None) is None
    assert split_repo("acme/repo with spaces") is None


def test_organizations_and_user_accounts_have_different_routes():
    assert account_route("acme", "Organization") == "/orgs/acme/installation"
    assert account_route("octocat", "User") == "/users/octocat/installation"
    assert account_route("acme", None) == "/orgs/acme/installation"


def test_a_public_repository_narrows_the_search_to_your_own_app():
    state, detail = visibility(200)
    assert state == "public-repo"
    assert "your side of the request" in detail


def test_a_404_without_a_credential_is_two_answers_and_says_so():
    state, detail = visibility(404)
    assert state == "not-public-or-absent"
    assert "cannot separate those two" in detail
    assert visibility(500)[0] == "visibility-unknown"


def test_installed_on_the_account_but_not_the_repository_is_the_headline():
    state, detail = classify(404, 200)
    assert state == "installed-on-account-not-repo"
    assert "never selected" in detail
    assert "add this repository" in repair_for(state, "selected")


def test_not_installed_at_all_is_a_different_repair_and_a_different_person():
    state, detail = classify(404, 404)
    assert state == "not-installed-on-account"
    assert "admin rights" in repair_for(state, None)


def test_installed_here_means_the_404_came_from_somewhere_else():
    state, detail = classify(200, 200)
    assert state == "installed-on-this-repo"
    assert "about something else" in detail


def test_a_refused_jwt_is_not_reported_as_an_absent_installation():
    assert classify(401, 404)[0] == "jwt-not-accepted"
    assert classify(404, 403)[0] == "jwt-not-accepted"
    assert "Fix the JWT first" in classify(401, 404)[1]


def test_an_unrecognised_pair_gets_no_verdict():
    assert classify(500, 200)[0] == "inconclusive"


def test_a_repository_newer_than_the_installation_is_a_recurring_cause():
    state, detail = creation_order(MAR, JAN, "selected")
    assert state == "repo-created-after-installation"
    assert "60 day(s) after" in detail
    assert "Every repository created from now on" in detail


def test_a_repository_older_than_the_installation_was_left_out_by_hand():
    assert creation_order(JAN, MAR, "selected")[0] == "repo-predates-installation"


def test_an_installation_covering_everything_makes_the_dates_irrelevant():
    state, detail = creation_order(MAR, JAN, "all")
    assert state == "selection-covers-everything"
    assert "automatically" in detail


def test_missing_inputs_produce_a_named_state_rather_than_a_guess():
    assert creation_order(None, JAN, "selected")[0] == "creation-order-unknown"
    assert creation_order(MAR, None, "selected")[0] == "creation-order-unknown"
    assert creation_order(MAR, JAN, None)[0] == "selection-unknown"


def test_timestamps_that_cannot_be_read_are_none_rather_than_an_exception():
    assert parse_iso("2026-01-01T00:00:00Z") is not None
    assert parse_iso("last thursday") is None
    assert parse_iso("") is None
    assert parse_iso(None) is None
''',
"test_js_file": "github-app-installation-presence.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  accountRoute, classify, creationOrder, parseIso, repairFor, splitRepo,
  visibility,
} from './github-app-installation-presence.mjs';

const JAN = parseIso('2026-01-01T00:00:00Z');
const MAR = parseIso('2026-03-02T00:00:00Z');

test('every shape of repository reference lands on the same pair', () => {
  assert.deepEqual(splitRepo('acme/reporting'), ['acme', 'reporting']);
  assert.deepEqual(splitRepo('https://github.com/acme/reporting'), ['acme', 'reporting']);
  assert.deepEqual(splitRepo('https://github.com/acme/reporting/'), ['acme', 'reporting']);
  assert.deepEqual(splitRepo('https://github.com/acme/reporting/pulls/12'), ['acme', 'reporting']);
  assert.deepEqual(splitRepo('https://api.github.com/repos/acme/reporting'), ['acme', 'reporting']);
  assert.deepEqual(splitRepo('git@github.com:acme/reporting.git'), ['acme', 'reporting']);
});

test('something that is not a repository reference is refused', () => {
  assert.equal(splitRepo('acme'), null);
  assert.equal(splitRepo(''), null);
  assert.equal(splitRepo(null), null);
  assert.equal(splitRepo('acme/repo with spaces'), null);
});

test('organizations and user accounts have different routes', () => {
  assert.equal(accountRoute('acme', 'Organization'), '/orgs/acme/installation');
  assert.equal(accountRoute('octocat', 'User'), '/users/octocat/installation');
  assert.equal(accountRoute('acme', null), '/orgs/acme/installation');
});

test('a public repository narrows the search to your own app', () => {
  const [state, detail] = visibility(200);
  assert.equal(state, 'public-repo');
  assert.match(detail, /your side of the request/);
});

test('a 404 without a credential is two answers and says so', () => {
  const [state, detail] = visibility(404);
  assert.equal(state, 'not-public-or-absent');
  assert.match(detail, /cannot separate those two/);
  assert.equal(visibility(500)[0], 'visibility-unknown');
});

test('installed on the account but not the repository is the headline', () => {
  const [state, detail] = classify(404, 200);
  assert.equal(state, 'installed-on-account-not-repo');
  assert.match(detail, /never selected/);
  assert.match(repairFor(state, 'selected'), /add this repository/);
});

test('not installed at all is a different repair and a different person', () => {
  const [state] = classify(404, 404);
  assert.equal(state, 'not-installed-on-account');
  assert.match(repairFor(state, null), /admin rights/);
});

test('installed here means the 404 came from somewhere else', () => {
  const [state, detail] = classify(200, 200);
  assert.equal(state, 'installed-on-this-repo');
  assert.match(detail, /about something else/);
});

test('a refused jwt is not reported as an absent installation', () => {
  assert.equal(classify(401, 404)[0], 'jwt-not-accepted');
  assert.equal(classify(404, 403)[0], 'jwt-not-accepted');
  assert.match(classify(401, 404)[1], /Fix the JWT first/);
});

test('an unrecognised pair gets no verdict', () => {
  assert.equal(classify(500, 200)[0], 'inconclusive');
});

test('a repository newer than the installation is a recurring cause', () => {
  const [state, detail] = creationOrder(MAR, JAN, 'selected');
  assert.equal(state, 'repo-created-after-installation');
  assert.match(detail, /60 day\\(s\\) after/);
  assert.match(detail, /Every repository created from now on/);
});

test('a repository older than the installation was left out by hand', () => {
  assert.equal(creationOrder(JAN, MAR, 'selected')[0], 'repo-predates-installation');
});

test('an installation covering everything makes the dates irrelevant', () => {
  const [state, detail] = creationOrder(MAR, JAN, 'all');
  assert.equal(state, 'selection-covers-everything');
  assert.match(detail, /automatically/);
});

test('missing inputs produce a named state rather than a guess', () => {
  assert.equal(creationOrder(null, JAN, 'selected')[0], 'creation-order-unknown');
  assert.equal(creationOrder(MAR, null, 'selected')[0], 'creation-order-unknown');
  assert.equal(creationOrder(MAR, JAN, null)[0], 'selection-unknown');
});

test('timestamps that cannot be read are null rather than an exception', () => {
  assert.notEqual(parseIso('2026-01-01T00:00:00Z'), null);
  assert.equal(parseIso('last thursday'), null);
  assert.equal(parseIso(''), null);
  assert.equal(parseIso(null), null);
});
''',
"faq": [
 ("Why 404 and not 403?",
  "Because 403 would confirm the repository exists, and for a private repository that is information the caller has not earned. GitHub applies the same rule everywhere rather than case by case, so a public repository outside your installation gets the same answer as a private one you have never heard of. It is the right trade and it is genuinely expensive to debug, which is why the useful move is to stop reading the status code and ask a route whose whole job is to answer the presence question."),
 ("The App works on eleven repositories and fails on the twelfth. Surely that is a repository problem?",
  "It almost never is. Eleven successes prove the credential, the App, the permissions and the network, all of which are shared. What is not shared is membership of the installation, and that is per repository. The quickest disproof is one request: GET /repos/{owner}/{repo}/installation under the App JWT returns the installation for any repository the App is installed on, so a 404 there settles it before anybody opens the repository's settings page."),
 ("Why does a brand new repository fail when the old ones work?",
  "Because an installation set to selected repositories does not grow. The list was fixed when somebody configured it, and a repository created afterwards is simply not on it. This is the most common cause of the whole failure and the one most likely to recur, since every future repository lands in the same state. Comparing the repository's creation date against the installation's is what turns a shrug into a sentence, and it is why the durable repair is usually switching the installation to all repositories rather than adding one."),
 ("Can I check this with the installation access token instead of the JWT?",
  "The per-repository presence route wants the App's JWT, so no. What an installation token can do is list what it reaches, which answers a related but different question: how much of the account the installation covers, in total. That measurement, and the gap between it and the account's real repository count, is its own note. For a single named repository the JWT route is one request and gives a yes or a no rather than a list you then have to search."),
 ("The App is installed on the repository and I still get 404. What now?",
  "Then this note is finished and the 404 is masking something else. The usual candidates are a permission the App does not hold on an endpoint that answers 404 rather than 403 for missing permissions, a path built from the wrong owner or a renamed repository, or a credential that is not this App's at all. Triaging a 404 across those causes is a separate check, and it starts by establishing which credential is actually in the header rather than which one you meant to put there."),
],
"related": [
 ("/github/installation-repository-selection-partial/", "An installation that covers only some repositories"),
 ("/github/404-masking-403/", "A permission error disguised as 404 Not Found"),
 ("/github/app-permission-missing/", "Resource not accessible by integration"),
],
"citations": [CITE_APP_INSTALL_AUTH, CITE_INSTALLATIONS_REST, CITE_INSTALLING, CITE_APPS_REST],
},

]
