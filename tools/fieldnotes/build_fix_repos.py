#!/usr/bin/env python3
"""Build script repos for the five field-note sections that never got one.

Nine of the fourteen Field Notes cards have a public `<platform>-fixes` repo. Five do not
— Technical SEO, Cloudflare, GitHub Actions, AWS cost and Email & SES — even though all 26
of their notes carry a full Python script, a full Node script, and a test for each. The
code was written and then only ever published as HTML.

This extracts those four files per note straight out of the built pages and lays them out
exactly like the existing nine, so the whole set looks like one body of work rather than
nine repos and five orphans:

    <slug>/python/<name>.py        <slug>/node/<name>.js
    <slug>/python/test_<name>.py   <slug>/node/<name>.test.js
    <slug>/README.md               + root README, LICENSE, .gitignore, CI workflow

One transformation is applied on the way out, and it is deliberate. The site version reads
credentials with `os.environ["KEY"]`, which is right for a human — it fails loudly when a
key is missing. A test cannot import that module without real credentials, so the existing
repos use `os.environ.get("KEY", "<dummy>")` instead. Matching that convention is what lets
CI run at all. It is applied ONLY to the repo copy; the page keeps the version that teaches
the safer habit.

Usage: build_fix_repos.py [--apply] [section ...]
"""
import html as H
import json
import re
import sys
from pathlib import Path

SITE = Path.home() / "Projects/allanninal.dev"
OUT = Path.home() / "Projects"
APPLY = "--apply" in sys.argv

# section -> (repo name, human label, one-line repo description)
SECTIONS = {
    "seo": ("technical-seo-fixes", "Technical SEO",
            "Python and Node.js scripts that detect and repair technical SEO problems — "
            "sitemaps of dead URLs, blocked noindex, wrong canonicals and soft 404s. "
            "Guides: allanninal.dev/seo"),
    "cloudflare": ("cloudflare-fixes", "Cloudflare",
                   "Python and Node.js scripts that detect and repair Cloudflare "
                   "configuration problems — shadowed page rules, purges that clear "
                   "nothing and Flexible SSL loops. Guides: allanninal.dev/cloudflare"),
    "ci": ("github-actions-fixes", "GitHub Actions",
           "Python and Node.js scripts that detect and repair GitHub Actions problems — "
           "empty secrets in fork PRs, silent cache misses and redundant billed runs. "
           "Guides: allanninal.dev/ci"),
    "aws": ("aws-cost-fixes", "AWS cost",
            "Python and Node.js scripts that find and fix avoidable AWS spend — idle NAT "
            "gateways, unattached EBS volumes, log retention and tag coverage. "
            "Guides: allanninal.dev/aws"),
    "email": ("email-ses-fixes", "Email & SES",
              "Python and Node.js scripts that detect and repair email deliverability "
              "problems — Amazon SES suppression, bounce rate, DKIM and DMARC alignment. "
              "Guides: allanninal.dev/email"),
    "stripe": ("stripe-fixes", "Stripe",
               "Read-only Python and Node.js scripts that find Stripe integration "
               "problems through the API — disabled webhooks, undelivered events, "
               "stalled subscriptions and blocked payouts. They report and print the "
               "repair; they never write. Guides: allanninal.dev/stripe"),
    "twilio": ("twilio-fixes", "Twilio",
               "Read-only Python and Node.js scripts that find Twilio problems through "
               "the API — numbers left on demo TwiML, unregistered 10DLC campaigns, "
               "webhooks pointing nowhere and messages filtered by carriers. They report "
               "and print the repair; they never write. Guides: allanninal.dev/twilio"),
}

