#!/usr/bin/env python3
"""/github/ field notes, batch G — the writing.

Four credential notes that sit next to each other in the index and must not be
four ways of saying "your token is bad". They are not, because each one probes a
different surface and reaches a conclusion the other three cannot reach.

The first never judges a credential at all: it reads the ceilings GET
/rate_limit hands out, names the class from the shape of them, and then does
arithmetic on a pool that belongs to the repository rather than to the job. The
second asks who produced a 401, using the two different messages GitHub puts in
the body and a control request that carries no credential at all. The third
needs two credentials and a ladder of resources, because "the token expired" and
"the world changed" are the same 401 until something else runs the same requests
at the same instant. The fourth never sees a failure: it reads an expiry off a
working credential and is honest about the case where there is no header to read.

Read only throughout. Every script GETs, reports, and prints the repair.
"""

CITE_REST_LIMITS = ("Rate limits for the REST API — GitHub Docs",
                    "https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api")
CITE_RATE_ENDPOINT = ("Rate limit — GitHub REST API",
                      "https://docs.github.com/en/rest/rate-limit/rate-limit")
CITE_GRAPHQL_LIMITS = ("Rate limits and node limits for the GraphQL API — GitHub Docs",
                       "https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api")
CITE_AUTOMATIC_TOKEN = ("Automatic token authentication — GitHub Docs",
                        "https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication")
CITE_TROUBLESHOOT = ("Troubleshooting the REST API — GitHub Docs",
                     "https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api")
CITE_AUTH_REST = ("Authenticating to the REST API — GitHub Docs",
                  "https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api")
CITE_USERS = ("Users — GitHub REST API",
              "https://docs.github.com/en/rest/users/users")
CITE_MANAGING_PATS = ("Managing your personal access tokens — GitHub Docs",
                      "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens")
CITE_APP_INSTALL_AUTH = ("Authenticating as a GitHub App installation — GitHub Docs",
                         "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation")
CITE_BEST = ("Best practices for using the REST API — GitHub Docs",
             "https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api")

GUIDES = [

{
"slug": "actions-token-repo-scoped-limit",
"title": "GITHUB_TOKEN gets 1,000 an hour, shared across the repo",
"description": "The Actions token has a 1,000 an hour ceiling belonging to the repository, not the job. GET /rate_limit names the class; arithmetic names the starving job.",
"h1": "GITHUB_TOKEN gets 1,000 an hour, shared across the repo",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github_token rate limit 1000", "github actions api rate limit exceeded",
             "github_token 1000 requests per hour", "actions token rate limit per repository",
             "github actions 403 api rate limit"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The script works on your laptop. It makes about 1,400 calls, finishes in two minutes, and nobody thinks about it again until it is moved into a workflow. There it gets to roughly call 1,000 and starts collecting <code>403</code>. Same code, same repository, same endpoints. The only thing that changed is which credential is in the environment, and that credential was handed a ceiling a fifth the size of the one you tested against.",
"short_answer": """<p>The <code>GITHUB_TOKEN</code> that Actions injects is not a small personal access token. It is a different class of credential with a <strong>1,000 request an hour core ceiling</strong>, 15,000 on Enterprise Cloud, and GraphQL gets 1,000 points an hour on the same credential. A user PAT gets 5,000.</p>
<p>The part that turns a budget into an outage is that the pool is <strong>per repository</strong>, not per job or per run. Every concurrent job in the run, every matrix leg, and every other workflow that fired in the same hour draw from the same 1,000 and reset on the same clock. The script below reads <code>GET /rate_limit</code>, names the credential class from the ceilings it was given, and then costs your workflow against the pool it will actually share, so the answer is a job number rather than a shrug.</p>""",
"problem": """<p>The symptom is a workflow that fails at a different point every time. Job three is fine on Tuesday and job three is the one that dies on Wednesday, because the deciding factor is not job three: it is how much of the shared 1,000 the other jobs happened to spend first. A failure that moves is the hardest kind to attribute, and it is the natural consequence of a pool with several concurrent claimants.</p>
<p>It also fails the obvious test. Run the same script locally with your own token and it passes, because your own token has five times the allowance. Run it in a workflow with <code>ACTIONS_STEP_DEBUG</code> on and it still fails, because verbosity does not change arithmetic. The reproduction that works is the one nobody thinks to do: read the ceiling from inside the job.</p>
<p>And a matrix multiplies it invisibly. Four operating systems by three versions is twelve jobs, and if each one makes 120 calls that is 1,440 requests against a pool of 1,000 without a single line of the script changing. The matrix was added for coverage; it silently became a concurrency setting for your API budget.</p>""",
"why": """<p><strong>The ceiling is a property of the credential class.</strong> <code>GET /rate_limit</code> returns <code>resources.core.limit</code>, and the number is a fingerprint: 60 is anonymous, 1,000 is the Actions token, 5,000 is an authenticated user or a GitHub App installation at the floor, 15,000 is Enterprise Cloud, and anything above 5,000 that is not 15,000 is an App installation that has scaled with the repositories and users it covers.</p>
<p><strong>1,000 has a second witness.</strong> The <code>graphql</code> row is 1,000 points an hour on the same credential, and <code>GET /user</code> answers <code>403</code> rather than <code>200</code>, because the Actions token is not a user. Two independent signals agreeing is what turns "probably an Actions token" into a finding, and the script reports which of them it got.</p>
<p><strong>The pool belongs to the repository.</strong> This is the sentence that explains the moving failure. Concurrency does not buy you more allowance; it spends the same allowance faster. Twelve jobs at 120 calls is one budget of 1,440, not twelve budgets of 120.</p>
<p><strong>Reading <code>remaining</code> from inside the job is the only honest headroom.</strong> The limit is what you would have had at the top of the hour. What you actually have is what the rest of the repository has left you, and only a call made in the job can see it.</p>
<p><strong>Raising the ceiling is the last move, not the first.</strong> A GitHub App installation lifts the floor to 5,000 and scales beyond it, which is the documented answer for API-heavy automation. But a job that needs 1,400 REST calls to build one summary usually needs four GraphQL queries instead, and conditional requests make the repeats free. Spend less before you buy more.</p>""",
"steps": [
 {"h": "Read the ceiling from inside the job, not from your laptop",
  "body": """<p>Add a step that calls <code>GET /rate_limit</code> with the same credential the job uses and prints <code>resources.core.limit</code> and <code>resources.core.remaining</code>. The call is free &mdash; <code>/rate_limit</code> does not consume quota &mdash; and it is the only place the real number lives. A 1,000 here and a 5,000 on your machine is the entire explanation for "it works locally".</p>"""},
 {"h": "Corroborate the class with the graphql row and GET /user",
  "body": """<p>The <code>graphql</code> row reading 1,000 points and <code>GET /user</code> answering <code>403</code> both point at the Actions token independently of the core number. If all three agree you are done identifying and can move on to counting. If they disagree, something is injecting a different credential than you think.</p>"""},
 {"h": "Count the calls the whole run makes, not the calls one job makes",
  "body": """<p>Multiply jobs by matrix legs by calls per job. Include the jobs you do not think of as API clients: a step that posts nothing but reads a file list is still spending core requests, and an action you pulled from the marketplace spends them on your budget rather than on its own.</p>"""},
 {"h": "Cost that number against remaining, not against the limit",
  "body": """<p>If two workflows fire on the same push, the second one starts with whatever the first left. The script accepts a <code>remaining</code> value read live so the report reflects the pool as it is rather than as it was at the top of the hour, and it names the first job index that runs dry.</p>"""},
 {"h": "Spend less before raising the ceiling",
  "body": """<p>Collapse REST loops into GraphQL where you are fetching related objects, and send <code>If-None-Match</code> where you are re-fetching the same object: a <code>304</code> does not count against the primary limit. When the volume is genuinely irreducible, authenticate as a GitHub App installation instead of using the built-in token. That is a change of credential, not a change of code, and it is the documented route to a higher ceiling.</p>"""},
],
"verify": """<p>Run the check as a step in the workflow and read the class and the costing together. The line you want is the one that names a job index, because that is the number a rerun will confirm.</p>
<pre><code class="language-bash">python3 github_actions_token_budget.py --jobs 12 --calls 120
# actions-token (high): a core ceiling of 1000 an hour is the built-in Actions
#   token, and it belongs to the repository rather than to this job
# pool-overrun: 12 job(s) at 120 call(s) each is 1440 request(s) against a
#   pool of 1000 that the whole repository shares. Job 9 of 12 is the first
#   to start seeing 403.</code></pre>""",
"code_intro": "One network call produces the finding and it is <code>GET /rate_limit</code>, which spends nothing. The optional <code>GET /user</code> is used for its status code alone; the body is never read, because the interesting thing about that request is that an Actions token is refused by it. Everything after that is arithmetic on plain numbers: a classifier over the ceilings, a costing over jobs and matrix legs, and a verdict. All three are pure, so the tests can hand them a 1,000 ceiling and an already-drained pool without needing either.",
"py_file": "github_actions_token_budget.py",
"py": '''"""Cost a workflow against the request pool it shares with its own repository.

Read only. Every request is a GET. GET /rate_limit consumes no quota from any
bucket, and the optional identity probe is a single GET /user used for its
status code rather than its body.

The built-in Actions credential is not a small personal access token. It is a
different class with a 1,000 an hour core ceiling, and that ceiling belongs to
the repository rather than to the job, so every concurrent job and every matrix
leg in the run draws from the same pool on the same clock.
"""
import argparse
import json
import logging
import os
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_actions_token_budget")

API = "https://api.github.com"
UA = "github-actions-token-budget/1.0"

# Ceilings that identify a credential class outright. 5000 is deliberately not
# in here: it is both the authenticated-user allowance and the floor for a
# GitHub App installation, so on its own it names two things and settles none.
ACTIONS_CEILING = 1000
ANON_CEILING = 60
ENTERPRISE_CEILING = 15000
USER_CEILING = 5000


def classify(core_limit, graphql_limit=None, user_status=None):
    """Name the credential class from the ceilings it was handed. Pure.

    Returns (klass, confidence, note). Confidence matters here because one of
    the numbers is genuinely ambiguous and pretending otherwise sends people
    looking for an App installation they do not have.
    """
    try:
        core = int(core_limit)
    except (TypeError, ValueError):
        return ("unknown", "none",
                "GET /rate_limit reported no core limit, so there is no ceiling "
                "to cost anything against")

    if core <= 0:
        return ("unknown", "none", "a core limit of %d is not a ceiling" % core)
    if core <= ANON_CEILING:
        return ("anonymous", "high",
                "a core ceiling of %d is the anonymous tier, counted per "
                "originating IP address. No credential is reaching GitHub" % core)
    if core == ACTIONS_CEILING:
        seconds = []
        if user_status == 403:
            seconds.append("GET /user answered 403, which a user token never does")
        try:
            if int(graphql_limit) == ACTIONS_CEILING:
                seconds.append("the graphql row is 1000 points as well")
        except (TypeError, ValueError):
            pass
        note = ("a core ceiling of 1000 an hour is the built-in Actions token, "
                "and it belongs to the repository rather than to this job")
        if seconds:
            note += ". " + "; ".join(seconds)
        return ("actions-token", "high" if seconds else "likely", note)
    if core == ENTERPRISE_CEILING:
        return ("enterprise-user", "likely",
                "15000 an hour is a user on GitHub Enterprise Cloud")
    if core == USER_CEILING:
        return ("user-or-app", "ambiguous",
                "5000 an hour is an authenticated user token or a GitHub App "
                "installation still at the floor; the number names two things "
                "and settles neither")
    if core > USER_CEILING:
        return ("app-installation", "likely",
                "%d an hour is above the 5000 floor, which only a GitHub App "
                "installation scaled by repositories and users reaches" % core)
    return ("unknown", "none",
            "a core ceiling of %d does not match a documented class" % core)


def plan(jobs, calls_per_job, matrix_legs=1, ceiling=ACTIONS_CEILING, remaining=None):
    """What one workflow run costs against a pool the repository shares. Pure.

    `remaining` is the honest input and `ceiling` is the optimistic one: the
    limit is what you would have had at the top of the hour, and remaining is
    what the rest of the repository left you. The source is reported so a reader
    can tell which number the verdict was built on.
    """
    def whole(value, floor=0):
        try:
            return max(floor, int(value))
        except (TypeError, ValueError):
            return floor

    legs = max(1, whole(matrix_legs, 1))
    count = whole(jobs)
    calls = whole(calls_per_job)
    ceiling = max(1, whole(ceiling, 1))

    effective = count * legs
    total = effective * calls
    if remaining is None:
        headroom, source = ceiling, "limit"
    else:
        headroom, source = whole(remaining), "remaining"

    served = effective if not calls else min(effective, headroom // calls)
    return {"legs": legs, "jobs": effective, "calls_per_job": calls,
            "total": total, "headroom": headroom, "source": source,
            "fits": total <= headroom, "jobs_served": served,
            "first_starved_job": None if total <= headroom else served + 1,
            "shortfall": max(0, total - headroom)}


def pool_reset_in(reset, now):
    """Seconds until the shared pool refills, floored at zero. Pure.

    None rather than 0 when the value is unreadable, because "refills now" and
    "I could not read the reset" must not print the same.
    """
    try:
        return max(0, int(reset) - int(now))
    except (TypeError, ValueError):
        return None


def verdict(klass, costing):
    """Turn the class and the costing into a finding. Pure."""
    if klass == "anonymous":
        return ("unauthenticated",
                "the ceiling being costed is the anonymous 60 an hour, so this "
                "is not a workflow budget problem yet: no credential is "
                "arriving at GitHub.")
    if costing["total"] == 0:
        return ("no-workflow",
                "no workflow was described, so there is nothing to cost against "
                "the %d request pool." % costing["headroom"])
    if klass != "actions-token":
        return ("different-ceiling",
                "the credential in this environment reads as %s with a ceiling "
                "of %d, not the 1000 the Actions token gets. The %d request(s) "
                "this run makes fit here and will not fit there. Run the check "
                "from inside the job." % (klass, costing["headroom"], costing["total"]))
    if not costing["fits"]:
        return ("pool-overrun",
                "%d job(s) at %d call(s) each is %d request(s) against a pool "
                "of %d that the whole repository shares. Job %d of %d is the "
                "first to start seeing 403, and any other run in the same hour "
                "moves that number down."
                % (costing["jobs"], costing["calls_per_job"], costing["total"],
                   costing["headroom"], costing["first_starved_job"], costing["jobs"]))
    if costing["total"] * 5 >= costing["headroom"] * 4:
        return ("pool-tight",
                "%d request(s) against %d is over four fifths of a pool shared "
                "with every other job and every other run in this repository "
                "within the same hour."
                % (costing["total"], costing["headroom"]))
    return ("fits",
            "%d request(s) against a shared pool of %d."
            % (costing["total"], costing["headroom"]))


def get(session, path):
    """One GET. Returns (status, json-or-None)."""
    response = session.get(API + path, timeout=30)
    try:
        body = response.json()
    except ValueError:
        body = None
    return response.status_code, body


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", type=int, default=0,
                        help="jobs in the workflow run")
    parser.add_argument("--calls", type=int, default=0,
                        help="core API requests one job makes")
    parser.add_argument("--matrix", type=int, default=1,
                        help="matrix legs each job expands into")
    parser.add_argument("--env", default="GITHUB_TOKEN",
                        help="environment variable holding the credential")
    parser.add_argument("--use-limit", action="store_true",
                        help="cost against the hourly limit rather than what "
                             "the repository has left right now")
    args = parser.parse_args()

    token = os.environ.get(args.env)
    if not token:
        log.error("set %s. Inside a workflow this is the credential Actions "
                  "injects; on a laptop it is your own, and the whole point of "
                  "this check is that the two have different ceilings", args.env)
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    status, payload = get(session, "/rate_limit")
    if status != 200:
        log.error("GET /rate_limit returned %d; without it there is no ceiling "
                  "to reason about", status)
        return 2

    resources = ((payload or {}).get("resources") or {})
    core = resources.get("core") or {}
    graphql = resources.get("graphql") or {}

    user_status, _ = get(session, "/user")
    log.info("GET /user answered %d (used as a fingerprint, not for its body)",
             user_status)

    klass, confidence, note = classify(core.get("limit"), graphql.get("limit"),
                                       user_status)
    log.info("%s (%s): %s", klass, confidence, note)
    log.info("core limit %s remaining %s, graphql limit %s remaining %s",
             core.get("limit"), core.get("remaining"),
             graphql.get("limit"), graphql.get("remaining"))

    wait = pool_reset_in(core.get("reset"), time.time())
    if wait is not None:
        log.info("the shared pool refills in %ds", wait)

    if os.environ.get("GITHUB_ACTIONS") != "true":
        log.warning("GITHUB_ACTIONS is not set to true, so this is not running "
                    "inside a workflow and the ceiling below is your laptop's, "
                    "not the one the job will get")

    ceiling = core.get("limit") or ACTIONS_CEILING
    remaining = None if args.use_limit else core.get("remaining")
    costing = plan(args.jobs, args.calls, args.matrix, ceiling, remaining)
    log.info("costed against the %s: %d request(s) against %d",
             costing["source"], costing["total"], costing["headroom"])

    state, detail = verdict(klass, costing)
    log.info("%s: %s", state, detail)

    if state in ("pool-overrun", "pool-tight"):
        log.info("repair: collapse related REST reads into one GraphQL query, "
                 "and send If-None-Match on repeats. A 304 does not count "
                 "against the primary limit.")
        log.info("repair: for volume that cannot be reduced, authenticate as a "
                 "GitHub App installation instead of the built-in token. That "
                 "lifts the floor to 5000 and scales past it.")
        log.info("repair: reduce concurrency. The pool is per repository, so "
                 "matrix legs do not each get their own budget.")

    print(json.dumps({"class": klass, "confidence": confidence,
                      "plan": costing, "state": state}, indent=2))
    return 1 if state in ("pool-overrun", "pool-tight", "unauthenticated") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-actions-token-budget.mjs",
"js": '''/**
 * Cost a workflow against the request pool it shares with its own repository.
 *
 * Read only. Every request is a GET. GET /rate_limit consumes no quota, and the
 * identity probe is a single GET /user read for its status code alone.
 *
 * The built-in Actions credential has a 1,000 an hour core ceiling and that
 * ceiling belongs to the repository, so every concurrent job and every matrix
 * leg draws from the same pool on the same clock.
 */
const API = 'https://api.github.com';
const UA = 'github-actions-token-budget/1.0';

export const ACTIONS_CEILING = 1000;
export const ANON_CEILING = 60;
export const ENTERPRISE_CEILING = 15000;
export const USER_CEILING = 5000;

/**
 * Name the credential class from the ceilings it was handed. Pure.
 * Returns [klass, confidence, note]; 5000 is reported as ambiguous because it
 * names both a user token and an App installation at the floor.
 */
export function classify(coreLimit, graphqlLimit = null, userStatus = null) {
  const core = Number.parseInt(coreLimit, 10);
  if (!Number.isFinite(core)) {
    return ['unknown', 'none',
      'GET /rate_limit reported no core limit, so there is no ceiling to cost anything against'];
  }
  if (core <= 0) return ['unknown', 'none', `a core limit of ${core} is not a ceiling`];
  if (core <= ANON_CEILING) {
    return ['anonymous', 'high',
      `a core ceiling of ${core} is the anonymous tier, counted per originating ` +
      'IP address. No credential is reaching GitHub'];
  }
  if (core === ACTIONS_CEILING) {
    const seconds = [];
    if (userStatus === 403) seconds.push('GET /user answered 403, which a user token never does');
    if (Number.parseInt(graphqlLimit, 10) === ACTIONS_CEILING) {
      seconds.push('the graphql row is 1000 points as well');
    }
    let note = 'a core ceiling of 1000 an hour is the built-in Actions token, ' +
      'and it belongs to the repository rather than to this job';
    if (seconds.length) note += `. ${seconds.join('; ')}`;
    return ['actions-token', seconds.length ? 'high' : 'likely', note];
  }
  if (core === ENTERPRISE_CEILING) {
    return ['enterprise-user', 'likely', '15000 an hour is a user on GitHub Enterprise Cloud'];
  }
  if (core === USER_CEILING) {
    return ['user-or-app', 'ambiguous',
      '5000 an hour is an authenticated user token or a GitHub App installation ' +
      'still at the floor; the number names two things and settles neither'];
  }
  if (core > USER_CEILING) {
    return ['app-installation', 'likely',
      `${core} an hour is above the 5000 floor, which only a GitHub App ` +
      'installation scaled by repositories and users reaches'];
  }
  return ['unknown', 'none', `a core ceiling of ${core} does not match a documented class`];
}

/** What one workflow run costs against a pool the repository shares. Pure. */
export function plan(jobs, callsPerJob, matrixLegs = 1,
                     ceiling = ACTIONS_CEILING, remaining = null) {
  const whole = (value, floor = 0) => {
    const n = Number.parseInt(value, 10);
    return Number.isFinite(n) ? Math.max(floor, n) : floor;
  };
  const legs = Math.max(1, whole(matrixLegs, 1));
  const count = whole(jobs);
  const calls = whole(callsPerJob);
  const cap = Math.max(1, whole(ceiling, 1));

  const effective = count * legs;
  const total = effective * calls;
  const headroom = remaining === null || remaining === undefined ? cap : whole(remaining);
  const source = remaining === null || remaining === undefined ? 'limit' : 'remaining';
  const served = calls ? Math.min(effective, Math.floor(headroom / calls)) : effective;

  return {
    legs, jobs: effective, calls_per_job: calls, total, headroom, source,
    fits: total <= headroom, jobs_served: served,
    first_starved_job: total <= headroom ? null : served + 1,
    shortfall: Math.max(0, total - headroom),
  };
}

/** Seconds until the shared pool refills; null when unreadable. Pure. */
export function poolResetIn(reset, now) {
  const r = Number.parseInt(reset, 10);
  const n = Number.parseInt(now, 10);
  if (!Number.isFinite(r) || !Number.isFinite(n)) return null;
  return Math.max(0, r - n);
}

/** Turn the class and the costing into a finding. Pure. */
export function verdict(klass, costing) {
  if (klass === 'anonymous') {
    return ['unauthenticated',
      'the ceiling being costed is the anonymous 60 an hour, so this is not a ' +
      'workflow budget problem yet: no credential is arriving at GitHub.'];
  }
  if (costing.total === 0) {
    return ['no-workflow',
      `no workflow was described, so there is nothing to cost against the ${costing.headroom} request pool.`];
  }
  if (klass !== 'actions-token') {
    return ['different-ceiling',
      `the credential in this environment reads as ${klass} with a ceiling of ` +
      `${costing.headroom}, not the 1000 the Actions token gets. The ${costing.total} ` +
      'request(s) this run makes fit here and will not fit there. Run the check ' +
      'from inside the job.'];
  }
  if (!costing.fits) {
    return ['pool-overrun',
      `${costing.jobs} job(s) at ${costing.calls_per_job} call(s) each is ` +
      `${costing.total} request(s) against a pool of ${costing.headroom} that the ` +
      `whole repository shares. Job ${costing.first_starved_job} of ${costing.jobs} ` +
      'is the first to start seeing 403, and any other run in the same hour moves ' +
      'that number down.'];
  }
  if (costing.total * 5 >= costing.headroom * 4) {
    return ['pool-tight',
      `${costing.total} request(s) against ${costing.headroom} is over four fifths ` +
      'of a pool shared with every other job and every other run in this ' +
      'repository within the same hour.'];
  }
  return ['fits', `${costing.total} request(s) against a shared pool of ${costing.headroom}.`];
}

async function get(token, path) {
  const res = await fetch(API + path, {
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': UA,
    },
  });
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  return { status: res.status, body };
}

async function main() {
  const envName = process.env.GITHUB_TOKEN_ENV || 'GITHUB_TOKEN';
  const token = process.env[envName];
  if (!token) {
    console.error(`set ${envName}. Inside a workflow this is the credential ` +
      'Actions injects; on a laptop it is your own, and the whole point of this ' +
      'check is that the two have different ceilings');
    process.exitCode = 2;
    return;
  }
  const jobs = Number.parseInt(process.argv[2] ?? '0', 10) || 0;
  const calls = Number.parseInt(process.argv[3] ?? '0', 10) || 0;
  const matrix = Number.parseInt(process.argv[4] ?? '1', 10) || 1;

  const rate = await get(token, '/rate_limit');
  if (rate.status !== 200) {
    console.error(`GET /rate_limit returned ${rate.status}; without it there is ` +
      'no ceiling to reason about');
    process.exitCode = 2;
    return;
  }

  const resources = (rate.body ?? {}).resources ?? {};
  const core = resources.core ?? {};
  const graphql = resources.graphql ?? {};

  const user = await get(token, '/user');
  console.log(`GET /user answered ${user.status} (a fingerprint, not a body read)`);

  const [klass, confidence, note] = classify(core.limit, graphql.limit, user.status);
  console.log(`${klass} (${confidence}): ${note}`);
  console.log(`core limit ${core.limit} remaining ${core.remaining}, ` +
    `graphql limit ${graphql.limit} remaining ${graphql.remaining}`);

  const wait = poolResetIn(core.reset, Math.floor(Date.now() / 1000));
  if (wait !== null) console.log(`the shared pool refills in ${wait}s`);

  if (process.env.GITHUB_ACTIONS !== 'true') {
    console.warn('GITHUB_ACTIONS is not set to true, so this is not running ' +
      'inside a workflow and the ceiling above is your laptop\\'s');
  }

  const costing = plan(jobs, calls, matrix, core.limit || ACTIONS_CEILING, core.remaining);
  const [state, detail] = verdict(klass, costing);
  console.log(`${state}: ${detail}`);

  if (state === 'pool-overrun' || state === 'pool-tight') {
    console.log('repair: collapse related REST reads into one GraphQL query and ' +
      'send If-None-Match on repeats; a 304 does not count against the primary limit.');
    console.log('repair: for irreducible volume, authenticate as a GitHub App ' +
      'installation instead of the built-in token.');
    console.log('repair: reduce concurrency. The pool is per repository, so matrix ' +
      'legs do not each get their own budget.');
  }

  console.log(JSON.stringify({ class: klass, confidence, plan: costing, state }, null, 2));
  process.exitCode = ['pool-overrun', 'pool-tight', 'unauthenticated'].includes(state) ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err); process.exitCode = 2; });
}
''',
"test_intro": "The cases worth pinning are the ones a live run will not produce on demand. A 5,000 ceiling has to come back as <em>ambiguous</em> rather than as a confident user token, because it is also an App installation at the floor. A 1,000 ceiling with two corroborating signals has to read differently from a 1,000 ceiling on its own. And the costing has to name a job index rather than a percentage, because the index is the only output anyone acts on. Every function takes plain numbers, so a drained pool is a literal rather than a fixture.",
"test_py_file": "test_github_actions_token_budget.py",
"test_py": '''from github_actions_token_budget import classify, plan, pool_reset_in, verdict


