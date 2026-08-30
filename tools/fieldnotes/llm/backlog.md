# /llm/ backlog — the honest work list

`research.md` enumerates **162** problem slugs. **24** are published under `/llm/`. The
remaining **138** were assembled in several passes and carry duplicates, near-duplicates of
published notes, and entries no read-only script can actually detect.

Swept against two rules: the section's premise (every note must be a problem a **read-only
script can detect through the provider's own API** — dashboard-only faults do not qualify) and
the dedup rule (**two notes that read the same surface and reach the same conclusion are one
note**, however differently they are named).

| | count |
| --- | --- |
| Enumerated in `research.md` | 162 |
| Already published | 24 |
| Backlog swept | 138 |
| **KEEP** — a distinct note | **73** |
| **MERGE** — covered by a published note or another backlog slug | **62** |
| **DROP** — no API-detectable signal, or dashboard-only | **3** |

73 is 18 batches: seventeen of four and one of five. The sweep originally merged the whole
"results never fetched" family into the published `batch-error-file-never-read`; that note reads
`error_file_id` only, so `batch-output-file-never-downloaded` was reinstated on review. Same
mechanism, different finding. Batches are ordered so related material ships together: money and
capacity first, then limits and errors, then the async and structured-output surfaces, then
caching, then the governance and storage sweeps.

---

## The batches

### Batch 1 — Money the token dashboard cannot see
Four dimensions of an Anthropic bill that are not priced per token, each a different field in
the same two reports.

| slug | what makes it distinct |
| --- | --- |
| `web-search-spend-unnoticed` | Sums `server_tool_use.web_search_requests` per key in the messages usage report; the only note that prices a per-search tool fee rather than tokens. |
| `code-execution-hours-exceed-free-allowance` | Reads `cost_type == "code_execution"` on the cost report — a line the messages report excludes entirely — and concludes the free 1,550 container hours are spent. |
| `us-inference-geo-premium-unnoticed` | Groups usage by `inference_geo` and reads each workspace's `data_residency` block; the only note about a geography multiplier on the base rate. |
| `long-context-requests-unwatched` | Groups by `context_window` and measures the `200k-1M` share of uncached input. Corrected while writing: this band is a **size** alarm, not a price band — current models bill it at standard rates, and the note says so. |

### Batch 2 — Which limiter is actually binding
Headroom, and the three token limiters that exhaust independently.

| slug | what makes it distinct |
| --- | --- |
| `rate-limit-headers-near-exhaustion` | Reads the `x-ratelimit-*` triples off one live `GET /v1/models` and reports headroom as a ratio; the only read-only view of OpenAI quota, since past 429s are unreadable. |
| `rate-limit-429-limiter-unidentified` | Reads Anthropic's three `anthropic-ratelimit-*` triples plus the aggregate "most restrictive" one against `GET /v1/organizations/rate_limits`; names which bucket emptied. |
| `itpm-exhausted-uncached-input` | Per-minute usage buckets against `input_tokens_per_minute`; concludes the input limiter, not the invoice, is the thing caching would fix. |
| `otpm-exhausted` | The same per-minute buckets against `output_tokens_per_minute`; concludes RPM was never the ceiling and more concurrency will not help. |

### Batch 3 — Ceilings nobody in the room set
Limits imposed by container config, ramp rate, backoff and tier availability.

| slug | what makes it distinct |
| --- | --- |
| `project-rate-limit-below-org` | The per-project and per-workspace rate-limit endpoints, where each limiter carries both its override and `org_limit`; reports the throttling override and the missing limiter alike. |
| `acceleration-limit-on-traffic-spike` | Adjacent one-minute buckets well under the configured limit while 429s still fire: the ramp rate is the limit, not the headline number. |
| `retry-after-header-ignored` | A read-only probe loop that proves `retry-after` reaches your client at all and is not stripped in transit by a proxy. |
| `flex-resource-unavailable-timeouts` | Flex line items plus hourly request shortfalls; the only note on a tier that fails by not being served rather than by erroring. |

