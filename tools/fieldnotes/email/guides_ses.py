#!/usr/bin/env python3
"""Content for the six Amazon SES field notes.

Every one is a problem you can DETECT and REPAIR with a script against the SES v2
API, which is the test for belonging in this section. Anything that can only be
fixed by opening a support ticket (a sending quota increase, a dedicated IP) is
covered only to the point where the script tells you that is what you need.
"""

GUIDES = [

# ─────────────────────────────────────────────────────────────────────────────
{
"slug": "ses-suppression-list-blocks-a-real-customer",
"title": "SES Suppression List Silently Blocks a Real Customer",
"description": "The customer never got the email and SES reported no error. Their address sits on the account-level suppression list from an old bounce, so the send is dropped.",
"h1": "SES suppression list silently blocks a real customer",
"category": "Amazon SES",
"pill": "Diagnostic",
"chips": ["Amazon SES v2 API", "Python and Node.js", "Fixable through the API"],
"keywords": ["Amazon SES suppression list", "SES account-level suppression",
             "ListSuppressedDestinations", "DeleteSuppressedDestination", "SES bounce"],
"deps": "Python 3.9+ with boto3, or Node.js 18+ with @aws-sdk/client-sesv2",
"lead": "The customer swears the password reset never arrived. Your logs show the send succeeded. SES returned a message ID and no error. Nothing is in the spam folder, and the address is spelled correctly. What actually happened is that SES accepted the call, matched the address against your account-level suppression list, and dropped the message before it ever left AWS &mdash; because six months ago that address hard bounced once, while the mailbox was full.",
"short_answer": """<p>SES keeps an <strong>account-level suppression list</strong>. By default it adds every address that hard bounces or files a complaint, and it then silently drops future sends to that address. The API call still succeeds and still returns a message ID, so nothing in your application logs looks wrong.</p>
<p>Check with <code>GetSuppressedDestination</code>, and remove with <code>DeleteSuppressedDestination</code>. But removing an address that genuinely bounces will put it straight back <em>and</em> charge the bounce against your reputation, so the script below reports first and only deletes what you tell it to.</p>""",
"problem": """<p>You send a transactional email through SES. The SDK returns a <code>MessageId</code>. Your application records a success. The recipient never receives anything, and no bounce or complaint event arrives either, because nothing was ever delivered to bounce.</p>
<p>This is by design and it is easy to miss: suppression happens <em>after</em> SES accepts the request. From the caller's point of view the send worked. The only place the truth exists is the suppression list itself and, if you have wired it up, a <code>Rendering Failure</code>-adjacent event stream that most teams never configure.</p>
<p>It bites hardest on transactional mail &mdash; password resets, receipts, invitations &mdash; where a single undelivered message is a support ticket rather than a rounding error in a campaign.</p>""",
"why": """<p>Three things combine.</p>
<p><strong>The default is aggressive.</strong> A new SES account has account-level suppression enabled for both <code>BOUNCE</code> and <code>COMPLAINT</code>. One hard bounce is enough. A full mailbox, a temporarily misconfigured MX, a typo the user later corrected &mdash; any of these can produce a hard bounce that suppresses the address permanently.</p>
<p><strong>Suppression is account-wide, not per identity.</strong> An address suppressed by a marketing blast is also suppressed for your password reset. The two have nothing to do with each other operationally, but they share one list.</p>
<p><strong>The failure is invisible by default.</strong> Unless the sending call goes through a configuration set with an event destination, there is no signal anywhere that the message was suppressed. Guide five in this section covers wiring that up, and it is the single change that makes this class of problem visible instead of mysterious.</p>""",
"steps": [
 {"h": "Check the one address first",
  "body": """<p>Before touching anything, confirm the diagnosis for the address the customer reported. <code>GetSuppressedDestination</code> returns the reason and the date, which tells you whether this was a bounce or a complaint &mdash; and those two want very different responses.</p>
<pre><code class="language-bash">aws sesv2 get-suppressed-destination --email-address customer@example.com</code></pre>
<p>A <code>NotFoundException</code> means the address is not suppressed and your problem is somewhere else. A result with <code>&quot;Reason&quot;: &quot;COMPLAINT&quot;</code> means they marked you as spam: do not remove it, and do not mail them again.</p>"""},
 {"h": "Decide bounce by bounce, never in bulk",
  "body": """<p>A <code>BOUNCE</code> reason is worth investigating; a <code>COMPLAINT</code> reason almost never is. The distinction matters because removing an address that still bounces re-suppresses it and the bounce counts against the account bounce rate that AWS uses to decide whether to keep sending your mail at all.</p>
<p>The script below defaults to reporting. You pass explicit addresses to remove.</p>"""},
 {"h": "Verify the mailbox exists before you remove",
  "body": """<p>If the original bounce was a full mailbox or a dead domain, the address will bounce again the moment you retry. Confirm the domain still has a working MX and, where you can, that the user has actually corrected the address, before removing the entry.</p>"""},
 {"h": "Reconsider the account-wide default",
  "body": """<p>If your account sends both marketing and transactional mail, account-level suppression is a blunt instrument. <code>PutAccountSuppressionAttributes</code> lets you narrow it to <code>COMPLAINT</code> only, and you then handle bounces yourself per list. That is a real decision with real risk &mdash; you become responsible for not re-mailing dead addresses &mdash; so the script only reports the current setting rather than changing it.</p>"""},
],
"verify": """<p>Re-run the check for the address. It should return <code>NotFoundException</code>. Then send one real message to it and watch for the delivery event rather than trusting the <code>MessageId</code>:</p>
<pre><code class="language-bash"># should now raise NotFoundException
aws sesv2 get-suppressed-destination --email-address customer@example.com

# and the send should produce a Delivery event, not silence
aws sesv2 send-email --from-email-address you@yourdomain.com \\
  --destination ToAddresses=customer@example.com \\
  --content 'Simple={Subject={Data=test},Body={Text={Data=test}}}'</code></pre>
<p>If it bounces again, the address is genuinely bad. Leave it suppressed.</p>""",
"code_intro": "The script lists the suppression list with paging, groups by reason so complaints and bounces are never confused, and removes only addresses you name explicitly. It stays in dry run until you pass <code>--apply</code>, and it refuses outright to remove an address suppressed for a complaint.",
"py_file": "ses_suppression_audit.py",
"py": '''"""Audit the SES account-level suppression list and remove named addresses.

Reports by default. Removal requires --apply AND an explicit address, because
deleting an entry that still bounces re-suppresses it and the bounce counts
against the account reputation.
"""
import argparse
import logging
import sys

import boto3
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ses_suppression_audit")

COMPLAINT = "COMPLAINT"


def list_suppressed(client, reasons=None):
    """Yield every suppressed destination, following pagination."""
    kwargs = {"PageSize": 1000}
    if reasons:
        kwargs["Reasons"] = reasons
    token = None
    while True:
        if token:
            kwargs["NextToken"] = token
        page = client.list_suppressed_destinations(**kwargs)
        for item in page.get("SuppressedDestinationSummaries", []):
            yield item
        token = page.get("NextToken")
        if not token:
            return


def describe(client, address):
    """Return the suppression record for one address, or None."""
    try:
        return client.get_suppressed_destination(
            EmailAddress=address)["SuppressedDestination"]
    except ClientError as exc:
        if exc.response["Error"]["Code"] == "NotFoundException":
            return None
        raise


def should_remove(record):
    """Pure decision function. No API calls, so it is trivial to test.

    A complaint means the recipient pressed 'this is spam'. Removing that entry
    and mailing them again is how an account gets shut down, so it is never
    eligible no matter what the operator passed on the command line.
    """
    if record is None:
        return False, "not suppressed"
    if record.get("Reason") == COMPLAINT:
        return False, "suppressed for a complaint; do not re-mail"
    return True, "suppressed for a bounce; safe to remove if the mailbox is fixed"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", default="us-east-1")
    ap.add_argument("--remove", nargs="*", default=[],
                    help="addresses to remove; each is checked individually")
    ap.add_argument("--apply", action="store_true", help="actually delete")
    args = ap.parse_args()

    ses = boto3.client("sesv2", region_name=args.region)

    account = ses.get_account()
    supp = account.get("SuppressionAttributes", {}).get("SuppressedReasons", [])
    log.info("account-level suppression is on for: %s", supp or "nothing")

    counts = {}
    for item in list_suppressed(ses):
        counts[item["Reason"]] = counts.get(item["Reason"], 0) + 1
    log.info("suppression list holds %s", counts or "no addresses")

    exit_code = 0
    for address in args.remove:
        record = describe(ses, address)
        ok, reason = should_remove(record)
        if not ok:
            log.warning("SKIP %s -- %s", address, reason)
            exit_code = 1
            continue
        log.info("%s %s -- %s (suppressed %s)",
                 "REMOVING" if args.apply else "WOULD REMOVE",
                 address, reason, record.get("LastUpdateTime"))
        if args.apply:
            ses.delete_suppressed_destination(EmailAddress=address)

    if not args.apply and args.remove:
        log.info("dry run -- pass --apply to actually delete")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "ses-suppression-audit.mjs",
"js": '''/**
 * Audit the SES account-level suppression list and remove named addresses.
 *
 * Reports by default. Removal requires --apply AND an explicit address, because
 * deleting an entry that still bounces re-suppresses it and the bounce counts
 * against the account reputation.
 */
import {
  SESv2Client,
  GetAccountCommand,
  ListSuppressedDestinationsCommand,
  GetSuppressedDestinationCommand,
  DeleteSuppressedDestinationCommand,
} from '@aws-sdk/client-sesv2';

const COMPLAINT = 'COMPLAINT';

async function* listSuppressed(client) {
  let NextToken;
  do {
    const page = await client.send(
      new ListSuppressedDestinationsCommand({ PageSize: 1000, NextToken }),
    );
    yield* page.SuppressedDestinationSummaries ?? [];
    NextToken = page.NextToken;
  } while (NextToken);
}

async function describe(client, address) {
  try {
    const out = await client.send(
      new GetSuppressedDestinationCommand({ EmailAddress: address }),
    );
    return out.SuppressedDestination;
  } catch (err) {
    if (err.name === 'NotFoundException') return null;
    throw err;
  }
}

/**
 * Pure decision function. No API calls, so it is trivial to test.
 *
 * A complaint means the recipient pressed 'this is spam'. Removing that entry
 * and mailing them again is how an account gets shut down, so it is never
 * eligible no matter what the operator passed on the command line.
 */
export function shouldRemove(record) {
  if (!record) return { ok: false, reason: 'not suppressed' };
  if (record.Reason === COMPLAINT) {
    return { ok: false, reason: 'suppressed for a complaint; do not re-mail' };
  }
  return { ok: true, reason: 'suppressed for a bounce; safe to remove if the mailbox is fixed' };
}

async function main() {
  const args = process.argv.slice(2);
  const apply = args.includes('--apply');
  const removeAt = args.indexOf('--remove');
  const remove = removeAt === -1 ? [] : args.slice(removeAt + 1).filter((a) => !a.startsWith('--'));
  const client = new SESv2Client({ region: process.env.AWS_REGION ?? 'us-east-1' });

  const account = await client.send(new GetAccountCommand({}));
  console.log('account-level suppression is on for:',
    account.SuppressionAttributes?.SuppressedReasons ?? 'nothing');

  const counts = {};
  for await (const item of listSuppressed(client)) {
    counts[item.Reason] = (counts[item.Reason] ?? 0) + 1;
  }
  console.log('suppression list holds', Object.keys(counts).length ? counts : 'no addresses');

  let exitCode = 0;
  for (const address of remove) {
    const record = await describe(client, address);
    const { ok, reason } = shouldRemove(record);
    if (!ok) {
      console.warn(`SKIP ${address} -- ${reason}`);
      exitCode = 1;
      continue;
    }
    console.log(`${apply ? 'REMOVING' : 'WOULD REMOVE'} ${address} -- ${reason}`);
    if (apply) {
      await client.send(new DeleteSuppressedDestinationCommand({ EmailAddress: address }));
    }
  }
  if (!apply && remove.length) console.log('dry run -- pass --apply to actually delete');
  process.exit(exitCode);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The decision is separated from the API on purpose, so the rule that protects you &mdash; never remove a complaint &mdash; can be tested without an AWS account or a mock.",
"test_py_file": "test_ses_suppression_audit.py",
"test_py": '''import pytest
from ses_suppression_audit import should_remove


def test_missing_address_is_not_removable():
    ok, reason = should_remove(None)
    assert ok is False
    assert "not suppressed" in reason


def test_complaint_is_never_removable():
    ok, reason = should_remove({"Reason": "COMPLAINT"})
    assert ok is False, "removing a complaint and re-mailing is how accounts get shut down"


def test_bounce_is_removable():
    ok, _ = should_remove({"Reason": "BOUNCE"})
    assert ok is True


@pytest.mark.parametrize("reason", ["COMPLAINT", "complaint".upper()])
def test_complaint_case_is_exact(reason):
    """SES returns the reason uppercase; this guards the comparison."""
    ok, _ = should_remove({"Reason": reason})
    assert ok is False
''',
"test_js_file": "ses-suppression-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { shouldRemove } from './ses-suppression-audit.mjs';

test('a missing address is not removable', () => {
  const { ok, reason } = shouldRemove(null);
  assert.equal(ok, false);
  assert.match(reason, /not suppressed/);
});

test('a complaint is never removable', () => {
  const { ok } = shouldRemove({ Reason: 'COMPLAINT' });
  assert.equal(ok, false, 'removing a complaint and re-mailing is how accounts get shut down');
});

test('a bounce is removable', () => {
  const { ok } = shouldRemove({ Reason: 'BOUNCE' });
  assert.equal(ok, true);
});
''',
"faq": [
 ("Why did the send succeed if the message was never delivered?",
  "SES applies the suppression list after it accepts the request. The API returns a MessageId and no error, so the caller sees success. The message is dropped inside SES and never reaches the recipient's mail server, which is also why no bounce arrives — there was no delivery attempt to bounce."),
 ("Is the account-level suppression list the same as the global suppression list?",
  "No. The global list is managed by AWS across all customers and you cannot edit it. The account-level list is yours, and it is the one you can read and delete from with the SES v2 API. An address can be on the global list and not yours; if you send to it, SES will attempt delivery, and a resulting bounce still counts against your bounce rate."),
 ("Should I just remove everything on the list?",
  "No. Every address on it bounced or complained at least once. Removing them all and re-sending recreates the bounces, drives your bounce rate up, and risks the account being put under review. Remove individual addresses you have a specific reason to believe are now valid."),
 ("Can I stop SES suppressing bounces automatically?",
  "Yes, with PutAccountSuppressionAttributes you can narrow suppression to complaints only. That makes you responsible for not re-mailing dead addresses yourself, which is a real operational burden — do it only if you already maintain your own bounce handling."),
 ("How do I find out this is happening without a customer complaint?",
  "Attach a configuration set with an event destination to your sends. That publishes delivery, bounce, complaint and rejection events to SNS, CloudWatch or Kinesis Firehose, which turns an invisible drop into a log line. It is the subject of a separate note in this section."),
],
"related": [
 ("/email/ses-bounce-rate-approaching-review/", "SES bounce rate creeping toward account review"),
 ("/email/ses-no-event-destination/", "SES bounces and complaints are invisible with no event destination"),
 ("/dns/mx-points-to-dead-host/", "MX record points at a host that no longer accepts mail"),
],
"citations": [
 ("Using the Amazon SES account-level suppression list — AWS docs",
  "https://docs.aws.amazon.com/ses/latest/dg/sending-email-suppression-list.html"),
 ("Amazon SES global suppression list — AWS docs",
  "https://docs.aws.amazon.com/ses/latest/dg/sending-email-global-suppression-list.html"),
 ("boto3 sesv2 list_suppressed_destinations",
  "https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sesv2/client/list_suppressed_destinations.html"),
 ("boto3 sesv2 put_account_suppression_attributes",
  "https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sesv2/client/put_account_suppression_attributes.html"),
],
},
# ─────────────────────────────────────────────────────────────────────────────
{
"slug": "ses-still-in-sandbox",
"title": "SES Silently Rejects Real Recipients: Still in the Sandbox",
"description": "Mail to your own address works, mail to customers fails with MessageRejected. The account never left the SES sandbox, which only allows verified recipients.",
"h1": "SES silently rejects real recipients because the account is still in the sandbox",
"category": "Amazon SES",
"pill": "Diagnostic",
"chips": ["Amazon SES v2 API", "Python and Node.js", "Detect through the API"],
"keywords": ["SES sandbox", "MessageRejected", "Email address is not verified",
             "SES production access", "GetAccount ProductionAccessEnabled"],
"deps": "Python 3.9+ with boto3, or Node.js 18+ with @aws-sdk/client-sesv2",
"lead": "Every test you ran worked. You sent to yourself, to a colleague, to a second address you own, and all of them arrived. Then the first real customer signed up and the send threw <code>MessageRejected: Email address is not verified</code>. Nothing changed in your code. The account is still in the SES sandbox, and the sandbox only lets you mail addresses you have already proved you control &mdash; which is exactly every address you tested with.",
"short_answer": """<p>A new SES account starts in the <strong>sandbox</strong>: 200 messages per 24 hours, one message per second, and recipients must be verified identities. Because you naturally test with addresses you own, and owning them is what verification proves, the restriction stays invisible until a stranger signs up.</p>
<p><code>GetAccount</code> returns <code>ProductionAccessEnabled</code>. Check it in your deploy pipeline rather than discovering it from a customer. Leaving the sandbox is a support request, not an API call, so the script detects and reports &mdash; it cannot fix this one for you.</p>""",
"problem": """<p>The error text is <code>MessageRejected</code> with a message like <code>Email address is not verified. The following identities failed the check in region US-EAST-1</code>. It names the recipient, which reads like the recipient is at fault. They are not. In the sandbox SES requires <em>both</em> ends of the send to be verified, and your customer obviously has not verified anything with your AWS account.</p>
<p>The trap is that the failure is invisible in testing. You verify your own domain, you send to yourself, everything passes. The restriction only appears the first time you mail somebody who is not you &mdash; usually in production, usually to a real user, usually on a signup or password reset.</p>""",
"why": """<p><strong>The sandbox is the default, and it is quiet about it.</strong> AWS puts every new SES account there to stop the service being used to send spam from a fresh account. Nothing in the send path warns you; the console shows a banner you stop noticing after a week.</p>
<p><strong>Verification proves control, and you control your test addresses.</strong> The sandbox rule is that recipients must be verified. Every address a developer naturally reaches for &mdash; their own, the team's, a second domain they own &mdash; is one they can verify. The test set and the restricted set are the same set, so the tests cannot catch it.</p>
<p><strong>Region is part of the answer.</strong> Sandbox status is per region. An account with production access in <code>us-east-1</code> can still be sandboxed in <code>eu-west-1</code>, and a deploy that changes region reintroduces the problem in a place nobody thinks to look.</p>""",
"steps": [
 {"h": "Ask the API rather than the console",
  "body": """<p><code>GetAccount</code> answers definitively for the region you call it in.</p>
<pre><code class="language-bash">aws sesv2 get-account --region us-east-1 \\
  --query '{Production:ProductionAccessEnabled,Max24Hour:SendQuota.Max24HourSend,Rate:SendQuota.MaxSendRate,Enforcement:EnforcementStatus}'</code></pre>
<p><code>Production: false</code> with <code>Max24Hour: 200</code> is the sandbox signature.</p>"""},
 {"h": "Check every region you actually send from",
  "body": """<p>Production access is granted per region. If your staging stack runs in one region and production in another, or you added a region for latency, each one needs its own request. The script below sweeps a list of regions so a missed one shows up before a customer finds it.</p>"""},
 {"h": "Request production access",
  "body": """<p>This part is not scriptable. Open the SES console for the region, choose <em>Request production access</em>, and describe how you send, how people opt in, and how you handle bounces and complaints. Requests that describe a real bounce-handling process are approved faster than ones that do not.</p>"""},
 {"h": "Make the check part of deployment",
  "body": """<p>Run the detector in CI against the region you are deploying to and fail the build if production access is off. That converts a customer-facing incident into a red pipeline, which is where you want to find out.</p>"""},
],
"verify": """<p>After approval, the same call flips over:</p>
<pre><code class="language-bash">aws sesv2 get-account --region us-east-1 --query 'ProductionAccessEnabled'
# true

# and the quota is no longer the sandbox 200
aws sesv2 get-account --region us-east-1 --query 'SendQuota'</code></pre>
<p>Send one real message to an address you have never verified. If it arrives, you are out.</p>""",
"code_intro": "The script checks one or more regions and exits non-zero if any of them is still sandboxed, so it can sit in a deploy pipeline. It reports the quota and the enforcement status alongside, because an account can have production access and still be paused.",
"py_file": "ses_sandbox_check.py",
"py": '''"""Fail if any SES region is still in the sandbox.

Written to run in CI: exits non-zero when a region cannot mail arbitrary
recipients, so a deploy stops before a customer finds out for you.
"""
import argparse
import logging
import sys

import boto3

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ses_sandbox_check")

SANDBOX_DAILY_QUOTA = 200.0


def assess(account):
    """Pure decision function over a GetAccount response.

    Production access and enforcement are separate: an account can be out of the
    sandbox and still be SHUTDOWN or UNDER_REVIEW, which fails sends just as hard.
    """
    production = bool(account.get("ProductionAccessEnabled"))
    enforcement = (account.get("EnforcementStatus") or "HEALTHY").upper()
    quota = float(account.get("SendQuota", {}).get("Max24HourSend") or 0)

    problems = []
    if not production:
        problems.append("still in the sandbox: recipients must be verified identities")
    if enforcement != "HEALTHY":
        problems.append(f"enforcement status is {enforcement}")
    if production and quota <= SANDBOX_DAILY_QUOTA:
        problems.append(f"production access is on but the quota is only {quota:.0f}/24h")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regions", nargs="+", default=["us-east-1"])
    args = ap.parse_args()

    failed = False
    for region in args.regions:
        account = boto3.client("sesv2", region_name=region).get_account()
        problems = assess(account)
        quota = account.get("SendQuota", {})
        if problems:
            failed = True
            for p in problems:
                log.error("%s: %s", region, p)
        else:
            log.info("%s: production access, %.0f/24h at %.0f/sec",
                     region, quota.get("Max24HourSend", 0), quota.get("MaxSendRate", 0))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "ses-sandbox-check.mjs",
"js": '''/**
 * Fail if any SES region is still in the sandbox.
 *
 * Written to run in CI: exits non-zero when a region cannot mail arbitrary
 * recipients, so a deploy stops before a customer finds out for you.
 */
import { SESv2Client, GetAccountCommand } from '@aws-sdk/client-sesv2';

const SANDBOX_DAILY_QUOTA = 200;

/**
 * Pure decision function over a GetAccount response.
 *
 * Production access and enforcement are separate: an account can be out of the
 * sandbox and still be SHUTDOWN or UNDER_REVIEW, which fails sends just as hard.
 */
export function assess(account) {
  const production = Boolean(account.ProductionAccessEnabled);
  const enforcement = (account.EnforcementStatus ?? 'HEALTHY').toUpperCase();
  const quota = Number(account.SendQuota?.Max24HourSend ?? 0);

  const problems = [];
  if (!production) problems.push('still in the sandbox: recipients must be verified identities');
  if (enforcement !== 'HEALTHY') problems.push(`enforcement status is ${enforcement}`);
  if (production && quota <= SANDBOX_DAILY_QUOTA) {
    problems.push(`production access is on but the quota is only ${quota}/24h`);
  }
  return problems;
}

async function main() {
  const regions = process.argv.slice(2).filter((a) => !a.startsWith('--'));
  const targets = regions.length ? regions : ['us-east-1'];

  let failed = false;
  for (const region of targets) {
    const account = await new SESv2Client({ region }).send(new GetAccountCommand({}));
    const problems = assess(account);
    if (problems.length) {
      failed = true;
      for (const p of problems) console.error(`${region}: ${p}`);
    } else {
      console.log(`${region}: production access, ${account.SendQuota?.Max24HourSend}/24h`);
    }
  }
  process.exit(failed ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The rule is worth testing because two of its three cases are easy to forget: an account can be out of the sandbox and still blocked, and production access with a 200/day quota means the increase never actually applied.",
"test_py_file": "test_ses_sandbox_check.py",
"test_py": '''from ses_sandbox_check import assess


def healthy():
    return {"ProductionAccessEnabled": True, "EnforcementStatus": "HEALTHY",
            "SendQuota": {"Max24HourSend": 50000.0, "MaxSendRate": 14.0}}


def test_healthy_account_has_no_problems():
    assert assess(healthy()) == []


def test_sandbox_is_reported():
    acct = healthy() | {"ProductionAccessEnabled": False}
    assert any("sandbox" in p for p in assess(acct))


def test_enforcement_is_separate_from_sandbox():
    """Out of the sandbox but SHUTDOWN still cannot send."""
    acct = healthy() | {"EnforcementStatus": "SHUTDOWN"}
    assert any("SHUTDOWN" in p for p in assess(acct))


def test_production_access_with_sandbox_quota_is_suspicious():
    acct = healthy() | {"SendQuota": {"Max24HourSend": 200.0, "MaxSendRate": 1.0}}
    assert any("quota" in p for p in assess(acct))


def test_missing_enforcement_defaults_to_healthy():
    acct = healthy()
    del acct["EnforcementStatus"]
    assert assess(acct) == []
''',
"test_js_file": "ses-sandbox-check.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { assess } from './ses-sandbox-check.mjs';

const healthy = () => ({
  ProductionAccessEnabled: true,
  EnforcementStatus: 'HEALTHY',
  SendQuota: { Max24HourSend: 50000, MaxSendRate: 14 },
});

test('a healthy account has no problems', () => {
  assert.deepEqual(assess(healthy()), []);
});

test('the sandbox is reported', () => {
  const problems = assess({ ...healthy(), ProductionAccessEnabled: false });
  assert.ok(problems.some((p) => p.includes('sandbox')));
});

test('enforcement is separate from the sandbox', () => {
  const problems = assess({ ...healthy(), EnforcementStatus: 'SHUTDOWN' });
  assert.ok(problems.some((p) => p.includes('SHUTDOWN')));
});

test('production access with a sandbox quota is suspicious', () => {
  const problems = assess({ ...healthy(), SendQuota: { Max24HourSend: 200, MaxSendRate: 1 } });
  assert.ok(problems.some((p) => p.includes('quota')));
});
''',
"faq": [
 ("Why did my tests pass if the account was sandboxed?",
  "Because the sandbox restricts recipients to verified identities, and every address a developer naturally tests with is one they own and can verify. The test set and the restricted set are the same set, so the restriction is invisible until a stranger receives mail."),
 ("Is the sandbox per account or per region?",
  "Per region. Production access in us-east-1 says nothing about eu-west-1. Adding a region, or a staging stack that runs somewhere else, reintroduces the sandbox in a place nobody thinks to check."),
 ("Can a script take the account out of the sandbox?",
  "No. Production access is a support request reviewed by AWS. A script can only detect the state and fail your pipeline, which is still worth doing because it moves the discovery from a customer to a build."),
 ("The account has production access but sends still fail. Why?",
  "Check EnforcementStatus. An account can be out of the sandbox and still be UNDER_REVIEW or SHUTDOWN because of bounce or complaint rates, which fails sends for a completely different reason. The detector reports both."),
 ("How many can I send in the sandbox?",
  "200 messages per 24 hours at one message per second, to verified identities only. If your quota still reads 200 after production access is granted, the increase did not apply and it is worth raising."),
],
"related": [
 ("/email/ses-bounce-rate-approaching-review/", "SES bounce rate creeping toward account review"),
 ("/email/ses-suppression-list-blocks-a-real-customer/", "SES suppression list silently blocks a real customer"),
 ("/email/ses-no-event-destination/", "SES bounces and complaints are invisible with no event destination"),
],
"citations": [
 ("Moving out of the Amazon SES sandbox — AWS docs",
  "https://docs.aws.amazon.com/ses/latest/dg/request-production-access.html"),
 ("Troubleshooting Amazon SES issues — AWS docs",
  "https://docs.aws.amazon.com/ses/latest/dg/troubleshoot.html"),
 ("boto3 sesv2 get_account",
  "https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sesv2/client/get_account.html"),
],
},

]
