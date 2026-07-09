# Facebook autoposting on AWS — full architecture & blog plan

> A cost-optimized, purely-AWS, serverless system for scheduled Facebook posting,
> with topic guardrails, a Google Drive knowledge base, and a real-time reply bot.
>
> Companion blog content for **allanninal.dev/build**.

---

## Table of contents

1. [Project goals & constraints](#1-project-goals--constraints)
2. [Engineering architecture (technical view)](#2-engineering-architecture-technical-view)
   - 2.1 [Master architecture](#21-master-architecture)
   - 2.2 [Build & deploy subsystem](#22-build--deploy-subsystem)
   - 2.3 [Posting pipeline with 5-stage guardrails](#23-posting-pipeline-with-5-stage-guardrails)
   - 2.4 [Knowledge base sync from Google Drive](#24-knowledge-base-sync-from-google-drive)
   - 2.5 [Real-time reply pipeline (RAG)](#25-real-time-reply-pipeline-rag)
   - 2.6 [Cost & free-tier breakdown](#26-cost--free-tier-breakdown)
3. [Blog-ready version (plain language)](#3-blog-ready-version-plain-language)
   - 3.1 [The whole system on one page](#31-the-whole-system-on-one-page)
   - 3.2 [How code becomes a working system](#32-how-code-becomes-a-working-system)
   - 3.3 [How a post actually goes out](#33-how-a-post-actually-goes-out)
   - 3.4 [How the Drive folder powers everything](#34-how-the-drive-folder-powers-everything)
   - 3.5 [How replies work without making things up](#35-how-replies-work-without-making-things-up)
   - 3.6 [What this all costs](#36-what-this-all-costs)
4. [Subdomain & blog setup decisions](#4-subdomain--blog-setup-decisions)
5. [Recommended build order](#5-recommended-build-order)
6. [Open questions to resolve](#6-open-questions-to-resolve)

---

## 1. Project goals & constraints

**The brief.** Build an autoposting system to a Facebook page using purely AWS
services, with the source code living in GitHub. Optimize for cost — no hidden
fees, no always-on resources, nothing that quietly accrues charges.

**Extended scope after iteration.**

- Topic/niche guardrails so a faith post never lands on a forex page (and vice versa).
- A Google Drive folder where the client edits FAQs, pricing, promos, and brand-voice rules.
- A real-time reply system that uses that knowledge base, grounded so the bot can't make things up.

**Hard rules that shaped every decision.**

- Stay inside the AWS perpetual free tier wherever possible.
- No NAT Gateway. No API Gateway (use Lambda Function URLs instead).
- No always-on compute. No infinite log retention.
- No long-lived credentials in GitHub (use OIDC).
- Drive must remain the client's authoring surface — they don't learn a new tool.
- Replies must cite a knowledge-base chunk or refuse to answer.

**Realistic monthly cost target.** $2–$5/month for a single page with steady posting and replies.

---

## 2. Engineering architecture (technical view)

### 2.1 Master architecture

The complete system on one canvas: three external surfaces (GitHub, Google
Drive, Facebook Graph API), four AWS subsystems, and three cross-cutting
concerns (logging, alarms, audit).

**External surfaces**

- GitHub repository — code and SAM template
- Google Drive — client-edited knowledge base folder
- Facebook Graph API — posts, DMs, comments

**Subsystem 1 — build & deploy**

`GitHub Actions → OIDC → AWS SAM → CloudFormation stack`. No static keys, all
infra reproducible from git.

**Subsystem 2 — scheduled posting with guardrails**

```
EventBridge (cron) → Publisher Lambda → DynamoDB (post queue)
                                      → Secrets Manager (Page tokens)
                                      → Graph API
```

**Subsystem 3 — knowledge base sync**

```
Drive webhook → Sync Lambda → S3 raw KB (versioned) → Chunker Lambda
                                                    → S3 Vectors index
```

**Subsystem 4 — real-time replies**

```
FB webhook → Lambda Function URL (HMAC verify) → SQS → Reply Lambda (RAG + judge)
                                                     → Graph API
```

**Cross-cutting**

- CloudWatch Logs with 7-day retention
- DLQ + SNS alarms for failures and billing
- Audit DynamoDB table — every action logged

---

### 2.2 Build & deploy subsystem

**Flow.** `git push origin main` → GitHub Actions runs lint & tests →
requests OIDC token → AWS IAM verifies (trusts only this repo, this branch) →
issues temporary credentials (~1hr lifetime) → `sam build && sam deploy` →
CloudFormation applies the change set.

**Why OIDC matters.** Without it, you'd store a long-lived AWS access key in
GitHub Secrets — the most common cause of compromised AWS accounts. With OIDC,
GitHub Actions presents a short-lived JWT, AWS verifies it, and hands back
credentials that expire in about an hour. Nothing to leak, nothing to rotate.

**Trust boundary specifics.**

- IAM OIDC provider: `token.actions.githubusercontent.com`
- Trust policy condition: `repo:<owner>/<repo>:ref:refs/heads/main`
- Audience: `sts.amazonaws.com`
- Action: `sts:AssumeRoleWithWebIdentity`

**Rollback strategy.** `git revert HEAD && git push` — the same pipeline rolls
infra back to the previous state via CloudFormation.

**Resulting infrastructure.** Single CloudFormation stack containing: Lambdas,
EventBridge schedules, DynamoDB tables, S3 buckets, Secrets Manager secrets,
IAM roles. Single source of truth in `template.yaml`.

---

### 2.3 Posting pipeline with 5-stage guardrails

**Trigger.** EventBridge Scheduler fires on a cron expression
(`cron(0 9,12,18 * * ? *)`). Lambda queries DynamoDB for posts where
`status=queued AND scheduled_at <= now()`.

**The five stages, run in order — cheap gates first.**

**Stage 1 — schema gate (free, in-Lambda).**
- Required fields present
- Body length within limits
- `page_id` matches `pillar` field — a faith post tagged with the DailyScalper page is rejected here, not later

**Stage 2 — keyword gates (free, in-Lambda).**
- **Allowlist:** required hashtags present (e.g. SFC posts need 5 specific tags)
- **Denylist:** page-specific blocked terms (e.g. "XAUUSD" on SFC = block)

**Stage 3 — semantic similarity (Bedrock Titan Embed).**
- Embed the post once via Bedrock Titan Text Embeddings v2 (1024 dimensions)
- Compute cosine similarity vs the page's pre-computed niche centroid
- Cost: ~$0.00002 per post

**Stage 4 — LLM judge (Bedrock Haiku, only on borderline).**
- Fires only when similarity is between 0.55 and 0.75
- Per-page system prompt with brand rules
- Returns structured `{on_topic, confidence, reason}`
- Hits ~5% of posts in steady state

**Stage 5 — verdict routing.**

| Verdict | Destination | Status |
|---------|------------|--------|
| PASS    | Graph API `/{page-id}/feed` | `published` |
| REVIEW  | SNS email with approve link | `pending_review` |
| BLOCK   | Audit table only | `blocked` |

**Per-page policy config.** Each page has a JSON file in S3 the Lambda loads
and caches. Tuning rules doesn't require redeploying:

```json
{
  "pillar": "faith",
  "required_hashtags": ["#FaithPoetry", "#CatholicLife",
                        "#DevLifeFaith", "#SanctifyTheOrdinary", "#FreeVerse"],
  "denylist": ["XAUUSD", "RoboForex", "FTMO", "pip", "leverage"],
  "language_hints": ["bisaya", "cebuano", "tagalog", "english"],
  "centroid_key": "centroids/sfc-faith.json",
  "similarity_threshold_pass": 0.75,
  "similarity_threshold_review": 0.55,
  "llm_judge": true
}
```

**Token refresh worker.** A separate weekly Lambda
(`cron(0 3 ? * SUN *)`) exchanges the Page Access Token before its 60-day
expiry and overwrites the same Secrets Manager secret.

---

### 2.4 Knowledge base sync from Google Drive

**Client surface.** A shared Drive folder per Facebook page, containing four Google Docs:

```
Page knowledge base/
├─ 01_faqs.gdoc        — Q&A pairs
├─ 02_pricing.gdoc     — service tiers, rates, payment methods
├─ 03_promos.gdoc      — active campaigns with start/end dates
└─ 04_do_not_say.gdoc  — refusals, off-limits topics, escalation rules
```

**Permissions model.**

- **Client team** — Editor on folder, sees only their KB
- **You** — Owner of folder, can revoke anytime
- **AWS service account** — Viewer (read-only), cannot edit or delete

**Change detection — push, not poll.** Drive `files.watch` push notification
calls a Lambda Function URL (free, near-instant). The watch channel renews
every 7 days via an EventBridge rule.

**Sync pipeline with safety layer.**

1. **Sync Lambda** — exports Google Docs to Markdown, diffs against last
   version, skips if no real change.
2. **Validation gate** — Markdown parses cleanly, pricing format intact, no
   empty required sections. Validators are page-specific.
3. **S3 raw bucket** — `kb/{page_id}/{filename}.md` with versioning enabled.
   Every save is a new version, one-click rollback on bad change.

**Indexing — only fires on change.** S3 PutObject event triggers:

1. **Chunker Lambda** — splits Markdown by heading, ~500 tokens per chunk with 50-token overlap.
2. **Bedrock Titan Embed** — one vector per chunk.
3. **S3 Vectors index** — one bucket per page (~90% cheaper than OpenSearch Serverless for this scale).

**Client feedback loop — written back to the doc.**

- **Sync OK** → Drive comment: "Live as of 14:23"
- **Sync failed** → Drive comment with the specific error; old version stays live
- **Channel renewal** → EventBridge weekly, Drive expires watches after 7 days

**Why Drive isn't on the hot path.** Replies read from S3, not Drive directly.
Drive outage doesn't break the live page. Drive API quotas can never rate-limit
your customer-facing replies.

---

### 2.5 Real-time reply pipeline (RAG)

**Inbound — webhook receiver.**

1. FB user sends a DM or comments on the page
2. Meta webhook → Lambda Function URL
3. Lambda verifies HMAC signature, returns 200 immediately

**Decoupling — buffer the work.** SQS queue with DLQ. Webhook returns fast
even when Bedrock is slow; failed messages go to DLQ for inspection.

**RAG retrieval flow.**

1. Reply Lambda receives message from SQS
2. Looks up page config (which index, which thresholds)
3. Embeds user's question via Bedrock Titan
4. Queries S3 Vectors for top 3-5 most relevant chunks

**Confidence gate.** Top-1 similarity score:
- ≥0.6 → answer
- <0.6 → escalate to you via SNS, log to `unanswered` DynamoDB table (becomes the next FAQ entry)

**Grounded generation.** Bedrock Haiku with retrieved chunks as context.
System prompt enforces:

- Answer ONLY from context
- Refuse if not covered
- Per-page voice (tone, language, brand rules from `04_do_not_say.gdoc`)
- Returns `{reply_text, cited_chunks}`

**Reply guardrails — same rules as posts.**

- **Citation required** — no cited chunk = no send (prevents hallucination)
- **Denylist applies** — same blocked terms as posts (no financial advice from SFC, no faith content from DailyScalper)

**Outbound.** Graph API: comment reply or DM. Logged to audit table with
cited chunk IDs so any answer can be traced back to its source.

**Optional v1 mode: draft-only.** Replies go to your inbox instead of being
sent. You review in batches. Eliminates risk of theological or financial
mishaps until you trust the system. Flip to auto-send later for tightly-bounded
categories first (like "what are the pricing tiers").

---

### 2.6 Cost & free-tier breakdown

**Always free at this scale**

| Service | Free tier | Notes |
|---------|-----------|-------|
| Lambda | 1M requests + 400K GB-s/month forever | ARM (Graviton) for 34% extra discount |
| EventBridge Scheduler | 14M invocations/month | Posts ~30/day = trivial |
| DynamoDB on-demand | 25 GB + 25 RCU/WCU forever | Post queue + audit table |
| SQS | 1M requests/month | DLQ traffic trivial |
| SNS | 1K email notifs/month | Alarms negligible |
| Lambda Function URL | Free | Used instead of API Gateway for webhooks |

**Small fixed costs**

- **Secrets Manager** — $0.40/secret/month × 3 secrets (FB token, Drive key, app secret) = ~$1.20/month
- **S3 storage + Vectors** — text KB easily under 1 GB; vector indexes small per page = ~$0.10–$0.50/month

**Variable with engagement**

- **Bedrock Titan Embed** — ~$0.00002 per embedding (posts + replies + KB chunks) = ~$0.10–$0.30/month
- **Bedrock Haiku** — ~$0.0007 per reply (1K replies/month ≈ $0.70); plus rare guardrail judge calls = $0.50–$2.00/month

**Hidden fees deliberately avoided**

- **No NAT Gateway** — would be $33/month + $0.045/GB. Lambda has no VPC; it reaches AWS services via internal network and the Graph API via public HTTPS for free.
- **No API Gateway** — Function URLs instead. Saves $3.50 per million requests.
- **No infinite logs** — `RetentionInDays: 7` set on every log group. CloudWatch can't bloat.
- **No provisioned concurrency** — Lambda cold starts are fine for this workload.
- **No CloudFront, no VPC endpoints, no ECR** — none needed for the architecture.

**Realistic monthly total: $2–$5/month** for a single page with steady posting and replies.

**Final safety net.** AWS Budget alarm at $10/month with SNS to your phone.

---

## 3. Blog-ready version (plain language)

Friendlier framing, no jargon walls, no code. For **allanninal.dev/build**.
Each section is self-contained — can be one long post or split into a six-part series.

### 3.1 The whole system on one page

You run a Facebook page. You want it to post on a schedule, stay on-topic,
answer questions correctly, and not surprise you with a huge cloud bill.
Here's how to build that.

**What you and your client touch (the outside)**

- **Your code on GitHub** — where the project lives
- **Google Drive folder** — where the client edits content
- **The Facebook page** — what the world sees

**What runs quietly in the cloud (the inside)**

- **The posting robot** — wakes up on schedule, picks the next post, checks it, posts it
- **The reply robot** — wakes up when someone messages, looks up the answer, replies
- **The shared brain** — a copy of the Drive folder, kept in sync, that both robots read from

**In plain words.** You write the rules in code. Your client writes the
content in Drive. Two small robots — one for posting, one for replying — do
the work in the background. They both share the same brain so they never
contradict each other. Total cost runs a few dollars a month, not a few hundred.

---

### 3.2 How code becomes a working system

**The flow.** You save your work → push to GitHub → a helper checks it (runs
your tests, stops if anything fails) → it opens the cloud door (with a
short-lived key that expires in an hour) → the cloud updates itself.

**In plain words.**

Old way: copy files to a server, restart things, hope nothing breaks.

New way: push to GitHub, walk away. The cloud handles the rest.

If something breaks, you undo your change and push again. The cloud rolls
back too. No passwords stored anywhere — the helper gets a fresh key each
time and throws it away. If the key ever leaks, it's already expired before
anyone could use it.

---

### 3.3 How a post actually goes out

A post passes through five quick checks between "it's time" and "post is live":

1. **A timer goes off** — "It's 9am, time to check if there's a post due"
2. **Check 1 — Is the post even valid?** Has text, has the right page, isn't empty
3. **Check 2 — Right hashtags?** Faith posts need faith tags
4. **Check 3 — Forbidden words?** No forex talk on a faith page
5. **Check 4 — Does it sound like this page?** A small AI compares it to past on-topic posts
6. **Check 5 — When in doubt, ask a smarter AI** Only used when Check 4 is unsure

**Three possible endings**

- **Looks good** → posts to Facebook, done
- **Not sure** → emails you to approve, you decide
- **Off-topic** → blocked, never posts, logged for review

**In plain words.** Cheap checks first, expensive checks only when needed.
A typo or bad hashtag is caught for free. The AI only weighs in when something
looks borderline. Most posts pass all five checks in well under a second. The
point isn't paranoia — it's making sure that when a faith post accidentally
gets tagged with a forex page (because someone got distracted while drafting),
the system catches it before the world sees it. You sleep better.

---

### 3.4 How the Drive folder powers everything

**The client's folder — four simple docs**

- **FAQs** — questions customers always ask
- **Pricing** — service tiers, what costs what
- **Promos** — current campaigns, when they end
- **Don't-say list** — topics to avoid, things to escalate to a human

**The flow.**

1. Drive tells the cloud the moment something changes (no checking every minute)
2. A safety check runs first — does the doc still parse? Are required sections filled in?
3. If something looks broken, the **old version stays live**
4. If it's good, it's saved (every save is kept — one-click rollback) and re-organized for fast lookup
5. Client gets a comment back on the doc — "Live as of 14:23" or "Pricing table is missing prices"

**In plain words.** Your client opens Google Docs. They edit. They save. A
few seconds later they get a comment confirming the change is live. If they
break something, nothing breaks — the old version keeps working until they
fix it. No dashboard. No "deploy" button. No tickets to file. They already
know how to use Google Docs. That's the whole interface.

---

### 3.5 How replies work without making things up

**The flow.**

1. Someone messages the page (DM, comment, anything)
2. Facebook tells the cloud right away — the cloud says "got it" in milliseconds, then takes its time to think
3. **Search the brain for relevant facts** — pull the most relevant lines from the client's docs (only — never anywhere else)
4. **Confidence check** — did we find a good match? If not, escalate to a human, don't guess
5. **AI writes the reply using ONLY those facts** — like a new employee with the FAQ binder open. If the answer isn't in the binder, they say "let me check with my manager"
6. **One last guardrail** — same forbidden-words check as posts
7. **Reply goes out** on Facebook, logged with the exact source it used

**In plain words.** The AI is forced to answer from the client's docs. It
can't invent prices or promises. AI reply bots have a bad reputation because
they confidently make things up — quote a price that doesn't exist, promise a
feature that's not real, give medical or financial advice they shouldn't. The
fix is simple: the AI is only allowed to answer using the client's own docs.
If the answer isn't in the docs, the bot says "let me get back to you" and
tags you. Boring, safe, correct.

---

### 3.6 What this all costs

**Free at this scale**

- The robots — free up to a million runs a month
- The timer — 14 million free wakeups a month
- The post queue — 25 GB of space always free

**Costs cents to a dollar each month**

- Password vault — stores your Facebook keys, about $1.20/month total
- File storage — holds the knowledge base, cents per month

**Grows with how busy the page is**

- The AI for replies — about one-tenth of a cent per reply. A thousand replies a month is around a dollar.

**Three traps you're avoiding**

- **No always-on server** — that alone would be $30+/month
- **No fancy gateway** — webhooks go straight to the robot
- **No infinite logs** — 7-day retention, can't pile up

**All-in: about $2 to $5 per month** for one Facebook page with steady posting
and replies. A budget alarm at $10 catches anything weird before it grows.

**In plain words.** A coffee a month, not a Netflix subscription. The bill
stays small because the system sleeps when there's nothing to do.

---

## 4. Subdomain & blog setup decisions

**Subdomain chosen: `allanninal.dev/build`**

Reasons it beat the alternatives:

- "Build" maps to identity better than "engineering" — covers DailyScalper, EruditionTx, this autoposting system, the SFC chatbot, the Threads autoposter, ministry-tech work, etc.
- Future-proofs the subdomain. Doesn't lock the writing into a single domain.
- Pairs cleanly with potential sibling subdomains: `faith.allanninal.dev` for SFC content, `forex.allanninal.dev` for trading content.
- Distinctive — stands out vs the generic `engineering.*` / `blog.*` / `dev.*` that every developer uses.

**URL pattern decision (to lock in early).**

Recommend: `allanninal.dev/build/<post-slug>` (flat, no `/posts/` prefix).
Cleaner, matches modern dev blogs. Reserve `/series/` for multi-part series later.

**Reserved neighbor subdomains (redirect to build).**

- `engineering.allanninal.dev` → `allanninal.dev/build`
- `blog.allanninal.dev` → `allanninal.dev/build`
- `www.allanninal.dev/build` → `allanninal.dev/build`

**OpenGraph image.** Auto-generate per post with: name, post title, build
subdomain. Cards with images get 2-3x click-through. Worth doing on day one.

**Series vs single post for this autoposting writeup.**

Six diagrams = six posts is the more strategic move:

- More SEO surface
- More shareables for Threads / LinkedIn / Facebook
- Six weeks of consistent content from one project
- Reuses well in DailyScalper / SFC / tech audiences

If you want one long reference link for clients, keep it whole.

---

## 5. Recommended build order

A sane sequence so each piece can be tested before the next layer goes on top.

1. **Build & deploy first.** Get a "hello world" Lambda deploying via GitHub Actions and OIDC. Once GitHub → AWS deploys cleanly, everything else is just code.
2. **Posting (no guardrails) second.** Get a Lambda posting to one Facebook page on a schedule. Prove the Graph API integration end-to-end. Token refresh worker in place from day one.
3. **Add stages 1-2 of guardrails.** Schema gate + keyword gates. Free, immediately useful. No Bedrock yet.
4. **KB sync from Drive.** Get one client's folder syncing to S3 with the validation gate and Drive comment write-back. This is what you'd demo to a client.
5. **Replies in draft mode.** Replies go to your inbox, not the page. Watch them for a week.
6. **Add Bedrock guardrails.** Stages 3-4 (semantic similarity + LLM judge), citation requirement on replies. Tune thresholds against real traffic.
7. **Flip replies to auto-send** — start with tightly-bounded categories (pricing) before broader ones (general FAQ).

---

## 6. Open questions to resolve

These decisions weren't pinned during the architecture discussion. Worth
deciding before writing the SAM template:

1. **Single SAM stack or split stacks?** Posting + KB + replies in one stack is simpler; splitting means each subsystem can deploy independently. For v1, single stack is right.
2. **Region.** Pick one with Bedrock availability and lowest latency from the Philippines. `ap-southeast-1` (Singapore) is the obvious choice — Bedrock is available there now.
3. **Per-client AWS account or shared account with isolation?** Shared with strict IAM boundaries is cheaper and simpler for early clients. Move to per-client accounts when there's a paying enterprise client who demands it.
4. **Do client edits to KB go live immediately, or require your approval first?** Diagram shows auto-publish with rollback. For less technical clients, add a `pending/` prefix in S3 and an SNS approval step.
5. **Reply auto-send vs draft mode by default?** Recommend draft mode for v1 on every new client. Earn trust before flipping the switch.
6. **Multi-page support from day one?** Schema in DynamoDB should be `pk = page_id` from the start. Adding multi-page later is painful; supporting it from day one costs almost nothing.
7. **OpenGraph card generation.** Build with the blog or defer? Worth doing with the blog — it's a one-time setup that pays off forever.
8. **Series titles for the blog** — six diagrams, six posts. Drafting these is a 30-minute task for the next session.

---

*Document compiled for handoff to Claude Code. Architecture decisions, plain-language framing, and operational details for a cost-optimized AWS-only Facebook autoposting system.*
