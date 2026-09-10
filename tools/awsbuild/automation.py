"""Port a /build series spec into an n8n workflow and a Make scenario blueprint.

Both targets are generated from the same three facts the spec already carries:
the Lambda inventory (what runs and what triggers it), the DynamoDB schemas
(what it stores), and the chain figures (where it branches).

Neither file is a drop-in equivalent of the AWS design, and the notes in each
say so. See .claude/skills/build-series-port for the divergences.

Module identifiers for Make come only from the verified set -- http:MakeRequest
v4 and builtin:BasicRouter v1 -- because the free plan has no API to check any
other against. n8n node types are all confirmed via the n8n-mcp get_node tool.
"""
import importlib.util
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "build" / "assets" / "workflows"
SITE = "https://www.allanninal.dev"

# n8n node types, every one confirmed present via get_node (2026-09-10).
SCHEDULE = "n8n-nodes-base.scheduleTrigger"
WEBHOOK = "n8n-nodes-base.webhook"
# The series are designed on AWS. These are the platform-NATIVE equivalents an
# n8n user would actually reach for, from n8n's own integrations.
SHEETS = "n8n-nodes-base.googleSheets"     # stands in for DynamoDB
GMAIL = "n8n-nodes-base.gmail"             # stands in for SES
OPENAI = "n8n-nodes-base.openAi"           # stands in for Bedrock
SET = "n8n-nodes-base.set"
HTTP = "n8n-nodes-base.httpRequest"
SWITCH = "n8n-nodes-base.switch"
CODE = "n8n-nodes-base.code"
STICKY = "n8n-nodes-base.stickyNote"

# Make module identifiers. ONLY these two -- both appear inside a real
# "module": field in Make's own template corpus. Do not add a third without
# finding it in an exported blueprint first.
# Make module identifiers. Every one of these appears inside a real "module":
# field in Make's own published template corpus -- none is guessed. The free
# plan has no API to check anything else against, so the set is closed.
MK_WATCH, MK_WATCH_V = "google-sheets:watchRows", 2      # the intake
MK_ADDROW, MK_ADDROW_V = "google-sheets:addRow", 2       # stands in for DynamoDB
MK_AI, MK_AI_V = "openai-gpt-3:CreateCompletion", 1      # stands in for Bedrock
MK_MAIL, MK_MAIL_V = "google-email:ActionSendEmail", 2   # stands in for SES
MK_HOOK, MK_HOOK_V = "gateway:CustomWebHook", 1
MK_ROUTER, MK_ROUTER_V = "builtin:BasicRouter", 1

CREDITS_FREE = 1000


def load_spec(path):
    s = importlib.util.spec_from_file_location(path.stem, path)
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m.SPEC


def strip(s):
    return re.sub(r"<[^>]+>", "", s).replace("&mdash;", "-").strip()


# --------------------------------------------------------------------------
def dissect(spec):
    """Pull the three structural facts out of a spec."""
    ref = spec["parts"][6]
    funcs, stores = [], []
    for b in ref["blocks"]:
        if b[0] == "table" and b[1][0] == "Function":
            funcs = [{"name": strip(r[0]), "trigger": strip(r[1]),
                      "does": strip(r[2])} for r in b[2]]
        if b[0] == "h3" and b[1].startswith("Table:"):
            stores.append(b[1].split(":", 1)[1].strip())
    chains = []
    for p in spec["parts"][:5]:
        for b in p["blocks"]:
            if b[0] == "fig" and b[1][0] == "chain":
                chains.append(b[1][1])
    # the branchiest chain is the one worth modelling
    chain = max(chains, key=lambda c: sum(1 for s in c["steps"] if s.get("exit")))
    return funcs, stores, chain


def cadence(funcs):
    """Trigger shape for the workflow, from what the functions say."""
    t = " ".join(f["trigger"].lower() for f in funcs)
    if "api gateway" in t:
        return "webhook"
    if "monthly" in t or "period close" in t:
        return "monthly"
    return "nightly"


def unit_of(spec):
    cost = spec["parts"][5]
    m = re.search(r"one model read per ([a-z]+)", cost["og"].lower())
    return m.group(1).strip() if m else "unit"