def test_a_thousand_is_the_actions_token():
    klass, confidence, note = classify(1000)
    assert klass == "actions-token"
    assert confidence == "likely"
    assert "belongs to the repository" in note


def test_two_corroborating_signals_raise_the_confidence():
    klass, confidence, note = classify(1000, graphql_limit=1000, user_status=403)
    assert klass == "actions-token"
    assert confidence == "high"
    assert "403" in note and "1000 points" in note


def test_five_thousand_is_reported_as_ambiguous_rather_than_as_a_user():
    klass, confidence, _ = classify(5000)
    assert klass == "user-or-app"
    assert confidence == "ambiguous"


def test_the_scaled_and_enterprise_ceilings_are_separated():
    assert classify(15000)[0] == "enterprise-user"
    assert classify(12500)[0] == "app-installation"


def test_sixty_is_the_anonymous_tier_and_not_a_budget_problem():
    assert classify(60)[0] == "anonymous"
    assert verdict("anonymous", plan(4, 100))[0] == "unauthenticated"


def test_an_unreadable_ceiling_does_not_become_a_number():
    assert classify(None)[0] == "unknown"
    assert classify("plenty")[1] == "none"


def test_the_matrix_multiplies_the_job_count():
    costing = plan(jobs=4, calls_per_job=120, matrix_legs=3)
    assert costing["legs"] == 3
    assert costing["jobs"] == 12
    assert costing["total"] == 1440


def test_an_overrun_names_the_first_job_that_starves():
    costing = plan(jobs=12, calls_per_job=120, ceiling=1000)
    assert costing["fits"] is False
    assert costing["jobs_served"] == 8
    assert costing["first_starved_job"] == 9
    assert costing["shortfall"] == 440


def test_remaining_is_used_when_it_is_supplied_and_is_labelled():
    costing = plan(jobs=5, calls_per_job=100, remaining=240)
    assert costing["source"] == "remaining"
    assert costing["headroom"] == 240
    assert costing["first_starved_job"] == 3


def test_no_calls_is_not_a_division_by_zero():
    costing = plan(jobs=6, calls_per_job=0)
    assert costing["total"] == 0
    assert costing["fits"] is True
    assert costing["first_starved_job"] is None


def test_a_described_overrun_reads_as_a_job_number():
    state, detail = verdict("actions-token", plan(12, 120, ceiling=1000))
    assert state == "pool-overrun"
    assert "Job 9 of 12" in detail
    assert "whole repository shares" in detail


def test_four_fifths_of_the_pool_is_already_a_finding():
    state, detail = verdict("actions-token", plan(8, 100, ceiling=1000))
    assert state == "pool-tight"
    assert "four fifths" in detail


def test_a_run_well_inside_the_pool_is_reported_as_fitting():
    assert verdict("actions-token", plan(2, 50, ceiling=1000))[0] == "fits"


def test_costing_a_laptop_credential_says_so_rather_than_passing():
    state, detail = verdict("user-or-app", plan(12, 120, ceiling=5000))
    assert state == "different-ceiling"
    assert "from inside the job" in detail


def test_nothing_described_is_not_a_pass_either():
    assert verdict("actions-token", plan(0, 0))[0] == "no-workflow"


def test_the_reset_is_seconds_or_nothing():
    assert pool_reset_in(1000, 940) == 60
    assert pool_reset_in(900, 940) == 0
    assert pool_reset_in(None, 940) is None
''',
"test_js_file": "github-actions-token-budget.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  classify, plan, poolResetIn, verdict,
} from './github-actions-token-budget.mjs';

test('a thousand is the actions token', () => {
  const [klass, confidence, note] = classify(1000);
  assert.equal(klass, 'actions-token');
  assert.equal(confidence, 'likely');
  assert.match(note, /belongs to the repository/);
});

test('two corroborating signals raise the confidence', () => {
  const [klass, confidence, note] = classify(1000, 1000, 403);
  assert.equal(klass, 'actions-token');
  assert.equal(confidence, 'high');
  assert.match(note, /403/);
  assert.match(note, /1000 points/);
});

test('five thousand is reported as ambiguous rather than as a user', () => {
  const [klass, confidence] = classify(5000);
  assert.equal(klass, 'user-or-app');
  assert.equal(confidence, 'ambiguous');
});

test('the scaled and enterprise ceilings are separated', () => {
  assert.equal(classify(15000)[0], 'enterprise-user');
  assert.equal(classify(12500)[0], 'app-installation');
});

test('sixty is the anonymous tier and not a budget problem', () => {
  assert.equal(classify(60)[0], 'anonymous');
  assert.equal(verdict('anonymous', plan(4, 100))[0], 'unauthenticated');
});

test('an unreadable ceiling does not become a number', () => {
  assert.equal(classify(null)[0], 'unknown');
  assert.equal(classify('plenty')[1], 'none');
});

test('the matrix multiplies the job count', () => {
  const costing = plan(4, 120, 3);
  assert.equal(costing.legs, 3);
  assert.equal(costing.jobs, 12);
  assert.equal(costing.total, 1440);
});

test('an overrun names the first job that starves', () => {
  const costing = plan(12, 120, 1, 1000);
  assert.equal(costing.fits, false);
  assert.equal(costing.jobs_served, 8);
  assert.equal(costing.first_starved_job, 9);
  assert.equal(costing.shortfall, 440);
});

test('remaining is used when it is supplied and is labelled', () => {
  const costing = plan(5, 100, 1, 1000, 240);
  assert.equal(costing.source, 'remaining');
  assert.equal(costing.headroom, 240);
  assert.equal(costing.first_starved_job, 3);
});

test('no calls is not a division by zero', () => {
  const costing = plan(6, 0);
  assert.equal(costing.total, 0);
  assert.equal(costing.fits, true);
  assert.equal(costing.first_starved_job, null);
});

test('a described overrun reads as a job number', () => {
  const [state, detail] = verdict('actions-token', plan(12, 120, 1, 1000));
  assert.equal(state, 'pool-overrun');
  assert.match(detail, /Job 9 of 12/);
  assert.match(detail, /whole repository shares/);
});

test('four fifths of the pool is already a finding', () => {
  const [state, detail] = verdict('actions-token', plan(8, 100, 1, 1000));
  assert.equal(state, 'pool-tight');
  assert.match(detail, /four fifths/);
});

test('a run well inside the pool is reported as fitting', () => {
  assert.equal(verdict('actions-token', plan(2, 50, 1, 1000))[0], 'fits');
});

test('costing a laptop credential says so rather than passing', () => {
  const [state, detail] = verdict('user-or-app', plan(12, 120, 1, 5000));
  assert.equal(state, 'different-ceiling');
  assert.match(detail, /from inside the job/);
});

test('nothing described is not a pass either', () => {
  assert.equal(verdict('actions-token', plan(0, 0))[0], 'no-workflow');
});

test('the reset is seconds or nothing', () => {
  assert.equal(poolResetIn(1000, 940), 60);
  assert.equal(poolResetIn(900, 940), 0);
  assert.equal(poolResetIn(null, 940), null);
});
''',
"faq": [
 ("Can I raise the 1,000 an hour limit on GITHUB_TOKEN?",
  "Not directly. The ceiling is a property of the credential class, so the way to change it is to change credentials: authenticate as a GitHub App installation, which starts at 5,000 an hour and scales with the repositories and users the installation covers. On GitHub Enterprise Cloud the built-in token gets 15,000 instead of 1,000, which is why the same workflow can behave differently between two organizations with identical YAML."),
 ("Does each job in a matrix get its own 1,000?",
  "No, and this is the single most expensive misunderstanding in the note. The pool is scoped to the repository. Twelve matrix legs at 120 calls each is one budget of 1,440 requests, not twelve budgets of 120. Adding concurrency spends the allowance faster; it never enlarges it."),
 ("Why does GET /user return 403 with the Actions token?",
  "Because the credential does not represent a user. It is scoped to the repository the workflow is running in, and the user endpoint has no user to answer with. That refusal is useful rather than annoying: it is a fingerprint no personal access token produces, so it corroborates the 1,000 reading from a completely independent direction."),
 ("Does GET /rate_limit itself use up part of the 1,000?",
  "No. The rate limit endpoint is explicitly exempt from the primary rate limit, which is what makes it safe to call at the top of every job and in a loop while you are investigating. It is the one request you never have to budget for."),
 ("The failure moves between jobs on every rerun. Is that the same problem?",
  "Almost certainly yes, and the movement is the diagnosis rather than a complication. A per-job quota would fail deterministically in the same job. A shared pool fails in whichever job happens to be holding the bag when the total crosses the ceiling, so the identity of the failing job is decided by scheduling. If the failing job moves and the total call count does not, you are looking at a shared budget."),
],
"related": [
 ("/github/rate-limit-core-exhausted/", "The core hourly quota is exhausted"),
 ("/github/rate-limit-unauthenticated/", "Requests go out anonymous at 60 an hour"),
 ("/github/no-conditional-requests/", "Polling without ETags spends full quota"),
],
"citations": [CITE_REST_LIMITS, CITE_AUTOMATIC_TOKEN, CITE_GRAPHQL_LIMITS, CITE_RATE_ENDPOINT],
},

