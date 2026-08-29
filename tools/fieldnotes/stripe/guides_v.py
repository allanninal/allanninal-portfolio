#!/usr/bin/env python3
"""/stripe/ field notes — batch V: Connect verification and settlement.

Four problems that all live on the Account object and none of which the Account
object shows you directly. The requirement is on a Person, or in a hash that does
not affect anything yet, or on a capability you never use, or in a currency that
has no bank account behind it.

Read only, like the rest of the section: the scripts hold a credential to a live
payments account, so they report and print the repair rather than running it.
"""

CITE_PERSON_OBJ = ("The Person object — Stripe API reference",
                   "https://docs.stripe.com/api/persons/object")
CITE_API_VERIFICATION = ("Handling verification with the API — Stripe Docs",
                         "https://docs.stripe.com/connect/handling-api-verification")
CITE_ACCOUNT_OBJ = ("The Account object — Stripe API reference",
                    "https://docs.stripe.com/api/accounts/object")
CITE_VERIFICATION_UPDATES = ("Handle verification updates — Stripe Docs",
                             "https://docs.stripe.com/connect/handle-verification-updates")
CITE_CAPABILITIES = ("Account capabilities — Stripe Docs",
                     "https://docs.stripe.com/connect/account-capabilities")
CITE_CAPABILITY_OBJ = ("The Capability object — Stripe API reference",
                       "https://docs.stripe.com/api/capabilities/object")
CITE_COUNTRY_SPEC = ("The Country Spec object — Stripe API reference",
                     "https://docs.stripe.com/api/country_specs/object")
CITE_CROSS_BORDER = ("Cross-border payouts — Stripe Docs",
                     "https://docs.stripe.com/connect/cross-border-payouts")
CITE_EXTERNAL_ACCOUNT = ("The external bank account object — Stripe API reference",
                         "https://docs.stripe.com/api/external_account_bank_accounts/object")

GUIDES = [

{
"slug": "person-requirements-outstanding",
"title": "A Person's currently_due blocks the whole account",
"description": "Every field on the account object is filled in and charges_enabled is still false. The missing paperwork belongs to a director, on an object you never read.",
"h1": "a Person's currently_due blocks the whole account",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe person requirements currently_due", "stripe connect person verification",
             "person_ verification.document", "stripe company account kyc",
             "stripe persons api requirements"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The seller filled in everything your onboarding form asked for. The account object shows a business name, an address, a tax id and a bank account, and <code>charges_enabled</code> is still <code>false</code>. The one thing in <code>requirements.currently_due</code> is a string that starts <code>person_1Mq</code> and ends <code>.verification.document</code>, and there is no field anywhere in your product that corresponds to it.",
"short_answer": """<p>For a company account the KYC data does not live on the Account. It lives on <strong>Person</strong> objects &mdash; the representative, the owners, the directors, the executives &mdash; and each one carries its own <code>requirements</code> hash. Read them with <code>GET /v1/accounts/{id}/persons?limit=100</code> and flag any where <code>requirements.currently_due</code> or <code>requirements.past_due</code> is non-empty, or <code>verification.status</code> is not <code>verified</code>.</p>
<p>The account-level entry is a pointer, not a field. <code>person_1MqEZ.verification.document</code> means <em>that person</em> owes <em>that field</em>. Split it on the first dot and you have the id to fetch and the thing to ask for; without that step the requirement is unactionable and stays outstanding indefinitely.</p>""",
"problem": """<p>What makes this one stick around is that nothing about it looks like a bug. The onboarding form works. The account was created, the details were submitted, the bank account attached. Support looks at the account object, sees every field populated, and concludes Stripe is being slow. Stripe is not being slow: it is waiting on a passport scan from a director whose record your application has never once fetched.</p>
<p>It is also the failure mode that survives a rewrite of the onboarding flow. Teams add fields to the company form, then more fields, then a document upload for the business, and none of it touches the sub-objects where the blocking requirement actually is. The account stays stuck through three rounds of improvements to a form that was never the problem.</p>""",
"why": """<p><strong>The requirement names an object you did not know you had.</strong> Stripe creates Person records for the representative and for anyone with significant ownership or control. They are separate resources with separate ids, and an integration that only ever calls <code>POST /v1/accounts</code> creates them implicitly and never looks at them again.</p>
<p><strong>The account-level string is deliberately opaque.</strong> <code>person_1MqEZ2eZvKYlo2C.verification.document</code> is not a field name, it is a path. Code that renders <code>currently_due</code> straight into a checklist prints that string to the seller, who has no idea what it means either. The dot is the whole trick: everything left of it is a resource to fetch.</p>
<p><strong>One person's paperwork disables the account, not just themselves.</strong> Capabilities are granted at the account level and verified against the union of what is outstanding. A single director missing a date of birth stops charges for the entire business, which is why the account boolean and the person record disagree so completely.</p>
<p><strong>Verification status is a third signal that neither array carries.</strong> A person can have an empty <code>currently_due</code> and a <code>verification.status</code> of <code>pending</code>, which means Stripe is reviewing something already submitted. Treating that as a missing field sends the seller a link to a form with nothing on it, and they reasonably conclude your product is broken.</p>""",
"steps": [
 {"h": "Resolve every person_ entry on the account first",
  "body": """<p>Take <code>requirements.currently_due</code> and <code>requirements.past_due</code> from the account, keep the entries beginning <code>person_</code>, and split each on the first dot. That gives you the exact list of humans the account is blocked on before you fetch anything, and it tells you which persons matter when an account has nine of them.</p>"""},
 {"h": "List the persons and read each requirements hash",
  "body": """<p><code>GET /v1/accounts/{id}/persons?limit=100</code>. Every object has its own <code>requirements.currently_due</code>, <code>requirements.past_due</code> and <code>requirements.eventually_due</code>. The account-level arrays flatten these together, so the per-person view is the only place you can say who owes what.</p>"""},
 {"h": "Separate under review from waiting on you",
  "body": """<p><code>verification.status</code> of <code>pending</code> means submitted and being checked. There is nothing to collect and no email to send. Lumping it in with <code>currently_due</code> produces a support queue full of people who have already done what you asked.</p>"""},
 {"h": "Name the human in whatever you show a support agent",
  "body": """<p><code>relationship</code> says whether this is the representative, an owner, a director or an executive, and the name fields say who they are. "The director Priya Raman owes a photo id" is a message someone can act on; a person id is a lookup task that gets deferred.</p>"""},
 {"h": "Check the persons for errors too, not only the account",
  "body": """<p>A rejected document produces an entry in <code>requirements.errors</code> on the <em>person</em>, and the account-level array can be empty while that one is not. The codes and what each of them actually asks for are covered in <a href="/stripe/verification-errors-unread/">requirements.errors explains the rejected document</a>.</p>"""},
],
"verify": """<p>Re-run the script. No person should report <code>past-due</code> or <code>blocking</code>, and the account's own requirements should no longer contain any <code>person_</code> entries.</p>
<pre><code class="language-bash">python3 stripe_person_requirements.py
# 412 account(s), 730 person(s), 0 needing attention</code></pre>""",
"code_intro": "One paginated GET over the accounts and one small GET per account for its persons, both read-only. Two pure functions carry the logic: one splits an account-level requirement string into the person id it points at, and one classifies a person. Keeping the split separate matters because it is the step everyone misses, and it is a one-line rule that is easy to get subtly wrong on entries that are not person references at all.",
"py_file": "stripe_person_requirements.py",
"py": '''"""Report the Persons whose outstanding requirements are blocking an account.

Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
access to Connected accounts. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_person_requirements")

API = "https://api.stripe.com/v1"


def person_ref(entry):
    """Return the Person id an account-level requirement points at, or None.

    Account requirements read like person_1MqEZ.verification.document: the id is
    everything left of the first dot, the rest is the field on that Person. Pure,
    so the parsing is testable without a network. Entries that are ordinary
    account fields come back as None rather than as a bogus id.
    """
    if not isinstance(entry, str) or not entry.startswith("person_"):
        return None
    return entry.split(".", 1)[0]


def verdict(person):
    """Classify one Person object. Pure, so the rules are visible and testable.

    Returns (state, detail). Ordered by what each state costs: a past_due field
    has already disabled something, a currently_due field has not yet, and a
    person Stripe is still reviewing needs nothing collected at all.
    """
    req = person.get("requirements") or {}
    past = req.get("past_due") or []
    due = req.get("currently_due") or []
    status = (person.get("verification") or {}).get("status")

    if past:
        return ("past-due",
                "%d field(s) past due (%s); capabilities that depend on this "
                "person are already off" % (len(past), ", ".join(past)))
    if due:
        return ("blocking",
                "%d field(s) currently due (%s)" % (len(due), ", ".join(due)))
    if status == "pending":
        return ("verifying",
                "submitted and under review; nothing to collect, and a link sent "
                "now opens a form with no fields on it")
    if status == "unverified":
        return ("unverified",
                "not verified and nothing due yet; Stripe asks at a threshold, so "
                "this is the cheap moment to collect it")
    if status == "verified":
        return ("clear", "verified, nothing outstanding")
    return ("unknown", "unrecognised verification status %r" % (status,))


def blocked_on(account):
    """The Person ids the account's own requirements point at, in order seen."""
    req = account.get("requirements") or {}
    out = []
    for entry in (req.get("past_due") or []) + (req.get("currently_due") or []):
        pid = person_ref(entry)
        if pid and pid not in out:
            out.append(pid)
    return out


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def paginate(session, path, limit):
    """Walk a list endpoint, stopping once `limit` objects have been yielded."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for obj in data:
            yield obj
            seen += 1
            if seen >= limit:
                return
        if not page.get("has_more") or not data:
            return
        params["starting_after"] = data[-1]["id"]


def describe(person):
    """A label a support agent can act on: the role if there is one, else a name."""
    rel = person.get("relationship") or {}
    roles = sorted(k for k, v in rel.items() if v is True)
    name = " ".join(x for x in (person.get("first_name"), person.get("last_name")) if x)
    return "/".join(roles) or name or person.get("id", "?")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-accounts", type=int, default=500,
                    help="stop after this many connected accounts")
    ap.add_argument("--show-clear", action="store_true",
                    help="also print the persons with nothing outstanding")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    accounts = people = bad = 0
    for acct in paginate(s, "/accounts", args.max_accounts):
        accounts += 1
        pointed_at = blocked_on(acct)
        for person in paginate(s, "/accounts/%s/persons" % acct["id"], 100):
            people += 1
            state, detail = verdict(person)
            line = "%-10s %s %s (%s)  %s" % (
                state, acct["id"], person["id"], describe(person), detail)
            if state in ("clear", "unverified") and not args.show_clear:
                continue
            if state in ("clear", "verifying", "unverified"):
                log.info(line)
                continue
            bad += 1
            log.warning(line)
            if person["id"] in pointed_at:
                log.warning("  the account's own requirements name this person")
            log.warning("  repair: POST %s/accounts/%s/persons/%s with the field(s) above",
                        API, acct["id"], person["id"])
            log.warning("  for a document, upload it to files.stripe.com with "
                        "purpose=identity_document and set verification[document][front]")

    log.info("%d account(s), %d person(s), %d needing attention", accounts, people, bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-person-requirements.mjs",
"js": '''/**
 * Report the Persons whose outstanding requirements are blocking an account.
 *
 * Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
 * access to Connected accounts. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Return the Person id an account-level requirement points at, or null.
 * Account requirements read like person_1MqEZ.verification.document.
 */
export function personRef(entry) {
  if (typeof entry !== 'string' || !entry.startsWith('person_')) return null;
  return entry.split('.')[0];
}

/**
 * Classify one Person object. Pure, so the rules are visible and testable.
 */
export function verdict(person) {
  const req = person.requirements ?? {};
  const past = req.past_due ?? [];
  const due = req.currently_due ?? [];
  const status = person.verification?.status;

  if (past.length) {
    return ['past-due',
      `${past.length} field(s) past due (${past.join(', ')}); capabilities that ` +
      'depend on this person are already off'];
  }
  if (due.length) {
    return ['blocking', `${due.length} field(s) currently due (${due.join(', ')})`];
  }
  if (status === 'pending') {
    return ['verifying',
      'submitted and under review; nothing to collect, and a link sent now opens ' +
      'a form with no fields on it'];
  }
  if (status === 'unverified') {
    return ['unverified',
      'not verified and nothing due yet; Stripe asks at a threshold, so this is ' +
      'the cheap moment to collect it'];
  }
  if (status === 'verified') return ['clear', 'verified, nothing outstanding'];
  return ['unknown', `unrecognised verification status ${JSON.stringify(status)}`];
}

/** The Person ids the account's own requirements point at, in order seen. */
export function blockedOn(account) {
  const req = account.requirements ?? {};
  const out = [];
  for (const entry of [...(req.past_due ?? []), ...(req.currently_due ?? [])]) {
    const pid = personRef(entry);
    if (pid && !out.includes(pid)) out.push(pid);
  }
  return out;
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function* paginate(key, path, limit) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, path, params);
    const data = page.data ?? [];
    for (const obj of data) {
      yield obj;
      if (++seen >= limit) return;
    }
    if (!page.has_more || data.length === 0) return;
    params.starting_after = data[data.length - 1].id;
  }
}

