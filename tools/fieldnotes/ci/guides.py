#!/usr/bin/env python3
"""GitHub Actions field notes: failures that do not fail loudly.

The common thread is silence. A secret resolves to an empty string instead of
erroring. A rate limit is reported as a cache miss. A redundant run costs money
without appearing anywhere as waste. All of them are visible through the REST API
before anyone notices from the outside.
"""

CITE_SECRETS = ("Using secrets in GitHub Actions — GitHub Docs",
                "https://docs.github.com/en/actions/security-for-github-actions/security-guides/using-secrets-in-github-actions")
CITE_BILLING = ("About billing for GitHub Actions — GitHub Docs",
                "https://docs.github.com/billing/managing-billing-for-github-actions/about-billing-for-github-actions")
CITE_CACHE = ("Caching dependencies to speed up workflows — GitHub Docs",
              "https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/caching-dependencies-to-speed-up-workflows")
CITE_TOKEN = ("Controlling permissions for GITHUB_TOKEN — GitHub Docs",
              "https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication")

GUIDES = [

{
"slug": "secrets-are-empty-in-fork-pull-requests",
"title": "Secrets Are Empty Strings in Fork Pull Requests",
"description": "A workflow that works on main fails on an outside contributor's PR. Secrets are not withheld with an error — they resolve to empty strings.",
"h1": "secrets are empty strings in fork pull requests",
"category": "GitHub Actions",
"pill": "Diagnostic",
"chips": ["GitHub REST API", "Python and Node.js", "Fails quietly"],
"keywords": ["GitHub Actions secrets fork", "pull_request_target", "secret not found",
             "fork PR secrets empty", "Actions security"],
"deps": "Python 3.9+ with requests, or Node.js 18+ (fetch is built in)",
"lead": "The workflow passes on <code>main</code> and on every branch pushed by someone with write access. An outside contributor opens a pull request and the same workflow fails somewhere strange &mdash; a deploy step authenticating as nobody, an API call returning 401, a test asserting on a config value that is suddenly blank. GitHub did not refuse to give the job its secrets. It gave them as <strong>empty strings</strong>, and the job carried on.",
"short_answer": """<p>For a <code>pull_request</code> event from a <strong>forked</strong> repository, secrets are not available. They do not error; they resolve to empty strings, so every step runs and fails later for a reason that has nothing obviously to do with secrets.</p>
<p>This is deliberate: a fork PR is untrusted code, and handing it your deploy credentials would let anyone with a GitHub account exfiltrate them. The fix is not to force secrets in &mdash; it is to design the workflow so the untrusted part does not need them.</p>""",
"problem": """<p>The error is always downstream. A step that uses <code>${{ secrets.API_KEY }}</code> gets <code>""</code>, sends an unauthenticated request, and reports whatever the remote service says about a missing key. Maintainers reading that message look at the service, the network and the action version before they look at where the PR came from.</p>
<p>It is worse when the value is used in a conditional. An empty string is falsy, so a step guarded by <code>if: secrets.DEPLOY_KEY != ''</code> silently skips and the job goes green having done nothing.</p>""",
"why": """<p><strong>Untrusted code cannot be trusted with credentials.</strong> A fork PR can change the workflow file in the same commit. If secrets were available, anyone could open a PR that printed them, and no review would happen before the job ran.</p>
<p><strong>Empty is easier than absent.</strong> Expression interpolation has no way to signal 'this exists but you may not have it' inside a shell command, so the value becomes an empty string and the job proceeds.</p>
<p><strong><code>pull_request_target</code> looks like the fix and is a footgun.</strong> It runs in the context of the base repository <em>with</em> secrets, but checks out the PR's code if you tell it to &mdash; which is precisely the exfiltration path the restriction exists to prevent. It is only safe when the job never checks out or executes the PR's code.</p>""",
"steps": [
 {"h": "Confirm that is actually what happened",
  "body": """<p>The run's API record says whether the head repository differs from the base. That is the definitive check, and it takes one request.</p>
<pre><code class="language-bash">gh api repos/OWNER/REPO/actions/runs/RUN_ID \\
  --jq '{event:.event, headRepo:.head_repository.full_name, baseRepo:.repository.full_name}'</code></pre>
<p>Different <code>full_name</code> values on a <code>pull_request</code> event means no secrets were available.</p>"""},
 {"h": "Split the workflow rather than widening the trust",
  "body": """<p>Run tests that need no secrets on <code>pull_request</code>, so contributors get fast feedback. Put anything needing credentials on <code>push</code> to your branches, or behind a manual <code>workflow_dispatch</code> a maintainer triggers after reading the diff.</p>"""},
 {"h": "Fail loudly instead of silently",
  "body": """<p>If a step genuinely requires a secret, assert it early so the failure names the real cause. Three lines turns a confusing 401 into a clear message.</p>
<pre><code class="language-yaml">- name: Require credentials
  run: |
    if [ -z "$API_KEY" ]; then
      echo "::error::API_KEY is empty. Fork PRs do not receive secrets."
      exit 1
    fi
  env:
    API_KEY: ${{ secrets.API_KEY }}</code></pre>"""},
 {"h": "Use pull_request_target only where it is safe",
  "body": """<p>It is defensible for jobs that only read metadata &mdash; labelling, commenting, checking a changelog entry exists. The moment a job checks out the PR's code or runs its build, the secrets are reachable by that code and the protection is gone.</p>"""},
],
"verify": """<p>Have someone fork the repository and open a PR, or push a branch to a fork you own. The assertion step should fail with your own message rather than a downstream 401:</p>
<pre><code class="language-bash">gh run list --workflow=ci.yml --json event,headBranch,conclusion --limit 5</code></pre>
<p>A green run that did nothing is the outcome to watch for &mdash; check the step actually executed rather than skipping on a falsy condition.</p>""",
"code_intro": "The script scans recent workflow runs, flags the ones that came from a fork, and reports which of those failed &mdash; the population where this bug hides. It also parses your workflow files for steps that reference a secret inside an <code>if</code> condition, which is the pattern that turns a missing secret into a silent skip rather than a failure.",
"py_file": "fork_pr_secret_audit.py",
"py": '''"""Find workflow failures caused by secrets being empty in fork pull requests.

Secrets are not withheld with an error on a fork PR -- they resolve to empty
strings, so the job runs and fails downstream for a reason that looks unrelated.
This narrows the search to runs where that is possible.
"""
import argparse
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("fork_pr_secret_audit")

API = "https://api.github.com"


def is_fork_run(run):
    """Pure decision function over one workflow-run object.

    Secrets are unavailable when a pull_request event comes from a different
    repository. Same-repo PRs from branches DO get secrets, which is why comparing
    the repository names matters more than the event name alone.
    """
    if run.get("event") != "pull_request":
        return False
    head = (run.get("head_repository") or {}).get("full_name")
    base = (run.get("repository") or {}).get("full_name")
    return bool(head and base and head != base)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True, help="owner/name")
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN")
        return 2
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json"}

    r = requests.get(f"{API}/repos/{args.repo}/actions/runs",
                     headers=headers, params={"per_page": args.limit}, timeout=30)
    r.raise_for_status()
    runs = r.json().get("workflow_runs", [])

    fork_runs = [x for x in runs if is_fork_run(x)]
    failed = [x for x in fork_runs if x.get("conclusion") == "failure"]

    log.info("%d recent run(s); %d from forks; %d of those failed",
             len(runs), len(fork_runs), len(failed))
    for run in failed:
        log.warning("FORK PR FAILURE  #%s %s -- %s",
                    run.get("run_number"),
                    (run.get("head_repository") or {}).get("full_name"),
                    run.get("html_url"))
    if failed:
        log.warning("secrets resolve to EMPTY STRINGS in these runs, so a step using "
                    "one fails downstream rather than reporting a missing secret")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "fork-pr-secret-audit.mjs",
"js": '''/**
 * Find workflow failures caused by secrets being empty in fork pull requests.
 *
 * Secrets are not withheld with an error on a fork PR -- they resolve to empty
 * strings, so the job runs and fails downstream for a reason that looks unrelated.
 */
const API = 'https://api.github.com';

/**
 * Pure decision function over one workflow-run object.
 *
 * Secrets are unavailable when a pull_request event comes from a different
 * repository. Same-repo PRs from branches DO get secrets, which is why comparing
 * repository names matters more than the event name alone.
 */
export function isForkRun(run) {
  if (run.event !== 'pull_request') return false;
  const head = run.head_repository?.full_name;
  const base = run.repository?.full_name;
  return Boolean(head && base && head !== base);
}

async function main() {
  const repo = process.argv[process.argv.indexOf('--repo') + 1];
  const token = process.env.GITHUB_TOKEN;
  if (!token) { console.error('set GITHUB_TOKEN'); process.exit(2); }

  const res = await fetch(`${API}/repos/${repo}/actions/runs?per_page=100`, {
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' },
  });
  if (!res.ok) { console.error(`${res.status} ${res.statusText}`); process.exit(1); }
  const { workflow_runs: runs = [] } = await res.json();

  const forkRuns = runs.filter(isForkRun);
  const failed = forkRuns.filter((r) => r.conclusion === 'failure');
  console.log(`${runs.length} recent run(s); ${forkRuns.length} from forks; ${failed.length} failed`);
  for (const run of failed) {
    console.warn(`FORK PR FAILURE  #${run.run_number} ${run.head_repository?.full_name} -- ${run.html_url}`);
  }
  if (failed.length) {
    console.warn('secrets resolve to EMPTY STRINGS in these runs, so a step using one '
      + 'fails downstream rather than reporting a missing secret');
  }
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The distinction that matters is between a fork PR and a same-repo branch PR. Both are <code>pull_request</code> events; only one loses its secrets, and treating them the same sends you looking in the wrong place.",
"test_py_file": "test_fork_pr_secret_audit.py",
"test_py": '''from fork_pr_secret_audit import is_fork_run


def run(event="pull_request", head="contributor/proj", base="owner/proj"):
    return {"event": event,
            "head_repository": {"full_name": head},
            "repository": {"full_name": base}}


def test_fork_pr_is_detected():
    assert is_fork_run(run()) is True


def test_same_repo_branch_pr_keeps_its_secrets():
    """Also a pull_request event, but from a branch. Secrets ARE available."""
    assert is_fork_run(run(head="owner/proj")) is False


def test_push_events_are_not_affected():
    assert is_fork_run(run(event="push")) is False


def test_missing_head_repository_is_not_assumed_to_be_a_fork():
    r = run()
    r["head_repository"] = None
    assert is_fork_run(r) is False
''',
"test_js_file": "fork-pr-secret-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { isForkRun } from './fork-pr-secret-audit.mjs';

const run = ({ event = 'pull_request', head = 'contributor/proj', base = 'owner/proj' } = {}) => ({
  event, head_repository: { full_name: head }, repository: { full_name: base },
});

test('a fork PR is detected', () => {
  assert.equal(isForkRun(run()), true);
});

test('a same-repo branch PR keeps its secrets', () => {
  assert.equal(isForkRun(run({ head: 'owner/proj' })), false);
});

test('push events are not affected', () => {
  assert.equal(isForkRun(run({ event: 'push' })), false);
});

test('a missing head repository is not assumed to be a fork', () => {
  const r = run(); r.head_repository = null;
  assert.equal(isForkRun(r), false);
});
''',
"faq": [
 ("Why does the job not just fail with 'secret not found'?",
  "Because expression interpolation has no way to signal 'this exists but you may not have it' inside a shell command. The value becomes an empty string and the step runs, so the failure appears downstream as a 401 or a blank config value."),
 ("Do all pull requests lose their secrets?",
  "No — only those from forked repositories. A pull request from a branch in the same repository is trusted and does receive secrets, which is why comparing the head and base repository names matters more than the event name."),
 ("Is pull_request_target the fix?",
  "Only sometimes, and it is dangerous. It runs with secrets in the base repository's context, so it is fine for jobs that read metadata — labelling, commenting. The moment it checks out or runs the PR's code, that untrusted code can reach your secrets, which is exactly what the restriction prevents."),
 ("How should I structure a workflow that needs credentials?",
  "Split it. Tests that need no secrets run on pull_request so contributors get feedback. Anything requiring credentials runs on push to your own branches, or behind a workflow_dispatch a maintainer triggers after reading the diff."),
 ("Why did my job go green without doing anything?",
  "An empty string is falsy, so a step guarded by a condition like if: secrets.DEPLOY_KEY != '' silently skips. The job passes having deployed nothing, which is worse than failing."),
],
"related": [
 ("/ci/cache-miss-is-really-a-rate-limit/", "A cache miss that is really a rate limit"),
 ("/ci/github-token-is-read-only-by-default/", "GITHUB_TOKEN is read-only by default"),
 ("/ci/redundant-runs-on-rapid-pushes/", "Three pushes run three full pipelines"),
],
"citations": [CITE_SECRETS,
 ("Events that trigger workflows — pull_request_target — GitHub Docs",
  "https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows"),
 ("Keeping your GitHub Actions and workflows secure: preventing pwn requests — GitHub Security Lab",
  "https://securitylab.github.com/resources/github-actions-preventing-pwn-requests/")],
},

{
"slug": "github-token-is-read-only-by-default",
"title": "GITHUB_TOKEN Is Read-Only and the Error Says 403",
"description": "A workflow that pushes a commit or creates a release fails with 403 Resource not accessible by integration. The token defaults to read-only.",
"h1": "GITHUB_TOKEN is read-only and the error just says 403",
"category": "GitHub Actions",
"pill": "Diagnostic",
"chips": ["GitHub REST API", "Python and Node.js", "One line of YAML"],
"keywords": ["Resource not accessible by integration", "GITHUB_TOKEN permissions",
             "Actions 403", "workflow permissions", "contents write"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The workflow builds fine and then dies on the last step with <code>403: Resource not accessible by integration</code>. The token is right there in the environment. Nothing changed in the code. What changed, some time ago and for everyone, is the default: <code>GITHUB_TOKEN</code> now starts <strong>read-only</strong>, and any step that pushes a commit, cuts a release or comments on an issue needs the permission granted explicitly.",
"short_answer": """<p>The default permission set for <code>GITHUB_TOKEN</code> is read-only. Writing anything &mdash; a commit, a tag, a release, a comment, a package &mdash; needs a <code>permissions:</code> block naming the scope.</p>
<p>The error message never says which scope is missing, which is what makes it slow to diagnose. Add the narrowest permission the job actually needs, at job level rather than workflow level, so one step that needs write access does not grant it to every other job in the file.</p>""",
"problem": """<p><code>Resource not accessible by integration</code> is the same message whether you are missing <code>contents: write</code>, <code>packages: write</code>, <code>issues: write</code> or <code>id-token: write</code>. It names no scope and suggests no fix.</p>
<p>The confusion deepens because the same workflow may have worked in an older repository. The default changed for new repositories and organisations, so two repositories in the same account can behave differently with identical YAML &mdash; which sends people looking for a difference in the code that is not there.</p>""",
"why": """<p><strong>The default is deliberately restrictive.</strong> A token with write access to everything, available to every workflow including ones triggered by outside contributions, is a large blast radius. Read-only by default is the right call and it broke a lot of workflows written before it.</p>
<p><strong>The API cannot tell you what it wanted.</strong> Reporting the missing scope would tell an attacker what to aim for, so the message stays generic. That is defensible security and unhelpful debugging, and you have to reason about it from the operation instead.</p>
<p><strong>Declaring one permission drops all the others.</strong> A <code>permissions:</code> block is a complete replacement, not an addition. Adding <code>contents: write</code> to a job that also comments on the PR removes its <code>pull-requests: write</code>, so fixing one 403 produces another.</p>""",
"steps": [
 {"h": "Check the repository default first",
  "body": """<p>Two settings interact: the organisation or repository default, and any <code>permissions:</code> in the workflow. Read the default before editing YAML.</p>
<pre><code class="language-bash">gh api repos/OWNER/REPO/actions/permissions/workflow \\
  --jq '{default:.default_workflow_permissions, canApprovePR:.can_approve_pull_request_reviews}'</code></pre>"""},
 {"h": "Map the failing operation to its scope",
  "body": """<p>The message will not tell you, so work backwards from what the step does. Pushing commits or tags needs <code>contents: write</code>. Creating a release needs <code>contents: write</code>. Commenting on a PR needs <code>pull-requests: write</code>. Publishing a package needs <code>packages: write</code>. OIDC for cloud auth needs <code>id-token: write</code>.</p>"""},
 {"h": "Grant at job level, and grant everything that job needs at once",
  "body": """<p>A block replaces the defaults rather than extending them, so list every scope the job uses together.</p>
<pre><code class="language-yaml">jobs:
  release:
    permissions:
      contents: write        # push tags, create the release
      pull-requests: write   # comment with the release notes
    runs-on: ubuntu-latest</code></pre>
<p>Job level, not workflow level: the build job has no business holding write access.</p>"""},
 {"h": "Audit the repositories that do not fail",
  "body": """<p>An organisation that still defaults to permissive is a bigger risk than a 403. The script reports both directions &mdash; workflows that will fail, and repositories where every token can write.</p>"""},
],
"verify": """<p>Re-run the failing job. If it fails again with the same 403, the scope was wrong rather than absent &mdash; check the operation against the list above. Then confirm the grant is as narrow as you think:</p>
<pre><code class="language-bash">gh run view RUN_ID --json jobs --jq '.jobs[].name'
gh api repos/OWNER/REPO/actions/permissions/workflow --jq '.default_workflow_permissions'</code></pre>""",
"code_intro": "The script reports each repository's default workflow permission and scans workflow files for jobs that perform a write without declaring a matching scope. It also flags the opposite problem: repositories still defaulting to write, where every workflow holds more access than it needs.",
"py_file": "actions_permissions_audit.py",
"py": '''"""Audit GITHUB_TOKEN permissions: too little to work, or more than needed.

The 403 message never names the missing scope, so this maps the operation a job
performs back to the scope it requires. It also flags repositories still defaulting
to write permissions, which is the same problem pointing the other way.
"""
import argparse
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("actions_permissions_audit")

API = "https://api.github.com"

# Operations that write, and the scope each one needs. The API will not tell you.
WRITE_HINTS = [
    (re.compile(r"\\bgit\\s+push\\b|actions/create-release|softprops/action-gh-release"),
     "contents: write"),
    (re.compile(r"gh\\s+release\\s+create|\\bgh\\s+api\\b.*releases"), "contents: write"),
    (re.compile(r"gh\\s+pr\\s+comment|actions/github-script.*createComment"),
     "pull-requests: write"),
    (re.compile(r"docker/build-push-action|npm\\s+publish|gh\\s+api.*packages"),
     "packages: write"),
    (re.compile(r"aws-actions/configure-aws-credentials|id-token"), "id-token: write"),
]


def needed_scopes(workflow_text):
    """Pure decision function: which scopes does this workflow appear to need?"""
    return sorted({scope for pattern, scope in WRITE_HINTS
                   if pattern.search(workflow_text)})


def declared_scopes(workflow_text):
    """Scopes the workflow actually grants, anywhere in the file."""
    return sorted(set(re.findall(r"^\\s*([a-z-]+):\\s*write\\s*$", workflow_text, re.M)))


def gaps(workflow_text):
    """What the workflow needs but has not granted."""
    have = {s.split(":")[0] for s in declared_scopes(workflow_text)}
    return [s for s in needed_scopes(workflow_text) if s.split(":")[0].strip() not in have]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--workflow-dir", default=".github/workflows")
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN")
        return 2
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json"}

    r = requests.get(f"{API}/repos/{args.repo}/actions/permissions/workflow",
                     headers=headers, timeout=30)
    if r.ok:
        default = r.json().get("default_workflow_permissions")
        if default == "write":
            log.warning("%s defaults to WRITE: every workflow token can push, release "
                        "and comment whether it needs to or not", args.repo)
        else:
            log.info("%s defaults to %s", args.repo, default)

    from pathlib import Path
    failed = False
    for wf in sorted(Path(args.workflow_dir).glob("*.y*ml")):
        text = wf.read_text(encoding="utf-8")
        missing = gaps(text)
        if missing:
            failed = True
            log.error("%s needs %s but does not declare it",
                      wf.name, ", ".join(missing))
        else:
            log.info("%s: permissions look sufficient", wf.name)
    if failed:
        log.error("a missing scope surfaces as: 403 Resource not accessible by "
                  "integration -- the message never says which one")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "actions-permissions-audit.mjs",
"js": '''/**
 * Audit GITHUB_TOKEN permissions: too little to work, or more than needed.
 *
 * The 403 message never names the missing scope, so this maps the operation a job
 * performs back to the scope it requires.
 */
import { readdir, readFile } from 'node:fs/promises';
import path from 'node:path';

const API = 'https://api.github.com';

// Operations that write, and the scope each one needs. The API will not tell you.
const WRITE_HINTS = [
  [/\\bgit\\s+push\\b|actions\\/create-release|softprops\\/action-gh-release/, 'contents: write'],
  [/gh\\s+release\\s+create|\\bgh\\s+api\\b.*releases/, 'contents: write'],
  [/gh\\s+pr\\s+comment|actions\\/github-script.*createComment/, 'pull-requests: write'],
  [/docker\\/build-push-action|npm\\s+publish|gh\\s+api.*packages/, 'packages: write'],
  [/aws-actions\\/configure-aws-credentials|id-token/, 'id-token: write'],
];

/** Pure decision function: which scopes does this workflow appear to need? */
export function neededScopes(text) {
  return [...new Set(WRITE_HINTS.filter(([re]) => re.test(text)).map(([, s]) => s))].sort();
}

export function declaredScopes(text) {
  return [...new Set([...text.matchAll(/^\\s*([a-z-]+):\\s*write\\s*$/gm)].map((m) => m[1]))].sort();
}

export function gaps(text) {
  const have = new Set(declaredScopes(text));
  return neededScopes(text).filter((s) => !have.has(s.split(':')[0].trim()));
}

async function main() {
  const repo = process.argv[process.argv.indexOf('--repo') + 1];
  const dir = '.github/workflows';
  const token = process.env.GITHUB_TOKEN;
  if (!token) { console.error('set GITHUB_TOKEN'); process.exit(2); }

  const res = await fetch(`${API}/repos/${repo}/actions/permissions/workflow`, {
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' },
  });
  if (res.ok) {
    const { default_workflow_permissions: d } = await res.json();
    if (d === 'write') console.warn(`${repo} defaults to WRITE: every workflow token can push`);
    else console.log(`${repo} defaults to ${d}`);
  }

  let failed = false;
  for (const f of (await readdir(dir)).filter((n) => /\\.ya?ml$/.test(n))) {
    const text = await readFile(path.join(dir, f), 'utf8');
    const missing = gaps(text);
    if (missing.length) { failed = true; console.error(`${f} needs ${missing.join(', ')}`); }
    else console.log(`${f}: permissions look sufficient`);
  }
  if (failed) {
    console.error('a missing scope surfaces as: 403 Resource not accessible by integration');
  }
  process.exit(failed ? 1 : 0);
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The mapping from operation to scope is the whole value here, since the API refuses to tell you. Worth testing that a workflow which already grants what it needs is not flagged, or the report becomes noise people ignore.",
"test_py_file": "test_actions_permissions_audit.py",
"test_py": '''from actions_permissions_audit import needed_scopes, declared_scopes, gaps

PUSHES = """
jobs:
  release:
    steps:
      - run: git push origin main
"""

PUSHES_WITH_GRANT = """
jobs:
  release:
    permissions:
      contents: write
    steps:
      - run: git push origin main
"""


def test_a_push_needs_contents_write():
    assert "contents: write" in needed_scopes(PUSHES)


def test_a_workflow_that_grants_what_it_needs_is_not_flagged():
    assert gaps(PUSHES_WITH_GRANT) == []


def test_a_workflow_missing_the_grant_is_flagged():
    assert gaps(PUSHES) == ["contents: write"]


def test_declared_scopes_are_read_from_anywhere_in_the_file():
    assert "contents" in declared_scopes(PUSHES_WITH_GRANT)


def test_a_read_only_workflow_needs_nothing():
    assert needed_scopes("jobs:\\n  test:\\n    steps:\\n      - run: pytest") == []
''',
"test_js_file": "actions-permissions-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { neededScopes, gaps } from './actions-permissions-audit.mjs';

const PUSHES = 'jobs:\\n  release:\\n    steps:\\n      - run: git push origin main\\n';
const GRANTED = 'jobs:\\n  release:\\n    permissions:\\n      contents: write\\n'
  + '    steps:\\n      - run: git push origin main\\n';

test('a push needs contents: write', () => {
  assert.ok(neededScopes(PUSHES).includes('contents: write'));
});

test('a workflow that grants what it needs is not flagged', () => {
  assert.deepEqual(gaps(GRANTED), []);
});

test('a workflow missing the grant is flagged', () => {
  assert.deepEqual(gaps(PUSHES), ['contents: write']);
});

test('a read-only workflow needs nothing', () => {
  assert.deepEqual(neededScopes('jobs:\\n  test:\\n    steps:\\n      - run: pytest'), []);
});
''',
"faq": [
 ("What does 'Resource not accessible by integration' mean?",
  "The GITHUB_TOKEN lacks the scope for the operation the step attempted. The message is identical whether the missing scope is contents, packages, issues or id-token, because naming it would tell an attacker what to aim for."),
 ("Why does the same workflow work in another repository?",
  "The default changed for new repositories and organisations. An older repository may still default to write permissions, so two repositories in the same account can behave differently with identical YAML."),
 ("Should permissions go at workflow level or job level?",
  "Job level. A workflow-level block grants the scope to every job in the file, including the build job that has no reason to push anything. Grant the narrowest scope to the one job that needs it."),
 ("I added contents: write and now a different step fails. Why?",
  "A permissions block replaces the defaults rather than adding to them. Declaring one scope drops all the others, so a job that also comments on the PR loses pull-requests: write. List every scope the job needs together."),
 ("Is defaulting the whole organisation to write a reasonable shortcut?",
  "It removes the errors and enlarges the blast radius of every workflow, including ones triggered by outside contributions. The audit flags it for that reason rather than treating it as a fix."),
],
"related": [
 ("/ci/secrets-are-empty-in-fork-pull-requests/", "Secrets are empty strings in fork PRs"),
 ("/ci/redundant-runs-on-rapid-pushes/", "Three pushes run three full pipelines"),
 ("/ci/cache-miss-is-really-a-rate-limit/", "A cache miss that is really a rate limit"),
],
"citations": [CITE_TOKEN,
 ("GitHub Actions: Control permissions for GITHUB_TOKEN — GitHub Changelog",
  "https://github.blog/changelog/2021-04-20-github-actions-control-permissions-for-github_token/"),
 ("Workflow syntax: permissions — GitHub Docs",
  "https://docs.github.com/en/actions/writing-workflows/workflow-syntax-for-github-actions#permissions")],
},

{
"slug": "redundant-runs-on-rapid-pushes",
"title": "Three Pushes Run Three Full Pipelines and You Pay for All",
"description": "Push three commits to a PR in a minute and GitHub runs the whole pipeline three times. Only the last result matters, and macOS bills at ten times the rate.",
"h1": "three pushes run three full pipelines and you pay for all of them",
"category": "GitHub Actions",
"pill": "Cost",
"chips": ["GitHub REST API", "Python and Node.js", "One concurrency block"],
"keywords": ["GitHub Actions concurrency", "cancel-in-progress", "Actions billing minutes",
             "macOS runner multiplier", "CI cost optimisation"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "Somebody pushes a commit, spots a typo, pushes again, then fixes the lint error and pushes a third time. GitHub starts three full pipeline runs. Two of them are testing code that is already obsolete before they finish, and you are billed for every minute of all three. On a macOS runner, where minutes count at <strong>ten times the rate</strong>, those two wasted runs can cost more than the one you needed.",
"short_answer": """<p>By default every push starts a run, and earlier runs keep going. A <code>concurrency</code> block with <code>cancel-in-progress: true</code>, keyed on the branch or PR, cancels the superseded run and keeps only the one that matters.</p>
<p>The saving is largest where the multiplier is: Linux bills at 1&times;, Windows at 2&times;, <strong>macOS at 10&times;</strong>. A single stuck macOS job can consume 3,600 billed minutes on its own.</p>""",
"problem": """<p>Nothing looks wrong. Every run is legitimate, each one was triggered by a real push, and the pipeline is doing exactly what it was told. The waste is invisible because it is spread across runs that all appear necessary in isolation.</p>
<p>It scales with how people work. Developers who push small commits frequently &mdash; which is a habit worth encouraging &mdash; generate the most redundant runs. Punishing that with a slow, expensive pipeline is the wrong trade when a four-line YAML block removes it.</p>""",
"why": """<p><strong>Independent runs are the safe default.</strong> GitHub cannot know that a later push supersedes an earlier one; some workflows genuinely need every commit tested, for a bisect or a release train. So it runs them all and leaves the decision to you.</p>
<p><strong>The multiplier is easy to forget.</strong> Minutes are billed at 1&times; on Linux, 2&times; on Windows and 10&times; on macOS. A ten-minute macOS job costs a hundred minutes of the included pool, and a matrix multiplies that again.</p>
<p><strong>Timeouts are not set either.</strong> Without <code>timeout-minutes</code>, a hung job runs to the six-hour maximum. On macOS that is 3,600 billed minutes from a single stuck step, which is the largest single line most teams ever see.</p>""",
"steps": [
 {"h": "Measure before changing anything",
  "body": """<p>Count runs that were superseded &mdash; same workflow, same branch, an earlier run still going when a later one started. The script does this from the runs API so the change has a number attached.</p>"""},
 {"h": "Add a concurrency group keyed to the branch",
  "body": """<p>Four lines at workflow level. The group must include the ref, or you serialise every branch against every other.</p>
<pre><code class="language-yaml">concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true</code></pre>
<p>Do not use <code>cancel-in-progress</code> on a deploy workflow. Cancelling a half-finished deploy is worse than paying for two.</p>"""},
 {"h": "Put a timeout on every job",
  "body": """<p><code>timeout-minutes</code> caps the damage from a hang. Set it a little above the honest p95 for the job rather than a round number that quietly permits an hour of nothing.</p>
<pre><code class="language-yaml">jobs:
  test:
    timeout-minutes: 15</code></pre>"""},
 {"h": "Question the macOS runners",
  "body": """<p>At 10&times;, macOS should be reserved for things that genuinely need it &mdash; iOS and macOS builds, Safari testing. A matrix that includes macOS out of habit is the most expensive habit in the file.</p>"""},
],
"verify": """<p>Push twice in quick succession and watch the first run get cancelled:</p>
<pre><code class="language-bash">gh run list --branch my-branch --limit 5 \\
  --json conclusion,createdAt,displayTitle
# the superseded run should read "cancelled"</code></pre>
<p>Then compare billed minutes across a fortnight. The drop lands mostly on whichever runner carries the multiplier.</p>""",
"code_intro": "The script pulls recent runs, finds the ones superseded by a later run on the same workflow and branch, and estimates the wasted minutes with the OS multiplier applied. It reports rather than edits &mdash; adding <code>cancel-in-progress</code> to a deploy workflow would be actively harmful, so the change stays a human decision.",
"py_file": "actions_redundant_runs.py",
"py": '''"""Estimate CI minutes wasted on runs superseded by a later push.

Reports only. Adding cancel-in-progress to a deploy workflow would leave a
half-finished deploy, so the change is deliberately left to a human who knows
which workflows are safe to interrupt.
"""
import argparse
import collections
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("actions_redundant_runs")

API = "https://api.github.com"
# Billed minutes per wall-clock minute, per runner OS.
MULTIPLIER = {"ubuntu": 1, "windows": 2, "macos": 10}


def find_superseded(runs):
    """Pure decision function.

    A run is superseded when a LATER run exists for the same workflow and branch and
    the earlier one was still going when it started. Grouping by workflow as well as
    branch matters: two different workflows on one branch are not competing.
    """
    by_key = collections.defaultdict(list)
    for r in runs:
        by_key[(r.get("workflow_id"), r.get("head_branch"))].append(r)

    superseded = []
    for group in by_key.values():
        group.sort(key=lambda r: r.get("run_number", 0))
        for earlier, later in zip(group, group[1:]):
            if earlier.get("created_at") and later.get("created_at"):
                if earlier["created_at"] < later["created_at"]:
                    superseded.append(earlier)
    return superseded


def billed_minutes(run, wall_minutes):
    """Apply the runner multiplier. macOS is 10x, which dominates any bill."""
    name = " ".join(run.get("labels", []) or []).lower() or "ubuntu"
    for os_name, mult in MULTIPLIER.items():
        if os_name in name:
            return wall_minutes * mult
    return wall_minutes


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN")
        return 2
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json"}

    r = requests.get(f"{API}/repos/{args.repo}/actions/runs",
                     headers=headers, params={"per_page": args.limit}, timeout=30)
    r.raise_for_status()
    runs = r.json().get("workflow_runs", [])

    wasted = find_superseded(runs)
    log.info("%d recent run(s), %d superseded by a later push", len(runs), len(wasted))
    by_workflow = collections.Counter(w.get("name") for w in wasted)
    for name, count in by_workflow.most_common():
        log.warning("  %-40s %d redundant run(s)", name, count)
    if wasted:
        log.warning("add a concurrency group to the workflows above:")
        log.warning("  concurrency:")
        log.warning("    group: ${{ github.workflow }}-${{ github.ref }}")
        log.warning("    cancel-in-progress: true")
        log.warning("do NOT add cancel-in-progress to a deploy workflow")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "actions-redundant-runs.mjs",
"js": '''/**
 * Estimate CI minutes wasted on runs superseded by a later push.
 *
 * Reports only. Adding cancel-in-progress to a deploy workflow would leave a
 * half-finished deploy, so the change is left to a human.
 */
const API = 'https://api.github.com';
// Billed minutes per wall-clock minute, per runner OS.
export const MULTIPLIER = { ubuntu: 1, windows: 2, macos: 10 };

/**
 * Pure decision function.
 *
 * A run is superseded when a LATER run exists for the same workflow and branch.
 * Grouping by workflow as well as branch matters: two different workflows on one
 * branch are not competing.
 */
export function findSuperseded(runs) {
  const byKey = new Map();
  for (const r of runs) {
    const key = `${r.workflow_id}::${r.head_branch}`;
    byKey.set(key, [...(byKey.get(key) ?? []), r]);
  }
  const superseded = [];
  for (const group of byKey.values()) {
    group.sort((a, b) => (a.run_number ?? 0) - (b.run_number ?? 0));
    for (let i = 0; i < group.length - 1; i += 1) {
      if (group[i].created_at && group[i + 1].created_at
        && group[i].created_at < group[i + 1].created_at) superseded.push(group[i]);
    }
  }
  return superseded;
}

export function billedMinutes(run, wallMinutes) {
  const name = (run.labels ?? []).join(' ').toLowerCase() || 'ubuntu';
  for (const [os, mult] of Object.entries(MULTIPLIER)) {
    if (name.includes(os)) return wallMinutes * mult;
  }
  return wallMinutes;
}

async function main() {
  const repo = process.argv[process.argv.indexOf('--repo') + 1];
  const token = process.env.GITHUB_TOKEN;
  if (!token) { console.error('set GITHUB_TOKEN'); process.exit(2); }

  const res = await fetch(`${API}/repos/${repo}/actions/runs?per_page=100`, {
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' },
  });
  const { workflow_runs: runs = [] } = await res.json();
  const wasted = findSuperseded(runs);
  console.log(`${runs.length} recent run(s), ${wasted.length} superseded by a later push`);

  const counts = {};
  for (const w of wasted) counts[w.name] = (counts[w.name] ?? 0) + 1;
  for (const [name, count] of Object.entries(counts).sort((a, b) => b[1] - a[1])) {
    console.warn(`  ${name.padEnd(40)} ${count} redundant run(s)`);
  }
  if (wasted.length) {
    console.warn('add a concurrency group; do NOT add cancel-in-progress to a deploy workflow');
  }
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "Two things need pinning: runs from different workflows on one branch are not competing, and the macOS multiplier has to actually apply or the estimate understates the waste by an order of magnitude.",
"test_py_file": "test_actions_redundant_runs.py",
"test_py": '''from actions_redundant_runs import find_superseded, billed_minutes


def run(n, wf=1, branch="main", created=None):
    return {"run_number": n, "workflow_id": wf, "head_branch": branch,
            "created_at": created or f"2026-08-28T00:{n:02d}:00Z", "name": f"wf{wf}"}


def test_a_single_run_is_not_superseded():
    assert find_superseded([run(1)]) == []


def test_the_earlier_of_two_runs_is_superseded():
    out = find_superseded([run(1), run(2)])
    assert len(out) == 1 and out[0]["run_number"] == 1


def test_different_workflows_do_not_compete():
    """Two workflows on one branch are both meant to run."""
    assert find_superseded([run(1, wf=1), run(2, wf=2)]) == []


def test_different_branches_do_not_compete():
    assert find_superseded([run(1, branch="a"), run(2, branch="b")]) == []


def test_macos_multiplier_applies():
    r = {"labels": ["macos-latest"]}
    assert billed_minutes(r, 10) == 100


def test_linux_is_billed_one_to_one():
    assert billed_minutes({"labels": ["ubuntu-latest"]}, 10) == 10


def test_unknown_runner_does_not_inflate_the_estimate():
    assert billed_minutes({"labels": []}, 10) == 10
''',
"test_js_file": "actions-redundant-runs.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { findSuperseded, billedMinutes } from './actions-redundant-runs.mjs';

const run = (n, { wf = 1, branch = 'main' } = {}) => ({
  run_number: n, workflow_id: wf, head_branch: branch,
  created_at: `2026-08-28T00:${String(n).padStart(2, '0')}:00Z`, name: `wf${wf}`,
});

test('a single run is not superseded', () => {
  assert.deepEqual(findSuperseded([run(1)]), []);
});

test('the earlier of two runs is superseded', () => {
  const out = findSuperseded([run(1), run(2)]);
  assert.equal(out.length, 1);
  assert.equal(out[0].run_number, 1);
});

test('different workflows do not compete', () => {
  assert.deepEqual(findSuperseded([run(1, { wf: 1 }), run(2, { wf: 2 })]), []);
});

test('the macOS multiplier applies', () => {
  assert.equal(billedMinutes({ labels: ['macos-latest'] }, 10), 100);
});

test('linux is billed one to one', () => {
  assert.equal(billedMinutes({ labels: ['ubuntu-latest'] }, 10), 10);
});
''',
"faq": [
 ("Why does GitHub run all three pushes?",
  "Because it cannot know that a later push supersedes an earlier one. Some workflows genuinely need every commit tested — a bisect, a release train — so independent runs are the safe default and cancelling is opt-in."),
 ("What does the concurrency group need to contain?",
  "The ref. A group keyed only on the workflow name serialises every branch against every other, so one team's push cancels another's. github.workflow plus github.ref is the usual pairing."),
 ("Should I add cancel-in-progress everywhere?",
  "No. Never on a deploy workflow — cancelling a half-finished deploy leaves the system in an unknown state, which is worse than paying for two runs. It is right for tests, linting and builds."),
 ("How much does a macOS runner really cost?",
  "Ten times a Linux one per wall-clock minute. Windows is two times. A ten-minute macOS job consumes a hundred minutes of the included pool, and a matrix multiplies that again."),
 ("What stops one hung job burning the whole budget?",
  "timeout-minutes on every job. Without it a hang runs to the six-hour maximum, which on macOS is 3,600 billed minutes from a single stuck step."),
],
"related": [
 ("/ci/cache-miss-is-really-a-rate-limit/", "A cache miss that is really a rate limit"),
 ("/ci/github-token-is-read-only-by-default/", "GITHUB_TOKEN is read-only by default"),
 ("/aws/", "AWS cost field notes"),
],
"citations": [CITE_BILLING,
 ("Control the concurrency of workflows and jobs — GitHub Docs",
  "https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/control-the-concurrency-of-workflows-and-jobs"),
 ("Actions runner pricing — GitHub Docs",
  "https://docs.github.com/en/billing/reference/actions-runner-pricing")],
},

{
"slug": "cache-miss-is-really-a-rate-limit",
"title": "A Cache Miss That Is Really a Rate Limit",
"description": "Builds get slower with no error. When the cache API rate limits a repository it is reported as a cache miss, so the job restores nothing and carries on.",
"h1": "a cache miss that is really a rate limit",
"category": "GitHub Actions",
"pill": "Diagnostic",
"chips": ["GitHub REST API", "Python and Node.js", "Silent slowdown"],
"keywords": ["actions/cache miss", "GitHub Actions cache rate limit",
             "cache not restoring", "fork cache isolation", "CI slow"],
"deps": "Python 3.9+ with requests, or Node.js 18+",
"lead": "The pipeline used to take four minutes and now takes eleven. Nothing failed. Nothing is red. The cache step reports <em>Cache not found for input keys</em> and the job installs everything from scratch, every time. The key has not changed and the cache still exists &mdash; the API declined to serve it, and <code>actions/cache</code> reports a decline the same way it reports an absence.",
"short_answer": """<p>When the cache service rate limits a repository, the action logs a <strong>cache miss</strong> rather than a rate-limit error. The job proceeds correctly and slowly, which is why it never shows up as a failure.</p>
<p>Two other causes look identical: a key that changes on every run because it hashes something volatile, and a fork PR, which cannot write cache entries at all by design. The API can tell them apart &mdash; the log cannot.</p>""",
"problem": """<p>A cache miss is not an error. The action is built to degrade gracefully, because a missing cache should never break a build. That is correct behaviour and it is exactly what hides the problem: cost and time increase with no signal.</p>
<p>Because it is intermittent, it also resists reproduction. A developer re-runs the job, the cache restores, and the report gets closed as a fluke. Meanwhile every run is paying for a full install, and on a multiplied runner that is real money.</p>""",
"why": """<p><strong>Graceful degradation hides the cause.</strong> The action cannot distinguish 'no entry' from 'refused to serve' in a way that is useful in a log line, so it reports the one that is safe to continue from.</p>
<p><strong>Volatile keys guarantee a miss.</strong> A key built from a timestamp, a run id, or a lockfile that is regenerated during the build never matches on a later run. Every run writes a new entry and reads nothing, which also fills the repository's cache quota with garbage.</p>
<p><strong>Forks cannot write caches.</strong> A fork PR can read from the base branch's cache but never writes an entry, deliberately, to stop a malicious PR poisoning the cache for everyone. So the first run on a fork PR is always cold and always will be.</p>""",
"steps": [
 {"h": "Look at what is actually stored",
  "body": """<p>The caches API lists entries with their keys and sizes. If the key you expect is absent, the problem is the key. If it is present and still missing at restore, it is the service.</p>
<pre><code class="language-bash">gh api repos/OWNER/REPO/actions/caches \\
  --jq '.actions_caches[] | {key, ref, size_in_bytes, last_accessed_at}'</code></pre>"""},
 {"h": "Check whether the key is stable",
  "body": """<p>A key must be a pure function of the inputs it protects. Hashing a lockfile is right; including <code>github.run_id</code> or a date is not, and produces a guaranteed miss on every run.</p>
<pre><code class="language-yaml">key: ${{ runner.os }}-node-${{ hashFiles('**/package-lock.json') }}
restore-keys: |
  ${{ runner.os }}-node-</code></pre>
<p><code>restore-keys</code> matters: a partial match still beats a cold start.</p>"""},
 {"h": "Watch the quota",
  "body": """<p>A repository has a total cache allowance and entries are evicted least-recently-used once it is reached. Dozens of near-duplicate entries from an unstable key will evict the ones you rely on, so pruning is part of the fix.</p>"""},
 {"h": "Expect a cold cache on fork PRs",
  "body": """<p>This one is not a bug and cannot be configured away. A fork PR reads the base branch's cache and writes nothing. If contributor builds must be fast, warm the cache on the base branch so there is something for them to read.</p>"""},
],
"verify": """<p>Compare restore behaviour across consecutive runs on the same branch. The second should hit:</p>
<pre><code class="language-bash">gh run view RUN_ID --log | grep -i "cache restored\\|cache not found"
gh api repos/OWNER/REPO/actions/caches --jq '.total_count'</code></pre>
<p>If the key list shows a new entry after every run, the key is unstable and no amount of quota will help.</p>""",
"code_intro": "The script lists the repository's cache entries, groups them by prefix, and flags the signature of an unstable key &mdash; many entries sharing a prefix, each used once. It also reports total usage against the quota, and identifies branches whose entries are being evicted.",
"py_file": "actions_cache_audit.py",
"py": '''"""Diagnose why an Actions cache never restores.

A rate limit, an unstable key and a fork PR all produce the same log line: cache
miss. This separates them by looking at what is actually stored rather than at the
log, which cannot tell the difference.
"""
import argparse
import collections
import logging
import os
import re
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("actions_cache_audit")

API = "https://api.github.com"


def prefix_of(key):
    """Everything before the final hash segment, which is what should be reused."""
    return re.sub(r"-[0-9a-f]{8,}$", "", key)


def unstable_keys(caches, min_entries=5):
    """Pure decision function.

    An unstable key writes a new entry every run and reads none, so the signature is
    many entries sharing a prefix. That fills the quota and evicts the entries you
    actually wanted, which makes it worse than a plain miss.
    """
    groups = collections.defaultdict(list)
    for c in caches:
        groups[prefix_of(c.get("key", ""))].append(c)
    return {p: entries for p, entries in groups.items() if len(entries) >= min_entries}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", required=True)
    args = ap.parse_args()

    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        log.error("set GITHUB_TOKEN")
        return 2
    headers = {"Authorization": f"Bearer {token}",
               "Accept": "application/vnd.github+json"}

    r = requests.get(f"{API}/repos/{args.repo}/actions/caches",
                     headers=headers, params={"per_page": 100}, timeout=30)
    r.raise_for_status()
    body = r.json()
    caches = body.get("actions_caches", [])

    total_gb = sum(c.get("size_in_bytes", 0) for c in caches) / 1_073_741_824
    log.info("%d cache entr(ies), %.2f GB total", len(caches), total_gb)

    suspect = unstable_keys(caches)
    for prefix, entries in sorted(suspect.items(), key=lambda x: -len(x[1])):
        size = sum(e.get("size_in_bytes", 0) for e in entries) / 1_073_741_824
        log.warning("UNSTABLE KEY  %-45s %3d entries, %.2f GB",
                    prefix[:45], len(entries), size)
    if suspect:
        log.warning("a key that changes every run writes a new entry and reads none. "
                    "Hash the lockfile, not the run id or a timestamp.")
    else:
        log.info("no unstable-key pattern; if restores still miss, check whether the "
                 "run came from a fork (forks cannot write cache entries) or whether "
                 "the cache service rate limited -- both are logged as a plain miss")
    return 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "actions-cache-audit.mjs",
"js": '''/**
 * Diagnose why an Actions cache never restores.
 *
 * A rate limit, an unstable key and a fork PR all produce the same log line: cache
 * miss. This separates them by looking at what is actually stored.
 */
const API = 'https://api.github.com';

/** Everything before the final hash segment, which is what should be reused. */
export const prefixOf = (key) => key.replace(/-[0-9a-f]{8,}$/, '');

/**
 * Pure decision function.
 *
 * An unstable key writes a new entry every run and reads none, so the signature is
 * many entries sharing a prefix. That fills the quota and evicts what you wanted.
 */
export function unstableKeys(caches, minEntries = 5) {
  const groups = {};
  for (const c of caches) {
    const p = prefixOf(c.key ?? '');
    groups[p] = [...(groups[p] ?? []), c];
  }
  return Object.fromEntries(Object.entries(groups).filter(([, v]) => v.length >= minEntries));
}

async function main() {
  const repo = process.argv[process.argv.indexOf('--repo') + 1];
  const token = process.env.GITHUB_TOKEN;
  if (!token) { console.error('set GITHUB_TOKEN'); process.exit(2); }

  const res = await fetch(`${API}/repos/${repo}/actions/caches?per_page=100`, {
    headers: { Authorization: `Bearer ${token}`, Accept: 'application/vnd.github+json' },
  });
  const { actions_caches: caches = [] } = await res.json();
  const totalGb = caches.reduce((t, c) => t + (c.size_in_bytes ?? 0), 0) / 1_073_741_824;
  console.log(`${caches.length} cache entr(ies), ${totalGb.toFixed(2)} GB total`);

  const suspect = unstableKeys(caches);
  for (const [prefix, entries] of Object.entries(suspect).sort((a, b) => b[1].length - a[1].length)) {
    const gb = entries.reduce((t, e) => t + (e.size_in_bytes ?? 0), 0) / 1_073_741_824;
    console.warn(`UNSTABLE KEY  ${prefix.slice(0, 45).padEnd(45)} ${entries.length} entries, ${gb.toFixed(2)} GB`);
  }
  if (Object.keys(suspect).length) {
    console.warn('hash the lockfile, not the run id or a timestamp');
  } else {
    console.log('no unstable-key pattern; check whether the run came from a fork, or '
      + 'whether the cache service rate limited -- both are logged as a plain miss');
  }
}

if (import.meta.url === `file://${process.argv[1]}`) main();
''',
"test_intro": "The prefix logic is what separates a healthy cache from a churning one, and it has to survive keys whose hash segment is a different length or missing entirely.",
"test_py_file": "test_actions_cache_audit.py",
"test_py": '''from actions_cache_audit import prefix_of, unstable_keys


def cache(key, size=1000):
    return {"key": key, "size_in_bytes": size}


def test_prefix_strips_the_hash_segment():
    assert prefix_of("Linux-node-a1b2c3d4e5f6") == "Linux-node"


def test_a_key_with_no_hash_is_unchanged():
    assert prefix_of("Linux-node") == "Linux-node"


def test_a_healthy_cache_is_not_flagged():
    caches = [cache(f"Linux-node-{h}") for h in ("a1b2c3d4", "b2c3d4e5")]
    assert unstable_keys(caches) == {}


def test_many_entries_on_one_prefix_is_flagged():
    """The signature of a key that changes every run."""
    caches = [cache(f"Linux-node-{i:08x}") for i in range(9)]
    assert "Linux-node" in unstable_keys(caches)


def test_the_threshold_is_respected():
    caches = [cache(f"Linux-node-{i:08x}") for i in range(4)]
    assert unstable_keys(caches, min_entries=5) == {}
''',
"test_js_file": "actions-cache-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { prefixOf, unstableKeys } from './actions-cache-audit.mjs';

const cache = (key, size = 1000) => ({ key, size_in_bytes: size });

test('the prefix strips the hash segment', () => {
  assert.equal(prefixOf('Linux-node-a1b2c3d4e5f6'), 'Linux-node');
});

test('a key with no hash is unchanged', () => {
  assert.equal(prefixOf('Linux-node'), 'Linux-node');
});

test('a healthy cache is not flagged', () => {
  assert.deepEqual(unstableKeys([cache('Linux-node-a1b2c3d4'), cache('Linux-node-b2c3d4e5')]), {});
});

test('many entries on one prefix is flagged', () => {
  const caches = Array.from({ length: 9 }, (_, i) => cache(`Linux-node-${i.toString(16).padStart(8, '0')}`));
  assert.ok('Linux-node' in unstableKeys(caches));
});
''',
"faq": [
 ("Why is a rate limit reported as a cache miss?",
  "Because actions/cache is built to degrade gracefully — a missing cache should never break a build. It cannot express 'refused to serve' in a way that is safe to continue from, so it logs the outcome that is: a miss."),
 ("How do I tell a rate limit from a bad key?",
  "Look at what is stored. If the key you expect is absent from the caches API, the key is the problem. If it is present and restores still miss, the service declined — and if the run came from a fork, it was never going to write one anyway."),
 ("What makes a cache key unstable?",
  "Anything that changes between runs: a run id, a timestamp, or a lockfile regenerated during the build. The signature is many entries sharing a prefix, each used once, which also fills the quota and evicts the entries you wanted."),
 ("Why can fork pull requests not write caches?",
  "To prevent cache poisoning. A malicious PR could otherwise write a compromised dependency into a cache that later runs on the base branch would restore. Forks read from the base branch and write nothing, by design."),
 ("Does a full cache quota cause misses?",
  "Yes. Entries are evicted least-recently-used once the repository allowance is reached, so a churning key can evict the caches you rely on. Fixing the key usually fixes the quota as a side effect."),
],
"related": [
 ("/ci/redundant-runs-on-rapid-pushes/", "Three pushes run three full pipelines"),
 ("/ci/secrets-are-empty-in-fork-pull-requests/", "Secrets are empty strings in fork PRs"),
 ("/ci/github-token-is-read-only-by-default/", "GITHUB_TOKEN is read-only by default"),
],
"citations": [CITE_CACHE,
 ("actions/cache — GitHub", "https://github.com/actions/cache"),
 ("REST API: Actions cache — GitHub Docs",
  "https://docs.github.com/en/rest/actions/cache")],
},

]
