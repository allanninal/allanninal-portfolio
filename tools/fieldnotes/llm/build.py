#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_section import build
from visuals import apply as apply_visuals

# Batches are discovered, not listed: this section is written a few notes at a
# time and each batch arrives as its own guides_<letter>.py. Sorted so the index
# order is stable between builds.
import importlib
GUIDES = []
for _m in sorted(q.stem for q in Path(__file__).resolve().parent.glob("guides*.py")):
    GUIDES.extend(importlib.import_module(_m).GUIDES)

CFG = {
  "section": "llm",
  "date": "2026-08-30",
  "nav": [("/", "Portfolio"), ("/stripe/", "Stripe"), ("/aws/", "AWS cost")],
  "footer_note": "Every script in this section is read only. They hold a key that can spend "
                 "money on inference, so none of them writes: they report what is wrong and "
                 "print the repair for you to run. A restricted or admin-read key is enough.",
  "index_title": "LLM API Fix Guides: OpenAI and Anthropic",
  "index_desc": "OpenAI and Anthropic problems a read-only script can find: retired models, "
                "runaway spend, rate limits misread as quota, and structured output that "
                "silently truncates.",
  "index_h1": "LLM API fix guides",
  "index_lead": "An LLM API bills you whether or not the answer was any good, and most of the "
                "ways it goes wrong do not raise an exception. A model id retires on a date "
                "nobody diaried, a response is cut off mid-JSON because nobody checked "
                "<code>finish_reason</code>, a retry storm triples the invoice. Each note here "
                "explains one such problem and gives you a script that finds it through the API.",
  "index_chips": ["Read-only key", "Python and Node.js", "Tests included"],
  "scope_title": "Why these scripts never write",
  "scope_body": "<p>A script here holds a key that can spend real money on inference. So these "
                "read, they tell you exactly what is wrong, and they print the repair: the "
                "endpoint, the parameter, the model id to migrate to. You run it.</p>"
                "<p>Several of them want an <strong>admin or organization-scoped read key</strong> "
                "rather than a project key, because usage and cost live on the organization. "
                "Each note says which it needs.</p>",
  "group_heading": "OpenAI and Anthropic",
}

build(CFG, apply_visuals(CFG["section"], GUIDES))