{
"slug": "bad-credentials-401",
"title": "401 Bad credentials on every endpoint, even public ones",
"description": "Bad credentials means GitHub parsed your token and refused it. Requires authentication means it never arrived. Two words apart, two different repairs.",
"h1": "401 Bad credentials on every endpoint, even public ones",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api 401 bad credentials", "bad credentials github token",
             "github requires authentication 401", "github api 401 every endpoint",
             "401 bad credentials personal access token"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "<code>401 {&quot;message&quot;:&quot;Bad credentials&quot;}</code> on every endpoint you try, including ones that need no credential at all. The token is right there in the environment, it was working yesterday, and the error names nothing: not the account, not the scope, not which of the six things that produce this message actually happened.",
"short_answer": """<p>GitHub returns two different 401 messages and they mean opposite things. <strong><code>Bad credentials</code></strong> means GitHub received something in the <code>Authorization</code> header, parsed it, and refused it. <strong><code>Requires authentication</code></strong> means GitHub received nothing and the endpoint needed something. One is a token problem; the other is a transport problem, and no amount of re-minting will fix the second.</p>
<p>The cheapest way to tell them apart is a control request against an endpoint that needs no credential at all. Send it once with the header and once without. A <code>200</code> without and a <code>401</code> with is proof the value you are sending is the thing being rejected. The script below runs that pair, checks that GitHub itself answered rather than something in front of it, and then asks the one question a valid token can still fail: is it the right account?</p>""",
"problem": """<p>The message is identical for causes that have nothing to do with each other. A revoked token, a token that expired last night, a value truncated by a secrets store, a trailing newline from <code>cat token.txt</code>, a shell variable that expanded to empty, a token minted on a different account: all of them are <code>Bad credentials</code>. That is not GitHub being unhelpful, it is GitHub deliberately refusing to confirm anything about a credential it does not accept.</p>
<p>So the investigation goes in a circle. Someone re-mints the token, it still fails, and now there are two tokens and no more information. Someone tries a different endpoint, gets the same 401, and concludes the whole API is down. Someone pastes the token into <code>curl</code> by hand, it works, and the conclusion is "the script is broken" &mdash; which is true, but only names the room, not the fault.</p>
<p>The genuinely disorienting version is the one where the token is fine. It authenticates, <code>GET /user</code> returns 200, and everything still fails, because the login coming back is a service account nobody remembered was in that variable. A valid credential for the wrong identity produces 404s and 403s all over an integration and never once says the word <em>credentials</em>.</p>""",
"why": """<p><strong>An invalid credential is rejected before authorization is considered.</strong> This is why the root endpoint, which any anonymous caller can read, answers 401 when you attach a broken <code>Authorization</code> header. Presenting a credential GitHub cannot accept is worse than presenting none at all, and that asymmetry is the most useful fact in this note.</p>
<p><strong>The two messages are the discriminator.</strong> <code>Bad credentials</code> is only ever produced when a value was received and refused. <code>Requires authentication</code> is only produced when nothing was received on an endpoint that required something. If you are getting the second one while your code is definitely setting a header, the header is being lost between your process and GitHub, and the token is innocent.</p>
<p><strong>A 401 is not always from GitHub.</strong> Corporate proxies, API gateways and mitm TLS appliances all answer 401, and their responses do not carry <code>x-github-request-id</code> or GitHub's <code>documentation_url</code>. Checking for that furniture takes one line and saves you from re-minting a token that never left the building.</p>
<p><strong>A 200 from <code>GET /user</code> is not the end of the check.</strong> It proves the credential is valid; it says nothing about whose it is. The login in that response is the only cheap assertion that catches a token from the wrong account, and it is the assertion almost nobody writes.</p>
<p><strong>The tier check is a different question.</strong> If the header is being stripped, the follow-up is how many requests an hour you now get and whether anything is quietly succeeding at 60 an hour. That is <a href="/github/rate-limit-unauthenticated/">its own note</a>, and this script hands off to it rather than duplicating it.</p>""",
"steps": [
 {"h": "Ask an endpoint that needs no credential, with the header attached",
  "body": """<p><code>GET /</code> is the REST root: an anonymous caller reads it fine. Attach your <code>Authorization</code> header to it. If it answers <code>401 Bad credentials</code>, GitHub received your value and rejected it, and you have eliminated every theory involving permissions, scopes, repositories and organizations in a single request.</p>"""},
 {"h": "Run the same request with no header at all as a control",
  "body": """<p>If the control also fails, the problem is not your credential: something is refusing you before authentication is even relevant &mdash; an IP allow list, a proxy, a captive network. A control that succeeds while the credentialled request fails is the clean, publishable result.</p>"""},
 {"h": "Confirm GitHub is the thing answering",
  "body": """<p>Look for <code>x-github-request-id</code> on the 401. GitHub puts it on every response. A 401 without it is very likely an intermediary, and the repair is a network conversation rather than a token rotation. Note the request id either way: it is the identifier support will ask for.</p>"""},
 {"h": "Read the message, not just the status",
  "body": """<p><code>Requires authentication</code> on <code>GET /user</code> while your code is setting a header means the header is not arriving. Common causes are a redirect that dropped it, a client library that only applies auth to configured hosts, and a proxy that strips unknown headers. Rotating the token cannot fix any of them.</p>"""},
 {"h": "Assert the login, not just the status code",
  "body": """<p>Once <code>GET /user</code> returns 200, compare the <code>login</code> against the account you expect and fail loudly on a mismatch. Do this at startup, before the integration does any real work. It is three lines, it costs one free request, and it is the only check that catches a perfectly valid credential belonging to the wrong identity.</p>"""},
],
"verify": """<p>The report should name a layer, not a feeling. Two of the states below are repaired by re-minting a token and three of them are not, which is exactly why the check exists.</p>
<pre><code class="language-bash">python3 github_401_provenance.py --expect-login acme-ci-bot
# public endpoint with the header:    401 bad credentials
# public endpoint without any header: 200
# credential-rejected: GitHub parsed the value in GITHUB_TOKEN and refused it.
#   An endpoint that needs no credential at all answered 200 without the
#   header and 401 with it, so the value is the thing being rejected.</code></pre>""",
"code_intro": "Three GETs and no state. Two of them hit the REST root, once with the header and once without, and the third is <code>GET /user</code>. None of them consume anything worth counting and none of them need a scope. The credential is read from the environment and never printed, not even a prefix: this script does not inspect the secret's text at all, because the whole argument is about what GitHub did with it. Everything that produces a verdict is a pure function over three small dicts.",
"py_file": "github_401_provenance.py",
"py": '''"""Say which layer produced a 401, using two messages and one control request.

Read only. Three GETs: the REST root with the credential attached, the REST root
with no credential at all, and GET /user. None of them writes and none of them
needs a scope.

GitHub returns two different 401 messages. "Bad credentials" means a value was
received and refused. "Requires authentication" means nothing was received. The
distance between those two sentences is the whole diagnosis, and the control
request is what makes the first one provable rather than assumed.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_401_provenance")

API = "https://api.github.com"
UA = "github-401-provenance/1.0"

# The REST root. Any anonymous caller may read it, which is precisely why
# attaching a broken credential to it is such a clean experiment.
PUBLIC_PATH = "/"

BAD_CREDENTIALS = "bad credentials"
REQUIRES_AUTH = "requires authentication"

# Response furniture GitHub puts on everything it answers. An appliance in the
# middle that decides to return 401 will not have any of it.
GITHUB_FURNITURE = ("x-github-request-id", "x-github-media-type",
                    "x-github-api-version-selected")


def message_of(body):
    """The message GitHub put in the body, folded to lower case. Pure.

    None for anything that is not a JSON object with a non-empty message, so a
    truncated body or an HTML error page from a proxy does not get read as a
    GitHub verdict.
    """
    if not isinstance(body, dict):
        return None
    value = body.get("message")
    if not isinstance(value, str) or not value.strip():
        return None
    return value.strip().lower()


def from_github(headers):
    """Whether GitHub itself answered, rather than something in front of it. Pure.

    Returns (bool, which-header-said-so). The negative result is the valuable
    one: a 401 with none of this furniture is very likely a proxy, and no amount
    of rotating credentials will change its mind.
    """
    lowered = {str(k).lower(): v for k, v in (headers or {}).items()}
    for name in GITHUB_FURNITURE:
        if lowered.get(name):
            return (True, name)
    if "github" in str(lowered.get("server", "")).lower():
        return (True, "server")
    return (False, None)


def rung(status, message):
    """Reduce one probe to a symbol. Pure.

    The two 401s get different symbols, because they are different findings, and
    a 401 with neither message gets a third symbol rather than being forced into
    whichever of the two the code happened to check first.
    """
    try:
        status = int(status)
    except (TypeError, ValueError):
        return "error"
    if status == 0:
        return "error"
    if 200 <= status < 300:
        return "ok"
    if status == 401:
        if message == BAD_CREDENTIALS:
            return "rejected"
        if message == REQUIRES_AUTH:
            return "anonymous"
        return "unlabelled-401"
    if status == 403:
        return "forbidden"
    return "http-%d" % status


def diagnose(public_with, public_without, user, expected_login=None):
    """Name the layer that produced the 401. Pure.

    Each probe is a dict of {"status", "message", "github", "login"}. Nothing
    here looks at the credential's text: the argument is entirely about what
    GitHub did with it.
    """
    def symbol(probe):
        probe = probe or {}
        return rung(probe.get("status"), probe.get("message"))

    with_header = symbol(public_with)
    without_header = symbol(public_without)
    identity = symbol(user)

    if with_header in ("rejected", "anonymous", "unlabelled-401") \\
            and not (public_with or {}).get("github"):
        return ("not-github",
                "the 401 carried none of GitHub's response furniture: no "
                "request id, no media type, no GitHub server header. Something "
                "between this process and api.github.com answered, and it is "
                "not looking at your credential. Re-minting will not help.")

    if without_header == "error":
        return ("no-baseline",
                "the control request, which carries no credential at all, could "
                "not be made. Without it nothing below can be separated from a "
                "network fault.")

    if without_header != "ok":
        return ("anonymous-refused",
                "the control request carries no credential and was still "
                "refused (%s). Whatever is producing this is not reading your "
                "token: look at IP allow lists, egress proxies and the network "
                "before you look at the credential." % without_header)

    if with_header == "rejected":
        return ("credential-rejected",
                "GitHub parsed the value and refused it. An endpoint that needs "
                "no credential at all answered 200 without the header and 401 "
                "with it, so the value being sent is the thing being rejected: "
                "expired, revoked, truncated, or from an account that no longer "
                "exists. That is a re-mint, not a network change.")

    if identity == "anonymous":
        return ("header-not-arriving",
                "GET /user answered 401 Requires authentication, which is the "
                "message for a request that carried nothing. The header is "
                "being lost between here and GitHub: a redirect that dropped "
                "it, a client that only applies auth to configured hosts, or a "
                "proxy that strips what it does not recognise.")

    if identity == "rejected" and with_header == "ok":
        return ("path-dependent",
                "the public endpoint accepted or ignored the same credential "
                "that GET /user refused. Two requests from the same process are "
                "not arriving as the same request, which points at something "
                "rewriting them in between.")

    if identity == "rejected":
        return ("credential-rejected",
                "GET /user answered 401 Bad credentials, so the value was "
                "received and refused.")

    if identity == "forbidden":
        return ("authenticated-but-forbidden",
                "the credential is valid and GET /user answered 403. That is "
                "not a bad credential: look at SSO authorisation, IP allow "
                "lists and organization policy.")

    if identity == "ok":
        login = (user or {}).get("login")
        if expected_login and str(login or "").lower() != str(expected_login).lower():
            return ("wrong-account",
                    "the credential is valid and belongs to %r, not to the "
                    "expected %r. A valid token for the wrong identity produces "
                    "404s and 403s all over an integration and never once says "
                    "the word credentials." % (login, expected_login))
        return ("credential-valid",
                "the credential authenticates as %r. Whatever is returning 401 "
                "is not this credential on this host, so look at the other "
                "variable, the other host, or the other process."
                % (login or "an unnamed account"))

    return ("unclear",
            "the three probes do not agree: root with header %s, root without "
            "header %s, /user %s. Report the request id from the failing "
            "response rather than guessing."
            % (with_header, without_header, identity))


def probe(path, token=None):
    """One GET, reduced to the four things the diagnosis needs."""
    headers = {"Accept": "application/vnd.github+json",
               "X-GitHub-Api-Version": "2022-11-28",
               "User-Agent": UA}
    if token:
        headers["Authorization"] = "Bearer " + token
    try:
        response = requests.get(API + path, headers=headers, timeout=30)
    except requests.RequestException as exc:
        log.error("GET %s failed: %s", path, exc)
        return {"status": 0, "message": None, "github": False, "login": None,
                "request_id": None}
    try:
        body = response.json()
    except ValueError:
        body = None
    is_github, which = from_github(response.headers)
    return {"status": response.status_code,
            "message": message_of(body),
            "github": is_github,
            "github_signal": which,
            "login": (body or {}).get("login") if isinstance(body, dict) else None,
            "request_id": response.headers.get("x-github-request-id")}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--env", default="GITHUB_TOKEN",
                        help="environment variable holding the credential")
    parser.add_argument("--expect-login",
                        help="the account this credential is supposed to be")
    args = parser.parse_args()

    token = os.environ.get(args.env)
    if not token:
        log.error("%s is not set, so there is no credential to account for. "
                  "That is a different note: every request goes out anonymous.",
                  args.env)
        return 2

    public_with = probe(PUBLIC_PATH, token)
    public_without = probe(PUBLIC_PATH, None)
    user = probe("/user", token)

    log.info("public endpoint with the header:    %d %s",
             public_with["status"], public_with["message"] or "")
    log.info("public endpoint without any header: %d %s",
             public_without["status"], public_without["message"] or "")
    log.info("GET /user:                          %d %s",
             user["status"], user["message"] or "")
    if not public_with["github"]:
        log.warning("the credentialled response carried none of GitHub's "
                    "response furniture")
    for name, result in (("root", public_with), ("user", user)):
        if result["request_id"]:
            log.info("%s request id %s", name, result["request_id"])

    state, detail = diagnose(public_with, public_without, user, args.expect_login)
    log.info("%s: %s", state, detail)

    if state == "credential-rejected":
        log.info("repair: re-mint the credential, store it with no surrounding "
                 "whitespace or quotes, and assert at startup that GET /user "
                 "returns 200 before doing any real work.")
    if state == "header-not-arriving":
        log.info("repair: log the outgoing request headers at the transport "
                 "layer and check the tier as well; a stripped header means "
                 "60 requests an hour, not zero.")
    if state == "wrong-account":
        log.info("repair: assert the expected login at startup. It is three "
                 "lines and it costs one free request.")

    print(json.dumps({"state": state,
                      "public_with": public_with["status"],
                      "public_without": public_without["status"],
                      "user": user["status"]}, indent=2))
    return 1 if state not in ("credential-valid",) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-401-provenance.mjs",
"js": '''/**
 * Say which layer produced a 401, using two messages and one control request.
 *
 * Read only. Three GETs: the REST root with the credential, the REST root with
 * no credential at all, and GET /user.
 *
 * "Bad credentials" means a value was received and refused. "Requires
 * authentication" means nothing was received. The control request is what makes
 * the first of those provable rather than assumed.
 */
const API = 'https://api.github.com';
const UA = 'github-401-provenance/1.0';

// The REST root: readable by any anonymous caller, which is what makes it a
// clean place to attach a broken credential.
export const PUBLIC_PATH = '/';

export const BAD_CREDENTIALS = 'bad credentials';
export const REQUIRES_AUTH = 'requires authentication';

export const GITHUB_FURNITURE = [
  'x-github-request-id', 'x-github-media-type', 'x-github-api-version-selected',
];

/** The message GitHub put in the body, folded to lower case. Pure. */
export function messageOf(body) {
  if (!body || typeof body !== 'object' || Array.isArray(body)) return null;
  const value = body.message;
  if (typeof value !== 'string' || !value.trim()) return null;
  return value.trim().toLowerCase();
}

/** Whether GitHub itself answered, rather than something in front of it. Pure. */
export function fromGithub(headers) {
  const lowered = {};
  for (const [k, v] of Object.entries(headers ?? {})) lowered[String(k).toLowerCase()] = v;
  for (const name of GITHUB_FURNITURE) {
    if (lowered[name]) return [true, name];
  }
  if (String(lowered.server ?? '').toLowerCase().includes('github')) return [true, 'server'];
  return [false, null];
}

/** Reduce one probe to a symbol. Pure. The two 401s get different symbols. */
export function rung(status, message) {
  const code = Number.parseInt(status, 10);
  if (!Number.isFinite(code) || code === 0) return 'error';
  if (code >= 200 && code < 300) return 'ok';
  if (code === 401) {
    if (message === BAD_CREDENTIALS) return 'rejected';
    if (message === REQUIRES_AUTH) return 'anonymous';
    return 'unlabelled-401';
  }
  if (code === 403) return 'forbidden';
  return `http-${code}`;
}

/** Name the layer that produced the 401. Pure. */
export function diagnose(publicWith, publicWithout, user, expectedLogin = null) {
  const symbol = (probe) => rung((probe ?? {}).status, (probe ?? {}).message);
  const withHeader = symbol(publicWith);
  const withoutHeader = symbol(publicWithout);
  const identity = symbol(user);

  if (['rejected', 'anonymous', 'unlabelled-401'].includes(withHeader)
      && !(publicWith ?? {}).github) {
    return ['not-github',
      "the 401 carried none of GitHub's response furniture: no request id, no " +
      'media type, no GitHub server header. Something between this process and ' +
      'api.github.com answered, and it is not looking at your credential. ' +
      'Re-minting will not help.'];
  }

  if (withoutHeader === 'error') {
    return ['no-baseline',
      'the control request, which carries no credential at all, could not be ' +
      'made. Without it nothing below can be separated from a network fault.'];
  }

  if (withoutHeader !== 'ok') {
    return ['anonymous-refused',
      `the control request carries no credential and was still refused (${withoutHeader}). ` +
      'Whatever is producing this is not reading your token: look at IP allow ' +
      'lists, egress proxies and the network before you look at the credential.'];
  }

  if (withHeader === 'rejected') {
    return ['credential-rejected',
      'GitHub parsed the value and refused it. An endpoint that needs no ' +
      'credential at all answered 200 without the header and 401 with it, so ' +
      'the value being sent is the thing being rejected: expired, revoked, ' +
      'truncated, or from an account that no longer exists. That is a re-mint, ' +
      'not a network change.'];
  }

  if (identity === 'anonymous') {
    return ['header-not-arriving',
      'GET /user answered 401 Requires authentication, which is the message for ' +
      'a request that carried nothing. The header is being lost between here ' +
      'and GitHub: a redirect that dropped it, a client that only applies auth ' +
      'to configured hosts, or a proxy that strips what it does not recognise.'];
  }

  if (identity === 'rejected' && withHeader === 'ok') {
    return ['path-dependent',
      'the public endpoint accepted or ignored the same credential that GET ' +
      '/user refused. Two requests from the same process are not arriving as ' +
      'the same request, which points at something rewriting them in between.'];
  }

  if (identity === 'rejected') {
    return ['credential-rejected',
      'GET /user answered 401 Bad credentials, so the value was received and refused.'];
  }

  if (identity === 'forbidden') {
    return ['authenticated-but-forbidden',
      'the credential is valid and GET /user answered 403. That is not a bad ' +
      'credential: look at SSO authorisation, IP allow lists and organization policy.'];
  }

  if (identity === 'ok') {
    const login = (user ?? {}).login;
    if (expectedLogin && String(login ?? '').toLowerCase() !== String(expectedLogin).toLowerCase()) {
      return ['wrong-account',
        `the credential is valid and belongs to '${login}', not to the expected ` +
        `'${expectedLogin}'. A valid token for the wrong identity produces 404s ` +
        'and 403s all over an integration and never once says the word credentials.'];
    }
    return ['credential-valid',
      `the credential authenticates as '${login ?? 'an unnamed account'}'. ` +
      'Whatever is returning 401 is not this credential on this host, so look ' +
      'at the other variable, the other host, or the other process.'];
  }

  return ['unclear',
    `the three probes do not agree: root with header ${withHeader}, root without ` +
    `header ${withoutHeader}, /user ${identity}. Report the request id from the ` +
    'failing response rather than guessing.'];
}

async function probe(path, token = null) {
  const headers = {
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
  if (token) headers.Authorization = `Bearer ${token}`;
  let res;
  try {
    res = await fetch(API + path, { headers });
  } catch (err) {
    console.error(`GET ${path} failed: ${err.message}`);
    return { status: 0, message: null, github: false, login: null, request_id: null };
  }
  let body = null;
  try { body = await res.json(); } catch { body = null; }
  const raw = {};
  for (const [k, v] of res.headers.entries()) raw[k.toLowerCase()] = v;
  const [isGithub, which] = fromGithub(raw);
  return {
    status: res.status,
    message: messageOf(body),
    github: isGithub,
    github_signal: which,
    login: body && typeof body === 'object' ? body.login ?? null : null,
    request_id: raw['x-github-request-id'] ?? null,
  };
}

async function main() {
  const envName = process.env.GITHUB_TOKEN_ENV || 'GITHUB_TOKEN';
  const token = process.env[envName];
  if (!token) {
    console.error(`${envName} is not set, so there is no credential to account ` +
      'for. That is a different note: every request goes out anonymous.');
    process.exitCode = 2;
    return;
  }
  const expectedLogin = process.argv[2] ?? null;

  const publicWith = await probe(PUBLIC_PATH, token);
  const publicWithout = await probe(PUBLIC_PATH, null);
  const user = await probe('/user', token);

  console.log(`public endpoint with the header:    ${publicWith.status} ${publicWith.message ?? ''}`);
  console.log(`public endpoint without any header: ${publicWithout.status} ${publicWithout.message ?? ''}`);
  console.log(`GET /user:                          ${user.status} ${user.message ?? ''}`);
  if (!publicWith.github) {
    console.warn("the credentialled response carried none of GitHub's response furniture");
  }
  for (const [name, result] of [['root', publicWith], ['user', user]]) {
    if (result.request_id) console.log(`${name} request id ${result.request_id}`);
  }

  const [state, detail] = diagnose(publicWith, publicWithout, user, expectedLogin);
  console.log(`${state}: ${detail}`);

  if (state === 'credential-rejected') {
    console.log('repair: re-mint the credential, store it with no surrounding ' +
      'whitespace or quotes, and assert at startup that GET /user returns 200.');
  }
  if (state === 'header-not-arriving') {
    console.log('repair: log the outgoing request headers at the transport layer ' +
      'and check the tier as well; a stripped header means 60 an hour, not zero.');
  }
  if (state === 'wrong-account') {
    console.log('repair: assert the expected login at startup. It is three lines ' +
      'and it costs one free request.');
  }

  console.log(JSON.stringify({
    state,
    public_with: publicWith.status,
    public_without: publicWithout.status,
    user: user.status,
  }, null, 2));
  process.exitCode = state === 'credential-valid' ? 0 : 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err); process.exitCode = 2; });
}
''',
"test_intro": "The classifier takes three small dicts, which means every branch is a two-line test and none of them needs a broken token to exist. The ones worth writing down are the near misses: a 401 with no request id must not be reported as a bad credential, a 401 on the control request must stop the diagnosis rather than continue it, and a 200 from <code>GET /user</code> under an unexpected login must be a failure rather than a pass. The unlabelled 401 gets its own symbol so a future message change degrades into <em>unclear</em> instead of into a confident wrong answer.",
"test_py_file": "test_github_401_provenance.py",
"test_py": '''from github_401_provenance import diagnose, from_github, message_of, rung


