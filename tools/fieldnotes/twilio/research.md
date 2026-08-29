# Twilio field notes — problem research

Every problem a Twilio integration can hit that a **read-only Twilio credential** can
detect through the API. Each entry carries a slug, a one-line failure title, the symptom
(with the Twilio error code where one exists), the mechanism, the exact read-only call and
field that detects it, the repair we print but never execute, a category, and sources.

**117 problems** across 8 categories.

| Category | Count |
| --- | --: |
| Messaging delivery | 18 |
| A2P 10DLC & compliance | 18 |
| Phone numbers & Messaging Services | 14 |
| Webhooks & callbacks | 21 |
| Voice | 11 |
| Verify & Lookup | 10 |
| Account & billing | 15 |
| Regulatory & geo | 10 |
| **Total** | **117** |

## Scope and known blind spots

- Every `detect` step is a `GET` (or a response header on a `GET`). No repair is executed;
  repairs are printed for a human to run.
- `GET https://monitor.twilio.com/v1/Alerts` is the single most important surface here, but
  `response_body`, `response_headers`, `request_headers` and `request_variables` are populated
  **only** on the single-alert fetch `GET /v1/Alerts/{AlertSid}`, never in the list response.
  Any check that needs to see what a webhook actually returned must do a second fetch per alert.
- Alerts are retained 30 days, capped at 10,000 per request. All trend analysis is bounded by that.
- Several real failures are logged at `LogLevel=warning`, not `error` (12200 schema validation,
  32012 CPS, several 132xx Dial attribute errors). Sweep both levels.
- `GET .../Messages.json` has **no** `Status` or `ErrorCode` filter — only `To`, `From`, `DateSent`,
  `DateSent<`, `DateSent>`, `PageSize`, `Page`, `PageToken`. Error-code detection means paging the
  list and filtering client-side.
- Request-time rejections (21211, 21606, 21617, 21703, 21704, 21620) often never create a Message
  row at all, so Alerts is the only read-only path for those.
- No read API exists for: the STOP/opt-out blocklist, SMS Geo Permissions, Verify Fraud Guard's
  enable state, Messaging Insights, or the Messaging Health Score. Those are inferred from error
  codes and conversion rates instead, and each is flagged in the relevant entry.
- Deprecated fields to avoid: `BrandRegistration.brand_feedback` and `.failure_reason` (use
  `errors[]`); error codes 30026/30027 are no longer generated; 30010 is obsolete.

## Table of contents

### Messaging delivery (18)

