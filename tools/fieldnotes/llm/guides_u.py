#!/usr/bin/env python3
"""/llm/ field notes, batch U — the writing.

Four surfaces closing, which is not four models retiring. A model id that dies
is a one-line diff: find the string, write the successor, deploy. None of these
four is that. An endpoint sunset needs an export or a rewrite, and the four here
were chosen because each one needs a *different* one.

The hazard is obvious from the outside: all four ask "does this endpoint still
answer", and asked four times that is one note about curl. So none of these
scripts grades a status code on its own, and no two of them grade the same kind
of pair.

`assistants-api-already-shut-down` is the only one whose date is in the past, so
its polarity is inverted: a 404 is the documented, expected answer and is not
the finding. A **200 is**, because it means this organization still has grace
access to an API that is over. A 404 on its own cannot tell a closed path from a
key that reads nothing, so the pair is the subject path against a **control
path on the same credential** — the path varies, the key and the headers do not.
The probe measures whether the endpoint answers today; it cannot date an
outage, and the usage cliff that dates it is reported separately and called an
inference in those words.

`sora-videos-api-no-replacement` is the only closure in the batch with nothing
to migrate to, which makes it the only one where the repair is not a migration.
Its `replacement_for()` returns `None` for every id and its replacement table is
empty on purpose, with a test that says so, because the failure mode for this
note is a script that helpfully invents a successor. What it grades instead is
**two clocks**: the endpoint's shutdown date, and each rendered asset's own
`expires_at`, which for some assets lands first. After either one you cannot
even download what you already paid to generate.

`prompts-evals-agentbuilder-sunset` is the only one about **content held on the
provider's side** rather than code in your tree, so its unit is exportability
and not validity. Three surfaces close on one date and the API reaches exactly
one of them: `GET /v1/evals` lists the full eval objects, which makes the
listing itself the export. Reusable prompts have no documented list endpoint at
all, so the script probes and grades the status rather than asserting one, and
falls back to the `pmpt_` ids in your own call sites. Agent Builder has no REST
surface whatsoever, and the script says so and assigns it to a person instead of
pretending to cover it.

`fine-tuning-jobs-blocked` is the only one where the endpoint keeps working for
one verb and stops for the other. Creating a job and serving a fine-tune are two
verbs on one resource with two different deadlines, and the create side is not a
date at all: from 2026-07-02 eligibility depends on **your own recent
inference**, which is readable, so the script computes a clock rather than
reading one. It never submits a job to find out. That would be the one thing a
script in this section must not do, and the eligibility function takes only
readable inputs so that a test can hold it to that.

Where these stop and the published notes start, since three of them live next
door to notes that already exist. `retired-model-id-still-in-code` and
`model-past-shutdown-date` own diffing the model strings in your configuration
against the model list. Nothing here does that: batch U owns **endpoints**, and
the only model ids it reads are the five Sora ids named in the deprecation table
and the base a fine-tuning job already recorded for itself. Neither is a config
scan. And `fine-tuned-model-never-used` owns a trained model nobody calls,
where zero traffic is waste; here the same zero is an eligibility clock that has
already closed the create verb. Same number, opposite meaning, different repair,
and the note says so out loud.

Read only, and stricter than the section baseline: every request in this batch
is a GET. Nothing creates an assistant, a video, an eval or a fine-tuning job to
find out whether the endpoint would still accept one — a note about a surface
that stopped accepting work has to detect that from readable state and printed
evidence, or it does not get written.

Dates and endpoint shapes were checked against the OpenAI deprecations page and
the API reference index on 2026-08-31. Four things came back different from the
research notes and are written the way the sources have them: the Assistants
announcement is 26 August 2025, not the 20th; there is no documented REST
endpoint for reusable prompts; Agent Builder has no REST surface at all; and the
2026-07-02 fine-tuning restriction is narrower and far more useful than
"inactive organizations", because "has not run inference on a fine-tuned model
in the past 60 days" is a thing a read-only script can measure.
"""

CITE_DEPRECATIONS = ("Deprecations — OpenAI platform docs",
                     "https://developers.openai.com/api/docs/deprecations")
CITE_MODELS = ("Models — OpenAI API reference",
               "https://platform.openai.com/docs/api-reference/models")
CITE_MODEL_OBJ = ("Retrieve model, including the shutdown_date field",
                  "https://developers.openai.com/api/docs/api-reference/models/retrieve")
CITE_USAGE = ("Usage, completions — OpenAI API reference",
              "https://platform.openai.com/docs/api-reference/usage/completions")
CITE_COSTS = ("Costs — OpenAI API reference",
              "https://platform.openai.com/docs/api-reference/usage/costs")
CITE_ADMIN = ("Admin APIs — OpenAI platform docs",
              "https://developers.openai.com/api/docs/guides/admin-apis")
CITE_RESPONSES = ("Migrate to the Responses API — OpenAI platform docs",
                  "https://developers.openai.com/api/docs/guides/migrate-to-responses")
CITE_CONVERSATIONS = ("Conversations — OpenAI API reference",
                      "https://developers.openai.com/api/docs/api-reference/conversations")
CITE_VIDEOS = ("List videos — OpenAI API reference",
               "https://developers.openai.com/api/docs/api-reference/videos/list")
CITE_EVALS = ("List evals — OpenAI API reference",
              "https://developers.openai.com/api/docs/api-reference/evals/list")
CITE_FINETUNE = ("Fine-tuning jobs — OpenAI API reference",
                 "https://developers.openai.com/api/docs/api-reference/fine-tuning/list")

REL_ASSISTANTS = ("/llm/assistants-api-already-shut-down/",
                  "The same closure one date earlier, and already past it")
REL_SORA = ("/llm/sora-videos-api-no-replacement/",
            "The closure with no successor, and an asset clock of its own")
REL_EXPORT = ("/llm/prompts-evals-agentbuilder-sunset/",
              "Three more surfaces closing, where the content is the thing at risk")
REL_FTGATE = ("/llm/fine-tuning-jobs-blocked/",
              "One resource, two verbs, and only one of them still accepted")
REL_ZERO_BUCKETS = ("/llm/live-project-zero-usage-buckets/",
                    "The same hole in the usage report, read as a dead deploy")
REL_PAST_DATE = ("/llm/model-past-shutdown-date/",
                 "A date already passed, for a model id rather than a path")
REL_90_DAYS = ("/llm/model-retiring-within-90-days/",
               "The diary entry version, for ids rather than endpoints")
REL_MEDIA_COST = ("/llm/audio-and-image-line-items-unnoticed/",
                  "What the cost report calls the media you generate")
REL_VS_EXPIRY = ("/llm/vector-store-expired-or-expiring/",
                 "Another stored object that deletes itself on a schedule")
REL_CACHE_NEVER = ("/llm/prompt-caching-never-used/",
                   "Prompt caching, which is a different thing from a stored prompt")
REL_FT_UNUSED = ("/llm/fine-tuned-model-never-used/",
                 "The other half of the lifecycle: trained, paid for, never called")

