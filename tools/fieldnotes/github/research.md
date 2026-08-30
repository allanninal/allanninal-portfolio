# GitHub API integration failures a read-only script can detect

Research file for the `github` field-notes section. Scope is the **GitHub API as an
integration surface** — REST and GraphQL, auth, rate limits, pagination, webhooks,
Apps, permissions, org policy. Workflow-authoring and Actions-runner problems are out
of scope; they are covered by the published `ci` section at allanninal.dev/ci.

Every entry below passes the hard filter: **a script holding a read-only token can see
it through the API.** Where the root cause lives in application code, the entry
describes the API-visible *symptom* instead and says so.

**Total problems: 101**

**By category:**

- Rate limits — 13
- Authentication and tokens — 14
- GitHub Apps — 13
- Webhooks — 14
- Pagination and queries — 12
- GraphQL — 11
- Permissions and access — 12
- Organization and SSO — 12

---

## Scope and known blind spots

These are the things the API genuinely cannot tell a read-only observer. The section
should say so plainly rather than pretend otherwise.

1. **Client-side code is invisible.** The API cannot see whether your client follows
   the `Link` header, honours `retry-after`, sends `If-None-Match`, verifies
   `X-Hub-Signature-256`, or retries with backoff. All pagination, conditional-request
   and signature-verification entries below are detected by *proxy*: the state of the
   resource (a hook with no secret configured, a `Link` header that exists and has a
   `rel="next"`, a rate-limit bucket that drains faster than a correct client would
   drain it). A script can prove the trap is set; it cannot prove you fell in.

2. **Secrets are never readable.** `config.secret` on a webhook comes back as
   `********` when it is set and is absent when it is not. A script can tell you a hook
   has *no* secret. It cannot tell you the secret on GitHub matches the one in your
   environment, so a *mismatched* secret is indistinguishable from a correct one until
   deliveries start failing with 401/403 from your own server — which the delivery log
   does show.

3. **Secondary rate limits are undocumented in the response.** There is no
   `x-ratelimit-*` bucket for secondary limits and no endpoint that reports how close
   you are to one. `GET /rate_limit` reports primary quota only. Secondary limits are
   only observable *after* the fact, as a 403/429 whose body contains "exceeded a
   secondary rate limit" plus a `retry-after` header. A script can look for evidence in
   past behaviour but cannot pre-emptively measure headroom.

Further, narrower blind spots worth a sentence each in the published note:

- **Your own token's identity is partially opaque.** `GET /user` names the account but
  a read-only token cannot enumerate all tokens on the account, so "this token expires
  in 6 days" is only knowable for the token you are holding, and only for fine-grained
  and App tokens where an expiry is exposed.
- **Webhook delivery history is retained for a limited window.** Deliveries older than
  the retention period are gone; a script cannot audit failures beyond it.
- **Org policy read requires org scope.** IP allow lists, OAuth App restrictions and
  token-approval policy are readable only with `admin:org`-class access. A repo-scoped
  read-only token sees the *effect* (a 403) but not the *rule*.
- **Rate-limit consumption is not attributable.** The `core` bucket is shared by every
  process using that token. The API reports the drain, never which process caused it.
- **GraphQL query text is not stored server-side.** Cost and node counts can only be
  measured by running the query, which spends points.

---

## Table of contents


**Rate limits**

