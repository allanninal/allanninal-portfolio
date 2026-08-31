"""Turn the monochrome /build diagrams into AWS-console-dark diagrams.

Two passes over every inline <svg> in a page:

  1. recolour  -- the diagrams were authored with a tiny monochrome vocabulary
     (white box fills, #111 strokes/text, #555 sub-labels), so the mapping onto
     the dark palette is mechanical and context-aware: a #111 on a <text> is
     type, a #111 on a <line> is a connector, a #111 on a marker path is an
     arrowhead.

  2. icons     -- each component box gets an AWS-category accent bar and, where
     the label leaves room, a colourful service tile chosen from the label text.
"""
import re
from .palette import (BOX_FILL, STROKE, LINE, TEXT, SUB, FAINT, DG_BG)
from .icons import tile, category_of, GLYPHS
from .palette import CAT

MONO_DARK = {"#111111", "#000000"}
MONO_MID = {"#555555", "#333333"}
MONO_FAINT = {"#777777", "#888888", "#666666", "#999999"}
WHITE = {"#ffffff", "#fff", "#FFFFFF"}

TEXTY = re.compile(r"text|title|label|note|conn|caption|head|sub|legend|type|word", re.I)
BOXY = re.compile(r"box|container|node|card|panel|rect|group|lane|band|plate", re.I)


# --------------------------------------------------------------------------
# pass 1 -- recolour
# --------------------------------------------------------------------------
def _style_block(css):
    def rule(m):
        sel, body = m.group(1), m.group(2)
        texty = bool(TEXTY.search(sel)) or "font-" in body
        boxy = bool(BOXY.search(sel))

        def decl(d):
            prop, val = d.group(1), d.group(2).strip().lower()
            if val in WHITE:
                new = BOX_FILL if prop == "fill" else STROKE
            elif val in MONO_DARK:
                if prop == "stroke":
                    new = STROKE if boxy else LINE
                else:
                    new = TEXT if texty else LINE
            elif val in MONO_MID:
                new = SUB
            elif val in MONO_FAINT:
                new = FAINT
            else:
                return d.group(0)
            return f"{prop}: {new}"

        body = re.sub(r"(fill|stroke)\s*:\s*(#[0-9a-fA-F]{3,6})", decl, body)
        return f"{sel}{{{body}}}"

    return re.sub(r"([^{}]+)\{([^{}]*)\}", rule, css)


def _elements(svg):
    """Recolour fill=/stroke= attributes, aware of the tag they sit on."""
    out, pos, in_marker = [], 0, 0
    for m in re.finditer(r"<(/?)([A-Za-z][\w:-]*)((?:\"[^\"]*\"|'[^']*'|[^>])*?)(/?)>", svg):
        out.append(svg[pos:m.start()])
        pos = m.end()
        close, tag, attrs, selfclose = m.groups()
        if tag == "marker":
            in_marker += 0 if close else 1
            if close:
                in_marker = max(0, in_marker - 1)
        if close:
            out.append(m.group(0))
            continue

        is_text = tag in ("text", "tspan", "textPath")
        is_shape = tag in ("rect", "circle", "ellipse", "polygon")
        is_stroked = tag in ("line", "path", "polyline")

        attrs = re.sub(
            r"(fill|stroke)=([\"'])(#[0-9a-fA-F]{3,6})\2",
            lambda d: _attr_swap(d, is_text, is_shape, is_stroked, in_marker),
            attrs)
        out.append(f"<{tag}{attrs}{selfclose}>")
    out.append(svg[pos:])
    return "".join(out)


def _attr_swap(d, is_text, is_shape, is_stroked, in_marker):
    prop, q, val = d.group(1), d.group(2), d.group(3).lower()
    if val in WHITE:
        new = BOX_FILL if prop == "fill" else STROKE
    elif val in MONO_DARK:
        if is_text:
            new = TEXT
        elif prop == "stroke":
            new = STROKE if is_shape else LINE
        else:
            new = LINE if (in_marker or is_stroked) else STROKE
    elif val in MONO_MID:
        new = SUB if is_text else STROKE
    elif val in MONO_FAINT:
        new = FAINT if is_text else STROKE
    else:
        return d.group(0)
    return f"{prop}={q}{new}{q}"