### Batch 4 — Four ceilings you can pre-flight
`count_tokens` and the model object are the only limits either API will state before you spend.

| slug | what makes it distinct |
| --- | --- |
| `prompt-too-long-context-overflow` | `POST /v1/messages/count_tokens` against `GET /v1/models/{id}.max_input_tokens`, plus batch results carrying `model_context_window_exceeded`. |
| `request-too-large-413` | `count_tokens` as a free pre-flight for the 32 MB *byte* ceiling; the only note that measures bytes rather than tokens. |
| `max-tokens-above-model-cap` | Configured `max_tokens` against the model object's own `max_tokens` field, which is the source of truth the docs table lags. |
| `non-streaming-request-over-ten-minutes` | A large `max_tokens` on a non-streaming path against the 10-minute wall clock; the fix is streaming, not a smaller prompt. |

### Batch 5 — Holes in the aggregate
Neither API lists requests. All four findings are shapes in the usage buckets.

| slug | what makes it distinct |
| --- | --- |
| `reasoning-model-rejects-max-tokens` | Buckets with `num_model_requests > 0` and `output_tokens == 0`: every call 400s before generation on a parameter a reasoning model refuses. |
| `requests-diverge-from-token-volume` | Tokens-per-request collapsing while request count climbs — the retry-storm signature, and nothing else produces it. |
| `overloaded-529-clusters` | Billed requests per minute subtracted from your own attempt counter; the residual is 5xx and 529 loss, clustered in specific minutes. |
| `live-project-zero-usage-buckets` | A project with traffic in the first half of the window and none in the last 48 hours: a deploy or a credential died. |

### Batch 6 — Rejected before a token is generated
Four faults provable with a probe of `GET /v1/models` and nothing else.

| slug | what makes it distinct |
| --- | --- |
| `anthropic-version-header-missing-or-ancient` | A three-way probe — no version header, current, ancient — that also tests whether a gateway injects or strips it. |
| `invalid-beta-header-value` | Loops every `anthropic-beta` string in the tree through `GET /v1/models` for 400-vs-200, then diffs response shapes to catch the ones that went GA. |
| `org-verification-required` | Model visible on `GET /v1/models/{id}` while the streaming key's buckets show requests with zero output tokens: verification, not access. |
| `unsupported-country-region` | The same call issued from the production egress path; 403 `unsupported_country_region_territory` against a known-good host isolates geography from credentials. |

### Batch 7 — Surfaces closing, not models retiring
Endpoint sunsets need an export or a rewrite, not a model-id swap.

| slug | what makes it distinct |
| --- | --- |
| `assistants-api-already-shut-down` | `GET /v1/assistants` 200-vs-404 tells you whether the org still has grace access on an API that is already past its date. |
| `sora-videos-api-no-replacement` | `GET /v1/videos` plus video line items still accruing: the only closure in the set with no successor to migrate to. |
| `prompts-evals-agentbuilder-sunset` | `GET /v1/prompts` and `GET /v1/evals` enumerate content that must be exported before the date, not code that must be changed. |
| `fine-tuning-jobs-blocked` | The job list plus the base models' `shutdown_date`: existing fine-tunes keep serving while new jobs stop being accepted. |

### Batch 8 — What a migration quietly breaks
Four assumptions that stop holding the day the model or the stored object underneath changes.

| slug | what makes it distinct |
| --- | --- |
| `token-counts-reused-across-tokenizers` | `count_tokens` called twice on a byte-identical body under two model ids; the delta is the estimate your budget is wrong by. |
| `seed-determinism-unreliable` | `system_fingerprint` on a canary response diffed against a stored baseline; the only note about reproducibility rather than cost or failure. |
| `previous-response-id-chain-broken` | Probing recorded `previous_response_id` values for non-200s: server-side conversation state aged out and the chain 404s. |
| `fine-tune-job-failed-with-error-code` | `status == "failed"` with `error.code`/`error.param` and the job events feed, including files stuck in `validating_files`. |