function describe(person) {
  const rel = person.relationship ?? {};
  const roles = Object.keys(rel).filter((k) => rel[k] === true).sort();
  const name = [person.first_name, person.last_name].filter(Boolean).join(' ');
  return roles.join('/') || name || person.id || '?';
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }
  const showClear = process.argv.includes('--show-clear');

  let accounts = 0, people = 0, bad = 0;
  for await (const acct of paginate(key, '/accounts', 500)) {
    accounts += 1;
    const pointedAt = blockedOn(acct);
    for await (const person of paginate(key, `/accounts/${acct.id}/persons`, 100)) {
      people += 1;
      const [state, detail] = verdict(person);
      const line = `${state.padEnd(10)} ${acct.id} ${person.id} ` +
                   `(${describe(person)})  ${detail}`;
      if ((state === 'clear' || state === 'unverified') && !showClear) continue;
      if (state === 'clear' || state === 'verifying' || state === 'unverified') {
        console.log(line);
        continue;
      }
      bad += 1;
      console.warn(line);
      if (pointedAt.includes(person.id)) {
        console.warn("  the account's own requirements name this person");
      }
      console.warn(`  repair: POST ${API}/accounts/${acct.id}/persons/${person.id} ` +
                   'with the field(s) above');
      console.warn('  for a document, upload it to files.stripe.com with ' +
                   'purpose=identity_document and set verification[document][front]');
    }
  }

  console.log(`${accounts} account(s), ${people} person(s), ${bad} needing attention`);
  process.exitCode = bad ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two things are worth pinning. The reference parser has to return the id for <code>person_1Mq.verification.document</code> and nothing at all for <code>business_profile.url</code>, because a parser that is generous about the prefix invents person ids that 404. And a person under review has to classify as its own state: it is not clear, and it is not something you can ask anyone to fix.",
"test_py_file": "test_stripe_person_requirements.py",
"test_py": '''from stripe_person_requirements import blocked_on, person_ref, verdict


def test_person_reference_yields_the_id_before_the_first_dot():
    assert person_ref("person_1MqEZ2eZvKYlo2C.verification.document") == "person_1MqEZ2eZvKYlo2C"


def test_ordinary_account_fields_are_not_person_references():
    assert person_ref("business_profile.url") is None
    assert person_ref("external_account") is None
    assert person_ref(None) is None


def test_past_due_outranks_currently_due():
    # past_due is a subset of currently_due, so the order of these checks is the
    # difference between "already broken" and "some paperwork outstanding".
    state, detail = verdict({"requirements": {"past_due": ["dob.day"],
                                              "currently_due": ["dob.day", "id_number"]}})
    assert state == "past-due"
    assert "dob.day" in detail


def test_currently_due_names_the_fields():
    state, detail = verdict({"requirements": {"currently_due": ["id_number"]}})
    assert state == "blocking"
    assert "id_number" in detail


def test_pending_verification_is_not_something_to_collect():
    state, _ = verdict({"requirements": {}, "verification": {"status": "pending"}})
    assert state == "verifying"


def test_missing_verification_status_is_not_silently_clear():
    assert verdict({})[0] == "unknown"


def test_account_requirements_resolve_to_a_deduplicated_person_list():
    acct = {"requirements": {
        "past_due": ["person_1A.verification.document"],
        "currently_due": ["person_1A.verification.document", "person_1B.dob.day",
                          "business_profile.url"]}}
    assert blocked_on(acct) == ["person_1A", "person_1B"]
''',
"test_js_file": "stripe-person-requirements.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { blockedOn, personRef, verdict } from './stripe-person-requirements.mjs';

test('person reference yields the id before the first dot', () => {
  assert.equal(personRef('person_1MqEZ2eZvKYlo2C.verification.document'),
               'person_1MqEZ2eZvKYlo2C');
});

test('ordinary account fields are not person references', () => {
  assert.equal(personRef('business_profile.url'), null);
  assert.equal(personRef(undefined), null);
});

test('past_due outranks currently_due', () => {
  const [state, detail] = verdict({
    requirements: { past_due: ['dob.day'], currently_due: ['dob.day', 'id_number'] },
  });
  assert.equal(state, 'past-due');
  assert.match(detail, /dob\\.day/);
});

test('currently_due names the fields', () => {
  const [state, detail] = verdict({ requirements: { currently_due: ['id_number'] } });
  assert.equal(state, 'blocking');
  assert.match(detail, /id_number/);
});

test('pending verification is not something to collect', () => {
  assert.equal(verdict({ verification: { status: 'pending' } })[0], 'verifying');
});

test('missing verification status is not silently clear', () => {
  assert.equal(verdict({})[0], 'unknown');
});