def recolour(svg):
    svg = re.sub(r"(<style[^>]*>)(.*?)(</style>)",
                 lambda m: m.group(1) + _style_block(m.group(2)) + m.group(3),
                 svg, flags=re.S)
    return _elements(svg)


# --------------------------------------------------------------------------
# pass 2 -- icons
# --------------------------------------------------------------------------
KEYWORDS = [
    ("lambda", ("aws lambda", "lambda")),
    ("flow", ("step function", "state machine", "orchestrat", "workflow", "pipeline")),
    ("event", ("eventbridge", "event bus", "event rule", "trigger", "fires")),
    ("queue", ("sqs", "queue", "backlog", "buffer")),
    ("topic", ("sns", "topic", "fan out", "fan-out", "broadcast")),
    ("gateway", ("api gateway", "function url", "gateway", "api endpoint", "http api", "rest api")),
    ("cdn", ("cloudfront", "cdn", "edge")),
    ("dns", ("route 53", "route53", "dns", "domain")),
    ("bucket", ("s3", "bucket", "object store", "blob")),
    ("archive", ("glacier", "archive", "cold storage", "backup")),
    ("database", ("dynamodb", "dynamo", "aurora", "rds", "postgres", "database", "db table",
                  "table", "ledger", "index store", "record store", "state store")),
    ("model", ("bedrock", "claude", "the model", "a model", "llm", "ai model", "language model",
               "sagemaker", "reader", "reads and", "classif", "score")),
    ("ocr", ("textract", "ocr", "extract text", "reads the pdf", "parser", "parse")),
    ("vision", ("rekognition", "vision", "image analysis", "detects objects", "moderation")),
    ("voice", ("transcribe", "polly", "voice", "speech", "audio", "recording", "transcript")),
    ("inbox", ("inbox", "mailbox", "incoming mail", "apply inbox")),
    ("email", ("amazon ses", "ses", "email", "e-mail", "mail out", "sends mail", "newsletter")),
    ("key", ("secrets manager", "kms", "secret", "api key", "credential", "token")),
    ("lock", ("iam", "permission", "access control", "auth", "signature", "signed")),
    ("shield", ("waf", "guardrail", "shield", "security", "safety", "protect", "compliance")),
    ("monitor", ("cloudwatch", "monitor", "metric", "health", "watch", "observab")),
    ("alarm", ("alarm", "alert", "escalat", "failure", "error", "incident")),
    ("log", ("log", "audit", "history", "trail", "journal")),
    ("clock", ("schedule", "cron", "timer", "daily", "hourly", "nightly", "weekly", "every day",
               "clock", "cadence", "at 8", "runs each")),
    ("counter", ("count", "counts", "tally", "total", "how many", "quantity", "units")),
    ("chart", ("athena", "quicksight", "analytics", "chart", "dashboard", "trend", "stats")),
    ("report", ("report", "digest", "summary", "brief", "roll-up", "rollup", "weekly report")),
    ("search", ("search", "lookup", "match", "find", "query")),
    ("webhook", ("webhook", "callback", "post back", "hook")),
    ("browser", ("browser", "website", "web page", "landing page", "your site", "web app", "portal")),
    ("phone", ("sms", "text message", "whatsapp", "phone", "mobile", "call", "twilio")),
    ("chat", ("slack", "chat", "message", "conversation", "reply", "thread", "dm")),
    ("form", ("form", "survey", "questionnaire", "intake form", "signup", "sign-up")),
    ("doc", ("pdf", "document", "resume", "cv", "contract", "policy", "spec", "statement", "file")),
    ("money", ("stripe", "payment", "invoice", "price", "cost", "refund", "money", "billing",
               "deposit", "charge", "payout", "revenue", "quote")),
    ("calendar", ("calendar", "booking", "appointment", "reservation", "rsvp", "slot", "diary")),
    ("cart", ("order", "cart", "checkout", "basket", "shop", "storefront", "purchase")),
    ("box", ("product", "inventory", "stock", "sku", "parcel", "package", "catalogue", "catalog",
             "warehouse", "item")),
    ("truck", ("delivery", "shipping", "shipment", "route", "driver", "courier", "dispatch")),
    ("tag", ("coupon", "discount", "offer", "promo", "tag", "label", "upsell", "add-on")),
    ("team", ("team", "crew", "staff", "colleagues", "the shop", "front desk")),
    ("person", ("customer", "owner", "manager", "person", "human", "you ", "operator",
                "reviewer", "applicant", "candidate", "client", "guest", "member", "supplier",
                "vendor", "contact", "lead", "subscriber", "patient", "tenant")),
    ("map", ("map", "location", "address", "geo", "territory")),
    ("image", ("photo", "image", "picture", "thumbnail", "screenshot")),
    ("link", ("link", "url", "short link", "one-tap")),
    ("code", ("code", "repo", "deploy", "ci", "build", "git", "cdk", "infrastructure")),
    ("filter", ("filter", "rules", "gate", "guard", "cap", "dedup", "de-dup", "threshold",
                "router", "routes", "decides where")),
    ("check", ("approve", "check", "verify", "confirm", "valid", "review", "pass mark", "yes")),
    ("bell", ("notify", "notification", "reminder", "nudge", "ping", "bell")),
    ("cloud", ("cloud", "aws account", "third party", "third-party", "external service")),
]