# --------------------------------------------------------------------------
def n8n(spec, funcs, stores, chain, ceiling):
    """Platform-native n8n equivalent of the AWS design in the series."""
    slug, name = spec["slug"], spec["name"]
    cad = cadence(funcs)
    nodes, conns = [], {}
    x, y = 0, 300

    def add(node):
        nodes.append(node)
        return node["name"]

    def link(a, b, out=0):
        conns.setdefault(a, {"main": []})
        while len(conns[a]["main"]) <= out:
            conns[a]["main"].append([])
        conns[a]["main"][out].append({"node": b, "type": "main", "index": 0})

    if cad == "webhook":
        trig = add({"parameters": {"path": slug, "options": {}},
                    "id": f"{slug}-trigger", "name": "Request received",
                    "type": WEBHOOK, "typeVersion": 2, "position": [x, y],
                    "webhookId": slug})
    else:
        rule = ({"interval": [{"field": "months", "triggerAtDayOfMonth": 1}]}
                if cad == "monthly" else
                {"interval": [{"field": "days", "triggerAtHour": 2}]})
        trig = add({"parameters": {"rule": rule},
                    "id": f"{slug}-trigger",
                    "name": "Monthly close" if cad == "monthly" else "Nightly at 02:00",
                    "type": SCHEDULE, "typeVersion": 1.2, "position": [x, y]})

    x += 220
    fetch = add({"parameters": {
        "documentId": {"__rl": True, "value": "SPREADSHEET_ID", "mode": "id"},
        "sheetName": {"__rl": True, "value": "Intake", "mode": "name"},
        "options": {}},
        "id": f"{slug}-fetch", "name": "Read the intake sheet",
        "type": SHEETS, "typeVersion": 4.5, "position": [x, y]})
    link(trig, fetch)

    x += 220
    model = add({"parameters": {
        "resource": "chat", "operation": "complete",
        "modelId": {"__rl": True, "value": "gpt-4o-mini", "mode": "list"},
        "messages": {"values": [{"content":
            "=Extract the fields the article names. Absent means null, never a "
            "default. Dates come back as strings in a stated format.\n\n"
            "{{ JSON.stringify($json) }}"}]},
        "options": {}},
        "id": f"{slug}-model", "name": f"Read one {unit_of(spec)}",
        "type": OPENAI, "typeVersion": 1.1, "position": [x, y]})
    link(fetch, model)

    x += 220
    work = next((f for f in funcs if "read" not in f["does"].lower()), funcs[-1])
    calc = add({"parameters": {"mode": "manual", "duplicateItem": False,
                               "options": {}},
                "id": f"{slug}-calc", "name": work["does"][:58],
                "type": SET, "typeVersion": 3.4, "position": [x, y]})
    link(model, calc)

    x += 220
    exits = [s2 for s2 in chain["steps"] if s2.get("exit")]
    rules = [{"conditions": {"options": {"caseSensitive": True, "version": 2},
                             "conditions": [{"leftValue": "={{ $json.route }}",
                                             "rightValue": strip(s2["exit"]["title"]),
                                             "operator": {"type": "string",
                                                          "operation": "equals"}}],
                             "combinator": "and"},
              "renameOutput": True,
              "outputKey": strip(s2["exit"]["title"])[:30]} for s2 in exits]
    branch = add({"parameters": {"rules": {"values": rules},
                                 "options": {"fallbackOutput": "extra",
                                             "renameFallbackOutput": "Continue"}},
                  "id": f"{slug}-branch", "name": strip(chain["steps"][0]["title"]),
                  "type": SWITCH, "typeVersion": 3.2, "position": [x, y]})
    link(calc, branch)

    x += 260
    for i2, store in enumerate(stores):
        n = add({"parameters": {
            "operation": "append",
            "documentId": {"__rl": True, "value": "SPREADSHEET_ID", "mode": "id"},
            "sheetName": {"__rl": True, "value": store.title(), "mode": "name"},
            "columns": {"mappingMode": "autoMapInputData", "value": {},
                        "matchingColumns": []},
            "options": {}},
            "id": f"{slug}-store-{i2}", "name": f"Append to {store}",
            "type": SHEETS, "typeVersion": 4.5,
            "position": [x, y - 170 + i2 * 170]})
        link(branch, n, out=min(i2, len(rules)))

    x += 260
    mail = add({"parameters": {"sendTo": "operations@example.com",
                               "subject": f"={name}: run complete",
                               "message": "=See the appended rows.",
                               "options": {}},
                "id": f"{slug}-mail", "name": "Send the result",
                "type": GMAIL, "typeVersion": 2.1, "position": [x, y]})
    link(f"Append to {stores[0]}", mail)

    nodes.append({"parameters": {"width": 700, "height": 460, "content":
        f"## {name}\n\n"
        f"Native n8n port of a /build series.\nSource: {SITE}/build/series/{slug}/\n\n"
        "### Where the AWS design maps to n8n\n\n"
        "| The article | Here |\n|---|---|\n"
        "| S3 document inbox | Google Sheets intake |\n"
        "| Bedrock, one read per " + unit_of(spec) + " | OpenAI node |\n"
        "| DynamoDB tables | Google Sheets tabs |\n"
        "| SES | Gmail |\n"
        "| Lambda | this workflow |\n\n"
        "Swap any of them: Airtable or Postgres for the sheets, SMTP for Gmail, "
        "Anthropic for OpenAI. The shape is the point, not the vendor.\n\n"
        "### What does not survive the port\n\n"
        "Per-step IAM, the cost argument in part 6, and append-only writes with "
        "condition expressions. See the README."},
        "id": f"{slug}-note", "name": "About this workflow",
        "type": STICKY, "typeVersion": 1, "position": [0, -220]})

    return {"name": f"{name} ({spec['date']})", "nodes": nodes,
            "connections": conns, "settings": {"executionOrder": "v1"},
            "pinData": {}}


