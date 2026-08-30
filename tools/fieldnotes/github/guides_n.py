#!/usr/bin/env python3
"""/github/ field notes, batch N — the writing.

Four notes about ceilings and volumes: two where a number is smaller than the
reader assumed, and two where a number is very much larger.

The first is a rate limit that was never going to be the one on the page. An
App installation does not get a flat 5,000 an hour; it gets a ceiling that
grows with the size of the installation, and an installation pinned to a
handful of selected repositories never earns the growth. This is not the note
about draining an hourly window, which is published already. It is about the
size of the bucket before anybody starts drawing from it.

The second is an identifier treated as a constant. Installation ids are not
stable across an uninstall and a reinstall, so a value pasted out of a URL two
years ago either stops resolving or, worse, still resolves and belongs to
somebody else. The script never mints a token, because minting is a write; it
reads the list of installations the App can actually see and diffs it against
what the configuration believes.

The third reads the delivery feed that an existing note already reads, and
deliberately reads a different column. That note counts failures by status
code. This one ignores status codes almost entirely and looks at duration
against a fixed ten-second cutoff, including on the deliveries that succeeded,
because a receiver about to start timing out looks perfectly healthy in a
failure count right up until the week it does not.

The fourth has no failure in it at all. A hook subscribed to the wildcard works
exactly as designed and costs volume: every event GitHub has, plus every event
GitHub ships next year, delivered to a receiver that discards most of them
after paying to verify each signature. The finding is a fraction, and the
repair is a list the script can print in full.

Read only throughout. Two of these four scripts could give a much better answer
if they were allowed one write each, and neither gets one.
"""

CITE_RATE_LIMITS = ("Rate limits for the REST API — GitHub Docs",
                    "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")
CITE_RATE_ENDPOINT = ("Rate limit — GitHub REST API",
                      "https://docs.github.com/en/rest/rate-limit/rate-limit")
CITE_INSTALLATIONS = ("Installations — GitHub REST API",
                      "https://docs.github.com/en/rest/apps/installations")
CITE_INSTALL_AUTH = ("Authenticating as a GitHub App installation — GitHub Docs",
                     "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation")
CITE_APP_AUTH = ("Authenticating as a GitHub App — GitHub Docs",
                 "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app")
CITE_APPS_REST = ("Apps — GitHub REST API",
                  "https://docs.github.com/en/rest/apps/apps")
CITE_TROUBLESHOOT = ("Troubleshooting webhooks — GitHub Docs",
                     "https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/troubleshooting-webhooks")
CITE_FAILED_DELIVERIES = ("Handling failed webhook deliveries — GitHub Docs",
                          "https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries")
CITE_REPO_HOOKS = ("Repository webhooks — GitHub REST API",
                   "https://docs.github.com/en/rest/repos/webhooks")
CITE_WEBHOOK_BEST = ("Best practices for using webhooks — GitHub Docs",
                     "https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks")
CITE_WEBHOOK_EVENTS = ("Webhook events and payloads — GitHub Docs",
                       "https://docs.github.com/en/webhooks/webhook-events-and-payloads")
CITE_CREATING_WEBHOOKS = ("Creating webhooks — GitHub Docs",
                          "https://docs.github.com/en/webhooks/using-webhooks/creating-webhooks")