- [`carrier-filtered-messages-30007`](#carrier-filtered-messages-30007) — Carrier or Twilio silently filters your SMS as spam
- [`unreachable-destination-handset-30003`](#unreachable-destination-handset-30003) — Handset unreachable: phone off, roaming, or out of coverage
- [`unknown-destination-handset-30005`](#unknown-destination-handset-30005) — Destination number no longer exists on the carrier
- [`landline-destination-30006`](#landline-destination-30006) — Sending SMS to landlines that can never receive it
- [`messaging-queue-overflow-30001`](#messaging-queue-overflow-30001) — Send loop outruns sender throughput and overflows the queue
- [`validity-period-expired-30036`](#validity-period-expired-30036) — Messages expire in queue because ValidityPeriod is too low
- [`opted-out-recipients-21610`](#opted-out-recipients-21610) — Sends to STOP'd recipients bounce and pollute your list
- [`sms-pumping-protection-30450`](#sms-pumping-protection-30450) — SMS Pumping Protection blocks legit OTPs for 15–30 minutes
- [`body-exceeds-1600-chars-21617`](#body-exceeds-1600-chars-21617) — Rendered template blows past the 1600-character body limit
- [`ucs2-segment-inflation`](#ucs2-segment-inflation) — One emoji triples your segment count and your bill
- [`mms-content-size-exceeds-carrier-30019`](#mms-content-size-exceeds-carrier-30019) — MMS image too large for the destination carrier
- [`deactivated-number-recycling`](#deactivated-number-recycling) — Recycled numbers send OTPs to the wrong person
- [`messages-stuck-queued-or-accepted`](#messages-stuck-queued-or-accepted) — Messages sit in queued/accepted and never reach a final state
- [`trial-account-segment-limit-30044`](#trial-account-segment-limit-30044) — Trial account rejects multi-segment messages
- [`outbound-messaging-disabled-30037`](#outbound-messaging-disabled-30037) — Subaccount cannot send: outbound messaging disabled
- [`status-callback-webhook-failing-11200`](#status-callback-webhook-failing-11200) — StatusCallback endpoint failing, so delivery state is blind
- [`link-shortening-cert-expiring`](#link-shortening-cert-expiring) — Link-shortening domain certificate expires and links break
- [`whatsapp-content-template-rejected`](#whatsapp-content-template-rejected) — A WhatsApp content template is rejected and sends fail

### A2P 10DLC & compliance (18)

- [`a2p-brand-registration-failed`](#a2p-brand-registration-failed) — A2P Brand registration is FAILED, so no campaign can attach
- [`a2p-brand-tax-id-legal-name-mismatch`](#a2p-brand-tax-id-legal-name-mismatch) — Brand failed 30799: the EIN does not match the legal name
- [`a2p-brand-stuck-pending-review`](#a2p-brand-stuck-pending-review) — Brand sat in PENDING/IN_REVIEW for weeks with no callback
- [`a2p-brand-suspended`](#a2p-brand-suspended) — A SUSPENDED brand silently suspends every campaign under it
- [`a2p-brand-missing-secondary-vetting`](#a2p-brand-missing-secondary-vetting) — Approved brand has no trust score, so throughput is floored
- [`sole-prop-otp-never-accepted`](#sole-prop-otp-never-accepted) — Sole Proprietor brand blocked: the SMS OTP expired unanswered
- [`sole-prop-extra-numbers-unregistered`](#sole-prop-extra-numbers-unregistered) — Sole Prop campaign has extra numbers that never register
- [`a2p-campaign-vetting-failed`](#a2p-campaign-vetting-failed) — Campaign is FAILED and errors[] names the exact rejection
- [`a2p-campaign-stuck-in-progress`](#a2p-campaign-stuck-in-progress) — Campaign parked at IN_PROGRESS while devs assume it is live
- [`a2p-campaign-suspended-30033`](#a2p-campaign-suspended-30033) — Carrier suspends your 10DLC campaign for policy violation
- [`a2p-throughput-exceeded-30022`](#a2p-throughput-exceeded-30022) — Sends burst past the campaign's carrier-assigned throughput
- [`tmobile-brand-daily-segment-cap`](#tmobile-brand-daily-segment-cap) — T-Mobile daily brand cap silently drops the day's later sends
- [`messaging-service-not-a2p-registered`](#messaging-service-not-a2p-registered) — Messaging Service has no A2P campaign attached at all
- [`number-missing-from-campaign-sender-pool`](#number-missing-from-campaign-sender-pool) — 10DLC number sends direct, bypassing the approved campaign
- [`sender-pending-carrier-provisioning`](#sender-pending-carrier-provisioning) — New sender not yet provisioned on the carrier network
- [`tollfree-number-not-verified`](#tollfree-number-not-verified) — Toll-free number is unverified, so all US/CA SMS is blocked
- [`tollfree-verification-rejected`](#tollfree-verification-rejected) — Toll-free verification is TWILIO_REJECTED with a coded reason
- [`tollfree-edit-window-expiring`](#tollfree-edit-window-expiring) — A rejected toll-free record's 7-day edit window is about to lapse

### Phone numbers & Messaging Services (14)

- [`phone-number-missing-fallback-url`](#phone-number-missing-fallback-url) — Phone number has no fallback URL, so an 11200 drops the call
- [`phone-number-insecure-or-unreachable-webhook-url`](#phone-number-insecure-or-unreachable-webhook-url) — Number webhook uses http://, localhost, or a tunnel URL
- [`phone-number-still-on-demo-twiml`](#phone-number-still-on-demo-twiml) — Number still points at Twilio's demo TwiML endpoint
- [`number-conflicting-url-and-application-sid`](#number-conflicting-url-and-application-sid) — Number has both a webhook URL and an Application SID set
- [`number-not-in-messaging-service`](#number-not-in-messaging-service) — SMS-capable number sits outside any Messaging Service
- [`messaging-service-empty-sender-pool`](#messaging-service-empty-sender-pool) — Messaging Service sender pool is empty, so every send 21704s
- [`no-sender-matching-destination`](#no-sender-matching-destination) — Pool has senders but none can reach the To (21703)
- [`from-number-not-sms-capable`](#from-number-not-sms-capable) — The From number cannot do SMS, so every send is 21606
- [`messaging-service-no-status-callback`](#messaging-service-no-status-callback) — No status_callback, so delivery failures never reach your app
- [`inbound-webhook-black-hole`](#inbound-webhook-black-hole) — Inbound webhook deferred to a number that has no sms_url
- [`sms-reply-loop-rate-limit-14107`](#sms-reply-loop-rate-limit-14107) — Auto-reply loop trips the SMS rate limit (14107)
- [`messaging-service-validity-period-too-long`](#messaging-service-validity-period-too-long) — A 36000-second validity period keeps dead messages queued 10h
- [`multiple-tollfree-in-one-pool`](#multiple-tollfree-in-one-pool) — Two toll-free numbers in one sender pool get the pool blocked
- [`idle-phone-numbers-billed`](#idle-phone-numbers-billed) — Phone numbers with no traffic still bill every month

### Webhooks & callbacks (21)

- [`webhook-http-retrieval-failure-11200`](#webhook-http-retrieval-failure-11200) — Webhook URL returns non-2xx, so Twilio errors with 11200
- [`webhook-connection-timeout-11205`](#webhook-connection-timeout-11205) — Twilio cannot open a TCP connection to your webhook (11205)
- [`webhook-http-protocol-violation-11206`](#webhook-http-protocol-violation-11206) — Webhook response violates HTTP, so Twilio errors with 11206
- [`webhook-dns-resolution-failure-11210`](#webhook-dns-resolution-failure-11210) — Webhook hostname has no public DNS record (11210)
- [`webhook-tls-handshake-failure-11220`](#webhook-tls-handshake-failure-11220) — TLS handshake with your webhook fails, raising error 11220
- [`webhook-tls-certificate-expired-11236`](#webhook-tls-certificate-expired-11236) — Webhook TLS certificate has expired, raising error 11236
- [`webhook-tls-chain-untrusted-11237`](#webhook-tls-chain-untrusted-11237) — Webhook cert chain is incomplete or self-signed (11237)
- [`twiml-response-body-too-large-11750`](#twiml-response-body-too-large-11750) — TwiML response exceeds the 64 kB limit (11750)
- [`twiml-document-parse-failure-12100`](#twiml-document-parse-failure-12100) — TwiML is not well-formed XML, so Twilio errors with 12100
- [`twiml-schema-validation-warning-12200`](#twiml-schema-validation-warning-12200) — TwiML verb is misspelled or wrongly cased (12200)
- [`webhook-invalid-content-type-12300`](#webhook-invalid-content-type-12300) — Webhook returns the wrong Content-Type for TwiML (12300)
- [`webhook-signature-validation-403-behind-proxy`](#webhook-signature-validation-403-behind-proxy) — Signature check rejects Twilio with 403 behind a proxy
- [`studio-flow-draft-not-published`](#studio-flow-draft-not-published) — Studio Flow is still in draft, so live traffic runs old logic
- [`studio-flow-invalid-definition`](#studio-flow-invalid-definition) — Studio Flow definition is invalid and widgets never run
- [`studio-flow-not-wired-to-number`](#studio-flow-not-wired-to-number) — A published Studio Flow that no phone number points at
- [`conversations-webhook-filters-empty`](#conversations-webhook-filters-empty) — Conversations webhooks fire for no events: filters are empty
- [`conversations-webhook-url-missing`](#conversations-webhook-url-missing) — Conversation webhook configured with no target URL (50369)
- [`conversations-webhook-limit`](#conversations-webhook-limit) — Conversation already has five webhooks, so a sixth is rejected
- [`event-streams-sink-failed`](#event-streams-sink-failed) — An Event Streams Sink is failed and events are being dropped
- [`no-error-log-subscription`](#no-error-log-subscription) — Nothing subscribes to error-log events, so failures are invisible
- [`sync-webhook-url-invalid`](#sync-webhook-url-invalid) — Sync Service webhook URL is rejected as invalid (54051)

### Voice (11)

- [`dial-number-unsupported-or-invalid-13224`](#dial-number-unsupported-or-invalid-13224) — Dial target is unsupported or invalid, raising error 13224
- [`dial-invalid-caller-id-13214`](#dial-invalid-caller-id-13214) — Forwarded caller ID is invalid, so Dial is rejected (13214)
- [`outbound-call-failure-rate-spike`](#outbound-call-failure-rate-spike) — A rising share of outbound calls end in status failed
- [`amd-machine-answer-misrouting`](#amd-machine-answer-misrouting) — Answering-machine detection sends humans to the voicemail flow
- [`recording-absent-with-error-code`](#recording-absent-with-error-code) — Call recordings silently absent with an error code
- [`sip-endpoint-not-registered-32009`](#sip-endpoint-not-registered-32009) — SIP user is not registered on the domain, so Dial fails
- [`sip-infrastructure-communication-error-32011`](#sip-infrastructure-communication-error-32011) — Twilio cannot reach your SIP infrastructure (32011)
- [`trunk-cps-limit-exceeded-32001`](#trunk-cps-limit-exceeded-32001) — SIP trunk exceeds its calls-per-second limit (32001)
- [`carrier-blocked-caller-id-32017`](#carrier-blocked-caller-id-32017) — Carrier blocks your caller ID for poor reputation (32017)
- [`trunk-missing-disaster-recovery-url`](#trunk-missing-disaster-recovery-url) — SIP trunk has no disaster recovery URL configured
- [`sip-domain-no-auth-type`](#sip-domain-no-auth-type) — SIP Domain has no auth_type and accepts no traffic at all

### Verify & Lookup (10)

- [`verify-lookup-disabled`](#verify-lookup-disabled) — Verify Service has lookup_enabled false, so landlines are billed
- [`verify-sms-to-landline`](#verify-sms-to-landline) — Verify sends SMS to landlines, giving 60205 or silence
- [`verify-code-length-too-short`](#verify-code-length-too-short) — Verify code_length is 4, so brute force needs about 50 guesses
- [`verify-no-rate-limits`](#verify-no-rate-limits) — Verify Service has zero Rate Limits configured
- [`verify-conversion-rate-collapse`](#verify-conversion-rate-collapse) — Verify conversion rate collapsing: SMS pumping in progress
- [`fraud-guard-blocking-prefix`](#fraud-guard-blocking-prefix) — Fraud Guard blocked the prefix, so legit users get 60410
- [`verify-max-check-attempts`](#verify-max-check-attempts) — Verification burned all five checks, so 60202 until it expires
- [`verify-max-send-attempts`](#verify-max-send-attempts) — Resend-code loop with no check trips 60203 max send attempts
- [`verify-do-not-share-warning-off`](#verify-do-not-share-warning-off) — OTP body ships without the do-not-share phishing warning
- [`lookup-invalid-or-uncovered-number`](#lookup-invalid-or-uncovered-number) — Number is invalid or uncovered, giving 21211 or 60600

### Account & billing (15)

- [`read-credential-permission-denied`](#read-credential-permission-denied) — API credential rejected: Twilio returns 20003 permission denied
- [`account-suspended-or-closed`](#account-suspended-or-closed) — Account status is suspended, so every send fails with 20005
- [`trial-account-still-in-use`](#trial-account-still-in-use) — Account is still Trial, so sends are restricted and prefixed
- [`trial-verified-caller-ids-exhausted`](#trial-verified-caller-ids-exhausted) — Trial verified-number pool exhausted, so 21608 on new testers
- [`balance-below-safety-floor`](#balance-below-safety-floor) — Account balance is one busy hour from a 20005 suspension
- [`no-usage-trigger-configured`](#no-usage-trigger-configured) — No Usage Trigger set, so fraud or overspend runs unalarmed
- [`auth-token-used-instead-of-api-key`](#auth-token-used-instead-of-api-key) — No API keys exist, so the account Auth Token is the credential
- [`stale-or-orphaned-api-keys`](#stale-or-orphaned-api-keys) — Years-old API keys are still live with no owner
- [`subaccount-suspended-silently`](#subaccount-suspended-silently) — A subaccount is suspended, so that tenant's traffic 20005s
- [`rest-api-concurrency-exhausted`](#rest-api-concurrency-exhausted) — REST concurrency limit hit, so bursts return 20429
- [`pinned-old-api-version`](#pinned-old-api-version) — Numbers still pinned to the stale 2008-08-01 API version
- [`eol-programmable-chat-in-use`](#eol-programmable-chat-in-use) — Account still runs Programmable Chat, dead 1 June 2026
- [`eol-notify-service-in-use`](#eol-notify-service-in-use) — Account still holds Notify services after Notify's EOL
- [`unreleased-recordings-storage`](#unreleased-recordings-storage) — Call recordings accumulate and bill for storage forever
- [`recordings-not-encrypted`](#recordings-not-encrypted) — Call recordings are stored without customer-key encryption

### Regulatory & geo (10)

- [`sms-geo-permissions-disabled`](#sms-geo-permissions-disabled) — SMS Geo Permissions off for the destination country (21408)
- [`voice-dialing-permissions-blocked`](#voice-dialing-permissions-blocked) — Voice dialing permissions block the destination (21215/13227)
- [`high-risk-dialing-permissions-open`](#high-risk-dialing-permissions-open) — High-risk toll-fraud dialing prefixes are left enabled
- [`regulatory-bundle-rejected`](#regulatory-bundle-rejected) — Regulatory Bundle is twilio-rejected, blocking number purchase
- [`regulatory-bundle-expiring`](#regulatory-bundle-expiring) — Approved bundle's valid_until is near; numbers face reclamation
- [`bundle-evaluation-noncompliant`](#bundle-evaluation-noncompliant) — Bundle evaluates noncompliant: a required field never passed
- [`trusthub-customer-profile-rejected`](#trusthub-customer-profile-rejected) — Trust Hub Customer Profile rejected, cascading into A2P and TFV
- [`alphanumeric-sender-id-unregistered`](#alphanumeric-sender-id-unregistered) — Alphanumeric Sender ID unregistered for the destination country
- [`shortcode-cross-border-sender-mismatch`](#shortcode-cross-border-sender-mismatch) — Short code used outside its own country fails 21612 or 21606
- [`emergency-address-unregistered`](#emergency-address-unregistered) — US/CA numbers have no registered E911 emergency address

---

# Messaging delivery

## carrier-filtered-messages-30007

- **title** — Carrier or Twilio silently filters your SMS as spam
- **symptom** — `status=undelivered` with `error_code=30007` ("Message filtered"). No delivery receipt, the recipient never sees anything, and you are still billed.
- **mechanism** — Twilio or the destination carrier blocked the message for violating the Messaging Policy / AUP or carrier rules: spam-shaped content, public URL shorteners, an unregistered sender, or a sender whose reputation has been damaged.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=YYYY-MM-DD&PageSize=1000` → count rows where `status == "undelivered" && error_code == 30007`. Cross-check `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 30007`.
- **repair** — No API fix. Rewrite content (drop public link shorteners, add an opt-out footer), confirm the A2P campaign use case matches the actual traffic, then collect 3+ Message SIDs with 30007 and open a Twilio Support ticket for a filtering review.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/30007 · https://support.twilio.com/hc/en-us/articles/360008704834-Error-30007-Message-Delivery-Message-Filtered-when-Sending-SMS

## unreachable-destination-handset-30003

- **title** — Handset unreachable: phone off, roaming, or out of coverage
- **symptom** — `status=undelivered` with `error_code=30003`, often clustered on the same recipients or the same carrier.
- **mechanism** — The device is powered off, has no signal, is roaming off its home network, or the destination is a landline. Persistent 30003 across many recipients can also mask carrier-side blocking of your sender.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → `status == "undelivered" && error_code == 30003`. Group by `to` (repeat offenders are dead numbers) and by `from` (concentration on one sender means blocking, not handsets).
- **repair** — Retry once after a delay for one-off failures. For numbers failing repeatedly, run `GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=line_type_intelligence` and drop anything not `mobile`. If 30003 concentrates on a single sender, escalate 3+ Message SIDs to Support.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/30003 · https://help.twilio.com/articles/360008508774

## unknown-destination-handset-30005

- **title** — Destination number no longer exists on the carrier
- **symptom** — `status=undelivered` with `error_code=30005` ("Unknown destination handset"). The same number fails every single time, forever.
- **mechanism** — The number was disconnected, never existed, or is a landline. The carrier does not recognise it at all — permanent, unlike 30003.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → `error_code == 30005`. Treat any `to` with two or more occurrences across distinct days as permanently dead.
- **repair** — Hard-delete those numbers from the sending list; never retry. Validate at capture time with `GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=line_type_intelligence` and reject invalid or non-mobile results.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/30005 · https://support.twilio.com/hc/en-us/articles/360008704674

## landline-destination-30006

- **title** — Sending SMS to landlines that can never receive it
- **symptom** — `error_code=30006` ("Landline or unreachable carrier") on undelivered messages, or `21614` ("'To' number is not a valid mobile number") rejected at request time.
- **mechanism** — The destination is a landline or VoIP line that cannot receive SMS, or a short code cannot reach that carrier. Retrying never helps.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → `error_code in [30006, 21614]`; collect distinct `to`. Confirm each with `GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=line_type_intelligence` → `line_type_intelligence.type == "landline"`.
- **repair** — Add a Lookup Line Type Intelligence gate before enqueueing, and flag landline contacts for voice or email instead. If sending from a short code, add a long-code fallback sender to the Messaging Service sender pool.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/30006 · https://www.twilio.com/docs/api/errors/21614

## messaging-queue-overflow-30001

- **title** — Send loop outruns sender throughput and overflows the queue
- **symptom** — Bulk jobs return `error_code=30001` ("Queue overflow"), or `21611` at request time ("This 'From' number has exceeded the maximum number of queued messages"). Messages queue for hours, then fail.
- **mechanism** — Each sender's queue holds roughly 10 hours of message segments at that sender's throughput (a US long code is about 1 MPS, a short code 100+ MPS). Firing thousands of messages at one long code overflows it.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → `error_code in [30001, 21611]`, grouped by `from`. Also `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 21611`. Check pool breadth with `GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers`.
- **repair** — Send through a Messaging Service (`MessagingServiceSid=MG…`) instead of a bare `From`, add senders with `POST https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers` (`PhoneNumberSid=PN…`), and rate-limit the producer to the sender's MPS. Escalate to toll-free or a short code for high volume.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/30001 · https://www.twilio.com/docs/api/errors/21611 · https://www.twilio.com/docs/messaging/guides/scaling-queueing-latency

## validity-period-expired-30036

- **title** — Messages expire in queue because ValidityPeriod is too low
- **symptom** — `error_code=30036` ("Validity Period Expired") — the messages never left Twilio. Related: `30045` (out of range, must be 1–36,000s) and `30012` (TTL too small) at request time.
- **mechanism** — `ValidityPeriod` (message-level or Messaging Service-level) is shorter than the actual queue wait, so throttled messages time out before their turn. The default is 36,000s.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → `error_code in [30036, 30045, 30012]`. Then `GET https://messaging.twilio.com/v1/Services/{ServiceSid}` → `validity_period` well below 36000.
- **repair** — `POST https://messaging.twilio.com/v1/Services/{ServiceSid}` with `ValidityPeriod=36000`, and stop passing a low per-message `ValidityPeriod`. Also reduce batch size so the queue drains.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/30036 · https://www.twilio.com/docs/api/errors/30045

## opted-out-recipients-21610

- **title** — Sends to STOP'd recipients bounce and pollute your list
- **symptom** — `error_code=21610` ("Attempt to send to unsubscribed recipient" / the from-to pair violates a blocklist rule). Rejected at request time, not billed.
- **mechanism** — The recipient replied STOP/UNSUBSCRIBE/CANCEL/QUIT to that sender or Messaging Service and your database never recorded it. The number may also have been reassigned to a new subscriber who opted out.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → collect distinct `to` where `error_code == 21610`. Also `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 21610`, and scan inbound messages (`direction == "inbound"`) whose `body` matches `^(STOP|STOPALL|UNSUBSCRIBE|CANCEL|END|QUIT)$`.
- **repair** — Mark those numbers unsubscribed in your own database — Twilio exposes no opt-out list read API. Only the recipient texting START/UNSTOP/YES re-subscribes them. Configure Advanced Opt-Out on the Messaging Service so keywords and confirmations are consistent across senders.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/21610 · https://www.twilio.com/docs/messaging/tutorials/advanced-opt-out

## sms-pumping-protection-30450

- **title** — SMS Pumping Protection blocks legit OTPs for 15–30 minutes
- **symptom** — OTP sends suddenly fail with `error_code=30450` ("Message delivery blocked") to one region or prefix, then recover on their own. Related: `30485`.
- **mechanism** — Twilio's fraud heuristics matched your traffic pattern to SMS pumping (artificially inflated traffic) against an unusual destination and applied a temporary block on that destination or region.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → `error_code in [30450, 30485]`. Group by the country prefix of `to` to see whether the block is region-scoped and time-bounded.
- **repair** — For genuinely legitimate destinations, add the numbers or prefixes to the Global Safe List (Console → Messaging → Settings → Global Safe List), or send that specific traffic with `RiskCheck=disable`. Keep RiskCheck on for OTP flows generally; escalate three Message SIDs if legitimate traffic keeps being blocked.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/30450 · https://www.twilio.com/docs/messaging/features/sms-pumping-protection-programmable-messaging

## body-exceeds-1600-chars-21617

- **title** — Rendered template blows past the 1600-character body limit
- **symptom** — `error_code=21617` ("The concatenated message body exceeds the 1600 character limit"). Request rejected, nothing sent — usually only for the subset of users with long interpolated values.
- **mechanism** — Template variables (names, addresses, product lists) expanded past 1600 characters at send time, and non-ASCII characters consumed extra encoding space.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&StartDate=…` → `error_code == 21617`. Rejected sends never create a Message row, so Alerts is the reliable read path. Also scan `Messages.json` for `num_segments >= 8` as a near-miss warning.
- **repair** — Truncate server-side before calling the API, or split into multiple messages. Validate the fully rendered body length rather than the template, and prefer under 320 characters for deliverability.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/21617 · https://help.twilio.com/articles/360033806753

## ucs2-segment-inflation

- **title** — One emoji triples your segment count and your bill
- **symptom** — No error code. Messages deliver, but `num_segments` is 3–5× expected and the SMS bill jumps. Long messages may also arrive out of order on the handset.
- **mechanism** — A single non-GSM-7 character (emoji, a smart quote pasted from a WYSIWYG editor, an accented letter) forces UCS-2 encoding for the entire body: 70 characters per segment instead of 160 (67 vs 153 when concatenated). Smart Encoding transliterates the common offenders but is a per-service toggle.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…&PageSize=1000` → flag rows where `num_segments >= 2 && len(body) < num_segments * 100` (the UCS-2 signature). Confirm the mitigation is off via `GET https://messaging.twilio.com/v1/Services/{ServiceSid}` → `smart_encoding == false`. Corroborate cost impact with `GET /2010-04-01/Accounts/{AccountSid}/Usage/Records/Daily.json?Category=sms-outbound` and compare `count` against `usage`.
- **repair** — `POST https://messaging.twilio.com/v1/Services/{ServiceSid}` with `SmartEncoding=true` (Console → Messaging → Services → Content Settings), and normalise curly quotes and dashes at template-authoring time.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/messaging/api/service-resource · https://www.twilio.com/docs/messaging/services

## mms-content-size-exceeds-carrier-30019

- **title** — MMS image too large for the destination carrier
- **symptom** — `error_code=30019` ("Content size exceeds carrier limit") on undelivered MMS. The same image delivers to some carriers and not others.
- **mechanism** — Twilio's hard ceiling is 5 MB for body plus attachments, but carrier ceilings are far lower — roughly 300–600 KB on many networks (AT&T short-code MMS caps at 600 KB), up to about 3.5 MB on tier-1 carriers.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → `error_code == 30019 && num_media > 0`. Then `GET /2010-04-01/Accounts/{AccountSid}/Messages/{MessageSid}/Media.json` to identify the offending media, and HEAD the original `MediaUrl` for `Content-Length`.
- **repair** — Resize or recompress to under 600 KB before hosting, serve only jpeg/png/gif (the three formats Twilio transcodes), and enable the MMS Converter: `POST https://messaging.twilio.com/v1/Services/{ServiceSid}` with `MmsConverter=true`.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/30019 · https://www.twilio.com/docs/messaging/guides/accepted-mime-types

## deactivated-number-recycling

- **title** — Recycled numbers send OTPs to the wrong person
- **symptom** — No error at all. Messages report `delivered`, but OTPs and account alerts reach a stranger who now owns the recycled number, and complaint rates rise — which later triggers 30007 filtering.
- **mechanism** — US carriers deactivate and reissue numbers to new subscribers. Your contact list still maps the number to the old owner until you reconcile against the daily deactivation feed.
- **detect** — `GET https://messaging.twilio.com/v1/Deactivations?Date=YYYY-MM-DD` → follow `redirect_to` (a signed URL, valid about two minutes) to fetch the newline-delimited E.164 list, then intersect with the numbers in your contact table. Free of charge.
- **repair** — Run the Deactivations pull daily, suppress or re-verify every matched number before sending again, and never carry an old consent record onto a recycled number.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/messaging/api/deactivations-resource · https://support.twilio.com/hc/en-us/articles/360042744973-Handling-Deactivated-Phone-Numbers

## messages-stuck-queued-or-accepted

- **title** — Messages sit in queued/accepted and never reach a final state
- **symptom** — `status` stays `queued`, `accepted`, or `sending` for hours with `error_code = null` and `date_sent` null. Eventually they flip to `failed` (30001/30036) — or, on carriers that send no DLR, they stop at `sent` and never become `delivered`.
- **mechanism** — Throughput starvation on the sender, or a scheduled message whose `SendAt` has not arrived. Separately, `sent` is a legitimate terminal state on carriers that return no delivery receipt, so treating `sent` as failure is a false alarm.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…&PageSize=1000` → rows where `status in ["queued","accepted","sending","scheduled"]` and `date_created` is older than about an hour. Separately count `status == "sent"` with no later `delivered` transition. Scheduled sends show `status == "scheduled"` with a future `SendAt` (15 minutes to 35 days out, 500,000 pending max, and no status callbacks).
- **repair** — Age out anything queued past your SLA and resend through a Messaging Service with a wider sender pool; raise `ValidityPeriod` to 36000; cancel unwanted scheduled sends with `POST /2010-04-01/Accounts/{AccountSid}/Messages/{MessageSid}.json` `Status=canceled`. Treat `sent` as success where the destination carrier provides no DLR.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/messaging/api/message-resource · https://www.twilio.com/docs/messaging/features/message-scheduling

## trial-account-segment-limit-30044

- **title** — Trial account rejects multi-segment messages
- **symptom** — `error_code=30044` ("Trial account message length exceeded"). Short test messages send fine but real templates fail.
- **mechanism** — Trial accounts cap message length far below paid accounts. A single non-GSM-7 character flips the whole body to UCS-2 and drops the per-segment budget from 160 to 70 characters, so a template that "fits" in testing does not in production.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}.json` → `type == "Trial"`. Then `Messages.json?DateSent>=…` → `error_code == 30044`, and check `num_segments > 1` on the failures.
- **repair** — Upgrade the account (Console → Billing → Upgrade), or shorten the body and strip Unicode. If sending via a Messaging Service, enable Smart Encoding: `POST https://messaging.twilio.com/v1/Services/{ServiceSid}` with `SmartEncoding=true`.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/30044 · https://support.twilio.com/hc/en-us/articles/360036052753-Twilio-Free-Trial-Limitations

## outbound-messaging-disabled-30037

- **title** — Subaccount cannot send: outbound messaging disabled
- **symptom** — `error_code=30037` ("Outbound message not allowed") on every send from one account or subaccount, while other accounts work fine.
- **mechanism** — Outbound messaging was disabled on that subaccount, the subaccount is suspended, or the code is authenticating with the wrong Account SID or API key.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}.json` → `status != "active"`. Enumerate `GET /2010-04-01/Accounts.json` for per-subaccount `status`, and match the failing `account_sid` on `Messages.json` rows with `error_code == 30037`.
- **repair** — Confirm the credential's Account SID matches the intended subaccount. Reactivate with `POST /2010-04-01/Accounts/{SubAccountSid}.json` `Status=active`. If the parent is suspended, only Support can lift it.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/30037 · https://www.twilio.com/docs/iam/api/subaccounts

## status-callback-webhook-failing-11200

- **title** — StatusCallback endpoint failing, so delivery state is blind
- **symptom** — Floods of `error_code=11200` ("HTTP retrieval failure") alerts. Your database shows every message stuck at `queued`/`sent` because the callbacks never landed, even though Twilio delivered them.
- **mechanism** — The StatusCallback URL returns non-2xx, times out on slow synchronous processing, is firewalled, or returns the wrong Content-Type. Twilio does not retry indefinitely.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&StartDate=…` → `error_code == 11200`; read `request_url` and `alert_text` to identify the failing endpoint. Reconcile against the source of truth: `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → real `status`/`error_code`. Read the configured URLs from `GET https://messaging.twilio.com/v1/Services/{ServiceSid}` → `status_callback` and `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json` → `status_callback`.
- **repair** — Make the handler return an empty `200 OK` immediately and process asynchronously; allowlist Twilio's egress IPs; then backfill missed state by polling `Messages.json` rather than trusting callbacks alone.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/11200 · https://www.twilio.com/docs/usage/monitor-alert

## link-shortening-cert-expiring

- **title** — Link-shortening domain certificate expires and links break
- **symptom** — Warning 30131 in the Debugger, then shortened links start failing TLS and messages error with 30120 or 30129.
- **mechanism** — A bring-your-own certificate on a link-shortening domain has a fixed expiry and is not auto-renewed unless the domain uses Twilio-managed certificates.
- **detect** — `GET https://messaging.twilio.com/v1/LinkShortening/Domains/{DomainSid}/Certificate` → `date_expires` within 30 days, or `cert_in_validation.status` not validated. Corroborate with `GET https://monitor.twilio.com/v1/Alerts` → `error_code in [30120, 30129, 30131]`.
- **repair** — `POST https://messaging.twilio.com/v1/LinkShortening/Domains/{DomainSid}/Certificate` with a fresh `TlsCert`, or switch the domain to Twilio-managed certificates in Console → Messaging → Link Shortening.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/messaging/features/link-shortening/onboarding-guide · https://www.twilio.com/docs/api/errors/30120

## whatsapp-content-template-rejected

- **title** — A WhatsApp content template is rejected and sends fail
- **symptom** — `error_code=63040` ("Template Rejected"); `63041` paused, `63042` disabled. Freeform sends outside the 24-hour window fail with `63016`.
- **mechanism** — Meta reviews every template. Malformed placeholders or policy-violating copy are rejected and the template stays unusable until resubmitted. Outside the 24-hour customer-service window only an approved template may be sent.
- **detect** — `GET https://content.twilio.com/v1/Content/{ContentSid}/ApprovalRequests` → `whatsapp.status == "rejected"` with `whatsapp.rejection_reason`. Or `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code in [63016, 63040, 63041, 63042]`.
- **repair** — Fix the body, then `POST https://content.twilio.com/v1/Content/{ContentSid}/ApprovalRequests/whatsapp` with `name` and `category`. Re-send only after status returns to `approved`; use an approved template for anything outside the 24-hour window.
- **category** — Messaging delivery
- **sources** — https://www.twilio.com/docs/api/errors/63040 · https://www.twilio.com/docs/whatsapp/tutorial/message-template-approvals-statuses · https://www.twilio.com/docs/api/errors/63016

---

# A2P 10DLC & compliance

## a2p-brand-registration-failed

- **title** — A2P Brand registration is FAILED, so no campaign can attach
- **symptom** — All US 10DLC sends return `30034` ("Message from an Unregistered Number"); the Console shows the Brand in red. Campaign creation is rejected because the brand never reached APPROVED.
- **mechanism** — `BrandRegistration.status` moves PENDING → IN_REVIEW → APPROVED/FAILED. FAILED means The Campaign Registry could not verify the submitted business identity. The `errors[]` array (which replaces the deprecated `failure_reason` / `brand_feedback`) carries the reason. No campaign, and therefore no number registration, is possible while the brand is FAILED.
- **detect** — `GET https://messaging.twilio.com/v1/a2p/BrandRegistrations` → for each item read `status` (`PENDING|IN_REVIEW|APPROVED|FAILED|SUSPENDED|DELETION_PENDING|DELETION_FAILED`) and `errors[]`. Flag `status == "FAILED"`. Also read `brand_type`, `customer_profile_bundle_sid`, `a2p_profile_bundle_sid`, `tcr_id` (null while unapproved).
- **repair** — Fix the underlying Business Profile, then `POST https://messaging.twilio.com/v1/a2p/BrandRegistrations/{BrandSid}` to resubmit. Three free resubmissions; a fourth returns 21724. If the profile data itself is wrong, correct the Customer Profile bundle first (Console → Trust Hub → Customer Profiles), then resubmit.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/messaging/api/brand-registration-resource · https://www.twilio.com/docs/api/errors/30034

## a2p-brand-tax-id-legal-name-mismatch

- **title** — Brand failed 30799: the EIN does not match the legal name
- **symptom** — `status == "FAILED"` with `errors[]` containing `30799` ("Brand Registration: Unable to verify registration details").
- **mechanism** — TCR cross-checks `business_registration_identifier` (EIN / Canadian BN) against public tax records and requires an exact match on legal company name and address. Most Standard/LVS brand failures are this mismatch — a DBA used instead of the legal name, an address differing from the IRS record, an EIN that is actually an SSN, or an unverifiable ticker for a public company. Government and nonprofit brands fail the same way when `company_type` or the 501(c) subsection code is wrong.
- **detect** — `GET https://messaging.twilio.com/v1/a2p/BrandRegistrations/{BrandSid}` → `errors[]` where `error_code == 30799`; each error object carries `code`, `description`, `fields`, `url`. Cross-read the linked profile with `GET https://trusthub.twilio.com/v1/CustomerProfiles/{customer_profile_bundle_sid}/EntityAssignments`.
- **repair** — Console → Trust Hub → Customer Profiles → edit the business End-User so legal name, address and `business_registration_identifier` match the IRS/CRA record exactly, then `POST /v1/a2p/BrandRegistrations/{BrandSid}` to resubmit.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/api/errors/30799 · https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/troubleshooting-a2p-brands/troubleshooting-and-rectifying-a2p-standardlvs-brands

## a2p-brand-stuck-pending-review

- **title** — Brand sat in PENDING/IN_REVIEW for weeks with no callback
- **symptom** — No error anywhere, but campaign creation keeps failing and 10DLC traffic still throws `30034`. `status` is `PENDING` or `IN_REVIEW` and `tcr_id` is null, days or weeks after `date_created`.
- **mechanism** — PENDING means TCR validation is incomplete (usually minutes, sometimes over 7 days). IN_REVIEW means manual third-party vetting is underway. Teams that wired only a `status_callback` and never poll never notice the brand parked here, and a missed webhook leaves them silently blocked.
- **detect** — `GET https://messaging.twilio.com/v1/a2p/BrandRegistrations` → flag items where `status` is `PENDING` or `IN_REVIEW` and `date_created` is older than 7 days. Confirm with `tcr_id == null` and `brand_score == null`.
- **repair** — No API action. IN_REVIEW requires no customer action. If PENDING exceeds 7 days, open a Twilio Support ticket quoting the `BN…` SID. Do not create a duplicate brand — duplicates on one EIN trigger 30898.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/messaging/api/brand-registration-resource · https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/troubleshooting-a2p-brands/troubleshooting-and-rectifying-a2p-standardlvs-brands

## a2p-brand-suspended

- **title** — A SUSPENDED brand silently suspends every campaign under it
- **symptom** — Previously working traffic starts returning `30033` ("Campaign Suspended"). Attempts to update the brand return `21731`; attempts to modify the campaign return `21729`.
- **mechanism** — Carrier or ecosystem review suspends the brand for policy violation — campaign-to-traffic mismatch, spam, phishing, controlled substances, excessive complaints. Suspension cascades, so every campaign attached to a suspended brand is suspended too and the campaign-level symptom hides a brand-level cause.
- **detect** — `GET https://messaging.twilio.com/v1/a2p/BrandRegistrations` → `status == "SUSPENDED"`. Then, per Messaging Service, `GET https://messaging.twilio.com/v1/Services/{MessagingServiceSid}/Compliance/Usa2p` → `campaign_status == "SUSPENDED"` with `brand_registration_sid` pointing at the suspended `BN…`.
- **repair** — No API repair. Resolve the brand suspension with Twilio Support first; campaigns stay suspended until the brand clears. Do not reroute the same traffic through a new brand or campaign — that risks account termination.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/api/errors/30033 · https://www.twilio.com/docs/messaging/api/brand-registration-resource

## a2p-brand-missing-secondary-vetting

- **title** — Approved brand has no trust score, so throughput is floored
- **symptom** — Brand is APPROVED but campaigns are rejected with "Brand not qualified to run Campaign for AT&T", or throughput is stuck at the lowest MPS tier and queues back up under load. `brand_score` is null.
- **mechanism** — Standard brands get an external secondary-vetting score of 0–100 from Aegis, and MPS toward AT&T/T-Mobile/Verizon scales with it. If `skip_automatic_sec_vet` was true at creation, or the vetting record failed, the brand approves but carries no score, and carriers treat it as low-trust. Sole Proprietor and Low-Volume Standard brands never get a score; their throughput is fixed by use case.
- **detect** — `GET https://messaging.twilio.com/v1/a2p/BrandRegistrations/{BrandSid}` → `status == "APPROVED"` AND `brand_score == null`; also read `brand_type`, `identity_status` (`SELF_DECLARED|UNVERIFIED|VERIFIED|VETTED_VERIFIED`) and `skip_automatic_sec_vet`. Then `GET https://messaging.twilio.com/v1/a2p/BrandRegistrations/{BrandSid}/Vettings` → `vetting_status` (`PENDING|SUCCESS|FAILED`), `vetting_class`, `vetting_provider`.
- **repair** — `POST https://messaging.twilio.com/v1/a2p/BrandRegistrations/{BrandSid}/Vettings` with `VettingProvider=aegis` (or `campaign-verify` plus `VettingId` for political brands). Console → Messaging → Regulatory Compliance → Brand → Request secondary vetting.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/messaging/api/brand-vetting-resource · https://support.twilio.com/hc/en-us/articles/1260803225669-Message-throughput-MPS-and-Trust-Scores-for-A2P-10DLC-in-the-US

## sole-prop-otp-never-accepted

- **title** — Sole Proprietor brand blocked: the SMS OTP expired unanswered
- **symptom** — The brand never reaches a usable state, `identity_status` stays below `VERIFIED`, and 10DLC sends keep returning `30034`. The end customer says they never got a text, or ignored it.
- **mechanism** — A Sole Proprietor brand triggers an SMS OTP to the registered mobile; the customer must reply within 24 hours or verification lapses. The mobile must be a real US/Canadian handset, not a CPaaS number, and can be reused at most three times across all TCR A2P brand registrations globally — including registrations made through other vendors.
- **detect** — `GET https://messaging.twilio.com/v1/a2p/BrandRegistrations` → filter `brand_type == "SOLE_PROPRIETOR"`, then flag rows where `identity_status != "VERIFIED"` and `date_created` is more than 24 hours old. `links.brand_registration_otps` on the same resource confirms the OTP subresource exists.
- **repair** — `POST https://messaging.twilio.com/v1/a2p/BrandRegistrations/{BrandSid}/SmsOtp` to re-trigger a fresh OTP, then have the customer reply within 24 hours. If the mobile has hit its three-registration cap, resubmit the profile with a different mobile number.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/onboarding-isv-api-sole-prop-new · https://www.twilio.com/docs/messaging/api/brand-registration-resource

## sole-prop-extra-numbers-unregistered

- **title** — Sole Prop campaign has extra numbers that never register
- **symptom** — One number in the sender pool delivers fine, the others return `30034` at random. Which number works looks arbitrary because the Messaging Service picks a sender per message.
- **mechanism** — A Sole Proprietor brand may have exactly one campaign, and that campaign exactly one 10DLC number. Adding more numbers to the pool does not error at add time — the extras simply sit at A2P status UNREGISTERED forever. The *intermittent* 30034 is the tell that distinguishes this from a number missing from the pool entirely, which fails consistently for one `from`.
- **detect** — `GET https://messaging.twilio.com/v1/Services/{MessagingServiceSid}/Compliance/Usa2p` → note `brand_registration_sid`. `GET https://messaging.twilio.com/v1/a2p/BrandRegistrations/{brand_registration_sid}` → `brand_type == "SOLE_PROPRIETOR"`. Then `GET https://messaging.twilio.com/v1/Services/{MessagingServiceSid}/PhoneNumbers` and flag a list length greater than one.
- **repair** — `DELETE https://messaging.twilio.com/v1/Services/{MessagingServiceSid}/PhoneNumbers/{PhoneNumberSid}` for every number except the intended sender. If more capacity is genuinely needed, register a Standard or Low-Volume Standard brand — Sole Proprietor cannot be widened.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/troubleshooting-a2p-brands/troubleshooting-a2p-phone-number-registration-issues · https://www.twilio.com/docs/api/errors/30034

## a2p-campaign-vetting-failed

- **title** — Campaign is FAILED and errors[] names the exact rejection
- **symptom** — `campaign_status == "FAILED"`; US traffic returns `30034`. `errors[]` carries a 308xx/309xx code — for example `30886` (description too vague), `30890` (help message missing brand name or support contact), `30892` (public URL shortener in samples), `30893` (samples do not match the stated use case), `30895` (direct lending not declared), `30898` (EIN used for too many brands), `30909` (message flow / call-to-action incomplete). `30883`/`30884`/`30885` (content violation, spam risk, fraud) are non-remediable.
- **mechanism** — TCR and carrier vetting review the campaign's `description`, `message_samples`, `message_flow`, `help_message`, and the boolean content attributes (`has_embedded_links`, `has_embedded_phone`, `subscriber_opt_in`, `age_gated`, `direct_lending`). Any mismatch between declared attributes and observable content fails the campaign. Developers frequently check only `campaign_status` and never read `errors[]`, so they resubmit the same content.
- **detect** — `GET https://messaging.twilio.com/v1/Services/{MessagingServiceSid}/Compliance/Usa2p` → `campaign_status` (`PENDING|IN_PROGRESS|VERIFIED|FAILED|SUSPENDED`). When FAILED, read `errors[]` — each object has `error_code`, `fields` (the campaign attribute that triggered it), `description`, `url`. Also read `campaign_id` and `us_app_to_person_usecase`.
- **repair** — Prefer editing in place: `POST https://messaging.twilio.com/v1/Services/{MessagingServiceSid}/Compliance/Usa2p/{QE…}` updating `Description`, `MessageFlow`, `MessageSamples`, `HelpMessage`, `HasEmbeddedLinks`, `DirectLending`. The vetting fee is charged once per campaign, so delete-and-recreate only if the use case itself was wrong.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/troubleshooting-a2p-brands/troubleshooting-and-rectifying-a2p-campaigns · https://www.twilio.com/docs/api/errors/30909

## a2p-campaign-stuck-in-progress

- **title** — Campaign parked at IN_PROGRESS while devs assume it is live
- **symptom** — Deploy goes out, US messages return `30034`, and `campaign_status` reads `IN_PROGRESS` or `PENDING` with `campaign_id == null`. Nothing is broken — it just is not approved yet.
- **mechanism** — After submission, TCR vetting runs asynchronously and `campaign_status` stays `IN_PROGRESS` until it resolves. Campaign review has run to three weeks during backlogs. Numbers in the sender pool cannot reach REGISTERED until the campaign is VERIFIED, so the launch is blocked with no error object to read.
- **detect** — `GET https://messaging.twilio.com/v1/Services/{MessagingServiceSid}/Compliance/Usa2p` → flag `campaign_status` in `{PENDING, IN_PROGRESS}` where `date_created` is older than your launch SLA. Corroborate with `campaign_id == null` and an empty `errors[]`.
- **repair** — No API action — wait. Gate the rollout on `campaign_status == "VERIFIED"` before enabling US sends, and fall back to a verified toll-free number or Twilio Verify in the interim. Escalate to Support only past about three weeks.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/messaging/api/usapptoperson-resource · https://www.twilio.com/docs/messaging/compliance/a2p-10dlc/troubleshooting-a2p-brands/troubleshooting-and-rectifying-a2p-campaigns

## a2p-campaign-suspended-30033

- **title** — Carrier suspends your 10DLC campaign for policy violation
- **symptom** — All messages on the campaign fail with `error_code=30033` ("US A2P 10DLC - Campaign Suspended"), often abruptly and account-wide.
- **mechanism** — Carrier or ecosystem review found campaign-to-traffic mismatch, spam, phishing, controlled substances, affiliate marketing, missing age gating, or excessive complaints — or the parent Brand was suspended.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → `error_code == 30033`. Confirm with `GET https://messaging.twilio.com/v1/Services/{ServiceSid}/Compliance/Usa2p` → `campaign_status` and `errors[]`, and `GET /v1/a2p/BrandRegistrations` → `status == "SUSPENDED"`.
- **repair** — No API fix. Read the suspension email, remediate the violating traffic, and reply to Twilio Support with evidence. Explicitly do not reroute the same traffic through another campaign — that escalates to account termination.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/api/errors/30033

## a2p-throughput-exceeded-30022

- **title** — Sends burst past the campaign's carrier-assigned throughput
- **symptom** — Intermittent `error_code=30022` ("US A2P 10DLC - Rate Limit Exceeded") during peaks; the same message succeeds when retried later.
- **mechanism** — Combined MPS across all numbers in the campaign exceeded the throughput the carrier assigned from your Brand Trust Score, or too many messages hit one recipient in quick succession.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → bucket `error_code == 30022` by minute; compare against `GET https://messaging.twilio.com/v1/Services/{ServiceSid}/Compliance/Usa2p` → `rate_limits` (per-carrier MPS and daily caps).
- **repair** — Throttle the producer to the `rate_limits` MPS value, queue bursts client-side, and either add senders to the pool or raise the Trust Score via Trust Hub secondary vetting.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/api/errors/30022 · https://www.twilio.com/docs/messaging/api/usapptoperson-resource

## tmobile-brand-daily-segment-cap

- **title** — T-Mobile daily brand cap silently drops the day's later sends
- **symptom** — Deliveries succeed all morning, then T-Mobile-destined messages start failing (`30023` "Daily Message Cap Reached", or generic undelivered) from a consistent point in the day, resetting at midnight US Pacific. Verizon and AT&T traffic is unaffected.
- **mechanism** — T-Mobile enforces a daily segment cap at the *brand* level, not per campaign or per number, shared across every platform registered under the same brand. Sole Proprietor brands are capped at 1,000 segments/day; Standard brands by trust tier, with Russell 3000 companies defaulting to 200,000 segments/day. Removing that ceiling requires T-Mobile's Special Business Review. Because the cap is external to Twilio, nothing errors at submit time.
- **detect** — `GET https://messaging.twilio.com/v1/a2p/BrandRegistrations/{BrandSid}` → read `brand_type`, `brand_score`, `russell_3000` to derive the tier. Read the per-carrier ceiling at `GET https://messaging.twilio.com/v1/Services/{MessagingServiceSid}/Compliance/Usa2p` → `rate_limits`. Then measure burn with `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent={today}` and sum `num_segments` against that ceiling.
- **repair** — Cannot be raised by API. Upgrade the brand (Sole Proprietor → Standard plus secondary vetting), or request a T-Mobile Special Business Review through Support. Operationally, throttle to stay under `rate_limits` and spread the day's volume.
- **category** — A2P 10DLC & compliance
- **sources** — https://support.twilio.com/hc/en-us/articles/1260804800549-T-Mobile-daily-message-limits-for-long-code-messaging-with-A2P-10DLC · https://www.twilio.com/docs/api/errors/30023

## messaging-service-not-a2p-registered

- **title** — Messaging Service has no A2P campaign attached at all
- **symptom** — Every US send through this Messaging Service returns `30034`, and there is no campaign object to inspect — `GET …/Compliance/Usa2p` returns an empty list. Common when a second service is created for staging or a new tenant and nobody registers it.
- **mechanism** — A2P registration is per Messaging Service, not per account. The Service resource exposes a single boolean, `us_app_to_person_registered`, which is the fastest account-wide way to find unregistered services. An unregistered service accepts numbers and API calls happily; only the outbound message fails.
- **detect** — `GET https://messaging.twilio.com/v1/Services` → flag every item where `us_app_to_person_registered == false`. For each flagged `MG…`, confirm with `GET https://messaging.twilio.com/v1/Services/{MessagingServiceSid}/Compliance/Usa2p` returning an empty array. Also read `usecase`.
- **repair** — `POST https://messaging.twilio.com/v1/Services/{MessagingServiceSid}/Compliance/Usa2p` with `BrandRegistrationSid`, `Description`, `MessageFlow`, `MessageSamples`, `UsAppToPersonUsecase`, `HasEmbeddedLinks`, `HasEmbeddedPhone`. Console → Messaging → Services → A2P 10DLC → Register.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/messaging/api/service-resource · https://www.twilio.com/docs/messaging/api/usapptoperson-resource

## number-missing-from-campaign-sender-pool

- **title** — 10DLC number sends direct, bypassing the approved campaign
- **symptom** — `30034` on a number that "is registered" — the brand is APPROVED and the campaign VERIFIED, but this particular +1 long code is absent from the registered service's sender pool. Typically the code sets `From=+1…` directly instead of `MessagingServiceSid=MG…`.
- **mechanism** — A2P approval attaches to numbers via the Messaging Service sender pool; carriers register numbers individually after campaign approval. A number outside the pool is UNREGISTERED regardless of brand or campaign state, and sending with an explicit `From` bypasses the service entirely. Numbers added in the last two weeks may also still be PENDING_REGISTRATION.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json` → collect every `phone_number` where `capabilities.sms` is true, starting `+1` and not toll-free. `GET https://messaging.twilio.com/v1/Services/{MessagingServiceSid}/PhoneNumbers` for each registered service → collect pool numbers. Set-difference the two lists, and cross-check failures via `Messages.json` → `error_code == 30034` grouped by `from`.
- **repair** — `POST https://messaging.twilio.com/v1/Services/{MessagingServiceSid}/PhoneNumbers` with `PhoneNumberSid=PN…`, then send using `MessagingServiceSid=MG…` rather than a bare `From`.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/messaging/api/phonenumber-resource · https://www.twilio.com/docs/api/errors/30034

## sender-pending-carrier-provisioning

- **title** — New sender not yet provisioned on the carrier network
- **symptom** — A number that should work returns `error_code=30024` ("Numeric Sender ID Not Provisioned on Carrier") or `30035` ("Number Pending Registration") for up to 24 hours.
- **mechanism** — The number sits in `PENDING_REGISTRATION`/`PENDING_DEREGISTRATION` after being added to, or moved between, Messaging Services; carrier routing tables have not caught up. Repeatedly removing and re-adding restarts the clock.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?From=%2B1XXXXXXXXXX&DateSent>=…` → `error_code in [30024, 30035]`. Confirm pool membership with `GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers`.
- **repair** — Wait up to 24 hours without touching the assignment; route the affected traffic through an already-registered sender meanwhile. If still not registered after 24 hours, open Support with the PN SID.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/api/errors/30035 · https://www.twilio.com/docs/api/errors/30024

## tollfree-number-not-verified

- **title** — Toll-free number is unverified, so all US/CA SMS is blocked
- **symptom** — 100% of messages from a +1 8XX number to US/CA mobiles fail with `30032` ("Toll-Free Number Has Not Been Verified"). Fees are still charged for the blocked attempts.
- **mechanism** — Since 31 January 2024, toll-free traffic in Restricted or Pending state is fully blocked, not throttled. Teams buy a toll-free number as the easy alternative to 10DLC, never file a verification, and discover at launch that toll-free now has its own mandatory verification with no unverified allowance.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/TollFree.json` → collect each `sid`/`phone_number`. `GET https://messaging.twilio.com/v1/Tollfree/Verifications` → build a set of `tollfree_phone_number_sid`. Flag any toll-free number with no verification record at all, plus any record whose `status` is `PENDING_REVIEW` or `IN_REVIEW` — both are blocked states.
- **repair** — `POST https://messaging.twilio.com/v1/Tollfree/Verifications` with `BusinessName`, `BusinessWebsite`, `NotificationEmail`, `UseCaseCategories`, `UseCaseSummary`, `ProductionMessageSample`, `OptInType`, `OptInImageUrls`, `MessageVolume`, `TollfreePhoneNumberSid`.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/api/errors/30032 · https://www.twilio.com/docs/messaging/api/tollfree-verification-resource

## tollfree-verification-rejected

- **title** — Toll-free verification is TWILIO_REJECTED with a coded reason
- **symptom** — `30032` persists after submitting. `status == "TWILIO_REJECTED"`, `rejection_reason` holds prose and `error_code`/`rejection_reasons[]` a 304xx code — for example `30469` (illegal substances or articles: cannabis, CBD, kratom, vape, fireworks). Developers resubmit identical data and are rejected again.
- **mechanism** — Twilio reviews business identity, use-case summary, sample content, the public website, the opt-in flow, and the linked privacy policy. Rejections split into fixable (unclear use case, missing opt-in evidence) and structural (the business category is prohibited on US/CA SMS routes regardless of local legality). Resubmitting a structurally rejected use case burns the edit window without effect.
- **detect** — `GET https://messaging.twilio.com/v1/Tollfree/Verifications?Status=TWILIO_REJECTED` → per record read `rejection_reason`, `rejection_reasons[]`, `error_code`, `edit_allowed`, `edit_expiration`, `use_case_categories`, `use_case_summary`, `opt_in_type`, `business_website`.
- **repair** — If `edit_allowed == true` and `edit_expiration` is in the future, `POST https://messaging.twilio.com/v1/Tollfree/Verifications/{Sid}` correcting the named fields. If `edit_allowed == false`, file a fresh `POST /v1/Tollfree/Verifications` — or, for a prohibited category, move the use case off SMS.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/messaging/api/tollfree-verification-resource · https://www.twilio.com/docs/api/errors/30469

## tollfree-edit-window-expiring

- **title** — A rejected toll-free record's 7-day edit window is about to lapse
- **symptom** — Nothing fails yet, but a rejected verification carries `edit_allowed == true` and an `edit_expiration` only days away. After it passes, the cheap in-place correction is gone and a full resubmission — back of the review queue — is the only path.
- **mechanism** — Twilio grants a limited resubmission window on rejected toll-free verifications. The window is exposed only on the resource; there is no console nag, and the status stays `TWILIO_REJECTED` either way, so it expires unnoticed while the fix sits in someone's queue.
- **detect** — `GET https://messaging.twilio.com/v1/Tollfree/Verifications?Status=TWILIO_REJECTED` → flag any item where `edit_allowed == true` and `edit_expiration` is within your alerting horizon (say under 72 hours).
- **repair** — `POST https://messaging.twilio.com/v1/Tollfree/Verifications/{Sid}` with the corrected fields before `edit_expiration`. Console → Phone Numbers → Manage → Active numbers → Regulatory Information → Edit and resubmit.
- **category** — A2P 10DLC & compliance
- **sources** — https://www.twilio.com/docs/messaging/api/tollfree-verification-resource · https://www.twilio.com/docs/api/errors/30032

---

# Phone numbers & Messaging Services

## phone-number-missing-fallback-url

- **title** — Phone number has no fallback URL, so an 11200 drops the call
- **symptom** — An 11200/11205 on the primary handler means the call or message is simply lost. `voice_fallback_url` and `sms_fallback_url` are empty on the number.
- **mechanism** — Twilio calls the fallback URL only when the primary webhook errors. With none configured, a single deploy blip, timeout, or 500 becomes a dropped customer interaction with no recovery path — the fallback is the one mitigation that works without changing the app.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000` → for each number, flag when `voice_url` is set but `voice_fallback_url` is empty (same for `sms_url`/`sms_fallback_url`). Where `voice_application_sid` is set instead, check `GET /2010-04-01/Accounts/{AccountSid}/Applications/{AppSid}.json` → `voice_fallback_url`.
- **repair** — `POST /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json` with `VoiceFallbackUrl=https://…/fallback&VoiceFallbackMethod=POST`. Console → Phone Numbers → Manage → Active numbers → "Primary handler fails".
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource · https://www.twilio.com/docs/api/errors/11200

## phone-number-insecure-or-unreachable-webhook-url

- **title** — Number webhook uses http://, localhost, or a tunnel URL
- **symptom** — Either signed webhook payloads travel in cleartext, or the number works in dev and dies in production with 11205/11210/11100.
- **mechanism** — Three related misconfigurations living in the same field. `http://` sends the body and `X-Twilio-Signature` unencrypted. `localhost`/RFC1918 addresses are unreachable from Twilio. An `ngrok.io` / `*.trycloudflare.com` / `*.loca.lt` URL is a dev tunnel that expires — it works until the laptop closes. All three survive into production because number config is edited by hand and never audited.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000` → for each of `voice_url`, `sms_url`, `status_callback`, `voice_fallback_url`, `sms_fallback_url`: flag scheme `http:`, hosts matching `localhost|127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.`, and hosts matching `ngrok|trycloudflare|loca\.lt|serveo|localtunnel`. Repeat over `GET /2010-04-01/Accounts/{AccountSid}/Applications.json`.
- **repair** — `POST /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json` with `VoiceUrl=https://{production-host}/voice&SmsUrl=https://{production-host}/sms`.
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource · https://www.twilio.com/docs/api/errors/11100 · https://www.twilio.com/docs/usage/security

## phone-number-still-on-demo-twiml

- **title** — Number still points at Twilio's demo TwiML endpoint
- **symptom** — Callers hear the Twilio demo greeting or a stock TwiML Bin instead of the application. No error code is raised — the webhook returns 200.
- **mechanism** — Newly purchased numbers are provisioned with `voice_url` set to `https://demo.twilio.com/docs/voice.xml`. Because that URL is healthy and returns valid TwiML, nothing appears in Alerts, every Call shows `completed`, and the misconfiguration is invisible to error-based monitoring. It is only caught when someone actually dials the number.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000` → flag any number whose `voice_url` or `sms_url` matches `demo\.twilio\.com` or `handler\.twilio\.com/twiml/` (an unedited TwiML Bin), or where all of `voice_url`, `sms_url` and `voice_application_sid` are empty. Cross-check the number sees traffic with `GET /2010-04-01/Accounts/{AccountSid}/Calls.json?To={E164}&PageSize=1`.
- **repair** — `POST /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json` with `VoiceUrl=https://…/voice&VoiceMethod=POST`.
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource

## number-conflicting-url-and-application-sid

- **title** — Number has both a webhook URL and an Application SID set
- **symptom** — Edits to the number's `voice_url` have no effect; traffic keeps hitting an old endpoint from a TwiML App nobody remembers creating.
- **mechanism** — When `voice_application_sid` is populated it takes precedence and `voice_url` is ignored entirely. The stale field remains visible in the API and Console, so developers "fix" the wrong field repeatedly. The same precedence applies to `sms_application_sid` over `sms_url`.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000` → flag numbers where `voice_application_sid` is non-empty AND `voice_url` is also non-empty and differs. Resolve the effective endpoint with `GET /2010-04-01/Accounts/{AccountSid}/Applications/{AppSid}.json` → `voice_url`, `voice_fallback_url`, `status_callback`. Also flag apps whose `voice_url` is empty — those route calls nowhere.
- **repair** — Either update the app (`POST /2010-04-01/Accounts/{AccountSid}/Applications/{AppSid}.json` with `VoiceUrl=…`) or detach it (`POST …/IncomingPhoneNumbers/{PNSid}.json` with an empty `VoiceApplicationSid`) so `voice_url` takes effect.
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/usage/api/applications · https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource

## number-not-in-messaging-service

- **title** — SMS-capable number sits outside any Messaging Service
- **symptom** — No error code — just poorer deliverability, no sender-pool failover, and A2P 10DLC registration that does not apply to the number.
- **mechanism** — A2P registration, sticky sender, geomatch, and long-code fallback all operate at the Messaging Service level. A number configured with a bare `sms_url` and no service association bypasses all of it. Traffic still sends, so nothing errors, but it is unregistered traffic subject to carrier filtering.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PageSize=1000` → collect every `sid` where `capabilities.sms` is true. Then `GET https://messaging.twilio.com/v1/Services?PageSize=1000` and per service `GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers?PageSize=1000` → collect associated SIDs. The set difference is the unattached SMS-capable numbers.
- **repair** — `POST https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers` with `PhoneNumberSid=PN…`. Console → Messaging → Services → Sender Pool → Add Senders. The default cap is 400 numbers per service.
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/messaging/api/phonenumber-resource · https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource

## messaging-service-empty-sender-pool

- **title** — Messaging Service sender pool is empty, so every send 21704s
- **symptom** — `21704` ("The Messaging Service contains no phone numbers") on every `Messages.create` that passes `MessagingServiceSid`. The Console shows the service exists and looks configured.
- **mechanism** — The service was created — often by IaC or a setup script — but no sender was ever added to the pool, or the last sender was removed or released. Twilio has no `From` to select and rejects before any carrier hop.
- **detect** — `GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers` → flag an empty `phone_numbers[]`. Also `GET https://messaging.twilio.com/v1/Services/{ServiceSid}/AlphaSenders` → empty `alpha_senders[]`. Both empty guarantees 21704.
- **repair** — `POST https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers` with `PhoneNumberSid=PN…` for each owned number.
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/api/errors/21704 · https://www.twilio.com/docs/messaging/api/phonenumber-resource

## no-sender-matching-destination

- **title** — Pool has senders but none can reach the To (21703)
- **symptom** — `21703` ("The Messaging Service does not have a phone number available to send a message") — works for some destinations, fails for others, typically US/CA or all MMS.
- **mechanism** — Sender selection found no pool member supporting the destination country *and* message type: no US/CA long code or short code for a US destination, or no MMS-capable US/CA long code when `MediaUrl` is present. Recently added senders still pending registration behave the same way.
- **detect** — `GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers` → per entry read `country_code` and `capabilities[]` (`SMS`, `MMS`, `voice`). Flag when no entry matches the destination's `country_code` from `GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}`, or when `MediaUrl` traffic exists but no entry lists `MMS`. Cross-check ownership with `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json` → `capabilities.mms`.
- **repair** — `POST https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers` with the `PhoneNumberSid` of a number in the destination country with the needed capability. For US MMS, add an MMS-capable US long code.
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/api/errors/21703 · https://www.twilio.com/docs/messaging/api/phonenumber-resource

## from-number-not-sms-capable

- **title** — The From number cannot do SMS, so every send is 21606
- **symptom** — `21606` ("'From' number is not a valid message-capable Twilio number for this account"). Voice on the same number works fine.
- **mechanism** — The number is voice-only (common for toll-free bought for IVR and for many non-US numbers), belongs to a different subaccount, is still provisioning after a port or host, or is passed in national rather than E.164 format. Using a production number with test credentials gives the same code.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json?PhoneNumber={E164}` → `capabilities.sms`, `capabilities.mms`, `capabilities.voice`, and `account_sid`. Flag `capabilities.sms == false`, an empty result set (number not on this account), or an `account_sid` that differs from the SID you authenticate with.
- **repair** — Buy an SMS-capable replacement: `GET /2010-04-01/Accounts/{AccountSid}/AvailablePhoneNumbers/US/Local.json?SmsEnabled=true`, then `POST …/IncomingPhoneNumbers.json`. Always send `From` in E.164.
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/api/errors/21606 · https://www.twilio.com/docs/phone-numbers/api/incomingphonenumber-resource

## messaging-service-no-status-callback

- **title** — No status_callback, so delivery failures never reach your app
- **symptom** — Your database shows every message as "sent"; users report nothing arrived. `21610` (opt-out), `30034`, `30007` exist only in Twilio's logs and are never surfaced. Silent list rot.
- **mechanism** — `Messages.create` returns `queued`/`accepted` — a synchronous success that says nothing about carrier delivery. Terminal status plus `error_code` arrives only via the status-callback webhook or Event Streams, and neither is configured by default.
- **detect** — `GET https://messaging.twilio.com/v1/Services` → per service flag `status_callback == null` and `fallback_url == null`. Then `GET https://events.twilio.com/v1/Sinks` → flag an empty list, or any sink whose `status` is not `active`; pair with `GET https://events.twilio.com/v1/Subscriptions` to confirm a subscription to `com.twilio.messaging.message.*` exists. No callback and no active sink means zero delivery observability.
- **repair** — `POST https://messaging.twilio.com/v1/Services/{ServiceSid}` with `StatusCallback=https://…/twilio/status` and `FallbackUrl=https://…/twilio/fallback`; validate `X-Twilio-Signature` on receipt, persist `MessageStatus` and `ErrorCode`, and suppress recipients on 21610.
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/messaging/api/service-resource · https://www.twilio.com/docs/events/event-streams/sink-resource

## inbound-webhook-black-hole

- **title** — Inbound webhook deferred to a number that has no sms_url
- **symptom** — Inbound SMS vanishes. No 4xx, no webhook hit, no error in your logs. Users' STOP replies never reach the app.
- **mechanism** — When `use_inbound_webhook_on_number` is true (Twilio's "defer to sender's webhook" default), the *number's* `sms_url` overrides the Messaging Service's `inbound_request_url`. Teams configure the service-level URL, assume it applies, and every pool number with a blank `sms_url` silently drops inbound traffic. The inverse also bites: `use_inbound_webhook_on_number == false` with `inbound_request_url == null` black-holes the whole pool.
- **detect** — `GET https://messaging.twilio.com/v1/Services/{ServiceSid}` → read `use_inbound_webhook_on_number`, `inbound_request_url`, `fallback_url`. If true, then for every entry in `GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers` look the number up in `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json` and flag empty `sms_url` (and empty `sms_fallback_url`).
- **repair** — Either centralise — `POST https://messaging.twilio.com/v1/Services/{ServiceSid}` with `UseInboundWebhookOnNumber=false&InboundRequestUrl=https://…/twilio/inbound` — or per number, `POST /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json` with `SmsUrl=…&SmsMethod=POST&SmsFallbackUrl=…`.
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/messaging/api/service-resource · https://www.twilio.com/en-us/changelog/messaging-services-defer-to-sender-s-webhook-option-now-availabl

## sms-reply-loop-rate-limit-14107

- **title** — Auto-reply loop trips the SMS rate limit (14107)
- **symptom** — `14107` "SMS send rate limit exceeded"; a conversation between two numbers floods, then messages stop.
- **mechanism** — Twilio caps outbound replies at 30 messages between the same two numbers in 30 seconds as a guard against messaging loops. TwiML that auto-replies to every inbound message, a `<Redirect>` cycle, or two Twilio numbers messaging each other will hit it. The limit is the symptom; the loop is the bug.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&StartDate=…` → `error_code == 14107`. Confirm the loop with `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?To={E164}&From={E164}&DateSent>=…&PageSize=1000` — a dense burst of identical bodies within seconds is the signature.
- **repair** — Add loop detection to the inbound handler (dedupe on body plus peer within a window) and audit every `<Message>` `action` URL and `<Redirect>` target for cycles.
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/api/errors/14107

## messaging-service-validity-period-too-long

- **title** — A 36000-second validity period keeps dead messages queued 10h
- **symptom** — Time-sensitive messages arrive hours late, or fail with 30001 long after the moment passed. Users complain the OTP arrived after they gave up.
- **mechanism** — `validity_period` defaults to 36,000 seconds. Anything still queued at the deadline fails, so an OTP can sit behind a backlog for ten hours and then deliver — worse than failing fast, because the user has already re-requested three codes.
- **detect** — `GET https://messaging.twilio.com/v1/Services/{ServiceSid}` → `validity_period == 36000` on a service carrying OTP or alert traffic. Corroborate with `GET /2010-04-01/Accounts/{AccountSid}/Messages.json` where `date_sent - date_created` exceeds a few minutes.
- **repair** — `POST https://messaging.twilio.com/v1/Services/{ServiceSid}` with `ValidityPeriod=300` for time-critical traffic; keep 36000 only for marketing.
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/messaging/api/service-resource · https://www.twilio.com/docs/messaging/guides/scaling-queueing-latency

## multiple-tollfree-in-one-pool

- **title** — Two toll-free numbers in one sender pool get the pool blocked
- **symptom** — Toll-free traffic starts failing with 30032 across the whole service, including numbers that were previously verified.
- **mechanism** — Carriers treat multiple toll-free senders in a single Messaging Service as snowshoeing — spreading volume across senders to evade filtering — and block the numbers. Twilio's own guidance is one toll-free number per service.
- **detect** — `GET https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers` → more than one entry whose `phone_number` matches a US toll-free prefix (`+1800`, `833`, `844`, `855`, `866`, `877`, `888`).
- **repair** — `DELETE https://messaging.twilio.com/v1/Services/{ServiceSid}/PhoneNumbers/{PNSid}` for the extras, and give each toll-free number its own Messaging Service.
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/messaging/services · https://www.twilio.com/docs/messaging/tutorials/send-messages-with-messaging-services

## idle-phone-numbers-billed

- **title** — Phone numbers with no traffic still bill every month
- **symptom** — The monthly invoice grows while message and call volume is flat. Nobody can say what half the numbers are for.
- **mechanism** — Every number on the account carries a recurring rental charge whether or not it is used, and numbers bought for one-off tests are rarely released. Idle numbers are also A2P-registration surface and a security liability.
- **detect** — For each `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json` entry, query `GET …/Messages.json?From={number}&DateSent>={90d ago}&PageSize=1` and `GET …/Calls.json?From={number}&StartTime>={90d ago}&PageSize=1`; both empty means idle. Corroborate spend with `GET /2010-04-01/Accounts/{AccountSid}/Usage/Records/Monthly.json?Category=phonenumbers`.
- **repair** — `DELETE /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json`. Release is free and recoverable for 10 days.
- **category** — Phone numbers & Messaging Services
- **sources** — https://www.twilio.com/docs/usage/manage-unused-resources · https://www.twilio.com/docs/phone-numbers/best-practices

---

# Webhooks & callbacks

## webhook-http-retrieval-failure-11200

- **title** — Webhook URL returns non-2xx, so Twilio errors with 11200
- **symptom** — The Debugger fills with `11200 HTTP retrieval failure`; calls and messages silently drop or hit the fallback. The alert's `alert_text` carries the failing URL and status.
- **mechanism** — Twilio treats anything outside 2xx as a retrieval failure — a 404 from a moved route, 401/403 from auth middleware, or a 500 from an app crash all surface identically. It also fires when the response exceeds Twilio's 15-second HTTP window or the URL resolves to a private IP.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&StartDate={ISO8601}` → count alerts where `error_code == 11200`; read `request_url`, `request_method`, `date_generated`. For the response Twilio actually received, fetch one by SID: `GET https://monitor.twilio.com/v1/Alerts/{AlertSid}` → `response_body`, `response_headers` (populated only on the single-resource fetch).
- **repair** — Make the handler return 2xx within 15 seconds — acknowledge immediately, process asynchronously. Then set a fallback: `POST /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json` with `VoiceFallbackUrl=https://…/fallback`.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/11200 · https://www.twilio.com/docs/usage/monitor-alert

## webhook-connection-timeout-11205

- **title** — Twilio cannot open a TCP connection to your webhook (11205)
- **symptom** — `11205 HTTP connection failure` alerts, and your own access log shows nothing at all for the request.
- **mechanism** — Twilio allows 10 seconds to establish the TCP connection and 15 seconds total for the HTTP response. A firewall dropping Twilio's egress ranges, a dead host, or a URL pointing at a private address never completes the handshake — so unlike 11200 the request never reaches your app.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&StartDate={ISO8601}` → filter `error_code == 11205`; group by `request_url` to find the unreachable host.
- **repair** — Allowlist Twilio's egress IP ranges at the firewall or WAF and confirm the host answers publicly. Verify the configured URL with `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json` → `voice_url`/`sms_url`.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/11205 · https://www.twilio.com/docs/usage/monitor-alert

## webhook-http-protocol-violation-11206

- **title** — Webhook response violates HTTP, so Twilio errors with 11206
- **symptom** — `11206 HTTP protocol violation` in Alerts even though your server logs a 200.
- **mechanism** — Twilio's HTTP client cannot parse what came back. Classic causes: plain HTTP sent to an HTTPS-only port, a truncated or malformed response, cookies with empty names, or `Set-Cookie` values containing raw control characters.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 11206`; then `GET https://monitor.twilio.com/v1/Alerts/{AlertSid}` → inspect `response_headers` for malformed `Set-Cookie` values.
- **repair** — Strip control characters from cookie values and drop nameless cookies; ensure the scheme in the configured URL matches the listener's port.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/11206 · https://www.twilio.com/docs/usage/monitor-alert

## webhook-dns-resolution-failure-11210

- **title** — Webhook hostname has no public DNS record (11210)
- **symptom** — `11210 HTTP bad host name`. The URL works from the developer's laptop but never from Twilio.
- **mechanism** — The host is resolvable only locally — an `/etc/hosts` entry, a split-horizon internal zone, or a domain whose DNS was never published or has expired. Twilio resolves from the public internet and gets NXDOMAIN.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 11210`; extract the hostname from `request_url`.
- **repair** — Publish a public A/AAAA/CNAME record for that hostname, then repoint: `POST /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json` with `VoiceUrl=https://{public-host}/voice`.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/11210

## webhook-tls-handshake-failure-11220

- **title** — TLS handshake with your webhook fails, raising error 11220
- **symptom** — `11220 SSL/TLS Handshake Error`. Browsers load the URL fine; Twilio cannot.
- **mechanism** — The connection resets during TLS negotiation because no cipher suite is shared. Most commonly an endpoint still pinned to TLS 1.0/1.1, or a hardened server offering only cipher suites Twilio's client does not present. Twilio has been progressively retiring TLS 1.0/1.1 across its interfaces.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 11220`; `request_url` gives the host to test.
- **repair** — Enable TLS 1.2+ with a modern cipher suite list on the terminating server or load balancer. No Twilio-side change is possible; the fix is entirely on the endpoint.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/11220

## webhook-tls-certificate-expired-11236

- **title** — Webhook TLS certificate has expired, raising error 11236
- **symptom** — `11236 Certificate Invalid - Certificate Expired`. Every webhook to that host fails at once, at a sharp timestamp boundary.
- **mechanism** — Twilio validates the certificate chain on every HTTPS webhook. An expired leaf — usually renewal automation that stopped, or a cert on a failover node nobody renewed — fails validation before any request is sent.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&StartDate={ISO8601}` → `error_code == 11236`; `date_generated` of the first alert marks the expiry moment and `request_url` names the host.
- **repair** — Renew the certificate and reload the server, then re-test the same URL with the Debugger's Request Inspector.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/11236

## webhook-tls-chain-untrusted-11237

- **title** — Webhook cert chain is incomplete or self-signed (11237)
- **symptom** — `11237 Certificate Invalid - Could not find path to certificate`. Related: `11235 Certificate Invalid - Domain Mismatch` when the CN/SAN does not cover the host.
- **mechanism** — Twilio trusts only Mozilla-approved CAs and does not chase missing intermediates. A server presenting only the leaf — or a self-signed certificate — leaves Twilio with no path to a trusted root.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code in (11235, 11237)`; read `request_url` and `alert_text`.
- **repair** — Serve the full chain (leaf plus intermediates concatenated) in the server's certificate file. For 11235, reissue with a SAN matching the webhook host exactly.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/11237 · https://www.twilio.com/docs/api/errors/11235

## twiml-response-body-too-large-11750

- **title** — TwiML response exceeds the 64 kB limit (11750)
- **symptom** — `11750 TwiML response body too large`; the call drops right after the webhook.
- **mechanism** — Twilio caps TwiML at 64 kB. Two causes dominate: a genuinely huge document (long `<Say>` loops, hundreds of `<Number>` elements), or — far more often — the app threw and returned a framework HTML stack trace instead of TwiML, which blows past the limit.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 11750`; then `GET https://monitor.twilio.com/v1/Alerts/{AlertSid}` → `response_body` shows whether it is real TwiML or an HTML error page.
- **repair** — Return an empty `<Response/>` for status callbacks and split long flows across `<Redirect>` hops. Disable HTML debug pages in production so failures return a small 500 instead of a stack trace.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/11750

## twiml-document-parse-failure-12100

- **title** — TwiML is not well-formed XML, so Twilio errors with 12100
- **symptom** — `12100 Document parse failure`; the caller hears an application-error message and the call ends.
- **mechanism** — Invalid XML. Nearly always whitespace or a blank line emitted before the XML declaration (a stray newline after a PHP close tag, or a template header), a missing `<Response>` root, unclosed tags, or unescaped `&`/`<` in dynamic `<Say>` text.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 12100`; then `GET https://monitor.twilio.com/v1/Alerts/{AlertSid}` → `response_body` contains the exact bytes Twilio received, and `alert_text` gives the offending line and column.
- **repair** — Emit the XML declaration as the first byte with no preceding output, and XML-escape all interpolated text.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/12100

## twiml-schema-validation-warning-12200

- **title** — TwiML verb is misspelled or wrongly cased (12200)
- **symptom** — `12200 Schema validation warning` — "The provided XML does not conform to the Twilio Markup XML schema." The document parses, but the verb is skipped silently.
- **mechanism** — TwiML is case-sensitive and closed-vocabulary. `<say>` instead of `<Say>`, `numdigits` instead of `numDigits`, or a verb nested where the schema disallows it all fail validation. Because it is logged as a warning rather than an error, the call continues and simply does nothing — which is why it goes unnoticed.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=warning&StartDate={ISO8601}` → `error_code == 12200`. Note the `LogLevel=warning` filter — these never appear in an error-only query.
- **repair** — Fix the verb and attribute casing to match the TwiML reference; `alert_text` gives the line and column.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/12200 · https://www.twilio.com/docs/usage/monitor-alert

## webhook-invalid-content-type-12300

- **title** — Webhook returns the wrong Content-Type for TwiML (12300)
- **symptom** — `12300 Invalid Content-Type`. Requests with no `Content-Type` at all show as 502 Bad Gateway in the Debugger.
- **mechanism** — Twilio dispatches on the response's `Content-Type` header. A handler returning valid TwiML as `text/html` or `application/json` — or a serverless function that omits the header — is rejected before the body is parsed. The same error appears when `<Play>` points at a URL serving HTML instead of audio.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 12300`; then `GET https://monitor.twilio.com/v1/Alerts/{AlertSid}` → `response_headers` shows the Content-Type actually sent.
- **repair** — Set `Content-Type: text/xml` (or `application/xml`) on every TwiML response, and serve `<Play>` targets as `audio/mpeg` or `audio/wav`.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/12300

## webhook-signature-validation-403-behind-proxy

- **title** — Signature check rejects Twilio with 403 behind a proxy
- **symptom** — A burst of 11200 alerts whose `response_body` is a 403 or "Invalid signature" page. Works locally, fails the moment it is deployed behind a load balancer or CDN.
- **mechanism** — `X-Twilio-Signature` is HMAC-SHA1 over the *full* URL Twilio called — scheme, host, port, query string — plus sorted POST params. A TLS-terminating proxy hands the app `http://` and often an internal hostname, so the app reconstructs a different URL, computes a different HMAC, and rejects a legitimate request. The same failure occurs when the app validates against `localhost` instead of the public tunnel URL Twilio signed.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → collect `error_code == 11200` alert SIDs, then `GET https://monitor.twilio.com/v1/Alerts/{AlertSid}` → a `response_body` containing 403 or "signature" text distinguishes this from an ordinary 5xx. The `request_url` field is the exact string that must be fed to the validator.
- **repair** — Reconstruct the URL from `X-Forwarded-Proto` / `X-Forwarded-Host`, or hardcode the public base URL, before calling `RequestValidator.validate()`. Confirm the canonical string against the alert's `request_url`.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/usage/security · https://github.com/twilio/twilio-node/issues/650

## studio-flow-draft-not-published

- **title** — Studio Flow is still in draft, so live traffic runs old logic
- **symptom** — Callers and texters get the previous behaviour; the Console shows edits that never take effect.
- **mechanism** — Studio keeps a published revision and a draft. Edits raise `revision`, but until Publish the live executions keep the last published definition. Only phone numbers listed under TEST USERS see the draft.
- **detect** — `GET https://studio.twilio.com/v2/Flows` → any flow with `status == "draft"`; compare `revision` against the revision referenced by live executions in `GET https://studio.twilio.com/v2/Flows/{FlowSid}/Executions`.
- **repair** — `POST https://studio.twilio.com/v2/Flows/{FlowSid}` with `Status=published`, or Console → Studio → open the Flow → Publish.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/studio/rest-api/v2/flow · https://support.twilio.com/hc/en-us/articles/360007772633-Testing-Twilio-Studio-Flows-in-Draft-Status

## studio-flow-invalid-definition

- **title** — Studio Flow definition is invalid and widgets never run
- **symptom** — Executions end immediately or skip widgets; the Flow resource reports errors while the Console still renders the canvas.
- **mechanism** — Widget references — transitions to deleted widgets, bad Liquid, missing required fields — leave the definition structurally invalid.
- **detect** — `GET https://studio.twilio.com/v2/Flows/{FlowSid}` → `valid == false`, then read the `errors[]` and `warnings[]` arrays; each entry carries a `message` and the `path` of the offending widget.
- **repair** — Fix the widget at the reported `path`, then republish. Validate first with `POST https://studio.twilio.com/v2/Flows/Validate`.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/studio/rest-api/v2/flow · https://www.twilio.com/docs/studio/rest-api/v2/flow-validate

## studio-flow-not-wired-to-number

- **title** — A published Studio Flow that no phone number points at
- **symptom** — The Flow has zero executions; inbound calls and SMS hit the old webhook or Twilio's demo TwiML.
- **mechanism** — Publishing a Flow does not attach it. The number's `voice_url`/`sms_url` (or `voice_application_sid`) must be set to the Flow webhook URL, or the number assigned to the Flow in the Console.
- **detect** — For each `GET https://studio.twilio.com/v2/Flows` entry, check `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json` for any number whose `voice_url` or `sms_url` contains the `FlowSid`. Corroborate with `GET https://studio.twilio.com/v2/Flows/{FlowSid}/Executions?PageSize=1` returning an empty list.
- **repair** — `POST /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json` with `SmsUrl=https://webhooks.twilio.com/v1/Accounts/{AccountSid}/Flows/{FlowSid}` and `SmsMethod=POST`.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/studio/user-guide/studio-faq · https://www.twilio.com/docs/studio/rest-api/v2/flow

## conversations-webhook-filters-empty

- **title** — Conversations webhooks fire for no events: filters are empty
- **symptom** — `post_webhook_url` is configured but the app never receives `onMessageAdded`.
- **mechanism** — Conversations only sends the events named in `filters`. An empty or partial filter list silently drops everything else, and the default is deliberately narrow to avoid feedback loops.
- **detect** — `GET https://conversations.twilio.com/v1/Configuration/Webhooks` → `filters` is `[]`, or is missing `onMessageAdded`/`onConversationStateUpdated`, while `post_webhook_url` is non-empty.
- **repair** — `POST https://conversations.twilio.com/v1/Configuration/Webhooks` with `Filters=onMessageAdded&Filters=onConversationStateUpdated&Filters=onParticipantAdded`.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/conversations/api/webhook-configuration-resource · https://www.twilio.com/docs/conversations/conversations-webhooks

## conversations-webhook-url-missing

- **title** — Conversation webhook configured with no target URL (50369)
- **symptom** — Error `50369` "Conversation webhook URL not provided" in the Debugger.
- **mechanism** — A conversation-scoped webhook of type `webhook` was created without `Configuration.Url`, or the URL was later cleared.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 50369`; corroborate with `GET https://conversations.twilio.com/v1/Conversations/{ConversationSid}/Webhooks` → `configuration.url` null.
- **repair** — `POST https://conversations.twilio.com/v1/Conversations/{ConversationSid}/Webhooks/{Sid}` with `Configuration.Url=https://…` and `Configuration.Method=POST`.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/50369 · https://www.twilio.com/docs/conversations/api/conversation-scoped-webhook-resource

## conversations-webhook-limit

- **title** — Conversation already has five webhooks, so a sixth is rejected
- **symptom** — Error `50361` "Too many conversation webhooks".
- **mechanism** — Conversations caps conversation-scoped webhooks at five. Automation that adds one per integration hits the ceiling, and the failure surfaces on whichever integration deploys last.
- **detect** — `GET https://conversations.twilio.com/v1/Conversations/{ConversationSid}/Webhooks` → `meta.total >= 5`; or `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 50361`.
- **repair** — `DELETE https://conversations.twilio.com/v1/Conversations/{ConversationSid}/Webhooks/{WebhookSid}` for the stale one, or move the integration to a service-scoped webhook.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/50361

## event-streams-sink-failed

- **title** — An Event Streams Sink is failed and events are being dropped
- **symptom** — Downstream analytics stop receiving events; the Debugger repeats a Sink failure notice every 20 minutes.
- **mechanism** — The webhook or Kinesis destination stopped responding inside the 5-second timeout, or credentials expired, so Twilio marks the Sink `failed` and stops delivering. Nothing in the messaging or voice logs changes.
- **detect** — `GET https://events.twilio.com/v1/Sinks` → `status` is `failed`, `validating`, or `initialized` rather than `active`. Cross-check `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` for the Sink SID in `resource_sid`.
- **repair** — Fix the destination, then `POST https://events.twilio.com/v1/Sinks/{SinkSid}/Validate` with a `TestId`, and re-attach with `POST https://events.twilio.com/v1/Subscriptions/{SubscriptionSid}` `SinkSid=…`.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/events/event-streams/sink-resource · https://www.twilio.com/docs/events/event-delivery-and-duplication

## no-error-log-subscription

- **title** — Nothing subscribes to error-log events, so failures are invisible
- **symptom** — Outages are found by customers, not monitoring. The Debugger is the only record, and it ages out at 30 days.
- **mechanism** — Debugger alerts are retained for a limited window and are not pushed anywhere unless a Debugger webhook or an Event Streams subscription to `com.twilio.error-logs` exists. Every detection in this section is bounded by that 30-day window.
- **detect** — `GET https://events.twilio.com/v1/Subscriptions` → no subscription whose `GET https://events.twilio.com/v1/Subscriptions/{Sid}/SubscribedEvents` includes an error-log event type, combined with no Debugger webhook configured.
- **repair** — `POST https://events.twilio.com/v1/Subscriptions` with `Types={"type":"com.twilio.error-logs.error-log.logged"}` and a `SinkSid`; or Console → Monitor → Debugger → Webhook.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/events/event-types/errors/error-logs · https://www.twilio.com/docs/usage/troubleshooting/debugging-your-application

## sync-webhook-url-invalid

- **title** — Sync Service webhook URL is rejected as invalid (54051)
- **symptom** — Error `54051` "Invalid webhook URL" in the error logs; Sync document changes never reach the backend.
- **mechanism** — The Sync Service `webhook_url` is empty, non-HTTPS, or unreachable — and `webhooks_from_rest_enabled` is off by default, so REST-driven changes produce no callback at all even when the URL is correct.
- **detect** — `GET https://sync.twilio.com/v1/Services` → `webhook_url` empty or `http://`, or `webhooks_from_rest_enabled == false` while the app relies on REST writes. Plus `GET https://monitor.twilio.com/v1/Alerts` → `error_code == 54051`.
- **repair** — `POST https://sync.twilio.com/v1/Services/{ServiceSid}` with `WebhookUrl=https://…` and `WebhooksFromRestEnabled=true`.
- **category** — Webhooks & callbacks
- **sources** — https://www.twilio.com/docs/api/errors/54051 · https://www.twilio.com/docs/sync/api/service

---

# Voice

## dial-number-unsupported-or-invalid-13224

- **title** — Dial target is unsupported or invalid, raising error 13224
- **symptom** — `13224 Dial: Twilio does not support calling this number or the number is invalid`. The `<Dial>` leg never rings and the parent call continues to the action URL.
- **mechanism** — The destination is not E.164 (missing `+` or country code), the country or area code does not exist, or it is a premium-rate / shared-cost range Twilio refuses to terminate on. Frequently a database of legacy national-format numbers being fed straight into `<Number>`.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&StartDate={ISO8601}` → `error_code == 13224`; join `resource_sid` (the CallSid) against `GET /2010-04-01/Accounts/{AccountSid}/Calls/{CallSid}.json` → `to` shows the exact malformed destination.
- **repair** — Normalize to E.164 before dialing and validate with `GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}` → `valid == true`. Exclude premium-rate ranges from the dial list.
- **category** — Voice
- **sources** — https://www.twilio.com/docs/api/errors/13224 · https://www.twilio.com/docs/api/errors/13223

## dial-invalid-caller-id-13214

- **title** — Forwarded caller ID is invalid, so Dial is rejected (13214)
- **symptom** — `13214 Dial: Invalid callerId value`. Outbound legs from inbound forwarding fail intermittently and unpredictably.
- **mechanism** — When `<Dial>` has no explicit `callerId`, Twilio passes the inbound call's `From` straight through. Carriers sometimes deliver malformed or non-E.164 caller IDs on inbound calls; that garbage propagates to the outbound leg and the terminating provider rejects it. The intermittency — only some inbound calls carry a bad `From` — is what makes this hard to spot.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 13214`; take `resource_sid` → `GET /2010-04-01/Accounts/{AccountSid}/Calls/{CallSid}.json` → compare `from` against E.164 and check `direction == "inbound"`.
- **repair** — Set an explicit verified caller ID on every `<Dial callerId="+1…">` rather than relying on pass-through, and substitute your own number when the inbound `From` fails E.164. List verified numbers with `GET /2010-04-01/Accounts/{AccountSid}/OutgoingCallerIds.json`.
- **category** — Voice
- **sources** — https://www.twilio.com/docs/api/errors/13214 · https://www.twilio.com/docs/voice/api/call-resource

## outbound-call-failure-rate-spike

- **title** — A rising share of outbound calls end in status failed
- **symptom** — No single error code dominates — just a rising count of calls whose `status` is `failed`, alongside `busy` and `no-answer`. Users report that calls do not go through.
- **mechanism** — `failed` means the call could not be completed as dialed: bad destination, carrier rejection, geo-permission block, or an unreachable SIP leg. Twilio raises a Debugger alert for only some of these, so the Calls resource is the authoritative denominator and the only place a *rate* rather than an event is visible.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Calls.json?Status=failed&StartTime>={YYYY-MM-DD}&PageSize=1000` → count, and compare against `Status=completed` over the same window. Bucket the failed set by `to` prefix and by `direction` (`outbound-api` vs `outbound-dial`) to localize the cause, then cross-reference `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error`.
- **repair** — Depends on the bucket: geo permissions, E.164 normalization, or caller-ID reputation. Pull per-call detail with `GET /2010-04-01/Accounts/{AccountSid}/Calls/{CallSid}/Events.json`.
- **category** — Voice
- **sources** — https://www.twilio.com/docs/voice/api/call-resource

## amd-machine-answer-misrouting

- **title** — Answering-machine detection sends humans to the voicemail flow
- **symptom** — Campaign connect rates look wrong; `answered_by` on completed calls is heavily `machine_start` or `unknown` where humans were expected.
- **mechanism** — With `MachineDetection=Enable`, Twilio classifies within the first seconds and returns `human`, `machine_start`, `fax`, or `unknown`. Slow greetings, hold music, or noisy lines get classified `machine_start`; `unknown` means detection timed out. Flows that branch on `AnsweredBy` then drop real humans into a voicemail-drop path.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Calls.json?StartTime>={YYYY-MM-DD}&PageSize=1000` → tally `answered_by` across completed calls. An `unknown` share above a few percent, or `machine_start` well above the expected voicemail rate, indicates mistuned detection. Correlate with `duration` — very short `machine_start` calls are the misroutes.
- **repair** — Switch to `MachineDetection=DetectMessageEnd` and raise `MachineDetectionTimeout` / `MachineDetectionSpeechThreshold` on the outbound create call, or use `AsyncAmd=true` with `AsyncAmdStatusCallback` so the call connects first and reclassifies after.
- **category** — Voice
- **sources** — https://www.twilio.com/docs/voice/answering-machine-detection · https://www.twilio.com/docs/voice/api/call-resource

## recording-absent-with-error-code

- **title** — Call recordings silently absent with an error code
- **symptom** — A recording row exists but `status` is `absent` and an `error_code` is populated; the media URL 404s. Compliance or QA discovers the gap weeks later.
- **mechanism** — Twilio creates the Recording resource when recording is requested, then marks it `absent` if the media was never produced or was lost. The call itself completed normally, so nothing in the call logs looks wrong. `error_code` is present only when `status` is `absent`.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Recordings.json?DateCreated>={YYYY-MM-DD}&PageSize=1000` → filter `status == "absent"` and read `error_code`, `call_sid`, `source` (`DialVerb`, `RecordVerb`, `Conference`, `StartCallRecordingAPI`) to see which mechanism is failing.
- **repair** — Cross-reference each `call_sid` in `GET https://monitor.twilio.com/v1/Alerts` for the same window, and add a `recordingStatusCallback` to the `<Dial>`/`<Record>` verb so failures alert in real time instead of being found by audit.
- **category** — Voice
- **sources** — https://www.twilio.com/docs/voice/api/recording

## sip-endpoint-not-registered-32009

- **title** — SIP user is not registered on the domain, so Dial fails
- **symptom** — `32009 The user you tried to dial is not registered with the corresponding SIP Domain`. `<Dial><Sip>` legs fail while PSTN legs work.
- **mechanism** — `<Dial><Sip>` to `sip:user@domain` requires that endpoint to hold an active registration. A softphone that dropped its REGISTER refresh, or a username that does not exactly match a credential-list entry, produces a destination Twilio cannot route to.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&StartDate={ISO8601}` → `error_code == 32009`. Confirm domain config with `GET /2010-04-01/Accounts/{AccountSid}/SIP/Domains.json` → `sip_registration == true`, and list registered endpoints via the domain's credential-list mappings subresource.
- **repair** — Verify the username in `<Dial><Sip>` matches a credential-list username exactly. Console → Voice → Manage → SIP Domains → Registered SIP Endpoints shows live registrations.
- **category** — Voice
- **sources** — https://www.twilio.com/docs/api/errors/32009 · https://www.twilio.com/docs/voice/sip/api/sip-domain-resource

## sip-infrastructure-communication-error-32011

- **title** — Twilio cannot reach your SIP infrastructure (32011)
- **symptom** — `32011 Error communicating with your SIP communications infrastructure`; slow call setup, then failure. Elastic SIP Trunking inbound and outbound are both affected.
- **mechanism** — Twilio got no response, an error response (SIP 5xx), or an invalid response from your origination URI. Causes: a firewall not permitting Twilio's SIP signalling and RTP ranges, a down PBX, a wrong SIP URI, or an endpoint that never enabled TLS 1.2 after Twilio's SIP TLS 1.0/1.1 end of life.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&StartDate={ISO8601}` → `error_code == 32011`. Then `GET https://trunking.twilio.com/v1/Trunks` and, per trunk, `GET https://trunking.twilio.com/v1/Trunks/{TrunkSid}/OriginationUrls` → check each `sip_url`, `enabled`, `priority`, `weight`.
- **repair** — Allowlist Twilio's SIP signalling and media IP ranges, enable TLS 1.2 on the SIP endpoint, and correct the origination `sip_url`. Add a second URI with a lower `priority` for failover.
- **category** — Voice
- **sources** — https://www.twilio.com/docs/api/errors/32011 · https://www.twilio.com/docs/sip-trunking/troubleshooting

## trunk-cps-limit-exceeded-32001

- **title** — SIP trunk exceeds its calls-per-second limit (32001)
- **symptom** — `32001 SIP: Trunk CPS limit exceeded`; calls rejected in bursts while the average rate looks fine.
- **mechanism** — Each Elastic SIP trunk has a calls-per-second ceiling. Predictive dialers and campaign bursts blow past it in the first seconds of a batch, so the failures cluster tightly in time and vanish from any hourly average.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 32001` (note that some CPS warnings, like 32012, are logged at `LogLevel=warning`). Correlate with `GET /2010-04-01/Accounts/{AccountSid}/Calls.json` clustered by `start_time` at second granularity.
- **repair** — Request a CPS increase for the trunk through Twilio Support, rate-limit the dialer, or spread traffic across additional trunks.
- **category** — Voice
- **sources** — https://www.twilio.com/docs/api/errors/32001 · https://www.twilio.com/docs/sip-trunking/troubleshooting

## carrier-blocked-caller-id-32017

- **title** — Carrier blocks your caller ID for poor reputation (32017)
- **symptom** — `32017 PSTN: Carrier blocked call due to calling number (caller ID)`. Failures cluster on one carrier and one `from` number.
- **mechanism** — Carrier-side analytics providers score numbers on answer rate, call duration, and complaint volume. A number used for high-volume short outbound calls accumulates a bad score and gets blocked or labelled. The block is at the terminating carrier, so nothing in your own configuration changed.
- **detect** — `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error&StartDate={ISO8601}` → `error_code == 32017`; take `resource_sid` → `GET /2010-04-01/Accounts/{AccountSid}/Calls/{CallSid}.json` → group by `from` to identify the flagged number. Compare each number's `failed` vs `completed` counts and mean `duration` via `Calls.json`.
- **repair** — Register the number at freecallerregistry.com and, for T-Mobile, portal.firstorion.com. Rotate outbound traffic across numbers and raise mean call duration.
- **category** — Voice
- **sources** — https://www.twilio.com/docs/api/errors/32017

## trunk-missing-disaster-recovery-url

- **title** — SIP trunk has no disaster recovery URL configured
- **symptom** — No error code at all — until the PBX goes down and every inbound call to the trunk is lost with no fallback and no voicemail.
- **mechanism** — `disaster_recovery_url` is the TwiML endpoint Twilio calls when the trunk's origination URIs are unreachable. It is optional and empty by default, so trunks provisioned quickly ship without it. The failure is invisible in normal operation, which is exactly why it survives to production.
- **detect** — `GET https://trunking.twilio.com/v1/Trunks?PageSize=1000` → flag any trunk where `disaster_recovery_url` is null or empty; also record `disaster_recovery_method`, `secure`, `transfer_mode`.
- **repair** — `POST https://trunking.twilio.com/v1/Trunks/{TrunkSid}` with `DisasterRecoveryUrl=https://…/dr-twiml` and `DisasterRecoveryMethod=POST`.
- **category** — Voice
- **sources** — https://www.twilio.com/docs/sip-trunking/api/trunk-resource

## sip-domain-no-auth-type

- **title** — SIP Domain has no auth_type and accepts no traffic at all
- **symptom** — Every inbound SIP call to the domain is rejected. No application-level error appears, because the request is refused at authentication.
- **mechanism** — A SIP Domain routes traffic only if `auth_type` is `IP_ACL`, `CREDENTIAL_LIST`, or both. Twilio's documentation is explicit: if `auth_type` is not defined the domain cannot receive any traffic. A domain created via API without mapping a credential list or IP ACL is inert — and looks correctly provisioned in a listing.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/SIP/Domains.json` → flag domains where `auth_type` is empty or null. Also check `voice_url` is non-empty and `voice_fallback_url` is set, and confirm mappings with `GET /2010-04-01/Accounts/{AccountSid}/SIP/Domains/{DomainSid}/Auth/Calls/CredentialListMappings.json` and the IP ACL equivalent.
- **repair** — `POST /2010-04-01/Accounts/{AccountSid}/SIP/Domains/{DomainSid}/Auth/Calls/CredentialListMappings.json` with `CredentialListSid=CL…`, or the IP ACL equivalent.
- **category** — Voice
- **sources** — https://www.twilio.com/docs/voice/sip/api/sip-domain-resource · https://www.twilio.com/docs/voice/api/sending-sip

---

# Verify & Lookup

## verify-lookup-disabled

- **title** — Verify Service has lookup_enabled false, so landlines are billed
- **symptom** — OTPs silently never arrive for a slice of users; Verify bills full price for each attempt; `60205` never appears in logs even though the destinations are landlines.
- **mechanism** — `lookup_enabled` controls whether Verify performs a Lookup on each verification start. It is off by default, and `skip_sms_to_landlines` requires it — with lookup off, Verify cannot classify the line type and happily sends SMS into landlines and unroutable ranges.
- **detect** — `GET https://verify.twilio.com/v2/Services/{ServiceSid}` → `lookup_enabled == false`. Cross-check `skip_sms_to_landlines`: `true` while `lookup_enabled` is `false` is a no-op configuration.
- **repair** — `POST https://verify.twilio.com/v2/Services/{ServiceSid}` with `LookupEnabled=true` and `SkipSmsToLandlines=true`. Console → Verify → Services → General → enable Lookup.
- **category** — Verify & Lookup
- **sources** — https://www.twilio.com/docs/verify/api/service · https://www.twilio.com/docs/api/errors/60205

## verify-sms-to-landline

- **title** — Verify sends SMS to landlines, giving 60205 or silence
- **symptom** — HTTP 403 `60205: SMS is not supported by landline phone number`, or — with lookup off — a `pending` verification that never converts.
- **mechanism** — The destination is a landline, `fixedVoip`, or `pager` range that cannot receive SMS. Signup forms that accept any digit string funnel these straight into Verify.
- **detect** — Pre-flight `GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=line_type_intelligence` → `line_type_intelligence.type` in `{landline, fixedVoip, pager, voicemail, unknown}`. Retrospectively, `GET https://verify.twilio.com/v2/Attempts?Status=unconverted&DateCreatedAfter={ISO8601}` and bucket `channel_data.to` by line type.
- **repair** — Set `SkipSmsToLandlines=true` (with `LookupEnabled=true`) on `POST https://verify.twilio.com/v2/Services/{ServiceSid}`, and route landline users to `Channel=call`. Gate signup on `line_type_intelligence.type == "mobile"`.
- **category** — Verify & Lookup
- **sources** — https://www.twilio.com/docs/api/errors/60205 · https://www.twilio.com/docs/lookup/v2-api/line-type-intelligence

## verify-code-length-too-short

- **title** — Verify code_length is 4, so brute force needs about 50 guesses
- **symptom** — No error. Account-takeover reports, plus `60202` spikes from attackers burning the five-check budget across many fresh verifications.
- **mechanism** — `code_length` is settable 4–10 and each verification allows five check attempts before `60202`. At length 4 the keyspace is 10,000; with no per-phone rate limit an attacker restarts verifications and grinds five guesses at a time. The ten-minute TTL is the only other brake.
- **detect** — `GET https://verify.twilio.com/v2/Services/{ServiceSid}` → `code_length < 6`. Read `custom_code_enabled` in the same response — `true` in production means app-supplied codes bypass Twilio's randomness entirely.
- **repair** — `POST https://verify.twilio.com/v2/Services/{ServiceSid}` with `CodeLength=6` and `CustomCodeEnabled=false`, paired with a per-phone rate limit.
- **category** — Verify & Lookup
- **sources** — https://www.twilio.com/docs/verify/api/service · https://www.twilio.com/docs/api/errors/60202

## verify-no-rate-limits

- **title** — Verify Service has zero Rate Limits configured
- **symptom** — `60212` "Too many concurrent requests for phone number" and `20429` under attack; unbounded verification spend from a scripted signup endpoint.
- **mechanism** — Verify's built-in platform protections are per phone number only. Service Rate Limits — keyed on your own identifier (IP, user ID, number prefix) with Buckets defining `max` per `interval` — are opt-in and do not exist by default, so an attacker rotating destination numbers from one IP is unthrottled.
- **detect** — `GET https://verify.twilio.com/v2/Services/{ServiceSid}/RateLimits` → flag an empty `rate_limits[]`. For each existing `RK…`, `GET https://verify.twilio.com/v2/Services/{ServiceSid}/RateLimits/{RateLimitSid}/Buckets` → flag empty `buckets[]` or a single bucket with an implausibly high `max` or long `interval`.
- **repair** — `POST https://verify.twilio.com/v2/Services/{ServiceSid}/RateLimits` with `UniqueName=end_user_ip`, then `POST …/RateLimits/{RK…}/Buckets` with `Max=5&Interval=60` and a second bucket `Max=25&Interval=3600`. Pass `RateLimits={"end_user_ip":"<ip>"}` on verification start.
- **category** — Verify & Lookup
- **sources** — https://www.twilio.com/docs/verify/api/service-rate-limits · https://www.twilio.com/docs/verify/api/service-rate-limit-buckets

## verify-conversion-rate-collapse

- **title** — Verify conversion rate collapsing: SMS pumping in progress
- **symptom** — Verify spend jumps 5–50×, mostly to one or two country codes, and almost none of those verifications are ever checked. No error code — the sends succeed.
- **mechanism** — SMS pumping (artificially inflated traffic): fraudsters drive your public signup or OTP endpoint with numbers on carriers they share revenue with. The OTP is delivered and billed; nobody ever enters it, so conversion rate on the affected prefix collapses toward zero.
- **detect** — `GET https://verify.twilio.com/v2/Attempts/Summary?VerifyServiceSid={VA…}&DateCreatedAfter={ISO8601}&Country={ISO2}` → `conversion_rate_percentage`, `total_attempts`, `total_converted`, `total_unconverted`. Flag any country or `DestinationPrefix` whose conversion rate is far below the service baseline on non-trivial volume. Drill in with `GET https://verify.twilio.com/v2/Attempts?Status=unconverted&Country={ISO2}` → `channel_data.to`, `price`.
- **repair** — Console → Verify → Services → SMS → enable Fraud Guard (Standard or Max). Add Geo Permissions restrictions for countries you do not serve, and add prefix-keyed Service Rate Limits.
- **category** — Verify & Lookup
- **sources** — https://www.twilio.com/docs/verify/api/verification-attempts-summary · https://www.twilio.com/docs/verify/preventing-toll-fraud

## fraud-guard-blocking-prefix

- **title** — Fraud Guard blocked the prefix, so legit users get 60410
- **symptom** — `60410` "Verification delivery attempt blocked" for a whole country or prefix; real users in that region cannot sign up for roughly twelve hours.
- **mechanism** — Fraud Guard detected pumping-shaped traffic to a number prefix and imposed a temporary 12-hour SMS block, re-arming in 12-hour increments while suspicious traffic continues. Legitimate users sharing the prefix are collateral.
- **detect** — `GET https://verify.twilio.com/v2/Attempts?Status=unconverted&DateCreatedAfter={ISO8601}` grouped by `channel_data.to` prefix and `country`. Confirm per number with `GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}?Fields=sms_pumping_risk` → `sms_pumping_risk.number_blocked`, `number_blocked_date`, `number_blocked_last_3_months`, `carrier_risk_category`, `sms_pumping_risk_score`.
- **repair** — No API unblock; the block expires once the fraudulent pattern stops. Cut off the source: add Service Rate Limits keyed on IP or user, gate signup on `sms_pumping_risk_score` (block at 90+, add friction 60–75), and lower the protection level at Console → Verify → Services → SMS if the block is a false positive.
- **category** — Verify & Lookup
- **sources** — https://www.twilio.com/docs/api/errors/60410 · https://www.twilio.com/docs/lookup/v2-api/sms-pumping-risk

## verify-max-check-attempts

- **title** — Verification burned all five checks, so 60202 until it expires
- **symptom** — HTTP 429 `60202: Max (5) verification check attempts reached`. The user is stuck: re-entering the code keeps failing and the UI shows no path forward.
- **mechanism** — Each verification permits five checks. Typos, a UI that auto-submits on every keystroke, or a double-firing check handler exhaust the budget; the verification moves to `max_attempts_reached` and stays dead for the rest of its ten-minute TTL.
- **detect** — `GET https://verify.twilio.com/v2/Services/{ServiceSid}/Verifications/{VE…}` → `status == "max_attempts_reached"`. Note the resource is soft-deleted once approved or expired, so a `20404` here means it already resolved. Fleet-wide, count that status against total verifications.
- **repair** — Debounce the check call client-side and submit only on a complete code; after `60202`, offer "request a new code" rather than retrying. Server-side, start a fresh verification, or resolve the stuck one with `POST …/Verifications/{VE…}` `Status=canceled`.
- **category** — Verify & Lookup
- **sources** — https://www.twilio.com/docs/api/errors/60202 · https://www.twilio.com/docs/verify/api/verification

## verify-max-send-attempts

- **title** — Resend-code loop with no check trips 60203 max send attempts
- **symptom** — HTTP 429 `60203: Max send attempts reached` after the user taps Resend a handful of times. You are billed for every send.
- **mechanism** — Verify allows five sends per verification before requiring the check step. A resend button with no cooldown, or a retry wrapper that treats slow SMS delivery as failure, drains it in seconds. The limit clears only after a check or after the ten-minute expiry.
- **detect** — `GET https://verify.twilio.com/v2/Services/{ServiceSid}/Verifications/{VE…}` → `send_code_attempts` (an array of `{channel, time, attempt_sid}`). Flag length ≥ 4 while `status == "pending"`. Aggregate with `GET https://verify.twilio.com/v2/Attempts?VerificationSid={VE…}`.
- **repair** — Enforce a 30–60 second client cooldown on resend and disable the button at three attempts. Resolve stuck verifications with `POST …/Verifications/{VE…}` `Status=canceled`, then start a new one, and add a `rate_limits` key on start so the platform enforces it too.
- **category** — Verify & Lookup
- **sources** — https://www.twilio.com/docs/api/errors/60203 · https://www.twilio.com/docs/verify/api/verification

## verify-do-not-share-warning-off

- **title** — OTP body ships without the do-not-share phishing warning
- **symptom** — No error. Users are socially engineered into reading codes aloud to "support", and the OTP SMS reads as a bare code with no caution line.
- **mechanism** — `do_not_share_warning_enabled` appends a security warning to the SMS verification body. It is off by default, so services built before the flag existed (or created via API without it) send warning-free codes. Related: `dtmf_input_required` on the voice channel guards against voicemail systems capturing a spoken code.
- **detect** — `GET https://verify.twilio.com/v2/Services/{ServiceSid}` → `do_not_share_warning_enabled == false`; `dtmf_input_required == false` if you use `Channel=call`; and `default_template_sid` — a custom template may have dropped the warning text, so cross-reference `GET https://verify.twilio.com/v2/Templates`.
- **repair** — `POST https://verify.twilio.com/v2/Services/{ServiceSid}` with `DoNotShareWarningEnabled=true` and, for voice, `DtmfInputRequired=true`. If a custom template is set, resubmit it with the warning line included.
- **category** — Verify & Lookup
- **sources** — https://www.twilio.com/docs/verify/api/service · https://www.twilio.com/docs/verify/api/templates

## lookup-invalid-or-uncovered-number

- **title** — Number is invalid or uncovered, giving 21211 or 60600
- **symptom** — `21211: The 'To' phone number is not a valid phone number or is incorrectly formatted` on send, or `60600: Unprovisioned or out of coverage` from Lookup/Verify. `21614` for landlines.
- **mechanism** — Stored numbers are national-format, missing the `+` and country code, have transposed digits, or sit in a range no carrier has been assigned. Twilio requires strict E.164 and does no fuzzy parsing. `60600` specifically means Twilio's carrier data has no record of the number.
- **detect** — `GET https://lookups.twilio.com/v2/PhoneNumbers/{E164}` → `valid` (boolean) and `validation_errors[]` with values `TOO_SHORT`, `TOO_LONG`, `INVALID_BUT_POSSIBLE`, `INVALID_COUNTRY_CODE`, `INVALID_LENGTH`, `NOT_A_NUMBER`. Also read `country_code`, `calling_country_code`, and the normalized `phone_number`.
- **repair** — Batch-run Lookup over the stored contact set and write back the normalized `phone_number`; quarantine rows where `valid == false`. At the input layer, validate with Lookup before persisting and store E.164 only.
- **category** — Verify & Lookup
- **sources** — https://www.twilio.com/docs/lookup/v2-api · https://www.twilio.com/docs/api/errors/21211 · https://www.twilio.com/docs/api/errors/60600

---

# Account & billing

## read-credential-permission-denied

- **title** — API credential rejected: Twilio returns 20003 permission denied
- **symptom** — HTTP 401 with `{"code": 20003, "message": "Authenticate"}` on every call; the SDK throws `TwilioRestException 20003`.
- **mechanism** — Account SID / Auth Token mismatch, a deleted or region-mismatched API key, whitespace in the secret, subaccount credentials used against the parent, or a Standard API key hitting `/Accounts` or `/Keys` (those need a Main key). A proxy stripping the `Authorization` header produces the same code.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}.json` — if HTTP 401 and the body's `code == 20003`, the credential is dead. Compare the returned `sid` against the SID you authenticated with to catch parent/subaccount crossing.
- **repair** — Console → Account → API keys & tokens → create a Main API key; use `SK…`/secret as the basic-auth pair with the target `AccountSid` in the path. Verify with `GET /2010-04-01/Accounts.json`.
- **category** — Account & billing
- **sources** — https://www.twilio.com/docs/api/errors/20003 · https://www.twilio.com/docs/iam/api-keys

## account-suspended-or-closed

- **title** — Account status is suspended, so every send fails with 20005
- **symptom** — HTTP 403 `20005: Account not active`; messages, calls and number purchases are all rejected while the Console still loads. Queued messages fail en masse with `30002`.
- **mechanism** — Balance hit zero or negative, a ToS or policy review disabled the project, or the parent account was suspended (which cascades to subaccounts). `closed` is terminal — the account cannot be reopened.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}.json` → `status`. Alert on anything other than `active`. Corroborate with `GET /2010-04-01/Accounts/{AccountSid}/Messages.json` → `error_code == 30002`.
- **repair** — If suspended for balance: Console → Billing → add funds, then wait 5–10 minutes for reactivation. If policy-related or closed, open a ticket at help.twilio.com; closed accounts require a new account.
- **category** — Account & billing
- **sources** — https://www.twilio.com/docs/api/errors/20005 · https://www.twilio.com/docs/api/errors/30002 · https://www.twilio.com/docs/iam/api/account

## trial-account-still-in-use

- **title** — Account is still Trial, so sends are restricted and prefixed
- **symptom** — `21608` on any unverified destination; every outbound SMS carries the "Sent from your Twilio trial account" prefix; `20008` when test credentials touch an unsupported resource.
- **mechanism** — `type: "Trial"` accounts may only message numbers listed as verified caller IDs, are capped at three verified numbers for the account's lifetime, and can only verify by SMS. Teams ship to staging and then production on a trial account and only discover it at real traffic.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}.json` → flag `type == "Trial"`.
- **repair** — Console → Billing → Upgrade (add a payment method). For upgraded accounts still hitting 21608, submit a Primary Compliance Profile under Console → Compliance → Trust Hub.
- **category** — Account & billing
- **sources** — https://www.twilio.com/docs/api/errors/21608 · https://support.twilio.com/hc/en-us/articles/360036052753-Twilio-Free-Trial-Limitations

## trial-verified-caller-ids-exhausted

- **title** — Trial verified-number pool exhausted, so 21608 on new testers
- **symptom** — `21608` for a teammate's phone while the original developer's phone still works.
- **mechanism** — A trial account can verify only three unique numbers over its entire lifetime, and only via SMS. Deleting a verified caller ID does not restore the quota.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/OutgoingCallerIds.json` → count entries and compare each `phone_number` against the `To` values your app actually sends to. On an account where `Accounts.json` reports `type == "Trial"`, a count at or near three means the pool is spent.
- **repair** — Upgrade the account (Console → Billing → Upgrade), which removes the verified-number restriction entirely. Do not try to free slots by deleting caller IDs.
- **category** — Account & billing
- **sources** — https://support.twilio.com/hc/en-us/articles/360036052753-Twilio-Free-Trial-Limitations · https://www.twilio.com/docs/voice/api/outgoing-caller-ids

## balance-below-safety-floor

- **title** — Account balance is one busy hour from a 20005 suspension
- **symptom** — Nothing — until traffic peaks, the balance crosses zero, and the whole account flips to `suspended` with `20005` mid-campaign.
- **mechanism** — Twilio is prepay by default: when the balance hits zero the account is suspended rather than throttled. Auto-recharge failing silently on an expired card has the same end state.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Balance.json` → `balance` and `currency`. Compare against a burn rate from `GET /2010-04-01/Accounts/{AccountSid}/Usage/Records/Daily.json?Category=totalprice&StartDate={7d ago}` → `usage_records[].price`. Flag when `balance` is less than seven times the median daily price.
- **repair** — Console → Billing → Manage billing → enable Auto Recharge with a trigger amount of at least seven days of spend and a valid card.
- **category** — Account & billing
- **sources** — https://www.twilio.com/docs/usage/api/usage-record · https://www.twilio.com/docs/api/errors/20005

## no-usage-trigger-configured

- **title** — No Usage Trigger set, so fraud or overspend runs unalarmed
- **symptom** — A five-figure SMS bill or a `20005` suspension arrives with no prior warning; no webhook ever fired.
- **mechanism** — Usage Triggers are the only server-side spend or volume alarm Twilio offers, and none exist by default. Without one, an SMS-pumping burst or a retry loop runs to balance exhaustion unobserved.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Usage/Triggers.json` → flag an empty `usage_triggers[]`, or the absence of any entry with `usage_category` in `{totalprice, sms, calls}`, `trigger_by == "price"`, a non-null `callback_url`, and `recurring` set to `daily`/`monthly` rather than a one-shot null.
- **repair** — `POST /2010-04-01/Accounts/{AccountSid}/Usage/Triggers.json` with `UsageCategory=totalprice&TriggerBy=price&TriggerValue={daily cap}&Recurring=daily&CallbackUrl={alerting endpoint}&CallbackMethod=POST`.
- **category** — Account & billing
- **sources** — https://www.twilio.com/docs/usage/api/usage-trigger · https://www.twilio.com/docs/usage/fraud-response-guide/contain

## auth-token-used-instead-of-api-key

- **title** — No API keys exist, so the account Auth Token is the credential
- **symptom** — No error. But rotating the compromised credential means a hard 20003 outage across every service simultaneously, with no per-service revocation.
- **mechanism** — The Auth Token is a single account-wide secret that also signs webhook `X-Twilio-Signature` validation. Using it as the runtime credential couples secret rotation to webhook verification and to every deployed service at once.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Keys.json` → an empty `keys[]`, or fewer keys than deployed services, means the Auth Token is doing the work.
- **repair** — `POST /2010-04-01/Accounts/{AccountSid}/Keys.json` with `FriendlyName={service-name}`; store the returned `sid` and `secret` as the basic-auth pair. Keep the Auth Token only for signature validation.
- **category** — Account & billing
- **sources** — https://www.twilio.com/docs/iam/api-keys · https://www.twilio.com/docs/usage/security/secure-your-twilio-account

## stale-or-orphaned-api-keys

- **title** — Years-old API keys are still live with no owner
- **symptom** — Silent. Surfaces as an unexplained 20003 after someone deletes "the unused one", or as an unattributable credential during an incident.
- **mechanism** — API keys never expire and carry no usage metadata. Keys from departed contractors, dead staging stacks, and one-off scripts accumulate, and each is a full-privilege path into the account.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Keys.json` → per entry read `sid`, `friendly_name`, `date_created`, `date_updated`. Flag keys where `date_created` is older than your rotation window, or `friendly_name` is empty or "Untitled".
- **repair** — Confirm ownership, then `DELETE /2010-04-01/Accounts/{AccountSid}/Keys/{SK…}` — this immediately revokes REST access and invalidates all Access Tokens signed with that key's secret.
- **category** — Account & billing
- **sources** — https://www.twilio.com/docs/iam/api-keys/key-resource-v2010 · https://www.twilio.com/docs/iam/api-keys

## subaccount-suspended-silently

- **title** — A subaccount is suspended, so that tenant's traffic 20005s
- **symptom** — One tenant reports total messaging failure while every other tenant is fine; the parent account dashboard looks healthy.
- **mechanism** — Subaccount status is set by API or cascades from a parent suspension, and Twilio sends no notification when a subaccount is suspended programmatically. Multi-tenant apps that key on the parent SID never see it.
- **detect** — `GET /2010-04-01/Accounts.json?Status=suspended` with parent credentials — any entry whose `owner_account_sid` equals your parent SID is a suspended tenant. Also list `?Status=closed`.
- **repair** — `POST /2010-04-01/Accounts/{SubAccountSid}.json` with `Status=active`, authenticated with the parent account credentials. Closed subaccounts are irreversible.
- **category** — Account & billing
- **sources** — https://www.twilio.com/docs/iam/api/subaccounts · https://support.twilio.com/hc/en-us/articles/223135987-How-to-Change-a-Subaccount-Status-to-Closed

## rest-api-concurrency-exhausted

- **title** — REST concurrency limit hit, so bursts return 20429
- **symptom** — HTTP 429 with `20429: Too many requests` during traffic spikes; requests succeed on retry. Common on `Messages.create` fan-outs and Verify status polling.
- **mechanism** — Twilio caps concurrent in-flight REST requests per account, and subaccount concurrency does not roll up to the parent. Unbounded worker pools or per-request Lambda concurrency blow through the ceiling, and the 429s themselves still count toward the tally.
- **detect** — Issue any cheap read, for example `GET /2010-04-01/Accounts/{AccountSid}.json`, and read the `Twilio-Concurrent-Requests` response header, which reports current concurrency. Sample it during peak; a value pinned near the limit, or any observed `20429`, confirms it.
- **repair** — No API or console setting — fix the client. Cap outbound concurrency below the observed ceiling, add exponential backoff with jitter on 429 (safe to retry; the request was never processed), and shard high-volume tenants across subaccounts so their concurrency budgets are independent.
- **category** — Account & billing
- **sources** — https://www.twilio.com/docs/api/errors/20429 · https://www.twilio.com/docs/usage/rest-api-best-practices

## pinned-old-api-version

- **title** — Numbers still pinned to the stale 2008-08-01 API version
- **symptom** — Response shapes differ from the documentation, and fields the docs promise — `error_code` on Messages, for one — are simply missing.
- **mechanism** — The Account resource carries a default `ApiVersion`, and legacy phone numbers carry their own `api_version` set at purchase time. Old pins keep serving the 2008 schema for webhooks to that number, indefinitely and invisibly.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json` → any entry where `api_version != "2010-04-01"`. Also read the account default from `GET /2010-04-01/Accounts/{AccountSid}.json`.
- **repair** — `POST /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers/{PNSid}.json` with `ApiVersion=2010-04-01`, and update the account default in Console → Account → API version.
- **category** — Account & billing
- **sources** — https://www.twilio.com/docs/usage/api/incoming-phone-number · https://www.twilio.com/docs/usage/api

## eol-programmable-chat-in-use

- **title** — Account still runs Programmable Chat, dead 1 June 2026
- **symptom** — The Chat SDK works today; no deprecation error yet, but the product is scheduled for end of life and will stop receiving fixes.
- **mechanism** — Programmable Chat was superseded by Conversations. Chat in Flex reaches EOL on 2026-06-01, after which it may stop working as expected. There is no automated migration.
- **detect** — `GET https://chat.twilio.com/v2/Services` returns one or more services with a recent `date_updated` — the account still holds live Chat services.
- **repair** — Migrate each Chat Service to Conversations (`GET/POST https://conversations.twilio.com/v1/Services`) and repoint clients before the cutover date.
- **category** — Account & billing
- **sources** — https://www.twilio.com/en-us/changelog/programmable-chat-in-flex-reaching-end-of-life-on-june-1--2026 · https://www.twilio.com/en-us/changelog/programmable-chat-end-of-life-notice

## eol-notify-service-in-use

- **title** — Account still holds Notify services after Notify's EOL
- **symptom** — Push notifications silently stop; Notify bindings no longer deliver and nothing in the API says why.
- **mechanism** — Twilio Notify reached end of life on 2025-12-31. Remaining services are unsupported, and the resource still exists in the API long after delivery stops.
- **detect** — `GET https://notify.twilio.com/v1/Services` returns a non-empty list.
- **repair** — Move push to the platform SDKs directly (FCM/APNs) or to Verify Push, then `DELETE https://notify.twilio.com/v1/Services/{Sid}` once traffic is off it.
- **category** — Account & billing
- **sources** — https://www.twilio.com/en-us/changelog/notify-api-end-of-life-further-extension-notice

## unreleased-recordings-storage

- **title** — Call recordings accumulate and bill for storage forever
- **symptom** — A growing recordings-storage line on the usage report with no retention policy behind it.
- **mechanism** — Twilio stores recordings indefinitely and bills per stored minute unless the application deletes them after download. Apps that fetch and archive recordings almost never delete the Twilio-side copy.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Recordings.json?PageSize=1` → a large total, plus `GET /2010-04-01/Accounts/{AccountSid}/Usage/Records/Daily.json?Category=recordings` showing rising `usage`.
- **repair** — Download, then `DELETE /2010-04-01/Accounts/{AccountSid}/Recordings/{RecordingSid}.json`; or set a retention policy in Console → Voice → Settings.
- **category** — Account & billing
- **sources** — https://www.twilio.com/docs/usage/manage-unused-resources · https://www.twilio.com/docs/voice/api/recording

## recordings-not-encrypted

- **title** — Call recordings are stored without customer-key encryption
- **symptom** — No error. Recordings sit in Twilio storage retrievable with account credentials alone, which is a finding the first time anyone runs a PCI or SOC 2 review.
- **mechanism** — Voice Recording Encryption is opt-in. Without it, `encryption_details` is absent and the media is accessible to anyone holding account credentials — including a leaked Auth Token.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Recordings.json` → recordings where `encryption_details` is null.
- **repair** — Console → Voice → Settings → General → enable Voice Recording Encryption and upload a public key. New recordings then carry `encryption_details`; existing ones are not retroactively encrypted.
- **category** — Account & billing
- **sources** — https://www.twilio.com/docs/voice/tutorials/voice-recording-encryption

---

# Regulatory & geo

## sms-geo-permissions-disabled

- **title** — SMS Geo Permissions off for the destination country (21408)
- **symptom** — `21408` "Message blocked: permissions disabled for the destination region" on every message to a given country, while identical code works domestically. Typically appears the day international users are onboarded.
- **mechanism** — New projects default to SMS-enabled for the home country only, inferred from the phone number verified at signup. Every other country must be explicitly enabled. Permissions are evaluated by destination country code, so a malformed `To` prefix produces the same error. Iran, Syria and Cuba are blocked outright regardless of settings.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → filter `error_code == 21408`, then group by the country prefix of `to` to enumerate exactly which countries are disabled. Corroborate with `GET https://monitor.twilio.com/v1/Alerts?LogLevel=error` → `error_code == 21408`. Note there is **no read or write REST API for SMS Geo Permissions** — this error is the only read-only signal, which makes it a known blind spot.
- **repair** — Console only: Messaging → Settings → Geo Permissions → enable the listed countries. There is no REST write path. Verify the `To` values are correct E.164 with the right country code first.
- **category** — Regulatory & geo
- **sources** — https://www.twilio.com/docs/api/errors/21408 · https://support.twilio.com/hc/en-us/articles/223181108-International-SMS-Messaging-Geographic-Permissions-Geo-Permissions-and-How-They-Work

## voice-dialing-permissions-blocked

- **title** — Voice dialing permissions block the destination (21215/13227)
- **symptom** — Outbound calls fail with `21215` (REST-initiated) or `13227` (TwiML `<Dial>`), both "account not authorized to call this number". Subaccounts fail while the parent account succeeds.
- **mechanism** — Voice Dialing Permissions are a per-country, per-risk-class allowlist with three independent switches: `low_risk_numbers_enabled`, `high_risk_special_numbers_enabled`, and `high_risk_tollfraud_numbers_enabled`. A country can be enabled for low risk yet still block a specific high-risk prefix. Separately, subaccounts inherit the parent's permissions only when `dialing_permissions_inheritance` is true; when false each subaccount carries its own home-country-only default, which is why a working integration breaks the moment traffic moves to a subaccount.
- **detect** — `GET https://voice.twilio.com/v1/DialingPermissions/Countries` → per country read `iso_code`, `country_codes`, and the three enabled flags; or filter directly with `?LowRiskNumbersEnabled=false`. For one country, `GET https://voice.twilio.com/v1/DialingPermissions/Countries/{IsoCode}` and its `HighRiskSpecialPrefixes` subresource. Check inheritance with `GET https://voice.twilio.com/v1/Settings` → `dialing_permissions_inheritance`. Confirm live failures via `GET https://monitor.twilio.com/v1/Alerts` → `error_code in {21215, 13227}`.
- **repair** — `POST https://voice.twilio.com/v1/DialingPermissions/BulkCountryUpdates` with an `UpdateRequest` JSON array of `{"iso_code":"XX","low_risk_numbers_enabled":true}`. To fix subaccounts wholesale, `POST https://voice.twilio.com/v1/Settings` with `DialingPermissionsInheritance=true`.
- **category** — Regulatory & geo
- **sources** — https://www.twilio.com/docs/voice/api/dialingpermissions-country-resource · https://www.twilio.com/docs/voice/api/dialingpermissions-settings-resource · https://www.twilio.com/docs/api/errors/21215

## high-risk-dialing-permissions-open

- **title** — High-risk toll-fraud dialing prefixes are left enabled
- **symptom** — A sudden burst of expensive international calls to premium ranges, discovered on the invoice. This is the inverse of the previous note: permissions too open rather than too closed.
- **mechanism** — On upgraded accounts, high-risk special-service and toll-fraud prefixes stay callable unless explicitly disabled. IRSF (international revenue share fraud) attackers target exactly these narrow ranges, and a single compromised endpoint can run five figures overnight.
- **detect** — `GET https://voice.twilio.com/v1/DialingPermissions/Countries` → entries with `high_risk_special_numbers_enabled == true` or `high_risk_tollfraud_numbers_enabled == true` for countries you do not serve. Cross-reference actual traffic with `GET /2010-04-01/Accounts/{AccountSid}/Calls.json` grouped by `to` prefix.
- **repair** — `POST https://voice.twilio.com/v1/DialingPermissions/BulkCountryUpdates` with an `UpdateRequest` disabling `high_risk_special_numbers_enabled` and `high_risk_tollfraud_numbers_enabled` for every unused ISO code.
- **category** — Regulatory & geo
- **sources** — https://www.twilio.com/docs/voice/api/dialing-permissions-resources · https://www.twilio.com/docs/voice/api/dialingpermissions-highriskspecialprefix-resource

## regulatory-bundle-rejected

- **title** — Regulatory Bundle is twilio-rejected, blocking number purchase
- **symptom** — Number provisioning in a regulated country fails, or an existing number is at risk of reclamation. `GET /v2/RegulatoryCompliance/Bundles` shows `status == "twilio-rejected"`.
- **mechanism** — Regulated countries require a Bundle — a container of End-User and Supporting Document item assignments matched to a Regulation for that ISO country and number type. Twilio's regulatory team rejects bundles whose documents do not match the end user, are illegible, expired, or of the wrong class. Bundle status is entirely out of band from the number itself, so teams only notice when a purchase 400s.
- **detect** — `GET https://numbers.twilio.com/v2/RegulatoryCompliance/Bundles?Status=twilio-rejected` → read `sid`, `friendly_name`, `regulation_sid`, `status`, `valid_until`, `email`. Filter the whole estate with `IsoCountry`, `NumberType`, `EndUserType`, `SortBy=date-updated`.
- **repair** — `GET /v2/RegulatoryCompliance/Bundles/{BundleSid}/ItemAssignments` to find the offending item, replace the End-User or Supporting Document, then `POST https://numbers.twilio.com/v2/RegulatoryCompliance/Bundles/{BundleSid}` with `Status=pending-review`.
- **category** — Regulatory & geo
- **sources** — https://www.twilio.com/docs/phone-numbers/regulatory/api/bundles · https://www.twilio.com/docs/phone-numbers/regulatory/api

## regulatory-bundle-expiring

- **title** — Approved bundle's valid_until is near; numbers face reclamation
- **symptom** — No error today. `status == "twilio-approved"` but `valid_until` is weeks away. On that date the bundle flips to `twilio-rejected` and the associated numbers become non-compliant and subject to loss.
- **mechanism** — Many national regulators require periodic re-attestation of address and identity documents. Twilio encodes that as `valid_until` on the Bundle; unless the compliance information is refreshed before it passes, the bundle is auto-rejected. This is the classic "worked for 18 months, then all our German numbers died" failure, and it is invisible unless someone polls the field.
- **detect** — `GET https://numbers.twilio.com/v2/RegulatoryCompliance/Bundles?HasValidUntilDate=true&SortBy=valid-until&SortDirection=ASC` (or `ValidUntilDate<=` with a horizon date) → flag `status == "twilio-approved"` with `valid_until` inside your renewal window.
- **repair** — Refresh the supporting documents (`POST /v2/RegulatoryCompliance/SupportingDocuments`, reassign via `POST /v2/RegulatoryCompliance/Bundles/{BundleSid}/ItemAssignments`), then `POST /v2/RegulatoryCompliance/Bundles/{BundleSid}` with `Status=pending-review`. Set `StatusCallback` on the bundle so future transitions webhook.
- **category** — Regulatory & geo
- **sources** — https://www.twilio.com/docs/phone-numbers/regulatory/api/bundles

## bundle-evaluation-noncompliant

- **title** — Bundle evaluates noncompliant: a required field never passed
- **symptom** — A bundle sits in `draft` and every submission attempt bounces, or a rejection gives no useful prose. The specific missing field is visible only in the Evaluations subresource, which most teams never call.
- **mechanism** — Before review, a bundle is machine-evaluated against its regulation's requirements. The evaluation returns compliant/noncompliant plus a per-requirement breakdown; a single missing attribute — wrong document type, absent business registration number, an address in the wrong country — makes the whole bundle noncompliant. The Bundles resource itself surfaces only the coarse `status`.
- **detect** — `GET https://numbers.twilio.com/v2/RegulatoryCompliance/Bundles/{BundleSid}/Evaluations` → `status` (`compliant|noncompliant`), then walk `results[]`: `requirement_friendly_name`, `requirement_name`, `object_type`, `passed`, `failure_reason`, `error_code`, and `invalid[]` with per-field `friendly_name`, `object_field`, `failure_reason`. Compare against `GET https://numbers.twilio.com/v2/RegulatoryCompliance/Regulations/{RegulationSid}` for the required item list.
- **repair** — For each entry in `results[].invalid[]`, correct the named `object_field` on the referenced End-User or Supporting Document, reassign it, then re-run `POST /v2/RegulatoryCompliance/Bundles/{BundleSid}/Evaluations` and submit once compliant.
- **category** — Regulatory & geo
- **sources** — https://www.twilio.com/docs/phone-numbers/regulatory/api/evaluations · https://www.twilio.com/docs/phone-numbers/regulatory/api/bundles

## trusthub-customer-profile-rejected

- **title** — Trust Hub Customer Profile rejected, cascading into A2P and TFV
- **symptom** — Brand registration and toll-free verification both fail for reasons that make no sense in isolation. The shared root: `GET /v1/CustomerProfiles` shows `status == "twilio-rejected"` (or still `draft`/`in-review`) with populated `errors`.
- **mechanism** — The Customer Profile is the upstream identity object that A2P brands (`customer_profile_bundle_sid`), toll-free verifications (`customer_profile_sid`), SHAKEN/STIR and Voice Integrity all hang off. Reject it and every downstream product fails with its own product-specific error code, which sends teams chasing symptoms per product instead of the single shared cause. A profile also carries `valid_until` and can lapse.
- **detect** — `GET https://trusthub.twilio.com/v1/CustomerProfiles` → read `status` (`draft|pending-review|in-review|twilio-rejected|twilio-approved`), `errors`, `valid_until`, `policy_sid`. For a failing profile, `GET https://trusthub.twilio.com/v1/CustomerProfiles/{Sid}/Evaluations` for the per-requirement breakdown and `GET …/{Sid}/EntityAssignments` for the submitted objects. Same shape at `GET https://trusthub.twilio.com/v1/TrustProducts`.
- **repair** — Correct the assigned End-User and Supporting Document objects, then `POST https://trusthub.twilio.com/v1/CustomerProfiles/{Sid}` with `Status=pending-review`. Re-trigger the downstream brand or toll-free verification only after the profile is approved.
- **category** — Regulatory & geo
- **sources** — https://www.twilio.com/docs/trust-hub/trusthub-rest-api/customer-profiles · https://www.twilio.com/docs/messaging/api/brand-registration-resource

## alphanumeric-sender-id-unregistered

- **title** — Alphanumeric Sender ID unregistered for the destination country
- **symptom** — `30040` ("Sender ID pre-registration required by destination carrier") or `30041` ("Message from a restricted or unregistered sender"). Works in one country, dies in the next. `30018` is the warning-level sibling.
- **mechanism** — A growing set of countries — India, Saudi Arabia, UAE, Vietnam — mandate pre-registration of alphanumeric sender IDs with the local regulator or carrier. Twilio must have the exact string registered for that country, and matching is case-sensitive, so `MyBrand` and `MYBRAND` are different senders. Sending without registration is blocked at the destination carrier, not at the API, so the create call returns 201 and only the status callback reveals the failure.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → filter `error_code in {30040, 30041, 30018}`, then group by the `from` string (non-E.164 `from` values are alphanumeric sender IDs) and by the country prefix of `to`. Also inspect `GET https://messaging.twilio.com/v1/Services/{ServiceSid}/AlphaSenders` → `alpha_sender`, `capabilities`. There is no REST resource listing which sender IDs are *registered* per country.
- **repair** — Submit the Alphanumeric Sender ID registration form per destination country (Console → Messaging → Senders → Alphanumeric Sender IDs), then `POST https://messaging.twilio.com/v1/Services/{ServiceSid}/AlphaSenders` with `AlphaSender=…`. Ensure `From` matches the registered string exactly, including case.
- **category** — Regulatory & geo
- **sources** — https://www.twilio.com/docs/api/errors/30041 · https://www.twilio.com/docs/api/errors/30040

## shortcode-cross-border-sender-mismatch

- **title** — Short code used outside its own country fails 21612 or 21606
- **symptom** — `21612` ("Message cannot be sent with the current combination of 'To' and/or 'From' parameters") or `21606` on a short code that works perfectly for domestic traffic. Also hits MMS attempts from short codes on carriers that do not support it.
- **mechanism** — Short codes are licensed nationally: a US short code can only message US handsets. A Messaging Service whose pool mixes a short code with long codes will happily select the short code for an international destination. Short codes are also entirely outside A2P 10DLC — they need no brand or campaign — so teams that add a short code to a registered service assume the service's approval covers everything and are surprised when the geographic constraint bites instead.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/SMS/ShortCodes.json` → enumerate `short_code`, `sid`, `sms_url`, `api_version`. Then `GET /2010-04-01/Accounts/{AccountSid}/Messages.json?DateSent>=…` → filter `error_code in {21612, 21606}` and group by `from`. Also `GET https://messaging.twilio.com/v1/Services/{ServiceSid}/ShortCodes` to see which services can select a short code as sender.
- **repair** — Segregate senders by destination country: `DELETE https://messaging.twilio.com/v1/Services/{ServiceSid}/ShortCodes/{Sid}` from the mixed pool, and route international traffic through a separate Messaging Service with long codes or a registered alphanumeric sender.
- **category** — Regulatory & geo
- **sources** — https://www.twilio.com/docs/messaging/api/short-code-resource · https://www.twilio.com/docs/api/errors/21612

## emergency-address-unregistered

- **title** — US/CA numbers have no registered E911 emergency address
- **symptom** — No error until someone dials 911: the call routes to a national call centre and Twilio passes through a $75 per-call fee.
- **mechanism** — `emergency_address_sid` is optional at purchase, so numbers ship without one. Without an MSAG-validated address the number cannot deliver location to a PSAP, and the registration itself can fail asynchronously without anyone noticing.
- **detect** — `GET /2010-04-01/Accounts/{AccountSid}/IncomingPhoneNumbers.json` → `emergency_address_sid` null, or `emergency_address_status` in `{unregistered, registration-failure, pending-registration}`, for `+1` numbers where `capabilities.voice == true`.
- **repair** — `POST /2010-04-01/Accounts/{AccountSid}/Addresses.json` with `EmergencyEnabled=true`, then `POST …/IncomingPhoneNumbers/{PNSid}.json` with `EmergencyAddressSid=AD…&EmergencyStatus=Active`.
- **category** — Regulatory & geo
- **sources** — https://www.twilio.com/docs/voice/tutorials/emergency-calling-for-programmable-voice · https://support.twilio.com/hc/en-us/articles/14034822575003-E911-Address-Enablement-using-The-Twilio-REST-API