NUM = r"[-+]?\d*\.?\d+"


def _fnum(attrs, name, default=None):
    m = re.search(rf'\b{name}=["\']({NUM})["\']', attrs)
    return float(m.group(1)) if m else default


# Named AWS services and unambiguous phrases. Checked before ROLES so that
# "Secrets Manager" is a key, not a manager, and "DynamoDB catalogue" is a
# database, not a catalogue of products.
SERVICES = [
    ("lambda",   ("aws lambda", "lambda")),
    ("key",      ("secrets manager", "parameter store", "kms", "key management")),
    ("database", ("dynamodb", "dynamo db", "amazon rds", "aurora", "documentdb", "elasticache",
                  "timestream", "neptune")),
    ("bucket",   ("amazon s3", "s3 bucket", "s3")),
    ("archive",  ("glacier", "deep archive")),
    ("queue",    ("amazon sqs", "sqs")),
    ("topic",    ("amazon sns", "sns")),
    ("email",    ("amazon ses", "ses", "workmail")),
    ("event",    ("eventbridge", "event bridge")),
    ("flow",     ("step functions", "step function", "state machine")),
    ("gateway",  ("api gateway", "function url", "lambda url")),
    ("cdn",      ("cloudfront",)),
    ("dns",      ("route 53", "route53")),
    ("model",    ("amazon bedrock", "bedrock", "sagemaker")),
    ("ocr",      ("textract", "amazon comprehend", "comprehend")),
    ("vision",   ("rekognition",)),
    ("voice",    ("transcribe", "amazon polly", "polly", "amazon connect")),
    ("monitor",  ("cloudwatch", "x-ray", "xray")),
    ("lock",     ("iam", "cognito", "sts")),
    ("shield",   ("aws waf", "waf", "guardduty", "aws shield")),
    ("chart",    ("athena", "quicksight", "glue", "kinesis")),
    ("code",     ("codebuild", "codepipeline", "cloudformation", "aws cdk", "cdk", "terraform")),
    ("clock",    ("eventbridge scheduler", "aws scheduler")),
    ("money",    ("aws budgets", "cost explorer", "stripe")),
]

# Terminal / outcome boxes -- "Drop 401", "Already firing, stop".
OUTCOMES = [
    ("stop",   ("drop", "discard", "ignore", "reject", "stop", "skip", "no-op", "noop",
                "do nothing", "nothing happens", "abort", "bail", "refuse", "block", "401",
                "403", "throw away", "dead letter")),
    ("check",  ("done", "accepted", "success", "delivered", "sent", "ok", "passes", "allowed")),
    ("retry",  ("retry", "retries", "back off", "backoff", "try again", "requeue", "re-queue")),
]