GUIDES = [

{
"slug": "app-rate-limit-not-scaling",
"title": "The App's rate limit never grew with the installation",
"description": "An App installation's hourly ceiling scales with the repositories and users it covers. A narrow installation stays at 5,000 however big the org is.",
"h1": "the App's rate limit never grew with the installation",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app rate limit 5000 not scaling",
             "github app installation rate limit 12500",
             "github app rate limit repositories users",
             "installation access token rate limit org size",
             "github app rate limit enterprise cloud 15000"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The App serves an organization with four hundred repositories, and it throttles like a personal access token. Somebody quotes the number they remember &mdash; Apps get more, Apps scale with the installation, we will be fine at this volume &mdash; and the plan was built on it. <code>GET /rate_limit</code> says <code>5000</code>, the same as the laptop script it replaced.",
"short_answer": """<p>An App installation's hourly ceiling is not a flat number. It starts at 5,000 and grows with the size of the installation: an installation covering more than twenty repositories earns extra requests per repository beyond that, and one covering more than twenty users earns extra per user, to a maximum of 12,500 an hour. Organizations on GitHub Enterprise Cloud get a flat 15,000 instead.</p>
<p>The growth is earned by the <em>installation</em>, not by the organization. An installation with <code>repository_selection: "selected"</code> pointed at nine repositories inside a four-hundred-repository org is a nine-repository installation as far as the ceiling is concerned, and it will sit at 5,000 forever. So the number to compare is not your usage against your limit; it is your limit against the limit an installation of this shape is entitled to. When those two agree, the ceiling is real and the answer is to make fewer requests. When they disagree, the installation is narrower than you think it is.</p>""",
"problem": """<p>The capacity plan was written against a number nobody read from the API. Apps scale is true enough to repeat and vague enough to be useless, and it gets turned into a spreadsheet where the ceiling is 12,500, the poll is every five minutes, and the whole thing fits with room to spare. Nothing in the plan is checkable until the integration is live, and by then the number that matters has already been decided by a checkbox on an installation screen.</p>
<p>Then it throttles, and the investigation goes to the wrong place. Everybody looks at usage, because usage is what a rate-limit problem is usually about: the drain per minute, the process that woke up and burnt three thousand calls, the poll interval that is too aggressive. All of that analysis is competent and none of it explains anything, because the usage is exactly what the plan predicted. It is the denominator that is wrong.</p>
<p>The fix that gets tried first is caching or backing off, which helps and does not resolve the confusion, because the ceiling stays stubbornly at the number a single-user token gets. There is a persistent suspicion that the App is somehow not authenticating as an App at all &mdash; that the token is a user token, or the JWT flow is broken &mdash; and that suspicion sends a week into the auth code, which is fine. A 5,000 ceiling on an installation token is not a sign of broken authentication. It is a sign of a small installation.</p>""",
"why": """<p><strong>The ceiling is a function of installation size.</strong> The baseline for an organization installation is 5,000 requests an hour. Beyond twenty repositories, each additional repository in the installation adds to the ceiling; beyond twenty users in the account, each additional user does the same. The sum is capped at 12,500 an hour. This is why two Apps doing identical work against the same organization can have ceilings two and a half times apart: one is installed on everything and one on a shortlist.</p>
<p><strong>A selected installation does not count the repositories it cannot see.</strong> <code>repository_selection</code> is either <code>all</code> or <code>selected</code>, and when it is <code>selected</code> the installation's size is the length of that selection. Adding repositories to the org does nothing. This is the whole mechanism, and it is invisible from inside the App, because the App's own view of the world is the selection.</p>
<p><strong>Enterprise Cloud replaces the formula rather than extending it.</strong> An installation on an Enterprise Cloud organization gets 15,000 an hour flat. That is above the 12,500 cap, so it is not reachable by widening an ordinary installation, and seeing exactly 15,000 tells you which kind of account you are on without asking anybody.</p>
<p><strong>This is not the same problem as running out.</strong> Draining an hourly window is a usage problem with an arithmetic answer, and it has <a href="/github/rate-limit-core-exhausted/">its own note</a>. This one is upstream of that: the window you are draining is the wrong size, and no amount of care with the drain will change it. The two look identical in production &mdash; 403s and an exhausted bucket &mdash; and they have completely different repairs.</p>
<p><strong>Half the formula is not readable from here, so the answer is a floor.</strong> A read-only installation token can count the repositories it reaches. It usually cannot count the members of the organization, which requires org-level read. Since the user term only ever <em>adds</em> to the ceiling, an entitlement computed from repositories alone is a lower bound: if the measured limit is already below that bound, the finding stands regardless of the member count. The script says which half it could see rather than presenting a guess as a calculation.</p>""",
"steps": [
 {"h": "Read the ceiling instead of quoting it",
  "body": """<p><code>GET /rate_limit</code> with the installation token, and look at <code>resources.core.limit</code> &mdash; the limit, not the remaining. That endpoint does not count against the quota it reports, so this check is free and can run on every deploy. Write the number down; it is the only figure in the conversation that is not somebody's recollection.</p>"""},
 {"h": "Ask the installation how big it is",
  "body": """<p><code>GET /installation/repositories?per_page=1</code> returns <code>total_count</code> and <code>repository_selection</code> without fetching a page of repositories. A <code>selected</code> installation with a small count and a 5,000 ceiling is the finding in one line. An <code>all</code> installation with a small count means the account really is small, and the ceiling is honest.</p>"""},
 {"h": "Compute what an installation of that shape earns",
  "body": """<p>Baseline 5,000, plus the per-repository and per-user increments above twenty of each, capped at 12,500; or 15,000 flat on Enterprise Cloud. Compare against the measured limit. Equal means the ceiling is correct and the repair is on the usage side. Measured below entitled means something about the installation is narrower than the size you fed in.</p>"""},
 {"h": "Turn the ceiling into a repository budget before you widen anything",
  "body": """<p>Divide the ceiling by the calls your loop makes per repository per hour. That gives the number of repositories the integration can actually service, which is the number worth arguing about in a planning meeting. Widening the installation raises both sides of that fraction &mdash; more repositories to service, and a higher ceiling &mdash; so it is not automatically a win, and the arithmetic says which way it falls.</p>"""},
 {"h": "Prefer spending fewer requests to earning more of them",
  "body": """<p>Widening an installation to buy quota is a bad trade if the App does not need the reach: it is more access than the job requires, for at most two and a half times the requests. Conditional requests, a larger <code>per_page</code>, and one GraphQL query in place of a fan-out of REST calls all move the same needle without asking an owner for more of their organization.</p>"""},
],
"verify": """<p>After the installation is widened to all repositories, or after the plan is rewritten against the real ceiling, the same free read confirms it.</p>
<pre><code class="language-bash">GITHUB_INSTALLATION_TOKEN=$INSTALL_TOKEN python3 github_app_limit_ceiling.py --calls-per-repo 12
# core ceiling: 5000/hour, graphql 5000/hour
# installation: repository_selection=selected, 9 repository/repositories reachable
# narrow-installation: the ceiling is 5000/hour, and an installation covering
# 400 repositories would be entitled to at least 12500/hour
# budget: 5000/hour serves 416 repositories at 12 call(s) each

# after widening the installation to all repositories
# scaled: the ceiling is 12500/hour, which matches an installation this size</code></pre>""",
"code_intro": "Two GETs, one of them free, and everything after them is arithmetic that can be tested without a network. The entitlement function is the centre of it: baseline, two increments that only start above twenty, a cap, and an Enterprise Cloud branch that replaces the sum rather than adding to it. It takes an unknown user count as zero on purpose, which makes its answer a floor rather than an estimate, and the verdict is careful never to claim a shortfall it computed from a number it could not read.",
"py_file": "github_app_limit_ceiling.py",
"py": '''"""Say whether a GitHub App installation has the rate-limit ceiling it earns.

Read only. Two GETs: the rate-limit endpoint, which does not consume quota, and
a one-item page of the installation's repositories, which is the cheapest way to
learn how big the installation is. Nothing is minted, widened or changed.

An installation's hourly ceiling starts at 5,000 and grows with the number of
repositories and users the installation covers, to a maximum of 12,500; an
Enterprise Cloud organization gets a flat 15,000 instead. An installation
restricted to a handful of selected repositories never earns the growth, so a
large organization behind a narrow installation throttles at the same ceiling a
single user gets.

This is not the note about draining an hourly window. It is about the size of
the window before anything draws from it.

Environment:

    GITHUB_INSTALLATION_TOKEN   an installation access token
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_app_limit_ceiling")

API = "https://api.github.com"
UA = "github-app-limit-ceiling/1.0"

# The documented shape of the ceiling. Kept as named constants because every one
# of them turns up in the output, and a reader comparing the script against the
# documentation should be able to find them in one place.
BASELINE = 5000
PER_UNIT = 50
SCALING_FLOOR = 20
FREE_CEILING = 12500
ENTERPRISE_CEILING = 15000
ANONYMOUS = 60


def entitled(repositories, users=None, enterprise=False):
    """The hourly ceiling an installation of this size earns. Pure.

    users is allowed to be None, because a read-only installation token usually
    cannot count the members of an organization. The user term only ever adds,
    so treating an unknown count as zero makes the result a lower bound rather
    than a guess: a measured limit below this number is a real shortfall
    whatever the true membership is.
    """
    if enterprise:
        return ENTERPRISE_CEILING
    try:
        repos = int(repositories or 0)
    except (TypeError, ValueError):
        repos = 0
    try:
        people = int(users or 0)
    except (TypeError, ValueError):
        people = 0
    extra = max(0, repos - SCALING_FLOOR) + max(0, people - SCALING_FLOOR)
    return min(FREE_CEILING, BASELINE + PER_UNIT * extra)


def is_lower_bound(users):
    """Whether the entitlement was computed without the user term. Pure."""
    return users is None


def classify_ceiling(limit):
    """Name the ceiling a credential was actually given. Pure.

    The names matter more than the numbers downstream, because the repair for a
    ceiling that sits at the floor and the repair for one already at the cap are
    opposite pieces of advice.
    """
    try:
        value = int(limit)
    except (TypeError, ValueError):
        return "unknown"
    if value == ANONYMOUS:
        return "unauthenticated"
    if value == ENTERPRISE_CEILING:
        return "enterprise"
    if value == FREE_CEILING:
        return "at-cap"
    if value == BASELINE:
        return "baseline"
    if BASELINE < value < FREE_CEILING:
        return "scaled"
    return "unknown"


def selection_of(view):
    """The repository_selection on an installation view, normalised. Pure."""
    if not isinstance(view, dict):
        return "unknown"
    raw = str(view.get("repository_selection") or "").strip().lower()
    return raw if raw in ("all", "selected") else "unknown"


def reachable(view):
    """How many repositories the installation covers, or None. Pure."""
    if not isinstance(view, dict):
        return None
    raw = view.get("total_count")
    if raw is None:
        return None
    try:
        return int(raw)
    except (TypeError, ValueError):
        return None


def shortfall(limit, entitlement):
    """Requests an hour the installation is not getting, or 0. Pure."""
    try:
        have, earned = int(limit), int(entitlement)
    except (TypeError, ValueError):
        return 0
    return max(0, earned - have)


def sustainable_repos(limit, calls_per_repo):
    """How many repositories a loop of this cost fits under the ceiling. Pure."""
    try:
        ceiling, cost = int(limit), int(calls_per_repo)
    except (TypeError, ValueError):
        return None
    if cost <= 0:
        return None
    return ceiling // cost


def verdict(limit, selection, covered, account_repos=None, users=None,
            enterprise=False, installation_seen=True):
    """Turn the two reads into a finding. Pure.

    covered is the size of the installation. account_repos, where the caller
    could learn it, is the size of the account behind the installation: the
    difference between those two is what makes a narrow installation narrow.
    """
    klass = classify_ceiling(limit)
    if klass == "unauthenticated":
        return ("unauthenticated",
                "the ceiling is 60/hour, which is the anonymous ceiling. This "
                "credential is not reaching GitHub as an installation at all.")
    if not installation_seen:
        return ("not-an-installation",
                "the ceiling is %s/hour and the installation endpoint did not "
                "answer, so this is a user or Actions credential rather than an "
                "installation token. Installation scaling does not apply to it."
                % limit)
    if klass == "enterprise":
        return ("enterprise",
                "the ceiling is 15000/hour, the flat Enterprise Cloud ceiling. "
                "Widening the installation cannot raise it further.")
    earned = entitled(account_repos if account_repos is not None else covered,
                      users, enterprise)
    if klass == "at-cap":
        return ("at-cap",
                "the ceiling is 12500/hour, the maximum outside Enterprise "
                "Cloud. There is no more to earn: spend fewer requests.")
    gap = shortfall(limit, earned)
    if gap and selection == "selected":
        return ("narrow-installation",
                "the ceiling is %s/hour, and an installation covering %s "
                "repositories would be entitled to at least %d/hour. The "
                "selection is what is capping it, not the account."
                % (limit, account_repos if account_repos is not None else covered,
                   earned))
    if gap:
        return ("below-entitlement",
                "the ceiling is %s/hour against an entitlement of at least "
                "%d/hour for this size. The installation is narrower than the "
                "size used for the comparison." % (limit, earned))
    if klass == "baseline":
        return ("baseline",
                "the ceiling is 5000/hour and the installation covers %s "
                "repositories, which is too few to earn any scaling. This "
                "ceiling is real: the repair is on the usage side."
                % covered)
    return ("scaled",
            "the ceiling is %s/hour, which matches an installation this size."
            % limit)


def repair(state, covered=None, account_repos=None):
    """The sentence a reader has to act on. Pure."""
    if state == "narrow-installation":
        return ("widen the installation to all repositories if the App "
                "legitimately needs org-wide reach, which raises the ceiling as "
                "a side effect. If it does not, keep the narrow selection and "
                "cut request volume instead: conditional requests, a bigger "
                "per_page, one GraphQL query for a fan-out of REST calls.")
    if state in ("at-cap", "enterprise", "baseline"):
        return ("nothing on the installation. This ceiling is the one you get, "
                "so the only lever left is spending fewer requests per unit of "
                "work.")
    if state == "unauthenticated":
        return ("send the installation access token in the Authorization "
                "header. Nothing about scaling matters while the requests are "
                "arriving anonymously.")
    if state == "not-an-installation":
        return ("point the check at an installation access token. A user token "
                "gets a flat 5000 and never scales, so comparing it against an "
                "installation entitlement is meaningless.")
    if state == "below-entitlement":
        return ("check repository_selection and the account behind the "
                "installation before widening anything: the numbers disagree "
                "for a reason this script could not see.")
    return "nothing."


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def core_limits(session):
    """The core and graphql ceilings from the free rate-limit endpoint."""
    status, body = get(session, "/rate_limit")
    if status != 200 or not isinstance(body, dict):
        log.error("GET /rate_limit returned %d", status)
        return None, None
    resources = body.get("resources") or {}
    core = (resources.get("core") or {}).get("limit")
    graphql = (resources.get("graphql") or {}).get("limit")
    return core, graphql


def installation_view(session):
    """total_count and repository_selection, without fetching repositories."""
    status, body = get(session, "/installation/repositories?per_page=1")
    if status != 200 or not isinstance(body, dict):
        return None
    return body


def account_size(session, org):
    """Repositories on the account behind the installation, where readable."""
    if not org:
        return None
    status, body = get(session, "/orgs/%s" % org)
    if status != 200 or not isinstance(body, dict):
        log.info("GET /orgs/%s returned %d; the account size is not readable "
                 "from here, so the comparison uses the installation size",
                 org, status)
        return None
    public = body.get("public_repos") or 0
    private = body.get("total_private_repos") or 0
    try:
        return int(public) + int(private)
    except (TypeError, ValueError):
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--org", default=os.environ.get("GITHUB_ORG"),
                    help="the account behind the installation, to size it")
    ap.add_argument("--users", type=int, default=None,
                    help="members of that account, if you know it; the API "
                         "rarely tells a read-only installation token")
    ap.add_argument("--calls-per-repo", type=int, default=10,
                    help="calls your loop makes per repository per hour")
    ap.add_argument("--enterprise", action="store_true",
                    help="the account is on GitHub Enterprise Cloud")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_INSTALLATION_TOKEN")
    if not token:
        log.error("set GITHUB_INSTALLATION_TOKEN to an installation access "
                  "token. A user token has a flat ceiling and nothing here "
                  "applies to it")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    core, graphql = core_limits(session)
    if core is None:
        return 2
    log.info("core ceiling: %s/hour, graphql %s/hour", core, graphql)

    view = installation_view(session)
    covered = reachable(view)
    selection = selection_of(view)
    if view is None:
        log.info("the installation endpoint did not answer for this token")
    else:
        log.info("installation: repository_selection=%s, %s repository/"
                 "repositories reachable", selection, covered)

    org_repos = account_size(session, args.org) if selection == "selected" else None
    state, detail = verdict(core, selection, covered, org_repos, args.users,
                            args.enterprise, installation_seen=view is not None)
    log.info("%s: %s", state, detail)
    log.info("repair: %s", repair(state, covered, org_repos))

    fits = sustainable_repos(core, args.calls_per_repo)
    if fits is not None:
        log.info("budget: %s/hour serves %d repositories at %d call(s) each",
                 core, fits, args.calls_per_repo)

    print(json.dumps({
        "core_limit": core,
        "graphql_limit": graphql,
        "repository_selection": selection,
        "repositories_covered": covered,
        "account_repositories": org_repos,
        "entitlement_is_lower_bound": is_lower_bound(args.users),
        "entitled": entitled(org_repos if org_repos is not None else covered,
                             args.users, args.enterprise),
        "ceiling_class": classify_ceiling(core),
        "state": state,
        "detail": detail,
        "repositories_supported": fits,
    }, indent=2, default=str))
    return 1 if state in ("narrow-installation", "below-entitlement",
                          "unauthenticated") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-app-limit-ceiling.mjs",
"js": '''/**
 * Say whether a GitHub App installation has the rate-limit ceiling it earns.
 *
 * Read only. Two GETs: the rate-limit endpoint, which does not consume quota,
 * and a one-item page of the installation's repositories. Nothing is minted,
 * widened or changed.
 *
 * Environment:
 *   GITHUB_INSTALLATION_TOKEN  an installation access token
 *   GITHUB_ORG                 optional, the account behind the installation
 */
const API = 'https://api.github.com';
const UA = 'github-app-limit-ceiling/1.0';

/** The documented shape of the ceiling. */
export const BASELINE = 5000;
export const PER_UNIT = 50;
export const SCALING_FLOOR = 20;
export const FREE_CEILING = 12500;
export const ENTERPRISE_CEILING = 15000;
export const ANONYMOUS = 60;

/**
 * The hourly ceiling an installation of this size earns. Pure.
 * users may be null: the user term only adds, so an unknown count makes the
 * answer a lower bound rather than a guess.
 */
export function entitled(repositories, users = null, enterprise = false) {
  if (enterprise) return ENTERPRISE_CEILING;
  const repos = Number.isFinite(Number(repositories)) ? Number(repositories) : 0;
  const people = Number.isFinite(Number(users)) ? Number(users) : 0;
  const extra = Math.max(0, repos - SCALING_FLOOR) + Math.max(0, people - SCALING_FLOOR);
  return Math.min(FREE_CEILING, BASELINE + PER_UNIT * extra);
}

/** Whether the entitlement was computed without the user term. Pure. */
export function isLowerBound(users) {
  return users === null || users === undefined;
}

/** Name the ceiling a credential was actually given. Pure. */
export function classifyCeiling(limit) {
  const value = Number(limit);
  if (!Number.isFinite(value)) return 'unknown';
  if (value === ANONYMOUS) return 'unauthenticated';
  if (value === ENTERPRISE_CEILING) return 'enterprise';
  if (value === FREE_CEILING) return 'at-cap';
  if (value === BASELINE) return 'baseline';
  if (value > BASELINE && value < FREE_CEILING) return 'scaled';
  return 'unknown';
}

/** The repository_selection on an installation view, normalised. Pure. */
export function selectionOf(view) {
  if (!view || typeof view !== 'object') return 'unknown';
  const raw = String(view.repository_selection ?? '').trim().toLowerCase();
  return ['all', 'selected'].includes(raw) ? raw : 'unknown';
}

/** How many repositories the installation covers, or null. Pure. */
export function reachable(view) {
  if (!view || typeof view !== 'object') return null;
  const raw = view.total_count;
  if (raw === null || raw === undefined) return null;
  const n = Number(raw);
  return Number.isFinite(n) ? Math.trunc(n) : null;
}

/** Requests an hour the installation is not getting, or 0. Pure. */
export function shortfall(limit, entitlement) {
  const num = (v) => (v === null || v === undefined || v === '' ? NaN : Number(v));
  const have = num(limit);
  const earned = num(entitlement);
  if (!Number.isFinite(have) || !Number.isFinite(earned)) return 0;
  return Math.max(0, earned - have);
}

/** How many repositories a loop of this cost fits under the ceiling. Pure. */
export function sustainableRepos(limit, callsPerRepo) {
  const ceiling = Number(limit);
  const cost = Number(callsPerRepo);
  if (!Number.isFinite(ceiling) || !Number.isFinite(cost) || cost <= 0) return null;
  return Math.floor(ceiling / cost);
}

/** Turn the two reads into a finding. Pure. */
export function verdict(limit, selection, covered, accountRepos = null,
                        users = null, enterprise = false, installationSeen = true) {
  const klass = classifyCeiling(limit);
  if (klass === 'unauthenticated') {
    return ['unauthenticated',
      'the ceiling is 60/hour, which is the anonymous ceiling. This credential '
      + 'is not reaching GitHub as an installation at all.'];
  }
  if (!installationSeen) {
    return ['not-an-installation',
      `the ceiling is ${limit}/hour and the installation endpoint did not `
      + 'answer, so this is a user or Actions credential rather than an '
      + 'installation token. Installation scaling does not apply to it.'];
  }
  if (klass === 'enterprise') {
    return ['enterprise',
      'the ceiling is 15000/hour, the flat Enterprise Cloud ceiling. Widening '
      + 'the installation cannot raise it further.'];
  }
  const size = accountRepos === null || accountRepos === undefined ? covered : accountRepos;
  const earned = entitled(size, users, enterprise);
  if (klass === 'at-cap') {
    return ['at-cap',
      'the ceiling is 12500/hour, the maximum outside Enterprise Cloud. There '
      + 'is no more to earn: spend fewer requests.'];
  }
  const gap = shortfall(limit, earned);
  if (gap && selection === 'selected') {
    return ['narrow-installation',
      `the ceiling is ${limit}/hour, and an installation covering ${size} `
      + `repositories would be entitled to at least ${earned}/hour. The `
      + 'selection is what is capping it, not the account.'];
  }
  if (gap) {
    return ['below-entitlement',
      `the ceiling is ${limit}/hour against an entitlement of at least `
      + `${earned}/hour for this size. The installation is narrower than the `
      + 'size used for the comparison.'];
  }
  if (klass === 'baseline') {
    return ['baseline',
      `the ceiling is 5000/hour and the installation covers ${covered} `
      + 'repositories, which is too few to earn any scaling. This ceiling is '
      + 'real: the repair is on the usage side.'];
  }
  return ['scaled', `the ceiling is ${limit}/hour, which matches an installation this size.`];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state) {
  if (state === 'narrow-installation') {
    return 'widen the installation to all repositories if the App legitimately '
      + 'needs org-wide reach, which raises the ceiling as a side effect. If it '
      + 'does not, keep the narrow selection and cut request volume instead: '
      + 'conditional requests, a bigger per_page, one GraphQL query for a '
      + 'fan-out of REST calls.';
  }
  if (['at-cap', 'enterprise', 'baseline'].includes(state)) {
    return 'nothing on the installation. This ceiling is the one you get, so '
      + 'the only lever left is spending fewer requests per unit of work.';
  }
  if (state === 'unauthenticated') {
    return 'send the installation access token in the Authorization header. '
      + 'Nothing about scaling matters while the requests are arriving anonymously.';
  }
  if (state === 'not-an-installation') {
    return 'point the check at an installation access token. A user token gets '
      + 'a flat 5000 and never scales, so comparing it against an installation '
      + 'entitlement is meaningless.';
  }
  if (state === 'below-entitlement') {
    return 'check repository_selection and the account behind the installation '
      + 'before widening anything: the numbers disagree for a reason this '
      + 'script could not see.';
  }
  return 'nothing.';
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function get(token, path) {
  const res = await fetch(API + path, { headers: headers(token) });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function main() {
  const token = process.env.GITHUB_INSTALLATION_TOKEN;
  if (!token) {
    console.error('set GITHUB_INSTALLATION_TOKEN to an installation access token');
    process.exitCode = 2;
    return;
  }
  const org = process.env.GITHUB_ORG || null;
  const callsPerRepo = Number(process.env.GITHUB_CALLS_PER_REPO || 10);

  const rate = await get(token, '/rate_limit');
  if (rate.status !== 200 || !rate.body) {
    console.error(`GET /rate_limit returned ${rate.status}`);
    process.exitCode = 2;
    return;
  }
  const resources = rate.body.resources || {};
  const core = (resources.core || {}).limit;
  const graphql = (resources.graphql || {}).limit;
  console.log(`core ceiling: ${core}/hour, graphql ${graphql}/hour`);

  const inst = await get(token, '/installation/repositories?per_page=1');
  const view = inst.status === 200 ? inst.body : null;
  const covered = reachable(view);
  const selection = selectionOf(view);
  if (view) {
    console.log(`installation: repository_selection=${selection}, ${covered} reachable`);
  }

  let orgRepos = null;
  if (org && selection === 'selected') {
    const o = await get(token, `/orgs/${org}`);
    if (o.status === 200 && o.body) {
      orgRepos = Number(o.body.public_repos || 0) + Number(o.body.total_private_repos || 0);
    } else {
      console.log(`GET /orgs/${org} returned ${o.status}; using the installation size`);
    }
  }

  const [state, detail] = verdict(core, selection, covered, orgRepos, null,
    false, view !== null);
  console.log(`${state}: ${detail}`);
  console.log(`repair: ${repair(state)}`);
  const fits = sustainableRepos(core, callsPerRepo);
  if (fits !== null) {
    console.log(`budget: ${core}/hour serves ${fits} repositories at ${callsPerRepo} call(s) each`);
  }
  console.log(JSON.stringify({
    core_limit: core,
    graphql_limit: graphql,
    repository_selection: selection,
    repositories_covered: covered,
    account_repositories: orgRepos,
    entitlement_is_lower_bound: isLowerBound(null),
    state,
    repositories_supported: fits,
  }, null, 2));
  process.exitCode = ['narrow-installation', 'below-entitlement', 'unauthenticated']
    .includes(state) ? 1 : 0;
}

// Guarded so importing this file from the test runner does not start a run and
// fail the suite even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The entitlement function gets the most attention, because every wrong answer downstream starts there: the increments must not begin below twenty of either kind, the two of them must add rather than compete, the cap must bind, and Enterprise Cloud must replace the sum instead of extending it. After that, the distinction the script exists to make &mdash; a 5,000 ceiling on a nine-repository installation is honest, and the same ceiling on a four-hundred-repository account is the finding &mdash; plus the refusal to treat an unknown user count as a reason to soften either answer.",
"test_py_file": "test_github_app_limit_ceiling.py",
"test_py": '''from github_app_limit_ceiling import (
    classify_ceiling, entitled, is_lower_bound, reachable, repair,
    selection_of, shortfall, sustainable_repos, verdict,
)

WIDE = {"total_count": 400, "repository_selection": "all"}
NARROW = {"total_count": 9, "repository_selection": "selected"}


def test_nothing_scales_below_twenty_of_either_kind():
    assert entitled(0, 0) == 5000
    assert entitled(20, 20) == 5000
    assert entitled(19, 19) == 5000


def test_repositories_and_users_both_add():
    assert entitled(21, 0) == 5050
    assert entitled(0, 21) == 5050
    assert entitled(21, 21) == 5100


def test_the_cap_binds_outside_enterprise_cloud():
    assert entitled(1000, 1000) == 12500
    assert entitled(400, None) == 12500


def test_enterprise_replaces_the_sum_rather_than_extending_it():
    assert entitled(0, 0, enterprise=True) == 15000
    assert entitled(5000, 5000, enterprise=True) == 15000


def test_an_unknown_user_count_makes_the_answer_a_floor():
    assert entitled(30, None) == entitled(30, 0)
    assert entitled(30, 40) > entitled(30, None)
    assert is_lower_bound(None)
    assert not is_lower_bound(0)


def test_each_ceiling_has_a_name():
    assert classify_ceiling(60) == "unauthenticated"
    assert classify_ceiling(5000) == "baseline"
    assert classify_ceiling(7200) == "scaled"
    assert classify_ceiling(12500) == "at-cap"
    assert classify_ceiling(15000) == "enterprise"
    assert classify_ceiling(None) == "unknown"


def test_the_installation_view_is_read_defensively():
    assert selection_of(NARROW) == "selected"
    assert selection_of({"repository_selection": "ALL "}) == "all"
    assert selection_of({}) == "unknown"
    assert selection_of(None) == "unknown"
    assert reachable(WIDE) == 400
    assert reachable({"total_count": None}) is None
    assert reachable(None) is None


def test_a_small_installation_at_five_thousand_is_honest():
    state, detail = verdict(5000, "all", 9)
    assert state == "baseline"
    assert "repair is on the usage side" in detail


def test_a_narrow_installation_on_a_big_account_is_the_finding():
    state, detail = verdict(5000, "selected", 9, account_repos=400)
    assert state == "narrow-installation"
    assert "12500" in detail
    assert "selection is what is capping it" in detail


def test_a_scaled_ceiling_that_matches_its_size_is_not_a_finding():
    assert verdict(entitled(60, None), "all", 60)[0] == "scaled"


def test_the_cap_and_enterprise_are_never_reported_as_shortfalls():
    assert verdict(12500, "selected", 900, account_repos=4000)[0] == "at-cap"
    assert verdict(15000, "all", 4000)[0] == "enterprise"


def test_an_anonymous_ceiling_is_not_an_installation_problem():
    state, _ = verdict(60, "unknown", None, installation_seen=False)
    assert state == "unauthenticated"


def test_a_credential_with_no_installation_view_is_named_as_such():
    state, detail = verdict(5000, "unknown", None, installation_seen=False)
    assert state == "not-an-installation"
    assert "user or Actions credential" in detail


def test_the_shortfall_never_goes_negative():
    assert shortfall(12500, 5000) == 0
    assert shortfall(5000, 12500) == 7500
    assert shortfall(None, 12500) == 0


def test_the_budget_divides_the_ceiling_by_the_loop():
    assert sustainable_repos(12500, 10) == 1250
    assert sustainable_repos(5000, 12) == 416
    assert sustainable_repos(5000, 0) is None


def test_the_repair_for_a_real_ceiling_does_not_suggest_widening():
    assert "widen" not in repair("baseline")
    assert "widen the installation" in repair("narrow-installation")
''',
"test_js_file": "github-app-limit-ceiling.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classifyCeiling, entitled, isLowerBound, reachable, repair,
  selectionOf, shortfall, sustainableRepos, verdict,
} from './github-app-limit-ceiling.mjs';

const WIDE = { total_count: 400, repository_selection: 'all' };
const NARROW = { total_count: 9, repository_selection: 'selected' };

test('nothing scales below twenty of either kind', () => {
  assert.equal(entitled(0, 0), 5000);
  assert.equal(entitled(20, 20), 5000);
  assert.equal(entitled(19, 19), 5000);
});

test('repositories and users both add', () => {
  assert.equal(entitled(21, 0), 5050);
  assert.equal(entitled(0, 21), 5050);
  assert.equal(entitled(21, 21), 5100);
});

test('the cap binds outside Enterprise Cloud', () => {
  assert.equal(entitled(1000, 1000), 12500);
  assert.equal(entitled(400, null), 12500);
});

test('enterprise replaces the sum rather than extending it', () => {
  assert.equal(entitled(0, 0, true), 15000);
  assert.equal(entitled(5000, 5000, true), 15000);
});

test('an unknown user count makes the answer a floor', () => {
  assert.equal(entitled(30, null), entitled(30, 0));
  assert.ok(entitled(30, 40) > entitled(30, null));
  assert.ok(isLowerBound(null));
  assert.ok(!isLowerBound(0));
});

test('each ceiling has a name', () => {
  assert.equal(classifyCeiling(60), 'unauthenticated');
  assert.equal(classifyCeiling(5000), 'baseline');
  assert.equal(classifyCeiling(7200), 'scaled');
  assert.equal(classifyCeiling(12500), 'at-cap');
  assert.equal(classifyCeiling(15000), 'enterprise');
  assert.equal(classifyCeiling(null), 'unknown');
});

test('the installation view is read defensively', () => {
  assert.equal(selectionOf(NARROW), 'selected');
  assert.equal(selectionOf({ repository_selection: 'ALL ' }), 'all');
  assert.equal(selectionOf({}), 'unknown');
  assert.equal(selectionOf(null), 'unknown');
  assert.equal(reachable(WIDE), 400);
  assert.equal(reachable({ total_count: null }), null);
  assert.equal(reachable(null), null);
});

test('a small installation at five thousand is honest', () => {
  const [state, detail] = verdict(5000, 'all', 9);
  assert.equal(state, 'baseline');
  assert.match(detail, /repair is on the usage side/);
});

test('a narrow installation on a big account is the finding', () => {
  const [state, detail] = verdict(5000, 'selected', 9, 400);
  assert.equal(state, 'narrow-installation');
  assert.match(detail, /12500/);
  assert.match(detail, /selection is what is capping it/);
});

test('a scaled ceiling that matches its size is not a finding', () => {
  assert.equal(verdict(entitled(60, null), 'all', 60)[0], 'scaled');
});

test('the cap and enterprise are never reported as shortfalls', () => {
  assert.equal(verdict(12500, 'selected', 900, 4000)[0], 'at-cap');
  assert.equal(verdict(15000, 'all', 4000)[0], 'enterprise');
});

test('an anonymous ceiling is not an installation problem', () => {
  assert.equal(verdict(60, 'unknown', null, null, null, false, false)[0], 'unauthenticated');
});

test('a credential with no installation view is named as such', () => {
  const [state, detail] = verdict(5000, 'unknown', null, null, null, false, false);
  assert.equal(state, 'not-an-installation');
  assert.match(detail, /user or Actions credential/);
});

test('the shortfall never goes negative', () => {
  assert.equal(shortfall(12500, 5000), 0);
  assert.equal(shortfall(5000, 12500), 7500);
  assert.equal(shortfall(null, 12500), 0);
});

test('the budget divides the ceiling by the loop', () => {
  assert.equal(sustainableRepos(12500, 10), 1250);
  assert.equal(sustainableRepos(5000, 12), 416);
  assert.equal(sustainableRepos(5000, 0), null);
});

test('the repair for a real ceiling does not suggest widening', () => {
  assert.ok(!repair('baseline').includes('widen'));
  assert.match(repair('narrow-installation'), /widen the installation/);
});
''',
"faq": [
 ("How is this different from the note about running out of quota?",
  "That note is about the drain: how fast you are spending the hour you have, and when the bucket empties. This one is about the size of the bucket. They produce the same production symptom, a wall of 403s with an exhausted core resource, and the repairs have nothing in common. If your ceiling is the one an installation of your size earns, the drain note is the one you want. If your ceiling is 5,000 while the installation covers a large organization, spending less will only postpone the problem you actually have."),
 ("Does widening the installation always help?",
  "No, and the arithmetic is worth doing before anybody asks an owner for more access. Widening raises the ceiling and it also raises the amount of work, because there are now more repositories to poll, watch and reconcile. Divide the ceiling by the calls your loop makes per repository per hour, before and after. If the ratio gets worse, widening bought you a bigger number and a smaller margin, and you have also taken more access than the App needs, which is its own cost."),
 ("Why can the script not read the number of users?",
  "Because counting the members of an organization needs org-level read, and a read-only installation token scoped to repositories does not have it. The script computes the entitlement from the repository term alone and labels the result a lower bound. That is enough to be useful: the user term only adds, so a measured ceiling below the repository-only entitlement is a genuine shortfall no membership figure can explain away. It is not enough to predict the exact ceiling you would get after widening, and the script does not pretend otherwise."),
 ("We see exactly 15,000. Is that a scaled installation?",
  "No, it is the flat Enterprise Cloud ceiling, and it is above the 12,500 cap that ordinary scaling stops at. Seeing it is a useful fact in itself: it tells you which kind of account the installation sits on without asking anybody, and it tells you that widening cannot buy any more requests. The only lever left at that point is the number of requests per unit of work."),
 ("Our GitHub Actions job gets 1,000 an hour. Does any of this apply?",
  "None of it. The token Actions injects is a different class of credential with its own repository-scoped pool, and it does not scale with anything. Comparing it against an installation entitlement produces a shortfall that is not real. The script notices when the installation endpoint does not answer for the credential it was given and says so rather than running the comparison anyway."),
],
"related": [
 ("/github/rate-limit-core-exhausted/", "The core hourly quota is exhausted"),
 ("/github/installation-repository-selection-partial/", "An installation that covers only some repositories"),
 ("/github/no-conditional-requests/", "Polling without ETags spends full quota"),
],
"citations": [CITE_RATE_LIMITS, CITE_RATE_ENDPOINT, CITE_INSTALLATIONS, CITE_INSTALL_AUTH],
},

{
"slug": "app-installation-id-hardcoded",
"title": "A hardcoded installation id stops matching reality",
"description": "Installation ids are not stable across a reinstall. A stored id either stops resolving or still resolves and belongs to a different account.",
"h1": "a hardcoded installation id stops matching reality",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app installation id changes on reinstall",
             "404 app installations access_tokens installation id",
             "get github app installation id at runtime",
             "github app wrong organization installation id",
             "orgs org installation endpoint current id"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The installation id was copied out of a settings URL in 2024 and pasted into an environment variable, where it has sat ever since. Last Tuesday an admin at one customer uninstalled the App during a security review and put it straight back, which they were entitled to do and which nobody told you about. Since then the token call for that customer has returned <code>404</code>, and the error says nothing about installations.",
"short_answer": """<p>Installation ids are not stable identifiers. Uninstalling and reinstalling an App produces a <em>new</em> installation, with a new id; the old id refers to a record that no longer exists, and the endpoint that mints a token for it answers 404. Any configuration that stores the id once and never re-reads it breaks on the next reinstall, which is an event you do not control and do not get told about.</p>
<p>Read <code>GET /app/installations</code> with the App's JWT. It lists every installation the App currently has, with <code>id</code>, <code>account.login</code>, <code>repository_selection</code> and <code>created_at</code>. If your configured id is not on that list it is stale. If it <em>is</em> on the list but sits against a different account than the one your configuration files it under, that is the worse case and the one worth checking for: the integration is not failing, it is working against somebody else's organization. The durable repair is to stop storing the id at all &mdash; resolve it per account from <code>GET /orgs/{org}/installation</code>, or take it from <code>installation.id</code> on the incoming webhook &mdash; and to key your own state on the account login, which does not change when an App is reinstalled.</p>""",
"problem": """<p>The 404 does not mention installations, so the search starts in the wrong place. A 404 from the token endpoint reads as a routing problem or a permissions problem, and the first hour goes into the private key, the JWT, the clock, the header. All of it is fine. The request is well formed and correctly signed, and it is asking about a record that was deleted.</p>
<p>Meanwhile the id looks like the most trustworthy thing in the configuration. It is a number, it has been there for two years, it is in the runbook, and it worked this morning. Nobody suspects a constant. The change that broke it happened in an organization you have no visibility into, was made by somebody exercising a documented right, and left no trace in your systems at all except the failure.</p>
<p>The quiet version is worse and nobody looks for it. If a stale id is reused, or if a configuration file has drifted &mdash; staging's id in production, two customers' entries transposed during an onboarding &mdash; the id still resolves. Tokens mint, calls succeed, and every request goes to the wrong organization. There is no error to alert on, because from the API's point of view nothing is wrong. The only signal is that the account behind the id is not the account you think it is, and the only way to see it is to look.</p>""",
"why": """<p><strong>An installation is a record, not a relationship.</strong> Uninstalling deletes the record. Reinstalling creates a new one, with a new id, new timestamps and a fresh grant. The App and the account are the same, the connection between them is a different object, and nothing carries over. That is why the id is the wrong thing to persist: it names an instance of a relationship rather than the relationship.</p>
<p><strong>The failure mode is asymmetric.</strong> A stale id fails loudly and immediately, which is annoying and survivable. A <em>crossed</em> id &mdash; one that resolves to an account other than the one it is filed under &mdash; does not fail at all. Everything is 200. The damage is that the integration reads, and in a writing integration writes, against the wrong organization. A check that only asks does my id still work will never find it, so the check has to compare the id against the account.</p>
<p><strong>The account login is the stable key.</strong> Logins can be renamed, but the account id and the login both survive an uninstall and a reinstall, while the installation id does not. Keying stored state on the installation id means a reinstall silently orphans everything you knew about that customer; keying it on the account means a reinstall is a change of one field.</p>
<p><strong>The current id is one GET away, per account.</strong> <code>GET /orgs/{org}/installation</code> with the JWT returns the installation for that organization as it exists right now, and the equivalent routes exist for users and repositories. Resolving at runtime costs one cheap request that can be cached for the life of the process, which is a good trade against a configuration value that goes wrong without telling you.</p>
<p><strong>The webhook already carries it.</strong> Every App webhook payload includes an <code>installation</code> object with the id on it. An integration that reacts to events rather than polling never needs to look the id up: the delivery that woke it names the installation it concerns, and that value is correct by construction because GitHub just used it.</p>""",
"steps": [
 {"h": "List what the App can actually see",
  "body": """<p><code>GET /app/installations</code> with the App's JWT, paginated. That is the authoritative set: every installation the App has right now, each with its id, its account and when it was created. Everything else in this check is a comparison against this list.</p>"""},
 {"h": "Look up each configured id twice",
  "body": """<p>Once by id, to see whether it exists. Once by account, to see what the current id for that account is. The two lookups answer different questions, and running only the first is how a crossed id survives an audit: it exists, so the check passes, and it belongs to somebody else.</p>"""},
 {"h": "Treat an account mismatch as the serious finding",
  "body": """<p>An id that resolves to a different account than the one it is filed under should stop a deploy, not raise a ticket. Nothing about it fails on its own, so there is no second chance to notice. The script reports it first and separately from the stale ones for exactly that reason.</p>"""},
 {"h": "Compare created_at against when the id was recorded",
  "body": """<p>An installation whose <code>created_at</code> is newer than the date you wrote the id down is a reinstall, whether or not the id happens to still match. That is the early warning: it tells you a customer removed and re-added the App, which is worth knowing even in the cases where nothing broke.</p>"""},
 {"h": "Stop storing the id",
  "body": """<p>Resolve it from <code>GET /orgs/{org}/installation</code> at startup, or take it from <code>installation.id</code> on the webhook that triggered the work, and cache it in memory rather than in configuration. Key stored state on the account login. After that a reinstall is an event your integration handles by continuing to work.</p>"""},
],
"verify": """<p>Once the ids are resolved at runtime, the same audit reports every configured account as current, and keeps doing so through the next reinstall without anybody editing anything.</p>
<pre><code class="language-bash">GITHUB_APP_JWT=$(python3 sign_app_jwt.py) \\
  GITHUB_INSTALLATION_MAP='acme-corp=41234567,beta-inc=41234568' \\
  python3 github_installation_id_drift.py
# 12 installation(s) visible to this App
# stale: acme-corp is configured as 41234567, which this App no longer has.
# The current installation for acme-corp is 55120044, created 2026-08-25T08:02:11Z
# crossed: beta-inc is configured as 41234568, which exists and belongs to
# gamma-labs. Nothing about this fails: it works against the wrong account.
# repair: resolve the id per account at runtime, and key stored state on the login

# after the resolution moves into the code
# current: acme-corp resolves to 55120044</code></pre>""",
"code_intro": "One paginated GET builds the authoritative list, and one optional GET per account confirms it from the other direction. Everything else is two dictionaries and a careful comparison: ids are matched as text because they arrive from environment variables and JSON files as often as from the API, logins are matched case-insensitively because GitHub treats them that way, and the four outcomes are kept apart deliberately. The endpoint that mints an installation token is a write and is not called here, so the script never reproduces the 404 that started the investigation; it explains it.",
"py_file": "github_installation_id_drift.py",
"py": '''"""Find configured GitHub App installation ids that no longer mean what they did.

Read only. One paginated GET over the App's own installations with the App JWT,
and one optional GET per configured account. Nothing is minted or changed. The
endpoint that mints an installation access token is a write, so this script does
not call it and never reproduces the 404 that usually starts the investigation.

Installation ids are not stable. Uninstalling and reinstalling an App creates a
new installation with a new id, so an id copied out of a URL once either stops
resolving or, if it was transposed or reused, resolves against an account that
is not the one your configuration believes.

Environment:

    GITHUB_APP_JWT           the JWT your own signing code produced
    GITHUB_INSTALLATION_MAP  account=id pairs, comma separated, or a JSON object
    GITHUB_MAP_RECORDED_AT   optional ISO date the map was last written
"""
import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_installation_id_drift")

API = "https://api.github.com"
UA = "github-installation-id-drift/1.0"

# The one finding that never announces itself. A stale id 404s on the next call;
# a crossed id succeeds forever against the wrong organization, so it is ordered
# first in every report this script prints.
SILENT = ("crossed",)


def parse_map(text):
    """account=id pairs, or a JSON object, into a plain dict. Pure.

    Accepts both because this value lives in an environment variable in some
    deployments and in a config file in others, and a checker that only reads
    one of the two shapes gets skipped in half of them.
    """
    raw = str(text or "").strip()
    if not raw:
        return {}
    if raw.startswith("{"):
        try:
            loaded = json.loads(raw)
        except ValueError:
            return {}
        return {str(k).strip().lower(): str(v).strip()
                for k, v in loaded.items() if str(k).strip()}
    out = {}
    for chunk in raw.replace(";", ",").split(","):
        if "=" not in chunk:
            continue
        account, _, ident = chunk.partition("=")
        account, ident = account.strip().lower(), ident.strip()
        if account and ident:
            out[account] = ident
    return out


def account_of(inst):
    """The login of the account an installation sits on. Pure."""
    if not isinstance(inst, dict):
        return None
    account = inst.get("account")
    if isinstance(account, dict) and account.get("login"):
        return str(account["login"])
    return None


def stable_key(inst):
    """The value worth keying stored state on. Pure.

    The login rather than the installation id, lowercased so the same account
    written two ways is one key. This is the whole recommendation of the note,
    expressed as a function so it can be tested rather than only asserted.
    """
    login = account_of(inst)
    return login.lower() if login else None


def index_by_id(installations):
    """Installations by their id, as text. Pure."""
    out = {}
    for inst in installations or []:
        if isinstance(inst, dict) and inst.get("id") is not None:
            out[str(inst["id"]).strip()] = inst
    return out


def index_by_account(installations):
    """Installations by lowercased account login. Pure."""
    out = {}
    for inst in installations or []:
        key = stable_key(inst)
        if key:
            out[key] = inst
    return out


def current_id_for(account, by_account):
    """The id this account's installation has right now, or None. Pure."""
    inst = (by_account or {}).get(str(account or "").strip().lower())
    return str(inst["id"]) if isinstance(inst, dict) and inst.get("id") is not None else None


def parse_moment(text):
    """An ISO 8601 timestamp as an aware datetime, or None. Pure."""
    raw = str(text or "").strip()
    if not raw:
        return None
    if raw.endswith("Z"):
        raw = raw[:-1] + "+00:00"
    try:
        when = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return when if when.tzinfo else when.replace(tzinfo=timezone.utc)


def reinstalled_since(inst, recorded_at):
    """Whether this installation was created after the map was written. Pure.

    None when either date is unreadable, which is a third answer rather than a
    False: not knowing is not the same as knowing nothing happened.
    """
    created = parse_moment((inst or {}).get("created_at") if isinstance(inst, dict) else None)
    recorded = parse_moment(recorded_at)
    if created is None or recorded is None:
        return None
    return created > recorded


def drift(account, configured_id, by_id, by_account, recorded_at=None):
    """Compare one configured pair against reality. Pure."""
    account = str(account or "").strip()
    wanted = str(configured_id or "").strip()
    listed = (by_id or {}).get(wanted)
    current = current_id_for(account, by_account)

    if listed is not None:
        owner = account_of(listed) or ""
        if owner.lower() != account.lower():
            return ("crossed",
                    "%s is configured as %s, which exists and belongs to %s. "
                    "Nothing about this fails: it works against the wrong "
                    "account." % (account, wanted, owner or "another account"))
        fresh = reinstalled_since(listed, recorded_at)
        if fresh:
            return ("current-but-reinstalled",
                    "%s still resolves to %s, and that installation was created "
                    "after the map was written, so the App was removed and "
                    "re-added at some point." % (account, wanted))
        return ("current", "%s resolves to %s." % (account, wanted))

    if current is not None:
        created = (by_account.get(account.lower()) or {}).get("created_at")
        return ("stale",
                "%s is configured as %s, which this App no longer has. The "
                "current installation for %s is %s%s."
                % (account, wanted, account, current,
                   ", created %s" % created if created else ""))
    return ("gone",
            "%s is configured as %s and this App has no installation on that "
            "account at all. It was uninstalled and not put back."
            % (account, wanted))


def unmapped(by_account, configured):
    """Accounts the App is installed on that the configuration omits. Pure."""
    known = {str(k).strip().lower() for k in (configured or {})}
    return sorted(k for k in (by_account or {}) if k not in known)


def summarize(findings):
    """Counts by state, with the silent finding pulled out. Pure."""
    counts = {}
    for f in findings or []:
        counts[f["state"]] = counts.get(f["state"], 0) + 1
    return {"total": len(findings or []), "by_state": counts,
            "silent": sum(counts.get(s, 0) for s in SILENT)}


def repair(state, account=None, current=None):
    """The sentence a reader has to act on. Pure."""
    if state == "crossed":
        return ("stop the deploy. The id filed under %s belongs to another "
                "account, so every call made with it lands on the wrong "
                "organization and nothing will ever error. Fix the mapping, "
                "then resolve the id at runtime so it cannot drift again."
                % (account or "this account"))
    if state == "stale":
        return ("resolve the id per account from the org's own installation "
                "route rather than storing it. The current id is %s today and "
                "will be a different one after the next reinstall."
                % (current or "on the list above"))
    if state == "gone":
        return ("the App is not installed on %s. This is not an id problem: "
                "somebody has to install it again, and your code should key "
                "state on the account login so the history survives."
                % (account or "that account"))
    if state == "current-but-reinstalled":
        return ("nothing is broken, but the id changed hands once already. "
                "Move the lookup into the code before it changes again.")
    return "nothing. This account resolves correctly."


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    url = API + path if path.startswith("/") else path
    r = session.get(url, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body


def list_installations(session, pages=10):
    """Every installation this App currently has. Read only."""
    out = []
    for page in range(1, pages + 1):
        status, body = get(session, "/app/installations?per_page=100&page=%d" % page)
        if status != 200 or not isinstance(body, list):
            if page == 1:
                log.error("GET /app/installations returned %d; this endpoint "
                          "wants the App's JWT", status)
            break
        out.extend(body)
        if len(body) < 100:
            break
    return out


def confirm_account(session, account):
    """The current installation for one organization, straight from the API."""
    status, body = get(session, "/orgs/%s/installation" % account)
    if status != 200 or not isinstance(body, dict):
        return None
    return str(body.get("id")) if body.get("id") is not None else None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--map", default=os.environ.get("GITHUB_INSTALLATION_MAP", ""),
                    help="account=id pairs, comma separated, or a JSON object")
    ap.add_argument("--recorded-at", default=os.environ.get("GITHUB_MAP_RECORDED_AT"),
                    help="ISO date the map was last written, to spot reinstalls")
    ap.add_argument("--confirm", action="store_true",
                    help="also resolve each account's current id directly")
    args = ap.parse_args()

    jwt = os.environ.get("GITHUB_APP_JWT")
    if not jwt:
        log.error("set GITHUB_APP_JWT. The installation list is read with the "
                  "App's JWT, not with a token minted from an installation")
        return 2

    configured = parse_map(args.map)
    if not configured:
        log.error("no account=id pairs to check; pass --map or set "
                  "GITHUB_INSTALLATION_MAP")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + jwt,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    installations = list_installations(session)
    log.info("%d installation(s) visible to this App", len(installations))
    by_id = index_by_id(installations)
    by_account = index_by_account(installations)

    findings = []
    for account, ident in sorted(configured.items()):
        state, detail = drift(account, ident, by_id, by_account, args.recorded_at)
        row = {"account": account, "configured_id": ident, "state": state,
               "detail": detail, "current_id": current_id_for(account, by_account)}
        if args.confirm:
            row["confirmed_id"] = confirm_account(session, account)
        findings.append(row)

    findings.sort(key=lambda f: (f["state"] not in SILENT, f["account"]))
    for f in findings:
        if f["state"] != "current":
            log.info("%s: %s", f["state"], f["detail"])
            log.info("repair: %s", repair(f["state"], f["account"], f["current_id"]))

    extra = unmapped(by_account, configured)
    if extra:
        log.info("also installed and not in the map: %s", ", ".join(extra))

    stats = summarize(findings)
    print(json.dumps({"visible": len(installations), "summary": stats,
                      "unmapped_accounts": extra, "findings": findings},
                     indent=2, default=str))
    return 1 if stats["by_state"].get("current", 0) != stats["total"] else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-installation-id-drift.mjs",
"js": '''/**
 * Find configured GitHub App installation ids that no longer mean what they did.
 *
 * Read only. One paginated GET over the App's own installations with the App
 * JWT, and one optional GET per configured account. The endpoint that mints an
 * installation access token is a write and is not called here.
 *
 * Environment:
 *   GITHUB_APP_JWT           the JWT your own signing code produced
 *   GITHUB_INSTALLATION_MAP  account=id pairs, comma separated, or a JSON object
 *   GITHUB_MAP_RECORDED_AT   optional ISO date the map was last written
 */
const API = 'https://api.github.com';
const UA = 'github-installation-id-drift/1.0';

/** The finding that never announces itself. */
export const SILENT = ['crossed'];

/** account=id pairs, or a JSON object, into a plain object. Pure. */
export function parseMap(text) {
  const raw = String(text ?? '').trim();
  if (!raw) return {};
  if (raw.startsWith('{')) {
    let loaded;
    try { loaded = JSON.parse(raw); } catch { return {}; }
    const out = {};
    for (const [k, v] of Object.entries(loaded || {})) {
      const key = String(k).trim().toLowerCase();
      if (key) out[key] = String(v).trim();
    }
    return out;
  }
  const out = {};
  for (const chunk of raw.replace(/;/g, ',').split(',')) {
    const at = chunk.indexOf('=');
    if (at < 0) continue;
    const account = chunk.slice(0, at).trim().toLowerCase();
    const ident = chunk.slice(at + 1).trim();
    if (account && ident) out[account] = ident;
  }
  return out;
}

/** The login of the account an installation sits on. Pure. */
export function accountOf(inst) {
  if (!inst || typeof inst !== 'object') return null;
  const account = inst.account;
  if (account && typeof account === 'object' && account.login) return String(account.login);
  return null;
}

/** The value worth keying stored state on. Pure. */
export function stableKey(inst) {
  const login = accountOf(inst);
  return login ? login.toLowerCase() : null;
}

/** Installations by their id, as text. Pure. */
export function indexById(installations) {
  const out = {};
  for (const inst of installations || []) {
    if (inst && typeof inst === 'object' && inst.id !== null && inst.id !== undefined) {
      out[String(inst.id).trim()] = inst;
    }
  }
  return out;
}

/** Installations by lowercased account login. Pure. */
export function indexByAccount(installations) {
  const out = {};
  for (const inst of installations || []) {
    const key = stableKey(inst);
    if (key) out[key] = inst;
  }
  return out;
}

/** The id this account's installation has right now, or null. Pure. */
export function currentIdFor(account, byAccount) {
  const inst = (byAccount || {})[String(account ?? '').trim().toLowerCase()];
  if (!inst || typeof inst !== 'object') return null;
  return inst.id === null || inst.id === undefined ? null : String(inst.id);
}

/** An ISO 8601 timestamp as epoch milliseconds, or null. Pure. */
export function parseMoment(text) {
  const raw = String(text ?? '').trim();
  if (!raw) return null;
  const ms = Date.parse(raw);
  return Number.isNaN(ms) ? null : ms;
}

/** Whether this installation was created after the map was written. Pure. */
export function reinstalledSince(inst, recordedAt) {
  const created = parseMoment(inst && typeof inst === 'object' ? inst.created_at : null);
  const recorded = parseMoment(recordedAt);
  if (created === null || recorded === null) return null;
  return created > recorded;
}

/** Compare one configured pair against reality. Pure. */
export function drift(account, configuredId, byId, byAccount, recordedAt = null) {
  const name = String(account ?? '').trim();
  const wanted = String(configuredId ?? '').trim();
  const listed = (byId || {})[wanted];
  const current = currentIdFor(name, byAccount);

  if (listed !== undefined && listed !== null) {
    const owner = accountOf(listed) || '';
    if (owner.toLowerCase() !== name.toLowerCase()) {
      return ['crossed',
        `${name} is configured as ${wanted}, which exists and belongs to `
        + `${owner || 'another account'}. Nothing about this fails: it works `
        + 'against the wrong account.'];
    }
    if (reinstalledSince(listed, recordedAt)) {
      return ['current-but-reinstalled',
        `${name} still resolves to ${wanted}, and that installation was created `
        + 'after the map was written, so the App was removed and re-added at '
        + 'some point.'];
    }
    return ['current', `${name} resolves to ${wanted}.`];
  }

  if (current !== null) {
    const created = ((byAccount || {})[name.toLowerCase()] || {}).created_at;
    return ['stale',
      `${name} is configured as ${wanted}, which this App no longer has. The `
      + `current installation for ${name} is ${current}`
      + `${created ? `, created ${created}` : ''}.`];
  }
  return ['gone',
    `${name} is configured as ${wanted} and this App has no installation on `
    + 'that account at all. It was uninstalled and not put back.'];
}

/** Accounts the App is installed on that the configuration omits. Pure. */
export function unmapped(byAccount, configured) {
  const known = new Set(Object.keys(configured || {}).map((k) => String(k).trim().toLowerCase()));
  return Object.keys(byAccount || {}).filter((k) => !known.has(k)).sort();
}

/** Counts by state, with the silent finding pulled out. Pure. */
export function summarize(findings) {
  const counts = {};
  for (const f of findings || []) counts[f.state] = (counts[f.state] || 0) + 1;
  return {
    total: (findings || []).length,
    by_state: counts,
    silent: SILENT.reduce((n, s) => n + (counts[s] || 0), 0),
  };
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, account = null, current = null) {
  if (state === 'crossed') {
    return `stop the deploy. The id filed under ${account || 'this account'} `
      + 'belongs to another account, so every call made with it lands on the '
      + 'wrong organization and nothing will ever error. Fix the mapping, then '
      + 'resolve the id at runtime so it cannot drift again.';
  }
  if (state === 'stale') {
    return 'resolve the id per account from the org\\'s own installation route '
      + `rather than storing it. The current id is ${current || 'on the list above'} `
      + 'today and will be a different one after the next reinstall.';
  }
  if (state === 'gone') {
    return `the App is not installed on ${account || 'that account'}. This is `
      + 'not an id problem: somebody has to install it again, and your code '
      + 'should key state on the account login so the history survives.';
  }
  if (state === 'current-but-reinstalled') {
    return 'nothing is broken, but the id changed hands once already. Move the '
      + 'lookup into the code before it changes again.';
  }
  return 'nothing. This account resolves correctly.';
}

function headers(jwt) {
  return {
    Authorization: `Bearer ${jwt}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function get(jwt, path) {
  const res = await fetch(API + path, { headers: headers(jwt) });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function main() {
  const jwt = process.env.GITHUB_APP_JWT;
  if (!jwt) {
    console.error('set GITHUB_APP_JWT; the installation list wants the App JWT');
    process.exitCode = 2;
    return;
  }
  const configured = parseMap(process.env.GITHUB_INSTALLATION_MAP || '');
  if (!Object.keys(configured).length) {
    console.error('set GITHUB_INSTALLATION_MAP to account=id pairs');
    process.exitCode = 2;
    return;
  }
  const recordedAt = process.env.GITHUB_MAP_RECORDED_AT || null;

  const installations = [];
  for (let page = 1; page <= 10; page += 1) {
    const { status, body } = await get(jwt, `/app/installations?per_page=100&page=${page}`);
    if (status !== 200 || !Array.isArray(body)) {
      if (page === 1) console.error(`GET /app/installations returned ${status}`);
      break;
    }
    installations.push(...body);
    if (body.length < 100) break;
  }
  console.log(`${installations.length} installation(s) visible to this App`);

  const byId = indexById(installations);
  const byAccount = indexByAccount(installations);
  const findings = Object.entries(configured).sort().map(([account, ident]) => {
    const [state, detail] = drift(account, ident, byId, byAccount, recordedAt);
    return {
      account, configured_id: ident, state, detail,
      current_id: currentIdFor(account, byAccount),
    };
  });
  findings.sort((a, b) => (SILENT.includes(b.state) ? 1 : 0) - (SILENT.includes(a.state) ? 1 : 0)
    || a.account.localeCompare(b.account));

  for (const f of findings) {
    if (f.state !== 'current') {
      console.log(`${f.state}: ${f.detail}`);
      console.log(`repair: ${repair(f.state, f.account, f.current_id)}`);
    }
  }
  const extra = unmapped(byAccount, configured);
  if (extra.length) console.log(`also installed and not in the map: ${extra.join(', ')}`);

  const stats = summarize(findings);
  console.log(JSON.stringify({
    visible: installations.length, summary: stats, unmapped_accounts: extra, findings,
  }, null, 2));
  process.exitCode = (stats.by_state.current || 0) === stats.total ? 0 : 1;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The case the tests are built around is the one that produces no error: an id that exists, resolves and belongs to somebody else. It has to come back as its own state, it has to be ordered ahead of the noisy failures, and it must never be confused with the stale id it superficially resembles. The rest pin the input shapes this check meets in the wild &mdash; a map written as pairs and as JSON, ids stored as numbers and as strings, logins in the wrong case &mdash; and the third answer for a reinstall date that cannot be read.",
"test_py_file": "test_github_installation_id_drift.py",
"test_py": '''from github_installation_id_drift import (
    account_of, current_id_for, drift, index_by_account, index_by_id, parse_map,
    reinstalled_since, repair, stable_key, summarize, unmapped,
)

ACME = {"id": 55120044, "account": {"login": "acme-corp"},
        "created_at": "2026-08-25T08:02:11Z"}
GAMMA = {"id": 41234568, "account": {"login": "gamma-labs"},
         "created_at": "2024-02-01T00:00:00Z"}
BY_ID = index_by_id([ACME, GAMMA])
BY_ACCOUNT = index_by_account([ACME, GAMMA])


def test_the_map_is_read_as_pairs_or_as_json():
    assert parse_map("acme-corp=41234567,beta-inc=41234568") == {
        "acme-corp": "41234567", "beta-inc": "41234568"}
    assert parse_map(' {"Acme-Corp": 41234567} ') == {"acme-corp": "41234567"}
    assert parse_map(" acme-corp = 41234567 ; beta-inc=9 ") == {
        "acme-corp": "41234567", "beta-inc": "9"}
    assert parse_map("") == {}
    assert parse_map("nonsense") == {}
    assert parse_map("{not json") == {}


def test_ids_are_indexed_as_text_however_they_arrived():
    assert BY_ID["55120044"] is ACME
    assert index_by_id([{"id": "77", "account": {"login": "x"}}])["77"]["id"] == "77"
    assert index_by_id([{"account": {"login": "x"}}]) == {}


def test_the_stable_key_is_the_login_not_the_id():
    assert stable_key(ACME) == "acme-corp"
    assert stable_key({"id": 5, "account": {"login": "Acme-Corp"}}) == "acme-corp"
    assert stable_key({"id": 5}) is None
    assert account_of(None) is None


def test_an_id_that_belongs_to_another_account_is_its_own_finding():
    state, detail = drift("beta-inc", 41234568, BY_ID, BY_ACCOUNT)
    assert state == "crossed"
    assert "gamma-labs" in detail
    assert "wrong account" in detail
    assert "stop the deploy" in repair(state, "beta-inc")


def test_a_missing_id_on_a_live_account_names_the_current_one():
    state, detail = drift("acme-corp", 41234567, BY_ID, BY_ACCOUNT)
    assert state == "stale"
    assert "55120044" in detail
    assert current_id_for("ACME-CORP", BY_ACCOUNT) == "55120044"


def test_a_missing_id_on_a_missing_account_is_not_a_stale_id():
    state, detail = drift("delta-ltd", 999, BY_ID, BY_ACCOUNT)
    assert state == "gone"
    assert "no installation on that account" in detail


def test_a_matching_id_is_current_whether_it_was_stored_as_text():
    assert drift("acme-corp", "55120044", BY_ID, BY_ACCOUNT)[0] == "current"
    assert drift("Acme-Corp", 55120044, BY_ID, BY_ACCOUNT)[0] == "current"


def test_a_reinstall_after_the_map_was_written_is_flagged_even_when_it_matches():
    state, detail = drift("acme-corp", 55120044, BY_ID, BY_ACCOUNT,
                          recorded_at="2026-01-01T00:00:00Z")
    assert state == "current-but-reinstalled"
    assert "removed and re-added" in detail


def test_an_unreadable_date_is_a_third_answer_and_not_a_no():
    assert reinstalled_since(ACME, "2026-01-01T00:00:00Z") is True
    assert reinstalled_since(ACME, "2026-12-01T00:00:00Z") is False
    assert reinstalled_since(ACME, None) is None
    assert reinstalled_since({}, "2026-01-01T00:00:00Z") is None


def test_installations_the_map_never_mentions_are_listed_separately():
    assert unmapped(BY_ACCOUNT, {"acme-corp": "1"}) == ["gamma-labs"]
    assert unmapped(BY_ACCOUNT, {"ACME-CORP": "1", "gamma-labs": "2"}) == []


def test_the_summary_counts_the_silent_finding_apart():
    stats = summarize([{"state": "crossed"}, {"state": "stale"}, {"state": "current"}])
    assert stats["total"] == 3
    assert stats["silent"] == 1
    assert stats["by_state"]["stale"] == 1
''',
"test_js_file": "github-installation-id-drift.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  accountOf, currentIdFor, drift, indexByAccount, indexById, parseMap,
  reinstalledSince, repair, stableKey, summarize, unmapped,
} from './github-installation-id-drift.mjs';

const ACME = {
  id: 55120044, account: { login: 'acme-corp' }, created_at: '2026-08-25T08:02:11Z',
};
const GAMMA = {
  id: 41234568, account: { login: 'gamma-labs' }, created_at: '2024-02-01T00:00:00Z',
};
const BY_ID = indexById([ACME, GAMMA]);
const BY_ACCOUNT = indexByAccount([ACME, GAMMA]);

test('the map is read as pairs or as JSON', () => {
  assert.deepEqual(parseMap('acme-corp=41234567,beta-inc=41234568'),
    { 'acme-corp': '41234567', 'beta-inc': '41234568' });
  assert.deepEqual(parseMap(' {"Acme-Corp": 41234567} '), { 'acme-corp': '41234567' });
  assert.deepEqual(parseMap(' acme-corp = 41234567 ; beta-inc=9 '),
    { 'acme-corp': '41234567', 'beta-inc': '9' });
  assert.deepEqual(parseMap(''), {});
  assert.deepEqual(parseMap('nonsense'), {});
  assert.deepEqual(parseMap('{not json'), {});
});

test('ids are indexed as text however they arrived', () => {
  assert.equal(BY_ID['55120044'], ACME);
  assert.equal(indexById([{ id: '77', account: { login: 'x' } }])['77'].id, '77');
  assert.deepEqual(indexById([{ account: { login: 'x' } }]), {});
});

test('the stable key is the login not the id', () => {
  assert.equal(stableKey(ACME), 'acme-corp');
  assert.equal(stableKey({ id: 5, account: { login: 'Acme-Corp' } }), 'acme-corp');
  assert.equal(stableKey({ id: 5 }), null);
  assert.equal(accountOf(null), null);
});

test('an id that belongs to another account is its own finding', () => {
  const [state, detail] = drift('beta-inc', 41234568, BY_ID, BY_ACCOUNT);
  assert.equal(state, 'crossed');
  assert.match(detail, /gamma-labs/);
  assert.match(detail, /wrong account/);
  assert.match(repair(state, 'beta-inc'), /stop the deploy/);
});

test('a missing id on a live account names the current one', () => {
  const [state, detail] = drift('acme-corp', 41234567, BY_ID, BY_ACCOUNT);
  assert.equal(state, 'stale');
  assert.match(detail, /55120044/);
  assert.equal(currentIdFor('ACME-CORP', BY_ACCOUNT), '55120044');
});

test('a missing id on a missing account is not a stale id', () => {
  const [state, detail] = drift('delta-ltd', 999, BY_ID, BY_ACCOUNT);
  assert.equal(state, 'gone');
  assert.match(detail, /no installation on that account/);
});

test('a matching id is current whether it was stored as text', () => {
  assert.equal(drift('acme-corp', '55120044', BY_ID, BY_ACCOUNT)[0], 'current');
  assert.equal(drift('Acme-Corp', 55120044, BY_ID, BY_ACCOUNT)[0], 'current');
});

test('a reinstall after the map was written is flagged even when it matches', () => {
  const [state, detail] = drift('acme-corp', 55120044, BY_ID, BY_ACCOUNT,
    '2026-01-01T00:00:00Z');
  assert.equal(state, 'current-but-reinstalled');
  assert.match(detail, /removed and re-added/);
});

test('an unreadable date is a third answer and not a no', () => {
  assert.equal(reinstalledSince(ACME, '2026-01-01T00:00:00Z'), true);
  assert.equal(reinstalledSince(ACME, '2026-12-01T00:00:00Z'), false);
  assert.equal(reinstalledSince(ACME, null), null);
  assert.equal(reinstalledSince({}, '2026-01-01T00:00:00Z'), null);
});

test('installations the map never mentions are listed separately', () => {
  assert.deepEqual(unmapped(BY_ACCOUNT, { 'acme-corp': '1' }), ['gamma-labs']);
  assert.deepEqual(unmapped(BY_ACCOUNT, { 'ACME-CORP': '1', 'gamma-labs': '2' }), []);
});

test('the summary counts the silent finding apart', () => {
  const stats = summarize([{ state: 'crossed' }, { state: 'stale' }, { state: 'current' }]);
  assert.equal(stats.total, 3);
  assert.equal(stats.silent, 1);
  assert.equal(stats.by_state.stale, 1);
});
''',
"faq": [
 ("Why does the installation id change at all?",
  "Because an installation is a record of one act of installing, not a permanent link between an App and an account. Uninstalling deletes that record; installing again creates a new one, with a new id, a new creation time and a freshly accepted permission grant. Nothing is carried across, and nothing about the old id is reserved. It is the same shape of mistake as treating a session id as a user id: it works until the session ends."),
 ("Can the script just mint a token to see whether the id still works?",
  "It could and it does not. Minting an installation access token is a write, and this section's scripts hold a credential that can reach your repositories, so none of them writes. It also would not answer the interesting question. A mint that succeeds tells you the id resolves; it does not tell you the account behind it is the one you meant, which is the failure that produces no error and does real damage. Listing the installations answers both at once."),
 ("What does a crossed id actually cost?",
  "It depends entirely on what the integration does with the token. A read-only integration leaks the other organization's data into your logs, your cache and possibly your product. One that writes will comment, label, dispatch or push against repositories belonging to somebody who never asked for it. In neither case does anything error, so the only bound on how long it runs is how long it takes somebody to notice their repository behaving strangely."),
 ("We get the id from the webhook payload. Are we safe?",
  "Largely, yes, and that is the pattern worth copying. Every App webhook delivery carries an installation object with the id on it, and it is correct by construction because GitHub used it to route the delivery. Two caveats: verify the signature before you trust anything in the payload, and remember that work not triggered by a webhook, such as a nightly reconciliation over every customer, still needs the id resolved from somewhere. That path is where the stored value usually survives."),
 ("How often should this run?",
  "On every deploy, and on a schedule between deploys. It is one paginated GET with a JWT you already hold, so the cost is negligible against the class of problem it catches. Run it as a deploy gate for the crossed state specifically, because that finding has no other chance of being noticed, and as a report for the rest. Recording the date the mapping was written buys the reinstall warning as well, which arrives before anything breaks."),
],
"related": [
 ("/github/installation-suspended/", "An installation suspended rather than removed"),
 ("/github/app-not-installed-on-repo/", "A 404 that means the App is not installed"),
 ("/github/installation-token-expired/", "The installation token expired an hour in"),
],
"citations": [CITE_INSTALLATIONS, CITE_APPS_REST, CITE_APP_AUTH, CITE_INSTALL_AUTH],
},

{
"slug": "webhook-timeout-10s",
"title": "The receiver takes longer than 10 seconds and times out",
"description": "GitHub allows a receiver 10 seconds. Every delivery record carries a duration, so the slide toward the cutoff is readable long before anything fails.",
"h1": "the receiver takes longer than 10 seconds and times out",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github webhook 10 second timeout",
             "github webhook delivery timed out duration",
             "webhook receiver too slow 202 queue",
             "github webhook deliveries duration field",
             "webhook handler synchronous work timeout"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The delivery log has started showing <code>timed out</code> against a handler that, according to your own logs, finished the job perfectly. It ran, it did the work, it wrote the record, it returned 200 &mdash; twelve seconds after it started. GitHub stopped listening at ten and filed the delivery as a failure, and the redelivery it may send will do the same twelve seconds of work again.",
"short_answer": """<p>A webhook receiver gets ten seconds to respond. Anything slower is recorded as a failed delivery whether or not your handler eventually succeeds, because GitHub is not waiting to find out. A handler that does the real work inline &mdash; clones a repository, calls three other APIs, waits on a build &mdash; sits under that ceiling comfortably at first and crosses it the month the repository grows.</p>
<p>Every record in <code>GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries</code> carries a <code>duration</code> alongside its status, on the successful deliveries as much as the failed ones, and that column is the one to read. Counting failures tells you the cutoff has already been crossed. Reading the duration distribution &mdash; the median, the 95th percentile, and which event types sit at the top of it &mdash; tells you how much room is left, which is the only version of this finding that arrives in time to be useful. The repair is structural: verify the signature, acknowledge, enqueue, and do the work somewhere the clock is not running.</p>""",
"problem": """<p>It looks like a lie, so it gets argued with. Your logs say the handler ran and returned 200; the delivery log says timed out; both are correct and they are describing different moments. The handler did return 200, to a connection GitHub had already abandoned. A morning goes into proving the receiver works, which it does, and none of that work touches the actual constraint, which is when the answer arrived rather than whether it was right.</p>
<p>Then it gets treated as flaky. Timeouts are intermittent by nature: the same handler on a small repository is fine and on the big one is not, so the failures cluster in a way that looks like network weather. Retries are added, alert thresholds are raised, and the timeouts are filed under things that sometimes happen. The population of deliveries that are slow but still inside the limit &mdash; the ones that will time out next quarter &mdash; is invisible to every one of those responses, because nothing in a failure count looks at them.</p>
<p>The redelivery makes it worse rather than better. A delivery that timed out at ten seconds is a delivery whose work may have completed anyway, so replaying it runs the same expensive job a second time. Handlers that were written on the assumption that a delivery arrives once now run twice under load, which is exactly when they can least afford it, and any part of them that is not idempotent starts producing duplicates at the worst possible moment.</p>""",
"why": """<p><strong>Ten seconds is the whole budget, not the handler's budget.</strong> The clock covers DNS, the TLS handshake, any queueing in your ingress, your framework's own startup on a cold instance, the handler, and the response. A handler that measures itself at eight seconds may still be recorded as a timeout, because it was never measuring the part of the ten that it did not control.</p>
<p><strong>The duration is recorded on every delivery, including the good ones.</strong> This is what makes the problem forecastable. The deliveries feed is not only a failure log; each record carries how long the attempt took, so a distribution that has crept from two seconds to seven is a finding today, before a single delivery has failed. That is the entire reason this check exists separately from a failure audit.</p>
<p><strong>It is not the same read as the failure audit.</strong> <a href="/github/webhook-deliveries-failing/">The note on failing deliveries</a> reads this same feed and buckets it by status code, because a 401 and a 500 want different repairs. This one throws the status codes away, except the one marker that says the attempt was abandoned, and reads the duration column on everything. The two answer different questions from the same request: <em>what broke</em>, and <em>how close is this to breaking</em>.</p>
<p><strong>The slowness is usually one event type.</strong> A <code>push</code> on a monorepo carries a large payload and usually triggers the most work; a <code>check_suite</code> or a <code>status</code> fires far more often than anybody expects. Grouping durations by event tells you which handler to make asynchronous first, and that is a smaller and more achievable change than making the whole receiver asynchronous at once.</p>
<p><strong>You cannot time this from outside.</strong> The obvious experiment &mdash; send a request at the receiver and measure it &mdash; is not available to a read-only script, and it would be a poor measurement anyway: a synthetic payload does not do the work a real one does, and the numbers you want are the ones GitHub already recorded from its own side of the connection. The feed has them. Reasoning from the record beats manufacturing a new one.</p>""",
"steps": [
 {"h": "Pull the deliveries and keep the duration column",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries?per_page=100</code>, following the cursor in the <code>Link</code> header. Keep every record, not just the failures. The successful ones are the sample that tells you where the distribution actually sits, and discarding them is how this problem stays invisible until it is an outage.</p>"""},
 {"h": "Normalise the duration before you compare anything",
  "body": """<p>The field is a bare number with no unit attached to it, and in practice deliveries come back with small values that are plainly seconds. Treat anything at or below sixty as seconds and anything above as milliseconds: no delivery survives past ten seconds, and none takes sixty thousand of them, so the rule is unambiguous on real data. Convert once, at the edge, and work in milliseconds after that.</p>"""},
 {"h": "Read the percentiles, not the mean",
  "body": """<p>A mean of three seconds hides a 95th percentile of nine. The number that matters is the tail, because the tail is what crosses the line first, and the headroom worth reporting is ten seconds minus the 95th percentile. Under two seconds of headroom is a finding even when the failure count is zero.</p>"""},
 {"h": "Group by event to find the handler to fix",
  "body": """<p>Compute the same percentile per event type. One event usually dominates, and making that single handler acknowledge-then-queue buys most of the headroom for a fraction of the work. It also makes the change reviewable, which the alternative &mdash; restructuring every handler at once &mdash; is not.</p>"""},
 {"h": "Make the synchronous path do nothing",
  "body": """<p>Verify the signature, put the raw payload on a queue, return <code>202</code>. That is the whole handler. Everything else moves behind the queue, where it can take twelve seconds or twelve minutes and retry on its own terms. Do the signature check before the enqueue, so the queue never holds anything unverified, and make the worker idempotent on the delivery guid, because redeliveries are now something you can survive rather than something you fear.</p>"""},
],
"verify": """<p>After the work moves behind a queue, the same read shows the tail collapsing while the delivery count stays exactly where it was.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_hook_delivery_duration.py \\
  --repo acme-corp/platform
# hook 517238001 -> https://hooks.example.com/github
# 400 delivery/deliveries, 6 timed out, p50 3410ms, p95 9120ms, max 10000ms
# timing-out: 6 deliveries were abandoned at the 10 second cutoff, and the 95th
# percentile is 9120ms, which leaves 880ms of headroom on everything else
# slowest event: push, p95 9740ms across 122 deliveries
# repair: verify the signature, enqueue the payload, return 202

# after the handler is split
# healthy: p95 is 240ms, 9760ms of headroom</code></pre>""",
"code_intro": "One GET for the hooks and a cursor-paginated GET for the deliveries, and nothing is ever sent to the receiver itself &mdash; the numbers this needs were recorded by GitHub from its own side of the connection, and a synthetic request would be both a write and a worse measurement. The pure part is small and does the arguing: a unit normalisation with one defensible rule, a nearest-rank percentile so a short window does not interpolate values that never happened, and a verdict that treats a healthy failure count with a tail at nine seconds as a finding rather than a pass.",
"py_file": "github_hook_delivery_duration.py",
"py": '''"""Report how close a webhook receiver is to the 10 second delivery cutoff.

Read only. GETs the repository's hooks and their delivery records. Nothing is
sent to the receiver: timing it from here would be a write, and it would be a
worse measurement than the one GitHub already recorded from its own side of the
connection.

GitHub allows a receiver ten seconds to respond and files anything slower as a
failed delivery, whatever the handler eventually does. Every delivery record
carries a duration, on the successful attempts as much as the failed ones, so
the slide toward the cutoff is readable before the first failure.

This is a different read from a delivery failure audit. That one buckets by
status code. This one ignores status codes except the abandonment marker and
reads the duration column on everything.

Environment:

    GITHUB_TOKEN   a read-only token with access to the repository
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_hook_delivery_duration")

API = "https://api.github.com"
UA = "github-hook-delivery-duration/1.0"

CUTOFF_MS = 10000
WARN_MS = 8000
SLOW_MS = 5000
# The duration field carries no unit. Nothing survives past ten seconds and
# nothing real takes sixty thousand of them, so a value at or under sixty is
# seconds and anything above it is already milliseconds.
SECONDS_CEILING = 60


def duration_ms(row):
    """A delivery's duration in milliseconds, or None. Pure."""
    if not isinstance(row, dict):
        return None
    raw = row.get("duration")
    if raw is None or isinstance(raw, bool):
        return None
    try:
        value = float(raw)
    except (TypeError, ValueError):
        return None
    if value < 0:
        return None
    return value * 1000.0 if value <= SECONDS_CEILING else value


def timed_out(row):
    """Whether GitHub abandoned this delivery. Pure.

    The status text is the reliable marker. A record can also carry a duration
    at the cutoff with no status text at all, which counts too, because that is
    the same event described by the other column.
    """
    if not isinstance(row, dict):
        return False
    status = " ".join(str(row.get("status") or "").lower().split())
    if "timed out" in status or "timeout" in status:
        return True
    ms = duration_ms(row)
    return ms is not None and ms >= CUTOFF_MS


def classify(row):
    """Sort one delivery by how much room it had left. Pure."""
    if timed_out(row):
        return "timed-out"
    ms = duration_ms(row)
    if ms is None:
        return "unknown"
    if ms >= WARN_MS:
        return "at-risk"
    if ms >= SLOW_MS:
        return "slow"
    return "fine"


def percentile(values, p):
    """Nearest-rank percentile over a list of numbers, or None. Pure.

    Nearest rank rather than interpolation on purpose: a delivery window is
    small and every value in it is a real measurement, so reporting a number
    that no delivery actually took would be a worse answer than reporting one
    that a delivery did.
    """
    numbers = sorted(v for v in (values or []) if isinstance(v, (int, float)))
    if not numbers:
        return None
    if p <= 0:
        return numbers[0]
    if p >= 100:
        return numbers[-1]
    import math
    rank = max(1, math.ceil(p / 100.0 * len(numbers)))
    return numbers[min(rank, len(numbers)) - 1]


def stats(rows):
    """The distribution that decides the verdict. Pure."""
    rows = [r for r in (rows or []) if isinstance(r, dict)]
    measured = [duration_ms(r) for r in rows]
    measured = [m for m in measured if m is not None]
    p95 = percentile(measured, 95)
    return {
        "count": len(rows),
        "measured": len(measured),
        "timed_out": sum(1 for r in rows if timed_out(r)),
        "p50": percentile(measured, 50),
        "p95": p95,
        "max": max(measured) if measured else None,
        "headroom_ms": None if p95 is None else CUTOFF_MS - p95,
    }


def by_event(rows, min_count=3):
    """The same distribution per event type. Pure."""
    groups = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        event = str(row.get("event") or "unknown").strip().lower() or "unknown"
        groups.setdefault(event, []).append(row)
    out = {}
    for event, group in groups.items():
        measured = [m for m in (duration_ms(r) for r in group) if m is not None]
        out[event] = {"count": len(group),
                      "timed_out": sum(1 for r in group if timed_out(r)),
                      "p95": percentile(measured, 95)}
    return {k: v for k, v in out.items() if v["count"] >= min_count or v["timed_out"]}


def slowest_event(rows, min_count=3):
    """The event type with the worst tail, or None. Pure."""
    grouped = by_event(rows, min_count)
    ranked = [(v["p95"], k, v) for k, v in grouped.items() if v["p95"] is not None]
    if not ranked:
        return None
    ranked.sort(key=lambda t: (-t[0], t[1]))
    p95, event, row = ranked[0]
    return {"event": event, "p95": p95, "count": row["count"],
            "timed_out": row["timed_out"]}


def verdict(st):
    """Turn the distribution into a finding. Pure."""
    if not st or not st.get("count"):
        return ("no-data",
                "no deliveries in the retained window, so there is nothing to "
                "measure. That is not the same as a receiver that is fast.")
    if not st.get("measured"):
        return ("no-durations",
                "%d delivery/deliveries carry no duration, so the tail cannot "
                "be measured from this feed." % st["count"])
    p95 = st["p95"]
    if st["timed_out"]:
        return ("timing-out",
                "%d deliveries were abandoned at the 10 second cutoff, and the "
                "95th percentile is %dms, which leaves %dms of headroom on "
                "everything else." % (st["timed_out"], p95, st["headroom_ms"]))
    if p95 >= WARN_MS:
        return ("at-the-edge",
                "nothing has timed out yet and the 95th percentile is %dms, "
                "leaving %dms before the cutoff. This fails on the next slow "
                "week." % (p95, st["headroom_ms"]))
    if p95 >= SLOW_MS:
        return ("slow",
                "the 95th percentile is %dms against a 10 second cutoff. The "
                "handler is doing real work inline and has %dms of room."
                % (p95, st["headroom_ms"]))
    return ("healthy",
            "the 95th percentile is %dms, %dms inside the cutoff."
            % (p95, st["headroom_ms"]))


def repair(state, worst=None):
    """The sentence a reader has to act on. Pure."""
    if state in ("timing-out", "at-the-edge", "slow"):
        target = (" Start with %s, whose 95th percentile is %dms."
                  % (worst["event"], worst["p95"])) if worst else ""
        return ("verify the signature, put the raw payload on a queue, return "
                "202, and do the work in a worker keyed on the delivery guid so "
                "a redelivery cannot run it twice.%s" % target)
    if state == "no-data":
        return ("nothing to repair, and nothing proved either. Check the hook "
                "is active and that the retention window covers a period when "
                "events actually happened.")
    if state == "no-durations":
        return ("read the durations from a wider page of deliveries; this "
                "window has statuses but no timings to work from.")
    return "nothing. The receiver answers well inside the cutoff."


def next_link(headers):
    """The rel=next URL from a Link header, or None. Pure."""
    link = (headers or {}).get("Link") or (headers or {}).get("link") or ""
    for part in str(link).split(","):
        section = part.split(";")
        if len(section) < 2:
            continue
        url = section[0].strip()
        if 'rel="next"' in part and url.startswith("<") and url.endswith(">"):
            return url[1:-1]
    return None


def get(session, url):
    """One GET. Returns (status, json-or-None, headers)."""
    full = API + url if url.startswith("/") else url
    r = session.get(full, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body, r.headers


def deliveries(session, owner, repo, hook_id, pages=8):
    """Delivery records for one hook, following the cursor. Read only."""
    url = "/repos/%s/%s/hooks/%s/deliveries?per_page=100" % (owner, repo, hook_id)
    out = []
    for _ in range(pages):
        status, body, headers = get(session, url)
        if status != 200 or not isinstance(body, list):
            log.error("deliveries for hook %s returned %d", hook_id, status)
            break
        out.extend(body)
        url = next_link(headers)
        if not url:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/repo")
    ap.add_argument("--hook-id", default=None, help="one hook; omit for all")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN to a read-only token that can read the "
                  "repository's hooks")
        return 2
    if "/" not in args.repo:
        log.error("--repo takes owner/repo")
        return 2
    owner, repo = args.repo.split("/", 1)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    status, hooks, _ = get(session, "/repos/%s/%s/hooks?per_page=100" % (owner, repo))
    if status != 200 or not isinstance(hooks, list):
        log.error("GET hooks returned %d", status)
        return 2
    if args.hook_id:
        hooks = [h for h in hooks if str(h.get("id")) == str(args.hook_id)]

    report = []
    worst_state = "healthy"
    for hook in hooks:
        hook_id = hook.get("id")
        url = (hook.get("config") or {}).get("url", "?")
        log.info("hook %s -> %s", hook_id, url)
        rows = deliveries(session, owner, repo, hook_id)
        st = stats(rows)
        state, detail = verdict(st)
        worst = slowest_event(rows)
        log.info("%d delivery/deliveries, %d timed out, p50 %sms, p95 %sms, "
                 "max %sms", st["count"], st["timed_out"],
                 int(st["p50"]) if st["p50"] is not None else "?",
                 int(st["p95"]) if st["p95"] is not None else "?",
                 int(st["max"]) if st["max"] is not None else "?")
        log.info("%s: %s", state, detail)
        if worst:
            log.info("slowest event: %s, p95 %dms across %d deliveries",
                     worst["event"], worst["p95"], worst["count"])
        log.info("repair: %s", repair(state, worst))
        if state in ("timing-out", "at-the-edge"):
            worst_state = state
        report.append({"hook_id": hook_id, "url": url, "stats": st,
                       "state": state, "detail": detail,
                       "slowest_event": worst,
                       "by_event": by_event(rows)})

    print(json.dumps({"repo": args.repo, "hooks": report}, indent=2, default=str))
    return 1 if worst_state != "healthy" else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-hook-delivery-duration.mjs",
"js": '''/**
 * Report how close a webhook receiver is to the 10 second delivery cutoff.
 *
 * Read only. GETs the repository's hooks and their delivery records. Nothing is
 * sent to the receiver: timing it from here would be a write, and a worse
 * measurement than the one GitHub already recorded from its own side.
 *
 * Environment:
 *   GITHUB_TOKEN    a read-only token with access to the repository
 *   GITHUB_REPO     owner/repo
 *   GITHUB_HOOK_ID  optional, one hook instead of all of them
 */
const API = 'https://api.github.com';
const UA = 'github-hook-delivery-duration/1.0';

export const CUTOFF_MS = 10000;
export const WARN_MS = 8000;
export const SLOW_MS = 5000;
// The duration field carries no unit; at or under sixty it is seconds.
export const SECONDS_CEILING = 60;

/** A delivery's duration in milliseconds, or null. Pure. */
export function durationMs(row) {
  if (!row || typeof row !== 'object') return null;
  const raw = row.duration;
  if (raw === null || raw === undefined || typeof raw === 'boolean') return null;
  const value = Number(raw);
  if (!Number.isFinite(value) || value < 0) return null;
  return value <= SECONDS_CEILING ? value * 1000 : value;
}

/** Whether GitHub abandoned this delivery. Pure. */
export function timedOut(row) {
  if (!row || typeof row !== 'object') return false;
  const status = String(row.status ?? '').toLowerCase().split(/\\s+/).join(' ');
  if (status.includes('timed out') || status.includes('timeout')) return true;
  const ms = durationMs(row);
  return ms !== null && ms >= CUTOFF_MS;
}

/** Sort one delivery by how much room it had left. Pure. */
export function classify(row) {
  if (timedOut(row)) return 'timed-out';
  const ms = durationMs(row);
  if (ms === null) return 'unknown';
  if (ms >= WARN_MS) return 'at-risk';
  if (ms >= SLOW_MS) return 'slow';
  return 'fine';
}

/** Nearest-rank percentile over a list of numbers, or null. Pure. */
export function percentile(values, p) {
  const numbers = (values || []).filter((v) => typeof v === 'number' && Number.isFinite(v))
    .sort((a, b) => a - b);
  if (!numbers.length) return null;
  if (p <= 0) return numbers[0];
  if (p >= 100) return numbers[numbers.length - 1];
  const rank = Math.max(1, Math.ceil((p / 100) * numbers.length));
  return numbers[Math.min(rank, numbers.length) - 1];
}

/** The distribution that decides the verdict. Pure. */
export function stats(rows) {
  const list = (rows || []).filter((r) => r && typeof r === 'object');
  const measured = list.map(durationMs).filter((m) => m !== null);
  const p95 = percentile(measured, 95);
  return {
    count: list.length,
    measured: measured.length,
    timed_out: list.filter(timedOut).length,
    p50: percentile(measured, 50),
    p95,
    max: measured.length ? Math.max(...measured) : null,
    headroom_ms: p95 === null ? null : CUTOFF_MS - p95,
  };
}

/** The same distribution per event type. Pure. */
export function byEvent(rows, minCount = 3) {
  const groups = {};
  for (const row of rows || []) {
    if (!row || typeof row !== 'object') continue;
    const event = String(row.event ?? 'unknown').trim().toLowerCase() || 'unknown';
    (groups[event] = groups[event] || []).push(row);
  }
  const out = {};
  for (const [event, group] of Object.entries(groups)) {
    const measured = group.map(durationMs).filter((m) => m !== null);
    const row = {
      count: group.length,
      timed_out: group.filter(timedOut).length,
      p95: percentile(measured, 95),
    };
    if (row.count >= minCount || row.timed_out) out[event] = row;
  }
  return out;
}

/** The event type with the worst tail, or null. Pure. */
export function slowestEvent(rows, minCount = 3) {
  const grouped = byEvent(rows, minCount);
  const ranked = Object.entries(grouped).filter(([, v]) => v.p95 !== null);
  if (!ranked.length) return null;
  ranked.sort((a, b) => b[1].p95 - a[1].p95 || a[0].localeCompare(b[0]));
  const [event, row] = ranked[0];
  return { event, p95: row.p95, count: row.count, timed_out: row.timed_out };
}

/** Turn the distribution into a finding. Pure. */
export function verdict(st) {
  if (!st || !st.count) {
    return ['no-data',
      'no deliveries in the retained window, so there is nothing to measure. '
      + 'That is not the same as a receiver that is fast.'];
  }
  if (!st.measured) {
    return ['no-durations',
      `${st.count} delivery/deliveries carry no duration, so the tail cannot be `
      + 'measured from this feed.'];
  }
  const p95 = st.p95;
  if (st.timed_out) {
    return ['timing-out',
      `${st.timed_out} deliveries were abandoned at the 10 second cutoff, and `
      + `the 95th percentile is ${Math.trunc(p95)}ms, which leaves `
      + `${Math.trunc(st.headroom_ms)}ms of headroom on everything else.`];
  }
  if (p95 >= WARN_MS) {
    return ['at-the-edge',
      `nothing has timed out yet and the 95th percentile is ${Math.trunc(p95)}ms, `
      + `leaving ${Math.trunc(st.headroom_ms)}ms before the cutoff. This fails on `
      + 'the next slow week.'];
  }
  if (p95 >= SLOW_MS) {
    return ['slow',
      `the 95th percentile is ${Math.trunc(p95)}ms against a 10 second cutoff. `
      + `The handler is doing real work inline and has ${Math.trunc(st.headroom_ms)}ms of room.`];
  }
  return ['healthy',
    `the 95th percentile is ${Math.trunc(p95)}ms, ${Math.trunc(st.headroom_ms)}ms inside the cutoff.`];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, worst = null) {
  if (['timing-out', 'at-the-edge', 'slow'].includes(state)) {
    const target = worst
      ? ` Start with ${worst.event}, whose 95th percentile is ${Math.trunc(worst.p95)}ms.`
      : '';
    return 'verify the signature, put the raw payload on a queue, return 202, and '
      + 'do the work in a worker keyed on the delivery guid so a redelivery cannot '
      + `run it twice.${target}`;
  }
  if (state === 'no-data') {
    return 'nothing to repair, and nothing proved either. Check the hook is '
      + 'active and that the retention window covers a period when events '
      + 'actually happened.';
  }
  if (state === 'no-durations') {
    return 'read the durations from a wider page of deliveries; this window has '
      + 'statuses but no timings to work from.';
  }
  return 'nothing. The receiver answers well inside the cutoff.';
}

/** The rel=next URL from a Link header, or null. Pure. */
export function nextLink(headers) {
  const link = (headers && (headers.get ? headers.get('link') : headers.Link || headers.link)) || '';
  for (const part of String(link).split(',')) {
    const url = part.split(';')[0].trim();
    if (part.includes('rel="next"') && url.startsWith('<') && url.endsWith('>')) {
      return url.slice(1, -1);
    }
  }
  return null;
}

function headersFor(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function get(token, url) {
  const res = await fetch(url.startsWith('/') ? API + url : url, { headers: headersFor(token) });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body, headers: res.headers };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repo = process.env.GITHUB_REPO;
  if (!token || !repo || !repo.includes('/')) {
    console.error('set GITHUB_TOKEN and GITHUB_REPO=owner/repo');
    process.exitCode = 2;
    return;
  }
  const [owner, name] = repo.split('/');
  const hooksRes = await get(token, `/repos/${owner}/${name}/hooks?per_page=100`);
  if (hooksRes.status !== 200 || !Array.isArray(hooksRes.body)) {
    console.error(`GET hooks returned ${hooksRes.status}`);
    process.exitCode = 2;
    return;
  }
  const wanted = process.env.GITHUB_HOOK_ID;
  const hooks = wanted
    ? hooksRes.body.filter((h) => String(h.id) === String(wanted))
    : hooksRes.body;

  let worstState = 'healthy';
  const report = [];
  for (const hook of hooks) {
    console.log(`hook ${hook.id} -> ${(hook.config || {}).url || '?'}`);
    const rows = [];
    let url = `/repos/${owner}/${name}/hooks/${hook.id}/deliveries?per_page=100`;
    for (let page = 0; page < 8 && url; page += 1) {
      const res = await get(token, url);
      if (res.status !== 200 || !Array.isArray(res.body)) {
        console.error(`deliveries returned ${res.status}`);
        break;
      }
      rows.push(...res.body);
      url = nextLink(res.headers);
    }
    const st = stats(rows);
    const [state, detail] = verdict(st);
    const worst = slowestEvent(rows);
    console.log(`${st.count} delivery/deliveries, ${st.timed_out} timed out, `
      + `p95 ${st.p95 === null ? '?' : Math.trunc(st.p95)}ms`);
    console.log(`${state}: ${detail}`);
    if (worst) {
      console.log(`slowest event: ${worst.event}, p95 ${Math.trunc(worst.p95)}ms `
        + `across ${worst.count} deliveries`);
    }
    console.log(`repair: ${repair(state, worst)}`);
    if (['timing-out', 'at-the-edge'].includes(state)) worstState = state;
    report.push({ hook_id: hook.id, stats: st, state, slowest_event: worst });
  }
  console.log(JSON.stringify({ repo, hooks: report }, null, 2));
  process.exitCode = worstState === 'healthy' ? 0 : 1;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The unit rule is tested first, because everything downstream is measured in milliseconds and a single delivery read as seconds would move a percentile by three orders of magnitude. Then the finding this note exists for: a window with zero failures and a tail at nine seconds has to come back as a problem, since a failure count calls that window perfectly healthy. The percentile is pinned to nearest rank so it only ever returns a duration some delivery really took, and the grouping has to survive an event type that appears twice and times out both times.",
"test_py_file": "test_github_hook_delivery_duration.py",
"test_py": '''from github_hook_delivery_duration import (
    by_event, classify, duration_ms, next_link, percentile, repair,
    slowest_event, stats, timed_out, verdict,
)


def d(duration, event="push", status="OK"):
    return {"duration": duration, "event": event, "status": status}


def test_seconds_and_milliseconds_both_normalise_to_milliseconds():
    assert duration_ms(d(0.62)) == 620.0
    assert duration_ms(d(9.87)) == 9870.0
    assert duration_ms(d(9870)) == 9870.0
    assert duration_ms(d(60)) == 60000.0
    assert duration_ms(d(61)) == 61.0


def test_an_unreadable_duration_is_none_rather_than_zero():
    assert duration_ms(d(None)) is None
    assert duration_ms(d("slow")) is None
    assert duration_ms(d(True)) is None
    assert duration_ms(d(-1)) is None
    assert duration_ms(None) is None


def test_an_abandoned_delivery_is_recognised_from_either_column():
    assert timed_out({"status": "timed out", "duration": None})
    assert timed_out({"status": "Timed Out", "duration": 2.0})
    assert timed_out({"status": "", "duration": 10.0})
    assert not timed_out(d(1.0))
    assert not timed_out(None)


def test_each_delivery_is_sorted_by_the_room_it_had_left():
    assert classify(d(9.5)) == "at-risk"
    assert classify(d(6.0)) == "slow"
    assert classify(d(0.4)) == "fine"
    assert classify(d(10.0)) == "timed-out"
    assert classify(d(None)) == "unknown"


def test_the_percentile_is_nearest_rank_and_never_invents_a_value():
    values = [100, 200, 300, 400]
    assert percentile(values, 50) == 200
    assert percentile(values, 95) == 400
    assert percentile(values, 0) == 100
    assert percentile([], 95) is None
    assert percentile([7], 95) == 7


def test_a_window_with_no_failures_and_a_nine_second_tail_is_a_finding():
    rows = [d(0.5)] * 18 + [d(9.1)] * 2
    st = stats(rows)
    assert st["timed_out"] == 0
    state, detail = verdict(st)
    assert state == "at-the-edge"
    assert "fails on the next slow week" in detail
    assert "return 202" in repair(state)


def test_a_fast_receiver_is_left_alone():
    st = stats([d(0.2)] * 50)
    assert verdict(st)[0] == "healthy"
    assert repair("healthy").startswith("nothing")


def test_timeouts_are_reported_with_the_headroom_on_everything_else():
    rows = [d(0.5)] * 90 + [{"status": "timed out", "event": "push"}] * 10
    st = stats(rows)
    assert st["timed_out"] == 10
    state, detail = verdict(st)
    assert state == "timing-out"
    assert "10 deliveries were abandoned" in detail


def test_an_empty_window_is_never_reported_as_healthy():
    state, detail = verdict(stats([]))
    assert state == "no-data"
    assert "not the same as a receiver that is fast" in detail


def test_a_window_with_statuses_but_no_timings_says_so():
    state, _ = verdict(stats([{"event": "push", "status": "OK"}] * 5))
    assert state == "no-durations"


def test_the_grouping_finds_the_handler_to_fix_first():
    rows = ([d(9.4, "push")] * 5 + [d(0.3, "issues")] * 5)
    worst = slowest_event(rows)
    assert worst["event"] == "push"
    assert worst["p95"] == 9400.0
    assert "Start with push" in repair("slow", worst)


def test_a_rare_event_is_kept_when_it_timed_out():
    rows = [d(0.2, "issues")] * 5 + [{"event": "release", "status": "timed out"}]
    grouped = by_event(rows)
    assert "release" in grouped
    assert grouped["release"]["timed_out"] == 1


def test_the_cursor_is_read_from_the_link_header():
    header = ('<https://api.github.com/repos/a/b/hooks/1/deliveries?cursor=v2>; '
              'rel="next"')
    assert next_link({"Link": header}).endswith("cursor=v2")
    assert next_link({"Link": '<https://x>; rel="prev"'}) is None
    assert next_link({}) is None
''',
"test_js_file": "github-hook-delivery-duration.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  byEvent, classify, durationMs, nextLink, percentile, repair,
  slowestEvent, stats, timedOut, verdict,
} from './github-hook-delivery-duration.mjs';

const d = (duration, event = 'push', status = 'OK') => ({ duration, event, status });

test('seconds and milliseconds both normalise to milliseconds', () => {
  assert.equal(durationMs(d(0.62)), 620);
  assert.equal(durationMs(d(9.87)), 9870);
  assert.equal(durationMs(d(9870)), 9870);
  assert.equal(durationMs(d(60)), 60000);
  assert.equal(durationMs(d(61)), 61);
});

test('an unreadable duration is null rather than zero', () => {
  assert.equal(durationMs(d(null)), null);
  assert.equal(durationMs(d('slow')), null);
  assert.equal(durationMs(d(true)), null);
  assert.equal(durationMs(d(-1)), null);
  assert.equal(durationMs(null), null);
});

test('an abandoned delivery is recognised from either column', () => {
  assert.ok(timedOut({ status: 'timed out', duration: null }));
  assert.ok(timedOut({ status: 'Timed Out', duration: 2.0 }));
  assert.ok(timedOut({ status: '', duration: 10.0 }));
  assert.ok(!timedOut(d(1.0)));
  assert.ok(!timedOut(null));
});

test('each delivery is sorted by the room it had left', () => {
  assert.equal(classify(d(9.5)), 'at-risk');
  assert.equal(classify(d(6.0)), 'slow');
  assert.equal(classify(d(0.4)), 'fine');
  assert.equal(classify(d(10.0)), 'timed-out');
  assert.equal(classify(d(null)), 'unknown');
});

test('the percentile is nearest rank and never invents a value', () => {
  const values = [100, 200, 300, 400];
  assert.equal(percentile(values, 50), 200);
  assert.equal(percentile(values, 95), 400);
  assert.equal(percentile(values, 0), 100);
  assert.equal(percentile([], 95), null);
  assert.equal(percentile([7], 95), 7);
});

test('a window with no failures and a nine second tail is a finding', () => {
  const rows = [...Array(18).fill(d(0.5)), ...Array(2).fill(d(9.1))];
  const st = stats(rows);
  assert.equal(st.timed_out, 0);
  const [state, detail] = verdict(st);
  assert.equal(state, 'at-the-edge');
  assert.match(detail, /fails on the next slow week/);
  assert.match(repair(state), /return 202/);
});

test('a fast receiver is left alone', () => {
  assert.equal(verdict(stats(Array(50).fill(d(0.2))))[0], 'healthy');
  assert.ok(repair('healthy').startsWith('nothing'));
});

test('timeouts are reported with the headroom on everything else', () => {
  const rows = [
    ...Array(90).fill(d(0.5)),
    ...Array(10).fill({ status: 'timed out', event: 'push' }),
  ];
  const st = stats(rows);
  assert.equal(st.timed_out, 10);
  const [state, detail] = verdict(st);
  assert.equal(state, 'timing-out');
  assert.match(detail, /10 deliveries were abandoned/);
});

test('an empty window is never reported as healthy', () => {
  const [state, detail] = verdict(stats([]));
  assert.equal(state, 'no-data');
  assert.match(detail, /not the same as a receiver that is fast/);
});

test('a window with statuses but no timings says so', () => {
  const rows = Array(5).fill({ event: 'push', status: 'OK' });
  assert.equal(verdict(stats(rows))[0], 'no-durations');
});

test('the grouping finds the handler to fix first', () => {
  const rows = [...Array(5).fill(d(9.4, 'push')), ...Array(5).fill(d(0.3, 'issues'))];
  const worst = slowestEvent(rows);
  assert.equal(worst.event, 'push');
  assert.equal(worst.p95, 9400);
  assert.match(repair('slow', worst), /Start with push/);
});

test('a rare event is kept when it timed out', () => {
  const rows = [
    ...Array(5).fill(d(0.2, 'issues')),
    { event: 'release', status: 'timed out' },
  ];
  const grouped = byEvent(rows);
  assert.ok('release' in grouped);
  assert.equal(grouped.release.timed_out, 1);
});

test('the cursor is read from the Link header', () => {
  const header = '<https://api.github.com/repos/a/b/hooks/1/deliveries?cursor=v2>; rel="next"';
  assert.ok(nextLink({ Link: header }).endsWith('cursor=v2'));
  assert.equal(nextLink({ Link: '<https://x>; rel="prev"' }), null);
  assert.equal(nextLink({}), null);
});
''',
"faq": [
 ("Is the ten seconds measured on my handler or on the whole request?",
  "The whole thing, from GitHub's side of the connection. DNS, the TLS handshake, whatever queueing happens in your load balancer or ingress, a cold start if the receiver is serverless, the handler itself, and the response on the way back. That is why a handler which times itself at eight seconds can still be recorded as a timeout, and why the durations in the deliveries feed are the numbers worth arguing from: they are the only ones that include everything the cutoff includes."),
 ("How is this different from auditing failed deliveries?",
  "Same request, different column, different question. A failure audit groups by status code and tells you what is broken, which matters because a 401 and a 500 have nothing in common. This one ignores status codes apart from the abandonment marker and reads the duration on every delivery, including the successful ones, so it can tell you a receiver is two seconds from the cutoff while the failure count is still zero. Run both; they catch different halves."),
 ("Why not just send a request at the receiver and time it?",
  "Two reasons. It is a write, and these scripts do not write. And it would be a worse measurement even if they did: a synthetic payload does not do the work a real one does, your receiver may reject an unsigned request in a millisecond, and you would be timing from wherever the script runs rather than from wherever GitHub does. Every number this check needs has already been recorded by the party whose clock actually decides."),
 ("The handler finished successfully. Does the work count?",
  "Your work happened; the delivery still failed. GitHub stopped waiting at ten seconds and recorded a failure, which means it may redeliver, which means the same expensive work runs again. So the honest answer is that a timed-out delivery leaves you in the worst state available: the side effects happened, nothing acknowledges them, and a replay is on its way. Keying the worker on the delivery guid is what makes that survivable."),
 ("What does a good synchronous path actually look like?",
  "Read the body, verify the signature over the raw bytes, write the payload to a queue or a durable table, return 202. Nothing else, and no network call to anything except the queue. Everything the handler used to do moves into a worker that can take as long as it needs, retry on its own schedule, and skip a delivery guid it has already processed. The measurable effect is that the 95th percentile stops tracking the size of the repository, which is the whole reason this problem grows over time."),
],
"related": [
 ("/github/webhook-deliveries-failing/", "Deliveries failing where nobody reads the log"),
 ("/github/duplicate-webhooks/", "The same URL registered twice"),
 ("/github/polling-instead-of-webhooks/", "Polling where a webhook would do"),
],
"citations": [CITE_TROUBLESHOOT, CITE_FAILED_DELIVERIES, CITE_REPO_HOOKS, CITE_WEBHOOK_BEST],
},

{
"slug": "webhook-wildcard-events",
"title": "The hook subscribes to every event with a wildcard",
"description": "A hook set to * receives everything GitHub has and everything it ships next. Nothing fails: the receiver pays for payloads it throws away.",
"h1": "the hook subscribes to every event with a wildcard",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github webhook wildcard events star",
             "github webhook subscribe to all events",
             "webhook receiver discarding payloads volume",
             "github hook events array asterisk",
             "reduce github webhook delivery volume"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The hook was set up in a hurry, with <code>*</code> in the events list, because nobody was sure yet which events the integration would need. That was two years ago. The receiver now handles four event types and is delivered somewhere north of forty, and every one of the ones it does not want still arrives, still gets its signature verified, and is still thrown away. Nothing has ever failed.",
"short_answer": """<p><code>events: ["*"]</code> subscribes the hook to every event type GitHub currently has <em>and</em> every event type it adds in future. There is no error and no failure: the hook does precisely what it was configured to do. The cost is volume &mdash; deliveries you pay to receive, authenticate and discard &mdash; and it grows on GitHub's release schedule rather than yours.</p>
<p>Read <code>GET /repos/{owner}/{repo}/hooks</code> and look for <code>*</code> in the <code>events</code> array. Then quantify it: count the deliveries by event over the retained window and work out what fraction came from events your handlers do not implement. That fraction is the finding, and it is usually large, because the highest-volume events on a busy repository &mdash; <code>push</code>, <code>status</code>, <code>check_run</code>, <code>workflow_job</code> &mdash; are rarely the ones a small integration cares about. The repair is a list, and the script can print it in full: the explicit set of events the receiver actually handles.</p>""",
"problem": """<p>Nothing draws attention to it, because nothing is wrong. There is no error rate to alert on, no failed delivery, no 4xx, no queue backing up in a way anybody has noticed. Every dashboard is green. A configuration that is quietly three times more expensive than it needs to be produces exactly the same monitoring signal as one that is right, which is why this survives audits that were genuinely looking for problems.</p>
<p>The cost shows up somewhere else, wearing a disguise. The receiver is a little slower than it should be, the bill for whatever runs it is a little higher, and when somebody eventually profiles it, the time is going into signature verification and JSON parsing of payloads that are discarded on the next line. That reads as a performance problem in the receiver, and it gets fixed as one: a faster parser, a bigger instance, more workers. The volume itself is treated as a given.</p>
<p>The part that makes it grow is that nobody revisits it. A wildcard subscription is a standing agreement to receive event types that did not exist when the agreement was made. Every time GitHub ships a new event, the firehose widens on its own, and the change arrives in production without a deploy, a review or a note in anybody's changelog. The volume in six months is not a number anybody chose.</p>""",
"why": """<p><strong>The wildcard is open ended by design.</strong> It does not expand to the list of events at the moment you save it; it means all events, evaluated at delivery time. That is a useful property for a mirror or an audit sink and a liability for anything else, because it means the subscription changes without you.</p>
<p><strong>The expensive events are rarely the interesting ones.</strong> Volume on a repository is dominated by pushes, statuses and CI events, and those payloads are large. An integration that cares about issues and pull requests receives all of it anyway, and the ratio gets worse the busier and healthier the repository is. Growth in the team makes the waste grow with it.</p>
<p><strong>Every delivery has a fixed cost before you know what it is.</strong> The connection, the body read, the signature computed over the raw bytes, the parse. Only after all of that can the handler discard the event. So the cost of an unwanted delivery is not zero and it is not small; it is most of the cost of a wanted one.</p>
<p><strong>It is the opposite failure to an unsubscribed event.</strong> <a href="/github/webhook-event-not-subscribed/">That note</a> looks for events in your code that are missing from the hook, where the symptom is a handler that never runs. This one looks in the other direction: events on the hook that are missing from your code, where the symptom is nothing at all. Same two sets, subtracted the other way round, and the reason both notes exist is that one of them has a symptom and the other has to be gone looking for.</p>
<p><strong>Data leaves GitHub either way.</strong> A wildcard hook sends your repository's activity &mdash; commit messages, branch names, issue bodies, review comments &mdash; to your endpoint whether or not anything reads it. Narrowing the subscription is a reduction in what crosses the boundary, which is worth saying out loud when the alternative is a conversation about parser performance.</p>""",
"steps": [
 {"h": "Find the wildcards",
  "body": """<p><code>GET /repos/{owner}/{repo}/hooks</code>, and the organization equivalent if you have org read. A hook whose <code>events</code> array contains <code>*</code> is the finding; it does not matter what else is in the array, because the wildcard subsumes it.</p>"""},
 {"h": "Count what actually arrives",
  "body": """<p>Page the deliveries feed and tally by <code>event</code>. This turns an abstract objection into a number: five hundred deliveries in the window, of which four hundred and ten were <code>push</code>, <code>status</code> and <code>check_run</code>, none of which the receiver implements. That is the sentence that gets the change approved.</p>"""},
 {"h": "State the fraction, not the count",
  "body": """<p>Deliveries the receiver discards, divided by all deliveries. A count depends on how long the window is and how busy the week was; a fraction does not, and it is comparable between repositories. Report both, lead with the fraction.</p>"""},
 {"h": "Write the explicit list",
  "body": """<p>Replace <code>*</code> with the events your handlers implement. The script prints the list, so the repair is a copy rather than an exercise. Include the events you handle but did not see in the window: an event that has not fired recently is not an event you do not need, and pruning on observation alone is how a release handler stops working three months later.</p>"""},
 {"h": "Decide deliberately about new events",
  "body": """<p>The wildcard's one genuine feature is that new event types arrive automatically. If you actually want that &mdash; a mirror, a compliance sink, an event lake &mdash; keep it, and say so in the code so the next audit does not undo it. If you do not, then adding a new event type should be a change somebody makes on purpose, which is what the explicit list buys.</p>"""},
],
"verify": """<p>After the list replaces the wildcard, the same read shows the subscription bounded and the discarded fraction at zero, with no change to the events the receiver actually uses.</p>
<pre><code class="language-bash">GITHUB_TOKEN=$READ_ONLY_TOKEN python3 github_hook_event_volume.py \\
  --repo acme-corp/platform --handles issues,pull_request,pull_request_review
# hook 517238001 -> https://hooks.example.com/github
# subscribed: * (wildcard)
# 500 deliveries in the window across 11 event type(s)
# wildcard: 410 of 500 deliveries (82.0%) were events this receiver does not
# implement, and * also subscribes to every event type GitHub ships next
# repair: replace ["*"] with
#   ["issues", "pull_request", "pull_request_review"]

# after the hook is narrowed
# tight: every subscribed event is one the receiver implements</code></pre>""",
"code_intro": "One GET for the hooks, a cursor-paginated GET for the deliveries, and the rest is set arithmetic in the direction nobody runs it: subscribed minus handled, rather than handled minus subscribed. The tally is the part that turns an opinion into a number, and the proposal function is the deliverable &mdash; it normalises, drops the wildcard, deduplicates and sorts, so the output is a list you can paste rather than a principle you have to apply. The one judgement encoded in it is that a handled event with no deliveries in the window stays on the list.",
"py_file": "github_hook_event_volume.py",
"py": '''"""Quantify what a wildcard webhook subscription costs a receiver.

Read only. GETs the repository's hooks and their delivery records, tallies the
deliveries by event type, and reports the fraction that came from events the
receiver does not implement. Nothing is created, edited or deleted: the script
prints the explicit events list to install in place of the wildcard.

A hook configured with ["*"] receives every event type GitHub has and every one
it adds afterwards. Nothing fails. The cost is volume, paid on every delivery
before the handler can decide it does not want it, and it grows on GitHub's
release schedule rather than yours.

This is the opposite comparison to an unsubscribed-event check. That one looks
for events in your code that are missing from the hook. This one looks for
events on the hook that are missing from your code.

Environment:

    GITHUB_TOKEN            a read-only token with access to the repository
    GITHUB_HANDLED_EVENTS   comma separated events your receiver implements
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_hook_event_volume")

API = "https://api.github.com"
UA = "github-hook-event-volume/1.0"

WILDCARD = "*"


def normalize(name):
    """One event name, lowercased and trimmed. Pure.

    Deliberately narrow: case and surrounding space only. A genuinely misspelled
    event name should stay visible as itself rather than be quietly corrected
    into something that looks subscribed.
    """
    return str(name or "").strip().lower()


def subscribed(hook):
    """The normalised events array on a hook. Pure."""
    if not isinstance(hook, dict):
        return []
    events = hook.get("events")
    if not isinstance(events, list):
        return []
    return [e for e in (normalize(x) for x in events) if e]


def is_wildcard(events):
    """Whether this subscription is open ended. Pure."""
    return WILDCARD in {normalize(e) for e in (events or [])}


def handled_set(names):
    """The events a receiver implements, as a normalised set. Pure."""
    if isinstance(names, str):
        names = names.replace(";", ",").split(",")
    return {e for e in (normalize(n) for n in (names or [])) if e and e != WILDCARD}


def tally(rows):
    """Deliveries by event type. Pure."""
    counts = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        event = normalize(row.get("event")) or "unknown"
        counts[event] = counts.get(event, 0) + 1
    return counts


def waste(counts, handled):
    """How much of the delivered volume the receiver discards. Pure."""
    counts = counts or {}
    handled = handled_set(handled)
    total = sum(counts.values())
    unwanted = {e: n for e, n in counts.items() if e not in handled}
    discarded = sum(unwanted.values())
    return {"total": total,
            "unhandled_deliveries": discarded,
            "unhandled_events": sorted(unwanted),
            "share": round(100.0 * discarded / total, 1) if total else 0.0}


def proposed_events(handled):
    """The explicit events list to install in place of the wildcard. Pure.

    Built from what the receiver implements rather than from what happened to
    arrive. An event that has not fired during the retained window is not an
    event you do not need, and pruning on observation alone is how a release
    handler stops working three months later.
    """
    return sorted(handled_set(handled))


def never_seen(counts, handled):
    """Handled events with no deliveries in the window. Pure.

    Reported as a caution, never as a reason to drop them.
    """
    counts = counts or {}
    return sorted(e for e in handled_set(handled) if not counts.get(e))


def verdict(events, counts, handled):
    """Turn the subscription and the volume into a finding. Pure."""
    subs = {e for e in (normalize(x) for x in (events or [])) if e}
    wanted = handled_set(handled)
    if WILDCARD in subs:
        w = waste(counts, wanted)
        if not w["total"]:
            return ("wildcard-unmeasured",
                    "this hook subscribes to every event with *, and no "
                    "deliveries in the retained window let the volume be "
                    "measured. The subscription is open ended either way: "
                    "every event type GitHub ships next joins it.")
        if w["unhandled_deliveries"]:
            return ("wildcard",
                    "%d of %d deliveries (%.1f%%) were events this receiver "
                    "does not implement, and * also subscribes to every event "
                    "type GitHub ships next."
                    % (w["unhandled_deliveries"], w["total"], w["share"]))
        return ("wildcard-all-handled",
                "every delivery in the window happened to be an event this "
                "receiver implements, which is luck rather than design: * "
                "subscribes to event types that do not exist yet.")
    extra = sorted(subs - wanted)
    if extra:
        return ("over-subscribed",
                "this hook subscribes to %d event(s) the receiver does not "
                "implement: %s." % (len(extra), ", ".join(extra)))
    if not subs:
        return ("no-events",
                "this hook has an empty events array, so nothing is delivered "
                "to it at all.")
    return ("tight", "every subscribed event is one the receiver implements.")


def repair(state, handled=None, counts=None):
    """The sentence a reader has to act on. Pure."""
    listing = json.dumps(proposed_events(handled))
    if state in ("wildcard", "wildcard-unmeasured", "wildcard-all-handled"):
        caution = ""
        pending = never_seen(counts, handled)
        if pending:
            caution = (" Keep %s on the list even though nothing arrived for "
                       "them in this window." % ", ".join(pending))
        return ("replace [\\"*\\"] with %s, which bounds the subscription and "
                "stops new event types joining it without a decision.%s"
                % (listing, caution))
    if state == "over-subscribed":
        return ("narrow the events array to %s. Nothing is failing; this is "
                "volume the receiver pays for and discards." % listing)
    if state == "no-events":
        return ("add the events the receiver implements: %s. An empty array "
                "delivers nothing." % listing)
    return "nothing. The subscription matches what the receiver handles."


def next_link(headers):
    """The rel=next URL from a Link header, or None. Pure."""
    link = (headers or {}).get("Link") or (headers or {}).get("link") or ""
    for part in str(link).split(","):
        url = part.split(";")[0].strip()
        if 'rel="next"' in part and url.startswith("<") and url.endswith(">"):
            return url[1:-1]
    return None


def get(session, url):
    """One GET. Returns (status, json-or-None, headers)."""
    full = API + url if url.startswith("/") else url
    r = session.get(full, timeout=30)
    try:
        body = r.json()
    except ValueError:
        body = None
    return r.status_code, body, r.headers


def deliveries(session, owner, repo, hook_id, pages=8):
    """Delivery records for one hook, following the cursor. Read only."""
    url = "/repos/%s/%s/hooks/%s/deliveries?per_page=100" % (owner, repo, hook_id)
    out = []
    for _ in range(pages):
        status, body, headers = get(session, url)
        if status != 200 or not isinstance(body, list):
            log.error("deliveries for hook %s returned %d", hook_id, status)
            break
        out.extend(body)
        url = next_link(headers)
        if not url:
            break
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repo", required=True, help="owner/repo")
    ap.add_argument("--handles", default=os.environ.get("GITHUB_HANDLED_EVENTS", ""),
                    help="comma separated events the receiver implements")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN to a read-only token that can read the "
                  "repository's hooks")
        return 2
    if "/" not in args.repo:
        log.error("--repo takes owner/repo")
        return 2
    handled = handled_set(args.handles)
    if not handled:
        log.error("pass --handles with the events your receiver implements; "
                  "without them there is nothing to compare the hook against")
        return 2
    owner, repo = args.repo.split("/", 1)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    status, hooks, _ = get(session, "/repos/%s/%s/hooks?per_page=100" % (owner, repo))
    if status != 200 or not isinstance(hooks, list):
        log.error("GET hooks returned %d", status)
        return 2

    findings = []
    for hook in hooks:
        hook_id = hook.get("id")
        url = (hook.get("config") or {}).get("url", "?")
        events = subscribed(hook)
        log.info("hook %s -> %s", hook_id, url)
        log.info("subscribed: %s", "* (wildcard)" if is_wildcard(events)
                 else ", ".join(events) or "nothing")
        rows = deliveries(session, owner, repo, hook_id)
        counts = tally(rows)
        log.info("%d deliveries in the window across %d event type(s)",
                 sum(counts.values()), len(counts))
        state, detail = verdict(events, counts, handled)
        log.info("%s: %s", state, detail)
        log.info("repair: %s", repair(state, handled, counts))
        findings.append({"hook_id": hook_id, "url": url, "events": events,
                         "wildcard": is_wildcard(events), "state": state,
                         "detail": detail, "counts": counts,
                         "waste": waste(counts, handled),
                         "proposed_events": proposed_events(handled),
                         "handled_but_unseen": never_seen(counts, handled)})

    print(json.dumps({"repo": args.repo, "handled": sorted(handled),
                      "hooks": findings}, indent=2, default=str))
    return 1 if any(f["state"] != "tight" for f in findings) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-hook-event-volume.mjs",
"js": '''/**
 * Quantify what a wildcard webhook subscription costs a receiver.
 *
 * Read only. GETs the repository's hooks and their delivery records, tallies
 * the deliveries by event type, and reports the fraction that came from events
 * the receiver does not implement. Nothing is created, edited or removed: the
 * script prints the explicit events list to install in place of the wildcard.
 *
 * Environment:
 *   GITHUB_TOKEN           a read-only token with access to the repository
 *   GITHUB_REPO            owner/repo
 *   GITHUB_HANDLED_EVENTS  comma separated events the receiver implements
 */
const API = 'https://api.github.com';
const UA = 'github-hook-event-volume/1.0';

export const WILDCARD = '*';

/** One event name, lowercased and trimmed. Pure. */
export function normalize(name) {
  return String(name ?? '').trim().toLowerCase();
}

/** The normalised events array on a hook. Pure. */
export function subscribed(hook) {
  if (!hook || typeof hook !== 'object' || !Array.isArray(hook.events)) return [];
  return hook.events.map(normalize).filter(Boolean);
}

/** Whether this subscription is open ended. Pure. */
export function isWildcard(events) {
  return (events || []).map(normalize).includes(WILDCARD);
}

/** The events a receiver implements, as a normalised set. Pure. */
export function handledSet(names) {
  const list = typeof names === 'string' ? names.replace(/;/g, ',').split(',') : (names || []);
  return new Set([...list].map(normalize).filter((e) => e && e !== WILDCARD));
}

/** Deliveries by event type. Pure. */
export function tally(rows) {
  const counts = {};
  for (const row of rows || []) {
    if (!row || typeof row !== 'object') continue;
    const event = normalize(row.event) || 'unknown';
    counts[event] = (counts[event] || 0) + 1;
  }
  return counts;
}

/** How much of the delivered volume the receiver discards. Pure. */
export function waste(counts, handled) {
  const table = counts || {};
  const wanted = handledSet(handled instanceof Set ? [...handled] : handled);
  const total = Object.values(table).reduce((a, b) => a + b, 0);
  const unwanted = Object.entries(table).filter(([e]) => !wanted.has(e));
  const discarded = unwanted.reduce((a, [, n]) => a + n, 0);
  return {
    total,
    unhandled_deliveries: discarded,
    unhandled_events: unwanted.map(([e]) => e).sort(),
    share: total ? Math.round((1000 * discarded) / total) / 10 : 0,
  };
}

/** The explicit events list to install in place of the wildcard. Pure. */
export function proposedEvents(handled) {
  return [...handledSet(handled instanceof Set ? [...handled] : handled)].sort();
}

/** Handled events with no deliveries in the window. Pure. */
export function neverSeen(counts, handled) {
  const table = counts || {};
  return [...handledSet(handled instanceof Set ? [...handled] : handled)]
    .filter((e) => !table[e]).sort();
}

/** Turn the subscription and the volume into a finding. Pure. */
export function verdict(events, counts, handled) {
  const subs = new Set((events || []).map(normalize).filter(Boolean));
  const wanted = handledSet(handled instanceof Set ? [...handled] : handled);
  if (subs.has(WILDCARD)) {
    const w = waste(counts, wanted);
    if (!w.total) {
      return ['wildcard-unmeasured',
        'this hook subscribes to every event with *, and no deliveries in the '
        + 'retained window let the volume be measured. The subscription is open '
        + 'ended either way: every event type GitHub ships next joins it.'];
    }
    if (w.unhandled_deliveries) {
      return ['wildcard',
        `${w.unhandled_deliveries} of ${w.total} deliveries (${w.share.toFixed(1)}%) `
        + 'were events this receiver does not implement, and * also subscribes to '
        + 'every event type GitHub ships next.'];
    }
    return ['wildcard-all-handled',
      'every delivery in the window happened to be an event this receiver '
      + 'implements, which is luck rather than design: * subscribes to event '
      + 'types that do not exist yet.'];
  }
  const extra = [...subs].filter((e) => !wanted.has(e)).sort();
  if (extra.length) {
    return ['over-subscribed',
      `this hook subscribes to ${extra.length} event(s) the receiver does not `
      + `implement: ${extra.join(', ')}.`];
  }
  if (!subs.size) {
    return ['no-events',
      'this hook has an empty events array, so nothing is delivered to it at all.'];
  }
  return ['tight', 'every subscribed event is one the receiver implements.'];
}

/** The sentence a reader has to act on. Pure. */
export function repair(state, handled = null, counts = null) {
  const listing = JSON.stringify(proposedEvents(handled));
  if (['wildcard', 'wildcard-unmeasured', 'wildcard-all-handled'].includes(state)) {
    const pending = neverSeen(counts, handled);
    const caution = pending.length
      ? ` Keep ${pending.join(', ')} on the list even though nothing arrived for them in this window.`
      : '';
    return `replace ["*"] with ${listing}, which bounds the subscription and stops `
      + `new event types joining it without a decision.${caution}`;
  }
  if (state === 'over-subscribed') {
    return `narrow the events array to ${listing}. Nothing is failing; this is `
      + 'volume the receiver pays for and discards.';
  }
  if (state === 'no-events') {
    return `add the events the receiver implements: ${listing}. An empty array `
      + 'delivers nothing.';
  }
  return 'nothing. The subscription matches what the receiver handles.';
}

/** The rel=next URL from a Link header, or null. Pure. */
export function nextLink(headers) {
  const link = (headers && (headers.get ? headers.get('link') : headers.Link || headers.link)) || '';
  for (const part of String(link).split(',')) {
    const url = part.split(';')[0].trim();
    if (part.includes('rel="next"') && url.startsWith('<') && url.endsWith('>')) {
      return url.slice(1, -1);
    }
  }
  return null;
}

function headersFor(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function get(token, url) {
  const res = await fetch(url.startsWith('/') ? API + url : url, { headers: headersFor(token) });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body, headers: res.headers };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  const repo = process.env.GITHUB_REPO;
  const handled = handledSet(process.env.GITHUB_HANDLED_EVENTS || '');
  if (!token || !repo || !repo.includes('/') || !handled.size) {
    console.error('set GITHUB_TOKEN, GITHUB_REPO=owner/repo and GITHUB_HANDLED_EVENTS');
    process.exitCode = 2;
    return;
  }
  const [owner, name] = repo.split('/');
  const hooksRes = await get(token, `/repos/${owner}/${name}/hooks?per_page=100`);
  if (hooksRes.status !== 200 || !Array.isArray(hooksRes.body)) {
    console.error(`GET hooks returned ${hooksRes.status}`);
    process.exitCode = 2;
    return;
  }

  const findings = [];
  for (const hook of hooksRes.body) {
    const events = subscribed(hook);
    console.log(`hook ${hook.id} -> ${(hook.config || {}).url || '?'}`);
    console.log(`subscribed: ${isWildcard(events) ? '* (wildcard)' : events.join(', ') || 'nothing'}`);
    const rows = [];
    let url = `/repos/${owner}/${name}/hooks/${hook.id}/deliveries?per_page=100`;
    for (let page = 0; page < 8 && url; page += 1) {
      const res = await get(token, url);
      if (res.status !== 200 || !Array.isArray(res.body)) break;
      rows.push(...res.body);
      url = nextLink(res.headers);
    }
    const counts = tally(rows);
    const [state, detail] = verdict(events, counts, handled);
    console.log(`${state}: ${detail}`);
    console.log(`repair: ${repair(state, handled, counts)}`);
    findings.push({
      hook_id: hook.id, events, wildcard: isWildcard(events), state,
      counts, waste: waste(counts, handled), proposed_events: proposedEvents(handled),
    });
  }
  console.log(JSON.stringify({ repo, handled: [...handled].sort(), hooks: findings }, null, 2));
  process.exitCode = findings.every((f) => f.state === 'tight') ? 0 : 1;
}

// Guarded so importing this file from the test runner does not start a run.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The direction of the subtraction is the thing to pin, because the same two sets read the other way round are a different note entirely: an event the receiver handles and the hook does not carry is not this finding and must not be reported as one. After that, the wildcard has to stay a finding even in the window where every delivery happened to be wanted, the fraction has to survive an empty window without dividing by zero, and the proposed list has to keep a handled event that produced no deliveries at all.",
"test_py_file": "test_github_hook_event_volume.py",
"test_py": '''from github_hook_event_volume import (
    handled_set, is_wildcard, never_seen, next_link, normalize,
    proposed_events, repair, subscribed, tally, verdict, waste,
)

HANDLES = "issues,pull_request,release"
STAR = {"id": 1, "events": ["*"], "config": {"url": "https://hooks.example.com/gh"}}
TIGHT = {"id": 2, "events": ["Issues", " pull_request "], "config": {}}


def test_event_names_are_normalised_narrowly():
    assert normalize(" Pull_Request ") == "pull_request"
    assert normalize(None) == ""
    assert subscribed(TIGHT) == ["issues", "pull_request"]
    assert subscribed({"events": "issues"}) == []
    assert subscribed(None) == []


def test_the_wildcard_is_recognised_however_it_is_written():
    assert is_wildcard(["*"])
    assert is_wildcard(["push", " * "])
    assert not is_wildcard(["push"])
    assert not is_wildcard([])


def test_the_handled_set_drops_a_wildcard_it_is_given():
    assert handled_set("issues, *, push") == {"issues", "push"}
    assert handled_set(["Issues", "issues"]) == {"issues"}
    assert handled_set("") == set()


def test_the_tally_counts_by_event_and_names_the_unknown():
    rows = [{"event": "push"}, {"event": "Push"}, {"event": None}, "junk"]
    assert tally(rows) == {"push": 2, "unknown": 1}


def test_the_waste_is_the_fraction_the_receiver_discards():
    counts = {"push": 300, "status": 110, "issues": 90}
    w = waste(counts, HANDLES)
    assert w["total"] == 500
    assert w["unhandled_deliveries"] == 410
    assert w["share"] == 82.0
    assert w["unhandled_events"] == ["push", "status"]


def test_an_empty_window_does_not_divide_by_zero():
    assert waste({}, HANDLES) == {"total": 0, "unhandled_deliveries": 0,
                                 "unhandled_events": [], "share": 0.0}


def test_a_wildcard_with_wasted_volume_is_the_headline_finding():
    counts = {"push": 300, "status": 110, "issues": 90}
    state, detail = verdict(subscribed(STAR), counts, HANDLES)
    assert state == "wildcard"
    assert "82.0%" in detail
    assert "ships next" in detail


def test_a_wildcard_stays_a_finding_when_the_window_was_all_wanted():
    state, detail = verdict(["*"], {"issues": 12}, HANDLES)
    assert state == "wildcard-all-handled"
    assert "luck rather than design" in detail


def test_a_wildcard_with_no_deliveries_is_still_reported():
    state, detail = verdict(["*"], {}, HANDLES)
    assert state == "wildcard-unmeasured"
    assert "open ended" in detail


def test_events_the_receiver_handles_and_the_hook_omits_are_not_this_finding():
    # release is handled and not subscribed; that is the other note's problem.
    state, _ = verdict(["issues", "pull_request"], {"issues": 4}, HANDLES)
    assert state == "tight"


def test_events_on_the_hook_and_not_in_the_code_are_this_finding():
    state, detail = verdict(["issues", "push", "status"], {"push": 3}, HANDLES)
    assert state == "over-subscribed"
    assert "push, status" in detail


def test_an_empty_subscription_is_its_own_state():
    assert verdict([], {}, HANDLES)[0] == "no-events"


def test_the_proposal_keeps_a_handled_event_that_never_fired():
    assert proposed_events(HANDLES) == ["issues", "pull_request", "release"]
    assert never_seen({"issues": 3}, HANDLES) == ["pull_request", "release"]
    text = repair("wildcard", HANDLES, {"issues": 3})
    assert '["issues", "pull_request", "release"]' in text
    assert "Keep pull_request, release on the list" in text


def test_a_tight_hook_gets_no_repair():
    assert repair("tight", HANDLES).startswith("nothing")


def test_the_cursor_is_read_from_the_link_header():
    header = '<https://api.github.com/repos/a/b/hooks/1/deliveries?cursor=v2>; rel="next"'
    assert next_link({"Link": header}).endswith("cursor=v2")
    assert next_link({}) is None
''',
"test_js_file": "github-hook-event-volume.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  handledSet, isWildcard, neverSeen, nextLink, normalize,
  proposedEvents, repair, subscribed, tally, verdict, waste,
} from './github-hook-event-volume.mjs';

const HANDLES = 'issues,pull_request,release';
const STAR = { id: 1, events: ['*'], config: { url: 'https://hooks.example.com/gh' } };
const TIGHT = { id: 2, events: ['Issues', ' pull_request '], config: {} };

test('event names are normalised narrowly', () => {
  assert.equal(normalize(' Pull_Request '), 'pull_request');
  assert.equal(normalize(null), '');
  assert.deepEqual(subscribed(TIGHT), ['issues', 'pull_request']);
  assert.deepEqual(subscribed({ events: 'issues' }), []);
  assert.deepEqual(subscribed(null), []);
});

test('the wildcard is recognised however it is written', () => {
  assert.ok(isWildcard(['*']));
  assert.ok(isWildcard(['push', ' * ']));
  assert.ok(!isWildcard(['push']));
  assert.ok(!isWildcard([]));
});

test('the handled set drops a wildcard it is given', () => {
  assert.deepEqual([...handledSet('issues, *, push')].sort(), ['issues', 'push']);
  assert.deepEqual([...handledSet(['Issues', 'issues'])], ['issues']);
  assert.equal(handledSet('').size, 0);
});

test('the tally counts by event and names the unknown', () => {
  const rows = [{ event: 'push' }, { event: 'Push' }, { event: null }, 'junk'];
  assert.deepEqual(tally(rows), { push: 2, unknown: 1 });
});

test('the waste is the fraction the receiver discards', () => {
  const counts = { push: 300, status: 110, issues: 90 };
  const w = waste(counts, HANDLES);
  assert.equal(w.total, 500);
  assert.equal(w.unhandled_deliveries, 410);
  assert.equal(w.share, 82.0);
  assert.deepEqual(w.unhandled_events, ['push', 'status']);
});

test('an empty window does not divide by zero', () => {
  assert.deepEqual(waste({}, HANDLES), {
    total: 0, unhandled_deliveries: 0, unhandled_events: [], share: 0,
  });
});

test('a wildcard with wasted volume is the headline finding', () => {
  const counts = { push: 300, status: 110, issues: 90 };
  const [state, detail] = verdict(subscribed(STAR), counts, HANDLES);
  assert.equal(state, 'wildcard');
  assert.match(detail, /82\\.0%/);
  assert.match(detail, /ships next/);
});

test('a wildcard stays a finding when the window was all wanted', () => {
  const [state, detail] = verdict(['*'], { issues: 12 }, HANDLES);
  assert.equal(state, 'wildcard-all-handled');
  assert.match(detail, /luck rather than design/);
});

test('a wildcard with no deliveries is still reported', () => {
  const [state, detail] = verdict(['*'], {}, HANDLES);
  assert.equal(state, 'wildcard-unmeasured');
  assert.match(detail, /open ended/);
});

test('events the receiver handles and the hook omits are not this finding', () => {
  const [state] = verdict(['issues', 'pull_request'], { issues: 4 }, HANDLES);
  assert.equal(state, 'tight');
});

test('events on the hook and not in the code are this finding', () => {
  const [state, detail] = verdict(['issues', 'push', 'status'], { push: 3 }, HANDLES);
  assert.equal(state, 'over-subscribed');
  assert.match(detail, /push, status/);
});

test('an empty subscription is its own state', () => {
  assert.equal(verdict([], {}, HANDLES)[0], 'no-events');
});

test('the proposal keeps a handled event that never fired', () => {
  assert.deepEqual(proposedEvents(HANDLES), ['issues', 'pull_request', 'release']);
  assert.deepEqual(neverSeen({ issues: 3 }, HANDLES), ['pull_request', 'release']);
  const text = repair('wildcard', HANDLES, { issues: 3 });
  assert.ok(text.includes('["issues","pull_request","release"]'));
  assert.match(text, /Keep pull_request, release on the list/);
});

test('a tight hook gets no repair', () => {
  assert.ok(repair('tight', HANDLES).startsWith('nothing'));
});

test('the cursor is read from the Link header', () => {
  const header = '<https://api.github.com/repos/a/b/hooks/1/deliveries?cursor=v2>; rel="next"';
  assert.ok(nextLink({ Link: header }).endsWith('cursor=v2'));
  assert.equal(nextLink({}), null);
});
''',
"faq": [
 ("Is a wildcard subscription ever the right answer?",
  "Yes, for a receiver whose job is to see everything: an audit sink, an event lake, a mirror that archives activity without interpreting it. For those the open-ended property is the feature, because a new event type should join the archive automatically. What makes it wrong everywhere else is that the same property applies whether or not anybody wanted it, and a receiver with four handlers is not an archive. If you keep it deliberately, say so in the code, so the next person to audit the hook does not quietly undo the decision."),
 ("Nothing is failing. Why is this worth changing?",
  "Because the cost is real and the trend is upward. Every unwanted delivery costs a connection, a body read, a signature computed over the raw bytes and a parse, before the handler can decide it does not care; that is most of the cost of a delivery that was wanted. It also means repository content, including commit messages and issue bodies, leaves GitHub for your endpoint whether or not anything reads it. And the volume grows on GitHub's release schedule, so the number in six months is not one anybody chose."),
 ("How is this different from the note about an unsubscribed event?",
  "It is the same two sets subtracted the other way round. That note looks for events your handlers implement that the hook does not send, and its symptom is a handler that never runs. This one looks for events the hook sends that your handlers do not implement, and its symptom is nothing at all, which is why it has to be gone looking for rather than reported. A hook can easily be wrong in both directions at once, and the two findings have different repairs."),
 ("Can I build the replacement list from what actually arrived?",
  "Only as a starting point, and the script deliberately does not. The delivery window covers a limited retention period, so an event that has not fired recently looks identical to one you do not need: a release handler on a quarterly release cycle disappears from any window shorter than a quarter. Build the list from what the receiver implements, use the tally to show what the wildcard is costing, and keep the handled events that produced nothing, which the script lists separately as a caution."),
 ("What about hooks on the organization rather than the repository?",
  "The same wildcard applies and the same reasoning holds, with more volume behind it, since an org hook receives from every repository in the org. Reading them needs org-level access that a repository-scoped token does not have, which is a real blind spot: a repository audit that comes back clean says nothing about an org hook pointed at the same receiver. If you have the access, run the same check against the org hooks, and remember that a URL reached by both an org hook and a repo hook has a second problem as well."),
],
"related": [
 ("/github/webhook-event-not-subscribed/", "The hook is not subscribed to your event"),
 ("/github/duplicate-webhooks/", "The same URL registered twice"),
 ("/github/webhook-deliveries-failing/", "Deliveries failing where nobody reads the log"),
],
"citations": [CITE_REPO_HOOKS, CITE_WEBHOOK_EVENTS, CITE_CREATING_WEBHOOKS, CITE_WEBHOOK_BEST],
},

]