# Dependencies are DERIVED from what the extracted files actually import, not typed.
# The first attempt shipped a workflow with a fixed `pip install` list and no package.json
# at all: python failed on a missing dnspython and every node test failed with
# ERR_MODULE_NOT_FOUND. A dependency list that is written by hand goes stale the first time
# a script gains an import.
PY_IMPORT = re.compile(r"^\s*(?:import|from)\s+([a-zA-Z_][\w]*)", re.M)
JS_IMPORT = re.compile(r"""from\s+['"]([^'".][^'"]*)['"]""")
STDLIB_HINT = {"os", "sys", "json", "re", "logging", "datetime", "collections", "pathlib",
               "argparse", "fnmatch", "email", "xml", "urllib", "time", "math", "typing",
               "itertools", "functools", "hashlib", "base64", "csv", "io", "textwrap"}
PYPI = {"dns": "dnspython", "requests": "requests", "boto3": "boto3", "botocore": "boto3",
        "pytest": "pytest", "yaml": "PyYAML", "bs4": "beautifulsoup4"}


def deps_for(dest: Path) -> tuple[set[str], set[str]]:
    """(pip packages, npm packages) actually imported anywhere in this repo."""
    pip, npm = {"pytest"}, set()
    for f in dest.rglob("*.py"):
        for mod in PY_IMPORT.findall(f.read_text(encoding="utf-8")):
            if mod in STDLIB_HINT or mod.startswith("_"):
                continue
            if mod in PYPI:
                pip.add(PYPI[mod])
    for f in list(dest.rglob("*.js")) + list(dest.rglob("*.mjs")):
        for mod in JS_IMPORT.findall(f.read_text(encoding="utf-8")):
            # A package specifier has no spaces. Without this, prose inside a string or
            # comment — "from 'has content'" in an assertion message — was picked up as a
            # dependency and written into package.json.
            if mod.startswith("node:") or mod.startswith(".") or " " in mod:
                continue
            npm.add(mod)
    return pip, npm


# No CI workflow is generated. Every one of the fourteen published repos had the
# one this script used to emit deleted by hand straight afterwards — see
# `aws-cost-fixes` commit 0b053b6 "Drop the CI workflow and the Tests badge". The
# tests are meant to be run by a reader who has cloned the repo, not by a runner.

GITIGNORE = "__pycache__/\n*.pyc\n.pytest_cache/\nnode_modules/\n.env\n.DS_Store\n"

LICENSE = (Path.home() / "Projects/dns-fixes/LICENSE")

# Sections whose scripts never write; see add_repo_links.READ_ONLY.
READ_ONLY = {"stripe", "twilio"}

# Make the module importable without real credentials, the way the existing repos do.
ENV_PY = re.compile(r'os\.environ\[(["\'])([A-Z0-9_]+)\1\]')
ENV_JS = re.compile(r'process\.env\.([A-Z0-9_]+)(?!\s*\|\|)')


def dummy_for(key: str) -> str:
    k = key.upper()
    if "URL" in k or "ENDPOINT" in k or "DOMAIN" in k:
        return "https://example.com"
    if "REGION" in k:
        return "us-east-1"
    return f"dummy-{k.lower().replace('_', '-')}"


def testable(src: str, lang: str) -> str:
    """Give every required env var a harmless default so CI can import the module."""
    if lang == "python":
        return ENV_PY.sub(lambda m: f'os.environ.get("{m.group(2)}", "{dummy_for(m.group(2))}")', src)
    return ENV_JS.sub(lambda m: f'(process.env.{m.group(1)} || "{dummy_for(m.group(1))}")', src)


def panes(html: str, heading: str):
    """Return (py_name, py_src, js_name, js_src) for the code block under `heading`."""
    m = re.search(rf'<h2>{heading}</h2>.*?(<div class="code-block".*?)(?=<h2>|<h3>)', html, re.S)
    if not m:
        return None
    blk = m.group(1)
    out = []
    for lang in ("python", "node"):
        pm = re.search(rf'<div class="code-pane" data-lang="{lang}"[^>]*>\s*'
                       rf'<div class="code-filename">(.*?)</div>\s*'
                       rf'<pre><code[^>]*>(.*?)</code></pre>', blk, re.S)
        if not pm:
            return None
        out += [H.unescape(pm.group(1)).strip(), H.unescape(pm.group(2))]
    return out[0], out[1], out[2], out[3]