def gh(status, message=None, login=None, github=True):
    return {"status": status, "message": message, "login": login, "github": github}


def test_the_two_messages_get_different_symbols():
    assert rung(401, "bad credentials") == "rejected"
    assert rung(401, "requires authentication") == "anonymous"


def test_a_401_with_neither_message_is_not_forced_into_one():
    assert rung(401, None) == "unlabelled-401"
    assert rung(401, "something new") == "unlabelled-401"


def test_the_ordinary_statuses_reduce_predictably():
    assert rung(200, None) == "ok"
    assert rung(204, None) == "ok"
    assert rung(403, "forbidden") == "forbidden"
    assert rung(404, None) == "http-404"
    assert rung(0, None) == "error"
    assert rung(None, None) == "error"


def test_the_message_is_only_read_from_a_json_object():
    assert message_of({"message": "  Bad Credentials "}) == "bad credentials"
    assert message_of({"message": ""}) is None
    assert message_of("<html>401</html>") is None
    assert message_of(None) is None


def test_githubs_furniture_is_recognised_whatever_the_header_case():
    assert from_github({"X-GitHub-Request-Id": "ABC:123"}) == (True, "x-github-request-id")
    assert from_github({"Server": "github.com"})[0] is True
    assert from_github({"server": "squid/5.7"}) == (False, None)
    assert from_github({}) == (False, None)


def test_a_401_without_githubs_furniture_is_an_intermediary():
    state, detail = diagnose(gh(401, "bad credentials", github=False),
                             gh(200), gh(401, "bad credentials", github=False))
    assert state == "not-github"
    assert "Re-minting will not help" in detail


def test_a_refused_control_stops_the_diagnosis():
    state, _ = diagnose(gh(401, "bad credentials"), gh(403, "forbidden"), gh(401))
    assert state == "anonymous-refused"


def test_a_control_that_could_not_be_made_is_its_own_state():
    assert diagnose(gh(401, "bad credentials"), gh(0), gh(401))[0] == "no-baseline"


def test_rejected_on_a_public_endpoint_is_the_credential():
    state, detail = diagnose(gh(401, "bad credentials"), gh(200),
                             gh(401, "bad credentials"))
    assert state == "credential-rejected"
    assert "200 without the header and 401 with it" in detail


def test_requires_authentication_means_the_header_never_arrived():
    state, detail = diagnose(gh(200), gh(200), gh(401, "requires authentication"))
    assert state == "header-not-arriving"
    assert "carried nothing" in detail


def test_a_credential_accepted_on_one_path_and_refused_on_another():
    state, _ = diagnose(gh(200), gh(200), gh(401, "bad credentials"))
    assert state == "path-dependent"


def test_a_valid_credential_for_the_wrong_account_is_a_failure():
    state, detail = diagnose(gh(200), gh(200), gh(200, login="someone-else"),
                             expected_login="acme-ci-bot")
    assert state == "wrong-account"
    assert "someone-else" in detail


def test_the_login_comparison_ignores_case():
    assert diagnose(gh(200), gh(200), gh(200, login="Acme-CI-Bot"),
                    expected_login="acme-ci-bot")[0] == "credential-valid"


def test_a_403_on_user_is_not_a_bad_credential():
    state, detail = diagnose(gh(200), gh(200), gh(403, "forbidden"))
    assert state == "authenticated-but-forbidden"
    assert "SSO" in detail


def test_a_working_credential_sends_you_to_look_elsewhere():
    state, detail = diagnose(gh(200), gh(200), gh(200, login="acme-ci-bot"))
    assert state == "credential-valid"
    assert "acme-ci-bot" in detail


def test_probes_that_disagree_are_reported_as_unclear_rather_than_guessed():
    assert diagnose(gh(500), gh(200), gh(500))[0] == "unclear"
''',
"test_js_file": "github-401-provenance.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  diagnose, fromGithub, messageOf, rung,
} from './github-401-provenance.mjs';

const gh = (status, message = null, login = null, github = true) =>
  ({ status, message, login, github });

test('the two messages get different symbols', () => {
  assert.equal(rung(401, 'bad credentials'), 'rejected');
  assert.equal(rung(401, 'requires authentication'), 'anonymous');
});

test('a 401 with neither message is not forced into one', () => {
  assert.equal(rung(401, null), 'unlabelled-401');
  assert.equal(rung(401, 'something new'), 'unlabelled-401');
});

test('the ordinary statuses reduce predictably', () => {
  assert.equal(rung(200, null), 'ok');
  assert.equal(rung(204, null), 'ok');
  assert.equal(rung(403, 'forbidden'), 'forbidden');
  assert.equal(rung(404, null), 'http-404');
  assert.equal(rung(0, null), 'error');
  assert.equal(rung(null, null), 'error');
});

test('the message is only read from a json object', () => {
  assert.equal(messageOf({ message: '  Bad Credentials ' }), 'bad credentials');
  assert.equal(messageOf({ message: '' }), null);
  assert.equal(messageOf('<html>401</html>'), null);
  assert.equal(messageOf(null), null);
});

test("github's furniture is recognised whatever the header case", () => {
  assert.deepEqual(fromGithub({ 'X-GitHub-Request-Id': 'ABC:123' }),
    [true, 'x-github-request-id']);
  assert.equal(fromGithub({ Server: 'github.com' })[0], true);
  assert.deepEqual(fromGithub({ server: 'squid/5.7' }), [false, null]);
  assert.deepEqual(fromGithub({}), [false, null]);
});

test('a 401 without github furniture is an intermediary', () => {
  const [state, detail] = diagnose(gh(401, 'bad credentials', null, false),
    gh(200), gh(401, 'bad credentials', null, false));
  assert.equal(state, 'not-github');
  assert.match(detail, /Re-minting will not help/);
});

test('a refused control stops the diagnosis', () => {
  const [state] = diagnose(gh(401, 'bad credentials'), gh(403, 'forbidden'), gh(401));
  assert.equal(state, 'anonymous-refused');
});

test('a control that could not be made is its own state', () => {
  assert.equal(diagnose(gh(401, 'bad credentials'), gh(0), gh(401))[0], 'no-baseline');
});

test('rejected on a public endpoint is the credential', () => {
  const [state, detail] = diagnose(gh(401, 'bad credentials'), gh(200),
    gh(401, 'bad credentials'));
  assert.equal(state, 'credential-rejected');
  assert.match(detail, /200 without the header and 401 with it/);
});

test('requires authentication means the header never arrived', () => {
  const [state, detail] = diagnose(gh(200), gh(200), gh(401, 'requires authentication'));
  assert.equal(state, 'header-not-arriving');
  assert.match(detail, /carried nothing/);
});

test('a credential accepted on one path and refused on another', () => {
  const [state] = diagnose(gh(200), gh(200), gh(401, 'bad credentials'));
  assert.equal(state, 'path-dependent');
});

test('a valid credential for the wrong account is a failure', () => {
  const [state, detail] = diagnose(gh(200), gh(200), gh(200, null, 'someone-else'),
    'acme-ci-bot');
  assert.equal(state, 'wrong-account');
  assert.match(detail, /someone-else/);
});

test('the login comparison ignores case', () => {
  assert.equal(diagnose(gh(200), gh(200), gh(200, null, 'Acme-CI-Bot'),
    'acme-ci-bot')[0], 'credential-valid');
});

test('a 403 on user is not a bad credential', () => {
  const [state, detail] = diagnose(gh(200), gh(200), gh(403, 'forbidden'));
  assert.equal(state, 'authenticated-but-forbidden');
  assert.match(detail, /SSO/);
});

test('a working credential sends you to look elsewhere', () => {
  const [state, detail] = diagnose(gh(200), gh(200), gh(200, null, 'acme-ci-bot'));
  assert.equal(state, 'credential-valid');
  assert.match(detail, /acme-ci-bot/);
});

test('probes that disagree are reported as unclear rather than guessed', () => {
  assert.equal(diagnose(gh(500), gh(200), gh(500))[0], 'unclear');
});
''',
"faq": [
 ("Is Bad credentials ever a permissions problem?",
  "No, and that is what makes it worth separating from everything else. Permissions and scopes produce 403 with a different message, usually naming the resource or the integration. A 401 means the credential itself was not accepted, so no amount of adding scopes, accepting an App permission upgrade or authorising SSO will change the answer. If you are getting 401 and reaching for the permissions page, you are in the wrong place."),
 ("Why does a public endpoint return 401 when I attach a bad token?",
  "Because presenting a credential is a claim, and GitHub validates the claim before it decides what you are allowed to see. An anonymous request makes no claim, so it is served. A request carrying something GitHub cannot accept is refused outright, even for content it would have handed to a stranger. That asymmetry is inconvenient in production and extremely useful in a diagnosis."),
 ("My token works in curl but not in the script. What is different?",
  "Usually the value, not the code. A token pasted into a terminal is exactly what you pasted; a token that has been through a file, a secrets store, an environment file and a shell may have picked up a newline, surrounding quotes or a truncation. The control request tells you which world you are in: if GitHub says Bad credentials, the value reaching it differs from the one you pasted."),
 ("The script says header-not-arriving. Where do I look first?",
  "At redirects and at your HTTP client's host rules. Most clients deliberately drop the Authorization header when a redirect crosses hosts, which is correct behaviour and surprising the first time. After that, look at any egress proxy: stripping unrecognised headers is a common default. Log the headers as they leave the process rather than as you set them."),
 ("Should the login assertion run on every request?",
  "Once at startup is enough, and once is the point. The check is cheap, it uses an endpoint that needs no scope, and it converts a class of failure that shows up hours later as scattered 404s into a single clear line at the moment the process starts. Anything that fails should fail while someone is still watching."),
],
"related": [
 ("/github/classic-pat-expired/", "A classic PAT passed its expiry date"),
 ("/github/rate-limit-unauthenticated/", "Requests go out anonymous at 60 an hour"),
 ("/github/404-masking-403/", "A 404 that is really a permissions problem"),
],
"citations": [CITE_TROUBLESHOOT, CITE_AUTH_REST, CITE_USERS, CITE_BEST],
},

