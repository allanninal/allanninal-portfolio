#!/usr/bin/env python3
"""Amazon SES field notes, part two: reputation, observability and alignment.

Split from guides_ses.py because appending to a Python literal with string surgery
broke it twice. Two files that both export GUIDES and get concatenated is duller and
does not break.
"""

GUIDES = [

# ─────────────────────────────────────────────────────────────────────────────
{
"slug": "ses-bounce-rate-approaching-review",
"title": "SES Bounce Rate Creeping Toward Account Review",
"description": "AWS reviews accounts at a 5% bounce rate and 0.1% complaints. The dashboard shows today, not the trend, so the first warning is often the review email itself.",
"h1": "SES bounce rate creeping toward account review",
"category": "Amazon SES",
"pill": "Monitoring",
"chips": ["CloudWatch metrics", "Python and Node.js", "Detect before AWS does"],
"keywords": ["SES bounce rate", "SES complaint rate", "SES account review",
             "SES reputation metrics", "CloudWatch SES Reputation"],
"deps": "Python 3.9+ with boto3, or Node.js 18+ with @aws-sdk/client-cloudwatch",
"lead": "Nobody watches the SES reputation dashboard daily. The number that matters is a rolling average, so a bad import on Tuesday keeps pushing the average up all week while each individual day looks survivable. By the time an email from AWS arrives saying the account is under review, the damage is a fortnight old and the fix &mdash; cleaning the list &mdash; takes longer than the review does.",
"short_answer": """<p>AWS publishes two thresholds: a <strong>bounce rate at or above 5%</strong> puts an account under review, and <strong>10%</strong> risks a sending pause. For complaints the numbers are <strong>0.1%</strong> and <strong>0.5%</strong>. They are computed over a rolling window, not per day.</p>
<p>Both are available as CloudWatch metrics (<code>AWS/SES</code>, <code>Reputation.BounceRate</code> and <code>Reputation.ComplaintRate</code>), so a scheduled script can alert you at a threshold you choose rather than the one AWS enforces.</p>""",
"problem": """<p>The rates are not shown to you at send time. Nothing in the API response tells you that this send pushed you over a line. The console has a reputation page, but it shows the current value rather than the trajectory, and current values that sit just under the threshold look fine right up until they do not.</p>
<p>What makes it dangerous is the lag. Bounce rate is an average over recent sending, so one bad batch keeps affecting the number long after you stopped sending it. If you only look when something feels wrong, you are looking at a number that already includes the damage.</p>""",
"why": """<p><strong>List quality decays quietly.</strong> Addresses go dead constantly: people leave companies, domains lapse, mailboxes fill. A list that bounced at 1% a year ago can bounce at 6% today with nobody changing anything.</p>
<p><strong>Imports skip validation.</strong> The most common cause of a sudden spike is a bulk import of addresses that were never confirmed &mdash; a purchased list, a CSV from an old system, a form with no double opt-in.</p>
<p><strong>Complaints are a different signal entirely.</strong> A complaint means someone pressed 'this is spam'. The threshold is 40 times stricter than the bounce one, because receivers treat it as much stronger evidence. A campaign that bounces cleanly can still be fatal on complaints.</p>""",
"steps": [
 {"h": "Read the actual numbers",
  "body": """<p>The rates live in CloudWatch, not in the SES API:</p>
<pre><code class="language-bash">aws cloudwatch get-metric-statistics \\\\
  --namespace AWS/SES --metric-name Reputation.BounceRate \\\\
  --start-time "$(date -u -v-14d '+%Y-%m-%dT%H:%M:%SZ')" \\\\
  --end-time "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" \\\\
  --period 86400 --statistics Maximum</code></pre>
<p>The value is a fraction, so <code>0.05</code> is 5%.</p>"""},
 {"h": "Alert at your threshold, not AWS's",
  "body": """<p>Alerting at 5% means alerting when you are already under review. Set your own line well below it &mdash; 2% for bounces and 0.05% for complaints gives room to act. The script takes both as arguments so the numbers live in your config, not buried in code.</p>"""},
 {"h": "Watch the direction, not just the level",
  "body": """<p>A flat 3% is a list-quality problem to schedule. A 1% that became 3% in four days is an incident happening right now. The script reports the trend across the window so the two are distinguishable, because they need different responses.</p>"""},
 {"h": "Fix the cause, not the number",
  "body": """<p>When it spikes, find the send that caused it. Attach a configuration set per campaign type so bounces are attributable, stop the offending list, and validate addresses before the next import. Removing addresses from the suppression list does <em>not</em> lower the rate &mdash; it raises it, because the retries bounce again.</p>"""},
],
"verify": """<p>Run the detector after a cleanup. The rate falls slowly, because it is an average over recent sending &mdash; expect days, not minutes:</p>
<pre><code class="language-bash">python ses_reputation_watch.py --days 14 --max-bounce 0.02 --max-complaint 0.0005
# exits 0 when both are under your thresholds, non-zero otherwise</code></pre>
<p>Run it on a schedule and page on the non-zero exit.</p>""",
"code_intro": "The script pulls both reputation metrics from CloudWatch over a window you choose, compares them against your own thresholds rather than the enforcement ones, and reports whether each is rising or steady. It exits non-zero on breach so it can drive an alert.",
"py_file": "ses_reputation_watch.py",
"py": '''"""Alert on SES bounce and complaint rates before AWS acts on them.

AWS reviews at 5% bounces / 0.1% complaints and can pause sending at 10% / 0.5%.
Alerting at those numbers means alerting when it is already too late, so the
thresholds here default well below and are configurable.
"""
import argparse
import datetime as dt
import logging
import sys

import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ses_reputation_watch")

AWS_REVIEW_BOUNCE = 0.05
AWS_REVIEW_COMPLAINT = 0.001


def fetch(cw, metric, days):
    end = dt.datetime.now(dt.timezone.utc)
    points = cw.get_metric_statistics(
        Namespace="AWS/SES",
        MetricName=metric,
        StartTime=end - dt.timedelta(days=days),
        EndTime=end,
        Period=86400,
        Statistics=["Maximum"],
    )["Datapoints"]
    return [p["Maximum"] for p in sorted(points, key=lambda p: p["Timestamp"])]


def judge(series, threshold, label):
    """Pure decision function over a daily series.

    Reports level AND direction, because a flat 3% is a list to clean next sprint
    while a 1% that became 3% this week is an incident happening now.
    """
    if not series:
        return [f"{label}: no data (has the account sent anything?)"]
    latest = series[-1]
    problems = []
    if latest >= threshold:
        problems.append(f"{label}: {latest:.3%} is at or over your {threshold:.3%} threshold")
    if len(series) >= 4:
        earlier = sum(series[:len(series) // 2]) / (len(series) // 2)
        recent = sum(series[len(series) // 2:]) / (len(series) - len(series) // 2)
        if earlier > 0 and recent > earlier * 1.5:
            problems.append(
                f"{label}: rising fast, {earlier:.3%} -> {recent:.3%} across the window")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--days", type=int, default=14)
    ap.add_argument("--max-bounce", type=float, default=0.02)
    ap.add_argument("--max-complaint", type=float, default=0.0005)
    args = ap.parse_args()

    cw = boto3.client("cloudwatch", region_name=args.region)
    problems = []
    for metric, threshold, label in (
        ("Reputation.BounceRate", args.max_bounce, "bounce rate"),
        ("Reputation.ComplaintRate", args.max_complaint, "complaint rate"),
    ):
        series = fetch(cw, metric, args.days)
        if series:
            log.info("%s: latest %.3%%, peak %.3%% over %d days",
                     label, series[-1] * 100, max(series) * 100, args.days)
        problems += judge(series, threshold, label)

    for p in problems:
        log.error(p)
    if problems:
        log.error("AWS reviews at %.0f%% bounces / %.1f%% complaints",
                  AWS_REVIEW_BOUNCE * 100, AWS_REVIEW_COMPLAINT * 100)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "ses-reputation-watch.mjs",
"js": '''/**
 * Alert on SES bounce and complaint rates before AWS acts on them.
 *
 * AWS reviews at 5% bounces / 0.1% complaints and can pause sending at 10% / 0.5%.
 * Alerting at those numbers means alerting when it is already too late, so the
 * thresholds here default well below and are configurable.
 */
import { CloudWatchClient, GetMetricStatisticsCommand } from '@aws-sdk/client-cloudwatch';

const AWS_REVIEW_BOUNCE = 0.05;
const AWS_REVIEW_COMPLAINT = 0.001;

async function fetchSeries(cw, MetricName, days) {
  const EndTime = new Date();
  const StartTime = new Date(EndTime.getTime() - days * 86400_000);
  const out = await cw.send(new GetMetricStatisticsCommand({
    Namespace: 'AWS/SES', MetricName, StartTime, EndTime,
    Period: 86400, Statistics: ['Maximum'],
  }));
  return (out.Datapoints ?? [])
    .sort((a, b) => a.Timestamp - b.Timestamp)
    .map((p) => p.Maximum);
}

/**
 * Pure decision function over a daily series.
 *
 * Reports level AND direction, because a flat 3% is a list to clean next sprint
 * while a 1% that became 3% this week is an incident happening now.
 */
export function judge(series, threshold, label) {
  if (!series.length) return [`${label}: no data (has the account sent anything?)`];
  const pct = (n) => `${(n * 100).toFixed(3)}%`;
  const latest = series.at(-1);
  const problems = [];
  if (latest >= threshold) {
    problems.push(`${label}: ${pct(latest)} is at or over your ${pct(threshold)} threshold`);
  }
  if (series.length >= 4) {
    const half = Math.floor(series.length / 2);
    const mean = (a) => a.reduce((x, y) => x + y, 0) / a.length;
    const earlier = mean(series.slice(0, half));
    const recent = mean(series.slice(half));
    if (earlier > 0 && recent > earlier * 1.5) {
      problems.push(`${label}: rising fast, ${pct(earlier)} -> ${pct(recent)} across the window`);
    }
  }
  return problems;
}

async function main() {
  const region = process.env.AWS_REGION ?? 'us-east-1';
  const days = Number(process.env.DAYS ?? 14);
  const maxBounce = Number(process.env.MAX_BOUNCE ?? 0.02);
  const maxComplaint = Number(process.env.MAX_COMPLAINT ?? 0.0005);
  const cw = new CloudWatchClient({ region });

  const problems = [];
  for (const [metric, threshold, label] of [
    ['Reputation.BounceRate', maxBounce, 'bounce rate'],
    ['Reputation.ComplaintRate', maxComplaint, 'complaint rate'],
  ]) {
    problems.push(...judge(await fetchSeries(cw, metric, days), threshold, label));
  }
  problems.forEach((p) => console.error(p));
  if (problems.length) {
    console.error(`AWS reviews at ${AWS_REVIEW_BOUNCE * 100}% bounces / ${AWS_REVIEW_COMPLAINT * 100}% complaints`);
  }
  process.exit(problems.length ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The judgement is separated from CloudWatch so both halves of it &mdash; the level and the trend &mdash; can be tested against fixed series without an AWS account.",
"test_py_file": "test_ses_reputation_watch.py",
"test_py": '''from ses_reputation_watch import judge


def test_empty_series_is_reported_not_ignored():
    assert judge([], 0.02, "bounce rate")


def test_under_threshold_and_flat_is_quiet():
    assert judge([0.01, 0.01, 0.011, 0.01], 0.02, "bounce rate") == []


def test_over_threshold_is_reported():
    problems = judge([0.01, 0.01, 0.01, 0.03], 0.02, "bounce rate")
    assert any("threshold" in p for p in problems)


def test_a_sharp_rise_is_caught_below_the_threshold():
    """0.9% is under a 2% threshold, but tripling in a week is the real signal."""
    problems = judge([0.003, 0.003, 0.009, 0.009], 0.02, "bounce rate")
    assert any("rising fast" in p for p in problems)


def test_short_series_does_not_claim_a_trend():
    assert judge([0.001, 0.001], 0.02, "bounce rate") == []
''',
"test_js_file": "ses-reputation-watch.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { judge } from './ses-reputation-watch.mjs';

test('an empty series is reported, not ignored', () => {
  assert.ok(judge([], 0.02, 'bounce rate').length);
});

test('under threshold and flat is quiet', () => {
  assert.deepEqual(judge([0.01, 0.01, 0.011, 0.01], 0.02, 'bounce rate'), []);
});

test('over threshold is reported', () => {
  const p = judge([0.01, 0.01, 0.01, 0.03], 0.02, 'bounce rate');
  assert.ok(p.some((x) => x.includes('threshold')));
});

test('a sharp rise is caught below the threshold', () => {
  const p = judge([0.003, 0.003, 0.009, 0.009], 0.02, 'bounce rate');
  assert.ok(p.some((x) => x.includes('rising fast')));
});
''',
"faq": [
 ("What bounce rate does AWS actually act on?",
  "AWS places an account under review at a bounce rate of 5% and may pause sending at 10%. For complaints the numbers are 0.1% and 0.5%. They are rolling averages over recent sending, not per-day figures, so a single bad batch affects the number for days afterwards."),
 ("Why alert at 2% when the limit is 5%?",
  "Because the rate lags. By the time it reads 5% the sends that caused it are days old and cleaning the list takes longer than the review. A threshold at 2% gives you the room to find and stop the cause."),
 ("Does removing addresses from the suppression list lower my bounce rate?",
  "No, it raises it. Those addresses bounced before; retrying them produces fresh bounces that count again. Suppression is what protects the rate — the fix is a cleaner list, not a shorter suppression list."),
 ("Bounces are fine but complaints are high. Is that different?",
  "Very. A complaint is someone pressing 'this is spam', and the threshold is 40 times stricter. High complaints with low bounces usually means the addresses are real but the mail is unwanted: check consent, sending frequency, and whether unsubscribe actually works."),
 ("Can I get this per campaign rather than per account?",
  "Yes. Send through a configuration set per campaign type and the events are attributable to it, so you can see which send moved the number. Without one, the account-level rate is all you get."),
],
"related": [
 ("/email/ses-suppression-list-blocks-a-real-customer/", "SES suppression list silently blocks a real customer"),
 ("/email/ses-no-event-destination/", "SES bounces and complaints are invisible with no event destination"),
 ("/email/ses-still-in-sandbox/", "SES silently rejects real recipients: still in the sandbox"),
],
"citations": [
 ("Amazon SES reputation metrics and account review — AWS docs",
  "https://docs.aws.amazon.com/ses/latest/dg/reputationdashboard-cloudwatch-schedule.html"),
 ("Bounce and complaint rates — AWS docs",
  "https://docs.aws.amazon.com/pinpoint/latest/userguide/channels-email-deliverability-dashboard-bounce-complaint.html"),
 ("Troubleshooting Amazon SES issues — AWS docs",
  "https://docs.aws.amazon.com/ses/latest/dg/troubleshoot.html"),
],
},

# ─────────────────────────────────────────────────────────────────────────────
{
"slug": "ses-no-event-destination",
"title": "SES Bounces Are Invisible With No Event Destination",
"description": "SES returns a MessageId whether or not the mail is delivered. With no event destination on the configuration set, nothing records what happened next.",
"h1": "SES bounces and complaints are invisible with no event destination",
"category": "Amazon SES",
"pill": "Observability",
"chips": ["SES configuration sets", "Python and Node.js", "Fixable through the API"],
"keywords": ["SES event destination", "SES configuration set", "SES bounce notification",
             "CreateConfigurationSetEventDestination", "SES CloudWatch events"],
"deps": "Python 3.9+ with boto3, or Node.js 18+ with @aws-sdk/client-sesv2",
"lead": "This is the note that makes the other five findable. SES returns a <code>MessageId</code> the moment it accepts a request, and that is the last thing most applications ever learn about the message. Whether it was delivered, bounced, suppressed, or complained about is published as an <em>event</em> &mdash; and if no configuration set carries an event destination, those events go nowhere and the information is simply lost.",
"short_answer": """<p>A <code>MessageId</code> means SES accepted the request. It does not mean anything was delivered. Delivery, bounce, complaint, reject and rendering-failure outcomes are published as events, and only if the send used a <strong>configuration set with an event destination</strong> attached.</p>
<p>Create one with <code>CreateConfigurationSetEventDestination</code> pointing at CloudWatch, SNS or Kinesis Firehose, then set it as the default for the identity so every send is covered without touching application code.</p>""",
"problem": """<p>Support says a customer never received their receipt. You check the logs: the send succeeded, here is the message ID. There is nowhere else to look. You cannot tell whether it bounced, whether it was suppressed before it left, whether the recipient marked it as spam, or whether it was delivered and they simply missed it.</p>
<p>Each of those has a different fix, and without events you cannot tell them apart. Teams end up guessing, or asking the customer to check their spam folder, which is the support equivalent of turning it off and on again.</p>""",
"why": """<p><strong>Event publishing is opt-in and off by default.</strong> A fresh SES account sends perfectly well with no configuration set at all, so nothing forces the decision at setup time and it is easy to never make it.</p>
<p><strong>The default configuration set is a separate setting again.</strong> Creating a configuration set does nothing unless sends actually reference it. You either pass <code>ConfigurationSetName</code> on every call &mdash; which means touching every code path &mdash; or set it as the identity default, which most people do not know exists.</p>
<p><strong>The gap is invisible while things work.</strong> Nobody misses bounce data until the first mystery, and by then the events for that message are long gone. Events are not retroactive; you only get them from the moment the destination exists.</p>""",
"steps": [
 {"h": "Find out what you have",
  "body": """<p>List the configuration sets and check whether each one actually has a destination attached. An empty configuration set is the common trap &mdash; it exists, so it looks configured, and it publishes nothing.</p>
<pre><code class="language-bash">aws sesv2 list-configuration-sets
aws sesv2 get-configuration-set-event-destinations --configuration-set-name default</code></pre>"""},
 {"h": "Create a destination that covers the failures",
  "body": """<p>Subscribe to the event types that mean something went wrong: <code>BOUNCE</code>, <code>COMPLAINT</code>, <code>REJECT</code>, <code>RENDERING_FAILURE</code>, and <code>DELIVERY_DELAY</code>. Add <code>DELIVERY</code> too if you want positive confirmation. CloudWatch is the least effort to start with; SNS is right if you want to act on events in code.</p>"""},
 {"h": "Make it the default for the identity",
  "body": """<p><code>PutEmailIdentityConfigurationSetAttributes</code> attaches a configuration set to a domain or address so every send from it is covered, including sends from code you have not touched in two years.</p>"""},
 {"h": "Keep one per traffic type",
  "body": """<p>One configuration set for transactional and one for marketing means the reputation numbers are attributable. When the bounce rate moves you can see which stream moved it, which is the difference between a fix and a guess.</p>"""},
],
"verify": """<p>Send a message to the AWS bounce simulator and confirm an event arrives:</p>
<pre><code class="language-bash">aws sesv2 send-email \\\\
  --from-email-address you@yourdomain.com \\\\
  --destination ToAddresses=bounce@simulator.amazonses.com \\\\
  --configuration-set-name transactional \\\\
  --content 'Simple={Subject={Data=test},Body={Text={Data=test}}}'</code></pre>
<p>Within a minute a <code>Bounce</code> event should appear at your destination. If nothing arrives, the destination is not attached to the configuration set the send actually used.</p>""",
"code_intro": "The script audits every configuration set for a destination that covers the failure event types, reports which identities have no default configuration set, and can create a CloudWatch destination with the right event types. It reports by default and writes only with <code>--apply</code>.",
"py_file": "ses_event_destination_audit.py",
"py": '''"""Audit SES configuration sets for event destinations that cover failures.

A configuration set with no destination publishes nothing, which is the common
trap: it exists, so it looks configured. This reports the gap and can create a
CloudWatch destination covering the event types that mean something went wrong.
"""
import argparse
import logging
import sys

import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ses_event_destination_audit")

# The outcomes worth knowing about. DELIVERY is optional; the rest are failures.
REQUIRED_EVENTS = {"BOUNCE", "COMPLAINT", "REJECT", "RENDERING_FAILURE"}


def missing_events(destinations):
    """Pure decision function. Which failure events is nothing listening for?

    An enabled destination is the only kind that counts -- a disabled one is
    indistinguishable from no destination at all, and is easy to miss by eye.
    """
    covered = set()
    for d in destinations:
        if not d.get("Enabled", False):
            continue
        covered |= {e.upper() for e in d.get("MatchingEventTypes", [])}
    return sorted(REQUIRED_EVENTS - covered)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--create-on", help="configuration set to add a CloudWatch destination to")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    ses = boto3.client("sesv2", region_name=args.region)

    names = ses.list_configuration_sets().get("ConfigurationSets", [])
    if not names:
        log.error("no configuration sets exist, so no send can publish any event")
    for name in names:
        dests = ses.get_configuration_set_event_destinations(
            ConfigurationSetName=name).get("EventDestinations", [])
        gaps = missing_events(dests)
        if gaps:
            log.error("%s: nothing is listening for %s", name, ", ".join(gaps))
        else:
            log.info("%s: all failure events covered", name)

    # Identities that do not default to a configuration set send unattributed mail.
    for ident in ses.list_email_identities().get("EmailIdentities", []):
        detail = ses.get_email_identity(EmailIdentity=ident["IdentityName"])
        if not detail.get("ConfigurationSetName"):
            log.warning("%s: no default configuration set; sends publish nothing",
                        ident["IdentityName"])

    if args.create_on:
        params = {
            "ConfigurationSetName": args.create_on,
            "EventDestinationName": "failures-to-cloudwatch",
            "EventDestination": {
                "Enabled": True,
                "MatchingEventTypes": sorted(REQUIRED_EVENTS),
                "CloudWatchDestination": {
                    "DimensionConfigurations": [{
                        "DimensionName": "ses:configuration-set",
                        "DimensionValueSource": "MESSAGE_TAG",
                        "DefaultDimensionValue": args.create_on,
                    }]
                },
            },
        }
        if args.apply:
            ses.create_configuration_set_event_destination(**params)
            log.info("created failures-to-cloudwatch on %s", args.create_on)
        else:
            log.info("WOULD create failures-to-cloudwatch on %s -- pass --apply", args.create_on)
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "ses-event-destination-audit.mjs",
"js": '''/**
 * Audit SES configuration sets for event destinations that cover failures.
 *
 * A configuration set with no destination publishes nothing, which is the common
 * trap: it exists, so it looks configured.
 */
import {
  SESv2Client,
  ListConfigurationSetsCommand,
  GetConfigurationSetEventDestinationsCommand,
  CreateConfigurationSetEventDestinationCommand,
  ListEmailIdentitiesCommand,
  GetEmailIdentityCommand,
} from '@aws-sdk/client-sesv2';

// The outcomes worth knowing about. DELIVERY is optional; the rest are failures.
const REQUIRED_EVENTS = ['BOUNCE', 'COMPLAINT', 'REJECT', 'RENDERING_FAILURE'];

/**
 * Pure decision function. Which failure events is nothing listening for?
 *
 * An enabled destination is the only kind that counts -- a disabled one is
 * indistinguishable from no destination at all, and is easy to miss by eye.
 */
export function missingEvents(destinations) {
  const covered = new Set();
  for (const d of destinations) {
    if (!d.Enabled) continue;
    for (const e of d.MatchingEventTypes ?? []) covered.add(String(e).toUpperCase());
  }
  return REQUIRED_EVENTS.filter((e) => !covered.has(e));
}

async function main() {
  const region = process.env.AWS_REGION ?? 'us-east-1';
  const apply = process.argv.includes('--apply');
  const createOn = process.argv[process.argv.indexOf('--create-on') + 1];
  const ses = new SESv2Client({ region });

  const { ConfigurationSets = [] } = await ses.send(new ListConfigurationSetsCommand({}));
  if (!ConfigurationSets.length) {
    console.error('no configuration sets exist, so no send can publish any event');
  }
  for (const name of ConfigurationSets) {
    const { EventDestinations = [] } = await ses.send(
      new GetConfigurationSetEventDestinationsCommand({ ConfigurationSetName: name }));
    const gaps = missingEvents(EventDestinations);
    if (gaps.length) console.error(`${name}: nothing is listening for ${gaps.join(', ')}`);
    else console.log(`${name}: all failure events covered`);
  }

  const { EmailIdentities = [] } = await ses.send(new ListEmailIdentitiesCommand({}));
  for (const ident of EmailIdentities) {
    const detail = await ses.send(new GetEmailIdentityCommand({ EmailIdentity: ident.IdentityName }));
    if (!detail.ConfigurationSetName) {
      console.warn(`${ident.IdentityName}: no default configuration set; sends publish nothing`);
    }
  }

  if (createOn && process.argv.includes('--create-on')) {
    const params = {
      ConfigurationSetName: createOn,
      EventDestinationName: 'failures-to-cloudwatch',
      EventDestination: {
        Enabled: true,
        MatchingEventTypes: REQUIRED_EVENTS,
        CloudWatchDestination: {
          DimensionConfigurations: [{
            DimensionName: 'ses:configuration-set',
            DimensionValueSource: 'MESSAGE_TAG',
            DefaultDimensionValue: createOn,
          }],
        },
      },
    };
    if (apply) {
      await ses.send(new CreateConfigurationSetEventDestinationCommand(params));
      console.log(`created failures-to-cloudwatch on ${createOn}`);
    } else {
      console.log(`WOULD create failures-to-cloudwatch on ${createOn} -- pass --apply`);
    }
  }
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The check that matters is subtle: a destination that exists but is disabled covers nothing, and reads as configured in the console. The test pins that down.",
"test_py_file": "test_ses_event_destination_audit.py",
"test_py": '''from ses_event_destination_audit import missing_events


def test_no_destinations_means_everything_is_missing():
    assert set(missing_events([])) == {"BOUNCE", "COMPLAINT", "REJECT", "RENDERING_FAILURE"}


def test_full_coverage_reports_nothing():
    dests = [{"Enabled": True,
              "MatchingEventTypes": ["BOUNCE", "COMPLAINT", "REJECT", "RENDERING_FAILURE"]}]
    assert missing_events(dests) == []


def test_a_disabled_destination_covers_nothing():
    """It exists, so the console makes it look configured. It publishes nothing."""
    dests = [{"Enabled": False,
              "MatchingEventTypes": ["BOUNCE", "COMPLAINT", "REJECT", "RENDERING_FAILURE"]}]
    assert len(missing_events(dests)) == 4


def test_coverage_is_summed_across_destinations():
    dests = [
        {"Enabled": True, "MatchingEventTypes": ["BOUNCE", "COMPLAINT"]},
        {"Enabled": True, "MatchingEventTypes": ["REJECT", "RENDERING_FAILURE"]},
    ]
    assert missing_events(dests) == []


def test_event_names_are_compared_case_insensitively():
    dests = [{"Enabled": True, "MatchingEventTypes": ["bounce", "complaint", "reject",
                                                      "rendering_failure"]}]
    assert missing_events(dests) == []
''',
"test_js_file": "ses-event-destination-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { missingEvents } from './ses-event-destination-audit.mjs';

const ALL = ['BOUNCE', 'COMPLAINT', 'REJECT', 'RENDERING_FAILURE'];

test('no destinations means everything is missing', () => {
  assert.deepEqual(missingEvents([]), ALL);
});

test('full coverage reports nothing', () => {
  assert.deepEqual(missingEvents([{ Enabled: true, MatchingEventTypes: ALL }]), []);
});

test('a disabled destination covers nothing', () => {
  assert.equal(missingEvents([{ Enabled: false, MatchingEventTypes: ALL }]).length, 4);
});

test('coverage is summed across destinations', () => {
  const dests = [
    { Enabled: true, MatchingEventTypes: ['BOUNCE', 'COMPLAINT'] },
    { Enabled: true, MatchingEventTypes: ['REJECT', 'RENDERING_FAILURE'] },
  ];
  assert.deepEqual(missingEvents(dests), []);
});
''',
"faq": [
 ("Does a MessageId mean the email was delivered?",
  "No. It means SES accepted the request. The message can still be suppressed before it leaves, rejected by the receiver, or bounce. Delivery is a separate event you only see if a configuration set with an event destination was used."),
 ("I created a configuration set but still see no events. Why?",
  "Two likely reasons. The configuration set may have no event destination attached — it exists but publishes nothing. Or the sends are not referencing it: either pass ConfigurationSetName on the call, or set it as the identity default so every send is covered."),
 ("CloudWatch, SNS or Kinesis Firehose?",
  "CloudWatch for metrics and alarms with the least setup. SNS when you want to react in code, for example writing bounces back to your own suppression table. Firehose when you want the raw events in S3 or a warehouse for analysis."),
 ("Can I get events for messages I already sent?",
  "No. Events are published as they happen and are not retroactive. You only get data from the moment the destination exists, which is why this is worth doing before you need it."),
 ("Do I need more than one configuration set?",
  "One per traffic type is worth it. With transactional and marketing separated, reputation numbers are attributable to a stream, so when the bounce rate moves you can see which one moved it."),
],
"related": [
 ("/email/ses-suppression-list-blocks-a-real-customer/", "SES suppression list silently blocks a real customer"),
 ("/email/ses-bounce-rate-approaching-review/", "SES bounce rate creeping toward account review"),
 ("/email/ses-mail-from-not-set/", "SES passes SPF and DKIM but DMARC still fails"),
],
"citations": [
 ("Monitoring email sending using Amazon SES event publishing — AWS docs",
  "https://docs.aws.amazon.com/ses/latest/dg/monitor-using-event-publishing.html"),
 ("Amazon SES event destinations — AWS docs",
  "https://docs.aws.amazon.com/ses/latest/dg/event-publishing-add-event-destination.html"),
 ("boto3 sesv2 create_configuration_set_event_destination",
  "https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sesv2/client/create_configuration_set_event_destination.html"),
],
},

# ─────────────────────────────────────────────────────────────────────────────
{
"slug": "ses-mail-from-not-set",
"title": "SES Passes SPF and DKIM but DMARC Still Fails",
"description": "SPF passes, DKIM passes, DMARC fails. The Return-Path is an amazonses.com subdomain, so SPF authenticates a domain that is not the one in the From header.",
"h1": "SES passes SPF and DKIM but DMARC still fails",
"category": "Amazon SES",
"pill": "Authentication",
"chips": ["SES custom MAIL FROM", "Python and Node.js", "Fixable through the API"],
"keywords": ["SES MAIL FROM domain", "DMARC alignment", "Return-Path amazonses.com",
             "PutEmailIdentityMailFromAttributes", "SPF alignment"],
"deps": "Python 3.9+ with boto3, or Node.js 18+ with @aws-sdk/client-sesv2, plus DNS access",
"lead": "The authentication headers look like a pass. <code>spf=pass</code>. <code>dkim=pass</code>. And then <code>dmarc=fail</code>, which reads like a contradiction until you look at what SPF actually authenticated. Without a custom MAIL FROM domain, SES uses its own <code>amazonses.com</code> subdomain as the Return-Path, so SPF passes <em>for that domain</em> &mdash; not for the one in your From header. DMARC requires alignment, and those two do not align.",
"short_answer": """<p>DMARC does not ask whether SPF passed. It asks whether SPF passed <strong>for the same domain as the From header</strong>. SES defaults the Return-Path to an <code>amazonses.com</code> subdomain, so SPF authenticates Amazon's domain and alignment fails.</p>
<p>Set a custom MAIL FROM domain with <code>PutEmailIdentityMailFromAttributes</code>, publish its MX and SPF records, and SPF starts authenticating a subdomain of yours, which aligns.</p>""",
"problem": """<p>You set up SES, published the DKIM CNAMEs, added an SPF record, and every test tool says SPF and DKIM pass. Then a DMARC report shows failures, or Gmail puts the mail in spam and the headers say <code>dmarc=fail</code>.</p>
<p>The mail is not forged and nothing is misconfigured in the usual sense. It is an alignment problem: DMARC passes if <em>either</em> SPF or DKIM passes <em>and</em> aligns with the From domain. DKIM usually saves you here, which is why many setups look fine &mdash; until a forwarder breaks the DKIM signature and SPF is the only thing left, and SPF is aligned to Amazon.</p>""",
"why": """<p><strong>The Return-Path is not the From address.</strong> SPF authenticates the envelope sender, which lives in the Return-Path, and receivers see whatever SES put there. By default that is a subdomain of <code>amazonses.com</code>.</p>
<p><strong>Alignment is the whole point of DMARC.</strong> Anyone can pass SPF for a domain they control. DMARC asks whether the domain that passed is the domain the recipient sees, which is what makes it useful against spoofing &mdash; and what makes the default SES setup fail it on the SPF side.</p>
<p><strong>DKIM masks the problem.</strong> With Easy DKIM the signature is aligned, DMARC passes on the DKIM leg, and nobody notices SPF is misaligned. The day a mailing list or forwarder rewrites the body, DKIM breaks, SPF is all that is left, and mail that worked for a year starts failing.</p>""",
"steps": [
 {"h": "Confirm what the Return-Path actually is",
  "body": """<p>Send yourself a message and look at the raw headers. If <code>Return-Path</code> ends in <code>amazonses.com</code> while <code>From</code> is your domain, that is the misalignment.</p>
<pre><code class="language-bash">aws sesv2 get-email-identity --email-identity yourdomain.com \\\\
  --query 'MailFromAttributes'</code></pre>
<p>An empty result, or <code>MailFromDomainStatus</code> of <code>PENDING</code>, means it is not in effect.</p>"""},
 {"h": "Choose a subdomain, not the root",
  "body": """<p>Use something like <code>mail.yourdomain.com</code>. The MAIL FROM domain needs its own MX record, and putting an MX on your root domain would interfere with receiving mail there. A dedicated subdomain avoids that entirely.</p>"""},
 {"h": "Set it on the identity",
  "body": """<p><code>PutEmailIdentityMailFromAttributes</code> takes the subdomain and a behaviour for when the records are missing. <code>USE_DEFAULT_VALUE</code> falls back to the amazonses.com domain if DNS is not ready, which keeps mail flowing; <code>REJECT_MESSAGE</code> fails the send instead. Start with the former.</p>"""},
 {"h": "Publish the two DNS records",
  "body": """<p>The subdomain needs an MX pointing at the SES inbound endpoint for your region, and a TXT SPF record containing <code>include:amazonses.com</code>. SES reports <code>SUCCESS</code> once it can see both.</p>"""},
],
"verify": """<p>Check the status is <code>SUCCESS</code>, then read the headers of a real message:</p>
<pre><code class="language-bash">aws sesv2 get-email-identity --email-identity yourdomain.com \\\\
  --query 'MailFromAttributes.MailFromDomainStatus'
# SUCCESS</code></pre>
<p>In the received message, <code>Return-Path</code> should now be at <code>mail.yourdomain.com</code>, and <code>Authentication-Results</code> should show <code>spf=pass</code> with that domain plus <code>dmarc=pass</code>.</p>""",
"code_intro": "The script reports the MAIL FROM state for every identity, flags the ones still defaulting to amazonses.com, and can set a subdomain on one. It prints the DNS records you then need to publish, because that half cannot be done from the SES API.",
"py_file": "ses_mail_from_audit.py",
"py": '''"""Report SES identities whose Return-Path is not aligned with the From domain.

DMARC passes only if SPF or DKIM passes AND aligns with the From domain. Without a
custom MAIL FROM, SES uses an amazonses.com subdomain, so the SPF leg never aligns
and DMARC rests entirely on DKIM -- which breaks the first time a forwarder rewrites
the message.
"""
import argparse
import logging
import sys

import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ses_mail_from_audit")


def alignment_problem(identity, attrs):
    """Pure decision function over GetEmailIdentity's MailFromAttributes.

    Three distinct states matter, and only one of them is fine.
    """
    domain = (attrs or {}).get("MailFromDomain")
    status = (attrs or {}).get("MailFromDomainStatus")
    if not domain:
        return f"{identity}: no custom MAIL FROM, so SPF aligns to amazonses.com and DMARC rests on DKIM alone"
    if status != "SUCCESS":
        return f"{identity}: MAIL FROM {domain} is {status}, so SES is still using the default"
    if not domain.endswith(identity) and identity not in domain:
        return f"{identity}: MAIL FROM {domain} is not a subdomain of the identity, so it does not align"
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--set-on", help="identity to configure")
    ap.add_argument("--subdomain", help="e.g. mail.yourdomain.com")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    ses = boto3.client("sesv2", region_name=args.region)

    problems = 0
    for ident in ses.list_email_identities().get("EmailIdentities", []):
        name = ident["IdentityName"]
        detail = ses.get_email_identity(EmailIdentity=name)
        problem = alignment_problem(name, detail.get("MailFromAttributes"))
        if problem:
            problems += 1
            log.error(problem)
        else:
            log.info("%s: MAIL FROM aligned", name)

    if args.set_on and args.subdomain:
        if args.apply:
            ses.put_email_identity_mail_from_attributes(
                EmailIdentity=args.set_on,
                MailFromDomain=args.subdomain,
                BehaviorOnMxFailure="USE_DEFAULT_VALUE",
            )
            log.info("set MAIL FROM %s on %s", args.subdomain, args.set_on)
        else:
            log.info("WOULD set MAIL FROM %s on %s -- pass --apply", args.subdomain, args.set_on)
        log.info("now publish, in the %s zone:", args.subdomain)
        log.info("  MX  10 feedback-smtp.%s.amazonses.com", args.region)
        log.info('  TXT "v=spf1 include:amazonses.com ~all"')
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "ses-mail-from-audit.mjs",
"js": '''/**
 * Report SES identities whose Return-Path is not aligned with the From domain.
 *
 * DMARC passes only if SPF or DKIM passes AND aligns with the From domain. Without
 * a custom MAIL FROM, SES uses an amazonses.com subdomain, so the SPF leg never
 * aligns and DMARC rests entirely on DKIM.
 */
import {
  SESv2Client,
  ListEmailIdentitiesCommand,
  GetEmailIdentityCommand,
  PutEmailIdentityMailFromAttributesCommand,
} from '@aws-sdk/client-sesv2';

/**
 * Pure decision function over GetEmailIdentity's MailFromAttributes.
 * Three distinct states matter, and only one of them is fine.
 */
export function alignmentProblem(identity, attrs) {
  const domain = attrs?.MailFromDomain;
  const status = attrs?.MailFromDomainStatus;
  if (!domain) {
    return `${identity}: no custom MAIL FROM, so SPF aligns to amazonses.com and DMARC rests on DKIM alone`;
  }
  if (status !== 'SUCCESS') {
    return `${identity}: MAIL FROM ${domain} is ${status}, so SES is still using the default`;
  }
  if (!domain.endsWith(identity) && !domain.includes(identity)) {
    return `${identity}: MAIL FROM ${domain} is not a subdomain of the identity, so it does not align`;
  }
  return null;
}

async function main() {
  const region = process.env.AWS_REGION ?? 'us-east-1';
  const apply = process.argv.includes('--apply');
  const setOn = process.argv[process.argv.indexOf('--set-on') + 1];
  const subdomain = process.argv[process.argv.indexOf('--subdomain') + 1];
  const ses = new SESv2Client({ region });

  let problems = 0;
  const { EmailIdentities = [] } = await ses.send(new ListEmailIdentitiesCommand({}));
  for (const ident of EmailIdentities) {
    const name = ident.IdentityName;
    const detail = await ses.send(new GetEmailIdentityCommand({ EmailIdentity: name }));
    const problem = alignmentProblem(name, detail.MailFromAttributes);
    if (problem) { problems += 1; console.error(problem); }
    else console.log(`${name}: MAIL FROM aligned`);
  }

  if (process.argv.includes('--set-on') && subdomain) {
    if (apply) {
      await ses.send(new PutEmailIdentityMailFromAttributesCommand({
        EmailIdentity: setOn, MailFromDomain: subdomain,
        BehaviorOnMxFailure: 'USE_DEFAULT_VALUE',
      }));
      console.log(`set MAIL FROM ${subdomain} on ${setOn}`);
    } else {
      console.log(`WOULD set MAIL FROM ${subdomain} on ${setOn} -- pass --apply`);
    }
    console.log(`now publish, in the ${subdomain} zone:`);
    console.log(`  MX  10 feedback-smtp.${region}.amazonses.com`);
    console.log('  TXT "v=spf1 include:amazonses.com ~all"');
  }
  process.exit(problems ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "Three states look similar and mean different things: no MAIL FROM at all, one that is set but still pending, and one set to a domain that does not actually align. The test separates them.",
"test_py_file": "test_ses_mail_from_audit.py",
"test_py": '''from ses_mail_from_audit import alignment_problem


def test_no_mail_from_is_a_problem():
    assert "amazonses.com" in alignment_problem("example.com", None)


def test_empty_attributes_are_treated_as_absent():
    assert alignment_problem("example.com", {}) is not None


def test_pending_status_is_still_a_problem():
    """SES has not verified the DNS yet, so it is still using the default."""
    out = alignment_problem("example.com",
                            {"MailFromDomain": "mail.example.com",
                             "MailFromDomainStatus": "PENDING"})
    assert "PENDING" in out


def test_aligned_subdomain_is_clean():
    assert alignment_problem("example.com",
                             {"MailFromDomain": "mail.example.com",
                              "MailFromDomainStatus": "SUCCESS"}) is None


def test_unrelated_domain_does_not_align():
    out = alignment_problem("example.com",
                            {"MailFromDomain": "mail.other.net",
                             "MailFromDomainStatus": "SUCCESS"})
    assert "does not align" in out
''',
"test_js_file": "ses-mail-from-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { alignmentProblem } from './ses-mail-from-audit.mjs';

test('no MAIL FROM is a problem', () => {
  assert.match(alignmentProblem('example.com', undefined), /amazonses\\.com/);
});

test('pending status is still a problem', () => {
  const out = alignmentProblem('example.com',
    { MailFromDomain: 'mail.example.com', MailFromDomainStatus: 'PENDING' });
  assert.match(out, /PENDING/);
});

test('an aligned subdomain is clean', () => {
  assert.equal(alignmentProblem('example.com',
    { MailFromDomain: 'mail.example.com', MailFromDomainStatus: 'SUCCESS' }), null);
});

test('an unrelated domain does not align', () => {
  const out = alignmentProblem('example.com',
    { MailFromDomain: 'mail.other.net', MailFromDomainStatus: 'SUCCESS' });
  assert.match(out, /does not align/);
});
''',
"faq": [
 ("How can SPF pass and DMARC still fail?",
  "DMARC does not ask whether SPF passed. It asks whether SPF passed for the same domain that appears in the From header. SES defaults the Return-Path to an amazonses.com subdomain, so SPF passes for Amazon's domain, which does not align with yours."),
 ("Why does it work today if SPF is misaligned?",
  "Because DMARC passes if either SPF or DKIM aligns, and Easy DKIM aligns. You are relying entirely on the DKIM leg. The day a mailing list or forwarder modifies the message, the DKIM signature breaks and there is nothing left to pass."),
 ("Why a subdomain rather than the root domain?",
  "The MAIL FROM domain requires its own MX record. Putting one on your root domain would interfere with receiving mail there. A dedicated subdomain such as mail.yourdomain.com keeps the two separate."),
 ("What does BehaviorOnMxFailure change?",
  "USE_DEFAULT_VALUE falls back to the amazonses.com domain if the MX record is missing, so mail keeps flowing while DNS propagates. REJECT_MESSAGE fails the send instead. Start with the former and tighten later if you want the stricter guarantee."),
 ("Do I still need my own SPF record on the root domain?",
  "Yes, for the From domain. The MAIL FROM subdomain needs its own SPF record too, containing include:amazonses.com. They serve different checks and both matter."),
],
"related": [
 ("/dns/dmarc-stuck-at-p-none/", "DMARC stuck at p=none and never enforcing"),
 ("/dns/spf-exceeds-lookup-limit/", "SPF exceeds the 10 DNS lookup limit"),
 ("/email/ses-no-event-destination/", "SES bounces are invisible with no event destination"),
],
"citations": [
 ("Using a custom MAIL FROM domain — AWS docs",
  "https://docs.aws.amazon.com/ses/latest/dg/mail-from.html"),
 ("Complying with DMARC authentication protocol in Amazon SES — AWS docs",
  "https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dmarc.html"),
 ("boto3 sesv2 put_email_identity_mail_from_attributes",
  "https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sesv2/client/put_email_identity_mail_from_attributes.html"),
],
},

# ─────────────────────────────────────────────────────────────────────────────
{
"slug": "ses-identity-verified-but-dkim-drifted",
"title": "SES Identity Still Verified but Its DKIM Records Have Drifted",
"description": "SES shows the domain as verified while the DKIM CNAMEs no longer resolve. Signing degrades quietly after a DNS migration, and DMARC starts failing weeks later.",
"h1": "SES identity still shows verified but its DKIM records have drifted",
"category": "Amazon SES",
"pill": "Diagnostic",
"chips": ["SES identity API", "Python and Node.js", "Detect through the API"],
"keywords": ["SES DKIM not signing", "DkimAttributes Status", "SES verified but failing",
             "Easy DKIM CNAME missing", "SES DNS migration"],
"deps": "Python 3.9+ with boto3 and dnspython, or Node.js 18+ with @aws-sdk/client-sesv2",
"lead": "Someone moved the DNS to a new provider and exported the old zone to do it. The export missed the three Easy DKIM CNAMEs, because they are long, look like machine noise, and nobody remembered what they were for. SES kept reporting the identity as verified for a while, mail kept sending, and the only visible change was that DMARC reports slowly filled with failures nobody was reading.",
"short_answer": """<p>SES tracks two things separately: whether the identity is <strong>verified for sending</strong> and whether <strong>DKIM signing</strong> is working. A domain can read verified while its DKIM tokens no longer resolve, and mail keeps going out unsigned.</p>
<p><code>GetEmailIdentity</code> exposes <code>DkimAttributes.Status</code> and the tokens. Compare those tokens against live DNS and you catch the drift before DMARC does.</p>""",
"problem": """<p>Nothing errors. Sends succeed, the console shows a verified domain, and for a while DKIM may still show as successful because SES caches the last good state. Meanwhile the CNAMEs that make signing possible are gone, so messages go out without a valid signature.</p>
<p>The consequence is delayed and indirect: DMARC then rests on SPF alone, which &mdash; if you have not set a custom MAIL FROM &mdash; does not align either. Mail that authenticated fine for a year starts landing in spam, and the change that caused it was a DNS migration weeks earlier.</p>""",
"why": """<p><strong>Easy DKIM tokens look disposable.</strong> Three CNAMEs with random-looking names pointing at <code>dkim.amazonses.com</code>. In a zone export, or a manual rebuild at a new registrar, they are the records most likely to be dropped as noise.</p>
<p><strong>Verification and signing are different checks.</strong> Identity verification can be satisfied by a TXT record or by the DKIM records depending on how it was set up, so one can survive while the other does not.</p>
<p><strong>The failure is silent by construction.</strong> An unsigned message is still a valid message. Nothing rejects it at send time. The only signal is in the receiving side's authentication results and in DMARC aggregate reports, and neither is somewhere anyone looks daily.</p>""",
"steps": [
 {"h": "Ask SES what it thinks the tokens are",
  "body": """<p><code>GetEmailIdentity</code> returns the DKIM status and, for Easy DKIM, the three tokens SES expects to find:</p>
<pre><code class="language-bash">aws sesv2 get-email-identity --email-identity yourdomain.com \\\\
  --query '{Verified:VerifiedForSendingStatus,Dkim:DkimAttributes}'</code></pre>"""},
 {"h": "Resolve each token against live DNS",
  "body": """<p>For each token, <code>&lt;token&gt;._domainkey.yourdomain.com</code> must be a CNAME to <code>&lt;token&gt;.dkim.amazonses.com</code>. Resolving them yourself is the part SES cannot do for you on demand, and it is what turns 'probably fine' into a definite answer.</p>"""},
 {"h": "Republish anything missing",
  "body": """<p>The tokens do not change when records go missing, so republishing the same three CNAMEs restores signing. If the identity was deleted and recreated the tokens will differ, and every one has to be republished.</p>"""},
 {"h": "Run the check on a schedule",
  "body": """<p>This is a drift problem, so a one-off check has a short shelf life. Running it weekly catches the next migration, the next registrar move, and the next well-meaning zone cleanup.</p>"""},
],
"verify": """<p>Resolve one token by hand and confirm SES agrees:</p>
<pre><code class="language-bash">dig +short abcdefg._domainkey.yourdomain.com CNAME
# abcdefg.dkim.amazonses.com.

aws sesv2 get-email-identity --email-identity yourdomain.com \\\\
  --query 'DkimAttributes.Status'
# SUCCESS</code></pre>
<p>Then send a message and check the received headers show <code>dkim=pass</code> with your domain.</p>""",
"code_intro": "The script asks SES for the expected DKIM tokens, resolves each one against live DNS, and reports any that are missing or point somewhere unexpected. It is read-only: publishing DNS records is your DNS provider's job, so it prints exactly what to add.",
"py_file": "ses_dkim_drift_check.py",
"py": '''"""Detect SES identities whose DKIM CNAMEs no longer resolve.

SES can report an identity as verified while DKIM signing has quietly stopped,
because the two are tracked separately. Mail then goes out unsigned and DMARC
starts failing weeks after whatever DNS change caused it.

Read-only. It prints the records to republish rather than writing DNS.
"""
import argparse
import logging
import sys

import boto3
import dns.resolver

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ses_dkim_drift_check")


def expected_cname(token, identity):
    """The record SES needs to exist for one Easy DKIM token."""
    return f"{token}._domainkey.{identity}", f"{token}.dkim.amazonses.com"


def resolve_cname(name):
    try:
        answers = dns.resolver.resolve(name, "CNAME")
        return str(answers[0].target).rstrip(".")
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return None


def check_identity(identity, dkim, resolver=resolve_cname):
    """Pure-ish decision function: the DNS lookup is injected so tests can fake it."""
    problems = []
    status = (dkim or {}).get("Status")
    tokens = (dkim or {}).get("Tokens") or []
    if status != "SUCCESS":
        problems.append(f"{identity}: SES reports DKIM status {status}")
    if not tokens:
        problems.append(f"{identity}: no DKIM tokens; signing is not configured")
        return problems
    for token in tokens:
        name, want = expected_cname(token, identity)
        got = resolver(name)
        if got is None:
            problems.append(f"{identity}: {name} does not resolve; republish CNAME -> {want}")
        elif got.rstrip(".") != want:
            problems.append(f"{identity}: {name} points at {got}, expected {want}")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="us-east-1")
    args = ap.parse_args()

    ses = boto3.client("sesv2", region_name=args.region)
    failed = False
    for ident in ses.list_email_identities().get("EmailIdentities", []):
        name = ident["IdentityName"]
        if ident.get("IdentityType") != "DOMAIN":
            continue
        detail = ses.get_email_identity(EmailIdentity=name)
        problems = check_identity(name, detail.get("DkimAttributes"))
        for p in problems:
            failed = True
            log.error(p)
        if not problems:
            log.info("%s: DKIM signing intact", name)
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "ses-dkim-drift-check.mjs",
"js": '''/**
 * Detect SES identities whose DKIM CNAMEs no longer resolve.
 *
 * SES can report an identity as verified while DKIM signing has quietly stopped,
 * because the two are tracked separately. Read-only: it prints the records to
 * republish rather than writing DNS.
 */
import { promises as dns } from 'node:dns';
import {
  SESv2Client,
  ListEmailIdentitiesCommand,
  GetEmailIdentityCommand,
} from '@aws-sdk/client-sesv2';

export function expectedCname(token, identity) {
  return {
    name: `${token}._domainkey.${identity}`,
    want: `${token}.dkim.amazonses.com`,
  };
}

async function resolveCname(name) {
  try {
    const [target] = await dns.resolveCname(name);
    return target ?? null;
  } catch {
    return null;
  }
}

/** Pure-ish decision function: the DNS lookup is injected so tests can fake it. */
export async function checkIdentity(identity, dkim, resolver = resolveCname) {
  const problems = [];
  const status = dkim?.Status;
  const tokens = dkim?.Tokens ?? [];
  if (status !== 'SUCCESS') problems.push(`${identity}: SES reports DKIM status ${status}`);
  if (!tokens.length) {
    problems.push(`${identity}: no DKIM tokens; signing is not configured`);
    return problems;
  }
  for (const token of tokens) {
    const { name, want } = expectedCname(token, identity);
    const got = await resolver(name);
    if (got === null) {
      problems.push(`${identity}: ${name} does not resolve; republish CNAME -> ${want}`);
    } else if (got.replace(/\\.$/, '') !== want) {
      problems.push(`${identity}: ${name} points at ${got}, expected ${want}`);
    }
  }
  return problems;
}

async function main() {
  const ses = new SESv2Client({ region: process.env.AWS_REGION ?? 'us-east-1' });
  let failed = false;
  const { EmailIdentities = [] } = await ses.send(new ListEmailIdentitiesCommand({}));
  for (const ident of EmailIdentities) {
    if (ident.IdentityType !== 'DOMAIN') continue;
    const detail = await ses.send(new GetEmailIdentityCommand({ EmailIdentity: ident.IdentityName }));
    const problems = await checkIdentity(ident.IdentityName, detail.DkimAttributes);
    problems.forEach((p) => { failed = true; console.error(p); });
    if (!problems.length) console.log(`${ident.IdentityName}: DKIM signing intact`);
  }
  process.exit(failed ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The DNS lookup is injected, so the whole rule &mdash; missing record, wrong target, no tokens at all &mdash; is testable offline with a fake resolver.",
"test_py_file": "test_ses_dkim_drift_check.py",
"test_py": '''from ses_dkim_drift_check import check_identity, expected_cname

DKIM_OK = {"Status": "SUCCESS", "Tokens": ["aaa", "bbb", "ccc"]}


def resolver_all_good(name):
    token = name.split("._domainkey.")[0]
    return f"{token}.dkim.amazonses.com"


def resolver_nothing(_name):
    return None


def test_expected_cname_shape():
    name, want = expected_cname("aaa", "example.com")
    assert name == "aaa._domainkey.example.com"
    assert want == "aaa.dkim.amazonses.com"


def test_all_records_present_is_clean():
    assert check_identity("example.com", DKIM_OK, resolver_all_good) == []


def test_missing_records_are_reported_with_the_fix():
    problems = check_identity("example.com", DKIM_OK, resolver_nothing)
    assert len(problems) == 3
    assert all("republish CNAME" in p for p in problems)


def test_no_tokens_short_circuits():
    problems = check_identity("example.com", {"Status": "SUCCESS", "Tokens": []},
                              resolver_all_good)
    assert any("not configured" in p for p in problems)


def test_wrong_target_is_caught():
    problems = check_identity("example.com", DKIM_OK,
                              lambda _n: "somewhere.else.example")
    assert all("expected" in p for p in problems)
''',
"test_js_file": "ses-dkim-drift-check.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { checkIdentity, expectedCname } from './ses-dkim-drift-check.mjs';

const DKIM_OK = { Status: 'SUCCESS', Tokens: ['aaa', 'bbb', 'ccc'] };
const allGood = async (name) => `${name.split('._domainkey.')[0]}.dkim.amazonses.com`;
const nothing = async () => null;

test('expectedCname shape', () => {
  const { name, want } = expectedCname('aaa', 'example.com');
  assert.equal(name, 'aaa._domainkey.example.com');
  assert.equal(want, 'aaa.dkim.amazonses.com');
});

test('all records present is clean', async () => {
  assert.deepEqual(await checkIdentity('example.com', DKIM_OK, allGood), []);
});

test('missing records are reported with the fix', async () => {
  const problems = await checkIdentity('example.com', DKIM_OK, nothing);
  assert.equal(problems.length, 3);
  assert.ok(problems.every((p) => p.includes('republish CNAME')));
});

test('no tokens short-circuits', async () => {
  const problems = await checkIdentity('example.com', { Status: 'SUCCESS', Tokens: [] }, allGood);
  assert.ok(problems.some((p) => p.includes('not configured')));
});
''',
"faq": [
 ("How can an identity be verified but not signing?",
  "SES tracks verification and DKIM separately. Verification can be satisfied by a TXT record while DKIM depends on three CNAMEs. Remove the CNAMEs and the domain still reads verified, but messages go out without a valid signature."),
 ("What actually breaks when DKIM stops?",
  "DMARC falls back to the SPF leg. If you have not configured a custom MAIL FROM, SPF authenticates an amazonses.com subdomain and does not align, so DMARC fails outright and mail starts landing in spam."),
 ("Do the DKIM tokens change if I republish them?",
  "No. The tokens belong to the identity, so republishing the same three CNAMEs restores signing. They only change if the identity is deleted and recreated, in which case every record must be replaced."),
 ("Why does this usually happen after a DNS migration?",
  "Easy DKIM records look like machine noise — three long random names pointing at dkim.amazonses.com. In a zone export or a manual rebuild at a new registrar they are the records most likely to be dropped as junk."),
 ("How often should I run this check?",
  "Weekly is enough. It is a drift problem, so the value is in catching the next migration rather than in any single run."),
],
"related": [
 ("/email/ses-mail-from-not-set/", "SES passes SPF and DKIM but DMARC still fails"),
 ("/dns/dkim-selector-missing/", "DKIM selector record missing from the zone"),
 ("/dns/dkim-key-stale-after-rotation/", "DKIM key stale after a rotation"),
],
"citations": [
 ("Easy DKIM in Amazon SES — AWS docs",
  "https://docs.aws.amazon.com/ses/latest/dg/send-email-authentication-dkim-easy.html"),
 ("Domain and email address verification problems — AWS docs",
  "https://docs.aws.amazon.com/ses/latest/dg/troubleshoot-verification.html"),
 ("boto3 sesv2 get_email_identity",
  "https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sesv2/client/get_email_identity.html"),
],
},

]