# Role words that name a component outright -- these beat any keyword found in
# the sub-label, which is what made "Intake / strip personal fields" pick up a
# person icon on the first pass.
ROLES = [
    ("inbox",    ("intake", "ingest", "receiver", "collector", "catcher", "mailroom")),
    ("model",    ("reader", "scorer", "classifier", "analyser", "analyzer", "extractor",
                  "summariser", "summarizer", "drafter", "writer", "composer", "generator",
                  "picker", "matcher", "planner", "grader", "judge", "ranker")),
    ("filter",   ("router", "dispatcher", "sorter", "gate", "guard", "screener", "triage",
                  "dedup", "deduper")),
    ("bell",     ("notifier", "reminder", "nudger", "pinger", "alerter")),
    ("email",    ("sender", "mailer", "publisher", "broadcaster")),
    ("database", ("ledger", "registry", "datastore", "data store", "record store", "memory")),
    ("clock",    ("scheduler", "timer", "cadence", "cron")),
    ("doc",      ("rubric", "policy", "template", "config", "settings", "playbook", "brief",
                  "spec", "rules doc", "checklist")),
    ("chart",    ("tracker", "meter", "counter", "scoreboard")),
    ("money",    ("biller", "charger", "collector of payment", "invoicer")),
    ("person",   ("owner", "manager", "operator", "reviewer", "approver", "human", "you")),
]


def _hit(text, keys):
    for k in keys:
        if re.search(r"(?<![a-z])" + re.escape(k) + r"(?![a-z])", text):
            return True
    return False


def pick_icon(label, sub, inside_aws):
    title = " " + label.lower().strip() + " "
    body = " " + sub.lower().strip() + " "

    for name, keys in SERVICES:
        if any(k in title for k in keys):
            return name
    for name, keys in OUTCOMES:
        if _hit(title, keys):
            return name
    if title.strip().endswith("?"):
        return "branch"
    for name, keys in ROLES:
        if _hit(title, keys):
            return name
    for name, keys in KEYWORDS:
        if _hit(title, keys):
            return name
    for name, keys in SERVICES:
        if any(k in body for k in keys):
            return name
    for name, keys in ROLES:
        if _hit(body, keys):
            return name
    for name, keys in KEYWORDS:
        if _hit(body, keys):
            return name
    for name, keys in OUTCOMES:
        if _hit(body, keys):
            return name
    return "compute" if inside_aws else "external"


TEXT_RE = re.compile(
    r'<text\b((?:"[^"]*"|\'[^\']*\'|[^>])*)>(.*?)</text>', re.S)
RECT_RE = re.compile(r'<rect\b((?:"[^"]*"|\'[^\']*\'|[^>])*?)/?>')
ENT = re.compile(r"&[#\w]+;")
TAGS = re.compile(r"<[^>]+>")


def _plain(s):
    return ENT.sub(" ", TAGS.sub("", s)).strip()


def _font_size(attrs, css_sizes, cls):
    fs = _fnum(attrs, "font-size")
    if fs:
        return fs
    for c in cls:
        if c in css_sizes:
            return css_sizes[c]
    return 12.0


def _css_font_sizes(svg):
    sizes = {}
    for m in re.finditer(r"([^{}]+)\{([^{}]*)\}", " ".join(
            re.findall(r"<style[^>]*>(.*?)</style>", svg, re.S))):
        fs = re.search(rf"font-size\s*:\s*({NUM})", m.group(2))
        if not fs:
            continue
        for sel in re.findall(r"\.([\w-]+)", m.group(1)):
            sizes[sel] = float(fs.group(1))
    return sizes


def _classes(attrs):
    m = re.search(r'class=["\']([^"\']*)["\']', attrs)
    return m.group(1).split() if m else []



INJECTED_ACCENT = re.compile(
    r'<line x1="[-\d.]+" y1="[-\d.]+" x2="[-\d.]+" y2="[-\d.]+" stroke="#[0-9A-Fa-f]{6}" '
    r'stroke-width="3\.4" stroke-linecap="round" opacity="0\.95"/>')
INJECTED_TILE = re.compile(
    r'<g transform="translate\([-\d.]+,[-\d.]+\)" aria-hidden="true"><rect width="[\d.]+" '
    r'height="[\d.]+" rx="[\d.]+" fill="#[0-9A-Fa-f]{6}"/><g transform="scale\([\d.]+\)">.*?</g></g>',
    re.S)