def article_title(html: str) -> str:
    m = re.search(r"<h1[^>]*>(.*?)</h1>", html, re.S)
    return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""


def lead(html: str) -> str:
    m = re.search(r'<p class="lead">(.*?)</p>', html, re.S)
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", m.group(1))).strip() if m else ""


def build(section: str) -> tuple[int, int]:
    repo_name, label, desc = SECTIONS[section]
    src_dir = SITE / section
    dest = OUT / repo_name
    made = skipped = 0
    entries = []

    for d in sorted(p for p in src_dir.iterdir() if p.is_dir() and p.name != "assets"):
        html = (d / "index.html").read_text(encoding="utf-8")
        code = panes(html, "The full code")
        test = panes(html, "Add a test")
        if not code or not test:
            print(f"    ⚠ {d.name}: could not extract code or test — skipped")
            skipped += 1
            continue
        py_f, py_s, js_f, js_s = code
        tpy_f, tpy_s, tjs_f, tjs_s = test
        title, ld = article_title(html), lead(html)
        entries.append((d.name, title, ld))

        if APPLY:
            for sub, fn, body in (("python", py_f, testable(py_s, "python")),
                                  ("python", tpy_f, tpy_s),
                                  ("node", js_f, testable(js_s, "node")),
                                  ("node", tjs_f, tjs_s)):
                p = dest / d.name / sub / fn
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(body.rstrip() + "\n", encoding="utf-8")
            (dest / d.name / "README.md").write_text(
                f"# {title}\n\n{ld}\n\n"
                f"**Full guide with diagrams:** https://www.allanninal.dev/{section}/{d.name}/\n\n"
                f"## Run it\n\n"
                f"```bash\nexport DRY_RUN=\"true\"   # report only, write nothing\n"
                f"python python/{py_f}\nnode node/{js_f}\n```\n\n"
                f"## Test it\n\n```bash\npytest python/{tpy_f}\nnode --test node/{tjs_f}\n```\n",
                encoding="utf-8")
        made += 1

    if APPLY:
        dest.mkdir(parents=True, exist_ok=True)
        lines = "\n".join(
            f"- [{t}](./{s}/) — https://www.allanninal.dev/{section}/{s}/" for s, t, _ in entries)
        # The read-only sections have no dry run, because they have no write mode.
        # Telling a reader to "keep DRY_RUN=true before letting it write" describes a
        # variable these scripts do not have and a step they cannot take.
        if section in READ_ONLY:
            safety_blurb = (
                "Every script here is read only. They hold a credential to a live "
                "account, so none of them writes: each one reads through the API, "
                "reports exactly what is wrong, and prints the repair for you to run."
            )
            run_blurb = (
                "Set the environment variables named in that folder's README and run it. "
                "Nothing writes, so there is no dry run to enable and no flag to be "
                "careful about \u2014 use a restricted, read-only credential and the worst "
                "case is that it tells you nothing is wrong."
            )
        else:
            safety_blurb = (
                "Every fix is safe by default. The scripts start in a dry run mode that "
                "reports what they would do, so you can read the plan before anything "
                "writes."
            )
            run_blurb = (
                "Set the environment variables named in that folder's README, keep "
                "`DRY_RUN=true` for the first pass, and read what it reports before "
                "letting it write."
            )
        (dest / "README.md").write_text(
            f"# {label} Fixes\n\n{desc.split('. Guides:')[0]}.\n\n"
            f"{safety_blurb}\n\n"
            f"By **[Allan Niñal](https://github.com/allanninal)** — AI Solutions Engineer. "
            f"I build AI powered tools, data products, and AWS automation.\n"
            f"Full write ups with diagrams for each fix live at "
            f"**[allanninal.dev/{section}](https://www.allanninal.dev/{section}/)**.\n\n"
            f"[![Follow on GitHub](https://img.shields.io/github/followers/allanninal?"
            f"label=Follow%20%40allanninal&style=social)](https://github.com/allanninal)\n"
            f"## The fixes\n\n{lines}\n\n"
            f"## How to run one\n\n"
            f"Each folder holds the same script in Python and in Node.js, plus its test. "
            f"{run_blurb}\n\n"
            f"## License\n\nMIT. Use it, change it, ship it.\n", encoding="utf-8")
        (dest / ".gitignore").write_text(GITIGNORE, encoding="utf-8")
        pip, npm = deps_for(dest)
        # "type": "module" matches the existing nine and is what lets `node --test`
        # discover and import the ES-module test files.
        pkg = {"name": repo_name, "version": "1.0.0", "description": desc.split(". Guides:")[0],
               "type": "module", "private": True,
               "scripts": {"test": "node --test"}, "license": "MIT"}
        if npm:
            pkg["dependencies"] = {m: "*" for m in sorted(npm)}
        (dest / "package.json").write_text(json.dumps(pkg, indent=2) + "\n", encoding="utf-8")
        if LICENSE.exists():
            (dest / "LICENSE").write_text(LICENSE.read_text(encoding="utf-8"), encoding="utf-8")
    return made, skipped