{
"slug": "classic-pat-expired",
"title": "A classic PAT passed its expiry and everything broke at once",
"description": "An expired token and a truncated one give the same 401. Running the same ladder under a control credential is what proves the token is the variable.",
"h1": "a classic PAT passed its expiry and everything broke at once",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github personal access token expired", "classic pat expired 401",
             "github token stopped working suddenly", "github pat expiry 401 bad credentials",
             "github token expired no warning"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The integration ran for eleven months without anyone touching it. At 09:14 on a Tuesday every call started returning <code>401 Bad credentials</code>, all at once, on every endpoint, with no deploy, no repository change and no org announcement. A classic personal access token reached its expiry date. So did a great many other theories that morning, and the API will not tell you which one was right.",
"short_answer": """<p>A classic PAT with an expiry stops working the moment it passes, with no grace period and no distinct error. It returns exactly the same <code>401 Bad credentials</code> as a token that was revoked, truncated in transit or typed wrong, and GitHub will not elaborate: a credential it does not accept gets no explanation.</p>
<p>Because the message cannot distinguish them, the useful question is not <em>why</em> the credential failed but <em>whether the credential is the variable at all</em>. That is answered by running the same ladder of resources &mdash; something public, something that needs any credential, the repository, the organization &mdash; under the suspect and under a known-good control at the same instant. A suspect that fails uniformly while the control succeeds uniformly eliminates the repository, the organization, the network and your code in one pass. Anything else points somewhere other than the calendar.</p>""",
"problem": """<p>The timeline is what makes this expensive. Nothing changed, so the search starts in the places where things do change: recent commits, a dependency bump, a runner image, an org policy someone might have flipped. All of those are plausible and all of them are wrong, and each one takes twenty minutes to eliminate.</p>
<p>The failure is also total, which cuts the wrong way. A partial failure narrows the search; a failure on every endpoint at once looks like an outage, so people check the status page, find it green, and then doubt the status page. Total, instantaneous and silent is the signature of a credential rather than a service, but only once you have seen it before.</p>
<p>And the 401 is a dead end by design. You cannot ask an expired token when it expired. The <code>github-authentication-token-expiration</code> header is only returned on <em>successful</em> authenticated calls, so at the moment you most want the expiry date it is unreadable. Every fact about the token you might use to confirm the theory disappeared with the token.</p>""",
"why": """<p><strong>GitHub deliberately refuses to characterise a credential it rejects.</strong> Naming which of expired, revoked, malformed or unknown applies would tell an attacker whether a guessed value was ever real. So the message is constant, and the discriminator has to be built outside GitHub.</p>
<p><strong>A control credential is the only variable-isolation you can run.</strong> Same process, same network, same host, same second, same URLs, one thing different. That is a controlled experiment and it is the only one available here, because everything else you might vary changes something other than the credential.</p>
<p><strong>The <em>shape</em> of the failure is the evidence, not the status code.</strong> Expiry is total: it fails the rung that needs no credential at all, because presenting a rejected credential is worse than presenting none. A credential that answers 200 to anything has not expired, whatever else is wrong with it, and that single observation redirects the whole investigation.</p>
<p><strong>Two credentials failing together is a different finding entirely.</strong> Tokens do not expire in the same second. If the control dies too, look at what the two share: the secrets store, the egress path, the organization that can revoke both, an IP allow list that changed underneath them.</p>
<p><strong>The repair is a calendar entry, not a token.</strong> Re-minting takes a minute and buys you another year of exactly this. Record the expiry where the credential is stored, alert before it, and for unattended automation move to a GitHub App installation, whose one-hour tokens are minted automatically. Watching the clock on a live credential is <a href="/github/token-expiring-soon/">the note next door</a>.</p>""",
"steps": [
 {"h": "Write down the minute it started, before anything else",
  "body": """<p>The expiry cliff is instantaneous and identical across every caller using that credential. If two unrelated services broke in the same minute and they share a token, you have your answer before you run anything. If they broke at different times, it is not one expiry.</p>"""},
 {"h": "Run a ladder, not a single endpoint",
  "body": """<p>Four rungs, in order of what they need: the REST root, which needs nothing; <code>GET /user</code>, which needs any valid credential; one repository; one organization. Each rung that fails tells you something different, and a failure at the first rung is the strongest single signal in the whole check.</p>"""},
 {"h": "Get a second credential and run the identical ladder",
  "body": """<p>Any credential known to work: a colleague's, a fresh one, the App installation you were going to migrate to anyway. Same process, same second. Without this the report is a description of a 401 rather than a diagnosis, and the script says so in those words rather than guessing.</p>"""},
 {"h": "Read the two ladders side by side",
  "body": """<p>Suspect uniformly 401, control uniformly 200 means the credential is the variable. Both failing on the same rung means the resource changed &mdash; a repository renamed, transferred or deleted answers the same way to everybody. Suspect succeeding on some rungs is not expiry at all, and the script refuses to call it that.</p>"""},
 {"h": "Re-mint, then record the expiry next to the secret",
  "body": """<p>Store the expiry date in the same place as the credential, so the next person to look at the secret sees the deadline without reading a wiki. Then set the alert. A token that expires with nobody watching is not a fixed problem, it is a scheduled one.</p>"""},
],
"verify": """<p>Two ladders, one table, one verdict. The line to look for is the one that names what has been eliminated, because that is the part a status page cannot give you.</p>
<pre><code class="language-bash">GITHUB_TOKEN=... GITHUB_CONTROL_TOKEN=... \\
  python3 github_credential_differential.py --repo acme/api --org acme
# rung          suspect  control
# public        401      200
# identity      401      200
# repository    401      200
# organization  401      200
# credential-is-the-variable: the suspect answered 401 on every rung including
#   the public one, at the same instant the control answered 200 on all of them.</code></pre>""",
"code_intro": "The network half is deliberately dull: one GET per rung per credential, at most eight requests, none of which needs a scope. Everything interesting is in three pure functions &mdash; one that reduces a status code to what it says about a credential, one that names the <em>shape</em> of a failure across the ladder, and one that reads two shapes side by side and refuses to say <em>expired</em> when the evidence does not support it. Neither credential is printed, compared or inspected as text at any point.",
"py_file": "github_credential_differential.py",
"py": '''"""Prove whether the credential is the variable, by running two of them.

Read only. One GET per rung per credential, at most eight requests, none of
which needs a scope and none of which writes.

An expired token, a revoked token and a truncated token all return the same
401 Bad credentials, so this does not try to tell them apart. It answers the
question that is actually answerable: is the credential the thing that changed,
or did the world change underneath it.
"""
import argparse
import json
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_credential_differential")

API = "https://api.github.com"
UA = "github-credential-differential/1.0"


def ladder(repo=None, org=None):
    """The rungs this run can actually probe, in order of what they need. Pure.

    The public rung is first on purpose: it is the one that needs no credential
    at all, so a 401 there is the strongest single observation in the check.
    """
    rungs = [("public", "/"), ("identity", "/user")]
    if repo:
        rungs.append(("repository", "/repos/" + str(repo)))
    if org:
        rungs.append(("organization", "/orgs/" + str(org)))
    return rungs


def outcome(status):
    """Reduce a status code to what it says about a credential. Pure."""
    try:
        status = int(status)
    except (TypeError, ValueError):
        return "error"
    if status == 0:
        return "error"
    if 200 <= status < 300:
        return "ok"
    if status == 401:
        return "unauthenticated"
    if status == 403:
        return "forbidden"
    if status == 404:
        return "missing"
    return "other"


def shape(rows):
    """Name the signature of a failure across the ladder. Pure.

    rows: [(rung, outcome), ...]

    The distinction that carries the note is uniform against selective. Expiry
    is total, because presenting a rejected credential is worse than presenting
    none, so a credential that answers 200 to anything has not expired.
    """
    results = [result for _rung, result in rows or []]
    if not results:
        return "nothing-probed"
    if all(result == "ok" for result in results):
        return "healthy"
    if all(result == "unauthenticated" for result in results):
        return "uniform-401"
    if any(result == "ok" for result in results):
        return "selective"
    return "mixed"


def compare(suspect, control):
    """Line the two ladders up rung by rung. Pure.

    A rung the control never ran comes back with control None and agrees False,
    so a partial control cannot be mistaken for agreement.
    """
    lookup = dict(control or [])
    rows = []
    for rung, result in suspect or []:
        other = lookup.get(rung)
        rows.append({"rung": rung, "suspect": result, "control": other,
                     "agrees": other is not None and other == result})
    return rows


def diagnose(suspect, control=None):
    """Read the two ladders side by side. Pure.

    Returns (state, detail). The state never says "expired", because nothing
    observable distinguishes expiry from revocation or truncation. It says what
    the evidence supports, which is whether the credential is the variable.
    """
    suspect_shape = shape(suspect)

    if suspect_shape == "nothing-probed":
        return ("nothing-probed",
                "no rungs were run, so there is nothing to compare.")

    if not control:
        if suspect_shape == "healthy":
            return ("suspect-healthy",
                    "the suspect credential answered 200 on every rung, so "
                    "whatever is failing is not this credential.")
        if suspect_shape == "uniform-401":
            return ("no-control",
                    "every rung answered 401, including the one that needs no "
                    "credential at all. That is the signature of a value the "
                    "server will not accept, and expiry, revocation and a "
                    "truncated string all produce it identically. Without a "
                    "second credential run at the same instant, the evidence "
                    "stops here.")
        return ("no-control",
                "the suspect failed as %s rather than uniformly, which is not "
                "what an expired credential looks like: expiry is total. "
                "Without a control credential this cannot be taken further."
                % suspect_shape)

    rows = compare(suspect, control)
    control_shape = shape(control)

    if suspect_shape == "healthy":
        return ("suspect-healthy",
                "the suspect credential answered 200 on every rung, so whatever "
                "is failing is not this credential.")

    if suspect_shape == "uniform-401" and control_shape == "uniform-401":
        return ("both-dead",
                "both credentials answered 401 on every rung. Two tokens do not "
                "expire in the same second, so look at what they share: the "
                "store they came from, the network they left by, and the "
                "organization that can revoke them together.")

    if suspect_shape == "uniform-401" and control_shape == "healthy":
        return ("credential-is-the-variable",
                "the suspect answered 401 on every rung including the public "
                "one, at the same instant the control answered 200 on all of "
                "them. The repository, the organization, the network and your "
                "code are eliminated: the credential is the only thing that "
                "differs. Expiry is the common reason, and revocation and "
                "truncation look identical from here.")

    if all(row["agrees"] for row in rows):
        failing = [row["rung"] for row in rows if row["suspect"] != "ok"]
        return ("resource-changed",
                "both credentials answer identically on every rung, and %s "
                "failed for both. The thing that changed is the resource, not "
                "the token: a repository renamed, transferred or deleted "
                "answers the same way to everybody." % ", ".join(failing))

    if suspect_shape == "selective":
        differing = ["%s (%s)" % (row["rung"], row["suspect"])
                     for row in rows if not row["agrees"]]
        return ("access-not-expiry",
                "the suspect answered 200 on at least one rung, so it has not "
                "expired: an expired credential cannot authenticate anything. "
                "It differs from the control at %s. Look at what that "
                "credential is allowed to reach rather than at its calendar."
                % ", ".join(differing))

    return ("mixed",
            "the two credentials fail in different ways (%s against %s), which "
            "is neither an expiry nor a changed resource. Report the rungs "
            "rather than picking a story." % (suspect_shape, control_shape))


def run_ladder(token, rungs):
    """One GET per rung. Returns [(rung, outcome), ...]."""
    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })
    rows = []
    for rung, path in rungs:
        try:
            status = session.get(API + path, timeout=30).status_code
        except requests.RequestException as exc:
            log.error("GET %s failed: %s", path, exc)
            status = 0
        rows.append((rung, outcome(status)))
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", help="owner/name, adds a repository rung")
    parser.add_argument("--org", help="login, adds an organization rung")
    parser.add_argument("--env", default="GITHUB_TOKEN",
                        help="environment variable holding the suspect")
    parser.add_argument("--control-env", default="GITHUB_CONTROL_TOKEN",
                        help="environment variable holding a known-good control")
    args = parser.parse_args()

    suspect_token = os.environ.get(args.env)
    if not suspect_token:
        log.error("set %s to the credential under suspicion", args.env)
        return 2

    rungs = ladder(args.repo, args.org)
    suspect = run_ladder(suspect_token, rungs)

    control_token = os.environ.get(args.control_env)
    control = run_ladder(control_token, rungs) if control_token else None
    if not control_token:
        log.warning("%s is not set. Without a control credential this is a "
                    "description of a 401 rather than a diagnosis.",
                    args.control_env)

    log.info("%-14s %-8s %s", "rung", "suspect", "control")
    for row in compare(suspect, control or []):
        log.info("%-14s %-8s %s", row["rung"], row["suspect"],
                 row["control"] or "-")

    state, detail = diagnose(suspect, control)
    log.info("%s: %s", state, detail)

    if state == "credential-is-the-variable":
        log.info("repair: re-mint the credential, then record its expiry date "
                 "in the same place the secret is stored and alert before it.")
        log.info("repair: for unattended automation, authenticate as a GitHub "
                 "App installation. Its one-hour tokens are minted "
                 "automatically and never need a calendar entry.")
    if state == "both-dead":
        log.info("repair: look at the secrets store, the egress path and any "
                 "organization policy that could revoke both at once.")

    print(json.dumps({"state": state, "suspect": suspect,
                      "control": control}, indent=2))
    return 1 if state not in ("suspect-healthy",) else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-credential-differential.mjs",
"js": '''/**
 * Prove whether the credential is the variable, by running two of them.
 *
 * Read only. One GET per rung per credential, at most eight requests, none of
 * which needs a scope.
 *
 * An expired token, a revoked token and a truncated token all return the same
 * 401, so this does not try to tell them apart. It answers the question that is
 * answerable: did the credential change, or did the world.
 */
const API = 'https://api.github.com';
const UA = 'github-credential-differential/1.0';

/** The rungs this run can probe, in order of what they need. Pure. */
export function ladder(repo = null, org = null) {
  const rungs = [['public', '/'], ['identity', '/user']];
  if (repo) rungs.push(['repository', `/repos/${repo}`]);
  if (org) rungs.push(['organization', `/orgs/${org}`]);
  return rungs;
}

/** Reduce a status code to what it says about a credential. Pure. */
export function outcome(status) {
  const code = Number.parseInt(status, 10);
  if (!Number.isFinite(code) || code === 0) return 'error';
  if (code >= 200 && code < 300) return 'ok';
  if (code === 401) return 'unauthenticated';
  if (code === 403) return 'forbidden';
  if (code === 404) return 'missing';
  return 'other';
}

/**
 * Name the signature of a failure across the ladder. Pure.
 * Uniform against selective is the distinction that carries the note: expiry is
 * total, so a credential that answers 200 to anything has not expired.
 */
export function shape(rows) {
  const results = (rows ?? []).map(([, result]) => result);
  if (!results.length) return 'nothing-probed';
  if (results.every((r) => r === 'ok')) return 'healthy';
  if (results.every((r) => r === 'unauthenticated')) return 'uniform-401';
  if (results.some((r) => r === 'ok')) return 'selective';
  return 'mixed';
}

/** Line the two ladders up rung by rung. Pure. */
export function compare(suspect, control) {
  const lookup = new Map(control ?? []);
  return (suspect ?? []).map(([rung, result]) => {
    const other = lookup.has(rung) ? lookup.get(rung) : null;
    return { rung, suspect: result, control: other, agrees: other !== null && other === result };
  });
}

/** Read the two ladders side by side. Pure. Never says "expired". */
export function diagnose(suspect, control = null) {
  const suspectShape = shape(suspect);

  if (suspectShape === 'nothing-probed') {
    return ['nothing-probed', 'no rungs were run, so there is nothing to compare.'];
  }

  const healthy = ['suspect-healthy',
    'the suspect credential answered 200 on every rung, so whatever is failing ' +
    'is not this credential.'];

  if (!control || !control.length) {
    if (suspectShape === 'healthy') return healthy;
    if (suspectShape === 'uniform-401') {
      return ['no-control',
        'every rung answered 401, including the one that needs no credential at ' +
        'all. That is the signature of a value the server will not accept, and ' +
        'expiry, revocation and a truncated string all produce it identically. ' +
        'Without a second credential run at the same instant, the evidence stops here.'];
    }
    return ['no-control',
      `the suspect failed as ${suspectShape} rather than uniformly, which is not ` +
      'what an expired credential looks like: expiry is total. Without a control ' +
      'credential this cannot be taken further.'];
  }

  const rows = compare(suspect, control);
  const controlShape = shape(control);

  if (suspectShape === 'healthy') return healthy;

  if (suspectShape === 'uniform-401' && controlShape === 'uniform-401') {
    return ['both-dead',
      'both credentials answered 401 on every rung. Two tokens do not expire in ' +
      'the same second, so look at what they share: the store they came from, ' +
      'the network they left by, and the organization that can revoke them together.'];
  }

  if (suspectShape === 'uniform-401' && controlShape === 'healthy') {
    return ['credential-is-the-variable',
      'the suspect answered 401 on every rung including the public one, at the ' +
      'same instant the control answered 200 on all of them. The repository, the ' +
      'organization, the network and your code are eliminated: the credential is ' +
      'the only thing that differs. Expiry is the common reason, and revocation ' +
      'and truncation look identical from here.'];
  }

  if (rows.every((row) => row.agrees)) {
    const failing = rows.filter((row) => row.suspect !== 'ok').map((row) => row.rung);
    return ['resource-changed',
      `both credentials answer identically on every rung, and ${failing.join(', ')} ` +
      'failed for both. The thing that changed is the resource, not the token: a ' +
      'repository renamed, transferred or deleted answers the same way to everybody.'];
  }

  if (suspectShape === 'selective') {
    const differing = rows.filter((row) => !row.agrees)
      .map((row) => `${row.rung} (${row.suspect})`);
    return ['access-not-expiry',
      'the suspect answered 200 on at least one rung, so it has not expired: an ' +
      'expired credential cannot authenticate anything. It differs from the ' +
      `control at ${differing.join(', ')}. Look at what that credential is ` +
      'allowed to reach rather than at its calendar.'];
  }

  return ['mixed',
    `the two credentials fail in different ways (${suspectShape} against ` +
    `${controlShape}), which is neither an expiry nor a changed resource. Report ` +
    'the rungs rather than picking a story.'];
}

async function runLadder(token, rungs) {
  const rows = [];
  for (const [rung, path] of rungs) {
    let status = 0;
    try {
      const res = await fetch(API + path, {
        headers: {
          Authorization: `Bearer ${token}`,
          Accept: 'application/vnd.github+json',
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent': UA,
        },
      });
      status = res.status;
    } catch (err) {
      console.error(`GET ${path} failed: ${err.message}`);
    }
    rows.push([rung, outcome(status)]);
  }
  return rows;
}

async function main() {
  const suspectToken = process.env.GITHUB_TOKEN;
  if (!suspectToken) {
    console.error('set GITHUB_TOKEN to the credential under suspicion');
    process.exitCode = 2;
    return;
  }
  const repo = process.argv[2] ?? null;
  const org = process.argv[3] ?? null;
  const rungs = ladder(repo, org);

  const suspect = await runLadder(suspectToken, rungs);
  const controlToken = process.env.GITHUB_CONTROL_TOKEN;
  const control = controlToken ? await runLadder(controlToken, rungs) : null;
  if (!controlToken) {
    console.warn('GITHUB_CONTROL_TOKEN is not set. Without a control credential ' +
      'this is a description of a 401 rather than a diagnosis.');
  }

  console.log(`${'rung'.padEnd(14)} ${'suspect'.padEnd(8)} control`);
  for (const row of compare(suspect, control ?? [])) {
    console.log(`${row.rung.padEnd(14)} ${row.suspect.padEnd(8)} ${row.control ?? '-'}`);
  }

  const [state, detail] = diagnose(suspect, control);
  console.log(`${state}: ${detail}`);

  if (state === 'credential-is-the-variable') {
    console.log('repair: re-mint the credential, then record its expiry date in ' +
      'the same place the secret is stored and alert before it.');
    console.log('repair: for unattended automation, authenticate as a GitHub App ' +
      'installation; its one-hour tokens need no calendar entry.');
  }
  if (state === 'both-dead') {
    console.log('repair: look at the secrets store, the egress path and any ' +
      'organization policy that could revoke both at once.');
  }

  console.log(JSON.stringify({ state, suspect, control }, null, 2));
  process.exitCode = state === 'suspect-healthy' ? 0 : 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err); process.exitCode = 2; });
}
''',
"test_intro": "Every interesting case here is a pair of ladders, which is exactly the thing you cannot arrange on demand: nobody has an expired token and a matching healthy one to hand at the moment they need one. Because the functions take lists of tuples, all of them are two lines. The tests that matter most are the refusals &mdash; a selective failure must not be reported as expiry, a missing control must produce <em>no-control</em> rather than a confident story, and two dead credentials must be a different finding from one.",
"test_py_file": "test_github_credential_differential.py",
"test_py": '''from github_credential_differential import compare, diagnose, ladder, outcome, shape