test('account requirements resolve to a deduplicated person list', () => {
  const acct = { requirements: {
    past_due: ['person_1A.verification.document'],
    currently_due: ['person_1A.verification.document', 'person_1B.dob.day',
                    'business_profile.url'],
  } };
  assert.deepEqual(blockedOn(acct), ['person_1A', 'person_1B']);
});
''',
"faq": [
 ("What does an entry like person_1Mq.verification.document mean?",
  "It is a path, not a field name. Everything left of the first dot is the id of a Person object on that account, and everything right of it is the field that person owes. Fetch GET /v1/accounts/{id}/persons and you will find the same requirement listed on that person's own requirements hash."),
 ("Which people does Stripe create Person objects for?",
  "The account representative, plus the owners, directors and executives that the account's country requires. A sole trader usually has one; a company can have several, and each of them carries an independent requirements hash and verification status."),
 ("Why is charges_enabled false when the account object looks complete?",
  "Because capabilities are verified against everything outstanding, including the sub-objects. One director missing a date of birth blocks the account, and nothing on the account object itself will show you which director or which field without resolving the person reference."),
 ("What is the difference between verification.status pending and a currently_due field?",
  "Pending means something was submitted and Stripe is reviewing it, so there is nothing for the seller to do. A currently_due field means Stripe is waiting on you. Sending an onboarding link for a pending person opens a form with no fields on it."),
 ("Can I do this check without a live secret key?",
  "Yes. A restricted key with read access to Connected accounts covers both the account list and the persons list. That key cannot submit any of the fields it reports, which is the point: the script tells you who owes what and you run the update yourself."),
],
"related": [
 ("/stripe/requirements-past-due-disables-account/", "requirements.past_due has already disabled the payouts"),
 ("/stripe/verification-errors-unread/", "requirements.errors explains the rejected document"),
 ("/stripe/connected-accounts-charges-disabled/", "A connected account sits with charges_enabled false"),
],
"citations": [CITE_PERSON_OBJ, CITE_API_VERIFICATION, CITE_ACCOUNT_OBJ],
},

{
"slug": "future-requirements-deadline-ignored",
"title": "future_requirements will revoke a capability on a date",
"description": "Verified accounts that process fine today all break on the same morning. The warning was in a hash your monitor does not read, with a deadline attached.",
"h1": "future_requirements will revoke a capability on a date",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe future_requirements", "current_deadline stripe connect",
             "stripe capability disabled deadline", "requirement_collection application",
             "stripe verification updates"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Fourteen connected accounts stopped taking payments on the same Thursday morning. All of them were fully verified. None of them had anything in <code>requirements</code> the night before, and the monitor that reads <code>requirements</code> every hour never made a sound. The fields that disabled them had been sitting on the same objects for six weeks, in a different hash, with the date printed on it.",
"short_answer": """<p>Read <code>future_requirements</code> as well as <code>requirements</code>. It is a separate hash with the same shape, holding fields Stripe will start enforcing later. It does <em>not</em> affect capabilities and its entries do <em>not</em> appear in <code>requirements</code>, so every check written against <code>requirements</code> is blind to it by design.</p>
<p>At <code>future_requirements.current_deadline</code> the entries migrate into <code>requirements</code>, and anything unmet disables the capability immediately. Paginate <code>GET /v1/accounts?limit=100</code>, keep the accounts where <code>controller.requirement_collection == "application"</code>, and sort those with a non-empty <code>future_requirements.currently_due</code> by their deadline.</p>""",
"problem": """<p>The shape of this failure is what makes it expensive. It is not one account breaking on a random day, it is a cohort breaking together, because the deadline is set by a change Stripe is rolling out and every affected account gets the same date. A support team sized for the usual trickle of verification problems gets a month's worth in one morning, from customers who were all working perfectly the day before.</p>
<p>And the accounts that break are the good ones. These are verified, processing, established sellers &mdash; the accounts nobody watches, because everything about them has been green for a year. The stalled and half-onboarded accounts that get all the monitoring attention are unaffected.</p>""",
"why": """<p><strong>The hash is invisible by design.</strong> <code>future_requirements</code> exists precisely so that upcoming changes do not disturb a working account. That is the right behaviour and it is also why nothing surfaces it: no capability changes, no <code>disabled_reason</code> appears, no event that your handler branches on fires with a status change in it.</p>
<p><strong>The migration is the moment of failure, not the collection.</strong> Fields do not gradually become required. At <code>current_deadline</code> they move into <code>requirements</code> and, if unmet, take the capability down in the same instant. There is no intermediate state you can alert on, so the only warning available is the one you have to go and look for.</p>
<p><strong>It only applies to accounts you are responsible for.</strong> <code>controller.requirement_collection</code> tells you who collects: <code>"stripe"</code> means Stripe chases the account owner directly and handles the update, <code>"application"</code> means you do. Alerting on future requirements for Stripe-collected accounts produces noise you cannot act on, and the field is the only way to tell them apart.</p>
<p><strong>A deadline can also be absent.</strong> Entries can appear in <code>future_requirements.currently_due</code> before any date is set. That is a real state and it is not benign: it means work is coming and you cannot yet say when. Code that sorts on <code>current_deadline</code> and assumes a number quietly drops those accounts.</p>""",
"steps": [
 {"h": "Filter to the accounts whose requirements you collect",
  "body": """<p><code>controller.requirement_collection == "application"</code>. Everything else is Stripe's to chase, and including it turns a short actionable list into a long one that gets ignored.</p>"""},
 {"h": "Read future_requirements, then sort by current_deadline",
  "body": """<p>The list you want is ordered by date, with days remaining next to each account. That converts a warning into a schedule, and a schedule is the only form of this information anybody acts on before the deadline rather than after.</p>"""},
 {"h": "Give the undated accounts their own bucket",
  "body": """<p>Entries with no <code>current_deadline</code> yet are work you know about with a date you do not. Sorting them last is fine; dropping them because the sort key is null is how they end up in the cohort that breaks.</p>"""},
 {"h": "Collect the future fields in the same session as everything else",
  "body": """<p>For hosted onboarding, pass <code>collection_options[future_requirements]=include</code> when creating the account link. That asks for today's fields and the upcoming ones in one visit, which is one email to the seller instead of two.</p>"""},
 {"h": "Rehearse the migration in a sandbox before it happens",
  "body": """<p>Creating a sandbox account with the email <code>jenny+enforce_future_requirements@example.com</code> forces every known future requirement into <code>requirements</code> immediately. That is the only way to see what your own product does on the morning of the deadline while there is still time to change it.</p>"""},
],
"verify": """<p>Re-run the script. Nothing should be overdue, and anything still listed should carry a deadline far enough out to be scheduled rather than chased.</p>
<pre><code class="language-bash">python3 stripe_future_requirements.py
# 412 account(s): 0 overdue, 0 due within 14 days, 6 scheduled, 2 undated</code></pre>""",
"code_intro": "One paginated GET against <code>/v1/accounts</code>, read-only, and no second call at all &mdash; the future hash comes back on the list response. The classifier is pure and takes the account plus the current time, because the entire value of this check is the ordering it produces, and an ordering is only testable if the clock is an argument rather than something the function reaches for itself.",
"py_file": "stripe_future_requirements.py",
"py": '''"""Report connected accounts whose future_requirements will disable a capability.

Read only. One paginated GET and no writes: give this a RESTRICTED key with read
access to Connected accounts. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_future_requirements")

API = "https://api.stripe.com/v1"

DAY = 86400


def verdict(account, now, soon_days=14):
    """Classify one account's future_requirements. Pure: `now` is an argument.

    Returns (state, detail). The states separate the three things a reader has to
    do differently: nothing, schedule it, or do it this week. Accounts whose
    requirements Stripe collects are excluded up front rather than reported as
    healthy, because their state is not yours to act on either way.
    """
    controller = account.get("controller") or {}
    if controller.get("requirement_collection") != "application":
        return ("stripe-managed",
                "Stripe collects for this account and handles the update itself")

    fr = account.get("future_requirements") or {}
    past = fr.get("past_due") or []
    due = fr.get("currently_due") or []
    eventually = fr.get("eventually_due") or []
    deadline = fr.get("current_deadline")

    if past:
        return ("overdue",
                "%d future field(s) already past due (%s)" % (len(past), ", ".join(past)))
    if due:
        if deadline is None:
            return ("undated",
                    "%d future field(s) with no deadline set yet (%s)"
                    % (len(due), ", ".join(due)))
        days = (deadline - now) / float(DAY)
        if days <= 0:
            return ("overdue",
                    "the deadline passed %.1f day(s) ago; these fields are moving "
                    "into requirements now" % (-days,))
        if days <= soon_days:
            return ("due-soon",
                    "%d future field(s) in %.1f day(s) (%s)"
                    % (len(due), days, ", ".join(due)))
        return ("scheduled",
                "%d future field(s) in %.1f day(s)" % (len(due), days))
    if eventually:
        return ("eventual",
                "%d field(s) Stripe will want at a later threshold" % len(eventually))
    return ("clear", "no future requirements")


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def paginate(session, path, limit):
    """Walk a list endpoint, stopping once `limit` objects have been yielded."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for obj in data:
            yield obj
            seen += 1
            if seen >= limit:
                return
        if not page.get("has_more") or not data:
            return
        params["starting_after"] = data[-1]["id"]


ORDER = {"overdue": 0, "due-soon": 1, "scheduled": 2, "undated": 3, "eventual": 4}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-accounts", type=int, default=500,
                    help="stop after this many connected accounts")
    ap.add_argument("--soon-days", type=int, default=14,
                    help="a deadline inside this many days is urgent")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    now = time.time()
    total = 0
    rows = []
    for acct in paginate(s, "/accounts", args.max_accounts):
        total += 1
        state, detail = verdict(acct, now, args.soon_days)
        if state in ("clear", "stripe-managed"):
            continue
        fr = acct.get("future_requirements") or {}
        rows.append((ORDER.get(state, 9),
                     fr.get("current_deadline") or float("inf"),
                     state, acct["id"], detail))

    rows.sort()
    for _, _, state, acct_id, detail in rows:
        log.warning("%-11s %s  %s", state, acct_id, detail)
        log.warning("  repair: POST %s/accounts/%s with the future field(s) before "
                    "the deadline", API, acct_id)
        log.warning("  hosted: create an account link with "
                    "collection_options[future_requirements]=include")

    counts = {}
    for _, _, state, _, _ in rows:
        counts[state] = counts.get(state, 0) + 1
    log.info("%d account(s): %d overdue, %d due within %d days, %d scheduled, %d undated",
             total, counts.get("overdue", 0), counts.get("due-soon", 0),
             args.soon_days, counts.get("scheduled", 0), counts.get("undated", 0))
    return 1 if counts.get("overdue") or counts.get("due-soon") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-future-requirements.mjs",
