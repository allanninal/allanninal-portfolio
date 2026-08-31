"""Builders for the two posts whose shape is the same in every series.

Parts 1 to 5 are the design and are written per system. Part 6 (what it costs)
and part 7 (engineering reference) are genuinely the same shape every time --
the same AWS bill, the same five sections of reference -- so they are built
from a compact config instead of being retyped and drifting.
"""

PAL = {"read": "#01A88D", "mail": "#E7157B", "store": "#7AA116",
       "fixed": "#FF9900", "other": "#7D8CA3", "ocr": "#8C4FFF",
       "sms": "#DD344C", "poll": "#4A90D9"}

FIXED = 0.86  # Secrets Manager ($0.40) + two AWS Budgets actions ($0.46)


# --------------------------------------------------------------------------
def cost_part(*, slug, name, unit, volumes, read_each, msgs_each=3.0,
              store_base=0.28, store_growth=0.00016, extra=(), lede, risks,
              takeaway_extra=None, per_unit_note=None, next_line=None):
    """Part 6. `volumes` is [(count, label)]; `extra` is [(key, label, colour,
    per-unit cost, flat cost)] for anything this system pays that the base
    design does not -- Textract, SNS SMS, a polled endpoint."""
    tiers, series = [], []
    keys = [("read", "Bedrock &mdash; one read per " + unit, PAL["read"]),
            ("mail", "SES &mdash; asks, results, receipts", PAL["mail"]),
            ("store", "S3 + DynamoDB", PAL["store"]),
            ("fixed", "Fixed &mdash; Secrets Manager, Budgets", PAL["fixed"]),
            ("other", "Lambda, SQS, CloudWatch", PAL["other"])]
    for k, label, col, _per, _flat in extra:
        keys.insert(2, (k, label, col))
    series = [(k, label, col) for k, label, col in keys]

    for n, label in volumes:
        parts = [("read", round(n * read_each, 2)),
                 ("mail", round(n * msgs_each * 0.0001 + n * 0.0005, 2)),
                 ("store", round(store_base + n * store_growth, 2)),
                 ("fixed", FIXED),
                 ("other", round(0.10 + n * 0.00085, 2))]
        for k, _l, _c, per, flat in extra:
            parts.insert(2, (k, round(flat + n * per, 2)))
        tiers.append({"label": label, "parts": parts})

    mid = tiers[len(tiers) // 2]
    mid_total = sum(v for _, v in mid["parts"])
    hi_total = sum(v for _, v in tiers[-1]["parts"])

    rows = [["Bedrock read", f"${mid['parts'][0][1]:.2f}",
             f"Linear. One call per {unit}, roughly 1,800 in and 200 out tokens."],
            ["SES", f"${[v for k, v in mid['parts'] if k == 'mail'][0]:.2f}",
             f"Linear. About {msgs_each:g} messages per {unit}."],
            ["DynamoDB + S3", f"${[v for k, v in mid['parts'] if k == 'store'][0]:.2f}",
             "Storage grows with what you retain, not with throughput."],
            ["Lambda + SQS", "$0.12",
             "Linear, and effectively free at this scale."],
            ["CloudWatch", "$0.16", "Flat, if you set retention. Unbounded if you do not."],
            ["Secrets Manager", "$0.40", "Flat. One secret, $0.40 a month."],
            ["AWS Budgets", "$0.46", "Flat. Two actions, so you find out before the bill does."]]
    for k, label, _c, per, flat in extra:
        rows.insert(1, [label.split(" &mdash;")[0], f"${[v for kk, v in mid['parts'] if kk == k][0]:.2f}",
                        f"Linear at ${per:.4f} per {unit}." if per else "Flat."])

    takeaways = [
     f"About ${mid_total:.0f} a month at {mid['label']}. Roughly ${hi_total:.0f} at "
     f"{tiers[-1]['label']}.",
     f"One Bedrock read per {unit} is the only line that scales. Everything else is rounding.",
     "Nothing is always-on, so a quiet month genuinely costs almost nothing.",
     "The duplicate test runs before the read, so resends are free.",
     "The three real risks: a retry loop, storage nobody expires, and a bigger model than the "
     "job needs.",
    ]
    if takeaway_extra:
        takeaways.insert(3, takeaway_extra)

    blocks = [
     ("h2", "The bill at three volumes"),
     ("p", "These are US East prices at the time of writing, at three volumes that bracket "
           "most small businesses. Find the bar closest to your own and read across."),
     ("fig", ("bars", {"tiers": tiers, "series": series,
                       "note": "The read is the only bar that grows with the business. The "
                               "orange fixed band never moves."}),
      f"The monthly bill at three volumes. The teal band &mdash; one model read per {unit} "
      f"&mdash; is the only part that grows; the orange fixed band is the same 86 cents at "
      f"every volume.",
      f"Monthly cost of the {name.lower()} at three volumes",
      f"A stacked bar chart with three bars, one per volume tier: {tiers[0]['label']} totalling "
      f"about ${sum(v for _, v in tiers[0]['parts']):.0f}, {mid['label']} totalling about "
      f"${mid_total:.0f}, and {tiers[-1]['label']} totalling about ${hi_total:.0f}. Each bar is "
      f"stacked from bands. The largest and fastest-growing is Bedrock, one read per {unit}, in "
      f"teal. Then SES for the messages, in pink. Then S3 and DynamoDB storage in green. Then a "
      f"fixed orange band for Secrets Manager and AWS Budgets, which is eighty-six cents at "
      f"every volume. Then a grey band for Lambda, SQS and CloudWatch. A note says the read is "
      f"the only bar that grows with the business and the orange band never moves."),
     ("h2", "Line by line"),
     ("table", ["Line", f"At {mid['label']}", "How it scales"], rows),
     ("p", per_unit_note or
      "The Bedrock line assumes one read against a small, fast model &mdash; the cheapest one "
      "that can do the extraction reliably, which is not a frontier model. Part 7 names the "
      "exact model id. Swapping it for something larger is the fastest way to multiply this "
      "bill for no measurable gain, because the task is extraction, not reasoning."),
     ("h2", "The three ways this bill surprises you"),
     ("p", "Every one of these has happened to somebody, and all three are cheap to prevent."),
     ("ul", list(risks)),
     ("h2", "What it costs when nothing happens"),
     ("p", "This matters more than the headline number for a seasonal business. In a month "
           "with nothing to process the bill is the fixed band: Secrets Manager at forty "
           "cents, AWS Budgets at forty-six, and a few cents of storage. Call it a dollar. "
           "There is no instance to stop and nothing to remember to turn off."),
     ("fig", ("strip", {
        "stages": [{"title": "Quiet month", "sub": ["~$1"], "icon": "clock"},
                   {"title": tiers[0]["label"], "sub": [f"~${sum(v for _, v in tiers[0]['parts']):.0f}"],
                    "icon": "form"},
                   {"title": mid["label"], "sub": [f"~${mid_total:.0f}"], "icon": "money"},
                   {"title": tiers[-1]["label"], "sub": [f"~${hi_total:.0f}"], "icon": "counter"},
                   {"title": "One bad loop", "sub": ["~$200"], "icon": "alarm"}],
        "title": "THE BILL, AT A GLANCE",
        "note": "Four of these are the design working. The fifth is a missing dead-letter queue."}),
      "The bill at a glance, including the one that is not a volume at all. A retry loop with "
      "no dead-letter queue costs more than every legitimate use of the system put together.",
      "The monthly bill at four volumes plus one failure mode",
      f"A horizontal row of five boxes. Quiet month, about one dollar. {tiers[0]['label']}, "
      f"about ${sum(v for _, v in tiers[0]['parts']):.0f}. {mid['label']}, about "
      f"${mid_total:.0f}. {tiers[-1]['label']}, about ${hi_total:.0f}. And one bad retry loop, "
      f"about two hundred dollars. A note says four of these are the design working and the "
      f"fifth is a missing dead-letter queue."),
     ("callout", "Set these on day one", [
      "A dead-letter queue on every SQS queue, with a maximum receive count of three.",
      "Thirty-day retention on every CloudWatch log group. There is no default that is safe.",
      "An S3 lifecycle rule on the object prefix, tiering at 90 days and expiring at your "
      "actual record-keeping horizon.",
      "Two AWS Budgets actions &mdash; one that emails at half your expected spend, one at "
      "double it. The second is how you find out about a loop in an hour instead of a month.",
      "Provisioned concurrency: none. Nothing here is latency-sensitive enough to justify "
      "paying for a warm function.",
     ]),
     ("p", next_line or "Next: the same system drawn for engineers &mdash; service names, "
                        "resource identifiers, IAM scopes, table schemas and the model id."),
    ]
    return {
     "slug": f"what-the-{slug}-costs",
     "title": f"What the {name.lower()} costs",
     "nav": "What it costs",
     "read": 5, "words": 820,
     "desc": (f"About ${mid_total:.0f} a month at {mid['label']}. Where every cent goes, "
              f"which line grows with volume, and the three ways this bill could surprise you."),
     "og": (f"One model read per {unit} is the whole bill. Everything else -- the queue, the "
            f"table, the mail, the storage -- rounds to nothing at small-business volume."),
     "abstract": (f"About ${mid_total:.0f} a month. One Bedrock read per {unit} is the only "
                  f"line that grows; the queue, the table, the mail and the storage are "
                  f"rounding errors. Plus the three ways the bill could surprise you."),
     "lede": lede,
     "tags": ["AWS cost", "serverless pricing", "AWS Bedrock", "Lambda", "DynamoDB",
              "small business"],
     "takeaways": takeaways,
     "blocks": blocks,
    }


# --------------------------------------------------------------------------
def reference_part(*, slug, name, prefix, lede, outside, inside, note,
                   diagram_desc, functions, roles, tables, inbound, model_notes,
                   gotchas, region="us-east-1", region_why=None, takeaways=None):
    """Part 7. Same five sections every time: the service-name diagram, region
    and account, the Lambda inventory, IAM, the schemas, and the model call."""
    blocks = [
     ("h2", "The system, by service name"),
     ("fig", ("system", {"outside": outside, "inside": inside, "note": note,
                         "edges": [{"from": 0, "to": 0, "label": "in"},
                                   {"from": 1, "to": 1, "label": "grounds"},
                                   {"from": 2, "to": 2, "label": "out", "up": True}]}),
      "The same shape as Part 1 with the service names filled in. Nothing here is new; it is "
      "the same three groups, named.",
      f"The {name.lower()} drawn with AWS service names", diagram_desc),
     ("h2", "Region and account"),
     ("ul", [
      f"<strong>Region:</strong> <code>{region}</code>. " + (region_why or
      "Chosen because SES inbound receipt rules exist in only a subset of regions and this one "
      "has the widest Bedrock model availability. If your data has to stay elsewhere, check "
      "both constraints before moving: inbound SES is the binding one."),
      "<strong>Account:</strong> one. This is a small system, and a separate account per "
      "environment costs more in wiring than it saves. A <code>dev</code> and a "
      "<code>prod</code> stack in the same account, with distinct resource prefixes, is the "
      "right size here.",
      "<strong>Everything is regional.</strong> The only global resources are the IAM roles "
      "and policies. There is no CloudFront, no global table and no cross-region replication, "
      "because nothing here has a latency or durability requirement that would justify them.",
     ]),
     ("h2", "Lambda inventory"),
     ("table", ["Function", "Trigger", "Does", "Timeout / memory"], functions),
     ("p", "Splitting this into separate functions is not about modularity. It is that only "
           "one of them needs Bedrock permissions and only one is reachable from the public "
           "internet, and neither of those is true if it is one handler behind a router."),
     ("h2", "IAM, scoped"),
     ("table", ["Role", "Allowed", "On"], roles),
     ("p", "No role has a <code>Resource: \"*\"</code> on anything that writes, and every "
           "<code>GetSecretValue</code> grant names a single secret arn. That is why there is "
           "more than one secret rather than one JSON blob with everything in it."),
     ("h2", "DynamoDB schemas"),
    ]
    for title, body in tables:
        blocks += [("h3", title), ("pre", body)]
    blocks += [
     ("h2", "Inbound and outbound"),
     ("ul", list(inbound)),
     ("h2", "The model call"),
     ("ul", list(model_notes)),
     ("callout", "Things worth knowing before you build it", list(gotchas)),
     ("p", "That is the whole system. Seven posts, one diagram at a time, and nothing in it "
           "that needs a server."),
    ]
    return {
     "slug": f"{slug}-engineering-reference",
     "title": f"Engineering reference: the {name.lower()} architecture",
     "nav": "Reference",
     "read": 7, "words": 1050,
     "desc": (f"The {name.lower()} drawn for engineers: service names, region, the Lambda "
              f"inventory, IAM scopes, DynamoDB schemas and the Bedrock model id."),
     "og": ("Service names, resource identifiers, table schemas, IAM scopes and the model id "
            "-- everything an engineer would need to rebuild it."),
     "abstract": ("Same system, drawn purely for engineers. Service names, region, Lambda "
                  "inventory, IAM scopes, the schemas and the exact model id."),
     "lede": lede,
     "tags": ["AWS architecture", "Lambda", "DynamoDB", "Amazon SES", "IAM", "AWS Bedrock",
              "engineering reference"],
     "takeaways": takeaways or [
      "Single region, single account. Every resource is regional; nothing is global except the "
      "IAM roles.",
      f"{len(functions)} Lambda functions, each with its own execution role. No shared role, "
      "no wildcards on resources.",
      f"{len(tables)} DynamoDB tables, each keyed so the concurrency story is a condition "
      "expression rather than a lock.",
      "One Bedrock model, called once, with a JSON schema it must fill or leave null.",
      "Nothing always-on: no instance, no container, no provisioned capacity.",
     ],
     "blocks": blocks,
    }
