#!/usr/bin/env python3
"""/github/ field notes, batch B — the writing.

Four failures with one shape: GitHub answers, the answer is well-formed, and the
answer is not the whole truth. A 404 that means "not allowed". A 200 that omits
two organizations and mentions it in a header. An installation that reports
faithfully on twelve of a hundred and forty repositories. And the one case where
GitHub does name what is missing, in a header nobody reads.

Read-only throughout: GET requests, a token with read access, and the repair
printed for a human to run rather than performed by a script holding a credential
that can reach private repositories.
"""

CITE_TROUBLESHOOT = ("Troubleshooting the REST API — GitHub Docs",
                     "https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api")
CITE_AUTHN = ("Authenticating to the REST API — GitHub Docs",
              "https://docs.github.com/en/rest/authentication/authenticating-to-the-rest-api")
CITE_PATS = ("Managing your personal access tokens — GitHub Docs",
             "https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens")
CITE_APP_PERMS = ("Permissions required for GitHub Apps — GitHub Docs",
                  "https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps")
CITE_CHOOSING = ("Choosing permissions for a GitHub App — GitHub Docs",
                 "https://docs.github.com/en/apps/creating-github-apps/registering-a-github-app/choosing-permissions-for-a-github-app")
CITE_EDIT_PERMS = ("Editing a GitHub App's permissions — GitHub Docs",
                   "https://docs.github.com/en/apps/maintaining-github-apps/editing-a-github-apps-permissions")
CITE_INSTALLATIONS = ("GitHub App installations — GitHub REST API",
                      "https://docs.github.com/en/rest/apps/installations")
CITE_APPS = ("GitHub Apps — GitHub REST API",
             "https://docs.github.com/en/rest/apps/apps")
CITE_INSTALL_AUTH = ("Authenticating as a GitHub App installation — GitHub Docs",
                     "https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation")
CITE_ORGS = ("Organizations — GitHub REST API",
             "https://docs.github.com/en/rest/orgs/orgs")
CITE_SAML_ABOUT = ("About authentication with SAML single sign-on — GitHub Docs",
                   "https://docs.github.com/en/enterprise-cloud@latest/authentication/authenticating-with-saml-single-sign-on/about-authentication-with-saml-single-sign-on")
CITE_SAML_AUTHZ = ("Authorizing a personal access token for use with SAML single sign-on — GitHub Docs",
                   "https://docs.github.com/en/enterprise-cloud@latest/authentication/authenticating-with-saml-single-sign-on/authorizing-a-personal-access-token-for-use-with-saml-single-sign-on")