- [`rate-limit-core-exhausted`](#rate-limit-core-exhausted) — Core REST quota is exhausted and every call returns 403
- [`rate-limit-unauthenticated`](#rate-limit-unauthenticated) — The script is unauthenticated and capped at 60 requests an hour
- [`secondary-limit-concurrency`](#secondary-limit-concurrency) — More than 100 concurrent requests trips a secondary limit
- [`secondary-limit-points-per-minute`](#secondary-limit-points-per-minute) — A hot endpoint burns 900 points a minute and gets throttled
- [`secondary-limit-content-creation`](#secondary-limit-content-creation) — Bulk issue or comment creation exceeds 80 requests a minute
- [`retry-after-ignored`](#retry-after-ignored) — The client ignores retry-after and keeps hammering the API
- [`search-bucket-exhausted`](#search-bucket-exhausted) — Search has its own 30-per-minute bucket and drains separately
- [`code-search-bucket-exhausted`](#code-search-bucket-exhausted) — Code search burns a separate 10-per-minute quota
- [`no-conditional-requests`](#no-conditional-requests) — Polling without ETags spends full quota on unchanged data
- [`etag-invalidated-by-token-rotation`](#etag-invalidated-by-token-rotation) — Rotating the token invalidates every cached ETag at once
- [`polling-instead-of-webhooks`](#polling-instead-of-webhooks) — The integration polls for events that a webhook would push
- [`poll-interval-header-ignored`](#poll-interval-header-ignored) — The x-poll-interval header is ignored on the events endpoints
- [`actions-token-repo-scoped-limit`](#actions-token-repo-scoped-limit) — GITHUB_TOKEN gets only 1,000 API requests per hour per repo

**Authentication and tokens**

- [`bad-credentials-401`](#bad-credentials-401) — Every request returns 401 Bad credentials
- [`classic-pat-expired`](#classic-pat-expired) — A classic personal access token has passed its expiry date
- [`token-expiring-soon`](#token-expiring-soon) — The token in use expires within days and nobody is watching
- [`missing-oauth-scope`](#missing-oauth-scope) — The token is missing a scope the endpoint requires
- [`over-scoped-token`](#over-scoped-token) — A read-only job holds a token with full repo and admin scopes
- [`basic-auth-password-removed`](#basic-auth-password-removed) — The client still sends a username and password to the API
- [`token-in-query-string`](#token-in-query-string) — The token is passed as an access_token query parameter
- [`user-agent-missing`](#user-agent-missing) — Requests without a User-Agent header are rejected outright
- [`wrong-authorization-scheme`](#wrong-authorization-scheme) — A JWT is sent as "token" or a PAT is sent as "Bearer" wrongly
- [`unused-classic-token-auto-revoked`](#unused-classic-token-auto-revoked) — A classic token unused for a year was removed automatically
- [`oauth-token-revoked-by-user`](#oauth-token-revoked-by-user) — A user revoked the OAuth grant and their token is dead
- [`installation-token-rejected-by-endpoint`](#installation-token-rejected-by-endpoint) — Some endpoints refuse installation access tokens entirely
- [`unsupported-api-version`](#unsupported-api-version) — A pinned X-GitHub-Api-Version is no longer supported
- [`wrong-identity-token`](#wrong-identity-token) — The token belongs to a person rather than a service account

**GitHub Apps**

- [`jwt-exp-too-far-future`](#jwt-exp-too-far-future) — The App JWT sets exp more than ten minutes ahead
- [`jwt-clock-drift-iat`](#jwt-clock-drift-iat) — Clock drift makes the JWT iat claim look like the future
- [`jwt-wrong-key-or-algorithm`](#jwt-wrong-key-or-algorithm) — The JWT is signed with the wrong key or the wrong algorithm
- [`installation-token-expired`](#installation-token-expired) — The installation access token expired after one hour
- [`app-not-installed-on-repo`](#app-not-installed-on-repo) — The App is not installed on the repository it is asked about
- [`installation-suspended`](#installation-suspended) — The installation is suspended and every call 403s
- [`installation-repository-selection-partial`](#installation-repository-selection-partial) — The installation covers only some repositories, silently
- [`app-permission-missing`](#app-permission-missing) — Resource not accessible by integration on one endpoint
- [`app-permission-upgrade-not-accepted`](#app-permission-upgrade-not-accepted) — A new App permission was added but installers never accepted it
- [`app-not-subscribed-to-event`](#app-not-subscribed-to-event) — The App never receives an event it was never subscribed to
- [`app-token-scoped-down-too-far`](#app-token-scoped-down-too-far) — A scoped-down installation token cannot reach the target repo
- [`app-rate-limit-not-scaling`](#app-rate-limit-not-scaling) — The App's rate limit never grew with the installation
- [`app-installation-id-hardcoded`](#app-installation-id-hardcoded) — A hardcoded installation id stops matching reality

**Webhooks**

- [`webhook-inactive`](#webhook-inactive) — The webhook exists but is switched off
- [`webhook-no-secret`](#webhook-no-secret) — The webhook has no secret so payloads cannot be verified
- [`webhook-sha1-signature-only`](#webhook-sha1-signature-only) — The receiver still validates the legacy SHA-1 signature
- [`webhook-insecure-ssl`](#webhook-insecure-ssl) — SSL verification is disabled on the webhook
- [`webhook-http-url`](#webhook-http-url) — The webhook posts to a plain http:// URL
- [`webhook-deliveries-failing`](#webhook-deliveries-failing) — Deliveries are failing and nobody is reading the log
- [`webhook-timeout-10s`](#webhook-timeout-10s) — The receiver takes longer than 10 seconds and times out
- [`webhook-event-not-subscribed`](#webhook-event-not-subscribed) — The hook is not subscribed to the event you are waiting for
- [`webhook-wildcard-events`](#webhook-wildcard-events) — The hook subscribes to every event with a wildcard
- [`webhook-content-type-mismatch`](#webhook-content-type-mismatch) — The hook sends form-encoded bodies to a JSON receiver
- [`webhook-ip-allowlist-drift`](#webhook-ip-allowlist-drift) — A firewall allow-list no longer matches GitHub's hook IP ranges
- [`duplicate-webhooks`](#duplicate-webhooks) — The same URL is registered on both the org and the repo
- [`webhook-secret-never-rotated`](#webhook-secret-never-rotated) — The webhook secret has not changed in years
- [`app-webhook-url-unset`](#app-webhook-url-unset) — The GitHub App has no webhook URL configured

**Pagination and queries**

- [`link-header-not-followed`](#link-header-not-followed) — Only the first page of results is ever read
- [`per-page-default-30`](#per-page-default-30) — per_page is unset so every list costs 3.3x more requests
- [`per-page-over-100-clamped`](#per-page-over-100-clamped) — per_page above 100 is silently reduced, not rejected
- [`rel-last-absent`](#rel-last-absent) — The Link header has no rel="last" and the loop terminates early
- [`endpoint-ignores-page-param`](#endpoint-ignores-page-param) — Some endpoints ignore page and per_page entirely
- [`search-1000-result-cap`](#search-1000-result-cap) — Search returns at most 1,000 results whatever total_count says
- [`search-incomplete-results`](#search-incomplete-results) — The search response sets incomplete_results and nobody checks it
- [`compare-250-commit-cap`](#compare-250-commit-cap) — The compare endpoint stops at 250 commits without paging
- [`pr-files-and-commits-caps`](#pr-files-and-commits-caps) — A pull request's files and commits lists are capped
- [`request-timeout-502`](#request-timeout-502) — Expensive requests are killed at 10 seconds with a 502
- [`unstable-sort-duplicates`](#unstable-sort-duplicates) — Items shift between pages and the walk skips records
- [`repo-renamed-301-redirect`](#repo-renamed-301-redirect) — The repository was renamed and requests 301 to a new URL

**GraphQL**

- [`graphql-200-with-errors`](#graphql-200-with-errors) — GraphQL returns HTTP 200 with an errors array and null data
- [`graphql-partial-data-nulls`](#graphql-partial-data-nulls) — Some fields come back null because of per-field permissions
- [`graphql-rate-limited`](#graphql-rate-limited) — GraphQL points run out in a bucket separate from REST
- [`graphql-node-limit-exceeded`](#graphql-node-limit-exceeded) — A nested query requests more than 500,000 nodes
- [`graphql-first-over-100`](#graphql-first-over-100) — A connection asks for first: 500 and is rejected
- [`graphql-nested-pagination-ignored`](#graphql-nested-pagination-ignored) — Only the outer connection is paginated, so inner data truncates
- [`graphql-cost-not-measured`](#graphql-cost-not-measured) — Nobody knows what the query costs until the budget is gone
- [`graphql-timeout-point-penalty`](#graphql-timeout-point-penalty) — A slow GraphQL query is killed and charged extra points
- [`graphql-mutation-secondary-cost`](#graphql-mutation-secondary-cost) — Mutations cost five times more against the secondary limit
- [`graphql-search-same-1000-cap`](#graphql-search-same-1000-cap) — GraphQL search hits the same 1,000-result ceiling as REST
- [`graphql-id-vs-databaseid`](#graphql-id-vs-databaseid) — GraphQL node ids are stored where REST ids are expected

**Permissions and access**

- [`404-masking-403`](#404-masking-403) — A permission error is disguised as 404 Not Found
- [`resource-not-accessible-by-pat`](#resource-not-accessible-by-pat) — Resource not accessible by personal access token
- [`branch-protection-requires-admin`](#branch-protection-requires-admin) — Reading branch protection needs admin and returns 403 without it
- [`repo-archived-writes-403`](#repo-archived-writes-403) — The repository is archived so every write returns 403
- [`repo-disabled`](#repo-disabled) — The repository is disabled and behaves like a ghost
- [`deploy-key-read-only-assumed-write`](#deploy-key-read-only-assumed-write) — A deploy key is read-only where the workflow expects write
- [`collaborator-permission-insufficient`](#collaborator-permission-insufficient) — The account behind the token has only read on the repo
- [`feature-disabled-endpoint-403`](#feature-disabled-endpoint-403) — Security-feature endpoints 403 because the feature is off
- [`fork-vs-upstream-confusion`](#fork-vs-upstream-confusion) — The integration is pointed at a fork, not the upstream repo
- [`private-repo-visibility-changed`](#private-repo-visibility-changed) — A repository went private and the integration lost access
- [`unverified-commit-signature-assumed`](#unverified-commit-signature-assumed) — Commit signature verification is assumed but never read
- [`missing-endpoint-404-vs-405`](#missing-endpoint-404-vs-405) — The wrong HTTP verb returns 404 rather than 405

**Organization and SSO**

- [`saml-token-not-authorized`](#saml-token-not-authorized) — The token is not SSO-authorized for the organization
- [`saml-partial-results`](#saml-partial-results) — Org lists silently omit SSO-enforced organizations
- [`saml-session-expired`](#saml-session-expired) — The SAML session lapsed and authorization must be renewed
- [`oauth-app-access-restricted`](#oauth-app-access-restricted) — The org blocks the OAuth app and requests to it 403
- [`fine-grained-pat-pending-approval`](#fine-grained-pat-pending-approval) — A fine-grained token is waiting for organization approval
- [`ip-allow-list-blocks-requests`](#ip-allow-list-blocks-requests) — An organization IP allow list blocks the integration's egress
- [`org-2fa-requirement-removed-member`](#org-2fa-requirement-removed-member) — Enforcing 2FA silently removed the machine account
- [`org-base-permission-changed`](#org-base-permission-changed) — The org's base permission dropped and reads started failing
- [`app-installation-request-pending`](#app-installation-request-pending) — The App installation was requested but never approved
- [`org-token-lifetime-policy`](#org-token-lifetime-policy) — An org policy caps token lifetime shorter than the rotation
- [`outside-collaborator-invisible-org-data`](#outside-collaborator-invisible-org-data) — An outside collaborator's token cannot see org-level data
- [`enterprise-endpoint-on-dotcom`](#enterprise-endpoint-on-dotcom) — The client points at the wrong API host for the account

---

# Rate limits

## rate-limit-core-exhausted
1. **slug** — `rate-limit-core-exhausted`
2. **title** — Core REST quota is exhausted and every call returns 403
3. **symptom** — `403 Forbidden` (sometimes `429`) with `{"message":"API rate limit exceeded for user ID 12345.","documentation_url":"https://docs.github.com/rest/overview/resources-in-the-rest-api#rate-limiting"}`. Every endpoint fails identically, so it reads like an outage or a bad token.
4. **mechanism** — Authenticated users get 5,000 requests/hour (15,000 on Enterprise Cloud) against the `core` bucket, shared across every process using that token. Once `x-ratelimit-remaining` reaches 0, all non-search REST calls fail until `x-ratelimit-reset`.
5. **detect** — `GET /rate_limit` → `resources.core.remaining`, `.limit`, `.used`, `.reset`. This endpoint does not count against the primary rate limit. Also read `x-ratelimit-remaining`, `x-ratelimit-used`, `x-ratelimit-reset` and `x-ratelimit-resource` on any real call. Flag when `used / limit > 0.8`, or when `remaining == 0`.
6. **repair** — Cache with conditional requests (`If-None-Match`) so unchanged resources cost nothing, move bulk reads to GraphQL where one query replaces many REST calls, and switch from polling to webhooks. If the workload is genuinely large, authenticate as a GitHub App installation, whose limit scales with installed repositories and users up to 12,500/hour.
7. **category** — Rate limits
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api · https://docs.github.com/en/rest/rate-limit/rate-limit · https://stackoverflow.com/questions/38378337/receiving-github-api-403-error-when-i-have-not-exceeded-my-rate-limit

## rate-limit-unauthenticated
1. **slug** — `rate-limit-unauthenticated`
2. **title** — The script is unauthenticated and capped at 60 requests an hour
3. **symptom** — Works for a minute, then `403` with `"API rate limit exceeded for <IP address>."` A shared CI IP or NAT gateway makes it fail almost immediately.
4. **mechanism** — Unauthenticated requests are limited to 60 per hour **per originating IP address**, not per script. Any code path that drops the `Authorization` header — an env var that resolved empty, a redirect that stripped it, a library default — silently falls back to this tier.
5. **detect** — `GET /rate_limit` → `resources.core.limit`. A value of `60` proves the request is unauthenticated; `5000` or `15000` proves it is not. Corroborate with `GET /user`: an unauthenticated call returns `401 {"message":"Requires authentication"}`. The `x-ratelimit-limit` header on any response says the same thing in one round trip.
6. **repair** — Send `Authorization: Bearer <token>` on every request and assert at startup that `GET /rate_limit` reports a limit above 60, failing loudly if it does not. Never let a missing token degrade to anonymous access.
7. **category** — Rate limits
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api · https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api

## secondary-limit-concurrency
1. **slug** — `secondary-limit-concurrency`
2. **title** — More than 100 concurrent requests trips a secondary limit
3. **symptom** — `403` or `429` with `"You have exceeded a secondary rate limit. Please wait a few minutes before you try again."` and a `retry-after` header, while `x-ratelimit-remaining` still shows thousands left.
4. **mechanism** — Secondary limits are separate from the hourly quota and exist to stop bursts. No more than 100 concurrent requests are allowed across REST and GraphQL. Parallelised scripts — a `Promise.all` over a repo list, a thread pool — hit this long before the primary quota is touched.
5. **detect** — Cannot be measured ahead of time (see blind spots). Detect after the fact: any response with status 403/429 whose body matches `secondary rate limit` **while** `x-ratelimit-remaining` is non-zero is a secondary limit, not a quota problem. Record the `retry-after` value and `x-github-request-id`.
6. **repair** — Serialise requests instead of fanning out: a queue with concurrency 1 for mutations and a small bounded pool for reads. Honour `retry-after` exactly; where it is absent, wait at least 60 seconds and then back off exponentially.
7. **category** — Rate limits
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api · https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api · https://stackoverflow.com/questions/70030298/continuously-hitting-the-github-secondary-rate-limit-even-after-following-the-be

## secondary-limit-points-per-minute
1. **slug** — `secondary-limit-points-per-minute`
2. **title** — A hot endpoint burns 900 points a minute and gets throttled
3. **symptom** — Intermittent `403`/`429` "secondary rate limit" bursts that clear after a minute and return. Retrying immediately reproduces it; the hourly quota never looks low.
4. **mechanism** — REST calls to a single endpoint are capped at 900 points per minute, and there is also a 90-seconds-of-CPU-time-per-60-seconds-of-real-time cap. Expensive endpoints (search, large diffs, repo listings for big orgs) consume disproportionate CPU, so a modest request rate can breach the CPU cap while the point count looks fine.
5. **detect** — Look for a cluster of `429`/`403` "secondary rate limit" responses concentrated on one path while `GET /rate_limit` shows `core.remaining` healthy. `x-ratelimit-resource` on the failing call names the bucket the request was billed to, which identifies the expensive endpoint.
6. **repair** — Spread hot-endpoint calls over time rather than bursting, and replace expensive per-item REST calls with a single GraphQL query that returns the same fields. Add at least one second between mutating requests.
7. **category** — Rate limits
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api · https://stackoverflow.com/questions/73644164/where-can-i-view-the-secondary-rate-limit-of-github-rest-api

## secondary-limit-content-creation
1. **slug** — `secondary-limit-content-creation`
2. **title** — Bulk issue or comment creation exceeds 80 requests a minute
3. **symptom** — A migration or bot that creates issues, comments or commits runs fine for the first ~80 items, then every subsequent `POST` returns `403` "secondary rate limit".
4. **mechanism** — Content-generating requests are limited to 80 per minute and 500 per hour, separately from the hourly quota. Creating an issue with a body and three labels can count as more than one content-generating request.
5. **detect** — A read-only detection is indirect but real: `GET /repos/{owner}/{repo}/issues?state=all&sort=created&direction=desc&per_page=100` and look at the `created_at` distribution. A dense burst — dozens of items within the same minute by the same `user.login` — is the signature of a script that will trip this limit. Correlate with `GET /users/{login}` → `type: "Bot"`.
6. **repair** — Rate-limit content creation client side to well under 80/minute, sleep at least one second between mutations, and treat a `403` with `retry-after` as a signal to pause the whole queue rather than retry the single item.
7. **category** — Rate limits
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api · https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api

## retry-after-ignored
1. **slug** — `retry-after-ignored`
2. **title** — The client ignores retry-after and keeps hammering the API
3. **symptom** — Logs show hundreds of consecutive `403`/`429` responses seconds apart. The throttle window keeps extending; the integration never recovers on its own.
4. **mechanism** — GitHub sends `retry-after` (seconds) on secondary-limit responses and `x-ratelimit-reset` (epoch seconds) on primary-limit responses. Clients that treat every non-2xx as a generic retryable error and use a fixed 1-second backoff hammer straight through both, which prolongs the throttle.
5. **detect** — Header-based: on a throttled response, `retry-after` and `x-ratelimit-reset` are both present. A read-only prober can request a known-cheap endpoint, and if it returns 403 with `retry-after: N`, report the required wait. Detecting the *client's* behaviour requires observing request timestamps, which is a blind spot; report the header contract instead.
6. **repair** — Branch on the headers: if `retry-after` is present, sleep exactly that many seconds; else if `x-ratelimit-remaining` is `0`, sleep until `x-ratelimit-reset`; else exponential backoff with jitter, capped, with a maximum attempt count.
7. **category** — Rate limits
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api · https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api

## search-bucket-exhausted
1. **slug** — `search-bucket-exhausted`
2. **title** — Search has its own 30-per-minute bucket and drains separately
3. **symptom** — `GET /search/issues` returns `403` "API rate limit exceeded" after roughly 30 calls in a minute, while ordinary REST calls with the same token keep working.
4. **mechanism** — Search is not billed to `core`. Authenticated search is limited to 30 requests/minute (10/minute unauthenticated), and the limit is per minute, not per hour, so a loop that searches once per repository exhausts it almost instantly.
5. **detect** — `GET /rate_limit` → `resources.search.limit`, `.remaining`, `.reset`. Compare against `resources.core` to show they are independent buckets. On a live search call, `x-ratelimit-resource: search` confirms which bucket was billed.
6. **repair** — Replace per-item searches with a single broader search plus client-side filtering, or with a list endpoint that is billed to `core`. Where search is unavoidable, throttle to under 30/minute and cache results by query string.
7. **category** — Rate limits
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api · https://stackoverflow.com/questions/75415450/i-keep-hitting-you-have-exceeded-a-secondary-rate-limit-on-my-github-api-after

## code-search-bucket-exhausted
1. **slug** — `code-search-bucket-exhausted`
2. **title** — Code search burns a separate 10-per-minute quota
3. **symptom** — `GET /search/code` throttles after a handful of calls, far sooner than other search endpoints, with `403` "secondary rate limit" or a code-search-specific rate-limit message.
4. **mechanism** — Code search has its own `code_search` bucket with a much tighter limit than general search, and it requires authentication at all. Tools that grep an org by iterating repositories through code search hit it within seconds.
5. **detect** — `GET /rate_limit` → `resources.code_search.limit`, `.remaining`, `.reset`. On a live call, `x-ratelimit-resource: code_search`.
6. **repair** — Do not iterate code search per repository. Use one `org:` or `user:` qualified query, page it, and cache. For exhaustive scans, clone shallowly and grep locally instead of using the API.
7. **category** — Rate limits
8. **sources** — https://docs.github.com/en/rest/rate-limit/rate-limit · https://stackoverflow.com/questions/75019972/why-is-my-github-code-search-hitting-secondary-rate-limits

## no-conditional-requests
1. **slug** — `no-conditional-requests`
2. **title** — Polling without ETags spends full quota on unchanged data
3. **symptom** — Quota drains steadily even though almost nothing in the repository changes. `x-ratelimit-used` climbs by exactly the number of requests made; there are no `304` responses anywhere.
4. **mechanism** — A `304 Not Modified` response **does not count against the primary rate limit**. A client that never sends `If-None-Match` (from the response `etag`) or `If-Modified-Since` (from `last-modified`) pays full price for every poll of data that has not moved.
5. **detect** — Call the endpoint the integration polls, keep the `etag` from the response, then repeat with `If-None-Match: <etag>` and compare `x-ratelimit-used` before and after. If the second call returns `304` and `used` did not increase, the saving is real and quantifiable; report the projected hourly saving for the observed poll rate.
6. **repair** — Store the `etag` per URL, send it back as `If-None-Match`, and treat `304` as "no change" rather than an error. Keep request parameters and sort order stable so responses stay cacheable.
7. **category** — Rate limits
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api · https://stackoverflow.com/questions/18489441/conditional-requests-with-paging-when-using-the-github-api

## etag-invalidated-by-token-rotation
1. **slug** — `etag-invalidated-by-token-rotation`
2. **title** — Rotating the token invalidates every cached ETag at once
3. **symptom** — Rate-limit consumption spikes on a fixed schedule — every hour for a GitHub App, or on each deploy — because a cache that was returning `304`s suddenly returns `200`s for everything.
4. **mechanism** — ETags are scoped to the credential. When an installation access token expires after one hour and a new one is minted, the stored ETags no longer match and every conditional request becomes a full, billable response. The same happens when a PAT is rotated.
5. **detect** — Sample `GET /rate_limit` → `resources.core.used` on a short interval and look for a sawtooth that resets on the hour. For an App, compare the `expires_at` on the installation token against the spike timing. A single conditional request made with an old ETag and a fresh token returns `200` rather than `304`, which demonstrates the effect directly.
6. **repair** — Key the ETag cache by credential so a rotation does not silently produce misses, and reuse an installation token for its full hour rather than minting one per request. Where possible let the same token serve the whole polling cycle.
7. **category** — Rate limits
8. **sources** — https://stackoverflow.com/questions/77098110/github-api-etags-are-invalidated-because-token-has-expired-and-causing-spike-in · https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation

## polling-instead-of-webhooks
1. **slug** — `polling-instead-of-webhooks`
2. **title** — The integration polls for events that a webhook would push
3. **symptom** — High, flat request volume against list endpoints; new events are noticed minutes late; quota is consumed proportional to poll frequency rather than to activity.
4. **mechanism** — GitHub's documented guidance is to subscribe to webhooks rather than poll. Polling costs quota linearly in time and adds latency equal to half the poll interval, and it cannot see events that happened and reverted between polls.
5. **detect** — Read the hooks that exist: `GET /repos/{owner}/{repo}/hooks` and `GET /orgs/{org}/hooks`. An empty array combined with a steadily climbing `resources.core.used` on `GET /rate_limit` is the signature of a poller. For an App, `GET /app/hook/config` returns `url`, `content_type` and `insecure_ssl`; a missing or unreachable `url` says the App is not receiving events.
6. **repair** — Create a repository or organization webhook for the events you currently poll for, subscribe to the specific event names rather than `*`, and keep polling only as a low-frequency reconciliation pass.
7. **category** — Rate limits
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api · https://docs.github.com/en/rest/repos/webhooks

## poll-interval-header-ignored
1. **slug** — `poll-interval-header-ignored`
2. **title** — The x-poll-interval header is ignored on the events endpoints
3. **symptom** — An events consumer polls `GET /repos/{owner}/{repo}/events` every few seconds, receives the same cached page repeatedly, and eventually gets throttled.
4. **mechanism** — Events endpoints are cached and return `x-poll-interval` telling the client the minimum seconds to wait. Polling faster returns identical data — often a `304` if ETags are used, or a billable duplicate `200` if not — and offers no fresher information.
5. **detect** — `GET /repos/{owner}/{repo}/events` (or `/users/{u}/events`) and read the `x-poll-interval` response header alongside `etag`. Report the header value as the floor; any configured interval below it is wasted quota by definition.
6. **repair** — Read `x-poll-interval` on each response and use it as the sleep duration for the next poll, combined with `If-None-Match` so unchanged pages are free.
7. **category** — Rate limits
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api · https://docs.github.com/en/rest/activity/events

## actions-token-repo-scoped-limit
1. **slug** — `actions-token-repo-scoped-limit`
2. **title** — GITHUB_TOKEN gets only 1,000 API requests per hour per repo
3. **symptom** — An API-heavy job that works locally with a PAT throttles when it runs with the built-in token: `403` "API rate limit exceeded" after roughly a thousand calls, and the limit is shared with every other job in the same repository.
4. **mechanism** — The Actions-issued `GITHUB_TOKEN` has a much smaller budget than a user token: 1,000 requests/hour per repository (15,000 on Enterprise Cloud), and every concurrent job in that repository draws from the same pool. GraphQL gets 1,000 points/hour on the same token.
5. **detect** — `GET /rate_limit` with the token in question → `resources.core.limit`. A limit of `1000` identifies an Actions token; `5000` a user PAT; `15000` Enterprise Cloud. `GET /user` with an Actions token returns `403`, which is itself a fingerprint.
6. **repair** — For API-heavy automation, authenticate as a GitHub App installation instead of using the built-in token, which raises the ceiling and scales with installation size. Reduce call count with GraphQL and conditional requests before raising the ceiling.
7. **category** — Rate limits
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api · https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api

---

# Authentication and tokens

## bad-credentials-401
1. **slug** — `bad-credentials-401`
2. **title** — Every request returns 401 Bad credentials
3. **symptom** — `401 Unauthorized` with `{"message":"Bad credentials","documentation_url":"https://docs.github.com/rest"}` on every endpoint, including ones that need no permissions at all.
4. **mechanism** — The token is malformed, revoked, expired, from the wrong account, or damaged in transit — a trailing newline from `cat token.txt`, a shell-quoted `$TOKEN` that expanded to nothing, a value truncated by a secret store. GitHub does not distinguish between these cases in the message.
5. **detect** — `GET /user` is the canonical probe. On success it returns the authenticated login and the response carries `x-oauth-scopes` and `x-accepted-oauth-scopes`. On failure, `401 Bad credentials`. Also check the token prefix locally without transmitting it: `ghp_` classic PAT, `github_pat_` fine-grained PAT, `gho_` OAuth user token, `ghs_` App installation token, `ghu_` App user-to-server token, `ghr_` refresh token.
6. **repair** — Re-mint the token, store it without surrounding whitespace, and add a startup assertion that `GET /user` returns 200 and the expected `login` before the integration does any real work.
7. **category** — Authentication and tokens
8. **sources** — https://stackoverflow.com/questions/44490426/receiving-401-bad-credentials-when-hitting-github-api-endpoint · https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api · https://stackoverflow.com/questions/79699917/github-personal-access-token-returns-401-bad-credentials-but-cli-works-perfect

## classic-pat-expired
1. **slug** — `classic-pat-expired`
2. **title** — A classic personal access token has passed its expiry date
3. **symptom** — The integration worked for months, then every call returns `401 Bad credentials` at the same moment. Nothing changed in the code or the repository.
4. **mechanism** — Classic PATs can be created with an expiry, and GitHub recommends one. When it passes, the token stops working with no grace period and no distinct error — it looks identical to a typo'd token.
5. **detect** — `GET /user` returning `401 Bad credentials` while a *known-good* token succeeds isolates the token as the cause. For a token that still works, the `github-authentication-token-expiration` response header (returned on authenticated REST calls for tokens that carry an expiry) gives the exact expiry timestamp so you can warn before the cliff.
6. **repair** — Rotate the token and record the expiry date in the same place the token is stored, then alert some days before it. Prefer a GitHub App installation, whose one-hour tokens are minted automatically and never require a human calendar entry.
7. **category** — Authentication and tokens
8. **sources** — https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens · https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api

## token-expiring-soon
1. **slug** — `token-expiring-soon`
2. **title** — The token in use expires within days and nobody is watching
3. **symptom** — Nothing yet. This is the note that fires before the outage, not after it.
4. **mechanism** — Fine-grained PATs must have an expiry of at most 366 days unless the organization allows otherwise, and organizations can enforce a shorter maximum lifetime. The expiry is invisible in normal operation, so the failure arrives as a total, sudden `401`.
5. **detect** — Make any authenticated request and read the `github-authentication-token-expiration` response header, which carries the token's expiry for tokens that have one. Report days remaining. For a GitHub App installation token, `POST /app/installations/{id}/access_tokens` returns `expires_at` (always one hour out), and the App's own JWT expiry is under your control.
6. **repair** — Alert on the header at 30, 14 and 3 days. Where the integration runs unattended, replace the PAT with a GitHub App so token minting is automatic and expiry is a non-event.
7. **category** — Authentication and tokens
8. **sources** — https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens · https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation

## missing-oauth-scope
1. **slug** — `missing-oauth-scope`
2. **title** — The token is missing a scope the endpoint requires
3. **symptom** — `403 Forbidden` with `"Must have admin rights to Repository."` or a bare `404 Not Found` on a resource you can see in the browser. Reads succeed, one specific call does not.
4. **mechanism** — Classic PATs and OAuth tokens carry coarse scopes. An endpoint that needs `repo` will 404 for a `public_repo`-only token; one that needs `admin:org` or `admin:repo_hook` will 403. The scope set is fixed at creation and cannot be widened without re-minting.
5. **detect** — Every authenticated REST response carries `x-oauth-scopes` (what the token has) and `x-accepted-oauth-scopes` (what the endpoint accepts). Call the failing endpoint and diff the two headers — the missing scope is named explicitly. `GET /user` gives the same headers cheaply for the common scopes.
6. **repair** — Re-create the token with exactly the scopes named in `x-accepted-oauth-scopes` and no more. For webhook management specifically that is `admin:repo_hook` or `admin:org_hook`; for private repositories, `repo`.
7. **category** — Authentication and tokens
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api · https://stackoverflow.com/questions/73327035/which-personal-access-token-scopes-are-necessary-to-create-a-github-repository-w · https://stackoverflow.com/questions/75310175/cannot-retrieve-scopes-for-useremail-on-the-github-api

## over-scoped-token
1. **slug** — `over-scoped-token`
2. **title** — A read-only job holds a token with full repo and admin scopes
3. **symptom** — Nothing fails. That is the problem: a token that only needs to list pull requests can delete repositories, and if it leaks the blast radius is the whole account.
4. **mechanism** — Classic PAT scopes are coarse — `repo` grants read *and write* to every repository the user can reach, including private ones and organization ones. Fine-grained tokens exist precisely to avoid this, but the default habit is to tick `repo` and move on.
5. **detect** — `GET /user` → read `x-oauth-scopes`. Flag any of `repo`, `delete_repo`, `admin:org`, `admin:repo_hook`, `workflow`, `write:packages` on a token used by a read-only integration. For a fine-grained token, `GET /rate_limit` still works but scope headers are absent; instead read `GET /installation/repositories` (Apps) or attempt a benign write and expect `403`.
6. **repair** — Replace the classic token with a fine-grained PAT limited to the specific repositories and the specific read permissions (`Contents: Read`, `Metadata: Read`, `Pull requests: Read`), or with an App installation carrying only the permissions listed in `X-Accepted-GitHub-Permissions` for the endpoints you actually call.
7. **category** — Authentication and tokens
8. **sources** — https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens · https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps

## basic-auth-password-removed
1. **slug** — `basic-auth-password-removed`
2. **title** — The client still sends a username and password to the API
3. **symptom** — `401` with `"Support for password authentication was removed. Please use a personal access token instead."` — one of the most-viewed GitHub errors on Stack Overflow.
4. **mechanism** — GitHub removed password authentication for the API. Basic auth with a username and *token* still works on some paths, but a username and account password never does. Old scripts, `Invoke-WebRequest` snippets and library defaults still carry the pattern.
5. **detect** — `GET /user` with the credentials in use. If the response is `401` with the "password authentication was removed" message, the credential shape is wrong rather than the credential itself. A correct call is `Authorization: Bearer <token>` and returns 200.
6. **repair** — Replace basic auth with the `Authorization: Bearer <token>` header (or `token <token>`, which is still accepted) and delete any username field from the client configuration.
7. **category** — Authentication and tokens
8. **sources** — https://stackoverflow.com/questions/68775869/message-support-for-password-authentication-was-removed · https://stackoverflow.com/questions/27951561/use-invoke-webrequest-with-a-username-and-password-for-basic-authentication-on-t

## token-in-query-string
1. **slug** — `token-in-query-string`
2. **title** — The token is passed as an access_token query parameter
3. **symptom** — `401 Requires authentication` on endpoints that clearly should work, and the token appearing in logs, proxy records and browser history.
4. **mechanism** — GitHub removed support for the `?access_token=` query parameter. Requests carrying it are treated as unauthenticated, which also silently drops the caller to the 60-per-hour anonymous tier before the outright 401.
5. **detect** — `GET /rate_limit?access_token=<token>` returns `resources.core.limit: 60`, whereas the same call with an `Authorization` header returns `5000`. The limit value is the tell.
6. **repair** — Move the credential into the `Authorization` header on every request and scrub any logged URLs that may still contain a token, then revoke and re-mint any token that was ever sent in a query string.
7. **category** — Authentication and tokens
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/authenticating-to-the-rest-api · https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api

## user-agent-missing
1. **slug** — `user-agent-missing`
2. **title** — Requests without a User-Agent header are rejected outright
3. **symptom** — `403 Forbidden` with `"Request forbidden by administrative rules. Please make sure your request has a User-Agent header."` Usually seen from raw `http.client`, Go's default transport with the header stripped, or a hand-rolled socket client.
4. **mechanism** — GitHub requires a `User-Agent` on every API request, ideally naming the application or the GitHub username. Most SDKs set one; anything below the SDK layer does not.
5. **detect** — Make one request without the header and one with it. The pair of responses — `403` with the administrative-rules message versus `200` — proves the cause in two calls and costs almost no quota. On a live integration, the failure is identifiable purely from the message string.
6. **repair** — Set a descriptive `User-Agent` such as `my-org-repo-auditor/1.2 (+https://example.com)` on the HTTP client's default headers so it cannot be forgotten per-request.
7. **category** — Authentication and tokens
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api · https://docs.github.com/en/rest/using-the-rest-api/getting-started-with-the-rest-api

## wrong-authorization-scheme
1. **slug** — `wrong-authorization-scheme`
2. **title** — A JWT is sent as "token" or a PAT is sent as "Bearer" wrongly
3. **symptom** — `401 Bad credentials` on App endpoints while the same token works elsewhere, or `403` on `GET /app` with a JWT that is otherwise valid.
4. **mechanism** — GitHub App JWTs must be sent as `Authorization: Bearer <jwt>`. Installation tokens and PATs accept both `Bearer` and the legacy `token` scheme. Mixing them — particularly sending a JWT with the `token` scheme — fails with the generic bad-credentials message, which hides the real cause.
5. **detect** — `GET /app` authenticated with the JWT as `Bearer` returns the App's `id`, `slug`, `owner` and `permissions`; anything else returns `401`. A PAT sent to `GET /app` also returns `403 {"message":"A JSON web token could not be decoded"}` or similar, which distinguishes "wrong scheme" from "wrong token type".
6. **repair** — Use `Bearer` for JWTs and for installation tokens uniformly. Assert at startup that `GET /app` succeeds with the JWT before attempting to mint installation tokens.
7. **category** — Authentication and tokens
8. **sources** — https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app · https://stackoverflow.com/questions/61770501/github-api-returns-401-while-trying-to-generate-access-token

## unused-classic-token-auto-revoked
1. **slug** — `unused-classic-token-auto-revoked`
2. **title** — A classic token unused for a year was removed automatically
3. **symptom** — A disaster-recovery script or an annual job fails on first run with `401 Bad credentials`, and the token is not listed in the account's token page any more.
4. **mechanism** — GitHub automatically removes classic personal access tokens that have not been used for a year. Tokens reserved for rare, important operations are exactly the ones this deletes.
5. **detect** — `GET /user` with the token returns `401 Bad credentials` and the token no longer appears anywhere. Positively: a periodic liveness check — one `GET /rate_limit` per month per credential — both proves the token still works and keeps it from being reaped.
6. **repair** — Add a scheduled liveness probe that calls `GET /rate_limit` with each stored credential, alerting on failure. It is a zero-quota call and it doubles as a keep-alive.
7. **category** — Authentication and tokens
8. **sources** — https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens · https://docs.github.com/en/rest/rate-limit/rate-limit

## oauth-token-revoked-by-user
1. **slug** — `oauth-token-revoked-by-user`
2. **title** — A user revoked the OAuth grant and their token is dead
3. **symptom** — One user's requests return `401 Bad credentials` while every other user of the same integration is fine. Re-running the OAuth flow fixes it, which makes it look transient.
4. **mechanism** — OAuth user tokens do not expire by default, but a user can revoke the application's authorization at any time from their settings, and an organization owner can revoke it for the whole org. The token dies immediately with no notification to the integration.
5. **detect** — Per-token liveness: `GET /user` returns `401` for the revoked token and 200 for healthy ones, isolating the affected account. An OAuth app owner can additionally check a specific token with `POST /applications/{client_id}/token` authenticated with the client id and secret, which returns `404` for a revoked or invalid token — note this needs app credentials, not the user token.
6. **repair** — Treat a `401` on a stored user token as "re-authorize this user", not as a retryable error: mark the connection broken, stop retrying, and prompt for a fresh OAuth flow.
7. **category** — Authentication and tokens
8. **sources** — https://stackoverflow.com/questions/26902600/whats-the-lifetime-of-github-oauth-api-access-token · https://docs.github.com/en/rest/apps/oauth-applications

## installation-token-rejected-by-endpoint
1. **slug** — `installation-token-rejected-by-endpoint`
2. **title** — Some endpoints refuse installation access tokens entirely
3. **symptom** — A GitHub App integration gets `403 {"message":"Resource not accessible by integration"}` on an endpoint that has nothing obviously to do with permissions — `GET /user` being the classic case.
4. **mechanism** — Not every REST endpoint accepts a server-to-server installation token. `GET /user` needs a *user* context, so an App authenticating as an installation has no "current user" and is refused, no matter what permissions the App holds. Terraform's GitHub provider hitting `/user` under App auth is a well-known instance.
5. **detect** — Call the endpoint with the installation token and read `x-accepted-github-permissions` on the response. If the header is absent while the status is 403, the endpoint is not installation-token-compatible at all rather than under-permissioned. `GET /installation/repositories` succeeding at the same time proves the token itself is valid.
6. **repair** — Use the App-appropriate equivalent — `GET /installation/repositories` instead of `GET /user/repos`, `GET /app` for App identity — or switch that specific call to a user-to-server token obtained through the App's OAuth flow.
7. **category** — Authentication and tokens
8. **sources** — https://stackoverflow.com/questions/70872272/terraform-github-provider-gets-a-403-error-on-user-using-github-app-auth · https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation

## unsupported-api-version
1. **slug** — `unsupported-api-version`
2. **title** — A pinned X-GitHub-Api-Version is no longer supported
3. **symptom** — `410 Gone` on every request, with a message about the API version not being supported. The integration was untouched; the calendar moved.
4. **mechanism** — REST requests may pin a date-based version with `X-GitHub-Api-Version`. Versions are retired over time, and a request pinned to a retired one is rejected outright. Requests with no header default to `2022-11-28`.
5. **detect** — `GET /versions` returns the list of currently supported version strings. Compare the value your client sends against that list and flag anything absent. Any `410` response with the version message confirms it live.
6. **repair** — Move the pin forward to a supported version after reading the breaking-change notes for the versions in between, and add a check that compares the pinned value against `GET /versions` so retirement is caught before it bites.
7. **category** — Authentication and tokens
8. **sources** — https://docs.github.com/en/rest/about-the-rest-api/api-versions · https://docs.github.com/en/rest/meta/meta

## wrong-identity-token
1. **slug** — `wrong-identity-token`
2. **title** — The token belongs to a person rather than a service account
3. **symptom** — Commits, comments and reviews from the automation are attributed to a named employee. When they leave and the account is deprovisioned, the integration dies with `401`.
4. **mechanism** — A PAT inherits the identity and the access of whoever created it. Automation built on a personal token is coupled to that person's employment, their SSO session, their 2FA and their org membership.
5. **detect** — `GET /user` → `login`, `type` and `name`. A `type` of `"User"` with a human-looking `login` on a token used by automation is the finding; `type: "Bot"` or an App-suffixed login (`my-app[bot]`) is what you want. Cross-check `GET /orgs/{org}/members/{login}` to see whether that human is still a member.
6. **repair** — Replace the personal token with a GitHub App installation (identity `my-app[bot]`, no human dependency) or, failing that, a dedicated machine account whose ownership is documented and whose PAT is stored in the team's secret manager.
7. **category** — Authentication and tokens
8. **sources** — https://docs.github.com/en/apps/creating-github-apps/about-creating-github-apps/about-creating-github-apps · https://stackoverflow.com/questions/70725496/personal-access-tokens-with-an-github-organization-instead-of-user-account

---

# GitHub Apps

## jwt-exp-too-far-future
1. **slug** — `jwt-exp-too-far-future`
2. **title** — The App JWT sets exp more than ten minutes ahead
3. **symptom** — `401` from `GET /app` with `{"message":"'Expiration time' claim ('exp') is too far in the future"}`. The private key is correct and the App exists.
4. **mechanism** — A GitHub App JWT must expire no more than 10 minutes after it is issued. Code that sets a comfortable one-hour expiry — a habit from other JWT systems — is rejected before any permission check happens.
5. **detect** — `GET /app` with the JWT. A 200 returns the App's `id`, `slug`, `name`, `owner`, `permissions` and `events`; a 401 with the `exp` message names the defect exactly. The JWT payload itself can be base64-decoded locally to read `iat` and `exp` without transmitting the key.
6. **repair** — Set `exp` to `iat + 540` (nine minutes) to leave headroom for clock drift, and mint a fresh JWT per token exchange rather than caching one.
7. **category** — GitHub Apps
8. **sources** — https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app · https://stackoverflow.com/questions/61770501/github-api-returns-401-while-trying-to-generate-access-token

## jwt-clock-drift-iat
1. **slug** — `jwt-clock-drift-iat`
2. **title** — Clock drift makes the JWT iat claim look like the future
3. **symptom** — Intermittent `401` with `{"message":"'Issued at' claim ('iat') must be an Integer representing the time that the assertion was issued"}`. It works on a laptop and fails in a container, or fails only on some hosts.
4. **mechanism** — If the signing host's clock runs even slightly ahead of GitHub's, `iat` lands in the future and the JWT is rejected. Containers without NTP, suspended VMs and CI runners with skewed clocks all produce this.
5. **detect** — Compare the `date` response header from any GitHub API call against the local clock; a difference of more than a few seconds is the finding. Then `GET /app` with the JWT to confirm the `iat` message.
6. **repair** — Backdate `iat` by 60 seconds when minting the JWT, and fix host time sync. The backdating is GitHub's own documented recommendation, not a workaround.
7. **category** — GitHub Apps
8. **sources** — https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app · https://stackoverflow.com/questions/77004388/how-to-generate-a-jwt-token-for-a-github-app-using-client-id-and-client-secret-u

## jwt-wrong-key-or-algorithm
1. **slug** — `jwt-wrong-key-or-algorithm`
2. **title** — The JWT is signed with the wrong key or the wrong algorithm
3. **symptom** — `401` with `{"message":"A JSON web token could not be decoded"}` or `"Integration not found"`. Often follows a private-key rotation or a copy-paste that mangled the PEM's line breaks.
4. **mechanism** — App JWTs must be signed `RS256` with a private key that is currently registered on the App, and `iss` must be the App's client ID or app ID. A revoked key, a key belonging to a different App, an `HS256` default in the JWT library, or a PEM whose newlines were flattened by an env var all fail here.
5. **detect** — `GET /app` with the JWT. On success the response body's `id` and `client_id` should match the `iss` you signed with — a mismatch means you are using the wrong App's key. `"Integration not found"` specifically means `iss` does not resolve to an App.
6. **repair** — Re-download the private key from the App's settings, store it with real newlines (base64-encode it for env transport), pin the algorithm to `RS256` explicitly in the JWT library, and set `iss` to the App's client ID.
7. **category** — GitHub Apps
8. **sources** — https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/generating-a-json-web-token-jwt-for-a-github-app · https://stackoverflow.com/questions/71951238/how-to-get-a-github-app-access-token-via-shell

## installation-token-expired
1. **slug** — `installation-token-expired`
2. **title** — The installation access token expired after one hour
3. **symptom** — A long-running job succeeds for 60 minutes and then every call returns `401 Bad credentials` at once. Restarting fixes it, which makes it look like a memory leak.
4. **mechanism** — Installation access tokens expire exactly one hour after minting. Code that fetches a token at startup and holds it for the life of the process — a daemon, a long migration, a queue worker — outlives its own credential.
5. **detect** — The mint response from `POST /app/installations/{installation_id}/access_tokens` includes `expires_at`. A read-only check compares that value against now; anything already past is the finding. Live, the pattern is unmistakable: a run of 200s followed by uniform 401s about an hour after process start.
6. **repair** — Re-mint on a timer at 50 minutes, or on any `401`, rather than at startup only. Octokit's App auth strategy does this automatically; hand-rolled clients must implement it.
7. **category** — GitHub Apps
8. **sources** — https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation · https://stackoverflow.com/questions/78862166/github-apps-jwt-to-installation-token-via-powershell

## app-not-installed-on-repo
1. **slug** — `app-not-installed-on-repo`
2. **title** — The App is not installed on the repository it is asked about
3. **symptom** — `404 Not Found` on a repository that plainly exists and is public, using a token that works for other repositories in the same organization.
4. **mechanism** — An installation token can only see repositories in that installation. If the App was installed with "selected repositories" and the target was never added — or the repo was created after installation — the App gets a 404, because GitHub returns 404 rather than 403 to avoid confirming a resource exists.
5. **detect** — `GET /repos/{owner}/{repo}/installation` with the App JWT returns the installation object if the App is installed there, and `404` if it is not. Complementarily, `GET /installation/repositories` with the installation token returns `total_count` and the exact `repositories[]` the token can reach — if the target is not in that list, this is the cause and not a permission problem.
6. **repair** — Add the repository to the installation, or change the installation to "all repositories" so newly created repos are covered automatically. Print the current `repository_selection` and the reachable repo list alongside the finding.
7. **category** — GitHub Apps
8. **sources** — https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation · https://docs.github.com/en/rest/apps/installations

## installation-suspended
1. **slug** — `installation-suspended`
2. **title** — The installation is suspended and every call 403s
3. **symptom** — Sudden `403` across the whole installation with no permission change and no code change. Webhooks stop arriving too.
4. **mechanism** — An organization owner can *suspend* an App installation rather than uninstalling it. The installation record survives, so the App still lists it, but tokens minted for it are refused and event delivery stops.
5. **detect** — `GET /app/installations` with the App JWT → each installation object carries `suspended_at` and `suspended_by`. A non-null `suspended_at` is the finding, and it is the only clean signal — the token-mint attempt returns a generic error. Also check `GET /app/installations/{installation_id}` for a single installation.
6. **repair** — Ask an organization owner to unsuspend the installation from the org's Installed GitHub Apps settings. Treat `suspended_at != null` as a distinct, non-retryable state in the integration so it stops burning quota on doomed retries.
7. **category** — GitHub Apps
8. **sources** — https://docs.github.com/en/rest/apps/apps · https://docs.github.com/en/apps/maintaining-github-apps/suspending-a-github-app-installation

## installation-repository-selection-partial
1. **slug** — `installation-repository-selection-partial`
2. **title** — The installation covers only some repositories, silently
3. **symptom** — An org-wide audit reports clean because it only ever saw 12 of 140 repositories. Nothing errors; the answer is just quietly incomplete.
4. **mechanism** — `repository_selection` on an installation is either `all` or `selected`. With `selected`, the App sees exactly the chosen repositories and no others, and new repositories are not added automatically. Every list endpoint returns a truthful but partial view.
5. **detect** — `GET /installation/repositories` → `total_count` and `repository_selection`. Compare `total_count` against the organization's real repository count from `GET /orgs/{org}` → `public_repos` plus `total_private_repos`, or against `GET /orgs/{org}/repos?per_page=1` and the `Link` `rel="last"` page number. A gap is the finding.
6. **repair** — Switch the installation to "All repositories", or add the missing repositories explicitly. Have the integration assert its coverage at startup and report the delta rather than silently auditing a subset.
7. **category** — GitHub Apps
8. **sources** — https://docs.github.com/en/rest/apps/installations · https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation

## app-permission-missing
1. **slug** — `app-permission-missing`
2. **title** — Resource not accessible by integration on one endpoint
3. **symptom** — `403 {"message":"Resource not accessible by integration"}` on a single endpoint while the rest of the integration works. Among the most-viewed GitHub errors anywhere.
4. **mechanism** — GitHub App permissions are per-resource and per-level (`read`/`write`). An App with `contents: read` cannot read `pull_requests`, and an App with `pull_requests: read` cannot request reviewers. The error names no permission, so it looks like a bug.
5. **detect** — Two reads. `GET /app` (JWT) or `GET /app/installations` returns `permissions` — the full map the App holds, e.g. `{"contents":"read","metadata":"read","pull_requests":"write"}`. Then call the failing endpoint and read the `x-accepted-github-permissions` response header, which names the permissions that endpoint accepts. The diff is the answer.
6. **repair** — Add exactly the permission named in `x-accepted-github-permissions` to the App, then have every organization owner accept the permission upgrade — new permissions are inert until accepted per installation.
7. **category** — GitHub Apps
8. **sources** — https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps · https://stackoverflow.com/questions/70435286/resource-not-accessible-by-integration-on-github-post-repos-owner-repo-ac · https://stackoverflow.com/questions/70840894/resource-not-accessible-by-integration-using-github-app

## app-permission-upgrade-not-accepted
1. **slug** — `app-permission-upgrade-not-accepted`
2. **title** — A new App permission was added but installers never accepted it
3. **symptom** — The App's settings show the permission granted, yet some installations still get `403 Resource not accessible by integration` and others do not. The split looks random.
4. **mechanism** — Changing an App's permissions does not retroactively apply. Each existing installation must accept the upgrade, usually via an email to the org owner. Until then, that installation's tokens carry the *old* permission set while the App definition shows the new one.
5. **detect** — Compare per-installation permissions against the App's declared permissions: `GET /app` → `permissions` (the App's current definition) versus each entry in `GET /app/installations` → `permissions` (what each installation actually granted). Any installation whose map is a strict subset has an unaccepted upgrade.
6. **repair** — Prompt each affected organization owner to accept the pending permission request from the org's Installed GitHub Apps page. Print the list of installation IDs and account logins that are behind.
7. **category** — GitHub Apps
8. **sources** — https://docs.github.com/en/apps/maintaining-github-apps/editing-a-github-apps-permissions · https://docs.github.com/en/rest/apps/apps

## app-not-subscribed-to-event
1. **slug** — `app-not-subscribed-to-event`
2. **title** — The App never receives an event it was never subscribed to
3. **symptom** — The handler for `pull_request_review_thread` or `release` never fires. No error, no failed delivery, no entry in the delivery log — the event simply does not exist as far as the App is concerned.
4. **mechanism** — A GitHub App receives only the webhook events it declares, and an event can only be declared if the App holds the permission that gates it. Subscribing to `pull_request` requires `pull_requests` permission; without it the checkbox is not even offered, so the subscription silently never happens.
5. **detect** — `GET /app` → `events` array lists exactly what the App subscribes to, and `permissions` shows what gates each. Diff `events` against the events your handlers implement. `GET /app/hook/deliveries` → the `event` field on recent deliveries shows what is actually arriving.
6. **repair** — Add the gating permission first, then subscribe to the event, then have installations accept the upgrade. All three steps are required; doing only the last is the common mistake.
7. **category** — GitHub Apps
8. **sources** — https://docs.github.com/en/webhooks/webhook-events-and-payloads · https://stackoverflow.com/questions/72643679/cannot-create-an-app-that-listens-the-webhook-pull-request-review-thread

## app-token-scoped-down-too-far
1. **slug** — `app-token-scoped-down-too-far`
2. **title** — A scoped-down installation token cannot reach the target repo
3. **symptom** — `404` on a repository the App is definitely installed on, only from one code path. Other code paths using the same App work.
4. **mechanism** — `POST /app/installations/{id}/access_tokens` accepts `repositories`, `repository_ids` and `permissions` body parameters that narrow the token below the installation's grant. A token minted for repo A cannot see repo B, and a token minted with `{"permissions":{"contents":"read"}}` cannot touch issues — even though the installation holds more.
5. **detect** — With the minted token, `GET /installation/repositories` returns only the repositories that token can reach, and the mint response body itself echoes back the granted `permissions` and `repository_selection`. Compare against `GET /app/installations/{id}` → `permissions` to see how far the token was narrowed.
6. **repair** — Mint the token with the repository set and permissions the job actually needs — which may mean widening the mint request, not the App. Print both the installation grant and the token grant so the narrowing is visible.
7. **category** — GitHub Apps
8. **sources** — https://docs.github.com/en/apps/creating-github-apps/authenticating-with-a-github-app/authenticating-as-a-github-app-installation · https://docs.github.com/en/rest/apps/apps

## app-rate-limit-not-scaling
1. **slug** — `app-rate-limit-not-scaling`
2. **title** — The App's rate limit never grew with the installation
3. **symptom** — A GitHub App serving a 400-repository organization throttles at 5,000 requests/hour as if it were a personal token.
4. **mechanism** — An installation's limit starts at 5,000/hour and scales with the number of repositories and users in the installation, up to 12,500/hour outside Enterprise Cloud. An installation restricted to a handful of selected repositories never earns the scaling, and Enterprise Cloud installations get a flat 15,000.
5. **detect** — `GET /rate_limit` with the installation token → `resources.core.limit`. Compare against `GET /installation/repositories` → `total_count` and `GET /app/installations/{id}` → `account` and `repository_selection`. A limit stuck at exactly 5000 with a large org behind it means the installation is narrow.
6. **repair** — Widen the installation to all repositories if the App legitimately needs org-wide reach, which also raises the ceiling. Otherwise reduce call volume with GraphQL and conditional requests instead of chasing the limit.
7. **category** — GitHub Apps
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api · https://docs.github.com/en/rest/rate-limit/rate-limit

## app-installation-id-hardcoded
1. **slug** — `app-installation-id-hardcoded`
2. **title** — A hardcoded installation id stops matching reality
3. **symptom** — `404` from `POST /app/installations/{id}/access_tokens` after an org reinstalls the App, or the integration writes to the wrong organization entirely.
4. **mechanism** — Installation IDs are not stable across uninstall/reinstall. Uninstalling and reinstalling produces a *new* installation ID; the old one 404s. Configurations that paste the ID from a URL once and never look again break on the next reinstall.
5. **detect** — `GET /app/installations` with the JWT lists every current installation with `id`, `account.login`, `repository_selection`, `created_at`, `suspended_at`. If the configured ID is absent from that list, it is stale. `GET /orgs/{org}/installation` resolves the *current* ID for a given org.
6. **repair** — Resolve the installation ID at runtime from `GET /orgs/{org}/installation` (or from the `installation.id` field on the incoming webhook payload) instead of storing it, and key any stored state on the account login rather than the installation ID.
7. **category** — GitHub Apps
8. **sources** — https://stackoverflow.com/questions/74462420/where-can-we-find-github-apps-installation-id · https://stackoverflow.com/questions/57960709/how-to-get-github-app-installation-id-on-pull-request-event

---

# Webhooks

## webhook-inactive
1. **slug** — `webhook-inactive`
2. **title** — The webhook exists but is switched off
3. **symptom** — No deliveries at all, no failures in the delivery log, and the hook is visibly configured with the right URL. Everything looks fine and nothing arrives.
4. **mechanism** — A webhook's `active` flag can be false — set that way at creation, toggled off during an incident and never toggled back, or disabled by GitHub after a long run of failures. An inactive hook generates no deliveries, so there is no failure to find.
5. **detect** — `GET /repos/{owner}/{repo}/hooks` (or `GET /orgs/{org}/hooks`) → the `active` boolean on each hook. `active: false` is the finding. Corroborate with `GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries`, which will show nothing recent, and with `updated_at` to date the change.
6. **repair** — Re-enable the hook (`PATCH` the hook with `active: true`) once the endpoint is confirmed healthy, then use the redelivery endpoint to replay anything missed within the retention window.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/rest/repos/webhooks · https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries

## webhook-no-secret
1. **slug** — `webhook-no-secret`
2. **title** — The webhook has no secret so payloads cannot be verified
3. **symptom** — Nothing fails. Your endpoint accepts any POST from anyone who knows the URL, because there is no `X-Hub-Signature-256` header to check.
4. **mechanism** — The HMAC-SHA256 signature header is only sent when a secret is configured on the hook. With no secret, GitHub omits `X-Hub-Signature-256` entirely — so a receiver that "verifies if the header is present" verifies nothing at all.
5. **detect** — `GET /repos/{owner}/{repo}/hooks` → `config`. When a secret is set, `config.secret` comes back masked as `********`; when it is not, the `secret` key is **absent from `config` entirely**. Absence is the finding. For an App, `GET /app/hook/config` shows the same shape.
6. **repair** — Set a high-entropy secret on the hook, then make the receiver *require* `X-Hub-Signature-256`, compute `hmac_sha256(secret, raw_body)` over the exact raw bytes, and compare in constant time. Reject when the header is missing rather than skipping the check.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries · https://docs.github.com/en/rest/repos/webhooks

## webhook-sha1-signature-only
1. **slug** — `webhook-sha1-signature-only`
2. **title** — The receiver still validates the legacy SHA-1 signature
3. **symptom** — Nothing fails today. The receiver checks `X-Hub-Signature` (HMAC-SHA1), which GitHub sends only for legacy compatibility, and ignores the SHA-256 header it should be using.
4. **mechanism** — GitHub sends both `X-Hub-Signature` (SHA-1, legacy) and `X-Hub-Signature-256` (SHA-256). SHA-1 is retained for old receivers; new code should use the SHA-256 header. This is a receiver-side choice, so the API cannot see it directly.
5. **detect** — API-visible proxy only: confirm a secret is set (`config.secret == "********"` on `GET /repos/{owner}/{repo}/hooks`), then inspect a delivery's request headers via `GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id}` → `request.headers`, which lists both signature headers as GitHub sent them. What the receiver *checked* is a documented blind spot; report the available headers and the recommendation.
6. **repair** — Validate `X-Hub-Signature-256` with `hmac.compare_digest` against the raw request body, and drop any reference to `X-Hub-Signature` from the receiver.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries · https://docs.github.com/en/rest/repos/webhooks

## webhook-insecure-ssl
1. **slug** — `webhook-insecure-ssl`
2. **title** — SSL verification is disabled on the webhook
3. **symptom** — Deliveries succeed, which is exactly why nobody looks. GitHub is not verifying your endpoint's TLS certificate, so a man-in-the-middle can receive your payloads.
4. **mechanism** — `config.insecure_ssl` set to `"1"` tells GitHub to skip certificate verification. It is usually enabled once to get past a self-signed cert during setup and never turned back off.
5. **detect** — `GET /repos/{owner}/{repo}/hooks` → `config.insecure_ssl`. A value of `"1"` (or `1`) is the finding; `"0"` is correct. Check `config.url` at the same time — an `http://` scheme is worse and is covered separately below.
6. **repair** — Install a valid certificate on the receiver and set `insecure_ssl` back to `"0"`. Rotate the webhook secret afterwards, since payloads may have been observable.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/rest/repos/webhooks · https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/troubleshooting-webhooks

## webhook-http-url
1. **slug** — `webhook-http-url`
2. **title** — The webhook posts to a plain http:// URL
3. **symptom** — Working deliveries over an unencrypted channel. Payloads — including private repository contents, branch names, issue bodies — cross the network in the clear, along with the signature header.
4. **mechanism** — GitHub will deliver to `http://` if configured to. Nothing warns about it, and a signature does not provide confidentiality; it only proves origin.
5. **detect** — `GET /repos/{owner}/{repo}/hooks` and `GET /orgs/{org}/hooks` → `config.url`. Flag any value whose scheme is `http`. Also flag hostnames that resolve to private ranges or to a host that no longer exists — the delivery log will confirm with connection errors.
6. **repair** — Move the receiver behind HTTPS and update `config.url`, then rotate the webhook secret because it was used to sign payloads over an observable channel.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/rest/repos/webhooks · https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries

## webhook-deliveries-failing
1. **slug** — `webhook-deliveries-failing`
2. **title** — Deliveries are failing and nobody is reading the log
3. **symptom** — Events appear to be "missed". The receiver's own logs are empty because the request never got a valid response, and GitHub's delivery log — which nobody checks — is full of 5xx.
4. **mechanism** — GitHub records every delivery attempt with the response it got. A receiver that returns 500 because of an unhandled event type, or 401 because of a signature mismatch, produces a delivery record that is invisible from the receiver's side.
5. **detect** — `GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries?per_page=100` → each record has `status`, `status_code`, `event`, `action`, `duration`, `delivered_at`, `redelivery`. Anything with `status` not equal to `"OK"` is a failure. `GET /repos/{owner}/{repo}/hooks/{hook_id}` also carries `last_response` with `code`, `status` and `message` for the most recent attempt — one call, immediate verdict.
6. **repair** — Fix the receiver for the specific `status_code` seen, then replay the lost events with `POST /repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id}/attempts`. Add monitoring that reads `last_response.code` on a schedule so this is never discovered by a user.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries · https://docs.github.com/en/rest/repos/webhooks

## webhook-timeout-10s
1. **slug** — `webhook-timeout-10s`
2. **title** — The receiver takes longer than 10 seconds and times out
3. **symptom** — Delivery records with `status: "timed out"` and a `duration` at or near 10 seconds. The receiver's logs show the work *completing* successfully, some seconds later.
4. **mechanism** — GitHub gives a webhook receiver 10 seconds to respond and records anything slower as a failure. A handler that does the real work synchronously — cloning a repo, calling three other APIs, running a build — will exceed it as soon as the repository grows.
5. **detect** — `GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries` → filter on `status == "timed out"`, and read the `duration` field across all recent deliveries. A `duration` distribution creeping toward 10000ms predicts the failure before it happens.
6. **repair** — Acknowledge with `202` immediately after verifying the signature, push the payload onto a queue, and do the work asynchronously. Make the handler's synchronous path do nothing but validate and enqueue.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/troubleshooting-webhooks · https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries

## webhook-event-not-subscribed
1. **slug** — `webhook-event-not-subscribed`
2. **title** — The hook is not subscribed to the event you are waiting for
3. **symptom** — A handler that was written, tested and deployed never runs in production. The delivery log has entries, just never for that event.
4. **mechanism** — A hook delivers only the events listed in its `events` array. Adding a handler for `release` or `workflow_job` does nothing unless the hook subscribes to it, and there is no error for an unsubscribed event — the delivery simply never exists.
5. **detect** — `GET /repos/{owner}/{repo}/hooks` → `events` array. Diff it against the set of events your handlers implement. `GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries` → collect the distinct `event` values actually seen in the retention window; an event in your handler set that never appears is the finding.
6. **repair** — Update the hook's `events` list to include the missing event names exactly as GitHub spells them (`pull_request`, not `pull-request`), and prefer explicit lists over `["*"]`.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/troubleshooting-webhooks · https://docs.github.com/en/webhooks/webhook-events-and-payloads

## webhook-wildcard-events
1. **slug** — `webhook-wildcard-events`
2. **title** — The hook subscribes to every event with a wildcard
3. **symptom** — Enormous delivery volume, a receiver that spends most of its time discarding payloads it does not care about, and a signature-verification cost paid on every push in the org.
4. **mechanism** — Setting `events: ["*"]` subscribes to all current *and future* event types. Each new event GitHub ships is silently added to your firehose, and large payloads (`push` on a monorepo, `status` on a busy CI setup) dominate.
5. **detect** — `GET /repos/{owner}/{repo}/hooks` → `events` containing `"*"`. Quantify with `GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries?per_page=100`: count deliveries by `event` and report the fraction of volume from events your handlers do not implement.
6. **repair** — Replace `["*"]` with the explicit list of events the receiver handles. This reduces delivery volume, receiver cost and the amount of repository data leaving GitHub.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/rest/repos/webhooks · https://docs.github.com/en/webhooks/webhook-events-and-payloads

## webhook-content-type-mismatch
1. **slug** — `webhook-content-type-mismatch`
2. **title** — The hook sends form-encoded bodies to a JSON receiver
3. **symptom** — The receiver returns 400 or 500 on every delivery with a JSON parse error, or parses an empty object and does nothing. Delivery records show a non-OK `status`.
4. **mechanism** — `config.content_type` defaults to `application/x-www-form-urlencoded`, which wraps the JSON in a `payload=` form field. A receiver written for `application/json` sees a form body and fails. It also breaks naive signature verification, because the HMAC is over the raw form body, not the inner JSON.
5. **detect** — `GET /repos/{owner}/{repo}/hooks` → `config.content_type`. A value of `form` (or the absence of `json`) on a hook whose receiver expects JSON is the finding. Confirm with `GET /repos/{owner}/{repo}/hooks/{hook_id}/deliveries/{delivery_id}` → `request.headers["content-type"]` and the shape of `request.payload`.
6. **repair** — Set `config.content_type` to `json` on the hook, and make the receiver compute the HMAC over the raw request bytes it received rather than over a re-serialised object.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/rest/repos/webhooks · https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries

## webhook-ip-allowlist-drift
1. **slug** — `webhook-ip-allowlist-drift`
2. **title** — A firewall allow-list no longer matches GitHub's hook IP ranges
3. **symptom** — Deliveries start failing with connection errors or timeouts from a subset of GitHub's senders. It looks intermittent because only some source IPs are blocked.
4. **mechanism** — GitHub publishes the CIDR ranges it delivers webhooks from, and those ranges change. A firewall or WAF allow-list copied once from the docs goes stale, blocking new ranges while the old ones still work.
5. **detect** — `GET /meta` → the `hooks` array is the authoritative current list of webhook source CIDRs (the response also carries `api`, `web`, `git`, `packages`, `actions`, `dependabot`). Diff it against the ranges configured in your firewall. Corroborate with delivery records showing connection failures.
6. **repair** — Automate the allow-list from `GET /meta` on a schedule rather than maintaining it by hand, and alert when the published set changes.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/webhooks/testing-and-troubleshooting-webhooks/troubleshooting-webhooks · https://docs.github.com/en/rest/meta/meta

## duplicate-webhooks
1. **slug** — `duplicate-webhooks`
2. **title** — The same URL is registered on both the org and the repo
3. **symptom** — Every event is processed twice. Bots comment twice, notifications double up, idempotency bugs that were dormant for a year start firing.
4. **mechanism** — Organization webhooks and repository webhooks are independent. A hook created at the org level for convenience, plus a per-repo hook created earlier by a script, both deliver the same events to the same URL. A GitHub App webhook can add a third copy.
5. **detect** — Collect `config.url` from `GET /orgs/{org}/hooks`, from `GET /repos/{owner}/{repo}/hooks` for every repository, and from `GET /app/hook/config`. Any URL appearing more than once for the same repository's events is the finding. Confirm by matching `delivered_at` and the `X-GitHub-Delivery` guid across delivery logs.
6. **repair** — Keep exactly one source of truth — usually the org-level hook or the App — and delete the redundant hooks. Independently, make the receiver idempotent on the `X-GitHub-Delivery` guid so a duplicate is harmless.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/rest/orgs/webhooks · https://docs.github.com/en/rest/repos/webhooks

## webhook-secret-never-rotated
1. **slug** — `webhook-secret-never-rotated`
2. **title** — The webhook secret has not changed in years
3. **symptom** — Nothing visible. The secret that authenticates every event has been in the same config file since the integration was built, surviving every staff change.
4. **mechanism** — Webhook secrets never expire and GitHub never prompts to rotate them. A secret set once is shared with every engineer who has ever read the receiver's configuration.
5. **detect** — `GET /repos/{owner}/{repo}/hooks` → `updated_at` on the hook. It changes whenever the hook config is modified, so a very old `updated_at` combined with a masked `config.secret` is strong evidence the secret has never been rotated. The secret value itself is never readable (blind spot); age is the proxy.
6. **repair** — Rotate on a schedule, using a receiver that accepts either the old or the new secret during a short overlap window, then update the hook and drop the old value.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/webhooks/using-webhooks/validating-webhook-deliveries · https://docs.github.com/en/rest/repos/webhooks

## app-webhook-url-unset
1. **slug** — `app-webhook-url-unset`
2. **title** — The GitHub App has no webhook URL configured
3. **symptom** — An App that reacts to events does nothing. There are no failed deliveries because there are no deliveries — the App has nowhere to send them.
4. **mechanism** — A GitHub App's webhook is configured on the App itself, not per installation, and it can be left blank or pointed at a placeholder from a tutorial. It can also be disabled independently of the App's event subscriptions.
5. **detect** — `GET /app/hook/config` with the App JWT → `url`, `content_type`, `insecure_ssl`, and `secret` (masked when set). An empty or obviously placeholder `url` (`smee.io`, `localhost`, `example.com`) is the finding. `GET /app/hook/deliveries` returning an empty list corroborates.
6. **repair** — Set the App's webhook URL to the production receiver, set a secret, set `content_type` to `json`, and confirm with `GET /app/hook/deliveries` that events start arriving.
7. **category** — Webhooks
8. **sources** — https://docs.github.com/en/rest/apps/webhooks · https://docs.github.com/en/webhooks/using-webhooks/handling-failed-webhook-deliveries

---

# Pagination and queries

## link-header-not-followed
1. **slug** — `link-header-not-followed`
2. **title** — Only the first page of results is ever read
3. **symptom** — A repository with 340 open pull requests reports 30. An audit says "no stale branches" because it only looked at the first 30 branches. Nothing errors.
4. **mechanism** — REST list endpoints paginate and advertise the next page in the `Link` header. A client that reads the JSON array and stops gets a truthful first page and a false total. This is the single most common silent GitHub API bug.
5. **detect** — Call the list endpoint the integration uses with `per_page=1` and read the `Link` header: `<...&page=2>; rel="next", <...&page=N>; rel="last"`. The `page=N` in `rel="last"` is the true item count. Compare it against what the integration reports. Where `rel="last"` is absent, follow `rel="next"` until it disappears.
6. **repair** — Follow `rel="next"` until it is absent — never construct page URLs by hand, since GitHub may change their format. In Octokit use `octokit.paginate()`; in PyGithub iterate the `PaginatedList` rather than slicing it.
7. **category** — Pagination and queries
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api · https://github.com/octokit/plugin-paginate-rest.js · https://stackoverflow.com/questions/8735792/how-to-parse-link-header-from-github-api

## per-page-default-30
1. **slug** — `per-page-default-30`
2. **title** — per_page is unset so every list costs 3.3x more requests
3. **symptom** — Quota drains far faster than expected. Fetching 3,000 issues takes 100 requests instead of 30, and the job runs three times longer.
4. **mechanism** — Most list endpoints default to 30 items per page. Raising `per_page` to 100 is free — it costs the same one request — but the default is what you get if you do not ask.
5. **detect** — Call the endpoint without `per_page` and count the items in the response array; 30 is the tell. Compare the `rel="last"` page number with `per_page=30` versus `per_page=100` to show the request-count difference directly.
6. **repair** — Set `per_page=100` on every list request. For a job that reads N items this reduces request count by roughly 70% and proportionally reduces rate-limit pressure.
7. **category** — Pagination and queries
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api · https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api

## per-page-over-100-clamped
1. **slug** — `per-page-over-100-clamped`
2. **title** — per_page above 100 is silently reduced, not rejected
3. **symptom** — A client asks for `per_page=500`, receives 100 items, assumes that is everything, and stops. No error, no warning — a quiet truncation to a fifth of the data.
4. **mechanism** — GitHub caps `per_page` at 100 and, rather than returning a 422, reduces the value silently. Code that trusts its own page size to decide "was this the last page?" is wrong by a factor of five.
5. **detect** — Request `per_page=500` on a collection known to hold more than 100 items and count the returned array — exactly 100 with a `Link` header carrying `rel="next"` proves both the clamp and the presence of more data.
6. **repair** — Set `per_page=100` explicitly and decide "last page" from the absence of `rel="next"` in the `Link` header, never from the returned item count.
7. **category** — Pagination and queries
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api · https://stackoverflow.com/questions/48371313/github-api-pagination-limit

## rel-last-absent
1. **slug** — `rel-last-absent`
2. **title** — The Link header has no rel="last" and the loop terminates early
3. **symptom** — A pager that reads `rel="last"` to compute a page count throws or silently returns page 1 on certain endpoints — commonly high-volume or cursor-based ones.
4. **mechanism** — GitHub only includes `rel="last"` when it can calculate the final page. On some endpoints it cannot, so the header contains only `rel="next"` (and `rel="first"`/`rel="prev"` where applicable). Clients that require `last` to exist break.
5. **detect** — Call the endpoint and parse the `Link` header's `rel` values. The presence of `rel="next"` with no `rel="last"` is the finding, and it tells you the endpoint must be walked rather than indexed.
6. **repair** — Drive pagination off `rel="next"` alone, treating its absence as the terminating condition. Never require `rel="last"`, and never use it to pre-compute a progress bar you then rely on for correctness.
7. **category** — Pagination and queries
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api · https://github.com/octokit/plugin-paginate-rest.js

## endpoint-ignores-page-param
1. **slug** — `endpoint-ignores-page-param`
2. **title** — Some endpoints ignore page and per_page entirely
3. **symptom** — Passing `page=2` returns the same items as `page=1`. A pager loops forever, or collects the first page N times and reports duplicates as new records.
4. **mechanism** — A minority of endpoints do not support offset pagination at all — repository activity and some newer list endpoints use `before`/`after` cursors, and a few accept neither. The offset parameters are ignored rather than rejected, so the loop never terminates naturally.
5. **detect** — Fetch `page=1` and `page=2` and compare the `id` (or `node_id`) of the first item. Identical ids with a 200 on both calls means offset pagination is not supported. Confirm by checking whether the `Link` header uses `after=`/`before=` cursors instead of `page=`.
6. **repair** — Switch to the cursor parameters the endpoint's own `Link` header uses, or to the GraphQL equivalent with `after: $cursor` and `pageInfo { hasNextPage endCursor }`. Do not synthesise page numbers.
7. **category** — Pagination and queries
8. **sources** — https://github.com/orgs/community/discussions/73014 · https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api

## search-1000-result-cap
1. **slug** — `search-1000-result-cap`
2. **title** — Search returns at most 1,000 results whatever total_count says
3. **symptom** — `total_count: 24831` in the response, but paging past page 10 at `per_page=100` returns `422 Validation Failed` with `"Only the first 1000 search results are available"`. The count is real; the results are not reachable.
4. **mechanism** — The Search API caps retrievable results at 1,000 per query regardless of the reported total. `total_count` describes the match set, not what you can page through.
5. **detect** — `GET /search/issues?q=...&per_page=100&page=11` → the 422 with the 1000-results message is definitive. Non-destructively: read `total_count` from page 1 and flag any value above 1000 as unreachable in full.
6. **repair** — Partition the query so each slice returns under 1,000 — by `created:` date ranges, by `repo:`, by label — and union the slices client-side. Where the goal is a complete inventory rather than a search, use the corresponding list endpoint, which has no such cap.
7. **category** — Pagination and queries
8. **sources** — https://stackoverflow.com/questions/37602893/github-search-limit-results · https://stackoverflow.com/questions/74869773/how-do-i-get-all-1000-results-using-the-github-search-api · https://docs.github.com/en/rest/search/search

## search-incomplete-results
1. **slug** — `search-incomplete-results`
2. **title** — The search response sets incomplete_results and nobody checks it
3. **symptom** — The same search returns different counts on different runs. Results are missing with no error at all — status 200, valid JSON, fewer items.
4. **mechanism** — Search queries have a server-side timeout. When it fires, GitHub returns whatever it found so far with `incomplete_results: true` rather than failing. Clients that read `items` and ignore the flag treat a partial answer as a complete one.
5. **detect** — Any `GET /search/*` response → the top-level `incomplete_results` boolean. `true` is the finding. Track it across repeated runs to show the flakiness; it correlates with broad, expensive queries.
6. **repair** — Treat `incomplete_results: true` as a retryable failure, not a result. Narrow the query (add `repo:`, `org:` or a date range) so it completes inside the timeout, and never cache a response that carried the flag.
7. **category** — Pagination and queries
8. **sources** — https://docs.github.com/en/rest/search/search · https://stackoverflow.com/questions/67851001/how-get-all-results-from-github-search-api

## compare-250-commit-cap
1. **slug** — `compare-250-commit-cap`
2. **title** — The compare endpoint stops at 250 commits without paging
3. **symptom** — A release-notes generator that diffs two tags produces a plausible but wrong changelog for large releases: exactly 250 commits, and the "oldest" commit is not the real merge base.
4. **mechanism** — `GET /repos/{owner}/{repo}/compare/{base}...{head}` returns at most 250 commits when called without pagination parameters, and the last commit in that unpaginated list is the most recent of the entire comparison rather than the 250th. Paginating changes the semantics: `files` is returned only on the first page, and the last commit of a page is not the newest overall.
5. **detect** — Call the endpoint and compare `total_commits` (the true count) against `commits.length` (what you received). Any case where `total_commits > commits.length` is silent truncation. If `total_commits > 250`, the unpaginated call cannot be correct.
6. **repair** — Read `total_commits` first; when it exceeds the page size, paginate with `per_page`/`page` and collect `files` from the first page only, or switch to `GET /repos/{owner}/{repo}/commits?sha=...&since=...` which paginates conventionally.
7. **category** — Pagination and queries
8. **sources** — https://docs.github.com/en/rest/commits/commits · https://github.com/orgs/community/discussions/33505 · https://github.com/PyGithub/PyGithub/issues/631

## pr-files-and-commits-caps
1. **slug** — `pr-files-and-commits-caps`
2. **title** — A pull request's files and commits lists are capped
3. **symptom** — A PR-review bot silently ignores changes in a large pull request. It reports "3 files changed" on a PR that changed 900, or misses the commit that introduced the bug.
4. **mechanism** — `GET /repos/{owner}/{repo}/pulls/{n}/files` paginates at 30 per page by default and is capped at 3,000 files total; `.../commits` paginates at 250. Clients that read one page, or that assume no cap, get a truncated diff with no error.
5. **detect** — Compare the PR object's own counters against what you collected: `GET /repos/{owner}/{repo}/pulls/{n}` → `changed_files`, `commits`, `additions`, `deletions`. If `changed_files` exceeds the number of entries you paginated, you truncated. A `changed_files` above 3,000 is unreachable in full through this endpoint.
6. **repair** — Paginate with `per_page=100` and validate the collected count against `changed_files` and `commits` on the PR object, failing loudly on a mismatch. For very large PRs, fetch the diff via the `application/vnd.github.diff` media type instead.
7. **category** — Pagination and queries
8. **sources** — https://docs.github.com/en/rest/pulls/pulls · https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api

## request-timeout-502
1. **slug** — `request-timeout-502`
2. **title** — Expensive requests are killed at 10 seconds with a 502
3. **symptom** — `502 Bad Gateway` or `504` with a "Server Error" body on specific heavy calls — a diff of a huge merge, a list on an enormous repository — while everything else is fine.
4. **mechanism** — GitHub terminates any API request it cannot serve within about 10 seconds. The failure is a gateway error rather than a 4xx, so retry logic treats it as transient and retries the same expensive call, which times out again.
5. **detect** — Reproduce the specific call and time it; a repeatable 502/504 at ~10 seconds on one path while `GET /rate_limit` is instant isolates the endpoint rather than the network. Record the `x-github-request-id` from the failing response — it is what support will ask for.
6. **repair** — Make the request cheaper rather than retrying it: reduce `per_page`, narrow the date range or path filter, split a comparison into smaller ranges, or move to a GraphQL query that fetches only the fields you need.
7. **category** — Pagination and queries
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api · https://docs.github.com/en/graphql/overview/resource-limitations

## unstable-sort-duplicates
1. **slug** — `unstable-sort-duplicates`
2. **title** — Items shift between pages and the walk skips records
3. **symptom** — A nightly sync misses issues at random and occasionally processes one twice. The counts never quite reconcile and nobody can reproduce it on demand.
4. **mechanism** — Offset pagination over a collection that is being written to is not stable. Sorting by `updated` (the default on issues) means an item touched mid-walk moves to page 1 and shifts everything after it, so the record that was at the page boundary is skipped.
5. **detect** — Walk the collection twice with the default sort and diff the id sets — a non-empty symmetric difference on a quiet repository is the finding. Confirm the risk from the endpoint's parameters: any list defaulting to `sort=updated` is exposed.
6. **repair** — Sort by something immutable — `sort=created&direction=asc` — or use `since=<timestamp>` for incremental syncs and deduplicate on `id` client-side. For large walks, prefer GraphQL cursors, which are stable against insertion.
7. **category** — Pagination and queries
8. **sources** — https://docs.github.com/en/rest/issues/issues · https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api

## repo-renamed-301-redirect
1. **slug** — `repo-renamed-301-redirect`
2. **title** — The repository was renamed and requests 301 to a new URL
3. **symptom** — Requests return `301 Moved Permanently`, and a client that does not follow redirects sees an empty body and a falsy result. A client that follows them works but keeps paying an extra round trip on every call, forever.
4. **mechanism** — Renaming or transferring a repository leaves a redirect at the old path. GitHub documents that a `301` means you should update your code to the `location` URL, while `302`/`307` should just be followed.
5. **detect** — `GET /repos/{owner}/{repo}` on the configured name and read the status plus `location`. Alternatively follow the redirect and compare `full_name` in the body against the name you asked for — a mismatch means the stored name is stale. `GET /repos/{owner}/{repo}` also returns `node_id`, which is stable across renames and makes a better key.
6. **repair** — Update the stored owner/repo to the value in `location` (or `full_name`), and key persistent state on the repository `id`/`node_id` so future renames are invisible to the integration.
7. **category** — Pagination and queries
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/best-practices-for-using-the-rest-api · https://docs.github.com/en/rest/repos/repos

---

# GraphQL

## graphql-200-with-errors
1. **slug** — `graphql-200-with-errors`
2. **title** — GraphQL returns HTTP 200 with an errors array and null data
3. **symptom** — The client's `if (response.ok)` check passes, `data.repository` is `null`, and the code crashes downstream on `Cannot read property 'name' of null` — or worse, records "0 pull requests" as a fact.
4. **mechanism** — GraphQL reports application errors in the response body, not the status line. A query that hit a permission problem, a missing resource or a rate limit still returns `200 OK` with `{"data": {...}, "errors": [{"type": "...", "message": "..."}]}`. HTTP-status-based error handling sees success.
5. **detect** — `POST /graphql` with your query and inspect the top-level `errors` array on a 200 response. The `type` field classifies the failure: `NOT_FOUND`, `FORBIDDEN`, `RATE_LIMITED`, `MAX_NODE_LIMIT_EXCEEDED`, `INTERNAL`. Any non-empty `errors` array is the finding, even alongside partial `data`.
6. **repair** — Check `body.errors` before touching `body.data` on every GraphQL response, and map each `type` to a distinct behaviour: `RATE_LIMITED` waits, `FORBIDDEN` alerts, `NOT_FOUND` marks the record missing. Never treat a 200 as success.
7. **category** — GraphQL
8. **sources** — https://docs.github.com/en/graphql/guides/using-the-graphql-api · https://stackoverflow.com/questions/45390076/valid-github-api-v4-query-keeps-returning-error-problems-parsing-json

## graphql-partial-data-nulls
1. **slug** — `graphql-partial-data-nulls`
2. **title** — Some fields come back null because of per-field permissions
3. **symptom** — A query over 50 repositories returns 50 objects, but eight of them have `null` in place of the private fields. Aggregations quietly under-count and no exception is thrown.
4. **mechanism** — GraphQL resolves each field independently. A field the token cannot see resolves to `null` and adds an entry to `errors` with `type: "FORBIDDEN"` and a `path`, while the rest of the response succeeds. The response is genuinely partial by design.
5. **detect** — On the 200 response, walk `errors[].path` — it points at the exact field that was nulled — and count nulls in the result set. A read-only prober can run the integration's own query shape against a known repository and report how many of the requested fields resolved.
6. **repair** — Handle partial responses explicitly: log `errors[].path`, treat nulled fields as unknown rather than zero, and widen the token's permissions if the fields are genuinely needed. Never aggregate over a response whose `errors` array is non-empty without saying so.
7. **category** — GraphQL
8. **sources** — https://docs.github.com/en/graphql/guides/using-the-graphql-api · https://stackoverflow.com/questions/76333420/error-message-resource-not-accessible-by-personal-access-token-when-trying-to

## graphql-rate-limited
1. **slug** — `graphql-rate-limited`
2. **title** — GraphQL points run out in a bucket separate from REST
3. **symptom** — Every GraphQL call returns `200` with `errors[0].type: "RATE_LIMITED"` and `"API rate limit exceeded"`, while REST calls with the same token still work perfectly.
4. **mechanism** — GraphQL is billed in points from its own hourly bucket: 5,000 points/hour for a user token, 1,000 for an Actions `GITHUB_TOKEN`, 10,000 on Enterprise Cloud. The REST `core` bucket is untouched, so a REST-based health check reports green.
5. **detect** — `GET /rate_limit` → `resources.graphql.limit`, `.remaining`, `.used`, `.reset` — free, and it covers GraphQL. Or query it in-band: `{ rateLimit { limit cost remaining resetAt used nodeCount } }`, which itself costs one point.
6. **repair** — Include `rateLimit { cost remaining }` in your real queries so every response reports its own price, and throttle on `remaining` rather than discovering exhaustion. Reduce cost by requesting fewer connections per query.
7. **category** — GraphQL
8. **sources** — https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api · https://docs.github.com/en/rest/rate-limit/rate-limit

## graphql-node-limit-exceeded
1. **slug** — `graphql-node-limit-exceeded`
2. **title** — A nested query requests more than 500,000 nodes
3. **symptom** — The query is rejected with an error whose `type` is `MAX_NODE_LIMIT_EXCEEDED`, or it returns partial results with a resource-limits error. It worked in development against a small org.
4. **mechanism** — Node count multiplies through nesting: `first: 100` repositories each with `first: 100` pull requests each with `first: 100` comments is 100 + 10,000 + 1,000,000 nodes, over the 500,000 cap. The cost is computed from the *requested* `first`/`last` values, not from what actually exists, so a small org still fails.
5. **detect** — Run the query and read `rateLimit { nodeCount cost }` in the same document — `nodeCount` is the computed node total for that call. Compare against 500,000. On rejection, the `errors[].type` names the limit directly.
6. **repair** — Reduce the `first` values at the deepest levels and paginate those connections separately with `pageInfo { hasNextPage endCursor }`, rather than requesting one enormous tree. Fetching 100 repos × 10 PRs and paging PRs per repo costs far fewer nodes than 100 × 100.
7. **category** — GraphQL
8. **sources** — https://docs.github.com/en/graphql/overview/resource-limitations · https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api

## graphql-first-over-100
1. **slug** — `graphql-first-over-100`
2. **title** — A connection asks for first: 500 and is rejected
3. **symptom** — `errors[0].message` reads roughly `"Argument 'first' on Field 'issues' has an invalid value (500). Expected type 'Int'."` or an explicit "must be between 1 and 100". The query never runs.
4. **mechanism** — Every GraphQL connection caps `first` and `last` at 100. Unlike REST's silent clamp of `per_page`, GraphQL rejects the query outright, which is at least honest but breaks code ported straight from a REST client.
5. **detect** — Submit the query and read the `errors` array; the message names the offending argument and field. Statically, scanning your query documents for `first:` or `last:` values above 100 finds them without spending a point.
6. **repair** — Set `first: 100` and paginate with `after: $cursor`, terminating on `pageInfo.hasNextPage == false`. Do not try to raise the ceiling; it is not adjustable.
7. **category** — GraphQL
8. **sources** — https://docs.github.com/en/graphql/overview/resource-limitations · https://stackoverflow.com/questions/49237159/display-more-than-100-entries-through-graphql-api

## graphql-nested-pagination-ignored
1. **slug** — `graphql-nested-pagination-ignored`
2. **title** — Only the outer connection is paginated, so inner data truncates
3. **symptom** — A query over repositories with nested pull requests pages correctly through repositories but returns only the first 100 PRs for each — quietly, with no error, and with a `totalCount` that proves there were more.
4. **mechanism** — Each connection in a GraphQL query has its own cursor. Paginating the outer connection does nothing for the inner ones; every new outer page restarts the inner connections at the beginning. Nested pagination requires a second loop per parent.
5. **detect** — Ask each nested connection for `totalCount` alongside `nodes` and `pageInfo { hasNextPage }`. Any node where `totalCount` exceeds the number of `nodes` returned, or where `hasNextPage` is `true` and you never followed it, is silent truncation.
6. **repair** — For each parent whose inner `pageInfo.hasNextPage` is true, issue follow-up queries scoped to that parent with `after: endCursor`. Structure the client as an outer walk plus a per-parent inner walk rather than one query.
7. **category** — GraphQL
8. **sources** — https://stackoverflow.com/questions/48116781/github-api-v4-how-can-i-traverse-with-pagination-graphql · https://docs.github.com/en/graphql/guides/using-pagination-in-the-graphql-api

## graphql-cost-not-measured
1. **slug** — `graphql-cost-not-measured`
2. **title** — Nobody knows what the query costs until the budget is gone
3. **symptom** — GraphQL quota disappears in unpredictable jumps. Adding one nested field to a dashboard query quietly multiplied its price and nobody noticed until the hourly budget ran out mid-afternoon.
4. **mechanism** — A GraphQL query's point cost is computed from the number of unique connections it could traverse — roughly the sum of `first`/`last` across connections, divided by 100 and rounded, minimum 1. It is not proportional to the data returned, so a query that returns almost nothing can still be expensive.
5. **detect** — Add `rateLimit { cost remaining nodeCount limit resetAt }` to the query itself; the response then reports its own price on every call. Baseline it: run the query once, record `cost`, and multiply by the expected call rate to project hourly consumption against `limit`.
6. **repair** — Track `cost` per query shape in your logs, alert when a deploy changes it, and split expensive multi-connection queries into cheaper focused ones. Where a query is called on a schedule, budget it explicitly against 5,000 points/hour.
7. **category** — GraphQL
8. **sources** — https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api · https://docs.github.com/en/graphql/overview/resource-limitations

## graphql-timeout-point-penalty
1. **slug** — `graphql-timeout-point-penalty`
2. **title** — A slow GraphQL query is killed and charged extra points
3. **symptom** — `502` or `504` from `/graphql` with a message about not being able to respond in time — and the hourly point budget drops by more than the query's normal cost.
4. **mechanism** — GitHub terminates GraphQL requests that take longer than 10 seconds, and explicitly deducts **additional** points from the primary rate limit as a penalty. Retrying the same heavy query therefore costs quota twice while returning nothing.
5. **detect** — Read `resources.graphql.used` from `GET /rate_limit` immediately before and after the failing query; the delta exceeding the query's normal `cost` demonstrates the penalty. The 502/504 status plus the timing (~10s) identifies the timeout itself.
6. **repair** — Break the query into smaller ones with lower `first` values and fewer nested connections, and do not blindly retry a timed-out query — retrying the identical document reproduces the timeout and the penalty.
7. **category** — GraphQL
8. **sources** — https://docs.github.com/en/graphql/overview/resource-limitations · https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api

## graphql-mutation-secondary-cost
1. **slug** — `graphql-mutation-secondary-cost`
2. **title** — Mutations cost five times more against the secondary limit
3. **symptom** — A bulk-mutation script trips `"You have exceeded a secondary rate limit"` at roughly a fifth of the request rate that read queries tolerate.
4. **mechanism** — For the secondary limit GitHub counts a GraphQL query without mutations as 1 point and a query containing a mutation as 5, against a ceiling of 2,000 points per minute. A mutation loop therefore hits the wall five times faster than the equivalent read loop.
5. **detect** — Cannot be pre-measured (secondary limits are a documented blind spot). Detect after the fact: 403/429 responses containing "secondary rate limit" from `/graphql` while `resources.graphql.remaining` from `GET /rate_limit` is still healthy proves it is the secondary limit and not the point budget.
6. **repair** — Rate-limit mutations to well under 400 per minute, serialise them rather than fanning out, and pause at least one second between them. Honour `retry-after` when it appears.
7. **category** — GraphQL
8. **sources** — https://docs.github.com/en/graphql/overview/resource-limitations · https://docs.github.com/en/graphql/overview/rate-limits-and-node-limits-for-the-graphql-api

## graphql-search-same-1000-cap
1. **slug** — `graphql-search-same-1000-cap`
2. **title** — GraphQL search hits the same 1,000-result ceiling as REST
3. **symptom** — A migration from REST search to GraphQL search, undertaken specifically to escape the 1,000-result cap, hits exactly the same wall — `issueCount` reports 18,000 and pagination stops after 1,000 nodes.
4. **mechanism** — GraphQL's `search` connection is backed by the same search index and inherits the same retrievable-result ceiling. Changing protocol does not change the index's limit.
5. **detect** — Query `search(query: $q, type: ISSUE, first: 100) { issueCount pageInfo { hasNextPage endCursor } }` and walk the cursor. `hasNextPage` turning false while `issueCount` is far larger is the finding, and it is visible after ten pages.
6. **repair** — Partition the search into date-bounded or repo-bounded slices under 1,000 results each and union them, exactly as with REST search. For complete inventories use the typed connections (`repository.issues`, `organization.repositories`), which paginate without a ceiling.
7. **category** — GraphQL
8. **sources** — https://docs.github.com/en/graphql/reference/queries · https://stackoverflow.com/questions/49344444/github-graphql-search-with-filtering

## graphql-id-vs-databaseid
1. **slug** — `graphql-id-vs-databaseid`
2. **title** — GraphQL node ids are stored where REST ids are expected
3. **symptom** — Records saved by the GraphQL path never match records saved by the REST path. A join produces zero rows; duplicates accumulate because `MDU6SXNzdWUx` and `1` are treated as different entities.
4. **mechanism** — GraphQL's `id` is an opaque global node ID (a base64-ish string), while REST's `id` is a numeric database ID. Both appear as "the id" in their own responses. GraphQL exposes the numeric one as `databaseId`, and REST exposes the global one as `node_id`, but neither is the default field.
5. **detect** — Fetch the same object both ways — `GET /repos/{owner}/{repo}/issues/{n}` → `id` and `node_id`; GraphQL `issue { id databaseId }` — and show that REST `node_id` equals GraphQL `id`, and REST `id` equals GraphQL `databaseId`. If your store holds a mix of both shapes for one entity type, that is the finding.
6. **repair** — Pick one identifier per entity and store it everywhere: request `databaseId` in GraphQL if the store is keyed numerically, or read `node_id` from REST if it is keyed by global ID. Migrate existing rows rather than joining on two key spaces.
7. **category** — GraphQL
8. **sources** — https://docs.github.com/en/graphql/guides/using-global-node-ids · https://docs.github.com/en/graphql/reference/interfaces

---

# Permissions and access

## 404-masking-403
1. **slug** — `404-masking-403`
2. **title** — A permission error is disguised as 404 Not Found
3. **symptom** — `404 {"message":"Not Found"}` on a repository you are looking at in a browser tab. The integration reports "repository does not exist" and someone spends an hour checking the spelling.
4. **mechanism** — GitHub deliberately returns 404 instead of 403 for private resources the token cannot see, to avoid confirming that a private repository exists. Missing scope, missing App installation and genuinely-deleted repository are therefore indistinguishable from the status code alone.
5. **detect** — Triangulate with three cheap reads. `GET /user` → does the token authenticate at all. `GET /repos/{owner}/{repo}` with a token known to have access → does the repository exist. `x-oauth-scopes` on any response → does the token carry `repo`. If the repo exists for one token and 404s for another, it is permission, not existence. For an App, `GET /repos/{owner}/{repo}/installation` settles it.
6. **repair** — Print all three signals in the diagnosis rather than the raw 404, and fix whichever is wrong: add the `repo` scope, add the repository to the App installation, or correct the name.
7. **category** — Permissions and access
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api · https://stackoverflow.com/questions/60787184/octokit-rest-js-throws-a-httperror-not-found · https://stackoverflow.com/questions/66345646/get-private-repo-branch-via-github-api

## resource-not-accessible-by-pat
1. **slug** — `resource-not-accessible-by-pat`
2. **title** — Resource not accessible by personal access token
3. **symptom** — `403 {"message":"Resource not accessible by personal access token"}` — the fine-grained-token counterpart of the App error, and it appears in GraphQL responses too, as an `errors` entry rather than a status.
4. **mechanism** — Fine-grained PATs carry per-resource permissions, not scopes. A token with `Contents: Read` cannot read issues; one with repository permissions cannot touch organization-level resources. Unlike classic tokens, there is no `x-oauth-scopes` header to inspect, so the token's grants are opaque from the response.
5. **detect** — Call the failing endpoint and read `x-accepted-github-permissions`, which names the required permission in fine-grained terms (e.g. `issues=read`). Confirm the token type from its `github_pat_` prefix and from the *absence* of `x-oauth-scopes` on `GET /user`. Probe individual permissions with cheap reads: `GET /repos/{o}/{r}` for Metadata, `GET /repos/{o}/{r}/issues?per_page=1` for Issues, `GET /repos/{o}/{r}/pulls?per_page=1` for Pull requests.
6. **repair** — Edit the fine-grained token's repository permissions to add exactly what `x-accepted-github-permissions` names, and re-request organization approval if the token targets org resources.
7. **category** — Permissions and access
8. **sources** — https://stackoverflow.com/questions/76333420/error-message-resource-not-accessible-by-personal-access-token-when-trying-to · https://docs.github.com/en/rest/authentication/permissions-required-for-github-apps

## branch-protection-requires-admin
1. **slug** — `branch-protection-requires-admin`
2. **title** — Reading branch protection needs admin and returns 403 without it
3. **symptom** — A compliance script reports "no branch protection" across the whole organization, when in fact every repository is protected. `GET .../protection` returned 403 or 404 and the script treated that as absence.
4. **mechanism** — Branch protection settings are readable only with admin rights on the repository. A read-only auditor token gets `403 {"message":"Must have admin rights to Repository."}` — or a 404 masking the same thing — which is easy to coerce into "not protected".
5. **detect** — `GET /repos/{owner}/{repo}/branches/{branch}/protection` and distinguish three outcomes explicitly: 200 with a protection object (protected), 404 with `{"message":"Branch not protected"}` (genuinely unprotected), 403 with the admin-rights message (unknown — you cannot see). Cross-check `GET /repos/{owner}/{repo}/branches/{branch}` → the `protected` boolean, which is visible without admin and is the honest fallback.
6. **repair** — Never report "unprotected" from a 403. Read the cheap `protected` boolean for coverage, and grant the auditing token repository admin (or an App with `administration: read`) where the detailed rules are genuinely needed.
7. **category** — Permissions and access
8. **sources** — https://docs.github.com/en/rest/branches/branch-protection · https://stackoverflow.com/questions/65348124/in-github-how-can-i-grant-an-app-permissions-to-commit-to-a-branch-with-protecti

## repo-archived-writes-403
1. **slug** — `repo-archived-writes-403`
2. **title** — The repository is archived so every write returns 403
3. **symptom** — Reads work perfectly; every `POST`/`PATCH` returns `403` with a message about the repository being archived. A bot retries forever against a repository that will never accept writes again.
4. **mechanism** — Archiving makes a repository read-only. The API still serves it — which is why reads succeed and the failure looks selective — but rejects all mutations regardless of the token's permissions.
5. **detect** — `GET /repos/{owner}/{repo}` → the `archived` boolean, and `disabled` alongside it. `archived: true` explains every write failure in one field, before any write is attempted. For an org-wide sweep, `GET /orgs/{org}/repos?type=all&per_page=100` returns `archived` per repository.
6. **repair** — Filter archived repositories out of any write-path automation at the top of the loop, and treat `archived: true` as a permanent skip rather than a retryable error. Unarchive only if the repository is genuinely still in use.
7. **category** — Permissions and access
8. **sources** — https://docs.github.com/en/rest/repos/repos · https://docs.github.com/en/repositories/archiving-a-github-repository/archiving-repositories

## repo-disabled
1. **slug** — `repo-disabled`
2. **title** — The repository is disabled and behaves like a ghost
3. **symptom** — Some endpoints 404 and others return partial data for a repository that clearly exists in the organization listing. Nothing explains it.
4. **mechanism** — A repository can be `disabled` — typically for billing or a terms violation, or because it belongs to a suspended account. It stays visible in listings but most sub-resources stop working.
5. **detect** — `GET /repos/{owner}/{repo}` → the `disabled` boolean, alongside `archived`, `private` and `fork`. `disabled: true` is the finding and is worth reporting separately from `archived`, since the remedies are different.
6. **repair** — Resolve the underlying account or billing problem with GitHub, and exclude disabled repositories from automation in the meantime so they do not poison org-wide aggregates.
7. **category** — Permissions and access
8. **sources** — https://docs.github.com/en/rest/repos/repos · https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api

## deploy-key-read-only-assumed-write
1. **slug** — `deploy-key-read-only-assumed-write`
2. **title** — A deploy key is read-only where the workflow expects write
3. **symptom** — Clones and fetches succeed; pushes fail with a permission error from Git rather than from the API, so the diagnosis starts in the wrong place.
4. **mechanism** — Deploy keys carry a `read_only` flag set at creation. Read-only is the safe default and the usual choice, so a deploy key added for CI reads works fine until someone adds a push step.
5. **detect** — `GET /repos/{owner}/{repo}/keys` → each key's `read_only`, `title`, `created_at`, `verified` and `added_by`. A `read_only: true` key on a repository whose automation pushes is the finding. The same listing surfaces long-lived keys nobody remembers: sort by `created_at`.
6. **repair** — Replace the key with one created with `read_only: false` if writes are genuinely required, or better, switch to a GitHub App installation token with `contents: write`, which is scoped, expiring and auditable. Delete deploy keys older than your rotation policy.
7. **category** — Permissions and access
8. **sources** — https://docs.github.com/en/rest/deploy-keys/deploy-keys · https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys

## collaborator-permission-insufficient
1. **slug** — `collaborator-permission-insufficient`
2. **title** — The account behind the token has only read on the repo
3. **symptom** — A token with the `repo` scope still cannot merge, label or comment. The scope is right; the *account's* access to that repository is not.
4. **mechanism** — Scopes bound what a token may do on the user's behalf; they cannot grant access the user does not have. A collaborator with `pull` (read) permission holds a token with the `repo` scope that is nonetheless powerless on that repository.
5. **detect** — `GET /repos/{owner}/{repo}` → the `permissions` object for the authenticated user: `{"admin": false, "maintain": false, "push": false, "triage": false, "pull": true}`. `push: false` explains every write failure. For a specific user, `GET /repos/{owner}/{repo}/collaborators/{username}/permission` returns `permission` and `role_name`.
6. **repair** — Raise the account's repository role to `write`/`maintain` (or add it to a team that has it), rather than widening the token's scopes, which will not help.
7. **category** — Permissions and access
8. **sources** — https://docs.github.com/en/rest/collaborators/collaborators · https://docs.github.com/en/rest/repos/repos

## feature-disabled-endpoint-403
1. **slug** — `feature-disabled-endpoint-403`
2. **title** — Security-feature endpoints 403 because the feature is off
3. **symptom** — `403` on `/secret-scanning/alerts`, `/dependabot/alerts` or `/code-scanning/alerts` with a message that the feature is disabled or not available — even for a token with the right permission.
4. **mechanism** — These endpoints require the corresponding feature to be *enabled on the repository* as well as a permission on the token. Advanced Security features are also plan-dependent, so a private repository on the wrong plan can never serve them.
5. **detect** — `GET /repos/{owner}/{repo}` → `security_and_analysis` reports each feature's `status` as `enabled` or `disabled` (`advanced_security`, `secret_scanning`, `secret_scanning_push_protection`, `dependabot_security_updates`). Read that before calling the alert endpoints; `disabled` explains the 403 without spending a failed call.
6. **repair** — Enable the feature on the repository (or at organization level for all repositories), confirm the plan supports it, and only then grant the token the matching read permission.
7. **category** — Permissions and access
8. **sources** — https://docs.github.com/en/rest/repos/repos · https://docs.github.com/en/rest/secret-scanning/secret-scanning

## fork-vs-upstream-confusion
1. **slug** — `fork-vs-upstream-confusion`
2. **title** — The integration is pointed at a fork, not the upstream repo
3. **symptom** — An audit reports almost no activity, stale branches and zero recent releases for a repository that is demonstrably busy. Everything "works" and every answer is wrong.
4. **mechanism** — A fork is a separate repository with its own issues, releases and branches. A configuration copied from someone's personal fork, or a repository that was forked and then renamed, silently points the integration at the wrong object.
5. **detect** — `GET /repos/{owner}/{repo}` → `fork` boolean, plus `parent.full_name` and `source.full_name` when it is a fork. `fork: true` on a repository the integration treats as canonical is the finding, and `source.full_name` names the repository it should be reading.
6. **repair** — Repoint the configuration at `source.full_name`, and key stored state on the repository `id` so a later fork or rename cannot silently substitute a different object.
7. **category** — Permissions and access
8. **sources** — https://docs.github.com/en/rest/repos/repos · https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/about-forks

## private-repo-visibility-changed
1. **slug** — `private-repo-visibility-changed`
2. **title** — A repository went private and the integration lost access
3. **symptom** — An integration that read a public repository anonymously for years starts returning `404`. Nothing about the integration changed.
4. **mechanism** — Making a repository private removes anonymous access entirely. Any unauthenticated or under-scoped client sees a 404 identical to deletion, and forks of the repository are detached, which compounds the confusion.
5. **detect** — With a token that has access, `GET /repos/{owner}/{repo}` → `private` and `visibility` (`public`, `private`, `internal`). If `private: true` while the integration authenticates anonymously or with a `public_repo`-only token, that is the cause. `GET /rate_limit` showing `core.limit: 60` confirms the client is anonymous.
6. **repair** — Authenticate the integration with a token carrying the `repo` scope (classic) or `Contents: Read` on that repository (fine-grained), or have the repository owner grant the machine account access.
7. **category** — Permissions and access
8. **sources** — https://docs.github.com/en/rest/repos/repos · https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/managing-repository-settings/setting-repository-visibility

## unverified-commit-signature-assumed
1. **slug** — `unverified-commit-signature-assumed`
2. **title** — Commit signature verification is assumed but never read
3. **symptom** — A policy that claims "all commits are signed" is never actually enforced, because the checking script looks at the commit author rather than the verification result.
4. **mechanism** — GitHub verifies signatures server-side and reports the result per commit. A commit's `author` and `committer` fields are attacker-controllable metadata; the `verification` object is not. Scripts routinely check the former.
5. **detect** — `GET /repos/{owner}/{repo}/commits?per_page=100` → each commit's `commit.verification` object with `verified` (boolean), `reason` (e.g. `valid`, `unsigned`, `unknown_key`, `expired_key`, `not_signing_key`) and `signature`. Count `verified: false` and group by `reason`.
6. **repair** — Assert on `commit.verification.verified` rather than on author identity, and where the policy matters, enable the repository rule requiring signed commits so unsigned pushes are rejected rather than merely reported.
7. **category** — Permissions and access
8. **sources** — https://docs.github.com/en/rest/commits/commits · https://docs.github.com/en/authentication/managing-commit-signature-verification/about-commit-signature-verification

## missing-endpoint-404-vs-405
1. **slug** — `missing-endpoint-404-vs-405`
2. **title** — The wrong HTTP verb returns 404 rather than 405
3. **symptom** — `404 Not Found` on a path copied straight from the documentation. The path is right; the method is not, and GitHub does not say so.
4. **mechanism** — GitHub returns `404` rather than `405 Method Not Allowed` for an unsupported verb on a valid path, so a `POST` where the endpoint only accepts `PUT` is indistinguishable from a missing resource.
5. **detect** — Re-issue the same path with `GET` (or with the verb the docs specify). A `GET` that returns 200 while another verb returns 404 identifies a method problem rather than a permission or existence problem. `x-accepted-github-permissions` being absent on the 404 supports the same conclusion.
6. **repair** — Match the verb to the documented one for that endpoint — `PUT` for idempotent set-like operations such as adding a collaborator or starring, `POST` for creation — and print the correct verb in the diagnosis.
7. **category** — Permissions and access
8. **sources** — https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api · https://docs.github.com/en/rest

---

# Organization and SSO

## saml-token-not-authorized
1. **slug** — `saml-token-not-authorized`
2. **title** — The token is not SSO-authorized for the organization
3. **symptom** — `403` with `"Resource protected by organization SAML enforcement. You must grant your OAuth token access to this organization."` — or a bare `404`, since SAML enforcement can also mask as not-found.
4. **mechanism** — Organizations that enforce SAML SSO require each classic PAT and OAuth token to be individually authorized for that organization, in addition to being valid. A brand-new, correctly-scoped token has *no* access to SSO-enforced org resources until a human authorizes it in the browser.
5. **detect** — Call any org-scoped endpoint (`GET /orgs/{org}/repos`) and read the `x-github-sso` response header. On a 403 it contains a URL you must visit to authorize the token; the URL expires after an hour. `GET /orgs/{org}` succeeding while `GET /orgs/{org}/repos` 403s with that header is the signature.
6. **repair** — Visit the URL from `x-github-sso` (or `https://github.com/orgs/ORG/sso`) and authorize the specific token for that organization. Automate nothing here — it is deliberately a human step. For unattended automation, use a GitHub App installation, which is not subject to per-token SSO authorization.
7. **category** — Organization and SSO
8. **sources** — https://docs.github.com/en/enterprise-cloud@latest/authentication/authenticating-with-saml-single-sign-on/authorizing-a-personal-access-token-for-use-with-saml-single-sign-on · https://github.com/cli/cli/issues/2661 · https://docs.github.com/en/enterprise-cloud@latest/rest/overview/authenticating-to-the-rest-api

## saml-partial-results
1. **slug** — `saml-partial-results`
2. **title** — Org lists silently omit SSO-enforced organizations
3. **symptom** — `GET /user/orgs` returns four organizations when the user belongs to six. Status 200, valid JSON, no error — the two SSO-enforced orgs are simply not there, and an inventory script under-reports forever.
4. **mechanism** — When a token spans multiple organizations and is not SSO-authorized for some of them, GitHub does not fail the request. It returns the organizations it may return and signals the omission only in a response header, which almost nobody reads.
5. **detect** — On any cross-org listing, read `x-github-sso`. The partial form looks like `X-GitHub-SSO: partial-results; organizations=21955855,20582480`, naming the database IDs of the organizations that were withheld. Its presence on a 200 response is the finding. Resolve each ID with `GET /organizations/{id}` where you have access.
6. **repair** — Check for `x-github-sso: partial-results` on every list response and treat it as an error condition for inventory work. Authorize the token for the named organizations, or run per-organization queries with credentials scoped to each.
7. **category** — Organization and SSO
8. **sources** — https://docs.github.com/en/enterprise-cloud@latest/rest/overview/authenticating-to-the-rest-api · https://github.com/github/docs/issues/31661

## saml-session-expired
1. **slug** — `saml-session-expired`
2. **title** — The SAML session lapsed and authorization must be renewed
3. **symptom** — A token that worked yesterday starts returning the SAML-enforcement 403 today, then works again after someone logs in through the browser. It reads as a flaky API.
4. **mechanism** — SAML authorization for a token is tied to an active SAML session with the identity provider, and organizations can require re-authentication on an interval. When the session lapses, previously authorized tokens are refused again.
5. **detect** — The presence of `x-github-sso` on a 403 that was previously succeeding, with the same token and no configuration change, distinguishes lapse from revocation. Where you hold `admin:org`, `GET /orgs/{org}/credential-authorizations` lists SSO-authorized credentials with `credential_id`, `credential_type`, `token_last_eight`, `authorized_credential_expires_at` and `credential_accessed_at`.
6. **repair** — For interactive use, re-authenticate through the SSO URL. For anything unattended, migrate off SAML-dependent user tokens to a GitHub App installation, which does not lapse with a human's IdP session.
7. **category** — Organization and SSO
8. **sources** — https://docs.github.com/en/enterprise-cloud@latest/authentication/authenticating-with-saml-single-sign-on/authorizing-a-personal-access-token-for-use-with-saml-single-sign-on · https://docs.github.com/en/rest/orgs/orgs

## oauth-app-access-restricted
1. **slug** — `oauth-app-access-restricted`
2. **title** — The org blocks the OAuth app and requests to it 403
3. **symptom** — An OAuth integration works for personal repositories and 403s on every organization resource, with a message about the organization having enabled OAuth App access restrictions. The app owner cannot see why.
4. **mechanism** — Organizations can restrict which OAuth Apps may access their data. Until an owner approves the app, its tokens are refused for that org's resources. Crucially, app owners cannot see whether their app is blocked — only the org's members can check.
5. **detect** — Compare behaviour across scopes with the same token: `GET /user/repos` succeeds while `GET /orgs/{org}/repos` returns 403 with the OAuth-restrictions message. Where you hold org access, `GET /orgs/{org}` and the org's OAuth application policy settings confirm it. Distinguish carefully from SAML enforcement, whose 403 carries `x-github-sso`; the OAuth-restriction 403 does not.
6. **repair** — Have an organization owner approve the OAuth App for the organization, or replace the OAuth App with a GitHub App, which uses per-installation approval rather than a blanket org policy.
7. **category** — Organization and SSO
8. **sources** — https://docs.github.com/en/organizations/managing-oauth-access-to-your-organizations-data/about-oauth-app-access-restrictions · https://docs.github.com/en/rest/using-the-rest-api/troubleshooting-the-rest-api

## fine-grained-pat-pending-approval
1. **slug** — `fine-grained-pat-pending-approval`
2. **title** — A fine-grained token is waiting for organization approval
3. **symptom** — The token exists, the permissions were selected correctly, and every organization resource returns 403 or 404. The token page shows it as pending; the API says nothing helpful.
4. **mechanism** — Organizations can require owner approval for any fine-grained PAT that can access their resources. Until an owner approves it, the token holds its permissions on paper and none in practice.
5. **detect** — Behavioural: `GET /user` succeeds (token is valid), personal-scope reads succeed, and every `GET /orgs/{org}/...` or org-repo read fails. That asymmetry, with no `x-github-sso` header and no OAuth-restriction message, points at pending approval. Where you hold `admin:org`, the organization's pending-request listing is the authoritative source.
6. **repair** — Have an organization owner approve the token request from the org's Personal access tokens settings. Where automation cannot wait on a human queue, use a GitHub App installation instead.
7. **category** — Organization and SSO
8. **sources** — https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens · https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization

## ip-allow-list-blocks-requests
1. **slug** — `ip-allow-list-blocks-requests`
2. **title** — An organization IP allow list blocks the integration's egress
3. **symptom** — `403` from a CI runner or a cloud function, while the identical request from a developer's laptop succeeds. Anonymous requests to the same public repository may still work, which makes it look like an auth bug.
4. **mechanism** — An organization IP allow list restricts which source addresses may reach its resources. Ephemeral CI egress IPs and serverless NAT addresses are rarely on it. App-managed allow lists cover installation tokens only — a user-to-server OAuth token is still judged against the *organization's* own list.
5. **detect** — Run the same authenticated request from two source addresses and compare: 403 from one, 200 from the other, with an identical token, isolates the network path. `GET /meta` gives GitHub's own ranges for the reverse direction. Where you hold `admin:org`, the organization's IP allow list settings are readable and can be diffed against your egress ranges.
6. **repair** — Add the integration's egress CIDRs to the organization's allow list, or route the integration through a fixed-IP NAT gateway that is already allowed. For a GitHub App, enable the App-managed allow list so its ranges are contributed automatically.
7. **category** — Organization and SSO
8. **sources** — https://github.com/orgs/community/discussions/191185 · https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-security-settings-for-your-organization/managing-allowed-ip-addresses-for-your-organization

## org-2fa-requirement-removed-member
1. **slug** — `org-2fa-requirement-removed-member`
2. **title** — Enforcing 2FA silently removed the machine account
3. **symptom** — A service account's token starts returning 404 for every organization repository. The token is valid — `GET /user` works — but the account is no longer a member.
4. **mechanism** — When an organization enables required two-factor authentication, members and outside collaborators without 2FA are **removed** from the organization. Machine accounts created without 2FA are the classic casualty, and the removal is not announced to the integration.
5. **detect** — `GET /user` → `login`, then `GET /orgs/{org}/members/{login}`: `204` means still a member, `404` means removed. `GET /orgs/{org}` → `two_factor_requirement_enabled: true` supplies the motive. `GET /user/orgs` no longer listing the organization corroborates.
6. **repair** — Enable 2FA on the machine account and have an owner re-invite it, or — better — replace the machine account with a GitHub App installation, which is unaffected by member 2FA policy.
7. **category** — Organization and SSO
8. **sources** — https://docs.github.com/en/rest/orgs/members · https://docs.github.com/en/organizations/keeping-your-organization-secure/managing-two-factor-authentication-for-your-organization/requiring-two-factor-authentication-in-your-organization

## org-base-permission-changed
1. **slug** — `org-base-permission-changed`
2. **title** — The org's base permission dropped and reads started failing
3. **symptom** — A read-only integration that saw every repository in the organization now sees only a handful. Nothing was revoked from the account explicitly.
4. **mechanism** — An organization's `default_repository_permission` (`none`, `read`, `write`, `admin`) governs what members can do on repositories they are not explicitly added to. Tightening it from `read` to `none` — a normal hardening step — instantly removes implicit access for every member, including machine accounts.
5. **detect** — `GET /orgs/{org}` → `default_repository_permission` (visible with org read access), plus `members_can_create_repositories` and `two_factor_requirement_enabled` for context. Correlate with a coverage count: `GET /user/repos?affiliation=organization_member&per_page=1` and the `rel="last"` page number versus the org's total repository count.
6. **repair** — Add the integration's account to the specific repositories or to a team with read access, rather than relying on a permissive org default. Base permissions are a security control and should stay tight.
7. **category** — Organization and SSO
8. **sources** — https://docs.github.com/en/rest/orgs/orgs · https://docs.github.com/en/organizations/managing-user-access-to-your-organizations-repositories/managing-repository-roles/setting-base-permissions-for-an-organization

## app-installation-request-pending
1. **slug** — `app-installation-request-pending`
2. **title** — The App installation was requested but never approved
3. **symptom** — A user completed what looked like an installation flow, the product shows the integration as connected, and no events or API access ever materialise.
4. **mechanism** — When a non-owner asks to install a GitHub App on an organization, it becomes a *request* an owner must approve. The request sits in a queue indefinitely and the App never appears in its own installation list.
5. **detect** — `GET /app/installations` with the App JWT: the organization is simply absent. `GET /orgs/{org}/installation` returns `404` for that App. Compare against your own record of who started an installation flow — accounts you believe installed but that do not appear are pending or abandoned requests.
6. **repair** — Surface the pending state in the product rather than showing "connected", and prompt the user to ask an organization owner to approve the request. Reconcile your stored connection state against `GET /app/installations` on a schedule.
7. **category** — Organization and SSO
8. **sources** — https://docs.github.com/en/rest/apps/apps · https://docs.github.com/en/apps/using-github-apps/requesting-a-github-app-from-your-organization-owner

## org-token-lifetime-policy
1. **slug** — `org-token-lifetime-policy`
2. **title** — An org policy caps token lifetime shorter than the rotation
3. **symptom** — Tokens that used to last a year now die after 90 days, and the rotation runbook — written when the policy was looser — is scheduled annually.
4. **mechanism** — Organizations can enforce a maximum lifetime for fine-grained personal access tokens accessing their resources. A policy change retroactively shortens the effective life of tokens, and the integration learns about it as a `401`.
5. **detect** — Read `github-authentication-token-expiration` on any authenticated response and compare it against your rotation interval. A gap where expiry lands before the next scheduled rotation is the finding, and it is knowable months in advance.
6. **repair** — Shorten the rotation interval to fit inside the enforced maximum and alert on the expiry header rather than a calendar. Where the cadence is impractical, move to a GitHub App whose installation tokens are minted hourly.
7. **category** — Organization and SSO
8. **sources** — https://docs.github.com/en/organizations/managing-programmatic-access-to-your-organization/setting-a-personal-access-token-policy-for-your-organization · https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

## outside-collaborator-invisible-org-data
1. **slug** — `outside-collaborator-invisible-org-data`
2. **title** — An outside collaborator's token cannot see org-level data
3. **symptom** — Repository reads work; every organization-level call (`teams`, `members`, org repository listings) returns `404`. It looks like a scope problem and adding scopes does not help.
4. **mechanism** — An outside collaborator has access to specific repositories but is not an organization member. Organization-level endpoints require membership, and fine-grained tokens explicitly cannot act for outside collaborators on organization repositories at all.
5. **detect** — `GET /orgs/{org}/members/{login}` → `404` while `GET /repos/{org}/{repo}` → `200` is the definitive pair. `GET /orgs/{org}/outside_collaborators` (needs org read) lists them explicitly. `GET /user/orgs` not listing the organization corroborates from the token's own side.
6. **repair** — Make the account a proper organization member with an appropriate role if org-level data is genuinely required, or drop the org-level calls from the integration and work purely at repository scope.
7. **category** — Organization and SSO
8. **sources** — https://docs.github.com/en/rest/orgs/outside-collaborators · https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens

## enterprise-endpoint-on-dotcom
1. **slug** — `enterprise-endpoint-on-dotcom`
2. **title** — The client points at the wrong API host for the account
3. **symptom** — `404` on endpoints that plainly exist, or `401` with a token that works elsewhere. Common when code is shared between github.com and GitHub Enterprise Server deployments.
4. **mechanism** — GitHub Enterprise Server lives at `https://HOSTNAME/api/v3` and its GraphQL at `https://HOSTNAME/api/graphql`; github.com uses `https://api.github.com`. A base-URL default baked into an SDK, or an env var that did not get set, silently sends requests to the wrong installation, where the token is meaningless and the resources do not exist.
5. **detect** — `GET /meta` on the configured base URL returns `installed_version` on Enterprise Server and does not on github.com; `GET /` returns the root endpoint map either way. `GET /user` returning the wrong `login`, or `html_url` on any object pointing at an unexpected hostname, confirms the target.
6. **repair** — Set the API base URL explicitly for every environment rather than relying on a library default, and assert at startup that `GET /user` returns the expected `login` and that object `html_url` values match the expected host.
7. **category** — Organization and SSO
8. **sources** — https://docs.github.com/en/enterprise-server@latest/rest/quickstart · https://docs.github.com/en/rest/meta/meta