GUIDES = [
{
"slug": "assistants-api-already-shut-down",
"title": "The Assistants API is shut down. Is yours still answering?",
"description": "Past a shutdown date a 404 is the expected answer and a 200 is the finding. Probe /v1/assistants against a control path, then date the outage.",
"h1": "The Assistants API is shut down. Is yours still answering?",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["assistants api shutdown 2026-08-26 404",
             "openai assistants threads runs deprecated migration",
             "migrate assistants api to responses conversations",
             "OpenAI-Beta assistants=v2 stopped working",
             "assistants api grace period still returns 200"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project read key, used only for GETs of /v1/assistants and /v1/models. Optionally OPENAI_ADMIN_KEY with api.usage.read, which is the only way to date the outage rather than merely observe it.",
"lead": "The pipeline has not run since Wednesday and the error is a 404 on a path that has been in the codebase for two years. Somebody checks the model id first, because that is what a 404 usually means, and the model id is fine. It is fine because the model was never the problem: the whole <code>/v1/assistants</code> family reached its published shutdown date on 26 August 2026 and the endpoint is simply not there any more. The uncomfortable part comes an hour later, when the same probe run against the staging organization returns <code>200</code>, and now you have two organizations, one dead API, and a question nobody wants to answer about how long the other one has.",
"short_answer": """<p>Read the polarity backwards, because the date is in the past. Every other deprecation note in this section treats a 404 as the alarm. Here a <code>404</code> is the <strong>documented, expected answer</strong> and is not a finding at all. The finding is a <code>200</code>: an organization that still gets a list object back from <code>GET /v1/assistants</code> five days after the shutdown is running on grace, not on support, and the next thing that changes is not announced.</p>
<p>One status code cannot carry that, because a 404 from a closed path and a 404 from a key that reads nothing are the same number. So the script grades a <strong>pair</strong>: the subject path <code>/v1/assistants</code> and a control path <code>/v1/models</code>, on the same key, with the same headers, in the same run. What varies is the path and only the path. Control 200 with subject 404 is a real closure. Control not-200 makes the whole reading worthless and the script says so instead of grading the rest.</p>
<p>A probe cannot date anything. It tells you what the endpoint does now, not when it stopped, and "when" is the question that separates a shutdown from a bad deploy on the same afternoon. That comes from a second, weaker reading with an <strong>admin-read key</strong>: <code>GET /v1/organization/usage/completions</code> with <code>bucket_width=1d</code> and <code>group_by[]=project_id</code> over the last 30 days. A project whose <code>num_model_requests</code> falls to zero <em>on 2026-08-26 specifically</em> lost its traffic to the shutdown. One that fell to zero on the 19th lost it to something you did.</p>
<p>The script keeps those two readings apart on the page and in the output, because one is a measurement and the other is an inference. It also refuses the flattering middle case: a project that also serves other traffic shows a dip on the date, not a cliff, and a dip is reported as a dip.</p>
<p>The repair is a rewrite, not a swap. Assistants, threads, runs and run steps become <code>POST /v1/responses</code> carrying a <code>conversation</code> id from the Conversations API, and the <code>OpenAI-Beta: assistants=v2</code> header goes away entirely. There is no model id to change, which is exactly why the model id was the wrong thing to check first.</p>""",
"problem": """<p>The Assistants API was announced for retirement on 26 August 2025 with a full year of notice and shut down on 26 August 2026. It was not one endpoint. Assistants, threads, messages, runs and run steps were a whole object model, and code written against it does not resemble the thing that replaced it: the Responses API plus the Conversations API keep the state but not the shape. So the migration is a rewrite of a call graph, which is why a year was not obviously too much notice and why some organizations still have not done it.</p>
<p>What makes it a field note rather than a calendar entry is that the shutdown does not land everywhere at once. Access after a published date is a matter of what the provider is still routing for whom, and organizations discover on different days. That produces the specific, miserable situation this note exists for: production is 404ing, staging is fine, and the difference between them is not a config value anybody can find. It is grace, and grace has no expiry you can read.</p>
<p>The failure is also badly disguised. A 404 on <code>/v1/threads/{id}/runs</code> looks exactly like a mistyped id, exactly like a deleted thread, and exactly like a model that does not exist — the SDKs raise the same <code>NotFoundError</code> for all of them. The first hour of the investigation goes into the id, because ids are what 404s are usually about. Nothing in the error body says "this API is over".</p>
<p>And the aggregate hides the moment it happened. Assistants runs billed as ordinary model requests, so a project's usage report shows the outage as a number going to zero among other numbers that did not, on a day that is not labelled. Nobody reads a usage report looking for a cliff unless somebody has already suggested there is one.</p>""",
"why": """<p><strong>Past the date, a 200 is the finding and a 404 is the baseline.</strong> This is the only note in the batch with that polarity and it changes what the script is for. It is not detecting a problem you already have; production told you about that. It is detecting the problem you do <em>not</em> have yet, in the organization that still answers, where nobody is looking because nothing is broken.</p>
<p><strong>A control path is what makes one 404 mean anything.</strong> Hold the credential, the headers and the host fixed, vary only the path, and the pair separates a closed endpoint from a key that cannot read. Without it a revoked key, a project-scoped credential and a shut-down API all produce the same evidence, and the script would confidently report a shutdown it has not observed.</p>
<p><strong>Dating an outage is a different question from observing one, and needs a different key.</strong> The probe answers "does it answer". Only the usage report answers "when did it stop", and it needs an admin-read credential the project key does not have. The script runs whichever readings it can and labels the ones it could not, because a missing admin key is a gap in coverage rather than a clean bill of health.</p>
<p><strong>A dip is not a cliff, and calling it one would be a lie the script cannot detect later.</strong> A project that ran assistants alongside ordinary completions loses part of its traffic on the date, not all of it. That is still evidence and it is weaker evidence, so it comes back as its own state with the reason attached. The temptation to round it up to a cliff is exactly how an inference gets published as a measurement.</p>
<p><strong>This note owns an endpoint family, not a model id.</strong> There are published notes that read <code>shutdown_date</code> off the model object and that diff your configured model strings against the model list. Neither one can see this: no model was retired, every id involved still resolves, and the thing that disappeared has no entry in <code>GET /v1/models</code> to check. That is the whole reason a surface closure needs its own note.</p>
<p><strong>The repair is a rewrite and the script does not pretend otherwise.</strong> There is no successor id to substitute. What gets printed is the shape of the change — runs become responses, threads become conversations, the beta header is deleted — plus the projects that still have traffic to move. A one-line diff would be the wrong output because it would be a false description of the work.</p>""",
"steps": [
 {"h": "Use a project read key, and know what each key can see",
  "body": """<p><code>OPENAI_API_KEY</code> reads the two listings. It cannot read organization usage, so the second half of the check needs <code>OPENAI_ADMIN_KEY</code> with <code>api.usage.read</code>. Run with only the project key and you learn whether the endpoint answers; add the admin key and you learn when it stopped. The script prints which of the two it did.</p>"""},
 {"h": "Probe the subject path and the control path in one run",
  "body": """<p><code>GET /v1/assistants?limit=1</code> and <code>GET /v1/models?limit=1</code>, same key, same headers. Do not raise on the 404 &mdash; it is the answer. Record the status and, where there is one, the <code>object</code> field on a 200 or the <code>error.code</code> on a failure.</p>"""},
 {"h": "Grade the pair, not either status",
  "body": """<p>Control 200 plus subject 404 is a confirmed closure. Control 200 plus subject 200 is grace access and is the finding worth acting on. Control anything else means the reading is void, and the script stops rather than reporting a shutdown it did not see.</p>"""},
 {"h": "Date the outage from the daily usage buckets",
  "body": """<p><code>GET /v1/organization/usage/completions?bucket_width=1d&amp;group_by[]=project_id</code> over 30 days. Fold the buckets into one series of <code>num_model_requests</code> per project per day, then look for the step and check whether it lands on 2026-08-26.</p>"""},
 {"h": "Print the rewrite, and print what was not proved",
  "body": """<p>Per project: the shape of the migration, and whether the evidence is a cliff, a dip, or nothing. For an organization still answering, print the sentence that matters &mdash; the date has passed, so this access is not a supported state and has no readable expiry.</p>"""},
],
"verify": """<p>After the migration, re-run. The subject probe should not change at all, because it never described your code; what should change is the usage series, which now shows the project's requests recovering on the day the Responses path shipped. The reading that will not improve is grace access, and it should not: the only thing that closes that finding is having nothing left behind the endpoint.</p>
<pre><code class="language-bash">OPENAI_API_KEY=sk-proj-... OPENAI_ADMIN_KEY=sk-admin-... \\
  python3 assistants_shutdown_probe.py --days 30
# shutdown 2026-08-26, 5 day(s) past
#   control  GET /v1/models      200  answering    200, and the response is list
#   subject  GET /v1/assistants  404  gone         404 model_not_found, which is what a
#                                                  closed path returns
# shut-down            the control path answers and the subject path does not, so this
#                      organization is past the 2026-08-26 shutdown
#   repair: runs become POST /v1/responses carrying a conversation id, threads become
#           POST /v1/conversations, and the OpenAI-Beta: assistants=v2 header is deleted
# proj_ab12            cliff-on-the-date  1,204 requests/day until 2026-08-25 and 0 from
#                      2026-08-26, which is the shutdown and not a deploy
# proj_cd34            dip-on-the-date    requests fell to 18% of the prior mean on
#                      2026-08-26, so part of this project was assistants traffic
# 3 finding(s)</code></pre>""",
"code_intro": "Two GETs, one optional report, and five pure functions. <code>days_past</code>, which is arithmetic against a published constant because no endpoint returns the date; <code>probe_state</code>, which says what one status means in isolation and refuses to say more, including the 429 case where a refusal proves the path is still routing; <code>access_verdict</code>, the only function that looks at both paths at once and the only one that can say the word shutdown; <code>cliff_verdict</code>, which grades a daily series into a cliff, a dip, or an admission that it cannot tell; and <code>repair_lines</code>, which prints the shape of a rewrite and never a model id, because there is not one.",
"py_file": "assistants_shutdown_probe.py",
"py": '''"""Probe an endpoint family that is already past its published shutdown date.

Read only. Every request is a GET: the assistants listing, a control listing of
models on the same key, and the organization usage report. Nothing here creates
an assistant, a thread or a run, and a 404 from a listing costs exactly as
little as a 200.

Past a shutdown date the polarity inverts. A 404 is the documented, expected
answer and is not the finding; a 200 is, because it means this organization
still has grace access to an API that is over. A 404 on its own cannot tell a
closed path from a key that reads nothing, so the unit here is a pair: the
subject path against a control path on the same credential, with the path as
the only thing that varies.

The probe measures whether the endpoint answers you today. It cannot date an
outage. That is what the usage report is for, and the two are reported
separately because one is a measurement and the other is an inference.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("assistants_shutdown_probe")

API = "https://api.openai.com/v1"
SUBJECT = "/assistants"
CONTROL = "/models"

# Announced 26 August 2025 with a year of notice; assistants, threads, messages,
# runs and run steps were replaced by the Responses API plus the Conversations
# API. The date is published and not readable -- no endpoint returns it, and
# nothing in GET /v1/models can see a path that no longer exists -- so it is a
# constant here and the note says where it came from.
SHUTDOWN = "2026-08-26"

# Live means the path still routes. A 429 is a refusal from something that
# exists, which is not the same as a 404 from something that does not.
LIVE = ("answering", "throttled")

FINDINGS = ("grace-access", "shut-down", "closed-early", "control-failed",
            "unreadable", "cliff-on-the-date", "dip-on-the-date")

REPAIRS = {
    "grace-access":
        "this organization still reaches an API that shut down on "
        + SHUTDOWN + ". That is grace, not support, and it has no expiry you "
        "can read. Move it now: runs become POST /v1/responses carrying a "
        "conversation id, threads become POST /v1/conversations, and the "
        "OpenAI-Beta header is deleted.",
    "shut-down":
        "runs become POST /v1/responses carrying a conversation id from "
        "POST /v1/conversations, and the OpenAI-Beta: assistants=v2 header is "
        "deleted. There is no model id to swap here, which is why checking the "
        "model id first never helps.",
    "closed-early":
        "the path is already gone and the published date has not arrived. "
        "Treat the date as the outside edge rather than the schedule.",
    "control-failed":
        "the control path did not answer either, so nothing was proved about "
        "the subject path. Fix the credential or the network and re-run before "
        "reading anything else here.",
    "cliff-on-the-date":
        "this project's traffic stopped on the shutdown date, so the outage is "
        "the closure and not a deploy. Migrate this project first: it has the "
        "most to move.",
    "dip-on-the-date":
        "part of this project's traffic stopped on the shutdown date. The "
        "project serves other work as well, so the assistants share is what "
        "needs migrating, not the whole project.",
}


def days_past(today, when=SHUTDOWN):
    """Whole days from a published date to today. Pure. Negative before it."""
    return (dt.date.fromisoformat(str(today))
            - dt.date.fromisoformat(str(when))).days


def probe_state(status, body=None):
    """What one listing's status means on its own. Pure. Returns (state, why).

    On its own is the operative phrase. A 404 from a path that is supposed to
    be gone and a 404 from a key that cannot see it are the same number, and
    only the pair in access_verdict() separates them.
    """
    if status is None:
        return ("unreachable", "no response at all from this path")
    status = int(status)
    body = body if isinstance(body, dict) else {}
    if status == 200:
        kind = body.get("object") or "a body with no object field"
        return ("answering", "200, and the response is %s" % kind)
    err = body.get("error") if isinstance(body.get("error"), dict) else {}
    code = err.get("code") or err.get("type") or "no error code"
    if status == 404:
        return ("gone", "404 %s, which is what a closed path returns" % code)
    if status in (401, 403):
        return ("credentials",
                "%d %s, so this probe says nothing about the path"
                % (status, code))
    if status == 429:
        return ("throttled",
                "429 %s, which is a refusal from a path that still routes"
                % code)
    return ("refused", "%d %s" % (status, code))


def access_verdict(subject, control, past):
    """Grade the subject path against the control path. Pure. (state, why).

    The only function here that looks at both paths at once, and the only one
    entitled to use the word shutdown. Everything upstream of it describes a
    single status code and stops.
    """
    if control not in LIVE:
        return ("control-failed",
                "the control path came back %s, so this key proves nothing "
                "about the subject path" % control)
    if subject in LIVE:
        if past >= 0:
            return ("grace-access",
                    "the subject path answered %d day(s) after its published "
                    "shutdown date, which is access on grace rather than a "
                    "supported state" % past)
        return ("still-open",
                "the subject path answers and the shutdown is %d day(s) away"
                % -past)
    if subject == "gone":
        if past >= 0:
            return ("shut-down",
                    "the control path answers and the subject path does not, "
                    "so this organization is past the %s shutdown" % SHUTDOWN)
        return ("closed-early",
                "the subject path is already gone with %d day(s) still to run "
                "on the published date" % -past)
    return ("unreadable",
            "the subject path came back %s, which is neither an answer nor a "
            "closure" % subject)


def cliff_verdict(series, when=SHUTDOWN):
    """Grade a daily [(date, requests)] series. Pure. Returns (state, why).

    Dates an outage, or declines to. A project that served only assistants
    traffic goes to zero on the date; one that served other work as well shows
    a step down, and a step down is reported as a step down. Rounding the
    second case up to the first is how an inference gets published as a fact.
    """
    rows = sorted((str(d), float(n or 0)) for d, n in (series or []))
    if not rows:
        return ("not-checked",
                "no usage buckets were read, so the outage could not be dated")
    before = [n for d, n in rows if d < str(when)]
    after = [n for d, n in rows if d >= str(when)]
    if not before or not after:
        return ("window-too-short",
                "the window does not span %s, so there is nothing to compare "
                "across it" % when)
    mean_before = sum(before) / len(before)
    mean_after = sum(after) / len(after)
    if mean_before == 0:
        return ("no-traffic-in-window",
                "this project had no requests before %s either, so there is "
                "no outage here to explain" % when)
    if mean_after == 0:
        last_live = max((d for d, n in rows if n > 0), default=None)
        eve = (dt.date.fromisoformat(str(when))
               - dt.timedelta(days=1)).isoformat()
        if last_live == eve:
            return ("cliff-on-the-date",
                    "%.0f requests/day until %s and none from %s, which is the "
                    "shutdown and not a deploy"
                    % (mean_before, last_live, when))
        return ("cliff-elsewhere",
                "traffic stopped, but the last live day is %s rather than %s, "
                "the day before %s" % (last_live, eve, when))
    share = mean_after / mean_before
    if share <= 0.5:
        return ("dip-on-the-date",
                "requests fell to %.0f%% of the prior mean on %s, so part of "
                "this project was assistants traffic and part was not"
                % (share * 100, when))
    return ("still-running",
            "requests continued across %s at %.0f%% of the prior mean"
            % (when, share * 100))


def repair_lines(state):
    """The repair for one verdict. Pure. Printed, never performed."""
    line = REPAIRS.get(state)
    if not line:
        return []
    if state in ("grace-access", "shut-down"):
        return [line,
                "the migration guide is Migrate to the Responses API. There is "
                "no successor model id, so no config change closes this."]
    return [line]


def get_json(session, base, path, key, params=None, timeout=30):
    """One GET. Returns (status, parsed body). Never raises on a 4xx."""
    try:
        r = session.get(base + path, headers={"Authorization": "Bearer " + key},
                        params=params or {}, timeout=timeout)
    except requests.RequestException as exc:
        log.debug("GET %s failed: %s", path, exc)
        return (None, {})
    try:
        return (r.status_code, r.json())
    except ValueError:
        return (r.status_code, {})


def usage_series(session, key, days):
    """{project_id: [(date, requests)]} from the daily usage report."""
    start = int((dt.datetime.now(dt.timezone.utc)
                 - dt.timedelta(days=days)).timestamp())
    params = {"start_time": start, "bucket_width": "1d",
              "group_by[]": ["project_id"], "limit": max(7, min(days, 180))}
    status, body = get_json(session, API, "/organization/usage/completions",
                            key, params)
    if status != 200:
        log.warning("usage report came back %s, so no outage can be dated",
                    status)
        return {}
    out = {}
    for bucket in body.get("data") or []:
        stamp = bucket.get("start_time")
        if not stamp:
            continue
        day = dt.datetime.fromtimestamp(int(stamp), dt.timezone.utc).date().isoformat()
        for row in bucket.get("results") or []:
            pid = row.get("project_id") or "(unattributed)"
            out.setdefault(pid, []).append((day, row.get("num_model_requests") or 0))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="days of daily usage buckets to read")
    ap.add_argument("--today", default=dt.date.today().isoformat(),
                    help="override the date the arithmetic is done against")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project read key. This script only "
                  "issues GET requests")
        return 2

    past = days_past(args.today)
    log.info("shutdown %s, %d day(s) %s", SHUTDOWN, abs(past),
             "past" if past >= 0 else "away")

    session = requests.Session()
    states = {}
    for role, path in (("control", CONTROL), ("subject", SUBJECT)):
        status, body = get_json(session, API, path, key, {"limit": 1})
        state, why = probe_state(status, body)
        states[role] = state
        emit = log.warning if role == "subject" and state in LIVE else log.info
        emit("  %-8s GET /v1%-12s %s  %-12s %s", role, path,
             "---" if status is None else status, state, why)

    findings = 0
    state, why = access_verdict(states["subject"], states["control"], past)
    emit = log.warning if state in FINDINGS else log.info
    emit("%-20s %s", state, why)
    for line in repair_lines(state):
        emit("  repair: %s", line)
    if state in FINDINGS:
        findings += 1

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.info("%-20s no admin key, so the outage was observed and not dated",
                 "not-dated")
    else:
        series = usage_series(session, admin, args.days)
        if not series:
            log.info("%-20s the usage report returned nothing to date it with",
                     "not-dated")
        for pid, rows in sorted(series.items()):
            state, why = cliff_verdict(rows)
            emit = log.warning if state in FINDINGS else log.info
            emit("%-20s %-18s %s", pid, state, why)
            for line in repair_lines(state):
                emit("  repair: %s", line)
            if state in FINDINGS:
                findings += 1

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "assistants-shutdown-probe.mjs",
"js": '''/**
 * Probe an endpoint family that is already past its published shutdown date.
 *
 * Read only. Every request is a GET: the assistants listing, a control listing
 * of models on the same key, and the organization usage report. Nothing here
 * creates an assistant, a thread or a run.
 *
 * Past a shutdown date the polarity inverts: a 404 is the expected answer and
 * a 200 is the finding. A 404 on its own cannot tell a closed path from a key
 * that reads nothing, so the unit is a pair with the path as the only variable.
 */
export const API = 'https://api.openai.com/v1';
export const SUBJECT = '/assistants';
export const CONTROL = '/models';

// Announced 26 August 2025 with a year of notice. Published, not readable.
export const SHUTDOWN = '2026-08-26';

// A 429 is a refusal from something that exists, which is not a 404.
const LIVE = new Set(['answering', 'throttled']);

const FINDINGS = new Set(['grace-access', 'shut-down', 'closed-early',
  'control-failed', 'unreadable', 'cliff-on-the-date', 'dip-on-the-date']);

const REPAIRS = {
  'grace-access':
    `this organization still reaches an API that shut down on ${SHUTDOWN}. That `
    + 'is grace, not support, and it has no expiry you can read. Move it now: '
    + 'runs become POST /v1/responses carrying a conversation id, threads become '
    + 'POST /v1/conversations, and the OpenAI-Beta header is deleted.',
  'shut-down':
    'runs become POST /v1/responses carrying a conversation id from '
    + 'POST /v1/conversations, and the OpenAI-Beta: assistants=v2 header is '
    + 'deleted. There is no model id to swap here, which is why checking the '
    + 'model id first never helps.',
  'closed-early':
    'the path is already gone and the published date has not arrived. Treat '
    + 'the date as the outside edge rather than the schedule.',
  'control-failed':
    'the control path did not answer either, so nothing was proved about the '
    + 'subject path. Fix the credential or the network and re-run.',
  'cliff-on-the-date':
    "this project's traffic stopped on the shutdown date, so the outage is the "
    + 'closure and not a deploy. Migrate this project first.',
  'dip-on-the-date':
    "part of this project's traffic stopped on the shutdown date. The project "
    + 'serves other work as well, so the assistants share is what needs '
    + 'migrating, not the whole project.',
};

const day = (iso) => Date.parse(`${iso}T00:00:00Z`);

/** Whole days from a published date to today. Pure. Negative before it. */
export function daysPast(today, when = SHUTDOWN) {
  return Math.round((day(String(today)) - day(String(when))) / 86400000);
}

/** What one listing's status means on its own. Pure. [state, why]. */
export function probeState(status, body = null) {
  if (status === null || status === undefined) {
    return ['unreachable', 'no response at all from this path'];
  }
  const s = Number(status);
  const b = (body && typeof body === 'object') ? body : {};
  if (s === 200) {
    const kind = b.object || 'a body with no object field';
    return ['answering', `200, and the response is ${kind}`];
  }
  const err = (b.error && typeof b.error === 'object') ? b.error : {};
  const code = err.code || err.type || 'no error code';
  if (s === 404) return ['gone', `404 ${code}, which is what a closed path returns`];
  if (s === 401 || s === 403) {
    return ['credentials', `${s} ${code}, so this probe says nothing about the path`];
  }
  if (s === 429) {
    return ['throttled', `429 ${code}, which is a refusal from a path that still routes`];
  }
  return ['refused', `${s} ${code}`];
}

/** Grade the subject path against the control path. Pure. [state, why]. */
export function accessVerdict(subject, control, past) {
  if (!LIVE.has(control)) {
    return ['control-failed',
      `the control path came back ${control}, so this key proves nothing about `
      + 'the subject path'];
  }
  if (LIVE.has(subject)) {
    if (past >= 0) {
      return ['grace-access',
        `the subject path answered ${past} day(s) after its published shutdown `
        + 'date, which is access on grace rather than a supported state'];
    }
    return ['still-open',
      `the subject path answers and the shutdown is ${-past} day(s) away`];
  }
  if (subject === 'gone') {
    if (past >= 0) {
      return ['shut-down',
        'the control path answers and the subject path does not, so this '
        + `organization is past the ${SHUTDOWN} shutdown`];
    }
    return ['closed-early',
      `the subject path is already gone with ${-past} day(s) still to run on `
      + 'the published date'];
  }
  return ['unreadable',
    `the subject path came back ${subject}, which is neither an answer nor a closure`];
}

/** Grade a daily [[date, requests]] series. Pure. [state, why]. */
export function cliffVerdict(series, when = SHUTDOWN) {
  const rows = (series || [])
    .map(([d, n]) => [String(d), Number(n) || 0])
    .sort((a, b) => (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0));
  if (!rows.length) {
    return ['not-checked', 'no usage buckets were read, so the outage could not be dated'];
  }
  const before = rows.filter(([d]) => d < String(when)).map(([, n]) => n);
  const after = rows.filter(([d]) => d >= String(when)).map(([, n]) => n);
  if (!before.length || !after.length) {
    return ['window-too-short',
      `the window does not span ${when}, so there is nothing to compare across it`];
  }
  const mean = (xs) => xs.reduce((a, b) => a + b, 0) / xs.length;
  const meanBefore = mean(before);
  const meanAfter = mean(after);
  if (meanBefore === 0) {
    return ['no-traffic-in-window',
      `this project had no requests before ${when} either, so there is no `
      + 'outage here to explain'];
  }
  if (meanAfter === 0) {
    const live = rows.filter(([, n]) => n > 0).map(([d]) => d);
    const lastLive = live.length ? live[live.length - 1] : null;
    const eve = new Date(day(String(when)) - 86400000).toISOString().slice(0, 10);
    if (lastLive === eve) {
      return ['cliff-on-the-date',
        `${meanBefore.toFixed(0)} requests/day until ${lastLive} and none from `
        + `${when}, which is the shutdown and not a deploy`];
    }
    return ['cliff-elsewhere',
      `traffic stopped, but the last live day is ${lastLive} rather than ${eve}, `
      + `the day before ${when}`];
  }
  const share = meanAfter / meanBefore;
  if (share <= 0.5) {
    return ['dip-on-the-date',
      `requests fell to ${(share * 100).toFixed(0)}% of the prior mean on ${when}, `
      + 'so part of this project was assistants traffic and part was not'];
  }
  return ['still-running',
    `requests continued across ${when} at ${(share * 100).toFixed(0)}% of the prior mean`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state) {
  const line = REPAIRS[state];
  if (!line) return [];
  if (state === 'grace-access' || state === 'shut-down') {
    return [line,
      'the migration guide is Migrate to the Responses API. There is no '
      + 'successor model id, so no config change closes this.'];
  }
  return [line];
}

async function getJson(path, key, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    for (const one of Array.isArray(v) ? v : [v]) url.searchParams.append(k, String(one));
  }
  try {
    const r = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
    let body = {};
    try { body = await r.json(); } catch { body = {}; }
    return [r.status, body];
  } catch {
    return [null, {}];
  }
}

async function usageSeries(key, days) {
  const start = Math.floor(Date.now() / 1000) - days * 86400;
  const [status, body] = await getJson('/organization/usage/completions', key, {
    start_time: start,
    bucket_width: '1d',
    'group_by[]': ['project_id'],
    limit: Math.max(7, Math.min(days, 180)),
  });
  if (status !== 200) {
    console.log(`usage report came back ${status}, so no outage can be dated`);
    return {};
  }
  const out = {};
  for (const bucket of body.data || []) {
    if (!bucket.start_time) continue;
    const d = new Date(bucket.start_time * 1000).toISOString().slice(0, 10);
    for (const row of bucket.results || []) {
      const pid = row.project_id || '(unattributed)';
      (out[pid] ||= []).push([d, row.num_model_requests || 0]);
    }
  }
  return out;
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project read key. This script only '
                  + 'issues GET requests');
    process.exitCode = 2;
    return;
  }
  const today = process.env.TODAY || new Date().toISOString().slice(0, 10);
  const days = Number(process.env.DAYS || 30);
  const past = daysPast(today);
  console.log(`shutdown ${SHUTDOWN}, ${Math.abs(past)} day(s) ${past >= 0 ? 'past' : 'away'}`);

  const states = {};
  for (const [role, path] of [['control', CONTROL], ['subject', SUBJECT]]) {
    const [status, body] = await getJson(path, key, { limit: 1 });
    const [state, why] = probeState(status, body);
    states[role] = state;
    console.log(`  ${role.padEnd(8)} GET /v1${path.padEnd(12)} ${status ?? '---'}  ${state.padEnd(12)} ${why}`);
  }

  let findings = 0;
  const [state, why] = accessVerdict(states.subject, states.control, past);
  console.log(`${state.padEnd(20)} ${why}`);
  for (const line of repairLines(state)) console.log(`  repair: ${line}`);
  if (FINDINGS.has(state)) findings += 1;

  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.log(`${'not-dated'.padEnd(20)} no admin key, so the outage was observed and not dated`);
  } else {
    const series = await usageSeries(admin, days);
    if (!Object.keys(series).length) {
      console.log(`${'not-dated'.padEnd(20)} the usage report returned nothing to date it with`);
    }
    for (const pid of Object.keys(series).sort()) {
      const [cstate, cwhy] = cliffVerdict(series[pid]);
      console.log(`${pid.padEnd(20)} ${cstate.padEnd(18)} ${cwhy}`);
      for (const line of repairLines(cstate)) console.log(`  repair: ${line}`);
      if (FINDINGS.has(cstate)) findings += 1;
    }
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the inversion, and it is the whole note: past the date a 404 is <code>shut-down</code> and a 200 is <code>grace-access</code>, which is the finding. The second is the control, asserted from both sides &mdash; a 404 on the subject path with a dead control must never produce a shutdown verdict, because that would be the script reporting a closure it did not observe. Then the 429, which is a refusal from a path that still exists and therefore counts as live. Then the three readings of a usage series: a cliff that lands on the date, the same cliff two days early, which is a deploy and is named as one, and the partial drop that is reported as a dip rather than rounded up. And finally the repair, asserted to describe a rewrite and to contain no model id at all.",
"test_py_file": "test_assistants_shutdown_probe.py",
"test_py": '''from assistants_shutdown_probe import (SHUTDOWN, access_verdict,
                                       cliff_verdict, days_past, probe_state,
                                       repair_lines)


def series(before=1000.0, after=0.0, last_live="2026-08-25"):
    days = ["2026-08-22", "2026-08-23", "2026-08-24", "2026-08-25",
            "2026-08-26", "2026-08-27", "2026-08-28"]
    out = []
    for d in days:
        if d < SHUTDOWN:
            out.append((d, before if d <= last_live else 0.0))
        else:
            out.append((d, after))
    return out


def test_past_the_date_a_200_is_the_finding_and_a_404_is_the_baseline():
    # The inversion this note exists for. Everywhere else in the section a 404
    # is the alarm; here it is the expected answer.
    state, why = access_verdict("gone", "answering", days_past("2026-08-31"))
    assert state == "shut-down"
    assert SHUTDOWN in why

    state, why = access_verdict("answering", "answering", days_past("2026-08-31"))
    assert state == "grace-access"
    assert "grace rather than a supported state" in why
    assert days_past("2026-08-31") == 5
    assert days_past("2026-08-20") == -6


def test_a_dead_control_path_can_never_produce_a_shutdown_verdict():
    # Without this the script reports a closure it has not observed every time
    # somebody runs it with a revoked key.
    state, why = access_verdict("gone", "credentials", 5)
    assert state == "control-failed"
    assert "proves nothing" in why
    assert access_verdict("gone", "unreachable", 5)[0] == "control-failed"
    assert any("re-run" in line for line in repair_lines("control-failed"))


def test_a_429_is_a_refusal_from_a_path_that_still_exists():
    state, why = probe_state(429, {"error": {"code": "rate_limit_exceeded"}})
    assert state == "throttled"
    assert "still routes" in why
    assert access_verdict("throttled", "answering", 5)[0] == "grace-access"
    assert probe_state(200, {"object": "list"})[0] == "answering"
    assert probe_state(404, {"error": {"code": "model_not_found"}})[0] == "gone"
    assert probe_state(None)[0] == "unreachable"
    assert probe_state(500, {})[0] == "refused"


def test_a_cliff_that_lands_on_the_date_is_the_shutdown():
    state, why = cliff_verdict(series())
    assert state == "cliff-on-the-date"
    assert "not a deploy" in why
    assert any("Migrate this project first" in line
               for line in repair_lines(state))


def test_a_cliff_two_days_early_is_a_deploy_and_is_named_as_one():
    state, why = cliff_verdict(series(last_live="2026-08-23"))
    assert state == "cliff-elsewhere"
    assert "2026-08-23" in why
    assert repair_lines(state) == []


def test_a_partial_drop_is_reported_as_a_dip_and_never_rounded_up():
    # A project that served other work as well loses part of its traffic. That
    # is weaker evidence, so it gets its own state and its own sentence.
    state, why = cliff_verdict(series(after=180.0))
    assert state == "dip-on-the-date"
    assert "18%" in why
    assert "part was not" in why
    assert cliff_verdict(series(after=900.0))[0] == "still-running"
    assert cliff_verdict([])[0] == "not-checked"
    assert cliff_verdict([("2026-08-01", 5)])[0] == "window-too-short"
    assert cliff_verdict(series(before=0.0))[0] == "no-traffic-in-window"


def test_the_repair_describes_a_rewrite_and_names_no_model_id():
    lines = repair_lines("shut-down")
    joined = " ".join(lines)
    assert "/v1/responses" in joined
    assert "/v1/conversations" in joined
    assert "assistants=v2" in joined
    assert "no successor model id" in joined
    assert "gpt-" not in joined
''',
"test_js_file": "assistants-shutdown-probe.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { SHUTDOWN, accessVerdict, cliffVerdict, daysPast, probeState,
         repairLines } from './assistants-shutdown-probe.mjs';

const series = ({ before = 1000, after = 0, lastLive = '2026-08-25' } = {}) =>
  ['2026-08-22', '2026-08-23', '2026-08-24', '2026-08-25',
   '2026-08-26', '2026-08-27', '2026-08-28'].map((d) =>
    (d < SHUTDOWN ? [d, d <= lastLive ? before : 0] : [d, after]));

test('past the date a 200 is the finding and a 404 is the baseline', () => {
  let [state, why] = accessVerdict('gone', 'answering', daysPast('2026-08-31'));
  assert.equal(state, 'shut-down');
  assert.ok(why.includes(SHUTDOWN));

  [state, why] = accessVerdict('answering', 'answering', daysPast('2026-08-31'));
  assert.equal(state, 'grace-access');
  assert.ok(why.includes('grace rather than a supported state'));
  assert.equal(daysPast('2026-08-31'), 5);
  assert.equal(daysPast('2026-08-20'), -6);
});

test('a dead control path can never produce a shutdown verdict', () => {
  const [state, why] = accessVerdict('gone', 'credentials', 5);
  assert.equal(state, 'control-failed');
  assert.ok(why.includes('proves nothing'));
  assert.equal(accessVerdict('gone', 'unreachable', 5)[0], 'control-failed');
  assert.ok(repairLines('control-failed').some((l) => l.includes('re-run')));
});

test('a 429 is a refusal from a path that still exists', () => {
  const [state, why] = probeState(429, { error: { code: 'rate_limit_exceeded' } });
  assert.equal(state, 'throttled');
  assert.ok(why.includes('still routes'));
  assert.equal(accessVerdict('throttled', 'answering', 5)[0], 'grace-access');
  assert.equal(probeState(200, { object: 'list' })[0], 'answering');
  assert.equal(probeState(404, { error: { code: 'model_not_found' } })[0], 'gone');
  assert.equal(probeState(null)[0], 'unreachable');
  assert.equal(probeState(500, {})[0], 'refused');
});

test('a cliff that lands on the date is the shutdown', () => {
  const [state, why] = cliffVerdict(series());
  assert.equal(state, 'cliff-on-the-date');
  assert.ok(why.includes('not a deploy'));
  assert.ok(repairLines(state).some((l) => l.includes('Migrate this project first')));
});

test('a cliff two days early is a deploy and is named as one', () => {
  const [state, why] = cliffVerdict(series({ lastLive: '2026-08-23' }));
  assert.equal(state, 'cliff-elsewhere');
  assert.ok(why.includes('2026-08-23'));
  assert.deepEqual(repairLines(state), []);
});

test('a partial drop is reported as a dip and never rounded up', () => {
  const [state, why] = cliffVerdict(series({ after: 180 }));
  assert.equal(state, 'dip-on-the-date');
  assert.ok(why.includes('18%'));
  assert.ok(why.includes('part was not'));
  assert.equal(cliffVerdict(series({ after: 900 }))[0], 'still-running');
  assert.equal(cliffVerdict([])[0], 'not-checked');
  assert.equal(cliffVerdict([['2026-08-01', 5]])[0], 'window-too-short');
  assert.equal(cliffVerdict(series({ before: 0 }))[0], 'no-traffic-in-window');
});

test('the repair describes a rewrite and names no model id', () => {
  const joined = repairLines('shut-down').join(' ');
  assert.ok(joined.includes('/v1/responses'));
  assert.ok(joined.includes('/v1/conversations'));
  assert.ok(joined.includes('assistants=v2'));
  assert.ok(joined.includes('no successor model id'));
  assert.ok(!joined.includes('gpt-'));
});
''',
"faq": [
 ("The Assistants API is already gone, so why run a script about it?",
  "Because it is not gone everywhere at the same moment. Access after a published shutdown date depends on what the provider is still routing and for whom, and the case this note exists for is the organization that still gets a 200 five days later. Nothing there is broken, so nobody is looking, and the access has no expiry you can read. The script exists to find the one that has not failed yet, not the one that already told you."),
 ("Why probe /v1/models as well? I know my key works.",
  "Because the script does not, and a 404 from a closed path and a 404 from a key with no access are the same number. Holding the credential, the headers and the host fixed while varying only the path is what turns one status code into evidence. If the control path does not answer, the script refuses to report a shutdown at all rather than reporting one it did not observe, and that refusal is a tested behaviour."),
 ("How is this different from the note about a model past its shutdown date?",
  "That note reads shutdown_date off the model object and diffs the model strings in your config against the model list. It cannot see this at all: no model was retired here, every id involved still resolves, and the thing that disappeared is a path, which has no entry in GET /v1/models to check. The distinction is the whole reason batch U exists. A retired model id is a one-line diff; a closed endpoint family is a rewrite."),
 ("The usage report shows a drop but not to zero. Is that the shutdown?",
  "Partly, and the script says partly. A project that ran assistants alongside ordinary completions loses the assistants share on the date and keeps the rest, which shows up as a step down rather than a cliff. That comes back as dip-on-the-date with the percentage attached, and it is deliberately a weaker claim than a cliff. What it tells you is that this project has assistants traffic to migrate; what it cannot tell you is how much, because the report does not separate the two."),
 ("What actually has to change in the code?",
  "The call graph, not a constant. An assistant plus a thread plus a run becomes a single POST /v1/responses carrying a conversation id from POST /v1/conversations, tool definitions move onto the response request, and the OpenAI-Beta: assistants=v2 header is deleted rather than updated. The script prints that shape and the projects that still have traffic on it. It deliberately prints no model id, because substituting one is what people try first and it never helps."),
],
"related": [REL_EXPORT, REL_ZERO_BUCKETS, REL_PAST_DATE],
"citations": [CITE_DEPRECATIONS, CITE_RESPONSES, CITE_CONVERSATIONS, CITE_USAGE],
},
{
"slug": "sora-videos-api-no-replacement",
"title": "The Videos API closes and no successor model is listed",
"description": "Sora 2 and /v1/videos shut down 2026-09-24 with an empty replacement column. Two clocks to read: the endpoint's date and each asset's own expires_at.",
"h1": "The Videos API closes and no successor model is listed",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["sora-2 shutdown 2026-09-24 no replacement",
             "openai videos api deprecated /v1/videos 404",
             "sora-2-pro retirement migration path",
             "video expires_at download before shutdown",
             "openai video generation removed from api"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project read key, used only for GETs of /v1/models/{id} and /v1/videos. Optionally OPENAI_ADMIN_KEY with api.usage.read to size the spend still moving through the surface.",
"lead": "The migration ticket is written before anybody reads the table properly, because everyone has done this before: find the retired id, look up the successor, change the string, ship. So the ticket says \"migrate off sora-2\" and it is assigned and estimated. Then somebody opens the deprecations page to fill in the target and finds the replacement column is empty. Not <em>to be announced</em>, not <em>see the migration guide</em>. Empty, for all five ids, because the thing being removed is not a model. It is the feature.",
"short_answer": """<p>Confirm the closure, then stop looking for a target. <code>GET /v1/models/sora-2</code> with a <strong>project read key</strong> returns a <code>shutdown_date</code> of <code>2026-09-24</code>, and <code>GET /v1/videos?limit=1</code> still returns a list today. That pair is the situation: the endpoint is alive, the date is close, and the deprecation table lists <strong>no replacement</strong> for <code>sora-2</code>, <code>sora-2-pro</code>, <code>sora-2-2025-10-06</code>, <code>sora-2-2025-12-08</code> or <code>sora-2-pro-2025-10-06</code>. The script has a replacement table and it is empty on purpose, with a test that keeps it empty, because a script about a capability being withdrawn that helpfully suggests a successor is worse than no script.</p>
<p>The reading that is actually urgent is the second one, and it is not on the deprecations page at all. Every video object carries its own <code>expires_at</code>. So each rendered asset has <strong>two deadlines</strong> and you need the earlier of them: the day the endpoint closes, and the day that particular file stops being served. An asset whose <code>expires_at</code> falls before 2026-09-24 is already on the shorter clock, and an asset with no expiry still dies with the endpoint, because after the closure there is nothing left to fetch it from.</p>
<p>So the script walks <code>GET /v1/videos</code> to the end, converts each <code>expires_at</code> to a day, and reports the inventory sorted by deadline rather than by creation. What comes out is a download list with dates on it, which is the only artefact that matters between now and the shutdown.</p>
<p>Then size the surface with an <strong>admin-read key</strong>: <code>GET /v1/organization/costs</code> grouped by <code>line_item</code>, filtered to the video lines. Spend still accruing three weeks out means the product feature is live and customers are using it, which is a different conversation from an experiment nobody shipped.</p>
<p>The repair is removal, and the script prints it as removal: take out the <code>/v1/videos</code> code path and the <code>sora-2*</code> constants, and change whatever the product promises about video. That is the whole reason this note is separate from every other deprecation note in the section. The others end in a new string. This one ends in a decision.</p>""",
"problem": """<p>Announced 24 March 2026, shutting down 24 September 2026: the Videos API and every Sora 2 model. Six months of notice, which is generous, and almost useless if the notice was read as a model retirement. The muscle memory for a deprecation notice is to find the successor id, and the ordinary case rewards that instantly. Here it fails silently: you look at the row, the replacement cell is blank, and a blank cell looks like a page that has not been filled in yet rather than a statement.</p>
<p>What is being removed is a product capability. There is no other OpenAI model that generates video, so nothing in the API can absorb the traffic. Anything built on it needs a third-party provider, a rebuild, or removal from the product, and all three of those are decisions somebody outside engineering has to make. That makes the lead time the important resource, and it is the resource a mis-read notice spends.</p>
<p>The quieter half is the assets. Generated videos are stored objects with an <code>expires_at</code> of their own, and the two clocks are independent. A file can expire while the API is still perfectly healthy, and every file that has not expired by 24 September becomes unreachable when the endpoint does, whatever its own expiry said. Teams that treat the shutdown as a code problem discover afterwards that the finished renders they were storing by id are now ids pointing at nothing.</p>
<p>And there is no warning shape for any of this. The endpoint returns 200 right up to the day. The models resolve. Costs keep posting. Nothing degrades, nothing warns, and then one morning a whole feature returns 404 and the only thing left to decide is what to tell customers.</p>""",
"why": """<p><strong>An empty replacement column is a finding, not a gap in the documentation.</strong> This is the only closure in the batch where the correct output contains no migration target, so the script models that explicitly: a lookup function that returns <code>None</code> for every id, backed by a table that is empty and a test that asserts it stays empty. Left implicit, the next person to touch the script fills the table in with the closest-looking model, and the script starts lying in the most confident possible way.</p>
<p><strong>Two clocks means you need the earlier one, per asset, not the earlier one overall.</strong> The endpoint date is uniform and the asset expiries are not, so the deadline is a property of each file. A summary that reports only "23 days left" is wrong for every asset whose <code>expires_at</code> lands sooner, and those are exactly the assets that go missing first. Sorting the inventory by deadline instead of by creation is what turns the report into a work queue.</p>
<p><strong>An asset with no expiry is not safe, and the script refuses to leave it unlabelled.</strong> A null <code>expires_at</code> means this file has no clock of its own; it does not mean it has no clock. It inherits the endpoint's. That case is reported with the shutdown date attached rather than as an absence, because an absence is what somebody skims past.</p>
<p><strong>Spend is the only readable measure of how much product is standing on this.</strong> Neither API lists requests, so "is this feature actually used" has to come from the cost report's video line items. It is a proxy and the script says so, but it separates the two situations that matter: a demo branch nobody deleted, and a live feature with customers on it and three weeks left.</p>
<p><strong>This note reads endpoints and one named id list, not your configuration.</strong> There is a published note that diffs the model strings in your config against the model list, and it would find <code>sora-2</code> there too &mdash; on the day it stops resolving, along with every other broken id, as one row among many. This one is early, specific and about a surface: it reads the five ids the deprecation table names, the endpoint that serves them, and the assets sitting behind it. The difference is that this one is useful in August rather than in October.</p>
<p><strong>The repair is a decision and pretending otherwise wastes the notice.</strong> What the script prints is the shape of the removal plus the two things engineering cannot decide alone: whether the feature is replaced by a third-party provider or dropped, and what the customer-facing copy promising video generation now says. Printing a code diff would imply this is a code problem.</p>""",
"steps": [
 {"h": "Read the shutdown date off the model objects, not off memory",
  "body": """<p><code>GET /v1/models/sora-2</code> and the four other ids the deprecation table names. The <code>shutdown_date</code> field on the model object is the authority; the script reports which ids answered, which already 404, and which returned no date at all, in those three separate states.</p>"""},
 {"h": "Ask for the successor, and print that there is not one",
  "body": """<p>The replacement lookup runs for every id and returns nothing for all of them. That is deliberate output, not a missing feature: this is the one closure in the section whose repair is not a substitution, and the script says so on the line where a model id would otherwise go.</p>"""},
 {"h": "Walk the whole video inventory to the end",
  "body": """<p><code>GET /v1/videos?limit=100</code>, paginating on <code>after</code> until the pages run out. Read <code>id</code>, <code>status</code>, <code>created_at</code> and above all <code>expires_at</code>. Do not stop at the first page: the oldest assets are the ones nearest their own expiry.</p>"""},
 {"h": "Take the earlier of the two clocks for each asset",
  "body": """<p>Per asset, compare its <code>expires_at</code> to the endpoint's shutdown date. Earlier expiry wins and becomes that file's deadline; a null expiry inherits the shutdown; an already-past expiry means those bytes are gone and only the metadata row is left. Sort by deadline, not by creation.</p>"""},
 {"h": "Size the surface, then print the removal",
  "body": """<p><code>GET /v1/organization/costs?bucket_width=1d&amp;group_by[]=line_item</code> over 30 days, filtered to the video lines. Then print the removal: the code path, the constants, and the customer-facing copy. No model id, because there is not one to print.</p>"""},
],
"verify": """<p>Re-run after the download pass and the inventory should shrink from the top: assets you have fetched drop off the work queue, and the earliest deadlines are the ones that disappear first. What will not change is the empty replacement column, and it should not. The reading that tells you the removal has actually happened is the cost report going quiet, not the probe, because the endpoint answers until the day it does not.</p>
<pre><code class="language-bash">OPENAI_API_KEY=sk-proj-... OPENAI_ADMIN_KEY=sk-admin-... \\
  python3 sora_shutdown_inventory.py --days 30
# endpoint /v1/videos closes 2026-09-24, 24 day(s) left
#   sora-2                    200  shutdown-dated  shutdown_date 2026-09-24, 24 day(s) away
#   sora-2-pro                200  shutdown-dated  shutdown_date 2026-09-24, 24 day(s) away
#   sora-2-2025-10-06         200  shutdown-dated  shutdown_date 2026-09-24, 24 day(s) away
#   no-replacement            the deprecation table lists no successor for any of these
#                             ids, so there is no string to substitute
# 214 asset(s) in the inventory
#   already-expired        12  the bytes are gone; only the metadata row is left
#   expires-first          61  earliest 2026-09-02, which is 22 day(s) before the endpoint
#   outlives-the-endpoint 118  their own expiry is later, so the endpoint closes first
#   no-asset-expiry        23  no expiry of their own, so they die with the endpoint
# video-spend-accruing     $412.80 on video line items in the last 30 day(s)
#   repair: remove the /v1/videos code path and the sora-2 constants. This is a
#           capability leaving the API, not a model changing name, so the decision is
#           a third-party provider or dropping the feature
# 4 finding(s)</code></pre>""",
"code_intro": "One GET per model id, a paginated walk of the video inventory, one cost report, and six pure functions. <code>days_left</code>, arithmetic against a published date; <code>iso_day</code>, which turns a unix stamp into a day and is separate so the two-clock logic can be tested without timestamps in it; <code>replacement_for</code>, which returns <code>None</code> for every id and exists precisely so a test can hold the replacement table empty; <code>model_verdict</code>, which grades one id and distinguishes a date read from the API from an id that no longer resolves; <code>asset_deadline</code>, the only function that compares the two clocks, and the only one that can say which of them a given file is on; and <code>spend_verdict</code>, which sizes the surface from the cost report and labels the number a proxy.",
"py_file": "sora_shutdown_inventory.py",
"py": '''"""Inventory a capability that is being withdrawn, with no successor to move to.

Read only. Every request is a GET: the model objects for the five ids the
deprecation table names, the video listing, and the organization cost report.
Nothing here renders a video, and no request in this script creates anything.

Two things make this different from a model retirement. The deprecation table
lists no replacement for any Sora id, so the repair is a removal rather than a
substitution -- REPLACEMENTS below is empty on purpose and there is a test that
keeps it empty. And every rendered asset carries its own expires_at, so each
file has two deadlines and needs the earlier one.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sora_shutdown_inventory")

API = "https://api.openai.com/v1"

# Announced 24 March 2026. The Videos API and every Sora 2 model close on this
# date. Published, and also readable: shutdown_date on the model object is the
# authority, and this constant is the fallback when the object carries no date.
SHUTDOWN = "2026-09-24"

# The five ids the deprecation table names.
SORA_IDS = ("sora-2", "sora-2-pro", "sora-2-2025-10-06", "sora-2-2025-12-08",
            "sora-2-pro-2025-10-06")

# Empty on purpose, and kept empty by a test. Every Sora row in the deprecation
# table has an empty replacement column, because what is being withdrawn is a
# capability and not a model. The failure mode for a script about a capability
# removal is that a later reader fills this in with the closest-looking model
# id, at which point the script lies confidently.
REPLACEMENTS = {}

FINDINGS = ("shutdown-dated", "past-shutdown", "already-gone",
            "already-expired", "expires-first", "outlives-the-endpoint",
            "no-asset-expiry", "video-spend-accruing")

REPAIRS = {
    "shutdown-dated":
        "remove the /v1/videos code path and the sora-2 constants. This is a "
        "capability leaving the API, not a model changing name, so the "
        "decision is a third-party provider or dropping the feature.",
    "past-shutdown":
        "the date has passed. Anything still calling this path is returning "
        "404 to somebody right now.",
    "already-gone":
        "this id no longer resolves, so the removal is already overdue for "
        "whatever still names it.",
    "already-expired":
        "these bytes are gone and only the metadata row is left. If the render "
        "mattered, it has to be regenerated before the endpoint closes, which "
        "is the last chance there will be.",
    "expires-first":
        "download these before their own expiry, which lands sooner than the "
        "endpoint shutdown. This is the front of the queue.",
    "outlives-the-endpoint":
        "download these before the shutdown. Their own expiry is later, which "
        "is irrelevant once there is no endpoint left to serve them.",
    "no-asset-expiry":
        "no expiry of their own does not mean no deadline. They inherit the "
        "endpoint's, so they need downloading like everything else.",
    "video-spend-accruing":
        "this is a live feature with money moving through it, not a branch "
        "somebody forgot. Whoever owns the customer-facing promise of video "
        "generation needs the date before engineering picks a plan.",
}


def days_left(today, when=SHUTDOWN):
    """Whole days from today to a date. Pure. Negative once it has passed."""
    return (dt.date.fromisoformat(str(when))
            - dt.date.fromisoformat(str(today))).days


def iso_day(stamp):
    """A unix second stamp as a UTC day, or None. Pure.

    Kept separate from asset_deadline() so the two-clock comparison can be
    tested in dates rather than in timestamps, which is the part of it that is
    easy to get wrong.
    """
    if stamp in (None, "", 0):
        return None
    try:
        return dt.datetime.fromtimestamp(int(stamp),
                                         dt.timezone.utc).date().isoformat()
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def replacement_for(model_id):
    """The documented successor for one id. Pure. Returns None, every time.

    The lookup exists so that the absence is printed rather than assumed. See
    REPLACEMENTS above for why it is empty and why it stays that way.
    """
    return REPLACEMENTS.get(str(model_id))


def model_verdict(model_id, status, shutdown_date, today):
    """Grade one model id. Pure. Returns (state, detail).

    Distinguishes a date the API stated from a date only the published table
    knows, because those are different levels of evidence and the second one
    goes stale without telling anybody.
    """
    if status is None:
        return ("unreachable", "no response for %s" % model_id)
    status = int(status)
    if status == 404:
        return ("already-gone",
                "%s no longer resolves, so it is out of the model list already"
                % model_id)
    if status != 200:
        return ("unreadable",
                "%d for %s, so nothing can be read about it" % (status, model_id))
    if not shutdown_date:
        return ("no-date-from-api",
                "the model object carried no shutdown_date, so the published "
                "table is the only source and it says %s" % SHUTDOWN)
    left = days_left(today, shutdown_date)
    if left < 0:
        return ("past-shutdown",
                "shutdown_date %s, which was %d day(s) ago"
                % (shutdown_date, -left))
    return ("shutdown-dated",
            "shutdown_date %s, %d day(s) away" % (shutdown_date, left))


def asset_deadline(expires_iso, today, when=SHUTDOWN):
    """The earlier of an asset's two clocks. Pure. (state, deadline, detail).

    The only function here that compares them, and the reason the report is
    sorted by deadline rather than by creation date. A null expiry is not an
    absence of a deadline: it inherits the endpoint's.
    """
    today = str(today)
    when = str(when)
    if not expires_iso:
        return ("no-asset-expiry", when,
                "no expiry of its own, so it dies with the endpoint on %s" % when)
    expires_iso = str(expires_iso)
    if expires_iso <= today:
        return ("already-expired", expires_iso,
                "expired on %s, so the bytes are already unreachable"
                % expires_iso)
    if expires_iso < when:
        gap = days_left(expires_iso, when)
        return ("expires-first", expires_iso,
                "expires %s, which is %d day(s) before the endpoint closes"
                % (expires_iso, gap))
    return ("outlives-the-endpoint", when,
            "its own expiry is %s, so the endpoint closes first on %s"
            % (expires_iso, when))


def spend_verdict(rows, days):
    """Sum the video line items. Pure. Returns (state, total, detail).

    A proxy and labelled as one: neither API lists requests, so spend is the
    only readable measure of how much product is standing on this surface.
    """
    total = 0.0
    for name, amount in rows or []:
        text = str(name or "").lower()
        if "video" in text or "sora" in text:
            total += float(amount or 0)
    if total > 0:
        return ("video-spend-accruing", total,
                "$%.2f on video line items in the last %d day(s), which is a "
                "live feature rather than a branch somebody forgot"
                % (total, days))
    return ("no-video-spend", 0.0,
            "no video line items in the last %d day(s). That is a proxy: it "
            "means nothing was billed, not that nothing calls the endpoint"
            % days)


def repair_lines(state):
    """The repair for one verdict. Pure. Printed, never performed."""
    line = REPAIRS.get(state)
    if not line:
        return []
    if state in ("shutdown-dated", "past-shutdown", "already-gone"):
        return [line,
                "there is no successor model id to print here. The replacement "
                "column is empty for every Sora id in the deprecation table."]
    return [line]


def get_json(session, path, key, params=None, timeout=30):
    """One GET. Returns (status, parsed body). Never raises on a 4xx."""
    try:
        r = session.get(API + path,
                        headers={"Authorization": "Bearer " + key},
                        params=params or {}, timeout=timeout)
    except requests.RequestException as exc:
        log.debug("GET %s failed: %s", path, exc)
        return (None, {})
    try:
        return (r.status_code, r.json())
    except ValueError:
        return (r.status_code, {})


def all_videos(session, key, pages=50):
    """Walk GET /v1/videos to the end. The oldest assets expire first."""
    out, after = [], None
    for _ in range(pages):
        params = {"limit": 100, "order": "asc"}
        if after:
            params["after"] = after
        status, body = get_json(session, "/videos", key, params)
        if status != 200:
            log.warning("video listing came back %s, so the inventory is "
                        "incomplete", status)
            break
        page = body.get("data") or []
        out.extend(page)
        if not page or not body.get("has_more"):
            break
        after = page[-1].get("id")
        if not after:
            break
    return out


def cost_rows(session, key, days):
    """[(line_item, amount)] from the daily cost report."""
    start = int((dt.datetime.now(dt.timezone.utc)
                 - dt.timedelta(days=days)).timestamp())
    status, body = get_json(session, "/organization/costs", key,
                            {"start_time": start, "bucket_width": "1d",
                             "group_by[]": ["line_item"], "limit": 180})
    if status != 200:
        log.warning("cost report came back %s, so the surface was not sized",
                    status)
        return []
    rows = []
    for bucket in body.get("data") or []:
        for row in bucket.get("results") or []:
            amount = row.get("amount") or {}
            rows.append((row.get("line_item"), amount.get("value")))
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--days", type=int, default=30,
                    help="days of cost buckets to read")
    ap.add_argument("--today", default=dt.date.today().isoformat(),
                    help="override the date the arithmetic is done against")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project read key. This script only "
                  "issues GET requests")
        return 2

    session = requests.Session()
    findings = 0
    log.info("endpoint /v1/videos closes %s, %d day(s) left", SHUTDOWN,
             days_left(args.today))

    for model_id in SORA_IDS:
        status, body = get_json(session, "/models/" + model_id, key)
        state, detail = model_verdict(model_id, status,
                                      (body or {}).get("shutdown_date"),
                                      args.today)
        emit = log.warning if state in FINDINGS else log.info
        emit("  %-26s %s  %-15s %s", model_id,
             "---" if status is None else status, state, detail)
        if replacement_for(model_id):
            log.error("  the replacement table is not empty. Read the note "
                      "before trusting this line")
    log.warning("  %-26s the deprecation table lists no successor for any of "
                "these ids, so there is no string to substitute",
                "no-replacement")
    for line in repair_lines("shutdown-dated"):
        log.warning("  repair: %s", line)
    findings += 1

    videos = all_videos(session, key)
    log.info("%d asset(s) in the inventory", len(videos))
    buckets = {}
    for video in videos:
        state, deadline, detail = asset_deadline(
            iso_day(video.get("expires_at")), args.today)
        entry = buckets.setdefault(state, [0, deadline, detail])
        entry[0] += 1
        if deadline < entry[1]:
            entry[1], entry[2] = deadline, detail
    for state, (count, deadline, detail) in sorted(
            buckets.items(), key=lambda kv: kv[1][1]):
        emit = log.warning if state in FINDINGS else log.info
        emit("  %-22s %4d  earliest %s: %s", state, count, deadline, detail)
        for line in repair_lines(state):
            emit("    repair: %s", line)
        if state in FINDINGS:
            findings += 1

    admin = os.environ.get("OPENAI_ADMIN_KEY")
    if not admin:
        log.info("%-22s no admin key, so the surface was not sized",
                 "not-sized")
    else:
        state, total, detail = spend_verdict(cost_rows(session, admin, args.days),
                                             args.days)
        emit = log.warning if state in FINDINGS else log.info
        emit("%-22s %s", state, detail)
        for line in repair_lines(state):
            emit("  repair: %s", line)
        if state in FINDINGS:
            findings += 1

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "sora-shutdown-inventory.mjs",
"js": '''/**
 * Inventory a capability being withdrawn, with no successor to move to.
 *
 * Read only. Every request is a GET: the model objects for the five ids the
 * deprecation table names, the video listing, and the cost report. Nothing
 * here renders a video and no request in this script creates anything.
 *
 * The deprecation table lists no replacement for any Sora id, so REPLACEMENTS
 * below is empty on purpose and a test keeps it empty. And every asset carries
 * its own expires_at, so each file has two deadlines and needs the earlier one.
 */
export const API = 'https://api.openai.com/v1';

// Announced 24 March 2026. Published, and also readable as shutdown_date.
export const SHUTDOWN = '2026-09-24';

export const SORA_IDS = ['sora-2', 'sora-2-pro', 'sora-2-2025-10-06',
  'sora-2-2025-12-08', 'sora-2-pro-2025-10-06'];

// Empty on purpose, and kept empty by a test. What is being withdrawn is a
// capability and not a model, so filling this in with the closest-looking id
// would make the script lie confidently.
export const REPLACEMENTS = {};

const FINDINGS = new Set(['shutdown-dated', 'past-shutdown', 'already-gone',
  'already-expired', 'expires-first', 'outlives-the-endpoint',
  'no-asset-expiry', 'video-spend-accruing']);

const REPAIRS = {
  'shutdown-dated':
    'remove the /v1/videos code path and the sora-2 constants. This is a '
    + 'capability leaving the API, not a model changing name, so the decision '
    + 'is a third-party provider or dropping the feature.',
  'past-shutdown':
    'the date has passed. Anything still calling this path is returning 404 to '
    + 'somebody right now.',
  'already-gone':
    'this id no longer resolves, so the removal is already overdue for '
    + 'whatever still names it.',
  'already-expired':
    'these bytes are gone and only the metadata row is left. If the render '
    + 'mattered, it has to be regenerated before the endpoint closes.',
  'expires-first':
    'download these before their own expiry, which lands sooner than the '
    + 'endpoint shutdown. This is the front of the queue.',
  'outlives-the-endpoint':
    'download these before the shutdown. Their own expiry is later, which is '
    + 'irrelevant once there is no endpoint left to serve them.',
  'no-asset-expiry':
    'no expiry of their own does not mean no deadline. They inherit the '
    + "endpoint's, so they need downloading like everything else.",
  'video-spend-accruing':
    'this is a live feature with money moving through it, not a branch '
    + 'somebody forgot. Whoever owns the customer-facing promise of video '
    + 'generation needs the date before engineering picks a plan.',
};

const day = (iso) => Date.parse(`${iso}T00:00:00Z`);

/** Whole days from today to a date. Pure. Negative once it has passed. */
export function daysLeft(today, when = SHUTDOWN) {
  return Math.round((day(String(when)) - day(String(today))) / 86400000);
}

/** A unix second stamp as a UTC day, or null. Pure. */
export function isoDay(stamp) {
  if (stamp === null || stamp === undefined || stamp === '' || stamp === 0) return null;
  const n = Number(stamp);
  if (!Number.isFinite(n)) return null;
  const d = new Date(n * 1000);
  if (Number.isNaN(d.getTime())) return null;
  return d.toISOString().slice(0, 10);
}

/** The documented successor for one id. Pure. Returns undefined, every time. */
export function replacementFor(modelId) {
  return REPLACEMENTS[String(modelId)];
}

/** Grade one model id. Pure. [state, detail]. */
export function modelVerdict(modelId, status, shutdownDate, today) {
  if (status === null || status === undefined) {
    return ['unreachable', `no response for ${modelId}`];
  }
  const s = Number(status);
  if (s === 404) {
    return ['already-gone',
      `${modelId} no longer resolves, so it is out of the model list already`];
  }
  if (s !== 200) {
    return ['unreadable', `${s} for ${modelId}, so nothing can be read about it`];
  }
  if (!shutdownDate) {
    return ['no-date-from-api',
      'the model object carried no shutdown_date, so the published table is '
      + `the only source and it says ${SHUTDOWN}`];
  }
  const left = daysLeft(today, shutdownDate);
  if (left < 0) {
    return ['past-shutdown', `shutdown_date ${shutdownDate}, which was ${-left} day(s) ago`];
  }
  return ['shutdown-dated', `shutdown_date ${shutdownDate}, ${left} day(s) away`];
}

/** The earlier of an asset's two clocks. Pure. [state, deadline, detail]. */
export function assetDeadline(expiresIso, today, when = SHUTDOWN) {
  const t = String(today);
  const w = String(when);
  if (!expiresIso) {
    return ['no-asset-expiry', w,
      `no expiry of its own, so it dies with the endpoint on ${w}`];
  }
  const e = String(expiresIso);
  if (e <= t) {
    return ['already-expired', e, `expired on ${e}, so the bytes are already unreachable`];
  }
  if (e < w) {
    return ['expires-first', e,
      `expires ${e}, which is ${daysLeft(e, w)} day(s) before the endpoint closes`];
  }
  return ['outlives-the-endpoint', w,
    `its own expiry is ${e}, so the endpoint closes first on ${w}`];
}

/** Sum the video line items. Pure. [state, total, detail]. */
export function spendVerdict(rows, days) {
  let total = 0;
  for (const [name, amount] of rows || []) {
    const text = String(name ?? '').toLowerCase();
    if (text.includes('video') || text.includes('sora')) total += Number(amount) || 0;
  }
  if (total > 0) {
    return ['video-spend-accruing', total,
      `$${total.toFixed(2)} on video line items in the last ${days} day(s), which `
      + 'is a live feature rather than a branch somebody forgot'];
  }
  return ['no-video-spend', 0,
    `no video line items in the last ${days} day(s). That is a proxy: it means `
    + 'nothing was billed, not that nothing calls the endpoint'];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state) {
  const line = REPAIRS[state];
  if (!line) return [];
  if (state === 'shutdown-dated' || state === 'past-shutdown' || state === 'already-gone') {
    return [line,
      'there is no successor model id to print here. The replacement column is '
      + 'empty for every Sora id in the deprecation table.'];
  }
  return [line];
}

async function getJson(path, key, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    for (const one of Array.isArray(v) ? v : [v]) url.searchParams.append(k, String(one));
  }
  try {
    const r = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
    let body = {};
    try { body = await r.json(); } catch { body = {}; }
    return [r.status, body];
  } catch {
    return [null, {}];
  }
}

async function allVideos(key, pages = 50) {
  const out = [];
  let after = null;
  for (let i = 0; i < pages; i += 1) {
    const params = { limit: 100, order: 'asc' };
    if (after) params.after = after;
    const [status, body] = await getJson('/videos', key, params);
    if (status !== 200) {
      console.log(`video listing came back ${status}, so the inventory is incomplete`);
      break;
    }
    const page = body.data || [];
    out.push(...page);
    if (!page.length || !body.has_more) break;
    after = page[page.length - 1].id;
    if (!after) break;
  }
  return out;
}

async function costRows(key, days) {
  const start = Math.floor(Date.now() / 1000) - days * 86400;
  const [status, body] = await getJson('/organization/costs', key, {
    start_time: start, bucket_width: '1d', 'group_by[]': ['line_item'], limit: 180,
  });
  if (status !== 200) {
    console.log(`cost report came back ${status}, so the surface was not sized`);
    return [];
  }
  const rows = [];
  for (const bucket of body.data || []) {
    for (const row of bucket.results || []) {
      rows.push([row.line_item, (row.amount || {}).value]);
    }
  }
  return rows;
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project read key. This script only '
                  + 'issues GET requests');
    process.exitCode = 2;
    return;
  }
  const today = process.env.TODAY || new Date().toISOString().slice(0, 10);
  const days = Number(process.env.DAYS || 30);
  let findings = 0;

  console.log(`endpoint /v1/videos closes ${SHUTDOWN}, ${daysLeft(today)} day(s) left`);
  for (const modelId of SORA_IDS) {
    const [status, body] = await getJson(`/models/${modelId}`, key);
    const [state, detail] = modelVerdict(modelId, status, body.shutdown_date, today);
    console.log(`  ${modelId.padEnd(26)} ${status ?? '---'}  ${state.padEnd(15)} ${detail}`);
    if (replacementFor(modelId)) {
      console.error('  the replacement table is not empty. Read the note before '
                    + 'trusting this line');
    }
  }
  console.log(`  ${'no-replacement'.padEnd(26)} the deprecation table lists no successor `
              + 'for any of these ids, so there is no string to substitute');
  for (const line of repairLines('shutdown-dated')) console.log(`  repair: ${line}`);
  findings += 1;

  const videos = await allVideos(key);
  console.log(`${videos.length} asset(s) in the inventory`);
  const buckets = new Map();
  for (const video of videos) {
    const [state, deadline, detail] = assetDeadline(isoDay(video.expires_at), today);
    const entry = buckets.get(state) || [0, deadline, detail];
    entry[0] += 1;
    if (deadline < entry[1]) { entry[1] = deadline; entry[2] = detail; }
    buckets.set(state, entry);
  }
  for (const [state, [count, deadline, detail]] of
       [...buckets.entries()].sort((a, b) => (a[1][1] < b[1][1] ? -1 : 1))) {
    console.log(`  ${state.padEnd(22)} ${String(count).padStart(4)}  earliest ${deadline}: ${detail}`);
    for (const line of repairLines(state)) console.log(`    repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;
  }

  const admin = process.env.OPENAI_ADMIN_KEY;
  if (!admin) {
    console.log(`${'not-sized'.padEnd(22)} no admin key, so the surface was not sized`);
  } else {
    const [state, , detail] = spendVerdict(await costRows(admin, days), days);
    console.log(`${state.padEnd(22)} ${detail}`);
    for (const line of repairLines(state)) console.log(`  repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the one that keeps the note honest: the replacement table is empty, <code>replacement_for</code> returns nothing for all five ids, and the repair text says in words that there is no successor to print. If a later reader fills that table in, this test fails and tells them why. The rest is the two clocks. An asset whose <code>expires_at</code> lands before the shutdown is on the earlier one and the detail says by how many days; one whose expiry is later is on the endpoint's, because the endpoint closes first; a null expiry inherits the shutdown rather than counting as no deadline at all; and an expiry already in the past is bytes that are gone. Then the model grading, which separates a <code>shutdown_date</code> the API stated from a 404 and from a model object that carried no date. And finally the spend proxy, asserted to describe itself as a proxy in the zero case, since that is the case somebody will read as an all-clear.",
"test_py_file": "test_sora_shutdown_inventory.py",
"test_py": '''from sora_shutdown_inventory import (REPLACEMENTS, SHUTDOWN, SORA_IDS,
                                     asset_deadline, days_left, iso_day,
                                     model_verdict, repair_lines,
                                     replacement_for, spend_verdict)

TODAY = "2026-08-31"


def test_there_is_no_successor_and_the_script_refuses_to_invent_one():
    # If somebody fills the table in with the closest-looking model id, this
    # fails and the message above it explains why that is not a kindness.
    assert REPLACEMENTS == {}
    for model_id in SORA_IDS:
        assert replacement_for(model_id) is None
    joined = " ".join(repair_lines("shutdown-dated"))
    assert "no successor model id" in joined
    assert "capability leaving the API" in joined
    assert "third-party provider or dropping the feature" in joined


def test_an_asset_that_expires_first_is_on_the_earlier_clock():
    state, deadline, detail = asset_deadline("2026-09-02", TODAY)
    assert state == "expires-first"
    assert deadline == "2026-09-02"
    assert "22 day(s) before the endpoint closes" in detail
    assert any("front of the queue" in line for line in repair_lines(state))


def test_an_asset_that_outlives_its_expiry_still_dies_with_the_endpoint():
    state, deadline, detail = asset_deadline("2026-12-01", TODAY)
    assert state == "outlives-the-endpoint"
    assert deadline == SHUTDOWN
    assert "the endpoint closes first" in detail

    # A null expiry is not an absence of a deadline. It inherits one.
    state, deadline, detail = asset_deadline(None, TODAY)
    assert state == "no-asset-expiry"
    assert deadline == SHUTDOWN
    assert "dies with the endpoint" in detail
    assert any("inherit" in line for line in repair_lines(state))


def test_an_expiry_already_past_means_the_bytes_are_gone():
    state, deadline, detail = asset_deadline("2026-08-04", TODAY)
    assert state == "already-expired"
    assert deadline == "2026-08-04"
    assert "already unreachable" in detail
    assert asset_deadline(TODAY, TODAY)[0] == "already-expired"


def test_unix_stamps_become_days_and_bad_ones_become_nothing():
    assert iso_day(1788000000) == "2026-08-29"
    assert iso_day(None) is None
    assert iso_day(0) is None
    assert iso_day("not a stamp") is None
    assert days_left(TODAY) == 24
    assert days_left("2026-10-01") == -7


def test_a_stated_shutdown_date_is_graded_apart_from_a_missing_one():
    state, detail = model_verdict("sora-2", 200, SHUTDOWN, TODAY)
    assert state == "shutdown-dated"
    assert "24 day(s) away" in detail

    state, detail = model_verdict("sora-2", 200, None, TODAY)
    assert state == "no-date-from-api"
    assert "published table is the only source" in detail

    assert model_verdict("sora-2", 404, None, TODAY)[0] == "already-gone"
    assert model_verdict("sora-2", 401, None, TODAY)[0] == "unreadable"
    assert model_verdict("sora-2", None, None, TODAY)[0] == "unreachable"
    assert model_verdict("sora-2", 200, "2026-08-01", TODAY)[0] == "past-shutdown"


def test_spend_is_a_proxy_and_says_so_in_the_case_that_looks_like_an_all_clear():
    state, total, detail = spend_verdict(
        [("Video generation", 400.5), ("sora-2-pro", 12.3), ("Text tokens", 99)], 30)
    assert state == "video-spend-accruing"
    assert round(total, 2) == 412.80
    assert "412.80" in detail

    state, total, detail = spend_verdict([("Text tokens", 99)], 30)
    assert state == "no-video-spend"
    assert total == 0.0
    assert "That is a proxy" in detail
    assert repair_lines(state) == []
''',
"test_js_file": "sora-shutdown-inventory.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { REPLACEMENTS, SHUTDOWN, SORA_IDS, assetDeadline, daysLeft, isoDay,
         modelVerdict, repairLines, replacementFor,
         spendVerdict } from './sora-shutdown-inventory.mjs';

const TODAY = '2026-08-31';

test('there is no successor and the script refuses to invent one', () => {
  assert.deepEqual(REPLACEMENTS, {});
  for (const id of SORA_IDS) assert.equal(replacementFor(id), undefined);
  const joined = repairLines('shutdown-dated').join(' ');
  assert.ok(joined.includes('no successor model id'));
  assert.ok(joined.includes('capability leaving the API'));
  assert.ok(joined.includes('third-party provider or dropping the feature'));
});

test('an asset that expires first is on the earlier clock', () => {
  const [state, deadline, detail] = assetDeadline('2026-09-02', TODAY);
  assert.equal(state, 'expires-first');
  assert.equal(deadline, '2026-09-02');
  assert.ok(detail.includes('22 day(s) before the endpoint closes'));
  assert.ok(repairLines(state).some((l) => l.includes('front of the queue')));
});

test('an asset that outlives its expiry still dies with the endpoint', () => {
  let [state, deadline, detail] = assetDeadline('2026-12-01', TODAY);
  assert.equal(state, 'outlives-the-endpoint');
  assert.equal(deadline, SHUTDOWN);
  assert.ok(detail.includes('the endpoint closes first'));

  [state, deadline, detail] = assetDeadline(null, TODAY);
  assert.equal(state, 'no-asset-expiry');
  assert.equal(deadline, SHUTDOWN);
  assert.ok(detail.includes('dies with the endpoint'));
  assert.ok(repairLines(state).some((l) => l.includes('inherit')));
});

test('an expiry already past means the bytes are gone', () => {
  const [state, deadline, detail] = assetDeadline('2026-08-04', TODAY);
  assert.equal(state, 'already-expired');
  assert.equal(deadline, '2026-08-04');
  assert.ok(detail.includes('already unreachable'));
  assert.equal(assetDeadline(TODAY, TODAY)[0], 'already-expired');
});

test('unix stamps become days and bad ones become nothing', () => {
  assert.equal(isoDay(1788000000), '2026-08-29');
  assert.equal(isoDay(null), null);
  assert.equal(isoDay(0), null);
  assert.equal(isoDay('not a stamp'), null);
  assert.equal(daysLeft(TODAY), 24);
  assert.equal(daysLeft('2026-10-01'), -7);
});

test('a stated shutdown date is graded apart from a missing one', () => {
  let [state, detail] = modelVerdict('sora-2', 200, SHUTDOWN, TODAY);
  assert.equal(state, 'shutdown-dated');
  assert.ok(detail.includes('24 day(s) away'));

  [state, detail] = modelVerdict('sora-2', 200, null, TODAY);
  assert.equal(state, 'no-date-from-api');
  assert.ok(detail.includes('published table is the only source'));

  assert.equal(modelVerdict('sora-2', 404, null, TODAY)[0], 'already-gone');
  assert.equal(modelVerdict('sora-2', 401, null, TODAY)[0], 'unreadable');
  assert.equal(modelVerdict('sora-2', null, null, TODAY)[0], 'unreachable');
  assert.equal(modelVerdict('sora-2', 200, '2026-08-01', TODAY)[0], 'past-shutdown');
});

test('spend is a proxy and says so in the case that looks like an all clear', () => {
  let [state, total, detail] = spendVerdict(
    [['Video generation', 400.5], ['sora-2-pro', 12.3], ['Text tokens', 99]], 30);
  assert.equal(state, 'video-spend-accruing');
  assert.equal(Math.round(total * 100) / 100, 412.8);
  assert.ok(detail.includes('412.80'));

  [state, total, detail] = spendVerdict([['Text tokens', 99]], 30);
  assert.equal(state, 'no-video-spend');
  assert.equal(total, 0);
  assert.ok(detail.includes('That is a proxy'));
  assert.deepEqual(repairLines(state), []);
});
''',
"faq": [
 ("What do I migrate sora-2 to?",
  "Nothing, and that is the finding rather than a gap in the answer. The deprecation table's replacement column is empty for sora-2, sora-2-pro and all three dated snapshots, because what is being withdrawn is video generation as a capability rather than one model within it. No other OpenAI model absorbs the traffic. The script's replacement table is empty on purpose and a test keeps it that way, so the output says there is no successor instead of guessing at the closest-looking id."),
 ("Why does the script care about expires_at when the endpoint is closing anyway?",
  "Because the two clocks are independent and the asset one is often earlier. Every video object carries its own expires_at, so a file can become unreachable weeks before 24 September while the API is still perfectly healthy. Sorting the inventory by the earlier of the two deadlines turns it into a download queue with real dates on it, which is the only artefact worth producing between now and the shutdown. An asset with no expiry of its own is not exempt; it simply inherits the endpoint's date."),
 ("Is this not the same as the note about a model past its shutdown date?",
  "No, and the difference is timing as much as mechanism. That note diffs the model strings in your configuration against the model list, which will find sora-2 on the day it stops resolving, as one broken id among however many others. This one reads the five ids the table names, the endpoint that serves them, and the assets sitting behind it, which is useful in August rather than in October. It also owns the part the model list cannot express: the endpoint itself is going, not just the ids."),
 ("Can I not just keep the rendered videos I already have?",
  "Only if you fetch them first. The stored assets live behind the same API that is closing, so after the shutdown an id you hold is an id pointing at nothing, whatever that asset's own expires_at said. The realistic plan is to walk the whole inventory now, download what the product actually needs, and store it somewhere you own. The script produces the list, sorted by deadline; it deliberately does not download anything itself, because that is not a read-only operation in any useful sense."),
 ("How do I tell whether this feature is actually being used?",
  "From the cost report, and only approximately. Neither API lists individual requests, so the readable signal is video line items on GET /v1/organization/costs grouped by line_item. Money still moving through the surface three weeks out means live customers rather than a branch nobody deleted. The script labels that number a proxy, including in the zero case, because no video spend means nothing was billed in the window and not that nothing calls the endpoint."),
],
"related": [REL_ASSISTANTS, REL_MEDIA_COST, REL_VS_EXPIRY],
"citations": [CITE_DEPRECATIONS, CITE_VIDEOS, CITE_MODEL_OBJ, CITE_COSTS],
},
{
"slug": "prompts-evals-agentbuilder-sunset",
"title": "Prompts, Evals and Agent Builder close: export, not rewrite",
"description": "Three surfaces close on 2026-11-30 and the content lives on OpenAI's side. Grade what the API can still export, and hand the rest to a person.",
"h1": "Prompts, Evals and Agent Builder close: export, not rewrite",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai reusable prompts shutdown 2026-11-30",
             "evals api deprecated export promptfoo",
             "agent builder sunset agents sdk migration",
             "pmpt_ prompt id no longer resolves responses api",
             "export openai evals definitions before shutdown"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project read key, used only for GETs of /v1/evals and /v1/prompts. Also takes the pmpt_ ids your own code passes to the Responses API, declared on the command line or in OPENAI_PROMPT_IDS, because there is no documented endpoint that will list them for you.",
"lead": "The deprecation notice reads like the others and gets triaged like the others: three surfaces, one date, put it in the sprint after next. What is different does not appear anywhere in the notice. The reusable prompt referenced as <code>pmpt_a1b2</code> in four services is four characters of your source code and several hundred words of somebody else's, and those words are on OpenAI's side of the line. On 1 December the code still compiles, the deploy still succeeds, and the prompt is not in the repository because it never was.",
"short_answer": """<p>Treat this as an export problem, because the thing at risk is content rather than code. Reusable Prompts, the Evals platform and Agent Builder all close on <strong>2026-11-30</strong>, and what disappears with them is stored material you did not write down: prompt versions, eval definitions and grader configuration, and published workflows.</p>
<p>The API reaches exactly one of the three. <code>GET /v1/evals</code> is documented, paginates on <code>after</code>, and returns the <strong>full eval object</strong> including <code>data_source_config</code> and <code>testing_criteria</code> &mdash; so the listing <em>is</em> the export, and one script can take the whole set.</p>
<p>Reusable prompts are the awkward one. There is <strong>no documented list endpoint</strong> for them anywhere in the API reference, so the script does not assert one: it probes <code>GET /v1/prompts</code> and grades whatever comes back, then falls back to the <code>pmpt_</code> ids in your own call sites and probes each individually. That is a real difference from the other two surfaces and it changes the plan, because a set you cannot enumerate is a set you can only be sure about by grepping your tree.</p>
<p>Agent Builder has <strong>no REST surface at all</strong>. Not a closed one, not an undocumented one: there is nothing to call. The script says so on its own line and assigns that surface to a person working in the dashboard, rather than quietly leaving it out of a report that otherwise looks complete.</p>
<p>So the output is a plan with an owner against each row: what a script can take, what a script can take only for ids you already hold, and what somebody has to open a browser for. Then the code change, which is small and second: <code>prompt={"id": "pmpt_a1b2", "version": "3"}</code> becomes an <code>instructions</code> string you now have in the repository, eval suites move to Promptfoo, and Agent Builder flows become Agents SDK code. None of that is possible until the export is done, which is why the export is the note.</p>""",
"problem": """<p>Announced 3 June 2026, closing 30 November 2026. Three things go at once and they are usually described together, which hides the fact that they fail differently. A prompt object is content. An eval suite is content plus configuration. An Agent Builder workflow is a published artefact with an id somebody else's code references. The only thing they share is a date and the direction of the loss.</p>
<p>The reusable prompt is the sharpest case because it is invisible in review. A call site reads <code>prompt={"id": "pmpt_a1b2", "version": "3"}</code>, which is a perfectly ordinary-looking line, and the several hundred words it stands for are stored server-side and versioned server-side. Nobody diffs them. Nobody has them in the repository. After the date, the same line is an invalid request against a prompt object that no longer resolves, and the text is not somewhere else &mdash; it is gone.</p>
<p>Evals are the surface people notice last and miss longest. An eval suite is not production traffic, so it is not on any dashboard anyone watches, and its absence does not break a deploy. It breaks the next time somebody wants to know whether a model change was safe, which is exactly when they cannot afford to reconstruct six months of graders from memory.</p>
<p>And the coverage is uneven in a way that a tidy report will conceal. One of the three enumerates cleanly, one has no documented listing at all, and one has no API. A script that reports on what it can reach and silently omits the rest produces a green summary for an organization that is going to lose an Agent Builder workflow on the last day of November.</p>""",
"why": """<p><strong>The unit here is exportability, not validity.</strong> Every other note in this batch asks whether an endpoint still answers. This one asks whether the content behind it can be got out, which is a different question with a different answer per surface and a different owner per answer. A surface that answers 200 and holds nothing you need is fine; a surface that cannot be listed and holds your prompt text is the problem, and status codes alone do not sort those two.</p>
<p><strong>An undocumented endpoint gets probed and reported, never asserted.</strong> The API reference index lists no path for reusable prompts. So the script issues the probe and prints the status it got, and the state it produces on a 404 is <em>no list endpoint</em> rather than <em>gone</em> &mdash; because those imply different next steps and only one of them is supported by the evidence. If the path does answer, the script says that too and the plan gets better.</p>
<p><strong>A surface with no API is a finding with a name, not an omission.</strong> Agent Builder is graded without a request, because there is nothing to request. That row exists so the report cannot look complete while covering two thirds of the problem, and it is asserted in a test: passing a 200 for that surface still produces <code>no-api-surface</code>, so a stray status from somewhere else can never promote it to covered.</p>
<p><strong>A structural fault is graded before the network, exactly as in the header notes.</strong> An id that does not begin <code>pmpt_</code> is a configuration bug and needs no request to prove it. Probing it first would spend a call and, worse, bury a definite finding under a status code.</p>
<p><strong>The listing is the export, and that is worth saying out loud.</strong> <code>GET /v1/evals</code> returns whole eval objects rather than stubs, so there is no second pass and no per-id fetch to get the definition. That is why the evals half of this is a solved problem and the prompts half is not, and stating the reason keeps somebody from writing the fetch loop that is not needed.</p>
<p><strong>The repair is a two-step and the steps are not interchangeable.</strong> Export, then inline. Nobody can replace <code>prompt={"id": ...}</code> with an <code>instructions</code> string they do not have. The script prints the export commands first and the code change second, and the code change is the short part.</p>""",
"steps": [
 {"h": "Count the days, and read the date as the export deadline",
  "body": """<p>2026-11-30. The script prints days remaining and treats the date as the last day the content is retrievable, not the last day the code works &mdash; those are the same date here, and the first one is the one with a queue behind it.</p>"""},
 {"h": "List the evals, which is the export",
  "body": """<p><code>GET /v1/evals?limit=100</code>, paginating on <code>after</code>. The response carries <code>name</code>, <code>data_source_config</code> and <code>testing_criteria</code> per eval, so the page itself is the material. Save it; there is no second call to make.</p>"""},
 {"h": "Probe the prompts path rather than assuming it",
  "body": """<p><code>GET /v1/prompts?limit=1</code> and record the status. The API reference documents no listing for reusable prompts, so this is a probe with a reported result, and a 404 means ids must come from your own tree rather than that the content is already gone.</p>"""},
 {"h": "Declare the pmpt_ ids your code actually passes",
  "body": """<p><code>OPENAI_PROMPT_IDS</code> as a comma-separated list, or repeated <code>--prompt-id</code>. Take them from the deployed call sites. Anything that does not start <code>pmpt_</code> is graded as a configuration bug without a request; the rest are probed individually.</p>"""},
 {"h": "Print the plan with an owner per surface",
  "body": """<p>Three rows: what a script exports, what a script exports only by id, and what a person exports in the dashboard. Agent Builder is always the third. Then the export commands, and then the code change &mdash; in that order, because the second one is impossible before the first.</p>"""},
],
"verify": """<p>Re-run after the export pass. The eval count should not move, because listing does not consume anything, and that is the point: the check is idempotent and the artefact lives in your repository now. What should change is the prompt roster, which shrinks as call sites move from <code>prompt={"id": ...}</code> to inline <code>instructions</code> and the declared id list gets shorter. The row that will never go green is Agent Builder, and it should not: no rerun of a script can close a surface that has no API.</p>
<pre><code class="language-bash">OPENAI_PROMPT_IDS=pmpt_a1b2,pmpt_c3d4,promptx \\
  python3 sunset_export_audit.py
# three surfaces close 2026-11-30, 91 day(s) left
#   evals          200  enumerable        the listing answered, so these can be exported
#                                         by script
#   prompts        404  no-list-endpoint  nothing answered at this path, so ids have to
#                                         come from your own call sites
#   agent-builder  ---  no-api-surface    no documented REST endpoints exist, so nothing
#                                         here can inventory or export it
# 12 eval(s) listed, and the listing carries the full definition
#   curl -s -H "Authorization: Bearer $OPENAI_API_KEY" \\
#        https://api.openai.com/v1/evals?limit=100 > export/evals.json
# 3 declared prompt id(s)
#   pmpt_a1b2  200  readable         the stored content came back
#   pmpt_c3d4  404  not-readable     nothing answered, so its text comes out of the
#                                    dashboard before the date
#   promptx    ---  not-a-prompt-id  reusable prompt ids start pmpt_, so this is a
#                                    configuration bug and not an id
# plan
#   evals          a script          one GET per page dumps the full objects
#   prompts        a script, by id   probe the ids you hold; the rest is the dashboard
#   agent-builder  a person          there is no endpoint, so nothing automates this
# 4 finding(s)</code></pre>""",
"code_intro": "One paginated listing, one probe, one probe per declared id, and five pure functions. <code>days_left</code>, arithmetic against the published date; <code>surface_reach</code>, which grades how far the API gets on one surface and returns <code>no-api-surface</code> for Agent Builder whatever status it is handed; <code>prompt_id_state</code>, which grades the shape of an id before it grades a response, so a string that is not a prompt id never costs a request; <code>export_plan</code>, the only function that turns reach into an owner, which is the output somebody can act on; and <code>export_command</code>, which builds the exact GET to run and is asserted by a test to be a read.",
"py_file": "sunset_export_audit.py",
"py": '''"""Audit three closing surfaces for what can still be exported, and by whom.

Read only. Every request is a GET: the evals listing, one probe of the prompts
path, and one probe per prompt id you declare. Nothing here creates an eval, a
run or a prompt version.

The unit is exportability rather than validity, because what closes on
2026-11-30 is content held on the provider's side. The three surfaces are not
equally reachable and the script refuses to hide that: evals list cleanly,
reusable prompts have no documented list endpoint so the path is probed rather
than assumed, and Agent Builder has no REST surface at all and is graded
without a request.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("sunset_export_audit")

API = "https://api.openai.com/v1"

# Announced 3 June 2026. Reusable Prompts, the Evals dashboard and API, and
# Agent Builder all close on this date. Published, not readable.
SHUTDOWN = "2026-11-30"

# Checked against the API reference index: there is a documented listing for
# evals and none for reusable prompts, and Agent Builder has no REST endpoints
# at all. That asymmetry is the reason this script grades reach per surface
# instead of running one loop over three paths.
AGENT_BUILDER = "agent-builder"

FINDINGS = ("no-api-surface", "no-list-endpoint", "not-readable",
            "not-a-prompt-id", "malformed", "credentials", "refused",
            "unreachable", "content-to-export")

REPAIRS = {
    "no-api-surface":
        "there is no endpoint, so nothing here automates it. Somebody has to "
        "open Agent Builder, export each published workflow, and rebuild it "
        "with the Agents SDK before the date.",
    "no-list-endpoint":
        "the API reference documents no listing for reusable prompts, so the "
        "authoritative roster is a grep of your own tree for pmpt_ ids. "
        "Anything only a colleague remembers comes out of the dashboard.",
    "not-readable":
        "nothing answered for this id, so its text is not retrievable by "
        "script. Copy it out of the dashboard and put it in the repository "
        "before the date, because after it there is nowhere to copy from.",
    "not-a-prompt-id":
        "reusable prompt ids start pmpt_. Fix the configuration; this one was "
        "never going to resolve, shutdown or no shutdown.",
    "content-to-export":
        "the listing carries the full definition, so one paginated GET is the "
        "whole export. Save it into the repository, then migrate the suites "
        "to Promptfoo.",
}


def days_left(today, when=SHUTDOWN):
    """Whole days from today to the date. Pure. Negative once it has passed."""
    return (dt.date.fromisoformat(str(when))
            - dt.date.fromisoformat(str(today))).days


def surface_reach(name, status):
    """How far the API gets on one surface. Pure. Returns (state, detail).

    Agent Builder is graded without a request and cannot be promoted by one:
    passing a 200 here still returns no-api-surface, because there is no path
    that 200 could have come from. That is asserted in a test, so a stray
    status from somewhere else can never make the report look complete.
    """
    if str(name) == AGENT_BUILDER:
        return ("no-api-surface",
                "no documented REST endpoints exist, so nothing here can "
                "inventory or export it")
    if status is None:
        return ("unreachable", "no response at all from this path")
    status = int(status)
    if status == 200:
        return ("enumerable",
                "the listing answered, so these can be exported by script")
    if status == 404:
        return ("no-list-endpoint",
                "nothing answered at this path, so ids have to come from your "
                "own call sites")
    if status in (401, 403):
        return ("credentials",
                "%d, so the reach of this surface was not established" % status)
    return ("refused", "%d, so the reach of this surface is unknown" % status)


def prompt_id_state(pid, status):
    """Grade one declared prompt id. Pure. Returns (state, detail).

    Shape first, response second. An id that is not a prompt id is a bug in the
    configuration and needs no request to prove it, and probing it anyway would
    bury a definite finding underneath a status code.
    """
    if not isinstance(pid, str) or not pid.strip():
        return ("malformed",
                "not a usable string, so this is a configuration bug rather "
                "than an id")
    pid = pid.strip()
    if not pid.startswith("pmpt_"):
        return ("not-a-prompt-id",
                "reusable prompt ids start pmpt_, so this is something else")
    if status is None:
        return ("not-probed", "no request was made for this id")
    status = int(status)
    if status == 200:
        return ("readable", "the stored content came back")
    if status == 404:
        return ("not-readable",
                "nothing answered, so its text comes out of the dashboard "
                "before the date")
    if status in (401, 403):
        return ("credentials", "%d, which is the key and not the id" % status)
    return ("refused", "%d" % status)


def export_plan(rows):
    """Turn reach into an owner per surface. Pure. [(name, owner, line)].

    The output somebody can actually act on: three rows, three owners, and no
    surface silently missing from the report.
    """
    plan = []
    for name, state in rows or []:
        if state == "enumerable":
            plan.append((name, "a script",
                         "one GET per page dumps the full objects"))
        elif state == "no-list-endpoint":
            plan.append((name, "a script, by id",
                         "probe the ids you hold; the rest is the dashboard"))
        elif state == "no-api-surface":
            plan.append((name, "a person",
                         "there is no endpoint, so nothing automates this"))
        else:
            plan.append((name, "a person, until proven otherwise",
                         "the reach could not be established, so assume the "
                         "dashboard"))
    return plan


def export_command(kind, ident=None):
    """The exact GET to run for one export. Pure. Printed, never performed."""
    auth = '-H "Authorization: Bearer $OPENAI_API_KEY"'
    if kind == "evals":
        return ("curl -s %s %s/evals?limit=100 > export/evals.json"
                % (auth, API))
    if kind == "prompt":
        return ("curl -s %s %s/prompts/%s > export/%s.json"
                % (auth, API, ident, ident))
    return ""


def repair_lines(state):
    """The repair for one verdict. Pure. Printed, never performed."""
    line = REPAIRS.get(state)
    if not line:
        return []
    if state in ("no-list-endpoint", "not-readable"):
        return [line,
                "then inline it: prompt={id: pmpt_...} becomes an instructions "
                "string you hold, which is the short half of this job and the "
                "half that is impossible before the export."]
    return [line]


def get_json(session, path, key, params=None, timeout=30):
    """One GET. Returns (status, parsed body). Never raises on a 4xx."""
    try:
        r = session.get(API + path,
                        headers={"Authorization": "Bearer " + key},
                        params=params or {}, timeout=timeout)
    except requests.RequestException as exc:
        log.debug("GET %s failed: %s", path, exc)
        return (None, {})
    try:
        return (r.status_code, r.json())
    except ValueError:
        return (r.status_code, {})


def all_evals(session, key, pages=50):
    """Walk GET /v1/evals to the end. Returns (status, [eval objects]).

    The listing carries data_source_config and testing_criteria, so the page is
    the export and there is no per-id fetch to write.
    """
    out, after, first = [], None, None
    for _ in range(pages):
        params = {"limit": 100, "order": "asc"}
        if after:
            params["after"] = after
        status, body = get_json(session, "/evals", key, params)
        if first is None:
            first = status
        if status != 200:
            break
        page = body.get("data") or []
        out.extend(page)
        if not page or not body.get("has_more"):
            break
        after = page[-1].get("id")
        if not after:
            break
    return (first, out)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--prompt-id", action="append", default=[],
                    help="a pmpt_ id your code passes (repeatable)")
    ap.add_argument("--today", default=dt.date.today().isoformat(),
                    help="override the date the arithmetic is done against")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project read key. This script only "
                  "issues GET requests")
        return 2

    left = days_left(args.today)
    log.info("three surfaces close %s, %d day(s) %s", SHUTDOWN, abs(left),
             "left" if left >= 0 else "past")

    session = requests.Session()
    findings = 0
    reach = []

    eval_status, evals = all_evals(session, key)
    prompt_status, _ = get_json(session, "/prompts", key, {"limit": 1})
    probes = [("evals", eval_status), ("prompts", prompt_status),
              (AGENT_BUILDER, None)]
    for name, status in probes:
        state, detail = surface_reach(name, status)
        reach.append((name, state))
        emit = log.warning if state in FINDINGS else log.info
        emit("  %-14s %s  %-17s %s", name,
             "---" if status is None else status, state, detail)
        for line in repair_lines(state):
            emit("    repair: %s", line)
        if state in FINDINGS:
            findings += 1

    if evals:
        log.warning("%d eval(s) listed, and the listing carries the full "
                    "definition", len(evals))
        log.warning("  %s", export_command("evals"))
        for line in repair_lines("content-to-export"):
            log.warning("  repair: %s", line)
        findings += 1

    declared = list(args.prompt_id)
    declared += [p.strip() for p in
                 (os.environ.get("OPENAI_PROMPT_IDS") or "").split(",")
                 if p.strip()]
    if declared:
        log.info("%d declared prompt id(s)", len(declared))
    for pid in declared:
        text = pid.strip() if isinstance(pid, str) else pid
        status = None
        if isinstance(text, str) and text.startswith("pmpt_"):
            status, _ = get_json(session, "/prompts/" + text, key)
        state, detail = prompt_id_state(text, status)
        emit = log.warning if state in FINDINGS else log.info
        emit("  %-12s %s  %-16s %s", text,
             "---" if status is None else status, state, detail)
        if state == "readable":
            log.info("    %s", export_command("prompt", text))
        for line in repair_lines(state):
            emit("    repair: %s", line)
        if state in FINDINGS:
            findings += 1

    log.info("plan")
    for name, owner, line in export_plan(reach):
        log.info("  %-14s %-28s %s", name, owner, line)

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "sunset-export-audit.mjs",
"js": '''/**
 * Audit three closing surfaces for what can still be exported, and by whom.
 *
 * Read only. Every request is a GET: the evals listing, one probe of the
 * prompts path, and one probe per declared prompt id. Nothing here creates an
 * eval, a run or a prompt version.
 *
 * The unit is exportability rather than validity, because what closes on
 * 2026-11-30 is content held on the provider's side. Evals list cleanly,
 * reusable prompts have no documented list endpoint so the path is probed
 * rather than assumed, and Agent Builder has no REST surface at all.
 */
export const API = 'https://api.openai.com/v1';

// Announced 3 June 2026. Published, not readable.
export const SHUTDOWN = '2026-11-30';

export const AGENT_BUILDER = 'agent-builder';

const FINDINGS = new Set(['no-api-surface', 'no-list-endpoint', 'not-readable',
  'not-a-prompt-id', 'malformed', 'credentials', 'refused', 'unreachable',
  'content-to-export']);

const REPAIRS = {
  'no-api-surface':
    'there is no endpoint, so nothing here automates it. Somebody has to open '
    + 'Agent Builder, export each published workflow, and rebuild it with the '
    + 'Agents SDK before the date.',
  'no-list-endpoint':
    'the API reference documents no listing for reusable prompts, so the '
    + 'authoritative roster is a grep of your own tree for pmpt_ ids. Anything '
    + 'only a colleague remembers comes out of the dashboard.',
  'not-readable':
    'nothing answered for this id, so its text is not retrievable by script. '
    + 'Copy it out of the dashboard and put it in the repository before the '
    + 'date, because after it there is nowhere to copy from.',
  'not-a-prompt-id':
    'reusable prompt ids start pmpt_. Fix the configuration; this one was never '
    + 'going to resolve, shutdown or no shutdown.',
  'content-to-export':
    'the listing carries the full definition, so one paginated GET is the whole '
    + 'export. Save it into the repository, then migrate the suites to Promptfoo.',
};

const day = (iso) => Date.parse(`${iso}T00:00:00Z`);

/** Whole days from today to the date. Pure. Negative once it has passed. */
export function daysLeft(today, when = SHUTDOWN) {
  return Math.round((day(String(when)) - day(String(today))) / 86400000);
}

/** How far the API gets on one surface. Pure. [state, detail]. */
export function surfaceReach(name, status) {
  if (String(name) === AGENT_BUILDER) {
    return ['no-api-surface',
      'no documented REST endpoints exist, so nothing here can inventory or export it'];
  }
  if (status === null || status === undefined) {
    return ['unreachable', 'no response at all from this path'];
  }
  const s = Number(status);
  if (s === 200) {
    return ['enumerable', 'the listing answered, so these can be exported by script'];
  }
  if (s === 404) {
    return ['no-list-endpoint',
      'nothing answered at this path, so ids have to come from your own call sites'];
  }
  if (s === 401 || s === 403) {
    return ['credentials', `${s}, so the reach of this surface was not established`];
  }
  return ['refused', `${s}, so the reach of this surface is unknown`];
}

/** Grade one declared prompt id. Pure. Shape first, response second. */
export function promptIdState(pid, status) {
  if (typeof pid !== 'string' || !pid.trim()) {
    return ['malformed',
      'not a usable string, so this is a configuration bug rather than an id'];
  }
  const id = pid.trim();
  if (!id.startsWith('pmpt_')) {
    return ['not-a-prompt-id', 'reusable prompt ids start pmpt_, so this is something else'];
  }
  if (status === null || status === undefined) {
    return ['not-probed', 'no request was made for this id'];
  }
  const s = Number(status);
  if (s === 200) return ['readable', 'the stored content came back'];
  if (s === 404) {
    return ['not-readable',
      'nothing answered, so its text comes out of the dashboard before the date'];
  }
  if (s === 401 || s === 403) return ['credentials', `${s}, which is the key and not the id`];
  return ['refused', `${s}`];
}

/** Turn reach into an owner per surface. Pure. [[name, owner, line]]. */
export function exportPlan(rows) {
  return (rows || []).map(([name, state]) => {
    if (state === 'enumerable') {
      return [name, 'a script', 'one GET per page dumps the full objects'];
    }
    if (state === 'no-list-endpoint') {
      return [name, 'a script, by id', 'probe the ids you hold; the rest is the dashboard'];
    }
    if (state === 'no-api-surface') {
      return [name, 'a person', 'there is no endpoint, so nothing automates this'];
    }
    return [name, 'a person, until proven otherwise',
      'the reach could not be established, so assume the dashboard'];
  });
}

/** The exact GET to run for one export. Pure. Printed, never performed. */
export function exportCommand(kind, ident = null) {
  const auth = '-H "Authorization: Bearer $OPENAI_API_KEY"';
  if (kind === 'evals') return `curl -s ${auth} ${API}/evals?limit=100 > export/evals.json`;
  if (kind === 'prompt') {
    return `curl -s ${auth} ${API}/prompts/${ident} > export/${ident}.json`;
  }
  return '';
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state) {
  const line = REPAIRS[state];
  if (!line) return [];
  if (state === 'no-list-endpoint' || state === 'not-readable') {
    return [line,
      'then inline it: prompt={id: pmpt_...} becomes an instructions string you '
      + 'hold, which is the short half of this job and the half that is '
      + 'impossible before the export.'];
  }
  return [line];
}

async function getJson(path, key, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    for (const one of Array.isArray(v) ? v : [v]) url.searchParams.append(k, String(one));
  }
  try {
    const r = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
    let body = {};
    try { body = await r.json(); } catch { body = {}; }
    return [r.status, body];
  } catch {
    return [null, {}];
  }
}