GUIDES = [

{
"slug": "404-masking-403",
"title": "A permission error is disguised as 404 Not Found",
"description": "GitHub answers 404 rather than 403 for private resources a token cannot see, so a missing scope, a missing installation and a deleted repo look identical.",
"h1": "a permission error is disguised as 404 Not Found",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github api 404 not found", "github 404 instead of 403",
             "github api private repo not found", "octokit httperror not found",
             "github token cannot see repository"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The repository is open in a browser tab in front of you. The script asks for the same repository and gets <code>404 {\"message\":\"Not Found\"}</code>. Somebody checks the spelling, then the owner name, then the case of both, then writes a ticket saying the API is broken. The API is not broken. It is refusing to tell you that the repository exists, because telling you would leak the existence of a private repository to a credential that has no business knowing about it.",
"short_answer": """<p>Treat the 404 as a missing <em>fact</em>, not a missing resource, and go and get the fact from somewhere else. Three cheap reads settle it: <code>GET /user</code> says whether the token authenticates at all and carries <code>x-oauth-scopes</code>; <code>GET /repos/{owner}/{repo}</code> is the call that failed; and for a GitHub App, <code>GET /installation/repositories</code> says whether the repository is inside the installation.</p>
<p>The four answers those reads distinguish &mdash; dead token, missing scope, repository not in the installation, and no grant at all &mdash; have four different repairs and one identical status code.</p>""",
"problem": """<p>Every other API you integrate with uses 403 to mean "you are who you say you are and you may not have this". GitHub uses 404, deliberately, on private resources. The reasoning is sound: a 403 on <code>/repos/acme/project-nightingale</code> would confirm that <code>acme</code> has a repository called <code>project-nightingale</code>, and for a private repository that confirmation is itself the leak. So the API declines to distinguish "no such thing" from "not for you".</p>
<p>The cost lands on the person debugging. A 404 reads as a typo, and typos are the first thing anyone checks, so the first hour goes to spelling and the second to whether the repository was deleted. Meanwhile the actual cause is a token minted with <code>public_repo</code> instead of <code>repo</code>, or an App installed on the organization but never ticked for this repository, and neither of those is anywhere near where anyone is looking.</p>""",
"why": """<p><strong>The masking is a documented design decision, not a bug.</strong> GitHub returns 404 instead of 403 on private resources specifically to avoid confirming that they exist. No header, no error code and no message distinguishes the two cases, because a distinguishable response would defeat the point.</p>
<p><strong>Classic scopes are coarse and silent.</strong> A classic token with <code>public_repo</code> can read every public repository on the platform and no private ones. Against a private repository it does not get "insufficient scope"; it gets the same 404 an anonymous request gets. The <code>x-oauth-scopes</code> header on any authenticated response names what the token actually carries, which is the only place that difference is visible.</p>
<p><strong>Fine-grained tokens and App installations grant repositories one at a time.</strong> Both models replace "everything the user can see" with an explicit list. A repository absent from that list is outside the credential's world entirely, and being outside the credential's world is indistinguishable, over HTTP, from not existing.</p>
<p><strong>A dead token 404s everything private and 200s everything public.</strong> That combination is the most misleading of all, because the script visibly works. Public repositories answer, private ones do not, and the shape looks exactly like a permissions problem on specific repositories rather than a credential that expired last Tuesday.</p>""",
"steps": [
 {"h": "Establish that the credential is alive before anything else",
  "body": """<p><code>GET /user</code>. A 200 gives you the login the token belongs to, which is worth reading out loud: half of these incidents end with somebody realising the CI job holds a different account's token. A <code>401 Bad credentials</code> here means every 404 downstream is noise, and the repository question cannot be answered until the token is replaced.</p>"""},
 {"h": "Read the scopes off that same response",
  "body": """<p><code>x-oauth-scopes</code> lists what a classic or OAuth token carries. Keep <em>absent</em> and <em>empty</em> apart: an empty header means a classic token with nothing ticked, and no header at all means a fine-grained token or an App installation token, which do not use scopes. Those two look the same if you parse carelessly and they need opposite repairs.</p>"""},
 {"h": "Name the credential from its prefix, locally",
  "body": """<p><code>ghp_</code> classic PAT, <code>github_pat_</code> fine-grained PAT, <code>gho_</code> OAuth user token, <code>ghs_</code> App installation token, <code>ghu_</code> user-to-server, <code>ghr_</code> refresh token. This is a string comparison on a value you already hold, costs no request, and decides which of the following checks is even meaningful.</p>"""},
 {"h": "For an App, ask what the installation actually contains",
  "body": """<p><code>GET /installation/repositories?per_page=100</code>, paged. If the repository is in that list and <code>GET /repos/{owner}/{repo}</code> still 404s, the App is installed on it and lacks <code>Metadata: Read</code>, which every repository endpoint requires. If it is not in the list, the installation is set to selected repositories and this one was never ticked.</p>"""},
 {"h": "Print all the signals, not the status code",
  "body": """<p>The output that ends the incident is not "404". It is "token <code>ghp_</code> authenticates as <code>ci-bot</code>, scopes <code>public_repo</code>, repository not readable" &mdash; at which point nobody checks the spelling, because the answer is on the screen. Where every signal is healthy and the 404 persists, say that plainly too: an account with no grant and a repository that was genuinely deleted are the same response, and pretending otherwise is worse than admitting it.</p>"""},
],
"verify": """<p>Re-run the script against the same repository after the repair. The verdict should be <code>visible</code>, and the login it reports should be the account you meant to use.</p>
<pre><code class="language-bash">python3 github_404_triage.py acme/project-nightingale
# visible          acme/project-nightingale  authenticated as ci-bot; the repository answered 200</code></pre>""",
"code_intro": "Three GET requests at most and no writes at all &mdash; a read-only token is enough, and is what you should give it. The two pure functions are the prefix reader and the verdict, because the whole value of this note is the branching: five identical 404s that mean five different things, laid out somewhere you can read the rules rather than infer them from a stack trace.",
"py_file": "github_404_triage.py",
"py": '''"""Tell apart the several different failures GitHub hides behind one 404.

Read only. GET requests and nothing else: a token with read access is enough.
The repair is printed, never performed, because this script holds a credential
that can reach private repositories.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_404_triage")

API = "https://api.github.com"
UA = "github-404-triage/1.0"

# Longest prefixes first so a future prefix that extends an existing one cannot
# be swallowed by its shorter neighbour.
PREFIXES = (
    ("github_pat_", "fine-grained PAT"),
    ("ghp_", "classic PAT"),
    ("gho_", "OAuth user token"),
    ("ghu_", "App user-to-server token"),
    ("ghs_", "App installation token"),
    ("ghr_", "App refresh token"),
)


def token_kind(token):
    """Name the credential from its prefix. Pure, and it never leaves the machine.

    Which check is worth making depends entirely on what kind of token this is:
    scopes are meaningless for an App installation token, and the installation
    question is meaningless for a classic PAT. A prefix comparison answers that
    for free, before a single request is spent.
    """
    value = (token or "").strip()
    for prefix, name in PREFIXES:
        if value.startswith(prefix):
            return name
    return "unknown"


def scope_list(header_value):
    """Read x-oauth-scopes into a list, keeping absent and empty apart.

    A classic token with nothing ticked sends the header with an empty value.
    A fine-grained token or an App token does not send it at all. Collapsing both
    to an empty list loses the one signal that decides which repair to print, so
    absence is None and emptiness is [].
    """
    if header_value is None:
        return None
    return [s.strip() for s in header_value.split(",") if s.strip()]


def verdict(probe):
    """Classify one 404. Pure, so the rules are readable rather than inferred.

    `probe` carries what the reads found: repo_status, authenticated, scopes
    (None when the token does not use them), token_kind, and in_installation
    (None when the question does not apply). Returns (state, detail).
    """
    status = probe.get("repo_status")

    if not probe.get("authenticated"):
        return ("bad-credentials",
                "GET /user did not authenticate. Every private repository 404s "
                "for a dead token while every public one answers 200, which is "
                "why this looks like a per-repository permission problem.")

    if status == 200:
        return ("visible", "the repository answered 200")
    if status == 403:
        return ("plain-403",
                "403 rather than 404, which is the honest one: rate limit, org "
                "IP allow list, or a policy that blocks this app. Read the "
                "message body and x-ratelimit-remaining before assuming access.")
    if status != 404:
        return ("unexpected", "HTTP %s is not the masked case" % (status,))

    kind = probe.get("token_kind")
    if kind == "App installation token":
        inside = probe.get("in_installation")
        if inside is True:
            return ("metadata-permission",
                    "the repository is inside the installation, so it exists and "
                    "you reach it. Every repository endpoint requires "
                    "Metadata: Read; without it the repository itself 404s.")
        if inside is False:
            return ("not-in-installation",
                    "the installation does not include this repository. "
                    "repository_selection is 'selected' and this one was never "
                    "ticked, so it is outside the token's world entirely.")
        return ("installation-unknown",
                "GET /installation/repositories could not be read, so the "
                "installation question is open. Retry with the installation "
                "token the failing call actually uses.")

    scopes = probe.get("scopes")
    if scopes is None:
        return ("repository-not-granted",
                "no x-oauth-scopes header, so this is a fine-grained token. "
                "Those grant repositories one at a time: this one is not in the "
                "token's repository list, or Metadata: Read is not on it.")
    if "repo" not in scopes:
        return ("missing-scope",
                "the token carries %s and not 'repo'. Public repositories answer "
                "and private ones return exactly this 404."
                % (", ".join(scopes) or "no scopes at all",))

    return ("no-access-or-gone",
            "the token authenticates and carries 'repo', so the scope is not the "
            "problem. What is left is an account that was never granted access, "
            "or a repository that is genuinely gone. GitHub returns the same 404 "
            "for both on purpose and no header separates them.")


def get(session, url, **params):
    return session.get(url, params=params, timeout=30)


def installation_repos(session, api, limit=2000):
    """Every repository inside this installation, or None if it cannot be read.

    Paged rather than trusted from one page: total_count is the size of the
    installation, and the repositories array is one page of it.
    """
    out = []
    page = 1
    while len(out) < limit:
        r = get(session, api + "/installation/repositories", per_page=100, page=page)
        if r.status_code != 200:
            return None
        items = r.json().get("repositories", [])
        out.extend(items)
        if len(items) < 100:
            break
        page += 1
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("repo", help="owner/name of the repository that returns 404")
    ap.add_argument("--api", default=API,
                    help="API host, for GitHub Enterprise Server")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (a read-only token is enough)")
        return 2
    if "/" not in args.repo:
        log.error("pass the repository as owner/name")
        return 2
    owner, name = args.repo.split("/", 1)

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        # GitHub rejects requests with no User-Agent outright, which is its own
        # confusing 403 and not the one this script is about.
        "User-Agent": UA,
    })

    kind = token_kind(token)
    me = get(session, args.api + "/user")
    probe = {
        "token_kind": kind,
        "authenticated": me.status_code == 200,
        "scopes": scope_list(me.headers.get("x-oauth-scopes")),
        "in_installation": None,
    }
    login = me.json().get("login") if probe["authenticated"] else None

    repo = get(session, "%s/repos/%s/%s" % (args.api, owner, name))
    probe["repo_status"] = repo.status_code

    if kind == "App installation token" and repo.status_code == 404:
        repos = installation_repos(session, args.api)
        if repos is not None:
            full = args.repo.lower()
            probe["in_installation"] = any(
                str(r.get("full_name") or "").lower() == full for r in repos)

    state, detail = verdict(probe)
    line = "%-22s %s  %s" % (state, args.repo, detail)
    if state == "visible":
        log.info("%s (authenticated as %s)", line, login)
        return 0

    log.warning(line)
    log.warning("  token: %s, login: %s, scopes: %s", kind, login,
                "absent" if probe["scopes"] is None else (probe["scopes"] or "none"))
    repairs = {
        "bad-credentials": "re-mint the token and assert GET /user returns the "
                           "expected login at startup",
        "missing-scope": "re-create the classic token with the 'repo' scope, or "
                         "move to a fine-grained token listing this repository",
        "repository-not-granted": "add this repository to the fine-grained "
                                  "token's repository access, with Metadata: Read",
        "not-in-installation": "add the repository to the App installation, or "
                               "switch the installation to All repositories",
        "metadata-permission": "add Metadata: Read to the App and have each "
                               "installation accept the updated permissions",
        "no-access-or-gone": "grant %s access to the repository, or confirm with "
                             "somebody who can see it that it still exists" % (login,),
    }
    if state in repairs:
        log.warning("  repair: %s", repairs[state])
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-404-triage.mjs",
"js": '''/**
 * Tell apart the several different failures GitHub hides behind one 404.
 *
 * Read only. GET requests and nothing else: a token with read access is enough.
 * The repair is printed, never performed.
 */
const API = 'https://api.github.com';
const UA = 'github-404-triage/1.0';

// Longest prefixes first so a future prefix that extends an existing one cannot
// be swallowed by its shorter neighbour.
const PREFIXES = [
  ['github_pat_', 'fine-grained PAT'],
  ['ghp_', 'classic PAT'],
  ['gho_', 'OAuth user token'],
  ['ghu_', 'App user-to-server token'],
  ['ghs_', 'App installation token'],
  ['ghr_', 'App refresh token'],
];

/**
 * Name the credential from its prefix. Pure, and it never leaves the machine.
 */
export function tokenKind(token) {
  const value = String(token ?? '').trim();
  for (const [prefix, name] of PREFIXES) {
    if (value.startsWith(prefix)) return name;
  }
  return 'unknown';
}

/**
 * Read x-oauth-scopes into an array, keeping absent (null) and empty ([]) apart.
 * A classic token with nothing ticked sends an empty header; a fine-grained or
 * App token sends none at all, and those need opposite repairs.
 */
export function scopeList(headerValue) {
  if (headerValue === null || headerValue === undefined) return null;
  return headerValue.split(',').map((s) => s.trim()).filter(Boolean);
}

/**
 * Classify one 404. Pure, so the rules are readable rather than inferred.
 * Returns [state, detail].
 */
export function verdict(probe) {
  const status = probe.repo_status;

  if (!probe.authenticated) {
    return ['bad-credentials',
      'GET /user did not authenticate. Every private repository 404s for a dead ' +
      'token while every public one answers 200, which is why this looks like a ' +
      'per-repository permission problem.'];
  }

  if (status === 200) return ['visible', 'the repository answered 200'];
  if (status === 403) {
    return ['plain-403',
      '403 rather than 404, which is the honest one: rate limit, org IP allow ' +
      'list, or a policy that blocks this app. Read the message body and ' +
      'x-ratelimit-remaining before assuming access.'];
  }
  if (status !== 404) return ['unexpected', `HTTP ${status} is not the masked case`];

  if (probe.token_kind === 'App installation token') {
    const inside = probe.in_installation;
    if (inside === true) {
      return ['metadata-permission',
        'the repository is inside the installation, so it exists and you reach ' +
        'it. Every repository endpoint requires Metadata: Read; without it the ' +
        'repository itself 404s.'];
    }
    if (inside === false) {
      return ['not-in-installation',
        "the installation does not include this repository. repository_selection " +
        "is 'selected' and this one was never ticked, so it is outside the " +
        "token's world entirely."];
    }
    return ['installation-unknown',
      'GET /installation/repositories could not be read, so the installation ' +
      'question is open. Retry with the installation token the failing call ' +
      'actually uses.'];
  }

  const scopes = probe.scopes;
  if (scopes === null || scopes === undefined) {
    return ['repository-not-granted',
      'no x-oauth-scopes header, so this is a fine-grained token. Those grant ' +
      'repositories one at a time: this one is not in the token\\'s repository ' +
      'list, or Metadata: Read is not on it.'];
  }
  if (!scopes.includes('repo')) {
    return ['missing-scope',
      `the token carries ${scopes.join(', ') || 'no scopes at all'} and not ` +
      "'repo'. Public repositories answer and private ones return exactly this 404."];
  }

  return ['no-access-or-gone',
    "the token authenticates and carries 'repo', so the scope is not the " +
    'problem. What is left is an account that was never granted access, or a ' +
    'repository that is genuinely gone. GitHub returns the same 404 for both on ' +
    'purpose and no header separates them.'];
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    // GitHub rejects requests with no User-Agent outright, which is its own
    // confusing 403 and not the one this script is about.
    'User-Agent': UA,
  };
}

async function get(token, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  return fetch(u, { headers: headers(token) });
}

export async function installationRepos(token, api, limit = 2000) {
  const out = [];
  let page = 1;
  while (out.length < limit) {
    const res = await get(token, `${api}/installation/repositories`,
                          { per_page: 100, page });
    if (res.status !== 200) return null;
    const items = (await res.json()).repositories ?? [];
    out.push(...items);
    if (items.length < 100) break;
    page += 1;
  }
  return out;
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (a read-only token is enough)');
    process.exitCode = 2;
    return;
  }
  const target = process.argv[2];
  if (!target || !target.includes('/')) {
    console.error('pass the repository as owner/name');
    process.exitCode = 2;
    return;
  }

  const kind = tokenKind(token);
  const me = await get(token, `${API}/user`);
  const probe = {
    token_kind: kind,
    authenticated: me.status === 200,
    scopes: scopeList(me.headers.get('x-oauth-scopes')),
    in_installation: null,
  };
  const login = probe.authenticated ? (await me.json()).login : null;

  const repo = await get(token, `${API}/repos/${target}`);
  probe.repo_status = repo.status;

  if (kind === 'App installation token' && repo.status === 404) {
    const repos = await installationRepos(token, API);
    if (repos !== null) {
      const full = target.toLowerCase();
      probe.in_installation = repos.some(
        (r) => String(r.full_name ?? '').toLowerCase() === full);
    }
  }

  const [state, detail] = verdict(probe);
  const line = `${state.padEnd(22)} ${target}  ${detail}`;
  if (state === 'visible') {
    console.log(`${line} (authenticated as ${login})`);
    return;
  }

  console.warn(line);
  console.warn(`  token: ${kind}, login: ${login}, scopes: ` +
    `${probe.scopes === null ? 'absent' : (probe.scopes.join(', ') || 'none')}`);
  const repairs = {
    'bad-credentials': 're-mint the token and assert GET /user returns the ' +
      'expected login at startup',
    'missing-scope': "re-create the classic token with the 'repo' scope, or move " +
      'to a fine-grained token listing this repository',
    'repository-not-granted': "add this repository to the fine-grained token's " +
      'repository access, with Metadata: Read',
    'not-in-installation': 'add the repository to the App installation, or switch ' +
      'the installation to All repositories',
    'metadata-permission': 'add Metadata: Read to the App and have each ' +
      'installation accept the updated permissions',
    'no-access-or-gone': `grant ${login} access to the repository, or confirm ` +
      'with somebody who can see it that it still exists',
  };
  if (repairs[state]) console.warn(`  repair: ${repairs[state]}`);
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing token, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two rules carry this note and both are easy to get wrong. An absent <code>x-oauth-scopes</code> header is not an empty one: absent means a fine-grained or App token, empty means a classic token with nothing ticked, and they lead to different pages of GitHub's settings. And the last state has to stay honest &mdash; when the token is alive, carries <code>repo</code>, and the repository still 404s, the script must say that no-grant and genuinely-deleted are the same response rather than pick the friendlier one.",
"test_py_file": "test_github_404_triage.py",
"test_py": '''from github_404_triage import scope_list, token_kind, verdict


def probe(**kw):
    base = {"repo_status": 404, "authenticated": True, "scopes": ["repo"],
            "token_kind": "classic PAT", "in_installation": None}
    base.update(kw)
    return base


def test_prefixes_name_the_credential_without_sending_it():
    assert token_kind("ghp_abc123") == "classic PAT"
    assert token_kind("github_pat_11ABCDE") == "fine-grained PAT"
    assert token_kind("ghs_installation") == "App installation token"
    assert token_kind("  gho_padded  ") == "OAuth user token"
    assert token_kind("v1.0123deadbeef") == "unknown"
    assert token_kind(None) == "unknown"


def test_absent_scopes_header_is_not_an_empty_one():
    # The whole branch between "fine-grained token" and "classic token with
    # nothing ticked" hangs on this distinction.
    assert scope_list(None) is None
    assert scope_list("") == []
    assert scope_list("repo, read:org") == ["repo", "read:org"]


def test_dead_token_beats_every_other_reading():
    state, detail = verdict(probe(authenticated=False, scopes=None))
    assert state == "bad-credentials"
    assert "public" in detail


def test_a_repository_that_answers_is_visible():
    assert verdict(probe(repo_status=200))[0] == "visible"


def test_a_real_403_is_reported_as_the_honest_one():
    state, detail = verdict(probe(repo_status=403))
    assert state == "plain-403"
    assert "rate limit" in detail


def test_classic_token_without_repo_scope_names_the_scope():
    state, detail = verdict(probe(scopes=["public_repo"]))
    assert state == "missing-scope"
    assert "public_repo" in detail


def test_no_scopes_at_all_is_still_a_classic_token():
    state, detail = verdict(probe(scopes=[]))
    assert state == "missing-scope"
    assert "no scopes at all" in detail


def test_missing_scope_header_means_a_fine_grained_token():
    state, _ = verdict(probe(scopes=None, token_kind="fine-grained PAT"))
    assert state == "repository-not-granted"


def test_app_token_outside_the_installation_is_its_own_state():
    state, _ = verdict(probe(token_kind="App installation token",
                             scopes=None, in_installation=False))
    assert state == "not-in-installation"


def test_app_token_inside_the_installation_points_at_metadata():
    state, detail = verdict(probe(token_kind="App installation token",
                                  scopes=None, in_installation=True))
    assert state == "metadata-permission"
    assert "Metadata" in detail


def test_the_indistinguishable_case_stays_indistinguishable():
    # Alive, scoped, still 404. The script must not guess which of the two it is.
    state, detail = verdict(probe())
    assert state == "no-access-or-gone"
    assert "same 404" in detail
''',
"test_js_file": "github-404-triage.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { scopeList, tokenKind, verdict } from './github-404-triage.mjs';

const probe = (over = {}) => ({
  repo_status: 404, authenticated: true, scopes: ['repo'],
  token_kind: 'classic PAT', in_installation: null, ...over,
});

test('prefixes name the credential without sending it', () => {
  assert.equal(tokenKind('ghp_abc123'), 'classic PAT');
  assert.equal(tokenKind('github_pat_11ABCDE'), 'fine-grained PAT');
  assert.equal(tokenKind('ghs_installation'), 'App installation token');
  assert.equal(tokenKind('  gho_padded  '), 'OAuth user token');
  assert.equal(tokenKind('v1.0123deadbeef'), 'unknown');
  assert.equal(tokenKind(null), 'unknown');
});

test('an absent scopes header is not an empty one', () => {
  assert.equal(scopeList(null), null);
  assert.deepEqual(scopeList(''), []);
  assert.deepEqual(scopeList('repo, read:org'), ['repo', 'read:org']);
});

test('dead token beats every other reading', () => {
  const [state, detail] = verdict(probe({ authenticated: false, scopes: null }));
  assert.equal(state, 'bad-credentials');
  assert.match(detail, /public/);
});

test('a repository that answers is visible', () => {
  assert.equal(verdict(probe({ repo_status: 200 }))[0], 'visible');
});

test('a real 403 is reported as the honest one', () => {
  const [state, detail] = verdict(probe({ repo_status: 403 }));
  assert.equal(state, 'plain-403');
  assert.match(detail, /rate limit/);
});

test('classic token without repo scope names the scope', () => {
  const [state, detail] = verdict(probe({ scopes: ['public_repo'] }));
  assert.equal(state, 'missing-scope');
  assert.match(detail, /public_repo/);
});

test('no scopes at all is still a classic token', () => {
  const [state, detail] = verdict(probe({ scopes: [] }));
  assert.equal(state, 'missing-scope');
  assert.match(detail, /no scopes at all/);
});

test('missing scope header means a fine-grained token', () => {
  assert.equal(
    verdict(probe({ scopes: null, token_kind: 'fine-grained PAT' }))[0],
    'repository-not-granted');
});

test('app token outside the installation is its own state', () => {
  assert.equal(
    verdict(probe({ token_kind: 'App installation token', scopes: null,
                    in_installation: false }))[0],
    'not-in-installation');
});

test('app token inside the installation points at metadata', () => {
  const [state, detail] = verdict(probe({
    token_kind: 'App installation token', scopes: null, in_installation: true }));
  assert.equal(state, 'metadata-permission');
  assert.match(detail, /Metadata/);
});

test('the indistinguishable case stays indistinguishable', () => {
  const [state, detail] = verdict(probe());
  assert.equal(state, 'no-access-or-gone');
  assert.match(detail, /same 404/);
});
''',
"faq": [
 ("Why does GitHub return 404 instead of 403 for a private repository?",
  "To avoid confirming that the repository exists. A 403 would tell an unauthorized caller that a particular private repository is real, which for a private repository is itself the information being protected. The API therefore answers identically whether the resource is absent or merely out of reach."),
 ("How do I tell a missing scope from a missing repository?",
  "Read x-oauth-scopes on any authenticated response. If a classic token carries public_repo and not repo, private repositories will 404 for it no matter how correct the name is. If the header is absent entirely the token is fine-grained or an App installation token, neither of which uses scopes, and the question becomes which repositories that credential was granted."),
 ("The token works for some repositories and 404s for others. Is that not proof it is a permissions problem?",
  "Not on its own. An expired or revoked token produces exactly that pattern: public repositories still answer 200 because anonymous access covers them, and every private one 404s. Check GET /user first; a 401 there means the per-repository theory is a coincidence."),
 ("My GitHub App is installed on the organization but the repository still 404s. Why?",
  "Two different causes, and GET /installation/repositories separates them. If the repository is absent from that list, the installation uses selected repositories and this one was never added. If it is present, the App is missing Metadata: Read, which every repository endpoint requires and which is easy to leave off when picking permissions."),
 ("Can the script ever tell me the repository was deleted?",
  "No, and neither can any other read-only caller. Once the token is alive and carries the right scope, no-grant and genuinely-deleted are the same 404 with the same body and the same headers. The script says so rather than picking one, because a confident wrong answer here costs more than an honest ambiguous one."),
],
"related": [
 ("/github/app-permission-missing/", "Resource not accessible by integration"),
 ("/github/installation-repository-selection-partial/", "An installation that covers only some repositories"),
 ("/github/saml-partial-results/", "Org lists that silently omit SSO-enforced orgs"),
],
"citations": [CITE_TROUBLESHOOT, CITE_AUTHN, CITE_PATS, CITE_APP_PERMS],
},


{
"slug": "saml-partial-results",
"title": "Org lists silently omit SSO-enforced organizations",
"description": "GET /user/orgs returns 200 and leaves out the orgs your token is not SSO-authorized for, mentioning the omission only in an X-GitHub-SSO header.",
"h1": "org lists silently omit SSO-enforced organizations",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["x-github-sso partial-results", "github saml sso api",
             "github user orgs missing", "github token not authorized for saml",
             "github sso enforced organization api"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The user belongs to six organizations. <code>GET /user/orgs</code> returns four. Status <code>200</code>, valid JSON, no <code>errors</code> array, nothing in the body that hints anything is absent. The two organizations that enforce SAML single sign-on for a token that was never authorized against them are simply not in the list, and the only place GitHub mentions it is a response header called <code>X-GitHub-SSO</code>.",
"short_answer": """<p>Read the <code>x-github-sso</code> response header on every cross-organization list, on every page, including the ones that returned 200. Its partial form looks like <code>X-GitHub-SSO: partial-results; organizations=21955855,20582480</code> and names the database IDs of the organizations that were withheld.</p>
<p>The presence of that header on a successful response <em>is</em> the finding. Resolve each ID with <code>GET /organizations/{id}</code> where you have access, then either authorize the token for those organizations or run per-organization queries with credentials scoped to each.</p>""",
"problem": """<p>An inventory script is trusted in proportion to how boring it is, and this one is very boring: it lists organizations, lists their repositories, and writes a row per repository. It has run nightly for two years. It has never errored. It has also never mentioned the two organizations that hold the regulated workloads, because those enforce SAML and the token was authorized for the other four.</p>
<p>What makes this worse than an outright failure is that partial results propagate. The inventory feeds a compliance report, the compliance report feeds a dashboard, and every consumer downstream treats a 200 as a complete answer, because a 200 <em>is</em> a complete answer everywhere else. Nobody is looking for the gap, and the gap has no shape: the missing organizations are not returned as empty, or as errors, or as anything at all.</p>""",
"why": """<p><strong>The failure is per organization, and the request spans several.</strong> A SAML-enforcing organization requires the token to be explicitly authorized against its identity provider. On a single-organization endpoint that produces a clean 403 with an authorization URL. On a cross-organization listing, failing the whole request because one of six organizations is unauthorized would break the endpoint for everyone, so GitHub returns what it may and flags the rest.</p>
<p><strong>The flag is in a header, and headers are where signals go to die.</strong> Most HTTP clients hand you the parsed body and put the headers somewhere you have to ask for. Every SDK that returns a plain array of organizations from this call has already discarded the header before your code sees it, which is why the omission survives so long.</p>
<p><strong>The header names IDs, not logins.</strong> <code>organizations=21955855,20582480</code> is not something anyone recognises. Turning it into names costs another request per ID, and where the token cannot see that organization at all, even that lookup can fail &mdash; so the honest report sometimes contains a number and the sentence "this ID was withheld and could not be resolved".</p>
<p><strong>Authorization lapses on a schedule you do not control.</strong> A token authorized today stops being authorized when the SAML session policy says so, or when an administrator revokes it, or when the identity provider configuration changes. The script that worked last month starts returning fewer organizations this month with no code change and no error.</p>""",
"steps": [
 {"h": "Call the listing and keep the response object, not just the body",
  "body": """<p><code>GET /user/orgs?per_page=100</code>. The instinct is to return <code>response.json()</code> and move on; that discards the only evidence there is. Whatever wrapper you use, make sure the headers survive as far as the code that decides whether the answer is complete.</p>"""},
 {"h": "Read x-github-sso on every page, not just the first",
  "body": """<p>The header is attached per response. A three-page listing is three responses and the flag can appear on any of them, so a check that only inspects page one is a check that works until the organization list grows past a hundred entries.</p>"""},
 {"h": "Parse the two forms apart",
  "body": """<p><code>partial-results; organizations=&lt;ids&gt;</code> arrives on a 200 and means the body is incomplete. <code>required; url=&lt;authorization url&gt;</code> arrives on a 403 and means the request failed outright, which is the loud, easy version. Anything else you cannot parse must be treated as suspect rather than folded into "no header" &mdash; a value nobody understood is still a value GitHub sent.</p>"""},
 {"h": "Resolve the withheld IDs into names",
  "body": """<p><code>GET /organizations/{id}</code> turns each database ID into a login you can put in a report. Expect some of them to fail: the token that could not list the organization may not be able to read it either, and a report that says <code>21955855</code> and admits it could not name it is more useful than one that quietly drops the row.</p>"""},
 {"h": "Make partial an error condition in anything that inventories",
  "body": """<p>For a dashboard, a partial list is a degraded view. For an audit, an inventory or a security report, a partial list is a wrong answer wearing a 200. Exit non-zero, name the withheld IDs, and authorize the token for those organizations &mdash; or accept the partition and run a separately scoped credential per organization, which is the honest architecture when the organizations are genuinely under different administration.</p>"""},
],
"verify": """<p>Re-run after authorizing the token. The header should be absent, and the organization count should match what the user sees on their profile.</p>
<pre><code class="language-bash">python3 github_sso_partial_results.py
# complete         6 organization(s), no partial-results header on any page</code></pre>""",
"code_intro": "One paginated GET, read with a token that needs nothing beyond <code>read:org</code>. The two pure functions are the header parser and the verdict, and they carry the whole note: parsing decides what GitHub said, and the verdict decides what to do about a header that was sent but not understood &mdash; which is the case that turns a silent omission into a clean bill of health if you get it wrong.",
"py_file": "github_sso_partial_results.py",
"py": '''"""Find organizations that GitHub withheld from a 200 because of SAML SSO.

Read only. GET requests and nothing else: read:org is enough. The repair is
printed, never performed, because this script holds a credential that spans
several organizations.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_sso_partial_results")

API = "https://api.github.com"
UA = "github-sso-partial-results/1.0"


def parse_sso(value):
    """Parse an X-GitHub-SSO header value. Pure, so both forms are testable.

    Two shapes exist. On a 200 the partial form names the organizations that were
    withheld from the body:

        partial-results; organizations=21955855,20582480

    On a 403 the required form carries the URL that authorizes the token:

        required; url=https://github.com/orgs/acme/sso?authorization_request=...

    A value that matches neither is reported as "unknown" rather than folded into
    "none". A header nobody parsed is still a header GitHub sent, and reading it
    as absence is exactly how a partial answer becomes a clean bill of health.
    """
    raw = (value or "").strip()
    if not raw:
        return {"kind": "none", "organizations": [], "url": None}

    parts = [p.strip() for p in raw.split(";") if p.strip()]
    kind = parts[0].lower()
    orgs, url = [], None
    for part in parts[1:]:
        name, sep, val = part.partition("=")
        if not sep:
            continue
        name = name.strip().lower()
        if name == "organizations":
            orgs = [o.strip() for o in val.split(",") if o.strip()]
        elif name == "url":
            url = val.strip()

    if kind not in ("partial-results", "required"):
        kind = "unknown"
    return {"kind": kind, "organizations": orgs, "url": url}


def verdict(status, sso, listed):
    """Decide what one response means. Pure. Returns (state, detail).

    The header outranks the status code: a 200 carrying partial-results is a
    failure and a 403 carrying required is at least an honest one.
    """
    kind = sso.get("kind")

    if kind == "partial-results":
        hidden = sso.get("organizations") or []
        return ("partial",
                "%d organization(s) in the body and %d withheld (%s). The status "
                "is 200 and the JSON is valid; the answer is not."
                % (listed, len(hidden), ", ".join(hidden) or "unnamed"))

    if kind == "required":
        return ("authorization-required",
                "the token is not SSO-authorized and GitHub said so out loud. "
                "Authorize it at %s" % (sso.get("url") or "the org's SSO page",))

    if kind == "unknown":
        return ("unreadable",
                "an X-GitHub-SSO header was sent and this parser did not "
                "understand it. Treat that as partial, never as clean, and read "
                "the raw value before trusting the list.")

    if status == 403:
        return ("forbidden",
                "403 with no X-GitHub-SSO header, so this is not SSO. Look at "
                "org OAuth app restrictions, an IP allow list, or a missing "
                "read:org scope instead.")
    if status != 200:
        return ("unexpected", "HTTP %s" % (status,))

    return ("complete", "%d organization(s), no partial-results header" % (listed,))


def get(session, url, **params):
    return session.get(url, params=params, timeout=30)


def list_orgs(session, api):
    """Page /user/orgs, returning (organizations, worst response seen).

    The header is attached per response, so every page is inspected. The first
    page carrying a partial-results header wins, because one hole makes the
    whole list partial.
    """
    orgs = []
    finding = {"status": 200, "sso": {"kind": "none", "organizations": [], "url": None}}
    page = 1
    while True:
        r = get(session, api + "/user/orgs", per_page=100, page=page)
        sso = parse_sso(r.headers.get("x-github-sso"))
        if sso["kind"] != "none" and finding["sso"]["kind"] == "none":
            finding = {"status": r.status_code, "sso": sso}
        if r.status_code != 200:
            finding["status"] = r.status_code
            break
        items = r.json()
        orgs.extend(items)
        if len(items) < 100:
            break
        page += 1
    return orgs, finding


def resolve(session, api, org_id):
    """Turn a withheld organization ID into a login, or admit it cannot."""
    r = get(session, "%s/organizations/%s" % (api, org_id))
    if r.status_code != 200:
        return None
    return r.json().get("login")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--api", default=API,
                    help="API host, for GitHub Enterprise Server")
    ap.add_argument("--resolve-ids", action="store_true",
                    help="one extra GET per withheld organization, to name it")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (read:org is enough)")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    orgs, finding = list_orgs(session, args.api)
    state, detail = verdict(finding["status"], finding["sso"], len(orgs))

    if state == "complete":
        log.info("%-22s %s", state, detail)
        return 0

    log.warning("%-22s %s", state, detail)
    log.warning("  visible: %s",
                ", ".join(str(o.get("login")) for o in orgs) or "none")

    if args.resolve_ids and finding["sso"]["kind"] == "partial-results":
        for org_id in finding["sso"]["organizations"]:
            name = resolve(session, args.api, org_id)
            log.warning("  withheld: %s (%s)", org_id,
                        name or "could not be resolved with this token either")

    log.warning("  repair: authorize this token for the withheld organizations "
                "in your GitHub settings under SSO, or run one credential per "
                "organization and stop asking a single token a question it "
                "cannot answer completely.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-sso-partial-results.mjs",
"js": '''/**
 * Find organizations that GitHub withheld from a 200 because of SAML SSO.
 *
 * Read only. GET requests and nothing else: read:org is enough. The repair is
 * printed, never performed.
 */
const API = 'https://api.github.com';
const UA = 'github-sso-partial-results/1.0';

/**
 * Parse an X-GitHub-SSO header value. Pure, so both forms are testable.
 *
 * On a 200:  partial-results; organizations=21955855,20582480
 * On a 403:  required; url=https://github.com/orgs/acme/sso?authorization_request=...
 *
 * Anything else is "unknown" rather than "none": a header nobody parsed is still
 * a header GitHub sent, and reading it as absence is how a partial answer becomes
 * a clean bill of health.
 */
export function parseSso(value) {
  const raw = String(value ?? '').trim();
  if (!raw) return { kind: 'none', organizations: [], url: null };

  const parts = raw.split(';').map((p) => p.trim()).filter(Boolean);
  let kind = (parts[0] ?? '').toLowerCase();
  let organizations = [];
  let url = null;
  for (const part of parts.slice(1)) {
    const at = part.indexOf('=');
    if (at < 0) continue;
    const name = part.slice(0, at).trim().toLowerCase();
    const val = part.slice(at + 1).trim();
    if (name === 'organizations') {
      organizations = val.split(',').map((o) => o.trim()).filter(Boolean);
    } else if (name === 'url') {
      url = val;
    }
  }
  if (kind !== 'partial-results' && kind !== 'required') kind = 'unknown';
  return { kind, organizations, url };
}

/**
 * Decide what one response means. Pure. Returns [state, detail]. The header
 * outranks the status code.
 */
export function verdict(status, sso, listed) {
  const kind = sso.kind;

  if (kind === 'partial-results') {
    const hidden = sso.organizations ?? [];
    return ['partial',
      `${listed} organization(s) in the body and ${hidden.length} withheld ` +
      `(${hidden.join(', ') || 'unnamed'}). The status is 200 and the JSON is ` +
      'valid; the answer is not.'];
  }

  if (kind === 'required') {
    return ['authorization-required',
      'the token is not SSO-authorized and GitHub said so out loud. Authorize ' +
      `it at ${sso.url ?? "the org's SSO page"}`];
  }

  if (kind === 'unknown') {
    return ['unreadable',
      'an X-GitHub-SSO header was sent and this parser did not understand it. ' +
      'Treat that as partial, never as clean, and read the raw value before ' +
      'trusting the list.'];
  }

  if (status === 403) {
    return ['forbidden',
      '403 with no X-GitHub-SSO header, so this is not SSO. Look at org OAuth ' +
      'app restrictions, an IP allow list, or a missing read:org scope instead.'];
  }
  if (status !== 200) return ['unexpected', `HTTP ${status}`];

  return ['complete', `${listed} organization(s), no partial-results header`];
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function get(token, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  return fetch(u, { headers: headers(token) });
}

export async function listOrgs(token, api = API) {
  const orgs = [];
  let finding = { status: 200, sso: { kind: 'none', organizations: [], url: null } };
  let page = 1;
  for (;;) {
    const res = await get(token, `${api}/user/orgs`, { per_page: 100, page });
    const sso = parseSso(res.headers.get('x-github-sso'));
    if (sso.kind !== 'none' && finding.sso.kind === 'none') {
      finding = { status: res.status, sso };
    }
    if (res.status !== 200) { finding.status = res.status; break; }
    const items = await res.json();
    orgs.push(...items);
    if (items.length < 100) break;
    page += 1;
  }
  return { orgs, finding };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (read:org is enough)');
    process.exitCode = 2;
    return;
  }

  const { orgs, finding } = await listOrgs(token);
  const [state, detail] = verdict(finding.status, finding.sso, orgs.length);

  if (state === 'complete') {
    console.log(`${state.padEnd(22)} ${detail}`);
    return;
  }

  console.warn(`${state.padEnd(22)} ${detail}`);
  console.warn(`  visible: ${orgs.map((o) => o.login).join(', ') || 'none'}`);

  if (process.argv.includes('--resolve-ids') &&
      finding.sso.kind === 'partial-results') {
    for (const id of finding.sso.organizations) {
      const res = await get(token, `${API}/organizations/${id}`);
      const name = res.status === 200 ? (await res.json()).login : null;
      console.warn(`  withheld: ${id} ` +
        `(${name ?? 'could not be resolved with this token either'})`);
    }
  }

  console.warn('  repair: authorize this token for the withheld organizations in ' +
               'your GitHub settings under SSO, or run one credential per ' +
               'organization and stop asking a single token a question it cannot ' +
               'answer completely.');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing token, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "The test that matters is the one for a header the parser did not recognise. Every other case is arithmetic; that one is a judgement, and the wrong judgement is silent. If an unfamiliar <code>X-GitHub-SSO</code> value falls through to <code>complete</code>, the script reports a clean inventory on exactly the day GitHub changed the header, which is the failure this whole note is about happening a second time inside the tool built to catch it.",
"test_py_file": "test_github_sso_partial_results.py",
"test_py": '''from github_sso_partial_results import parse_sso, verdict


def test_partial_form_yields_the_withheld_ids():
    sso = parse_sso("partial-results; organizations=21955855,20582480")
    assert sso["kind"] == "partial-results"
    assert sso["organizations"] == ["21955855", "20582480"]
    assert sso["url"] is None


def test_required_form_yields_the_authorization_url():
    sso = parse_sso("required; url=https://github.com/orgs/acme/sso?x=1")
    assert sso["kind"] == "required"
    assert sso["url"] == "https://github.com/orgs/acme/sso?x=1"


def test_absent_and_blank_headers_are_the_same_nothing():
    assert parse_sso(None)["kind"] == "none"
    assert parse_sso("")["kind"] == "none"
    assert parse_sso("   ")["kind"] == "none"


def test_an_unrecognised_value_is_never_read_as_absence():
    # The whole point. A header GitHub sent that this parser did not understand
    # must not fall through to "clean".
    sso = parse_sso("some-future-directive; organizations=1")
    assert sso["kind"] == "unknown"
    assert verdict(200, sso, 4)[0] == "unreadable"


def test_a_200_with_partial_results_is_a_failure():
    sso = parse_sso("partial-results; organizations=21955855,20582480")
    state, detail = verdict(200, sso, 4)
    assert state == "partial"
    assert "4 organization(s)" in detail
    assert "2 withheld" in detail
    assert "21955855" in detail


def test_a_403_with_the_required_form_is_the_loud_version():
    sso = parse_sso("required; url=https://github.com/orgs/acme/sso")
    state, detail = verdict(403, sso, 0)
    assert state == "authorization-required"
    assert "https://github.com/orgs/acme/sso" in detail


def test_a_403_without_the_header_is_not_an_sso_problem():
    state, detail = verdict(403, parse_sso(None), 0)
    assert state == "forbidden"
    assert "read:org" in detail


def test_a_clean_200_is_complete():
    state, detail = verdict(200, parse_sso(None), 6)
    assert state == "complete"
    assert "6 organization(s)" in detail


def test_the_header_outranks_the_status_code():
    # A partial-results header on a 200 is worse news than a 403, so it must not
    # be reachable only through the non-200 branch.
    sso = parse_sso("partial-results; organizations=99")
    assert verdict(200, sso, 1)[0] == "partial"
    assert verdict(500, sso, 1)[0] == "partial"
''',
"test_js_file": "github-sso-partial-results.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { parseSso, verdict } from './github-sso-partial-results.mjs';

test('partial form yields the withheld ids', () => {
  const sso = parseSso('partial-results; organizations=21955855,20582480');
  assert.equal(sso.kind, 'partial-results');
  assert.deepEqual(sso.organizations, ['21955855', '20582480']);
  assert.equal(sso.url, null);
});

test('required form yields the authorization url', () => {
  const sso = parseSso('required; url=https://github.com/orgs/acme/sso?x=1');
  assert.equal(sso.kind, 'required');
  assert.equal(sso.url, 'https://github.com/orgs/acme/sso?x=1');
});

test('absent and blank headers are the same nothing', () => {
  assert.equal(parseSso(null).kind, 'none');
  assert.equal(parseSso('').kind, 'none');
  assert.equal(parseSso('   ').kind, 'none');
});

test('an unrecognised value is never read as absence', () => {
  const sso = parseSso('some-future-directive; organizations=1');
  assert.equal(sso.kind, 'unknown');
  assert.equal(verdict(200, sso, 4)[0], 'unreadable');
});

test('a 200 with partial results is a failure', () => {
  const sso = parseSso('partial-results; organizations=21955855,20582480');
  const [state, detail] = verdict(200, sso, 4);
  assert.equal(state, 'partial');
  assert.match(detail, /4 organization\\(s\\)/);
  assert.match(detail, /2 withheld/);
  assert.match(detail, /21955855/);
});

test('a 403 with the required form is the loud version', () => {
  const sso = parseSso('required; url=https://github.com/orgs/acme/sso');
  const [state, detail] = verdict(403, sso, 0);
  assert.equal(state, 'authorization-required');
  assert.match(detail, /orgs\\/acme\\/sso/);
});

test('a 403 without the header is not an sso problem', () => {
  const [state, detail] = verdict(403, parseSso(null), 0);
  assert.equal(state, 'forbidden');
  assert.match(detail, /read:org/);
});

test('a clean 200 is complete', () => {
  const [state, detail] = verdict(200, parseSso(null), 6);
  assert.equal(state, 'complete');
  assert.match(detail, /6 organization\\(s\\)/);
});

test('the header outranks the status code', () => {
  const sso = parseSso('partial-results; organizations=99');
  assert.equal(verdict(200, sso, 1)[0], 'partial');
  assert.equal(verdict(500, sso, 1)[0], 'partial');
});
''',
"faq": [
 ("Why does GitHub return 200 when part of the answer is missing?",
  "Because the endpoint spans organizations and the authorization is per organization. Failing the whole call because one of six organizations enforces SSO would make the endpoint useless for everyone in that position, so GitHub returns what the token may see and records the omission in the X-GitHub-SSO response header."),
 ("What exactly does the X-GitHub-SSO header look like?",
  "Two forms. On a successful but incomplete response it reads partial-results; organizations=21955855,20582480, naming the database IDs of the withheld organizations. On a rejected single-organization request it reads required; url=... and carries the link that authorizes the token. The first is the dangerous one because it accompanies a 200."),
 ("My SDK returns an array of organizations. Where do I get the header?",
  "You often cannot, which is the practical problem. Most clients expose a lower-level request method or a response hook that keeps the raw headers; use that for cross-organization listings specifically. If the wrapper genuinely discards headers, this one call is worth making with a plain HTTP client."),
 ("The header names IDs. How do I turn those into organization names?",
  "GET /organizations/{id} resolves a database ID to a login. Expect some to fail: a token that could not list the organization may not be able to read it either. Report the bare ID in that case rather than dropping the row, since the ID is still enough for an administrator to identify."),
 ("Should a partial result fail the job or just warn?",
  "It depends on what the job is for. A dashboard can show a degraded view. An inventory, an audit or a security report cannot: a partial answer there is a wrong answer with a 200 attached, and it will be quoted downstream by things that have no idea anything was withheld. Exit non-zero and name the IDs."),
],
"related": [
 ("/github/404-masking-403/", "A permission error disguised as 404 Not Found"),
 ("/github/installation-repository-selection-partial/", "An installation that covers only some repositories"),
 ("/github/app-permission-missing/", "Resource not accessible by integration"),
],
"citations": [CITE_SAML_ABOUT, CITE_SAML_AUTHZ, CITE_AUTHN, CITE_ORGS],
},


{
"slug": "installation-repository-selection-partial",
"title": "The installation covers only some repositories, silently",
"description": "repository_selection is selected, the App sees 12 of 140 repositories, and every endpoint answers truthfully about those 12 and says nothing about the rest.",
"h1": "the installation covers only some repositories, silently",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["github app repository_selection selected",
             "github app installation repositories missing",
             "github app not seeing all repos", "installation repositories total_count",
             "github app all repositories vs selected"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The scanner reports clean. Every repository it looked at was fine, every check passed, and the summary at the bottom says so. It looked at twelve repositories. The organization has a hundred and forty. Nothing errored, nothing warned, and no line of that report is untrue &mdash; the App installation was set to selected repositories at some point in 2023 and the other hundred and twenty-eight have never been inside its field of view.",
"short_answer": """<p><code>GET /installation/repositories</code> returns <code>repository_selection</code> and <code>total_count</code>. When the selection is <code>selected</code>, that count is the size of the App's world, not the size of the organization's.</p>
<p>Get the second number independently &mdash; <code>GET /orgs/{org}</code> gives <code>public_repos</code> plus <code>total_private_repos</code> &mdash; and compare. The gap is the finding, and it is the only way an audit can state its own coverage instead of assuming it.</p>""",
"problem": """<p>Partial coverage is the most expensive kind of wrong answer because it looks exactly like a right one. A scanner that crashes gets fixed on Tuesday. A scanner that reports "0 findings across 12 repositories" gets a green tick, and the number 12 sits in a line nobody reads next to the number that everybody reads.</p>
<p>It also drifts in one direction only. Somebody installs the App on three repositories to try it, it works, it goes to production, and every repository created afterwards is outside it. A selected installation does not grow: new repositories are not added automatically, so the gap between what the App sees and what exists widens every time the organization ships something new.</p>""",
"why": """<p><strong><code>repository_selection</code> has exactly two values and only one of them is safe to assume.</strong> <code>all</code> means the installation follows the account, including repositories created tomorrow. <code>selected</code> means a fixed list chosen by whoever clicked through the installation screen, possibly years ago, possibly in a hurry.</p>
<p><strong>The API is not lying, which is why nothing detects it.</strong> Every list endpoint under an installation token returns a complete answer for the installation's scope. There is no truncation flag, no <code>incomplete_results</code>, no header. The response is correct; it is the question that was smaller than anyone thought.</p>
<p><strong>The comparison needs a number from outside the installation.</strong> This is the part that makes it real work: nothing inside the App's own view can tell it what it is missing. You need the organization's repository count from <code>GET /orgs/{org}</code>, or the last page number from a <code>Link</code> header on <code>GET /orgs/{org}/repos?per_page=1</code>, and both of those need a credential that can see the whole organization.</p>
<p><strong>That outside number is itself sometimes unavailable.</strong> <code>total_private_repos</code> on the organization object is only returned to callers with enough access. Without it, the public count alone is a floor, not a total &mdash; and a coverage figure computed from a floor understates the gap, which is worse than reporting no figure at all.</p>""",
"steps": [
 {"h": "Read the installation's own view first",
  "body": """<p><code>GET /installation/repositories?per_page=100</code>. Take <code>repository_selection</code> and <code>total_count</code> from the first page: <code>total_count</code> is the full size of the installation, while the <code>repositories</code> array is one page of it. If the selection is <code>all</code>, you are done and the answer is good news.</p>"""},
 {"h": "Get the organization's real total from outside the App",
  "body": """<p><code>GET /orgs/{org}</code> returns <code>public_repos</code> and, for callers with enough access, <code>total_private_repos</code>. Add them. Where <code>total_private_repos</code> is absent, do not substitute the public count and call it a total &mdash; report that the comparison could not be made, because a coverage number computed from half the denominator is a confident understatement of the gap.</p>"""},
 {"h": "Compare, and treat a match as fragile rather than fixed",
  "body": """<p>Twelve of a hundred and forty is the obvious finding. A hundred and forty of a hundred and forty on a <code>selected</code> installation is the subtle one: complete today and complete by coincidence, because nothing adds the repository somebody creates this afternoon. Those two deserve different words in the report and both deserve a mention.</p>"""},
 {"h": "Name the repositories that are outside, not just the count",
  "body": """<p>With a credential that can list <code>GET /orgs/{org}/repos?per_page=100</code>, diff the full names against the installation's list. A count starts an argument about whether the count is right; a list of twelve repository names that nobody has ever scanned ends it.</p>"""},
 {"h": "Make coverage part of every run, permanently",
  "body": """<p>The repair is to switch the installation to All repositories, or to add the missing ones explicitly. The durable fix is that the tool asserts its own coverage at startup and prints it in the summary next to the findings, so "0 findings" is never again allowed to appear without the number of repositories that produced it.</p>"""},
],
"verify": """<p>Re-run after widening the installation. The state should be <code>all-repositories</code>, and the count the script prints should match the organization's own total.</p>
<pre><code class="language-bash">python3 github_app_coverage_audit.py --org acme
# all-repositories   140 repository(ies) visible; new repositories join automatically</code></pre>""",
"code_intro": "Two GET requests: one inside the installation, one outside it. The pure functions are the denominator and the comparison, kept apart on purpose &mdash; deciding that an organization total is unreadable is a different judgement from deciding what a gap means, and folding them together is how a missing <code>total_private_repos</code> quietly becomes a coverage figure of 100%.",
"py_file": "github_app_coverage_audit.py",
"py": '''"""Report how much of an organization a GitHub App installation can actually see.

Read only. Two GET requests and no writes: an installation token plus a token
that can read the organization is enough. The repair is printed, never performed.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_app_coverage_audit")

API = "https://api.github.com"
UA = "github-app-coverage-audit/1.0"


def expected_total(org):
    """Repositories the organization actually has, or None if it cannot be known.

    public_repos plus total_private_repos. total_private_repos is only returned
    to callers with enough access; when it is absent the public count is a floor
    and not a total. Returning it anyway would produce a coverage figure that
    understates the gap, so this returns None and lets the caller say so.
    """
    if not isinstance(org, dict):
        return None
    public = org.get("public_repos")
    private = org.get("total_private_repos")
    if public is None or private is None:
        return None
    return int(public) + int(private)


def coverage(selection, seen, expected):
    """Compare what the installation sees against what exists. Pure.

    Returns (state, detail). A `selected` installation whose count happens to
    match today is deliberately not the same state as `all`: it is correct now
    and nothing keeps it correct.
    """
    sel = str(selection or "").strip().lower()

    if sel == "all":
        return ("all-repositories",
                "%d repository(ies) visible, and repository_selection is 'all', "
                "so repositories created later join the installation "
                "automatically." % (seen,))

    if sel != "selected":
        return ("unknown-selection",
                "repository_selection is %r, which is neither 'all' nor "
                "'selected'. Do not assume coverage from a value you cannot "
                "interpret." % (selection,))

    if expected is None:
        return ("unmeasured",
                "%d repository(ies) selected. The organization's own total is "
                "not readable with this credential, so this is a count and not a "
                "coverage figure. Say so in the report rather than implying "
                "completeness." % (seen,))

    if seen > expected:
        return ("inconsistent",
                "%d repository(ies) visible against an organization total of %d. "
                "The installation spans more than this organization, or one of "
                "the two counts is stale. Resolve it before quoting either."
                % (seen, expected))

    if seen == expected:
        return ("selected-complete",
                "%d of %d today, and nothing keeps it that way: a 'selected' "
                "installation does not pick up repositories created later, so "
                "this is complete by coincidence." % (seen, expected))

    return ("partial",
            "%d of %d repositories. Every endpoint answers truthfully about "
            "those %d and says nothing at all about the other %d, so a clean "
            "report here covers %.0f%% of the organization."
            % (seen, expected, seen, expected - seen, 100.0 * seen / expected))


def get(session, url, **params):
    return session.get(url, params=params, timeout=30)


def installation_view(session, api):
    """repository_selection, total_count and the full names, from inside the App."""
    names = []
    selection, total = None, 0
    page = 1
    while True:
        r = get(session, api + "/installation/repositories", per_page=100, page=page)
        if r.status_code != 200:
            raise SystemExit("%d from GET /installation/repositories: this needs "
                             "an App installation token" % (r.status_code,))
        body = r.json()
        if page == 1:
            selection = body.get("repository_selection")
            total = int(body.get("total_count") or 0)
        items = body.get("repositories", [])
        names.extend(str(r_.get("full_name") or "") for r_ in items)
        if len(items) < 100:
            break
        page += 1
    return selection, total, names


def org_repo_names(session, api, org):
    """Every repository in the organization, from outside the installation."""
    names = []
    page = 1
    while True:
        r = get(session, "%s/orgs/%s/repos" % (api, org), per_page=100, page=page)
        if r.status_code != 200:
            return None
        items = r.json()
        names.extend(str(x.get("full_name") or "") for x in items)
        if len(items) < 100:
            break
        page += 1
    return names


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--org", required=True,
                    help="the organization the installation is meant to cover")
    ap.add_argument("--api", default=API,
                    help="API host, for GitHub Enterprise Server")
    ap.add_argument("--list-missing", action="store_true",
                    help="name the repositories outside the installation")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (an App installation token, read-only)")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    selection, seen, inside = installation_view(session, args.api)

    org_response = get(session, "%s/orgs/%s" % (args.api, args.org))
    expected = expected_total(org_response.json()) if org_response.status_code == 200 else None

    state, detail = coverage(selection, seen, expected)
    line = "%-18s %s" % (state, detail)
    if state == "all-repositories":
        log.info(line)
        return 0

    log.warning(line)
    if args.list_missing:
        outside = org_repo_names(session, args.api, args.org)
        if outside is None:
            log.warning("  the organization's repository list is not readable "
                        "with this credential, so the missing names cannot be "
                        "printed. The counts above still stand.")
        else:
            have = {n.lower() for n in inside}
            missing = sorted(n for n in outside if n.lower() not in have)
            for name in missing[:50]:
                log.warning("  outside the installation: %s", name)
            if len(missing) > 50:
                log.warning("  ... and %d more", len(missing) - 50)

    log.warning("  repair: switch the installation to All repositories, or add "
                "the missing repositories to it. Then have the tool print its "
                "own coverage next to its findings, so a clean report can never "
                "again appear without the number of repositories behind it.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-app-coverage-audit.mjs",
"js": '''/**
 * Report how much of an organization a GitHub App installation can actually see.
 *
 * Read only. Two GET requests and no writes. The repair is printed, never
 * performed.
 */
const API = 'https://api.github.com';
const UA = 'github-app-coverage-audit/1.0';

/**
 * Repositories the organization actually has, or null if it cannot be known.
 * total_private_repos is only returned to callers with enough access; without it
 * the public count is a floor, and a coverage figure built on a floor understates
 * the gap, so this returns null rather than a number.
 */
export function expectedTotal(org) {
  if (!org || typeof org !== 'object') return null;
  const pub = org.public_repos;
  const priv = org.total_private_repos;
  if (pub === null || pub === undefined) return null;
  if (priv === null || priv === undefined) return null;
  return Number(pub) + Number(priv);
}

/**
 * Compare what the installation sees against what exists. Pure.
 * Returns [state, detail].
 */
export function coverage(selection, seen, expected) {
  const sel = String(selection ?? '').trim().toLowerCase();

  if (sel === 'all') {
    return ['all-repositories',
      `${seen} repository(ies) visible, and repository_selection is 'all', so ` +
      'repositories created later join the installation automatically.'];
  }

  if (sel !== 'selected') {
    return ['unknown-selection',
      `repository_selection is ${JSON.stringify(selection)}, which is neither ` +
      "'all' nor 'selected'. Do not assume coverage from a value you cannot " +
      'interpret.'];
  }

  if (expected === null || expected === undefined) {
    return ['unmeasured',
      `${seen} repository(ies) selected. The organization's own total is not ` +
      'readable with this credential, so this is a count and not a coverage ' +
      'figure. Say so in the report rather than implying completeness.'];
  }

  if (seen > expected) {
    return ['inconsistent',
      `${seen} repository(ies) visible against an organization total of ` +
      `${expected}. The installation spans more than this organization, or one ` +
      'of the two counts is stale. Resolve it before quoting either.'];
  }

  if (seen === expected) {
    return ['selected-complete',
      `${seen} of ${expected} today, and nothing keeps it that way: a ` +
      "'selected' installation does not pick up repositories created later, so " +
      'this is complete by coincidence.'];
  }

  const pct = Math.round((100 * seen) / expected);
  return ['partial',
    `${seen} of ${expected} repositories. Every endpoint answers truthfully ` +
    `about those ${seen} and says nothing at all about the other ` +
    `${expected - seen}, so a clean report here covers ${pct}% of the ` +
    'organization.'];
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function get(token, url, params = {}) {
  const u = new URL(url);
  for (const [k, v] of Object.entries(params)) u.searchParams.set(k, v);
  return fetch(u, { headers: headers(token) });
}

export async function installationView(token, api = API) {
  const names = [];
  let selection = null;
  let total = 0;
  let page = 1;
  for (;;) {
    const res = await get(token, `${api}/installation/repositories`,
                          { per_page: 100, page });
    if (res.status !== 200) {
      throw new Error(`${res.status} from GET /installation/repositories: this ` +
                      'needs an App installation token');
    }
    const body = await res.json();
    if (page === 1) {
      selection = body.repository_selection;
      total = Number(body.total_count ?? 0);
    }
    const items = body.repositories ?? [];
    names.push(...items.map((r) => String(r.full_name ?? '')));
    if (items.length < 100) break;
    page += 1;
  }
  return { selection, total, names };
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (an App installation token, read-only)');
    process.exitCode = 2;
    return;
  }
  const at = process.argv.indexOf('--org');
  const org = at >= 0 ? process.argv[at + 1] : null;
  if (!org) {
    console.error('pass --org <login>');
    process.exitCode = 2;
    return;
  }

  const { selection, total: seen } = await installationView(token);

  const orgRes = await get(token, `${API}/orgs/${org}`);
  const expected = orgRes.status === 200 ? expectedTotal(await orgRes.json()) : null;

  const [state, detail] = coverage(selection, seen, expected);
  const line = `${state.padEnd(18)} ${detail}`;
  if (state === 'all-repositories') {
    console.log(line);
    return;
  }

  console.warn(line);
  console.warn('  repair: switch the installation to All repositories, or add the ' +
               'missing repositories to it. Then have the tool print its own ' +
               'coverage next to its findings, so a clean report can never again ' +
               'appear without the number of repositories behind it.');
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing token, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Two cases are worth pinning. A <code>selected</code> installation whose count matches the organization today must not report as <code>all</code>, because the two differ entirely in what happens next week. And an organization object with no <code>total_private_repos</code> must produce no coverage figure at all &mdash; the tempting shortcut is to fall back to <code>public_repos</code>, which turns an unmeasurable gap into a reassuring percentage.",
"test_py_file": "test_github_app_coverage_audit.py",
"test_py": '''from github_app_coverage_audit import coverage, expected_total


def test_org_total_needs_both_halves():
    assert expected_total({"public_repos": 40, "total_private_repos": 100}) == 140
    assert expected_total({"public_repos": 0, "total_private_repos": 0}) == 0


def test_a_missing_private_count_yields_no_total_at_all():
    # Falling back to public_repos here is how an unmeasurable gap becomes a
    # reassuring percentage.
    assert expected_total({"public_repos": 40}) is None
    assert expected_total({}) is None
    assert expected_total(None) is None


def test_all_repositories_is_the_only_good_news():
    state, detail = coverage("all", 140, 140)
    assert state == "all-repositories"
    assert "automatically" in detail


def test_twelve_of_a_hundred_and_forty_names_the_gap_and_the_share():
    state, detail = coverage("selected", 12, 140)
    assert state == "partial"
    assert "12 of 140" in detail
    assert "128" in detail
    assert "9%" in detail


def test_selected_and_complete_is_not_the_same_as_all():
    # Correct today, and nothing keeps it correct.
    state, detail = coverage("selected", 140, 140)
    assert state == "selected-complete"
    assert "coincidence" in detail


def test_no_org_total_means_a_count_not_a_coverage_figure():
    state, detail = coverage("selected", 12, None)
    assert state == "unmeasured"
    assert "not a coverage figure" in detail


def test_seeing_more_than_exists_is_reported_rather_than_averaged_away():
    state, _ = coverage("selected", 150, 140)
    assert state == "inconsistent"


def test_an_uninterpretable_selection_is_never_assumed_complete():
    assert coverage(None, 12, 140)[0] == "unknown-selection"
    assert coverage("some-new-value", 12, 140)[0] == "unknown-selection"
''',
"test_js_file": "github-app-coverage-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { coverage, expectedTotal } from './github-app-coverage-audit.mjs';

test('org total needs both halves', () => {
  assert.equal(expectedTotal({ public_repos: 40, total_private_repos: 100 }), 140);
  assert.equal(expectedTotal({ public_repos: 0, total_private_repos: 0 }), 0);
});

test('a missing private count yields no total at all', () => {
  assert.equal(expectedTotal({ public_repos: 40 }), null);
  assert.equal(expectedTotal({}), null);
  assert.equal(expectedTotal(null), null);
});

test('all repositories is the only good news', () => {
  const [state, detail] = coverage('all', 140, 140);
  assert.equal(state, 'all-repositories');
  assert.match(detail, /automatically/);
});

test('twelve of a hundred and forty names the gap and the share', () => {
  const [state, detail] = coverage('selected', 12, 140);
  assert.equal(state, 'partial');
  assert.match(detail, /12 of 140/);
  assert.match(detail, /128/);
  assert.match(detail, /9%/);
});

test('selected and complete is not the same as all', () => {
  const [state, detail] = coverage('selected', 140, 140);
  assert.equal(state, 'selected-complete');
  assert.match(detail, /coincidence/);
});

test('no org total means a count, not a coverage figure', () => {
  const [state, detail] = coverage('selected', 12, null);
  assert.equal(state, 'unmeasured');
  assert.match(detail, /not a coverage figure/);
});

test('seeing more than exists is reported rather than averaged away', () => {
  assert.equal(coverage('selected', 150, 140)[0], 'inconsistent');
});

test('an uninterpretable selection is never assumed complete', () => {
  assert.equal(coverage(null, 12, 140)[0], 'unknown-selection');
  assert.equal(coverage('some-new-value', 12, 140)[0], 'unknown-selection');
});
''',
"faq": [
 ("How do I find out whether an installation covers every repository?",
  "GET /installation/repositories returns repository_selection alongside total_count. A value of all means the installation follows the account and picks up new repositories; selected means a fixed list. Only the first of those can be assumed complete."),
 ("Why does the App not see repositories created after it was installed?",
  "Because a selected installation is a list, not a rule. Repositories are added to it by a person, so anything created afterwards is outside it until somebody goes back and ticks it. This is the reason the gap only ever grows."),
 ("Is there a flag on the response that says the results are incomplete?",
  "No, and that is the whole difficulty. Every endpoint under the installation token returns a correct, complete answer for the installation's scope. There is no truncation marker to check, so the incompleteness has to be established by comparing against a count obtained from outside the App."),
 ("What if I cannot read the organization's total?",
  "total_private_repos on GET /orgs/{org} is only returned to callers with enough access. Without it, report the number of repositories the installation covers and state plainly that coverage could not be computed. Substituting public_repos produces a percentage that is confidently too high."),
 ("The counts match. Is the installation fine?",
  "Today. A selected installation that happens to cover everything right now still does not cover the repository somebody creates this afternoon, so it is worth reporting as its own state rather than as a pass. Switching to All repositories is what actually removes the failure mode."),
],
"related": [
 ("/github/app-permission-missing/", "Resource not accessible by integration"),
 ("/github/404-masking-403/", "A permission error disguised as 404 Not Found"),
 ("/github/saml-partial-results/", "Org lists that silently omit SSO-enforced orgs"),
],
"citations": [CITE_INSTALLATIONS, CITE_INSTALL_AUTH, CITE_ORGS, CITE_CHOOSING],
},


{
"slug": "app-permission-missing",
"title": "Resource not accessible by integration on one endpoint",
"description": "One endpoint 403s for a GitHub App while everything else works. The x-accepted-github-permissions header names exactly what the endpoint wanted.",
"h1": "resource not accessible by integration on one endpoint",
"category": "GitHub API",
"pill": "Diagnostic",
"chips": ["Read-only token", "Python and Node.js", "Tests included"],
"keywords": ["resource not accessible by integration",
             "x-accepted-github-permissions", "github app 403 permission",
             "github app permissions missing", "github app permission upgrade accepted"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Nineteen endpoints work. The twentieth returns <code>403 {\"message\":\"Resource not accessible by integration\"}</code>, which names no permission, no resource and no level, and reads like a platform bug rather than a configuration one. It is the one failure in this cluster where GitHub actually tells you the answer: it is in the <code>x-accepted-github-permissions</code> response header on that very 403, which almost no HTTP client shows you by default.",
"short_answer": """<p>Make the failing call again and read <code>x-accepted-github-permissions</code> off the response. It names the permission and level the endpoint accepts, in the form <code>pull_requests=write</code>. Then read what the App actually holds from <code>GET /app</code> under the App's JWT, which returns the full <code>permissions</code> map. The difference is the answer.</p>
<p>Two cases hide in here. A 403 with <strong>no</strong> such header means the endpoint does not accept installation tokens at all, so no permission will open it. And adding a permission to the App is only half a repair: it stays inert until each installation accepts the upgrade.</p>""",
"problem": """<p>"Resource not accessible by integration" is one of the most-searched GitHub errors in existence, and the reason is that the message contains no nouns. It does not say which resource, which integration, or what would make it accessible. Read cold, it suggests the endpoint is broken for Apps generally, and the natural next move &mdash; trying a different endpoint, or a different token, or the same call from a workflow &mdash; wastes an afternoon confirming that the rest of the integration is healthy.</p>
<p>The information is right there in the response. It is simply in a header, and the code that raised the exception kept the status and the body and dropped everything else. That is why this note is the odd one in this group: it is not GitHub withholding anything. It is GitHub answering a question nobody read the reply to.</p>""",
"why": """<p><strong>App permissions are per resource and per level, and there are dozens of them.</strong> An App with <code>contents: read</code> cannot list pull requests; an App with <code>pull_requests: read</code> cannot request a reviewer. Each endpoint has its own requirement, so an integration can be nineteen-twentieths correct and the twentieth call is the one that finds the hole.</p>
<p><strong>The error message is deliberately generic and the header is deliberately specific.</strong> <code>x-accepted-github-permissions</code> exists exactly because the message cannot carry this. It is on the 403 itself, so no second call is needed &mdash; only a client that keeps headers.</p>
<p><strong>A 403 with no header is a completely different problem.</strong> Some endpoints do not accept a server-to-server installation token at all: <code>GET /user</code> is the classic case, because an installation has no current user. That failure looks identical from the message alone and no permission change will ever fix it. The absence of the header is the signal, which means you have to distinguish "header absent" from "header not read".</p>
<p><strong>Adding the permission does not grant it.</strong> A new or widened permission on a GitHub App is pending until each installation's owner accepts it. The App's own settings page will show the permission, <code>GET /app</code> will show the permission, and installations that have not accepted keep 403ing exactly as before &mdash; which is the second afternoon this error costs people.</p>""",
"steps": [
 {"h": "Repeat the failing call and keep the headers",
  "body": """<p>Any client that exposes the raw response will do. The value looks like <code>x-accepted-github-permissions: pull_requests=write</code>; where an endpoint accepts more than one way in, more than one pair appears. Log the whole header verbatim before parsing it, because the parse is a convenience and the raw string is the evidence.</p>"""},
 {"h": "Read what the App holds, not what you remember granting",
  "body": """<p><code>GET /app</code> authenticated with the App's JWT returns the <code>permissions</code> map. This is the only authoritative statement of what the App asks for. An installation token cannot read it &mdash; which is itself worth reporting rather than papering over, since it tells you which credential to go and fetch.</p>"""},
 {"h": "Diff by level, not by presence",
  "body": """<p><code>read</code> is not <code>write</code>. Half of these incidents are a permission that is present in the map at the wrong level, which looks correct in a glance down a settings page and is not correct to the endpoint. Rank the levels and compare them numerically so <code>contents: read</code> against <code>contents=write</code> reports as a level problem rather than as satisfied.</p>"""},
 {"h": "Treat a 403 with no header as a different diagnosis entirely",
  "body": """<p>If the header is genuinely absent on a 403, the endpoint does not accept installation tokens. Stop looking at the permission map and switch that specific call to the App-appropriate equivalent &mdash; <code>GET /installation/repositories</code> rather than <code>GET /user/repos</code>, <code>GET /app</code> for the App's own identity &mdash; or to a user-to-server token obtained through the App's OAuth flow.</p>"""},
 {"h": "Add the permission, then chase the acceptances",
  "body": """<p>Add exactly what the header named and nothing more. Then remember that every existing installation keeps its old permission set until an owner accepts the upgrade, so the endpoint keeps failing for them after your change looks complete. Notify the installers, and keep this check running until the 403 stops rather than until the settings page looks right.</p>"""},
],
"verify": """<p>Re-run against the endpoint that was failing. It should answer, and the verdict should be <code>accessible</code>.</p>
<pre><code class="language-bash">python3 github_app_permission_diff.py --path /repos/acme/api/pulls
# accessible       HTTP 200: the endpoint answered, so there is nothing to diff.</code></pre>""",
"code_intro": "One GET at the endpoint that fails and one at <code>GET /app</code>, both read-only. The pure functions are the header parser and the diff, and the diff carries the two distinctions that make this note worth writing: a permission held at too low a level is not a permission that is absent, and a 403 with no header at all is not a permission problem in the first place.",
"py_file": "github_app_permission_diff.py",
"py": '''"""Name the GitHub App permission a 403 was actually asking for.

Read only. GET requests and nothing else. The repair is printed, never
performed, because this script holds a credential that reaches repositories.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("github_app_permission_diff")

API = "https://api.github.com"
UA = "github-app-permission-diff/1.0"

# Ordered so a comparison is arithmetic. "read" satisfying a "write" requirement
# is the single most common way this error survives a careful look at a settings
# page, and only a ranking catches it.
LEVELS = {"none": 0, "read": 1, "write": 2, "admin": 3}


def parse_accepted(value):
    """Parse x-accepted-github-permissions into (permission, level) pairs. Pure.

    The value is a list of name=level pairs. Endpoints that accept more than one
    route in list more than one pair, and the separator is not consistent across
    every endpoint, so both commas and semicolons are accepted here rather than
    depending on which one a given endpoint used.
    """
    raw = (value or "").strip()
    if not raw:
        return []
    out = []
    for chunk in raw.replace(";", ",").split(","):
        chunk = chunk.strip()
        name, sep, level = chunk.partition("=")
        if not sep or not name.strip():
            continue
        out.append((name.strip(), level.strip().lower()))
    return out


def diff(held, accepted, status=403):
    """Compare what the App holds against what the endpoint asked for. Pure.

    `held` is the permissions map from GET /app, or None when it could not be
    read. `accepted` is the parsed header. Returns (state, detail).

    Where an endpoint lists alternatives, holding one of them can be enough, so
    reporting every unmet pair is a superset. That is the safe direction for a
    diagnostic: it can send you to check a permission you did not need, but it
    will never report one as fine when it is not.
    """
    if status < 400:
        return ("accessible",
                "HTTP %s: the endpoint answered, so there is nothing to diff."
                % (status,))
    if status != 403:
        return ("not-a-permission-error",
                "HTTP %s is not 'Resource not accessible by integration'. A 404 "
                "here is the masked-permission case and a 401 is a dead "
                "credential." % (status,))

    if not accepted:
        return ("endpoint-refuses-apps",
                "403 with no x-accepted-github-permissions header. The endpoint "
                "does not accept an installation token at all, so no permission "
                "you add will open it: use the App equivalent, or a "
                "user-to-server token from the App's OAuth flow.")

    wanted = ", ".join("%s: %s" % (n, l) for n, l in accepted)

    if held is None:
        return ("needed",
                "the endpoint accepts %s. The App's own permission map is not "
                "readable with this credential; read it with GET /app under the "
                "App JWT to see which of those it is missing." % (wanted,))

    missing, low = [], []
    for name, level in accepted:
        have = str(held.get(name) or "none").strip().lower()
        rank = LEVELS.get(have, 0)
        need = LEVELS.get(level, 0)
        if rank == 0:
            missing.append("%s: %s" % (name, level))
        elif rank < need:
            low.append("%s has %s and needs %s" % (name, have, level))

    if not missing and not low:
        return ("sufficient",
                "the App already holds %s, so the permission map is not the "
                "cause. Check that the installation covers this repository and "
                "that the permission upgrade was accepted by this installation."
                % (wanted,))

    if not missing:
        return ("level-too-low",
                "held, but at the wrong level: %s. A permission at 'read' looks "
                "correct on a settings page and is not correct to the endpoint."
                % ("; ".join(low),))

    return ("permission-absent",
            "not held at all: %s.%s" % (", ".join(missing),
                                        (" Also at the wrong level: %s."
                                         % "; ".join(low)) if low else ""))


def get(session, url, **params):
    return session.get(url, params=params, timeout=30)


def held_permissions(session, api):
    """The App's own permission map, or None when the credential cannot read it.

    GET /app needs the App JWT. An installation token gets a 403 here, which is
    a fact about the credential rather than about the App, so None is returned
    and the caller says so out loud.
    """
    r = get(session, api + "/app")
    if r.status_code != 200:
        return None
    return r.json().get("permissions") or {}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--path", required=True,
                    help="the API path that returns 403, e.g. /repos/acme/api/pulls")
    ap.add_argument("--api", default=API,
                    help="API host, for GitHub Enterprise Server")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN (an App installation token, or the App JWT "
                  "if you also want the permission map)")
        return 2

    session = requests.Session()
    session.headers.update({
        "Authorization": "Bearer " + token,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": UA,
    })

    path = args.path if args.path.startswith("/") else "/" + args.path
    probe = get(session, args.api + path)
    raw = probe.headers.get("x-accepted-github-permissions")
    log.info("%s -> HTTP %s", path, probe.status_code)
    log.info("x-accepted-github-permissions: %s", raw if raw is not None else "absent")

    accepted = parse_accepted(raw)
    held = held_permissions(session, args.api)
    state, detail = diff(held, accepted, probe.status_code)

    if state == "accessible":
        log.info("%-24s %s", state, detail)
        return 0

    log.warning("%-24s %s", state, detail)
    if held is not None:
        log.warning("  the App holds: %s",
                    ", ".join("%s: %s" % (k, v) for k, v in sorted(held.items()))
                    or "nothing")
    if state in ("permission-absent", "level-too-low"):
        log.warning("  repair: add exactly the permission named above to the App, "
                    "then have every installation owner accept the upgrade. Until "
                    "an installation accepts it, that installation keeps the old "
                    "permission set and keeps returning this same 403.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "github-app-permission-diff.mjs",
"js": '''/**
 * Name the GitHub App permission a 403 was actually asking for.
 *
 * Read only. GET requests and nothing else. The repair is printed, never
 * performed.
 */
const API = 'https://api.github.com';
const UA = 'github-app-permission-diff/1.0';

// Ordered so a comparison is arithmetic. "read" satisfying a "write" requirement
// is the most common way this error survives a careful look at a settings page.
const LEVELS = { none: 0, read: 1, write: 2, admin: 3 };

/**
 * Parse x-accepted-github-permissions into [permission, level] pairs. Pure.
 * Both commas and semicolons are accepted as separators rather than depending on
 * which one a given endpoint used.
 */
export function parseAccepted(value) {
  const raw = String(value ?? '').trim();
  if (!raw) return [];
  const out = [];
  for (const chunk of raw.replace(/;/g, ',').split(',')) {
    const at = chunk.indexOf('=');
    if (at < 0) continue;
    const name = chunk.slice(0, at).trim();
    const level = chunk.slice(at + 1).trim().toLowerCase();
    if (!name) continue;
    out.push([name, level]);
  }
  return out;
}

/**
 * Compare what the App holds against what the endpoint asked for. Pure.
 * `held` is the map from GET /app, or null when it could not be read.
 * Returns [state, detail].
 *
 * Where an endpoint lists alternatives, holding one can be enough, so reporting
 * every unmet pair is a superset: it may send you to check a permission you did
 * not need, but it never reports one as fine when it is not.
 */
export function diff(held, accepted, status = 403) {
  if (status < 400) {
    return ['accessible',
      `HTTP ${status}: the endpoint answered, so there is nothing to diff.`];
  }
  if (status !== 403) {
    return ['not-a-permission-error',
      `HTTP ${status} is not 'Resource not accessible by integration'. A 404 ` +
      'here is the masked-permission case and a 401 is a dead credential.'];
  }

  if (!accepted || accepted.length === 0) {
    return ['endpoint-refuses-apps',
      '403 with no x-accepted-github-permissions header. The endpoint does not ' +
      'accept an installation token at all, so no permission you add will open ' +
      "it: use the App equivalent, or a user-to-server token from the App's " +
      'OAuth flow.'];
  }

  const wanted = accepted.map(([n, l]) => `${n}: ${l}`).join(', ');

  if (held === null || held === undefined) {
    return ['needed',
      `the endpoint accepts ${wanted}. The App's own permission map is not ` +
      'readable with this credential; read it with GET /app under the App JWT ' +
      'to see which of those it is missing.'];
  }

  const missing = [];
  const low = [];
  for (const [name, level] of accepted) {
    const have = String(held[name] ?? 'none').trim().toLowerCase();
    const rank = LEVELS[have] ?? 0;
    const need = LEVELS[level] ?? 0;
    if (rank === 0) missing.push(`${name}: ${level}`);
    else if (rank < need) low.push(`${name} has ${have} and needs ${level}`);
  }

  if (missing.length === 0 && low.length === 0) {
    return ['sufficient',
      `the App already holds ${wanted}, so the permission map is not the cause. ` +
      'Check that the installation covers this repository and that the ' +
      'permission upgrade was accepted by this installation.'];
  }

  if (missing.length === 0) {
    return ['level-too-low',
      `held, but at the wrong level: ${low.join('; ')}. A permission at 'read' ` +
      'looks correct on a settings page and is not correct to the endpoint.'];
  }

  const extra = low.length ? ` Also at the wrong level: ${low.join('; ')}.` : '';
  return ['permission-absent', `not held at all: ${missing.join(', ')}.${extra}`];
}

function headers(token) {
  return {
    Authorization: `Bearer ${token}`,
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    'User-Agent': UA,
  };
}

async function get(token, url) {
  return fetch(url, { headers: headers(token) });
}

export async function heldPermissions(token, api = API) {
  const res = await get(token, `${api}/app`);
  if (res.status !== 200) return null;
  return (await res.json()).permissions ?? {};
}

async function main() {
  const token = process.env.GITHUB_TOKEN;
  if (!token) {
    console.error('set GITHUB_TOKEN (an App installation token, or the App JWT ' +
                  'if you also want the permission map)');
    process.exitCode = 2;
    return;
  }
  const at = process.argv.indexOf('--path');
  let path = at >= 0 ? process.argv[at + 1] : null;
  if (!path) {
    console.error('pass --path /repos/owner/name/pulls');
    process.exitCode = 2;
    return;
  }
  if (!path.startsWith('/')) path = `/${path}`;

  const probe = await get(token, API + path);
  const raw = probe.headers.get('x-accepted-github-permissions');
  console.log(`${path} -> HTTP ${probe.status}`);
  console.log(`x-accepted-github-permissions: ${raw ?? 'absent'}`);

  const accepted = parseAccepted(raw);
  const held = await heldPermissions(token);
  const [state, detail] = diff(held, accepted, probe.status);

  if (state === 'accessible') {
    console.log(`${state.padEnd(24)} ${detail}`);
    return;
  }

  console.warn(`${state.padEnd(24)} ${detail}`);
  if (held !== null) {
    const shown = Object.entries(held).sort()
      .map(([k, v]) => `${k}: ${v}`).join(', ');
    console.warn(`  the App holds: ${shown || 'nothing'}`);
  }
  if (state === 'permission-absent' || state === 'level-too-low') {
    console.warn('  repair: add exactly the permission named above to the App, ' +
                 'then have every installation owner accept the upgrade. Until an ' +
                 'installation accepts it, that installation keeps the old ' +
                 'permission set and keeps returning this same 403.');
  }
  process.exitCode = 1;
}

// Only run when invoked directly. The test file imports this module, and without
// the guard main() would run there too, fail on the missing token, and set a
// non-zero exit code that fails the whole test file even as every test passes.
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch((err) => { console.error(err.message); process.exitCode = 2; });
}
''',
"test_intro": "Three rules earn their tests. A permission held at <code>read</code> where the endpoint wants <code>write</code> has to report as its own state rather than as satisfied, because it is the case that survives a careful reading of the settings page. A 403 with no header must never be diagnosed as a missing permission, since nothing you add will fix it. And an empty permission map is not the same as an unreadable one &mdash; the first says the App has nothing, the second says you brought the wrong credential.",
"test_py_file": "test_github_app_permission_diff.py",
"test_py": '''from github_app_permission_diff import diff, parse_accepted


def test_the_header_parses_to_name_and_level_pairs():
    assert parse_accepted("pull_requests=write") == [("pull_requests", "write")]
    assert parse_accepted("contents=read, metadata=read") == [
        ("contents", "read"), ("metadata", "read")]
    assert parse_accepted("issues=write; pull_requests=write") == [
        ("issues", "write"), ("pull_requests", "write")]


def test_an_absent_header_parses_to_nothing_rather_than_a_guess():
    assert parse_accepted(None) == []
    assert parse_accepted("") == []
    assert parse_accepted("garbage-with-no-equals") == []


def test_a_403_with_no_header_is_not_a_permission_problem():
    # GET /user under an installation token. No permission will ever open it.
    state, detail = diff({"contents": "read"}, [], 403)
    assert state == "endpoint-refuses-apps"
    assert "installation token" in detail


def test_read_where_write_is_needed_is_its_own_state():
    state, detail = diff({"pull_requests": "read"},
                         parse_accepted("pull_requests=write"))
    assert state == "level-too-low"
    assert "has read and needs write" in detail


def test_a_permission_that_is_absent_is_named():
    state, detail = diff({"contents": "read"},
                         parse_accepted("pull_requests=write"))
    assert state == "permission-absent"
    assert "pull_requests: write" in detail


def test_holding_everything_asked_for_points_elsewhere():
    state, detail = diff({"pull_requests": "write", "metadata": "read"},
                         parse_accepted("pull_requests=write, metadata=read"))
    assert state == "sufficient"
    assert "accepted" in detail


def test_write_satisfies_a_read_requirement():
    assert diff({"contents": "write"}, parse_accepted("contents=read"))[0] == "sufficient"


def test_an_unreadable_map_is_not_an_empty_one():
    # None means "wrong credential"; {} means "the App holds nothing".
    assert diff(None, parse_accepted("issues=write"))[0] == "needed"
    assert diff({}, parse_accepted("issues=write"))[0] == "permission-absent"


def test_a_success_and_a_non_403_are_not_diffed_at_all():
    assert diff({}, parse_accepted("issues=write"), 200)[0] == "accessible"
    state, detail = diff({}, parse_accepted("issues=write"), 404)
    assert state == "not-a-permission-error"
    assert "masked" in detail
''',
"test_js_file": "github-app-permission-diff.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { diff, parseAccepted } from './github-app-permission-diff.mjs';

test('the header parses to name and level pairs', () => {
  assert.deepEqual(parseAccepted('pull_requests=write'), [['pull_requests', 'write']]);
  assert.deepEqual(parseAccepted('contents=read, metadata=read'),
    [['contents', 'read'], ['metadata', 'read']]);
  assert.deepEqual(parseAccepted('issues=write; pull_requests=write'),
    [['issues', 'write'], ['pull_requests', 'write']]);
});

test('an absent header parses to nothing rather than a guess', () => {
  assert.deepEqual(parseAccepted(null), []);
  assert.deepEqual(parseAccepted(''), []);
  assert.deepEqual(parseAccepted('garbage-with-no-equals'), []);
});

test('a 403 with no header is not a permission problem', () => {
  const [state, detail] = diff({ contents: 'read' }, [], 403);
  assert.equal(state, 'endpoint-refuses-apps');
  assert.match(detail, /installation token/);
});

test('read where write is needed is its own state', () => {
  const [state, detail] = diff({ pull_requests: 'read' },
                               parseAccepted('pull_requests=write'));
  assert.equal(state, 'level-too-low');
  assert.match(detail, /has read and needs write/);
});

test('a permission that is absent is named', () => {
  const [state, detail] = diff({ contents: 'read' },
                               parseAccepted('pull_requests=write'));
  assert.equal(state, 'permission-absent');
  assert.match(detail, /pull_requests: write/);
});

test('holding everything asked for points elsewhere', () => {
  const [state, detail] = diff({ pull_requests: 'write', metadata: 'read' },
                               parseAccepted('pull_requests=write, metadata=read'));
  assert.equal(state, 'sufficient');
  assert.match(detail, /accepted/);
});

test('write satisfies a read requirement', () => {
  assert.equal(diff({ contents: 'write' }, parseAccepted('contents=read'))[0],
               'sufficient');
});

test('an unreadable map is not an empty one', () => {
  assert.equal(diff(null, parseAccepted('issues=write'))[0], 'needed');
  assert.equal(diff({}, parseAccepted('issues=write'))[0], 'permission-absent');
});

test('a success and a non-403 are not diffed at all', () => {
  assert.equal(diff({}, parseAccepted('issues=write'), 200)[0], 'accessible');
  const [state, detail] = diff({}, parseAccepted('issues=write'), 404);
  assert.equal(state, 'not-a-permission-error');
  assert.match(detail, /masked/);
});
''',
"faq": [
 ("What does 'Resource not accessible by integration' actually mean?",
  "That a GitHub App called an endpoint its permission set does not cover. The message names nothing because the specifics live in the x-accepted-github-permissions response header on the same 403, which lists the permission and level the endpoint accepts."),
 ("Where do I see the x-accepted-github-permissions header?",
  "On the 403 response itself, so no second request is needed. You do need a client that surfaces response headers: most SDKs raise an exception carrying the status and the body and discard the rest, which is why so much time gets spent on this error with the answer already on the wire."),
 ("I added the permission and it still returns 403. Why?",
  "Because a new or widened permission on a GitHub App is pending until each installation's owner accepts it. Your settings page and GET /app both show the permission immediately; installations that have not accepted keep the old set and keep failing. Notify the installers and keep checking the endpoint rather than the settings page."),
 ("The 403 has no x-accepted-github-permissions header at all. What then?",
  "That is a different diagnosis: the endpoint does not accept installation tokens. GET /user is the standard example, since an installation has no current user. Use the App-appropriate equivalent, such as GET /installation/repositories instead of GET /user/repos, or a user-to-server token from the App's OAuth flow."),
 ("The endpoint lists two permissions. Do I need both?",
  "Sometimes one is enough. Where an endpoint offers more than one route in, holding either satisfies it, so a script that reports every unmet pair is giving you a superset. That is the safe direction for a diagnostic: it can send you to check something you did not need, but it will never tell you a permission is fine when it is not."),
],
"related": [
 ("/github/404-masking-403/", "A permission error disguised as 404 Not Found"),
 ("/github/installation-repository-selection-partial/", "An installation that covers only some repositories"),
 ("/github/saml-partial-results/", "Org lists that silently omit SSO-enforced orgs"),
],
"citations": [CITE_APP_PERMS, CITE_CHOOSING, CITE_EDIT_PERMS, CITE_APPS],
},

]