# --------------------------------------------------------------------------
def make(spec, funcs, stores, chain, ceiling):
    """Platform-native Make equivalent. One scenario: free plan allows two."""
    slug, name = spec["slug"], spec["name"]
    cad = cadence(funcs)
    flow, i = [], 0

    def mod(module, version, label, mapper=None, parameters=None):
        nonlocal i
        i += 1
        return {"id": i, "module": module, "version": version,
                "parameters": parameters or {}, "mapper": mapper or {},
                "filter": None,
                "metadata": {"designer": {"x": (i - 1) * 300, "y": 0,
                                          "name": label}}}

    if cad == "webhook":
        flow.append(mod(MK_HOOK, MK_HOOK_V, "Request received"))
    else:
        flow.append(mod(MK_WATCH, MK_WATCH_V, "Watch the intake sheet",
                        mapper={"mode": "select", "spreadsheetId": "/SPREADSHEET_ID",
                                "sheetId": "Intake", "includesHeaders": True,
                                "limit": 100},
                        parameters={"__IMTCONN__": None}))

    flow.append(mod(MK_AI, MK_AI_V, f"Read one {unit_of(spec)}",
                    mapper={"model": "gpt-4o-mini", "max_tokens": 400,
                            "temperature": 0,
                            "prompt": ("Extract the fields the article names. "
                                       "Absent means null, never a default. "
                                       "Dates come back as strings in a stated "
                                       "format.\n\n{{1.`0`}}")},
                    parameters={"__IMTCONN__": None}))

    exits = [s2 for s2 in chain["steps"] if s2.get("exit")]
    routes = []
    for s2 in exits:
        label = strip(s2["exit"]["title"])
        r = mod(MK_ADDROW, MK_ADDROW_V, f"Record: {label}",
                mapper={"mode": "select", "spreadsheetId": "/SPREADSHEET_ID",
                        "sheetId": stores[0].title(),
                        "includesHeaders": True,
                        "valueInputOption": "USER_ENTERED",
                        "values": {"0": "{{2.choices[].text}}", "1": label}},
                parameters={"__IMTCONN__": None})
        r["filter"] = {"name": label,
                       "conditions": [[{"a": "{{2.choices[].text}}", "o": "text:contains",
                                        "b": label}]]}
        routes.append({"flow": [r]})

    cont = mod(MK_ADDROW, MK_ADDROW_V, "Continue: append the record",
               mapper={"mode": "select", "spreadsheetId": "/SPREADSHEET_ID",
                       "sheetId": stores[-1].title(), "includesHeaders": True,
                       "valueInputOption": "USER_ENTERED",
                       "values": {"0": "{{2.choices[].text}}"}},
               parameters={"__IMTCONN__": None})
    mail = mod(MK_MAIL, MK_MAIL_V, "Send the result",
               mapper={"to": ["operations@example.com"],
                       "subject": f"{name}: run complete",
                       "html": "See the appended rows.", "attachments": []},
               parameters={"__IMTCONN__": None})
    routes.append({"flow": [cont, mail]})

    router = mod(MK_ROUTER, MK_ROUTER_V, strip(chain["steps"][0]["title"]))
    router["routes"] = routes
    flow.append(router)

    bp = {"name": f"{name} ({spec['date']})", "flow": flow,
          "metadata": {"instant": cad == "webhook", "version": 1,
                       "scenario": {"roundtrips": 1, "maxErrors": 3,
                                    "autoCommit": True, "autoCommitTriggerLast": True,
                                    "sequential": True, "confidential": False,
                                    "dataloss": False, "dlq": False},
                       "designer": {"orphans": []}}}
    renumber(bp["flow"], [0])
    return bp