def publish(dest: Path, repo_name: str, description: str) -> str:
    """Create the public repo and push it, or push an update if it already exists.

    This was the one manual step left in the pipeline: the builder wrote the folder
    and then somebody ran git and gh by hand. With several sections landing at once
    that is several chances to push the wrong thing, so it happens here where the
    repo name and description are already known to be right.
    """
    import subprocess

    def run(*args, **kw):
        return subprocess.run(args, cwd=dest, capture_output=True, text=True, **kw)

    if not (dest / ".git").is_dir():
        run("git", "init", "-q", "-b", "main")
    run("git", "add", "-A")
    if not run("git", "diff", "--cached", "--quiet").returncode:
        return "no changes"
    msg = "Add the scripts" if not (dest / ".git" / "refs" / "heads").exists() else "Update the scripts"
    run("git", "commit", "-q", "-m", msg)

    exists = subprocess.run(["gh", "repo", "view", f"allanninal/{repo_name}"],
                            capture_output=True, text=True).returncode == 0
    if not exists:
        r = subprocess.run(
            ["gh", "repo", "create", f"allanninal/{repo_name}", "--public",
             "--source", str(dest), "--remote", "origin", "--push",
             "--description", description],
            capture_output=True, text=True)
        return "created" if r.returncode == 0 else f"gh failed: {r.stderr.strip()[:120]}"

    if not run("git", "remote", "get-url", "origin").stdout.strip():
        run("git", "remote", "add", "origin", f"git@github.com:allanninal/{repo_name}.git")
    r = run("git", "push", "-u", "origin", "main")
    return "pushed" if r.returncode == 0 else f"push failed: {r.stderr.strip()[:120]}"


if __name__ == "__main__":
    want = [a for a in sys.argv[1:] if not a.startswith("--")] or list(SECTIONS)
    PUBLISH = "--publish" in sys.argv
    tm = ts = 0
    for s in want:
        repo_name = SECTIONS[s][0]
        m, k = build(s)
        tm += m; ts += k
        line = (f"  {s:<11} -> {repo_name:<22} {m} fixes extracted"
                + (f", {k} skipped" if k else ""))
        if PUBLISH and APPLY:
            line += f"  [{publish(OUT / repo_name, repo_name, SECTIONS[s][2])}]"
        print(line)
    print(f"\n  {tm} fix folder(s), {ts} skipped")
    print("APPLIED" if APPLY else "DRY RUN — pass --apply to write")