### Batch 9 — Asynchronous jobs that end without raising
Five terminal states of a batch or background job that no exception announces. This is the one
batch of five: the output-file note was reinstated after review (see the MERGE table).

| slug | what makes it distinct |
| --- | --- |
| `batch-failed-input-validation` | `status == "failed"` with `errors.data[].line` naming the offending row — including the wrong-`purpose` input file. |
| `batch-cancelled-partial-results` | A cancelled batch with `completed`/`succeeded > 0`: billed work whose output is still salvageable, plus cancels stuck mid-flight. |
| `background-response-never-polled` | The Responses API background mode, not batches: ids stuck `queued`/`in_progress` past your SLA, or 404ing outright. |
| `batch-output-file-never-downloaded` | The mirror of the published `batch-error-file-never-read`: a **succeeded** batch whose `output_file_id` expired unfetched. Same ledger join, opposite finding — not failures nobody read, but work you paid for and never collected. Absorbs `batch-created-never-polled`, `batch-results-never-fetched` and `batches-created-but-never-polled` as states within it. |
| `batch-queue-limit-reached` | Live queue depth summed across non-terminal batches against the org's `enqueued_batch_requests` ceiling; submissions are being refused, not failing. |

### Batch 10 — Structured output that returns 200
Four reads of a stored Response object, four ways a JSON contract breaks with no error.

| slug | what makes it distinct |
| --- | --- |
| `structured-output-truncated-by-length` | `status == "incomplete"` with `incomplete_details.reason == "max_output_tokens"`, and `stop_reason == "max_tokens"` in batch results: the answer was cut, not refused. |
| `refusal-field-ignored` | `output[].content[].type == "refusal"` and the `content_filter` incomplete reason: the model declined and the field was never read. |
| `strict-false-schema-silently-ignored` | The echoed `text.format` with `strict` absent or false, or legacy `json_object` mode: the schema was only ever advisory. |
| `tool-call-arguments-unparseable` | Parsing every `function_call.arguments` string and validating it against the declared schema; the dispatcher throws, not the API. |

### Batch 11 — What you attach to every request
Tools and prefixes are paid for on every call whether or not they earn it.

| slug | what makes it distinct |
| --- | --- |
| `tool-defined-but-never-called` | The set of declared tool names minus the set that ever appears as a `function_call` across a large sample of stored responses. |
| `tool-schemas-dominate-input-tokens` | `count_tokens` with and without `tools` on the same body: the difference is the per-call schema overhead in tokens. |
| `parallel-tool-calls-with-strict-schema` | More than one `function_call` in one turn while `strict: true` is declared — a documented interaction that voids the guarantee. |
| `cache-invalidated-by-changing-prefix` | Cache writes on more than half of input with reads near zero, sustained: the prefix (or an option like `reasoning.effort`) changes every call. |

### Batch 12 — Why the cached share is zero
Four different causes behind one number, each with a different repair.

| slug | what makes it distinct |
| --- | --- |
| `prompt-below-model-cache-minimum` | Mean input per request under the model's cache minimum with zero writes *and* zero reads: structurally ineligible, not unlucky. |
| `prompt-cache-key-not-set` | A cached share that *degrades at peak hours* — load-correlated, which is routing scatter across servers, not prefix instability. |
| `prompt-cache-retention-left-at-default` | Zero cached share in the buckets that follow gaps in traffic: eviction between runs, not misconfiguration. |
| `cache-hit-rate-collapsed-after-model-change` | A step change in cache-read share aligned with the day a new `model` value first appears. |

### Batch 13 — Anthropic capabilities you pay for and do not get
Four checks that a provisioned capability is actually reaching production.