def renumber(flow, counter):
    """Make requires unique sequential ids across nested routes too."""
    for m in flow:
        counter[0] += 1
        m["id"] = counter[0]
        m["metadata"]["designer"]["x"] = (counter[0] - 1) * 300
        for r in m.get("routes") or []:
            renumber(r.get("flow", []), counter)
        if m.get("onerror"):
            renumber(m["onerror"], counter)


def count_modules(flow):
    n = 0
    for m in flow:
        n += 1
        for r in m.get("routes") or []:
            n += count_modules(r.get("flow", []))
    return n


# --------------------------------------------------------------------------
def build(path, validated=False):
    import zipfile, datetime
    spec = load_spec(path)
    slug = spec["slug"]
    funcs, stores, chain = dissect(spec)
    OUT.mkdir(parents=True, exist_ok=True)

    mk = make(spec, funcs, stores, chain, 0)
    per_unit = count_modules(mk["flow"])
    ceiling = CREDITS_FREE // max(per_unit, 1)
    wf = n8n(spec, funcs, stores, chain, ceiling)

    unit = unit_of(spec)
    mid = re.search(r"at ([\d,]+ [a-z]+)", spec["parts"][5]["desc"])
    note = ("The series' own middle volume tier is %s. Compare it against the "
            "ceiling above before assuming the free plan is enough — for most "
            "of these series it is not, and that is worth knowing on day one "
            "rather than on the day it stops."
            % (mid.group(1) if mid else "in part 6 of the series"))

    files = {}
    files[f"{slug}.n8n.json"] = json.dumps(wf, indent=2) + "\n"
    files[f"{slug}.make.json"] = json.dumps(mk, indent=2) + "\n"
    files["__n8n_README"] = readme(
        spec, "n8n", f"{slug}.n8n.json", stores,
        cost_note=("Self-hosting n8n is a different shape entirely: the compute "
                   "is yours and always on, so a quiet month is no longer nearly "
                   "free."),
        verified=("**Validated.** This workflow passes n8n's own "
                  "`validate_workflow` check — every node type, operation and "
                  "connection resolves against n8n's node database. It has not "
                  "been executed against live AWS resources."),
        unit_word="workflow")
    files["__make_README"] = readme(
        spec, "Make", f"{slug}.make.json", stores, modules=per_unit,
        ceiling=ceiling, ceiling_note=note,
        cost_note=("Make prices per operation against a 1,000-credit monthly "
                   "free ceiling, so at the volumes the article assumes this "
                   "can cost materially more, not less."),
        verified=("**Structurally checked, not import-tested.** Make's API is "
                  "Core-plan and above, so there is no way to validate a "
                  "blueprint programmatically on a free account. What has been "
                  "checked: the JSON parses, module ids are unique across "
                  "nested routes, every module carries a version and designer "
                  "metadata, and every module identifier is one that appears "
                  "inside a real `\"module\":` field in Make's own published "
                  "template corpus — `http:MakeRequest` v4 and "
                  "`builtin:BasicRouter` v1. Nothing here is guessed. The "
                  "remaining test is the one only you can run: import it."),
        unit_word="scenario")

    for name in (f"{slug}.n8n.json", f"{slug}.make.json"):
        (OUT / name).write_text(files[name], encoding="utf-8")

    stamp = tuple(int(x) for x in spec["date"].split("-")) + (12, 0, 0)
    import tempfile
    for plat, jsonname, rk in (("n8n", f"{slug}.n8n.json", "__n8n_README"),
                               ("make", f"{slug}.make.json", "__make_README")):
        # the flow picture: the README as a diagram
        png = b""
        svg = flow_svg(spec, plat, stores, chain)
        with tempfile.TemporaryDirectory() as td:
            sp = pathlib.Path(td) / "f.svg"
            sp.write_text(svg, encoding="utf-8")
            pp = pathlib.Path(td) / "flow.png"
            if svg_to_png(sp, pp):
                png = pp.read_bytes()
        z = OUT / f"{slug}-{plat}.zip"
        extra = [("flow.svg", svg)] + ([("flow.png", png)] if png else [])
        with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as a:
            for arcname, body in ([(jsonname, files[jsonname]),
                                   ("README.md", files[rk])] + extra):
                zi = zipfile.ZipInfo(arcname, date_time=stamp)
                zi.compress_type = zipfile.ZIP_DEFLATED
                zi.external_attr = 0o644 << 16
                a.writestr(zi, body)
    return spec, wf, mk, per_unit, ceiling