DEAD = [("public", "unauthenticated"), ("identity", "unauthenticated"),
        ("repository", "unauthenticated")]
ALIVE = [("public", "ok"), ("identity", "ok"), ("repository", "ok")]


def test_the_ladder_only_includes_rungs_it_can_probe():
    assert ladder() == [("public", "/"), ("identity", "/user")]
    rungs = ladder(repo="acme/api", org="acme")
    assert rungs[2] == ("repository", "/repos/acme/api")
    assert rungs[3] == ("organization", "/orgs/acme")


def test_status_codes_reduce_to_what_they_say_about_a_credential():
    assert outcome(200) == "ok"
    assert outcome(401) == "unauthenticated"
    assert outcome(403) == "forbidden"
    assert outcome(404) == "missing"
    assert outcome(500) == "other"
    assert outcome(0) == "error"
    assert outcome(None) == "error"


def test_a_total_failure_and_a_partial_one_have_different_names():
    assert shape(DEAD) == "uniform-401"
    assert shape(ALIVE) == "healthy"
    assert shape([("public", "ok"), ("identity", "forbidden")]) == "selective"
    assert shape([("public", "missing"), ("identity", "forbidden")]) == "mixed"
    assert shape([]) == "nothing-probed"


def test_a_rung_the_control_never_ran_does_not_count_as_agreement():
    rows = compare(ALIVE, [("public", "ok")])
    assert rows[0]["agrees"] is True
    assert rows[1]["control"] is None
    assert rows[1]["agrees"] is False


def test_without_a_control_the_script_declines_to_name_a_cause():
    state, detail = diagnose(DEAD)
    assert state == "no-control"
    assert "expiry, revocation and a truncated string" in detail


def test_a_uniform_401_against_a_healthy_control_is_the_credential():
    state, detail = diagnose(DEAD, ALIVE)
    assert state == "credential-is-the-variable"
    assert "eliminated" in detail
    assert "expired" not in state


def test_two_dead_credentials_are_not_two_expiries():
    state, detail = diagnose(DEAD, DEAD)
    assert state == "both-dead"
    assert "same second" in detail


def test_identical_failures_on_one_rung_are_the_resource():
    suspect = [("public", "ok"), ("identity", "ok"), ("repository", "missing")]
    state, detail = diagnose(suspect, list(suspect))
    assert state == "resource-changed"
    assert "repository" in detail


def test_a_credential_that_authenticates_anything_has_not_expired():
    suspect = [("public", "ok"), ("identity", "ok"), ("repository", "forbidden")]
    state, detail = diagnose(suspect, ALIVE)
    assert state == "access-not-expiry"
    assert "has not expired" in detail
    assert "repository (forbidden)" in detail


def test_a_healthy_suspect_sends_you_somewhere_else():
    assert diagnose(ALIVE, ALIVE)[0] == "suspect-healthy"
    assert diagnose(ALIVE)[0] == "suspect-healthy"


def test_disagreeing_shapes_are_reported_rather_than_narrated():
    suspect = [("public", "missing"), ("identity", "forbidden")]
    control = [("public", "ok"), ("identity", "unauthenticated")]
    state, detail = diagnose(suspect, control)
    assert state == "mixed"
    assert "rather than picking a story" in detail


def test_nothing_probed_is_not_a_pass():
    assert diagnose([], ALIVE)[0] == "nothing-probed"
''',
"test_js_file": "github-credential-differential.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  compare, diagnose, ladder, outcome, shape,
} from './github-credential-differential.mjs';

const DEAD = [['public', 'unauthenticated'], ['identity', 'unauthenticated'],
  ['repository', 'unauthenticated']];
const ALIVE = [['public', 'ok'], ['identity', 'ok'], ['repository', 'ok']];

test('the ladder only includes rungs it can probe', () => {
  assert.deepEqual(ladder(), [['public', '/'], ['identity', '/user']]);
  const rungs = ladder('acme/api', 'acme');
  assert.deepEqual(rungs[2], ['repository', '/repos/acme/api']);
  assert.deepEqual(rungs[3], ['organization', '/orgs/acme']);
});

test('status codes reduce to what they say about a credential', () => {
  assert.equal(outcome(200), 'ok');
  assert.equal(outcome(401), 'unauthenticated');
  assert.equal(outcome(403), 'forbidden');
  assert.equal(outcome(404), 'missing');
  assert.equal(outcome(500), 'other');
  assert.equal(outcome(0), 'error');
  assert.equal(outcome(null), 'error');
});

test('a total failure and a partial one have different names', () => {
  assert.equal(shape(DEAD), 'uniform-401');
  assert.equal(shape(ALIVE), 'healthy');
  assert.equal(shape([['public', 'ok'], ['identity', 'forbidden']]), 'selective');
  assert.equal(shape([['public', 'missing'], ['identity', 'forbidden']]), 'mixed');
  assert.equal(shape([]), 'nothing-probed');
});

test('a rung the control never ran does not count as agreement', () => {
  const rows = compare(ALIVE, [['public', 'ok']]);
  assert.equal(rows[0].agrees, true);
  assert.equal(rows[1].control, null);
  assert.equal(rows[1].agrees, false);
});

test('without a control the script declines to name a cause', () => {
  const [state, detail] = diagnose(DEAD);
  assert.equal(state, 'no-control');
  assert.match(detail, /expiry, revocation and a truncated string/);
});

test('a uniform 401 against a healthy control is the credential', () => {
  const [state, detail] = diagnose(DEAD, ALIVE);
  assert.equal(state, 'credential-is-the-variable');
  assert.match(detail, /eliminated/);
});

test('two dead credentials are not two expiries', () => {
  const [state, detail] = diagnose(DEAD, DEAD);
  assert.equal(state, 'both-dead');
  assert.match(detail, /same second/);
});

test('identical failures on one rung are the resource', () => {
  const suspect = [['public', 'ok'], ['identity', 'ok'], ['repository', 'missing']];
  const [state, detail] = diagnose(suspect, suspect.map((row) => [...row]));
  assert.equal(state, 'resource-changed');
  assert.match(detail, /repository/);
});

test('a credential that authenticates anything has not expired', () => {
  const suspect = [['public', 'ok'], ['identity', 'ok'], ['repository', 'forbidden']];
  const [state, detail] = diagnose(suspect, ALIVE);
  assert.equal(state, 'access-not-expiry');
  assert.match(detail, /has not expired/);
  assert.match(detail, /repository \\(forbidden\\)/);
});

test('a healthy suspect sends you somewhere else', () => {
  assert.equal(diagnose(ALIVE, ALIVE)[0], 'suspect-healthy');
  assert.equal(diagnose(ALIVE)[0], 'suspect-healthy');
});

test('disagreeing shapes are reported rather than narrated', () => {
  const suspect = [['public', 'missing'], ['identity', 'forbidden']];
  const control = [['public', 'ok'], ['identity', 'unauthenticated']];
  const [state, detail] = diagnose(suspect, control);
  assert.equal(state, 'mixed');
  assert.match(detail, /rather than picking a story/);
});

test('nothing probed is not a pass', () => {
  assert.equal(diagnose([], ALIVE)[0], 'nothing-probed');
});
''',
"faq": [
 ("Can I ask the API when my token expired?",
  "Not after the fact. The github-authentication-token-expiration header is only returned on successful authenticated requests, so it exists precisely while you do not need it and disappears the moment you do. A read-only credential also cannot enumerate the tokens on an account, so there is no endpoint that will list the dead one and its date. The expiry has to be recorded where the secret is stored, by you, when you mint it."),
 ("How is an expired token different from a revoked one, from the API's side?",
  "It is not, and that is a deliberate design choice rather than an oversight. Distinguishing them would tell anyone holding a guessed value whether it was ever real. The practical consequence is that the script in this note never prints the word expired as a conclusion: it reports that the credential is the variable, and the calendar entry you kept is what turns that into expiry."),
 ("What counts as a good control credential?",
  "Anything known to work right now, run from the same process at the same moment. A colleague's token, a freshly minted one, or the App installation you were planning to migrate to. What it must not be is a token used at a different time or from a different machine, because then you have varied two things and the comparison proves nothing."),
 ("Both credentials failed. What does that actually mean?",
  "That the cause is something they share rather than something either of them is. In practice that is the secrets store handing out a stale or truncated value to both, an egress proxy or IP allow list that changed, or an organization action that revoked a whole class of tokens at once. The useful next step is to try a credential that did not come through the same pipeline."),
 ("Do fine-grained tokens have the same cliff?",
  "They have a harder one. Fine-grained personal access tokens must carry an expiry, capped at 366 days unless the organization allows longer, and organizations can enforce a shorter maximum. So the question is never whether a fine-grained token will expire, only when. That makes watching the clock on a live credential the higher-value habit, which is the note next door."),
],
"related": [
 ("/github/token-expiring-soon/", "The token expires in days and nobody is watching"),
 ("/github/bad-credentials-401/", "401 Bad credentials on every endpoint"),
 ("/github/saml-partial-results/", "Org lists silently omit SSO-enforced orgs"),
],
"citations": [CITE_MANAGING_PATS, CITE_TROUBLESHOOT, CITE_AUTH_REST, CITE_APP_INSTALL_AUTH],
},