| slug | what makes it distinct |
| --- | --- |
| `priority-tier-model-unsupported` | `group_by[]=service_tier`: a model that never reports `priority` has no coverage — and Priority costs are absent from the cost report entirely. |
| `long-context-gated-on-obsolete-beta` | `max_input_tokens` per model id against the ceiling the application enforces; the 1M window is bought and capped at 200k in code. |
| `claude-code-sessions-not-hitting-cache` | The Claude Code usage report per actor: `num_sessions >= 2` with `tokens.cache_read == 0`. |
| `claude-code-edit-rejection-rate-high` | The same report's `tool_actions` acceptance rates: output that is billed, generated and then thrown away. |

### Batch 14 — Keys that outlive their purpose
The key roster, read four ways.

| slug | what makes it distinct |
| --- | --- |
| `api-key-never-used` | `last_used_at` null or older than 90 days on an enabled key — with `owner_project_access=any` so the audit is not silently filtered. |
| `legacy-user-owned-keys-in-project` | `owner.type == "user"` joined to cost by `api_key_id`: production money moving on a personal credential. |
| `service-account-key-never-rotated` | Max key `created_at` per service account past 180 days, confirmed by the absence of rotation events in the audit log. |
| `unreviewed-key-lifecycle-in-audit-log` | The audit log / compliance activity feed itself: key and member lifecycle events, with actors resolved against the current roster. |

### Batch 15 — Org topology and who can spend
The shape of the organization, not the credentials inside it.

| slug | what makes it distinct |
| --- | --- |
| `no-prod-dev-project-separation` | A single active project or workspace, or one holding over 95% of cost: there is no boundary to attribute or cap spend against. |
| `default-workspace-cost-unattributable` | Cost rows whose `workspace_id` is null, traced to organization-scoped keys via `scope.type` on the key list. |
| `too-many-organization-owners` | The role distribution across org members and workspace members, excluding service accounts. |
| `openai-invites-pending-past-expiry` | The invite list: `pending` records past `expires_at`, and the roles those lapsed invites carried. |

### Batch 16 — Controls everyone assumes are on
Four safety and compliance settings the API says are not configured.

| slug | what makes it distinct |
| --- | --- |
| `moderation-never-called` | The moderations usage endpoint: zero requests on a public product, or requests still attributed to a retired `text-moderation-*` id. |
| `zero-data-retention-not-configured` | The org and per-project `data_retention` objects, whose `type` values disagree more often than anyone expects. |
| `project-model-permissions-unrestricted` | `model_permissions` per project: no policy, an empty deny list, or frontier models allowed in a project that should not reach them. |
| `external-key-config-unattached` | `attachment.type == "unattached"` on a CMEK external key config, or a `geo` that contradicts the residency commitment. |

### Batch 17 — Vector stores that are not what you think
Four states of a retrieval index that all return a 200 to `file_search`.

| slug | what makes it distinct |
| --- | --- |
| `vector-store-file-attach-failed` | Per-file `last_error.code` under `filter=failed`, reconciled with the store's own `file_counts`, plus files still `in_progress` long after ingestion ended. |
| `empty-vector-store-still-referenced` | `file_counts.total == 0` or `usage_bytes == 0` on a store the application still names in `vector_store_ids`. |
| `vector-store-expired-or-expiring` | `expires_after` on a store treated as permanent, and stores already `expired`: the index deletes itself on a schedule. |
| `vector-store-storage-cost-creeping` | `usage_bytes` trended across 90 days of the vector-stores usage endpoint against retrieval volume: hourly billing on bytes nobody queries. |

### Batch 18 — Storage that accumulates and storage that vanishes
Server-side objects nobody owns after upload.