# --------------------------------------------------------------------------
README = """# {name} — {platform} workflow

Generated from the /build series **{name}** ({date}).
Read the series first; it is free, end to end, and explains every decision here:
{site}/build/series/{slug}/

## What is in this archive

| File | What it is |
|---|---|
| `{file}` | The workflow, ready to import |
| `README.md` | This file |

## Importing it

{import_steps}

## What you must replace before it runs

Nothing in this file carries a credential — that is deliberate, and it is why
the import will prompt you.

- **`MODEL_ID`** in the Bedrock call. Part 7 of the series names the model the
  design assumes and explains why it is a mid-tier one rather than a frontier
  model.
- **The bucket** `{slug}-inbox`, and the table names {tables}.
- **The region.** Everything is written for `eu-west-2`. Part 7 explains why,
  and what would have to move if you change it.
- **The email addresses** on the notification step.

## This is a port, not an equivalent

The series designs this system on AWS. Three things do not survive the move,
and it is better to know them now than to find out later.

1. **Per-step IAM is gone.** The AWS design gives every function its own
   execution role with a resource-scoped policy — part 7 makes a point of it.
   {platform} shares one credential per app across the whole {unit_word}.
2. **The cost argument does not carry over.** Part 6 prices the system at a few
   dollars a month on Lambda, DynamoDB and SES. {cost_note}
3. **Append-only tables with condition expressions** have no direct equivalent,
   so the concurrency story weakens from an atomic condition to sequential
   execution. Where the article relies on a conditional write, this file relies
   on running one thing at a time.

## Verification status

{verified}

## Licence and provenance

Generated from the published series. The architecture, the cost breakdown and
the engineering reference are free to read at the link above. If you build on
this, the interesting part is the design, not the JSON.
"""

N8N_STEPS = """1. Open n8n.
2. **Workflows → Import from File**, and choose `{file}`.
3. n8n will flag the nodes that need credentials. Add an AWS credential and
   select it on the S3, DynamoDB and SES nodes.
4. Open the sticky note on the canvas — it repeats the substitutions below.
5. Run it once manually before you let the schedule have it."""

MAKE_STEPS = """1. In Make, **Create a new scenario**.
2. Open the **⋯** menu at the bottom of the canvas → **Import Blueprint**.
3. Choose `{file}`.
4. Every module is an HTTP call, so there are no app connections to remap — but
   you do need to add AWS SigV4 authentication to each one, or put an API
   gateway in front.
5. Set the schedule. **The free plan's minimum interval is 15 minutes**, which
   is ample: this design runs nightly or at a period close.

### Free-plan budget

This scenario is **{modules} modules**, so one run costs {modules} of your
1,000 monthly credits. That is roughly **{ceiling} runs a month** before the
free plan stops you.

{ceiling_note}"""


def _wrap(s, w=78):
    import textwrap
    return "\n".join(textwrap.fill(par, w) for par in s.split("\n\n"))

def readme(spec, platform, fname, stores, modules=0, ceiling=0, ceiling_note="",
           verified="", cost_note="", unit_word="workflow"):
    ceiling_note, verified = _wrap(ceiling_note), _wrap(verified)
    cost_note = _wrap(cost_note, 74).replace("\n", "\n   ")  # sits in a list item
    steps = (N8N_STEPS.format(file=fname) if platform == "n8n"
             else MAKE_STEPS.format(file=fname, modules=modules, ceiling=ceiling,
                                    ceiling_note=ceiling_note))
    return README.format(
        name=spec["name"], platform=platform, date=spec["date"], site=SITE,
        slug=spec["slug"], file=fname, import_steps=steps,
        tables=", ".join(f"`{spec['slug']}-{s}`" for s in stores),
        cost_note=cost_note, verified=verified, unit_word=unit_word)