def strip_injected(svg):
    return INJECTED_TILE.sub("", INJECTED_ACCENT.sub("", svg))

def add_icons(svg, seen_cats):
    """Append accent bars + service tiles for each component box."""
    svg = strip_injected(svg)
    sizes = _css_font_sizes(svg)

    texts = []
    for m in TEXT_RE.finditer(svg):
        a = m.group(1)
        x, y = _fnum(a, "x"), _fnum(a, "y")
        if x is None or y is None:
            continue
        body = _plain(m.group(2))
        if not body:
            continue
        anchor = "middle" if 'text-anchor="middle"' in a else (
            "end" if 'text-anchor="end"' in a else "start")
        cls = _classes(a)
        fs = _font_size(a, sizes, cls)
        bold = ("font-weight" in a and re.search(r'font-weight=["\'](600|700|bold)', a)) or \
               any(c in sizes and False for c in cls) or fs >= 13
        texts.append(dict(x=x, y=y, s=body, anchor=anchor, fs=fs, bold=bold))

    # dashed containers -> "this box is inside the AWS account"
    containers = []
    boxes = []
    for m in RECT_RE.finditer(svg):
        a = m.group(1)
        x, y = _fnum(a, "x"), _fnum(a, "y")
        w, h = _fnum(a, "width"), _fnum(a, "height")
        if None in (x, y, w, h):
            continue
        cls = " ".join(_classes(a))
        dashed = "stroke-dasharray" in a or "container" in cls or "lane" in cls
        if dashed and w > 300 and h > 140:
            containers.append((x, y, w, h))
        else:
            boxes.append((x, y, w, h, a, m.start()))

    add = []
    for (x, y, w, h, a, _at) in boxes:
        if w < 96 or h < 38:
            continue
        inner = [t for t in texts if x + 2 <= t["x"] <= x + w - 2 and y <= t["y"] <= y + h + 2]
        if not inner:
            continue
        inner.sort(key=lambda t: t["y"])
        title = max(inner, key=lambda t: (t["fs"], -t["y"]))
        sub = " ".join(t["s"] for t in inner if t is not title)
        inside = any(cx <= x and cy <= y and x + w <= cx + cw and y + h <= cy + ch
                     for (cx, cy, cw, ch) in containers)
        name = pick_icon(title["s"], sub, inside)
        if name not in GLYPHS:
            name = "compute" if inside else "external"
        cat = category_of(name)
        col = CAT[cat]
        seen_cats.add(cat)

        # accent rule along the top edge of the box
        add.append(
            f'<line x1="{x + 3:.1f}" y1="{y + 2:.1f}" x2="{x + w - 3:.1f}" y2="{y + 2:.1f}" '
            f'stroke="{col}" stroke-width="3.4" stroke-linecap="round" opacity="0.95"/>')

        # service tile, only where it cannot collide with the label
        top = min(t["y"] for t in inner)
        if h >= 66:
            size, inset = 24.0, 11.0
        elif h >= 50:
            size, inset = 18.0, 8.0
        else:
            size, inset = 15.0, 6.0
        tx, ty = x + inset, y + inset
        room = True
        for t in inner:
            width = len(t["s"]) * t["fs"] * 0.52
            left = t["x"] - width / 2 if t["anchor"] == "middle" else (
                t["x"] - width if t["anchor"] == "end" else t["x"])
            if t["y"] - t["fs"] < ty + size and t["y"] + 3 > ty and left < tx + size + 6:
                room = False
                break
        if room and top - 3 > ty:
            add.append(tile(name, tx, ty, size, 4.5))

    if not add:
        return svg
    return re.sub(r"</svg>\s*$", "".join(add) + "</svg>", svg, count=1)


def transform(svg):
    cats = set()
    svg = recolour(svg)
    svg = add_icons(svg, cats)
    return svg, cats


SVG_RE = re.compile(r"<svg\b.*?</svg>", re.S)


def transform_page(html):
    cats = set()

    def one(m):
        out, c = transform(m.group(0))
        cats.update(c)
        return out

    return SVG_RE.sub(one, html), cats