| slug | what makes it distinct |
| --- | --- |
| `files-accumulating-against-storage-quota` | Summed `bytes`/`size_bytes` across every page against the project and org quotas, with per-file size outliers flagged. |
| `orphaned-assistants-purpose-files` | `purpose=assistants` files not referenced by any vector store — a whole purpose class orphaned by the Assistants shutdown. |
| `expired-files-still-referenced` | `expires_at` already past on ids the application still holds; the API silently omits ids that are already gone. |
| `stored-responses-accumulating` | `store: true` retention on responses and conversations, probed by id because neither resource has a list endpoint. |

---

## MERGE — 62 slugs

Listed in `research.md` order. "(published)" marks a survivor already live under `/llm/`.

| slug | survivor | why they are the same problem |
| --- | --- | --- |
| `spend-spiking-week-over-week` | `spend-spike-week-over-week` (published) | Same weekly fold of the cost report; this is the Anthropic half of a note that already covers both providers. |
| `cost-concentrated-in-one-key-or-workspace` | `one-model-or-project-dominates-cost` (published) | Rank cost rows by share of total; `workspace_id` is a third group-by on the same call. |
| `opus-tier-model-for-cheap-work` | `frontier-model-on-trivial-workload` (published) | Output-per-request ratio on an expensive model — the same test, worded for Anthropic. |
| `priority-tier-spend-missing-from-cost-report` | `priority-tier-model-unsupported` | One `group_by[]=service_tier` read answers both halves: whether Priority served you, and whether the cost report can see it. |
| `fast-mode-premium-spend-hidden` | `fast-mode-silently-downgraded` (published) | The published note already reads the configured tier against the invoice in both directions. |
| `rate-limit-exceeded-429` | `rate-limit-headers-near-exhaustion` | Same headers off the same probe call; "already 429ing" and "about to" are one measurement. |
| `spend-cap-429-retried-forever` | `quota-exhausted-not-rate-limited` (published) | A spend-cap 429 with no `retry-after` is exactly the billing wall the published note branches on. |
| `workspace-rate-limit-override-throttles` | `project-rate-limit-below-org` | Same container rate-limit endpoint; the Anthropic object states `org_limit` outright, which is the OpenAI note's cross-project comparison. |
| `shutdown-date-approaching` | `model-retiring-within-90-days` (published) | Identical: `shutdown_date` under 90 days, ordered by traffic. |
| `legacy-completions-endpoint-sunset` | `model-retiring-within-90-days` (published) | A hardcoded id list against the same `shutdown_date` field. |
| `legacy-gpt-snapshots-october-2026` | `model-retiring-within-90-days` (published) | Same field, different regex. |
| `o-series-reasoning-models-retiring` | `model-retiring-within-90-days` (published) | Same field, different regex. |
| `gpt5-snapshots-shutdown-december` | `model-retiring-within-90-days` (published) | Same field, different regex. |
| `floating-alias-snapshot-drift` | `floating-alias-instead-of-pinned-snapshot` (published) | An alias resolving to a moving snapshot; the published note reads the resolution directly instead of diffing a baseline. |
| `dalle-models-removed` | `retired-model-id-still-in-code` (published) | A removed id has no date left to read: absence from `GET /v1/models` is the whole finding. |
| `gpt-image-generation-churn` | `model-retiring-within-90-days` (published) | `shutdown_date` on an id filter, sized by the images usage endpoint. |
| `audio-realtime-models-deprecated` | `model-retiring-within-90-days` (published) | `shutdown_date` on an id filter, sized by the audio usage endpoints. |
| `text-moderation-model-retired` | `moderation-never-called` | Both read the moderations usage endpoint grouped by model; zero requests and requests against a dead id are two branches of one script. |
| `legacy-embeddings-and-endpoints-dead` | `retired-model-id-still-in-code` (published) | Ids absent from the model list; adds only a 2024 id list. |
| `model-not-available-to-this-org` | `retired-model-id-still-in-code` (published) | The published note *is* the config-strings-vs-`GET /v1/models` diff; "retired" and "never entitled to you" produce the same 404 and the same repair. |
| `batch-enqueued-token-limit-exceeded` | `batch-queue-limit-reached` | Queue occupancy against the enqueued ceiling; the Anthropic endpoint states the limit the OpenAI note has to estimate. |
| `batch-input-file-wrong-purpose` | `batch-failed-input-validation` | A wrong-purpose input file surfaces as exactly the validation failure the survivor already enumerates. |
| `batch-created-never-polled` | `batch-output-file-never-downloaded` (kept) | "Created and never polled" is a state inside the unclaimed-output check, not its own note. |
| `batch-requests-expired-after-24h` | `batch-expired-past-24h-window` (published) | The Anthropic twin: `expired > 0` against a fixed 24-hour window. |
| `batch-errored-requests-unread` | `batch-partial-failure-unnoticed` (published) | `request_counts.errored > 0` is the Anthropic spelling of `request_counts.failed > 0` on a batch that reads as finished. |
| `batch-results-never-fetched` | `batch-output-file-never-downloaded` (kept) | Results lapsing at 29 days is that note's headline finding. |
| `batch-canceled-mid-flight-anthropic` | `batch-cancelled-partial-results` | Same finding: a cancelled batch holding billed, salvageable output. |
| `batches-created-but-never-polled` | `batch-output-file-never-downloaded` (kept) | Ended, unarchived, unclaimed — the same ledger join, third naming. |
| `batch-tier-never-used` | `batch-discount-left-unused` (published) | The 50% discount going unused, found by looking for batch-shaped traffic on the synchronous path. |
| `single-api-key-generates-all-spend` | `one-model-or-project-dominates-cost` (published) | The same `GET /v1/organization/costs` call with `group_by=api_key_id` and the same share-of-total arithmetic. |
| `api-key-dormant-for-months` | `api-key-never-used` | Same endpoint, same `last_used_at` field, adjacent thresholds, identical repair. |
| `conversations-never-deleted` | `stored-responses-accumulating` | Neither resource has a list endpoint, so both are probed by ids you already hold and flagged against the same retention window; one script, two object types. |
| `active-api-keys-never-used` | `api-key-never-used` | The Anthropic spelling: active keys minus keys seen in the usage report. |
| `api-key-created-by-departed-member` | `key-owner-lost-project-access` (published) | Both are a live key whose human is gone; the published note reads the flag the provider sets when that happens. |
| `api-keys-not-scoped-to-a-workspace` | `default-workspace-cost-unattributable` | Organization-scoped keys are the cause of the null-`workspace_id` cost rows the survivor measures. |
| `archived-workspace-with-active-keys` | `archived-project-still-holds-keys` (published) | The Anthropic twin, including the `include_archived` parameter that makes the audit see them at all. |
| `no-dev-prod-workspace-separation` | `no-prod-dev-project-separation` | One container holding every environment; workspace and project are the same topology on two providers. |
| `anthropic-invites-pending-past-expiry` | `openai-invites-pending-past-expiry` | Same list, same `status`/`expires_at` test. |
| `too-many-org-admins` | `too-many-organization-owners` | Same roster, same role-share computation. |
| `workspace-has-no-spend-or-rate-guard` | `project-rate-limit-below-org` | Read from the same workspace rate-limit endpoint; a missing limiter and a throttling one are the two outcomes of one check (the spend half is Console-only). |
| `compliance-activity-feed-never-read` | `unreviewed-key-lifecycle-in-audit-log` | Both walk the provider's audit trail for key, member and role events and resolve actors against the roster. |
| `vector-store-file-counts-failed` | `vector-store-file-attach-failed` | The store's failure counter and the per-file `last_error` are two granularities of one finding. |
| `vector-store-stuck-in-progress` | `vector-store-file-attach-failed` | Same `/files` listing with a different status filter; both conclude documents you think are searchable are not in the index. |
| `files-storage-quota-climbing` | `files-accumulating-against-storage-quota` | Sum file bytes against the quota; only the quota number and the pagination style differ. |
| `orphaned-files-never-deleted` | `files-accumulating-against-storage-quota` | "`expires_at` null and older than retention" is already the survivor's flag. |
| `files-api-beta-header-shape-drift` | `invalid-beta-header-value` | The detection is the same with/without beta-header diff; the survivor runs it over every beta string the code sends. |
| `prompt-cache-share-near-zero` | `prompt-caching-never-used` (published) | Cached share at zero across the org — the OpenAI wording of the published finding. |
| `one-hour-cache-ttl-not-earning-back` | `cache-writes-with-no-reads` (published) | The published note computes the break-even from the same 1.25x/2x/0.1x multipliers, 1h case included. |
| `cache-read-share-below-breakeven` | `cache-writes-with-no-reads` (published) | This *is* the published note's arithmetic, priced from the cost report instead of the token report. |
| `openai-prompt-below-cache-minimum` | `prompt-below-model-cache-minimum` | Mean input per request under the model's cache minimum; one provider each. |
| `cache-invalidated-by-request-option-churn` | `cache-invalidated-by-changing-prefix` | Prompt text and request options invalidate the same prefix the same way, and both show as writes-every-call with no reads. |
| `reasoning-model-rejects-temperature` | `reasoning-model-rejects-max-tokens` | Identical signature — requests billed, zero output tokens — and one repair: stop sending the parameters reasoning models refuse. |
| `context-length-exceeded` | `prompt-too-long-context-overflow` | Input overflowing the window; the survivor measures it exactly with `count_tokens` instead of inferring it from per-request means. |
| `silent-output-truncation` | `structured-output-truncated-by-length` | A round-number mean output is a weak proxy for the `incomplete_details.reason` the survivor reads directly. |
| `service-tier-not-allowed` | `fast-mode-silently-downgraded` (published) | The published note already reads the project's tier setting against what the app sends and what the invoice shows, in both directions. |
| `server-errors-not-retried` | `overloaded-529-clusters` | Both size 5xx loss as the gap between attempted and billed requests; 500, 503 and 529 differ only in which retry policy you print. |
| `fine-tune-training-file-validation-errors` | `fine-tune-job-failed-with-error-code` | `error.param == "training_file"` is one branch of the survivor's `error.code` report on the same job list. |
| `audio-transcription-25mb-limit` | `files-accumulating-against-storage-quota` | The only read-only signal is a size scan of `/v1/files`, which the survivor already performs. |
| `stale-beta-header-after-graduation` | `invalid-beta-header-value` | One loop over every beta string the code sends reports both the 400s and the accepted-but-obsolete ones. |
| `api-error-500-not-retried` | `overloaded-529-clusters` | Same attempted-minus-billed residual; capturing `request-id` is a line in the survivor, not a note. |
| `stop-reason-max-tokens-truncation` | `structured-output-truncated-by-length` | Answers cut at the output cap; the batch results file is a second corpus for the same conclusion. |
| `token-counting-endpoint-unused` | `prompt-too-long-context-overflow` | "Nothing calls `count_tokens`" is the survivor's repair, and the rate-limit group it proposes reading reports a configured limit, not usage. |

## DROP — 3 slugs

| slug | why it cannot carry a note |
| --- | --- |
| `self-set-spend-limit-400` | The limit lives in Console and no Admin endpoint returns it, so the script has nothing to compare month-to-date spend against; the only positive signal is the text of a 400 body a read-only script cannot provoke. |
| `usage-tier-too-low` | No endpoint reports the organization's usage tier. Every signal it proposes — models missing from `GET /v1/models`, rate-limit headers, cumulative spend — is another note's read, and the repair (prepay, or wait) is not something a script finds. |
| `realtime-session-60-minute-cap` | Hourly usage buckets cannot resolve a session boundary inside the hour, so the "sawtooth" is not observable. The cap is documented server behaviour, not readable state. |