"js": '''/**
 * Report connected accounts whose future_requirements will disable a capability.
 *
 * Read only. One paginated GET and no writes: give this a RESTRICTED key with
 * read access to Connected accounts. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';
const DAY = 86400;

/**
 * Classify one account's future_requirements. Pure: `now` is an argument, so the
 * ordering this produces can be tested against a fixed clock.
 */
export function verdict(account, now, soonDays = 14) {
  const controller = account.controller ?? {};
  if (controller.requirement_collection !== 'application') {
    return ['stripe-managed',
      'Stripe collects for this account and handles the update itself'];
  }

  const fr = account.future_requirements ?? {};
  const past = fr.past_due ?? [];
  const due = fr.currently_due ?? [];
  const eventually = fr.eventually_due ?? [];
  const deadline = fr.current_deadline;

  if (past.length) {
    return ['overdue',
      `${past.length} future field(s) already past due (${past.join(', ')})`];
  }
  if (due.length) {
    if (deadline === null || deadline === undefined) {
      return ['undated',
        `${due.length} future field(s) with no deadline set yet (${due.join(', ')})`];
    }
    const days = (deadline - now) / DAY;
    if (days <= 0) {
      return ['overdue',
        `the deadline passed ${(-days).toFixed(1)} day(s) ago; these fields are ` +
        'moving into requirements now'];
    }
    if (days <= soonDays) {
      return ['due-soon',
        `${due.length} future field(s) in ${days.toFixed(1)} day(s) (${due.join(', ')})`];
    }
    return ['scheduled', `${due.length} future field(s) in ${days.toFixed(1)} day(s)`];
  }
  if (eventually.length) {
    return ['eventual',
      `${eventually.length} field(s) Stripe will want at a later threshold`];
  }
  return ['clear', 'no future requirements'];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function* paginate(key, path, limit) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, path, params);
    const data = page.data ?? [];
    for (const obj of data) {
      yield obj;
      if (++seen >= limit) return;
    }
    if (!page.has_more || data.length === 0) return;
    params.starting_after = data[data.length - 1].id;
  }
}

const ORDER = { overdue: 0, 'due-soon': 1, scheduled: 2, undated: 3, eventual: 4 };

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }
  const soonDays = 14;
  const now = Date.now() / 1000;

  let total = 0;
  const rows = [];
  for await (const acct of paginate(key, '/accounts', 500)) {
    total += 1;
    const [state, detail] = verdict(acct, now, soonDays);
    if (state === 'clear' || state === 'stripe-managed') continue;
    const fr = acct.future_requirements ?? {};
    rows.push([ORDER[state] ?? 9, fr.current_deadline ?? Infinity, state, acct.id, detail]);
  }

  rows.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const counts = {};
  for (const [, , state, id, detail] of rows) {
    counts[state] = (counts[state] ?? 0) + 1;
    console.warn(`${state.padEnd(11)} ${id}  ${detail}`);
    console.warn(`  repair: POST ${API}/accounts/${id} with the future field(s) ` +
                 'before the deadline');
    console.warn('  hosted: create an account link with ' +
                 'collection_options[future_requirements]=include');
  }

  console.log(`${total} account(s): ${counts.overdue ?? 0} overdue, ` +
              `${counts['due-soon'] ?? 0} due within ${soonDays} days, ` +
              `${counts.scheduled ?? 0} scheduled, ${counts.undated ?? 0} undated`);
  process.exitCode = (counts.overdue || counts['due-soon']) ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The clock is a parameter, which is what makes the interesting cases cheap to write: the same account is <code>scheduled</code> six weeks out and <code>due-soon</code> five days out, and the test says so directly instead of mocking time. The two cases that actually bite are also pinned here &mdash; an account Stripe collects for is never reported, and future entries with a null deadline are their own state rather than a sort key that evaluates to zero.",
"test_py_file": "test_stripe_future_requirements.py",
"test_py": '''from stripe_future_requirements import verdict

NOW = 1_700_000_000
APP = {"requirement_collection": "application"}


def account(**future):
    return {"controller": APP, "future_requirements": future}


def test_stripe_collected_accounts_are_never_reported():
    # Stripe chases the owner and applies the update itself, so an alert here is
    # noise nobody can act on.
    acct = {"controller": {"requirement_collection": "stripe"},
            "future_requirements": {"currently_due": ["id_number"],
                                    "current_deadline": NOW + 3600}}
    assert verdict(acct, NOW)[0] == "stripe-managed"


def test_a_distant_deadline_is_scheduled():
    state, _ = verdict(account(currently_due=["id_number"],
                               current_deadline=NOW + 42 * 86400), NOW)
    assert state == "scheduled"


def test_the_same_account_is_urgent_inside_the_window():
    state, detail = verdict(account(currently_due=["id_number"],
                                    current_deadline=NOW + 5 * 86400), NOW)
    assert state == "due-soon"
    assert "id_number" in detail


def test_an_elapsed_deadline_is_overdue_not_merely_urgent():
    state, _ = verdict(account(currently_due=["id_number"],
                               current_deadline=NOW - 86400), NOW)
    assert state == "overdue"


def test_future_entries_without_a_deadline_are_their_own_state():
    state, _ = verdict(account(currently_due=["id_number"], current_deadline=None), NOW)
    assert state == "undated"


def test_eventually_due_alone_is_not_urgent_and_not_silent():
    assert verdict(account(eventually_due=["id_number"]), NOW)[0] == "eventual"


def test_an_empty_future_hash_is_clear():
    assert verdict(account(), NOW)[0] == "clear"
''',
"test_js_file": "stripe-future-requirements.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-future-requirements.mjs';

const NOW = 1700000000;
const account = (future) => ({
  controller: { requirement_collection: 'application' },
  future_requirements: future,
});

test('stripe collected accounts are never reported', () => {
  const acct = {
    controller: { requirement_collection: 'stripe' },
    future_requirements: { currently_due: ['id_number'], current_deadline: NOW + 3600 },
  };
  assert.equal(verdict(acct, NOW)[0], 'stripe-managed');
});

test('a distant deadline is scheduled', () => {
  const acct = account({ currently_due: ['id_number'],
                         current_deadline: NOW + 42 * 86400 });
  assert.equal(verdict(acct, NOW)[0], 'scheduled');
});

test('the same account is urgent inside the window', () => {
  const acct = account({ currently_due: ['id_number'],
                         current_deadline: NOW + 5 * 86400 });
  const [state, detail] = verdict(acct, NOW);
  assert.equal(state, 'due-soon');
  assert.match(detail, /id_number/);
});

test('an elapsed deadline is overdue not merely urgent', () => {
  const acct = account({ currently_due: ['id_number'], current_deadline: NOW - 86400 });
  assert.equal(verdict(acct, NOW)[0], 'overdue');
});

test('future entries without a deadline are their own state', () => {
  const acct = account({ currently_due: ['id_number'], current_deadline: null });
  assert.equal(verdict(acct, NOW)[0], 'undated');
});

test('eventually_due alone is not urgent and not silent', () => {
  assert.equal(verdict(account({ eventually_due: ['id_number'] }), NOW)[0], 'eventual');
});

test('an empty future hash is clear', () => {
  assert.equal(verdict(account({}), NOW)[0], 'clear');
});
''',
"faq": [
 ("What is the difference between requirements and future_requirements?",
  "requirements is what is being enforced now, and unmet entries there disable capabilities. future_requirements is what will be enforced later; it does not affect capabilities and its entries do not appear in requirements until the deadline passes. They are two hashes with the same shape and completely different urgency."),
 ("What happens at current_deadline exactly?",
  "The entries in future_requirements move into requirements. Anything still unmet at that moment disables the capabilities that depend on it, with no intermediate warning state. That is why the deadline is the alert and the migration is not."),
 ("Why should I skip accounts where requirement_collection is stripe?",
  "Because Stripe collects those fields from the account owner directly and applies the update. You cannot submit them and you will not be told when they are satisfied, so listing those accounts adds volume to a report without adding anything to do."),
 ("What does an empty current_deadline with fields in currently_due mean?",
  "That Stripe knows what it will need and has not set a date yet. It is genuinely coming, so it belongs in the report, but it cannot be sorted alongside the dated ones. Give it its own bucket rather than treating a null as zero or dropping it."),
 ("How do I test my handling before a real deadline arrives?",
  "Create a sandbox account with the email jenny+enforce_future_requirements@example.com. Stripe forces all known future requirements straight into requirements for that account, which reproduces the morning of the deadline while you still have time to change what your product does."),
],
"related": [
 ("/stripe/requirements-past-due-disables-account/", "requirements.past_due has already disabled the payouts"),
 ("/stripe/person-requirements-outstanding/", "A Person's currently_due blocks the whole account"),
 ("/stripe/transfers-capability-inactive/", "transfers capability is inactive so every transfer 400s"),
],
"citations": [CITE_VERIFICATION_UPDATES, CITE_ACCOUNT_OBJ, CITE_API_VERIFICATION],
},