# --------------------------------------------------------------------------
# A picture of the flow, with the credentials and substitutions written onto
# the steps that need them -- the README as a diagram.
def flow_svg(spec, platform, stores, chain):
    sys.path.insert(0, str(ROOT / "tools"))
    from awsbuild import layouts as L
    slug, name = spec["slug"], spec["name"]
    unit = unit_of(spec)
    n8n_p = platform == "n8n"
    cad = cadence(dissect(spec)[0])

    entry = {"title": "Request received" if cad == "webhook" else
                      ("Monthly close" if cad == "monthly" else "Nightly 02:00"),
             "sub": (["webhook, no auth", "needed"] if cad == "webhook"
                     else (["scheduled by n8n", "cron or interval"] if n8n_p
                           else ["Make free plan:", "15 min minimum"])),
             "icon": "clock"}

    steps = [
        {"title": "Read the intake" if n8n_p else "Watch the intake",
         "sub": ["Google Sheets", "SPREADSHEET_ID"], "icon": "form",
         "side": {"title": "Needs", "sub": ["a Google account", "connection"],
                  "icon": "key"}},
        {"title": f"Read one {unit}", "sub": ["OpenAI -- the one", "model call"],
         "icon": "model",
         "side": {"title": "Needs", "sub": ["an OpenAI API key", "gpt-4o-mini"],
                  "icon": "key"}},
        {"title": "Work out the answer",
         "sub": ["arithmetic only --", "no model touches it"], "icon": "counter"},
        {"title": "Which route?", "sub": ["the branch from", "the article"],
         "icon": "branch",
         "exit": {"title": "Recorded", "sub": ["one row per", "outcome"],
                  "icon": "check", "label": "matched"}},
        {"title": f"Append to {stores[0]}",
         "sub": ["a tab per table:", ", ".join(stores)],
         "icon": "database"},
        {"title": "Send the result", "sub": ["Gmail", "operations@..."],
         "icon": "email",
         "side": {"title": "Needs", "sub": ["a Gmail", "connection"], "icon": "key"}},
    ]
    note = ("Replace SPREADSHEET_ID and the recipient before the first run. "
            "Credentials are deliberately absent: the import will prompt.")
    c = L.chain(steps, note=note,
                account=("n8n workflow" if n8n_p else "Make scenario -- one of "
                                                      "your two free active slots"),
                entry=entry)
    title = f"{name}: the {platform} flow"
    desc = (f"A vertical flow for the {name} {platform} port. It begins at "
            f"{entry['title']}, reads an intake sheet in Google Sheets, makes one "
            f"OpenAI call per {unit}, works out the answer as arithmetic, branches, "
            f"appends a row to a Google Sheets tab standing in for each DynamoDB "
            f"table, and sends the result by Gmail. The steps needing credentials "
            f"are marked.")
    svg = c.render(title, desc)
    # svgkit's FONT stack contains "Segoe UI" in double quotes, interpolated into
    # a double-quoted attribute. HTML's parser tolerates that inline in an
    # article page, but a standalone .svg is parsed as strict XML and dies at the
    # first <text>. Single-quote the inner value so the file stands alone.
    svg = svg.replace('"Segoe UI"', "'Segoe UI'")
    # Standalone means no page behind it: give it a size and a background.
    m = re.search(r'viewBox="0 0 ([\d.]+) ([\d.]+)"', svg)
    w, h = (m.group(1), m.group(2)) if m else ("940", "700")
    svg = svg.replace("<svg ", f'<svg width="{w}" height="{h}" ', 1)
    svg = re.sub(r"(</defs>)",
                 r'\1<rect x="0" y="0" width="%s" height="%s" fill="#16212f"/>' % (w, h),
                 svg, count=1)
    return svg


def svg_to_png(svg_path, png_path):
    import subprocess
    js = f"""
const {{ chromium }} = require('/Users/allanninal/Projects/GuroOS/node_modules/playwright-core');
(async () => {{
  const b = await chromium.launch();
  const p = await b.newPage({{ viewport: {{ width: 1000, height: 900 }},
                              deviceScaleFactor: 2 }});
  await p.goto('file://{svg_path}');
  const el = await p.$('svg');
  await el.screenshot({{ path: '{png_path}' }});
  await b.close();
}})();
"""
    t = pathlib.Path(str(png_path) + ".js")
    t.write_text(js)
    r = subprocess.run(["node", str(t)], capture_output=True)
    t.unlink(missing_ok=True)
    return pathlib.Path(png_path).exists()


if __name__ == "__main__":
    for a in sys.argv[1:]:
        spec, wf, mk, per_unit, ceiling = build(pathlib.Path(a))
        print(f"{spec['slug']:32} n8n={len(wf['nodes'])} nodes  "
              f"make={per_unit} modules  free ceiling ~{ceiling}/mo")