async function allEvals(key, pages = 50) {
  const out = [];
  let after = null;
  let first = null;
  for (let i = 0; i < pages; i += 1) {
    const params = { limit: 100, order: 'asc' };
    if (after) params.after = after;
    const [status, body] = await getJson('/evals', key, params);
    if (first === null) first = status;
    if (status !== 200) break;
    const page = body.data || [];
    out.push(...page);
    if (!page.length || !body.has_more) break;
    after = page[page.length - 1].id;
    if (!after) break;
  }
  return [first, out];
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project read key. This script only '
                  + 'issues GET requests');
    process.exitCode = 2;
    return;
  }
  const today = process.env.TODAY || new Date().toISOString().slice(0, 10);
  const left = daysLeft(today);
  console.log(`three surfaces close ${SHUTDOWN}, ${Math.abs(left)} day(s) `
              + `${left >= 0 ? 'left' : 'past'}`);

  let findings = 0;
  const reach = [];
  const [evalStatus, evals] = await allEvals(key);
  const [promptStatus] = await getJson('/prompts', key, { limit: 1 });

  for (const [name, status] of [['evals', evalStatus], ['prompts', promptStatus],
                                [AGENT_BUILDER, null]]) {
    const [state, detail] = surfaceReach(name, status);
    reach.push([name, state]);
    console.log(`  ${name.padEnd(14)} ${status ?? '---'}  ${state.padEnd(17)} ${detail}`);
    for (const line of repairLines(state)) console.log(`    repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;
  }

  if (evals.length) {
    console.log(`${evals.length} eval(s) listed, and the listing carries the full definition`);
    console.log(`  ${exportCommand('evals')}`);
    for (const line of repairLines('content-to-export')) console.log(`  repair: ${line}`);
    findings += 1;
  }

  const declared = (process.env.OPENAI_PROMPT_IDS ?? '')
    .split(',').map((s) => s.trim()).filter(Boolean);
  if (declared.length) console.log(`${declared.length} declared prompt id(s)`);
  for (const pid of declared) {
    let status = null;
    if (pid.startsWith('pmpt_')) [status] = await getJson(`/prompts/${pid}`, key);
    const [state, detail] = promptIdState(pid, status);
    console.log(`  ${pid.padEnd(12)} ${status ?? '---'}  ${state.padEnd(16)} ${detail}`);
    if (state === 'readable') console.log(`    ${exportCommand('prompt', pid)}`);
    for (const line of repairLines(state)) console.log(`    repair: ${line}`);
    if (FINDINGS.has(state)) findings += 1;
  }

  console.log('plan');
  for (const [name, owner, line] of exportPlan(reach)) {
    console.log(`  ${name.padEnd(14)} ${owner.padEnd(28)} ${line}`);
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the one that keeps the report honest: Agent Builder grades as <code>no-api-surface</code> even when a 200 is handed to it, because there is no path that 200 could have come from, and a surface with no API must never be promoted to covered by a stray status. The second is the correction this note was written around &mdash; a 404 on the prompts path is <code>no-list-endpoint</code>, not <code>gone</code>, and the detail sends you to your own call sites rather than to a conclusion the evidence does not support. Then the plan, asserted to put a person against exactly the surfaces a script cannot reach. Then the shape check, which catches an id that is not a prompt id with no request made at all. And finally the export command, asserted to be a read: a GET, with no write verb anywhere in it.",
"test_py_file": "test_sunset_export_audit.py",
"test_py": '''from sunset_export_audit import (AGENT_BUILDER, SHUTDOWN, days_left,
                                 export_command, export_plan, prompt_id_state,
                                 repair_lines, surface_reach)

TODAY = "2026-08-31"


def test_a_surface_with_no_api_is_never_promoted_by_a_stray_status():
    # There is no path a 200 could have come from, so one must not make the
    # report look complete. This is the whole reason the row exists.
    for status in (None, 200, 404, 401):
        state, detail = surface_reach(AGENT_BUILDER, status)
        assert state == "no-api-surface"
        assert "no documented REST endpoints" in detail
    assert any("open Agent Builder" in line
               for line in repair_lines("no-api-surface"))


def test_a_404_on_the_prompts_path_means_no_listing_and_not_gone():
    # Those imply different next steps and only one is supported by the
    # evidence: the API reference documents no listing for reusable prompts.
    state, detail = surface_reach("prompts", 404)
    assert state == "no-list-endpoint"
    assert "your own call sites" in detail
    assert "gone" not in detail
    lines = repair_lines(state)
    assert any("grep of your own tree" in line for line in lines)
    assert any("impossible before the export" in line for line in lines)


def test_the_plan_puts_a_person_against_what_no_script_can_reach():
    plan = export_plan([("evals", "enumerable"),
                        ("prompts", "no-list-endpoint"),
                        (AGENT_BUILDER, "no-api-surface"),
                        ("something", "credentials")])
    owners = {name: owner for name, owner, _ in plan}
    assert owners["evals"] == "a script"
    assert owners["prompts"] == "a script, by id"
    assert owners[AGENT_BUILDER] == "a person"
    assert owners["something"].startswith("a person, until")
    assert len(plan) == 4


def test_an_id_that_is_not_a_prompt_id_is_caught_without_a_request():
    state, detail = prompt_id_state("promptx", None)
    assert state == "not-a-prompt-id"
    assert "start pmpt_" in detail
    assert prompt_id_state("", None)[0] == "malformed"
    assert prompt_id_state(None, 200)[0] == "malformed"
    # A real id with no probe is honestly reported as not probed, which is a
    # different thing from unreadable.
    assert prompt_id_state("pmpt_a1b2", None)[0] == "not-probed"


def test_a_declared_id_is_graded_by_what_answered_for_it():
    assert prompt_id_state("pmpt_a1b2", 200)[0] == "readable"
    state, detail = prompt_id_state("  pmpt_c3d4  ", 404)
    assert state == "not-readable"
    assert "out of the dashboard" in detail
    assert prompt_id_state("pmpt_c3d4", 401)[0] == "credentials"
    assert prompt_id_state("pmpt_c3d4", 500)[0] == "refused"


def test_the_export_command_is_a_read():
    line = export_command("evals")
    assert line.startswith("curl -s ")
    assert "/v1/evals?limit=100" in line
    assert "$OPENAI_API_KEY" in line
    assert "-X" not in line
    assert export_command("prompt", "pmpt_a1b2").endswith("export/pmpt_a1b2.json")
    assert export_command("agent-builder") == ""


def test_the_date_is_the_export_deadline_and_the_arithmetic_says_so():
    assert days_left(TODAY) == 91
    assert days_left("2026-11-30") == 0
    assert days_left("2026-12-05") == -5
    assert SHUTDOWN == "2026-11-30"
''',
"test_js_file": "sunset-export-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { AGENT_BUILDER, SHUTDOWN, daysLeft, exportCommand, exportPlan,
         promptIdState, repairLines, surfaceReach } from './sunset-export-audit.mjs';

const TODAY = '2026-08-31';

test('a surface with no api is never promoted by a stray status', () => {
  for (const status of [null, 200, 404, 401]) {
    const [state, detail] = surfaceReach(AGENT_BUILDER, status);
    assert.equal(state, 'no-api-surface');
    assert.ok(detail.includes('no documented REST endpoints'));
  }
  assert.ok(repairLines('no-api-surface').some((l) => l.includes('open Agent Builder')));
});

test('a 404 on the prompts path means no listing and not gone', () => {
  const [state, detail] = surfaceReach('prompts', 404);
  assert.equal(state, 'no-list-endpoint');
  assert.ok(detail.includes('your own call sites'));
  assert.ok(!detail.includes('gone'));
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes('grep of your own tree')));
  assert.ok(lines.some((l) => l.includes('impossible before the export')));
});

test('the plan puts a person against what no script can reach', () => {
  const plan = exportPlan([['evals', 'enumerable'],
                           ['prompts', 'no-list-endpoint'],
                           [AGENT_BUILDER, 'no-api-surface'],
                           ['something', 'credentials']]);
  const owners = Object.fromEntries(plan.map(([n, o]) => [n, o]));
  assert.equal(owners.evals, 'a script');
  assert.equal(owners.prompts, 'a script, by id');
  assert.equal(owners[AGENT_BUILDER], 'a person');
  assert.ok(owners.something.startsWith('a person, until'));
  assert.equal(plan.length, 4);
});

test('an id that is not a prompt id is caught without a request', () => {
  const [state, detail] = promptIdState('promptx', null);
  assert.equal(state, 'not-a-prompt-id');
  assert.ok(detail.includes('start pmpt_'));
  assert.equal(promptIdState('', null)[0], 'malformed');
  assert.equal(promptIdState(null, 200)[0], 'malformed');
  assert.equal(promptIdState('pmpt_a1b2', null)[0], 'not-probed');
});

test('a declared id is graded by what answered for it', () => {
  assert.equal(promptIdState('pmpt_a1b2', 200)[0], 'readable');
  const [state, detail] = promptIdState('  pmpt_c3d4  ', 404);
  assert.equal(state, 'not-readable');
  assert.ok(detail.includes('out of the dashboard'));
  assert.equal(promptIdState('pmpt_c3d4', 401)[0], 'credentials');
  assert.equal(promptIdState('pmpt_c3d4', 500)[0], 'refused');
});

test('the export command is a read', () => {
  const line = exportCommand('evals');
  assert.ok(line.startsWith('curl -s '));
  assert.ok(line.includes('/v1/evals?limit=100'));
  assert.ok(line.includes('$OPENAI_API_KEY'));
  assert.ok(!line.includes('-X'));
  assert.ok(exportCommand('prompt', 'pmpt_a1b2').endsWith('export/pmpt_a1b2.json'));
  assert.equal(exportCommand('agent-builder'), '');
});

test('the date is the export deadline and the arithmetic says so', () => {
  assert.equal(daysLeft(TODAY), 91);
  assert.equal(daysLeft('2026-11-30'), 0);
  assert.equal(daysLeft('2026-12-05'), -5);
  assert.equal(SHUTDOWN, '2026-11-30');
});
''',
"faq": [
 ("Can I list my reusable prompts through the API?",
  "Not according to the reference. There is no documented endpoint for reusable prompts anywhere in the API reference index, which is why this script probes GET /v1/prompts and prints the status it got rather than asserting a listing exists. If the path answers, the script says so and your job gets easier. If it 404s, that is reported as no list endpoint rather than as gone, because the two mean different things: the content may be perfectly alive in the dashboard while being unenumerable from code. Either way the authoritative roster is a grep of your own tree for pmpt_ ids."),
 ("Why is Agent Builder in a report about API calls at all?",
  "Because leaving it out is how a report about three surfaces becomes a green summary about two. Agent Builder has no REST endpoints, so the script grades it without a request and assigns it to a person in the dashboard. There is a test that this row cannot be promoted by a status code — hand it a 200 and it still returns no-api-surface, because there is no path that 200 could have come from."),
 ("Do I need to fetch each eval individually to export it?",
  "No, and that is worth knowing before you write the loop. GET /v1/evals returns the full eval object per row, including name, data_source_config and testing_criteria, so the paginated listing is itself the export. Save the pages, put them in the repository, and migrate the suites to Promptfoo, which is the replacement OpenAI names. The prompts half of this job is the hard half precisely because it has no equivalent."),
 ("Is a stored prompt the same thing as prompt caching?",
  "No, and confusing them is easy because both involve a prompt living somewhere other than your request. A reusable prompt is a content object with an id and versions that you reference instead of sending the text; prompt caching is a billing and latency mechanism for text you do send. This closure affects the first and not the second. Nothing here changes your cached share, and nothing about caching survives or replaces a pmpt_ id."),
 ("What actually breaks on 1 December if I do nothing?",
  "Any call that passes a pmpt_ id to the Responses API fails as an invalid request, because the referenced object no longer resolves. The code does not stop compiling and the deploy does not fail; the request does. The worse loss is quieter: the prompt text and the eval definitions were never in your repository, so there is nothing to restore from. That is why the script orders the output as export first and code change second — the second is a few lines and is impossible without the first."),
],
"related": [REL_ASSISTANTS, REL_CACHE_NEVER, REL_90_DAYS],
"citations": [CITE_DEPRECATIONS, CITE_EVALS, CITE_RESPONSES, CITE_ADMIN],
},
{
"slug": "fine-tuning-jobs-blocked",
"title": "Fine-tuning stops taking new jobs while old ones keep serving",
"description": "Two verbs, two deadlines. Whether you can still create a job depends on your own last 60 days of fine-tuned inference, and that is readable.",
"h1": "Fine-tuning stops taking new jobs while old ones keep serving",
"category": "LLM APIs",
"pill": "Diagnostic",
"chips": ["Read-only key", "Python and Node.js", "Tests included"],
"keywords": ["openai fine-tuning wind down 2027-01-06 new jobs",
             "fine-tuned base model shutdown 2026-10-23",
             "cannot create fine-tuning job organization restriction",
             "ft: model inference 60 days eligibility",
             "retrain fine-tune before base model deprecated"],
"deps": "Python 3.9+ with requests, or Node.js 18+. Needs OPENAI_API_KEY, a project read key, for GETs of /v1/fine_tuning/jobs and /v1/models/{id}. Optionally OPENAI_ADMIN_KEY with api.usage.read, which is what makes the 60-day eligibility clock readable rather than guessed.",
"lead": "Nothing is broken, which is the problem. The classifier fine-tune is serving traffic, the job list is full of green, and the plan &mdash; retrain it in the new year when there is time &mdash; sounds entirely reasonable to everybody in the room. It is not reasonable, and the reason is not on any dashboard: nobody has run inference against a fine-tuned model in about nine weeks, because the classifier was quietly replaced by a prompt in June and only the old batch job still calls it. The right to create a fine-tuning job expired somewhere in there. There was no notification, because nothing happened.",
"short_answer": """<p>Split the resource by verb, because the two halves have different deadlines and only one of them is on a calendar. <strong>Creating</strong> a job and <strong>serving</strong> an existing fine-tune are separate rights with separate clocks, and an organization can lose the first while the second still looks perfectly healthy.</p>
<p>The create side ramps in three steps. From <strong>2026-05-07</strong> an organization that has never run fine-tuning cannot start; from <strong>2026-07-02</strong> an organization that has not run inference on a fine-tuned model <em>in the past 60 days</em> cannot start; and from <strong>2027-01-06</strong> nobody can. That middle rule is the one worth a script, because it is not a date you can diary. It is a rolling window over your own traffic, so it closes silently on a Tuesday when the last <code>ft:</code> call ages out.</p>
<p>And it is readable. <code>GET /v1/fine_tuning/jobs</code> with a <strong>project read key</strong> tells you whether this organization has ever fine-tuned; <code>GET /v1/organization/usage/completions</code> grouped by <code>model</code> with an <strong>admin-read key</strong> tells you the last day any <code>ft:</code> prefixed id produced requests. Those two facts decide eligibility. The script computes the clock from them and <strong>never submits a job</strong> to test it &mdash; a note about an endpoint that stopped accepting work has no business submitting work.</p>
<p>The serving side is a date and a different one: every fine-tunable base in the deprecation table shuts down <strong>2026-10-23</strong>, which is before the create cutoff arrives. So the two clocks cross. Your existing fine-tunes stop serving in October, and the window to retrain onto a supported base closes in January. Discover that in October and you have about ten weeks, once, ever.</p>
<p>The script reads <code>shutdown_date</code> off each fine-tuned model and off its base where the API supplies one, and falls back to the published table by family where it does not &mdash; labelling which is which, because those are different grades of evidence.</p>""",
"problem": """<p>Announced 7 May 2026, self-serve fine-tuning is being wound down in stages rather than switched off. That is generous and it is also why it goes unnoticed: a staged withdrawal produces no single failing day for most organizations, and the stage that catches people is the second one, which is not a date at all. From 2 July 2026, creating a job requires that the organization has run inference on a fine-tuned model within the last 60 days.</p>
<p>Read that again as an operational fact. Eligibility is a rolling window over your own traffic. It closes without a deploy, without an error, and without anybody doing anything &mdash; specifically, it closes because somebody did nothing, which is the hardest kind of change to notice. A team that replaced its fine-tune with a prompt in the spring is disqualified from retraining it in the autumn, and the first evidence is a rejected create call at the exact moment they need one.</p>
<p>The other half of the wind-down is a hard date and it lands first. Every fine-tunable base named in the deprecation table &mdash; the <code>ft-gpt-3.5-turbo</code>, <code>ft-gpt-4</code>, <code>ft-gpt-4.1-nano-2025-04-14</code>, <code>ft-babbage-002</code>, <code>ft-davinci-002</code> and <code>ft-o4-mini-2025-04-16</code> families &mdash; shuts down on 23 October 2026. Inference on a fine-tune dies with its base, so the model serving your traffic today has a date on it whether or not anybody has looked.</p>
<p>Put together, the dates cross in the worst possible order. October removes the models. January removes the ability to make new ones. An organization that discovers the first in October has one narrow window to retrain everything it wants to keep, and if the 60-day inference clock has also lapsed in the meantime, it does not have that window either.</p>""",
"why": """<p><strong>One resource, two verbs, and the script reports them as two sections.</strong> Everything else in this batch closes an endpoint outright. Here the endpoint keeps answering: jobs list, models resolve, inference bills. What stops is one verb, on a schedule that has nothing to do with the other. Merging them into a single verdict would produce the exact sentence that gets somebody into trouble &mdash; "fine-tuning is fine" &mdash; which is true of one half and false of the other.</p>
<p><strong>Eligibility is computed from readable state, never from an attempt.</strong> The obvious way to find out whether you can still create a job is to create one. That is unacceptable here: it spends money, it trains a model nobody asked for, and it is a write in a section that promises never to write. So the eligibility function takes exactly three readable inputs &mdash; the date, whether the job list is non-empty, and days since the last <code>ft:</code> request &mdash; and there is a test that a blocked verdict is reached from those alone.</p>
<p><strong>The same zero means the opposite of what it means in the published note next door.</strong> <a href="/llm/fine-tuned-model-never-used/">The note about a fine-tune nobody calls</a> reads zero traffic on a trained model as waste: you paid to train it and never routed to it, so either route or retire. Here zero <code>ft:</code> traffic is an <em>eligibility clock that has already run out</em>. Same number, opposite meaning, opposite repair &mdash; that note tells you to retire the model, and this one tells you the traffic is the thing keeping your right to retrain alive.</p>
<p><strong>A date read off the API and a date read off a published table are labelled differently.</strong> Where <code>GET /v1/models/{id}</code> returns a <code>shutdown_date</code>, that is the authority and the script says so. Where it does not, the deprecation table's family row is the only source, and the script says <em>that</em>, because a published table lags and a reader deserves to know which kind of claim they are looking at.</p>
<p><strong>Base matching is exact or hyphen-delimited, and never a loose prefix.</strong> <code>gpt-4.1-nano-2025-04-14</code> starts with the characters <code>gpt-4</code>, and a careless prefix match files it under the wrong family with the wrong replacement. A base the table does not cover comes back as unknown rather than as the nearest-looking row, which is the same discipline the Sora note applies to replacements.</p>
<p><strong>This is not the published note about model ids in your configuration.</strong> That one greps your config strings and diffs them against the model list. Nothing here reads your configuration at all: the base model comes off the job object, where the platform recorded it, and the fine-tuned id comes off the same object. The unit is a job, not a string in a file.</p>""",
"steps": [
 {"h": "List the jobs, which answers the first eligibility question",
  "body": """<p><code>GET /v1/fine_tuning/jobs?limit=100</code>, paginating on <code>after</code>. An empty list past 2026-05-07 is already a blocked organization, and that is established from a listing rather than from an attempt.</p>"""},
 {"h": "Read the last day any ft: model produced requests",
  "body": """<p><code>GET /v1/organization/usage/completions?bucket_width=1d&amp;group_by[]=model</code> over about 70 days with an admin-read key. Any <code>results[].model</code> starting <code>ft:</code> with requests against it dates the clock. No admin key means no clock, and the script reports that as unknown rather than as fine.</p>"""},
 {"h": "Compute the create clock, and do not test it by creating",
  "body": """<p>Three inputs, all readable: the date, whether the job list is non-empty, and days since the last <code>ft:</code> request. Past 60 the create right is gone; between 45 and 60 it is expiring and the script prints the days left. Nothing submits a job to confirm this.</p>"""},
 {"h": "Read each fine-tune's serving deadline, and say where it came from",
  "body": """<p>Per succeeded job: <code>GET /v1/models/{fine_tuned_model}</code>, then the base, for a <code>shutdown_date</code>. Where the API gives one, that is the answer and it is labelled as measured. Where it does not, the family row in the deprecation table supplies 2026-10-23 and is labelled as published.</p>"""},
 {"h": "Print both halves and the order the work has to happen in",
  "body": """<p>Retraining needs eligibility, and eligibility needs recent <code>ft:</code> inference, so the sequence matters: keep the clock alive, retrain onto a supported base before October, and stop treating January as the deadline. It is the outside edge, not the schedule.</p>"""},
],
"verify": """<p>Re-run after the retraining pass. The create clock should reset, because a new job and the inference that follows it both refresh the 60-day window &mdash; that is the reading that proves the eligibility half is fixed. The serving half is proved differently: each retrained model's deadline should now come back from the API with a later date or none at all, rather than from the published table. A row that still says <code>published-table</code> is a fine-tune whose base the model object will not talk about, and it should stay visible.</p>
<pre><code class="language-bash">OPENAI_API_KEY=sk-proj-... OPENAI_ADMIN_KEY=sk-admin-... \\
  python3 fine_tuning_gate_audit.py
# create: 4 job(s) in the list, last ft: inference 63 day(s) ago
# blocked-no-recent-inference  no fine-tuned model has served a request for 63 day(s),
#                              and the 60 day rule has applied since 2026-07-02, so new
#                              jobs are already being refused. Read from usage, not from
#                              an attempt
#   repair: route real traffic to a fine-tune to reopen the window, or accept that this
#           organization is out of the fine-tuning business as of 2026-07-02
# serve: 3 succeeded job(s)
#   ft:gpt-4.1-nano-2025-04-14:acme::Ab12  2026-10-23  published-table  dying-soon
#                                          53 day(s) of inference left; retrain onto
#                                          gpt-5.6-luna
#   ft:gpt-3.5-turbo:acme::Cd34            2026-10-23  published-table  dying-soon
#                                          53 day(s) of inference left; retrain onto
#                                          gpt-5.6-terra
#   ft:gpt-4o-mini-2024-07-18:acme::Ef56   ---         unknown          no-base-date
# 4 finding(s)</code></pre>""",
"code_intro": "One paginated job listing, one usage report, two model lookups per job, and six pure functions. <code>days_left</code>, arithmetic against three published dates rather than one; <code>create_eligibility</code>, the centre of the note, which takes only readable inputs so that a test can prove a blocked verdict is reached without submitting anything; <code>family_for</code>, which matches a base exactly or on a hyphen boundary so <code>gpt-4.1-nano</code> can never collapse into <code>gpt-4</code>; <code>serving_deadline</code>, which returns the date together with where it came from, because a field the API stated and a row in a published table are different grades of evidence; <code>job_verdict</code>, which grades one fine-tune against its own deadline; and <code>repair_lines</code>, which prints two repairs because there are two verbs.",
"py_file": "fine_tuning_gate_audit.py",
"py": '''"""Grade two verbs on one resource: creating a fine-tuning job, and serving one.

Read only. Every request is a GET: the job listing, the organization usage
report, and the model objects for each fine-tune and its base. Nothing here
submits a job. That matters more than usual: the obvious way to find out
whether creation is still accepted is to attempt one, and attempting one spends
money, trains a model nobody asked for, and is a write.

So eligibility is computed from readable state instead. Three inputs decide it,
all of them readable with the keys this script already holds: the date, whether
the job list is non-empty, and how long it has been since any ft: prefixed
model produced a request.

The serving side is a separate clock and lands first. Every fine-tunable base
in the deprecation table shuts down 2026-10-23, before the create cutoff
arrives, so the two deadlines cross in the worst order.
"""
import argparse
import datetime as dt
import logging
import os
import sys

import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("fine_tuning_gate_audit")

API = "https://api.openai.com/v1"

# Announced 7 May 2026, in three stages. The middle one is the only rule here
# that is not a date: it is a rolling 60 day window over your own traffic.
NEVER_FINE_TUNED = "2026-05-07"   # never fine-tuned before: cannot create
NO_RECENT_INFERENCE = "2026-07-02"  # no ft: inference in 60 days: cannot create
CUTOFF = "2027-01-06"             # nobody can create
WINDOW = 60                       # days of ft: inference the middle rule wants

# Inference on a fine-tune dies with its base, and every fine-tunable base in
# the deprecation table shuts down on this date. Used only as the fallback when
# the model object itself carries no shutdown_date, and labelled as such.
BASE_SHUTDOWN = "2026-10-23"

# The deprecation table's six fine-tuned families and their replacements. The
# match is exact or hyphen-delimited, never a loose prefix: gpt-4.1-nano starts
# with the characters gpt-4 and must not be filed under ft-gpt-4 with the wrong
# replacement. A base the table does not cover comes back unknown rather than
# as the nearest-looking row.
FAMILIES = (
    ("gpt-3.5-turbo", "ft-gpt-3.5-turbo", "gpt-5.6-terra"),
    ("gpt-4.1-nano-2025-04-14", "ft-gpt-4.1-nano-2025-04-14", "gpt-5.6-luna"),
    ("gpt-4", "ft-gpt-4", "gpt-5.6-sol"),
    ("babbage-002", "ft-babbage-002", "gpt-5.6-terra"),
    ("davinci-002", "ft-davinci-002", "gpt-5.6-terra"),
    ("o4-mini-2025-04-16", "ft-o4-mini-2025-04-16", "gpt-5.6-terra"),
)

FINDINGS = ("blocked-never-fine-tuned", "blocked-no-recent-inference",
            "eligibility-expiring", "create-closed", "unknown-eligibility",
            "already-dead", "dying-soon", "no-base-date")

REPAIRS = {
    "blocked-never-fine-tuned":
        "this organization has no fine-tuning history and the "
        + NEVER_FINE_TUNED + " restriction has passed, so creation is already "
        "refused. Nothing reopens that.",
    "blocked-no-recent-inference":
        "route real traffic to a fine-tune to reopen the window, or accept "
        "that this organization is out of the fine-tuning business as of "
        + NO_RECENT_INFERENCE + ".",
    "eligibility-expiring":
        "the 60 day window is closing. Either retrain now, while creating a "
        "job is still permitted, or keep a real workload on a fine-tuned model "
        "so the clock does not run out on a quiet week.",
    "create-closed":
        "the " + CUTOFF + " cutoff has passed and no organization can create "
        "a fine-tuning job. Whatever is still serving is the last of it.",
    "unknown-eligibility":
        "the inference clock could not be read, so eligibility is unknown "
        "rather than fine. Re-run with an admin-read key before planning "
        "around it.",
    "already-dead":
        "the base is past its shutdown date, so this fine-tune has stopped "
        "serving. Retraining onto a supported base is the only route back, and "
        "it is only available until " + CUTOFF + ".",
    "dying-soon":
        "retrain onto the supported base before the date. Where the fine-tune "
        "only ever encoded formatting, evaluate replacing it with prompting "
        "plus structured outputs instead of retraining at all.",
    "no-base-date":
        "neither the model object nor the published table has a date for this "
        "base, so its serving deadline is unknown. Treat it as undated rather "
        "than as safe.",
}


def days_left(today, when):
    """Whole days from today to a date. Pure. Negative once it has passed."""
    return (dt.date.fromisoformat(str(when))
            - dt.date.fromisoformat(str(today))).days


def create_eligibility(today, has_prior_jobs, days_since_ft_inference):
    """Can this organization still create a job? Pure. (state, detail).

    Three readable inputs and nothing else. days_since_ft_inference is an int,
    the string "none-in-window" when the usage window held no ft: traffic at
    all, or None when it could not be read. There is a test that a blocked
    verdict comes out of these alone, because the alternative way to answer
    this question is to submit a job, and this script never will.
    """
    if days_left(today, CUTOFF) < 0:
        return ("create-closed",
                "the %s cutoff has passed, so no organization can create a "
                "fine-tuning job" % CUTOFF)
    if not has_prior_jobs and days_left(today, NEVER_FINE_TUNED) < 0:
        return ("blocked-never-fine-tuned",
                "the job list is empty and the %s restriction has passed, so "
                "this organization cannot create a job today. Read from the "
                "listing, not from an attempt" % NEVER_FINE_TUNED)
    if days_left(today, NO_RECENT_INFERENCE) >= 0:
        return ("eligible",
                "the 60 day inference rule does not apply until %s; %d day(s) "
                "until the %s cutoff"
                % (NO_RECENT_INFERENCE, days_left(today, CUTOFF), CUTOFF))
    if days_since_ft_inference is None:
        return ("unknown-eligibility",
                "the inference clock could not be read, so eligibility is "
                "unknown rather than fine")
    if days_since_ft_inference == "none-in-window":
        return ("blocked-no-recent-inference",
                "no fine-tuned model produced a request anywhere in the window "
                "read, so the %d day rule has already closed creation. Read "
                "from usage, not from an attempt" % WINDOW)
    days = int(days_since_ft_inference)
    if days > WINDOW:
        return ("blocked-no-recent-inference",
                "no fine-tuned model has served a request for %d day(s), and "
                "the %d day rule has applied since %s, so new jobs are already "
                "being refused. Read from usage, not from an attempt"
                % (days, WINDOW, NO_RECENT_INFERENCE))
    if days > 45:
        return ("eligibility-expiring",
                "the last fine-tuned request was %d day(s) ago, so %d day(s) "
                "of the %d day window are left"
                % (days, WINDOW - days, WINDOW))
    return ("eligible",
            "the last fine-tuned request was %d day(s) ago and %d day(s) "
            "remain until the %s cutoff"
            % (days, days_left(today, CUTOFF), CUTOFF))


def family_for(base_model):
    """The deprecation family and replacement for a base. Pure. (family, to).

    Exact or hyphen-delimited, never a loose prefix. gpt-4.1-nano-2025-04-14
    starts with the characters gpt-4, and filing it under ft-gpt-4 would print
    the wrong replacement with complete confidence.
    """
    base = str(base_model or "")
    for prefix, family, replacement in FAMILIES:
        if base == prefix or base.startswith(prefix + "-"):
            return (family, replacement)
    return (None, None)


def serving_deadline(api_shutdown_date, family):
    """When this fine-tune stops serving. Pure. (date, source, detail).

    Returns where the date came from as well as the date. A field the API
    stated and a row in a published table are different grades of evidence and
    a reader is entitled to know which one they are looking at.
    """
    if api_shutdown_date:
        return (str(api_shutdown_date), "api",
                "shutdown_date read off the model object")
    if family:
        return (BASE_SHUTDOWN, "published-table",
                "the model object carried no shutdown_date, so this is the %s "
                "row in the deprecation table" % family)
    return (None, "unknown",
            "neither the model object nor the published table has a date for "
            "this base")


def job_verdict(status, fine_tuned_model, deadline, today):
    """Grade one job's serving half. Pure. Returns (state, detail)."""
    if str(status) != "succeeded" or not fine_tuned_model:
        return ("not-serving",
                "status %s with no fine-tuned model, so nothing is serving "
                "from this job" % status)
    if not deadline:
        return ("no-base-date",
                "no serving deadline could be established for this base")
    left = days_left(today, deadline)
    if left < 0:
        return ("already-dead",
                "the base shut down %d day(s) ago, so this fine-tune has "
                "stopped serving" % -left)
    if left <= 90:
        return ("dying-soon", "%d day(s) of inference left" % left)
    return ("serving", "%d day(s) of inference left" % left)


def repair_lines(state, replacement=None):
    """The repair for one verdict. Pure. Printed, never performed."""
    line = REPAIRS.get(state)
    if not line:
        return []
    if state in ("dying-soon", "already-dead") and replacement:
        return [line, "the documented replacement base is %s." % replacement]
    if state == "blocked-no-recent-inference":
        return [line,
                "note the order the dates fall in: the bases die %s and the "
                "right to retrain closes %s, so October is the deadline and "
                "January is only the outside edge."
                % (BASE_SHUTDOWN, CUTOFF)]
    return [line]


def get_json(session, path, key, params=None, timeout=30):
    """One GET. Returns (status, parsed body). Never raises on a 4xx."""
    try:
        r = session.get(API + path,
                        headers={"Authorization": "Bearer " + key},
                        params=params or {}, timeout=timeout)
    except requests.RequestException as exc:
        log.debug("GET %s failed: %s", path, exc)
        return (None, {})
    try:
        return (r.status_code, r.json())
    except ValueError:
        return (r.status_code, {})


def all_jobs(session, key, pages=20):
    """Walk GET /v1/fine_tuning/jobs to the end."""
    out, after = [], None
    for _ in range(pages):
        params = {"limit": 100}
        if after:
            params["after"] = after
        status, body = get_json(session, "/fine_tuning/jobs", key, params)
        if status != 200:
            log.warning("job listing came back %s, so eligibility cannot be "
                        "read from it", status)
            break
        page = body.get("data") or []
        out.extend(page)
        if not page or not body.get("has_more"):
            break
        after = page[-1].get("id")
        if not after:
            break
    return out


def days_since_ft_inference(session, key, today, days=70):
    """Days since any ft: model produced a request. Int, sentinel, or None."""
    start = int((dt.datetime.now(dt.timezone.utc)
                 - dt.timedelta(days=days)).timestamp())
    status, body = get_json(session, "/organization/usage/completions", key,
                            {"start_time": start, "bucket_width": "1d",
                             "group_by[]": ["model"], "limit": 180})
    if status != 200:
        log.warning("usage report came back %s, so the inference clock could "
                    "not be read", status)
        return None
    last = None
    for bucket in body.get("data") or []:
        stamp = bucket.get("start_time")
        if not stamp:
            continue
        day = dt.datetime.fromtimestamp(int(stamp),
                                        dt.timezone.utc).date().isoformat()
        for row in bucket.get("results") or []:
            model = str(row.get("model") or "")
            if model.startswith("ft:") and (row.get("num_model_requests") or 0) > 0:
                last = day if last is None else max(last, day)
    if last is None:
        return "none-in-window"
    return -days_left(today, last)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--today", default=dt.date.today().isoformat(),
                    help="override the date the arithmetic is done against")
    args = ap.parse_args()

    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        log.error("set OPENAI_API_KEY to a project read key. This script only "
                  "issues GET requests and never submits a job")
        return 2

    session = requests.Session()
    findings = 0

    jobs = all_jobs(session, key)
    admin = os.environ.get("OPENAI_ADMIN_KEY")
    since = (days_since_ft_inference(session, admin, args.today)
             if admin else None)
    log.info("create: %d job(s) in the list, last ft: inference %s", len(jobs),
             "unknown" if since is None else
             "not in the window" if since == "none-in-window" else
             "%d day(s) ago" % since)

    state, detail = create_eligibility(args.today, bool(jobs), since)
    emit = log.warning if state in FINDINGS else log.info
    emit("%-28s %s", state, detail)
    for line in repair_lines(state):
        emit("  repair: %s", line)
    if state in FINDINGS:
        findings += 1

    succeeded = [j for j in jobs if str(j.get("status")) == "succeeded"
                 and j.get("fine_tuned_model")]
    log.info("serve: %d succeeded job(s)", len(succeeded))
    for job in succeeded:
        ftm = job.get("fine_tuned_model")
        base = job.get("model")
        family, replacement = family_for(base)
        _, ftm_body = get_json(session, "/models/" + str(ftm), key)
        shutdown = (ftm_body or {}).get("shutdown_date")
        if not shutdown and base:
            _, base_body = get_json(session, "/models/" + str(base), key)
            shutdown = (base_body or {}).get("shutdown_date")
        deadline, source, why = serving_deadline(shutdown, family)
        state, detail = job_verdict(job.get("status"), ftm, deadline,
                                    args.today)
        emit = log.warning if state in FINDINGS else log.info
        emit("  %-40s %-11s %-16s %-13s %s", ftm, deadline or "---", source,
             state, detail)
        log.debug("    %s", why)
        for line in repair_lines(state, replacement):
            emit("    repair: %s", line)
        if state in FINDINGS:
            findings += 1

    log.info("%d finding(s)", findings)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
''',
"js_file": "fine-tuning-gate-audit.mjs",
"js": '''/**
 * Grade two verbs on one resource: creating a fine-tuning job, and serving one.
 *
 * Read only. Every request is a GET: the job listing, the usage report, and
 * the model objects for each fine-tune and its base. Nothing here submits a
 * job. The obvious way to find out whether creation is still accepted is to
 * attempt one, and attempting one spends money, trains a model nobody asked
 * for, and is a write.
 *
 * So eligibility is computed from readable state: the date, whether the job
 * list is non-empty, and how long since any ft: model produced a request.
 */
export const API = 'https://api.openai.com/v1';

// Announced 7 May 2026, in three stages. The middle one is a rolling window
// over your own traffic rather than a date.
export const NEVER_FINE_TUNED = '2026-05-07';
export const NO_RECENT_INFERENCE = '2026-07-02';
export const CUTOFF = '2027-01-06';
export const WINDOW = 60;

// Inference on a fine-tune dies with its base. Fallback only, and labelled.
export const BASE_SHUTDOWN = '2026-10-23';

// Exact or hyphen-delimited, never a loose prefix: gpt-4.1-nano starts with
// the characters gpt-4 and must not be filed under ft-gpt-4.
export const FAMILIES = [
  ['gpt-3.5-turbo', 'ft-gpt-3.5-turbo', 'gpt-5.6-terra'],
  ['gpt-4.1-nano-2025-04-14', 'ft-gpt-4.1-nano-2025-04-14', 'gpt-5.6-luna'],
  ['gpt-4', 'ft-gpt-4', 'gpt-5.6-sol'],
  ['babbage-002', 'ft-babbage-002', 'gpt-5.6-terra'],
  ['davinci-002', 'ft-davinci-002', 'gpt-5.6-terra'],
  ['o4-mini-2025-04-16', 'ft-o4-mini-2025-04-16', 'gpt-5.6-terra'],
];

const FINDINGS = new Set(['blocked-never-fine-tuned', 'blocked-no-recent-inference',
  'eligibility-expiring', 'create-closed', 'unknown-eligibility', 'already-dead',
  'dying-soon', 'no-base-date']);

const REPAIRS = {
  'blocked-never-fine-tuned':
    `this organization has no fine-tuning history and the ${NEVER_FINE_TUNED} `
    + 'restriction has passed, so creation is already refused. Nothing reopens that.',
  'blocked-no-recent-inference':
    'route real traffic to a fine-tune to reopen the window, or accept that this '
    + `organization is out of the fine-tuning business as of ${NO_RECENT_INFERENCE}.`,
  'eligibility-expiring':
    'the 60 day window is closing. Either retrain now, while creating a job is '
    + 'still permitted, or keep a real workload on a fine-tuned model so the clock '
    + 'does not run out on a quiet week.',
  'create-closed':
    `the ${CUTOFF} cutoff has passed and no organization can create a fine-tuning `
    + 'job. Whatever is still serving is the last of it.',
  'unknown-eligibility':
    'the inference clock could not be read, so eligibility is unknown rather than '
    + 'fine. Re-run with an admin-read key before planning around it.',
  'already-dead':
    'the base is past its shutdown date, so this fine-tune has stopped serving. '
    + 'Retraining onto a supported base is the only route back, and it is only '
    + `available until ${CUTOFF}.`,
  'dying-soon':
    'retrain onto the supported base before the date. Where the fine-tune only ever '
    + 'encoded formatting, evaluate replacing it with prompting plus structured '
    + 'outputs instead of retraining at all.',
  'no-base-date':
    'neither the model object nor the published table has a date for this base, so '
    + 'its serving deadline is unknown. Treat it as undated rather than as safe.',
};

const day = (iso) => Date.parse(`${iso}T00:00:00Z`);

/** Whole days from today to a date. Pure. Negative once it has passed. */
export function daysLeft(today, when) {
  return Math.round((day(String(when)) - day(String(today))) / 86400000);
}

/** Can this organization still create a job? Pure. [state, detail]. */
export function createEligibility(today, hasPriorJobs, daysSinceFtInference) {
  if (daysLeft(today, CUTOFF) < 0) {
    return ['create-closed',
      `the ${CUTOFF} cutoff has passed, so no organization can create a fine-tuning job`];
  }
  if (!hasPriorJobs && daysLeft(today, NEVER_FINE_TUNED) < 0) {
    return ['blocked-never-fine-tuned',
      `the job list is empty and the ${NEVER_FINE_TUNED} restriction has passed, so `
      + 'this organization cannot create a job today. Read from the listing, not '
      + 'from an attempt'];
  }
  if (daysLeft(today, NO_RECENT_INFERENCE) >= 0) {
    return ['eligible',
      `the 60 day inference rule does not apply until ${NO_RECENT_INFERENCE}; `
      + `${daysLeft(today, CUTOFF)} day(s) until the ${CUTOFF} cutoff`];
  }
  if (daysSinceFtInference === null || daysSinceFtInference === undefined) {
    return ['unknown-eligibility',
      'the inference clock could not be read, so eligibility is unknown rather than fine'];
  }
  if (daysSinceFtInference === 'none-in-window') {
    return ['blocked-no-recent-inference',
      'no fine-tuned model produced a request anywhere in the window read, so the '
      + `${WINDOW} day rule has already closed creation. Read from usage, not from `
      + 'an attempt'];
  }
  const days = Number(daysSinceFtInference);
  if (days > WINDOW) {
    return ['blocked-no-recent-inference',
      `no fine-tuned model has served a request for ${days} day(s), and the ${WINDOW} `
      + `day rule has applied since ${NO_RECENT_INFERENCE}, so new jobs are already `
      + 'being refused. Read from usage, not from an attempt'];
  }
  if (days > 45) {
    return ['eligibility-expiring',
      `the last fine-tuned request was ${days} day(s) ago, so ${WINDOW - days} day(s) `
      + `of the ${WINDOW} day window are left`];
  }
  return ['eligible',
    `the last fine-tuned request was ${days} day(s) ago and ${daysLeft(today, CUTOFF)} `
    + `day(s) remain until the ${CUTOFF} cutoff`];
}

/** The deprecation family and replacement for a base. Pure. [family, to]. */
export function familyFor(baseModel) {
  const base = String(baseModel ?? '');
  for (const [prefix, family, replacement] of FAMILIES) {
    if (base === prefix || base.startsWith(`${prefix}-`)) return [family, replacement];
  }
  return [null, null];
}

/** When this fine-tune stops serving. Pure. [date, source, detail]. */
export function servingDeadline(apiShutdownDate, family) {
  if (apiShutdownDate) {
    return [String(apiShutdownDate), 'api', 'shutdown_date read off the model object'];
  }
  if (family) {
    return [BASE_SHUTDOWN, 'published-table',
      `the model object carried no shutdown_date, so this is the ${family} row in `
      + 'the deprecation table'];
  }
  return [null, 'unknown',
    'neither the model object nor the published table has a date for this base'];
}

/** Grade one job's serving half. Pure. [state, detail]. */
export function jobVerdict(status, fineTunedModel, deadline, today) {
  if (String(status) !== 'succeeded' || !fineTunedModel) {
    return ['not-serving',
      `status ${status} with no fine-tuned model, so nothing is serving from this job`];
  }
  if (!deadline) {
    return ['no-base-date', 'no serving deadline could be established for this base'];
  }
  const left = daysLeft(today, deadline);
  if (left < 0) {
    return ['already-dead',
      `the base shut down ${-left} day(s) ago, so this fine-tune has stopped serving`];
  }
  if (left <= 90) return ['dying-soon', `${left} day(s) of inference left`];
  return ['serving', `${left} day(s) of inference left`];
}

/** The repair for one verdict. Pure. Printed, never performed. */
export function repairLines(state, replacement = null) {
  const line = REPAIRS[state];
  if (!line) return [];
  if ((state === 'dying-soon' || state === 'already-dead') && replacement) {
    return [line, `the documented replacement base is ${replacement}.`];
  }
  if (state === 'blocked-no-recent-inference') {
    return [line,
      `note the order the dates fall in: the bases die ${BASE_SHUTDOWN} and the right `
      + `to retrain closes ${CUTOFF}, so October is the deadline and January is only `
      + 'the outside edge.'];
  }
  return [line];
}

async function getJson(path, key, params = {}) {
  const url = new URL(API + path);
  for (const [k, v] of Object.entries(params)) {
    for (const one of Array.isArray(v) ? v : [v]) url.searchParams.append(k, String(one));
  }
  try {
    const r = await fetch(url, { headers: { Authorization: `Bearer ${key}` } });
    let body = {};
    try { body = await r.json(); } catch { body = {}; }
    return [r.status, body];
  } catch {
    return [null, {}];
  }
}

async function allJobs(key, pages = 20) {
  const out = [];
  let after = null;
  for (let i = 0; i < pages; i += 1) {
    const params = { limit: 100 };
    if (after) params.after = after;
    const [status, body] = await getJson('/fine_tuning/jobs', key, params);
    if (status !== 200) {
      console.log(`job listing came back ${status}, so eligibility cannot be read from it`);
      break;
    }
    const page = body.data || [];
    out.push(...page);
    if (!page.length || !body.has_more) break;
    after = page[page.length - 1].id;
    if (!after) break;
  }
  return out;
}

async function daysSinceFtInference(key, today, days = 70) {
  const start = Math.floor(Date.now() / 1000) - days * 86400;
  const [status, body] = await getJson('/organization/usage/completions', key, {
    start_time: start, bucket_width: '1d', 'group_by[]': ['model'], limit: 180,
  });
  if (status !== 200) {
    console.log(`usage report came back ${status}, so the inference clock could not be read`);
    return null;
  }
  let last = null;
  for (const bucket of body.data || []) {
    if (!bucket.start_time) continue;
    const d = new Date(bucket.start_time * 1000).toISOString().slice(0, 10);
    for (const row of bucket.results || []) {
      const model = String(row.model ?? '');
      if (model.startsWith('ft:') && (row.num_model_requests || 0) > 0) {
        last = last === null || d > last ? d : last;
      }
    }
  }
  if (last === null) return 'none-in-window';
  return -daysLeft(today, last);
}

async function main() {
  const key = process.env.OPENAI_API_KEY;
  if (!key) {
    console.error('set OPENAI_API_KEY to a project read key. This script only issues '
                  + 'GET requests and never submits a job');
    process.exitCode = 2;
    return;
  }
  const today = process.env.TODAY || new Date().toISOString().slice(0, 10);
  let findings = 0;

  const jobs = await allJobs(key);
  const admin = process.env.OPENAI_ADMIN_KEY;
  const since = admin ? await daysSinceFtInference(admin, today) : null;
  const sinceText = since === null ? 'unknown'
    : since === 'none-in-window' ? 'not in the window' : `${since} day(s) ago`;
  console.log(`create: ${jobs.length} job(s) in the list, last ft: inference ${sinceText}`);

  const [state, detail] = createEligibility(today, jobs.length > 0, since);
  console.log(`${state.padEnd(28)} ${detail}`);
  for (const line of repairLines(state)) console.log(`  repair: ${line}`);
  if (FINDINGS.has(state)) findings += 1;

  const succeeded = jobs.filter((j) => String(j.status) === 'succeeded' && j.fine_tuned_model);
  console.log(`serve: ${succeeded.length} succeeded job(s)`);
  for (const job of succeeded) {
    const ftm = job.fine_tuned_model;
    const base = job.model;
    const [family, replacement] = familyFor(base);
    const [, ftmBody] = await getJson(`/models/${ftm}`, key);
    let shutdown = ftmBody.shutdown_date;
    if (!shutdown && base) {
      const [, baseBody] = await getJson(`/models/${base}`, key);
      shutdown = baseBody.shutdown_date;
    }
    const [deadline, source] = servingDeadline(shutdown, family);
    const [jstate, jdetail] = jobVerdict(job.status, ftm, deadline, today);
    console.log(`  ${String(ftm).padEnd(40)} ${(deadline || '---').padEnd(11)} `
                + `${source.padEnd(16)} ${jstate.padEnd(13)} ${jdetail}`);
    for (const line of repairLines(jstate, replacement)) console.log(`    repair: ${line}`);
    if (FINDINGS.has(jstate)) findings += 1;
  }

  console.log(`${findings} finding(s)`);
  process.exitCode = findings ? 1 : 0;
}

if (import.meta.url === `file://${process.argv[1]}`) await main();
''',
"test_intro": "The first test is the constraint made mechanical: a blocked verdict is reached from three readable inputs &mdash; a date, a non-empty job list, and days since the last <code>ft:</code> request &mdash; and the detail says <em>read from usage, not from an attempt</em>, because the alternative way to answer this question is to submit a job. Then the ordering trap: <code>gpt-4.1-nano-2025-04-14</code> begins with the characters <code>gpt-4</code> and must not come back as <code>ft-gpt-4</code> with <code>gpt-5.6-sol</code> beside it, and a base the table does not cover comes back as nothing rather than as the nearest row. Then the evidence label, which distinguishes a <code>shutdown_date</code> the API stated from the published table's fallback. Then the two verbs held apart: a fine-tune that is still serving healthily alongside an organization that can no longer create, which is the pair of readings the note exists to produce. And finally the three shapes of the inference clock, including the one where it could not be read at all, which must come back as unknown rather than as eligible.",
"test_py_file": "test_fine_tuning_gate_audit.py",
"test_py": '''from fine_tuning_gate_audit import (BASE_SHUTDOWN, CUTOFF, WINDOW,
                                    create_eligibility, days_left, family_for,
                                    job_verdict, repair_lines,
                                    serving_deadline)

TODAY = "2026-08-31"


def test_a_blocked_verdict_comes_from_readable_state_and_not_an_attempt():
    # The whole constraint, made mechanical. Three inputs, all readable with
    # the keys this script already holds, and no job is ever submitted.
    state, detail = create_eligibility(TODAY, True, 63)
    assert state == "blocked-no-recent-inference"
    assert "63 day(s)" in detail
    assert "Read from usage, not from an attempt" in detail
    lines = repair_lines(state)
    assert any("route real traffic" in line for line in lines)
    assert any(BASE_SHUTDOWN in line and CUTOFF in line for line in lines)

    state, detail = create_eligibility(TODAY, False, 3)
    assert state == "blocked-never-fine-tuned"
    assert "Read from the listing, not from an attempt" in detail


def test_the_window_closing_is_its_own_state_with_the_days_left_in_it():
    state, detail = create_eligibility(TODAY, True, 52)
    assert state == "eligibility-expiring"
    assert "%d day(s)" % (WINDOW - 52) in detail
    assert create_eligibility(TODAY, True, 12)[0] == "eligible"
    assert create_eligibility("2027-02-01", True, 1)[0] == "create-closed"
    # Before the middle rule applied, recent inference was irrelevant.
    assert create_eligibility("2026-06-01", True, 400)[0] == "eligible"


def test_the_three_shapes_of_the_inference_clock():
    assert create_eligibility(TODAY, True, "none-in-window")[0] == \\
        "blocked-no-recent-inference"
    state, detail = create_eligibility(TODAY, True, None)
    assert state == "unknown-eligibility"
    assert "unknown rather than fine" in detail
    assert any("admin-read key" in line for line in repair_lines(state))


def test_a_base_is_matched_exactly_or_on_a_hyphen_and_never_loosely():
    # gpt-4.1-nano-2025-04-14 starts with the characters gpt-4. Filing it under
    # ft-gpt-4 would print gpt-5.6-sol with complete confidence.
    family, replacement = family_for("gpt-4.1-nano-2025-04-14")
    assert family == "ft-gpt-4.1-nano-2025-04-14"
    assert replacement == "gpt-5.6-luna"
    assert family_for("gpt-4")[0] == "ft-gpt-4"
    assert family_for("gpt-4-0613") == ("ft-gpt-4", "gpt-5.6-sol")
    assert family_for("gpt-3.5-turbo-0125")[1] == "gpt-5.6-terra"
    # A base the table does not cover is unknown, not the nearest-looking row.
    assert family_for("gpt-4o-mini-2024-07-18") == (None, None)
    assert family_for(None) == (None, None)


def test_a_date_from_the_api_is_labelled_apart_from_the_published_table():
    date, source, why = serving_deadline("2026-12-01", "ft-gpt-4")
    assert (date, source) == ("2026-12-01", "api")
    assert "read off the model object" in why

    date, source, why = serving_deadline(None, "ft-gpt-4")
    assert (date, source) == (BASE_SHUTDOWN, "published-table")
    assert "ft-gpt-4 row in the deprecation table" in why

    date, source, _ = serving_deadline(None, None)
    assert (date, source) == (None, "unknown")


def test_the_two_verbs_are_graded_apart_and_can_disagree():
    # The pair this note exists to produce: creation already refused while a
    # fine-tune is serving perfectly well for months yet.
    create, _ = create_eligibility(TODAY, True, 63)
    serve, detail = job_verdict("succeeded", "ft:gpt-4:acme::Ab12",
                                "2027-06-01", TODAY)
    assert create == "blocked-no-recent-inference"
    assert serve == "serving"
    assert "day(s) of inference left" in detail

    state, detail = job_verdict("succeeded", "ft:gpt-4:acme::Ab12",
                                BASE_SHUTDOWN, TODAY)
    assert state == "dying-soon"
    assert "53 day(s)" in detail
    lines = repair_lines(state, "gpt-5.6-sol")
    assert any("gpt-5.6-sol" in line for line in lines)
    assert any("structured outputs" in line for line in lines)


def test_a_job_with_nothing_serving_and_a_base_with_no_date():
    assert job_verdict("failed", None, BASE_SHUTDOWN, TODAY)[0] == "not-serving"
    assert job_verdict("succeeded", None, BASE_SHUTDOWN, TODAY)[0] == "not-serving"
    state, _ = job_verdict("succeeded", "ft:x:acme::Zz99", None, TODAY)
    assert state == "no-base-date"
    assert any("undated rather than as safe" in line
               for line in repair_lines(state))
    assert job_verdict("succeeded", "ft:x:acme::Zz99", "2026-08-01",
                       TODAY)[0] == "already-dead"
    assert days_left(TODAY, BASE_SHUTDOWN) == 53
''',
"test_js_file": "fine-tuning-gate-audit.test.mjs",
"test_js": '''import { test } from 'node:test';
import assert from 'node:assert/strict';
import { BASE_SHUTDOWN, CUTOFF, WINDOW, createEligibility, daysLeft, familyFor,
         jobVerdict, repairLines, servingDeadline } from './fine-tuning-gate-audit.mjs';

const TODAY = '2026-08-31';

test('a blocked verdict comes from readable state and not an attempt', () => {
  let [state, detail] = createEligibility(TODAY, true, 63);
  assert.equal(state, 'blocked-no-recent-inference');
  assert.ok(detail.includes('63 day(s)'));
  assert.ok(detail.includes('Read from usage, not from an attempt'));
  const lines = repairLines(state);
  assert.ok(lines.some((l) => l.includes('route real traffic')));
  assert.ok(lines.some((l) => l.includes(BASE_SHUTDOWN) && l.includes(CUTOFF)));

  [state, detail] = createEligibility(TODAY, false, 3);
  assert.equal(state, 'blocked-never-fine-tuned');
  assert.ok(detail.includes('Read from the listing, not from an attempt'));
});

test('the window closing is its own state with the days left in it', () => {
  const [state, detail] = createEligibility(TODAY, true, 52);
  assert.equal(state, 'eligibility-expiring');
  assert.ok(detail.includes(`${WINDOW - 52} day(s)`));
  assert.equal(createEligibility(TODAY, true, 12)[0], 'eligible');
  assert.equal(createEligibility('2027-02-01', true, 1)[0], 'create-closed');
  assert.equal(createEligibility('2026-06-01', true, 400)[0], 'eligible');
});

test('the three shapes of the inference clock', () => {
  assert.equal(createEligibility(TODAY, true, 'none-in-window')[0],
               'blocked-no-recent-inference');
  const [state, detail] = createEligibility(TODAY, true, null);
  assert.equal(state, 'unknown-eligibility');
  assert.ok(detail.includes('unknown rather than fine'));
  assert.ok(repairLines(state).some((l) => l.includes('admin-read key')));
});

test('a base is matched exactly or on a hyphen and never loosely', () => {
  const [family, replacement] = familyFor('gpt-4.1-nano-2025-04-14');
  assert.equal(family, 'ft-gpt-4.1-nano-2025-04-14');
  assert.equal(replacement, 'gpt-5.6-luna');
  assert.equal(familyFor('gpt-4')[0], 'ft-gpt-4');
  assert.deepEqual(familyFor('gpt-4-0613'), ['ft-gpt-4', 'gpt-5.6-sol']);
  assert.equal(familyFor('gpt-3.5-turbo-0125')[1], 'gpt-5.6-terra');
  assert.deepEqual(familyFor('gpt-4o-mini-2024-07-18'), [null, null]);
  assert.deepEqual(familyFor(null), [null, null]);
});

test('a date from the api is labelled apart from the published table', () => {
  let [date, source, why] = servingDeadline('2026-12-01', 'ft-gpt-4');
  assert.equal(date, '2026-12-01');
  assert.equal(source, 'api');
  assert.ok(why.includes('read off the model object'));

  [date, source, why] = servingDeadline(null, 'ft-gpt-4');
  assert.equal(date, BASE_SHUTDOWN);
  assert.equal(source, 'published-table');
  assert.ok(why.includes('ft-gpt-4 row in the deprecation table'));

  [date, source] = servingDeadline(null, null);
  assert.equal(date, null);
  assert.equal(source, 'unknown');
});

test('the two verbs are graded apart and can disagree', () => {
  const [create] = createEligibility(TODAY, true, 63);
  let [serve, detail] = jobVerdict('succeeded', 'ft:gpt-4:acme::Ab12', '2027-06-01', TODAY);
  assert.equal(create, 'blocked-no-recent-inference');
  assert.equal(serve, 'serving');
  assert.ok(detail.includes('day(s) of inference left'));

  [serve, detail] = jobVerdict('succeeded', 'ft:gpt-4:acme::Ab12', BASE_SHUTDOWN, TODAY);
  assert.equal(serve, 'dying-soon');
  assert.ok(detail.includes('53 day(s)'));
  const lines = repairLines(serve, 'gpt-5.6-sol');
  assert.ok(lines.some((l) => l.includes('gpt-5.6-sol')));
  assert.ok(lines.some((l) => l.includes('structured outputs')));
});

test('a job with nothing serving and a base with no date', () => {
  assert.equal(jobVerdict('failed', null, BASE_SHUTDOWN, TODAY)[0], 'not-serving');
  assert.equal(jobVerdict('succeeded', null, BASE_SHUTDOWN, TODAY)[0], 'not-serving');
  const [state] = jobVerdict('succeeded', 'ft:x:acme::Zz99', null, TODAY);
  assert.equal(state, 'no-base-date');
  assert.ok(repairLines(state).some((l) => l.includes('undated rather than as safe')));
  assert.equal(jobVerdict('succeeded', 'ft:x:acme::Zz99', '2026-08-01', TODAY)[0],
               'already-dead');
  assert.equal(daysLeft(TODAY, BASE_SHUTDOWN), 53);
});
''',
"faq": [
 ("How is this different from the note about a fine-tuned model nobody calls?",
  "Same number, opposite meaning. That note reads zero traffic on a trained model as waste: you paid for training and never routed to it, so either route or retire. Here zero ft: traffic is an eligibility clock. Since 2 July 2026 an organization that has not run inference on a fine-tuned model in the past 60 days can no longer create a job, so the traffic that note tells you to consider stopping is the thing keeping your right to retrain alive. Read both before you retire anything."),
 ("Why not just try creating a job and see whether it is refused?",
  "Because that is a write, it costs money, and it trains a model nobody asked for. Every script in this section is read-only, and a note about an endpoint that stopped accepting work has no business submitting work to find out. The eligibility function takes three readable inputs — today's date, whether the job list is non-empty, and days since the last ft: request — and there is a test asserting that a blocked verdict is reached from those alone."),
 ("Which deadline should I actually plan around?",
  "October, not January. Every fine-tunable base in the deprecation table shuts down on 23 October 2026, and inference on a fine-tune dies with its base, so your models stop serving then. The 6 January 2027 date is when creating new jobs ends for everyone — the outside edge of the window in which you can react, not the schedule. An organization that notices the first date in October has roughly ten weeks to retrain everything worth keeping, once."),
 ("The script says published-table rather than api for my model. Does that matter?",
  "It tells you how strong the claim is. Where GET /v1/models/{id} returns a shutdown_date, the API stated it and that is authoritative. Where it does not, the only source is the deprecation table's family row, which is a document and documents lag. Both produce the same date today; only one of them will update itself if the schedule changes. Labelling them separately is the same discipline the rest of this section applies to anything it inferred rather than measured."),
 ("My base model is not in any of the six families. What then?",
  "The script reports the family as unknown and the serving deadline as no-base-date, rather than filing it under the nearest-looking row. Matching is exact or hyphen-delimited on purpose: gpt-4.1-nano-2025-04-14 begins with the characters gpt-4, and a loose prefix match would print the wrong replacement with total confidence. An undated base is not a safe base — it means neither source has a date for it, and you should establish one before assuming it outlives October."),
],
"related": [REL_FT_UNUSED, REL_PAST_DATE, REL_EXPORT],
"citations": [CITE_DEPRECATIONS, CITE_FINETUNE, CITE_MODEL_OBJ, CITE_USAGE],
},
]