{
"slug": "card-payments-inactive-cascades",
"title": "card_payments inactive disables transfers as well",
"description": "You satisfy every field the transfers capability lists and it stays inactive. The blocking requirement belongs to a capability you do not even use.",
"h1": "card_payments inactive disables transfers as well",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe card_payments inactive", "capabilities transfers inactive",
             "stripe connect capability coupling", "stripe capabilities currently_due",
             "stripe capability requirements union"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "You read <code>capabilities.transfers</code>, saw <code>inactive</code>, fetched the capability, collected the two fields in its <code>currently_due</code>, and submitted them. Stripe accepted the update. The capability is still <code>inactive</code>, its <code>currently_due</code> is now empty, and transfers still fail. Nothing you can see on that capability explains it, because the requirement holding it down is filed under a different one.",
"short_answer": """<p>Stripe documents a coupling: if an account has both <code>card_payments</code> and <code>transfers</code>, and the <code>status</code> of <em>either</em> is <code>inactive</code>, then <strong>both</strong> are disabled. So a platform that only cares about transfers can satisfy every requirement transfers lists and stay blocked on a <code>card_payments</code> field it never reads.</p>
<p>Check the pair together from <code>GET /v1/accounts?limit=100</code>, then take the <em>union</em> of <code>requirements.currently_due</code> across every entry from <code>GET /v1/accounts/{id}/capabilities</code> rather than the one capability you use. That union is the actual list of fields to collect, and it can be satisfied in a single account update.</p>""",
"problem": """<p>This is the failure that survives being fixed. Somebody works the capability's own requirement list to empty, watches nothing change, and concludes there is a delay on Stripe's side. A week later they work it again. The loop is stable because the evidence available on the object you are looking at is genuinely consistent with everything being fine.</p>
<p>Where it hurts most is on platforms that never take card payments through the connected account at all. Destination charges settle on the platform and are transferred onward, so <code>card_payments</code> on the seller's account is a capability nobody has thought about since it was requested by whatever onboarding preset created the account. It is unmonitored, it is unmentioned in any runbook, and it is holding the money.</p>""",
"why": """<p><strong>The coupling is symmetric, so the direction of the fault is not obvious.</strong> An inactive <code>card_payments</code> disables <code>transfers</code> and an inactive <code>transfers</code> disables <code>card_payments</code>. Reading either status alone tells you something is wrong; it does not tell you which of the two is the cause, and the repair depends entirely on that.</p>
<p><strong>Requirements are filed per capability, and only per capability.</strong> The account-level <code>currently_due</code> is a flattened view that does not say which capability each field belongs to. The per-capability view says exactly that, and it is the only way to see a field that exists solely because of a capability you do not use.</p>
<p><strong>Fixing one capability at a time cannot converge.</strong> Clearing the transfers list leaves the card_payments list untouched, and the pair stays down. The union collected in one pass is not just faster, it is the only approach that ends. This is the mechanism; the <em>status values</em> themselves and the case where a capability was never requested at all are covered in <a href="/stripe/transfers-capability-inactive/">transfers capability is inactive so every transfer 400s</a>.</p>
<p><strong>Dropping the capability is a real option and is sometimes the right one.</strong> If the connected account genuinely never needs to take card payments, requesting <code>card_payments=false</code> removes it and with it the coupling. It fails for capabilities that are permanent on that account type, which is itself a useful thing to learn early rather than during an incident.</p>""",
"steps": [
 {"h": "Read the pair, not one capability",
  "body": """<p>From the accounts list, take <code>capabilities.card_payments</code> and <code>capabilities.transfers</code> together. Both present and either one <code>inactive</code> is the flag. If only one of the two exists on the account there is no coupling to worry about, and that is a different diagnosis.</p>"""},
 {"h": "Pull every capability, not the one you use",
  "body": """<p><code>GET /v1/accounts/{id}/capabilities</code> returns them all, each with its own <code>requirements</code> hash. This is one extra GET per unhealthy account and it is where the field you are missing actually lives.</p>"""},
 {"h": "Union the currently_due lists and keep the owner of each field",
  "body": """<p>The union is what to collect. Keeping the capability name alongside each field is what makes the report legible: seeing <code>business_profile.mcc</code> attributed to <code>card_payments</code> is the moment the whole thing makes sense to whoever is reading.</p>"""},
 {"h": "Submit the union in one account update",
  "body": """<p>One <code>POST /v1/accounts/{id}</code> carrying every field in the union. Splitting it across two updates re-creates the loop you are trying to escape, because the pair only comes back up when neither capability is inactive.</p>"""},
 {"h": "Or drop the capability you do not need",
  "body": """<p>Requesting <code>card_payments</code> as <code>false</code> removes it from the account and the coupling with it. Only do this where the account really will never take a card payment directly, and expect it to fail on account types where the capability is permanent.</p>"""},
],
"verify": """<p>Re-run the script. Every account with both capabilities should report both <code>active</code>, and the union of outstanding fields should be empty.</p>
<pre><code class="language-bash">python3 stripe_capability_coupling.py
# 412 account(s): 410 healthy, 0 coupled down, 2 pending, 0 field(s) outstanding</code></pre>""",
"code_intro": "One paginated GET over the accounts, then one GET of the capabilities list for each account that is not healthy &mdash; a restricted key with read access to Connected accounts covers both. Two pure functions: one classifies the coupled pair from the statuses alone, and one unions the outstanding fields across every capability while remembering which capability asked for each. The second is the part that changes what you do next, so it is worth having outside the request loop where it can be read.",
"py_file": "stripe_capability_coupling.py",
"py": '''"""Report connected accounts where the card_payments/transfers pair is down.

Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
access to Connected accounts. The repair is printed, never performed, because
this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_capability_coupling")

API = "https://api.stripe.com/v1"

PAIR = ("card_payments", "transfers")


def verdict(capabilities):
    """Classify the coupled pair on one account. Pure and offline testable.

    Stripe couples card_payments and transfers: where an account has both, either
    one sitting at inactive disables the pair. Returns (state, detail). An account
    that has only one of the two is reported as uncoupled rather than as healthy,
    because the coupling is not what is wrong with it.
    """
    caps = capabilities or {}
    present = [name for name in PAIR if name in caps]
    if len(present) < len(PAIR):
        return ("uncoupled",
                "only %s on this account, so the pair cannot disable itself"
                % (", ".join(present) or "neither capability",))

    inactive = [name for name in PAIR if caps[name] == "inactive"]
    if len(inactive) == len(PAIR):
        return ("coupled-down",
                "both card_payments and transfers are inactive; collect the union "
                "of their requirements, not one list at a time")
    if inactive:
        blocked = [name for name in PAIR if name not in inactive]
        return ("coupled-down",
                "%s is inactive, which disables %s as well; the field you need may "
                "be filed under %s" % (inactive[0], blocked[0], inactive[0]))

    pending = [name for name in PAIR if caps[name] == "pending"]
    if pending:
        return ("coupled-pending",
                "%s is pending verification; nothing to collect until Stripe "
                "finishes with what it already has" % (", ".join(pending),))

    other = [name for name in PAIR if caps[name] != "active"]
    if other:
        return ("unknown",
                "unrecognised status for %s" % (", ".join(
                    "%s=%r" % (name, caps[name]) for name in other),))
    return ("healthy", "both capabilities active")


def union_due(capability_objects):
    """Union currently_due across every capability, keeping who asked for each.

    Returns [(field, [capability, ...]), ...] sorted by field. This is the list to
    submit in one account update: collecting one capability's list at a time
    cannot converge, because the pair stays disabled while either half is.
    """
    owed = {}
    for cap in capability_objects or []:
        name = cap.get("id") or "?"
        req = cap.get("requirements") or {}
        for field in (req.get("past_due") or []) + (req.get("currently_due") or []):
            owed.setdefault(field, set()).add(name)
    return [(field, sorted(owners)) for field, owners in sorted(owed.items())]


def get(session, path, **params):
    r = session.get(API + path, params=params, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def paginate(session, path, limit):
    """Walk a list endpoint, stopping once `limit` objects have been yielded."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for obj in data:
            yield obj
            seen += 1
            if seen >= limit:
                return
        if not page.get("has_more") or not data:
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-accounts", type=int, default=500,
                    help="stop after this many connected accounts")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    total = healthy = down = pending = fields = 0
    for acct in paginate(s, "/accounts", args.max_accounts):
        total += 1
        state, detail = verdict(acct.get("capabilities"))
        if state == "healthy":
            healthy += 1
            continue
        if state == "uncoupled":
            continue
        if state == "coupled-pending":
            pending += 1
            log.info("%-16s %s  %s", state, acct["id"], detail)
            continue
        down += 1
        log.warning("%-16s %s  %s", state, acct["id"], detail)

        caps = get(s, "/accounts/%s/capabilities" % acct["id"]).get("data", [])
        outstanding = union_due(caps)
        fields += len(outstanding)
        for field, owners in outstanding:
            log.warning("    %-42s required by %s", field, ", ".join(owners))
        if outstanding:
            log.warning("  repair: one POST %s/accounts/%s carrying every field above",
                        API, acct["id"])
        else:
            log.warning("  no fields outstanding: check requirements.disabled_reason "
                        "and requirements.errors on each capability")

    log.info("%d account(s): %d healthy, %d coupled down, %d pending, %d field(s) outstanding",
             total, healthy, down, pending, fields)
    return 1 if down else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-capability-coupling.mjs",
"js": '''/**
 * Report connected accounts where the card_payments/transfers pair is down.
 *
 * Read only. Paginated GETs and no writes: give this a RESTRICTED key with read
 * access to Connected accounts. The repair is printed, never performed.
 */
const API = 'https://api.stripe.com/v1';

const PAIR = ['card_payments', 'transfers'];

/**
 * Classify the coupled pair on one account. Pure and offline testable.
 * Stripe couples card_payments and transfers: where an account has both, either
 * one sitting at inactive disables the pair.
 */
export function verdict(capabilities) {
  const caps = capabilities ?? {};
  const present = PAIR.filter((name) => name in caps);
  if (present.length < PAIR.length) {
    return ['uncoupled',
      `only ${present.join(', ') || 'neither capability'} on this account, so the ` +
      'pair cannot disable itself'];
  }

  const inactive = PAIR.filter((name) => caps[name] === 'inactive');
  if (inactive.length === PAIR.length) {
    return ['coupled-down',
      'both card_payments and transfers are inactive; collect the union of their ' +
      'requirements, not one list at a time'];
  }
  if (inactive.length) {
    const blocked = PAIR.filter((name) => !inactive.includes(name));
    return ['coupled-down',
      `${inactive[0]} is inactive, which disables ${blocked[0]} as well; the field ` +
      `you need may be filed under ${inactive[0]}`];
  }

  const pending = PAIR.filter((name) => caps[name] === 'pending');
  if (pending.length) {
    return ['coupled-pending',
      `${pending.join(', ')} is pending verification; nothing to collect until ` +
      'Stripe finishes with what it already has'];
  }

  const other = PAIR.filter((name) => caps[name] !== 'active');
  if (other.length) {
    return ['unknown', `unrecognised status for ${other.map(
      (name) => `${name}=${JSON.stringify(caps[name])}`).join(', ')}`];
  }
  return ['healthy', 'both capabilities active'];
}

/**
 * Union currently_due across every capability, keeping who asked for each.
 * Returns [[field, [capability, ...]], ...] sorted by field.
 */
export function unionDue(capabilityObjects) {
  const owed = new Map();
  for (const cap of capabilityObjects ?? []) {
    const name = cap.id ?? '?';
    const req = cap.requirements ?? {};
    for (const field of [...(req.past_due ?? []), ...(req.currently_due ?? [])]) {
      if (!owed.has(field)) owed.set(field, new Set());
      owed.get(field).add(name);
    }
  }
  return [...owed.entries()]
    .sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))
    .map(([field, owners]) => [field, [...owners].sort()]);
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function* paginate(key, path, limit) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, path, params);
    const data = page.data ?? [];
    for (const obj of data) {
      yield obj;
      if (++seen >= limit) return;
    }
    if (!page.has_more || data.length === 0) return;
    params.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  let total = 0, healthy = 0, down = 0, pending = 0, fields = 0;
  for await (const acct of paginate(key, '/accounts', 500)) {
    total += 1;
    const [state, detail] = verdict(acct.capabilities);
    if (state === 'healthy') { healthy += 1; continue; }
    if (state === 'uncoupled') continue;
    if (state === 'coupled-pending') {
      pending += 1;
      console.log(`${state.padEnd(16)} ${acct.id}  ${detail}`);
      continue;
    }
    down += 1;
    console.warn(`${state.padEnd(16)} ${acct.id}  ${detail}`);

    const { data: caps = [] } = await get(key, `/accounts/${acct.id}/capabilities`);
    const outstanding = unionDue(caps);
    fields += outstanding.length;
    for (const [field, owners] of outstanding) {
      console.warn(`    ${field.padEnd(42)} required by ${owners.join(', ')}`);
    }
    if (outstanding.length) {
      console.warn(`  repair: one POST ${API}/accounts/${acct.id} carrying every ` +
                   'field above');
    } else {
      console.warn('  no fields outstanding: check requirements.disabled_reason and ' +
                   'requirements.errors on each capability');
    }
  }

  console.log(`${total} account(s): ${healthy} healthy, ${down} coupled down, ` +
              `${pending} pending, ${fields} field(s) outstanding`);
  process.exitCode = down ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that matters is the asymmetric one: <code>transfers</code> is <code>active</code>, <code>card_payments</code> is <code>inactive</code>, and the account is still down. A check written around the capability you actually use calls that healthy. The other is the union: a field owed only by <code>card_payments</code> has to appear in the list even though you were looking at transfers, which is the whole reason for collecting across every capability rather than one.",
