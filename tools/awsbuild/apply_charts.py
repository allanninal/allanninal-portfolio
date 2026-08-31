"""Colour the /build cost charts by AWS service instead of grey hatch patterns.

The cost pages draw a stacked bar per volume tier, one <pattern> per cost line
("bedrock", "textract", "fixed", ...). Hatch fills read as noise on a dark
plate; a solid service colour makes the dominant cost obvious at a glance and
matches the icon colours used in the architecture diagrams above it.
"""
import pathlib
import re
import sys

SERIES = [
    ("#ED7100", ("lambda", "compute", "fargate", "ec2", "runtime")),
    ("#01A88D", ("bedrock", "model", "llm", "claude", "ai", "inference", "sagemaker")),
    ("#8C4FFF", ("textract", "ocr", "transcribe", "rekognition", "comprehend", "polly",
                 "translate", "vision", "speech", "network", "transfer", "cloudfront")),
    ("#7AA116", ("s3", "storage", "bucket", "glacier", "efs")),
    ("#C925D1", ("dynamo", "ddb", "database", "rds", "aurora", "table", "db")),
    ("#E7157B", ("ses", "sns", "sqs", "email", "mail", "eventbridge", "events", "queue",
                 "messaging", "notify", "sms", "twilio")),
    ("#4A90D9", ("apigw", "gateway", "api", "http", "url", "route53", "dns")),
    ("#DD344C", ("cloudwatch", "logs", "monitor", "secrets", "kms", "waf", "security")),
    ("#FF9900", ("fixed", "base", "baseline", "always", "budget", "subscription")),
    ("#7D8CA3", ("other", "rest", "misc", "everything", "remainder", "else")),
]
FALLBACK = ["#ED7100", "#01A88D", "#8C4FFF", "#7AA116", "#C925D1",
            "#E7157B", "#4A90D9", "#DD344C", "#FF9900", "#7D8CA3"]

SVG_RE = re.compile(r"<svg\b.*?</svg>", re.S)
NEUTRAL = "#7D8CA3"


def colour_for(series, i):
    s = series.lower()
    for col, keys in SERIES:
        if any(k in s for k in keys):
            return col
    return FALLBACK[i % len(FALLBACK)]


def do_svg(svg):
    ids = re.findall(r'<pattern id="([\w-]+)"', svg)
    if not ids:
        return svg, False
    used = {}
    for i, pid in enumerate(ids):
        series = pid.rsplit("-", 1)[-1]
        used[pid] = colour_for(series, i)

    def swap(m):
        pid = m.group(2)
        if pid not in used:
            return m.group(0)
        return f'{m.group(1)}="{used[pid]}"'

    out = re.sub(r'(fill|stroke)="url\(#([\w-]+)\)"', swap, svg)

    # the "everything else" band is a plain class fill, not a pattern
    out = re.sub(r'(\.[\w-]*(?:other|rest|misc)\s*\{[^}]*?fill\s*:\s*)#[0-9a-fA-F]{3,6}',
                 lambda m: m.group(1) + NEUTRAL, out)

    # patterns are dead weight once the fills are solid
    out = re.sub(r"<pattern id=\"[\w-]+\".*?</pattern>\s*", "", out, flags=re.S)
    out = re.sub(r"<defs>\s*</defs>\s*", "", out)
    return out, out != svg


def main(root="build"):
    pages = 0
    for f in sorted(pathlib.Path(root).rglob("*.html")):
        s = f.read_text(encoding="utf-8")
        if "<pattern id=" not in s:
            continue
        hit = [False]

        def one(m):
            out, ch = do_svg(m.group(0))
            hit[0] |= ch
            return out

        out = SVG_RE.sub(one, s)
        if hit[0]:
            f.write_text(out, encoding="utf-8")
            pages += 1
    print("cost charts coloured on", pages, "pages")


if __name__ == "__main__":
    main(*sys.argv[1:])
