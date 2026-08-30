# OpenAI and Anthropic integration failures a read-only script can detect

**162 distinct problems** across the OpenAI and Anthropic APIs, every one of them detectable
by a script holding only a **read-only project key** or an **admin-read organization key**.
Grouped into nine categories.

Each entry carries eight fields: `slug`, `title`, `symptom`, `mechanism`, `detect` (the exact
read-only call and the field to inspect), `repair` (printed, never executed), `category`,
`sources`.

**Scope rule applied throughout:** a problem is included only if a script holding a read-only
or admin-read key can *detect* it through the provider's own API. Faults that live only in
application source — a badly worded prompt, a retry loop with no jitter, a proxy that buffers
a stream — appear only where they leave an API-visible symptom, and the detection described is
that symptom, not the code.

Research date: 2026-08-30.

**Credentials assumed.** OpenAI: a project API key set to **Read Only** (or a Restricted key
carrying the `*.read` scopes), plus an **organization admin key** (`sk-admin-`) for everything
under `/v1/organization/*`. Both are needed — the Usage, Costs, Projects, API-keys, rate-limit
and audit-log endpoints reject project keys outright. Anthropic: a **workspace API key** for
the data plane (`/v1/models`, `/v1/messages/batches`, `/v1/files`, `/v1/messages/count_tokens`)
plus an **Admin API key** (`sk-ant-admin...`) for everything under `/v1/organizations/*` and
`/v1/compliance/*`. Admin keys can be provisioned read-only, and workspace-scoped keys are
rejected by every Admin endpoint.

**Docs moved during this research.** `platform.openai.com/docs/*` now 301-redirects to
`developers.openai.com/api/docs/*`, and `docs.claude.com/en/*` now 301-redirects to
`platform.claude.com/docs/en/*`. Sources below use the current hosts.

---

## Scope and known blind spots

These matter more than the count. Nine things the two APIs genuinely cannot tell a read-only
script, and the compromises made because of them.

1. **Neither provider exposes a request log.** There is no endpoint on either API that lists
   individual inference requests with their status codes, latencies or error bodies. The
   dashboards show request-level detail; the APIs do not. Every error-rate finding below is
   therefore inferred from one of three weaker signals — a hole or cliff in the aggregate
   usage buckets, a bucket with `num_model_requests > 0` but `output_tokens == 0` (calls that
   400'd before generation), or a live probe re-issued from the script itself. You cannot ask
   either API "which of my requests failed yesterday, and why".

2. **Prompts, completions, tool schemas and client configuration are never readable.** Nothing
   in either API returns what you actually sent. Prompt wording, JSON-schema shape, tool
   descriptions, `strict` flags, retry policy, client timeouts, streaming handling and
   connection pooling live only in your source tree. This is why **Structured output and
   tools** is the thinnest category here: most of its failures are visible only as a shape in
   aggregate token counts, and the honest ones are listed while the unverifiable ones are not.

3. **Anthropic's messages usage report has no request-count field.** `GET
   /v1/organizations/usage_report/messages` returns token sums per bucket and nothing else, so
   every "per request" ratio on the Anthropic side must be derived from tokens rather than call
   volume. OpenAI's usage endpoints do carry `num_model_requests`, which is why several
   detections that are precise on OpenAI are approximate on Anthropic.

4. **Rate-limit headroom exists only on response headers, never on a GET you can schedule.**
   `x-ratelimit-remaining-tokens` / `anthropic-ratelimit-input-tokens-remaining` and their
   siblings come back attached to responses. A read-only audit sees them only by making a cheap
   real call — `GET /v1/models` works — and the numbers it reads are the ones for *that call's*
   scope at *that* moment, not a stored quota it can query later.

5. **Geography and verification faults only reproduce from the production egress path.** A 403
   `unsupported_country_region_territory`, an org-verification block on streaming, and a
   corporate TLS-interception failure all depend on where the request leaves from. Run the
   script inside the same VPC, region or edge runtime as the application, or these entries are
   undetectable.

6. **OpenAI's model object does not carry the context window or max output tokens.** Anthropic's
   `GET /v1/models/<built-in function id>` returns `max_input_tokens` and `max_output_tokens`, so window checks
   there are exact. OpenAI's does not, so any OpenAI context-window check has to compare against
   a hardcoded table that goes stale. Conversely OpenAI's model object *does* now carry
   `shutdown_date`, which makes deprecation drift a one-call check — Anthropic has no equivalent
   field and its retirement dates must come from the published deprecation table.

7. **Retention windows bound every historical finding.** OpenAI batch output and error files
   expire after 30 days; Anthropic batch results after 29 days; Claude Code analytics arrive
   with up to an hour's delay and only in daily buckets; cost reports lag real time. Anything
   that has already aged out cannot be recovered by any read call, so a finding of "no evidence"
   is never proof of "no problem" outside the window.

8. **There is no list endpoint for several OpenAI resources.** `/v1/responses` and
   `/v1/conversations` cannot be enumerated — stored responses and conversations are reachable
   only by an id you already hold. OpenAI's webhook endpoints have no public list call either
   (unlike Stripe's `GET /v1/webhook_endpoints`), so webhook misconfiguration is dashboard-only
   and is deliberately absent from this reference.

9. **Anthropic has no read-only tier for the data plane.** A workspace API key is all-or-nothing:
   the same credential that reads `GET /v1/models` can send a `POST /v1/messages`. Only the
   Admin API distinguishes read from write. Where an entry below needs a workspace key, the
   script is trusted not to write rather than prevented from writing — and the Files API is the
   mirror image, readable *only* with a workspace key because an Admin key cannot reach it at
   all.

---

## Table of contents

| # | Category | Count |
| --- | --- | --- |
| 1 | [Cost and usage](#cost-and-usage) | 24 |
| 2 | [Rate limits and retries](#rate-limits-and-retries) | 14 |
| 3 | [Models and deprecations](#models-and-deprecations) | 21 |
| 4 | [Structured output and tools](#structured-output-and-tools) | 7 |
| 5 | [Batch and async](#batch-and-async) | 18 |
| 6 | [Keys, projects and access](#keys-projects-and-access) | 28 |
| 7 | [Files and vector stores](#files-and-vector-stores) | 12 |
| 8 | [Prompt caching](#prompt-caching) | 13 |
| 9 | [Errors and reliability](#errors-and-reliability) | 25 |
| | **Total** | **162** |

### Cost and usage

1. [`reasoning-tokens-billed-invisibly`](#reasoning-tokens-billed-invisibly) — Reasoning tokens are billed as output but never returned
2. [`fast-mode-silently-downgraded`](#fast-mode-silently-downgraded) — Fast mode requests get served as default and lose the speedup
3. [`streaming-usage-lost`](#streaming-usage-lost) — Streamed responses report no token usage, breaking cost tracking
4. [`spend-spike-week-over-week`](#spend-spike-week-over-week) — Org spend jumped week over week with no release to explain it
5. [`one-model-or-project-dominates-cost`](#one-model-or-project-dominates-cost) — One line item or project is eating most of the org's spend
6. [`frontier-model-on-trivial-workload`](#frontier-model-on-trivial-workload) — A frontier model is doing work a mini model would do fine
7. [`no-organization-spend-limit`](#no-organization-spend-limit) — No hard spend limit is set, so the bill has no ceiling
8. [`per-tenant-cost-attribution-impossible`](#per-tenant-cost-attribution-impossible) — Per-customer cost is unknowable because all tenants share a key
9. [`audio-and-image-line-items-unnoticed`](#audio-and-image-line-items-unnoticed) — Audio and image usage never shows up in token dashboards
10. [`fine-tuned-model-never-used`](#fine-tuned-model-never-used) — Fine-tuned model trained, paid for, and never called once
11. [`moderation-never-called`](#moderation-never-called) — Free moderation endpoint sees zero traffic on a public app
12. [`token-counts-reused-across-tokenizers`](#token-counts-reused-across-tokenizers) — Token estimates reused across tokenizers undercount 30%
13. [`priority-tier-model-unsupported`](#priority-tier-model-unsupported) — service_tier auto silently never reaches Priority Tier
14. [`spend-spiking-week-over-week`](#spend-spiking-week-over-week) — Organization spend jumped week over week unnoticed
15. [`cost-concentrated-in-one-key-or-workspace`](#cost-concentrated-in-one-key-or-workspace) — One workspace or key accounts for most of the spend
16. [`opus-tier-model-for-cheap-work`](#opus-tier-model-for-cheap-work) — An Opus-tier model is doing work Haiku could do
17. [`output-tokens-dominate-cost`](#output-tokens-dominate-cost) — Output tokens, not input, are what the bill is made of
18. [`priority-tier-spend-missing-from-cost-report`](#priority-tier-spend-missing-from-cost-report) — Priority Tier spend is invisible in the cost report
19. [`web-search-spend-unnoticed`](#web-search-spend-unnoticed) — Web search is billing $10 per 1,000 searches unnoticed
20. [`code-execution-hours-exceed-free-allowance`](#code-execution-hours-exceed-free-allowance) — Code execution container hours exceed the free 1,550
21. [`long-context-requests-unwatched`](#long-context-requests-unwatched) — Most tokens are spent in the 200k-1M context bucket
22. [`us-inference-geo-premium-unnoticed`](#us-inference-geo-premium-unnoticed) — US inference geo silently bills at a 1.1x multiplier
23. [`fast-mode-premium-spend-hidden`](#fast-mode-premium-spend-hidden) — Fast mode is billing Opus at $10/$50 per MTok
24. [`claude-code-edit-rejection-rate-high`](#claude-code-edit-rejection-rate-high) — Claude Code edit proposals are rejected more than accepted

### Rate limits and retries

25. [`rate-limit-exceeded-429`](#rate-limit-exceeded-429) — Requests fail with 429 rate_limit_exceeded under burst load
26. [`rate-limit-headers-near-exhaustion`](#rate-limit-headers-near-exhaustion) — x-ratelimit-remaining headers sit near zero before any 429
27. [`project-rate-limit-below-org`](#project-rate-limit-below-org) — A project's per-model rate limit is far below the org tier
28. [`quota-exhausted-not-rate-limited`](#quota-exhausted-not-rate-limited) — 429 credit_balance_exhausted retried forever as a rate limit
29. [`usage-tier-too-low`](#usage-tier-too-low) — Org is stuck on a low usage tier with tight per-model limits
30. [`flex-resource-unavailable-timeouts`](#flex-resource-unavailable-timeouts) — Flex tier returns 429 Resource Unavailable and times out at 10m
31. [`rate-limit-429-limiter-unidentified`](#rate-limit-429-limiter-unidentified) — 429s are retried blindly without reading which limit hit
32. [`itpm-exhausted-uncached-input`](#itpm-exhausted-uncached-input) — ITPM runs out because uncached input is never cached
33. [`otpm-exhausted`](#otpm-exhausted) — Output tokens per minute is the real ceiling, not RPM
34. [`retry-after-header-ignored`](#retry-after-header-ignored) — Retries fire before retry-after elapses and fail again
35. [`spend-cap-429-retried-forever`](#spend-cap-429-retried-forever) — A spend-cap 429 has no retry-after and never recovers
36. [`self-set-spend-limit-400`](#self-set-spend-limit-400) — A self-set spend limit returns 400, not 429
37. [`workspace-rate-limit-override-throttles`](#workspace-rate-limit-override-throttles) — A workspace override throttles far below the org limit
38. [`acceleration-limit-on-traffic-spike`](#acceleration-limit-on-traffic-spike) — A sudden traffic ramp trips acceleration-limit 429s

### Models and deprecations

39. [`assistants-api-already-shut-down`](#assistants-api-already-shut-down) — Assistants API was shut down on 2026-08-26 and now 404s
40. [`model-past-shutdown-date`](#model-past-shutdown-date) — A model id in use is past its published shutdown date
41. [`shutdown-date-approaching`](#shutdown-date-approaching) — A model in production has a shutdown date under 90 days out
42. [`legacy-completions-endpoint-sunset`](#legacy-completions-endpoint-sunset) — /v1/completions models all shut down 2026-09-28
43. [`legacy-gpt-snapshots-october-2026`](#legacy-gpt-snapshots-october-2026) — gpt-3.5-turbo, gpt-4 and gpt-4-turbo shut down 2026-10-23
44. [`o-series-reasoning-models-retiring`](#o-series-reasoning-models-retiring) — o1, o3-mini and o4-mini all shut down 2026-10-23
45. [`gpt5-snapshots-shutdown-december`](#gpt5-snapshots-shutdown-december) — Pinned gpt-5-2025-08-07 snapshots shut down 2026-12-11
46. [`floating-alias-snapshot-drift`](#floating-alias-snapshot-drift) — Unpinned model alias silently repoints to a new snapshot
47. [`dalle-models-removed`](#dalle-models-removed) — dall-e-2 and dall-e-3 were shut down on 2026-05-12
48. [`gpt-image-generation-churn`](#gpt-image-generation-churn) — gpt-image-1 dies 2026-10-23, gpt-image-1.5/mini on 2026-12-01
49. [`sora-videos-api-no-replacement`](#sora-videos-api-no-replacement) — Videos API and all Sora 2 models shut down 2026-09-24
50. [`audio-realtime-models-deprecated`](#audio-realtime-models-deprecated) — gpt-realtime and gpt-audio families shut down 2027-01-20
51. [`prompts-evals-agentbuilder-sunset`](#prompts-evals-agentbuilder-sunset) — /v1/prompts, Evals API and Agent Builder close 2026-11-30
52. [`fine-tuning-jobs-blocked`](#fine-tuning-jobs-blocked) — Fine-tuning stops accepting new jobs from 2027-01-06
53. [`text-moderation-model-retired`](#text-moderation-model-retired) — text-moderation-* models were shut down on 2025-10-27
54. [`legacy-embeddings-and-endpoints-dead`](#legacy-embeddings-and-endpoints-dead) — First-gen embeddings and /v1/edits have been dead since 2024
55. [`retired-model-id-still-in-code`](#retired-model-id-still-in-code) — Retired model id in code fails every call with 404
56. [`model-retiring-within-90-days`](#model-retiring-within-90-days) — A model still in production retires in under 90 days
57. [`floating-alias-instead-of-pinned-snapshot`](#floating-alias-instead-of-pinned-snapshot) — A floating model alias silently changes model under you
58. [`model-not-available-to-this-org`](#model-not-available-to-this-org) — Code names a model this organization cannot call
59. [`long-context-gated-on-obsolete-beta`](#long-context-gated-on-obsolete-beta) — 1M context is gated behind an obsolete beta header

### Structured output and tools

60. [`structured-output-truncated-by-length`](#structured-output-truncated-by-length) — JSON cut off mid-object — `max_output_tokens` truncation
61. [`refusal-field-ignored`](#refusal-field-ignored) — Model refused and the `refusal` field was never checked
62. [`strict-false-schema-silently-ignored`](#strict-false-schema-silently-ignored) — `strict` omitted, so the JSON schema is only a suggestion
63. [`tool-call-arguments-unparseable`](#tool-call-arguments-unparseable) — Tool-call `arguments` is a JSON string that fails to parse
64. [`tool-defined-but-never-called`](#tool-defined-but-never-called) — Tool ships in every request but the model never calls it
65. [`parallel-tool-calls-with-strict-schema`](#parallel-tool-calls-with-strict-schema) — Parallel tool calls quietly void the strict-schema promise
66. [`tool-schemas-dominate-input-tokens`](#tool-schemas-dominate-input-tokens) — Tool schemas dominate the input tokens on every call

### Batch and async

67. [`batch-discount-left-unused`](#batch-discount-left-unused) — Every request is real-time, so the Batch discount is unused
68. [`batch-expired-past-24h-window`](#batch-expired-past-24h-window) — Batch hit `expired` — 24h window closed on unfinished rows
69. [`batch-failed-input-validation`](#batch-failed-input-validation) — Batch went straight to `failed` on input-file validation
70. [`batch-error-file-never-read`](#batch-error-file-never-read) — `error_file_id` exists but the error file was never fetched
71. [`batch-partial-failure-unnoticed`](#batch-partial-failure-unnoticed) — Batch says `completed` while `request_counts.failed > 0`
72. [`batch-enqueued-token-limit-exceeded`](#batch-enqueued-token-limit-exceeded) — Batch rejected with `token_limit_exceeded` on the queue cap
73. [`batch-input-file-wrong-purpose`](#batch-input-file-wrong-purpose) — Batch input file uploaded with the wrong `purpose`
74. [`batch-output-file-never-downloaded`](#batch-output-file-never-downloaded) — Completed batch results expire undownloaded after 30 days
75. [`batch-created-never-polled`](#batch-created-never-polled) — Batch created days ago and never polled to a terminal state
76. [`batch-cancelled-partial-results`](#batch-cancelled-partial-results) — Cancelled batch left billed, partially-written output behind
77. [`background-response-never-polled`](#background-response-never-polled) — Background response left in `queued` and never collected
78. [`batch-requests-expired-after-24h`](#batch-requests-expired-after-24h) — Batch requests expire unprocessed at the 24-hour mark
79. [`batch-errored-requests-unread`](#batch-errored-requests-unread) — Batch request_counts.errored is above zero and unread
80. [`batch-results-never-fetched`](#batch-results-never-fetched) — Batch results lapse unread after the 29-day retention
81. [`batch-canceled-mid-flight-anthropic`](#batch-canceled-mid-flight-anthropic) — A canceled batch holds partial results nobody read
82. [`batches-created-but-never-polled`](#batches-created-but-never-polled) — Batches end and are never polled, so results are dropped
83. [`batch-queue-limit-reached`](#batch-queue-limit-reached) — The enqueued batch-request limit blocks new submissions
84. [`batch-tier-never-used`](#batch-tier-never-used) — The 50% Batch API discount is never used

### Keys, projects and access

85. [`org-verification-required`](#org-verification-required) — Unverified org can call a model but cannot stream it
86. [`unsupported-country-region`](#unsupported-country-region) — Requests from an unsupported region are blocked with 403
87. [`single-api-key-generates-all-spend`](#single-api-key-generates-all-spend) — A single API key accounts for nearly all org spend
88. [`api-key-never-used`](#api-key-never-used) — Project API keys exist that have never been used once
89. [`api-key-dormant-for-months`](#api-key-dormant-for-months) — A live API key has not been used in months
90. [`key-owner-lost-project-access`](#key-owner-lost-project-access) — Keys still work whose owner no longer has project access
91. [`legacy-user-owned-keys-in-project`](#legacy-user-owned-keys-in-project) — Production keys are owned by people, not service accounts
92. [`service-account-key-never-rotated`](#service-account-key-never-rotated) — A service account key has never been rotated since creation
93. [`no-prod-dev-project-separation`](#no-prod-dev-project-separation) — Prod and dev share one project, so spend cannot be split
94. [`archived-project-still-holds-keys`](#archived-project-still-holds-keys) — An archived project still holds live API keys
95. [`openai-invites-pending-past-expiry`](#openai-invites-pending-past-expiry) — Organization invites have sat pending until they expired
96. [`too-many-organization-owners`](#too-many-organization-owners) — Almost every org member holds the owner role
97. [`unreviewed-key-lifecycle-in-audit-log`](#unreviewed-key-lifecycle-in-audit-log) — API keys were created or deleted and nobody reviewed it
98. [`zero-data-retention-not-configured`](#zero-data-retention-not-configured) — Zero data retention was assumed but never configured
99. [`project-model-permissions-unrestricted`](#project-model-permissions-unrestricted) — Any model can be called from any project, including costly ones
100. [`stored-responses-accumulating`](#stored-responses-accumulating) — `store: true` is the default and every response is retained
101. [`conversations-never-deleted`](#conversations-never-deleted) — Conversations persist "until deleted" with no list endpoint
102. [`default-workspace-cost-unattributable`](#default-workspace-cost-unattributable) — Default-workspace cost cannot be attributed to a team
103. [`active-api-keys-never-used`](#active-api-keys-never-used) — Active API keys exist that no request has ever used
104. [`api-key-created-by-departed-member`](#api-key-created-by-departed-member) — An API key was created by a member who has left
105. [`api-keys-not-scoped-to-a-workspace`](#api-keys-not-scoped-to-a-workspace) — API keys are not scoped to any workspace
106. [`archived-workspace-with-active-keys`](#archived-workspace-with-active-keys) — An archived workspace still has active API keys
107. [`no-dev-prod-workspace-separation`](#no-dev-prod-workspace-separation) — Dev and prod traffic share one workspace
108. [`anthropic-invites-pending-past-expiry`](#anthropic-invites-pending-past-expiry) — Invites are sitting pending past their expiry
109. [`too-many-org-admins`](#too-many-org-admins) — Too many org members hold the admin role
110. [`workspace-has-no-spend-or-rate-guard`](#workspace-has-no-spend-or-rate-guard) — A workspace has no rate limit or spend guard
111. [`compliance-activity-feed-never-read`](#compliance-activity-feed-never-read) — Nobody reads Anthropic's activity feed for key and member changes
112. [`external-key-config-unattached`](#external-key-config-unattached) — A CMEK external key config is inert but assumed to be live

### Files and vector stores

113. [`vector-store-storage-cost-creeping`](#vector-store-storage-cost-creeping) — Vector store bytes keep growing and are billed hourly
114. [`files-accumulating-against-storage-quota`](#files-accumulating-against-storage-quota) — Uploaded files pile up against the 2.5 TB project quota
115. [`orphaned-assistants-purpose-files`](#orphaned-assistants-purpose-files) — `purpose=assistants` files orphaned by the Assistants sunset
116. [`vector-store-file-attach-failed`](#vector-store-file-attach-failed) — File silently failed to index — `last_error.code` on the store
117. [`vector-store-file-counts-failed`](#vector-store-file-counts-failed) — Vector store reports `file_counts.failed > 0` and nobody looked
118. [`vector-store-stuck-in-progress`](#vector-store-stuck-in-progress) — Vector store stuck `in_progress` long after ingestion ended
119. [`vector-store-expired-or-expiring`](#vector-store-expired-or-expiring) — Vector store `expires_after` will silently delete the index
120. [`empty-vector-store-still-referenced`](#empty-vector-store-still-referenced) — Empty vector store still wired into the file_search tool
121. [`files-storage-quota-climbing`](#files-storage-quota-climbing) — Files storage is climbing toward the 1 TB org limit
122. [`orphaned-files-never-deleted`](#orphaned-files-never-deleted) — Uploaded files are never deleted and accumulate
123. [`expired-files-still-referenced`](#expired-files-still-referenced) — Expired files still referenced return 404 or fail inference
124. [`files-api-beta-header-shape-drift`](#files-api-beta-header-shape-drift) — Files API pagination breaks when the beta header drops

### Prompt caching

125. [`prompt-cache-share-near-zero`](#prompt-cache-share-near-zero) — Cached input tokens are near zero, so caching saves nothing
126. [`prompt-caching-never-used`](#prompt-caching-never-used) — Prompt caching is never used anywhere in the organization
127. [`cache-writes-with-no-reads`](#cache-writes-with-no-reads) — Cache writes are paid for but almost never read back
128. [`one-hour-cache-ttl-not-earning-back`](#one-hour-cache-ttl-not-earning-back) — 1h cache TTL costs 2x but traffic never earns it back
129. [`prompt-below-model-cache-minimum`](#prompt-below-model-cache-minimum) — Prompt is under the model's cache minimum, so nothing caches
130. [`cache-invalidated-by-changing-prefix`](#cache-invalidated-by-changing-prefix) — Cache is invalidated every call by a changing prefix
131. [`cache-hit-rate-collapsed-after-model-change`](#cache-hit-rate-collapsed-after-model-change) — Cache hit rate collapsed right after a model switch
132. [`cache-read-share-below-breakeven`](#cache-read-share-below-breakeven) — Cache reads are too few to beat the write premium
133. [`claude-code-sessions-not-hitting-cache`](#claude-code-sessions-not-hitting-cache) — Claude Code sessions run with zero cache reads
134. [`openai-prompt-below-cache-minimum`](#openai-prompt-below-cache-minimum) — OpenAI prompts sit under the 1,024-token cache minimum
135. [`prompt-cache-key-not-set`](#prompt-cache-key-not-set) — prompt_cache_key is unset so identical prefixes miss the cache
136. [`cache-invalidated-by-request-option-churn`](#cache-invalidated-by-request-option-churn) — Changing reasoning.effort or tools voids the cache every call
137. [`prompt-cache-retention-left-at-default`](#prompt-cache-retention-left-at-default) — Cache retention default means overnight jobs always run cold

### Errors and reliability

138. [`reasoning-model-rejects-max-tokens`](#reasoning-model-rejects-max-tokens) — Reasoning models reject max_tokens, require max_completion_tokens
139. [`reasoning-model-rejects-temperature`](#reasoning-model-rejects-temperature) — Reasoning models reject any temperature other than 1
140. [`context-length-exceeded`](#context-length-exceeded) — Input plus requested output exceeds the model context window
141. [`silent-output-truncation`](#silent-output-truncation) — Responses stop mid-answer with status incomplete, not an error
142. [`service-tier-not-allowed`](#service-tier-not-allowed) — service_tier value rejected because the project disallows it
143. [`server-errors-not-retried`](#server-errors-not-retried) — 500 and 503 overloaded errors surface to users unretried
144. [`seed-determinism-unreliable`](#seed-determinism-unreliable) — seed no longer reproduces output after a fingerprint change
145. [`live-project-zero-usage-buckets`](#live-project-zero-usage-buckets) — A project that should be live shows zero usage buckets
146. [`requests-diverge-from-token-volume`](#requests-diverge-from-token-volume) — Request count grew far faster than tokens: a retry storm
147. [`fine-tune-job-failed-with-error-code`](#fine-tune-job-failed-with-error-code) — Fine-tuning job ended `failed` and `error.code` went unread
148. [`fine-tune-training-file-validation-errors`](#fine-tune-training-file-validation-errors) — Training file rejected during `validating_files`
149. [`realtime-session-60-minute-cap`](#realtime-session-60-minute-cap) — Realtime session dies at the 60-minute server-side ceiling
150. [`audio-transcription-25mb-limit`](#audio-transcription-25mb-limit) — Transcription rejects any upload over the 25 MB file limit
151. [`previous-response-id-chain-broken`](#previous-response-id-chain-broken) — `previous_response_id` 404s once the prior response is gone
152. [`anthropic-version-header-missing-or-ancient`](#anthropic-version-header-missing-or-ancient) — anthropic-version is missing or pinned to 2023-01-01
153. [`invalid-beta-header-value`](#invalid-beta-header-value) — A misspelled anthropic-beta value 400s the whole call
154. [`stale-beta-header-after-graduation`](#stale-beta-header-after-graduation) — Code still sends a beta header that has gone GA
155. [`overloaded-529-clusters`](#overloaded-529-clusters) — 529 overloaded_error arrives in clusters and is fatal
156. [`api-error-500-not-retried`](#api-error-500-not-retried) — 500 api_error is treated as a permanent client failure
157. [`non-streaming-request-over-ten-minutes`](#non-streaming-request-over-ten-minutes) — A non-streaming request over 10 minutes times out (504)
158. [`request-too-large-413`](#request-too-large-413) — A 32 MB request is rejected by Cloudflare with 413
159. [`max-tokens-above-model-cap`](#max-tokens-above-model-cap) — max_tokens is set above the model's own output cap
160. [`stop-reason-max-tokens-truncation`](#stop-reason-max-tokens-truncation) — Answers are silently truncated by stop_reason max_tokens
161. [`prompt-too-long-context-overflow`](#prompt-too-long-context-overflow) — Prompts overflow the window and 400 with prompt too long
162. [`token-counting-endpoint-unused`](#token-counting-endpoint-unused) — Nothing calls count_tokens, so overflow is a surprise

---

## reasoning-tokens-billed-invisibly

- **slug**: `reasoning-tokens-billed-invisibly`
- **title**: Reasoning tokens are billed as output but never returned
- **symptom**: No error. Cost per request jumps 3–10x after switching to a reasoning model while the visible response text is the same length. `usage.output_tokens` is far larger than the token count of the text you actually received; `usage.output_tokens_details.reasoning_tokens` holds the difference.
- **mechanism**: Reasoning tokens are generated, billed at the output rate, and consume context window, but are not returned in the API response. `reasoning.mode: "pro"` on GPT-5.6 "performs more model work than standard mode, increasing token usage and cost" — a single flag can multiply the bill. Teams costing a migration off visible output length underestimate by the reasoning fraction.
- **detect**: Admin-read key → `GET /v1/organization/usage/completions?start_time=<30d ago>&bucket_width=1d&group_by[]=model&group_by[]=project_id` and compute `results[].output_tokens / results[].num_model_requests` per model per day; a step change on the day a model constant changed, with no change to `input_tokens` per request, is the reasoning-token tax. Cross-check spend with `GET /v1/organization/costs?start_time=<30d ago>&bucket_width=1d&group_by[]=line_item`.
- **repair**: Add `reasoning={"effort": "low"}` (or `"minimal"`/`"none"` where the model supports it) for tasks that do not need deliberation, and drop `reasoning={"mode":"pro"}` unless the eval justifies it. Log `usage.output_tokens_details.reasoning_tokens` per call so the invisible half is visible in your own metrics.
- **category**: Cost and usage
- **sources**: https://developers.openai.com/api/docs/guides/reasoning

## fast-mode-silently-downgraded

- **slug**: `fast-mode-silently-downgraded`
- **title**: Fast mode requests get served as default and lose the speedup
- **symptom**: `200`, but the response body's `service_tier` field reads `"default"` even though the request sent `"fast"`. p95 latency regresses to standard levels while the team believes it is paying and receiving the 2.5x speedup. Conversely, a project defaulted to Fast mode bills at 2x with no code change visible anywhere.
- **mechanism**: Fast mode has ramp rate limits; when they trigger, requests are downgraded and `"default"` is assigned as the served tier. The request field and the response field are separate — the API reports what you *got*, not what you *asked for*, and nothing raises. Billing is real either way: for GPT-5.6 Sol, Fast mode is twice the Standard rate ($8/1M input, $40/1M output short-context; $16/1M input, $60/1M output long-context).
- **detect**: Admin-read key → `GET /v1/organization/costs?start_time=<30d ago>&bucket_width=1d&group_by[]=line_item` and look for Fast/Priority line items; compare the effective $/token against the Standard rate to confirm which tier actually served the traffic. `GET /v1/organization/projects/{project_id}` shows whether Project Service Tier is set to Fast — a project defaulted to Fast bills every request at 2x even when no code sends `service_tier`. Project read-only key → in any live response, read the top-level `service_tier` field and compare it to what was requested.
- **repair**: If the premium is not being delivered, drop `"service_tier": "fast"` (or set the Project Service Tier back to Standard) and stop paying 2x. If the speedup is needed, print the requested-vs-served mismatch rate and the ramp-limit increase to request. Always log the response's `service_tier` field, not the request's.
- **category**: Cost and usage
- **sources**: https://developers.openai.com/api/docs/guides/fast-mode · https://openai.com/api-priority-processing/

## streaming-usage-lost

- **slug**: `streaming-usage-lost`
- **title**: Streamed responses report no token usage, breaking cost tracking
- **symptom**: Every streamed chunk has `usage: null`. Internal cost dashboards show zero tokens for streaming traffic while the OpenAI bill keeps rising — a silent divergence between what the app records and what the org is charged. On a dropped or cancelled connection, even the final usage chunk never arrives.
- **mechanism**: In Chat Completions streaming, `usage` is `null` on every chunk unless `stream_options: {"include_usage": true}` is set, in which case a final chunk carries the totals (with `choices` as an empty array). If the stream is interrupted or the client cancels, that final chunk is never delivered — so the tokens are billed but never recorded, and the loss is proportional to your client-abandonment rate.
- **detect**: Admin-read key → `GET /v1/organization/usage/completions?start_time=<7d ago>&bucket_width=1d&group_by[]=project_id&group_by[]=model` and compare `results[].input_tokens + results[].output_tokens` against the same period's totals in your own telemetry. A persistent shortfall concentrated in projects that stream is this bug; the gap size estimates your untracked spend. Cross-check dollars with `GET /v1/organization/costs?start_time=<7d ago>&bucket_width=1d&group_by[]=project_id`.
- **repair**: Add `stream_options={"include_usage": True}` to every streaming Chat Completions call and read the final chunk's `usage`. On the Responses API, consume the terminal `response.completed` event and read `response.usage`. Handle client disconnects by reconciling against the Admin usage API rather than trusting per-request telemetry alone.
- **category**: Cost and usage
- **sources**: https://developers.openai.com/api/docs/guides/streaming-responses · https://community.openai.com/t/usage-stats-now-available-when-using-streaming-with-the-chat-completions-api-or-completions-api/738156

## spend-spike-week-over-week

- **slug**: `spend-spike-week-over-week`
- **title**: Org spend jumped week over week with no release to explain it
- **symptom**: No error and no HTTP status: the API keeps working perfectly. The first signal is a monthly invoice or a billing email that is 2–5x the previous period, weeks after the change that caused it landed. Nothing in application logs looks different.
- **mechanism**: Cost is a product of request volume, model choice, and tokens per request, and any of the three can move without a deploy: a prompt template grew, a retry loop got more aggressive, a customer onboarded, a cron went from hourly to every five minutes, or a fallback path started firing. Because OpenAI bills post-paid and the dashboard is a pull surface nobody pulls, the feedback loop between "the change shipped" and "the bill arrived" is 2–6 weeks long.
- **detect**: Organization **ADMIN** key required. `GET /v1/organization/costs?start_time={now-56d}&bucket_width=1d&limit=56`. Costs only supports `bucket_width=1d`; `limit` ranges 1–180 (default 7), so ask for the full window explicitly. Sum `data[].results[].amount.value` (a float; `amount.currency` is lowercase ISO-4217, e.g. `"usd"`) into 7-day windows using each bucket's `start_time`. Flag when the most recent complete week exceeds the trailing 4-week mean by more than 40%. Re-run with `&group_by=line_item&group_by=project_id` to attribute the delta — the same call returns `line_item` (e.g. `"gpt-4o-2024-08-06, input"`) and `project_id` populated once grouped.
- **repair**: Print the two week totals, the percentage change, and the top three `line_item` values by delta. Then: set a hard ceiling with `POST /v1/organization/spend_limit` (`{"threshold_amount": <cents>, "currency": "USD", "interval": "month"}`) and an early-warning alert with `POST /v1/organization/spend_alerts` at ~60% of that threshold. Never execute either — print the exact curl.
- **category**: Cost and usage
- **sources**: https://platform.openai.com/docs/api-reference/usage/costs · https://developers.openai.com/api/docs/guides/admin-apis · https://developers.openai.com/cookbook/examples/completions_usage_api

## one-model-or-project-dominates-cost

- **slug**: `one-model-or-project-dominates-cost`
- **title**: One line item or project is eating most of the org's spend
- **symptom**: No error. The total bill is "about what we expected", so nobody looks inside it. When someone finally does, a single model or a single project turns out to be 70–90% of the number, and it is often not the one the team assumed was expensive.
- **mechanism**: Cost concentration is the normal shape of an LLM bill, not an anomaly — but it is invisible unless you group. The default `GET /v1/organization/costs` response returns one undifferentiated `amount` per bucket with `line_item` and `project_id` both `null`, which reads as a single opaque number. Teams then optimize whatever they *remember* being expensive rather than what the data says, and spend weeks shaving a line item worth 3% of the bill.
- **detect**: Organization **ADMIN** key required. Two calls over the same window: `GET /v1/organization/costs?start_time={now-30d}&limit=30&group_by=line_item` and `…&group_by=project_id`. `group_by` accepts only `project_id`, `line_item`, and `api_key_id` on the costs endpoint (unlike usage, it does **not** accept `model`; the model appears inside the `line_item` string). Aggregate `data[].results[].amount.value` per `line_item` and per `project_id`, sort descending, and compute each one's share of total. Flag any single `line_item` or `project_id` above 50%. Grouped results also carry `quantity` and `quantity_unit` (one of `tokens`, `1000_tokens`, `duration_seconds`, `duration_minutes`, `duration_hours`, `gibibyte_hours`, `images`, `characters`), which lets you derive an effective unit price and compare it against the price card.
- **repair**: Print a ranked table: `line_item`, `amount.value`, share of total, `quantity`, `quantity_unit`. For the top entry, print the cheaper substitute and the arithmetic — e.g. "`gpt-4o, input` is $X/mo at N tokens; `gpt-4o-mini` at the same volume is $X/12". Suggest isolating the dominant project behind its own `POST /v1/organization/projects/{project_id}/spend_limit`.
- **category**: Cost and usage
- **sources**: https://platform.openai.com/docs/api-reference/usage/costs · https://github.com/openai/openai-python/blob/main/api.md · https://help.openai.com/en/articles/10478918

## frontier-model-on-trivial-workload

- **slug**: `frontier-model-on-trivial-workload`
- **title**: A frontier model is doing work a mini model would do fine
- **symptom**: No error. A classifier, an intent router, a title generator, or a short extraction step is running on the org's most expensive model, returning 20-token answers, and costing 10–30x what it needs to. Usually the model name was copy-pasted from a demo and never revisited.
- **mechanism**: Model selection is a string literal in a config file. It gets set once, during prototyping, when correctness matters and cost does not — and it is never audited, because nothing in the API distinguishes "this model is necessary here" from "this model is habit here". The tell is shape, not volume: high request counts with very low output tokens per request means the model is being asked trivial questions.
- **detect**: Organization **ADMIN** key required. `GET /v1/organization/usage/completions?start_time={now-14d}&bucket_width=1d&limit=14&group_by=model&group_by=project_id`. For each result compute `output_tokens / num_model_requests` and `input_tokens / num_model_requests`. Flag any premium model (`gpt-4o`, `gpt-4.1`, `o3`, `gpt-5`, and similar non-`mini`/non-`nano` names in `model`) where mean output is under ~50 tokens and `num_model_requests` is high — a lot of calls producing almost nothing. Cross-reference `GET /v1/organization/costs?start_time=…&group_by=line_item` to price that model's share, and `GET /v1/organization/projects/{project_id}/model_permissions` (returns `object: "project.model_permissions"`, `mode: "allow_list" | "deny_list"`, `model_ids[]`) to see whether the project is even constrained.
- **repair**: Print, per model: request count, mean output tokens, and current monthly cost from the costs call. Recommend the `-mini` / `-nano` sibling for the low-output workloads and print the projected saving using the real request volume. For durable enforcement, print the `POST /v1/organization/projects/{project_id}/model_permissions` body — `{"mode": "allow_list", "model_ids": ["gpt-4o-mini"]}` — so the cheap project cannot reach the expensive model at all.
- **category**: Cost and usage
- **sources**: https://platform.openai.com/docs/api-reference/usage/completions · https://developers.openai.com/api/docs/guides/admin-apis · https://platform.openai.com/docs/api-reference/projects

## no-organization-spend-limit

- **slug**: `no-organization-spend-limit`
- **title**: No hard spend limit is set, so the bill has no ceiling
- **symptom**: No error until it is far too late. `GET /v1/organization/spend_limit` returns no configured limit (or an `enforcement.status` of `"inactive"`), and `GET /v1/organization/spend_alerts` returns an empty list. A leaked key, an infinite agent loop, or a retry storm can run for days at any spend rate with nothing to stop it. When a limit *is* configured and is reached, affected requests begin returning `429` with code `organization_spend_limit_exceeded` (or `project_spend_limit_exceeded` for a project-scoped cap) — which is the controlled outage you are choosing over an unbounded invoice.
- **mechanism**: Post-paid billing with auto-recharge has no natural ceiling: the platform's job is to serve requests, and it will keep serving them. The hard limit is opt-in and lives on a separate admin endpoint from everything else, so it is easy to assume the console's "budget" display is enforcement when it is only a chart. Alerts are similarly opt-in and separately configured — an org can have alerts without a limit (warning, no brake) or a limit without alerts (brake, no warning).
- **detect**: Organization **ADMIN** key required. Three read-only calls. `GET /v1/organization/spend_limit` returns an `organization.spend_limit` object with `threshold_amount` (**in cents**), `currency` (`"USD"`), `interval` (`"month"`), and `enforcement.status` (`"inactive"` or `"enforcing"`) — flag a missing limit, or one present but `"inactive"`. `GET /v1/organization/spend_alerts` returns `organization.spend_alert` objects with `id`, `threshold_amount`, `currency`, `interval`, and `notification_channel` (`type: "email"`, `recipients[]`, `subject_prefix`) — flag an empty list, or alerts whose `recipients[]` contain departed addresses not present in `GET /v1/organization/users`. Then sanity-check the numbers against reality: sum `amount.value` from `GET /v1/organization/costs?start_time={month_start}&limit=31` and flag when the limit is more than ~5x current monthly run rate (a ceiling that high will never fire) or already exceeded by run rate. Repeat per project with `GET /v1/organization/projects/{project_id}/spend_limit` and `…/spend_alerts`.
- **repair**: Print current month-to-date spend, the trailing 3-month mean, and the configured limit (or "none"). Print the exact bodies: `POST /v1/organization/spend_limit` with `{"threshold_amount": <2x_monthly_mean_in_cents>, "currency": "USD", "interval": "month"}`, and `POST /v1/organization/spend_alerts` at 50% / 75% / 90% of that with a real `notification_channel.recipients` list. State plainly that `threshold_amount` is cents — a limit entered as dollars is 100x too low and will page you immediately.
- **category**: Cost and usage
- **sources**: https://developers.openai.com/api/docs/guides/admin-apis · https://github.com/openai/openai-python/blob/main/api.md · https://help.openai.com/en/articles/10478918

## per-tenant-cost-attribution-impossible

- **slug**: `per-tenant-cost-attribution-impossible`
- **title**: Per-customer cost is unknowable because all tenants share a key
- **symptom**: No error. A multi-tenant product cannot answer "what does customer X cost us", so it cannot price, cannot spot the one account burning the margin, and cannot enforce a per-tenant quota. Teams reach for `group_by=user_id` expecting it to segment their end users, and get rows that instead name their own employees and service accounts.
- **mechanism**: This is a widely-held misconception worth stating precisely: **`user_id` in the Usage API is the OpenAI org member or service account that owns the calling API key — not an end-user identifier you supply.** The attribution chain is request → API key → key owner → `user_id`. The request-level `user` field never reaches the Usage API at all; it exists for abuse detection and cache bucketing, and is now marked deprecated in the OpenAPI spec in favour of `safety_identifier` and `prompt_cache_key`. So no application-side change can make the Usage API segment by your customers. The only dimensions the platform can attribute along are the ones it controls server-side: `project_id`, `api_key_id`, and `user_id` (your own principals).
- **detect**: Organization **ADMIN** key required. `GET /v1/organization/usage/completions?start_time={now-7d}&bucket_width=1d&limit=7&group_by=user_id&group_by=api_key_id&group_by=project_id`. Resolve each returned `user_id` against `GET /v1/organization/users?limit=100` — if every `user_id` maps to a staff member or a service account (`is_service_account: true`) rather than to a customer, the org has no tenant-level attribution, regardless of what the application sends. Confirm the concentration with `GET /v1/organization/costs?start_time={now-30d}&limit=30&group_by=api_key_id`: a small number of `api_key_id` values covering all spend while the product serves many customers means tenant cost is structurally unrecoverable. Compare the count of distinct `api_key_id` values against the known tenant count — if keys are far fewer than tenants, attribution is impossible by construction.
- **repair**: Print the distinct `user_id` / `api_key_id` values with their 30-day spend, and state plainly that the Usage API cannot segment by end user. The architectural change to print: issue a **separate API key (or a separate project) per tenant** — or per tenant tier, if per-tenant is too many — mint them via `POST /v1/organization/projects/{project_id}/service_accounts/{service_account_id}/api_keys`, and attribute with `group_by=api_key_id` / `group_by=project_id`. Note this is forward-only and cannot backfill. For orgs unwilling to split keys, the fallback is application-side token accounting from each response's `usage` block, reconciled against `/v1/organization/costs` totals.
- **category**: Cost and usage
- **sources**: https://platform.openai.com/docs/api-reference/usage/completions · https://github.com/openai/openai-openapi/blob/master/openapi.yaml · https://platform.openai.com/docs/api-reference/project-api-keys

## audio-and-image-line-items-unnoticed

- **slug**: `audio-and-image-line-items-unnoticed`
- **title**: Audio and image usage never shows up in token dashboards
- **symptom**: No error. An internal cost dashboard built on `/v1/organization/usage/completions` reports a number that is meaningfully lower than the invoice. The gap is speech synthesis, transcription, image generation, web search calls, and code interpreter sessions — none of which are denominated in tokens and none of which appear on the completions endpoint at all.
- **mechanism**: The Usage API is deliberately split by modality, and each surface has its own units: audio speech bills by characters, transcription by seconds, images by image count and size, code interpreter by session, file search and web search by call. A monitoring script written against completions is structurally incapable of seeing any of it, and because the missing spend is usually a minority of the bill, the discrepancy gets rationalized as rounding rather than investigated. Multimodal chat complicates it further — audio and image tokens flowing *through* the completions endpoint appear as `input_audio_tokens` / `output_audio_tokens` / `input_image_tokens` / `output_image_tokens`, which a naive `input_tokens + output_tokens` sum silently double-counts or misprices.
- **detect**: Organization **ADMIN** key required. Sweep every usage surface over the same window, each with `start_time`, `bucket_width=1d`, `limit=31`, `group_by=project_id`: `/v1/organization/usage/audio_speeches` (result object `organization.usage.audio_speeches.result`, field `characters`), `/v1/organization/usage/audio_transcriptions` (`organization.usage.audio_transcriptions.result`, field `seconds`), `/v1/organization/usage/images` (`organization.usage.images.result`, field `images`, groupable and filterable by `size` — `256x256`, `512x512`, `1024x1024`, `1792x1792`, `1024x1792` — and by `source` — `image.generation` / `image.edit` / `image.variation`), `/v1/organization/usage/code_interpreter_sessions` (`organization.usage.code_interpreter_sessions.result`, field `num_sessions`), `/v1/organization/usage/file_search_calls` (`organization.usage.file_searches.result`, field `num_requests`, groupable by `vector_store_id`), `/v1/organization/usage/web_search_calls` (`organization.usage.web_searches.result`, fields `num_requests` and `num_model_requests`, groupable by `context_level`), `/v1/organization/usage/embeddings`, and `/v1/organization/usage/moderations`. Then reconcile: sum `amount.value` from `GET /v1/organization/costs?start_time=…&group_by=line_item` and flag any `line_item` whose spend has no corresponding entry in your dashboard. Within completions, also read `input_audio_tokens` and `input_image_tokens` separately from `input_text_tokens`.
- **repair**: Print a reconciliation table: total from `/v1/organization/costs` versus the sum your dashboard covers, with each unaccounted `line_item` and its `amount.value`, `quantity`, and `quantity_unit`. Recommend driving the dashboard from `/v1/organization/costs` grouped by `line_item` as the source of truth for money, and using the per-modality usage endpoints only to explain *why* a line item moved.
- **category**: Cost and usage
- **sources**: https://platform.openai.com/docs/api-reference/usage · https://platform.openai.com/docs/api-reference/usage/costs · https://github.com/openai/openai-python/blob/main/api.md

## fine-tuned-model-never-used

- **slug**: `fine-tuned-model-never-used`
- **title**: Fine-tuned model trained, paid for, and never called once
- **symptom**: `GET /v1/fine_tuning/jobs` shows `status: "succeeded"` jobs with a populated `fine_tuned_model` (e.g. `ft:gpt-4o-mini-2024-07-18:acme::AbC123`) and non-zero `trained_tokens`, but `GET /v1/organization/usage/completions?...&group_by=model` reports zero `num_model_requests` for that model id. Training was billed; inference never happened.
- **mechanism**: Deploying a fine-tune is a config change on your side — nothing in the API switches traffic over. Experiments that "succeeded" but never won an eval, or models superseded by the next run, remain listed forever. Their `result_files` and checkpoints also linger in Files storage.
- **detect**: Collect `fine_tuned_model` from `GET /v1/fine_tuning/jobs?limit=100` where `status == "succeeded"`, plus `GET /v1/fine_tuning/jobs/{id}/checkpoints` for intermediate `fine_tuned_model_checkpoint` ids. Then `GET /v1/organization/usage/completions?start_time=<30d ago>&bucket_width=1d&group_by=model` (**admin read key**) and flag any fine-tuned model id whose summed `num_model_requests` is 0. Confirm the model still exists with `GET /v1/models/{model}`. Requires: project read key + admin read key (`api.usage.read`).
- **repair**: print — `Either route traffic to the fine-tune or retire it. Delete unused custom models and their result_files (GET /v1/files?purpose=fine-tune-results) to stop storage charges. Note the platform timeline: new fine-tuning jobs are being wound down (announced 2026-05-07; active customers cannot create new jobs after 2027-01-06), and fine-tuned snapshots on retired base models shut down 2026-10-23 — inference on a fine-tune dies with its base model.`
- **category**: Cost and usage
- **sources**: https://developers.openai.com/api/docs/api-reference/fine-tuning · https://developers.openai.com/api/docs/deprecations

## moderation-never-called

- **slug**: `moderation-never-called`
- **title**: Free moderation endpoint sees zero traffic on a public app
- **symptom**: `GET /v1/organization/usage/moderations?start_time=...&bucket_width=1d` returns zero buckets (or zero `num_model_requests`) while `GET /v1/organization/usage/completions` for the same window shows heavy user-facing traffic. No error — just an unused safety layer.
- **mechanism**: Moderation is opt-in and **free** (`omni-moderation-latest`, text + image, images up to 20 MB). Nothing routes user input through it automatically. Its response gives `flagged` (boolean), `categories` (per-category booleans), `category_scores` (0-1 confidence) and `category_applied_input_types` across 13 categories: harassment, harassment/threatening, hate, hate/threatening, illicit, illicit/violent, self-harm, self-harm/intent, self-harm/instructions, sexual, sexual/minors, violence, violence/graphic. An app that never calls it discovers its content problems through refusals, account warnings, or users.
- **detect**: `GET /v1/organization/usage/moderations?start_time=<30d ago>&end_time=<now>&bucket_width=1d` and compare `num_model_requests` against `GET /v1/organization/usage/completions` over the same window (**admin read key** with `api.usage.read` for both). A completions:moderations ratio far from 1:1 on a user-facing product is the finding. Requires: admin read key.
- **repair**: print — `Call POST /v1/moderations on user input (and on model output where you republish it) before the completion. It costs nothing. Branch on flagged, and log category_scores so you can tune thresholds per category rather than trusting the single boolean. Note the endpoint does not classify audio.`
- **category**: Cost and usage
- **sources**: https://developers.openai.com/api/docs/guides/moderation · https://github.com/openai/openai-python/blob/main/api.md

## token-counts-reused-across-tokenizers

- **slug**: `token-counts-reused-across-tokenizers`
- **title**: Token estimates reused across tokenizers undercount 30%
- **symptom**: No error at first. Budgets, chunk sizes and window checks that passed on the old model start failing after a migration: `prompt is too long` 400s, unexplained ~30% cost increases, and RAG chunks that no longer fit.
- **mechanism**: Claude 4.7 and later models — Opus 4.7, Opus 4.8, Opus 5, Sonnet 5, Fable 5, Mythos 5 and Mythos Preview — use a **newer tokenizer that produces approximately 30% more tokens for the same text**; the exact increase depends on content and workload shape. Sonnet 4.6 and earlier use the previous tokenizer. Billing reflects the new counts, so reusing a count measured on a pre-4.7 model to estimate cost or window fit on a post-4.7 model is wrong in the expensive direction. Conversely, 1M tokens is ~555k words on the new tokenizer and ~750k words on the old.
- **detect**: Workspace/project API key, free and read-only: call `POST /v1/messages/count_tokens` **twice with the byte-identical body**, once with your current `model` and once with the target `model`, and compare the two `input_tokens` values — "the token counting endpoint returns the count under the tokenizer of the `model` you pass." Admin API key: `GET /v1/organizations/usage_report/messages?group_by[]=model&bucket_width=1d` across a migration date shows the input-token step change per model for identical traffic.
- **repair**: Print: the two `input_tokens` values, the measured ratio for *this* workload (not the generic 30%), and every hard-coded token budget, chunk size or window guard that needs re-baselining. Flag any cached count table keyed only by text, not by model. Do not recount at scale.
- **category**: Cost and usage
- **sources**: https://platform.claude.com/docs/en/build-with-claude/token-counting · https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/models/overview

## priority-tier-model-unsupported

- **slug**: `priority-tier-model-unsupported`
- **title**: service_tier auto silently never reaches Priority Tier
- **symptom**: `service_tier: "auto"` is set on every request but `usage.service_tier` in the response always reads `standard`, and the `anthropic-priority-input-tokens-limit` / `-remaining` / `-reset` headers are absent. The team believes it has overload protection it does not have, and 529s keep landing.
- **mechanism**: Two independent traps. First, model coverage: "Priority Tier is supported on all available Claude models **except** Claude Mythos 5, Claude Mythos Preview, Claude Opus 5, and Claude Sonnet 5" — so migrating to Opus 5 or Sonnet 5 silently drops Priority Tier. Second, capacity: Priority Tier capacity commitments are **no longer available for purchase**; only orgs with an existing commitment have any. Requests beyond the committed input/output tokens per minute fall back to standard automatically, and Priority requests also draw on the normal rate limits — if servicing one would exceed those, it is declined outright. Priority Tier costs are excluded from the Cost API entirely.
- **detect**: Admin API key: `GET /v1/organizations/usage_report/messages?group_by[]=service_tier&group_by[]=model&bucket_width=1d` — look for the `priority` value; a model/tier combination that never reports `priority` has no coverage. Because Priority costs are excluded from `/v1/organizations/cost_report`, the usage endpoint is the only read-only source for them. Response-side: the presence of the `anthropic-priority-*` header triple tells you a request was *eligible* for Priority Tier even when it was over the limit — absence means the model or the org is not covered.
- **repair**: Print: per model, the share of traffic reported as `priority` vs `standard` vs `batch`; flag any model on the exclusion list that is configured with `service_tier: "auto"` under the assumption of priority routing. Note that `"standard_only"` is the way to deliberately preserve commitment capacity, and that burndown is 0.1x for cache reads, 1.25x for 5-minute cache writes, 2.0x for 1-hour cache writes and 1.1x for `inference_geo: "us"` on 4.6+ models. Do not change `service_tier`.
- **category**: Cost and usage
- **sources**: https://platform.claude.com/docs/en/api/service-tiers · https://platform.claude.com/docs/en/manage-claude/usage-cost-api · https://platform.claude.com/docs/en/api/rate-limits

## spend-spiking-week-over-week

- **slug**: `spend-spiking-week-over-week`
- **title**: Organization spend jumped week over week unnoticed
- **symptom**: No error. `GET /v1/organizations/cost_report` shows the trailing 7 daily `amount` totals several times the prior 7 days', with no corresponding change in the organization's key or workspace inventory.
- **mechanism**: Nothing in the API pushes an alert on spend. A retry storm, a loop that re-sends the full conversation each turn, a model upgrade, or a new tenant onboarding all show up only as a larger number in a report nobody is reading. Compounding it: the cost report is daily-granularity only (`bucket_width` accepts `1d` only) with a default `limit` of 7 and a maximum of 31, so a naive call returns exactly one week and hides the comparison you need.
- **detect**: Admin API key required. Call `GET /v1/organizations/cost_report?starting_at= {T-14d}&ending_at={T}&limit=31&group_by[]=workspace_id&group_by[]=description` and page on `next_page` until `has_more` is false. Sum `data[].results[].amount` (a decimal **string** in cents — parse as decimal, not float) for days 0–6 and 7–13 and flag a ratio above your threshold. Attribute the delta by re-grouping on `workspace_id`, then on `description` to see which `model` / `token_type` moved.
- **repair**: Print, do not run: name the workspace and `description` rows that account for the delta and hand them to the owning team. Note that data can be revised as late events arrive, so re-read the same window before escalating.
- **category**: Cost and usage
- **sources**: https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report · https://platform.claude.com/docs/en/manage-claude/usage-cost-api

## cost-concentrated-in-one-key-or-workspace

- **slug**: `cost-concentrated-in-one-key-or-workspace`
- **title**: One workspace or key accounts for most of the spend
- **symptom**: No error. Grouping the cost report by `workspace_id` shows a single `workspace_id` holding the large majority of `amount`; grouping the usage report by `api_key_id` shows a single key holding the large majority of tokens.
- **mechanism**: Concentration is not automatically wrong, but it is always worth naming, because it means one failure — a runaway loop behind one key, one tenant's traffic, one misconfigured cron — can move the entire organization's bill. It is also the case that hits the reporting blind spots hardest: usage in the **default workspace** reports `workspace_id: null`, and Console playground usage reports `api_key_id: null`, so a concentration that lands in either bucket is unattributable to a team without further work.
- **detect**: Admin API key required. `GET /v1/organizations/cost_report?starting_at={T-30d}& limit=31&group_by[]=workspace_id` — rank `data[].results[]` by `amount` and compute each workspace's share. Then `GET /v1/organizations/usage_report/messages?starting_at={T-30d}& bucket_width=1d&limit=31&group_by[]=api_key_id` and rank keys by `uncached_input_tokens + cache_creation.* + output_tokens`. Resolve the winning IDs to names via `GET /v1/organizations/workspaces` and `GET /v1/organizations/api_keys` (`name`, `partial_key_hint`, `created_by`).
- **repair**: Print, do not run: report the top workspace and top key with their share of spend and their owners. If the top row is `null`, state which of the two `null` meanings applies (default workspace, or Console playground) rather than reporting it as "unknown".
- **category**: Cost and usage
- **sources**: https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report · https://platform.claude.com/docs/en/manage-claude/usage-cost-api · https://platform.claude.com/docs/en/api/admin-api/apikeys/list-api-keys

## opus-tier-model-for-cheap-work

- **slug**: `opus-tier-model-for-cheap-work`
- **title**: An Opus-tier model is doing work Haiku could do
- **symptom**: No error. The usage report grouped by `model` shows an Opus-tier model (`claude-opus-5`, `claude-opus-4-8`) carrying most tokens on a workload whose output is short and whose input is repetitive — small `output_tokens` relative to `uncached_input_tokens`, flat day over day.
- **mechanism**: Claude Opus 5 is **$5 / MTok** input and **$25 / MTok** output; Claude Haiku 4.5 is **$1 / $5**; Claude Sonnet 5 is **$2 / $10**. Claude Fable 5 is **$10 / $50**. A classification, extraction, or routing workload running on Opus costs 5x what it costs on Haiku for identical throughput. Nothing in the API objects — model choice is never validated against task difficulty — so the overspend only ever appears as a model column in a report.
- **detect**: Admin API key required. `GET /v1/organizations/usage_report/messages?starting_at= {T-30d}&bucket_width=1d&limit=31&group_by[]=model&group_by[]=api_key_id`. For each `(model, api_key_id)` pair compute `output_tokens / uncached_input_tokens`. A low, stable ratio on an Opus-tier model is the shape of cheap work on an expensive model. Price the gap with `GET /v1/organizations/cost_report?starting_at={T-30d}&group_by[]=description` — each result carries `model` and `token_type` so you can compute the model-substituted total.
- **repair**: Print, do not run: name the `api_key_id` and the candidate cheaper model, and print the estimated monthly delta at the published rates. Do not change the model — that is the owning team's call.
- **category**: Cost and usage
- **sources**: https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report

## output-tokens-dominate-cost

- **slug**: `output-tokens-dominate-cost`
- **title**: Output tokens, not input, are what the bill is made of
- **symptom**: No error. In the cost report grouped by `description`, rows with `token_type: "output_tokens"` hold most of the `amount`, and in the usage report `output_tokens` is large relative to `uncached_input_tokens`.
- **mechanism**: Output is priced at **5x** input on every current model ($25 vs $5 on Opus 5, $10 vs $2 on Sonnet 5, $50 vs $10 on Fable 5). Thinking tokens are billed as output tokens when generated, and adaptive thinking allocates them dynamically — so raising `effort`, or moving to a model where thinking is on by default (Claude Opus 5 runs adaptive thinking when `thinking` is omitted, unlike Opus 4.8/4.7), silently shifts the bill toward the 5x side. No caching discount exists for output; the only lever is generating less.
- **detect**: Admin API key required. `GET /v1/organizations/cost_report?starting_at={T-30d}& limit=31&group_by[]=description` — compute `sum(amount)` where `token_type == "output_tokens"` as a share of total. Then `GET /v1/organizations/ usage_report/messages?starting_at={T-30d}&bucket_width=1d&limit=31&group_by[]=model` and track `output_tokens` per model per day; a step increase with no input increase points at a thinking/effort change rather than more traffic.
- **repair**: Print, do not run: for the model and workspace carrying the output spend, suggest lowering `output_config.effort` (e.g. `high` → `medium`) and re-reading the same daily series a week later. Never change effort settings from a read-only audit.
- **category**: Cost and usage
- **sources**: https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report · https://platform.claude.com/docs/en/build-with-claude/context-windows

## priority-tier-spend-missing-from-cost-report

- **slug**: `priority-tier-spend-missing-from-cost-report`
- **title**: Priority Tier spend is invisible in the cost report
- **symptom**: No error, and worse than an error: a silent reconciliation gap. The usage report grouped by `service_tier` returns results with `service_tier: "priority"` (or `"priority_on_demand"`) carrying real token volume, but the cost report's `service_tier` field only ever takes the values `"batch"`, `"standard"`, or `null` — the priority tokens have no corresponding `amount` row.
- **mechanism**: Priority Tier uses a different billing model and is deliberately **not included** in `GET /v1/organizations/cost_report`. Any dashboard that treats the cost report as the organization's total spend will under-report by exactly the Priority Tier commitment. The tokens are still visible — just on the usage endpoint only.
- **detect**: Admin API key required. Compare the two endpoints over the same window. `GET /v1/organizations/usage_report/messages?starting_at={T-30d}&bucket_width=1d&limit=31& group_by[]=service_tier` — if any result has `service_tier` in `{"priority", "priority_on_demand"}` with non-zero tokens, then `GET /v1/organizations/cost_report?starting_at={T-30d}&limit=31&group_by[]=description` will not account for them (its `service_tier` enum is only `batch` / `standard` / `null`). Flag the discrepancy explicitly rather than letting the totals silently differ.
- **repair**: Print, do not run: annotate the cost dashboard to state that Priority Tier is excluded, and track priority token volume from the usage endpoint separately against the contracted commitment.
- **category**: Cost and usage
- **sources**: https://platform.claude.com/docs/en/manage-claude/usage-cost-api · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report

## web-search-spend-unnoticed

- **slug**: `web-search-spend-unnoticed`
- **title**: Web search is billing $10 per 1,000 searches unnoticed
- **symptom**: No error. `data[].results[].server_tool_use.web_search_requests` in the usage report is a large number, and the cost report contains rows with `cost_type: "web_search"` whose `amount` nobody has attributed to a feature.
- **mechanism**: The web search server tool is billed at **$10 per 1,000 searches** on top of standard token costs, and search results become input tokens both in the turn that fetched them and in every subsequent turn of the conversation — so a chatty agent pays for the same results repeatedly. Each search counts as one use regardless of how many results come back; errored searches are not billed. Because search is a `tools` entry rather than a distinct endpoint, it never appears as its own line in most homegrown dashboards.
- **detect**: Admin API key required. `GET /v1/organizations/usage_report/messages?starting_at= {T-30d}&bucket_width=1d&limit=31&group_by[]=api_key_id` and sum `results[].server_tool_use.web_search_requests` per key; multiply by $10/1,000 for the tool-fee estimate. Confirm against `GET /v1/organizations/cost_report?starting_at={T-30d}& limit=31&group_by[]=description`, filtering `data[].results[]` to `cost_type == "web_search"`.
- **repair**: Print, do not run: for the top keys by `web_search_requests`, recommend a `max_uses` cap on the tool definition and `allowed_domains` narrowing, then re-read the monthly search count.
- **category**: Cost and usage
- **sources**: https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report

## code-execution-hours-exceed-free-allowance

- **slug**: `code-execution-hours-exceed-free-allowance`
- **title**: Code execution container hours exceed the free 1,550
- **symptom**: No error. The cost report contains results with `cost_type: "code_execution"` (description `Code Execution Usage`) carrying a non-zero `amount`, which by definition means the free allowance is exhausted. Meanwhile the *usage* report shows nothing — code execution is not reported there at all.
- **mechanism**: Each organization gets **1,550 free container-hours per month**; beyond that, usage is billed at **$0.05 per hour, per container**, with a **5-minute minimum** per execution. Crucially, if files are attached to the request, execution time is billed **even if the tool is never called**, because the files are preloaded onto the container. So a route that attaches a dataset "just in case" accrues container time on every request. Code execution is free only when bundled with `web_search_20260209` or `web_fetch_20260209` or later.
- **detect**: Admin API key required. `GET /v1/organizations/cost_report?starting_at={T-30d}& ending_at={T}&limit=31&group_by[]=description&group_by[]=workspace_id`; filter `data[].results[]` to `cost_type == "code_execution"` and sum `amount` per `workspace_id`. Any non-zero total means the 1,550-hour allowance is spent. Do **not** look for this in the messages usage report — code execution is excluded from it.
- **repair**: Print, do not run: identify workspaces attaching files to requests that do not need code execution, and note that pairing code execution with the current web search/fetch tool versions removes the charge entirely.
- **category**: Cost and usage
- **sources**: https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/manage-claude/usage-cost-api · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report

## long-context-requests-unwatched

- **slug**: `long-context-requests-unwatched`
- **title**: Most tokens are spent in the 200k-1M context bucket
- **symptom**: No error. Grouping the usage report by `context_window` shows the `"200k-1M"` bucket holding a large and growing share of `uncached_input_tokens` — often with `cache_read_input_tokens` near zero in that same bucket.
- **mechanism**: A common belief is that crossing 200k input tokens triggers premium pricing. On current models it does **not**: for every model with a 1M-token context window, 1M is the default, no beta header is needed, and long-context requests bill at **standard** rates. What the `"200k-1M"` bucket actually reveals is context bloat — a conversation or agent loop resending a very large prefix on every turn. At $5 / MTok input on Opus 5, a 400k-token prefix is $2 per uncached call, and accuracy degrades as the window fills (context rot). The bucket is a size alarm, not a price alarm — except on retired models, where a 1M-context beta did carry a premium.
- **detect**: Admin API key required. `GET /v1/organizations/usage_report/messages?starting_at= {T-30d}&bucket_width=1d&limit=31&group_by[]=context_window&group_by[]=model` — the `context_window` field takes `"0-200k"`, `"200k-1M"`, or `null`. Compute the `"200k-1M"` share of `uncached_input_tokens`, and check `cache_read_input_tokens` in the same results: large long-context volume with no cache reads is the expensive combination. You can also filter directly with `context_window[]=200k-1M`.
- **repair**: Print, do not run: recommend server-side compaction or context editing for the routes generating 200k+ prefixes, and a `cache_control` breakpoint on the stable portion. Re-read the `context_window` split after the change.
- **category**: Cost and usage
- **sources**: https://platform.claude.com/docs/en/build-with-claude/context-windows · https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report

## us-inference-geo-premium-unnoticed

- **slug**: `us-inference-geo-premium-unnoticed`
- **title**: US inference geo silently bills at a 1.1x multiplier
- **symptom**: No error. The usage report grouped by `inference_geo` returns results with `inference_geo: "us"` carrying meaningful token volume, and the corresponding cost rows are ~10% higher per token than the `"global"` rows for the same model.
- **mechanism**: On Claude 4.6 and later models, `inference_geo: "us"` applies a **1.1x multiplier on every token pricing category** — input, output, cache writes, and cache reads alike. The parameter can be set per request *or* inherited from the workspace's `data_residency.default_inference_geo`, so a workspace configured for US residency applies the premium to all its traffic whether or not any caller asked for it. Models released before February 2026 do not support the parameter and report `"not_available"`.
- **detect**: Admin API key required. `GET /v1/organizations/usage_report/messages?starting_at= {T-30d}&bucket_width=1d&limit=31&group_by[]=inference_geo&group_by[]=workspace_id` — the `inference_geo` field takes `"global"`, `"us"`, `"not_available"`, or `null`. Multiply the `"us"` token totals by 0.1 of base rate for the premium estimate. Confirm the source with `GET /v1/organizations/workspaces` and read each workspace's `data_residency.default_inference_geo` and `data_residency.allowed_inference_geos`.
- **repair**: Print, do not run: for workspaces whose `default_inference_geo` is `us` without a compliance requirement, note the 1.1x premium and its monthly dollar value. Do not change residency configuration from an audit script — it is a compliance setting.
- **category**: Cost and usage
- **sources**: https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report · https://platform.claude.com/docs/en/api/admin-api/workspaces/list-workspaces

## fast-mode-premium-spend-hidden

- **slug**: `fast-mode-premium-spend-hidden`
- **title**: Fast mode is billing Opus at $10/$50 per MTok
- **symptom**: No error. Fast-mode usage is invisible by default: the `speed` dimension does not appear in the usage report unless you send the `fast-mode-2026-02-01` beta header, so the premium tokens are silently merged into the model's totals.
- **mechanism**: Fast mode (research preview, Claude Opus 5 and Opus 4.8 only) runs the same model faster at **$10 / MTok input and $50 / MTok output** — double the standard Opus rate — and the premium applies across the full context window. Prompt-caching and data-residency multipliers stack on top. Because `speed: "fast"` is a per-request parameter, one team can double the effective rate for their traffic without any organization-level configuration change, and the default usage report will not break it out.
- **detect**: Admin API key required **plus** the beta header. `GET /v1/organizations/ usage_report/messages?starting_at={T-30d}&bucket_width=1d&limit=31&group_by[]=speed& group_by[]=model&group_by[]=api_key_id` with `anthropic-beta: fast-mode-2026-02-01`. Results carry `speed` of `"fast"` or `"standard"`. You can also filter with `speeds[]=fast`. Without the beta header, both the `speed` group-by and the `speeds[]` filter are unavailable — an audit that omits it will report fast-mode spend as ordinary Opus spend.
- **repair**: Print, do not run: report the `api_key_id` values with non-zero `fast` tokens and the premium in dollars. Note that fast mode is unavailable with the Batch API and on Priority Tier, so it cannot be combined with the usual discounts.
- **category**: Cost and usage
- **sources**: https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/manage-claude/usage-cost-api · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report

## claude-code-edit-rejection-rate-high

- **slug**: `claude-code-edit-rejection-rate-high`
- **title**: Claude Code edit proposals are rejected more than accepted
- **symptom**: No error. In `GET /v1/organizations/usage_report/claude_code`, records show `tool_actions.edit_tool.rejected` comparable to or larger than `tool_actions.edit_tool.accepted`, while `model_breakdown[].estimated_cost.amount` for those actors is high.
- **mechanism**: Every rejected edit proposal was fully generated and fully billed — the tokens are spent whether or not the user takes the diff. A sustained low acceptance rate means the organization is paying Opus-tier output rates for work that is thrown away, and usually points at a missing project context file, an unclear task framing, or a model/effort mismatch rather than at the tool itself. The endpoint exposes accepted/rejected counts per tool (`edit_tool`, `multi_edit_tool`, `write_tool`, `notebook_edit_tool`), so the rate is directly computable: `accepted / (accepted + rejected)`.
- **detect**: Admin API key required. `GET /v1/organizations/usage_report/claude_code? starting_at=YYYY-MM-DD&limit=1000`, paging on `next_page` until `has_more` is false; repeat per day for the window. Per record compute the acceptance rate for each tool in `tool_actions`, and pair it with `core_metrics.num_sessions`, `core_metrics.lines_of_code.added` / `.removed`, `core_metrics.commits_by_claude_code`, `core_metrics.pull_requests_by_claude_code`, and total `model_breakdown[].estimated_cost.amount`. Data is aggregated daily in UTC and only records older than 1 hour are returned.
- **repair**: Print, do not run: name the actors with acceptance below your threshold and their daily estimated cost, and suggest the team review project setup (CLAUDE.md context, task scoping) for those repositories.
- **category**: Cost and usage
- **sources**: https://platform.claude.com/docs/en/manage-claude/claude-code-analytics-api · https://platform.claude.com/docs/en/manage-claude/analytics-api

## rate-limit-exceeded-429

- **slug**: `rate-limit-exceeded-429`
- **title**: Requests fail with 429 rate_limit_exceeded under burst load
- **symptom**: `429` `RateLimitError`, message `Rate limit reached for <model> in organization org-... on tokens per min (TPM): Limit N, Used M, Requested R.` Response carries `Retry-After` and the `x-ratelimit-*` header set. Failures cluster in bursts and disappear between them.
- **mechanism**: Limits apply at both organization and project level across six dimensions — RPM, RPD, TPM, TPD, IPM, and audio minutes per minute — and "rate limits can be hit across any of the options depending on what occurs first". A workload well under its TPM can still 429 on RPM if it makes many tiny calls, and long-context models like GPT-5.5 carry a *separate* rate limit for long-context requests.
- **detect**: Project read-only key → any lightweight call (e.g. `GET /v1/models`) and read the response headers `x-ratelimit-limit-requests`, `x-ratelimit-remaining-requests`, `x-ratelimit-reset-requests`, `x-ratelimit-limit-tokens`, `x-ratelimit-remaining-tokens`, `x-ratelimit-reset-tokens`, plus the project-scoped variants `x-ratelimit-limit-project-tokens`, `x-ratelimit-remaining-project-tokens`, `x-ratelimit-reset-project-tokens`. Admin-read key → `GET /v1/organization/projects/{project_id}/rate_limits` → `data[].model`, `max_requests_per_1_minute`, `max_tokens_per_1_minute`, and compare against observed peak load from `GET /v1/organization/usage/completions?bucket_width=1m&group_by[]=model`.
- **repair**: Implement exponential backoff with jitter and honour `Retry-After` (the official SDKs do this by default — check `max_retries` is not set to `0`). Where RPM is the binding dimension, batch prompts into fewer requests; where TPM binds, lower `max_output_tokens` to match expected response size, or move non-urgent work to the Batch API.
- **category**: Rate limits and retries
- **sources**: https://developers.openai.com/api/docs/guides/rate-limits · https://developers.openai.com/api/docs/guides/error-codes

## rate-limit-headers-near-exhaustion

- **slug**: `rate-limit-headers-near-exhaustion`
- **title**: x-ratelimit-remaining headers sit near zero before any 429
- **symptom**: No errors yet. `x-ratelimit-remaining-tokens` or `x-ratelimit-remaining-requests` is a small fraction of the matching `x-ratelimit-limit-*` value at steady state, and `x-ratelimit-reset-*` shows a short window. Latency creeps up as requests queue. The first traffic spike converts this into `429`.
- **mechanism**: The headers are the only forward-looking signal OpenAI gives — they are returned on *every* response, including successful ones, and reflect the remaining budget in the current window at organization or project scope. Most integrations never read them, so the headroom margin is invisible until it is gone.
- **detect**: Project read-only key → issue any request and record the ratio `x-ratelimit-remaining-tokens / x-ratelimit-limit-tokens` and `x-ratelimit-remaining-requests / x-ratelimit-limit-requests` at peak hour; alert below 0.2. Note which dimension is scarcest — token headroom and request headroom exhaust independently. If the project-scoped headers `x-ratelimit-limit-project-tokens` / `x-ratelimit-remaining-project-tokens` are present, the project ceiling is lower than the org ceiling and is the real constraint.
- **repair**: Print the observed limit/remaining pair and the binding dimension, then: request a tier increase, spread load with a client-side token-bucket sized to `x-ratelimit-limit-tokens`, or raise the project's limit via the Admin API `POST /v1/organization/projects/{project_id}/rate_limits/{rate_limit_id}` (write call — report only, do not execute).
- **category**: Rate limits and retries
- **sources**: https://developers.openai.com/api/docs/guides/rate-limits

## project-rate-limit-below-org

- **slug**: `project-rate-limit-below-org`
- **title**: A project's per-model rate limit is far below the org tier
- **symptom**: `429` `rate_limit_exceeded` on one project while other projects in the same organization run fine on the same model. The `x-ratelimit-limit-project-tokens` header on the failing project is much lower than `x-ratelimit-limit-tokens`.
- **mechanism**: Project-level rate limits are set independently of the organization's usage-tier limits and default lower in some setups. A staging project created for isolation (which the production-best-practices guide recommends) can end up with a throttle that follows the code into production if the project id is reused.
- **detect**: Admin-read key → `GET /v1/organization/projects?limit=100` → `data[].id`, `data[].name`, `data[].status`; then for each, `GET /v1/organization/projects/{project_id}/rate_limits` → `data[]` objects with `object: "project.rate_limit"`, `id`, `model`, `max_requests_per_1_minute`, `max_tokens_per_1_minute`, and optionally `max_images_per_1_minute`, `max_audio_megabytes_per_1_minute`, `max_requests_per_1_day`, `batch_1_day_max_input_tokens`. Compare the same `model` row across projects — an outlier low `max_tokens_per_1_minute` is the throttled project.
- **repair**: Print the project id, model, and the low `max_tokens_per_1_minute`/`max_requests_per_1_minute` values, and the exact admin call to raise it: `POST /v1/organization/projects/{project_id}/rate_limits/{rate_limit_id}` with `{"max_tokens_per_1_minute": <org value>}`. Do not execute.
- **category**: Rate limits and retries
- **sources**: https://developers.openai.com/api/docs/guides/rate-limits · https://openai-hd4n6.mintlify.app/api-reference/projects/list-project-rate-limits

## quota-exhausted-not-rate-limited

- **slug**: `quota-exhausted-not-rate-limited`
- **title**: 429 credit_balance_exhausted retried forever as a rate limit
- **symptom**: `429` with `code: "credit_balance_exhausted"` (historically `insufficient_quota`), message `Your organization has no prepaid credits remaining.` The SDK raises `RateLimitError` — the same class as a genuine throttle — so backoff logic retries it indefinitely. Traffic stops completely rather than degrading, and retry storms burn CPU for hours.
- **mechanism**: OpenAI overloads HTTP 429 for four distinct billing conditions alongside true throttling: `credit_balance_exhausted` (no prepaid credits), `organization_spend_limit_exceeded` (monthly org cap hit), `project_spend_limit_exceeded` (project cap hit), and `organization_usage_limit_exceeded` (OpenAI-assigned ceiling reached). None of these clear on retry; only adding credits or raising the limit fixes them. Retrying is not just useless, it is indistinguishable to naive code.
- **detect**: Admin-read key → `GET /v1/organization/costs?start_time=<start of month>&bucket_width=1d` and sum `data[].results[].amount.value`; compare against the tier's monthly usage limit (Free/Tier 1 $100, Tier 2 $500, Tier 3 $1,000, Tier 4 $5,000, Tier 5 $200,000). Approaching or at the cap predicts `organization_usage_limit_exceeded`. Also `GET /v1/organization/projects/{project_id}` and check the project's configured spend limit against `GET /v1/organization/costs?group_by[]=project_id`. A sharp cliff in `GET /v1/organization/usage/completions` `num_model_requests` to zero mid-billing-cycle is the live symptom.
- **repair**: Branch on `error.code` before retrying: retry only when `code` is absent or is a true throttle; on `credit_balance_exhausted`, `organization_spend_limit_exceeded`, `project_spend_limit_exceeded`, `organization_usage_limit_exceeded`, fail fast and page. Print the specific remedy per code — add prepaid credits, raise the org/project monthly spend limit, or request a higher approved usage limit from OpenAI.
- **category**: Rate limits and retries
- **sources**: https://developers.openai.com/api/docs/guides/error-codes · https://developers.openai.com/api/docs/guides/rate-limits

## usage-tier-too-low

- **slug**: `usage-tier-too-low`
- **title**: Org is stuck on a low usage tier with tight per-model limits
- **symptom**: Persistent `429` `rate_limit_exceeded` at modest traffic, plus `404` `model_not_found` on flagship models the org should be able to see. `x-ratelimit-limit-tokens` is small relative to the model's published tier-5 ceiling.
- **mechanism**: Tiers graduate on cumulative paid spend: Tier 1 at $5 paid, Tier 2 at $50, Tier 3 at $100, Tier 4 at $250, Tier 5 at $1,000, with monthly usage limits of $100 / $500 / $1,000 / $5,000 / $200,000 respectively. Newer flagship models are gated behind higher tiers, and a lower-tier key gets a `404` rather than a `403` — OpenAI returns "does not exist or you do not have access to it" deliberately so tier gating is indistinguishable from a typo.
- **detect**: Project read-only key → `GET /v1/models` and diff `data[].id` against the published model list; models documented as available but absent from your `data[]` are tier- or verification-gated. Read `x-ratelimit-limit-tokens` from the response headers and compare against the model's documented tier-5 TPM. Admin-read key → `GET /v1/organization/costs?start_time=<12 months ago>&bucket_width=1d`, sum `results[].amount.value` to infer cumulative paid spend and therefore the tier boundary you sit under.
- **repair**: Print the inferred tier, the next tier's threshold and the spend gap. Prepay credits to cross the threshold (Tier 2 at $50 paid, Tier 3 at $100, Tier 4 at $250, Tier 5 at $1,000) — graduation is automatic. Until then, pin to a model that `GET /v1/models` actually returns rather than one the docs advertise.
- **category**: Rate limits and retries
- **sources**: https://developers.openai.com/api/docs/guides/rate-limits · https://ofox.ai/blog/openai-api-model-not-found-errors-troubleshooting/

## flex-resource-unavailable-timeouts

- **slug**: `flex-resource-unavailable-timeouts`
- **title**: Flex tier returns 429 Resource Unavailable and times out at 10m
- **symptom**: Intermittent `429 Resource Unavailable` on requests sending `"service_tier": "flex"` — notably **not billed** when it happens. Separately, `408 Request Timeout` far more often than on standard processing, because the SDK default request timeout is 10 minutes and flex responses regularly exceed it.
- **mechanism**: Flex trades latency and availability for Batch-API-rate pricing. Capacity is best-effort, so `429 Resource Unavailable` means "no capacity right now", not "you exceeded a limit" — retrying with backoff genuinely helps, unlike the billing 429s. The docs recommend raising the client timeout from the 10-minute default to at least 15 minutes; the official SDKs auto-retry `408` exactly twice, which silently triples cost-free wall time before surfacing.
- **detect**: Admin-read key → `GET /v1/organization/costs?start_time=<7d ago>&bucket_width=1d&group_by[]=line_item` → Flex line items confirm flex is in use. `GET /v1/organization/usage/completions?start_time=<7d ago>&bucket_width=1h&group_by[]=model&group_by[]=project_id` → hours where `num_model_requests` is far below the job's expected volume indicate requests dying before completion. Project read-only key → in a live response, read the top-level `service_tier` field to confirm `"flex"` was actually served.
- **repair**: Raise the client timeout: `OpenAI(timeout=600.0)` → `OpenAI(timeout=900.0)` (15 minutes minimum per the flex guide). Add exponential backoff on `429 Resource Unavailable`, or fall back to `"service_tier": "auto"` when completion certainty matters more than cost. Keep flex only for evals, data enrichment and background jobs — never on a user-facing path.
- **category**: Rate limits and retries
- **sources**: https://developers.openai.com/api/docs/guides/flex-processing

## rate-limit-429-limiter-unidentified

- **slug**: `rate-limit-429-limiter-unidentified`
- **title**: 429s are retried blindly without reading which limit hit
- **symptom**: `429` with `"error": {"type": "rate_limit_error"}`. The message names which limit was exceeded and a `retry-after` header says how long to wait, but a handler that catches "429 → sleep(1) → retry" throws all of that away and cannot tell RPM starvation from token starvation.
- **mechanism**: There is no single TPM limit. Each model group carries three independent limiters — requests per minute (RPM), input tokens per minute (ITPM) and output tokens per minute (OTPM) — enforced by a token-bucket that refills continuously. Separate groups exist for the Message Batches API, the Token Counting API, the Files API, agent skills and web search; Managed Agents endpoints have their own 300 rpm (create) / 1,200 rpm (read) limits. Limits are per model, so different models can be saturated independently.
- **detect**: Response headers on any rate-limited call tell you which bucket is empty: `anthropic-ratelimit-requests-limit` / `-remaining` / `-reset`, `anthropic-ratelimit-input-tokens-limit` / `-remaining` / `-reset`, `anthropic-ratelimit-output-tokens-limit` / `-remaining` / `-reset` (all `-reset` values are RFC 3339), plus the aggregate `anthropic-ratelimit-tokens-*` triple which reports the **most restrictive** limit currently in effect. Read-only reconstruction: Admin API key → `GET /v1/organizations/rate_limits` returns each `model_group` with its configured `{type: "requests_per_minute" | "input_tokens_per_minute" | "output_tokens_per_minute", value}` pairs; compare against `GET /v1/organizations/usage_report/messages?bucket_width=1m&group_by[]=model` (1m buckets, up to 1,440) to see which of the three the traffic actually saturates.
- **repair**: Print: for each model group, the configured RPM/ITPM/OTPM and the observed 1-minute peak of each; name the binding limiter. Recommend logging the three `-remaining` headers and `retry-after` on every 429 rather than catching a broad `APIStatusError`. Do not change client code.
- **category**: Rate limits and retries
- **sources**: https://platform.claude.com/docs/en/api/rate-limits · https://platform.claude.com/docs/en/manage-claude/rate-limits-api · https://platform.claude.com/docs/en/manage-claude/usage-cost-api

## itpm-exhausted-uncached-input

- **slug**: `itpm-exhausted-uncached-input`
- **title**: ITPM runs out because uncached input is never cached
- **symptom**: `429 rate_limit_error` with `anthropic-ratelimit-input-tokens-remaining` at or near `0` while `anthropic-ratelimit-requests-remaining` is still healthy.
- **mechanism**: Only **uncached** input counts toward ITPM: `input_tokens` (tokens after the last cache breakpoint) and `cache_creation_input_tokens` count; `cache_read_input_tokens` does **not**, on every model except Claude Haiku 3.5 (marked † in the tier tables), which does count cache reads. So an 80% cache hit rate against a 2,000,000 ITPM limit lets you push 10,000,000 total input tokens/minute. Standard ITPM: Start 2,000,000 / Build 5,000,000 / Scale 10,000,000 for Opus 5, Opus 4.x, Sonnet 5, Sonnet 4.x and Haiku 4.5; Claude Fable 5 is much lower at 500,000 / 1,500,000 / 4,000,000. Note `input_tokens` is only the tail after the last breakpoint, so `total_input = cache_read + cache_creation + input_tokens`.
- **detect**: Admin API key: `GET /v1/organizations/usage_report/messages?bucket_width=1m&group_by[]=model` returns uncached input, cache-creation, cache-read and output tokens per minute; compute `(uncached + cache_creation)` per bucket and compare against `input_tokens_per_minute` from `GET /v1/organizations/rate_limits?model=<id>`. A cache-read share near zero on a workload with a stable system prompt is the tell. Response-side confirmation: `anthropic-ratelimit-input-tokens-remaining` (rounded to the nearest thousand) and `-reset`.
- **repair**: Print: per model group, the peak-minute uncached input against the ITPM ceiling, and the current cache-read share. Recommend `cache_control` on the stable prefix (tools → system → messages render order) and note the Haiku 3.5 exception if it is in the mix. Do not modify prompts.
- **category**: Rate limits and retries
- **sources**: https://platform.claude.com/docs/en/api/rate-limits · https://platform.claude.com/docs/en/manage-claude/usage-cost-api · https://platform.claude.com/docs/en/manage-claude/rate-limits-api

## otpm-exhausted

- **slug**: `otpm-exhausted`
- **title**: Output tokens per minute is the real ceiling, not RPM
- **symptom**: `429 rate_limit_error` with `anthropic-ratelimit-output-tokens-remaining` at `0` while both requests-remaining and input-tokens-remaining are comfortable. Teams tune concurrency against RPM and never move the needle.
- **mechanism**: OTPM is evaluated in real time against tokens actually generated. Crucially, "the `max_tokens` parameter does not factor into OTPM rate limit calculations, so there is no rate limit downside to setting a higher `max_tokens` value" — but thinking tokens *are* billed and counted as output, so adaptive thinking at high effort can saturate OTPM on a low request rate. Standard OTPM: Start 400,000 / Build 1,000,000 / Scale 2,000,000 for Opus 5, Opus 4.x, Sonnet 5, Sonnet 4.x, Haiku 4.5; Claude Fable 5 100,000 / 300,000 / 800,000. OTPM is roughly one fifth of ITPM at every tier, so any generation-heavy workload hits it first.
- **detect**: Admin API key: `GET /v1/organizations/usage_report/messages?bucket_width=1m&group_by[]=model` → output tokens per minute vs `output_tokens_per_minute` from `GET /v1/organizations/rate_limits`. Response-side: `anthropic-ratelimit-output-tokens-limit` / `-remaining` / `-reset`. Batch results are a second read-only corpus — stream `GET /v1/messages/batches/{id}/results` and sum `.result.message.usage.output_tokens`.
- **repair**: Print: peak output tokens/minute per model against the OTPM ceiling, and the effort setting in use if known. Suggest lowering `output_config.effort`, moving latency-tolerant work to the Message Batches API (separate limits, 50% cost), or requesting a limit increase. Do not change effort settings.
- **category**: Rate limits and retries
- **sources**: https://platform.claude.com/docs/en/api/rate-limits · https://platform.claude.com/docs/en/manage-claude/rate-limits-api · https://platform.claude.com/docs/en/build-with-claude/context-windows

## retry-after-header-ignored

- **slug**: `retry-after-header-ignored`
- **title**: Retries fire before retry-after elapses and fail again
- **symptom**: A burst of consecutive `429 rate_limit_error` responses in a tight cluster, each one burning an RPM slot. The docs are explicit: `retry-after` is "the number of seconds to wait until you can retry the request. **Earlier retries will fail.**"
- **mechanism**: The bucket refills continuously, so a retry before the stated delay is guaranteed to 429 again and pushes the reset further out. The official SDKs retry transient failures (408/409/429/5xx and connection errors) twice by default with exponential backoff and honor `retry-after`; hand-rolled clients, gateways and queue workers with a fixed `sleep(1)` do not. Note the SDK default also means wall-clock latency can reach `timeout × (max_retries + 1)`.
- **detect**: Workspace/project API key: a read-only probe loop against `GET /v1/models` (which counts against the org RPM limiter) will eventually return a 429 whose `retry-after` and `anthropic-ratelimit-requests-reset` you can record without generating a single token — that proves the headers reach your client and are not stripped by a proxy. Admin API key: `GET /v1/organizations/usage_report/messages?bucket_width=1m` — the report carries token sums and no request count (blind spot 3), so read the shape in token volume: a spike in one bucket followed by a flat next bucket is honored backoff; sustained saturation across consecutive buckets is ignored backoff.
- **repair**: Print: whether `retry-after` survives the proxy chain, the client's configured `max_retries` / backoff if discoverable, and the recommendation to use the SDK's built-in retry (or read `retry-after` and the matching `anthropic-ratelimit-*-reset` before sleeping). Flag any handler that catches a broad `APIStatusError` instead of a most-specific-first chain. Do not change retry config.
- **category**: Rate limits and retries
- **sources**: https://platform.claude.com/docs/en/api/rate-limits · https://platform.claude.com/docs/en/api/errors

## spend-cap-429-retried-forever

- **slug**: `spend-cap-429-retried-forever`
- **title**: A spend-cap 429 has no retry-after and never recovers
- **symptom**: `429` with `"error": {"type": "rate_limit_error", "message": "You have reached your API usage limits: your organization has crossed its monthly API usage threshold, set based on your organization's API tier. You will regain access on 2026-09-01 at 00:00 UTC.", "details": {"error_code": "enforced_spend_limit_reached"}}` — and **no `retry-after` header**. Retrying, including the SDKs' automatic retries, fails until access resumes.
- **mechanism**: Each tier carries a monthly spend cap: Start **$500**, Build **$1,000**, Scale **$200,000**; Custom tier has none. On reaching it, API usage pauses until 00:00 UTC on the first day of the next month unless a higher limit is granted. The error type is the same `rate_limit_error` as a real rate limit, so every generic 429 handler treats a billing stop as a transient blip and hammers a dead endpoint for the rest of the month.
- **detect**: Admin API key: `GET /v1/organizations/cost_report?starting_at=<first of month>&ending_at=<now>&group_by[]=workspace_id&group_by[]=description` returns month-to-date USD (decimal strings, in cents) — compare against your tier's cap. Note Priority Tier costs are excluded from the cost endpoint, so track those via `GET /v1/organizations/usage_report/messages?group_by[]=service_tier`. Response-side: the discriminator is `error.details.error_code == "enforced_spend_limit_reached"` plus the absence of `retry-after`.
- **repair**: Print: month-to-date spend, the tier cap, projected exhaustion date at the current burn rate, and the note that this 429 must be routed to a page/alert, not to the retry queue — the discriminator is `error.details.error_code`. Do not raise limits.
- **category**: Rate limits and retries
- **sources**: https://platform.claude.com/docs/en/api/rate-limits · https://platform.claude.com/docs/en/manage-claude/usage-cost-api · https://platform.claude.com/docs/en/api/errors

## self-set-spend-limit-400

- **slug**: `self-set-spend-limit-400`
- **title**: A self-set spend limit returns 400, not 429
- **symptom**: `400 invalid_request_error` whose message begins `You have reached your specified API usage limits` (or `You have reached your specified workspace API usage limits` for a workspace-scoped limit) and states when access resumes.
- **mechanism**: A spend limit you configure in Console below your tier's cap stops traffic with a **400**, not a 429 — a deliberate split from the tier spend cap. Error handlers that classify 400 as "permanent client bug, page the on-call engineer, log and drop the job" will misdiagnose a purely financial stop as a malformed request. The one exception: limits on the Claude Code workspace are checked separately and can instead return a 429 carrying a `retry-after` header.
- **detect**: Admin API key: `GET /v1/organizations/cost_report?starting_at=…&ending_at=…&group_by[]=workspace_id` for month-to-date spend per workspace, and `GET /v1/organizations/workspaces` to enumerate workspace ids. The configured self-set limit itself lives in Console (not exposed by the Admin API), so the API-side detection is the shape of the 400 body: match the message prefix `You have reached your specified`. Read the `anthropic-workspace-id` response header to know which workspace a key resolves to.
- **repair**: Print: each workspace's month-to-date spend, whether a 400 with the `You have reached your specified` prefix has been observed, and the recommendation to branch on that message prefix before treating a 400 as a code defect. Do not change limits.
- **category**: Rate limits and retries
- **sources**: https://platform.claude.com/docs/en/api/rate-limits · https://platform.claude.com/docs/en/api/errors · https://platform.claude.com/docs/en/manage-claude/usage-cost-api

## workspace-rate-limit-override-throttles

- **slug**: `workspace-rate-limit-override-throttles`
- **title**: A workspace override throttles far below the org limit
- **symptom**: `429 rate_limit_error` on one service while the org-level dashboard shows plenty of headroom. The `anthropic-ratelimit-tokens-*` headers report values far below the published tier numbers, because they surface the most restrictive limit in effect — the workspace one.
- **mechanism**: Workspaces can carry per-limiter overrides below the organization limit (the default workspace cannot). Organization-wide limits always apply even if workspace limits sum to more. A group absent from the workspace response has **no** override and inherits the org limit — it is not unlimited; likewise a limiter type absent from a present group's `limits[]` inherits.
- **detect**: Admin API key: `GET /v1/organizations/workspaces/{workspace_id}/rate_limits` returns only the overrides, and each limiter carries both `value` (the workspace override) and `org_limit` (the organization value, or `null` if none is configured) — the ratio is the throttle. `GET /v1/organizations/workspaces` for the ids; `GET /v1/organizations/rate_limits` for the inherited baseline. Any workspace/project key can read the `anthropic-workspace-id` response header on any call to learn which workspace it resolves to.
- **repair**: Print: per workspace and per limiter, `value` vs `org_limit` and the percentage; flag any override under ~25% of the org limit that is co-located with saturated traffic in the usage report. Note that overrides are Console-only (the Rate Limits API is read-only and cannot update them). Do not change limits.
- **category**: Rate limits and retries
- **sources**: https://platform.claude.com/docs/en/manage-claude/rate-limits-api · https://platform.claude.com/docs/en/api/rate-limits

## acceleration-limit-on-traffic-spike

- **slug**: `acceleration-limit-on-traffic-spike`
- **title**: A sudden traffic ramp trips acceleration-limit 429s
- **symptom**: `429 rate_limit_error` at usage levels visibly **below** the published tier limits, right after a launch, a backfill, or a cron fan-out.
- **mechanism**: Two separate effects. First, acceleration limits: "you might also encounter 429 errors because of acceleration limits on the API if your organization has a sharp increase in usage" — the fix is to ramp gradually and keep patterns consistent. Second, sub-minute enforcement: "a rate of 60 requests per minute (RPM) might be enforced as 1 request per second", so a burst of 60 requests in one second trips a limit that a per-minute counter says is fine. New organizations may also start in the **Evaluation tier**, with limits below the standard tables while account history is established.
- **detect**: Admin API key: `GET /v1/organizations/usage_report/messages?bucket_width=1m` (default 60 buckets, max 1,440) — a step change between adjacent minutes is the acceleration signature; compare each minute's peak against `GET /v1/organizations/rate_limits`. If the peak minute is well under the configured limit and 429s still occurred, the cause is acceleration or sub-minute bursting, not the headline number. Data lands within ~5 minutes; poll no more than once per minute for sustained use.
- **repair**: Print: the observed minute-over-minute ramp factor, the configured limits, and the recommendation to ramp gradually and spread bursts across the minute (client-side pacing or a queue). Note that if the org is on the Evaluation tier the published tables do not apply. Do not adjust traffic.
- **category**: Rate limits and retries
- **sources**: https://platform.claude.com/docs/en/api/rate-limits · https://platform.claude.com/docs/en/manage-claude/usage-cost-api · https://platform.claude.com/docs/en/api/errors

## assistants-api-already-shut-down

- **slug**: `assistants-api-already-shut-down`
- **title**: Assistants API was shut down on 2026-08-26 and now 404s
- **symptom**: Every call to `/v1/assistants`, `/v1/threads`, `/v1/threads/{id}/runs` returns `404` `invalid_request_error`; SDKs raise `NotFoundError`. Previously-working `OpenAI-Beta: assistants=v2` traffic stopped. In the Admin usage API the `num_model_requests` for the app's project drops to zero on 2026-08-26.
- **mechanism**: Announced 2025-08-20 with a shutdown date of 2026-08-26. The Assistants API (assistants, threads, runs, run steps) was replaced by the Responses API plus the Conversations API. As of today (2026-08-30) the shutdown date has already passed.
- **detect**: Project read-only key → `GET /v1/assistants?limit=1`; a `200` with `object: "list"` means the org still has grace access, a `404`/`invalid_request_error` confirms shutdown. Cross-check with admin-read key: `GET /v1/organization/usage/completions?start_time=<30d ago>&bucket_width=1d&group_by[]=project_id` and look for a project whose `results[].num_model_requests` collapses to `0` after `2026-08-26`.
- **repair**: Migrate assistants/threads/runs to `POST /v1/responses` with `conversation: {id}` from `POST /v1/conversations`. Replace `client.beta.threads.runs.create(...)` with `client.responses.create(model=..., conversation=conv.id, input=...)`. Drop the `OpenAI-Beta: assistants=v2` header entirely.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations

## model-past-shutdown-date

- **slug**: `model-past-shutdown-date`
- **title**: A model id in use is past its published shutdown date
- **symptom**: `404` `invalid_request_error` with `code: "model_not_found"` and message `The model \`<id>\` does not exist or you do not have access to it.` Before shutdown the same id worked; after shutdown every request for it fails identically to a typo.
- **mechanism**: OpenAI retires model snapshots on a published schedule. After the shutdown date the id is removed from routing and returns the same 404 as a nonexistent model — there is no distinct "retired" error code, so the failure is indistinguishable from a misspelling unless you know the calendar.
- **detect**: Project read-only key → `GET /v1/models` and inspect each `data[].id` and `data[].shutdown_date`. Any id whose `shutdown_date` is non-null and earlier than now is already dead. Also `GET /v1/models/{model}` for each model id your org actually used — pull that list with an admin-read key via `GET /v1/organization/usage/completions?start_time=<90d ago>&bucket_width=1d&group_by[]=model` and read `data[].results[].model`; any model appearing in usage but absent from `GET /v1/models` `data[].id` is retired or unavailable.
- **repair**: Replace the retired id with its documented successor and pin the new snapshot, e.g. `model="o4-mini"` → `model="gpt-5.6-terra"`, `model="gpt-4-turbo"` → `model="gpt-5.6-sol"`. Print the exact one-line diff for each call site.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations · https://developers.openai.com/api/docs/api-reference/models

## shutdown-date-approaching

- **slug**: `shutdown-date-approaching`
- **title**: A model in production has a shutdown date under 90 days out
- **symptom**: Nothing yet — calls succeed with `200`. The only signal is `GET /v1/models/{model}` returning a non-null `shutdown_date` in the near future. The failure arrives as a hard `404` `model_not_found` on the shutdown date with no warning in the response body beforehand.
- **mechanism**: OpenAI publishes shutdown dates roughly 3–6 months ahead but does not add a deprecation warning header or a `warnings` array to successful inference responses. Teams that pin snapshots (correctly) get no runtime notice at all until the id disappears.
- **detect**: Project read-only key → for each model id the org used in the last 90 days, `GET /v1/models/{model}` → read `shutdown_date`. Flag any where `shutdown_date - now < 90 days`. Get the in-use model list with an admin-read key: `GET /v1/organization/usage/completions?start_time=<90d ago>&bucket_width=1d&group_by[]=model` → `data[].results[].model`. Sort flagged models by descending `num_model_requests` so the noisiest migration comes first.
- **repair**: Schedule the swap now. Print `model="<current>" # shutdown_date=<date>` → `model="<replacement>"` per the deprecations table, and note that a pinned replacement snapshot avoids silent behavior change on cutover.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations · https://developers.openai.com/api/docs/api-reference/models

## legacy-completions-endpoint-sunset

- **slug**: `legacy-completions-endpoint-sunset`
- **title**: /v1/completions models all shut down 2026-09-28
- **symptom**: Today: `200` from `POST /v1/completions`. On 2026-09-28: `404` `invalid_request_error` `model_not_found` for `gpt-3.5-turbo-instruct`, `babbage-002`, `davinci-002`, and every `ft-babbage-002`/`ft-davinci-002` fine-tune. Since these are the last models that serve the legacy text-completion endpoint, `/v1/completions` becomes unusable.
- **mechanism**: Announced 2025-09-26. `gpt-3.5-turbo-instruct`, `babbage-002`, `davinci-002` and `gpt-3.5-turbo-1106` all shut down 2026-09-28, recommended replacement `gpt-5.6-terra`. The old `text-davinci-*` / `text-*-001` InstructGPT family and the base `ada`/`babbage`/`curie`/`davinci` models were already killed on 2024-01-04. This is under 30 days away as of 2026-08-30.
- **detect**: Project read-only key → `GET /v1/models/gpt-3.5-turbo-instruct`, `GET /v1/models/babbage-002`, `GET /v1/models/davinci-002` → confirm `shutdown_date` = `2026-09-28`. Admin-read key → `GET /v1/organization/usage/completions?start_time=<30d ago>&bucket_width=1d&group_by[]=model&group_by[]=project_id`; any bucket whose `results[].model` is one of those ids (or starts with `ft:babbage-002`/`ft:davinci-002`) is live traffic that dies in weeks.
- **repair**: Move off the completions endpoint entirely: `POST /v1/completions` with `{"model":"gpt-3.5-turbo-instruct","prompt": p}` → `POST /v1/responses` with `{"model":"gpt-5.6-terra","input": p}`. Note the prompt must be re-tested — instruct-style prompts behave differently on a chat/reasoning model.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations

## legacy-gpt-snapshots-october-2026

- **slug**: `legacy-gpt-snapshots-october-2026`
- **title**: gpt-3.5-turbo, gpt-4 and gpt-4-turbo shut down 2026-10-23
- **symptom**: Calls succeed until 2026-10-23, then `404` `model_not_found`. Affected ids: `gpt-3.5-turbo`, `gpt-3.5-turbo-0125`, `gpt-4`, `gpt-4-0613`, `gpt-4-1106-preview`, `gpt-4-turbo`, `gpt-4-turbo-2024-04-09`, `gpt-4o-2024-05-13`, `gpt-4.1-nano`, `gpt-4.1-nano-2025-04-14`.
- **mechanism**: Announced 2026-04-22 with a 2026-10-23 shutdown. `gpt-3.5-turbo` → `gpt-5.6-terra`; `gpt-4`/`gpt-4-turbo`/`gpt-4o-2024-05-13` → `gpt-5.6-sol`; `gpt-4.1-nano` → `gpt-5.6-luna`. The `gpt-3.5-turbo` and `gpt-4` bare aliases die with their snapshots, so alias users are not spared.
- **detect**: Project read-only key → `GET /v1/models` → filter `data[]` where `id` matches `^(gpt-3\.5-turbo|gpt-4($|-)|gpt-4-turbo|gpt-4o-2024-05-13|gpt-4\.1-nano)` and `shutdown_date == "2026-10-23"`. Admin-read key → `GET /v1/organization/usage/completions?start_time=<7d ago>&bucket_width=1d&group_by[]=model` → any of those ids present in `results[].model` is live traffic.
- **repair**: `model="gpt-3.5-turbo"` → `model="gpt-5.6-terra"`; `model="gpt-4"` / `"gpt-4-turbo"` / `"gpt-4o-2024-05-13"` → `model="gpt-5.6-sol"`; `model="gpt-4.1-nano"` → `model="gpt-5.6-luna"`. Warn that the replacements are reasoning-capable and will reject `temperature` and `max_tokens` (see `reasoning-model-rejects-max-tokens`).
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations

## o-series-reasoning-models-retiring

- **slug**: `o-series-reasoning-models-retiring`
- **title**: o1, o3-mini and o4-mini all shut down 2026-10-23
- **symptom**: `404` `model_not_found` after 2026-10-23 for `o1`, `o1-2024-12-17`, `o1-pro`, `o1-pro-2025-03-19`, `o3-mini`, `o3-mini-2025-01-31`, `o4-mini`, `o4-mini-2025-04-16`, `ft-o4-mini-2025-04-16`. `o1-preview` (2025-07-28) and `o1-mini` (2025-10-27) are already gone; `o3-deep-research` and `o4-mini-deep-research` died 2026-07-23.
- **mechanism**: Announced 2026-04-22. The whole o-series is collapsing into the GPT-5.6 family: `o1`/`o3-mini`/`o1-pro` → `gpt-5.6-sol` (with `reasoning.mode: "pro"` for the pro variants), `o4-mini` → `gpt-5.6-terra`. `o3-2025-04-16` and `o3-pro-2025-06-10` follow on 2026-12-11.
- **detect**: Project read-only key → `GET /v1/models` → any `data[].id` matching `^(o1|o3|o4)` with a non-null `shutdown_date`. Confirm per-model with `GET /v1/models/o4-mini` → `shutdown_date`. Admin-read key → `GET /v1/organization/usage/completions?start_time=<30d ago>&bucket_width=1d&group_by[]=model` for live o-series traffic. A fine-tuned o4-mini shows as `ft:o4-mini-2025-04-16:...` — also check `GET /v1/fine_tuning/jobs?limit=100` → `data[].fine_tuned_model` and `data[].model`.
- **repair**: `model="o4-mini"` → `model="gpt-5.6-terra"`; `model="o1"` / `"o3-mini"` → `model="gpt-5.6-sol"`; `model="o1-pro"` → `model="gpt-5.6-sol"` plus `reasoning={"mode":"pro"}`. Fine-tunes must be retrained — the weights do not migrate.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations

## gpt5-snapshots-shutdown-december

- **slug**: `gpt5-snapshots-shutdown-december`
- **title**: Pinned gpt-5-2025-08-07 snapshots shut down 2026-12-11
- **symptom**: Works today, `404` `model_not_found` on 2026-12-11 for `gpt-5-2025-08-07`, `gpt-5-mini-2025-08-07`, `gpt-5-nano-2025-08-07`, `gpt-5-pro-2025-10-06`, `o3-2025-04-16`, `o3-pro-2025-06-10`. The `-chat-latest` and `-codex` variants of the same generation (`gpt-5-chat-latest`, `gpt-5-codex`, `gpt-5.1-codex`, `gpt-5.2-codex`) already died 2026-07-23, and `gpt-5.2-chat-latest`/`gpt-5.3-chat-latest` died 2026-08-10.
- **mechanism**: Announced 2026-06-11. Teams that did the right thing and pinned `gpt-5-2025-08-07` are hit here — pinning buys stability but not permanence, and the snapshot's retirement is silent until the date.
- **detect**: Project read-only key → `GET /v1/models/gpt-5-2025-08-07` → `shutdown_date` = `2026-12-11`. Sweep with `GET /v1/models` → any `data[].id` starting `gpt-5-` or `gpt-5.1`/`gpt-5.2`/`gpt-5.3` with non-null `shutdown_date`. Admin-read key → `GET /v1/organization/usage/completions?start_time=<7d ago>&bucket_width=1d&group_by[]=model` for which of them still carry traffic.
- **repair**: `model="gpt-5-2025-08-07"` → `model="gpt-5.6-sol"`; `"gpt-5-mini-2025-08-07"` → `"gpt-5.6-terra"`; `"gpt-5-nano-2025-08-07"` → `"gpt-5.6-luna"`; `"gpt-5-pro-2025-10-06"` / `"o3-pro-2025-06-10"` → `"gpt-5.6-sol"` with `reasoning={"mode":"pro"}`.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations

## floating-alias-snapshot-drift

- **slug**: `floating-alias-snapshot-drift`
- **title**: Unpinned model alias silently repoints to a new snapshot
- **symptom**: No error. Output quality, latency, token counts and cost per call change overnight with no deploy. `system_fingerprint` in the Chat Completions response changes value; token usage per request shifts in the Admin usage API; eval scores move. In the worst case a prompt that relied on a quirk of the old snapshot starts producing malformed structured output.
- **mechanism**: Bare aliases like `gpt-5.6` (which points at GPT-5.6 Sol) and any `*-latest` alias are repointed by OpenAI without notice. The alias is stable; the weights behind it are not. `system_fingerprint` is the documented identifier for "the current combination of model weights, infrastructure, and other configuration" and changes when OpenAI changes what is serving you.
- **detect**: Project read-only key → `GET /v1/models` → compare the set of `data[].id` values against a stored baseline; a bare alias present alongside newly-appeared dated snapshots (`<alias>-YYYY-MM-DD`) indicates alias-vs-snapshot divergence. Admin-read key → `GET /v1/organization/usage/completions?start_time=<30d ago>&bucket_width=1d&group_by[]=model` → any `results[].model` that is an unpinned alias (no trailing date, or ending `-latest`) is unpinned production traffic. Track step changes in `results[].output_tokens / results[].num_model_requests` (mean output tokens per request) across days as the drift symptom.
- **repair**: Pin the snapshot: `model="gpt-5.6"` → `model="gpt-5.6-sol"` and, where a dated snapshot exists in `GET /v1/models`, pin that instead. Add a scheduled `GET /v1/models/{pinned}` check on `shutdown_date` so pinning does not become entry `model-past-shutdown-date`.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/api-reference/models · https://cookbook.openai.com/examples/reproducible_outputs_with_the_seed_parameter

## dalle-models-removed

- **slug**: `dalle-models-removed`
- **title**: dall-e-2 and dall-e-3 were shut down on 2026-05-12
- **symptom**: `POST /v1/images/generations` with `"model":"dall-e-3"` returns `404` `invalid_request_error` `model_not_found`. Any code still defaulting to `dall-e-2` (the historical default when `model` was omitted) fails the same way.
- **mechanism**: Announced 2025-11-14, shut down 2026-05-12, replaced by the `gpt-image-*` family. Image code paths are often lightly exercised (avatar generation, OG images) so the breakage can sit unnoticed for months.
- **detect**: Project read-only key → `GET /v1/models/dall-e-3` → expect `404`; `GET /v1/models` → confirm no `data[].id` starting `dall-e`. Admin-read key → `GET /v1/organization/usage/images?start_time=<90d ago>&bucket_width=1d&group_by[]=model` → a model id of `dall-e-2`/`dall-e-3` with `num_model_requests > 0` followed by a drop to zero is a broken image path.
- **repair**: `{"model":"dall-e-3", "size":"1024x1024", "response_format":"b64_json"}` → `{"model":"gpt-image-2", "size":"1024x1024"}`. Note `gpt-image-*` always returns base64 and does not accept `response_format`, so the response parser must change too.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations

## gpt-image-generation-churn

- **slug**: `gpt-image-generation-churn`
- **title**: gpt-image-1 dies 2026-10-23, gpt-image-1.5/mini on 2026-12-01
- **symptom**: Image generation returns `404` `model_not_found` after the cutover date. `gpt-image-1` shuts down 2026-10-23 (announced 2026-04-22); `gpt-image-1-mini`, `gpt-image-1.5` and `chatgpt-image-latest` shut down 2026-12-01 (announced 2026-06-02). All three route to `gpt-image-2`.
- **mechanism**: The image model line has turned over three times in under a year. Teams that migrated off DALL·E onto `gpt-image-1` in May are already on a model that dies in October, and the `-mini` cost-optimisation many picked in between dies in December.
- **detect**: Project read-only key → `GET /v1/models/gpt-image-1` and `GET /v1/models/gpt-image-1-mini` → read `shutdown_date` (`2026-10-23` and `2026-12-01`). Admin-read key → `GET /v1/organization/usage/images?start_time=<30d ago>&bucket_width=1d&group_by[]=model&group_by[]=project_id` → live `results[].model` values in that set, with `results[].images` counts to size the migration.
- **repair**: `model="gpt-image-1"` / `"gpt-image-1-mini"` / `"gpt-image-1.5"` / `"chatgpt-image-latest"` → `model="gpt-image-2"`. Re-check `size` and `quality` enum values against the new model before shipping.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations

## sora-videos-api-no-replacement

- **slug**: `sora-videos-api-no-replacement`
- **title**: Videos API and all Sora 2 models shut down 2026-09-24
- **symptom**: `POST /v1/videos` and `GET /v1/videos/{id}` return `404` after 2026-09-24; `sora-2`, `sora-2-pro`, `sora-2-2025-10-06`, `sora-2-2025-12-08`, `sora-2-pro-2025-10-06` all return `404` `model_not_found`. The deprecations table lists **no replacement** for any of them.
- **mechanism**: Announced 2026-03-24. Unlike model retirements this removes a whole capability from the API — there is no successor model to swap to, so any product feature built on it must be rearchitected or dropped. Under 30 days away as of 2026-08-30.
- **detect**: Project read-only key → `GET /v1/models/sora-2` → `shutdown_date` = `2026-09-24`; `GET /v1/videos?limit=1` → a `200` list confirms the endpoint is still live. Admin-read key → `GET /v1/organization/costs?start_time=<30d ago>&bucket_width=1d&group_by[]=line_item` and look for video line items still accruing spend.
- **repair**: No in-API fix exists. Print: remove the `/v1/videos` code path and the `sora-2*` model constants; the feature needs a third-party video provider or removal from the product. Flag any customer-facing copy promising video generation.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations

## audio-realtime-models-deprecated

- **slug**: `audio-realtime-models-deprecated`
- **title**: gpt-realtime and gpt-audio families shut down 2027-01-20
- **symptom**: Realtime sessions and audio completions fail with `404` `model_not_found` after 2027-01-20 for `gpt-realtime`, `gpt-realtime-mini`, `gpt-audio`, `gpt-audio-mini`, `gpt-4o-realtime`, `gpt-4o-mini-realtime`, `gpt-4o-audio`, `gpt-4o-mini-audio`, `gpt-4o-mini-transcribe-2025-03-20`. Separately, the `OpenAI-Beta: realtime=v1` header and the `gpt-4o-*-realtime-preview`/`gpt-4o-*-audio-preview` models were already shut down on 2026-05-12 and 2026-05-07 — those fail **today**.
- **mechanism**: Announced 2026-07-20 for the 2027-01-20 wave. Realtime went GA in 2025 and the beta header path was retired 2026-05-12; anything still sending `OpenAI-Beta: realtime=v1` is already broken. Replacements: `gpt-realtime-2.1`, `gpt-realtime-2.1-mini`, `gpt-audio-1.5`, `gpt-4o-mini-transcribe-2025-12-15`.
- **detect**: Project read-only key → `GET /v1/models` → filter `data[].id` matching `realtime|audio|transcribe` and read `shutdown_date`; `GET /v1/models/gpt-4o-realtime-preview` returning `404` confirms the already-dead preview line. Admin-read key → `GET /v1/organization/usage/audio_speeches` and `GET /v1/organization/usage/audio_transcriptions` with `?start_time=<30d ago>&bucket_width=1d&group_by[]=model` → live `results[].model` values in the deprecated set.
- **repair**: Remove the `OpenAI-Beta: realtime=v1` header (GA needs no beta header). `model="gpt-realtime"` → `"gpt-realtime-2.1"`; `"gpt-realtime-mini"` → `"gpt-realtime-2.1-mini"`; `"gpt-audio"` / `"gpt-4o-audio"` / `"gpt-audio-mini"` → `"gpt-audio-1.5"`; `"gpt-4o-mini-transcribe-2025-03-20"` → `"gpt-4o-mini-transcribe-2025-12-15"`.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations

## prompts-evals-agentbuilder-sunset

- **slug**: `prompts-evals-agentbuilder-sunset`
- **title**: /v1/prompts, Evals API and Agent Builder close 2026-11-30
- **symptom**: `404` on `/v1/prompts/*` and on the Evals endpoints after 2026-11-30. Before then, calls that pass `prompt: {"id": "pmpt_...", "version": "N"}` to `/v1/responses` succeed; afterwards they fail as invalid requests because the referenced prompt object no longer resolves.
- **mechanism**: Announced 2026-06-03. Reusable Prompts (server-stored prompt templates), the Evals dashboard/API, and Agent Builder are all shutting down on 2026-11-30. The failure mode is nastier than a model retirement because the prompt *content* lives on OpenAI's side — if it is not exported before the date, the text is gone.
- **detect**: Project read-only key → `GET /v1/prompts?limit=100` → a non-empty `data[]` means the org has stored prompts that must be exported; record `data[].id` and each version's content now. Admin-read key → `GET /v1/organization/usage/completions?start_time=<7d ago>&bucket_width=1d&group_by[]=project_id` to identify which projects are still routing through them. Also `GET /v1/evals?limit=100` → non-empty `data[]` means eval definitions need exporting.
- **repair**: Export every prompt version to source control now, then inline it: `responses.create(prompt={"id":"pmpt_abc","version":"3"})` → `responses.create(instructions=PROMPT_V3, input=...)`. Migrate eval suites to Promptfoo (OpenAI's named replacement); replace Agent Builder flows with the Agents SDK.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations

## fine-tuning-jobs-blocked

- **slug**: `fine-tuning-jobs-blocked`
- **title**: Fine-tuning stops accepting new jobs from 2027-01-06
- **symptom**: Today: fine-tuning works, but inactive organizations already face restrictions on new jobs as of 2026-07-02. From 2027-01-06 `POST /v1/fine_tuning/jobs` is rejected for all orgs. Existing fine-tunes keep serving inference only until their **base** model is deprecated — and every current fine-tunable base (`ft-gpt-3.5-turbo`, `ft-gpt-4`, `ft-gpt-4.1-nano-2025-04-14`, `ft-babbage-002`, `ft-davinci-002`, `ft-o4-mini-2025-04-16`) shuts down 2026-10-23, before the job cutoff even arrives.
- **mechanism**: Announced 2026-05-07. The two dates interact badly: the base models your existing fine-tunes sit on die on 2026-10-23, and the window to retrain onto a newer base closes 2027-01-06. An org that discovers the 404 in October has roughly ten weeks to retrain everything, permanently.
- **detect**: Project read-only key → `GET /v1/fine_tuning/jobs?limit=100` → `data[].fine_tuned_model`, `data[].model` (the base), `data[].status`, `data[].created_at`. Any `data[].model` whose `GET /v1/models/{base}` returns a `shutdown_date` of `2026-10-23` is a fine-tune with a dying base. Admin-read key → `GET /v1/organization/usage/completions?start_time=<30d ago>&bucket_width=1d&group_by[]=model` → `results[].model` values starting `ft:` show which fine-tunes carry real traffic.
- **repair**: Print each `fine_tuned_model` id, its base, and the base's shutdown date. Retrain onto a supported base before 2027-01-06: `ft-gpt-3.5-turbo` / `ft-babbage-002` / `ft-davinci-002` / `ft-o4-mini-2025-04-16` → `gpt-5.6-terra`; `ft-gpt-4` → `gpt-5.6-sol`; `ft-gpt-4.1-nano-2025-04-14` → `gpt-5.6-luna`. Where the fine-tune only encoded formatting, evaluate replacing it with prompting plus structured outputs instead.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations

## text-moderation-model-retired

- **slug**: `text-moderation-model-retired`
- **title**: text-moderation-* models were shut down on 2025-10-27
- **symptom**: `POST /v1/moderations` with `"model": "text-moderation-latest"`, `"text-moderation-stable"` or `"text-moderation-007"` returns `404` `model_not_found`. Because moderation calls are often fire-and-forget with errors swallowed, the practical symptom is that **moderation silently stops running** — unsafe content flows through to the model or to users with no alert.
- **mechanism**: Announced 2025-04-28, shut down 2025-10-27, replaced by `omni-moderation`. `text-moderation-latest` was the historical default, so code that never named a model may also be affected. The safety-critical failure mode is a `try/except: pass` around the moderation call, which converts a hard 404 into an invisible policy gap.
- **detect**: Project read-only key → `GET /v1/models/text-moderation-latest` → expect `404`; `GET /v1/models` → confirm `omni-moderation-latest` is present in `data[].id` and no `text-moderation-*` id is. Admin-read key → `GET /v1/organization/usage/moderations?start_time=<90d ago>&bucket_width=1d&group_by[]=model` → `num_model_requests` dropping to zero, or requests attributed to a `text-moderation-*` id, both confirm a dead moderation path.
- **repair**: `model="text-moderation-latest"` → `model="omni-moderation-latest"`. Remove any bare `except: pass` around the moderation call so a future model retirement fails loudly instead of disabling moderation. `omni-moderation` accepts images as well as text, so the input shape can be widened at the same time.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations

## legacy-embeddings-and-endpoints-dead

- **slug**: `legacy-embeddings-and-endpoints-dead`
- **title**: First-gen embeddings and /v1/edits have been dead since 2024
- **symptom**: `404` on `POST /v1/edits`, `POST /v1/fine-tunes`, `POST /v1/engines/*`, `/v1/search`, `/v1/classifications`, `/v1/answers`; `404` `model_not_found` for every `text-similarity-*`, `text-search-*`, `code-search-*` (ada/babbage/curie/davinci) embedding model and for `text-davinci-edit-001` / `code-davinci-edit-001`. Vector stores populated with these embeddings cannot be extended — new documents cannot be embedded in the same space as the existing index.
- **mechanism**: First-generation embeddings and the edits/search/classifications/answers endpoints were shut down 2024-01-04 (legacy `/v1/engines`, `/v1/search`, `/v1/classifications`, `/v1/answers` back on 2022-12-03; `/v1/fine-tunes` on 2024-01-04). Recommended replacement for the embedding family is `text-embedding-3-small`. Because embeddings from different models are not comparable, an index built on a retired model is effectively frozen: retrieval still works over stored vectors, but nothing new can be added.
- **detect**: Project read-only key → `GET /v1/models/text-search-ada-doc-001` → expect `404`; `GET /v1/models` → confirm no `text-similarity-*`/`text-search-*`/`code-search-*` ids in `data[]` and that `text-embedding-3-small` is present. `GET /v1/vector_stores?limit=100` → `data[].id`, `data[].file_counts`, `data[].last_active_at`; a store with a stale `last_active_at` and nonzero `file_counts.completed` is a frozen index. Admin-read key → `GET /v1/organization/usage/embeddings?start_time=<90d ago>&bucket_width=1d&group_by[]=model` → any retired embedding id, or a drop to zero, confirms it.
- **repair**: `POST /v1/edits` → `POST /v1/responses`; `POST /v1/fine-tunes` → `POST /v1/fine_tuning/jobs`; `/v1/engines/{id}` → `/v1/models/{id}`. For embeddings, re-embed the whole corpus with `model="text-embedding-3-small"` into a **new** index — mixing embedding spaces silently degrades retrieval rather than erroring, so partial migration is worse than none.
- **category**: Models and deprecations
- **sources**: https://developers.openai.com/api/docs/deprecations

## retired-model-id-still-in-code

- **slug**: `retired-model-id-still-in-code`
- **title**: Retired model id in code fails every call with 404
- **symptom**: HTTP `404` with `"error": {"type": "not_found_error", "message": "The requested resource could not be found."}` on every request that names the id. The SDKs raise the typed 404 class (`anthropic.NotFoundError`, `Anthropic::Errors::NotFoundError`, `com.anthropic.errors.NotFoundException`, or `*anthropic.Error` with `StatusCode == 404` in Go).
- **mechanism**: Anthropic retires models on a published schedule and the id disappears from the API on the retirement date; "Requests to models past the retirement date will fail." Already retired on the Claude API: `claude-opus-4-1-20250805` (Aug 5, 2026), `claude-opus-4-20250514` and `claude-sonnet-4-20250514` (June 15, 2026), `claude-3-haiku-20240307` (Apr 20, 2026), `claude-3-7-sonnet-20250219` and `claude-3-5-haiku-20241022` (Feb 19, 2026), `claude-3-opus-20240229` (Jan 5, 2026), `claude-3-5-sonnet-20240620` and `claude-3-5-sonnet-20241022` (Oct 28, 2025), `claude-2.0`, `claude-2.1`, `claude-3-sonnet-20240229` (July 21, 2025), `claude-1.0`/`1.1`/`1.2`/`1.3` and `claude-instant-1.0`/`1.1`/`1.2` (Nov 6, 2024). A hard-coded id in a config file, a fallback branch, or a batch `params` block outlives the migration of the main call path.
- **detect**: Workspace/project API key: `GET /v1/models/{model_id}` for every model string you can find in config; a retired or unknown id returns `404 not_found_error`, a live one returns a `ModelInfo` object. Enumerate what is live with `GET /v1/models?limit=1000` and diff `data[].id` against your strings. Admin API key (`sk-ant-admin01-...`): `GET /v1/organizations/usage_report/messages?starting_at=…&ending_at=…&group_by[]=model&bucket_width=1d` shows whether any traffic is still being attributed to the id (retired ids stop appearing because the calls fail, so an id that vanished from the report on its exact retirement date is the fingerprint).
- **repair**: Print: the retired id, its retirement date, the recommended replacement from the deprecation table (`claude-opus-4-8` for the Opus 4/4.1 line, `claude-sonnet-4-6` for Sonnet 3.x/4, `claude-haiku-4-5-20251001` for the Haiku/Instant line), and every config key or file path that still holds the old string. Do not edit or send a test message.
- **category**: Models and deprecations
- **sources**: https://platform.claude.com/docs/en/about-claude/model-deprecations · https://platform.claude.com/docs/en/api/models · https://platform.claude.com/docs/en/api/errors

## model-retiring-within-90-days

- **slug**: `model-retiring-within-90-days`
- **title**: A model still in production retires in under 90 days
- **symptom**: No error today. After the retirement date every call to the id returns `404 not_found_error`. Anthropic gives at least 60 days' notice by email to orgs with active deployments, which is easy to miss if the notice goes to a billing address nobody reads.
- **mechanism**: The model status table assigns a tentative retirement date to every id. As of the current table: `claude-sonnet-4-5-20250929` retires not sooner than **September 29, 2026**; `claude-haiku-4-5-20251001` not sooner than **October 15, 2026**; `claude-opus-4-5-20251101` not sooner than **November 24, 2026**; `claude-opus-4-6` February 5, 2027; `claude-sonnet-4-6` February 17, 2027; `claude-opus-4-7` April 16, 2027; `claude-opus-4-8` May 28, 2027; `claude-fable-5` June 9, 2027; `claude-sonnet-5` June 30, 2027; `claude-opus-5` July 24, 2027. Lifecycle states are Active / Legacy / Deprecated / Retired; partner platforms (Amazon Bedrock, Google Cloud) set their own, later dates, so a model can be dead on the Claude API and alive on Bedrock.
- **detect**: Admin API key: `GET /v1/organizations/usage_report/messages?group_by[]=model&bucket_width=1d` over the last 30 days gives every model id your org actually billed; join that list against the published retirement dates and flag any id whose date is inside your migration window. Workspace/project key: `GET /v1/models?limit=1000` lists the ids still callable and `GET /v1/models/{id}` returns `created_at`, `max_input_tokens`, `max_tokens` and `capabilities` for the replacement you are considering. The API does not expose the retirement date — that comes from the deprecations page.
- **repair**: Print: each in-use id, its retirement date, days remaining, the share of last-30-days tokens it carries (from the usage report), and the recommended replacement. Note that Claude 4.7 and later use a new tokenizer, so any cost model built on the old id needs re-baselining. Do not migrate anything.
- **category**: Models and deprecations
- **sources**: https://platform.claude.com/docs/en/about-claude/model-deprecations · https://platform.claude.com/docs/en/manage-claude/usage-cost-api · https://platform.claude.com/docs/en/models/overview

## floating-alias-instead-of-pinned-snapshot

- **slug**: `floating-alias-instead-of-pinned-snapshot`
- **title**: A floating model alias silently changes model under you
- **symptom**: No HTTP error. `response.model` and the Admin usage report show a different underlying id than the string you sent, and that underlying id can change without a deploy. Evals drift, prompt-cache hit rates drop, and token counts move.
- **mechanism**: For models released before the 4.6 generation the undated string is an alias — a convenience pointer that resolves to a dated snapshot: `claude-haiku-4-5` → `claude-haiku-4-5-20251001`, `claude-sonnet-4-5` → `claude-sonnet-4-5-20250929`, `claude-opus-4-5` → `claude-opus-4-5-20251101`. From the 4.6 generation onward the dateless id (`claude-opus-4-6`, `claude-sonnet-4-6`, `claude-opus-4-7`, `claude-opus-4-8`, `claude-opus-5`, `claude-sonnet-5`, `claude-fable-5`) **is itself a pinned snapshot** — a very common source of the opposite mistake, where somebody appends a date suffix that does not exist and gets a 404.
- **detect**: Workspace/project API key: `GET /v1/models/{alias}` — "The Models API response can be used to … resolve a model alias to a model ID"; the returned `id` is the snapshot the alias currently points to. Admin API key: `GET /v1/organizations/rate_limits?model=<alias>` returns the one `model_group` entry whose `models[]` array lists every id **and** alias that counts against that group — the canonical mapping. `GET /v1/organizations/usage_report/messages?group_by[]=model` shows which string was actually billed.
- **repair**: Print: each alias in config, the snapshot id it resolves to today, and the pinned id to write instead. Note that no date suffix should ever be appended to a 4.6-or-later id. Do not rewrite config.
- **category**: Models and deprecations
- **sources**: https://platform.claude.com/docs/en/models/overview · https://platform.claude.com/docs/en/api/models · https://platform.claude.com/docs/en/manage-claude/rate-limits-api

## model-not-available-to-this-org

- **slug**: `model-not-available-to-this-org`
- **title**: Code names a model this organization cannot call
- **symptom**: `404 not_found_error` for an id that exists in the docs, or `403 permission_error` ("Your API key does not have permission to use the specified resource").
- **mechanism**: Model availability is per-organization and per-platform, not global. `claude-mythos-5` and `claude-mythos-preview` are limited-availability (Project Glasswing). Platform coverage differs: Claude Opus 5 has no Claude Platform on AWS id; Claude Haiku 3.5 is retired on the Claude API but still live on Amazon Bedrock and Google Cloud; Bedrock ids carry an `anthropic.` prefix and Google Cloud dated ids use `@` (`claude-haiku-4-5@20251001`). Code copied from a doc, a sample, or a sibling service that runs on a different platform hits this immediately.
- **detect**: Workspace/project API key: `GET /v1/models?limit=1000` returns exactly the models available for use with **this** key, most recent first; diff `data[].id` against every model string in config. `GET /v1/models/{id}` per string separates "not available to you" (404) from "you lack permission" (403). Admin API key: `GET /v1/organizations/rate_limits` lists a `model_group` for every model family the org is provisioned for.
- **repair**: Print: the unavailable id, whether it 404s or 403s, the closest available id from `GET /v1/models`, and the platform mismatch if the id looks like a Bedrock/Vertex form (`anthropic.` prefix or `@` separator) on a first-party client. Do not request access.
- **category**: Models and deprecations
- **sources**: https://platform.claude.com/docs/en/api/models · https://platform.claude.com/docs/en/models/overview · https://platform.claude.com/docs/en/api/errors

## long-context-gated-on-obsolete-beta

- **slug**: `long-context-gated-on-obsolete-beta`
- **title**: 1M context is gated behind an obsolete beta header
- **symptom**: Two shapes. On Claude Sonnet 4.5 or Sonnet 4: requests over 200K tokens return `400 invalid_request_error` / `prompt is too long` **even with** `anthropic-beta: context-1m-2025-08-07`, because the header is now inert on those models. On Claude 4.6+: no error, but the application caps context near 200K, routes long inputs to a "long context" code path that charges a premium that no longer exists, or throttles against dedicated 1M rate limits that were removed.
- **mechanism**: The 1M-token context window graduated. On Claude Opus 5, Opus 4.8, Opus 4.7, Opus 4.6, Sonnet 5, Sonnet 4.6, Fable 5, Mythos 5 and Mythos Preview, **1M is the default**: no beta header, standard pricing across the full window ("a 900k-token request is billed at the same per-token rate as a 9k-token request"), prompt-caching and batch discounts at standard rates. The dedicated 1M rate limits were removed — standard account limits apply at every context length. And the `context-1m-2025-08-07` beta was **retired for Claude Sonnet 4.5 and Claude Sonnet 4 on April 30, 2026**: the header has no effect and requests over the standard 200k window error. Every model with a 1M window is capped at 128k output tokens per request.
- **detect**: Workspace/project API key: `GET /v1/models/{model_id}` → `max_input_tokens` is authoritative per id (200000 vs 1000000); loop it over every model in config and compare with whatever ceiling the application enforces. Probe the header itself read-only: `GET /v1/models -H "anthropic-beta: context-1m-2025-08-07"` still returns 200 (the name is valid), so acceptance proves nothing — the finding is that the header is present in code for a model where it is inert. Admin API key: `GET /v1/organizations/usage_report/messages?context_window[]=0-200k&group_by[]=model` (and the complementary slice) shows how much traffic actually crosses 200K; `GET /v1/organizations/rate_limits?model=<id>` confirms there is no separate long-context limit group.
- **repair**: Print: per model id, `max_input_tokens` from the Models API vs the ceiling enforced in code; every call site still sending `context-1m-2025-08-07`; every pricing branch that assumes a >200K premium (there is none on 4.6+); and, for any remaining Sonnet 4.5 / Sonnet 4 usage, the note that 1M there is gone and the path forward is Sonnet 4.6 or later. Do not edit config or send a long request.
- **category**: Models and deprecations
- **sources**: https://platform.claude.com/docs/en/build-with-claude/context-windows · https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/release-notes/overview

## structured-output-truncated-by-length

- **slug**: `structured-output-truncated-by-length`
- **title**: JSON cut off mid-object — `max_output_tokens` truncation
- **symptom**: Responses API: `"status": "incomplete"` with `"incomplete_details": {"reason": "max_output_tokens"}`. Chat Completions: `finish_reason: "length"`. The content is syntactically invalid JSON — it stops mid-string — and `json.loads()` throws a `JSONDecodeError` far from the API call site. HTTP status is 200.
- **mechanism**: Structured Outputs guarantees the model *follows* the schema, not that it *finishes*. If generation hits `max_output_tokens` (or the model's output ceiling) the response is truncated exactly like any other completion, leaving a half-written object. Large arrays and long free-text fields inside the schema are the usual cause. Because the request succeeded, retry-on-exception logic never engages.
- **detect**: `GET /v1/responses/{response_id}` for stored responses and check `status == "incomplete"` and `incomplete_details.reason == "max_output_tokens"`; also inspect `usage.output_tokens` against the `max_output_tokens` you configured. At org level, `GET /v1/organization/usage/completions?start_time=...&bucket_width=1d&group_by=model` (**admin read key**) shows output-token saturation trends. Requires: project read key (responses must have been created with `store: true`); admin read key for aggregates.
- **repair**: print — `Check response.status !== "completed" before parsing, and branch on incomplete_details.reason. Raise max_output_tokens, or reshape the schema to emit fewer/shorter fields per call and paginate. Never call json.loads on output text without first confirming the response completed.`
- **category**: Structured output and tools
- **sources**: https://developers.openai.com/api/docs/guides/structured-outputs · https://developers.openai.com/api/docs/api-reference/responses

## refusal-field-ignored

- **slug**: `refusal-field-ignored`
- **title**: Model refused and the `refusal` field was never checked
- **symptom**: HTTP 200, but the output contains `{"type": "refusal", "refusal": "I'm sorry, I can't help with that."}` instead of the expected structured content. In Chat Completions the same thing appears as a non-null `choices[0].message.refusal` with `message.content == null`, so `.parsed` is `None` and the code either crashes on `NoneType` or writes an empty record.
- **mechanism**: Structured Outputs adds a dedicated refusal channel so a safety refusal does not have to be squeezed into the schema. The refusal is a distinct content type, not a schema-conforming object and not an error. Any parser that reaches straight for the text/parsed field misses it entirely.
- **detect**: `GET /v1/responses/{response_id}` and scan `output[].content[]` for `type == "refusal"`, reading the `refusal` string. Also flag responses where `status == "incomplete"` and `incomplete_details.reason == "content_filter"` — the adjacent failure mode. Requires: project read key, and the response must have been stored (`store: true`).
- **repair**: print — `Handle refusal as a first-class branch before parsing: if any output content item has type "refusal", surface refusal text to the caller and do not attempt schema parsing. Log refusal rate per prompt template — a spike usually means a prompt or an input source went bad, not that users turned malicious.`
- **category**: Structured output and tools
- **sources**: https://developers.openai.com/api/docs/guides/structured-outputs · https://developers.openai.com/api/docs/api-reference/responses

## strict-false-schema-silently-ignored

- **slug**: `strict-false-schema-silently-ignored`
- **title**: `strict` omitted, so the JSON schema is only a suggestion
- **symptom**: HTTP 200 and valid JSON, but with extra keys, missing required keys, or wrong types — intermittently, on maybe 1-3% of calls. Downstream validation (Pydantic/Zod) throws unpredictably in production while the same prompt passes every time in testing.
- **mechanism**: Structured Outputs only *guarantees* schema adherence when `strict: true` is set — in `text.format` for the Responses API, in `response_format.json_schema` for Chat Completions, and per-tool in `tools[].function.strict` for function calling. With `strict` absent or `false` the schema degrades to a hint the model usually follows. There is no warning: the request is accepted either way. Constrained decoding also requires `additionalProperties: false` on every object, all `properties` listed in `required`, and a root of type `object` (never `anyOf`); a schema that violates these cannot be used with `strict: true` at all, which is why teams quietly drop the flag.
- **detect**: Read-only detection is inferential and cheap: `GET /v1/responses/{response_id}` for stored responses and inspect the echoed `text.format` — flag any where `type == "json_schema"` and `strict` is absent or `false`, or where `format.type == "json_object"` (legacy JSON mode, no schema at all). Same for `tools[].function.strict` on tool definitions echoed back in the response object. Requires: project read key with `store: true` responses.
- **repair**: print — `Set strict: true everywhere and fix the schema to satisfy the subset: additionalProperties: false on every object, every property listed in required (use type: ["string","null"] for optionals), root type object. Keep within the limits — up to 5 levels of nesting, 5,000 object properties, 1,000 enum values, 120,000 total schema characters. Drop unsupported keywords (minLength, maxLength, pattern, format, minimum, maximum, minItems, maxItems, uniqueItems) — they are silently unenforced.`
- **category**: Structured output and tools
- **sources**: https://developers.openai.com/api/docs/guides/structured-outputs · https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs · https://community.openai.com/t/structured-outputs-limits-are-raised-to-support-larger-schemas/1313593

## tool-call-arguments-unparseable

- **slug**: `tool-call-arguments-unparseable`
- **title**: Tool-call `arguments` is a JSON string that fails to parse
- **symptom**: HTTP 200 with `finish_reason: "tool_calls"` (Chat Completions) or an output item of `type: "function_call"` (Responses). `arguments` is a **string**, and `json.loads(arguments)` raises — truncated, doubled braces, or a hallucinated field. The traceback is a `JSONDecodeError` in your dispatcher, nowhere near the API layer.
- **mechanism**: Function arguments are returned JSON-*encoded*, not as a parsed object, and the docs are explicit that they may be malformed. Without `strict: true` on the tool there is no grammar constraint at all; even with strict mode, hitting the output-token ceiling truncates the argument string mid-write. Parallel tool calls multiply the exposure since each call carries its own argument blob.
- **detect**: `GET /v1/responses/{response_id}` for stored responses; for each output item with `type == "function_call"`, attempt to parse `arguments` and validate against the declared tool schema. Report the `name`, `call_id`, and the parse error. Also correlate with `status == "incomplete"` / `incomplete_details.reason == "max_output_tokens"`, which explains truncated argument strings. Requires: project read key with stored responses.
- **repair**: print — `Wrap every argument parse in try/except and feed the parse error back to the model as a tool result so it can self-correct, rather than crashing the turn. Set strict: true on every tool with additionalProperties: false and all params required. Raise max_output_tokens if truncation is the cause.`
- **category**: Structured output and tools
- **sources**: https://developers.openai.com/api/docs/guides/function-calling · https://developers.openai.com/api/docs/api-reference/responses

## tool-defined-but-never-called

- **slug**: `tool-defined-but-never-called`
- **title**: Tool ships in every request but the model never calls it
- **symptom**: No error at all. Input tokens rise on every single call (the tool schema is re-sent each turn) while the tool's own handler logs stay at zero. `tool_choice` is `"auto"`, so the model is free to ignore the tool — and does.
- **mechanism**: Tool definitions are part of the prompt and are billed as input tokens on every request. A tool with a vague description, a name that collides with another, or one of twenty crowding the same turn (the docs recommend keeping fewer than 20 tools available at the start of a turn) simply never gets selected. The cost is continuous and invisible; the capability is absent.
- **detect**: `GET /v1/responses/{response_id}` across a sample of stored responses; build two sets — tool names present in the request's `tools[]`, and tool names appearing in `output[]` items of `type: "function_call"`. Any tool in the first set that never appears in the second across a large sample is dead weight. Quantify the cost with `GET /v1/organization/usage/completions?start_time=...&bucket_width=1d&group_by=model` (**admin read key**) and compare `input_tokens` before/after. Requires: project read key; admin read key for cost sizing.
- **repair**: print — `Rewrite the tool description to say exactly when to call it and prune unused tools from the request. Use tool_choice "required" or a named tool ({"type":"function","name":"..."}) when a call is mandatory, or allowed_tools to narrow the set per turn. Cache the static tool block so repeat definitions hit the prompt cache.`
- **category**: Structured output and tools
- **sources**: https://developers.openai.com/api/docs/guides/function-calling · https://developers.openai.com/api/docs/api-reference/responses

## parallel-tool-calls-with-strict-schema

- **slug**: `parallel-tool-calls-with-strict-schema`
- **title**: Parallel tool calls quietly void the strict-schema promise
- **symptom**: HTTP 200, `finish_reason: "tool_calls"`, several `function_call` items in one turn — and argument objects that violate the declared schema despite `strict: true`. Deterministic in tests (one tool call), flaky in production (several).
- **mechanism**: Structured Outputs is not supported together with parallel function calls; the guidance is to set `parallel_tool_calls: false` when relying on strict schemas. `parallel_tool_calls` defaults to true, so the guarantee silently degrades exactly when the model decides to fan out. Additionally, duplicate or conflicting parallel calls to the same tool cause double side effects in handlers written for one call per turn.
- **detect**: `GET /v1/responses/{response_id}` on stored responses; flag any response where `output[]` contains more than one `function_call` item **and** the request echoes `parallel_tool_calls` true (or absent) with any tool declaring `strict: true`. Also flag repeated `function_call` items sharing the same `name` in a single turn. Requires: project read key with stored responses.
- **repair**: print — `Set parallel_tool_calls: false whenever strict tool schemas matter. If you need fan-out, drop strict and validate arguments yourself. Make every tool handler idempotent and keyed on call_id so duplicate parallel calls cannot double-apply.`
- **category**: Structured output and tools
- **sources**: https://developers.openai.com/api/docs/guides/function-calling · https://learn.microsoft.com/en-us/azure/foundry/openai/how-to/structured-outputs

## tool-schemas-dominate-input-tokens

- **slug**: `tool-schemas-dominate-input-tokens`
- **title**: Tool schemas dominate the input tokens on every call
- **symptom**: No error. The usage report shows large `uncached_input_tokens` that does not scale with user-visible work, and `cache_read_input_tokens` near zero — the shape of a big fixed prefix being resent uncached. Token counting confirms it: the same request with and without `tools` differs by most of the input.
- **mechanism**: Everything in `tools` counts as input tokens — tool names, descriptions, and full JSON schemas — plus an automatic tool-use system prompt whose size is model-specific: **286 tokens** on Claude Opus 5 for `tool_choice` of `auto`/`none` and **406** for `any`/`tool`; **290/410** on Opus 4.8; **675/804** on Opus 4.7; **497/589** on Opus 4.6 and Sonnet 4.6; **354/474** on Sonnet 5; **496/588** on Opus 4.5, Sonnet 4.5 and Haiku 4.5. Anthropic-defined tools add their own: bash is **325** tokens on Opus 5/4.8/4.7 (244 on Opus 4.6, Sonnet 4.6 and earlier), text editor **700**, the `computer_toolset_20260801` about **4,500**, and `browser_toolset_20260801` about **6,600**. A 40-tool surface can therefore cost more per call than the user's actual message — and because tool definitions sit first in the cache order (`tools` → `system` → `messages`), any change to them invalidates everything.
- **detect**: Two reads. (1) Admin API key: `GET /v1/organizations/usage_report/messages? starting_at={T-30d}&bucket_width=1d&limit=31&group_by[]=api_key_id&group_by[]=model` to find keys with high flat `uncached_input_tokens` and near-zero `cache_read_input_tokens`. (2) Workspace key: `POST /v1/messages/count_tokens` — non-billed and non-mutating — with the exact `tools`, `system`, and a one-line `messages` payload, then again with `tools` omitted. The difference is the per-call tool overhead. `usage` on any real response also reports the exact count for that request.
- **repair**: Print, do not run: report the measured tool overhead per call and the monthly dollar cost at the model's input rate, then recommend a `cache_control` breakpoint after the tool definitions, or the tool search tool with `defer_loading: true` on rarely-used tools (never on all of them — the API returns 400 "All tools have defer_loading set").
- **category**: Structured output and tools
- **sources**: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview · https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/build-with-claude/prompt-caching

## batch-discount-left-unused

- **slug**: `batch-discount-left-unused`
- **title**: Every request is real-time, so the Batch discount is unused
- **symptom**: No error. `group_by=batch` on the usage endpoint returns a single row with `batch: false` and no `batch: true` counterpart. Nightly enrichment jobs, backfills, evaluation runs, and bulk classification are all going through the synchronous endpoint at full price, often at 2x what the same work would cost asynchronously.
- **mechanism**: The synchronous endpoint is what every example uses and what every SDK call defaults to, so latency-insensitive work inherits latency-sensitive pricing by default. Nothing about a batch-shaped workload announces itself to the API — a nightly job that fires 40,000 chat completions in twenty minutes is indistinguishable, request by request, from user traffic. The signal is only visible in aggregate: heavily clustered request volume with no interactive pattern.
- **detect**: Organization **ADMIN** key required. `GET /v1/organization/usage/completions?start_time={now-7d}&bucket_width=1h&limit=168&group_by=batch&group_by=project_id&group_by=model`. Each result carries `batch` (a boolean, non-`null` only because you grouped by it) alongside `input_tokens`, `output_tokens`, and `num_model_requests`. Compute the share of tokens on `batch == false`. Then look for batch-shaped traffic inside the synchronous half: with `bucket_width=1h` over 7 days, flag any `project_id` whose `num_model_requests` is concentrated into a handful of hours per day (e.g. >70% of the week's requests inside <10% of the buckets) — that is a scheduled job paying interactive prices. You can also filter directly with `&batch=true` or `&batch=false` to isolate either population. Confirm the money at stake with `GET /v1/organization/costs?start_time=…&group_by=line_item`, where batch and non-batch appear as distinct `line_item` strings.
- **repair**: Print, per project: percentage of tokens on `batch == false`, the hours-of-day where requests cluster, and the 30-day cost of that traffic with the batch-price equivalent beside it. Recommend moving the identified jobs to the Batch API (upload a JSONL of requests to `/v1/files` with `purpose="batch"`, then `POST /v1/batches` with a 24h completion window) and note the trade: roughly half price, in exchange for giving up latency guarantees.
- **category**: Batch and async
- **sources**: https://platform.openai.com/docs/api-reference/usage/completions · https://platform.openai.com/docs/api-reference/batch · https://github.com/openai/openai-python/blob/main/api.md

## batch-expired-past-24h-window

- **slug**: `batch-expired-past-24h-window`
- **title**: Batch hit `expired` — 24h window closed on unfinished rows
- **symptom**: `GET /v1/batches/{id}` returns `"status": "expired"`, `expired_at` set, and `request_counts.completed < request_counts.total`. Every unfinished row lands in the error file with `{"code": "batch_expired", "message": "This request could not be executed before the completion window expired."}`. No HTTP error is ever raised — the create call 200'd a day earlier.
- **mechanism**: `completion_window` is fixed at `"24h"`. Whatever OpenAI has not processed 24 hours after `in_progress_at` is abandoned. Oversized batches (up to 50,000 requests / 200 MB input file) and batches submitted behind a long queue routinely fail to drain in time. The batch object stays queryable but the work is gone; callers that only check `status == "completed"` treat an expired batch as "still running" forever.
- **detect**: `GET /v1/batches?limit=100` (paginate on `after`). Flag any object with `status == "expired"`, and compute the shortfall as `request_counts.total - request_counts.completed`. Also pre-emptively flag `status in ("validating","in_progress","finalizing")` where `time.time() - created_at > 82800` (23h) — those are about to expire. Read `expires_at`/`expired_at` for exact timing. Requires: project read key.
- **repair**: print — `Re-submit the missing rows. Download the error file (GET /v1/files/{error_file_id}/content), select lines whose error.code == "batch_expired", rebuild a .jsonl of just those custom_ids, and split future submissions so a single batch stays well under 50,000 requests. Track expires_at in your own job table and alert at the 20-hour mark.`
- **category**: Batch and async
- **sources**: https://developers.openai.com/api/docs/guides/batch · https://developers.openai.com/api/docs/api-reference/batch

## batch-failed-input-validation

- **slug**: `batch-failed-input-validation`
- **title**: Batch went straight to `failed` on input-file validation
- **symptom**: `GET /v1/batches/{id}` returns `"status": "failed"` with `failed_at` set, `output_file_id: null`, and a populated `errors` object: `{"object":"list","data":[{"code": "...", "message": "...", "param": "...", "line": 42}]}`. `request_counts` is all zeros. Nothing was ever billed and nothing was ever produced.
- **mechanism**: The batch first enters `validating`, where OpenAI parses every line of the input `.jsonl`. A malformed line, a missing `custom_id`, a duplicate `custom_id`, an `endpoint` that does not match the per-line `url`, or a model the project cannot access fails the whole batch. Because `POST /v1/batches` returned 200, code that fires-and-forgets never learns the batch died seconds later.
- **detect**: `GET /v1/batches?limit=100`, filter `status == "failed"`, then read `errors.data[]` for `code`, `message`, `param` and `line`. The `line` number points at the offending row of the input file. Requires: project read key.
- **repair**: print — `Fix the input .jsonl at the reported line numbers, then re-upload and re-create. Validate locally before upload: every line needs a unique custom_id, a method, a url matching the batch endpoint, and a body whose model is enabled for this project. Never treat a 200 from POST /v1/batches as success — poll until status leaves "validating".`
- **category**: Batch and async
- **sources**: https://developers.openai.com/api/docs/api-reference/batch · https://developers.openai.com/api/docs/guides/batch

## batch-error-file-never-read

- **slug**: `batch-error-file-never-read`
- **title**: `error_file_id` exists but the error file was never fetched
- **symptom**: A completed batch carries a non-null `error_file_id`, yet `GET /v1/files/{error_file_id}` shows the file still sitting there and nothing in the pipeline ever called `/content`. Downstream tables are silently short of rows and no exception was ever raised.
- **mechanism**: The Batch API splits results across two files: successes go to `output_file_id`, failures go to `error_file_id`. Each error line is `{"custom_id": "...", "response": null, "error": {"code": "...", "message": "..."}}` (or a `response.status_code` of 4xx/5xx). Code that only reads `output_file_id` gets a silently truncated result set — the batch reports `completed`, which reads as total success.
- **detect**: `GET /v1/batches?limit=100`; for every batch flag `error_file_id != null`. Cross-check with `GET /v1/files?purpose=batch_output` to confirm the file exists and note its `bytes` — a non-zero error file that your own ingest log never references is the finding. Requires: project read key.
- **repair**: print — `Download and parse the error file for every batch: GET /v1/files/{error_file_id}/content. Group the failures by error.code, retry the transient ones (rate_limit_exceeded, server_error), and fix the rest. Make "error_file_id is null" an assertion in your batch-completion handler rather than an afterthought.`
- **category**: Batch and async
- **sources**: https://developers.openai.com/api/docs/guides/batch · https://developers.openai.com/api/docs/api-reference/batch

## batch-partial-failure-unnoticed

- **slug**: `batch-partial-failure-unnoticed`
- **title**: Batch says `completed` while `request_counts.failed > 0`
- **symptom**: `GET /v1/batches/{id}` returns `"status": "completed"` alongside e.g. `"request_counts": {"total": 50000, "completed": 49131, "failed": 869}`. No HTTP error anywhere; the output file simply has fewer lines than the input file.
- **mechanism**: `completed` means "the batch finished running", not "every request succeeded". Individual rows can fail on rate limits, context-length overflow, content filtering or transient server errors and still leave the batch in `completed`. The only signal is the arithmetic in `request_counts` plus the error file.
- **detect**: `GET /v1/batches?limit=100`. For each object assert `request_counts.failed == 0` and `request_counts.completed == request_counts.total`. Any batch where those disagree is a partial failure, regardless of `status`. Requires: project read key.
- **repair**: print — `Treat request_counts.failed > 0 as a job failure in your orchestrator. Read the error file, bucket by error.code, and re-submit the failed custom_ids in a follow-up batch. Reconcile output line count against input line count before marking the job done.`
- **category**: Batch and async
- **sources**: https://developers.openai.com/api/docs/api-reference/batch · https://developers.openai.com/api/docs/guides/batch

## batch-enqueued-token-limit-exceeded

- **slug**: `batch-enqueued-token-limit-exceeded`
- **title**: Batch rejected with `token_limit_exceeded` on the queue cap
- **symptom**: `POST /v1/batches` returns HTTP 400 with `"code": "token_limit_exceeded"` and a message of the form `Enqueued token limit reached for <model> in organization org-xxx. Limit: N enqueued tokens. Please try again once some in_progress batches have been completed.` Some client libraries surface this later as a batch whose `errors.data[].code` is `token_limit_exceeded`.
- **mechanism**: Batch has a *separate* rate-limit dimension from synchronous traffic: a per-model cap on total input tokens sitting in the queue across all your `validating`/`in_progress`/`finalizing` batches. Tokens are released only when a batch reaches a terminal state. A pipeline that submits N batches in a loop will sail past the cap on the first run and then fail every subsequent submission until the queue drains. Separately, batch creation is capped at 2,000 batches per hour.
- **detect**: `GET /v1/batches?limit=100` and sum `usage.input_tokens` (or your own estimate of input tokens) across every batch not in a terminal state — that approximates current queue occupancy per `model`. Also count batches created in the last hour from `created_at` and flag counts approaching 2,000. Cross-check org-level batch spend with `GET /v1/organization/usage/completions?batch=true&start_time=...&bucket_width=1d` (**admin read key**). Requires: project read key (admin read key for the usage cross-check).
- **repair**: print — `Submit batches with a concurrency gate instead of a loop: hold at most K in-flight batches and only enqueue the next one after a prior batch reaches completed/failed/expired/cancelled. Read your per-model enqueued-token limit on the Platform limits page, keep total queued input tokens under it, and stay under 2,000 batch creations per hour.`
- **category**: Batch and async
- **sources**: https://developers.openai.com/api/docs/guides/batch · https://community.openai.com/t/enqueued-token-limit-reached/1051238

## batch-input-file-wrong-purpose

- **slug**: `batch-input-file-wrong-purpose`
- **title**: Batch input file uploaded with the wrong `purpose`
- **symptom**: `POST /v1/batches` returns HTTP 400 `invalid_request_error` complaining the `input_file_id` is not a valid batch input file. Inspecting the file shows `"purpose": "assistants"` or `"user_data"` or `"fine-tune"` instead of `"batch"`.
- **mechanism**: The Files API namespaces uploads by `purpose` (`assistants`, `assistants_output`, `batch`, `batch_output`, `fine-tune`, `fine-tune-results`, `vision`, `user_data`). `/v1/batches` will only accept a file whose purpose is exactly `batch`. Shared upload helpers that hard-code a default purpose produce a file that looks fine in `GET /v1/files` but can never be used as a batch input — and the wrong-purpose file still consumes project storage.
- **detect**: `GET /v1/files?purpose=batch` and compare against the `input_file_id` values seen in `GET /v1/batches?limit=100`. Then `GET /v1/files?limit=10000` and flag any `.jsonl` filename that looks like batch input but carries a non-`batch` purpose. `GET /v1/files/{file_id}` confirms `purpose` for a single file. Requires: project read key.
- **repair**: print — `Re-upload the file with purpose="batch" (files.create(file=..., purpose="batch")) and delete the mis-purposed copy. Add an assertion in the upload helper that the purpose matches the consuming endpoint.`
- **category**: Batch and async
- **sources**: https://developers.openai.com/api/docs/api-reference/files · https://developers.openai.com/api/docs/guides/batch

## batch-output-file-never-downloaded

- **slug**: `batch-output-file-never-downloaded`
- **title**: Completed batch results expire undownloaded after 30 days
- **symptom**: `GET /v1/batches` shows batches with `status: "completed"` and a non-null `output_file_id` whose file is missing from `GET /v1/files?purpose=batch_output`, or `GET /v1/files/{output_file_id}` returns HTTP 404 `"code": "invalid_request_error"`. The work was paid for and the results are gone.
- **mechanism**: Batch output files are retained for 30 days after completion and then deleted. A batch whose completion callback failed, or one submitted by an ad-hoc script nobody re-ran, leaves paid-for results sitting in a file that quietly disappears. The batch object itself survives, so the audit trail shows a completed job with an unreachable `output_file_id`.
- **detect**: `GET /v1/batches?limit=100`; for each `status == "completed"` collect `output_file_id` and intersect with the ids from `GET /v1/files?purpose=batch_output`. Report any `output_file_id` absent from the file list, and any present file whose `created_at` is more than ~25 days old (about to expire). Requires: project read key.
- **repair**: print — `Download completed batch outputs immediately: GET /v1/files/{output_file_id}/content, persist to your own object store keyed by batch id. For future batches set output_expires_after on POST /v1/batches so unread outputs stop billing storage, and add a daily sweep that downloads any completed batch whose output has not yet been archived.`
- **category**: Batch and async
- **sources**: https://developers.openai.com/api/docs/guides/batch · https://developers.openai.com/api/docs/api-reference/batch

## batch-created-never-polled

- **slug**: `batch-created-never-polled`
- **title**: Batch created days ago and never polled to a terminal state
- **symptom**: `GET /v1/batches` returns objects still in `validating` or `in_progress` whose `created_at` is far older than 24 hours, or terminal batches (`completed`/`failed`/`expired`) that no application record acknowledges. No error is emitted anywhere — the job simply has no consumer.
- **mechanism**: Batch is fully asynchronous with no webhook by default. If the process that created the batch died, was redeployed, or lost its job-id table, nothing ever calls `GET /v1/batches/{id}`. The batch still runs, still bills, still occupies the enqueued-token limit until it terminates, and its results still expire on schedule.
- **detect**: `GET /v1/batches?limit=100` and paginate fully. Flag (a) any batch whose `status` is non-terminal and `created_at` is older than 86,400 seconds — this is physically impossible for a live batch and means the object is stale; (b) any terminal batch whose `id` is not present in your own jobs table. `metadata` on the batch object (up to 16 key/value pairs) is the join key if you set one. Requires: project read key.
- **repair**: print — `Record every batch id plus its metadata in durable storage at creation time, and run a reconciler that lists /v1/batches and closes out any batch your table does not know about. Set metadata like {"job":"nightly-embed","run_id":"..."} on POST /v1/batches so orphans are identifiable. Consider subscribing to batch webhooks instead of polling.`
- **category**: Batch and async
- **sources**: https://developers.openai.com/api/docs/api-reference/batch · https://developers.openai.com/api/docs/guides/batch

## batch-cancelled-partial-results

- **slug**: `batch-cancelled-partial-results`
- **title**: Cancelled batch left billed, partially-written output behind
- **symptom**: `GET /v1/batches/{id}` returns `"status": "cancelled"` (or `"cancelling"` for up to 10 minutes) with `cancelling_at`/`cancelled_at` set, a non-null `output_file_id`, and `request_counts.completed` somewhere between 0 and `total`.
- **mechanism**: `POST /v1/batches/{id}/cancel` moves the batch to `cancelling` and it can take up to 10 minutes to reach `cancelled`. Requests already completed before cancellation are billed and *are* written to the output file. Teams that cancel on a deploy or a timeout assume nothing happened, so they re-run the whole batch — paying twice for the overlapping rows — and leave the partial output file to rot.
- **detect**: `GET /v1/batches?limit=100`, filter `status in ("cancelling","cancelled")`. Flag any with `request_counts.completed > 0` (billed work that produced output) and any stuck in `cancelling` for more than ~15 minutes. Requires: project read key.
- **repair**: print — `Before re-running a cancelled batch, download its output file and subtract the custom_ids that already succeeded. Confirm the batch reached "cancelled" and not just "cancelling" before assuming billing has stopped. Reconcile the cost against GET /v1/organization/costs for the affected day.`
- **category**: Batch and async
- **sources**: https://developers.openai.com/api/docs/api-reference/batch · https://developers.openai.com/api/docs/guides/batch

## background-response-never-polled

- **slug**: `background-response-never-polled`
- **title**: Background response left in `queued` and never collected
- **symptom**: `GET /v1/responses/{response_id}` returns `"status": "queued"` or `"in_progress"` long after creation, or `"status": "failed"` with `error: {"code": "server_error" | "rate_limit_exceeded" | "invalid_prompt", "message": "..."}`. The originating request returned 200 immediately and the caller moved on.
- **mechanism**: With `background: true` the Responses API returns as soon as the job is accepted; the result only exists on the response object. The `status` enum is `queued`, `in_progress`, `completed`, `incomplete`, `failed`, `cancelled` — four of those six are not success. A worker that crashes between creation and polling strands the job: it still runs, still bills, and (only if `background: true`) can still be cancelled via `POST /v1/responses/{id}/cancel`.
- **detect**: Poll `GET /v1/responses/{response_id}` for every id in your job table and bucket by `status`. Flag `queued`/`in_progress` older than your SLA, `failed` (read `error.code`), `incomplete` (read `incomplete_details.reason`), and any id in your table that 404s. Requires: project read key (`store` must not be false for the response to be retrievable).
- **repair**: print — `Persist the response id transactionally at creation, then reconcile with a poller that drives every id to a terminal status. Cancel abandoned background jobs with POST /v1/responses/{response_id}/cancel — only background responses are cancellable. Alert on failed with error.code so server_error and rate_limit_exceeded get retried while invalid_prompt gets escalated.`
- **category**: Batch and async
- **sources**: https://developers.openai.com/api/docs/api-reference/responses · https://github.com/openai/openai-python/blob/main/api.md

## batch-requests-expired-after-24h

- **slug**: `batch-requests-expired-after-24h`
- **title**: Batch requests expire unprocessed at the 24-hour mark
- **symptom**: After `processing_status` reaches `ended`, `request_counts.expired` is greater than zero, and those lines in the results file carry `{"result": {"type": "expired"}}`. You are not billed for them — you simply never get the answers, and any downstream job keyed on "batch ended = all results present" silently processes a partial set.
- **mechanism**: "You can access batch results when all messages have completed or after 24 hours, whichever comes first. Batches expire if processing does not complete within 24 hours." `expires_at` is exactly `created_at + 24h`. Most batches finish in under an hour, so expiry means the batch was too large, submitted into a saturated queue, or hit the org-wide enqueued-request ceiling behind other work.
- **detect**: Workspace/project API key: `GET /v1/messages/batches?limit=1000` returns every batch in the workspace, newest first, each with `created_at`, `expires_at`, `ended_at`, `processing_status` and the full `request_counts` object (`processing` / `succeeded` / `errored` / `canceled` / `expired`, which always sum to the batch size). Flag any batch with `expired > 0`, and any batch whose `ended_at` is within minutes of `expires_at`. Per-request detail: stream `GET /v1/messages/batches/{batch_id}/results` and count `.result.type == "expired"` by `custom_id`.
- **repair**: Print: batch id, `created_at`, `expires_at`, expired count and percentage, and the list of unanswered `custom_id`s to resubmit. Recommend smaller batches (cap is 100,000 requests or 256 MB, whichever comes first) and checking queue depth before submitting. Do not resubmit.
- **category**: Batch and async
- **sources**: https://platform.claude.com/docs/en/build-with-claude/batch-processing · https://platform.claude.com/docs/en/api/messages/batches/list

## batch-errored-requests-unread

- **slug**: `batch-errored-requests-unread`
- **title**: Batch request_counts.errored is above zero and unread
- **symptom**: `request_counts.errored > 0` after the batch ends; the corresponding result lines are `{"custom_id": "...", "result": {"type": "errored", "error": {"type": "error", "error": {"type": "invalid_request_error", ...}}}}`. Not billed. A pipeline that only reads `succeeded` lines drops these on the floor and reports success.
- **mechanism**: "Validation of the `params` object for each message request is performed asynchronously, and validation errors are returned when processing of the entire batch has ended." So a retired model id, a `max_tokens` above the model cap, a `max_tokens: 0`, or a malformed tool schema inside **one** request is completely invisible at submit time — the batch is accepted and only 24 hours later does the error surface. Errored results cover both validation errors and internal server errors, and they are distinguished only by the inner `error.type`.
- **detect**: Workspace/project API key: `GET /v1/messages/batches?limit=1000` → flag every batch with `request_counts.errored > 0`. Then stream `GET /v1/messages/batches/{batch_id}/results` and group `.result.error.error.type` by `custom_id` — `invalid_request_error` means your payload, `api_error` means Anthropic's side and is worth resubmitting. Cross-check any offending model string with `GET /v1/models/{id}` (404 = retired) and any offending `max_tokens` with that model's `max_tokens` field.
- **repair**: Print: batch id, errored count, the histogram of inner `error.type` values, and the offending `custom_id`s with their diagnosed cause (retired model, `max_tokens` over cap, `max_tokens: 0` which is unsupported in a batch because an ephemeral cache entry would expire before the follow-up request, bad `custom_id` format — it must match `^[a-zA-Z0-9_-]{1,64}$`). Recommend validating one representative request against the Messages API shape before batching. Do not resubmit.
- **category**: Batch and async
- **sources**: https://platform.claude.com/docs/en/build-with-claude/batch-processing · https://platform.claude.com/docs/en/api/messages/batches/list · https://platform.claude.com/docs/en/api/errors

## batch-results-never-fetched

- **slug**: `batch-results-never-fetched`
- **title**: Batch results lapse unread after the 29-day retention
- **symptom**: The batch object is still listable and still shows `succeeded > 0`, but `archived_at` is set and the results are gone — `results_url` no longer downloads anything. You paid for the tokens (at 50% off) and the output is unrecoverable.
- **mechanism**: "Batch results are available for 29 days after creation. After that, you may still view the Batch, but its results will no longer be available for download." `archived_at` is documented precisely as "the time at which the Message Batch was archived and its results became unavailable." The failure mode is a submit-and-forget pipeline, an outage during the polling window, or a downstream consumer that was disabled while batches kept being created.
- **detect**: Workspace/project API key: `GET /v1/messages/batches?limit=1000` (paginate with `after_id`) and evaluate each batch: `archived_at != null` with `request_counts.succeeded > 0` is money already lost; `ended_at != null`, `results_url != null`, `archived_at == null` and `created_at` older than ~25 days is about to lapse and is the actionable set. There is no API flag for "results were downloaded", so pair the list against your own consumer's ledger of processed batch ids.
- **repair**: Print two lists: **lapsed** (batch id, `created_at`, `archived_at`, succeeded count — unrecoverable, must be re-run) and **expiring soon** (batch id, days remaining until `created_at + 29d`, `results_url`). Recommend a reconciliation job that lists batches and downloads any `ended` batch whose id is not in the consumer ledger. Do not download or delete.
- **category**: Batch and async
- **sources**: https://platform.claude.com/docs/en/build-with-claude/batch-processing · https://platform.claude.com/docs/en/api/messages/batches/list

## batch-canceled-mid-flight-anthropic

- **slug**: `batch-canceled-mid-flight-anthropic`
- **title**: A canceled batch holds partial results nobody read
- **symptom**: `cancel_initiated_at` is set, `processing_status` has passed through `canceling` to `ended`, and `request_counts` shows a non-zero `canceled` **alongside** a non-zero `succeeded`. The succeeded results are billed, downloadable and usually discarded because the operator assumed cancel meant nothing came back.
- **mechanism**: Cancellation is not instantaneous. "Immediately after cancellation, a batch's `processing_status` will be `canceling`… Canceled batches end up with a status of `ended` and may contain partial results for requests that were processed before cancellation." Canceled requests are not billed; already-processed ones are. The same 29-day retention clock applies to the partial results.
- **detect**: Workspace/project API key: `GET /v1/messages/batches?limit=1000` → flag batches with `cancel_initiated_at != null`; for each, read `request_counts.succeeded` and `request_counts.canceled`. Anything with `succeeded > 0` has salvageable output at `results_url`. Stream `GET /v1/messages/batches/{batch_id}/results` and separate `.result.type == "succeeded"` from `"canceled"` by `custom_id`. A batch still showing `processing_status: "canceling"` is mid-cancellation, not finished.
- **repair**: Print: batch id, `cancel_initiated_at`, succeeded vs canceled counts, the `results_url`, days left before archival, and the list of `custom_id`s that completed and can be reused instead of re-run. Do not download or re-run.
- **category**: Batch and async
- **sources**: https://platform.claude.com/docs/en/build-with-claude/batch-processing · https://platform.claude.com/docs/en/api/messages/batches/list

## batches-created-but-never-polled

- **slug**: `batches-created-but-never-polled`
- **title**: Batches end and are never polled, so results are dropped
- **symptom**: A long tail of batches with `processing_status: "ended"`, `ended_at` set and a live `results_url` that nothing ever downloads. Tokens are billed; nothing consumes the output. Frequently paired with a re-run of the identical work, so the org pays twice.
- **mechanism**: The Batch API is fire-and-poll by design: "You can poll for the status of the batch and retrieve results when processing has ended for all requests." There is no webhook or callback in the Messages Batches flow, so a submitter without a polling loop — or a polling loop that dies and is never restarted — leaves finished work unclaimed. Most batches complete in under an hour, so the window between "ready" and "forgotten" is wide.
- **detect**: Workspace/project API key: `GET /v1/messages/batches?limit=1000` and count batches where `ended_at != null` and `archived_at == null`; join against your consumer's ledger of processed ids to find the unclaimed set. Admin API key: `GET /v1/organizations/usage_report/messages?service_tiers[]=batch&group_by[]=model&bucket_width=1d` proves the tokens were billed at the batch rate; if that spend has no matching downstream artifact, the results were dropped. The `processing` count in `request_counts` being zero while `succeeded` is high confirms the batch is complete and waiting.
- **repair**: Print: the count and ids of `ended` batches with no ledger entry, their `succeeded` totals, their `results_url`, days remaining before the 29-day archival, and the billed batch spend they represent. Recommend a reconciliation sweep (list → diff against ledger → stream results, keying by `custom_id` since order is not guaranteed). Do not download.
- **category**: Batch and async
- **sources**: https://platform.claude.com/docs/en/build-with-claude/batch-processing · https://platform.claude.com/docs/en/api/messages/batches/list · https://platform.claude.com/docs/en/manage-claude/usage-cost-api

## batch-queue-limit-reached

- **slug**: `batch-queue-limit-reached`
- **title**: The enqueued batch-request limit blocks new submissions
- **symptom**: `429 rate_limit_error` on `POST /v1/messages/batches` even though the Messages API model limits are nowhere near saturated, or new batches sit at `processing_status: "in_progress"` with a large `request_counts.processing` and drift toward their 24-hour `expires_at`.
- **mechanism**: The Message Batches API has its own limits, **shared across all models**: an RPM limit on the endpoints, a cap on batch requests in the processing queue, and a per-batch cap. Enqueued batch requests: Start **200,000**, Build **300,000**, Scale **500,000**. Per batch: **100,000** requests or **256 MB**, whichever comes first, at every tier. Batch endpoint RPM: 1,000 / 2,000 / 4,000. "A batch request is considered part of the processing queue when it has yet to be successfully processed by the model" — so one giant unfinished batch can starve every later submission across the whole org.
- **detect**: Admin API key: `GET /v1/organizations/rate_limits?group_type=batch` returns the configured `enqueued_batch_requests` value for the org (and the workspace endpoint returns any override, with `org_limit` alongside). Workspace/project key: `GET /v1/messages/batches?limit=1000` and sum `request_counts.processing` across every batch with `processing_status` of `in_progress` or `canceling` — that sum is your live queue depth against the ceiling.
- **repair**: Print: current queue depth vs the configured `enqueued_batch_requests`, the batches contributing most `processing` requests with their `expires_at`, and the per-batch caps. Recommend splitting submissions and draining before enqueuing more. Do not cancel any batch.
- **category**: Batch and async
- **sources**: https://platform.claude.com/docs/en/api/rate-limits · https://platform.claude.com/docs/en/manage-claude/rate-limits-api · https://platform.claude.com/docs/en/build-with-claude/batch-processing

## batch-tier-never-used

- **slug**: `batch-tier-never-used`
- **title**: The 50% Batch API discount is never used
- **symptom**: No error. Grouping the usage report by `service_tier` returns only `standard` — no result ever carries `service_tier: "batch"` — even though a substantial share of traffic is non-interactive (nightly jobs, backfills, evaluation runs).
- **mechanism**: The Message Batches API discounts **both input and output by 50%** (Opus 5 at $2.50 / $12.50 per MTok instead of $5 / $25). It is opt-in per request path, and there is no automatic routing: a job that could tolerate asynchronous completion but calls `POST /v1/messages` directly pays full price forever. Batch and prompt-caching discounts stack, so the two together are the largest available saving on bulk work.
- **detect**: Admin API key required. `GET /v1/organizations/usage_report/messages?starting_at= {T-30d}&bucket_width=1d&limit=31&group_by[]=service_tier&group_by[]=api_key_id`. Check the distinct `service_tier` values returned across all buckets against the full enum — `batch`, `flex`, `flex_discount`, `priority`, `priority_on_demand`, `standard`. If `batch` never appears, no batch traffic exists. Look for candidate keys whose token volume is concentrated in a narrow nightly window in an hourly report (`bucket_width=1h&limit=168`).
- **repair**: Print, do not run: list the `api_key_id` values whose traffic is time-clustered and therefore batch-eligible, with the 50% saving computed at published rates. Re-check `service_tier` grouping after the owning team migrates.
- **category**: Batch and async
- **sources**: https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report · https://platform.claude.com/docs/en/manage-claude/usage-cost-api

## org-verification-required

- **slug**: `org-verification-required`
- **title**: Unverified org can call a model but cannot stream it
- **symptom**: Non-streaming calls return `200`. Adding `"stream": true` returns `400` `invalid_request_error` with `code: "unsupported_value"`, `param: "stream"`, message `Your organization must be verified to stream this model. Please go to: https://platform.openai.com/settings/organization/general and click on Verify Organization.` Some models instead 404 outright with `Your organization must be verified to use the model '<id>'`. Reasoning summaries (`reasoning.summary`) are gated the same way.
- **mechanism**: OpenAI requires government-ID organization verification for streaming and reasoning summaries on advanced models, historically for tiers 1–3 (tiers 4–5 were exempt for o3/o4-mini). Because the non-streaming path works, the failure only appears on the streaming code path — often only in the UI-facing route, not in batch jobs or tests. Propagation takes up to 15 minutes after verifying, and one government ID can verify only one org per 90 days.
- **detect**: Project read-only key → `GET /v1/models/{model}` returns `200` (model is visible) while the app's streaming route 400s — that pairing isolates verification rather than access. Admin-read key → `GET /v1/organization/usage/completions?start_time=<24h ago>&bucket_width=1h&group_by[]=model&group_by[]=api_key_id`: the key serving the streaming route shows `num_model_requests` with zero `output_tokens` while a sibling key on the same model produces output normally.
- **repair**: Verify the organization at platform.openai.com/settings/organization/general (allow 15 minutes to propagate). As a stopgap, print the fallback: set `stream=False` on the affected route and buffer the full response, and remove `reasoning={"summary": ...}` until verification lands.
- **category**: Keys, projects and access
- **sources**: https://help.openai.com/en/articles/10910291-api-organization-verification · https://github.com/RooCodeInc/Roo-Code/issues/6868

## unsupported-country-region

- **slug**: `unsupported-country-region`
- **title**: Requests from an unsupported region are blocked with 403
- **symptom**: `403` `PermissionDeniedError` with `code: "unsupported_country_region_territory"`, message `Country, region, or territory not supported.` Failure is total from the affected host and works fine from a developer laptop, so it typically appears only after deploying to a new cloud region or edge runtime.
- **mechanism**: OpenAI geo-blocks by the *request's* egress IP, not by account country. Deploying to a non-US cloud region (reported cases: GCP `asia-northeast3`, edge functions running in Hong Kong), routing through a VPN, or letting an edge platform pick a nearby PoP moves the egress IP into a blocked geography. Cloudflare Workers and Vercel/Supabase edge functions relocate execution silently, so the same code can pass in CI and fail in production.
- **detect**: Run the read-only script **from the production egress path** (same VPC/region/edge runtime) and issue `GET /v1/models` with the project read-only key: a `200` proves the geography is allowed from that host, a `403` with `code: "unsupported_country_region_territory"` proves it is not. Comparing against the same call from a known-good host isolates it to geography rather than credentials. Also `GET /v1/organization/usage/completions?group_by[]=project_id` — a project with zero requests despite deployed traffic corroborates a hard block.
- **repair**: Pin execution to a supported region. For edge functions, add the runtime's region pin (e.g. Vercel `export const config = { regions: ['iad1'] }`); for Cloud Run/Lambda, redeploy in a US region; for a VPN, disable it or route the OpenAI host through a US egress. Do not attempt to mask the region — print the region-pin change, not a proxy.
- **category**: Keys, projects and access
- **sources**: https://developers.openai.com/api/docs/guides/error-codes · https://community.openai.com/t/cloud-run-in-asia-northeast3-suddenly-getting-unsupported-country-region-territory-error-from-openai-api/1279969

## single-api-key-generates-all-spend

- **slug**: `single-api-key-generates-all-spend`
- **title**: A single API key accounts for nearly all org spend
- **symptom**: No error. Grouping cost by `api_key_id` returns one row that is essentially the whole bill. When something starts costing money, there is no way to tell which service, environment, or customer did it — the answer is always "the key".
- **mechanism**: One key gets minted during the first integration and then propagated: into CI, into the staging env file, into a teammate's laptop, into a second service, into a notebook. Each copy is invisible. The key becomes a shared bus with no attribution and no blast radius control — you cannot rotate it without an unknown number of outages, and you cannot rate-limit or budget one consumer without affecting all of them.
- **detect**: Organization **ADMIN** key required. `GET /v1/organization/costs?start_time={now-30d}&limit=30&group_by=api_key_id` and compute each `api_key_id`'s share of summed `amount.value`. Flag when one key holds more than 80% of spend while the org has more than one active project. Confirm the breadth with `GET /v1/organization/usage/completions?start_time={now-7d}&group_by=api_key_id&group_by=model`: a shared key shows an implausibly wide spread of distinct `model` values under one `api_key_id`. Resolve the key to a human-readable identity via `GET /v1/organization/projects/{project_id}/api_keys`, matching on `id`; each `organization.project.api_key` returns `name`, `redacted_value`, `created_at`, `last_used_at`, and `owner.type` (`"user"` or `"service_account"`).
- **repair**: Print the key's `name`, `redacted_value`, `created_at`, and its share of spend. Recommend one key per deployable unit: create a service account per service with `POST /v1/organization/projects/{project_id}/service_accounts`, mint its key with `POST /v1/organization/projects/{project_id}/service_accounts/{service_account_id}/api_keys`, cut services over one at a time, then `DELETE /v1/organization/projects/{project_id}/api_keys/{api_key_id}`. Print the commands; do not run them.
- **category**: Keys, projects and access
- **sources**: https://platform.openai.com/docs/api-reference/project-api-keys · https://platform.openai.com/docs/api-reference/usage/costs · https://github.com/openai/openai-python/blob/main/api.md

## api-key-never-used

- **slug**: `api-key-never-used`
- **title**: Project API keys exist that have never been used once
- **symptom**: No error — that is the whole problem. `GET /v1/organization/projects/{project_id}/api_keys` returns keys whose `last_used_at` is `null`, sometimes years after `created_at`. Each is a live credential with full project access that no system depends on.
- **mechanism**: Keys are created during debugging, during onboarding, for a spike that got abandoned, or "just in case" for a vendor evaluation that went nowhere. Creation is one click; deletion requires someone to be confident nothing breaks. Since an unused key produces no signal — no traffic, no cost, no log line — nothing ever prompts the cleanup, and the key sits in whatever Slack DM or `.env.example` it was pasted into.
- **detect**: Organization **ADMIN** key required. Enumerate projects with `GET /v1/organization/projects?limit=100&include_archived=true`, then for each `id` call `GET /v1/organization/projects/{project_id}/api_keys?limit=100&owner_project_access=any`. Pass `owner_project_access=any` explicitly: without it the endpoint applies membership-based visibility rules that can hide enabled keys from your audit. Flag every `organization.project.api_key` where `last_used_at` is `null` **and** `created_at` is older than 30 days. Report `id`, `name`, `redacted_value`, `created_at`, and `owner.type`.
- **repair**: Print each never-used key as `name` + `redacted_value` + age in days, and the exact revocation call: `DELETE /v1/organization/projects/{project_id}/api_keys/{api_key_id}`. Because a never-used key by definition has no traffic to break, note that these are the safest keys in the org to delete — but still print rather than execute.
- **category**: Keys, projects and access
- **sources**: https://platform.openai.com/docs/api-reference/project-api-keys · https://platform.openai.com/docs/api-reference/projects · https://github.com/openai/openai-python/blob/main/api.md

## api-key-dormant-for-months

- **slug**: `api-key-dormant-for-months`
- **title**: A live API key has not been used in months
- **symptom**: No error. A key has a real `last_used_at` — it was genuinely load-bearing once — but the timestamp is 6, 12, or 24 months old. The service it belonged to was decommissioned, migrated, or rewritten, and the credential outlived it.
- **mechanism**: Decommissioning a service is a checklist item; revoking its API key is a checklist item someone else owns. The key remains valid indefinitely (project API keys have no expiry — unlike admin keys, whose `organization.admin_api_key` object carries an optional `expires_at`). It survives in old container images, in a Terraform state file, in a backup of a `.env`. Every copy is a working credential with the same permissions the live service had.
- **detect**: Organization **ADMIN** key required. For each project from `GET /v1/organization/projects?limit=100`, call `GET /v1/organization/projects/{project_id}/api_keys?limit=100&owner_project_access=any`. Flag any key where `last_used_at` is non-null but older than 90 days. Note that `last_used_at` is the *only* usage signal on the key object — for spend attribution you must cross-reference `GET /v1/organization/costs?start_time=…&group_by=api_key_id` and match on `api_key_id`; a dormant key should be absent from those results entirely, which is your confirmation. Do the same sweep over `GET /v1/organization/admin_api_keys`, whose `AdminAPIKey` object also exposes `last_used_at`, `expires_at`, `redacted_value`, and `owner`.
- **repair**: Print `name`, `redacted_value`, `last_used_at` as a human date, and days dormant. Recommend a rotation policy (revoke anything unused for 90 days) and print `DELETE /v1/organization/projects/{project_id}/api_keys/{api_key_id}` for each. For admin keys, print `DELETE /v1/organization/admin_api_keys/{key_id}` and recommend setting `expires_at` on replacements so dormancy self-corrects.
- **category**: Keys, projects and access
- **sources**: https://platform.openai.com/docs/api-reference/project-api-keys · https://developers.openai.com/api/docs/guides/admin-apis · https://github.com/openai/openai-python/blob/main/api.md

## key-owner-lost-project-access

- **slug**: `key-owner-lost-project-access`
- **title**: Keys still work whose owner no longer has project access
- **symptom**: No error, and the key keeps billing. Someone left the company or was removed from a project months ago; their personal API key is still valid and still serving production traffic, or still sitting in a laptop backup. Offboarding was marked complete.
- **mechanism**: A project API key owned by a *user* (rather than a service account) does not die when that user's membership does — the credential is independent of the membership record. Removing the person from the org or the project revokes their console access, not their key material. The API models this explicitly: every `organization.project.api_key` carries `owner_project_access`, which flips to `"inactive"` when the owning principal no longer has effective access to the project, while the key itself remains enabled and usable.
- **detect**: Organization **ADMIN** key required. This is the single highest-value call in the whole admin surface: for each project, `GET /v1/organization/projects/{project_id}/api_keys?limit=100&owner_project_access=inactive`. Every object returned is a live key whose owner has lost access. Report `id`, `name`, `redacted_value`, `owner.type`, `owner.user.email`, and `last_used_at`. Corroborate with `GET /v1/organization/users?limit=100` (the `organization.user` object exposes `email`, `role`, `added_at`, and `api_key_last_used_at`) — an email present on a key but absent from the users list is a departed member. Then confirm the timeline via `GET /v1/organization/audit_logs?event_types[]=user.deleted&event_types[]=api_key.created`, comparing `effective_at` values.
- **repair**: Print each key as `owner.user.email` + `name` + `redacted_value` + `last_used_at`, sorted by most recently used first (those are the ones with production traffic and therefore real breakage risk). Recommend re-issuing under a service account before revoking, then `DELETE /v1/organization/projects/{project_id}/api_keys/{api_key_id}`. Add the offboarding checklist item: run the `owner_project_access=inactive` sweep as a scheduled job, not a manual one.
- **category**: Keys, projects and access
- **sources**: https://platform.openai.com/docs/api-reference/project-api-keys · https://github.com/openai/openai-python/blob/main/api.md · https://platform.openai.com/docs/api-reference/audit-logs

## legacy-user-owned-keys-in-project

- **slug**: `legacy-user-owned-keys-in-project`
- **title**: Production keys are owned by people, not service accounts
- **symptom**: No error. `GET /v1/organization/projects/{project_id}/api_keys` shows production traffic flowing through keys whose `owner.type` is `"user"` — an individual engineer's personal credential is the thing keeping the service up.
- **mechanism**: Personal keys are the path of least resistance: any project member can mint one, and it works immediately. Service accounts require thinking about the project structure first. The consequence is that the credential's lifecycle is bound to a person's employment rather than to the service's lifecycle — the key dies (or should die) when they leave, and until it does, spend and audit-log actions attribute to a human who may have had nothing to do with the traffic for a year.
- **detect**: Organization **ADMIN** key required. For each project, `GET /v1/organization/projects/{project_id}/api_keys?limit=100&owner_project_access=any` and filter on `owner.type == "user"`. The owner block carries `owner.user.id`, `owner.user.email`, `owner.user.name`, and `owner.user.role`. Cross-reference `GET /v1/organization/costs?start_time={now-30d}&group_by=api_key_id` to find which of those user-owned keys carry real money — a user-owned key with meaningful `amount.value` is production traffic on a personal credential. Compare against `GET /v1/organization/projects/{project_id}/service_accounts`, which returns `organization.project.service_account` objects with `id`, `name`, `role` (`"owner"` / `"member"` / `"none"`), and `created_at`; an empty list here alongside spending user keys is the clearest form of the finding.
- **repair**: Print each user-owned key with `owner.user.email`, 30-day spend, and `last_used_at`. Print the migration: `POST /v1/organization/projects/{project_id}/service_accounts` with `{"name": "<service-name>"}`, then `POST /v1/organization/projects/{project_id}/service_accounts/{service_account_id}/api_keys` to mint the replacement, deploy it, verify traffic moved by re-checking `group_by=api_key_id`, then `DELETE` the old key. Note that the service-account key value is returned exactly once at creation.
- **category**: Keys, projects and access
- **sources**: https://platform.openai.com/docs/api-reference/project-api-keys · https://platform.openai.com/docs/api-reference/projects · https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform

## service-account-key-never-rotated

- **slug**: `service-account-key-never-rotated`
- **title**: A service account key has never been rotated since creation
- **symptom**: No error. The org did the right thing — production runs on service accounts, not personal keys — but `created_at` on those service accounts and their keys is two years old and there is no second key, no overlap window, and no rotation history in the audit log.
- **mechanism**: Service accounts solve ownership but not freshness. Because a service-account key never expires and nothing prompts rotation, "we use service accounts" quietly becomes "we have a permanent, never-changed credential in production". Rotation is also genuinely risky when there is only ever one key: swapping it is a hard cutover with no rollback, so it keeps getting deferred. The right pattern — mint a second key, deploy, verify, revoke the first — requires two keys to coexist, which the current state never has.
- **detect**: Organization **ADMIN** key required. For each project: `GET /v1/organization/projects/{project_id}/service_accounts?limit=100` for the roster (`id`, `name`, `role`, `created_at`), then `GET /v1/organization/projects/{project_id}/api_keys?limit=100&owner_project_access=any` filtered to `owner.type == "service_account"`. For each service account, take the max `created_at` across its keys — flag any where that is older than 180 days. The absence of rotation is confirmable directly: `GET /v1/organization/audit_logs?event_types[]=api_key.created&effective_at[gte]={now-180d}&limit=100` returns `api_key.created` events with `id`, `data.scopes`, `effective_at`, `project.id`, and `actor` — if no event exists for that project, no key has been minted there in six months.
- **repair**: Print each service account with its oldest key age in days, `name`, and `redacted_value`. Print the zero-downtime rotation as an ordered sequence: mint via `POST /v1/organization/projects/{project_id}/service_accounts/{service_account_id}/api_keys`, deploy the new value, confirm the old key's `last_used_at` stops advancing, then `DELETE /v1/organization/projects/{project_id}/api_keys/{api_key_id}`. Recommend a 90-day cadence.
- **category**: Keys, projects and access
- **sources**: https://platform.openai.com/docs/api-reference/projects · https://platform.openai.com/docs/api-reference/audit-logs · https://github.com/openai/openai-python/blob/main/api.md

## no-prod-dev-project-separation

- **slug**: `no-prod-dev-project-separation`
- **title**: Prod and dev share one project, so spend cannot be split
- **symptom**: No error. `GET /v1/organization/projects` returns one project (often named `Default project`) carrying 100% of org spend. Nobody can answer "how much does production actually cost" because experiments, local development, CI, and customer traffic all land in the same bucket.
- **mechanism**: The default project is created for you and works immediately, so there is never a moment where you are forced to choose a structure. But the project is the unit of nearly every control OpenAI offers: rate limits, spend limits, spend alerts, model permissions, hosted tool permissions, and data retention are all configured per project. Collapsing everything into one means none of those controls can be applied differentially — you cannot cap dev spend without capping prod, or grant `o3` to research without granting it to the batch job.
- **detect**: Organization **ADMIN** key required. `GET /v1/organization/projects?limit=100&include_archived=false`. Each `organization.project` returns `id`, `name`, `created_at`, `archived_at`, `status` (`"active"` / `"archived"`), and optionally `residency`. Flag when the count of `status == "active"` projects is 1, or when `GET /v1/organization/costs?start_time={now-30d}&limit=30&group_by=project_id` shows a single `project_id` holding over 95% of `amount.value`. A supporting signal: `GET /v1/organization/projects/{project_id}/api_keys?owner_project_access=any` returning keys whose `name` values mix environments (`"staging"`, `"local"`, `"prod"`) inside one project.
- **repair**: Print the current project list with 30-day spend per project. Recommend at minimum three projects — `prod`, `staging`, `dev` — created with `POST /v1/organization/projects`, each with its own service account and key, its own `POST /v1/organization/projects/{project_id}/spend_limit`, and its own rate limits. Note that projects can be archived but not deleted, so the split is one-way; get the names right the first time.
- **category**: Keys, projects and access
- **sources**: https://platform.openai.com/docs/api-reference/projects · https://help.openai.com/en/articles/9186755-managing-projects-in-the-api-platform · https://developers.openai.com/api/docs/guides/admin-apis

## archived-project-still-holds-keys

- **slug**: `archived-project-still-holds-keys`
- **title**: An archived project still holds live API keys
- **symptom**: No error. A project was archived to signal "we're done with this", but its API keys were never enumerated or revoked. Worse, the project no longer appears in the default `GET /v1/organization/projects` listing, so routine key audits skip it entirely — the keys are both live and invisible.
- **mechanism**: Archiving is a visibility operation, not a revocation operation. `POST /v1/organization/projects/{project_id}/archive` sets `archived_at` and flips `status` to `"archived"`, which removes the project from default listings and from the console's project switcher. It does not enumerate, disable, or delete the credentials inside. Any audit script that iterates projects without `include_archived=true` will therefore under-report the org's live key surface, and the archived project's keys become the org's least-monitored credentials.
- **detect**: Organization **ADMIN** key required, and the parameter is the whole trick. Call `GET /v1/organization/projects?limit=100&include_archived=true` — archived projects are excluded by default. Filter to `status == "archived"` (equivalently, `archived_at != null`), then for each call `GET /v1/organization/projects/{project_id}/api_keys?limit=100&owner_project_access=any`. Any key returned is live inside a project everyone considers closed. Escalate anything whose `last_used_at` is recent — that means the archived project is still serving traffic. Corroborate with `GET /v1/organization/costs?start_time={now-30d}&group_by=project_id`: an archived `project_id` with non-zero `amount.value` is an archived project that is still billing.
- **repair**: Print each archived project's `name`, `archived_at`, live key count, and any non-zero recent spend. Print `DELETE /v1/organization/projects/{project_id}/api_keys/{api_key_id}` per key. Add the durable fix to the output: every key-audit job must pass `include_archived=true`, or it is auditing a subset of the org by construction.
- **category**: Keys, projects and access
- **sources**: https://platform.openai.com/docs/api-reference/projects · https://platform.openai.com/docs/api-reference/project-api-keys · https://github.com/openai/openai-python/blob/main/api.md

## openai-invites-pending-past-expiry

- **slug**: `openai-invites-pending-past-expiry`
- **title**: Organization invites have sat pending until they expired
- **symptom**: No error. New team members report they "never got access", or quietly work around it by borrowing a colleague's API key. Meanwhile `GET /v1/organization/invites` is full of `status: "pending"` and `status: "expired"` rows going back months, several of them for people who have since left.
- **mechanism**: An invite is fire-and-forget: it lands in an email that gets filtered, or the recipient accepts the ChatGPT invite and assumes it covers the API platform. Nothing chases it. Invites carry `expires_at` and transition to `"expired"` on their own, but that transition produces no notification to the sender either. The security half is worse than the access half — a pending invite for a candidate who was never hired, or an employee who has since departed, is a standing offer of org membership that nobody is watching.
- **detect**: Organization **ADMIN** key required. `GET /v1/organization/invites?limit=100`. Each `organization.invite` returns `id`, `email`, `role` (`"owner"` or `"reader"`), `status` (`"accepted"` / `"expired"` / `"pending"`), `created_at`, `expires_at`, `accepted_at`, and `projects[]` (each with `id` and `role` of `"member"` / `"owner"`). Flag: any `status == "pending"` where `created_at` is older than 14 days; any `status == "pending"` where `expires_at` is already in the past (a stale record that should be cleaned up); and — highest priority — any pending or expired invite with `role == "owner"`, since that is an unclaimed grant of full org control. Cross-check `GET /v1/organization/users?limit=100` to see whether the invitee already exists under a different email. Reconstruct the history with `GET /v1/organization/audit_logs?event_types[]=invite.sent&event_types[]=invite.accepted&event_types[]=invite.deleted`; the `invite.sent` payload carries `data.email` and `data.role`.
- **repair**: Print each stale invite as `email` + `role` + `projects[]` + age in days + `expires_at`. For invites that should proceed, print `DELETE /v1/organization/invites/{invite_id}` followed by a fresh `POST /v1/organization/invites`. For everything else — departed people, wrong addresses, abandoned hires — print just the `DELETE`. Call out `role: "owner"` rows first.
- **category**: Keys, projects and access
- **sources**: https://platform.openai.com/docs/api-reference/invite · https://platform.openai.com/docs/api-reference/audit-logs · https://github.com/openai/openai-python/blob/main/api.md

## too-many-organization-owners

- **slug**: `too-many-organization-owners`
- **title**: Almost every org member holds the owner role
- **symptom**: No error. `GET /v1/organization/users` returns a roster where most or all entries have `role: "owner"`. Anyone in the list can mint admin keys, create and archive projects, change rate limits, alter billing, invite new owners, and remove other members.
- **mechanism**: The org role model is coarse — `owner` or `reader` — and `reader` is genuinely restrictive, so the first time someone needs to do anything (create a project, add a key, change a limit) the fastest unblock is to promote them to owner. Nobody demotes anyone afterward, because demotion is a visible act with social cost and no forcing function. Over a year the distinction erodes to nothing, and the org loses the ability to say who is accountable for a configuration change.
- **detect**: Organization **ADMIN** key required. `GET /v1/organization/users?limit=100` (paginate on `after`; this endpoint also uniquely accepts an `emails[]` filter for targeted lookups). Each `organization.user` object returns `id`, `email`, `name`, `role` (`"owner"` / `"reader"`), `added_at`, `api_key_last_used_at`, `is_service_account`, `is_scim_managed`, and — when included — `projects.data[]` with per-project `role`. Compute the owner ratio, excluding `is_service_account == true`. Flag when owners exceed 50% of human members, or when the absolute owner count exceeds 5. Two sharpening cross-checks: flag owners whose `api_key_last_used_at` is `null` or very old (privilege held by someone not actually using the platform), and list who holds admin credentials via `GET /v1/organization/admin_api_keys`, reading `owner.name` and `owner.id` on each `organization.admin_api_key`. Review role churn with `GET /v1/organization/audit_logs?event_types[]=user.updated&event_types[]=user.added&event_types[]=role.assignment.created`.
- **repair**: Print the roster as `email` + `role` + `added_at` + `api_key_last_used_at`, owners first, and the owner ratio. Recommend demoting to `reader` anyone who does not administer billing, keys, or projects, via `POST /v1/organization/users/{user_id}` with `{"role": "reader"}`, and granting per-project rights instead with `POST /v1/organization/projects/{project_id}/users` (`role` of `"member"` or `"owner"` scoped to that project only). Print the calls; do not run them.
- **category**: Keys, projects and access
- **sources**: https://platform.openai.com/docs/api-reference/administration · https://platform.openai.com/docs/api-reference/audit-logs · https://github.com/openai/openai-python/blob/main/api.md

## unreviewed-key-lifecycle-in-audit-log

- **slug**: `unreviewed-key-lifecycle-in-audit-log`
- **title**: API keys were created or deleted and nobody reviewed it
- **symptom**: No error and no alert. The audit log faithfully records every `api_key.created`, `api_key.updated`, and `api_key.deleted` event — and nobody has ever read it. A key minted at 2am by an actor nobody recognizes, or a production key deleted during an outage, sits in the log unexamined.
- **mechanism**: The Audit Logs API is pull-only: there is no webhook, no email, and no default alerting. It captures exactly the events you would want to be paged on — credential creation and deletion, invite lifecycle, service account lifecycle, role assignment, `login.failed`, SCIM and SSO changes — and stores them, waiting. Because reviewing it requires standing up a job, and because the log is silent when healthy, it is the classic control that exists on paper and has never fired. Note also that audit logging is generally gated to orgs that have it enabled; a script that finds the endpoint empty should say so rather than report "clean".
- **detect**: Organization **ADMIN** key required. `GET /v1/organization/audit_logs?effective_at[gte]={now-7d}&limit=100&event_types[]=api_key.created&event_types[]=api_key.deleted&event_types[]=api_key.updated&event_types[]=service_account.created&event_types[]=service_account.deleted&event_types[]=login.failed` (`limit` 1–100 default 20; paginate with `after`/`before`; filter further with `actor_emails[]`, `actor_ids[]`, `project_ids[]`, `resource_ids[]`, and `tenant_only` for `tenant.*` events). Each entry returns `id`, `type`, `effective_at`, `project.id` / `project.name`, and `actor`. `actor.type` is `"session"` or `"api_key"`; a **session** actor is the forensically rich one — `actor.session.user.email`, `actor.session.ip_address`, `actor.session.user_agent`, TLS fingerprints `actor.session.ja3` / `ja4`, and `actor.session.ip_address_details` with `country`, `city`, `region`, `asn`, `latitude`, `longitude`. An **api_key** actor carries `actor.api_key.id` (a tracking id), `actor.api_key.type`, and either `actor.api_key.user.email` or `actor.api_key.service_account.id`. The event-specific payload hangs off a sibling key named exactly after the event type — `"api_key.created"` with `data.scopes`, `"api_key.updated"` with `changes_requested.scopes`, `"api_key.deleted"` with `id` (in the Python SDK these are pydantic aliases, e.g. attribute `api_key_created`). Flag: any `api_key.created` whose `ip_address_details.country` is outside your operating geographies, any burst of `login.failed`, and any `api_key.created` whose `effective_at` falls outside business hours. This endpoint is also the one admin path that declares its own `429` with `Retry-After`, so back off rather than hammering it.
- **repair**: Print each unreviewed event as `effective_at` + `type` + actor email + `ip_address` + `project.name`. Recommend a scheduled read-only job polling `effective_at[gte]` = last watermark, routing `api_key.created`, `api_key.deleted`, `service_account.created`, `user.added`, and `login.failed` to an alerting channel. Note that admin actions taken via an Admin API key are attributed to the default project, so `project` on those entries is not meaningful.
- **category**: Keys, projects and access
- **sources**: https://platform.openai.com/docs/api-reference/audit-logs · https://help.openai.com/en/articles/9687866-admin-and-audit-logs-api-for-the-api-platform · https://github.com/openai/openai-python/blob/main/api.md

## zero-data-retention-not-configured

- **slug**: `zero-data-retention-not-configured`
- **title**: Zero data retention was assumed but never configured
- **symptom**: No error. A customer questionnaire, a DPA, or a security review asserts that prompts and completions are not retained. `GET /v1/organization/data_retention` says otherwise — or the project a regulated workload runs in inherits the org default rather than the stricter setting someone believes was applied.
- **mechanism**: Retention posture is configuration, not a property of the API, and it is set at two levels that can disagree. The organization has a default; each project can override it or inherit via `organization_default`. Teams that negotiated ZDR at the account level frequently never propagate it, or create a *new* project later that inherits a default set before the negotiation. Nothing in the request or response path indicates the current retention mode, so the only way to know is to ask the admin endpoint — and nobody does, because the answer was assumed at contract-signing time.
- **detect**: Organization **ADMIN** key required. `GET /v1/organization/data_retention` returns an `organization.data_retention` object whose `type` is one of `zero_data_retention`, `modified_abuse_monitoring`, `enhanced_zero_data_retention`, or `enhanced_modified_abuse_monitoring`. Then, for every project from `GET /v1/organization/projects?limit=100&include_archived=true`, call `GET /v1/organization/projects/{project_id}/data_retention`, which returns `project.data_retention` with `type` drawn from a wider set that adds `organization_default` and `none`. Flag any project whose effective retention is weaker than the posture you claim — in particular any project resolving to `none`, and any project on `organization_default` when the org default is not a ZDR variant. While you are there, read `residency` off each `organization.project` (values include `GLOBAL`, `US_STORAGE_PROCESSING`, `EU_STORAGE_PROCESSING`, and country-specific storage options) and flag any project whose data residency does not match its jurisdictional commitment. Confirm nothing has drifted with `GET /v1/organization/audit_logs?event_types[]=organization.updated&event_types[]=project.updated`.
- **repair**: Print a per-project table of `name`, effective retention `type`, and `residency`, with the org default at the top and mismatches highlighted. Print the corrective call — `POST /v1/organization/projects/{project_id}/data_retention` — and flag the asymmetry that trips people up: the **request** body field is `retention_type` while the **response** field is `type`. Note that ZDR and enhanced variants generally require enablement on the account by OpenAI rather than being self-serve, so the script should say "request this", not "set this". Never execute a retention change from an audit script.
- **category**: Keys, projects and access
- **sources**: https://platform.openai.com/docs/guides/your-data · https://developers.openai.com/api/docs/guides/admin-apis · https://github.com/openai/openai-python/blob/main/api.md

## project-model-permissions-unrestricted

- **slug**: `project-model-permissions-unrestricted`
- **title**: Any model can be called from any project, including costly ones
- **symptom**: No error — the call just succeeds. A scratch project, a demo, or a CI job reaches for the org's most expensive frontier model and gets it, because no project in the org has a model allowlist configured. The same is true of hosted tools: web search, code interpreter, and file search are billable and enabled everywhere by default.
- **mechanism**: Model access defaults to open across the org: every project can call every model the org is entitled to, and every hosted tool is available. The controls exist (`model_permissions` and `hosted_tool_permissions` per project) but are opt-in and per-project, so a new project created a year after the policy was written silently inherits none of it. This is what turns the "expensive model on trivial work" problem from a code review issue into a structural one — there is no mechanism preventing the mistake, only the hope that nobody makes it.
- **detect**: Organization **ADMIN** key required. For each project from `GET /v1/organization/projects?limit=100`, call `GET /v1/organization/projects/{project_id}/model_permissions`, which returns a `project.model_permissions` object with `mode` (`"allow_list"` or `"deny_list"`) and `model_ids[]`. Flag any project with no policy configured, any `deny_list` that is empty (functionally unrestricted), and any `allow_list` containing frontier models in a project whose 30-day spend from `GET /v1/organization/costs?group_by=project_id` says it is a low-value environment. Separately call `GET /v1/organization/projects/{project_id}/hosted_tool_permissions`, which returns `project.hosted_tool_permissions` with a nested `{"enabled": bool}` for each of `code_interpreter`, `file_search`, `image_generation`, `mcp`, and `web_search`; flag `enabled: true` for tools the project has no usage for — confirm with `GET /v1/organization/usage/web_search_calls` and `/v1/organization/usage/code_interpreter_sessions` grouped by `project_id`, where zero `num_requests` / `num_sessions` alongside `enabled: true` is unused attack and cost surface.
- **repair**: Print, per project: current `mode` and `model_ids[]` (or "unrestricted"), the models actually used in the last 30 days from `GET /v1/organization/usage/completions?group_by=model&group_by=project_id`, and the enabled hosted tools versus the used ones. Print a least-privilege `POST /v1/organization/projects/{project_id}/model_permissions` body — `{"mode": "allow_list", "model_ids": [<models actually observed>]}` — and a `POST …/hosted_tool_permissions` body disabling the unused tools. Recommend adding both to project-creation automation so new projects start restricted.
- **category**: Keys, projects and access
- **sources**: https://developers.openai.com/api/docs/guides/admin-apis · https://platform.openai.com/docs/api-reference/projects · https://github.com/openai/openai-python/blob/main/api.md

## stored-responses-accumulating

- **slug**: `stored-responses-accumulating`
- **title**: `store: true` is the default and every response is retained
- **symptom**: No error. `GET /v1/responses/{id}` succeeds for responses you thought were ephemeral, returning full `input` and `output` including any customer data. Retention is *"at least 30 days"* for stored response data. There is **no** `GET /v1/responses` list endpoint, so you cannot enumerate what you are holding.
- **mechanism**: The Responses API stores responses by default so that `previous_response_id` threading and background mode work. Every prompt and completion — PII, secrets pasted by users, retrieved document text — is persisted server-side unless you explicitly pass `store: false` (which Zero Data Retention orgs get forced to anyway). Because there is no list-all endpoint, the only inventory is the one you keep yourself.
- **detect**: Sample response ids from your own logs and call `GET /v1/responses/{response_id}`; a 200 proves the response is stored and readable, and the echoed `store` field confirms the setting. `GET /v1/responses/{response_id}/input_items` shows exactly what input was retained. Size the exposure at org level with `GET /v1/organization/usage/completions?start_time=...&bucket_width=1d` (**admin read key**) for request volume. Requires: project read key; admin read key for volume.
- **repair**: print — `Decide store per call rather than by default: pass store: false for anything carrying regulated data, and keep store: true only where you actually use previous_response_id, conversations or background mode. Delete what you no longer need with DELETE /v1/responses/{response_id}. Maintain your own index of stored response ids since the API offers no list endpoint. If you need a blanket guarantee, pursue Zero Data Retention — under ZDR store is always treated as false.`
- **category**: Keys, projects and access
- **sources**: https://developers.openai.com/api/docs/guides/your-data · https://developers.openai.com/api/docs/api-reference/responses

## conversations-never-deleted

- **slug**: `conversations-never-deleted`
- **title**: Conversations persist "until deleted" with no list endpoint
- **symptom**: `GET /v1/conversations/{conversation_id}` returns 200 for conversations created months ago, and `GET /v1/conversations/{conversation_id}/items` replays the whole transcript. Conversation data is retained *until deleted*. There is no `GET /v1/conversations` list-all endpoint — lose the id and the data stays but becomes uninventoriable.
- **mechanism**: Conversations are the Responses-era replacement for Assistants threads and are the recommended threading primitive. Each `POST /v1/responses` with a `conversation` appends items indefinitely. Nothing expires them, nothing caps their length, and a conversation that grows without bound also grows the input tokens billed on every subsequent turn in that thread.
- **detect**: Take conversation ids from your own datastore and probe `GET /v1/conversations/{conversation_id}` (200 = still live) and `GET /v1/conversations/{conversation_id}/items?limit=100`, paginating to count items and spot runaway threads. Flag any conversation whose last item predates your retention window, and any whose item count is large enough to dominate per-turn input cost. Cross-check growth in `input_tokens` via `GET /v1/organization/usage/completions?...&bucket_width=1d` (**admin read key**). Requires: project read key; admin read key for cost trend.
- **repair**: print — `Own the lifecycle: store every conversation id with a created_at, and run a scheduled sweep calling DELETE /v1/conversations/{conversation_id} past your retention window. Trim individual turns with DELETE /v1/conversations/{conversation_id}/items/{item_id}, or start a fresh conversation seeded with a summary once a thread gets long, so input tokens stop compounding.`
- **category**: Keys, projects and access
- **sources**: https://developers.openai.com/api/docs/api-reference/conversations · https://developers.openai.com/api/docs/guides/your-data

## default-workspace-cost-unattributable

- **slug**: `default-workspace-cost-unattributable`
- **title**: Default-workspace cost cannot be attributed to a team
- **symptom**: No error. A large share of cost-report rows come back with `workspace_id: null`, and usage-report rows come back with `api_key_id: null`, so chargeback reporting shows a big unallocated bucket that never shrinks.
- **mechanism**: `null` carries two distinct meanings here and both mean "cannot attribute". Usage and costs in the organization's **default workspace** report `workspace_id: null`, and API usage from the Console **playground** is not associated with any API key so `api_key_id` is `null` even when grouping by that dimension. Every user whose org role permits API access, and every service account, can use the Default Workspace in addition to whatever workspaces they are explicitly added to — so it is the path of least resistance and accretes traffic from everywhere. The default workspace also cannot carry rate-limit overrides.
- **detect**: Admin API key required. `GET /v1/organizations/cost_report?starting_at={T-30d}& limit=31&group_by[]=workspace_id` and compute the `amount` share of results where `workspace_id` is `null`. Then `GET /v1/organizations/usage_report/messages?starting_at= {T-30d}&bucket_width=1d&limit=31&group_by[]=api_key_id&group_by[]=workspace_id` and separate the two `null` causes. Cross-reference `GET /v1/organizations/api_keys?limit=1000` and count keys whose `scope.type == "workspace"` resolves to the default workspace (the deprecated top-level `workspace_id` is `null` for those, while `scope.workspace_id` gives the real ID).
- **repair**: Print, do not run: list the keys currently landing in the default workspace and the named workspace each ought to move to, so cost lands on a workspace that can be rate-limited and charged back.
- **category**: Keys, projects and access
- **sources**: https://platform.claude.com/docs/en/manage-claude/usage-cost-api · https://platform.claude.com/docs/en/api/admin-api/apikeys/list-api-keys · https://platform.claude.com/docs/en/manage-claude/rate-limits-api

## active-api-keys-never-used

- **slug**: `active-api-keys-never-used`
- **title**: Active API keys exist that no request has ever used
- **symptom**: No error. `GET /v1/organizations/api_keys?status=active` returns keys whose IDs never appear as an `api_key_id` in any bucket of the usage report over the full retrievable window.
- **mechanism**: There is no `last_used_at` field on the API key object — the schema is `id`, `created_at`, `created_by`, `expires_at`, `name`, `partial_key_hint`, `principal`, `scope`, `status`, `type`, and the deprecated `workspace_id`. So "unused" is only computable by joining the key inventory against the usage report. An `active` key that no traffic uses is live credential surface with no operational value: it can still authenticate, still counts against nothing, and is the classic residue of a proof-of-concept, a rotated integration whose old key was never archived, or a laptop that was reimaged.
- **detect**: Admin API key required. (1) `GET /v1/organizations/api_keys?status=active& limit=1000`, paging on `last_id`/`after_id` until `has_more` is false; collect every `id`. (2) `GET /v1/organizations/usage_report/messages?starting_at={T-31d}&bucket_width=1d&limit=31& group_by[]=api_key_id` and collect the set of non-null `api_key_id` values seen. The set difference is the unused-key list. Report each with `name`, `partial_key_hint`, `created_at`, `created_by.id`, and `scope`.
- **repair**: Print, do not run: for each unused active key, print the archive call (`POST /v1/organizations/api_keys/{api_key_id}` with `status: "archived"`) as text for a human to run after confirming ownership. Never execute it from the audit.
- **category**: Keys, projects and access
- **sources**: https://platform.claude.com/docs/en/api/admin-api/apikeys/list-api-keys · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report

## api-key-created-by-departed-member

- **slug**: `api-key-created-by-departed-member`
- **title**: An API key was created by a member who has left
- **symptom**: No error. An `active` key's `created_by.id` (with `created_by.type: "user"`) does not resolve to any `id` in `GET /v1/organizations/users`, or resolves to a user whose access should have been removed. In some cases `created_by` is `null` entirely.
- **mechanism**: Removing a member from the organization does not archive the API keys they created — the key is an independent object with its own `status`. So offboarding leaves live credentials behind whose owner no longer exists, with no one to ask what depends on them. The `created_by` field is also `null` for legacy, workload-identity-federated, and system-created keys, which is a different problem with the same symptom: unattributable credentials.
- **detect**: Admin API key required. (1) `GET /v1/organizations/users?limit=1000`, paging on `after_id`, and build the set of member `id` values with their `email` and `role`. (2) `GET /v1/organizations/api_keys?status=active&limit=1000` and, for each key, check `created_by.id` against that set. Flag keys whose `created_by.id` is absent from the member set, and separately flag keys whose `created_by` is `null`. Optionally narrow with `GET /v1/organizations/api_keys?created_by_user_id={user_id}` once you have a suspect. Then join the flagged key IDs against `group_by[]=api_key_id` in the usage report to see whether the orphaned key is still carrying traffic.
- **repair**: Print, do not run: for each orphaned key, print its `name`, `partial_key_hint`, `scope`, recent token volume, and the archive call for a human to run once a new owner is named.
- **category**: Keys, projects and access
- **sources**: https://platform.claude.com/docs/en/api/admin-api/apikeys/list-api-keys · https://platform.claude.com/docs/en/api/admin-api/users/list-users

## api-keys-not-scoped-to-a-workspace

- **slug**: `api-keys-not-scoped-to-a-workspace`
- **title**: API keys are not scoped to any workspace
- **symptom**: No error. `GET /v1/organizations/api_keys` returns keys whose `scope` is `{"type": "organization"}` — the key has no workspace at all — and/or a large population of keys all resolving to the organization's default workspace.
- **mechanism**: The workspace is the isolation and accounting boundary: rate-limit overrides, file access, and cost attribution all key off it. A principal-bound key with `scope.type == "organization"` has no workspace and therefore no workspace rate limit and no attributable cost row. The deprecated top-level `workspace_id` field cannot distinguish these cases — it is `null` **both** for a key in the default workspace and for an organization-scoped key — so any audit reading `workspace_id` instead of `scope` silently conflates two different problems. Files compound it: uploaded files are readable by **any** key with access to that workspace, so unscoped keys widen the blast radius of a leaked file ID.
- **detect**: Admin API key required. `GET /v1/organizations/api_keys?status=active&limit=1000`, paging on `after_id`. Bucket results by `scope.type`: count `"organization"` (no workspace) versus `"workspace"`, and for the workspace ones read `scope.workspace_id` (the real ID, even for the default workspace). Resolve names with `GET /v1/organizations/workspaces?limit=1000`. Report the count and share of organization-scoped keys plus the default-workspace key count.
- **repair**: Print, do not run: list the org-scoped and default-workspace keys with their `name`, `created_by`, and 30-day token volume from the usage report, and the named workspace each should be re-issued in. Key scope is set at creation — this is a re-issue, not an edit.
- **category**: Keys, projects and access
- **sources**: https://platform.claude.com/docs/en/api/admin-api/apikeys/list-api-keys · https://platform.claude.com/docs/en/build-with-claude/files · https://platform.claude.com/docs/en/api/admin-api/workspaces/list-workspaces

## archived-workspace-with-active-keys

- **slug**: `archived-workspace-with-active-keys`
- **title**: An archived workspace still has active API keys
- **symptom**: No error. A workspace returned by `GET /v1/organizations/workspaces? include_archived=true` has a non-null `archived_at`, yet `GET /v1/organizations/api_keys?workspace_id={id}&status=active` returns keys.
- **mechanism**: Archiving a workspace is a Console-level lifecycle action; it does not cascade into the key inventory. The default listing hides archived workspaces (`include_archived` defaults to `false`), so a routine audit that enumerates workspaces and then their keys will never see this pair — the workspace is invisible while its credentials are not. Any files uploaded into that workspace also remain reachable by those keys.
- **detect**: Admin API key required. (1) `GET /v1/organizations/workspaces? include_archived=true&limit=1000`, paging on `after_id`; keep every workspace where `archived_at != null`. (2) For each, `GET /v1/organizations/api_keys?workspace_id={id}& status=active&limit=1000`. Any non-empty `data` is the finding. (3) Check whether those keys are still live by looking for their IDs in `GET /v1/organizations/usage_report/messages? starting_at={T-31d}&bucket_width=1d&limit=31&group_by[]=api_key_id& workspace_ids[]={id}`.
- **repair**: Print, do not run: for each archived workspace, print the workspace name, `archived_at`, and the list of still-active keys with `partial_key_hint`, plus the archive call for each key for a human to run.
- **category**: Keys, projects and access
- **sources**: https://platform.claude.com/docs/en/api/admin-api/workspaces/list-workspaces · https://platform.claude.com/docs/en/api/admin-api/apikeys/list-api-keys

## no-dev-prod-workspace-separation

- **slug**: `no-dev-prod-workspace-separation`
- **title**: Dev and prod traffic share one workspace
- **symptom**: No error. `GET /v1/organizations/workspaces` returns one or two workspaces while `GET /v1/organizations/api_keys` returns many keys all scoped to the same `scope.workspace_id`, and the usage report grouped by `api_key_id` within that workspace shows both a steady high-volume pattern (production) and spiky low-volume patterns (development).
- **mechanism**: Workspaces are the only boundary the platform gives you for rate limits, file isolation, and cost attribution. With everything in one workspace, a developer's runaway loop consumes the same `requests_per_minute` and `input_tokens_per_minute` allocation as production traffic, every uploaded file is readable by every key, and chargeback is impossible. Each organization can have up to **100 workspaces**, so scarcity is not the reason people skip this. Workspace `tags` (a string map, keys may not begin with `anthropic`) exist to label environment, but only if workspaces exist to tag.
- **detect**: Admin API key required. `GET /v1/organizations/workspaces?limit=1000` — count workspaces and inspect each one's `name` and `tags` for environment markers. Then `GET /v1/organizations/api_keys?limit=1000` and count distinct `scope.workspace_id` values; a key count far exceeding the workspace count with no environment split is the finding. Corroborate with `GET /v1/organizations/usage_report/messages?starting_at={T-7d}& bucket_width=1h&limit=168&group_by[]=api_key_id&workspace_ids[]={id}` to see the mixed traffic shapes. Finally, `GET /v1/organizations/workspaces/{workspace_id}/rate_limits` — a workspace holding both environments almost always has no overrides at all.
- **repair**: Print, do not run: propose a workspace per environment, list which keys would move where, and note the 100-workspace ceiling. Workspace creation is a write — leave it to a human.
- **category**: Keys, projects and access
- **sources**: https://platform.claude.com/docs/en/api/admin-api/workspaces/list-workspaces · https://platform.claude.com/docs/en/build-with-claude/files · https://platform.claude.com/docs/en/manage-claude/rate-limits-api

## anthropic-invites-pending-past-expiry

- **slug**: `anthropic-invites-pending-past-expiry`
- **title**: Invites are sitting pending past their expiry
- **symptom**: No error. `GET /v1/organizations/invites` returns objects with `status: "pending"` whose `expires_at` is already in the past, and/or a backlog of `status: "expired"` invites that nobody has cleaned up or re-sent.
- **mechanism**: Invites carry `invited_at`, `expires_at`, `accepted_at`, `role`, and a `status` from `pending` / `accepted` / `expired` / `deleted`. Nothing re-sends or garbage-collects them. A stale pending invite is an onboarding failure that looks like success on the sending side; a pile of expired invites at a privileged `role` is also a signal about how access is handed out — the invite records the role the user will receive on acceptance, so an expired invite for `admin` documents an intent that may no longer be appropriate.
- **detect**: Admin API key required. `GET /v1/organizations/invites?limit=1000`, paging on `after_id` until `has_more` is false. Omitting `statuses[]` returns `pending`, `accepted`, and `expired` alike, which is what you want for an audit; narrow with `statuses[]=pending&statuses[]=expired` for the actionable set. Flag any record where `status == "pending"` and `expires_at < now`, and group the `expired` set by `role` (`admin`, `billing`, `claude_code_user`, `developer`, `managed`, `membership_admin`, `owner`, `primary_owner`, `user`). Compare `email` against `GET /v1/organizations/users?email={email}` to see whether the person joined by another route.
- **repair**: Print, do not run: list stale pending and expired invites with `email`, `role`, `invited_at`, and `expires_at`, and let an admin decide whether to re-invite or delete.
- **category**: Keys, projects and access
- **sources**: https://platform.claude.com/docs/en/api/admin-api/invites/list-invites · https://platform.claude.com/docs/en/api/admin-api/users/list-users

## too-many-org-admins

- **slug**: `too-many-org-admins`
- **title**: Too many org members hold the admin role
- **symptom**: No error. `GET /v1/organizations/users?roles=admin` returns a large fraction of the membership, and cross-checking the usage report shows most of those admins have no associated API traffic — they are administrators by default rather than by need.
- **mechanism**: Only members with the `admin` role can provision an Admin API key (`sk-ant-admin...`), and only admin/owner/primary_owner can obtain an `org:admin` OAuth token. An `org:admin` token grants access to the **whole organization regardless of the workspace** the underlying profile is bound to — so every extra admin is a full-organization credential waiting to be minted. The `developer` role is the correct default for people who need to build against the API. Role enums differ by org type: Console/API organizations use `user`, `developer`, `billing`, `admin`, `claude_code_user`; Claude Enterprise organizations use `user`, `owner`, `primary_owner`, `membership_admin`, `managed`.
- **detect**: Admin API key required. `GET /v1/organizations/users?limit=1000`, paging on `after_id`, and tally the `role` distribution; or filter directly with `roles=admin` (repeatable, OR'ed). Compute admins as a share of total members. Then, per workspace, `GET /v1/organizations/workspaces/{workspace_id}/members?limit=1000` and tally `workspace_role` (`workspace_admin`, `workspace_billing`, `workspace_developer`, `workspace_restricted_developer`, `workspace_user`) to find the same over-provisioning one level down.
- **repair**: Print, do not run: list org admins with `email` and `added_at`, note which have no API traffic attributable to keys they created, and recommend `developer` for those. Role changes are writes — leave them to an admin.
- **category**: Keys, projects and access
- **sources**: https://platform.claude.com/docs/en/api/admin-api/users/list-users · https://platform.claude.com/docs/en/manage-claude/admin-api · https://platform.claude.com/docs/en/api/admin-api/workspace_members/list-workspace-members

## workspace-has-no-spend-or-rate-guard

- **slug**: `workspace-has-no-spend-or-rate-guard`
- **title**: A workspace has no rate limit or spend guard
- **symptom**: No error. `GET /v1/organizations/workspaces/{workspace_id}/rate_limits` returns an empty `data` array (or a `data` array missing the `model_group` the workspace actually uses), meaning the workspace has no overrides and inherits the full organization limit.
- **mechanism**: The workspace rate-limits endpoint returns **only overrides**. A group absent from `data` has no workspace override and inherits the organization-level limit — it is not unlimited, but it is also not bounded below the org ceiling, so one workspace can consume the entire organization's `requests_per_minute` / `input_tokens_per_minute` / `output_tokens_per_minute` allocation and starve the others. The **default workspace cannot have rate-limit overrides at all**, so any traffic that lands there is structurally unbounded relative to the org limit. Dollar-denominated per-user spend limits exist only for Claude Enterprise organizations (the Spend Limits API), not for Console/Platform workspaces.
- **detect**: Admin API key required. (1) `GET /v1/organizations/workspaces?limit=1000`. (2) For each non-default workspace, `GET /v1/organizations/workspaces/{workspace_id}/ rate_limits` and record which `group_type` entries and which `limits[].type` values are present; each present limiter also reports `org_limit` for comparison. (3) `GET /v1/organizations/rate_limits` (optionally `?group_type=model_group` or `?model={id}`) for the inherited org values. Flag workspaces carrying real traffic (from the usage report, `workspace_ids[]={id}`) with zero overrides. On Claude Enterprise, additionally `GET /v1/organizations/spend_limits/effective?limit=100` (needs the `read:spend_limits` scope) and flag members whose `amount` is `null` (unlimited) or whose `period_to_date_spend / amount` exceeds your threshold.
- **repair**: Print, do not run: for each unguarded workspace print its 30-day token volume, the inherited `org_limit` values, and a suggested override. Rate limits are set in the Console — this API cannot write them.
- **category**: Keys, projects and access
- **sources**: https://platform.claude.com/docs/en/manage-claude/rate-limits-api · https://platform.claude.com/docs/en/manage-claude/spend-limits-api · https://platform.claude.com/docs/en/api/admin-api/workspaces/list-workspaces

## compliance-activity-feed-never-read

- **slug**: `compliance-activity-feed-never-read`
- **title**: Nobody reads Anthropic's activity feed for key and member changes
- **symptom**: An API key appears in `GET /v1/organizations/api_keys` that no current engineer recognises, or a member's role changed months ago and nobody can say when or by whom. The Admin API's key and user objects carry `created_at` and `created_by` but no history — you can see the current state and not a single transition that produced it.
- **mechanism**: Anthropic's audit trail lives in a different API from the Admin API most teams wire up. `GET /v1/compliance/activities` returns per-event `Activity` records — actor (`email_address`, `user_id`, `ip_address`, `user_agent`), `type`, `created_at`, `organization_id` — and an Admin API key reaches it, but only that one endpoint. Because the feed is documented under Compliance rather than under Admin, integrations that pull usage and keys almost never pull activity, so key creation, role escalation and workspace changes go unreviewed indefinitely.
- **detect**: Admin API key (`sk-ant-admin...`, or a Compliance Access Key) with the `read:compliance_activities` scope → `GET https://api.anthropic.com/v1/compliance/activities?limit=100`, paginating on `has_more`/`last_id`. Filter `data[].type` for key, member, role and workspace lifecycle events and correlate `data[].actor.email_address` against the current roster from `GET /v1/organizations/users`. Flag any actor no longer in the roster, any event from an unexpected `actor.ip_address`, and any key in `GET /v1/organizations/api_keys` whose `created_by` has no corresponding creation event in the retained feed. All `/v1/compliance/*` endpoints share a 600 req/min limit per organization.
- **repair**: Print the unreviewed events with actor, type and timestamp. Wire the feed into the same job that reads usage — a daily pull with a stored `last_id` cursor — and forward it to your SIEM. Note that a standalone Claude Console organization can query the Activity Feed only; chat, file and session content needs a Compliance Access Key on a Claude Enterprise tenant.
- **category**: Keys, projects and access
- **sources**: https://platform.claude.com/docs/en/manage-claude/compliance-api · https://platform.claude.com/docs/en/manage-claude/compliance-activity-feed · https://platform.claude.com/docs/en/manage-claude/admin-api

## external-key-config-unattached

- **slug**: `external-key-config-unattached`
- **title**: A CMEK external key config is inert but assumed to be live
- **symptom**: No error. A security questionnaire or DPA states that workspace data is encrypted under a customer-managed KMS key, but `GET /v1/organizations/external_keys` shows the config with `attachment.type: "unattached"` — meaning no live or archived workspace uses it and the encryption path never touches it. Or the reverse: an attached config nobody remembers exists is still holding archived-workspace data hostage to a KMS key that may get rotated or deleted.
- **mechanism**: An external key config is created and attached in two separate steps, and only an attached config participates in encryption. A config left unattached is described in the docs as "inert" and can be deleted safely — which is exactly the state a half-finished CMEK rollout leaves behind. Nothing on the inference path signals which key, if any, is protecting a workspace, so the claim on the questionnaire and the state in the API drift apart silently.
- **detect**: Admin API key or an `org:admin` OAuth token → `GET /v1/organizations/external_keys?limit=100`, paginating on `next_page`. For each `data[]` entry read `attachment.type` (`"attached"` / `"unattached"`), `display_name`, `geo`, `created_at`, and `provider_config` (`type` `aws`/`gcp`/`azure`, plus `kms_arn`, `key_name` or `vault_uri`). Flag every `unattached` config, every attached config whose `geo` does not match the data-residency commitment for that workspace, and any org with zero configs at all while a CMEK obligation exists. Cross-reference the live workspace list from `GET /v1/organizations/workspaces` to see how much surface is actually covered.
- **repair**: Print the config id, `display_name`, `attachment.type`, `geo` and KMS coordinates for each entry, alongside the workspaces that are supposed to be covered. For an unattached config, print the attach step for a human to run in the Console and note that attachment is what makes it live. For a genuinely orphaned config, print the delete call but do not run it — deleting a config that is attached to an archived workspace makes that workspace's retained data unrecoverable.
- **category**: Keys, projects and access
- **sources**: https://platform.claude.com/docs/en/api/admin/external_keys/list · https://platform.claude.com/docs/en/manage-claude/admin-api

## vector-store-storage-cost-creeping

- **slug**: `vector-store-storage-cost-creeping`
- **title**: Vector store bytes keep growing and are billed hourly
- **symptom**: No error. A small, steady line item on the invoice grows every month and nobody can name it. It is vector store storage — billed on bytes retained per unit time, not per query — accumulating from every file ever indexed for file search, including the ones from experiments abandoned a year ago.
- **mechanism**: Vector store cost is a *stock*, not a *flow*. Every other line item on the bill is driven by requests, so it falls to zero when traffic stops; storage keeps billing whether anyone queries it or not. Uploading files to a vector store is a natural part of building retrieval, deleting them is nobody's task, and the resulting cost is small enough per month to stay below the threshold that would trigger investigation — while compounding indefinitely. Expiration policies exist but are opt-in and are rarely set on stores created interactively or during prototyping.
- **detect**: Organization **ADMIN** key required for the aggregate; a project read-only key can enumerate the individual stores. `GET /v1/organization/usage/vector_stores?start_time={now-90d}&bucket_width=1d&limit=31&group_by=project_id` returns `organization.usage.vector_stores.result` objects carrying `usage_bytes` and `project_id`. Fit a trend across buckets and flag any `project_id` whose `usage_bytes` has grown monotonically over 90 days without a corresponding rise in retrieval traffic — get that from `GET /v1/organization/usage/file_search_calls?start_time=…&group_by=project_id&group_by=vector_store_id`, whose `organization.usage.file_searches.result` exposes `num_requests` and `vector_store_id`. A store with growing `usage_bytes` and zero `num_requests` is pure waste. Price it with `GET /v1/organization/costs?start_time=…&group_by=line_item`, where the storage line item reports `quantity_unit: "gibibyte_hours"` — confirming the stock-not-flow billing model. With a project key, `GET /v1/vector_stores` lists each store's `id`, `name`, `usage_bytes`, `file_counts`, `last_active_at`, and `expires_after` / `expires_at`.
- **repair**: Print, per project and per `vector_store_id`: current `usage_bytes` in GiB, 90-day growth, `num_requests` over the same window, and monthly cost from the `gibibyte_hours` line item. For stores with no retrieval traffic, print `DELETE /v1/vector_stores/{vector_store_id}`. For active stores, print the durable fix — set an expiration policy at creation (`expires_after` with an `anchor` of `last_active_at` and a `days` value) so unused stores age out on their own rather than billing forever.
- **category**: Files and vector stores
- **sources**: https://platform.openai.com/docs/api-reference/usage · https://platform.openai.com/docs/api-reference/vector-stores · https://github.com/openai/openai-python/blob/main/api.md

## files-accumulating-against-storage-quota

- **slug**: `files-accumulating-against-storage-quota`
- **title**: Uploaded files pile up against the 2.5 TB project quota
- **symptom**: `GET /v1/files` returns thousands of objects with no `expires_at`, and eventually `POST /v1/files` starts returning HTTP 400 storage-limit errors. Individual files can be up to 512 MB; each project can store up to 2.5 TB in total.
- **mechanism**: Files uploaded for batch input, fine-tuning, vision and file search are permanent unless explicitly deleted or given an `expires_after` policy. Batch output and error files, `fine-tune-results` files and `assistants` attachments accumulate on every run. Nothing garbage-collects them, and the storage is billed. The 2.5 TB ceiling arrives quietly, mid-pipeline.
- **detect**: `GET /v1/files?limit=10000&order=asc` and paginate on `after`. Sum `bytes` for the project total; group by `purpose` to see which class dominates. Flag every object where `expires_at` is null and `created_at` is older than your retention window, and every object with `bytes > 100_000_000`. Cross-check with `GET /v1/organization/costs?start_time=...&bucket_width=1d` for the storage line item (**admin read key**). Requires: project read key.
- **repair**: print — `Set an expiry at upload time: expires_after={"anchor":"created_at","seconds":2592000} (30 days). Sweep existing files with DELETE /v1/files/{file_id} for anything older than your retention window whose purpose is batch, batch_output, fine-tune-results or assistants and which is not referenced by a live vector store or fine-tuning job.`
- **category**: Files and vector stores
- **sources**: https://developers.openai.com/api/docs/api-reference/files · https://developers.openai.com/api/docs/guides/your-data

## orphaned-assistants-purpose-files

- **slug**: `orphaned-assistants-purpose-files`
- **title**: `purpose=assistants` files orphaned by the Assistants sunset
- **symptom**: `GET /v1/files?purpose=assistants` returns files that no live object references, because the Assistants API that owned them was shut down on **August 26, 2026**. `GET /v1/files?purpose=assistants_output` shows the same for code-interpreter outputs. The files are still billed as storage; the assistants and threads that pointed at them are gone.
- **mechanism**: Files uploaded with `purpose: "assistants"` were attached to assistants, threads, messages and vector stores. When the Assistants API was sunset, `/v1/assistants` and `/v1/threads` were removed — the ownership graph vanished but the file objects did not. Vector stores and files persist (they carry over to the Responses API's file search tool), so only files never attached to a surviving vector store are truly orphaned.
- **detect**: `GET /v1/files?purpose=assistants&limit=10000` plus `GET /v1/files?purpose=assistants_output`. Build the set of still-referenced file ids by walking `GET /v1/vector_stores` then `GET /v1/vector_stores/{id}/files` for each. Any `assistants`-purpose file id not in that set, with `expires_at == null`, is an orphan. Requires: project read key.
- **repair**: print — `Delete confirmed orphans with DELETE /v1/files/{file_id} after archiving anything you still need. For files that ARE still in a vector store, keep them — file search under the Responses API reads the same vector stores. Re-upload future file-search sources with purpose="user_data" and an expires_after policy.`
- **category**: Files and vector stores
- **sources**: https://developers.openai.com/api/docs/assistants/migration · https://developers.openai.com/api/docs/api-reference/files · https://developers.openai.com/api/docs/deprecations

## vector-store-file-attach-failed

- **slug**: `vector-store-file-attach-failed`
- **title**: File silently failed to index — `last_error.code` on the store
- **symptom**: `GET /v1/vector_stores/{id}/files?filter=failed` returns entries with `"status": "failed"` and `"last_error": {"code": "unsupported_file" | "invalid_file" | "server_error", "message": "..."}`. The attach call returned 200 at the time; retrieval just silently misses that document forever.
- **mechanism**: Attaching a file to a vector store is asynchronous. `POST /v1/vector_stores/{id}/files` accepts the request and returns a `vector_store.file` in `in_progress`; parsing, chunking (default `max_chunk_size_tokens` 800, `chunk_overlap_tokens` 400) and embedding happen afterwards. A password-protected PDF, a scanned image-only PDF, an unsupported extension, an empty file, or a file over 512 MB / 5,000,000 tokens ends in `failed` with `last_error` populated. Nothing raises; file search just returns fewer results.
- **detect**: For each store from `GET /v1/vector_stores?limit=100`, call `GET /v1/vector_stores/{vector_store_id}/files?filter=failed&limit=100` and report `id`, `status`, `last_error.code`, `last_error.message`. `GET /v1/vector_stores/{vector_store_id}/files/{file_id}` gives the full object for one file. Requires: project read key.
- **repair**: print — `Bucket failures by last_error.code: "unsupported_file" needs a format conversion (OCR the scanned PDF, export to .md/.txt); "invalid_file" usually means empty, corrupt, or encrypted — fix at source; "server_error" is transient, just re-attach. After every bulk ingest, assert file_counts.failed == 0 before declaring the store ready.`
- **category**: Files and vector stores
- **sources**: https://developers.openai.com/api/docs/api-reference/vector-stores-files · https://developers.openai.com/api/docs/guides/retrieval

## vector-store-file-counts-failed

- **slug**: `vector-store-file-counts-failed`
- **title**: Vector store reports `file_counts.failed > 0` and nobody looked
- **symptom**: `GET /v1/vector_stores/{id}` returns `"status": "completed"` next to `"file_counts": {"in_progress": 0, "completed": 812, "failed": 37, "cancelled": 0, "total": 849}`. The store looks healthy at a glance; 4% of the corpus is missing from every search.
- **mechanism**: A vector store's top-level `status` becomes `completed` once no files remain `in_progress` — it does **not** mean every file succeeded. `file_counts.failed` is the only aggregate signal. Ingestion scripts that poll for `status == "completed"` and then move on ship a silently incomplete index.
- **detect**: `GET /v1/vector_stores?limit=100` (paginate on `after`). For each object assert `file_counts.failed == 0` and `file_counts.completed == file_counts.total`. Report `name`, `id`, the failed count, and the failure rate. Requires: project read key.
- **repair**: print — `Make file_counts.failed == 0 the completion gate in your ingestion job, not status == "completed". For stores already failing, list the failed files (filter=failed), fix or convert them, re-attach, and re-verify the counts. Alert when the failure rate crosses 1%.`
- **category**: Files and vector stores
- **sources**: https://developers.openai.com/api/docs/api-reference/vector-stores · https://developers.openai.com/api/docs/guides/retrieval

## vector-store-stuck-in-progress

- **slug**: `vector-store-stuck-in-progress`
- **title**: Vector store stuck `in_progress` long after ingestion ended
- **symptom**: `GET /v1/vector_stores/{id}` shows `"status": "in_progress"` with `file_counts.in_progress > 0` hours or days after the last attach, and `last_active_at` frozen at the ingest time. Searches against the store return partial results with no error.
- **mechanism**: Each file attach is processed independently. A very large file, a file batch that hit the 2,000-files-per-minute-per-org attachment limit, or a stalled server-side job can leave individual `vector_store.file` objects pinned in `in_progress`. The parent store's `status` stays `in_progress` as long as any child is, so the store never becomes fully queryable and no error is raised.
- **detect**: `GET /v1/vector_stores?limit=100`; flag `status == "in_progress"` where `now - last_active_at > 3600`. Drill in with `GET /v1/vector_stores/{id}/files?filter=in_progress` and check each file's `created_at`. Requires: project read key.
- **repair**: print — `Detach and re-attach the pinned files (DELETE then POST /v1/vector_stores/{id}/files). Stagger large ingests to stay under 2,000 file attachments per minute per organization, and poll file_counts.in_progress down to zero with a timeout rather than assuming attach == indexed.`
- **category**: Files and vector stores
- **sources**: https://developers.openai.com/api/docs/api-reference/vector-stores · https://developers.openai.com/api/docs/api-reference/files

## vector-store-expired-or-expiring

- **slug**: `vector-store-expired-or-expiring`
- **title**: Vector store `expires_after` will silently delete the index
- **symptom**: `GET /v1/vector_stores/{id}` returns `"status": "expired"`, or `"expires_after": {"anchor": "last_active_at", "days": 7}` with a `last_active_at` several days stale and an `expires_at` in the near future. File search against an expired store returns nothing; when it expires, **all associated `vector_store.file` objects are deleted**.
- **mechanism**: `expires_after` is anchored to `last_active_at`, not to creation — the clock resets on use and runs down during idle periods. A store built during a burst of development and then unused for a week evaporates. Stores created implicitly by tooling often inherit a short default policy nobody chose. Deletion of the contained `vector_store.file` objects is permanent.
- **detect**: `GET /v1/vector_stores?limit=100`. Flag (a) `status == "expired"`; (b) `expires_after != null` and `expires_at - now < 7 * 86400`; (c) `expires_after != null` on any store your application treats as permanent. Also report `last_active_at` and `usage_bytes` for each. Requires: project read key.
- **repair**: print — `For stores that must persist, clear the policy: POST /v1/vector_stores/{id} with expires_after set to null. For genuinely temporary stores keep the policy but confirm the anchor is what you want — last_active_at means idle stores die. Re-ingest any store already in status "expired"; its files are gone and cannot be recovered from the store.`
- **category**: Files and vector stores
- **sources**: https://developers.openai.com/api/docs/api-reference/vector-stores · https://developers.openai.com/api/docs/guides/retrieval

## empty-vector-store-still-referenced

- **slug**: `empty-vector-store-still-referenced`
- **title**: Empty vector store still wired into the file_search tool
- **symptom**: `GET /v1/vector_stores` returns stores with `"file_counts": {"total": 0, ...}` and `"usage_bytes": 0`, yet those ids are still passed as `tools: [{"type":"file_search","vector_store_ids":[...]}]`. Every retrieval call succeeds with HTTP 200 and returns zero citations — the model answers from parametric memory and looks confidently wrong.
- **mechanism**: File search does not error on an empty store; it returns no results. An empty store arises when ingestion failed entirely, when the store expired and its files were deleted, or when a create-then-attach sequence broke halfway. The failure surfaces as degraded answer quality, never as an exception.
- **detect**: `GET /v1/vector_stores?limit=100`; flag `file_counts.total == 0` or `file_counts.completed == 0` or `usage_bytes == 0`. Cross-reference the ids against the `vector_store_ids` your application configures (grep config / env) to find the ones actually in use. Requires: project read key.
- **repair**: print — `Add a startup assertion: for each configured vector_store_id, GET /v1/vector_stores/{id} and refuse to boot if file_counts.completed == 0. Re-run ingestion for the empty stores and delete abandoned ones with DELETE /v1/vector_stores/{id}.`
- **category**: Files and vector stores
- **sources**: https://developers.openai.com/api/docs/api-reference/vector-stores · https://developers.openai.com/api/docs/guides/retrieval

## files-storage-quota-climbing

- **slug**: `files-storage-quota-climbing`
- **title**: Files storage is climbing toward the 1 TB org limit
- **symptom**: Nothing until you hit it, and then uploads fail with **HTTP 400** and `error.type: "invalid_request_error"` — "Storage limit exceeded: your organization has reached the 1 TB storage limit". Before that, `GET /v1/files` simply returns a growing list.
- **mechanism**: Limits are **500 MB per file** and **1 TB total per organization**, and files persist until explicitly deleted or until they reach an `expires_at` that was set at upload time. Because Files API operations are free (upload, download, list, metadata, delete), there is no cost signal at all as the quota fills — the first feedback is a hard failure on upload. There is no endpoint that reports remaining quota; you have to sum it yourself.
- **detect**: **Not an Admin API key** — the Files API is workspace-scoped, so this needs one normal API key per workspace you want to measure. `GET /v1/files?limit=1000`, paging by passing the response's `next_page` back as the `page` parameter until it is `null`. Sum `data[].size_bytes` across every page, per workspace, and compare against 1 TB (1,000,000,000,000 bytes) organization-wide. Flag individual files approaching 500 MB. Note that a request carrying `anthropic-beta: files-api-2025-04-14` gets the older `{data, has_more, first_id, last_id}` shape with `before_id`/`after_id` cursors instead.
- **repair**: Print, do not run: report total bytes per workspace, the largest files by `size_bytes`, and the `DELETE /v1/files/{file_id}` calls for files a human confirms are dead. Also print the `expires_in_seconds` upload option (3,600 to 7,776,000 seconds) as the preventive fix.
- **category**: Files and vector stores
- **sources**: https://platform.claude.com/docs/en/build-with-claude/files · https://platform.claude.com/docs/en/api/files/list

## orphaned-files-never-deleted

- **slug**: `orphaned-files-never-deleted`
- **title**: Uploaded files are never deleted and accumulate
- **symptom**: No error. `GET /v1/files` returns files with old `created_at` timestamps, `expires_at: null`, and `downloadable: false`, in a count far exceeding anything the application tracks.
- **mechanism**: Files are create-once and never modified; they persist indefinitely unless deleted or given an expiration at upload. Applications that upload a document per request and reference it once leave the file behind forever. Two aggravating facts: uploaded files have `downloadable: false`, so you cannot inspect their contents through the API to decide whether they matter (only files created by skills or the code execution tool are downloadable); and every file is readable by **any** key with access to that workspace, so an accumulating pile is also a growing lateral-read surface. Listing and metadata reads are *not* recorded in the Compliance API Activity Feed, so there is no audit trail of who enumerated them.
- **detect**: Workspace-scoped API key required (not an Admin key). `GET /v1/files?limit=1000`, paging with `page`/`next_page`. Files come back newest first. Bucket by `created_at` age and flag anything older than your retention policy with `expires_at: null`. To check a known set of IDs your application still references, pass up to **100** `ids[]` values in one request — any ID that does not resolve is silently omitted from `data`, so compare the returned IDs against the requested IDs to find both dangling references and, by set difference against the full listing, the orphans nothing references.
- **repair**: Print, do not run: the orphan list with `id`, `filename`, `size_bytes`, `created_at`, and the `DELETE /v1/files/{file_id}` call for each. Deleted files cannot be recovered — never delete from an audit script.
- **category**: Files and vector stores
- **sources**: https://platform.claude.com/docs/en/build-with-claude/files · https://platform.claude.com/docs/en/api/files/list

## expired-files-still-referenced

- **slug**: `expired-files-still-referenced`
- **title**: Expired files still referenced return 404 or fail inference
- **symptom**: `GET /v1/files/{file_id}/content` returns **HTTP 404** with `error.type: "not_found_error"`, and a Messages request referencing the file **fails before inference**. Meanwhile `GET /v1/files/{file_id}` still returns metadata with an `expires_at` in the past, and the file still appears in list responses.
- **mechanism**: `expires_in_seconds` is set once at upload (integer, 3,600 to 7,776,000 seconds — 1 hour to 90 days) and cannot be changed afterward. When the file passes `expires_at`, its content stops being retrievable and it is released from the storage quota, but its **metadata remains readable for up to 30 days** and it keeps appearing in list responses during that window. So a naive "does this file exist?" check against the list endpoint or the metadata endpoint returns yes for a file that will fail every actual use.
- **detect**: Workspace-scoped API key required (not an Admin key). `GET /v1/files?limit=1000` with `page`/`next_page` paging, and compare each `data[].expires_at` against the current time — the guidance is explicit that you must filter expired files yourself. For the specific IDs your application holds, `GET /v1/files?ids[]=...` (up to 100 per request) and check `expires_at` on each returned object; IDs missing from `data` are already fully gone. Note `expires_at` is only returned when the `files-api-2025-04-14` beta header is **absent** — with the header the field is not returned at all, so this check silently cannot run.
- **repair**: Print, do not run: the list of referenced-but-expired file IDs and the application records pointing at them, plus `DELETE /v1/files/{file_id}` (which removes metadata immediately rather than waiting out the 30-day window) for a human to run.
- **category**: Files and vector stores
- **sources**: https://platform.claude.com/docs/en/build-with-claude/files · https://platform.claude.com/docs/en/api/files/list

## files-api-beta-header-shape-drift

- **slug**: `files-api-beta-header-shape-drift`
- **title**: Files API pagination breaks when the beta header drops
- **symptom**: **HTTP 400** `invalid_request_error` when `before_id` or `after_id` is passed without the beta header, or a silent break: the client reads `has_more` / `first_id` / `last_id` from a response that no longer contains them, concludes there is one page, and audits only the newest 20 files.
- **mechanism**: The Files API left beta. Requests still sending `anthropic-beta: files-api-2025-04-14` keep the old shapes — list returns `{data, has_more, first_id, last_id}` with `before_id`/`after_id` cursors, `expires_at` is not returned, and `Content-Type` on the uploaded part is required. Without the header, list returns `{data, next_page}` paged with `page` or up to 100 `ids[]`, `before_id`/`after_id` return **400**, and `expires_at` is always present. SDK versions moved independently: from Python SDK 1.2.0, TypeScript 0.122.0, Go 1.68.0, Java 2.59.0, Ruby 1.67.0, and C# 12.44.0, `client.beta.files` stopped sending the header — so a routine SDK bump flips the response shape under code that never changed. (A separate carve-out: requests carrying `managed-agents-2026-04-01` without `files-api-2025-04-14` still accept `before_id`/`after_id` and include `has_more`/`first_id`/`last_id` alongside `next_page`.)
- **detect**: Workspace-scoped API key required. Issue `GET /v1/files?limit=1` twice — once with and once without `anthropic-beta: files-api-2025-04-14` — and diff the response keys. The presence of `next_page` versus `has_more`/`first_id`/`last_id`, and the presence or absence of `expires_at` on `data[0]`, tells you which contract this key's traffic is on. Then confirm the client agrees: an audit that assumes `has_more` while the server returns `next_page` will under-count files, which silently invalidates the quota and orphan checks above.
- **repair**: Print, do not run: state which shape the endpoint is returning, and the migration steps — drop the beta header, replace `before_id`/`after_id` loops with `page`/`next_page`, and start reading `expires_at`.
- **category**: Files and vector stores
- **sources**: https://platform.claude.com/docs/en/build-with-claude/files · https://platform.claude.com/docs/en/api/files/list

## prompt-cache-share-near-zero

- **slug**: `prompt-cache-share-near-zero`
- **title**: Cached input tokens are near zero, so caching saves nothing
- **symptom**: No error, no warning. Input token cost per request is flat over time even though every request sends the same 4,000-token system prompt and tool schema. The bill scales linearly with traffic when it should have flattened.
- **mechanism**: OpenAI's automatic prompt caching only fires when the prefix of the request is byte-identical to a recent request and long enough to qualify. It is silently defeated by putting anything variable *before* the stable block — a timestamp in the system message, a session ID, a user name, shuffled tool definitions, or a retrieved-context block placed above the instructions rather than below. Nothing reports the miss; you simply pay full price for tokens that were eligible for a discount. Because the discount is applied silently when it works, its absence is equally silent.
- **detect**: Organization **ADMIN** key required. `GET /v1/organization/usage/completions?start_time={now-7d}&bucket_width=1d&limit=7&group_by=model&group_by=project_id`. Each `organization.usage.completions.result` carries `input_tokens` (which *includes* cached and cache-write tokens), `input_cached_tokens`, `input_uncached_tokens`, `input_cache_write_tokens`, and the finer-grained `input_cached_text_tokens` / `input_cached_audio_tokens` / `input_cached_image_tokens`. Compute `input_cached_tokens / input_tokens` per `model`. Flag any model with a cache ratio below 0.10 while averaging more than ~1,024 input tokens per request (`input_tokens / num_model_requests`) — that is a workload large enough to cache that is not caching. A second, sharper signal: `input_cache_write_tokens` materially greater than zero while `input_cached_tokens` stays near zero means you are paying to populate a cache whose entries are never read again.
- **repair**: Print the per-model cache ratio and the average input tokens per request. Then the fix: move every static element — system instructions, tool/function definitions, few-shot examples — to the very front of the message array in a byte-stable order, and move all variable content (user turn, retrieved chunks, timestamps, IDs) after it. Print a reminder that reordering `tools` between calls breaks the prefix just as thoroughly as changing the text.
- **category**: Prompt caching
- **sources**: https://platform.openai.com/docs/api-reference/usage/completions · https://platform.openai.com/docs/guides/prompt-caching · https://github.com/openai/openai-python/blob/main/api.md

## prompt-caching-never-used

- **slug**: `prompt-caching-never-used`
- **title**: Prompt caching is never used anywhere in the organization
- **symptom**: No HTTP error and no `error.type` — this failure is silent and shows only in billing. Across every bucket of `GET /v1/organizations/usage_report/messages`, every result has `cache_read_input_tokens: 0` and `cache_creation.ephemeral_5m_input_tokens: 0` and `cache_creation.ephemeral_1h_input_tokens: 0`, while `uncached_input_tokens` is large and growing. In the cost report, the only `token_type` values that ever appear are `uncached_input_tokens` and `output_tokens`.
- **mechanism**: Prompt caching is opt-in. Without either a top-level `cache_control: {"type": "ephemeral"}` on `messages.create()` or an explicit `cache_control` breakpoint on a content block, every request reprocesses the whole prefix — system prompt, tool definitions, documents, conversation history — at the full base input rate. A cache read costs **0.1x** base input, so a workload with a stable prefix is paying up to 10x what it needs to on the cached portion. Nothing in the API warns you: there is no error, no header, no flag.
- **detect**: Admin API key required. `GET /v1/organizations/usage_report/messages?starting_at= {T-30d}&bucket_width=1d&limit=31&group_by[]=model&group_by[]=workspace_id`. Sum `data[].results[].cache_read_input_tokens` and both `cache_creation.*` fields across the whole page set. If both sums are `0` while `uncached_input_tokens` is non-trivial, caching is entirely absent. Confirm from the money side with `GET /v1/organizations/cost_report? starting_at={T-30d}&group_by[]=description` and check that no result carries `token_type: "cache_read_input_tokens"`.
- **repair**: Print, do not run: add `cache_control: {"type": "ephemeral"}` at the top level of the `messages.create()` call for the highest-volume model/workspace pair, then re-read the same usage window 24h later and confirm `cache_read_input_tokens` is non-zero.
- **category**: Prompt caching
- **sources**: https://platform.claude.com/docs/en/build-with-claude/prompt-caching · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report · https://platform.claude.com/docs/en/about-claude/pricing

## cache-writes-with-no-reads

- **slug**: `cache-writes-with-no-reads`
- **title**: Cache writes are paid for but almost never read back
- **symptom**: No error. In the usage report, `cache_creation.ephemeral_5m_input_tokens + cache_creation.ephemeral_1h_input_tokens` is of the same order as (or larger than) `cache_read_input_tokens` in every bucket. In the cost report grouped by `description`, the `token_type: "cache_creation.ephemeral_5m_input_tokens"` rows carry more `amount` than the `token_type: "cache_read_input_tokens"` rows.
- **mechanism**: Cache thrash. A 5-minute write is billed at **1.25x** base input and a 1-hour write at **2x**; a read is **0.1x**. Caching only pays off after roughly one read for a 5m entry and two reads for a 1h entry. When the cached prefix changes shape on nearly every call — a rotating breakpoint position, a per-request identifier landing before the breakpoint, a request rate slower than the TTL — each call writes a fresh entry that nobody ever reads, and the integration ends up paying a 1.25x–2x surcharge for a feature that is producing negative value.
- **detect**: Admin API key required. `GET /v1/organizations/usage_report/messages?starting_at= {T-7d}&bucket_width=1h&limit=168&group_by[]=api_key_id`. Per bucket compute `writes = cache_creation.ephemeral_5m_input_tokens + cache_creation.ephemeral_1h_input_tokens` and flag any `api_key_id` where `cache_read_input_tokens / writes < 1`. Cross-check spend with `GET /v1/organizations/cost_report?starting_at={T-30d}&group_by[]=description` and compare the `amount` on the `cache_creation.*` rows against the `cache_read_input_tokens` row.
- **repair**: Print, do not run: for the flagged `api_key_id`, move the `cache_control` breakpoint to the end of the stable prefix, keep volatile content (timestamps, request IDs, the user's varying question) strictly after it, and re-measure the write:read ratio over the next 24h.
- **category**: Prompt caching
- **sources**: https://platform.claude.com/docs/en/build-with-claude/prompt-caching · https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report

## one-hour-cache-ttl-not-earning-back

- **slug**: `one-hour-cache-ttl-not-earning-back`
- **title**: 1h cache TTL costs 2x but traffic never earns it back
- **symptom**: No error. `cache_creation.ephemeral_1h_input_tokens` is non-zero and material, but with `bucket_width=1h` most hours in the window show 1h writes with little or no `cache_read_input_tokens` in the same or the following hour. The cost report shows a `token_type: "cache_creation.ephemeral_1h_input_tokens"` line whose `amount` is a large share of total token spend.
- **mechanism**: `cache_control: {"type": "ephemeral", "ttl": "1h"}` is billed at **2x** base input — versus 1.25x for the 5m default — on the bet that the entry will be read at least twice before it expires. Bursty traffic breaks that bet: a burst writes the 1h entry, the burst ends, the hour elapses with no reads, and the next burst writes it again. The integration is paying a 60% premium over the 5m TTL for a retention window it never uses.
- **detect**: Admin API key required. `GET /v1/organizations/usage_report/messages?starting_at= {T-7d}&bucket_width=1h&limit=168&group_by[]=api_key_id`. For each key, count hours where `cache_creation.ephemeral_1h_input_tokens > 0` and compare against `cache_read_input_tokens` in that hour and the next. A ratio of reads to 1h-writes below 2:1 means the 1h TTL is a net loss. Attribute the money with `GET /v1/organizations/ cost_report?starting_at={T-30d}&group_by[]=description&group_by[]=workspace_id`, filtering results to `token_type == "cache_creation.ephemeral_1h_input_tokens"`.
- **repair**: Print, do not run: drop `"ttl": "1h"` back to the 5m default on the flagged key, or add a pre-warm call (`max_tokens: 0`) at the start of each burst so the 1h entry is read more than twice. Re-read the same hourly window afterward.
- **category**: Prompt caching
- **sources**: https://platform.claude.com/docs/en/build-with-claude/prompt-caching · https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report

## prompt-below-model-cache-minimum

- **slug**: `prompt-below-model-cache-minimum`
- **title**: Prompt is under the model's cache minimum, so nothing caches
- **symptom**: No error and no warning — `cache_control` is accepted and silently ignored. In the usage report grouped by `model`, a model shows `cache_creation.*` and `cache_read_input_tokens` both exactly `0` while `uncached_input_tokens` is non-zero, even though the calling code sets `cache_control`.
- **mechanism**: A prefix shorter than the model's minimum cacheable token count cannot be cached, and the API returns no error for it. The minimums are **512** tokens (Claude Opus 5, Fable 5, Mythos 5), **1,024** (Opus 4.8, Sonnet 5, Sonnet 4.6, Sonnet 4.5, Opus 4.1, Opus 4, Sonnet 4), **2,048** (Mythos Preview, Opus 4.7, Haiku 3.5), and **4,096** (Opus 4.6, Opus 4.5, Haiku 4.5). Migrating from Opus 5 (512) to Haiku 4.5 (4,096) can therefore silently switch caching off for a prompt that never changed.
- **detect**: Admin API key required. `GET /v1/organizations/usage_report/messages?starting_at= {T-30d}&bucket_width=1d&limit=31&group_by[]=model&group_by[]=api_key_id`. Flag any `(model, api_key_id)` pair where both `cache_creation` sub-fields and `cache_read_input_tokens` are `0` across every bucket while `uncached_input_tokens > 0`; then compare the model's minimum against the prefix size. On the request side (workspace key, not Admin key), `POST /v1/messages/count_tokens` with the same `system` and `tools` is a non-billed, non-mutating way to measure the prefix.
- **repair**: Print, do not run: either pad the cached prefix past the minimum for that model or drop `cache_control` on that route so the code is honest about not caching. Recheck the usage report the next day for a non-zero `cache_creation` value.
- **category**: Prompt caching
- **sources**: https://platform.claude.com/docs/en/build-with-claude/prompt-caching · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report

## cache-invalidated-by-changing-prefix

- **slug**: `cache-invalidated-by-changing-prefix`
- **title**: Cache is invalidated every call by a changing prefix
- **symptom**: No error. `cache_creation.ephemeral_5m_input_tokens` tracks `uncached_input_tokens` almost one-for-one in every bucket while `cache_read_input_tokens` stays near `0`. In the cost report, `cache_creation.ephemeral_5m_input_tokens` spend rises in lockstep with request volume rather than flattening out.
- **mechanism**: The cache is a **prefix** match rendered in the order `tools` → `system` → `messages`. Any byte change anywhere in the prefix invalidates everything after it. Changing the tool definitions invalidates the tools, system, and messages caches; toggling web search, toggling citations, changing `speed`, changing `tool_choice`, or adding/removing images invalidates progressively less. So a `datetime.now()` in the system prompt, a tool list built from an unordered dict, or a per-user preamble placed before the breakpoint turns every request into a fresh write at 1.25x with no read.
- **detect**: Admin API key required. `GET /v1/organizations/usage_report/messages?starting_at= {T-7d}&bucket_width=1h&limit=168&group_by[]=api_key_id`. Flag keys where `cache_creation.ephemeral_5m_input_tokens / (uncached_input_tokens + cache_creation.ephemeral_5m_input_tokens) > 0.5` with `cache_read_input_tokens ≈ 0` sustained across buckets — that is the signature of write-every-call. (Per-request cache diagnosis exists but is a beta *Messages* feature requiring a workspace key and the `cache-diagnosis-2026-04-07` beta, not an Admin read.)
- **repair**: Print, do not run: audit the prefix for silent invalidators — timestamps, unsorted JSON keys, a conditionally-appended tool, a per-request ID — and move each one after the last `cache_control` breakpoint. Verify by re-reading the hourly usage report.
- **category**: Prompt caching
- **sources**: https://platform.claude.com/docs/en/build-with-claude/prompt-caching · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report

## cache-hit-rate-collapsed-after-model-change

- **slug**: `cache-hit-rate-collapsed-after-model-change`
- **title**: Cache hit rate collapsed right after a model switch
- **symptom**: No error. In a daily usage report grouped by `model`, a new model ID appears on day N and, from that day forward, the organization-wide ratio `cache_read_input_tokens / (cache_read_input_tokens + uncached_input_tokens)` drops sharply while total `uncached_input_tokens` rises.
- **mechanism**: Caches are keyed per model — a model switch starts from a cold cache by definition, and the first day of writes is expected. A *sustained* collapse means something structural changed with the model: the new model's minimum cacheable token count is higher (Opus 4.6/4.5 and Haiku 4.5 need 4,096 tokens where Opus 5 needs 512), or thinking / effort parameters that are model-specific cache invalidators now differ, or the newer tokenizer (Claude 4.7 and later produce roughly 30% more tokens for the same text) moved the prefix across a boundary. The prompt did not change; the caching outcome did.
- **detect**: Admin API key required. `GET /v1/organizations/usage_report/messages?starting_at= {T-31d}&bucket_width=1d&limit=31&group_by[]=model`. Compute the cache-read share per model per day and look for a step change aligned with a new `model` value first appearing. Confirm the spend consequence with `GET /v1/organizations/cost_report?starting_at={T-31d}& group_by[]=description`, comparing `uncached_input_tokens` `amount` before and after.
- **repair**: Print, do not run: check the new model's minimum cacheable token count and its thinking/effort defaults against the old model's, adjust the breakpoint placement, and re-measure the cache-read share over the following 3 days.
- **category**: Prompt caching
- **sources**: https://platform.claude.com/docs/en/build-with-claude/prompt-caching · https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-messages-usage-report

## cache-read-share-below-breakeven

- **slug**: `cache-read-share-below-breakeven`
- **title**: Cache reads are too few to beat the write premium
- **symptom**: No error. Caching is clearly enabled — both `cache_creation.*` and `cache_read_input_tokens` are non-zero — but in the cost report the summed `amount` of the two `cache_creation.*` `token_type` rows exceeds what the same tokens would have cost as plain `uncached_input_tokens`.
- **mechanism**: The multipliers are exact and can be arithmetic-checked: 5m write **1.25x** base input, 1h write **2x**, read **0.1x**. Caching is net-positive only once reads outnumber the premium: roughly one read per 5m write, two reads per 1h write. A workload that caches but reads back only occasionally — low request rate against a 5-minute TTL, or many distinct prefixes each read once — sits on the wrong side of that line and pays more than it would with caching switched off entirely.
- **detect**: Admin API key required. `GET /v1/organizations/cost_report?starting_at={T-30d}& ending_at={T}&group_by[]=description&group_by[]=workspace_id`. Bucket `data[].results[]` by `token_type` and compare `sum(amount)` for `cache_creation.ephemeral_5m_input_tokens` + `cache_creation.ephemeral_1h_input_tokens` against `sum(amount)` for `cache_read_input_tokens`. Get the token counterparts from `GET /v1/organizations/ usage_report/messages` over the same window and evaluate `1.25*W5 + 2.0*W1h + 0.1*R` versus `1.0*(W5 + W1h + R)` in base-input units.
- **repair**: Print, do not run: for workspaces on the wrong side of breakeven, either raise request density against the cached prefix (batch callers, pre-warm) or disable `cache_control` on that route. Re-run the same arithmetic on the next 30-day window.
- **category**: Prompt caching
- **sources**: https://platform.claude.com/docs/en/about-claude/pricing · https://platform.claude.com/docs/en/api/admin-api/usage-cost/get-cost-report · https://platform.claude.com/docs/en/build-with-claude/prompt-caching

## claude-code-sessions-not-hitting-cache

- **slug**: `claude-code-sessions-not-hitting-cache`
- **title**: Claude Code sessions run with zero cache reads
- **symptom**: No error. In `GET /v1/organizations/usage_report/claude_code`, records have `model_breakdown[].tokens.cache_read == 0` (and often `cache_creation == 0`) while `tokens.input` is large and `estimated_cost.amount` is high for the number of `core_metrics.num_sessions`.
- **mechanism**: Claude Code's value depends on a long, stable prefix (project context, tool definitions, file contents) being cached across turns within a session. When cache reads are zero, either the sessions are so short that no turn reuses the prefix, or something in the harness is invalidating it each turn. Because Claude Code sends very large prefixes, the difference between 0.1x reads and 1.0x uncached input dominates the per-developer bill.
- **detect**: Admin API key required. `GET /v1/organizations/usage_report/claude_code? starting_at=YYYY-MM-DD&limit=1000` (one UTC day per request; page with `next_page`). For each record, read `actor` (`user_actor.email_address` or `api_actor.api_key_name`), `core_metrics.num_sessions`, and every `model_breakdown[]` entry's `tokens.input`, `tokens.cache_read`, `tokens.cache_creation`, and `estimated_cost.amount` (cents USD). Flag actors with `num_sessions >= 2` and `cache_read == 0`. Note: this endpoint covers Claude Code on the Claude API only — Bedrock, Google Cloud, Foundry, and Claude Platform on AWS usage is not reported here.
- **repair**: Print, do not run: check whether those actors are starting a fresh session per prompt rather than continuing one, and whether any per-turn injected context sits before the cached prefix. Re-read the same day's record after a week of changed usage.
- **category**: Prompt caching
- **sources**: https://platform.claude.com/docs/en/manage-claude/claude-code-analytics-api · https://platform.claude.com/docs/en/manage-claude/analytics-api

## openai-prompt-below-cache-minimum

- **slug**: `openai-prompt-below-cache-minimum`
- **title**: OpenAI prompts sit under the 1,024-token cache minimum
- **symptom**: No error, no warning. `usage.input_tokens_details.cached_tokens` is `0` on every response even though the same system prompt and tool block are sent thousands of times an hour. In the Usage API, `input_cached_tokens` stays flat at zero while `input_tokens` climbs. The bill shows no caching discount at all.
- **mechanism**: OpenAI's prompt caching is automatic but has a hard floor: GPT-5.6 and later require **1,024 visible input tokens** before a prefix is eligible, and earlier models require **2,048**. A prompt that is stable but short — a terse system message plus a one-line user turn — never crosses the floor, so the cache never engages no matter how repetitive the traffic. Because caching is automatic there is no flag to set and therefore no flag whose absence points at the problem.
- **detect**: Admin-read key → `GET /v1/organization/usage/completions?start_time=<7d ago>&bucket_width=1d&group_by[]=model&group_by[]=project_id`. For each bucket compute mean input tokens per request as `results[].input_tokens / results[].num_model_requests`. Flag any model whose mean sits below 1,024 (2,048 for pre-GPT-5.6 ids) **and** whose `results[].input_cached_tokens` is `0` — that pairing proves the traffic is structurally ineligible rather than merely unlucky. Project read-only key → confirm the model generation with `GET /v1/models/{model}`.
- **repair**: Print the mean input tokens per request and the model's floor. Either move more stable material into the prefix — full tool schemas, few-shot examples, retrieval instructions — so the shared prefix crosses 1,024 tokens, or accept that this workload cannot be cached and stop budgeting for a discount that will never arrive. Do not pad the prompt with filler purely to cross the threshold; padding is billed at full rate on the first call and only pays back at very high repeat volume.
- **category**: Prompt caching
- **sources**: https://developers.openai.com/api/docs/guides/prompt-caching · https://developers.openai.com/api/docs/api-reference/usage

## prompt-cache-key-not-set

- **slug**: `prompt-cache-key-not-set`
- **title**: prompt_cache_key is unset so identical prefixes miss the cache
- **symptom**: No error. `usage.input_tokens_details.cached_tokens` is non-zero but erratic — high on some calls, zero on others, for what is provably the same prefix. The cached share in the Usage API hovers well below the fraction of the prompt that is actually static, and the hit rate gets worse as traffic scales out across more workers.
- **mechanism**: Cache lookup is prefix-based *and* routing-sensitive. `prompt_cache_key` exists to make "requests with the same prefix reach the same cache"; the docs are explicit that it influences routing and does "not pin requests to a machine or guarantee a cache read hit". Without it, a fleet spraying identical prompts across many backends scatters them over many caches, so each machine sees a cold prefix. The more you scale horizontally, the worse the hit rate gets — the opposite of the intuition.
- **detect**: Admin-read key → `GET /v1/organization/usage/completions?start_time=<7d ago>&bucket_width=1h&group_by[]=model&group_by[]=project_id` → compute `results[].input_cached_tokens / results[].input_tokens` per bucket. A ratio that is materially below the known static share of the prompt, and that *degrades* during peak hours when concurrency is highest, is the routing-scatter signature rather than a prefix-instability one (prefix instability produces a flat low ratio, not a load-correlated one). Project read-only key → read `usage.input_tokens_details.cached_tokens` off any live response to confirm caching engages at all.
- **repair**: Set `prompt_cache_key` to a value that is stable per prompt-template and coarse enough to concentrate traffic — the template name plus tenant, not a per-request id. Print: `client.responses.create(..., prompt_cache_key="rag-answer-v3")`. Keep it out of the prompt itself; it is a routing hint, not content.
- **category**: Prompt caching
- **sources**: https://developers.openai.com/api/docs/guides/prompt-caching

## cache-invalidated-by-request-option-churn

- **slug**: `cache-invalidated-by-request-option-churn`
- **title**: Changing reasoning.effort or tools voids the cache every call
- **symptom**: No error. `input_cached_tokens` is at or near zero across every bucket even though the system prompt and tool definitions are, in the developer's mental model, identical on every request. Cost per request does not fall as traffic grows.
- **mechanism**: The cached prefix covers more than the message text. OpenAI invalidates it when the model changes, when tool definitions, their ordering or their schemas change, and when `parallel_tool_calls`, `text.format`, `reasoning.effort`, `text.verbosity` or `context_management` change. Code that builds the tool array from a dict, or that picks `reasoning.effort` per request based on input length, mutates the prefix on every call without anyone realising the prefix is what is being mutated.
- **detect**: Admin-read key → `GET /v1/organization/usage/completions?start_time=<7d ago>&bucket_width=1d&group_by[]=model&group_by[]=project_id`. A project with high `num_model_requests`, large `input_tokens`, and `input_cached_tokens` at or near `0` for every bucket — while a sibling project on the same model shows a healthy cached share — is prefix churn, not ineligibility (check the mean input tokens per request is above the 1,024 floor first, which rules out `openai-prompt-below-cache-minimum`). On Anthropic the equivalent read is `GET /v1/organizations/usage_report/messages` with `cache_creation.*` large and `cache_read_input_tokens` near zero.
- **repair**: Print the invalidating knobs to freeze: serialise `tools` from an ordered list, not a dict; pin `reasoning.effort`, `text.verbosity`, `text.format` and `parallel_tool_calls` per route rather than per request; and put anything genuinely variable — timestamps, user ids, retrieved chunks — *after* the static block, never before it. Cache matching is prefix-only, so one early variable byte costs the whole prefix.
- **category**: Prompt caching
- **sources**: https://developers.openai.com/api/docs/guides/prompt-caching

## prompt-cache-retention-left-at-default

- **slug**: `prompt-cache-retention-left-at-default`
- **title**: Cache retention default means overnight jobs always run cold
- **symptom**: No error. Cached token share is respectable during a busy hour and collapses to zero at the start of every scheduled job, every morning, and after any quiet period. The Usage API shows `input_cached_tokens` tracking request density rather than prefix stability.
- **mechanism**: Cached prefixes are evicted after a short idle period. On GPT-5.6 and later, retention is controlled by `prompt_cache_options.ttl` (currently `"30m"`); on earlier models by `prompt_cache_retention`, which accepts `"in_memory"` (the short default) or `"24h"`. A nightly batch, a low-traffic tenant, or a cron job that fires every few hours falls outside the default window every single time, so it pays the uncached rate on a prefix that has not changed in months.
- **detect**: Admin-read key → `GET /v1/organization/usage/completions?start_time=<14d ago>&bucket_width=1h&group_by[]=project_id&group_by[]=model` → plot `results[].input_cached_tokens / results[].input_tokens` against `results[].num_model_requests` per hour. Buckets with non-trivial request volume but a cached share of zero, occurring after gaps in traffic, are eviction rather than misconfiguration. Contrast with continuously-busy hours on the same project to confirm the prefix is cacheable at all.
- **repair**: For pre-GPT-5.6 models, print `prompt_cache_retention="24h"` on the affected route (it is opt-in and costs nothing extra to set). For GPT-5.6 and later, set `prompt_cache_options={"ttl": "30m"}` explicitly so the intent is visible, and reshape the schedule: run intermittent jobs in a single contiguous window rather than scattered across the day, so the first call warms a cache the rest can read.
- **category**: Prompt caching
- **sources**: https://developers.openai.com/api/docs/guides/prompt-caching

## reasoning-model-rejects-max-tokens

- **slug**: `reasoning-model-rejects-max-tokens`
- **title**: Reasoning models reject max_tokens, require max_completion_tokens
- **symptom**: `400` `invalid_request_error` with `code: "unsupported_parameter"`, `param: "max_tokens"`, message `Unsupported parameter: 'max_tokens' is not supported with this model. Use 'max_completion_tokens' instead.` Hits every request; 100% failure rate the moment the model constant is swapped.
- **mechanism**: On Chat Completions the o-series and GPT-5.x reasoning models replaced `max_tokens` with `max_completion_tokens` because the cap must cover invisible reasoning tokens as well as visible output. On the Responses API the equivalent field is `max_output_tokens`. A wrapper library or config file that hardcodes `max_tokens` breaks on the first migration to a reasoning model — which is exactly what every deprecation entry above forces you to do.
- **detect**: Admin-read key → `GET /v1/organization/usage/completions?start_time=<24h ago>&bucket_width=1h&group_by[]=model&group_by[]=project_id`; a project whose model was swapped to a GPT-5.x id and whose `results[].num_model_requests` is present while `results[].output_tokens` is `0` indicates every call is erroring before generation. Project read-only key → confirm the target is a reasoning model via `GET /v1/models/{model}` returning `200` while the app 400s, which isolates the fault to parameters rather than access.
- **repair**: Chat Completions: `"max_tokens": 4096` → `"max_completion_tokens": 4096`. Responses API: `"max_tokens": 4096` → `"max_output_tokens": 4096`. Raise the value — the cap now also has to absorb reasoning tokens.
- **category**: Errors and reliability
- **sources**: https://developers.openai.com/api/docs/guides/reasoning · https://github.com/BerriAI/litellm/issues/13381

## reasoning-model-rejects-temperature

- **slug**: `reasoning-model-rejects-temperature`
- **title**: Reasoning models reject any temperature other than 1
- **symptom**: `400` `invalid_request_error` with `code: "unsupported_value"`, `param: "temperature"`, message `Unsupported value: 'temperature' does not support 0.2 with this model. Only the default (1) value is supported.` Same shape for `top_p`, `presence_penalty`, `frequency_penalty`, `logprobs`.
- **mechanism**: Reasoning models control output variance through `reasoning.effort` (`none`, `minimal`, `low`, `medium`, `high`, `xhigh`, `max`) rather than sampling parameters, so the sampling knobs are rejected outright instead of ignored. Codebases that set `temperature=0` "for determinism" — an extremely common default — fail on every call after a model swap.
- **detect**: Admin-read key → `GET /v1/organization/usage/completions?start_time=<24h ago>&bucket_width=1h&group_by[]=model&group_by[]=api_key_id`; a key whose traffic against a GPT-5.x/o-series model shows `num_model_requests` with `input_tokens` and `output_tokens` both `0` is 400-ing pre-generation. Project read-only key → `GET /v1/models/{model}` returns `200`, proving the id is valid and the failure is parameter-level.
- **repair**: Delete `temperature`, `top_p`, `presence_penalty`, `frequency_penalty` from the request body for reasoning models and replace the intent with `reasoning={"effort": "low"}` for cheap/fast or `"high"`/`"max"` for quality. Do not send `temperature: 1` explicitly — omit it.
- **category**: Errors and reliability
- **sources**: https://developers.openai.com/api/docs/guides/reasoning · https://github.com/getzep/graphiti/issues/874

## context-length-exceeded

- **slug**: `context-length-exceeded`
- **title**: Input plus requested output exceeds the model context window
- **symptom**: `400` `invalid_request_error` with `code: "context_length_exceeded"` and message `This model's maximum context length is N tokens. However, you requested M tokens (X in the messages, Y in the completion). Please reduce the length of the messages or completion.` Typically intermittent — only long conversations or big RAG payloads trip it.
- **mechanism**: The window covers input + output + (for reasoning models) invisible reasoning tokens together. GPT-5.6 Sol/Terra/Luna carry a 1.05M-token window with 128K max output, but a smaller pinned legacy model or a fine-tune may be far smaller, so the same payload that fits one model 400s on another. The docs recommend reserving at least 25,000 tokens for reasoning and output.
- **detect**: Admin-read key → `GET /v1/organization/usage/completions?start_time=<7d ago>&bucket_width=1h&group_by[]=model&group_by[]=project_id` and compute peak `results[].input_tokens / results[].num_model_requests`; flag any model where the peak per-request input is within 25,000 tokens of the model's context window. Project read-only key → `GET /v1/models/{model}` confirms which model id is in play so you can look up its window. Corroborating symptom: hours where `num_model_requests > 0` but `output_tokens == 0` are pre-generation 400s.
- **repair**: Either raise headroom — `max_output_tokens` down so `input + max_output_tokens + 25000 < context_window` — or switch to a large-window model (`model="gpt-5.6-sol"`, 1.05M context). For RAG, cap retrieved chunks; for chat, truncate or summarise history above a token budget rather than letting it grow unbounded.
- **category**: Errors and reliability
- **sources**: https://developers.openai.com/api/docs/guides/reasoning · https://developers.openai.com/api/docs/models

## silent-output-truncation

- **slug**: `silent-output-truncation`
- **title**: Responses stop mid-answer with status incomplete, not an error
- **symptom**: HTTP `200`. The response body has `status: "incomplete"` and `incomplete_details.reason: "max_output_tokens"` (Chat Completions equivalent: `choices[0].finish_reason == "length"`). Downstream JSON parsing throws on truncated output; users see sentences cut off mid-word. Full token cost is charged.
- **mechanism**: `max_output_tokens` caps reasoning tokens plus visible output together. A cap sized for the old non-reasoning model gets entirely consumed by reasoning on a GPT-5.x model, so zero visible text is produced yet the call is billed and returns 200 — nothing raises an exception in the SDK.
- **detect**: Admin-read key → `GET /v1/organization/usage/completions?start_time=<7d ago>&bucket_width=1h&group_by[]=model` and look for buckets where mean output tokens per request sits exactly at a round number (the configured cap) — a hard ceiling in the data rather than a distribution is truncation. Compare `output_tokens` against `output_tokens_details.reasoning_tokens` for the same buckets: when reasoning tokens approach total output tokens, visible output is near zero.
- **repair**: Raise the cap and reserve reasoning room: `max_output_tokens=1024` → `max_output_tokens=25000` (docs recommend reserving at least 25,000 tokens for reasoning plus output), or lower cost instead with `reasoning={"effort":"low"}`. Add an explicit check on `response.status == "incomplete"` / `finish_reason == "length"` before parsing.
- **category**: Errors and reliability
- **sources**: https://developers.openai.com/api/docs/guides/reasoning

## service-tier-not-allowed

- **slug**: `service-tier-not-allowed`
- **title**: service_tier value rejected because the project disallows it
- **symptom**: `400` `invalid_request_error` with `code: "service_tier"`, message `The requested service tier is not allowed for the project.` Every request carrying `"service_tier": "fast"` (or `"priority"`, or `"flex"`) fails while identical requests without the field succeed.
- **mechanism**: Service tier is allow-listed per project. Fast mode (renamed from Priority processing on 2026-07-30 — both `"fast"` and `"priority"` are accepted values) must be enabled under Settings → Project → General → Project Service Tier. Flex is beta with limited model availability. Fast mode also excludes fine-tuned models and embeddings, so a request pairing `service_tier: "fast"` with a fine-tune fails regardless of project settings.
- **detect**: Admin-read key → `GET /v1/organization/projects/{project_id}` and read the project's service tier setting; compare against the `service_tier` value the app sends. Project read-only key → `GET /v1/models/{model}` confirms the model exists, isolating the fault to the tier field. Admin-read key → `GET /v1/organization/usage/completions?start_time=<24h ago>&bucket_width=1h&group_by[]=project_id`: a project with requests but no output tokens is 400-ing pre-generation.
- **repair**: Either remove the field (`"service_tier": "fast"` → omit, which uses the project default) or enable Fast mode for the project in Settings → Project → General → Project Service Tier. If the model is a fine-tune or an embedding model, remove `service_tier` unconditionally — Fast mode does not support them.
- **category**: Errors and reliability
- **sources**: https://developers.openai.com/api/docs/guides/error-codes · https://developers.openai.com/api/docs/guides/fast-mode

## server-errors-not-retried

- **slug**: `server-errors-not-retried`
- **title**: 500 and 503 overloaded errors surface to users unretried
- **symptom**: `500` `InternalServerError` ("issue on our servers while processing your request"), `503` overloaded ("our servers are experiencing high traffic"), or `503` Slow Down ("traffic has increased significantly and is overloading the model"). Errors arrive in correlated clusters and vanish; user-facing requests fail hard because the client has `max_retries=0` or catches only `RateLimitError`.
- **mechanism**: These are transient server-side conditions with no client-side cause. The documented remedy differs per code: 500 → retry after a brief wait; 503 overloaded → retry with exponential backoff; **503 Slow Down → reduce your request rate for 15 minutes**, which backoff alone will not satisfy since naive retries keep the offered load high. Also `ConflictError` (409) and `UnprocessableEntityError` (422) are documented as retryable, and many clients treat all 4xx as fatal.
- **detect**: Admin-read key → `GET /v1/organization/usage/completions?start_time=<7d ago>&bucket_width=1h&group_by[]=model&group_by[]=project_id`; hours where `num_model_requests` dips sharply against the workload's known cadence, with no matching change in `input_tokens` per request, indicate server-side rejection rather than reduced demand. Correlate the dip windows against status.openai.com incident times. Project read-only key → repeated `GET /v1/models` polling that returns 5xx confirms a live incident rather than an app bug.
- **repair**: Set `max_retries` to at least 3 on the client (do not leave it at `0`) and catch `InternalServerError`, `APITimeoutError`, `APIConnectionError`, `ConflictError` and `UnprocessableEntityError` alongside `RateLimitError`. Add a circuit breaker that drops offered load for 15 minutes on 503 Slow Down rather than retrying into it.
- **category**: Errors and reliability
- **sources**: https://developers.openai.com/api/docs/guides/error-codes

## seed-determinism-unreliable

- **slug**: `seed-determinism-unreliable`
- **title**: seed no longer reproduces output after a fingerprint change
- **symptom**: No error. Golden-file tests and cached-by-hash layers that assume identical output for identical `(seed, prompt, params)` start failing or missing. The `system_fingerprint` value in the Chat Completions response differs from the recorded one. On the Responses API and reasoning models, `seed` is not honoured at all.
- **mechanism**: `seed` is explicitly best-effort, not a guarantee: "the system will make a best effort to sample deterministically". `system_fingerprint` identifies the current combination of model weights, infrastructure and configuration, and changes whenever OpenAI updates any of them — at which point the same seed produces different output. Reasoning models remove the sampling knobs entirely (see `reasoning-model-rejects-temperature`), so determinism strategies built on `seed` plus `temperature=0` do not survive a migration onto GPT-5.x.
- **detect**: Project read-only key → record `system_fingerprint` from a canary Chat Completions response and diff it against the stored baseline on each run; any change invalidates seed-based reproducibility. Admin-read key → `GET /v1/organization/usage/completions?start_time=<30d ago>&bucket_width=1d&group_by[]=model` and watch mean output tokens per request for a step change on the same day the fingerprint moved. `GET /v1/models/{model}` → a bare alias id (no trailing date) means the underlying weights can move under you at any time.
- **repair**: Stop treating `seed` as a cache key or a test oracle. Pin the model snapshot (`model="gpt-5.6"` → `model="gpt-5.6-sol"`), assert on structure and semantics rather than exact strings, and record `system_fingerprint` alongside every golden file so a fingerprint change explains the diff instead of failing the build. For genuine determinism, cache your own responses rather than relying on the API.
- **category**: Errors and reliability
- **sources**: https://cookbook.openai.com/examples/reproducible_outputs_with_the_seed_parameter · https://developers.openai.com/api/reference/resources/chat/subresources/completions/methods/create

## live-project-zero-usage-buckets

- **slug**: `live-project-zero-usage-buckets`
- **title**: A project that should be live shows zero usage buckets
- **symptom**: No error anywhere — no 4xx, no 5xx, no exception, because no request is being made. A feature that is supposed to be calling the API has silently stopped. It is discovered weeks later by a customer, or never. The usage response for that project returns buckets with empty `results` arrays.
- **mechanism**: An integration can go dark without failing loudly: a feature flag flipped, a queue consumer died, a config change pointed at the wrong key, a code path got refactored behind a condition that is now always false, or an upstream service stopped producing the events that trigger it. All of these produce *silence*, and silence is the one thing application monitoring is worst at detecting — dashboards alert on error rates and latency, both of which look perfect at zero traffic.
- **detect**: Organization **ADMIN** key required. `GET /v1/organization/usage/completions?start_time={now-14d}&bucket_width=1d&limit=14&group_by=project_id`. Buckets are returned for the full range even when there was no traffic, so a live-but-idle project shows `data[].results` as an empty array (or omits that `project_id`) for recent buckets while earlier buckets contain results. Flag any `project_id` with non-zero `num_model_requests` in the first half of the window and zero in the last 48 hours. Because this endpoint covers only completions, repeat the sweep across the other usage surfaces that the project uses — `/v1/organization/usage/embeddings`, `/v1/organization/usage/images`, `/v1/organization/usage/audio_speeches`, `/v1/organization/usage/audio_transcriptions`, `/v1/organization/usage/moderations`, `/v1/organization/usage/file_search_calls`, `/v1/organization/usage/web_search_calls` — each takes the same `start_time` / `bucket_width` / `limit` / `group_by=project_id` shape. Corroborate with `GET /v1/organization/projects/{project_id}/api_keys?owner_project_access=any`: the project's key `last_used_at` frozen at the same timestamp confirms the integration, not just the model call, went quiet. Allow for usage data lag — do not alert on the current partial bucket.
- **repair**: Print, per project: last bucket with traffic, hours since, and prior 7-day mean `num_model_requests`. Recommend a scheduled liveness check that treats *absence* of usage as an alert condition — a floor threshold per project, not just a ceiling — and note that this is the one check whose value comes entirely from firing on zero.
- **category**: Errors and reliability
- **sources**: https://platform.openai.com/docs/api-reference/usage · https://developers.openai.com/cookbook/examples/completions_usage_api · https://github.com/openai/openai-python/blob/main/api.md

## requests-diverge-from-token-volume

- **slug**: `requests-diverge-from-token-volume`
- **title**: Request count grew far faster than tokens: a retry storm
- **symptom**: No error visible to the application, because the retries eventually succeed. `num_model_requests` climbs 3–10x week over week while `input_tokens` and `output_tokens` stay roughly flat. Latency percentiles get worse. Rate limits start being hit at volumes that used to be comfortable.
- **mechanism**: Every OpenAI SDK retries automatically on `429` and `5xx`, and application code frequently adds a second retry layer on top — a wrapper, a queue redelivery, a job runner. The layers multiply: two levels of three attempts is nine requests for one logical call. Failed and retried attempts consume rate-limit budget and, for partially-completed streams, real tokens. The divergence between request count and token count is the fingerprint, because a genuine traffic increase moves both together while a retry storm moves only one.
- **detect**: Organization **ADMIN** key required. `GET /v1/organization/usage/completions?start_time={now-14d}&bucket_width=1h&limit=168&group_by=model&group_by=project_id`. Per bucket compute `(input_tokens + output_tokens) / num_model_requests`. A sharp *drop* in tokens-per-request while `num_model_requests` rises is the retry signature — many short, failed or truncated calls. Compare the two series' week-over-week growth rates and flag when request growth exceeds token growth by more than 2x. Cross-reference `GET /v1/organization/projects/{project_id}/rate_limits` for that model's `max_requests_per_1_minute` and `max_tokens_per_1_minute` — a retry storm typically shows the project pinned near its RPM ceiling while nowhere near its TPM ceiling, which is itself diagnostic. Also check `group_by=service_tier`, since a workload spilling between tiers changes the retry economics.
- **repair**: Print the two growth rates side by side, the tokens-per-request trend, and the current RPM/TPM headroom. Recommend collapsing to a single retry layer — set `max_retries` explicitly on the SDK client and remove the outer wrapper, or set `max_retries=0` and keep the outer one — with exponential backoff plus jitter, and a circuit breaker so a sustained failure stops re-amplifying. Print the RPM increase call (`POST /v1/organization/projects/{project_id}/rate_limits/{rate_limit_id}`) only as a secondary measure, after the retry layering is fixed.
- **category**: Errors and reliability
- **sources**: https://platform.openai.com/docs/api-reference/usage/completions · https://platform.openai.com/docs/guides/rate-limits · https://github.com/openai/openai-python/blob/main/api.md

## fine-tune-job-failed-with-error-code

- **slug**: `fine-tune-job-failed-with-error-code`
- **title**: Fine-tuning job ended `failed` and `error.code` went unread
- **symptom**: `GET /v1/fine_tuning/jobs/{id}` returns `"status": "failed"` with `"error": {"code": "invalid_training_file" | "invalid_n_examples" | "exceeded_quota" | ..., "message": "...", "param": "training_file"}`, `fine_tuned_model: null` and `trained_tokens: null`. `POST /v1/fine_tuning/jobs` had returned 200 hours earlier.
- **mechanism**: Job creation is asynchronous: the job moves `validating_files` → `queued` → `running` → `succeeded`/`failed`/`cancelled`. Validation and training failures surface only on the job object, never as an HTTP error on create. `error.param` names the offending input (usually `training_file` or `validation_file`). Teams that kick off a job and check back a week later find the deploy silently still pointing at the old model.
- **detect**: `GET /v1/fine_tuning/jobs?limit=100` (paginate on `after`; `metadata[k]=v` filters if you tag jobs). Flag `status == "failed"` and print `error.code`, `error.message`, `error.param`. For narrative detail call `GET /v1/fine_tuning/jobs/{id}/events?limit=100` and read the `level`/`message` fields. Requires: project read key.
- **repair**: print — `Read error.code and act: "invalid_training_file" means the JSONL is malformed — every line needs a messages array with at least one assistant message; "invalid_n_examples" means too few/too many examples; "exceeded_quota" is a billing problem. Fix, re-upload with purpose="fine-tune", and re-create. Poll the job to a terminal status in CI instead of assuming create == trained.`
- **category**: Errors and reliability
- **sources**: https://developers.openai.com/api/docs/api-reference/fine-tuning · https://community.openai.com/t/fine-tuning-error-the-job-failed-due-to-an-invalid-training-file-unexpected-file-format-expected-either-prompt-completion-pairs-or-chat-messages/726568

## fine-tune-training-file-validation-errors

- **slug**: `fine-tune-training-file-validation-errors`
- **title**: Training file rejected during `validating_files`
- **symptom**: `GET /v1/fine_tuning/jobs/{id}` sits in `"status": "validating_files"` and then flips to `failed` with `error.param == "training_file"` and a message such as *"The job failed due to an invalid training file. Unexpected file format, expected either prompt/completion pairs or chat messages."* The uploaded file itself shows `purpose: "fine-tune"` and looks fine in `GET /v1/files`.
- **mechanism**: The Files API accepts any bytes for `purpose: "fine-tune"` — it does not parse them. Format validation happens later, inside the job. A trailing blank line, a UTF-8 BOM, a JSON array instead of JSONL, a row with no assistant message, or a schema mixed between the legacy prompt/completion form and the chat form all pass upload and fail validation. The file keeps consuming project storage either way.
- **detect**: `GET /v1/fine_tuning/jobs?limit=100`, flag `status == "validating_files"` older than ~1 hour and any `failed` job whose `error.param` is `training_file` or `validation_file`. Then `GET /v1/files?purpose=fine-tune` and report files whose id appears only on failed jobs — those are dead uploads still billing storage. `GET /v1/fine_tuning/jobs/{id}/events` gives the per-line validation messages. Requires: project read key.
- **repair**: print — `Validate the JSONL locally before upload: one JSON object per line, no trailing newline object, no BOM, each line {"messages":[...]} with at least one assistant turn, consistent schema across all rows. Delete the rejected file (DELETE /v1/files/{file_id}) so it stops counting against the 2.5 TB project quota.`
- **category**: Errors and reliability
- **sources**: https://developers.openai.com/api/docs/api-reference/fine-tuning · https://developers.openai.com/api/docs/api-reference/files

## realtime-session-60-minute-cap

- **slug**: `realtime-session-60-minute-cap`
- **title**: Realtime session dies at the 60-minute server-side ceiling
- **symptom**: A live WebRTC/WebSocket Realtime connection drops mid-conversation with no application-level error. The `session.created` event carried an `expires_at` timestamp roughly 60 minutes out; the server closes at that point regardless of activity. Users experience it as the assistant going silent.
- **mechanism**: Realtime sessions are capped at a maximum duration of 60 minutes (raised from an earlier 30-minute limit). There is no server-side parameter to extend the lifetime once connected — `expires_at` on `session.created` is the only warning. Long-lived kiosk, support-line and always-on agent deployments hit this daily. Realtime audio also bills at audio-token rates, so a forgotten open session is expensive as well as fragile.
- **detect**: Read-only detection is at the org layer: `GET /v1/organization/usage/completions?start_time=...&bucket_width=1h&group_by=model` (**admin read key**) filtered to realtime model ids — look for `input_audio_tokens`/`output_audio_tokens` accumulating in ~60-minute sawtooth blocks, and for hours of continuous audio billing that imply sessions running to the cap. Also check `GET /v1/models` for whether you are still pinned to a deprecated realtime snapshot. Requires: admin read key; project read key for `/v1/models`.
- **repair**: print — `Track expires_at from the session.created event and hand off gracefully before it fires: open a fresh session and replay a summarised transcript rather than the full history. Enforce your own shorter session budget so cost is bounded. Do not rely on the connection staying open past 60 minutes.`
- **category**: Errors and reliability
- **sources**: https://developers.openai.com/api/docs/guides/realtime · https://community.openai.com/t/realtime-api-session-timeout-post-ga/1357331

## audio-transcription-25mb-limit

- **slug**: `audio-transcription-25mb-limit`
- **title**: Transcription rejects any upload over the 25 MB file limit
- **symptom**: `POST /v1/audio/transcriptions` returns HTTP 413 (or 400 `invalid_request_error`) on files above the cap. The docs are explicit: *"Files can be up to 25 MB."* Supported input formats are mp3, mp4, mpeg, mpga, m4a, wav and webm — anything else 400s too.
- **mechanism**: The 25 MB ceiling is on the uploaded bytes, not on duration, so an uncompressed WAV blows past it in about 20 minutes while a 64 kbps MP3 survives for hours. Pipelines that record in WAV and transcribe "whatever the user uploads" fail on exactly the long recordings that matter most. Naive chunking then re-introduces accuracy loss by cutting mid-sentence.
- **detect**: If audio is staged through the Files API, `GET /v1/files?limit=10000` and flag any object with an audio filename extension and `bytes > 26_214_400`. At org level, `GET /v1/organization/usage/audio_transcriptions?start_time=...&bucket_width=1d` (**admin read key**) — flat or missing buckets on days your ingest ran indicate wholesale rejection. Requires: project read key; admin read key for usage.
- **repair**: print — `Compress before upload (mp3/m4a at a modest bitrate keeps hours of speech under 25 MB) or split into <25 MB segments on silence boundaries, never mid-sentence, and stitch the transcripts. Validate file size client-side before the request so the failure is caught at ingest rather than at the API.`
- **category**: Errors and reliability
- **sources**: https://developers.openai.com/api/docs/guides/speech-to-text · https://developers.openai.com/api/docs/api-reference/audio

## previous-response-id-chain-broken

- **slug**: `previous-response-id-chain-broken`
- **title**: `previous_response_id` 404s once the prior response is gone
- **symptom**: `POST /v1/responses` returns HTTP 404 `invalid_request_error` naming `previous_response_id` — the referenced response no longer exists. The user sees a conversation that abruptly forgets everything, or an error mid-thread.
- **mechanism**: `previous_response_id` chains server-side state. That state only exists if the earlier call used `store: true`, and it lives for a bounded retention period (at least 30 days) or until someone calls `DELETE /v1/responses/{id}`. A ZDR org, a call that set `store: false`, a manual cleanup sweep, or simply an old thread breaks the chain. Nothing warns at write time; the break only surfaces on the next turn.
- **detect**: For each `previous_response_id` your application has recorded, probe `GET /v1/responses/{response_id}` and flag non-200s. On responses that do resolve, confirm the echoed `store` is true and read `created_at` to find chains approaching the retention edge. Requires: project read key.
- **repair**: print — `Do not rely on previous_response_id as durable memory. Either use conversations (an explicit, deletable object) or keep the full message history in your own store and replay it. Before continuing an old thread, verify the parent response still resolves and fall back to replaying local history when it does not.`
- **category**: Errors and reliability
- **sources**: https://developers.openai.com/api/docs/api-reference/responses · https://developers.openai.com/api/docs/guides/your-data

## anthropic-version-header-missing-or-ancient

- **slug**: `anthropic-version-header-missing-or-ancient`
- **title**: anthropic-version is missing or pinned to 2023-01-01
- **symptom**: Missing header: `400 invalid_request_error` on every request from that client. Pinned to `2023-01-01`: requests may work today but are on a deprecated version — "Previous versions are considered deprecated and may be unavailable for new users" — and the client will not receive the `2023-06-01` SSE format (incremental named events, no `data: [DONE]`).
- **mechanism**: "When making API requests, you must send an `anthropic-version` request header." The official SDKs set `anthropic-version: 2023-06-01` automatically; hand-rolled `curl`/`fetch`/`requests` clients, webhook receivers, proxies and gateways written from a half-remembered snippet do not. Only two values have ever existed: `2023-01-01` (initial release) and `2023-06-01` (current). A version pin also freezes the error-condition and enum-variant behavior the version policy allows Anthropic to change.
- **detect**: Workspace/project API key, read-only probe against the Models endpoint (no tokens billed, no state changed): `curl -sS -o /dev/null -w '%{http_code}' https://api.anthropic.com/v1/models -H "x-api-key: $KEY"` with no version header → 400; repeat with `-H 'anthropic-version: 2023-06-01'` → 200; repeat with `-H 'anthropic-version: 2023-01-01'` and record the status. Any proxy or gateway you can reach read-only should be probed the same way, since the header may be injected or stripped in transit.
- **repair**: Print: which clients omit the header, which pin `2023-01-01`, and the one-line fix (`anthropic-version: 2023-06-01`, or drop the raw HTTP client for the official SDK, which sets it for you). Do not patch the client.
- **category**: Errors and reliability
- **sources**: https://platform.claude.com/docs/en/api/versioning · https://platform.claude.com/docs/en/api/errors

## invalid-beta-header-value

- **slug**: `invalid-beta-header-value`
- **title**: A misspelled anthropic-beta value 400s the whole call
- **symptom**: `400 invalid_request_error` with message: ``Unexpected value(s) `invalid-beta-name` for the `anthropic-beta` header. Please consult our documentation at platform.claude.com/docs or try again without the header.`` The same 400 is returned for a beta your organization does not have access to, so a typo and a permissions gap look identical.
- **mechanism**: Beta names follow `feature-name-YYYY-MM-DD` and must match exactly. Multiple betas go in one comma-separated header (`anthropic-beta: feature1,feature2`); the SDKs take them as `betas=[...]`. In the `ant` CLI only the first `--beta` flag takes effect, so repeating the flag silently drops betas. Endpoint-scoped headers are not freely combinable: on memory-store endpoints `agent-memory-2026-07-22` **replaces** `managed-agents-2026-04-01` and sending both returns 400.
- **detect**: Workspace/project API key: `GET /v1/models` accepts and validates the `anthropic-beta` header, so it is a free, read-only, zero-token validator for any beta string — `curl -sS -o /dev/null -w '%{http_code}' https://api.anthropic.com/v1/models -H "x-api-key: $KEY" -H 'anthropic-version: 2023-06-01' -H "anthropic-beta: <value>"`. 400 means invalid or not entitled; 200 means accepted. Loop it over every beta string found in the codebase.
- **repair**: Print: each rejected beta string, whether a near-match exists in the documented set (e.g. `context-1m-2025-08-07`, `context-management-2025-06-27`, `model-context-window-exceeded-2025-08-26`, `output-300k-2026-03-24`, `fast-mode-2026-02-01`, `task-budgets-2026-03-13`, `compact-2026-01-12`, `structured-outputs-2025-11-13`), and whether the call sites use repeated `--beta` flags. Do not send the corrected request.
- **category**: Errors and reliability
- **sources**: https://platform.claude.com/docs/en/api/beta-headers · https://platform.claude.com/docs/en/api/models · https://platform.claude.com/docs/en/api/errors

## stale-beta-header-after-graduation

- **slug**: `stale-beta-header-after-graduation`
- **title**: Code still sends a beta header that has gone GA
- **symptom**: No error and no obvious breakage — which is the problem. Requests that still send a graduated beta header keep receiving the **older beta response shape**, so a client sitting on the header quietly misses fields and pagination that GA callers get, and drifts further with every release.
- **mechanism**: Betas graduate and the header becomes optional but not inert. `files-api-2025-04-14` and `skills-2025-10-02` graduated in August 2026: requests without the header get file expiration (`expires_in_seconds` / `expires_at`), `page`/`next_page` pagination and the `ids[]` filter, while requests that still send the header keep the previous format. `ce-user-management-2026-07-13` is likewise no longer required. Other features that shed their header entirely: `search-results-2025-06-09`, the code execution / web fetch / tool search / memory tools, the effort parameter, fine-grained tool streaming, the 1-hour prompt-cache TTL, 8,192-token Sonnet 3.5 output (`max-tokens-3-5-sonnet-2024-07-15`).
- **detect**: Workspace/project API key: `GET /v1/models -H "anthropic-beta: files-api-2025-04-14"` still returns 200, so acceptance is not proof of currency — the finding is the header's *presence* in code. Confirm the shape divergence read-only by calling the same GET twice, once with and once without the header, and diffing the JSON: `GET /v1/files` (with vs. without `files-api-2025-04-14`) shows the `expires_at` field and `page`/`next_page` keys appearing only in the GA form. Record every beta string your clients send and mark those absent from the current documented beta list as graduated.
- **repair**: Print: each graduated header still being sent, the response-shape difference it pins you to, and the migration note to read before dropping it. Do not remove headers.
- **category**: Errors and reliability
- **sources**: https://platform.claude.com/docs/en/api/beta-headers · https://platform.claude.com/docs/en/release-notes/overview · https://platform.claude.com/docs/en/api/models

## overloaded-529-clusters

- **slug**: `overloaded-529-clusters`
- **title**: 529 overloaded_error arrives in clusters and is fatal
- **symptom**: `529` with `"error": {"type": "overloaded_error"}`, typically several in a row across unrelated requests. Non-SDK clients that only special-case 429 and 500 let these fall through to a generic failure path and drop the work.
- **mechanism**: "529 errors can occur when the API experiences high traffic across all users" — a platform-wide capacity condition, not something your traffic caused, and it clusters in time. It is a retryable transient; the SDKs retry 5xx twice by default with exponential backoff. Priority Tier existed to minimize these but capacity commitments are no longer available for purchase, so 529 handling is now everyone's problem.
- **detect**: There is no endpoint that reports 529s directly; the read-only signal is the gap between requests your client attempted and requests the platform actually billed. Admin API key: `GET /v1/organizations/usage_report/messages?bucket_width=1m&group_by[]=model` gives billed **token** sums per minute and no request count (blind spot 3) — so served volume has to be derived from tokens against a median baseline, and the residual against your client's attempt counter is 5xx/529 loss. Use a median rather than a mean: a mean absorbs the very outage it is hunting. Report contiguous runs of minutes, not scattered ones. Group by `service_tier` to see whether any traffic reached `priority`. Workspace/project key: every response, including errors, carries a `request-id` header (mirrored as `request_id` in error bodies) — those are the ids to quote to support.
- **repair**: Print: the minutes with the largest attempted-vs-billed gap, the clustering pattern, and the recommendation to treat 529 alongside 429 and 5xx in one retryable class with exponential backoff and jitter (or to use the SDK's built-in retry rather than a hand-rolled `except`). Include the captured `request-id` values. Do not retry anything.
- **category**: Errors and reliability
- **sources**: https://platform.claude.com/docs/en/api/errors · https://platform.claude.com/docs/en/api/service-tiers · https://platform.claude.com/docs/en/manage-claude/usage-cost-api

## api-error-500-not-retried

- **slug**: `api-error-500-not-retried`
- **title**: 500 api_error is treated as a permanent client failure
- **symptom**: `500` with `"error": {"type": "api_error"}` — "An unexpected error has occurred internal to Anthropic's systems" — surfacing to users as a hard failure, with no `request-id` captured to give support.
- **mechanism**: 500 is retryable ("Retry the request with exponential backoff; if the error persists, contact support with the request ID"), but a client that catches one broad class — `except APIStatusError` in Python, `catch (AnthropicServiceException)` in Java, `rescue APIError` in Ruby — flattens retryable (429, ≥500, network) and non-retryable (400, 404) into the same branch, and a client configured with `max_retries=0` disables the SDK's default two retries entirely. Also note a mid-stream failure after a 200 does **not** follow this path: SSE error events have their own shape.
- **detect**: Workspace/project API key: any read-only call (`GET /v1/models`) returns a `request-id` header — verify your logging pipeline actually captures it (Python/TypeScript expose `_request_id`; C#, Go, Java and PHP via raw-response accessors; Ruby via middleware). Admin API key: `GET /v1/organizations/usage_report/messages?bucket_width=1m` gives billed requests; the shortfall against your attempt counter, minus the 529 clusters, is 500-class loss. Check whether the client's configured `max_retries` is non-zero.
- **repair**: Print: observed 500 volume (as attempted-minus-billed), whether `request-id` is captured, the client's `max_retries` setting, and a recommended most-specific-first exception chain (`NotFoundError` → `RateLimitError` → `APIStatusError` → `APIConnectionError`, or `errors.As` + `switch apierr.StatusCode` in Go). Do not change the handler.
- **category**: Errors and reliability
- **sources**: https://platform.claude.com/docs/en/api/errors · https://platform.claude.com/docs/en/manage-claude/usage-cost-api

## non-streaming-request-over-ten-minutes

- **slug**: `non-streaming-request-over-ten-minutes`
- **title**: A non-streaming request over 10 minutes times out (504)
- **symptom**: `504` with `"error": {"type": "timeout_error"}` ("The request timed out while processing"), or — worse — no response at all, because an intermediate network dropped the idle connection before Anthropic answered.
- **mechanism**: "Consider using the streaming Messages API or Message Batches API for long-running requests, especially those over 10 minutes." The SDKs validate that non-streaming Messages requests are not expected to exceed a 10-minute timeout and refuse the combination; a raw HTTP client has no such guard. Default client timeout is 10 minutes (units differ per SDK — Python/Ruby seconds, TypeScript **milliseconds**, Go `time.Duration`, Java `Duration`, C# `TimeSpan`). Large `max_tokens` is the usual trigger: Opus 5 / Sonnet 5 / Fable 5 / Opus 4.6–4.8 / Sonnet 4.6 allow up to **128,000** output tokens, and 128K tokens cannot be generated inside 10 minutes on a single non-streaming call.
- **detect**: Workspace/project API key: `GET /v1/models/{model_id}` returns `max_tokens` — the per-model ceiling for the parameter — and `max_input_tokens`. Flag any non-streaming call path whose configured `max_tokens` is a large fraction of that ceiling (rule of thumb: anything above ~16,000 on a non-streaming path). Size the prompt side read-only with `POST /v1/messages/count_tokens` (free) to estimate turn length. Admin API key: `GET /v1/organizations/usage_report/messages?bucket_width=1h` — a workload whose mean output tokens per request is very high is the one at risk.
- **repair**: Print: each call path's `max_tokens`, the model's `max_tokens` cap from the Models API, and whether the path streams. Recommend `.stream()` + `.get_final_message()` / `.finalMessage()` (identical `Message` object, no event handling required) for anything long, the Message Batches API for anything latency-tolerant, and TCP keep-alive for direct HTTP integrations. Do not change the call.
- **category**: Errors and reliability
- **sources**: https://platform.claude.com/docs/en/api/errors · https://platform.claude.com/docs/en/api/models · https://platform.claude.com/docs/en/models/overview

## request-too-large-413

- **slug**: `request-too-large-413`
- **title**: A 32 MB request is rejected by Cloudflare with 413
- **symptom**: `413` with `"error": {"type": "request_too_large"}` — "Request exceeds the maximum allowed number of bytes." On the direct Claude API this is returned by Cloudflare *before* the request reaches Anthropic's servers, so it never appears in usage data and the error body can look unlike the usual JSON envelope.
- **mechanism**: Per-endpoint ceilings: **Messages API 32 MB**, **Token Counting API 32 MB**, **Batch API 256 MB**, **Files API 500 MB**. Base64 inflates payloads by ~33%, so a 24 MB PDF blows the 32 MB Messages limit. A separate content ceiling applies independently: a single request can include up to **600 images or PDF pages** (100 on 200k-context models), and you can hit the byte limit long before the token limit.
- **detect**: Workspace/project API key: `POST /v1/messages/count_tokens` shares the same **32 MB** ceiling and is free, so posting the identical payload there returns 413 on exactly the bodies the Messages API would reject — a zero-cost pre-flight. If it returns `{"input_tokens": N}` instead, the body is under the byte limit and you also learn the token size. For batch submissions, sum the serialized `params` blocks against 256 MB and the 100,000-request-per-batch cap. `GET /v1/models/{id}` gives `max_input_tokens` for the separate token ceiling.
- **repair**: Print: the endpoint, the measured payload size, the applicable ceiling, and whether the fix is the Files API (500 MB, upload once and reference by `file_id`) or splitting the request. Note that an inline base64 string must have no newlines. Do not upload or split anything.
- **category**: Errors and reliability
- **sources**: https://platform.claude.com/docs/en/api/errors · https://platform.claude.com/docs/en/build-with-claude/token-counting · https://platform.claude.com/docs/en/build-with-claude/context-windows

## max-tokens-above-model-cap

- **slug**: `max-tokens-above-model-cap`
- **title**: max_tokens is set above the model's own output cap
- **symptom**: `400 invalid_request_error` naming the maximum `max_tokens` value for that model. Typically appears the moment a config is reused across models — the value that was legal on Opus 5 is illegal on Haiku 4.5.
- **mechanism**: "Different models have different maximum values for this parameter." Synchronous Messages API caps: **128K** output tokens on Claude Fable 5, Opus 5, Sonnet 5, Opus 4.8, Opus 4.7, Opus 4.6 and Sonnet 4.6; **64K** on Claude Haiku 4.5. On the **Message Batches API** those same 1M-context models support up to **300K** output tokens with the `output-300k-2026-03-24` beta header — so the legal ceiling depends on the endpoint as well as the model. Minimum inside a batch is `max_tokens >= 1`.
- **detect**: Workspace/project API key: `GET /v1/models/{model_id}` returns `max_tokens`, documented as "Maximum value for the `max_tokens` parameter when using this model" (and `max_input_tokens` for the context window). Loop it over every model id in config and compare each configured `max_tokens`. The Models API is the single source of truth — do not infer the cap from the docs table, which lags.
- **repair**: Print: per model id, the configured `max_tokens`, the API-reported cap, and the delta. Flag any shared config that spans model tiers. Note the 300K batch path requires `output-300k-2026-03-24` and is Batch-only. Do not edit config.
- **category**: Errors and reliability
- **sources**: https://platform.claude.com/docs/en/api/models · https://platform.claude.com/docs/en/models/overview · https://platform.claude.com/docs/en/build-with-claude/batch-processing

## stop-reason-max-tokens-truncation

- **slug**: `stop-reason-max-tokens-truncation`
- **title**: Answers are silently truncated by stop_reason max_tokens
- **symptom**: HTTP **200** with `stop_reason: "max_tokens"`. Nothing raises. JSON comes back unparseable, prose stops mid-sentence, and — the expensive case — the final content block is an incomplete `tool_use` whose `input` cannot be executed, which in an agentic loop poisons every later turn.
- **mechanism**: `max_tokens` is a hard ceiling the model is not aware of (unlike a `task_budget`, which is advisory and lets the model pace itself). Thinking tokens are a subset of `max_tokens` and are billed as output, so adaptive thinking at high effort eats the budget before the visible answer starts. Lowballing `max_tokens` — a classification-sized 256 or 1024 inherited from an old snippet — is the usual cause. Note in streaming, `stop_reason` is `null` in `message_start` and only arrives in `message_delta`.
- **detect**: The Message Batches results file is a complete read-only corpus of finished responses: stream `GET /v1/messages/batches/{batch_id}/results` (JSONL, one object per line) and count lines where `.result.message.stop_reason == "max_tokens"`, keyed by `.custom_id`. In the same stream compare `.result.message.usage.output_tokens` against the `max_tokens` you submitted and against `GET /v1/models/{id}.max_tokens`. Admin API key: `GET /v1/organizations/usage_report/messages?group_by[]=model` — output-token totals pinned to a round per-request ceiling is a second signal. Results arrive in any order; always key by `custom_id`, never by position.
- **repair**: Print: the truncation rate per `custom_id` prefix / model, the configured `max_tokens`, the model's cap, and the recommended default (~16,000 non-streaming, ~64,000 streaming; ~256 only for genuine classification). Flag any response whose last block is a `tool_use`. Recommend checking `stop_reason` before reading `content` on every call. Do not re-run the requests.
- **category**: Errors and reliability
- **sources**: https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons · https://platform.claude.com/docs/en/build-with-claude/batch-processing · https://platform.claude.com/docs/en/api/models

## prompt-too-long-context-overflow

- **slug**: `prompt-too-long-context-overflow`
- **title**: Prompts overflow the window and 400 with prompt too long
- **symptom**: `400 invalid_request_error` with the message `prompt is too long` when the input alone exceeds the context window — on **every** model. Or, on Claude 4.5 and newer, HTTP 200 with `stop_reason: "model_context_window_exceeded"`, which is a truncated-but-valid response that a client checking only `end_turn` will happily treat as complete.
- **mechanism**: Everything counts toward the window: system prompt, every message including tool results, images and documents, the `tools` definitions themselves, and the output the model generates including its thinking. With prompt caching, `input_tokens` + `cache_read_input_tokens` + `cache_creation_input_tokens` all count — caching changes what you pay for those tokens, not whether they occupy the window. On Claude 4.5+ a request whose input **plus** `max_tokens` exceeds the window is accepted and stops with `model_context_window_exceeded` rather than erroring; on earlier models that combination is a validation error unless you send `model-context-window-exceeded-2025-08-26`.
- **detect**: Workspace/project API key: `POST /v1/messages/count_tokens` with the real payload (accepts the same body as Messages — `system`, `tools`, images, PDFs, thinking blocks — and returns `{"input_tokens": N}`) compared against `GET /v1/models/{model_id}.max_input_tokens`. Note the count is an estimate and may include unbilled system-added tokens. Scan batch results (`GET /v1/messages/batches/{id}/results`) for `.result.message.stop_reason == "model_context_window_exceeded"` and for `.result.error` bodies containing `prompt is too long`.
- **repair**: Print: the counted input tokens, the model's `max_input_tokens`, the overflow margin, and which component dominates (tool definitions, history, documents). Recommend server-side compaction (`compact-2026-01-12`) for long conversations, context editing (`clear_tool_uses_20250919` / `clear_thinking_20251015`) for agentic loops, or the tool search tool to defer tool definitions. Note that previous-turn thinking blocks are kept on Opus 4.5+/Sonnet 4.6+ and stripped on earlier models. Do not truncate content.
- **category**: Errors and reliability
- **sources**: https://platform.claude.com/docs/en/build-with-claude/context-windows · https://platform.claude.com/docs/en/build-with-claude/token-counting · https://platform.claude.com/docs/en/build-with-claude/handling-stop-reasons

## token-counting-endpoint-unused

- **slug**: `token-counting-endpoint-unused`
- **title**: Nothing calls count_tokens, so overflow is a surprise
- **symptom**: `400 invalid_request_error` / `prompt is too long` and `413 request_too_large` occurring in production with no pre-flight estimate anywhere in the code path, and cost forecasts built on a character-count heuristic or on `tiktoken` (which is a different tokenizer entirely).
- **mechanism**: `POST /v1/messages/count_tokens` is **free**, accepts the same structured body as `POST /v1/messages` (system prompts, tools, images, PDFs, thinking blocks), and returns `{"input_tokens": N}`. It carries its **own** rate limit, entirely independent of message creation: Start **2,000 RPM**, Build **4,000 RPM**, Scale **8,000 RPM** — "usage of one does not count against the limits of the other." It does not use caching logic (a `cache_control` block is accepted but no caching occurs), and server-tool token counts apply only to the first sampling call.
- **detect**: Admin API key: the token-counting limiter is its own rate limit group — `GET /v1/organizations/rate_limits?group_type=token_count` confirms it exists and its configured value. Then compare against `GET /v1/organizations/usage_report/messages` for the `model_group` traffic: heavy Messages usage with no corresponding token-count activity means the endpoint is never called. Workspace/project key: call `POST /v1/messages/count_tokens` yourself on a representative payload — it costs nothing, changes nothing, and gives you the number the pipeline should have been checking.
- **repair**: Print: the counted `input_tokens` for representative payloads vs `GET /v1/models/{id}.max_input_tokens`, the free-tier RPM available on the counting endpoint, and the recommendation to add a pre-flight count on any path that assembles variable-length context (RAG, agent loops, document ingestion). Explicitly flag any use of `tiktoken` or a chars/4 heuristic. Do not add the call.
- **category**: Errors and reliability
- **sources**: https://platform.claude.com/docs/en/build-with-claude/token-counting · https://platform.claude.com/docs/en/manage-claude/rate-limits-api · https://platform.claude.com/docs/en/build-with-claude/context-windows