"test_py_file": "test_stripe_capability_coupling.py",
"test_py": '''from stripe_capability_coupling import union_due, verdict


def test_both_active_is_healthy():
    assert verdict({"card_payments": "active", "transfers": "active"})[0] == "healthy"


def test_an_active_transfers_is_still_down_when_card_payments_is_inactive():
    # The whole point of the note: reading only the capability you use says fine.
    state, detail = verdict({"card_payments": "inactive", "transfers": "active"})
    assert state == "coupled-down"
    assert "card_payments" in detail
    assert "transfers" in detail


def test_the_coupling_runs_the_other_way_too():
    state, detail = verdict({"card_payments": "active", "transfers": "inactive"})
    assert state == "coupled-down"
    assert "transfers is inactive" in detail


def test_one_capability_alone_is_not_a_coupling_problem():
    assert verdict({"transfers": "inactive"})[0] == "uncoupled"
    assert verdict({})[0] == "uncoupled"


def test_pending_is_separated_from_inactive():
    state, _ = verdict({"card_payments": "pending", "transfers": "active"})
    assert state == "coupled-pending"


def test_an_unrecognised_status_is_not_silently_healthy():
    assert verdict({"card_payments": "revoked", "transfers": "active"})[0] == "unknown"


def test_the_union_keeps_fields_owed_by_a_capability_you_do_not_use():
    caps = [
        {"id": "transfers", "requirements": {"currently_due": []}},
        {"id": "card_payments",
         "requirements": {"currently_due": ["business_profile.mcc"],
                          "past_due": ["business_profile.url"]}},
    ]
    assert union_due(caps) == [
        ("business_profile.mcc", ["card_payments"]),
        ("business_profile.url", ["card_payments"]),
    ]


def test_a_field_owed_by_both_names_both():
    caps = [
        {"id": "transfers", "requirements": {"currently_due": ["tos_acceptance.date"]}},
        {"id": "card_payments", "requirements": {"currently_due": ["tos_acceptance.date"]}},
    ]
    assert union_due(caps) == [("tos_acceptance.date", ["card_payments", "transfers"])]
''',
"test_js_file": "stripe-capability-coupling.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { unionDue, verdict } from './stripe-capability-coupling.mjs';

test('both active is healthy', () => {
  assert.equal(verdict({ card_payments: 'active', transfers: 'active' })[0], 'healthy');
});

test('an active transfers is still down when card_payments is inactive', () => {
  const [state, detail] = verdict({ card_payments: 'inactive', transfers: 'active' });
  assert.equal(state, 'coupled-down');
  assert.match(detail, /card_payments/);
  assert.match(detail, /transfers/);
});

test('the coupling runs the other way too', () => {
  const [state, detail] = verdict({ card_payments: 'active', transfers: 'inactive' });
  assert.equal(state, 'coupled-down');
  assert.match(detail, /transfers is inactive/);
});

test('one capability alone is not a coupling problem', () => {
  assert.equal(verdict({ transfers: 'inactive' })[0], 'uncoupled');
  assert.equal(verdict({})[0], 'uncoupled');
});

test('pending is separated from inactive', () => {
  assert.equal(verdict({ card_payments: 'pending', transfers: 'active' })[0],
               'coupled-pending');
});

test('an unrecognised status is not silently healthy', () => {
  assert.equal(verdict({ card_payments: 'revoked', transfers: 'active' })[0], 'unknown');
});

test('the union keeps fields owed by a capability you do not use', () => {
  const caps = [
    { id: 'transfers', requirements: { currently_due: [] } },
    { id: 'card_payments',
      requirements: { currently_due: ['business_profile.mcc'],
                      past_due: ['business_profile.url'] } },
  ];
  assert.deepEqual(unionDue(caps), [
    ['business_profile.mcc', ['card_payments']],
    ['business_profile.url', ['card_payments']],
  ]);
});