{
"slug": "token-expiring-soon",
"title": "The token expires in days and nothing is watching the clock",
"description": "Every authenticated response carries the token's expiry in a header. Reading it turns a total outage into a calendar entry; absence is its own finding.",
"h1": "the token expires in days and nothing is watching the clock",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github token expiration header", "github-authentication-token-expiration",
             "github fine-grained token expiry", "warn before github token expires",
             "github pat expiry monitoring"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nothing is broken. That is the entire point of this note: it is the one that runs before the outage rather than after it. Somewhere in your environment is a credential with six days left on it, and the only thing standing between you and a 09:14 Tuesday is that nobody has read a header GitHub has been sending on every single response for months.",
"short_answer": """<p>Every authenticated REST response for a credential that <em>has</em> an expiry carries <code>github-authentication-token-expiration</code>, with the exact timestamp. One free request reads it. Fine-grained personal access tokens must have an expiry, capped at 366 days unless the organization permits longer, and organizations can enforce something much shorter, so for those the question is never whether but when.</p>
<p>The honest half of the check is what happens when the header is <strong>not</strong> there, and it is why this cannot be a one-liner. An absent header means either the credential never expires &mdash; which is a bigger risk than one that does, not a smaller one &mdash; or that its class does not report an expiry. Those are different findings with different repairs, and a script that prints "no expiry" for both is worse than no script. The one below names which, alerts at 30, 14 and 3 days, and refuses to raise an alarm about a GitHub App installation token whose one-hour life is the desired state.</p>""",
"problem": """<p>Expiry has no warning signal in normal operation. There is no 429, no deprecation notice, no degraded mode, no email to the service account nobody reads. The credential works perfectly at 09:13 and is refused at 09:14, and the failure is total across every endpoint at once. As failure modes go it is maximally abrupt and minimally informative.</p>
<p>The information is also asymmetric in the worst direction. The expiry is readable only while the credential still works, and becomes unreadable at exactly the moment you want it. So the check has to be running <em>before</em> the incident or it can never run at all &mdash; there is no post-mortem version of it.</p>
<p>And the naive version of the check is actively misleading. A script that reports "no expiry found, all good" gives a clean bill of health to a credential that never expires, which is the one you should be most worried about, and to a credential whose class simply does not report one, about which it has learned nothing. Two very different silences, printed identically.</p>""",
"why": """<p><strong>The header is on ordinary responses, not on a special endpoint.</strong> There is no "describe my token" API. GitHub attaches <code>github-authentication-token-expiration</code> to authenticated REST responses for credentials that carry an expiry, which means any free call &mdash; <code>GET /rate_limit</code> is the obvious one, since it consumes no quota &mdash; will tell you.</p>
<p><strong>You can only ask about the credential you are holding.</strong> A read-only token cannot enumerate the tokens on an account, so this is a per-credential check, not an inventory of everything your organization has issued. The way to cover a fleet is to name every environment variable that holds one and check them all in the same run, which is what the script does.</p>
<p><strong>Absence of the header is ambiguous and must be reported as such.</strong> Classic PATs can be minted with no expiry at all; some credential classes do not surface one. The script separates "the request succeeded and there was no header" from "the request failed so nothing could be read", because only the first of those is a finding about the credential.</p>
<p><strong>An expiry under two hours is almost always good news.</strong> A GitHub App installation token lives about an hour and is minted automatically. Alarming on it would train everyone to ignore the alert. The script labels it as short-lived and says plainly that it cannot distinguish it from a PAT in its final two hours, which is the rare case where you would want to know.</p>
<p><strong>Thresholds beat a single alarm.</strong> Thirty days is when someone can plan a rotation, fourteen is when it goes on a sprint, three is when it is an interrupt. One alert at zero is not monitoring, it is an incident with extra steps.</p>""",
"steps": [
 {"h": "List every environment variable that holds a GitHub credential",
  "body": """<p>Not just the obvious one. Most integrations have accumulated a second token for a different account, a control credential from the last incident, and one in a CI secret nobody has touched in a year. The check costs one free request each, so the marginal cost of including a credential is nothing and the cost of omitting it is the outage.</p>"""},
 {"h": "Make one free authenticated request per credential and read the header",
  "body": """<p><code>GET /rate_limit</code> is authenticated and consumes no quota, which makes it the right probe to run on a schedule. Read <code>github-authentication-token-expiration</code> off the response case-insensitively, because header case is not something to rely on.</p>"""},
 {"h": "Classify the credentials that report no expiry, rather than passing them",
  "body": """<p>A successful request with no expiry header means the credential does not expire, or does not say. Report that as its own state and treat a never-expiring credential as a finding to act on: an unrotated permanent token is a larger long-term risk than one with a date attached.</p>"""},
 {"h": "Bucket by 30, 14 and 3 days and sort by urgency",
  "body": """<p>Sorting by soonest is not enough on its own, because an unreadable credential should outrank one with ninety days left. Order by state first and by remaining time second, so the top line of the report is always the thing to do next.</p>"""},
 {"h": "Move the unattended ones to a GitHub App and stop keeping the calendar",
  "body": """<p>For automation with no human owner, an App installation removes the whole category: tokens are minted on demand, live about an hour, and never appear in anyone's diary. Rotation stops being a task. Keep the expiry check running afterwards anyway &mdash; it will show short-lived and prove the migration actually happened.</p>"""},
],
"verify": """<p>Run it on a schedule and read the first line. The report is ordered so the top row is the credential to deal with, whether that is because it is closest to expiry or because it could not be read at all.</p>
<pre><code class="language-bash">python3 github_token_expiry_watch.py GITHUB_TOKEN GITHUB_CI_TOKEN GITHUB_BOT_TOKEN
# GITHUB_CI_TOKEN   critical            2.4 day(s)  read from the header
# GITHUB_TOKEN      notice             28.9 day(s)  read from the header
# GITHUB_BOT_TOKEN  no-expiry-reported          -   succeeded and carried no
#                                                   expiry header
# critical: GITHUB_CI_TOKEN expires in 2.4 day(s). Alert at 30, 14 and 3 days
#   rather than at zero.</code></pre>""",
"code_intro": "One free GET per credential and nothing else on the wire. The credentials are read from named environment variables and never printed, compared or fingerprinted: this script does not care what class a token is, only what its response headers say about its remaining life. The parsing is the fiddly part &mdash; the timestamp arrives in more than one shape and a timezone that has to be honoured &mdash; so it is a pure function, as are the bucketing, the classification of a missing header, and the ordering.",
"py_file": "github_token_expiry_watch.py",
"py": '''"""Read how long each GitHub credential has left, before it costs you an outage.

Read only. One GET /rate_limit per credential, which is authenticated and
consumes no quota from any bucket, so this is safe to run on a schedule.

GitHub attaches github-authentication-token-expiration to authenticated REST
responses for credentials that carry an expiry. That header is the only place
the date is readable, and it is readable only while the credential still works.
"""
import argparse
import calendar
import json
import logging
import os
import re
import sys
import time

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_token_expiry_watch")

API = "https://api.github.com"
UA = "github-token-expiry-watch/1.0"

HEADER = "github-authentication-token-expiration"
DAY = 86400

# Under two hours on a working credential is a minted GitHub App installation
# token, which is the desired end state rather than an emergency. It is also a
# personal access token in its final two hours, and the header cannot tell them
# apart, so the report says both.
SHORT_LIVED_S = 2 * 3600

# Notice, warning, critical. One alarm at zero is not monitoring.
DEFAULT_THRESHOLDS = (30, 14, 3)

_ISO_T = re.compile(r"^(\\d{4}-\\d{2}-\\d{2})T")
_STAMP = re.compile(r"^(\\d{4})-(\\d{2})-(\\d{2})(?:[ ](\\d{2}):(\\d{2})(?::(\\d{2}))?)?$")
_OFFSET = re.compile(r"([+-]\\d{2}:?\\d{2})$")


def parse_expiry(value):
    """Epoch seconds from the expiry header, or None. Pure.

    The documented shape is "2026-09-30 12:00:00 UTC", but an ISO timestamp with
    a Z or a numeric offset turns up too. Anything that does not parse returns
    None rather than a plausible wrong date, because a wrong expiry is worse
    than no expiry.
    """
    if not isinstance(value, str):
        return None
    # Only the ISO separator, never any other T: the documented shape ends in
    # "UTC", and a blanket replace turns that into "U C".
    text = _ISO_T.sub(r"\\1 ", value.strip())
    if not text:
        return None

    offset = "+0000"
    upper = text.upper()
    if upper.endswith(" UTC") or upper.endswith(" GMT"):
        text = text[:-4].strip()
    elif upper.endswith("Z"):
        text = text[:-1].strip()
    else:
        found = _OFFSET.search(text)
        if found:
            offset = found.group(1).replace(":", "")
            text = text[:found.start()].strip()

    stamp = _STAMP.match(text)
    if not stamp:
        return None
    year, month, day, hour, minute, second = stamp.groups()
    sign = 1 if offset[0] == "-" else -1
    shift = sign * (int(offset[1:3]) * 3600 + int(offset[3:5]) * 60)
    base = calendar.timegm((int(year), int(month), int(day), int(hour or 0),
                            int(minute or 0), int(second or 0), 0, 0, 0))
    return base + shift


def header_value(headers, name=HEADER):
    """Case-insensitive header lookup. Pure."""
    for key, value in (headers or {}).items():
        if str(key).lower() == name:
            return value
    return None


def seconds_left(expiry, now):
    """Seconds between now and the expiry; None when either is unreadable. Pure."""
    try:
        return int(expiry) - int(now)
    except (TypeError, ValueError):
        return None


def bucket(remaining, thresholds=DEFAULT_THRESHOLDS):
    """Name the urgency of a remaining lifetime. Pure."""
    if remaining is None:
        return "unknown"
    if remaining <= 0:
        return "expired"
    if remaining < SHORT_LIVED_S:
        return "short-lived"
    notice, warning, critical = thresholds
    days = remaining / DAY
    if days <= critical:
        return "critical"
    if days <= warning:
        return "warning"
    if days <= notice:
        return "notice"
    return "ok"


def reading(name, status, headers, now, thresholds=DEFAULT_THRESHOLDS):
    """One credential's expiry reading, including why there might not be one. Pure.

    The states that matter are the two silences. A request that succeeded and
    carried no expiry header is a finding about the credential. A request that
    failed is a finding about nothing at all, and printing them the same way is
    how a monitoring script gives a permanent token a clean bill of health.
    """
    try:
        status = int(status)
    except (TypeError, ValueError):
        status = 0

    if status == 401:
        return {"name": name, "state": "rejected", "seconds_left": None,
                "why": "the credential was refused, so its expiry is no longer "
                       "a forecast"}
    if not 200 <= status < 300:
        return {"name": name, "state": "unreadable", "seconds_left": None,
                "why": "the probe returned %d, so nothing can be read from its "
                       "headers" % status}

    raw = header_value(headers)
    if raw is None:
        return {"name": name, "state": "no-expiry-reported", "seconds_left": None,
                "why": "the request succeeded and carried no expiry header, "
                       "which means either the credential never expires or its "
                       "class does not report one. The header cannot tell those "
                       "apart"}

    expiry = parse_expiry(raw)
    if expiry is None:
        return {"name": name, "state": "unreadable-header", "seconds_left": None,
                "why": "the expiry header was present but did not parse: %r" % raw}

    remaining = seconds_left(expiry, now)
    return {"name": name, "state": bucket(remaining, thresholds),
            "seconds_left": remaining, "expires_at": expiry,
            "why": "read from the %s response header" % HEADER}


# Urgency first. An unreadable credential outranks one with ninety days left,
# because you have learned nothing about it and that is worse than good news.
ORDER = {"expired": 0, "critical": 1, "warning": 2, "rejected": 3,
         "unreadable-header": 4, "unreadable": 5, "no-expiry-reported": 6,
         "notice": 7, "short-lived": 8, "ok": 9, "unknown": 10}


def schedule(rows):
    """Order the readings by urgency, then by soonest. Pure."""
    def key(row):
        remaining = row.get("seconds_left")
        return (ORDER.get(row.get("state"), 99),
                remaining if isinstance(remaining, int) else 1 << 30,
                str(row.get("name")))
    return sorted(rows or [], key=key)


def verdict(ordered):
    """The one line to act on. Pure."""
    if not ordered:
        return ("nothing-checked",
                "no credentials were named, so nothing was checked.")
    top = ordered[0]
    state = top["state"]
    name = top["name"]
    remaining = top.get("seconds_left")

    if state == "expired":
        return ("expired",
                "%s has already passed its expiry. It will be answering 401 Bad "
                "credentials, identically to a credential that was revoked." % name)
    if state in ("critical", "warning", "notice"):
        return (state,
                "%s expires in %.1f day(s). Alert at 30, 14 and 3 days rather "
                "than at zero." % (name, remaining / DAY))
    if state == "short-lived":
        return ("short-lived",
                "%s expires in %d minute(s), which is what a freshly minted "
                "GitHub App installation token looks like and is a non-event. "
                "It is also what a personal access token in its final two hours "
                "looks like, and the header does not distinguish them."
                % (name, remaining // 60))
    if state == "rejected":
        return ("rejected",
                "%s was refused, so there is no expiry left to forecast. Whether "
                "it expired or was revoked is not observable from here." % name)
    if state in ("unreadable", "unreadable-header"):
        return ("unreadable", "%s could not be read: %s" % (name, top.get("why")))
    if state == "no-expiry-reported":
        return ("no-expiry-reported",
                "%s reported no expiry. Either it never expires, which is a "
                "larger standing risk than one that does, or its class does not "
                "surface a date. Find out which before calling it healthy." % name)
    return ("ok", "the soonest expiry is %s at %.1f day(s)."
            % (name, (remaining or 0) / DAY))


def probe(name, token):
    """One free authenticated GET. Returns (status, headers)."""
    try:
        response = requests.get(
            API + "/rate_limit",
            headers={"Authorization": "Bearer " + token,
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28",
                     "User-Agent": UA},
            timeout=30)
    except requests.RequestException as exc:
        log.error("%s: request failed: %s", name, exc)
        return 0, {}
    return response.status_code, dict(response.headers)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("env", nargs="*", default=["GITHUB_TOKEN"],
                        help="environment variable names holding credentials")
    parser.add_argument("--notice", type=int, default=DEFAULT_THRESHOLDS[0])
    parser.add_argument("--warning", type=int, default=DEFAULT_THRESHOLDS[1])
    parser.add_argument("--critical", type=int, default=DEFAULT_THRESHOLDS[2])
    args = parser.parse_args()

    thresholds = (args.notice, args.warning, args.critical)
    now = int(time.time())
    rows = []
    for name in (args.env or ["GITHUB_TOKEN"]):
        token = os.environ.get(name)
        if not token:
            rows.append({"name": name, "state": "unreadable", "seconds_left": None,
                         "why": "the environment variable is not set"})
            continue
        status, headers = probe(name, token)
        rows.append(reading(name, status, headers, now, thresholds))

    ordered = schedule(rows)
    for row in ordered:
        remaining = row.get("seconds_left")
        left = "-" if remaining is None else "%.1f day(s)" % (remaining / DAY)
        log.info("%-20s %-20s %12s  %s", row["name"], row["state"], left,
                 row.get("why", ""))

    state, detail = verdict(ordered)
    log.info("%s: %s", state, detail)

    if state in ("critical", "warning", "expired"):
        log.info("repair: rotate now, and record the new expiry in the same "
                 "place the secret is stored so the next person sees it.")
    if state in ("critical", "warning", "notice", "expired", "no-expiry-reported"):
        log.info("repair: for automation with no human owner, authenticate as a "
                 "GitHub App installation. Its tokens are minted on demand, live "
                 "about an hour, and never need a diary entry.")

    print(json.dumps({"state": state, "readings": ordered}, indent=2))
    return 1 if state not in ("ok", "short-lived", "nothing-checked") else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-token-expiry-watch.mjs",
"js": '''/**
 * Read how long each GitHub credential has left, before it costs you an outage.
 *
 * Read only. One GET /rate_limit per credential, which is authenticated and
 * consumes no quota, so this is safe to run on a schedule.
 *
 * github-authentication-token-expiration is the only place the date is
 * readable, and it is readable only while the credential still works.
 */
const API = 'https://api.github.com';
const UA = 'github-token-expiry-watch/1.0';

export const HEADER = 'github-authentication-token-expiration';
export const DAY = 86400;

// Under two hours on a working credential is a minted App installation token,
// which is the desired end state. It is also a PAT in its final two hours, and
// the header cannot tell them apart.
export const SHORT_LIVED_S = 2 * 3600;

// Notice, warning, critical. One alarm at zero is not monitoring.
export const DEFAULT_THRESHOLDS = [30, 14, 3];

const STAMP = /^(\\d{4})-(\\d{2})-(\\d{2})(?:[ ](\\d{2}):(\\d{2})(?::(\\d{2}))?)?$/;
const OFFSET = /([+-]\\d{2}:?\\d{2})$/;

/**
 * Epoch seconds from the expiry header, or null. Pure.
 * Anything that does not parse returns null rather than a plausible wrong date.
 */
export function parseExpiry(value) {
  if (typeof value !== 'string') return null;
  // Only the ISO separator, never any other T: the documented shape ends in
  // 'UTC', and a blanket replace turns that into 'U C'.
  let text = value.trim().replace(/^(\\d{4}-\\d{2}-\\d{2})T/, '$1 ');
  if (!text) return null;

  let offset = '+0000';
  const upper = text.toUpperCase();
  if (upper.endsWith(' UTC') || upper.endsWith(' GMT')) {
    text = text.slice(0, -4).trim();
  } else if (upper.endsWith('Z')) {
    text = text.slice(0, -1).trim();
  } else {
    const found = text.match(OFFSET);
    if (found) {
      offset = found[1].replace(':', '');
      text = text.slice(0, found.index).trim();
    }
  }

  const stamp = text.match(STAMP);
  if (!stamp) return null;
  const [, year, month, day, hour, minute, second] = stamp;
  const sign = offset[0] === '-' ? 1 : -1;
  const shift = sign * (Number(offset.slice(1, 3)) * 3600 + Number(offset.slice(3, 5)) * 60);
  const base = Date.UTC(Number(year), Number(month) - 1, Number(day),
    Number(hour ?? 0), Number(minute ?? 0), Number(second ?? 0)) / 1000;
  return base + shift;
}

/** Case-insensitive header lookup. Pure. */
export function headerValue(headers, name = HEADER) {
  for (const [key, value] of Object.entries(headers ?? {})) {
    if (String(key).toLowerCase() === name) return value;
  }
  return null;
}

/** Seconds between now and the expiry; null when either is unreadable. Pure. */
export function secondsLeft(expiry, now) {
  const e = Number.parseInt(expiry, 10);
  const n = Number.parseInt(now, 10);
  if (!Number.isFinite(e) || !Number.isFinite(n)) return null;
  return e - n;
}

/** Name the urgency of a remaining lifetime. Pure. */
export function bucket(remaining, thresholds = DEFAULT_THRESHOLDS) {
  if (remaining === null || remaining === undefined) return 'unknown';
  if (remaining <= 0) return 'expired';
  if (remaining < SHORT_LIVED_S) return 'short-lived';
  const [notice, warning, critical] = thresholds;
  const days = remaining / DAY;
  if (days <= critical) return 'critical';
  if (days <= warning) return 'warning';
  if (days <= notice) return 'notice';
  return 'ok';
}

/** One credential's expiry reading, including why there might not be one. Pure. */
export function reading(name, status, headers, now, thresholds = DEFAULT_THRESHOLDS) {
  const code = Number.parseInt(status, 10);
  const value = Number.isFinite(code) ? code : 0;

  if (value === 401) {
    return { name, state: 'rejected', seconds_left: null,
      why: 'the credential was refused, so its expiry is no longer a forecast' };
  }
  if (!(value >= 200 && value < 300)) {
    return { name, state: 'unreadable', seconds_left: null,
      why: `the probe returned ${value}, so nothing can be read from its headers` };
  }

  const raw = headerValue(headers);
  if (raw === null || raw === undefined) {
    return { name, state: 'no-expiry-reported', seconds_left: null,
      why: 'the request succeeded and carried no expiry header, which means ' +
        'either the credential never expires or its class does not report one. ' +
        'The header cannot tell those apart' };
  }

  const expiry = parseExpiry(raw);
  if (expiry === null) {
    return { name, state: 'unreadable-header', seconds_left: null,
      why: `the expiry header was present but did not parse: '${raw}'` };
  }

  const remaining = secondsLeft(expiry, now);
  return { name, state: bucket(remaining, thresholds), seconds_left: remaining,
    expires_at: expiry, why: `read from the ${HEADER} response header` };
}

// Urgency first. An unreadable credential outranks one with ninety days left.
export const ORDER = {
  expired: 0, critical: 1, warning: 2, rejected: 3, 'unreadable-header': 4,
  unreadable: 5, 'no-expiry-reported': 6, notice: 7, 'short-lived': 8, ok: 9,
  unknown: 10,
};

/** Order the readings by urgency, then by soonest. Pure. */
export function schedule(rows) {
  const rank = (row) => [
    ORDER[row.state] ?? 99,
    Number.isInteger(row.seconds_left) ? row.seconds_left : 2 ** 30,
    String(row.name),
  ];
  return [...(rows ?? [])].sort((a, b) => {
    const x = rank(a);
    const y = rank(b);
    for (let i = 0; i < x.length; i += 1) {
      if (x[i] < y[i]) return -1;
      if (x[i] > y[i]) return 1;
    }
    return 0;
  });
}

/** The one line to act on. Pure. */
export function verdict(ordered) {
  if (!ordered || !ordered.length) {
    return ['nothing-checked', 'no credentials were named, so nothing was checked.'];
  }
  const top = ordered[0];
  const { state, name } = top;
  const remaining = top.seconds_left;

  if (state === 'expired') {
    return ['expired',
      `${name} has already passed its expiry. It will be answering 401 Bad ` +
      'credentials, identically to a credential that was revoked.'];
  }
  if (['critical', 'warning', 'notice'].includes(state)) {
    return [state,
      `${name} expires in ${(remaining / DAY).toFixed(1)} day(s). Alert at 30, ` +
      '14 and 3 days rather than at zero.'];
  }
  if (state === 'short-lived') {
    return ['short-lived',
      `${name} expires in ${Math.floor(remaining / 60)} minute(s), which is what ` +
      'a freshly minted GitHub App installation token looks like and is a ' +
      'non-event. It is also what a personal access token in its final two hours ' +
      'looks like, and the header does not distinguish them.'];
  }
  if (state === 'rejected') {
    return ['rejected',
      `${name} was refused, so there is no expiry left to forecast. Whether it ` +
      'expired or was revoked is not observable from here.'];
  }
  if (state === 'unreadable' || state === 'unreadable-header') {
    return ['unreadable', `${name} could not be read: ${top.why}`];
  }
  if (state === 'no-expiry-reported') {
    return ['no-expiry-reported',
      `${name} reported no expiry. Either it never expires, which is a larger ` +
      'standing risk than one that does, or its class does not surface a date. ' +
      'Find out which before calling it healthy.'];
  }
  return ['ok',
    `the soonest expiry is ${name} at ${((remaining ?? 0) / DAY).toFixed(1)} day(s).`];
}

async function probe(name, token) {
  try {
    const res = await fetch(`${API}/rate_limit`, {
      headers: {
        Authorization: `Bearer ${token}`,
        Accept: 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
        'User-Agent': UA,
      },
    });
    const headers = {};
    for (const [k, v] of res.headers.entries()) headers[k.toLowerCase()] = v;
    return { status: res.status, headers };
  } catch (err) {
    console.error(`${name}: request failed: ${err.message}`);
    return { status: 0, headers: {} };
  }
}

async function main() {
  const names = process.argv.slice(2);
  const wanted = names.length ? names : ['GITHUB_TOKEN'];
  const now = Math.floor(Date.now() / 1000);

  const rows = [];
  for (const name of wanted) {
    const token = process.env[name];
    if (!token) {
      rows.push({ name, state: 'unreadable', seconds_left: null,
        why: 'the environment variable is not set' });
      continue;
    }
    const { status, headers } = await probe(name, token);
    rows.push(reading(name, status, headers, now));
  }

  const ordered = schedule(rows);
  for (const row of ordered) {
    const left = row.seconds_left === null ? '-' : `${(row.seconds_left / DAY).toFixed(1)} day(s)`;
    console.log(`${row.name.padEnd(20)} ${row.state.padEnd(20)} ${left.padStart(12)}  ${row.why ?? ''}`);
  }

  const [state, detail] = verdict(ordered);
  console.log(`${state}: ${detail}`);

  if (['critical', 'warning', 'expired'].includes(state)) {
    console.log('repair: rotate now, and record the new expiry in the same place ' +
      'the secret is stored so the next person sees it.');
  }
  if (['critical', 'warning', 'notice', 'expired', 'no-expiry-reported'].includes(state)) {
    console.log('repair: for automation with no human owner, authenticate as a ' +
      'GitHub App installation; its tokens live about an hour and need no diary entry.');
  }

  console.log(JSON.stringify({ state, readings: ordered }, null, 2));
  process.exitCode = ['ok', 'short-lived', 'nothing-checked'].includes(state) ? 0 : 1;
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err); process.exitCode = 2; });
}
''',
"test_intro": "Three things decide whether this report is trustworthy, and none of them needs a network. The timestamp has to parse in every shape GitHub sends it in and return nothing at all for a shape it does not recognise, because a plausible wrong date is worse than a blank. A successful request with no header and a failed request must land in different states. And the ordering has to put an unreadable credential above a healthy one, because good news you cannot verify is not good news.",
"test_py_file": "test_github_token_expiry_watch.py",
"test_py": '''from github_token_expiry_watch import (
    bucket, header_value, parse_expiry, reading, schedule, seconds_left, verdict,
)

