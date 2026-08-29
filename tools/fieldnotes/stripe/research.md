# Stripe integration failures a read-only script can detect

**114 distinct problems**, every one detectable through the Stripe API with a restricted (read-only, GET-only) key. Grouped into ten categories.

Each entry carries eight fields: `slug`, `title`, `symptom`, `mechanism`, `detect` (the exact read-only call and the field to inspect), `repair` (printed, never executed), `category`, `sources`.

**Scope rule applied throughout:** a problem is included only if a script holding a restricted Stripe API key can *detect* it via the API. Source-code-only faults — a webhook handler that parses the body before verifying the signature, for example — appear only where they have an API-visible symptom, and the detection described is that symptom.

Research date: 2026-08-30. Current Stripe API release line: Clover (`2025-09-30.clover` onward; prior lines Basil `2025-03-31`, Acacia `2024-09-30`). Event retention through `GET /v1/events` is 30 days. Every Stripe API supports restricted keys with per-resource **Read** permission, so every `detect` below is reachable GET-only.

---

## Table of contents

| # | Category | Count |
| --- | --- | --- |
| 1 | [Webhooks & events](#webhooks--events) | 15 |
| 2 | [Payments & intents](#payments--intents) | 13 |
| 3 | [Subscriptions & billing](#subscriptions--billing) | 13 |
| 4 | [Invoices & tax](#invoices--tax) | 10 |
| 5 | [Connect & payouts](#connect--payouts) | 15 |
| 6 | [Disputes & fraud](#disputes--fraud) | 11 |
| 7 | [Customers & payment methods](#customers--payment-methods) | 10 |
| 8 | [Checkout & links](#checkout--links) | 11 |
| 9 | [API versioning & idempotency](#api-versioning--idempotency) | 7 |
| 10 | [Reporting & reconciliation](#reporting--reconciliation) | 9 |
| | **Total** | **114** |

### Webhooks & events

1. [`no-live-webhook-endpoints`](#no-live-webhook-endpoints) — Live mode has zero webhook endpoints registered
2. [`webhook-endpoint-disabled`](#webhook-endpoint-disabled) — A webhook endpoint sits in status disabled after failed retries
3. [`non-https-or-tunnel-webhook-url`](#non-https-or-tunnel-webhook-url) — A live endpoint points at http:// or a dead dev tunnel
4. [`wildcard-enabled-events`](#wildcard-enabled-events) — Endpoint subscribes to `*` and floods the handler
5. [`duplicate-endpoints-same-url`](#duplicate-endpoints-same-url) — Two endpoints share one URL, so every event is handled twice
6. [`events-with-pending-webhooks`](#events-with-pending-webhooks) — Recent events still show pending_webhooks above zero
7. [`undelivered-events-nearing-retention`](#undelivered-events-nearing-retention) — Undelivered events are aging out of the 30-day window
8. [`unsubscribed-event-types-firing`](#unsubscribed-event-types-firing) — Event types are firing that no endpoint subscribes to
9. [`charge-events-but-paymentintent-integration`](#charge-events-but-paymentintent-integration) — Endpoint listens for charge.succeeded but you use PaymentIntents
10. [`missing-payment-failure-events`](#missing-payment-failure-events) — No endpoint subscribes to any payment-failure event
11. [`missing-subscription-deleted`](#missing-subscription-deleted) — customer.subscription.deleted is missing, so access never ends
12. [`missing-dispute-and-fraud-events`](#missing-dispute-and-fraud-events) — Nothing subscribes to disputes or early fraud warnings
13. [`missing-payout-failed`](#missing-payout-failed) — payout.failed is unsubscribed so broken bank details go unseen
14. [`connect-platform-missing-account-updated`](#connect-platform-missing-account-updated) — Connect platform has no endpoint scoped to connected accounts
15. [`no-v2-event-destinations`](#no-v2-event-destinations) — No v2 event destination exists, so thin events never arrive

### Payments & intents

16. [`stale-requires-payment-method-intents`](#stale-requires-payment-method-intents) — PaymentIntents sit in requires_payment_method for weeks
17. [`abandoned-requires-action-intents`](#abandoned-requires-action-intents) — requires_action intents pile up: the 3DS handoff is broken
18. [`expired-manual-capture-holds`](#expired-manual-capture-holds) — Manual-capture holds expire before anyone captures them
19. [`uncaptured-charge-expiry-refunds`](#uncaptured-charge-expiry-refunds) — Refunds reason expired_uncaptured_charge: lost revenue
20. [`radar-blocked-payments-ignored`](#radar-blocked-payments-ignored) — Radar blocks payments and no one reads the block reasons
21. [`elevated-risk-charges-no-review`](#elevated-risk-charges-no-review) — Elevated-risk charges captured with no manual review step
22. [`off-session-authentication-required-declines`](#off-session-authentication-required-declines) — Off-session charges die on authentication_required
23. [`testmode-decline-in-live-mode`](#testmode-decline-in-live-mode) — Live charges fail with testmode_decline from test cards
24. [`card-only-payment-method-types`](#card-only-payment-method-types) — Intents hardcode payment_method_types to card only
25. [`wallet-domain-not-registered`](#wallet-domain-not-registered) — No payment method domain registered, so wallets never show
26. [`legacy-charges-api-no-payment-intent`](#legacy-charges-api-no-payment-intent) — Charges have null payment_intent: legacy Charges API
27. [`bank-debit-intents-stuck-processing`](#bank-debit-intents-stuck-processing) — Bank-debit intents stay in processing for over a week
28. [`refunds-failed-or-stuck`](#refunds-failed-or-stuck) — Refunds sit failed or requires_action and nobody notices

### Subscriptions & billing

29. [`past-due-subscriptions-accumulating`](#past-due-subscriptions-accumulating) — past_due subscriptions keep billing but nobody revokes access
30. [`subscriptions-stuck-incomplete`](#subscriptions-stuck-incomplete) — incomplete subscriptions die silently after 23 hours
31. [`incomplete-expired-signup-leak`](#incomplete-expired-signup-leak) — incomplete_expired volume means checkout confirmation is broken
32. [`unpaid-subscriptions-still-provisioned`](#unpaid-subscriptions-still-provisioned) — unpaid subscriptions still have access but never bill again
33. [`subscription-without-payment-method`](#subscription-without-payment-method) — Active subscriptions with no payment method anywhere to charge
34. [`sca-authentication-stuck-subscriptions`](#sca-authentication-stuck-subscriptions) — Subscriptions frozen on requires_action 3DS authentication
35. [`trial-ends-without-payment-method`](#trial-ends-without-payment-method) — Trials about to end with no payment method on file
36. [`paused-subscriptions-never-resumed`](#paused-subscriptions-never-resumed) — paused subscriptions never resume and stop invoicing forever
37. [`pause-collection-left-on-indefinitely`](#pause-collection-left-on-indefinitely) — pause_collection with no resumes_at quietly bills nothing
38. [`send-invoice-without-days-until-due`](#send-invoice-without-days-until-due) — send_invoice subscriptions with no days_until_due set
39. [`cancel-at-period-end-churn-backlog`](#cancel-at-period-end-churn-backlog) — A wall of cancel_at_period_end subscriptions nobody noticed
40. [`save-default-payment-method-off`](#save-default-payment-method-off) — save_default_payment_method off orphans the card after payment
41. [`metered-items-with-no-usage-reported`](#metered-items-with-no-usage-reported) — Metered subscription items with zero usage events reported

### Invoices & tax

42. [`draft-invoices-never-finalized`](#draft-invoices-never-finalized) — Draft invoices older than 30 days that never finalized
43. [`draft-invoices-blocked-by-tax-location`](#draft-invoices-blocked-by-tax-location) — Invoices stuck in draft on customer_tax_location_invalid
44. [`open-invoices-past-due-date`](#open-invoices-past-due-date) — open invoices past their due_date with nobody chasing them
45. [`dunning-retries-exhausted`](#dunning-retries-exhausted) — Invoices where retries ran out and no attempt is scheduled
46. [`automatic-tax-disabled-everywhere`](#automatic-tax-disabled-everywhere) — automatic_tax disabled on every invoice while selling abroad
47. [`automatic-tax-requires-location-inputs`](#automatic-tax-requires-location-inputs) — automatic_tax.status is requires_location_inputs or failed
48. [`no-tax-registrations-while-selling-abroad`](#no-tax-registrations-while-selling-abroad) — No tax registrations while invoicing many countries
49. [`prices-with-tax-behavior-unspecified`](#prices-with-tax-behavior-unspecified) — Prices left at tax_behavior unspecified break tax math
50. [`missing-customer-tax-ids-b2b-eu`](#missing-customer-tax-ids-b2b-eu) — EU B2B invoices with no customer_tax_ids miss reverse charge
51. [`orphaned-pending-invoice-items`](#orphaned-pending-invoice-items) — Pending invoice items that never got attached to an invoice

### Connect & payouts

52. [`connected-accounts-charges-disabled`](#connected-accounts-charges-disabled) — Connected accounts sit with charges_enabled false unnoticed
53. [`requirements-past-due-disables-account`](#requirements-past-due-disables-account) — requirements.past_due already disabled the account's payouts
54. [`current-deadline-passes-unwatched`](#current-deadline-passes-unwatched) — current_deadline passes before you collect currently_due fields
55. [`transfers-capability-inactive`](#transfers-capability-inactive) — transfers capability is inactive so every transfer 400s
56. [`card-payments-inactive-cascades`](#card-payments-inactive-cascades) — card_payments inactive silently disables transfers too
57. [`no-external-account-attached`](#no-external-account-attached) — Connected account has no external account, so payouts never run
58. [`external-account-errored`](#external-account-errored) — Bank account status errored halts all scheduled payouts
59. [`payouts-failing-bank-rejection`](#payouts-failing-bank-rejection) — Payouts fail with account_closed and nobody is watching
60. [`platform-paused-payouts-left-on`](#platform-paused-payouts-left-on) — Platform-paused payouts were never unpaused
61. [`payout-schedule-left-on-manual`](#payout-schedule-left-on-manual) — Payout schedule was left on manual and funds pile up
62. [`onboarding-abandoned-details-not-submitted`](#onboarding-abandoned-details-not-submitted) — Accounts stall at details_submitted false after link expiry
63. [`person-requirements-outstanding`](#person-requirements-outstanding) — A Person's currently_due blocks the whole account
64. [`verification-errors-unread`](#verification-errors-unread) — requirements.errors codes like greyscale docs go unread
65. [`future-requirements-deadline-ignored`](#future-requirements-deadline-ignored) — future_requirements deadline will revoke a live capability
66. [`external-account-currency-mismatch`](#external-account-currency-mismatch) — External account currency can't settle the account's balance

### Disputes & fraud

67. [`dispute-deadline-72h-no-evidence`](#dispute-deadline-72h-no-evidence) — Disputes are hours from due_by with no evidence attached
68. [`inquiry-needs-response-ignored`](#inquiry-needs-response-ignored) — Inquiries sit unanswered and escalate into real chargebacks
69. [`dispute-rate-above-threshold`](#dispute-rate-above-threshold) — Dispute activity is above the 0.75% excessive threshold
70. [`disputes-lost-without-response`](#disputes-lost-without-response) — Disputes were lost by default because nobody responded
71. [`efw-actionable-not-refunded`](#efw-actionable-not-refunded) — Actionable early fraud warnings were never refunded
72. [`radar-reviews-open-stale`](#radar-reviews-open-stale) — Radar reviews sit open for days while funds stay at risk
73. [`radar-blocked-rate-overblocking`](#radar-blocked-rate-overblocking) — Radar is blocking a large share of your charge attempts
74. [`highest-risk-charges-succeeded`](#highest-risk-charges-succeeded) — Highest-risk charges are succeeding instead of being blocked
75. [`avs-cvc-fail-captured`](#avs-cvc-fail-captured) — Charges captured after AVS and CVC verification failed
76. [`missing-statement-descriptor`](#missing-statement-descriptor) — No statement descriptor, so customers dispute what they see
77. [`no-3ds-on-elevated-risk`](#no-3ds-on-elevated-risk) — Elevated-risk card charges are captured with no 3DS

### Customers & payment methods

78. [`duplicate-customers-same-email`](#duplicate-customers-same-email) — Duplicate customers share an email and split billing
79. [`customers-missing-email`](#customers-missing-email) — Customers have no email, so Stripe sends no receipts
80. [`customers-missing-address`](#customers-missing-address) — Customers have no address; tax and SCA exemptions fail
81. [`expired-saved-cards-attached`](#expired-saved-cards-attached) — Saved cards are already expired but still attached
82. [`cards-expiring-within-60-days`](#cards-expiring-within-60-days) — Saved cards expire within 60 days with no updater
83. [`unattached-payment-methods-orphaned`](#unattached-payment-methods-orphaned) — PaymentMethods created but never attached to a customer
84. [`setup-intents-never-confirmed`](#setup-intents-never-confirmed) — SetupIntents created but never confirmed by the client
85. [`setup-intent-on-session-for-off-session`](#setup-intent-on-session-for-off-session) — SetupIntents use on_session but you bill off-session
86. [`legacy-card-sources-still-attached`](#legacy-card-sources-still-attached) — Legacy card sources still live under customer.sources
87. [`payment-intents-with-null-customer`](#payment-intents-with-null-customer) — PaymentIntents have a null customer: payments orphaned

### Checkout & links

88. [`checkout-expired-session-share`](#checkout-expired-session-share) — Most Checkout Sessions expire unpaid and nobody is told
89. [`checkout-complete-payment-unpaid`](#checkout-complete-payment-unpaid) — Session status is complete but payment_status is still unpaid
90. [`checkout-sessions-unreconcilable`](#checkout-sessions-unreconcilable) — Checkout Sessions carry no ID that maps back to your order
91. [`checkout-guest-customer-null`](#checkout-guest-customer-null) — Guest checkouts finish with customer null and can't be linked
92. [`checkout-recovery-never-enabled`](#checkout-recovery-never-enabled) — Expired Checkout Sessions are never recovered by email
93. [`checkout-embedded-no-return-url`](#checkout-embedded-no-return-url) — Embedded Checkout never redirects and return_url is null
94. [`payment-link-inactive-still-published`](#payment-link-inactive-still-published) — A deactivated Payment Link is still linked from your site
95. [`payment-link-hosted-confirmation-no-fulfilment`](#payment-link-hosted-confirmation-no-fulfilment) — Payment Link ends on Stripe's page, so fulfilment never fires
96. [`payment-link-completion-limit-reached`](#payment-link-completion-limit-reached) — Payment Link hit its completed-session limit and went dead
97. [`billing-portal-no-configuration`](#billing-portal-no-configuration) — No Billing Portal configuration, so portal sessions 400
98. [`billing-portal-cancel-disabled`](#billing-portal-cancel-disabled) — Billing Portal can't cancel, so customers charge back instead

### API versioning & idempotency

99. [`dead-or-rejected-enabled-events`](#dead-or-rejected-enabled-events) — enabled_events lists event types that are dead or rejected
100. [`endpoint-api-version-pinned-stale`](#endpoint-api-version-pinned-stale) — A webhook endpoint is pinned to an ancient api_version
101. [`endpoint-api-version-drift`](#endpoint-api-version-drift) — Endpoints render events at different pinned API versions
102. [`account-default-api-version-stale`](#account-default-api-version-stale) — Account default API version is years behind the current one
103. [`mixed-event-api-versions`](#mixed-event-api-versions) — Recent events carry two different api_version values
104. [`missing-idempotency-keys-on-payments`](#missing-idempotency-keys-on-payments) — Payment-creating requests carry no idempotency key
105. [`idempotency-key-reuse-conflict`](#idempotency-key-reuse-conflict) — Reused idempotency keys hit 409 idempotency_key_in_use

### Reporting & reconciliation

106. [`connect-reserved-balance-growing`](#connect-reserved-balance-growing) — connect_reserved keeps growing from negative account balances
107. [`stranded-currency-balance`](#stranded-currency-balance) — A second-currency balance bucket can never be paid out
108. [`application-fees-zero-on-platform`](#application-fees-zero-on-platform) — Platform takes zero application fees on its own charges
109. [`payout-reconciliation-unavailable`](#payout-reconciliation-unavailable) — Payouts cannot be tied back to their balance transactions
110. [`report-run-failed-silently`](#report-run-failed-silently) — reporting.report_run silently fails and the CSV never lands
111. [`report-interval-past-data-available-end`](#report-interval-past-data-available-end) — Reports run past data_available_end and return short data
112. [`sigma-scheduled-query-failing`](#sigma-scheduled-query-failing) — Sigma scheduled query runs time out and email nothing
113. [`terminal-readers-offline`](#terminal-readers-offline) — Terminal readers sit offline and take no payments
114. [`issuing-cardholder-requirements-past-due`](#issuing-cardholder-requirements-past-due) — Cardholder requirements.past_due keeps every card inactive

---

# Webhooks & events

## no-live-webhook-endpoints

- **slug**: `no-live-webhook-endpoints`
- **title**: Live mode has zero webhook endpoints registered
- **symptom**: Payments succeed in the Stripe Dashboard but nothing happens in the app — no order rows, no fulfilment emails, no subscription provisioning. Works perfectly in local dev because `stripe listen` was doing the delivery all along.
- **mechanism**: The developer only ever tested with the Stripe CLI listener, which creates an ephemeral in-memory destination and prints its own `whsec_`. No persistent endpoint was ever created in live mode, so Stripe has nowhere to push events.
- **detect**: `GET /v1/webhook_endpoints?limit=100` with a **live** restricted key → `data.length == 0`. Corroborate that traffic exists with `GET /v1/events?limit=1&types[]=payment_intent.succeeded` → `data.length > 0`. Zero endpoints plus non-zero payment events = confirmed.
- **repair**: `POST /v1/webhook_endpoints` with `url=https://<yourdomain>/stripe/webhook`, `enabled_events[]=payment_intent.succeeded`, `enabled_events[]=payment_intent.payment_failed`. Or Dashboard → Workbench → Webhooks → Create an event destination → Your account → Webhook endpoint. Copy the `whsec_` into your server env.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/webhooks · https://docs.stripe.com/api/webhook_endpoints/create

## webhook-endpoint-disabled

- **slug**: `webhook-endpoint-disabled`
- **title**: A webhook endpoint sits in status disabled after failed retries
- **symptom**: Events flowed fine for months, then stopped completely on a specific date. No errors in the app logs, because nothing is arriving at all.
- **mechanism**: Stripe retries a failing destination with exponential backoff for up to three days in live mode. Sustained non-2xx responses (a rotated secret returning 400, a moved route returning 404, a WAF returning 403) end with the endpoint being disabled, and once disabled Stripe prevents future retries of pending events.
- **detect**: `GET /v1/webhook_endpoints?limit=100` → any `data[].status == "disabled"`. Report `data[].url`, `data[].created`, `data[].enabled_events`. Size the damage with `GET /v1/events?delivery_success=false&limit=100` → count of undelivered events.
- **repair**: Fix the handler first (secret, route, firewall), then `POST /v1/webhook_endpoints/{we_id}` with `disabled=false`. Backfill with `GET /v1/events?delivery_success=false&types[]=...&ending_before=<last_good_evt>` replayed through your own processor.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/api/webhook_endpoints/object · https://docs.stripe.com/webhooks · https://docs.stripe.com/webhooks/process-undelivered-events

## non-https-or-tunnel-webhook-url

- **slug**: `non-https-or-tunnel-webhook-url`
- **title**: A live endpoint points at http:// or a dead dev tunnel
- **symptom**: Delivery fails with "Unable to connect" or a TLS error on every attempt. Or it worked for exactly one afternoon during development and never again.
- **mechanism**: Registered endpoints must be publicly reachable HTTPS URLs and Stripe supports only TLS 1.2/1.3. A tunnel hostname from `ngrok`, `loca.lt`, `trycloudflare.com`, or a literal `localhost` was pasted into the live configuration and expired when the tunnel closed.
- **detect**: `GET /v1/webhook_endpoints?limit=100` → flag any entry where `data[].livemode == true` and (`data[].url` does not start with `https://`, **or** the host matches `/localhost|127\.0\.0\.1|\.ngrok(-free)?\.(io|app|dev)|\.loca\.lt|\.trycloudflare\.com|\.serveo\.net/`). Also flag RFC1918 IP literals in the host.
- **repair**: `POST /v1/webhook_endpoints/{we_id}` with `url=https://<production-domain>/stripe/webhook`. If it is a leftover dev artefact, `DELETE /v1/webhook_endpoints/{we_id}` instead. Verify TLS with an SSL Labs server test.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/webhooks · https://docs.stripe.com/api/webhook_endpoints/object

## wildcard-enabled-events

- **slug**: `wildcard-enabled-events`
- **title**: Endpoint subscribes to `*` and floods the handler
- **symptom**: The webhook route receives dozens of event types it has no branch for, response times spike at month-end renewal peaks, and the endpoint intermittently times out and gets retried.
- **mechanism**: `enabled_events: ["*"]` enables every event type except those requiring explicit selection. Stripe explicitly recommends against it — listening for extra events puts undue strain on your server — and the volume amplification is worst exactly when billing volume peaks.
- **detect**: `GET /v1/webhook_endpoints?limit=100` → any `data[].enabled_events` containing the literal `"*"`, or whose `length > 40` (a de-facto wildcard). Compare against what actually fires: `GET /v1/events?limit=100` paginated, tallying distinct `data[].type`.
- **repair**: `POST /v1/webhook_endpoints/{we_id}` with an explicit `enabled_events[]` list limited to the types your handler branches on. Derive the list from your code's switch statement, not from the wildcard.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/webhooks · https://docs.stripe.com/api/webhook_endpoints/update

## duplicate-endpoints-same-url

- **slug**: `duplicate-endpoints-same-url`
- **title**: Two endpoints share one URL, so every event is handled twice
- **symptom**: Duplicate order rows, double fulfilment emails, customers credited twice. The handler looks correct in isolation and the bug is not reproducible locally.
- **mechanism**: A second endpoint was created during a migration or an API-version upgrade — Stripe's own upgrade procedure tells you to create a second endpoint with the same URL plus a query parameter — and the old one was never disabled. Each endpoint has its own signing secret, so both deliveries verify successfully.
- **detect**: `GET /v1/webhook_endpoints?limit=100` → normalise `data[].url` (strip query string and trailing slash) and group. Flag any normalised URL with more than one `status == "enabled"` endpoint at the same `livemode`. Corroborate with `GET /v1/events?limit=20` → `data[].pending_webhooks` matching the endpoint count rather than 0.
- **repair**: Pick the canonical endpoint, then `POST /v1/webhook_endpoints/{stale_we_id}` with `disabled=true` (or `DELETE`). Regardless, make the handler idempotent by persisting processed `event.id` values and short-circuiting repeats.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/webhooks/versioning · https://docs.stripe.com/webhooks

## events-with-pending-webhooks

- **slug**: `events-with-pending-webhooks`
- **title**: Recent events still show pending_webhooks above zero
- **symptom**: The endpoint is `enabled` and the Dashboard shows no red banner, but a subset of payments never got processed. Failures look random rather than total.
- **mechanism**: `pending_webhooks` is the number of destinations that have not yet returned a 2xx for that event. A nonzero value hours after `created` means the handler is timing out, 500-ing, or returning 3xx redirects (Stripe treats redirects on webhook requests as failures). Because Stripe retries for three days, this can persist short of full disablement.
- **detect**: `GET /v1/events?limit=100&created[lt]=<now-3600>` → flag every entry with `data[].pending_webhooks > 0`. Equivalently: `GET /v1/events?delivery_success=false&limit=100` → any non-empty `data`. Group results by `data[].type` to identify the failing handler branch.
- **repair**: Return `200` before doing any work and move processing to an async queue. Then replay: `GET /v1/events?delivery_success=false&types[]=payment_intent.succeeded&ending_before=<evt_id>` with auto-pagination, guarded by your processed-event table.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/api/events/object · https://docs.stripe.com/webhooks/process-undelivered-events · https://docs.stripe.com/webhooks

## undelivered-events-nearing-retention

- **slug**: `undelivered-events-nearing-retention`
- **title**: Undelivered events are aging out of the 30-day window
- **symptom**: An outage is discovered weeks late. The team goes to replay the missed events and finds the oldest ones are simply gone from `/v1/events`, leaving a permanent hole in the order table.
- **mechanism**: Events are retrievable through the API for 30 days only. Automatic retries stop after three days, Dashboard "Resend" works for 15 days, CLI resend for 30. Anything undelivered and older than 30 days can never be recovered from Stripe.
- **detect**: `GET /v1/events?delivery_success=false&limit=100` with auto-pagination → compute `min(data[].created)`. Flag if `now - min(created) > 20 * 86400`; hard-fail above `29 * 86400`.
- **repair**: Replay immediately, oldest first: `GET /v1/events?delivery_success=false&ending_before=<evt_id>&types[]=...` paginated chronologically. For anything past 30 days, reconcile from source objects instead — `GET /v1/charges?created[gte]=...`, `GET /v1/invoices?created[gte]=...` — which are not retention-limited.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/api/events/list · https://docs.stripe.com/webhooks/process-undelivered-events · https://docs.stripe.com/webhooks

## unsubscribed-event-types-firing

- **slug**: `unsubscribed-event-types-firing`
- **title**: Event types are firing that no endpoint subscribes to
- **symptom**: A whole class of business event is invisible to the app. Nobody notices, because an unsubscribed event produces no error anywhere — it simply is not sent.
- **mechanism**: `enabled_events` is an allowlist. Any type outside the union of all endpoints' arrays is generated by Stripe, visible in `/v1/events`, and never delivered. This drifts silently as products are enabled (Radar, disputes, Connect, Billing) long after the endpoint was configured.
- **detect**: Build `subscribed = union(GET /v1/webhook_endpoints?limit=100 → data[].enabled_events)`, treating `"*"` as everything. Then `GET /v1/events?limit=100` paginated over 30 days → `fired = set(data[].type)`. Report `fired - subscribed`, ranked by occurrence count.
- **repair**: `POST /v1/webhook_endpoints/{we_id}` adding the missing types to `enabled_events[]`, after confirming your handler has a branch for each. Do not simply switch to `"*"`.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/api/events/list · https://docs.stripe.com/api/webhook_endpoints/update · https://docs.stripe.com/webhooks

## charge-events-but-paymentintent-integration

- **slug**: `charge-events-but-paymentintent-integration`
- **title**: Endpoint listens for charge.succeeded but you use PaymentIntents
- **symptom**: Fulfilment fires on a Charge object whose `metadata` is empty and which has no `customer` attached, so the handler cannot map the payment back to a cart or user. Or 3DS payments never fulfil at all.
- **mechanism**: An endpoint configured in the Charges-API era was never updated when the integration moved to PaymentIntents or Checkout. `charge.succeeded` carries the Charge, not the PaymentIntent, so the metadata and `client_reference_id` your code depends on live on a different object — and Checkout flows need `checkout.session.completed`, which no `charge.*` subscription implies.
- **detect**: `GET /v1/webhook_endpoints?limit=100` → endpoint where `enabled_events` contains `charge.succeeded` but contains **neither** `payment_intent.succeeded` **nor** `checkout.session.completed`. Confirm integration style with `GET /v1/events?limit=100&types[]=payment_intent.succeeded&types[]=checkout.session.completed` → non-empty `data`.
- **repair**: `POST /v1/webhook_endpoints/{we_id}` with `enabled_events[]=payment_intent.succeeded`, `enabled_events[]=payment_intent.payment_failed`, and `enabled_events[]=checkout.session.completed` if you use Checkout. Move fulfilment onto the PaymentIntent/Session branch, then drop `charge.succeeded`.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/api/webhook_endpoints/create · https://github.com/stripe/stripe-node/issues/2112

## missing-payment-failure-events

- **slug**: `missing-payment-failure-events`
- **title**: No endpoint subscribes to any payment-failure event
- **symptom**: The success path is wired up perfectly and failures are a black hole. Carts stay stuck in "processing" forever, dunning emails never go out, and delinquent subscribers keep their access.
- **mechanism**: Developers subscribe to the happy-path event they tested against and stop. `payment_intent.payment_failed` and `invoice.payment_failed` (covering declined and soft-declined renewals, and the "no stored payment method" case) are separate subscriptions, never implied.
- **detect**: Let `subscribed` be the union of all `data[].enabled_events`. Flag if `payment_intent.succeeded ∈ subscribed` but `payment_intent.payment_failed ∉ subscribed`. Separately flag if `GET /v1/subscriptions?limit=1&status=active` → `data.length > 0` while `invoice.payment_failed ∉ subscribed`. Quantify with `GET /v1/events?types[]=invoice.payment_failed&limit=100` → `data.length`.
- **repair**: `POST /v1/webhook_endpoints/{we_id}` with `enabled_events[]=payment_intent.payment_failed` and `enabled_events[]=invoice.payment_failed` appended. Add `invoice.payment_action_required` if you support 3DS on renewals.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/api/webhook_endpoints/create · https://docs.stripe.com/webhooks

## missing-subscription-deleted

- **slug**: `missing-subscription-deleted`
- **title**: customer.subscription.deleted is missing, so access never ends
- **symptom**: Cancelled and dunning-exhausted customers keep full product access indefinitely. Revenue looks fine; entitlements are wrong. Usually discovered by a support ticket from an honest user.
- **mechanism**: `customer.subscription.deleted` is the only event that fires when a subscription actually ends — including the delayed end of a `cancel_at_period_end` cancellation and Smart Retries giving up. Handlers built around `customer.subscription.created` and `invoice.paid` have no downgrade path.
- **detect**: `GET /v1/webhook_endpoints?limit=100` → union of `enabled_events`. Flag if any `customer.subscription.*` or `invoice.*` type is subscribed but `customer.subscription.deleted` is not. Size the gap with `GET /v1/events?types[]=customer.subscription.deleted&limit=100` and `GET /v1/subscriptions?status=canceled&limit=100`.
- **repair**: `POST /v1/webhook_endpoints/{we_id}` with `enabled_events[]=customer.subscription.deleted` and `enabled_events[]=customer.subscription.updated` added. Reconcile existing over-entitled users against `GET /v1/subscriptions?status=canceled`.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/api/webhook_endpoints/create · https://stackoverflow.com/questions/41550426/detect-automatic-cancellation-of-stripe-subscription-with-cancel-at-period-end-t

## missing-dispute-and-fraud-events

- **slug**: `missing-dispute-and-fraud-events`
- **title**: Nothing subscribes to disputes or early fraud warnings
- **symptom**: Chargebacks are first noticed when the balance drops or Stripe emails a deadline reminder. Evidence windows are missed and the dispute is lost by default. Fraudulent orders ship because nothing flagged them.
- **mechanism**: `charge.dispute.created` is the only push signal for a new chargeback, and `radar.early_fraud_warning.created` fires when the issuer flags a payment *before* it becomes a formal dispute — the window in which a proactive refund prevents the chargeback entirely. Neither is enabled by default nor implied by `charge.*` success subscriptions.
- **detect**: Union all `data[].enabled_events`. Flag if `charge.dispute.created ∉ union` while `GET /v1/disputes?limit=1` → `data.length > 0`. Flag separately if `radar.early_fraud_warning.created ∉ union` while `GET /v1/radar/early_fraud_warnings?limit=1` → `data.length > 0`.
- **repair**: `POST /v1/webhook_endpoints/{we_id}` with `enabled_events[]=charge.dispute.created`, `enabled_events[]=charge.dispute.closed`, `enabled_events[]=radar.early_fraud_warning.created`. On an EFW with no dispute and no full refund, refund proactively.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/api/radar/early_fraud_warnings · https://docs.stripe.com/api/webhook_endpoints/create · https://docs.stripe.com/radar/testing

## missing-payout-failed

- **slug**: `missing-payout-failed`
- **title**: payout.failed is unsubscribed so broken bank details go unseen
- **symptom**: Money stops arriving in the bank account (or in connected accounts' bank accounts) and nobody knows for days. On Connect, sellers complain before the platform notices.
- **mechanism**: When a payout fails the external account involved is disabled, and no automatic or manual payouts can be processed until it is updated. `payout.paid` is what people subscribe to; `payout.failed` arrives later and separately, with `account.external_account.updated` as the companion signal.
- **detect**: Union all `data[].enabled_events`. Flag if `payout.failed ∉ union`. Confirm relevance with `GET /v1/payouts?limit=100` → any `data[].status == "failed"`, or `GET /v1/events?types[]=payout.failed&limit=100` → `data.length > 0`.
- **repair**: `POST /v1/webhook_endpoints/{we_id}` with `enabled_events[]=payout.failed` and `enabled_events[]=payout.paid`; on Connect add `enabled_events[]=account.external_account.updated` to the Connect-scoped endpoint. Alert on `payout.failure_code`.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/connect/webhooks · https://docs.stripe.com/api/webhook_endpoints/create

## connect-platform-missing-account-updated

- **slug**: `connect-platform-missing-account-updated`
- **title**: Connect platform has no endpoint scoped to connected accounts
- **symptom**: Connected accounts get stuck mid-onboarding. `charges_enabled` flips false and the platform UI still shows them as live. Sellers who disconnect keep appearing as active.
- **mechanism**: A Connect endpoint (`connect=true` at creation, "Connected accounts" in Workbench) is a separate object from the account endpoint. Events from connected accounts carry a top-level `account` property and only reach a Connect-scoped destination — an account-scoped endpoint never sees them, whatever `enabled_events` says.
- **detect**: Establish the account is a platform: `GET /v1/accounts?limit=1` → `data.length > 0`. Then `GET /v1/webhook_endpoints?limit=100`. Because the `connect` flag is **not returned** on the endpoint object (only `application` is), use the proxy signal: flag if no endpoint's `enabled_events` contains `account.updated` or `account.application.deauthorized`.
- **repair**: `POST /v1/webhook_endpoints` with `connect=true`, `url=https://<yourdomain>/stripe/connect-webhook`, `enabled_events[]=account.updated`, `enabled_events[]=account.application.deauthorized`, `enabled_events[]=capability.updated`, `enabled_events[]=person.updated`, `enabled_events[]=payout.failed`. In Workbench: Create an event destination → **Connected accounts**. Handle `event.account` and make API calls as that account.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/connect/webhooks · https://docs.stripe.com/api/webhook_endpoints/create · https://stackoverflow.com/questions/72575728/stripe-webhook-account-updated-never-triggered-whenever-an-connected-account-st

## no-v2-event-destinations

- **slug**: `no-v2-event-destinations`
- **title**: No v2 event destination exists, so thin events never arrive
- **symptom**: A newer Stripe feature (Billing meters, Accounts v2, money-management APIs) documents a `v1.*`-prefixed event, the team adds it to the v1 endpoint, and it is silently rejected or never delivered.
- **mechanism**: Thin events from API v2 resources are delivered only to a v2 event destination created with `event_payload: "thin"` — a completely separate object from `/v1/webhook_endpoints`, with its own registration and its own signing secret. Snapshot (v1) endpoints cannot carry them.
- **detect**: `GET /v2/core/event_destinations` (with `Stripe-Version` set to a v2-capable version) → `data.length == 0`, or no entry with `event_payload == "thin"`. Also inspect each destination's `status`, `status_details`, `events_from`, `snapshot_api_version`. Flag as relevant only if `GET /v1/billing/meters?limit=1` (or another v2 feature) returns data.
- **repair**: `POST /v2/core/event_destinations` with `type=webhook_endpoint`, `event_payload=thin`, `events_from=["@self"]`, `enabled_events=["v1.billing.meter.error_report_triggered", ...]`, `webhook_endpoint.url=https://<yourdomain>/stripe/thin-webhook`, `include=["webhook_endpoint.signing_secret"]`. Parse with `parse_event_notification()` and `fetchRelatedObject()`.
- **category**: Webhooks & events
- **sources**: https://docs.stripe.com/api/v2/core/event-destinations/object · https://docs.stripe.com/webhooks · https://github.com/stripe/stripe-ruby/issues/1860

---

# Payments & intents

## stale-requires-payment-method-intents

- **slug**: `stale-requires-payment-method-intents`
- **title**: PaymentIntents sit in requires_payment_method for weeks
- **symptom**: A large share of PaymentIntents were created but never got a payment method attached, and they just sit there forever. Dashboard payment volume looks far lower than checkout starts, and "incomplete" payments accumulate indefinitely.
- **mechanism**: A PaymentIntent enters `requires_payment_method` the moment it is created, and returns to that status after any failed confirmation. Integrations that create an intent on page load (rather than at confirm time), or that never retry after a decline, leave a permanent trail of dead intents that nobody cancels or follows up on. The sibling status `requires_confirmation` behaves the same way when `confirmation_method: manual` is used and the server never calls confirm.
- **detect**: `GET /v1/payment_intents?limit=100&created[lt]={now-7d}` (paginate via `starting_after`). Count `data[].status == "requires_payment_method"` and `data[].status == "requires_confirmation"`. Flag when `(stale_rpm + stale_rc) / total_older_than_7d > 0.30`. Split by `data[].last_payment_error` being `null` (never attempted) vs non-null (attempted and declined). Search alternative: `GET /v1/payment_intents/search?query=status:'requires_payment_method' AND created<{now-7d}`.
- **repair**: Create the PaymentIntent at confirm time, not page load. Cancel dead intents with `POST /v1/payment_intents/{id}/cancel` with `cancellation_reason=abandoned`. For the never-attempted bucket, move the intent creation behind the "Pay" button; for the declined bucket, add a retry UI that reuses the same intent and surfaces `last_payment_error.message`.
- **category**: Payments & intents
- **sources**: https://docs.stripe.com/payments/paymentintents/lifecycle · https://stackoverflow.com/questions/66244386/stripe-status-requires-payment-method · https://docs.stripe.com/api/payment_intents/object

## abandoned-requires-action-intents

- **slug**: `abandoned-requires-action-intents`
- **title**: requires_action intents pile up: the 3DS handoff is broken
- **symptom**: Payments stall at the 3D Secure step. Intents show `status: "requires_action"` with a populated `next_action`, but never advance to `succeeded` or `canceled`. European and Indian card volume looks disproportionately low.
- **mechanism**: When the issuer or SCA rules require authentication, Stripe moves the intent to `requires_action` and expects the client to call `stripe.handleNextAction()` / `confirmPayment`. If the frontend never calls it, redirects to a `return_url` that doesn't exist, or the redirect is blocked in an iframe/webview, the customer silently drops out and the intent freezes.
- **detect**: `GET /v1/payment_intents?limit=100&created[lt]={now-24h}` (paginate). Count `data[].status == "requires_action"`, and bucket by `data[].next_action.type` (`use_stripe_sdk`, `redirect_to_url`, `three_d_secure_redirect`). Compute abandonment rate as `count(requires_action older than 24h) / count(intents that ever entered requires_action)`; anything over 15% means broken UX rather than customer choice. Cross-check `GET /v1/charges?limit=100` for `outcome.reason == "authentication_required"`.
- **repair**: On the client, always handle the returned status: `const {error} = await stripe.confirmPayment({elements, confirmParams: {return_url}})`, and implement the `return_url` page to re-retrieve the intent by `client_secret`. For server-confirmed flows call `stripe.handleNextAction({clientSecret})`. Verify the `return_url` is registered and reachable, and stop launching 3DS inside a cross-origin iframe.
- **category**: Payments & intents
- **sources**: https://docs.stripe.com/payments/paymentintents/lifecycle · https://stackoverflow.com/questions/56279543/why-is-stripe-not-giving-me-a-payment-intents-requires-action-status-when-i-use · https://stackoverflow.com/questions/55858767/how-to-fix-the-3d-secure-confirm-payment-on-client-side-or-on-server-side-in-str

## expired-manual-capture-holds

- **slug**: `expired-manual-capture-holds`
- **title**: Manual-capture holds expire before anyone captures them
- **symptom**: Authorized payments show `requires_capture` but were never captured. Customers see a pending hold drop off their statement, and you never receive the money. Capture attempts return `charge_expired_for_capture`.
- **mechanism**: With `capture_method: manual`, the authorization is only valid for a limited window — 7 days for most card-not-present transactions, 5 days for Visa MIT, 2 days for most card-present. Once `payment_method_details.card.capture_before` passes, the funds are released and the intent transitions to `canceled` automatically. Any workflow that captures on fulfillment (shipping, check-out, service delivery) with a slower-than-7-day cycle loses the revenue.
- **detect**: `GET /v1/payment_intents?limit=100&expand[]=data.latest_charge` (paginate). Filter `data[].capture_method == "manual"`. For each, read `data[].latest_charge.payment_method_details.card.capture_before` and flag when it is `< now` (already lost) or `< now + 48h` (about to be lost) while `data[].status == "requires_capture"`. Also count `data[].status == "canceled" && data[].cancellation_reason == "automatic"` on manual-capture intents — that is the historical loss.
- **repair**: Capture within the window: `POST /v1/payment_intents/{id}/capture`. Add a daily job driven by `capture_before`. For flows that genuinely need longer, either request extended authorization (`payment_method_options[card][request_extended_authorization]=true`) or switch to `payment_method_options[card][capture_method]=automatic_delayed` with `capture_by=auth_expiry`, which makes Stripe capture ~6 hours before expiry.
- **category**: Payments & intents
- **sources**: https://docs.stripe.com/payments/place-a-hold-on-a-payment-method · https://docs.stripe.com/error-codes · https://stackoverflow.com/questions/33230810/stripe-cancel-a-pre-authorization

## uncaptured-charge-expiry-refunds

- **slug**: `uncaptured-charge-expiry-refunds`
- **title**: Refunds reason expired_uncaptured_charge: lost revenue
- **symptom**: Refund objects appear in the account that nobody in the business issued. The reported refund rate is inflated and reconciliation shows money that was authorized but never actually collected.
- **mechanism**: When an authorization expires without capture, Stripe generates a Refund with the Stripe-internal `reason: "expired_uncaptured_charge"`. This is the hard, after-the-fact proof of the capture-window failure above — it is not a customer-requested refund and it is not visible as one in most homegrown refund reports.
- **detect**: `GET /v1/refunds?limit=100&created[gte]={now-90d}` (paginate). Count `data[].reason == "expired_uncaptured_charge"`. Compute lost value as `sum(data[].amount)` for those, and express it as a percentage of `sum(amount)` across all refunds in the window. Cross-reference each `data[].charge` with `GET /v1/charges/{id}` to confirm `captured == false`.
- **repair**: Fix the capture pipeline (see `expired-manual-capture-holds`). Separately, exclude `reason == "expired_uncaptured_charge"` from customer-facing refund-rate metrics — these are integration failures, not returns. Add alerting on `charge.refund.updated` where reason equals this value.
- **category**: Payments & intents
- **sources**: https://docs.stripe.com/api/refunds/object · https://docs.stripe.com/payments/place-a-hold-on-a-payment-method

## radar-blocked-payments-ignored

- **slug**: `radar-blocked-payments-ignored`
- **title**: Radar blocks payments and no one reads the block reasons
- **symptom**: A visible slice of checkout attempts never reach the issuer. Support hears "my card works everywhere else." The charges show as failed with a generic message and no bank decline behind them.
- **mechanism**: Radar (and Adaptive Acceptance on IC+ pricing) blocks payments before authorization. The Charge records `outcome.type == "blocked"` with `outcome.network_status == "not_sent_to_network"` and a specific `outcome.reason` — `highest_risk_level`, `elevated_risk_level`, a custom `rule`, or `low_probability_of_authorization`. Custom rules written years ago (blocking a country, a BIN range, an amount ceiling) keep firing long after the fraud pattern they targeted is gone.
- **detect**: `GET /v1/charges?limit=100&created[gte]={now-30d}` (paginate). Filter `data[].outcome.type == "blocked"`. Group by `data[].outcome.reason` and report counts plus `sum(amount)` per reason. Flag when blocked charges exceed 2% of total charges, or when a single `outcome.reason == "rule"` accounts for the majority. Read `data[].outcome.seller_message` for the human-readable explanation.
- **repair**: In the Dashboard go to Radar → Rules and disable or narrow the rule identified by `outcome.reason`. For `highest_risk_level`, raise the block threshold and add a review threshold instead. For legitimate blocked payments, open the payment in the Dashboard and click **Add to allow list**. For `low_probability_of_authorization`, this is Adaptive Acceptance saving network fees — leave it alone but exclude it from your fraud metrics.
- **category**: Payments & intents
- **sources**: https://docs.stripe.com/declines · https://docs.stripe.com/api/charges/object

## elevated-risk-charges-no-review

- **slug**: `elevated-risk-charges-no-review`
- **title**: Elevated-risk charges captured with no manual review step
- **symptom**: Disputes arrive weeks after payments that Stripe already flagged as risky. Chargeback rate creeps toward the network threshold. Nobody remembers seeing a review queue.
- **mechanism**: Radar assigns each charge an `outcome.risk_level` of `normal`, `elevated`, `highest`, or `not_assessed`. `elevated` charges are authorized and captured by default unless a review rule places them in the manual review queue, which populates `charge.review`. Accounts that never configured a review rule capture every elevated-risk payment straight through and only find out at dispute time.
- **detect**: `GET /v1/charges?limit=100&created[gte]={now-90d}` (paginate). Filter `data[].outcome.risk_level == "elevated" && data[].outcome.type == "authorized"` and count how many have `data[].review == null` and `data[].captured == true`. Correlate with `data[].disputed == true` on that same subset to compute the elevated-risk dispute rate versus the `normal` baseline. Also flag if `outcome.risk_level == "not_assessed"` dominates, which means Radar sessions are not being collected from the client.
- **repair**: In the Dashboard, Radar → Rules, add "Place in review if `:risk_level:` = `elevated`" (or an amount-scoped variant such as `:risk_level: = 'elevated' and :amount_in_usd: > 100`). If `risk_level` is `not_assessed`, mount Stripe.js on the payment page so a Radar session is created, or pass `radar_options[session]` explicitly for server-side confirms.
- **category**: Payments & intents
- **sources**: https://docs.stripe.com/declines · https://docs.stripe.com/api/charges/object

## off-session-authentication-required-declines

- **slug**: `off-session-authentication-required-declines`
- **title**: Off-session charges die on authentication_required
- **symptom**: Saved-card charges for renewals or delayed billing fail with "Your card was declined." The `decline_code` is `authentication_required` or `authentication_not_handled`, and retrying the same card off-session fails identically.
- **mechanism**: Under SCA, an off-session merchant-initiated transaction is only exempt if the card was authenticated on-session when it was saved, and a mandate exists. If the card was saved by bare `POST /v1/payment_methods/{id}/attach` — without a SetupIntent or `setup_future_usage` — no mandate exists and the issuer soft-declines every off-session attempt. Stripe surfaces this as `billing_invalid_mandate` on invoice paths and `authentication_required` on the intent.
- **detect**: `GET /v1/payment_intents?limit=100&created[gte]={now-90d}` (paginate). Count `data[].last_payment_error.decline_code` in `("authentication_required", "authentication_not_handled")`. For each affected `data[].payment_method`, call `GET /v1/setup_intents?limit=100&customer={customer}` and check whether any SetupIntent for that customer has `status == "succeeded"` and non-null `mandate`; absence proves the card was never authenticated. Also count `GET /v1/charges` where `outcome.reason == "authentication_required"`.
- **repair**: Stop attaching payment methods directly. Save cards with `POST /v1/setup_intents` using `usage=off_session` and confirm it on-session so a `mandate` is generated, or save during payment with `POST /v1/payment_intents` + `setup_future_usage=off_session`. For already-broken saved cards, email customers a Setup Intent link to re-authenticate; then charge with `POST /v1/payment_intents` including `off_session=true` and `confirm=true`.
- **category**: Payments & intents
- **sources**: https://docs.stripe.com/strong-customer-authentication · https://docs.stripe.com/declines/codes · https://docs.stripe.com/error-codes

## testmode-decline-in-live-mode

- **slug**: `testmode-decline-in-live-mode`
- **title**: Live charges fail with testmode_decline from test cards
- **symptom**: Real customers get "Your card was declined" in production. Charges show `decline_code: "testmode_decline"`, or every live API call returns `resource_missing` saying "a similar object exists in test mode, but a live mode key was used."
- **mechanism**: Test card numbers (4242…, `pm_card_*`, `tok_visa`) and test-mode object IDs are rejected outright in live mode, and vice versa. This happens when a deploy ships with the wrong `sk_`/`pk_` pair, when a seeded price or customer ID from the sandbox is hardcoded, or when a live account was never activated so only `testmode_charges_only` applies. This is one of the highest-view Stripe questions on Stack Overflow (54k+).
- **detect**: With a live restricted key: `GET /v1/account` → flag if `charges_enabled == false` or `details_submitted == false` while payments are being attempted (this is the `testmode_charges_only` condition). Then `GET /v1/charges?limit=100` → count `data[].failure_code == "testmode_decline"` or `data[].outcome.reason == "testmode_decline"`. Also `GET /v1/payment_intents?limit=100` → count `data[].last_payment_error.code == "testmode_decline"`. If a live key returns zero objects across `/v1/charges`, `/v1/customers`, and `/v1/payment_intents` while the business is live, the app is pointed at test mode.
- **repair**: Rotate to matching live keys on both server (`sk_live_…`) and client (`pk_live_…`) and confirm they belong to the same account. Complete activation at https://dashboard.stripe.com/account/onboarding until `charges_enabled` is `true`. Remove hardcoded test-mode IDs and look prices/products up by `lookup_key` instead, so the same code resolves correctly in both modes.
- **category**: Payments & intents
- **sources**: https://stackoverflow.com/questions/28952987/stripe-no-such-token-a-similar-object-exists-in-test-mode-but-a-live-mode-ke · https://docs.stripe.com/declines/codes · https://docs.stripe.com/error-codes

## card-only-payment-method-types

- **slug**: `card-only-payment-method-types`
- **title**: Intents hardcode payment_method_types to card only
- **symptom**: The Payment Element renders a bare card form. Wallets, Link, buy-now-pay-later, and local methods never appear, even though they are enabled in the Dashboard. Conversion is flat in markets where cards are not the norm.
- **mechanism**: If a PaymentIntent is created with an explicit `payment_method_types` array, Stripe honours exactly that list and dynamic payment methods are bypassed entirely — Dashboard settings, payment method configurations, and the ordering models all become inert. Integrations written before API version 2023-08-16, or copied from old tutorials, almost always pin `payment_method_types: ['card']`.
- **detect**: `GET /v1/payment_intents?limit=100&created[gte]={now-30d}` (paginate). Flag when `data[].automatic_payment_methods == null` on the majority of intents, and when `data[].payment_method_types` equals `["card"]` (or `["card","link"]`) across nearly all of them. Cross-check what is actually available: `GET /v1/payment_method_configurations` → count entries where `<method>.available == true` but `<method>.display_preference.value == "on"` yet the method never appears in any intent's `payment_method_types`. A large gap between "available and on" and "actually offered" confirms the hardcode.
- **repair**: Remove `payment_method_types` from the create call and pass `automatic_payment_methods[enabled]=true` instead: `POST /v1/payment_intents -d amount=1099 -d currency=eur -d "automatic_payment_methods[enabled]=true"`. Manage the method list at https://dashboard.stripe.com/settings/payment_methods. Use `excluded_payment_method_types[]` for per-transaction exclusions rather than an allowlist.
- **category**: Payments & intents
- **sources**: https://docs.stripe.com/payments/payment-methods/dynamic-payment-methods · https://stackoverflow.com/questions/75761101/stripe-payment-element-not-showing-payment-options · https://stackoverflow.com/questions/72233594/stripe-api-no-valid-payment-method-types-for-this-payment-intent

## wallet-domain-not-registered

- **slug**: `wallet-domain-not-registered`
- **title**: No payment method domain registered, so wallets never show
- **symptom**: Apple Pay and Google Pay buttons appear on localhost or in the Stripe demo, but vanish in production. Mobile conversion is materially worse than desktop, and Link never surfaces either.
- **mechanism**: Apple Pay on the web, Google Pay, Link, and PayPal in Elements require the serving domain to be registered and verified with Stripe. Registration is per-domain and per-mode, so a domain verified in test mode does nothing in live mode, and a new subdomain (`checkout.example.com` vs `example.com`) needs its own registration. Without it the wallet is silently filtered out — no error is thrown.
- **detect**: `GET /v1/payment_method_domains?limit=100` with a live key. Flag if the list is empty. Otherwise, for each entry check `data[].enabled == true` and `data[].apple_pay.status == "active"`, `data[].google_pay.status == "active"`, `data[].link.status == "active"`; any status other than `active` (read `<wallet>.status_details.error_message`) means that wallet is dark. Compare `data[].domain_name` values against the domains you actually serve checkout from, and confirm `data[].livemode == true`.
- **repair**: Register the exact production domain: `POST /v1/payment_method_domains -d domain_name=checkout.example.com` in live mode, then host `/.well-known/apple-developer-merchantid-domain-association` (Stripe serves it automatically for Stripe-hosted flows). Re-validate with `POST /v1/payment_method_domains/{id}/validate`. Repeat per subdomain. Dashboard path: Settings → Payments → Payment method domains.
- **category**: Payments & intents
- **sources**: https://docs.stripe.com/api/payment_method_domains/object · https://stackoverflow.com/questions/71710164/apple-pay-button-not-show-in-stripe · https://stackoverflow.com/questions/76091660/stripe-paymentelement-not-showing-google-pay

## legacy-charges-api-no-payment-intent

- **slug**: `legacy-charges-api-no-payment-intent`
- **title**: Charges have null payment_intent: legacy Charges API
- **symptom**: European card decline rates are far above the account average. Charges exist with no corresponding PaymentIntent, and 3D Secure never triggers for any of them.
- **mechanism**: The direct Charges API (`POST /v1/charges` with a `source` or token) predates SCA and cannot perform 3D Secure authentication. Stripe explicitly warns that integrations still on it "might see high rates of declines from banks that enforce SCA." Every charge created this way has `payment_intent: null`, which makes the legacy path trivially countable.
- **detect**: `GET /v1/charges?limit=100&created[gte]={now-90d}` (paginate). Count `data[].payment_intent == null` — that is the legacy Charges API surface. Report it as a fraction of total charges and as `sum(amount)`. Then measure the damage: for that same subset compare the rate of `data[].outcome.type == "issuer_declined"` and `data[].outcome.reason == "authentication_required"` against the `payment_intent != null` subset. Also check `GET /v1/customers/{id}/sources?object=card` being non-empty, which is the companion legacy-storage signal.
- **repair**: Migrate to the Payment Intents API: replace `POST /v1/charges -d source=tok_… -d customer=cus_…` with `POST /v1/payment_intents -d amount=… -d currency=… -d customer=cus_… -d payment_method=pm_… -d confirm=true -d "automatic_payment_methods[enabled]=true"`, and handle `requires_action` on the client. Convert stored `card_*` sources to PaymentMethods before cutting over.
- **category**: Payments & intents
- **sources**: https://docs.stripe.com/strong-customer-authentication · https://docs.stripe.com/api/charges/object · https://stackoverflow.com/questions/50284633/stripe-payments-source-vs-token-card

## bank-debit-intents-stuck-processing

- **slug**: `bank-debit-intents-stuck-processing`
- **title**: Bank-debit intents stay in processing for over a week
- **symptom**: ACH, SEPA, or BECS payments sit at `status: "processing"` indefinitely. Orders are either fulfilled immediately (and later charged back) or never fulfilled at all, because the code only ever checks for `succeeded`.
- **mechanism**: Asynchronous payment methods take days to settle and legitimately pass through `processing`. But if the integration never subscribes to `payment_intent.succeeded` / `payment_intent.payment_failed` and only polls once at checkout, `processing` becomes a terminal state in the application's mind. Genuinely stuck intents — beyond the method's normal settlement window — indicate a mandate or verification problem.
- **detect**: `GET /v1/payment_intents?limit=100&created[lt]={now-7d}` (paginate). Filter `data[].status == "processing"` and inspect `data[].payment_method_types` for `us_bank_account`, `sepa_debit`, `acss_debit`, `au_becs_debit`, `bacs_debit`. Anything older than 7 days (ACH settles in ~4 business days, SEPA in ~5) is stuck. Corroborate with `GET /v1/charges?limit=100` counting `data[].status == "pending"` with the same age, and read `data[].payment_method_details.us_bank_account.status_details` for verification failures.
- **repair**: Register a webhook endpoint handling `payment_intent.succeeded`, `payment_intent.processing`, and `payment_intent.payment_failed`, and gate fulfilment on `succeeded` only. Where micro-deposit verification stalled, re-run it (`POST /v1/payment_intents/{id}/verify_microdeposits`). For long-dead intents use `POST /v1/payment_intents/{id}/cancel` — cancellation is permitted in `processing` for ACH/ACSS/BECS/BACS/SEPA within a limited window.
- **category**: Payments & intents
- **sources**: https://docs.stripe.com/payments/paymentintents/lifecycle · https://docs.stripe.com/api/payment_intents/object

## refunds-failed-or-stuck

- **slug**: `refunds-failed-or-stuck`
- **title**: Refunds sit failed or requires_action and nobody notices
- **symptom**: Support marked a refund as issued, the money left your Stripe balance, but the customer never received it. They open a dispute for the same transaction, so you pay twice plus the dispute fee.
- **mechanism**: A Refund is not final when created. It can land on `pending`, `requires_action`, or `failed`. `failure_reason` explains why: `expired_or_canceled_card` (card closed since the original charge), `lost_or_stolen_card`, `insufficient_funds`, `declined`, `charge_for_pending_refund_disputed`, or `unknown`. Most refund flows fire and forget, never listening for `charge.refund.updated`.
- **detect**: `GET /v1/refunds?limit=100&created[gte]={now-180d}` (paginate). Flag `data[].status in ("failed", "requires_action")` and group by `data[].failure_reason`. Separately flag `data[].status == "pending"` where `created < now - 10d`, and read `data[].pending_reason` (`processing`, `insufficient_funds`, `charge_pending`). Sum `data[].amount` for failed refunds — that is money debited from your balance that never reached anyone. Cross-check the corresponding `data[].charge` via `GET /v1/charges/{id}` for `disputed == true`.
- **repair**: Handle the `charge.refund.updated` webhook and treat `status == "failed"` as an open support ticket. For `expired_or_canceled_card`, refund out of band (bank transfer or credit) since retrying the same card will fail again. For `requires_action`, follow `refund.next_action` to give the customer the instructions link. Reconcile refunds against `failure_balance_transaction` so failed refunds are re-credited correctly in your ledger.
- **category**: Payments & intents
- **sources**: https://docs.stripe.com/api/refunds/object · https://docs.stripe.com/refunds

---

# Subscriptions & billing

## past-due-subscriptions-accumulating

- **slug**: `past-due-subscriptions-accumulating`
- **title**: past_due subscriptions keep billing but nobody revokes access
- **symptom**: A growing pile of subscriptions sits in `past_due`. Customers still have full product access because the app only checks `status != "canceled"`, and the invoices keep piling up unpaid.
- **mechanism**: With `collection_method=charge_automatically`, a failed renewal moves the subscription to `past_due` and Stripe keeps generating invoices each period. The Dashboard failed-payment setting decides whether it eventually becomes `canceled`, `unpaid`, or stays `past_due` forever — and "leave past due" is a valid, silent choice.
- **detect**: `GET /v1/subscriptions?status=past_due&limit=100&expand[]=data.latest_invoice`. Flag when `data[]` length > 0. Severity from `data[].latest_invoice.attempt_count` and age of `data[].latest_invoice.created`; compare count against `GET /v1/subscriptions?status=active&limit=100` for a ratio.
- **repair**: Dashboard → **Billing → Revenue recovery → Retries** → set the post-retry action to "Cancel the subscription" or "Mark the subscription as unpaid" instead of leaving past due. In code, gate provisioning on `status in ("active","trialing")` only, and for each stuck one call `POST /v1/subscriptions/{id}` with `cancel_at_period_end=true` or `DELETE /v1/subscriptions/{id}`.
- **category**: Subscriptions & billing
- **sources**: https://docs.stripe.com/api/subscriptions/object · https://docs.stripe.com/billing/subscriptions/overview · https://docs.stripe.com/billing/revenue-recovery/smart-retries

## subscriptions-stuck-incomplete

- **slug**: `subscriptions-stuck-incomplete`
- **title**: incomplete subscriptions die silently after 23 hours
- **symptom**: Subscriptions created hours ago are still `incomplete`. The customer thinks they subscribed, your app shows nothing, and in under a day the record becomes unrecoverable.
- **mechanism**: When the first invoice on a `charge_automatically` subscription isn't paid, the subscription stays `incomplete` for exactly 23 hours, then transitions to the terminal `incomplete_expired` and the open invoice is voided. An integration that creates the subscription but never confirms the PaymentIntent (or loses the client secret) leaves every signup in this window.
- **detect**: `GET /v1/subscriptions?status=incomplete&limit=100`. Flag any where `now - data[].created > 82800` (23 h), and flag the whole integration if the count of `status=incomplete` older than 1 hour is a meaningful fraction of daily signups.
- **repair**: Create subscriptions with `payment_behavior=default_incomplete`, surface the resulting invoice's PaymentIntent client secret to the client, and confirm it in the same session. For records already past 23 hours you cannot revive them — create a new subscription: `POST /v1/subscriptions` with `customer`, `items[0][price]`, `default_payment_method`.
- **category**: Subscriptions & billing
- **sources**: https://docs.stripe.com/api/subscriptions/object · https://docs.stripe.com/billing/collection-method · https://docs.stripe.com/billing/subscriptions/overview

## incomplete-expired-signup-leak

- **slug**: `incomplete-expired-signup-leak`
- **title**: incomplete_expired volume means checkout confirmation is broken
- **symptom**: Dozens or hundreds of `incomplete_expired` subscriptions accumulate. Nobody was ever charged, no error was logged, and revenue quietly never appeared.
- **mechanism**: `incomplete_expired` is the terminal state for a first invoice that went unpaid for 23 hours. A high volume relative to activations is not a card-decline problem — it's a confirmation-flow bug: the client never calls `confirmCardPayment` / `handleNextAction`, or the server creates the subscription and redirects away.
- **detect**: `GET /v1/subscriptions?status=incomplete_expired&limit=100&created[gte]=<unix 30d ago>`. Compute the ratio against `GET /v1/subscriptions?status=active&limit=100&created[gte]=<same>`. Flag when expired ≥ ~10% of activations in the window.
- **repair**: Switch subscription creation to `payment_behavior=default_incomplete`, expand `latest_invoice.confirmation_secret`, and confirm client-side. Add a server-side `invoice.payment_action_required` / `checkout.session.completed` handler so abandoned confirmations are retried by email rather than expiring.
- **category**: Subscriptions & billing
- **sources**: https://docs.stripe.com/api/subscriptions/create · https://docs.stripe.com/billing/subscriptions/overview · https://docs.stripe.com/billing/collection-method

## unpaid-subscriptions-still-provisioned

- **slug**: `unpaid-subscriptions-still-provisioned`
- **title**: unpaid subscriptions still have access but never bill again
- **symptom**: Customers in `unpaid` are still using the product. Invoices keep generating but stay in `draft` and no payment is ever attempted, so the balance owed grows and nothing collects it.
- **mechanism**: `unpaid` is the end-of-dunning alternative to `canceled`. Stripe's docs are explicit: once a subscription is `unpaid`, subsequent invoices are created but immediately closed and payments aren't attempted. Teams that only revoke on `canceled` never notice.
- **detect**: `GET /v1/subscriptions?status=unpaid&limit=100`; flag any results. Then per subscription `GET /v1/invoices?subscription={sub_id}&status=draft&limit=100` — a stack of draft invoices confirms billing has silently stopped.
- **repair**: Revoke entitlement on `unpaid` in your provisioning check. To collect, `POST /v1/invoices/{id}/send` on the past-due invoice, or `POST /v1/invoices/{id}` with `auto_advance=true` on the drafts. To stop the bleed, change **Billing → Revenue recovery → Retries** end behavior to "Cancel the subscription".
- **category**: Subscriptions & billing
- **sources**: https://docs.stripe.com/api/subscriptions/object · https://docs.stripe.com/billing/collection-method · https://docs.stripe.com/billing/subscriptions/overview

## subscription-without-payment-method

- **slug**: `subscription-without-payment-method`
- **title**: Active subscriptions with no payment method anywhere to charge
- **symptom**: Subscriptions look `active` and healthy, then fail 100% of renewals. Retries never execute because Stripe has nothing to charge.
- **mechanism**: Stripe resolves a payment method in a strict order: `subscription.default_payment_method` → `subscription.default_source` → `customer.invoice_settings.default_payment_method` → `customer.default_source`. If all four are null the renewal invoice can never be paid, and the smart-retry docs state Stripe doesn't retry at all when no payment method is available.
- **detect**: `GET /v1/subscriptions?status=active&limit=100&expand[]=data.customer`, then flag rows where all of `data[].default_payment_method`, `data[].default_source`, `data[].customer.invoice_settings.default_payment_method`, and `data[].customer.default_source` are `null`. Repeat for `status=trialing`.
- **repair**: For each customer, collect a card via a SetupIntent or the billing portal, then `POST /v1/customers/{cus}` with `invoice_settings[default_payment_method]={pm}` — and set it on the subscription too with `POST /v1/subscriptions/{sub}` `default_payment_method={pm}`, because retries follow the field the failure occurred on.
- **category**: Subscriptions & billing
- **sources**: https://docs.stripe.com/billing/revenue-recovery/smart-retries · https://docs.stripe.com/api/subscriptions/object

## sca-authentication-stuck-subscriptions

- **slug**: `sca-authentication-stuck-subscriptions`
- **title**: Subscriptions frozen on requires_action 3DS authentication
- **symptom**: European customers subscribe, the card is fine, but the subscription never activates. The invoice stays `open` and the payment sits waiting for a challenge nobody ever showed the customer.
- **mechanism**: When an issuer demands 3DS, the PaymentIntent goes to `requires_action`, the invoice stays `open`, and the subscription stays `incomplete`. `authentication_required` is also on Stripe's hard-decline list, so retries are scheduled but never execute until a new payment method appears.
- **detect**: On API versions before `2025-03-31.basil`: `GET /v1/subscriptions?status=incomplete&limit=100&expand[]=data.latest_invoice.payment_intent` → flag `data[].latest_invoice.payment_intent.status == "requires_action"`. On Basil and later: `GET /v1/invoices?status=open&limit=100&expand[]=data.payments.data.payment.payment_intent` → same status check.
- **repair**: Turn on Dashboard → **Settings → Billing → Automatic collection** reminder emails so Stripe mails the Hosted Invoice Page link on `requires_action`. In-app, handle the `invoice.payment_action_required` event and pass the client secret to `stripe.handleNextAction`.
- **category**: Subscriptions & billing
- **sources**: https://docs.stripe.com/billing/subscriptions/overview · https://docs.stripe.com/invoicing/integration/workflow-transitions · https://docs.stripe.com/billing/revenue-recovery/smart-retries

## trial-ends-without-payment-method

- **slug**: `trial-ends-without-payment-method`
- **title**: Trials about to end with no payment method on file
- **symptom**: A cohort of `trialing` subscriptions has no card attached. On the trial end date they all fail at once, flooding `past_due` (or vanishing into `paused`, depending on config).
- **mechanism**: `trial_settings.end_behavior.missing_payment_method` defaults to `create_invoice` — Stripe cuts an invoice that immediately fails. The alternatives are `pause` (subscription enters the `paused` status and stops invoicing) and `cancel`. Only `pause` produces a recoverable state; `create_invoice` produces silent dunning.
- **detect**: `GET /v1/subscriptions?status=trialing&limit=100&expand[]=data.customer`. Flag rows where `data[].trial_end` is within the next 72 hours AND `data[].default_payment_method`, `data[].default_source`, and `data[].customer.invoice_settings.default_payment_method` are all `null`. Cross-tab by `data[].trial_settings.end_behavior.missing_payment_method`.
- **repair**: `POST /v1/subscriptions/{sub}` with `trial_settings[end_behavior][missing_payment_method]=pause` so no-card trials pause instead of dunning, and act on the `customer.subscription.trial_will_end` webhook (fires 3 days out) to email a billing-portal link for card capture.
- **category**: Subscriptions & billing
- **sources**: https://docs.stripe.com/billing/subscriptions/trials · https://docs.stripe.com/api/subscriptions/object · https://docs.stripe.com/billing/collection-method

## paused-subscriptions-never-resumed

- **slug**: `paused-subscriptions-never-resumed`
- **title**: paused subscriptions never resume and stop invoicing forever
- **symptom**: Subscriptions in `paused` accumulate indefinitely. No invoices are generated, no revenue arrives, and no one is chasing these customers because they don't show up in past-due reports.
- **mechanism**: `paused` is only reachable when a trial ends without a payment method and `missing_payment_method=pause`. Stripe stops creating invoices entirely and the subscription stays `paused` until explicitly resumed after a default payment method is attached — there is no automatic timeout.
- **detect**: `GET /v1/subscriptions?status=paused&limit=100`. Flag all, and bucket by age using `data[].trial_end` or `data[].start_date`; anything older than one billing interval is dead inventory.
- **repair**: Handle `customer.subscription.paused` by revoking access and starting a win-back email sequence pointing at the billing portal. To resume after a card is attached: `POST /v1/subscriptions/{sub}` with `pause_collection=""` and a valid `default_payment_method` (this may generate an invoice that must be paid before the status leaves `paused`).
- **category**: Subscriptions & billing
- **sources**: https://docs.stripe.com/billing/subscriptions/overview · https://docs.stripe.com/billing/subscriptions/trials · https://github.com/stripe/stripe-dotnet/issues/2592

## pause-collection-left-on-indefinitely

- **slug**: `pause-collection-left-on-indefinitely`
- **title**: pause_collection with no resumes_at quietly bills nothing
- **symptom**: A subscription reads `active` in every report, but no money has arrived for months. Invoices are draft, uncollectible, or voided depending on the behavior chosen.
- **mechanism**: `pause_collection` is entirely separate from the `paused` status — the docs are explicit that the subscription status is unchanged. If `resumes_at` is null, collection stays paused until a human unsets it. A one-off support grace period becomes permanent.
- **detect**: `GET /v1/subscriptions?status=active&limit=100`, then flag rows where `data[].pause_collection != null` AND `data[].pause_collection.resumes_at == null`. Confirm the damage with `GET /v1/invoices?subscription={sub}&status=draft&limit=100` (behavior `keep_as_draft`) or `status=void` / `status=uncollectible`.
- **repair**: `POST /v1/subscriptions/{sub}` with `pause_collection=` (empty value) to resume. Then for each stranded draft, `POST /v1/invoices/{inv}` with `auto_advance=true` to restart collection. Going forward always set `pause_collection[resumes_at]` to a real timestamp.
- **category**: Subscriptions & billing
- **sources**: https://docs.stripe.com/billing/subscriptions/pause-payment · https://docs.stripe.com/api/subscriptions/object

## send-invoice-without-days-until-due

- **slug**: `send-invoice-without-days-until-due`
- **title**: send_invoice subscriptions with no days_until_due set
- **symptom**: Invoiced (non-card) customers get invoices with no due date. Nothing ever goes "past due", no reminders fire, and the AR ages invisibly.
- **mechanism**: `days_until_due` is what populates `invoice.due_date` for `collection_method=send_invoice`; it is null for `charge_automatically` and optional on creation. Without a `due_date`, the past-due machinery (reminders, the 30/60/90-day subscription action) has no anchor to fire against.
- **detect**: `GET /v1/subscriptions?collection_method=send_invoice&status=all&limit=100` → flag rows where `data[].days_until_due == null`. Corroborate with `GET /v1/invoices?collection_method=send_invoice&status=open&limit=100` → `data[].due_date == null`.
- **repair**: `POST /v1/subscriptions/{sub}` with `days_until_due=30` (or your terms). Then Dashboard → **Settings → Billing → Invoices** → enable up to three reminders and set the post-due-date subscription action (30/60/90 days) to cancel or mark unpaid.
- **category**: Subscriptions & billing
- **sources**: https://docs.stripe.com/billing/collection-method · https://docs.stripe.com/api/subscriptions/object · https://docs.stripe.com/api/invoices/object

## cancel-at-period-end-churn-backlog

- **slug**: `cancel-at-period-end-churn-backlog`
- **title**: A wall of cancel_at_period_end subscriptions nobody noticed
- **symptom**: MRR looks flat because everything is still `active`, but a large share of those subscriptions are already scheduled to terminate at their next renewal date.
- **mechanism**: `cancel_at_period_end=true` leaves `status` as `active` right up until the period boundary — the churn is fully committed but invisible to any status-based dashboard. `canceled_at` reflects when the flag was set, not when service ends, which hides the trend further.
- **detect**: `GET /v1/subscriptions?status=active&limit=100` → count where `data[].cancel_at_period_end == true` (also `data[].cancel_at != null`). Divide by total `active` for a pending-churn rate; bucket by `data[].items.data[0].current_period_end` to see the cliff, and read `data[].cancellation_details.feedback` for reasons.
- **repair**: Reactivate salvageable ones with `POST /v1/subscriptions/{sub}` `cancel_at_period_end=false`. Structurally: enable the billing portal's `subscription_cancel.cancellation_reason` so reasons get captured, and trigger save-offer emails off `customer.subscription.updated` when the flag flips.
- **category**: Subscriptions & billing
- **sources**: https://docs.stripe.com/api/subscriptions/object · https://docs.stripe.com/api/subscriptions/list · https://docs.stripe.com/api/customer_portal/configurations/object

## save-default-payment-method-off

- **slug**: `save-default-payment-method-off`
- **title**: save_default_payment_method off orphans the card after payment
- **symptom**: The first charge succeeds, but every renewal fails. The card that just worked was never promoted to the subscription's default.
- **mechanism**: `payment_settings.save_default_payment_method` defaults to `off`. A card confirmed on the first invoice's PaymentIntent is used once and never attached as `subscription.default_payment_method`, so the next cycle falls back to the customer default — which may not exist.
- **detect**: `GET /v1/subscriptions?status=active&limit=100&expand[]=data.customer` → flag rows where `data[].payment_settings.save_default_payment_method == "off"` AND `data[].default_payment_method == null` AND `data[].customer.invoice_settings.default_payment_method == null`. A high count across all subscriptions means the create call never sets it.
- **repair**: Set it at creation: `POST /v1/subscriptions` with `payment_settings[save_default_payment_method]=on_subscription`. For existing ones the field is updatable even while `incomplete`: `POST /v1/subscriptions/{sub}` `payment_settings[save_default_payment_method]=on_subscription`.
- **category**: Subscriptions & billing
- **sources**: https://docs.stripe.com/api/subscriptions/object · https://docs.stripe.com/billing/collection-method · https://docs.stripe.com/api/subscriptions/create

## metered-items-with-no-usage-reported

- **slug**: `metered-items-with-no-usage-reported`
- **title**: Metered subscription items with zero usage events reported
- **symptom**: Usage-based subscriptions invoice for 0 (or only the flat fee) every cycle. Customers are clearly using the product; Stripe has no record of it.
- **mechanism**: A metered price bills whatever the attached Billing Meter aggregated. If your emitter sends the wrong `event_name`, or the payload key doesn't match the meter's `customer_mapping.event_payload_key` / `value_settings.event_payload_key`, the events are dropped and the meter aggregates to zero. Billing Meters only reconciles at invoice time, so nothing surfaces until the invoice is wrong.
- **detect**: `GET /v1/billing/meters?status=active&limit=100`. For each metered subscription item (`data[].items.data[].price.recurring.usage_type == "metered"`), call `GET /v1/billing/meters/{meter_id}/event_summaries?customer={cus_id}&start_time={current_period_start}&end_time={now}`. Flag when `data` is empty or every `data[].aggregated_value == 0`. Corroborate with `GET /v1/invoices?subscription={sub}&status=paid` → line `amount == 0`.
- **repair**: Compare your emitter's payload against the meter: `GET /v1/billing/meters/{id}` gives the required `event_name`, `customer_mapping.event_payload_key`, and `value_settings.event_payload_key`. Fix the emitter, then backfill with `POST /v1/billing/meter_events` before the period closes (events can't be added after the invoice finalizes).
- **category**: Subscriptions & billing
- **sources**: https://docs.stripe.com/api/billing/meter/object · https://docs.stripe.com/api/billing/meter-event_summary/list · https://docs.stripe.com/billing/subscriptions/usage-based

---

# Invoices & tax

## draft-invoices-never-finalized

- **slug**: `draft-invoices-never-finalized`
- **title**: Draft invoices older than 30 days that never finalized
- **symptom**: Invoices sit in `draft` for weeks or months. They have no number, no `hosted_invoice_url`, no PDF — and Stripe explicitly cannot collect payment on an unfinalized invoice.
- **mechanism**: Stripe auto-finalizes roughly 1 hour after successful `invoice.created` webhook delivery (up to 72 hours if endpoints are failing). Invoices created with `auto_advance=false` — the default under `payment_behavior=default_incomplete`, under `pause_collection[behavior]=keep_as_draft`, and for subscriptions that went `unpaid` — never advance on their own.
- **detect**: `GET /v1/invoices?status=draft&limit=100&created[lt]=<unix now-30d>`. Flag every result; inspect `data[].auto_advance` (`false` = will never advance), `data[].automatically_finalizes_at` (`null` = nothing scheduled), and `data[].amount_due` for the money at stake.
- **repair**: `POST /v1/invoices/{id}/finalize` for the ones you want to collect, or `POST /v1/invoices/{id}` with `auto_advance=true` to hand the invoice back to Stripe's automatic collection. Delete the ones you don't want: `DELETE /v1/invoices/{id}` (drafts only). Also verify webhook endpoints are returning 2xx — failing endpoints delay finalization.
- **category**: Invoices & tax
- **sources**: https://docs.stripe.com/invoicing/integration/workflow-transitions · https://docs.stripe.com/api/invoices/object · https://docs.stripe.com/billing/subscriptions/pause-payment

## draft-invoices-blocked-by-tax-location

- **slug**: `draft-invoices-blocked-by-tax-location`
- **title**: Invoices stuck in draft on customer_tax_location_invalid
- **symptom**: Subscriptions stay `active`, customers keep their access, but renewal invoices are frozen in `draft` and no payment is ever collected. Revenue silently flatlines for a subset of customers.
- **mechanism**: With Stripe Tax enabled, finalization requires a resolvable customer location — a country for non-US, a 5-digit ZIP for US, a province or postal code for Canada. If the address is missing or unresolvable, finalization fails with `customer_tax_location_invalid` and the invoice stays draft. (Stripe added an auto-disable fallback in late 2024, but historical drafts remain stuck.)
- **detect**: `GET /v1/invoices?status=draft&limit=100` → flag `data[].last_finalization_error.code == "customer_tax_location_invalid"`, or `data[].automatic_tax.status == "requires_location_inputs"`, or `data[].automatic_tax.disabled_reason == "finalization_requires_location_inputs"`. Confirm the root cause with `GET /v1/customers/{cus}?expand[]=tax` → `tax.automatic_tax == "unrecognized_location"`.
- **repair**: Fix the customer: `POST /v1/customers/{cus}` with `address[country]`, `address[postal_code]`, `address[state]`, `tax[validate_location]=immediately`. Then `POST /v1/invoices/{id}/finalize`. If you can't get an address, `POST /v1/invoices/{id}` with `automatic_tax[enabled]=false` before finalizing. Prevent recurrences by collecting `address` in Checkout and enabling `customer_update.allowed_updates=address` in the billing portal.
- **category**: Invoices & tax
- **sources**: https://support.stripe.com/questions/manage-draft-subscription-invoices-with-invalid-tax-location-details · https://docs.stripe.com/tax/invoicing · https://docs.stripe.com/api/invoices/object

## open-invoices-past-due-date

- **slug**: `open-invoices-past-due-date`
- **title**: open invoices past their due_date with nobody chasing them
- **symptom**: Invoiced customers have finalized invoices sitting unpaid weeks past the due date. No reminder went out and the subscription never changed status.
- **mechanism**: For `collection_method=send_invoice`, Stripe emails the invoice and waits — it does not auto-charge. Reminders and the 30/60/90-day subscription action are opt-in Dashboard settings; with them off, an overdue invoice just sits at `open` indefinitely.
- **detect**: `GET /v1/invoices?status=open&collection_method=send_invoice&limit=100` (the list endpoint has **no** server-side `due_date` filter), then filter client-side for `data[].due_date != null && data[].due_date < now`. Rank by `data[].amount_remaining` and days overdue. Add `data[].status_transitions.finalized_at` for aging.
- **repair**: Dashboard → **Settings → Billing → Invoices** → enable reminder emails (up to three, from 10 days before to 60 days after due) and set the past-due subscription action. Per invoice: `POST /v1/invoices/{id}/send` to re-send, or `POST /v1/invoices/{id}/mark_uncollectible` to clear the AR honestly.
- **category**: Invoices & tax
- **sources**: https://docs.stripe.com/billing/collection-method · https://docs.stripe.com/api/invoices/list · https://docs.stripe.com/api/invoices/object

## dunning-retries-exhausted

- **slug**: `dunning-retries-exhausted`
- **title**: Invoices where retries ran out and no attempt is scheduled
- **symptom**: Open invoices with several failed attempts and no future attempt planned. Stripe has given up; your team never found out.
- **mechanism**: After the final Smart Retry (default 8 tries over 2 weeks), Stripe makes no further attempts and `next_payment_attempt` goes null. On a hard decline (`lost_card`, `stolen_card`, `authentication_required`, `transaction_not_allowed`, …) retries are still *scheduled* and `attempt_count` still increments, but they only execute once a new payment method appears — so a high count with no new charges is the signature.
- **detect**: `GET /v1/invoices?status=open&collection_method=charge_automatically&limit=100` → flag `data[].attempt_count >= 4 && data[].next_payment_attempt == null && data[].amount_remaining > 0`. Separately flag `attempt_count` high AND `next_payment_attempt != null` for the hard-decline stall.
- **repair**: Dashboard → **Billing → Revenue recovery → Retries** → enable Smart Retries (8 tries / 2 weeks) and pick an end-of-dunning action. Per customer, collect a new card and set it on the field that failed (`POST /v1/subscriptions/{sub}` `default_payment_method={pm}`), then `POST /v1/invoices/{id}/pay`. Write off the rest with `POST /v1/invoices/{id}/mark_uncollectible`.
- **category**: Invoices & tax
- **sources**: https://docs.stripe.com/billing/revenue-recovery/smart-retries · https://docs.stripe.com/api/invoices/object

## automatic-tax-disabled-everywhere

- **slug**: `automatic-tax-disabled-everywhere`
- **title**: automatic_tax disabled on every invoice while selling abroad
- **symptom**: Invoices to Germany, France, and the UK carry zero VAT. Nothing errors — the totals are just wrong, and the liability compounds every month until an audit finds it.
- **mechanism**: `automatic_tax.enabled` defaults to `false` on subscriptions and invoices. Enabling Stripe Tax in the Dashboard only affects *new* Dashboard-created invoices; API-created subscriptions keep billing untaxed unless the create call passes `automatic_tax[enabled]=true`.
- **detect**: `GET /v1/subscriptions?automatic_tax[enabled]=false&status=active&limit=100` → count. Then `GET /v1/invoices?status=paid&limit=100` and cross-tab `data[].automatic_tax.enabled == false` against the set of distinct `data[].customer_address.country`. Flag when tax is off and you're invoicing more than one country (especially any EU/UK/AU/CA country).
- **repair**: Backfill existing subscriptions: `POST /v1/subscriptions/{sub}` with `automatic_tax[enabled]=true`. Set it on every create path — `POST /v1/subscriptions` and `POST /v1/checkout/sessions` both take `automatic_tax[enabled]=true`. Note you must have active registrations first, or tax still computes to zero.
- **category**: Invoices & tax
- **sources**: https://docs.stripe.com/tax/invoicing · https://docs.stripe.com/api/subscriptions/list · https://docs.stripe.com/api/invoices/object

## automatic-tax-requires-location-inputs

- **slug**: `automatic-tax-requires-location-inputs`
- **title**: automatic_tax.status is requires_location_inputs or failed
- **symptom**: Stripe Tax is on, but individual invoices carry no tax or fail to finalize. The failure is per-customer, so it hides inside an otherwise-working integration.
- **mechanism**: `automatic_tax.status` reports the last calculation: `complete`, `failed` (Stripe-side error), or `requires_location_inputs` — "the location details supplied on the customer aren't valid or don't provide enough location information". Checkout without billing-address collection, or API-created customers with no `address`, produce this at scale.
- **detect**: `GET /v1/invoices?limit=100&created[gte]=<unix 90d ago>` → flag `data[].automatic_tax.status in ("requires_location_inputs","failed")` and `data[].automatic_tax.disabled_reason in ("finalization_requires_location_inputs","finalization_system_error")`. Confirm per customer: `GET /v1/customers/{cus}?expand[]=tax` → `tax.automatic_tax` of `unrecognized_location` or `not_collecting`, and `tax.location`.
- **repair**: `POST /v1/customers/{cus}` with a full `address` plus `tax[validate_location]=immediately` (or `tax[ip_address]` as a fallback). In Checkout set `billing_address_collection=required`. For invoices already stuck, re-finalize after fixing the address: `POST /v1/invoices/{id}/finalize`.
- **category**: Invoices & tax
- **sources**: https://docs.stripe.com/api/invoices/object · https://docs.stripe.com/tax/invoicing · https://docs.stripe.com/tax/customer-locations

## no-tax-registrations-while-selling-abroad

- **slug**: `no-tax-registrations-while-selling-abroad`
- **title**: No tax registrations while invoicing many countries
- **symptom**: Stripe Tax is enabled, `automatic_tax.status` is `complete`, and every invoice still shows zero tax with `taxability_reason: not_collecting`. It looks like it's working.
- **mechanism**: Stripe only calculates tax where you hold an active Registration. Without one in the customer's jurisdiction the calculation returns zero — a successful calculation of nothing. Meanwhile economic-nexus thresholds accrue silently; Stripe only emails threshold alerts once you exceed $10k yearly revenue and only in live mode.
- **detect**: `GET /v1/tax/registrations?status=active&limit=100` → collect `data[].country` (and `data[].country_options.us.state`). Separately `GET /v1/invoices?status=paid&limit=100&created[gte]=<unix 365d ago>` → collect distinct `data[].customer_address.country`. Flag every billed country absent from the registration set; also flag `GET /v1/tax/registrations?status=expired` results with a non-null `expires_at` in the past.
- **repair**: Register with each authority, then record it: `POST /v1/tax/registrations` with `country=DE`, `country_options[de][type]=standard`, `active_from=now`. Review Dashboard → **Tax → Locations → Needs attention** for threshold breaches, and set notification preferences under **Settings → Tax → Thresholds**.
- **category**: Invoices & tax
- **sources**: https://docs.stripe.com/api/tax/registrations/all · https://docs.stripe.com/tax/zero-tax · https://docs.stripe.com/tax/monitoring

## prices-with-tax-behavior-unspecified

- **slug**: `prices-with-tax-behavior-unspecified`
- **title**: Prices left at tax_behavior unspecified break tax math
- **symptom**: Tax amounts are wrong or absent, and adding those line items to an automatic-tax invoice fails outright.
- **mechanism**: `tax_behavior` defaults to `unspecified`, meaning Stripe doesn't know whether the amount includes tax. The invoice docs state plainly that items with `tax_behavior=unspecified` **cannot be added to automatic tax invoices**. The field is also immutable once set to `inclusive` or `exclusive` — you must create a replacement price.
- **detect**: `GET /v1/prices?active=true&limit=100` → flag `data[].tax_behavior == "unspecified"`. Cross-reference which of those are live: for each flagged `price.id`, `GET /v1/subscriptions?price={price_id}&status=active&limit=100` and count. Also check `GET /v1/products?active=true&limit=100` → `data[].tax_code == null`.
- **repair**: Set a default in Dashboard → **Settings → Tax** so new prices inherit it. For each live price, create a replacement — `POST /v1/prices` with `product`, `unit_amount`, `currency`, `recurring[interval]`, `tax_behavior=exclusive` — migrate subscriptions with `POST /v1/subscriptions/{sub}` `items[0][id]=...&items[0][price]=<new>&proration_behavior=none`, then `POST /v1/prices/{old}` `active=false`. Set product tax codes with `POST /v1/products/{prod}` `tax_code=txcd_...`.
- **category**: Invoices & tax
- **sources**: https://docs.stripe.com/api/prices/object · https://docs.stripe.com/api/invoices/object · https://docs.stripe.com/tax/invoicing

## missing-customer-tax-ids-b2b-eu

- **slug**: `missing-customer-tax-ids-b2b-eu`
- **title**: EU B2B invoices with no customer_tax_ids miss reverse charge
- **symptom**: Business customers in the EU are charged local VAT they shouldn't pay, and their finance teams reject the invoice because it carries no VAT number and no reverse-charge notice.
- **mechanism**: Stripe Tax applies reverse charge automatically **based on the presence of a valid tax ID** and the jurisdictions involved. No tax ID means Stripe treats the sale as B2C and charges VAT. Worse, finalization freezes `customer_tax_ids` and `customer_tax_exempt` onto the invoice permanently — adding the VAT number afterwards does nothing for that document.
- **detect**: `GET /v1/invoices?status=paid&limit=100&created[gte]=<unix 180d ago>` → flag rows where `data[].customer_tax_ids` is `[]` AND `data[].customer_address.country` is an EU member AND `data[].customer_tax_exempt == "none"` AND `data[].total_taxes` is non-empty. Per customer, confirm with `GET /v1/customers/{cus}/tax_ids` (empty), and check `data[].verification.status` for `unverified` on the ones that do exist.
- **repair**: Collect the VAT number and `POST /v1/tax_ids` with `type=eu_vat`, `value=DE123456789`, `owner[type]=customer`, `owner[customer]={cus}` — then verify `verification.status` reaches `verified` (VIES). Enable `customer_update.allowed_updates[]=tax_id` on the billing portal and `tax_id_collection[enabled]=true` in Checkout. Already-finalized invoices can't be edited: void and reissue, or issue a credit note via `POST /v1/credit_notes`.
- **category**: Invoices & tax
- **sources**: https://docs.stripe.com/billing/customer/tax-ids · https://docs.stripe.com/tax/zero-tax · https://docs.stripe.com/invoicing/integration/workflow-transitions

## orphaned-pending-invoice-items

- **slug**: `orphaned-pending-invoice-items`
- **title**: Pending invoice items that never got attached to an invoice
- **symptom**: One-off charges, overages, and manual prorations were created months ago and have never appeared on any invoice. The revenue is recorded nowhere.
- **mechanism**: An invoice item with `invoice: null` is "pending" — it waits to be swept onto the customer's next invoice. If the customer has no active subscription, or the subscription was canceled (which stops new invoice generation), or `proration_behavior=none` was used without a follow-up invoice, the item waits forever.
- **detect**: `GET /v1/invoiceitems?pending=true&limit=100` → flag rows where `now - data[].date > 60 days`. Bucket by `data[].customer` and sum `data[].amount` for exposure. Cross-check whether each customer still has a live subscription: `GET /v1/subscriptions?customer={cus}&status=active&limit=100` — an empty result means the item will never be swept up.
- **repair**: Sweep them onto a real invoice: `POST /v1/invoices` with `customer={cus}`, `collection_method=charge_automatically`, `auto_advance=true`, then `POST /v1/invoices/{id}/finalize`. Delete the ones that are no longer owed with `DELETE /v1/invoiceitems/{id}`. To prevent recurrence, set `pending_invoice_item_interval` on the subscription, or use `proration_behavior=always_invoice` instead of `create_prorations` when the change should bill immediately.
- **category**: Invoices & tax
- **sources**: https://docs.stripe.com/api/invoiceitems/list · https://docs.stripe.com/api/invoiceitems/object · https://docs.stripe.com/billing/subscriptions/prorations

---

# Connect & payouts

## connected-accounts-charges-disabled

- **slug**: `connected-accounts-charges-disabled`
- **title**: Connected accounts sit with charges_enabled false unnoticed
- **symptom**: A seller's checkout returns errors or their payments silently route nowhere, and support hears about it weeks later. The platform dashboard looks fine because the platform account itself is healthy.
- **mechanism**: `charges_enabled` flips to `false` whenever a capability the account depends on goes inactive, whether from unmet KYC, a risk review, or a platform pause. Nothing pushes this to your app unless you subscribe to `account.updated`, so the account stays broken until someone complains.
- **detect**: `GET /v1/accounts?limit=100` (paginate with `starting_after`) → flag any `data[].charges_enabled == false`. Cross-reference `data[].requirements.disabled_reason` for the cause and `data[].capabilities.card_payments != "active"`.
- **repair**: Read `requirements.currently_due`, then `POST /v1/account_links` with `account=acct_x`, `type=account_onboarding`, `collection_options[fields]=currently_due` and send the account owner to the returned `url`. For `disabled_reason` values in the `rejected.*` / `under_review` family, resolve from the Dashboard Connected accounts page instead — the API can't clear them.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/api/accounts/object · https://docs.stripe.com/connect/handling-api-verification

## requirements-past-due-disables-account

- **slug**: `requirements-past-due-disables-account`
- **title**: requirements.past_due already disabled the account's payouts
- **symptom**: A connected account was working, then payouts stop with no error from your code. `payouts_enabled` is `false` and `requirements.disabled_reason` reads `requirements.past_due`.
- **mechanism**: Fields in `currently_due` that aren't resolved before `requirements.current_deadline` move into `past_due`, and Stripe disables the capabilities that depend on them. `past_due` is a strict subset of `currently_due`, so a script that only checks `currently_due.length` can't tell "warning" from "already broken."
- **detect**: `GET /v1/accounts?limit=100` → alert where `data[].requirements.past_due` has length > 0, or `data[].requirements.disabled_reason == "requirements.past_due"`. Get the per-capability breakdown with `GET /v1/accounts/{id}/capabilities` → `data[].requirements.past_due`.
- **repair**: `POST /v1/accounts/{id}` supplying every string in `requirements.past_due` (e.g. `company[tax_id]`, `business_profile[url]`), or `POST /v1/account_links` with `type=account_onboarding` and `collection_options[fields]=eventually_due` so the account clears future items in the same session.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/connect/handling-api-verification · https://docs.stripe.com/api/accounts/object

## current-deadline-passes-unwatched

- **slug**: `current-deadline-passes-unwatched`
- **title**: current_deadline passes before you collect currently_due fields
- **symptom**: Accounts look healthy (`charges_enabled: true`, `payouts_enabled: true`) right up until a fixed date, then a whole cohort breaks at once because they all hit the same threshold deadline.
- **mechanism**: `requirements.current_deadline` is the earliest deadline across all requested capabilities and hidden risk requirements. It's set as soon as a threshold is crossed, giving you a window — but a boolean "does this account have requirements?" check gives you no sense of urgency, so nobody chases the account until the window closes.
- **detect**: `GET /v1/accounts?limit=100` → flag where `data[].requirements.current_deadline != null` AND `data[].requirements.current_deadline - now < 14*86400` AND `data[].requirements.currently_due.length > 0`. Sort your alert by `current_deadline` ascending.
- **repair**: `POST /v1/account_links` (`account`, `refresh_url`, `return_url`, `type=account_onboarding`, `collection_options[fields]=eventually_due`) and email the link the moment the deadline lands inside your window. Collecting `eventually_due` rather than `currently_due` stops the account re-entering this state at the next threshold.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/connect/handling-api-verification · https://docs.stripe.com/connect/hosted-onboarding

## transfers-capability-inactive

- **slug**: `transfers-capability-inactive`
- **title**: transfers capability is inactive so every transfer 400s
- **symptom**: `POST /v1/transfers` (or a destination charge with `transfer_data[destination]`) fails for one seller while working for everyone else. Payments succeed on the platform but the seller's balance never moves.
- **mechanism**: You can only move funds to a connected account whose `transfers` capability is `active`. A capability sits at `inactive` until its specific requirements are verified, and it can drop back to `inactive` if new requirements go unmet past their deadline — independent of `charges_enabled`.
- **detect**: `GET /v1/accounts?limit=100` → flag where `data[].capabilities.transfers != "active"` (values are `active`, `inactive`, `pending`, or the key is absent meaning unrequested). For the reason: `GET /v1/accounts/{id}/capabilities/transfers` → `requirements.currently_due`, `requirements.disabled_reason`, `status`.
- **repair**: If `status` is missing/unrequested: `POST /v1/accounts/{id}/capabilities/transfers` with `requested=true`. If `inactive` with requirements: `POST /v1/accounts/{id}` supplying the fields listed in that capability's `requirements.currently_due`.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/connect/account-capabilities · https://docs.stripe.com/api/capabilities/object

## card-payments-inactive-cascades

- **slug**: `card-payments-inactive-cascades`
- **title**: card_payments inactive silently disables transfers too
- **symptom**: You fix a `transfers` requirement, `capabilities.transfers` still shows inactive, and transfers still fail. The requirement you actually need to fix belongs to a capability you weren't looking at.
- **mechanism**: Stripe documents an explicit coupling: if an account has both `card_payments` and `transfers` and the `status` of *either* is `inactive`, then *both* capabilities are disabled. A monitor that checks only the capability it uses will chase the wrong requirement set forever.
- **detect**: `GET /v1/accounts?limit=100` → flag where `data[].capabilities.card_payments` and `data[].capabilities.transfers` both exist and either is `"inactive"` or `"pending"`. Then `GET /v1/accounts/{id}/capabilities` and union `data[].requirements.currently_due` across *all* returned capabilities rather than just the one you use.
- **repair**: Satisfy the union of all capabilities' `currently_due` in one `POST /v1/accounts/{id}` call. If you don't need card payments at all, `POST /v1/accounts/{id}/capabilities/card_payments` with `requested=false` to drop the coupling (fails for permanent capabilities).
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/connect/account-capabilities · https://docs.stripe.com/api/accounts/object

## no-external-account-attached

- **slug**: `no-external-account-attached`
- **title**: Connected account has no external account, so payouts never run
- **symptom**: A seller's Stripe balance climbs for months. No payout objects exist for them at all, and no error was ever raised, because nothing ever tried to create a payout.
- **mechanism**: `external_account` is a standard `currently_due` requirement, but if your onboarding disabled `external_account_collection` (common when a platform plans to collect bank details itself) the account can finish onboarding with `details_submitted: true` and still have zero destinations. Automatic payouts simply have nowhere to go.
- **detect**: `GET /v1/accounts/{id}/external_accounts?limit=100` → flag where `data.length == 0`, or where no entry has `default_for_currency == true` for the account's `default_currency`. Confirm with `GET /v1/accounts?limit=100` → `data[].requirements.currently_due` containing the literal string `"external_account"`.
- **repair**: `POST /v1/accounts/{id}` with `external_account={{BANK_ACCOUNT_TOKEN}}`, or `POST /v1/account_links` with `type=account_update` and let the account add it. If you turned collection off, re-enable it at Dashboard → Settings → Connect → Payouts → External accounts.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/api/external_account_bank_accounts/object · https://docs.stripe.com/connect/hosted-onboarding

## external-account-errored

- **slug**: `external-account-errored`
- **title**: Bank account status errored halts all scheduled payouts
- **symptom**: One payout failed a month ago, was written off as a blip, and no payout has gone out since. The balance keeps growing and no new failed payouts appear either — because none are being attempted.
- **mechanism**: Stripe sets the external account's `status` to `errored` after a payout to it fails, and explicitly stops sending scheduled payouts to that destination until the bank details are updated. Watching only `GET /v1/payouts?status=failed` misses this: the failure count stops growing precisely because the account is frozen.
- **detect**: `GET /v1/accounts/{id}/external_accounts?limit=100` → flag `data[].status` in `["errored", "verification_failed", "tokenized_account_number_deactivated"]`. Corroborate with `GET /v1/payouts?limit=1` scoped to that account (`Stripe-Account` header) and compare `data[0].created` against `GET /v1/balance` showing a positive `available[].amount`.
- **repair**: Attach fresh details — `POST /v1/accounts/{id}` with a new `external_account` token, then `POST /v1/accounts/{id}/external_accounts/{ba_id}` with `default_for_currency=true`. Updating account/routing numbers on the existing object does not clear `errored`; a new external account is the reliable fix.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/api/external_account_bank_accounts/object · https://docs.stripe.com/api/payouts/object

## payouts-failing-bank-rejection

- **slug**: `payouts-failing-bank-rejection`
- **title**: Payouts fail with account_closed and nobody is watching
- **symptom**: Money left your Stripe balance, came back days later, and the recipient insists they were never paid. Your ledger shows a payout that briefly read `paid`.
- **mechanism**: Payouts move `pending → in_transit → paid`, and can flip from `paid` to `failed` up to 5 business days later when the bank rejects the credit. The `failure_code` enum (`account_closed`, `no_account`, `invalid_account_number`, `invalid_account_number_length`, `debit_not_authorized`, `could_not_process`, `declined`, `insufficient_funds`, `bank_account_restricted`, `incorrect_account_holder_name`, `incorrect_account_type`, `invalid_currency`, `account_frozen`, `unsupported_card`, …) tells you which fix applies, but only if something reads it.
- **detect**: `GET /v1/payouts?status=failed&limit=100&created[gte]={{now-90d}}` on the platform, and again per connected account with the `Stripe-Account` header. Group by `data[].failure_code` and read `data[].failure_message`. Also check `data[].failure_balance_transaction != null` to confirm the funds came back.
- **repair**: For `account_closed` / `no_account` / `invalid_account_number*`: `POST /v1/accounts/{id}` with a new `external_account` token and `default_for_currency=true`. For `debit_not_authorized` / `incorrect_account_type`: the account holder must authorize both credits and debits with their bank. For `insufficient_funds`: `POST /v1/topups`. Separately, subscribe to the `payout.failed` event — verify with `GET /v1/webhook_endpoints?limit=100` → `data[].enabled_events` containing `payout.failed` or `*`.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/api/payouts/object · https://docs.stripe.com/api/external_account_bank_accounts/object

## platform-paused-payouts-left-on

- **slug**: `platform-paused-payouts-left-on`
- **title**: Platform-paused payouts were never unpaused
- **symptom**: A risk team paused a seller during an investigation months ago. The investigation closed, nobody unpaused, and the seller's funds have been stranded ever since. Custom accounts get no notification from Stripe at all.
- **mechanism**: Pausing sets `charges_enabled` and/or `payouts_enabled` to `false` with `requirements.disabled_reason == "platform_paused"`. In-flight payouts stay `pending` for up to 10 days and then get **canceled** with funds returned to the connected balance — so the paper trail is a cluster of canceled payouts, not failures.
- **detect**: `GET /v1/accounts?limit=100` → flag `data[].requirements.disabled_reason == "platform_paused"`. Corroborate with `GET /v1/payouts?status=canceled&limit=100` using the `Stripe-Account` header for that account.
- **repair**: Dashboard → Connect → Connected accounts → open the account → unpause payments/payouts (there is no v1 API for unpausing; this control is Dashboard-only and unsupported on Accounts v2). Then confirm `payouts_enabled` returns to `true` and re-issue the canceled payouts with `POST /v1/payouts`.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/connect/pausing-payments-or-payouts-on-connected-accounts · https://docs.stripe.com/api/accounts/object

## payout-schedule-left-on-manual

- **slug**: `payout-schedule-left-on-manual`
- **title**: Payout schedule was left on manual and funds pile up
- **symptom**: A subset of connected accounts accumulate a large `available` balance and have never received a payout. Everything reports healthy: `payouts_enabled: true`, no requirements, a valid bank account.
- **mechanism**: `settings.payouts.schedule.interval` set to `manual` means Stripe never initiates a payout — your code must. This gets set deliberately during a hold-funds phase, or inherited from a platform-level default, and then nobody ever writes the `POST /v1/payouts` job. A related trap: an unusually high `delay_days` makes payouts look "missing" when they're merely far out.
- **detect**: `GET /v1/accounts?limit=100` → flag where `data[].settings.payouts.schedule.interval == "manual"` and `data[].payouts_enabled == true`. Confirm stranding: with `Stripe-Account: acct_x`, `GET /v1/balance` → `available[].amount > 0`, and `GET /v1/payouts?limit=1` → empty or `data[0].created` older than 30 days. Also flag `data[].settings.payouts.schedule.delay_days > 14`.
- **repair**: `POST /v1/accounts/{id}` with `settings[payouts][schedule][interval]=daily` (or `weekly` + `weekly_anchor`), or keep manual and add the missing `POST /v1/payouts` job. Reduce `settings[payouts][schedule][delay_days]` to the country minimum if it was inflated.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/payouts · https://docs.stripe.com/api/accounts/object

## onboarding-abandoned-details-not-submitted

- **slug**: `onboarding-abandoned-details-not-submitted`
- **title**: Accounts stall at details_submitted false after link expiry
- **symptom**: A long tail of `acct_` records exist in your database with no activity ever. Users report "the Stripe page said something went wrong" or that clicking the emailed link did nothing.
- **mechanism**: An AccountLink `url` expires within a few minutes and is strictly single-use — a page refresh, a back button, or a messaging client auto-previewing the link burns it. If your `refresh_url` doesn't mint a new link, the user is dumped and the account is left at `details_submitted: false` forever.
- **detect**: `GET /v1/accounts?limit=100` → flag where `data[].details_submitted == false` AND `now - data[].created > 7*86400`. Segment by `data[].requirements.currently_due.length` to separate "never started" from "partially completed."
- **repair**: Fix the `refresh_url` handler to call `POST /v1/account_links` again with the same parameters and 302 to the new `url`. Never email or SMS an AccountLink — hand it to an already-authenticated user inside your app. Then re-onboard the stalled cohort with fresh links.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/connect/hosted-onboarding · https://docs.stripe.com/api/accounts/object

## person-requirements-outstanding

- **slug**: `person-requirements-outstanding`
- **title**: A Person's currently_due blocks the whole account
- **symptom**: The Account object's own fields look complete, yet `charges_enabled` stays `false`. The `requirements.currently_due` array contains opaque entries prefixed with a `person_...` ID that your onboarding form has no field for.
- **mechanism**: For company accounts, KYC data lives on `Person` objects (representative, owners, directors, executives), each with its own `requirements` hash. Account-level `currently_due` references them as `{{PERSON_ID}}.verification.document`, so a script that only reads the Account can't resolve which human is missing what.
- **detect**: For each account: `GET /v1/accounts/{id}/persons?limit=100` → flag where `data[].requirements.currently_due.length > 0` or `data[].requirements.past_due.length > 0` or `data[].verification.status != "verified"`. Also check `data[].requirements.errors[]` and `data[].future_requirements.currently_due`. On the Account, look for `requirements.currently_due` entries matching `/^person_/`.
- **repair**: `POST /v1/accounts/{id}/persons/{person_id}` with the missing fields (`dob[day|month|year]`, `address[line1]`, `id_number`, `relationship[title]`, …). For documents, `POST https://files.stripe.com/v1/files` with `purpose=identity_document`, then `POST /v1/accounts/{id}/persons/{person_id}` with `verification[document][front]={{FILE_ID}}`.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/api/persons/object · https://docs.stripe.com/connect/handling-api-verification

## verification-errors-unread

- **slug**: `verification-errors-unread`
- **title**: requirements.errors codes like greyscale docs go unread
- **symptom**: A user uploads their passport four times and verification keeps failing. Your UI just says "verification pending." Duplicate uploads of the same file auto-fail, so the loop never ends.
- **mechanism**: `requirements.errors[]` carries `{code, reason, requirement}` explaining exactly why a submission was rejected — `verification_document_failed_greyscale`, `verification_document_not_readable`, `verification_document_expired`, `verification_document_missing_back`, `verification_failed_keyed_identity`, `information_missing`, `verification_missing_owners`, `invalid_street_address`, `invalid_tax_id_format`, `verification_document_failed_other`, plus the whole `invalid_url_website_*` family. Most integrations never surface it.
- **detect**: `GET /v1/accounts?limit=100` → flag any account where `data[].requirements.errors.length > 0`; read `errors[].code`, `errors[].reason`, `errors[].requirement`. Repeat for `data[].future_requirements.errors[]`, `GET /v1/accounts/{id}/persons` → `data[].requirements.errors[]`, and `GET /v1/accounts/{id}/capabilities` → `data[].requirements.errors[]`.
- **repair**: Map each `code` to a specific user-facing instruction and re-submit a *different* file — a color scan ≤8000×8000px, ≤10MB, JPG/PNG for identity docs, JPG/PNG/PDF for entity docs, not password-protected. For `invalid_url_website_*`, `POST /v1/accounts/{id}` with a corrected `business_profile[url]`; if you fixed the website itself, flip the URL to another value and back to force re-verification.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/connect/handling-api-verification · https://docs.stripe.com/api/accounts/object

## future-requirements-deadline-ignored

- **slug**: `future-requirements-deadline-ignored`
- **title**: future_requirements deadline will revoke a live capability
- **symptom**: Accounts that are fully verified and processing today all break on the same future date. Your monitoring, which watches `requirements`, saw nothing coming.
- **mechanism**: Upcoming KYC changes land in `future_requirements` — a separate hash that does *not* affect capabilities and does *not* appear in `requirements`. At `future_requirements.current_deadline` the entries migrate into `requirements`, and unmet ones immediately disable capabilities. This only applies to accounts where `controller.requirement_collection == "application"`; Stripe handles it for you when it's `"stripe"`.
- **detect**: `GET /v1/accounts?limit=100` → flag where `data[].controller.requirement_collection == "application"` AND (`data[].future_requirements.currently_due.length > 0` OR `data[].future_requirements.past_due.length > 0`). Sort by `data[].future_requirements.current_deadline`. Also read `data[].future_requirements.eventually_due` for threshold-triggered items and `data[].future_requirements.errors[]` for rejected submissions.
- **repair**: `POST /v1/accounts/{id}` (or `/persons/{person_id}`) with the future fields ahead of the deadline. For hosted flows, pass `collection_options[future_requirements]=include` when calling `POST /v1/account_links`. Test your handling first by creating a sandbox account with `email=jenny+enforce_future_requirements@example.com`, which forces all known future requirements into `requirements`.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/connect/handle-verification-updates · https://docs.stripe.com/api/accounts/object

## external-account-currency-mismatch

- **slug**: `external-account-currency-mismatch`
- **title**: External account currency can't settle the account's balance
- **symptom**: `POST /v1/payouts` returns "Sorry, you don't have any external accounts in that currency (usd)", or a cross-border transfer is rejected outright. The account plainly has a bank account attached.
- **mechanism**: Payouts settle per currency: a balance bucket in `usd` needs an external account whose `currency == "usd"` and `default_for_currency == true`. A US-country account with an AUD bank account, or a platform trying to reach a connected account outside the supported cross-border corridor (US, UK, EEA, CA, CH), has no valid settlement path. Recipient-service-agreement accounts are excluded from cross-border payouts entirely.
- **detect**: For each account: `GET /v1/accounts/{id}` → note `country` and `default_currency`; `GET /v1/accounts/{id}/external_accounts?limit=100` → flag when no entry has `currency == default_currency` with `default_for_currency == true`. Validate legality with `GET /v1/country_specs/{platform_country}` → check the connected account's `country` appears in `supported_transfer_countries`, and that the bank currency is a key of `supported_bank_account_currencies` for that country.
- **repair**: `POST /v1/accounts/{id}` with an `external_account` token in the correct currency, then `POST /v1/accounts/{id}/external_accounts/{ba_id}` with `default_for_currency=true`. If the corridor isn't in `supported_transfer_countries`, switch that recipient to Global Payouts or a locally-acquiring platform account — no API change will make the transfer legal.
- **category**: Connect & payouts
- **sources**: https://docs.stripe.com/api/country_specs/object · https://docs.stripe.com/connect/cross-border-payouts · https://stackoverflow.com/questions/48334911/stripe-create-payout-getting-error-sorry-you-dont-have-any-external-accounts

---

# Disputes & fraud

## dispute-deadline-72h-no-evidence

- **slug**: `dispute-deadline-72h-no-evidence`
- **title**: Disputes are hours from due_by with no evidence attached
- **symptom**: Disputes are discovered after they close. The Dashboard shows them as lost, the funds are gone permanently, and the dispute fee is not returned.
- **mechanism**: You have a limited window to respond — usually 7 to 21 days depending on the card network — and "if you don't respond before the deadline, you automatically lose the dispute and can't retrieve the disputed funds." The deadline is exposed as `evidence_details.due_by`, but nothing pushes a reminder as it approaches.
- **detect**: `GET /v1/disputes?limit=100` (auto-paginate) → alert on any dispute where `status == "needs_response"` AND `evidence_details.has_evidence == false` AND `evidence_details.due_by - now <= 259200` (72 hours). Escalate when `evidence_details.past_due == true` while `status` is still `"needs_response"`. Enrich each with `GET /v1/charges/{dispute.charge}` for amount at risk, and check `enhanced_eligibility_types` — a dispute containing `visa_compelling_evidence_3` is one Stripe will largely pre-populate for you.
- **repair**: Submit before `due_by` — `POST /v1/disputes/{du_id} -d "evidence[product_description]=..." -d "evidence[receipt]=<file_id>" -d "evidence[shipping_tracking_number]=..." -d "evidence[customer_communication]=<file_id>"` — or accept deliberately with `POST /v1/disputes/{du_id}/close`. Evidence can only be submitted once, so assemble everything first.
- **category**: Disputes & fraud
- **sources**: https://docs.stripe.com/disputes/responding · https://docs.stripe.com/api/disputes/object

## inquiry-needs-response-ignored

- **slug**: `inquiry-needs-response-ignored`
- **title**: Inquiries sit unanswered and escalate into real chargebacks
- **symptom**: Disputes appear to arrive out of nowhere as formal chargebacks. In hindsight each was preceded by an inquiry that was visible in the API for days and never answered.
- **mechanism**: `warning_needs_response` is a pre-dispute inquiry, not a chargeback — no funds have moved yet. Responding at this stage "prevent[s] a formal dispute escalation, which saves you time, fees, and your rating with the card networks." Unescalated inquiries don't count toward network monitoring programs; escalated chargebacks do. Most integrations filter disputes on `status == "needs_response"` and miss the `warning_` family entirely.
- **detect**: `GET /v1/disputes?limit=100` (auto-paginate) → flag `status == "warning_needs_response"` with `evidence_details.has_evidence == false`, sorted by `evidence_details.due_by`. Measure the leak historically: over the last 180 days compute `count(status in ("needs_response","under_review","lost","won")) / count(all disputes)` for disputes whose charge previously carried a `warning_` status — a high escalation share means inquiries are being ignored. Note that accepting an inquiry does not resolve it; only evidence does.
- **repair**: Respond with evidence at the inquiry stage: `POST /v1/disputes/{du_id} -d "evidence[uncategorized_text]=..."` plus the category-appropriate fields. Alert on `charge.dispute.created` events where `data.object.status` starts with `warning_`, not just on `needs_response`.
- **category**: Disputes & fraud
- **sources**: https://docs.stripe.com/disputes/responding · https://docs.stripe.com/disputes/monitoring-programs · https://docs.stripe.com/api/disputes/object

## dispute-rate-above-threshold

- **slug**: `dispute-rate-above-threshold`
- **title**: Dispute activity is above the 0.75% excessive threshold
- **symptom**: No single dispute looks alarming, but the ratio has been creeping up for months. The first hard signal is an email from Stripe about a card-network monitoring program and a fine.
- **mechanism**: "The credit card processing industry standard recognizes dispute activity above 0.75% as excessive", and a sudden spike or steep trend can trigger placement before that threshold. Visa's VAMP flags a non-compliant ratio at 0.5% (excessive at 1.5%, or 2.2% in CEMEA) with a count floor of 5, and counts early fraud warnings toward the same ratio. Mastercard ECM starts at 100 disputes and a 1.5% chargeback rate. All disputes count, won or lost.
- **detect**: Over a rolling calendar month: `GET /v1/disputes?created[gte]=<month_start>&created[lt]=<month_end>&limit=100` (auto-paginate, count all) and `GET /v1/charges?created[gte]=<month_start>&created[lt]=<month_end>&limit=100` (auto-paginate, count `status == "succeeded" AND captured == true`). Compute `disputes / successful_charges`. Alert at `>= 0.005` (VAMP non-compliant) and page at `>= 0.0075`. For the VAMP ratio specifically, add `GET /v1/radar/early_fraud_warnings?created[gte]=...&limit=100` to the numerator, since Visa counts EFWs and disputes together.
- **repair**: There is no API toggle — reduce the numerator. Enable Radar risk controls, turn on `Block if :risk_level: = 'highest'`, refund actionable EFWs before they escalate, fix the statement descriptor, and add self-serve cancellation. Stripe publishes a remediation template at https://docs.stripe.com/disputes/monitoring-programs.
- **category**: Disputes & fraud
- **sources**: https://docs.stripe.com/disputes/measuring · https://docs.stripe.com/disputes/monitoring-programs

## disputes-lost-without-response

- **slug**: `disputes-lost-without-response`
- **title**: Disputes were lost by default because nobody responded
- **symptom**: The dispute list is a wall of `lost`. Nobody can say which were genuinely indefensible and which simply timed out.
- **mechanism**: `evidence_details.submission_count` records how many times evidence was submitted. A dispute that closed as `lost` with `submission_count == 0` was never contested — it was forfeited by the deadline, not decided against you. This is invisible in the Dashboard's headline numbers, which show only the outcome.
- **detect**: `GET /v1/disputes?created[gte]=<now-365d>&limit=100` (auto-paginate) → compute `count(status == "lost" AND evidence_details.submission_count == 0) / count(status == "lost")`. Any non-zero value is recoverable process loss; above ~0.3 the dispute workflow is effectively absent. Separately report `count(status == "lost") / count(status in ("lost","won"))` as the true loss rate on contested disputes only.
- **repair**: Build a daily read-only sweep on `evidence_details.due_by` (see `dispute-deadline-72h-no-evidence`) and route to a human. Automate the mechanical parts with Stripe Workflows, and pre-populate evidence by passing customer IP, email, shipping address, and product description on every payment so Visa CE 3.0 eligibility can be assessed.
- **category**: Disputes & fraud
- **sources**: https://docs.stripe.com/api/disputes/object · https://docs.stripe.com/disputes/responding

## efw-actionable-not-refunded

- **slug**: `efw-actionable-not-refunded`
- **title**: Actionable early fraud warnings were never refunded
- **symptom**: Charges flagged by the issuer as suspected fraud stay captured, and weeks later the same charges arrive as fraud disputes — each carrying a dispute fee and a hit to the dispute rate.
- **mechanism**: "An EFW is actionable if it has not received a dispute and has not been fully refunded." That window is the only chance to refund and avoid the dispute fee, the dispute-rate increase, and the loss of product. Note the EFW itself still counts toward Visa's VAMP ratio whether or not you refund — but the resulting chargeback would be counted a second time.
- **detect**: `GET /v1/radar/early_fraud_warnings?created[gte]=<now-90d>&limit=100` (auto-paginate) → for each item with `actionable == true`, call `GET /v1/charges/{efw.charge}` and flag when `refunded == false` AND `amount_refunded == 0` AND `disputed == false`. Prioritise by `created` age and `charge.amount`. Also break down by `fraud_type` — clusters of `made_with_stolen_card` or `unauthorized_use_of_card` indicate an active attack, not one-offs.
- **repair**: `POST /v1/refunds -d charge=ch_... -d reason=fraudulent` (or Dashboard → the payment → **Refund as fraud**, which also adds the card fingerprint and email to your block lists). Subscribe to `radar.early_fraud_warning.created` so the window is caught in real time rather than by sweep.
- **category**: Disputes & fraud
- **sources**: https://docs.stripe.com/api/radar/early_fraud_warnings/object · https://docs.stripe.com/disputes/prevention/best-practices · https://docs.stripe.com/disputes/measuring

## radar-reviews-open-stale

- **slug**: `radar-reviews-open-stale`
- **title**: Radar reviews sit open for days while funds stay at risk
- **symptom**: The review queue grows and nobody works it. Flagged payments ship anyway, and uncaptured authorizations quietly expire.
- **mechanism**: `open == true` means "the review needs action". Payments placed in review are already processed and charged unless you use separate auth and capture — in which case the authorization is released automatically if not captured within 7 days. Stripe's guidance is to review payments in the queue "as soon as possible". A stale queue is the same as having no review rules at all, except it also blocks capture.
- **detect**: `GET /v1/reviews?limit=100` (auto-paginate) → flag every review where `open == true` AND `created < now - 259200` (3 days); treat `open == true AND created < now - 604800` (7 days) as critical because any uncaptured authorization has lapsed. Segment by `opened_reason` (`rule` vs `manual`) to see which custom rule is flooding the queue. Then audit outcomes: over 90 days compute `count(closed_reason == "approved") / count(closed_reason != null)` — near 1.0 means the review rule is too broad and should be removed or narrowed.
- **repair**: Work or close the queue (Dashboard → Radar → Reviews → Approve / Refund / Refund and report fraud). If approvals dominate, narrow the review rule (Stripe's own example: `if :card_funding: = 'prepaid'` → `if :is_disposable_email: and :card_funding: = 'prepaid'`) or delete it. Subscribe to `review.opened` to alert rather than poll.
- **category**: Disputes & fraud
- **sources**: https://docs.stripe.com/api/radar/reviews/object · https://docs.stripe.com/radar/reviews · https://docs.stripe.com/radar/rules

## radar-blocked-rate-overblocking

- **slug**: `radar-blocked-rate-overblocking`
- **title**: Radar is blocking a large share of your charge attempts
- **symptom**: Conversion drops after a rule change. Customers report their card "doesn't work" on your site but works everywhere else, and the payment never reaches their bank.
- **mechanism**: When Radar blocks a payment it never requests authorization from the issuer, so the charge records `outcome.type: "blocked"` with `network_status: "not_sent_to_network"`. An over-broad block rule (Stripe's own bad example: `if :card_country: != 'US'`) shows up only as a blocked-rate shift; `outcome.reason` distinguishes Stripe's own model (`highest_risk_level`) from your rule (`rule`, with the predicate in `outcome.rule`).
- **detect**: `GET /v1/charges?created[gte]=<now-30d>&limit=100` (auto-paginate) → compute `count(outcome.type == "blocked") / count(all)`, and compare against the same window 30 days earlier to catch a step change after a rule edit. Group blocked charges by `outcome.rule.predicate` and by `outcome.reason`; a single custom predicate responsible for most blocks while `outcome.risk_level == "normal"` on those same charges is over-blocking. Also count `outcome.reason == "low_probability_of_authorization"` separately — that's Adaptive Acceptance, not your rule.
- **repair**: Narrow the offending predicate in Dashboard → Radar → Rules (add `and :risk_level: = 'elevated'` per Stripe's own remediation example), or convert the block rule to a review rule while you gather data. Individual false positives can be released with **Add to allow list** on the payment page. Check the rule's **Est. false positive rate** metric before re-enabling.
- **category**: Disputes & fraud
- **sources**: https://docs.stripe.com/declines · https://docs.stripe.com/radar/rules · https://docs.stripe.com/api/charges/object

## highest-risk-charges-succeeded

- **slug**: `highest-risk-charges-succeeded`
- **title**: Highest-risk charges are succeeding instead of being blocked
- **symptom**: Payments Stripe scored as highest risk settle normally, and a disproportionate share of them later turn into early fraud warnings or fraud disputes.
- **mechanism**: `if :risk_level: = 'highest'` is a Radar default rule, but an allow rule overrides all other rules *including* Stripe's defaults — Stripe warns that allow rules "override the Stripe default rules, along with any other custom rules that match the same criteria". A broad allow rule (`if :ip_country: = 'GB'`) therefore lets highest-risk traffic straight through, and the block rule looks enabled while doing nothing.
- **detect**: `GET /v1/charges?created[gte]=<now-90d>&limit=100` (auto-paginate) → flag charges where `outcome.risk_level == "highest"` AND `status == "succeeded"` AND `captured == true`. Read `outcome.rule` on those charges: a populated rule with `action == "allow"` names the override. Then quantify: for that flagged set, cross-reference `GET /v1/radar/early_fraud_warnings?limit=100` and `GET /v1/disputes?limit=100` by `charge` id — a materially higher EFW/dispute incidence than the baseline confirms the leak.
- **repair**: Add Stripe's recommended guard to every allow rule — `and :risk_level: != 'highest'` — in Dashboard → Radar → Rules, and confirm the built-in `if :risk_level: = 'highest'` block rule is enabled. Consider Radar risk controls with dynamic risk thresholds instead of hand-maintained allow rules.
- **category**: Disputes & fraud
- **sources**: https://docs.stripe.com/radar/rules · https://docs.stripe.com/api/charges/object · https://docs.stripe.com/declines

## avs-cvc-fail-captured

- **slug**: `avs-cvc-fail-captured`
- **title**: Charges captured after AVS and CVC verification failed
- **symptom**: Payments where the billing postal code or security code demonstrably didn't match the issuer's records are captured and shipped, then disputed as fraudulent with no defensible evidence.
- **mechanism**: An issuer can approve a payment that fails CVC or AVS because it weighs many other signals. Stripe surfaces the result in `payment_method_details.card.checks` but does not act on it unless you enable the corresponding Radar rule; `settings.card_payments.decline_on.avs_failure` and `.cvc_failure` both default to `false`. Stripe's dispute guidance is blunt: "If verification fails, consider rejecting the payment because this might indicate fraud."
- **detect**: `GET /v1/account` → flag when `settings.card_payments.decline_on.avs_failure == false` AND `settings.card_payments.decline_on.cvc_failure == false`. Then `GET /v1/charges?created[gte]=<now-90d>&limit=100` (auto-paginate) → count charges where `status == "succeeded"` AND `captured == true` AND (`payment_method_details.card.checks.address_postal_code_check == "fail"` OR `payment_method_details.card.checks.cvc_check == "fail"` OR `payment_method_details.card.checks.address_line1_check == "fail"`). Also count `... == null` on card-type charges — null means the data was never collected, which is the deeper problem. Cross-reference the failing set against `GET /v1/disputes?limit=100` by `charge`.
- **repair**: Enable the Radar built-ins in Dashboard → Radar → Rules: *"if Postal code verification fails based on risk score"* and *"if CVC verification fails based on risk score"* (the risk-scored variants avoid blocking wallets that don't supply the data). At the same time force collection: `POST /v1/checkout/sessions -d billing_address_collection=required`.
- **category**: Disputes & fraud
- **sources**: https://docs.stripe.com/api/accounts/object · https://docs.stripe.com/radar/rules · https://docs.stripe.com/disputes/prevention/best-practices

## missing-statement-descriptor

- **slug**: `missing-statement-descriptor`
- **title**: No statement descriptor, so customers dispute what they see
- **symptom**: A steady trickle of disputes with reason `unrecognized`, `general`, or `duplicate` from customers who genuinely bought the product and simply didn't recognise the line on their statement.
- **mechanism**: If the account has no statement descriptor prefix, the descriptor that reaches the card networks is a generic default rather than your brand. Stripe lists clear descriptors as a primary prevention control ("use your website domain or business name"), and notes that unrecognised descriptors specifically produce `general` and `duplicate` disputes. Visa also *identifies monitored accounts by the static component of the statement descriptor* — so a missing or inconsistent prefix fragments your VAMP reporting across phantom accounts.
- **detect**: `GET /v1/account` → flag when `settings.payments.statement_descriptor == null` OR `settings.card_payments.statement_descriptor_prefix == null`. Then `GET /v1/charges?created[gte]=<now-30d>&limit=100` (auto-paginate) → inspect `calculated_statement_descriptor`; flag when it is empty, generic, or takes more than one distinct value across the sample (fragmented Visa identity), and count charges where `statement_descriptor_suffix == null`. Quantify: `GET /v1/disputes?created[gte]=<now-180d>&limit=100` → share of `reason in ("unrecognized","general","duplicate")`.
- **repair**: Set it in Dashboard → Settings → Business → Public business information (https://dashboard.stripe.com/settings/public); 5–22 characters, at least 5 letters, no `< > ' "`. Add a per-payment suffix at creation: `POST /v1/payment_intents -d statement_descriptor_suffix="ORDER1234"`. Give every descriptor the same static prefix so Visa aggregates your volume as one account.
- **category**: Disputes & fraud
- **sources**: https://docs.stripe.com/disputes/prevention/best-practices · https://docs.stripe.com/api/charges/object · https://docs.stripe.com/disputes/monitoring-programs

## no-3ds-on-elevated-risk

- **slug**: `no-3ds-on-elevated-risk`
- **title**: Elevated-risk card charges are captured with no 3DS
- **symptom**: Fraud disputes on card-not-present payments land entirely on you. None of the disputed charges carry a 3D Secure result, so there is no liability shift to invoke.
- **mechanism**: 3DS shifts liability for most fraud disputes from seller to issuer, but Stripe only triggers it automatically for regulatory reasons (SCA) or issuer soft declines — not because Radar scored the payment as risky. Without a *Request 3D Secure* rule, `payment_method_details.card.three_d_secure` stays `null` on elevated- and highest-risk charges. Mastercard's EFM program additionally penalises merchants whose 3DS share is at or below 10% of Mastercard volume (50% in regulated countries).
- **detect**: `GET /v1/charges?created[gte]=<now-90d>&limit=100` (auto-paginate) → flag charges where `payment_method_details.type == "card"` AND `outcome.risk_level in ("elevated","highest")` AND `payment_method_details.card.three_d_secure == null` AND `status == "succeeded"`. Also compute the account-wide 3DS share `count(three_d_secure != null) / count(card charges)` and alert below 0.10. For charges that did use 3DS, flag `payment_method_details.card.three_d_secure.result` values other than `"authenticated"` (e.g. `attempt_acknowledged`, `processing_error`) that were still captured.
- **repair**: Add in Dashboard → Radar → Rules: `Request 3D Secure if :risk_level: != 'normal' and :amount_in_usd: > 25`, paired with Stripe's recommended companion block rule `Block if not :is_3d_secure: and :risk_level: != 'normal' and not :is_off_session: and :digital_wallet: != 'apple_pay' and not (:digital_wallet: = 'android_pay' and :has_cryptogram:)` so cards without a 3DS flow don't slip through. Note EFWs still arrive on 3DS-authenticated payments and still count toward VAMP.
- **category**: Disputes & fraud
- **sources**: https://docs.stripe.com/radar/rules · https://docs.stripe.com/disputes/prevention/best-practices · https://docs.stripe.com/disputes/monitoring-programs

---

# Customers & payment methods

## duplicate-customers-same-email

- **slug**: `duplicate-customers-same-email`
- **title**: Duplicate customers share an email and split billing
- **symptom**: One person has three Customer records. Their saved card lives on one, their subscription on another, and their invoices on a third. Support cannot find "the" customer, and churn analytics double-count.
- **mechanism**: Stripe does not enforce email uniqueness on Customers — this is by design and one of the oldest high-view complaints in the ecosystem. Any code path that calls `POST /v1/customers` without first searching (a second checkout, a retried webhook, a re-signup, Checkout with `customer_creation: always`) mints a fresh `cus_` every time.
- **detect**: `GET /v1/customers?limit=100` (paginate through the full list). Normalise `data[].email` to lowercase, group, and flag any key with count > 1; report the worst offenders and the total duplicate count. Confirm any specific case with `GET /v1/customers?email={email}` (exact, case-sensitive filter) or `GET /v1/customers/search?query=email~"{local_part}"` for substring matching. Enrich by checking which duplicates actually have value: for each, `GET /v1/payment_methods?customer={id}&type=card` and `GET /v1/subscriptions?customer={id}` — duplicates holding cards or subscriptions are the dangerous ones.
- **repair**: Before creating, look up: `GET /v1/customers?email={email}&limit=1` and reuse the ID if present; store the `cus_` ID on your own user row as the single source of truth. Merge existing duplicates by moving payment methods (`POST /v1/payment_methods/{pm}/attach -d customer={keeper}`) and subscriptions, then `DELETE /v1/customers/{dupe}`. In Checkout, pass an existing `customer` rather than relying on `customer_creation`.
- **category**: Customers & payment methods
- **sources**: https://stackoverflow.com/questions/26392819/stripe-making-multiple-customers-with-same-email-address · https://stackoverflow.com/questions/26767150/is-it-possible-to-search-for-a-stripe-customer-by-their-email · https://docs.stripe.com/api/customers/list

## customers-missing-email

- **slug**: `customers-missing-email`
- **title**: Customers have no email, so Stripe sends no receipts
- **symptom**: Customers say they never got a receipt and open "unrecognised charge" disputes. Dunning emails for failed subscription payments go nowhere. The Dashboard customer list is full of blank name/email rows.
- **mechanism**: Stripe emails receipts and dunning notices to `customer.email` (or a per-payment `receipt_email`). Integrations that create the Customer server-side before collecting contact details, or that pass email only to their own database, leave the field null. Missing receipts correlate directly with friendly-fraud disputes, since the cardholder has nothing linking the statement descriptor to your business.
- **detect**: `GET /v1/customers?limit=100` (paginate). Count `data[].email == null` or empty, as an absolute number and a percentage. Weight by value: for each such customer, `GET /v1/subscriptions?customer={id}&status=active` — an emailless customer with an active subscription is unreachable for dunning. Also `GET /v1/charges?limit=100` and count `data[].receipt_email == null && data[].customer == null`, which are receipt-less one-off payments. Correlate with `data[].disputed == true` on the emailless cohort.
- **repair**: Backfill from your own user table: `POST /v1/customers/{id} -d email=user@example.com -d name="Jenny Rosen"`. Always pass `email` at creation. For guest checkouts that have no Customer, set `receipt_email` on the PaymentIntent: `POST /v1/payment_intents -d receipt_email=user@example.com`. Confirm email receipts are on at https://dashboard.stripe.com/settings/emails.
- **category**: Customers & payment methods
- **sources**: https://docs.stripe.com/api/customers/object · https://docs.stripe.com/api/payment_intents/object · https://stackoverflow.com/questions/71087234/stripe-doesnt-save-the-customer-email-and-name-in-the-dashboard

## customers-missing-address

- **slug**: `customers-missing-address`
- **title**: Customers have no address; tax and SCA exemptions fail
- **symptom**: Stripe Tax refuses to finalize invoices with `customer_tax_location_invalid`. European card authorization rates lag. Radar has less signal to work with, so more legitimate payments land in `elevated` risk.
- **mechanism**: `customer.address` (minimally `country` plus `postal_code`) drives Stripe Tax location resolution, AVS checks, and several SCA low-risk exemption calculations. Integrations that collect a shipping address into their own database but never write it to the Customer, or that use Checkout without `billing_address_collection: required`, leave it null. Stripe Tax then hard-fails at invoice finalization rather than degrading gracefully.
- **detect**: `GET /v1/customers?limit=100` (paginate). Count `data[].address == null`, and separately `data[].address.country == null || data[].address.postal_code == null` — partial addresses fail the same way. Scope to customers that matter: intersect with `GET /v1/subscriptions?limit=100&status=active&expand[]=data.customer`. Confirm the downstream breakage with `GET /v1/invoices/search?query=last_finalization_error_code:'customer_tax_location_invalid'`. Also check AVS coverage: `GET /v1/payment_methods?customer={id}&type=card` and count `data[].card.checks.address_postal_code_check == null` (never checked).
- **repair**: Write the address to the Customer: `POST /v1/customers/{id} -d "address[line1]=…" -d "address[city]=…" -d "address[postal_code]=…" -d "address[country]=US"`. In Checkout set `billing_address_collection=required`; with the Payment Element set `fields: {billingDetails: 'auto'}` and pass `confirmParams.payment_method_data.billing_details.address`. For tax specifically, `customer.tax.ip_address` can serve as a fallback location signal.
- **category**: Customers & payment methods
- **sources**: https://docs.stripe.com/error-codes · https://docs.stripe.com/api/customers/object · https://docs.stripe.com/strong-customer-authentication

## expired-saved-cards-attached

- **slug**: `expired-saved-cards-attached`
- **title**: Saved cards are already expired but still attached
- **symptom**: Renewal charges fail with `expired_card`. The customer's saved card in your UI still shows as valid. Involuntary churn quietly eats into MRR every month.
- **mechanism**: Stripe's automatic card updater handles many US-issued Visa/Mastercard/Amex/Discover reissues, but coverage is partial and international support varies widely — and it is impossible to tell which cards participate. Cards outside that coverage simply expire in place, staying attached to the Customer as dead payment methods that nothing prunes.
- **detect**: `GET /v1/customers?limit=100` (paginate); for each, `GET /v1/payment_methods?customer={id}&type=card&limit=100`. Flag any `data[].card` where `exp_year < currentYear`, or `exp_year == currentYear && exp_month < currentMonth`. Escalate when that expired PM is also referenced by `customer.invoice_settings.default_payment_method` or by an active subscription's `default_payment_method`. Confirm the damage with `GET /v1/payment_intents?limit=100` counting `last_payment_error.decline_code == "expired_card"` and `GET /v1/charges` where `outcome.reason == "expired_card"`.
- **repair**: Detach the dead card (`POST /v1/payment_methods/{pm}/detach`) and email the customer a Setup Intent or Customer Portal link to add a new one. Enable the Customer Portal at https://dashboard.stripe.com/settings/billing/portal with payment method updates allowed. Subscribe to `payment_method.automatically_updated` so network-updated cards refresh your local copy of `exp_month`/`exp_year`/`last4`.
- **category**: Customers & payment methods
- **sources**: https://docs.stripe.com/payments/cards/overview · https://docs.stripe.com/api/payment_methods/object · https://docs.stripe.com/declines/codes

## cards-expiring-within-60-days

- **slug**: `cards-expiring-within-60-days`
- **title**: Saved cards expire within 60 days with no updater
- **symptom**: Churn arrives in predictable monthly clusters that map exactly to card expiry dates. Nobody warned the customer, so the first they hear about it is a failed-payment email.
- **mechanism**: This is the preventable half of the previous problem. Card expiry is known months in advance from `card.exp_month`/`card.exp_year`, yet most integrations only react after the decline. Where the automatic card updater does not cover the issuer, a proactive 30–60 day nudge is the only thing standing between you and involuntary churn.
- **detect**: For each customer with an active subscription (`GET /v1/subscriptions?limit=100&status=active`), call `GET /v1/payment_methods?customer={id}&type=card&limit=100`. Compute the card's expiry as the last day of `exp_month`/`exp_year` and flag when it falls between `now` and `now + 60d`. Prioritise cards that are the billing default. As a secondary signal, read `data[].card.networks.available` and `data[].card.wallet` — network-tokenised and wallet-backed credentials (`wallet.type` of `apple_pay`/`google_pay`) survive reissue and can be excluded from the warning list.
- **repair**: Run a scheduled job that emails customers 45 days before expiry with a Customer Portal link (`POST /v1/billing_portal/sessions -d customer=cus_X -d return_url=…`). Enable Smart Retries and the card-updater-driven recovery under https://dashboard.stripe.com/settings/billing/automatic. Encourage wallet-based saves (Apple Pay/Google Pay/Link) at checkout, since those tokens do not expire with the plastic.
- **category**: Customers & payment methods
- **sources**: https://docs.stripe.com/payments/cards/overview · https://docs.stripe.com/api/payment_methods/object

## unattached-payment-methods-orphaned

- **slug**: `unattached-payment-methods-orphaned`
- **title**: PaymentMethods created but never attached to a customer
- **symptom**: Reusing a saved card fails with "This PaymentMethod was previously used without being attached to a Customer or was detached from a Customer, and may not be used again." Customers have to re-enter card details on every purchase.
- **mechanism**: A PaymentMethod created by Elements is not attached to anyone by default — `customer` stays null. Once it has been consumed by a single PaymentIntent without `setup_future_usage` or an explicit attach, it is burned and cannot be reused. Integrations that store the `pm_` ID in their own database for "next time" discover this only when the second charge fails.
- **detect**: `GET /v1/payment_methods?type=card&limit=100` (the `customer` parameter is optional; omitting it lists account-wide). Count `data[].customer == null` where `data[].created < now - 24h`. Compare against the attached population to get an orphan ratio. Corroborate from the payment side: `GET /v1/payment_intents?limit=100` and count intents where `customer != null` but `setup_future_usage == null` — those confirmed a card against a customer without ever saving it. Also count `last_payment_error.code == "payment_method_unexpected_state"`.
- **repair**: Save the card as part of the payment: `POST /v1/payment_intents -d customer=cus_X -d setup_future_usage=off_session`, which attaches the PaymentMethod on success. To save without charging, use `POST /v1/setup_intents -d customer=cus_X -d usage=off_session`. Prefer either over a bare `POST /v1/payment_methods/{id}/attach`, which skips the setup optimisation and makes later declines more likely.
- **category**: Customers & payment methods
- **sources**: https://stackoverflow.com/questions/60333494/this-paymentmethod-was-previously-used-without-being-attached-to-a-customer-or-w · https://docs.stripe.com/api/payment_methods/attach · https://docs.stripe.com/api/payment_methods/list

## setup-intents-never-confirmed

- **slug**: `setup-intents-never-confirmed`
- **title**: SetupIntents created but never confirmed by the client
- **symptom**: "Add a payment method" flows appear to succeed to the user, but no card ever lands on the Customer. A pile of SetupIntents sits at `requires_payment_method` or `requires_confirmation` and never resolves.
- **mechanism**: SetupIntents follow the same lifecycle as PaymentIntents. Creating one server-side is only step one; the client must call `stripe.confirmSetup()` and handle `requires_action` for 3DS. If the frontend errors out, the modal closes early, or the `return_url` is missing, the SetupIntent freezes and no mandate is ever created — which then breaks every downstream off-session charge.
- **detect**: `GET /v1/setup_intents?limit=100&created[lt]={now-24h}` (paginate). Count `data[].status` in `("requires_payment_method", "requires_confirmation", "requires_action")` as a fraction of all SetupIntents created in the window; above ~20% indicates a broken confirm path rather than user abandonment. Bucket by `data[].next_action.type` for the `requires_action` slice, and read `data[].last_setup_error.code` (e.g. `setup_intent_authentication_failure`, `setup_intent_setup_attempt_expired`) for the failures. Cross-check `data[].mandate == null` on everything that is not `succeeded`.
- **repair**: On the client, confirm and handle the result: `const {error, setupIntent} = await stripe.confirmSetup({elements, confirmParams: {return_url}})`, then treat only `setupIntent.status === 'succeeded'` as success. Implement the `return_url` landing page. Cancel dead intents with `POST /v1/setup_intents/{id}/cancel -d cancellation_reason=abandoned` and drive persistence from the `setup_intent.succeeded` webhook rather than the browser.
- **category**: Customers & payment methods
- **sources**: https://docs.stripe.com/api/setup_intents/object · https://docs.stripe.com/payments/paymentintents/lifecycle · https://stackoverflow.com/questions/65136921/why-is-stripe-confirmcardsetup-failing-for-me

## setup-intent-on-session-for-off-session

- **slug**: `setup-intent-on-session-for-off-session`
- **title**: SetupIntents use on_session but you bill off-session
- **symptom**: Cards saved through your "save for later" flow work fine at checkout, but every unattended renewal or usage-based charge fails with `authentication_required` or `billing_invalid_mandate`.
- **mechanism**: `SetupIntent.usage` tells Stripe and the issuer what agreement is being established. `on_session` records consent for customer-present reuse only; `off_session` (the default) creates the merchant-initiated-transaction mandate that unattended charges depend on. Setting `usage: "on_session"` — or setting `setup_future_usage: "on_session"` on a PaymentIntent — while actually billing unattended produces cards that look saved but are not authorised for MIT.
- **detect**: `GET /v1/setup_intents?limit=100&created[gte]={now-180d}` (paginate). Flag `data[].status == "succeeded" && data[].usage == "on_session" && data[].mandate == null` where the customer also has an active subscription. Mirror it on the payment side: `GET /v1/payment_intents?limit=100` flagging `data[].setup_future_usage == "on_session"` on intents whose customer is subscribed. Confirm the fallout by counting `last_payment_error.decline_code == "authentication_required"` and invoice errors `billing_invalid_mandate` for the same customers.
- **repair**: Create setup with `POST /v1/setup_intents -d customer=cus_X -d usage=off_session` (or omit `usage`, which defaults to `off_session`), and use `setup_future_usage=off_session` when saving during a payment. Present mandate text at collection time covering permission, frequency, and how the amount is determined. Re-collect consent for existing `on_session` cards via a fresh off-session SetupIntent before the next renewal.
- **category**: Customers & payment methods
- **sources**: https://docs.stripe.com/api/setup_intents/object · https://docs.stripe.com/strong-customer-authentication · https://docs.stripe.com/error-codes

## legacy-card-sources-still-attached

- **slug**: `legacy-card-sources-still-attached`
- **title**: Legacy card sources still live under customer.sources
- **symptom**: Some customers charge fine and others fail with "Customer cus_… does not have a linked card with ID tok_…" or "Cannot charge a customer that has no active card." Half the billing code paths use `card_*` IDs and half use `pm_*`.
- **mechanism**: Cards saved before the PaymentMethods API live under `customer.sources` as `card_*` / `src_*` objects and are referenced by `customer.default_source`. They cannot carry a 3DS mandate and are invisible to `GET /v1/payment_methods`, so an integration that half-migrated ends up with two parallel card stores and code that only sees one of them.
- **detect**: For each customer from `GET /v1/customers?limit=100`, call `GET /v1/customers/{id}/sources?object=card&limit=100` and flag a non-empty `data`. The sharpest signal is the split-brain case: `customer.default_source != null` while `customer.invoice_settings.default_payment_method == null`, and `GET /v1/payment_methods?customer={id}&type=card` returning empty. Count those customers. Corroborate with `GET /v1/charges?limit=100` where `data[].payment_intent == null` (the legacy charge path) and `last_payment_error.code == "missing"`.
- **repair**: Migrate each legacy source to a PaymentMethod, then set the modern default: `POST /v1/customers/{id} -d "invoice_settings[default_payment_method]=pm_XXX"`. Where the source cannot be converted, prompt the customer through a SetupIntent to re-add the card (which also earns an SCA mandate). Once migrated, delete the legacy source with `DELETE /v1/customers/{id}/sources/{card_id}` and stop reading `default_source` anywhere in the billing path.
- **category**: Customers & payment methods
- **sources**: https://stackoverflow.com/questions/34415987/stripe-payment-getting-error-as-customer-cus-does-not-have-a-linked-card · https://stackoverflow.com/questions/34319591/stripe-cannot-charge-a-customer-that-has-no-active-card · https://docs.stripe.com/api/customers/object

## payment-intents-with-null-customer

- **slug**: `payment-intents-with-null-customer`
- **title**: PaymentIntents have a null customer: payments orphaned
- **symptom**: The Dashboard shows a long list of payments with no customer attached. You cannot see a customer's payment history, cannot offer one-click repeat purchases, and Radar has no returning-customer signal to work with.
- **mechanism**: `customer` is optional on a PaymentIntent. Guest-checkout implementations that never create or look up a Customer produce payments that are permanently unlinkable — the card cannot be saved, `setup_future_usage` has nothing to attach to, and Radar loses the history that would otherwise let it approve a known-good buyer. Stripe's own risk models weigh customer history heavily, so the orphan cohort also declines more.
- **detect**: `GET /v1/payment_intents?limit=100&created[gte]={now-90d}` (paginate). Count `data[].customer == null` as a fraction of all intents, and sum `data[].amount` for that slice. Confirm the reuse loss by counting how many of those also have `data[].setup_future_usage == null`. Then look for the same human paying twice as a stranger: `GET /v1/charges?limit=100&created[gte]={now-90d}`, group by `data[].payment_method_details.card.fingerprint` where `data[].customer == null`, and flag fingerprints appearing more than once — those are repeat buyers with no Customer record. Search alternative: `GET /v1/charges/search?query=payment_method_details.card.fingerprint:'{fp}'`.
- **repair**: Create or look up a Customer before the intent and pass it through: `POST /v1/payment_intents -d customer=cus_X -d setup_future_usage=off_session`. In Checkout, pass an existing `customer` or set `customer_creation=always`. Backfill historical orphans by matching `payment_method_details.card.fingerprint` and `billing_details.email` to your own user table, then attaching future payments to the resolved `cus_` ID.
- **category**: Customers & payment methods
- **sources**: https://docs.stripe.com/api/payment_intents/object · https://docs.stripe.com/search · https://stackoverflow.com/questions/62280252/stripe-is-creating-duplicate-customers-when-checkout-using-different-cards

---

# Checkout & links

## checkout-expired-session-share

- **slug**: `checkout-expired-session-share`
- **title**: Most Checkout Sessions expire unpaid and nobody is told
- **symptom**: A large share of created Checkout Sessions never complete. Revenue looks flat while session creation volume is healthy, and there is no abandonment metric anywhere in the app.
- **mechanism**: A Checkout Session becomes abandoned when it reaches its `expires_at` timestamp without the customer completing checkout. If `expires_at` isn't set it defaults to 24 hours after creation (minimum 30 minutes), so abandonment is only visible a full day later via the `checkout.session.expired` event — which most integrations never subscribe to.
- **detect**: `GET /v1/checkout/sessions?created[gte]=<now-30d>&limit=100` (auto-paginate), then compute `count(status == "expired") / count(all)`. Cross-check with `GET /v1/checkout/sessions?status=expired&created[gte]=<now-30d>&limit=100` and `GET /v1/checkout/sessions?status=complete&...`. Flag when the expired share exceeds ~0.5, or when `count(status == "open" AND expires_at < now)` is non-zero (sessions that lapsed unnoticed).
- **repair**: Shorten the window at creation — `POST /v1/checkout/sessions -d expires_at=<now+7200>` (min 30 min, max 24 h) so abandonment surfaces in hours, and subscribe an event destination to `checkout.session.expired` so each lapse is recorded.
- **category**: Checkout & links
- **sources**: https://docs.stripe.com/api/checkout/sessions/object · https://docs.stripe.com/payments/checkout/abandoned-carts · https://stackoverflow.com/questions/62797608/how-to-set-a-timeout-for-a-stripe-session-checkout

## checkout-complete-payment-unpaid

- **slug**: `checkout-complete-payment-unpaid`
- **title**: Session status is complete but payment_status is still unpaid
- **symptom**: Orders are fulfilled on `checkout.session.completed` but the money never arrives, or arrives days later. Some of those payments later fail outright and the goods are already gone.
- **mechanism**: `status` and `payment_status` are independent. `status: "complete"` explicitly means "payment processing may still be in progress". Delayed payment methods (ACH Direct Debit, bank transfers) leave `payment_status: "unpaid"` and only settle later via `checkout.session.async_payment_succeeded` — or fail via `checkout.session.async_payment_failed`.
- **detect**: `GET /v1/checkout/sessions?status=complete&created[gte]=<now-90d>&limit=100` → flag every session where `payment_status == "unpaid"`. Confirm exposure by expanding the PaymentIntent: `GET /v1/checkout/sessions/{cs_id}?expand[]=payment_intent` → `payment_intent.status == "processing"` or `"requires_payment_method"`. Also list `GET /v1/checkout/sessions?limit=100` and count sessions whose `payment_method_types` includes any of `us_bank_account`, `sepa_debit`, `boleto`, `konbini`, `oxxo`.
- **repair**: Gate fulfilment on `payment_status != "unpaid"` (Stripe's own reference implementation), and register `checkout.session.async_payment_succeeded` and `checkout.session.async_payment_failed` alongside `checkout.session.completed` on the event destination.
- **category**: Checkout & links
- **sources**: https://docs.stripe.com/checkout/fulfillment · https://docs.stripe.com/api/checkout/sessions/object · https://stackoverflow.com/questions/62882815/when-does-checkout-session-completed-trigger

## checkout-sessions-unreconcilable

- **slug**: `checkout-sessions-unreconcilable`
- **title**: Checkout Sessions carry no ID that maps back to your order
- **symptom**: A payment lands and nobody can say which cart, order, or user it belongs to. Support reconciles by matching email and amount by hand, and disputes are answered with guesswork.
- **mechanism**: `client_reference_id` and `metadata` are the only two fields on a Checkout Session that carry your own identifiers, and both default to null/empty. If neither is set at creation, the Session, the PaymentIntent it creates, and the eventual Dispute all contain nothing that points back at your database.
- **detect**: `GET /v1/checkout/sessions?created[gte]=<now-30d>&limit=100` (auto-paginate) → count sessions where `client_reference_id == null` AND (`metadata` is `{}` or missing every expected key such as `order_id`). Report the ratio against total. Sessions where `payment_status == "paid"` and both are empty are the actively dangerous subset.
- **repair**: `POST /v1/checkout/sessions -d client_reference_id=<your_order_id> -d "metadata[order_id]=<your_order_id>" -d "metadata[user_id]=<uid>"`. For Payment Links set `metadata` on the link itself — link metadata is automatically copied onto every Checkout Session it creates.
- **category**: Checkout & links
- **sources**: https://docs.stripe.com/api/checkout/sessions/object · https://stackoverflow.com/questions/63850669/stripe-payment-client-reference-id · https://stackoverflow.com/questions/68916387/stripe-checkout-session-is-missing-metadata

## checkout-guest-customer-null

- **slug**: `checkout-guest-customer-null`
- **title**: Guest checkouts finish with customer null and can't be linked
- **symptom**: Paid Checkout Sessions have no Customer attached, so repeat buyers appear as strangers, the Billing Portal can't be opened for them, and lifetime-value and refund history are unqueryable.
- **mechanism**: `customer_creation` defaults to `if_required`, and Stripe only *requires* a Customer for `subscription` mode and for `payment` mode with post-purchase invoices enabled. Every other `payment`-mode Session therefore completes with `customer: null` — the email lives only in `customer_details.email`, which is not a Customer object.
- **detect**: `GET /v1/checkout/sessions?status=complete&created[gte]=<now-90d>&limit=100` (auto-paginate) → count sessions where `mode == "payment"` AND `customer == null` AND `customer_creation == "if_required"`. Confirm the config source: `GET /v1/payment_links?limit=100` → `customer_creation == "if_required"`.
- **repair**: `POST /v1/checkout/sessions -d customer_creation=always` (or pass an existing `-d customer=cus_...`). For links: `POST /v1/payment_links/{plink_id} -d customer_creation=always`.
- **category**: Checkout & links
- **sources**: https://docs.stripe.com/api/checkout/sessions/object · https://docs.stripe.com/api/payment-link/create · https://stackoverflow.com/questions/72637352/stripe-payment-link-creates-new-customer

## checkout-recovery-never-enabled

- **slug**: `checkout-recovery-never-enabled`
- **title**: Expired Checkout Sessions are never recovered by email
- **symptom**: Abandoned carts are written off entirely. No recovery email goes out, and no completed session ever references the one it rescued.
- **mechanism**: Checkout's built-in abandoned-cart recovery is opt-in via `after_expiration[recovery][enabled]=true` at session creation. Without it, the `checkout.session.expired` payload has no `after_expiration.recovery.url`, so there is nothing to embed in a follow-up email. The recovery URL, when present, is valid for 30 days (`after_expiration.recovery.expires_at`), and a session created from it carries `recovered_from` pointing at the original.
- **detect**: `GET /v1/checkout/sessions?status=expired&created[gte]=<now-60d>&limit=100` → count where `after_expiration == null` OR `after_expiration.recovery.enabled == false`. Then `GET /v1/checkout/sessions?status=complete&created[gte]=<now-60d>&limit=100` → if `count(recovered_from != null) == 0` while expired sessions are non-trivial, no recovery is happening at all. Also check `consent_collection.promotions == null` on those sessions (no consent means you may not legally email them).
- **repair**: `POST /v1/checkout/sessions -d "after_expiration[recovery][enabled]=true" -d "after_expiration[recovery][allow_promotion_codes]=true" -d "consent_collection[promotions]=auto"`, then handle `checkout.session.expired` and mail `after_expiration.recovery.url` to `customer_details.email` when `consent.promotions == "opt_in"`.
- **category**: Checkout & links
- **sources**: https://docs.stripe.com/payments/checkout/abandoned-carts · https://docs.stripe.com/api/checkout/sessions/object

## checkout-embedded-no-return-url

- **slug**: `checkout-embedded-no-return-url`
- **title**: Embedded Checkout never redirects and return_url is null
- **symptom**: Customers pay in the embedded form and are left staring at the widget. Redirect-based payment methods (iDEAL, Bancontact, 3DS challenges on some issuers) bounce back to nowhere and appear to fail.
- **mechanism**: For `ui_mode: "embedded_page"`, `redirect_on_completion` defaults to `always` but can be set to `never` — and `never` also *disables redirect-based payment methods*. `return_url` is the URL the customer returns to after authenticating on the payment method's own site; if it's null while redirect methods are enabled, that return leg has no destination.
- **detect**: `GET /v1/checkout/sessions?created[gte]=<now-30d>&limit=100` → flag sessions where `ui_mode` is `"embedded_page"` or `"elements"` AND `return_url == null`; separately flag `redirect_on_completion == "never"` combined with a `payment_method_types` array containing any redirect method (`ideal`, `bancontact`, `p24`, `sofort`, `eps`, `giropay`, `blik`). Also flag `ui_mode == "hosted_page"` sessions where `success_url` does not contain the literal `{CHECKOUT_SESSION_ID}`.
- **repair**: `POST /v1/checkout/sessions -d ui_mode=embedded_page -d return_url="https://example.com/after-checkout?session_id={CHECKOUT_SESSION_ID}" -d redirect_on_completion=if_required`. For hosted mode, add the `{CHECKOUT_SESSION_ID}` placeholder to `success_url`.
- **category**: Checkout & links
- **sources**: https://docs.stripe.com/api/checkout/sessions/object · https://docs.stripe.com/checkout/fulfillment

## payment-link-inactive-still-published

- **slug**: `payment-link-inactive-still-published`
- **title**: A deactivated Payment Link is still linked from your site
- **symptom**: Customers click a buy button and land on a page telling them the link has been deactivated. Conversion for that product silently drops to zero and nothing errors server-side.
- **mechanism**: A Payment Link's `url` stays a valid, resolvable address forever, but when `active` flips to `false` Stripe serves a deactivation page instead of checkout. Nothing propagates that state back to the HTML, CMS entry, or email template that embeds the URL.
- **detect**: `GET /v1/payment_links?limit=100` (auto-paginate; pass `-d active=false` to isolate them) → collect every `url` where `active == false`. Diff that set against the URLs referenced in your site/content. Corroborate that a dead link was in real use with `GET /v1/checkout/sessions?payment_link={plink_id}&limit=100` → recent `created` timestamps. A non-null `inactive_message` is a strong signal the link was deliberately retired and should have been unpublished.
- **repair**: Either republish the product against a live link, or reactivate: `POST /v1/payment_links/{plink_id} -d active=true`. Set `-d inactive_message="..."` with a forwarding instruction on links you intend to leave dead.
- **category**: Checkout & links
- **sources**: https://docs.stripe.com/api/payment-link/object · https://docs.stripe.com/api/payment-link/create

## payment-link-hosted-confirmation-no-fulfilment

- **slug**: `payment-link-hosted-confirmation-no-fulfilment`
- **title**: Payment Link ends on Stripe's page, so fulfilment never fires
- **symptom**: Payments from a Payment Link succeed but nothing is provisioned. The customer sees Stripe's generic confirmation page, never touches your server, and emails support asking where their purchase went.
- **mechanism**: `after_completion.type` defaults to `hosted_confirmation`, which terminates the flow on Stripe's own page. There is no redirect carrying `{CHECKOUT_SESSION_ID}` back to you, so the landing-page fulfilment trigger doesn't exist. If the account also has no webhook subscribed to `checkout.session.completed`, nothing fulfils at all — and Stripe is explicit that "you can't rely on triggering fulfillment only from your checkout landing page".
- **detect**: `GET /v1/payment_links?limit=100` → flag links where `after_completion.type == "hosted_confirmation"`. For each, `GET /v1/checkout/sessions?payment_link={plink_id}&limit=100` → count sessions with `payment_status == "paid"` and empty `metadata` / null `client_reference_id`. Then `GET /v1/webhook_endpoints?limit=100` → flag when no endpoint has `status == "enabled"` and lists `checkout.session.completed` in `enabled_events` (a `["*"]` entry also satisfies this).
- **repair**: `POST /v1/payment_links/{plink_id} -d "after_completion[type]=redirect" -d "after_completion[redirect][url]=https://example.com/after-checkout?session_id={CHECKOUT_SESSION_ID}"` — or in the Dashboard, the link's **After payment** tab, **Don't show confirmation page**. Add a `checkout.session.completed` + `checkout.session.async_payment_succeeded` endpoint regardless.
- **category**: Checkout & links
- **sources**: https://docs.stripe.com/checkout/fulfillment · https://docs.stripe.com/api/payment-link/object

## payment-link-completion-limit-reached

- **slug**: `payment-link-completion-limit-reached`
- **title**: Payment Link hit its completed-session limit and went dead
- **symptom**: A campaign link works for the first N buyers and then stops converting. No error is raised anywhere; the link just stops producing sessions.
- **mechanism**: `restrictions.completed_sessions.limit` caps how many Checkout Sessions may complete on a link. Once `restrictions.completed_sessions.count` reaches that limit the restriction is met and the link stops accepting new completions. The counter is read-only and there is no notification as it approaches the cap.
- **detect**: `GET /v1/payment_links?limit=100` (auto-paginate) → flag any link where `restrictions.completed_sessions.limit` is non-null AND `restrictions.completed_sessions.count >= restrictions.completed_sessions.limit` (exhausted), or `count / limit >= 0.9` (about to exhaust). Confirm traffic is still arriving with `GET /v1/checkout/sessions?payment_link={plink_id}&limit=100` → recent sessions with `status == "expired"` or `"open"`.
- **repair**: Raise or clear the cap — `POST /v1/payment_links/{plink_id} -d "restrictions[completed_sessions][limit]=<higher>"` — or create a fresh link for the next tranche and swap the published URL.
- **category**: Checkout & links
- **sources**: https://docs.stripe.com/api/payment-link/object · https://docs.stripe.com/api/payment-link/create

## billing-portal-no-configuration

- **slug**: `billing-portal-no-configuration`
- **title**: No Billing Portal configuration, so portal sessions 400
- **symptom**: "Manage subscription" throws a 500 in production. The Stripe error reads *"No configuration provided and your ... default configuration has not been created. Provide a configuration or create your default by saving your customer portal settings."*
- **mechanism**: `POST /v1/billing_portal/sessions` falls back to the account's default configuration when `configuration` isn't passed. That default only exists once someone saves the portal settings in the Dashboard — and test mode and live mode are configured independently, so a portal that works in test fails on the first live click.
- **detect**: `GET /v1/billing_portal/configurations?limit=100` → the failure condition is an empty `data` array, or no element with `is_default == true` AND `active == true`. Run this against the **live** key specifically: a test-mode key returning configurations proves nothing about live. Cross-check demand with `GET /v1/subscriptions?status=active&limit=100` → a non-empty result plus zero configurations means every portal click is currently erroring.
- **repair**: Save the portal settings once in the Dashboard at https://dashboard.stripe.com/settings/billing/portal (and the `/test/` equivalent), or create one via API: `POST /v1/billing_portal/configurations -d "business_profile[privacy_policy_url]=..." -d "business_profile[terms_of_service_url]=..." -d "features[invoice_history][enabled]=true"`, then pass its id as `-d configuration=bpc_...`.
- **category**: Checkout & links
- **sources**: https://docs.stripe.com/api/customer_portal/sessions/create · https://docs.stripe.com/api/customer_portal/configurations/object · https://docs.stripe.com/customer-management/activate-no-code-customer-portal

## billing-portal-cancel-disabled

- **slug**: `billing-portal-cancel-disabled`
- **title**: Billing Portal can't cancel, so customers charge back instead
- **symptom**: Customers who want out email support, wait, and then dispute the charge. Disputes cluster under reason `subscription_canceled`.
- **mechanism**: `features.subscription_cancel.enabled` defaults to `false` on a Billing Portal configuration. With no self-serve cancel button, the fastest exit a customer has is their bank. Stripe's own dispute-prevention guidance names an in-app cancellation button as "often the best solution, because it doesn't require the cardholder to wait to confirm their refund".
- **detect**: `GET /v1/billing_portal/configurations?limit=100` → flag the `is_default == true` configuration (and any referenced by your code) where `features.subscription_cancel.enabled == false`, or where `features.payment_method_update.enabled == false`. Quantify the damage: `GET /v1/disputes?created[gte]=<now-180d>&limit=100` → count `reason == "subscription_canceled"` as a share of all disputes.
- **repair**: `POST /v1/billing_portal/configurations/{bpc_id} -d "features[subscription_cancel][enabled]=true" -d "features[subscription_cancel][mode]=at_period_end" -d "features[subscription_cancel][cancellation_reason][enabled]=true" -d "features[payment_method_update][enabled]=true"`.
- **category**: Checkout & links
- **sources**: https://docs.stripe.com/api/customer_portal/configurations/object · https://docs.stripe.com/disputes/monitoring-programs

---

# API versioning & idempotency

## dead-or-rejected-enabled-events

- **slug**: `dead-or-rejected-enabled-events`
- **title**: enabled_events lists event types that are dead or rejected
- **symptom**: Branches in the webhook handler never execute — card-expiry reminders stopped going out at some point and nobody can say when. Separately, an attempt to update the endpoint fails with `You do not have access to the event types: invoiceitem.updated`.
- **mechanism**: Two decay modes. Deprecated-but-still-valid types (`source.chargeable`, `customer.source.expiring`) stay configurable but stop firing once the integration moves to PaymentMethods — Stripe documents that `customer.source.expiring` won't occur if you use the PaymentMethod API. Outright-removed types remain in stale SDK constant lists but are rejected by the API.
- **detect**: `GET /v1/webhook_endpoints?limit=100` → for each `data[].enabled_events` entry, (a) flag anything matching `^source\.` or `^customer\.source\.` while `GET /v1/events?types[]=source.chargeable&types[]=customer.source.expiring&limit=100` returns `data.length == 0` across the full 30-day window; (b) diff every entry against the live enum published in the `enabled_events` parameter of `POST /v1/webhook_endpoints` and flag any type absent from it.
- **repair**: `POST /v1/webhook_endpoints/{we_id}` with the dead entries removed from `enabled_events[]`. Replace card-expiry logic with `payment_method.automatically_updated` plus a periodic `GET /v1/payment_methods?customer=...` sweep on `card.exp_month`/`card.exp_year`; replace `source.chargeable` with PaymentIntent lifecycle events.
- **category**: API versioning & idempotency
- **sources**: https://docs.stripe.com/sources · https://docs.stripe.com/payments/older-apis · https://github.com/stripe/stripe-dotnet/issues/2763

## endpoint-api-version-pinned-stale

- **slug**: `endpoint-api-version-pinned-stale`
- **title**: A webhook endpoint is pinned to an ancient api_version
- **symptom**: Fields the current SDK expects are absent from `event.data.object`. In stripe-java, `getDataObjectDeserializer().getObject()` returns an empty `Optional`; in stripe-dotnet, `Data.Object as PaymentIntent` yields `null` **without throwing**. Re-fetching the object from the API works, so the bug looks like "Stripe sends empty objects".
- **mechanism**: `api_version` is fixed at endpoint creation and renders `data` at that version forever, independent of the account default. Statically typed SDKs (.NET, Java, Go) deserialize against the version they were generated for; when endpoint and SDK versions diverge, deserialization degrades silently *after* signature verification passes.
- **detect**: `GET /v1/webhook_endpoints?limit=100` → for each entry read `data[].api_version`. **Treat both `null` and `""` as unpinned** (`unpinned = ep.api_version in (None, "")`) — an `is not None` test misclassifies unpinned endpoints as pinned. For pinned entries, flag any `YYYY-MM-DD` prefix older than the current release line; hard-flag anything older than `2024-09-30` (pre-Acacia, where every prior bump carried breaking changes).
- **repair**: `api_version` is **not updatable** — `POST /v1/webhook_endpoints/{id}` accepts only `url`, `enabled_events`, `description`, `metadata`, `disabled`. Use the dual-endpoint migration: `POST /v1/webhook_endpoints` with the same `url` plus a distinguishing query param (`?version=<new>`), the same `enabled_events`, and the target `api_version`; ignore-and-200 those events until new code ships; then cut over and `POST /v1/webhook_endpoints/{old_we_id}` with `disabled=true`.
- **category**: API versioning & idempotency
- **sources**: https://docs.stripe.com/webhooks/versioning · https://docs.stripe.com/api/webhook_endpoints/update · https://github.com/stripe/stripe-java/issues/1177

## endpoint-api-version-drift

- **slug**: `endpoint-api-version-drift`
- **title**: Endpoints render events at different pinned API versions
- **symptom**: The same logical event reaches two services with different payload shapes. One reads `invoice.subscription`, the other reads `invoice.parent`, and only one crashes. A half-finished migration left both live.
- **mechanism**: Each endpoint pins independently, and one is often left unpinned (inheriting the account default) while another is explicitly pinned. The documented upgrade procedure deliberately creates this state temporarily — the failure mode is never finishing it. No SDK can decode two API versions at once, so there is no code-side workaround.
- **detect**: `GET /v1/webhook_endpoints?limit=100` → collect `distinct(data[].api_version)` across all `status == "enabled"` entries, **normalising both `null` and `""` to the single sentinel "account default"** before deduplicating. Flag if that set has more than one member. Report each endpoint's `url`, `api_version`, `created`, and whether URLs differ only by query string — the tell-tale sign of an abandoned migration.
- **repair**: Finish or abandon the migration. Keep exactly one endpoint per logical consumer: `POST /v1/webhook_endpoints/{losing_we_id}` with `disabled=true`, then `DELETE /v1/webhook_endpoints/{losing_we_id}` once nothing depends on it. Pin the survivor deliberately rather than leaving it unpinned.
- **category**: API versioning & idempotency
- **sources**: https://docs.stripe.com/webhooks/versioning · https://docs.stripe.com/api/webhook_endpoints/list · https://github.com/stripe/stripe-dotnet/issues/1874

## account-default-api-version-stale

- **slug**: `account-default-api-version-stale`
- **title**: Account default API version is years behind the current one
- **symptom**: New features documented in the API reference return "no such parameter" errors. Stripe-generated events and automated Billing operations arrive in an old shape. Copy-pasted docs examples fail for no visible reason.
- **mechanism**: Your version is set the first time you make an API request and never moves on its own. Automated Billing operations Stripe performs on your behalf (generating renewal invoices) use the account default. Every major release since — Acacia `2024-09-30`, Basil `2025-03-31`, Clover `2025-09-30` — carries breaking changes that accumulate.
- **detect**: **There is no API endpoint that returns the account's default API version**, and unpinned webhook endpoints report `null` or `""` rather than the inherited value — so read it indirectly: `GET /v1/events?limit=1` → `data[0].api_version`, which is the account default in force when that event was created. Flag if the `YYYY-MM-DD` prefix is more than ~12 months behind current. Corroborate by issuing any GET over raw HTTP **without** a `Stripe-Version` request header and reading the `Stripe-Version` response header (SDKs pin their own version, so use curl).
- **repair**: Read the changelog for every release between your version and current. Test first with a per-request `Stripe-Version: <target>` header without changing the account default. Then Dashboard → Workbench → Overview → API versions → **Upgrade available** → Upgrade. You get a 72-hour rollback window, during which failed new-shape webhooks are retried with the old structure.
- **category**: API versioning & idempotency
- **sources**: https://docs.stripe.com/upgrades · https://docs.stripe.com/api/versioning · https://github.com/stripe/stripe-dotnet/issues/1971

## mixed-event-api-versions

- **slug**: `mixed-event-api-versions`
- **title**: Recent events carry two different api_version values
- **symptom**: A handler that parsed fine all week starts throwing on a subset of events at a specific timestamp. Replaying an older event through the same code path succeeds.
- **mechanism**: Event objects are immutable and rendered at the account default in force when they occurred. An account upgrade, a rollback inside the 72-hour window, or a per-endpoint re-pin creates a hard boundary in the event stream, so a 30-day backfill spans two incompatible payload shapes at once. Historical example: `request` changed from a bare string ID to an object with `id` + `idempotency_key`, breaking every handler at that boundary.
- **detect**: `GET /v1/events?limit=100` paginated across the 30-day window → collect `distinct(data[].api_version)`. Flag if the set has more than one member, and report the `created` timestamp of the transition. Cross-reference `GET /v1/webhook_endpoints` → `data[].api_version` to attribute the boundary to an account upgrade versus an endpoint re-pin.
- **repair**: No Stripe-side change — this is a code fix. Branch on `event.api_version` (or defensively read both old and new field paths) for the 30-day overlap, and prefer re-fetching the object by ID (`GET /v1/payment_intents/{id}`) over trusting `data.object` shape during the transition.
- **category**: API versioning & idempotency
- **sources**: https://docs.stripe.com/api/events/object · https://docs.stripe.com/upgrades · https://github.com/stripe/stripe-dotnet/issues/908

## missing-idempotency-keys-on-payments

- **slug**: `missing-idempotency-keys-on-payments`
- **title**: Payment-creating requests carry no idempotency key
- **symptom**: Occasional duplicate charges or duplicate customers, always during network blips, timeouts, or a client-side double-click. Impossible to reproduce and disproportionately reported by customers on flaky mobile connections.
- **mechanism**: All POST requests accept an `Idempotency-Key`, but nothing requires one. Without it, a retry after a timeout — by your own code, a load balancer, or the user — executes a second real charge. Stripe saves the status code and body of the first request per key, which is exactly the protection you forgo.
- **detect**: `GET /v1/events?limit=100&types[]=payment_intent.created&types[]=charge.succeeded&types[]=customer.created&types[]=refund.created` → flag entries where `data[].request.id != null` **and** `data[].request.idempotency_key == null`. The `request.id != null` guard is mandatory: both fields are `null` for Stripe-initiated events (e.g. `customer.subscription.trial_will_end`), so omitting it produces a false positive on every automated Billing event. Report the null-key ratio per type; anything above 0% on money-moving types is a finding.
- **repair**: Send `Idempotency-Key: <v4 uuid>` on every mutating request, derived from the business operation (order ID + attempt) and never regenerated per retry. stripe-node: `stripe.paymentIntents.create(params, { idempotencyKey })`; stripe-python: `stripe.PaymentIntent.create(..., idempotency_key=key)`; stripe-php: `$stripe->paymentIntents->create($params, ['idempotency_key' => $key])` — note it goes in the **options** argument, not the params hash.
- **category**: API versioning & idempotency
- **sources**: https://docs.stripe.com/api/idempotent_requests · https://docs.stripe.com/api/events/object · https://github.com/stripe/stripe-node/issues/1951

## idempotency-key-reuse-conflict

- **slug**: `idempotency-key-reuse-conflict`
- **title**: Reused idempotency keys hit 409 idempotency_key_in_use
- **symptom**: Sporadic `409 Conflict` with "There is currently another in-progress request using this Idempotent Key", or a 400 `idempotency_error` reading "Keys for idempotent requests can only be used with the same parameters they were first used with." Under load the checkout endpoint fails for a slice of users.
- **mechanism**: Two failure shapes. Concurrent requests sharing a key collide before either result is saved (409, retryable — Stripe saves results only after endpoint execution begins). And keys are pruned after ~24 hours, so a key reused after pruning starts a genuinely new request and creates a duplicate rather than replaying. A key derived from something non-unique (a user ID, a cart ID, a date) hits both.
- **detect**: `GET /v1/events?limit=100` paginated over 30 days → group by `data[].request.idempotency_key`, ignoring nulls. Flag any key value appearing on more than one distinct `data[].request.id`, and any key appearing on events whose `created` timestamps differ by more than 86400 seconds — both prove the key is not unique per logical operation. Also flag obviously-derived keys matching `^(cus_|pi_|user[-_])` or parsing as a bare integer/date.
- **repair**: Generate a fresh v4 UUID per logical operation, persist it alongside the operation record, and reuse it only for retries of that exact request with identical parameters. On `409` / `idempotency_key_in_use`, back off and retry with the *same* key. Never use an email address or personal identifier as a key. Keys cap at 255 characters.
- **category**: API versioning & idempotency
- **sources**: https://docs.stripe.com/api/idempotent_requests · https://docs.stripe.com/api/errors · https://github.com/stripe/stripe-ruby/issues/431

---

# Reporting & reconciliation

## connect-reserved-balance-growing

- **slug**: `connect-reserved-balance-growing`
- **title**: connect_reserved keeps growing from negative account balances
- **symptom**: Your platform's `available` balance is smaller than your books say it should be, and the gap grows every month. Payouts to your own bank shrink for no visible reason.
- **mechanism**: When a connected account you're liable for goes negative (refunds, chargebacks), Stripe reserves a matching amount from your platform's `available` balance and books it as a `reserve_transaction`. If the account stays negative for 180 days, Stripe zeroes it by moving your reserve across as a `connect_collection_transfer` — a real, permanent platform loss.
- **detect**: On the platform: `GET /v1/balance` → flag `connect_reserved[].amount > 0`. Quantify the trend with `GET /v1/balance_transactions?type=reserve_transaction&limit=100&created[gte]={{now-90d}}` and `GET /v1/balance_transactions?type=connect_collection_transfer&limit=100`. Find the culprits: for each account, `GET /v1/balance` with `Stripe-Account: acct_x` → `available[].amount < 0`. Confirm liability via `GET /v1/accounts/{id}` → `controller.losses.payments == "application"`.
- **repair**: `POST /v1/transfers` to the negative account to zero it out (this releases your reserve), or `POST /v1/balance_settings` with `payments[debit_negative_balances]=true` (with `Stripe-Account`) so Stripe debits the account's own bank. For accounts already cleared by a collection transfer, `POST /v1/accounts/{id}/reject` with `reason=other` to prevent further losses.
- **category**: Reporting & reconciliation
- **sources**: https://docs.stripe.com/connect/account-balances · https://docs.stripe.com/api/balance/balance_object

## stranded-currency-balance

- **slug**: `stranded-currency-balance`
- **title**: A second-currency balance bucket can never be paid out
- **symptom**: Total Stripe balance in the Dashboard doesn't reconcile with bank deposits, and the difference is a fixed amount in a currency you barely trade in. It never moves.
- **mechanism**: `GET /v1/balance` returns `available` and `pending` as *arrays*, one entry per currency, further split by `source_types`. Automatic payouts only clear a currency with a matching `default_for_currency` external account. A handful of EUR or GBP charges on a USD-only account create a bucket that no payout will ever drain, and a reconciler that reads `available[0].amount` never notices.
- **detect**: `GET /v1/balance` (platform, and per account with `Stripe-Account`) → flag when `available.length > 1` or `pending.length > 1`. For each currency `c` with `amount > 0`, check `GET /v1/accounts/{id}/external_accounts?limit=100` has no entry with `currency == c`, and `GET /v1/payouts?limit=100` contains no payout with `currency == c` in the last 90 days. Also flag entries whose `pending` grows while `available` stays flat.
- **repair**: Add a destination for that currency: `POST /v1/accounts/{id}` with an `external_account` in currency `c`, then set `default_for_currency=true`. If you can't hold that currency, stop accepting it — remove it from your payment method configuration and drain the residue with a one-off `POST /v1/payouts` with `currency=c` once a destination exists.
- **category**: Reporting & reconciliation
- **sources**: https://docs.stripe.com/api/balance/balance_object · https://docs.stripe.com/payouts

## application-fees-zero-on-platform

- **slug**: `application-fees-zero-on-platform`
- **title**: Platform takes zero application fees on its own charges
- **symptom**: Revenue reports show marketplace GMV climbing while platform revenue stays flat at zero. The Dashboard's Connect → Application fees page is empty.
- **mechanism**: On destination charges and separate charges/transfers, an `ApplicationFee` object is only created when you pass `application_fee_amount`. Omit it (or set the fee implicitly by under-transferring via `transfer_data[amount]`) and no fee object ever exists. A related failure: passing `application_fee_amount` to an account whose `transfers` capability isn't `active` makes the whole charge fail rather than silently drop the fee.
- **detect**: `GET /v1/application_fees?limit=100&created[gte]={{now-30d}}` → flag `data.length == 0`. Compare against `GET /v1/charges?limit=100&created[gte]={{now-30d}}` → count entries with `data[].transfer_data.destination != null` but `data[].application_fee_amount == null`. Cross-check `GET /v1/balance_transactions?type=application_fee&limit=100` is likewise empty.
- **repair**: Add `application_fee_amount` (in minor units) to your PaymentIntent/Charge creation calls alongside `transfer_data[destination]`. Before doing so, verify each destination with `GET /v1/accounts/{id}` → `capabilities.transfers == "active"`, since fee collection depends on it.
- **category**: Reporting & reconciliation
- **sources**: https://docs.stripe.com/api/application_fees/object · https://docs.stripe.com/connect/charges

## payout-reconciliation-unavailable

- **slug**: `payout-reconciliation-unavailable`
- **title**: Payouts cannot be tied back to their balance transactions
- **symptom**: Finance receives a single bank deposit and can't explain which charges, refunds, fees, and transfers it contains. `GET /v1/balance_transactions?payout=po_x` returns an empty list.
- **mechanism**: Balance transactions are only listable by payout when `payout.reconciliation_status == "completed"`, and Stripe only supports that for **standard automatic** payouts. Every manual `POST /v1/payouts` produces `reconciliation_status: "not_applicable"` — meaning a platform that runs manual payouts has structurally destroyed its own payout-to-transaction linkage. Unlinked `transfer_group` values and unreconciled reversals compound the gap.
- **detect**: `GET /v1/payouts?limit=100&created[gte]={{now-90d}}` → flag `data[].reconciliation_status != "completed"` and `data[].automatic == false`. For payouts that are `completed`, verify the arithmetic: paginate `GET /v1/balance_transactions?payout={{po_id}}&limit=100` and assert `sum(data[].net) == payout.amount`. Separately, spot orphaned money movement via `GET /v1/charges?limit=100` → `data[].transfer_group == null` and `GET /v1/transfers?limit=100` → `data[].reversed == true` or `data[].amount_reversed > 0`.
- **repair**: Switch to an automatic payout schedule (`POST /v1/accounts/{id}` with `settings[payouts][schedule][interval]=daily`) so `reconciliation_status` becomes `completed`. For history you can't re-run, use the Reporting API: `POST /v1/reporting/report_runs` with `report_type=payout_reconciliation.by_id.itemized.1` and `parameters[payout]={{po_id}}`, or `payout_reconciliation.itemized.7` over an interval and join on the `automatic_payout_id` column. Always set `transfer_group` on charges and transfers going forward.
- **category**: Reporting & reconciliation
- **sources**: https://docs.stripe.com/api/payouts/object · https://docs.stripe.com/reports/report-types/payout-reconciliation · https://docs.stripe.com/api/transfers/object

## report-run-failed-silently

- **slug**: `report-run-failed-silently`
- **title**: reporting.report_run silently fails and the CSV never lands
- **symptom**: A nightly finance export stops appearing. The job "succeeded" from your app's perspective because creating the report run returned 200 — the failure happened asynchronously.
- **mechanism**: `POST /v1/reporting/report_runs` returns immediately with `status: "pending"`. The run later resolves to `succeeded` (with `result` populated) or `failed` (with `error` populated). If you don't poll or subscribe to `reporting.report_run.failed`, a run that dies on bad `interval_start`/`interval_end` parameters or an unavailable interval leaves you with no file and no alert.
- **detect**: `GET /v1/reporting/report_runs?limit=100&created[gte]={{now-30d}}` → flag `data[].status == "failed"` and read `data[].error`. Also flag runs stuck in `pending` (`data[].status == "pending"` AND `now - data[].created > 3600`), and gaps: assert that every expected day has a run with `status == "succeeded"` and a non-null `succeeded_at`.
- **repair**: Fix the parameters the `error` string names and re-issue `POST /v1/reporting/report_runs`, then poll `GET /v1/reporting/report_runs/{frr_id}` until `status` leaves `pending`. Add `reporting.report_run.failed` and `reporting.report_run.succeeded` to a webhook endpoint (verify with `GET /v1/webhook_endpoints?limit=100` → `data[].enabled_events`).
- **category**: Reporting & reconciliation
- **sources**: https://docs.stripe.com/api/reporting/report_run/object · https://docs.stripe.com/reports

## report-interval-past-data-available-end

- **slug**: `report-interval-past-data-available-end`
- **title**: Reports run past data_available_end and return short data
- **symptom**: A month-end report run succeeds but the totals are lower than the Dashboard. Re-running the identical report a day later produces different, larger numbers.
- **mechanism**: Each report type exposes `data_available_start` and `data_available_end` — the window Stripe has finalized. Data lags real time (Sigma's daily snapshot, for example, is typically ready around 14:00 UTC for the previous UTC day). Requesting an `interval_end` beyond `data_available_end` yields a truncated but *successful* report, so nothing errors.
- **detect**: `GET /v1/reporting/report_types?limit=100` → for the type you run, read `data[].data_available_end` and `data[].data_available_start`. Flag any of your `GET /v1/reporting/report_runs` where `data[].parameters.interval_end >` the matching type's `data_available_end` at the time of the run. Also flag types whose `data_available_end` is more than ~36 hours stale.
- **repair**: Gate the job: fetch `GET /v1/reporting/report_types/{type_id}` first and only create the run when `data_available_end >= interval_end`; otherwise defer. Also pin the `version` you depend on (`balance.summary.1` vs `.2`), since different versions accept different parameters and emit different schemas.
- **category**: Reporting & reconciliation
- **sources**: https://docs.stripe.com/api/reporting/report_type/object · https://docs.stripe.com/stripe-data/schedule-queries

## sigma-scheduled-query-failing

- **slug**: `sigma-scheduled-query-failing`
- **title**: Sigma scheduled query runs time out and email nothing
- **symptom**: A recurring Sigma email that finance relies on just stops arriving. Nobody notices for weeks because "no email" looks identical to "quiet week."
- **mechanism**: Scheduled query runs land in one of four terminal states: `completed`, `canceled`, `failed`, or `timed_out`. A query that grows past the execution budget as your data volume grows starts timing out, and the failure only surfaces as an absent email — plus results expire at `result_available_until`, so even successful runs go stale.
- **detect**: `GET /v1/sigma/scheduled_query_runs?limit=100` → flag `data[].status != "completed"` and read `data[].error`. Also detect silent schedule loss by asserting a run exists for each expected `data_load_time` cadence, and flag `data[].result_available_until < now` on runs whose CSV you still need. Confirm anyone is listening: `GET /v1/webhook_endpoints?limit=100` → `data[].enabled_events` contains `sigma.scheduled_query_run.created`.
- **repair**: Open the query in Dashboard → Data → Sigma, narrow it (add a `created >=` bound, drop wide joins, select fewer columns) and re-save the schedule. Then consume results programmatically rather than by email: handle `sigma.scheduled_query_run.created` and download `data.object.file.url` via `GET https://files.stripe.com/v1/files/{{FILE_ID}}/contents` before `result_available_until`.
- **category**: Reporting & reconciliation
- **sources**: https://docs.stripe.com/api/sigma/scheduled_queries/object · https://docs.stripe.com/stripe-data/schedule-queries

## terminal-readers-offline

- **slug**: `terminal-readers-offline`
- **title**: Terminal readers sit offline and take no payments
- **symptom**: A location's card volume drops to zero over a weekend. Staff say "the machine isn't doing anything" and there are no failed PaymentIntents to investigate, because none were ever created.
- **mechanism**: A reader that loses network or power reports `status: "offline"` and stops accepting `process_payment_intent` actions. `last_seen_at` (in **milliseconds**, unlike every other Stripe timestamp) is the true liveness signal — `status` alone is explicitly not recommended for blocking flows, and a reader can be stale without being marked offline yet.
- **detect**: `GET /v1/terminal/readers?limit=100` (optionally `&status=offline`, `&location={{tml_id}}`) → flag `data[].status == "offline"`, and independently flag `now_ms - data[].last_seen_at > 6*3600*1000`. Flag firmware drift by grouping `data[].device_sw_version` per `device_type` and alerting on outliers. Check `data[].action.status == "failed"` and `data[].action.failure_code` for stuck actions.
- **repair**: Power-cycle the reader and confirm the location's network allows Stripe's endpoints; then re-verify with `GET /v1/terminal/readers/{tmr_id}` → `status == "online"` and a fresh `last_seen_at`. For stale firmware, leave the reader powered and connected during its configured update window (Dashboard → Terminal → Locations → configuration). Retire dead hardware with `DELETE /v1/terminal/readers/{tmr_id}` so it stops polluting the alert.
- **category**: Reporting & reconciliation
- **sources**: https://docs.stripe.com/api/terminal/readers/object · https://docs.stripe.com/terminal

## issuing-cardholder-requirements-past-due

- **slug**: `issuing-cardholder-requirements-past-due`
- **title**: Cardholder requirements.past_due keeps every card inactive
- **symptom**: You issue a card, try to activate it, and it stays `inactive` — or activation is rejected. Every authorization on it declines instantly at the terminal.
- **mechanism**: Issuing cards default to `status: "inactive"`, and Stripe blocks activation when the linked Cardholder has past-due requirements — typically `individual.card_issuing.user_terms_acceptance.ip`, `.date`, `individual.first_name`, `individual.last_name`. The Cardholder carries `requirements.disabled_reason: "requirements.past_due"`. Declines then show up as `card_inactive` in the authorization's `request_history`.
- **detect**: `GET /v1/issuing/cardholders?limit=100` → flag `data[].requirements.disabled_reason != null` or `data[].requirements.past_due.length > 0`, and `data[].status != "active"`. Then `GET /v1/issuing/cards?status=inactive&limit=100` → correlate `data[].cardholder.id`. Confirm impact with `GET /v1/issuing/authorizations?limit=100` → flag `data[].approved == false` and read `data[].request_history[].reason` (e.g. `card_inactive`, `cardholder_inactive`, `verification_failed`, `insufficient_funds`, `spending_controls`, `webhook_timeout`).
- **repair**: `POST /v1/issuing/cardholders/{ich_id}` supplying every field in `requirements.past_due` — including `individual[card_issuing][user_terms_acceptance][date]` and `[ip]` captured at the moment the cardholder accepted the Authorized User Terms. Then `POST /v1/issuing/cards/{ic_id}` with `status=active`. If declines are `insufficient_funds`, top up via `GET /v1/balance` → `issuing.available[]` and `POST /v1/topups`.
- **category**: Reporting & reconciliation
- **sources**: https://docs.stripe.com/api/issuing/cards/object · https://docs.stripe.com/api/issuing/authorizations/object

---