test('a field owed by both names both', () => {
  const caps = [
    { id: 'transfers', requirements: { currently_due: ['tos_acceptance.date'] } },
    { id: 'card_payments', requirements: { currently_due: ['tos_acceptance.date'] } },
  ];
  assert.deepEqual(unionDue(caps),
                   [['tos_acceptance.date', ['card_payments', 'transfers']]]);
});
''',
"faq": [
 ("Does an inactive card_payments really stop transfers?",
  "Yes, where the account has both. Stripe documents the coupling explicitly: if an account has card_payments and transfers and either one is inactive, both are disabled. It is symmetric, so an inactive transfers takes card_payments down in the same way."),
 ("Why is the capability's own currently_due empty while it stays inactive?",
  "Because the field holding it down is filed under the other half of the pair. Requirements are attached per capability, so clearing the list on the capability you use tells you nothing about the one that is actually blocking it."),
 ("Why not just fix the capabilities one at a time?",
  "Because that cannot converge. The pair only comes back up when neither half is inactive, so clearing one list and leaving the other still leaves both disabled. Collect the union in one pass and submit it in one account update."),
 ("Can I remove card_payments if the seller never takes cards directly?",
  "Often, yes. Requesting card_payments as false drops it from the account and removes the coupling. It fails on account types where the capability is permanent, so check the result rather than assuming it worked."),
 ("What if the union is empty and the pair is still down?",
  "Then the block is not a missing field. Read requirements.disabled_reason and requirements.errors on each capability: a rejected document or a platform-level pause produces an inactive status with nothing outstanding to collect."),
],
"related": [
 ("/stripe/transfers-capability-inactive/", "transfers capability is inactive so every transfer 400s"),
 ("/stripe/connected-accounts-charges-disabled/", "A connected account sits with charges_enabled false"),
 ("/stripe/future-requirements-deadline-ignored/", "future_requirements will revoke a capability on a date"),
],
"citations": [CITE_CAPABILITIES, CITE_CAPABILITY_OBJ, CITE_ACCOUNT_OBJ],
},

{
"slug": "external-account-currency-mismatch",
"title": "No external account can settle the account's currency",
"description": "A payout fails saying there is no external account in that currency, on an account that plainly has a bank account attached.",
"h1": "no external account can settle the account's currency",
"category": "Stripe",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["stripe no external accounts in that currency", "default_for_currency",
             "stripe cross border payout", "supported_transfer_countries",
             "stripe country_specs bank account currencies"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The payout call comes back with <em>Sorry, you don't have any external accounts in that currency (usd)</em>. The account plainly has a bank account: you can see it in the Dashboard, the seller added it during onboarding, and it has been sitting there for months. It is an Australian bank account, the balance is in dollars, and there is no arrangement under which one settles the other.",
"short_answer": """<p>Payouts settle per currency. A balance bucket in <code>usd</code> needs an external account whose <code>currency</code> is <code>usd</code> <em>and</em> which is marked <code>default_for_currency</code>. Read <code>GET /v1/accounts/{id}/external_accounts?limit=100</code> and check for both conditions against the account's <code>default_currency</code>; a bank account in the wrong currency is not a partial answer, it is no answer.</p>
<p>Before blaming the bank details, check the route is legal at all. <code>GET /v1/country_specs/{platform_country}</code> returns <code>supported_transfer_countries</code> and <code>supported_bank_account_currencies</code>. If the connected account's <code>country</code> is not in the first list, no external account of any currency will make the transfer work.</p>""",
"problem": """<p>The error message is unusually good and still gets misread, because it names a currency rather than a bank account and the person reading it is looking straight at a bank account. So the first attempt at a fix is to re-enter the same account and routing numbers, which changes nothing, and the second is to add a second bank account in the same wrong currency, which also changes nothing.</p>
<p>The version of this that costs the most is the one where the corridor is not supported. Somebody spends a fortnight collecting bank details from a seller in a country the platform cannot pay out to, and every one of those details is correct. There is no field to fix. The account needed a different payout arrangement from the day it was created, and nothing on the account object says so.</p>""",
"why": """<p><strong>Stripe will not convert to reach a destination.</strong> A USD balance goes to a USD bank account. There is no implicit FX at payout time, so a destination in another currency is not a worse option than the right one, it is not an option.</p>
<p><strong><code>default_for_currency</code> is the field that actually decides which destination is used.</strong> Adding a correctly denominated bank account is only half the change. Until one of them is flagged as the default for that currency, automatic payouts have nothing to target and the balance sits exactly where it was. This is why a first attempt at the fix often appears to do nothing.</p>
<p><strong>Country and currency are two different constraints.</strong> <code>supported_transfer_countries</code> says where the platform may send money at all. <code>supported_bank_account_currencies</code> says which currencies a bank account in a given country can hold. An account can pass the first and fail the second, and the repair is different: the first needs a different payout product, the second needs a different bank.</p>
<p><strong>Recipients on the recipient service agreement are excluded from cross-border payouts entirely.</strong> That is a property of how the account was created, not something a bank account can satisfy, and it produces exactly the same unhelpful symptom as a wrong-currency destination.</p>""",
"steps": [
 {"h": "Check the corridor before you check the bank details",
  "body": """<p>One <code>GET /v1/country_specs/{platform_country}</code> for the whole run. If the connected account's <code>country</code> is missing from <code>supported_transfer_countries</code>, stop: collecting bank details is wasted work and telling the seller their details are wrong is worse than wasted.</p>"""},
 {"h": "Compare each destination's currency against default_currency",
  "body": """<p><code>GET /v1/accounts/{id}/external_accounts?limit=100</code>. Match on the <code>currency</code> field of each bank account. Report the currencies that <em>are</em> present alongside the one that is needed, because that single line usually explains the whole thing to whoever is reading it.</p>"""},
 {"h": "Treat a matching but unflagged destination as its own finding",
  "body": """<p>A USD bank account with <code>default_for_currency</code> false is a different problem from having no USD bank account, and it has a one-line fix. Collapsing the two into "currency problem" sends someone to collect details that are already on the account.</p>"""},
 {"h": "Check the currency is one that country can bank in",
  "body": """<p><code>supported_bank_account_currencies</code> maps each currency to the countries whose bank accounts may hold it. A destination country that cannot hold the settlement currency is a dead end no matter how many times the details are re-entered.</p>"""},
 {"h": "Separate this from a balance stuck in a second currency",
  "body": """<p>This note is about the account's own <code>default_currency</code> having no way out. A residual balance in some other currency that no payout will ever drain is a related but distinct problem, covered in <a href="/stripe/stranded-currency-balance/">a second-currency balance bucket can never be paid out</a>.</p>"""},
],
"verify": """<p>Re-run the script. Every account should report <code>settles</code>, meaning a destination exists in the settlement currency and is flagged as the default for it.</p>
<pre><code class="language-bash">python3 stripe_settlement_currency.py
# 412 account(s): 412 settling, 0 blocked</code></pre>""",
"code_intro": "Three read-only calls: the platform account for its country, one country spec for the corridor rules, and the external accounts for each connected account. The classifier is pure and takes all three facts at once, because the order of the checks is the useful part &mdash; an unsupported corridor has to be reported before a currency mismatch, since in that case the currency is not what is wrong and collecting a new bank account cannot help.",
"py_file": "stripe_settlement_currency.py",
"py": '''"""Report connected accounts with no external account able to settle their balance.

Read only. Three kinds of GET and no writes: give this a RESTRICTED key with read
access to Connected accounts and External accounts. The repair is printed, never
performed, because this script holds a credential to a live payments account.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("stripe_settlement_currency")

API = "https://api.stripe.com/v1"


def verdict(account, external_accounts, spec=None):
    """Classify one account's settlement path. Pure, so the order is testable.

    `spec` is the platform's country spec, or None to skip the corridor checks.
    Returns (state, detail). The corridor is checked first on purpose: when the
    route is not supported, the currency is not what is wrong and no external
    account will fix it, so reporting a currency mismatch there is misleading.
    """
    country = account.get("country")
    currency = (account.get("default_currency") or "").lower()
    accounts = external_accounts or []

    if not currency:
        return ("unknown", "the account has no default_currency to settle in")

    if spec:
        transferable = spec.get("supported_transfer_countries")
        if transferable is not None and country not in transferable:
            return ("unsupported-corridor",
                    "%s is not in this platform's supported_transfer_countries; no "
                    "bank account of any currency makes this payout legal" % country)
        bankable = spec.get("supported_bank_account_currencies")
        if bankable is not None and country not in (bankable.get(currency) or []):
            return ("unbankable-currency",
                    "a bank account in %s cannot hold %s under this country spec"
                    % (country, currency.upper()))

    if not accounts:
        return ("no-destination",
                "no external account at all, so no payout is ever attempted")

    matching = [e for e in accounts
                if (e.get("currency") or "").lower() == currency]
    if not matching:
        held = sorted({(e.get("currency") or "?").lower() for e in accounts})
        return ("currency-missing",
                "settles in %s but the only destination(s) are %s"
                % (currency.upper(), ", ".join(c.upper() for c in held)))
    if not any(e.get("default_for_currency") for e in matching):
        return ("not-default",
                "a %s destination exists but none is default_for_currency, so "
                "automatic payouts have no target" % currency.upper())
    return ("settles", "%s destination present and default_for_currency" % currency.upper())


def get(session, path, account=None, **params):
    headers = {"Stripe-Account": account} if account else None
    r = session.get(API + path, params=params, headers=headers, timeout=30)
    if r.status_code == 401:
        raise SystemExit("401 from Stripe: the key is wrong, or is for the other mode")
    r.raise_for_status()
    return r.json()


def paginate(session, path, limit):
    """Walk a list endpoint, stopping once `limit` objects have been yielded."""
    seen = 0
    params = {"limit": 100}
    while True:
        page = get(session, path, **params)
        data = page.get("data", [])
        for obj in data:
            yield obj
            seen += 1
            if seen >= limit:
                return
        if not page.get("has_more") or not data:
            return
        params["starting_after"] = data[-1]["id"]


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--max-accounts", type=int, default=500,
                    help="stop after this many connected accounts")
    ap.add_argument("--skip-country-spec", action="store_true",
                    help="skip the corridor checks and only compare currencies")
    args = ap.parse_args()

    key = os.environ.get("STRIPE_API_KEY")
    if not key:
        log.error("set STRIPE_API_KEY (use a restricted, read-only key)")
        return 2

    s = requests.Session()
    s.headers.update({"Authorization": "Bearer " + key})

    spec = None
    if not args.skip_country_spec:
        platform = get(s, "/account")
        spec = get(s, "/country_specs/%s" % platform.get("country", "US"))
        log.info("platform in %s, %d transfer country/countries supported",
                 platform.get("country"),
                 len(spec.get("supported_transfer_countries") or []))

    total = settling = blocked = 0
    for acct in paginate(s, "/accounts", args.max_accounts):
        total += 1
        externals = get(s, "/accounts/%s/external_accounts" % acct["id"],
                        limit=100).get("data", [])
        state, detail = verdict(acct, externals, spec)
        line = "%-21s %s  %s" % (state, acct["id"], detail)
        if state == "settles":
            settling += 1
            continue
        blocked += 1
        log.warning(line)
        if state == "not-default":
            log.warning("  repair: POST %s/accounts/%s/external_accounts/{ba_id} with "
                        "default_for_currency=true", API, acct["id"])
        elif state in ("currency-missing", "no-destination", "unbankable-currency"):
            log.warning("  repair: POST %s/accounts/%s with an external_account token "
                        "in %s, then flag it default_for_currency=true",
                        API, acct["id"], (acct.get("default_currency") or "?").upper())
        elif state == "unsupported-corridor":
            log.warning("  repair: none by API. Move this recipient to Global Payouts "
                        "or a locally acquiring platform account.")

    log.info("%d account(s): %d settling, %d blocked", total, settling, blocked)
    return 1 if blocked else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "stripe-settlement-currency.mjs",
"js": '''/**
 * Report connected accounts with no external account able to settle their balance.
 *
 * Read only. Three kinds of GET and no writes: give this a RESTRICTED key with
 * read access to Connected accounts and External accounts. The repair is printed,
 * never performed.
 */
const API = 'https://api.stripe.com/v1';

/**
 * Classify one account's settlement path. Pure, so the order of the checks is
 * testable. `spec` is the platform's country spec, or null to skip the corridor.
 */
export function verdict(account, externalAccounts, spec = null) {
  const country = account.country;
  const currency = (account.default_currency ?? '').toLowerCase();
  const accounts = externalAccounts ?? [];

  if (!currency) return ['unknown', 'the account has no default_currency to settle in'];

  if (spec) {
    const transferable = spec.supported_transfer_countries;
    if (transferable && !transferable.includes(country)) {
      return ['unsupported-corridor',
        `${country} is not in this platform's supported_transfer_countries; no bank ` +
        'account of any currency makes this payout legal'];
    }
    const bankable = spec.supported_bank_account_currencies;
    if (bankable && !(bankable[currency] ?? []).includes(country)) {
      return ['unbankable-currency',
        `a bank account in ${country} cannot hold ${currency.toUpperCase()} under ` +
        'this country spec'];
    }
  }

  if (accounts.length === 0) {
    return ['no-destination', 'no external account at all, so no payout is ever attempted'];
  }

  const matching = accounts.filter(
    (e) => (e.currency ?? '').toLowerCase() === currency);
  if (matching.length === 0) {
    const held = [...new Set(accounts.map((e) => (e.currency ?? '?').toUpperCase()))].sort();
    return ['currency-missing',
      `settles in ${currency.toUpperCase()} but the only destination(s) are ` +
      held.join(', ')];
  }
  if (!matching.some((e) => e.default_for_currency)) {
    return ['not-default',
      `a ${currency.toUpperCase()} destination exists but none is ` +
      'default_for_currency, so automatic payouts have no target'];
  }
  return ['settles',
    `${currency.toUpperCase()} destination present and default_for_currency`];
}

async function get(key, path, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
  if (res.status === 401) {
    throw new Error('401 from Stripe: the key is wrong, or is for the other mode');
  }
  if (!res.ok) throw new Error(`${res.status} from ${url.pathname}`);
  return res.json();
}

async function* paginate(key, path, limit) {
  let seen = 0;
  const params = { limit: 100 };
  for (;;) {
    const page = await get(key, path, params);
    const data = page.data ?? [];
    for (const obj of data) {
      yield obj;
      if (++seen >= limit) return;
    }
    if (!page.has_more || data.length === 0) return;
    params.starting_after = data[data.length - 1].id;
  }
}

async function main() {
  const key = process.env.STRIPE_API_KEY;
  if (!key) {
    console.error('set STRIPE_API_KEY (use a restricted, read-only key)');
    process.exitCode = 2;
    return;
  }

  let spec = null;
  if (!process.argv.includes('--skip-country-spec')) {
    const platform = await get(key, '/account');
    spec = await get(key, `/country_specs/${platform.country ?? 'US'}`);
    console.log(`platform in ${platform.country}, ` +
                `${(spec.supported_transfer_countries ?? []).length} transfer ` +
                'country/countries supported');
  }

  let total = 0, settling = 0, blocked = 0;
  for await (const acct of paginate(key, '/accounts', 500)) {
    total += 1;
    const { data: externals = [] } =
      await get(key, `/accounts/${acct.id}/external_accounts`, { limit: 100 });
    const [state, detail] = verdict(acct, externals, spec);
    if (state === 'settles') { settling += 1; continue; }
    blocked += 1;
    console.warn(`${state.padEnd(21)} ${acct.id}  ${detail}`);
    if (state === 'not-default') {
      console.warn(`  repair: POST ${API}/accounts/${acct.id}/external_accounts/` +
                   '{ba_id} with default_for_currency=true');
    } else if (['currency-missing', 'no-destination', 'unbankable-currency'].includes(state)) {
      console.warn(`  repair: POST ${API}/accounts/${acct.id} with an ` +
                   `external_account token in ` +
                   `${(acct.default_currency ?? '?').toUpperCase()}, then flag it ` +
                   'default_for_currency=true');
    } else if (state === 'unsupported-corridor') {
      console.warn('  repair: none by API. Move this recipient to Global Payouts or ' +
                   'a locally acquiring platform account.');
    }
  }

  console.log(`${total} account(s): ${settling} settling, ${blocked} blocked`);
  process.exitCode = blocked ? 1 : 0;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing key, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Ordering is the thing under test. An account in an unsupported corridor <em>also</em> has a currency mismatch, and reporting the mismatch sends someone to collect bank details that can never work; the corridor check has to win. The other case worth pinning is the destination in the right currency with <code>default_for_currency</code> false, which is a one-line fix that looks identical to the expensive one if the two are collapsed.",
"test_py_file": "test_stripe_settlement_currency.py",
"test_py": '''from stripe_settlement_currency import verdict

US_SPEC = {
    "supported_transfer_countries": ["US", "GB", "DE"],
    "supported_bank_account_currencies": {"usd": ["US"], "gbp": ["GB"], "eur": ["DE"]},
}
US = {"country": "US", "default_currency": "usd"}


def test_a_matching_default_destination_settles():
    externals = [{"currency": "usd", "default_for_currency": True}]
    assert verdict(US, externals, US_SPEC)[0] == "settles"


def test_a_matching_destination_that_is_not_the_default_is_its_own_finding():
    # One flag away from working, and nothing to collect from the seller.
    state, detail = verdict(US, [{"currency": "usd", "default_for_currency": False}],
                            US_SPEC)
    assert state == "not-default"
    assert "default_for_currency" in detail


def test_a_wrong_currency_destination_names_what_is_actually_attached():
    state, detail = verdict(US, [{"currency": "aud", "default_for_currency": True}],
                            US_SPEC)
    assert state == "currency-missing"
    assert "AUD" in detail
    assert "USD" in detail


def test_no_destination_at_all_is_separate_from_a_wrong_one():
    assert verdict(US, [], US_SPEC)[0] == "no-destination"


def test_an_unsupported_corridor_outranks_the_currency_check():
    # Both are true for this account. Reporting the currency sends someone to
    # collect bank details that cannot be made to work.
    acct = {"country": "BR", "default_currency": "brl"}
    state, detail = verdict(acct, [{"currency": "aud"}], US_SPEC)
    assert state == "unsupported-corridor"
    assert "BR" in detail


def test_a_country_that_cannot_hold_the_currency_is_reported_as_such():
    acct = {"country": "GB", "default_currency": "usd"}
    assert verdict(acct, [{"currency": "gbp"}], US_SPEC)[0] == "unbankable-currency"


def test_the_corridor_checks_are_skipped_without_a_spec():
    acct = {"country": "BR", "default_currency": "brl"}
    externals = [{"currency": "brl", "default_for_currency": True}]
    assert verdict(acct, externals, None)[0] == "settles"


def test_a_missing_default_currency_is_not_silently_settling():
    assert verdict({"country": "US"}, [{"currency": "usd"}], None)[0] == "unknown"
''',
"test_js_file": "stripe-settlement-currency.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { verdict } from './stripe-settlement-currency.mjs';

const US_SPEC = {
  supported_transfer_countries: ['US', 'GB', 'DE'],
  supported_bank_account_currencies: { usd: ['US'], gbp: ['GB'], eur: ['DE'] },
};
const US = { country: 'US', default_currency: 'usd' };

test('a matching default destination settles', () => {
  const externals = [{ currency: 'usd', default_for_currency: true }];
  assert.equal(verdict(US, externals, US_SPEC)[0], 'settles');
});

test('a matching destination that is not the default is its own finding', () => {
  const [state, detail] = verdict(
    US, [{ currency: 'usd', default_for_currency: false }], US_SPEC);
  assert.equal(state, 'not-default');
  assert.match(detail, /default_for_currency/);
});

test('a wrong currency destination names what is actually attached', () => {
  const [state, detail] = verdict(
    US, [{ currency: 'aud', default_for_currency: true }], US_SPEC);
  assert.equal(state, 'currency-missing');
  assert.match(detail, /AUD/);
  assert.match(detail, /USD/);
});

test('no destination at all is separate from a wrong one', () => {
  assert.equal(verdict(US, [], US_SPEC)[0], 'no-destination');
});

test('an unsupported corridor outranks the currency check', () => {
  const acct = { country: 'BR', default_currency: 'brl' };
  const [state, detail] = verdict(acct, [{ currency: 'aud' }], US_SPEC);
  assert.equal(state, 'unsupported-corridor');
  assert.match(detail, /BR/);
});

test('a country that cannot hold the currency is reported as such', () => {
  const acct = { country: 'GB', default_currency: 'usd' };
  assert.equal(verdict(acct, [{ currency: 'gbp' }], US_SPEC)[0], 'unbankable-currency');
});

test('the corridor checks are skipped without a spec', () => {
  const acct = { country: 'BR', default_currency: 'brl' };
  const externals = [{ currency: 'brl', default_for_currency: true }];
  assert.equal(verdict(acct, externals, null)[0], 'settles');
});

test('a missing default_currency is not silently settling', () => {
  assert.equal(verdict({ country: 'US' }, [{ currency: 'usd' }], null)[0], 'unknown');
});
''',
"faq": [
 ("Why does Stripe say I have no external accounts in that currency when one is attached?",
  "Because the attached one is denominated in a different currency. Payouts settle per currency and Stripe does not convert to reach a destination, so a bank account in AUD cannot receive a USD balance. The message is about the currency of the destination, not its existence."),
 ("What does default_for_currency actually do?",
  "It nominates which destination automatic payouts use for a given currency. Adding a correctly denominated bank account without setting it leaves the balance where it is, which is why a first attempt at this fix often appears to have done nothing."),
 ("How do I know whether the payout is even allowed?",
  "GET /v1/country_specs/{platform_country}. If the connected account's country is not in supported_transfer_countries, the route is not available to that platform and no bank account will change it. supported_bank_account_currencies then says which currencies a bank account in each country can hold."),
 ("What do I do about an unsupported corridor?",
  "Nothing through this API. The recipient needs a different arrangement: Global Payouts, or a platform account that acquires locally in that country. Collecting more bank details from the seller is wasted effort and reads to them as your product being broken."),
 ("Is this the same as a balance stuck in a second currency?",
  "No. This is the account's own default_currency having no settlement path. A residual balance in an unrelated currency that no payout will drain is a separate problem with a separate fix, and an account can have both at once."),
],
"related": [
 ("/stripe/no-external-account-attached/", "A connected account has no external account to pay out to"),
 ("/stripe/stranded-currency-balance/", "A second-currency balance bucket can never be paid out"),
 ("/stripe/payouts-failing-bank-rejection/", "Payouts fail with account_closed and nobody is watching"),
],
"citations": [CITE_COUNTRY_SPEC, CITE_CROSS_BORDER, CITE_EXTERNAL_ACCOUNT, CITE_ACCOUNT_OBJ],
},

]