NOON = 1790769600  # 2026-09-30 12:00:00 UTC


def test_the_documented_shape_parses_to_the_right_instant():
    assert parse_expiry("2026-09-30 12:00:00 UTC") == NOON


def test_the_iso_shapes_parse_to_the_same_instant():
    assert parse_expiry("2026-09-30T12:00:00Z") == NOON
    assert parse_expiry("2026-09-30T12:00:00+00:00") == NOON


def test_a_numeric_offset_is_honoured_rather_than_ignored():
    assert parse_expiry("2026-09-30 07:00:00 -0500") == NOON
    assert parse_expiry("2026-09-30 14:00:00 +02:00") == NOON


def test_a_bare_date_is_read_as_midnight_utc():
    assert parse_expiry("2026-09-30") == NOON - 12 * 3600


def test_a_shape_that_is_not_recognised_returns_nothing_at_all():
    assert parse_expiry("soon") is None
    assert parse_expiry("30/09/2026") is None
    assert parse_expiry("") is None
    assert parse_expiry(None) is None


def test_the_header_is_found_whatever_its_case():
    assert header_value({"Github-Authentication-Token-Expiration": "x"}) == "x"
    assert header_value({"github-authentication-token-expiration": "y"}) == "y"
    assert header_value({"etag": "z"}) is None
    assert header_value(None) is None


def test_remaining_time_is_a_number_or_nothing():
    assert seconds_left(NOON, NOON - 60) == 60
    assert seconds_left(None, NOON) is None
    assert seconds_left(NOON, "later") is None


def test_the_thresholds_bucket_as_advertised():
    assert bucket(None) == "unknown"
    assert bucket(0) == "expired"
    assert bucket(-1) == "expired"
    assert bucket(3600) == "short-lived"
    assert bucket(2 * 86400) == "critical"
    assert bucket(10 * 86400) == "warning"
    assert bucket(20 * 86400) == "notice"
    assert bucket(90 * 86400) == "ok"


def test_custom_thresholds_are_respected():
    assert bucket(20 * 86400, thresholds=(60, 30, 21)) == "critical"


def test_a_successful_request_with_no_header_is_its_own_state():
    row = reading("GITHUB_TOKEN", 200, {"etag": "abc"}, NOON)
    assert row["state"] == "no-expiry-reported"
    assert "never expires or its class does not report one" in row["why"]


def test_a_failed_request_is_not_the_same_silence():
    assert reading("GITHUB_TOKEN", 500, {}, NOON)["state"] == "unreadable"
    assert reading("GITHUB_TOKEN", 0, {}, NOON)["state"] == "unreadable"


def test_a_refused_credential_has_no_forecast_left():
    assert reading("GITHUB_TOKEN", 401, {}, NOON)["state"] == "rejected"


def test_an_unparseable_header_is_reported_rather_than_guessed():
    row = reading("GITHUB_TOKEN", 200,
                  {"github-authentication-token-expiration": "next tuesday"}, NOON)
    assert row["state"] == "unreadable-header"
    assert "did not parse" in row["why"]


def test_a_live_reading_carries_the_remaining_seconds():
    headers = {"github-authentication-token-expiration": "2026-09-30 12:00:00 UTC"}
    row = reading("GITHUB_TOKEN", 200, headers, NOON - 2 * 86400)
    assert row["state"] == "critical"
    assert row["seconds_left"] == 2 * 86400
    assert row["expires_at"] == NOON


def test_an_unreadable_credential_outranks_a_healthy_one():
    rows = [{"name": "b", "state": "ok", "seconds_left": 90 * 86400},
            {"name": "a", "state": "unreadable", "seconds_left": None},
            {"name": "c", "state": "critical", "seconds_left": 2 * 86400}]
    assert [row["name"] for row in schedule(rows)] == ["c", "a", "b"]


def test_the_soonest_wins_inside_one_state():
    rows = [{"name": "later", "state": "warning", "seconds_left": 12 * 86400},
            {"name": "sooner", "state": "warning", "seconds_left": 8 * 86400}]
    assert schedule(rows)[0]["name"] == "sooner"


def test_the_verdict_is_the_top_row():
    ordered = schedule([{"name": "GITHUB_CI_TOKEN", "state": "critical",
                         "seconds_left": 2 * 86400}])
    state, detail = verdict(ordered)
    assert state == "critical"
    assert "2.0 day(s)" in detail
    assert "30, 14 and 3 days" in detail


def test_an_hour_left_is_reported_as_a_non_event():
    state, detail = verdict([{"name": "GITHUB_TOKEN", "state": "short-lived",
                              "seconds_left": 3540}])
    assert state == "short-lived"
    assert "59 minute(s)" in detail
    assert "does not distinguish them" in detail


def test_no_expiry_is_a_finding_and_not_a_clean_bill_of_health():
    state, detail = verdict([{"name": "GITHUB_BOT_TOKEN",
                              "state": "no-expiry-reported", "seconds_left": None}])
    assert state == "no-expiry-reported"
    assert "larger standing risk" in detail


def test_nothing_named_is_reported_as_nothing_checked():
    assert verdict([])[0] == "nothing-checked"
''',
"test_js_file": "github-token-expiry-watch.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import {
  bucket, headerValue, parseExpiry, reading, schedule, secondsLeft, verdict,
} from './github-token-expiry-watch.mjs';

const NOON = 1790769600; // 2026-09-30 12:00:00 UTC

test('the documented shape parses to the right instant', () => {
  assert.equal(parseExpiry('2026-09-30 12:00:00 UTC'), NOON);
});

test('the iso shapes parse to the same instant', () => {
  assert.equal(parseExpiry('2026-09-30T12:00:00Z'), NOON);
  assert.equal(parseExpiry('2026-09-30T12:00:00+00:00'), NOON);
});

test('a numeric offset is honoured rather than ignored', () => {
  assert.equal(parseExpiry('2026-09-30 07:00:00 -0500'), NOON);
  assert.equal(parseExpiry('2026-09-30 14:00:00 +02:00'), NOON);
});

test('a bare date is read as midnight utc', () => {
  assert.equal(parseExpiry('2026-09-30'), NOON - 12 * 3600);
});

test('a shape that is not recognised returns nothing at all', () => {
  assert.equal(parseExpiry('soon'), null);
  assert.equal(parseExpiry('30/09/2026'), null);
  assert.equal(parseExpiry(''), null);
  assert.equal(parseExpiry(null), null);
});

test('the header is found whatever its case', () => {
  assert.equal(headerValue({ 'Github-Authentication-Token-Expiration': 'x' }), 'x');
  assert.equal(headerValue({ 'github-authentication-token-expiration': 'y' }), 'y');
  assert.equal(headerValue({ etag: 'z' }), null);
  assert.equal(headerValue(null), null);
});

test('remaining time is a number or nothing', () => {
  assert.equal(secondsLeft(NOON, NOON - 60), 60);
  assert.equal(secondsLeft(null, NOON), null);
  assert.equal(secondsLeft(NOON, 'later'), null);
});

test('the thresholds bucket as advertised', () => {
  assert.equal(bucket(null), 'unknown');
  assert.equal(bucket(0), 'expired');
  assert.equal(bucket(-1), 'expired');
  assert.equal(bucket(3600), 'short-lived');
  assert.equal(bucket(2 * 86400), 'critical');
  assert.equal(bucket(10 * 86400), 'warning');
  assert.equal(bucket(20 * 86400), 'notice');
  assert.equal(bucket(90 * 86400), 'ok');
});

test('custom thresholds are respected', () => {
  assert.equal(bucket(20 * 86400, [60, 30, 21]), 'critical');
});

test('a successful request with no header is its own state', () => {
  const row = reading('GITHUB_TOKEN', 200, { etag: 'abc' }, NOON);
  assert.equal(row.state, 'no-expiry-reported');
  assert.match(row.why, /never expires or its class does not report one/);
});

test('a failed request is not the same silence', () => {
  assert.equal(reading('GITHUB_TOKEN', 500, {}, NOON).state, 'unreadable');
  assert.equal(reading('GITHUB_TOKEN', 0, {}, NOON).state, 'unreadable');
});

test('a refused credential has no forecast left', () => {
  assert.equal(reading('GITHUB_TOKEN', 401, {}, NOON).state, 'rejected');
});

test('an unparseable header is reported rather than guessed', () => {
  const row = reading('GITHUB_TOKEN', 200,
    { 'github-authentication-token-expiration': 'next tuesday' }, NOON);
  assert.equal(row.state, 'unreadable-header');
  assert.match(row.why, /did not parse/);
});

test('a live reading carries the remaining seconds', () => {
  const headers = { 'github-authentication-token-expiration': '2026-09-30 12:00:00 UTC' };
  const row = reading('GITHUB_TOKEN', 200, headers, NOON - 2 * 86400);
  assert.equal(row.state, 'critical');
  assert.equal(row.seconds_left, 2 * 86400);
  assert.equal(row.expires_at, NOON);
});

test('an unreadable credential outranks a healthy one', () => {
  const rows = [
    { name: 'b', state: 'ok', seconds_left: 90 * 86400 },
    { name: 'a', state: 'unreadable', seconds_left: null },
    { name: 'c', state: 'critical', seconds_left: 2 * 86400 },
  ];
  assert.deepEqual(schedule(rows).map((row) => row.name), ['c', 'a', 'b']);
});

test('the soonest wins inside one state', () => {
  const rows = [
    { name: 'later', state: 'warning', seconds_left: 12 * 86400 },
    { name: 'sooner', state: 'warning', seconds_left: 8 * 86400 },
  ];
  assert.equal(schedule(rows)[0].name, 'sooner');
});

test('the verdict is the top row', () => {
  const ordered = schedule([{ name: 'GITHUB_CI_TOKEN', state: 'critical', seconds_left: 2 * 86400 }]);
  const [state, detail] = verdict(ordered);
  assert.equal(state, 'critical');
  assert.match(detail, /2\\.0 day\\(s\\)/);
  assert.match(detail, /30, 14 and 3 days/);
});

test('an hour left is reported as a non event', () => {
  const [state, detail] = verdict([{ name: 'GITHUB_TOKEN', state: 'short-lived', seconds_left: 3540 }]);
  assert.equal(state, 'short-lived');
  assert.match(detail, /59 minute\\(s\\)/);
  assert.match(detail, /does not distinguish them/);
});

test('no expiry is a finding and not a clean bill of health', () => {
  const [state, detail] = verdict([{ name: 'GITHUB_BOT_TOKEN', state: 'no-expiry-reported', seconds_left: null }]);
  assert.equal(state, 'no-expiry-reported');
  assert.match(detail, /larger standing risk/);
});

test('nothing named is reported as nothing checked', () => {
  assert.equal(verdict([])[0], 'nothing-checked');
});
''',
"faq": [
 ("Which request should I use to read the expiry header?",
  "Any authenticated one, which makes GET /rate_limit the obvious choice because it consumes no quota from any bucket. That matters when the check runs on a schedule across several credentials: the monitoring costs nothing it is monitoring. GET /user works too but is refused by an Actions token, so it fails on exactly the credential class you might want to include."),
 ("Can I list every token on the account and check them all?",
  "No. A read-only credential cannot enumerate the tokens on an account, so the API can only tell you about the credential you are currently holding. Fleet coverage has to come from your side: name every environment variable that holds one and check them in the same run. Anything not in that list is not being watched, and the script cannot know it exists."),
 ("The header is missing. Does that mean the token never expires?",
  "It means one of two things and the header will not say which. Classic personal access tokens can be minted with no expiry at all, and some credential classes simply do not surface a date. The script reports no-expiry-reported rather than picking one, because a permanent token treated as healthy is exactly the failure the check exists to prevent."),
 ("How far ahead should the alert fire?",
  "Thirty days is when a rotation can be planned, fourteen is when it fits in a sprint, and three is when it becomes an interrupt. The reason for three thresholds rather than one is that a single alarm gets snoozed once and then forgotten, whereas an escalating one is hard to ignore twice. Zero is not a threshold, it is an incident."),
 ("Our App installation token shows about an hour. Should I alert on that?",
  "No, that is the migration working. Installation tokens are minted on demand and live about an hour by design, so a short life there means nobody has to remember anything. The script labels it short-lived rather than critical for that reason, while saying plainly that a personal access token in its final two hours looks identical from the header alone."),
],
"related": [
 ("/github/classic-pat-expired/", "A classic PAT passed its expiry date"),
 ("/github/bad-credentials-401/", "401 Bad credentials on every endpoint"),
 ("/github/installation-repository-selection-partial/", "An App installation covers only some repos"),
],
"citations": [CITE_MANAGING_PATS, CITE_AUTH_REST, CITE_APP_INSTALL_AUTH, CITE_TROUBLESHOOT],
},

]
