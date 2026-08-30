# Slack app integration failures a read-only script can detect

**109 distinct problems**, every one detectable through the Slack Web API using a token that holds only read scopes. Grouped into nine categories.

Each entry carries eight fields: `slug`, `title`, `symptom`, `mechanism`, `detect` (the exact read-only call and the field or header to inspect), `repair` (printed, never executed), `category`, `sources`.

**Scope rule applied throughout:** a problem is included only if a script holding a read-scoped Slack token can *detect* it via the Web API. App-side faults — a handler that never verifies `X-Slack-Signature`, for example — appear only where they have an API-visible symptom, and the detection described is that symptom.

Research date: 2026-08-30. Reference token scope set assumed by the detections below:

```
channels:read  groups:read  im:read  mpim:read  channels:history
users:read     users:read.email  team:read  files:read  emoji:read
usergroups:read  reactions:read  pins:read  links:read  bookmarks:read
```

Optional extras that unlock whole categories, listed per entry where needed:
`admin.apps:read`, `admin.conversations:read`, `admin.teams:read`, `admin.users:read` (user token, Enterprise Grid);
`authorizations:read` and `connections:write` (app-level `xapp-` token);
`app_configurations:read` (app configuration token, for manifest reads).

---

## The single most important structural fact

**Slack answers almost every failure with HTTP 200.** A request that is unauthenticated, unscoped, rate-limited, aimed at a deleted channel, or carrying malformed Block Kit still comes back `200 OK`, with the failure carried in the JSON body as `{"ok": false, "error": "..."}`. Only a handful of surfaces break this pattern — incoming webhooks return real 4xx/5xx with a plain-text body, and rate limiting sometimes surfaces as a true `429` with `Retry-After`.

Every HTTP client library on earth defaults to "200 means it worked." That mismatch is the root of an enormous share of Slack integration bugs, and it is the first thing a detector should check. See [`http-200-ok-false`](#http-200-ok-false).

---

## Scope and known blind spots

The Web API is a workspace-state API, not an application-introspection API. These things are genuinely invisible to a read-only token, and no amount of cleverness recovers them:

1. **Request signature verification.** Whether your handler computes `v0=HMAC-SHA256(signing_secret, "v0:" + timestamp + ":" + body)` and compares it in constant time, whether it enforces the five-minute timestamp window, or whether it verifies at all, is entirely inside your process. Slack never reports it. The only API-visible shadow is the *absence* of a symptom: an app whose Request URL is configured and whose event subscriptions have not been auto-disabled is at least returning 2xx — it says nothing about whether it verified anything first. Treat signature verification as a source-review item, not a detector item.

2. **The signing secret and client secret values themselves.** No read method returns them, and no method reports whether they were rotated, committed to a repository, or shared. `apps.manifest.export` returns the manifest, not credentials.

3. **What your event handler actually does with an event.** Delivery is observable in aggregate (Slack disables subscriptions after sustained failure), but per-event outcomes are not. A handler that returns `200 OK` and then silently drops the payload is indistinguishable, from Slack's side, from one that processed it perfectly. Duplicate processing driven by `X-Slack-Retry-Num` is likewise only visible if the duplicates reach the workspace as duplicate messages.

4. **Your app's Request URL, Interactivity URL, and slash-command URLs.** These live in app configuration. A *bot* token cannot read them. They become readable only with an **app configuration token** and `apps.manifest.export` — a different credential class that a runtime bot token does not have. Detections that depend on the manifest are marked as such; without that token they are unavailable.

5. **The full granted scope list for scopes the token cannot exercise.** `X-OAuth-Scopes` is reliable, but there is no method that returns "the scopes this app *requested* at install versus the ones the admin approved." You see what was granted, not the gap against what was asked for.

6. **Per-channel posting history and quota state.** There is no method that reports "you are currently at 0.9 requests/second against `chat.postMessage` in C123." Rate-limit posture is inferred from headers on live calls, never queried.

7. **Anything about users or channels the token cannot see.** A bot with `channels:read` but not `groups:read` cannot enumerate private channels — so it cannot distinguish "this private channel does not exist" from "I am not allowed to know." `channel_not_found` is genuinely ambiguous, and every private-channel detection below inherits that ambiguity.

8. **Workflow Builder internals.** Since the September 2024 retirement of legacy Steps from Apps there is no read API that enumerates which Workflow Builder workflows call your app's steps or how often they fail.

9. **Socket Mode connection health.** `apps.connections.open` is a *write* method (it mints a URL). A read-only script can confirm that Socket Mode is viable by checking the app-level token's scopes, but cannot open a socket to observe `refresh_requested` / `link_disabled` frames, nor count how many of the 10 permitted connections are live.

---

## Table of contents

| # | Category | Count |
| --- | --- | --- |
| 1 | [Scopes and tokens](#scopes-and-tokens) | 15 |
| 2 | [Channels and membership](#channels-and-membership) | 14 |
| 3 | [Rate limits](#rate-limits) | 11 |
| 4 | [Events and request URLs](#events-and-request-urls) | 12 |
| 5 | [Messaging and Block Kit](#messaging-and-block-kit) | 16 |
| 6 | [Files and uploads](#files-and-uploads) | 9 |
| 7 | [Socket Mode and connections](#socket-mode-and-connections) | 8 |
| 8 | [App configuration and manifests](#app-configuration-and-manifests) | 13 |
| 9 | [Enterprise Grid and admin](#enterprise-grid-and-admin) | 11 |
| | **Total** | **109** |

### Scopes and tokens

1. [`http-200-ok-false`](#http-200-ok-false) — Every failure arrives as HTTP 200 and is read as success
2. [`missing-scope-on-read`](#missing-scope-on-read) — A read call dies on missing_scope with needed and provided
3. [`bot-vs-user-scope-mixup`](#bot-vs-user-scope-mixup) — The scope was granted to the user token, not the bot
4. [`token-revoked`](#token-revoked) — token_revoked: the app was uninstalled from the workspace
5. [`account-inactive`](#account-inactive) — account_inactive after the installing user was deactivated
6. [`token-expired-rotation`](#token-expired-rotation) — Rotation is on and the 12-hour token expired unrefreshed
7. [`refresh-token-reused`](#refresh-token-reused) — A single-use refresh token was replayed and revoked
8. [`invalid-auth-wrong-token-type`](#invalid-auth-wrong-token-type) — invalid_auth from using an xapp- token on the Web API
9. [`not-allowed-token-type`](#not-allowed-token-type) — not_allowed_token_type: right secret, wrong token class
10. [`classic-app-coarse-scopes`](#classic-app-coarse-scopes) — A classic app holds bot/client/read, not granular scopes
11. [`over-broad-scopes`](#over-broad-scopes) — The token carries admin and write scopes it never uses
12. [`users-read-email-missing`](#users-read-email-missing) — Every user profile has a null email and nobody noticed
13. [`app-level-token-missing-connections-write`](#app-level-token-missing-connections-write) — The xapp- token lacks connections:write for Socket Mode
14. [`authorizations-read-missing`](#authorizations-read-missing) — authorizations:read absent, so multi-install events are wrong
15. [`config-token-expired`](#config-token-expired) — The app configuration token expired after 12 hours

### Channels and membership

16. [`bot-not-in-channel`](#bot-not-in-channel) — not_in_channel: the bot was never invited to the channel
17. [`channel-name-instead-of-id`](#channel-name-instead-of-id) — A channel name is passed where an ID is required
18. [`archived-channel-target`](#archived-channel-target) — is_archived: the target channel was archived months ago
19. [`private-channel-invisible`](#private-channel-invisible) — channel_not_found because groups:read was never granted
20. [`channel-renamed-hardcoded`](#channel-renamed-hardcoded) — A hardcoded #channel name no longer resolves after a rename
21. [`channel-converted-to-private`](#channel-converted-to-private) — A public channel went private and the bot lost access
22. [`membership-lost-silently`](#membership-lost-silently) — Someone removed the bot and posting stopped without an alert
23. [`dm-never-opened`](#dm-never-opened) — DMs fail because no IM conversation was ever opened
24. [`dm-to-deactivated-user`](#dm-to-deactivated-user) — Messages are sent into DMs with deactivated accounts
25. [`general-channel-restricted`](#general-channel-restricted) — posting_to_general_channel_denied on the default channel
26. [`read-only-channel`](#read-only-channel) — restricted_action_read_only_channel: admins locked the channel
27. [`thread-only-or-non-threadable`](#thread-only-or-non-threadable) — Top-level or threaded posts are refused by channel policy
28. [`slack-connect-external-channel`](#slack-connect-external-channel) — The channel is externally shared and posts leak outside the org
29. [`bot-in-too-many-channels`](#bot-in-too-many-channels) — The bot joined thousands of channels and every scan times out

### Rate limits

30. [`ratelimited-retry-after-ignored`](#ratelimited-retry-after-ignored) — ratelimited returned and Retry-After was never honored
31. [`non-marketplace-history-clamp`](#non-marketplace-history-clamp) — conversations.history clamped to 1/min and 15 objects
32. [`postmessage-one-per-second`](#postmessage-one-per-second) — chat.postMessage bursts past one message per second per channel
33. [`tier1-method-hammered`](#tier1-method-hammered) — A Tier 1 method is polled far above 1+ per minute
34. [`invalid-limit`](#invalid-limit) — invalid_limit from asking for more than 1000 per page
35. [`pagination-not-followed`](#pagination-not-followed) — next_cursor is ignored so only the first page is ever seen
36. [`invalid-cursor`](#invalid-cursor) — invalid_cursor: a stored cursor was replayed after expiry
37. [`parallel-workers-share-quota`](#parallel-workers-share-quota) — Concurrent workers share one per-method quota and starve
38. [`message-limit-exceeded`](#message-limit-exceeded) — message_limit_exceeded: the workspace posting cap was hit
39. [`accesslimited-ip-allowlist`](#accesslimited-ip-allowlist) — accesslimited: the caller IP is outside the allowed range
40. [`retry-storm-from-event-retries`](#retry-storm-from-event-retries) — Event retries multiply API calls into a self-inflicted 429

### Events and request URLs

41. [`request-url-unverified`](#request-url-unverified) — The Request URL never passed the url_verification challenge
42. [`event-subscriptions-auto-disabled`](#event-subscriptions-auto-disabled) — Slack disabled event delivery after sustained 5xx
43. [`three-second-timeout`](#three-second-timeout) — Handlers exceed 3 seconds and every event is retried
44. [`duplicate-processing-on-retry`](#duplicate-processing-on-retry) — X-Slack-Retry-Num retries produce duplicate side effects
45. [`no-event-subscriptions`](#no-event-subscriptions) — The app subscribes to zero events and reacts to nothing
46. [`event-scope-mismatch`](#event-scope-mismatch) — A subscribed event needs a scope the token never got
47. [`bot-message-echo-loop`](#bot-message-echo-loop) — The bot answers its own messages in an endless loop
48. [`message-subtypes-ignored`](#message-subtypes-ignored) — Edits, deletes and joins are processed as new messages
49. [`app-mention-vs-message-double-fire`](#app-mention-vs-message-double-fire) — Both message.channels and app_mention fire, doubling replies
50. [`http-or-dead-tunnel-request-url`](#http-or-dead-tunnel-request-url) — The Request URL is http:// or a dead ngrok tunnel
51. [`multi-install-authorizations`](#multi-install-authorizations) — One event serves many installs and only one is handled
52. [`rtm-legacy-still-used`](#rtm-legacy-still-used) — The app still runs on the retired RTM API

### Messaging and Block Kit

53. [`invalid-blocks`](#invalid-blocks) — invalid_blocks: the Block Kit payload failed validation
54. [`msg-blocks-too-long`](#msg-blocks-too-long) — More than 50 blocks in one message
55. [`blocks-without-text-fallback`](#blocks-without-text-fallback) — Blocks with no text fallback, so notifications are blank
56. [`text-length-limits`](#text-length-limits) — A section text object exceeds 3000 characters
57. [`too-many-attachments`](#too-many-attachments) — More than 100 attachments on a single message
58. [`no-text-empty-message`](#no-text-empty-message) — no_text: an empty message body was posted
59. [`cannot-reply-to-message`](#cannot-reply-to-message) — cannot_reply_to_message: threading onto a non-threadable post
60. [`thread-ts-is-a-reply`](#thread-ts-is-a-reply) — A reply ts is used as thread_ts, flattening the thread
61. [`chat-update-message-not-found`](#chat-update-message-not-found) — message_not_found: the ts being updated no longer exists
62. [`cant-update-or-delete-message`](#cant-update-or-delete-message) — cant_update_message: the message belongs to another author
63. [`ephemeral-user-not-in-channel`](#ephemeral-user-not-in-channel) — user_not_in_channel: ephemeral posts to a non-member
64. [`scheduled-message-in-past`](#scheduled-message-in-past) — time_in_past: scheduled sends land behind the clock
65. [`scheduled-messages-orphaned`](#scheduled-messages-orphaned) — Hundreds of scheduled messages queued and forgotten
66. [`unfurl-domain-not-configured`](#unfurl-domain-not-configured) — Links never unfurl because no domain is registered
67. [`trigger-id-expired`](#trigger-id-expired) — expired_trigger_id: the modal opened too late
68. [`duplicate-messages-no-dedupe`](#duplicate-messages-no-dedupe) — The same message is posted repeatedly with no idempotency

### Files and uploads

69. [`files-upload-retired`](#files-upload-retired) — The retired files.upload method is still being called
70. [`incomplete-external-upload`](#incomplete-external-upload) — getUploadURLExternal was never completed, orphaning files
71. [`file-not-shared-to-channel`](#file-not-shared-to-channel) — Files upload successfully but appear in no channel
72. [`file-not-visible`](#file-not-visible) — not_visible: the token cannot see a file it uploaded
73. [`file-deleted-link-rot`](#file-deleted-link-rot) — file_deleted: stored file IDs point at deleted files
74. [`file-download-without-auth`](#file-download-without-auth) — Downloading url_private without a bearer header yields HTML
75. [`public-file-links-exposed`](#public-file-links-exposed) — Files were made public and are readable without Slack
76. [`file-size-limit`](#file-size-limit) — Uploads over the 1 GB per-file ceiling are rejected
77. [`file-retention-deletes-history`](#file-retention-deletes-history) — Workspace retention deletes files the app still references

### Socket Mode and connections

78. [`socket-mode-and-request-url-both-on`](#socket-mode-and-request-url-both-on) — Socket Mode and an HTTP Request URL are both configured
79. [`socket-mode-blocks-distribution`](#socket-mode-blocks-distribution) — A Socket Mode app cannot be listed on the Marketplace
80. [`connections-open-unusable`](#connections-open-unusable) — apps.connections.open is unusable with the token on hand
81. [`socket-connection-cap`](#socket-connection-cap) — More than 10 concurrent Socket Mode connections
82. [`refresh-requested-unhandled`](#refresh-requested-unhandled) — refresh_requested disconnects are treated as crashes
83. [`socket-mode-single-instance`](#socket-mode-single-instance) — Multiple replicas each open a socket and duplicate work
84. [`socket-mode-off-but-no-request-url`](#socket-mode-off-but-no-request-url) — Socket Mode is off and no Request URL replaced it
85. [`interactivity-not-enabled`](#interactivity-not-enabled) — Buttons render but no interaction payload is ever delivered

### App configuration and manifests

86. [`manifest-drift`](#manifest-drift) — The deployed manifest differs from the one in the repo
87. [`app-not-distributed`](#app-not-distributed) — The app is single-workspace and cannot be installed elsewhere
88. [`oauth-redirect-mismatch`](#oauth-redirect-mismatch) — bad_redirect_uri: the callback URL is not on the allow list
89. [`app-access-restricted`](#app-access-restricted) — app_access_restricted: an admin blocked the app for this user
90. [`messages-tab-disabled`](#messages-tab-disabled) — messages_tab_disabled: the App Home DM surface is off
91. [`slash-command-not-registered`](#slash-command-not-registered) — A slash command in the code was never registered
92. [`incoming-webhook-dead`](#incoming-webhook-dead) — no_service: the incoming webhook was removed or disabled
93. [`webhook-locked-to-one-channel`](#webhook-locked-to-one-channel) — The webhook posts to one fixed channel regardless of payload
94. [`webhook-invalid-payload`](#webhook-invalid-payload) — invalid_payload: the webhook body is malformed JSON
95. [`legacy-workflow-steps`](#legacy-workflow-steps) — The app still ships retired Steps from Apps
96. [`deprecated-method-in-use`](#deprecated-method-in-use) — method_deprecated on a legacy channels.* or groups.* call
97. [`app-home-tab-disabled`](#app-home-tab-disabled) — The Home tab is published to but not enabled
98. [`app-uninstalled-orphan-install-record`](#app-uninstalled-orphan-install-record) — The installation store keeps rows for uninstalled workspaces

### Enterprise Grid and admin

99. [`workspace-token-in-grid`](#workspace-token-in-grid) — team_access_not_granted: the token is scoped to one workspace
100. [`org-wide-install-mishandled`](#org-wide-install-mishandled) — is_enterprise_install is true and team_id lookups break
101. [`enterprise-is-restricted`](#enterprise-is-restricted) — enterprise_is_restricted: the method is barred on Grid
102. [`org-login-required`](#org-login-required) — org_login_required during an Enterprise migration
103. [`team-added-to-org`](#team-added-to-org) — team_added_to_org: the workspace is mid-migration to Grid
104. [`admin-method-needs-user-token`](#admin-method-needs-user-token) — admin.* calls fail because a bot token was used
105. [`not-an-admin`](#not-an-admin) — not_an_admin: the installing user is not an org admin
106. [`feature-not-enabled`](#feature-not-enabled) — feature_not_enabled: admin APIs require an Enterprise plan
107. [`app-restricted-by-admin`](#app-restricted-by-admin) — The app sits on the org restricted list, not the approved one
108. [`ekm-access-denied`](#ekm-access-denied) — ekm_access_denied: Enterprise Key Management blocked the write
109. [`enterprise-id-not-stored`](#enterprise-id-not-stored) — Installs are keyed on team_id alone and collide across the org

---

# Scopes and tokens

## http-200-ok-false

- **slug**: `http-200-ok-false`
- **title**: Every failure arrives as HTTP 200 and is read as success
- **symptom**: The deploy is green, the logs say `POST https://slack.com/api/chat.postMessage 200`, and nothing ever appears in Slack. Nobody notices for weeks. When someone finally logs the body, it reads `{"ok": false, "error": "not_in_channel"}` — and has done for the entire time.
- **mechanism**: Slack's Web API is an RPC layer over HTTP that reserves non-2xx status codes for transport-level problems. Application-level failures — bad auth, missing scopes, missing channels, malformed blocks — are all returned inside a `200 OK` body. Every HTTP client in common use (`requests`, `axios`, `fetch` with `res.ok`, `HttpClient.EnsureSuccessStatusCode`) treats 200 as unconditional success, so the error never raises. The official SDKs (`@slack/web-api`, `slack_sdk`) *do* throw on `ok: false`, which is precisely why hand-rolled clients fail here and SDK users do not.
- **detect**: Make any read call — `GET https://slack.com/api/auth.test` with `Authorization: Bearer <token>` — and assert on the JSON body, not the status line. The rule for the whole audit: **`response.status == 200` proves nothing; `body.ok === true` is the only success signal.** For every method the script probes, record `body.ok`, `body.error`, `body.needed`, `body.provided`, `body.warning`, and `body.response_metadata.warnings[]`. `body.warning` in particular carries non-fatal notices like `missing_charset` and `superfluous_charset` that are invisible if you only read `ok`.
- **repair**: Wrap the transport so every Slack call raises on `ok !== true`. In Node: `const r = await fetch(...); const j = await r.json(); if (!j.ok) throw new Error("slack:" + j.error);`. Better: adopt the official SDK (`@slack/web-api` `WebClient`, or `slack_sdk.WebClient`), which raises `SlackApiError` / `WebClientError` automatically and exposes `e.data.error`. Then log `body.warning` at WARN level so charset and deprecation notices surface.
- **category**: Scopes and tokens
- **sources**: https://docs.slack.dev/apis/web-api/ · https://stackoverflow.com/questions/40986822 · https://docs.slack.dev/reference/methods/chat.postMessage

## missing-scope-on-read

- **slug**: `missing-scope-on-read`
- **title**: A read call dies on missing_scope with needed and provided
- **symptom**: `{"ok": false, "error": "missing_scope", "needed": "channels:history", "provided": "chat:write,commands,users:read"}`. The developer swears they added the scope in the app config — and they did, but the app was never reinstalled, so the issued token still carries the old grant.
- **mechanism**: A Slack token is a frozen snapshot of the scopes granted at the moment of installation. Editing the scope list in the app configuration changes what will be *requested* at the next install; it does not upgrade tokens already in circulation. Until an admin runs the install flow again, the old token keeps its old `X-OAuth-Scopes`. This is the single most-repeated Slack question on Stack Overflow after `not_in_channel`.
- **detect**: Two complementary probes. (1) Cheap and exact: read the `X-OAuth-Scopes` response header on *any* Web API response — Slack returns the calling token's complete current scope list there on every request. Diff it against the set of scopes your app's methods require. (2) Empirical: call each read method the app depends on with a harmless argument and inspect `body.error === "missing_scope"`, then read `body.needed` (comma-separated scopes that would satisfy the call) and `body.provided` (what the token actually has). `needed` is an OR-list, not an AND-list — any one of them suffices.
- **repair**: Add the scope under **OAuth & Permissions → Scopes → Bot Token Scopes** (or **User Token Scopes**), then **reinstall the app to the workspace** and replace the stored token. In a manifest-managed app, add it to `oauth_config.scopes.bot` and re-deploy the manifest before reinstalling. For distributed apps, every existing installation must re-authorize; ship a re-consent prompt rather than assuming installs upgrade themselves.
- **category**: Scopes and tokens
- **sources**: https://stackoverflow.com/questions/44048855 · https://stackoverflow.com/questions/56696117 · https://docs.slack.dev/reference/scopes/

## bot-vs-user-scope-mixup

- **slug**: `bot-vs-user-scope-mixup`
- **title**: The scope was granted to the user token, not the bot
- **symptom**: The OAuth screen showed the scope, the admin approved it, and the call still returns `missing_scope`. Checking the app config shows the scope listed — under **User Token Scopes**, while the code is authenticating with the `xoxb-` bot token.
- **mechanism**: Slack maintains two independent scope lists per app. Bot Token Scopes attach to the `xoxb-` token and act as the app; User Token Scopes attach to the `xoxp-` token and act as the installing human. They are granted in the same consent screen and stored in the same OAuth response (`access_token` vs `authed_user.access_token`), which makes it very easy to add a scope to one list and read with the other. Some scopes exist only on one side: `search:read` and `users.profile:write` are user-only; `app_mentions:read` and `commands` are bot-only.
- **detect**: Call `auth.test` with each stored token. A bot token returns a `bot_id` field and a `user_id` beginning `U`/`W` that is the *bot user*; a user token returns no `bot_id`. Then read `X-OAuth-Scopes` on that same response — that is the scope set for *that* token. If the scope you need appears on the user token's header and your runtime code path uses the bot token (or vice versa), you have the mixup. Cross-check by calling the target method once with each token and comparing which one avoids `missing_scope`.
- **repair**: Decide which identity should perform the action. If the app should act as itself, move the scope to **Bot Token Scopes** and reinstall. If it must act as a human (searching messages, editing a user's profile), keep it under **User Token Scopes** and change the code to authenticate with `authed_user.access_token`. Store the two tokens under distinct keys — never a single `SLACK_TOKEN` env var — so the choice is explicit at every call site.
- **category**: Scopes and tokens
- **sources**: https://stackoverflow.com/questions/55506352 · https://stackoverflow.com/questions/47914487 · https://docs.slack.dev/authentication/tokens

## token-revoked

- **slug**: `token-revoked`
- **title**: token_revoked: the app was uninstalled from the workspace
- **symptom**: One tenant of a multi-workspace app stops receiving anything. Every call for that workspace returns `{"ok": false, "error": "token_revoked"}` and the installation row still sits happily in the database marked active.
- **mechanism**: An admin removed the app from **Manage apps**, or a user revoked their own authorization, or the workspace was deleted. Slack invalidates the token immediately and emits an `app_uninstalled` / `tokens_revoked` event — which the app may not have subscribed to, or may have dropped. Nothing else changes; the stored token simply becomes a dead string.
- **detect**: Iterate the installation store and call `auth.test` per token. `body.error === "token_revoked"` (user tokens and app removal) or `token_revoked` on a bot token means the grant is gone. Distinguish from `account_inactive`, which means the *user or workspace* was deactivated rather than the app removed. A healthy install returns `ok: true` plus `team_id`.
- **repair**: Delete or tombstone the installation record and stop scheduling work for that workspace. Subscribe to the `app_uninstalled` and `tokens_revoked` events so the store self-heals, and handle them in the same code path your audit uses. Do not retry a revoked token — it never recovers; only a fresh OAuth install produces a working one.
- **category**: Scopes and tokens
- **sources**: https://docs.slack.dev/reference/methods/auth.test · https://docs.slack.dev/reference/events/tokens_revoked · https://stackoverflow.com/questions/72892299

## account-inactive

- **slug**: `account-inactive`
- **title**: account_inactive after the installing user was deactivated
- **symptom**: A long-running integration dies the week someone leaves the company. Errors read `{"ok": false, "error": "account_inactive"}` and the app still shows as installed in the workspace.
- **mechanism**: A **user** token is bound to a human account. When that account is deactivated — offboarding, SSO deprovisioning, SCIM sync — the token stops working even though the app installation survives. This is the specific failure mode that makes user tokens unsuitable for unattended automation. Bot tokens are immune to the installer leaving, which is why Slack recommends them for anything that must outlive a person.
- **detect**: `auth.test` per stored token → `body.error === "account_inactive"`. To find installs *at risk* before they break, take each installation's `authed_user.id`, call `users.info?user=<id>` with a `users:read` token, and check `user.deleted === true` — or list all members via `users.list` and build a set of `deleted` ids to join against your install table.
- **repair**: Migrate the automation to a bot token (`xoxb-`) with the equivalent bot scopes; a bot token survives the installer's departure. If a user token is genuinely required (message search, acting-as-user posts), designate a service account that is exempt from offboarding, document it, and monitor `users.info` for its `deleted` flag.
- **category**: Scopes and tokens
- **sources**: https://stackoverflow.com/questions/72892299 · https://docs.slack.dev/authentication/tokens · https://docs.slack.dev/reference/methods/users.info

## token-expired-rotation

- **slug**: `token-expired-rotation`
- **title**: Rotation is on and the 12-hour token expired unrefreshed
- **symptom**: The app works perfectly for half a day after each deploy, then every call returns `{"ok": false, "error": "token_expired"}` until someone restarts it. A cron job that redeploys nightly masks the problem for months.
- **mechanism**: Token rotation was enabled on the app (deliberately, or by adopting a manifest with `token_rotation_enabled: true`). Rotated access tokens carry the `xoxe.xoxb-` / `xoxe.xoxp-` prefix and expire after exactly `expires_in: 43200` seconds — 12 hours. The install flow returns a companion `xoxe-1-...` refresh token, and the app is expected to call `oauth.v2.access` with `grant_type=refresh_token` before expiry. Rotation **cannot be turned off once turned on**, so an app that opted in without building the refresh loop is permanently broken on a 12-hour cycle.
- **detect**: Inspect the stored token string: a `xoxe.` prefix means rotation is on. Call `auth.test` — a rotated token that is still valid returns `ok: true`; an expired one returns `body.error === "token_expired"`. If your store recorded the OAuth response, check for a non-null `expires_in` (always 43200) and a `refresh_token` field; their presence with no scheduled refresh job is the finding. Reading the manifest with an app configuration token via `apps.manifest.export` shows `settings.token_rotation_enabled`.
- **repair**: Implement the refresh loop: `POST https://slack.com/api/oauth.v2.access` with `client_id`, `client_secret`, `grant_type=refresh_token`, `refresh_token=<xoxe-1-...>`. Persist **both** returned values — the new access token and the new refresh token — atomically, and schedule the refresh at roughly `expires_in / 2` rather than at expiry. The official SDKs ship this: Bolt's `installationStore` handles rotation when you pass `tokenRotationEnabled`.
- **category**: Scopes and tokens
- **sources**: https://docs.slack.dev/authentication/using-token-rotation · https://docs.slack.dev/reference/methods/oauth.v2.access · https://docs.slack.dev/reference/methods/oauth.v2.exchange

## refresh-token-reused

- **slug**: `refresh-token-reused`
- **title**: A single-use refresh token was replayed and revoked
- **symptom**: Rotation works for a while, then breaks hard: `token_expired` on the access token and `invalid_refresh_token` (or `invalid_auth`) on the refresh attempt. It correlates with running two replicas, or with a retry after a timeout.
- **mechanism**: Slack refresh tokens are **single-use**. Each successful refresh returns a *new* refresh token and starts revoking the old one after a short grace period. Two workers refreshing concurrently, or a retry after a request that actually succeeded but whose response was lost, both burn the token twice. Slack additionally enforces a **2 active token limit** — refreshing repeatedly inside one 12-hour window revokes the older excess tokens, which looks identical to random logouts.
- **detect**: `auth.test` returns `token_expired` while the stored `refresh_token` no longer produces a working token. Correlate by counting distinct refresh attempts per installation in your own logs against the 12-hour window; more than two per window is over the limit. From the API side the observable is simply: stored access token invalid **and** stored refresh token no longer redeemable — a state distinguishable from `token_revoked` (uninstall) because the app still appears installed and other installs are healthy.
- **repair**: Serialize refreshes behind a per-installation lock (a database row lock or a distributed lock), write the new pair inside the same transaction that reads the old one, and make the refresh call idempotent by checking whether another worker already wrote a fresher token before issuing your own. Never refresh on a fixed cron from multiple replicas. If the refresh token is already dead, the only recovery is a fresh OAuth install.
- **category**: Scopes and tokens
- **sources**: https://docs.slack.dev/authentication/using-token-rotation · https://docs.slack.dev/reference/methods/oauth.v2.access

## invalid-auth-wrong-token-type

- **slug**: `invalid-auth-wrong-token-type`
- **title**: invalid_auth from using an xapp- token on the Web API
- **symptom**: `{"ok": false, "error": "invalid_auth"}` on a call that plainly should work, with a token the developer just copied out of the app config. The token starts with `xapp-`.
- **mechanism**: Slack issues at least six token classes with different prefixes and different accepted surfaces: `xoxb-` (bot), `xoxp-` (user), `xapp-` (app-level, for `apps.connections.open` and `apps.event.authorizations.list` only), `xoxe-`/`xoxe.` (rotation), `xwfp-` (workflow, 15-minute life), and app configuration tokens (manifest APIs only). The Basic Information page and the OAuth page both display tokens, and picking the wrong one produces `invalid_auth` rather than anything descriptive. A related variant: `xoxc-` browser session tokens scraped from the Slack web client work briefly and are entirely unsupported.
- **detect**: Read the prefix of every configured token before doing anything else, then call `auth.test`. `auth.test` succeeds for `xoxb-`/`xoxp-` and returns `team_id` + `user_id`; it fails with `invalid_auth` or `not_allowed_token_type` for `xapp-`. Assert the prefix matches the intended role: the Socket Mode credential must be `xapp-`, the Web API credential must be `xoxb-` or `xoxp-`, and anything else is a misconfiguration.
- **repair**: Take the bot token from **OAuth & Permissions → Bot User OAuth Token** (`xoxb-`) for Web API calls, and the app-level token from **Basic Information → App-Level Tokens** (`xapp-`) for Socket Mode. Name the environment variables for their role — `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` — and validate the prefix at process startup so a swap fails loudly instead of at 3am.
- **category**: Scopes and tokens
- **sources**: https://stackoverflow.com/questions/51618547 · https://docs.slack.dev/authentication/tokens · https://stackoverflow.com/questions/62759949

## not-allowed-token-type

- **slug**: `not-allowed-token-type`
- **title**: not_allowed_token_type: right secret, wrong token class
- **symptom**: `{"ok": false, "error": "not_allowed_token_type"}` — a distinct and more specific error than `invalid_auth`. The token authenticates fine elsewhere; this particular method refuses it.
- **mechanism**: Many methods accept only one token class. `admin.*` methods require a **user** token from an org owner or admin and reject `xoxb-` outright. `apps.event.authorizations.list` requires an **app-level** token *passed in the Authorization header* and rejects it as a POST parameter. `chat.postMessage` with message `metadata` requires an app-level token. Legacy `as_user` behavior differs between token classes. The error tells you the class is wrong without telling you which class is right.
- **detect**: For each method the app uses, call it with the token you actually deploy and check `body.error === "not_allowed_token_type"`. Then call `auth.test` on that same token to establish its class (`bot_id` present → bot token; no `bot_id` → user token; `auth.test` failure with an `xapp-` prefix → app-level). The pairing of "method rejects the class" plus "auth.test says which class it is" localizes the fix exactly.
- **repair**: Consult the method's reference page for the accepted token type and switch credentials. In practice: `admin.*` → user token held by an org admin with the matching `admin.*:read`/`:write` scope; `apps.connections.open` and `apps.event.authorizations.list` → `xapp-` app-level token sent as `Authorization: Bearer xapp-...`; everything else → `xoxb-`.
- **category**: Scopes and tokens
- **sources**: https://stackoverflow.com/questions/71409815 · https://stackoverflow.com/questions/60539601 · https://docs.slack.dev/reference/methods/apps.event.authorizations.list

## classic-app-coarse-scopes

- **slug**: `classic-app-coarse-scopes`
- **title**: A classic app holds bot/client/read, not granular scopes
- **symptom**: The scope list in `X-OAuth-Scopes` reads `bot,client,identify,post,read` rather than `channels:read,chat:write,...`. Attempts to add a modern granular scope in the app config are refused, and `chat:write:bot` — which the code references — no longer exists.
- **mechanism**: Apps created before the 2020 granular-permissions migration are "classic" apps with coarse, all-or-nothing scopes. They cannot mix classic and granular scopes, and Slack does not upgrade them in place. The migration also retired intermediate scopes like `chat:write:bot` and `chat:write:user` in favor of `chat:write` plus `chat:write.customize`. Classic apps additionally still have access to the RTM API, which is why so many of them are still running on it.
- **detect**: Read `X-OAuth-Scopes` from any Web API response. If it contains any of the bare classic scopes — `bot`, `client`, `read`, `post`, `identify`, `admin` (bare, not `admin.*:read`) — the installation is classic. Corroborate with `auth.test`: classic bot installs return a `bot_id` but the app was created under the old model. Also flag any reference to `chat:write:bot` / `chat:write:user` in `provided`, which indicates a token minted before the split.
- **repair**: Create a **new** Slack app with granular scopes (ideally from a manifest), migrate the code to the `conversations.*` methods and Socket Mode or the Events API, install the new app alongside the old one, cut traffic over, then uninstall the classic app. There is no in-place upgrade path. Replace `chat:write:bot` with `chat:write`, and add `chat:write.customize` only if you override `username` or `icon_emoji`.
- **category**: Scopes and tokens
- **sources**: https://stackoverflow.com/questions/59370449 · https://stackoverflow.com/questions/27833715 · https://docs.slack.dev/reference/scopes/

## over-broad-scopes

- **slug**: `over-broad-scopes`
- **title**: The token carries admin and write scopes it never uses
- **symptom**: Nothing is broken — which is the point. `X-OAuth-Scopes` lists thirty scopes including `admin.users:write`, `files:write`, `chat:write.public` and `users:read.email`, while the app only ever posts a nightly digest to one channel. Every security review flags it and nobody can say which ones are load-bearing.
- **mechanism**: Scopes accrete. A developer adds one to unblock an error, reinstalls, and never removes it. Copy-pasted manifests carry a maximal scope list. Because Slack tokens are long-lived bearer credentials with no per-call attenuation, an over-scoped token that leaks — into a log, a CI variable, a Docker image layer — hands the finder everything the app was ever granted, including the ability to read every message in the workspace if `channels:history` is present.
- **detect**: Read `X-OAuth-Scopes` for the complete granted set. Compare it against the union of scopes actually required by the methods the app calls; any scope in the granted set with no corresponding call site is surplus. High-signal flags for a read-only auditor: presence of any `admin.*` scope on a routine integration; `users:read.email` (PII); `channels:history` / `groups:history` (full message archive); `files:read` combined with `files:write`; `chat:write.public` (post to any public channel without joining).
- **repair**: Prune the scope list in **OAuth & Permissions** down to the minimum, then reinstall — removing a scope also requires reinstallation to take effect on the token. Prefer `chat:write` plus an explicit channel invite over `chat:write.public`. Where the app genuinely needs broad read access, split it into two apps so the high-privilege token has a smaller blast radius and a separate rotation schedule.
- **category**: Scopes and tokens
- **sources**: https://docs.slack.dev/reference/scopes/ · https://stackoverflow.com/questions/52956270

## users-read-email-missing

- **slug**: `users-read-email-missing`
- **title**: Every user profile has a null email and nobody noticed
- **symptom**: The user-sync job runs green every night and writes rows with `email = null`. `users.list` returns `ok: true` and full profiles — with `profile.email` simply absent. Downstream matching against the HR system silently produces zero joins.
- **mechanism**: `users:read` grants profile access but deliberately withholds email addresses; the email field requires the separate `users:read.email` scope. Because the omission is a *missing key* rather than an error, `ok` stays `true` and no exception is raised anywhere. The same pattern applies to `users.lookupByEmail`, which returns `users_not_found` rather than a scope error when the scope is absent.
- **detect**: Call `users.list?limit=200` and count members where `deleted === false && is_bot === false && profile.email` is undefined or null. If that count equals the total human member count, the scope is missing, not the data. Confirm directly by reading `X-OAuth-Scopes` for the presence of `users.profile:read`/`users:read.email`, and by calling `users.lookupByEmail?email=<a known member>` — `missing_scope` or a persistent `users_not_found` for an address you know exists is the tell.
- **repair**: Add `users:read.email` to **Bot Token Scopes**, reinstall, and replace the token. Note that Slack requires a justification for this scope on Marketplace submissions, and some workspaces hide email by admin policy even with the scope — so also assert on a per-user basis rather than assuming the scope alone guarantees a value.
- **category**: Scopes and tokens
- **sources**: https://stackoverflow.com/questions/41564027 · https://stackoverflow.com/questions/29392407 · https://docs.slack.dev/reference/methods/users.list

## app-level-token-missing-connections-write

- **slug**: `app-level-token-missing-connections-write`
- **title**: The xapp- token lacks connections:write for Socket Mode
- **symptom**: The app boots, tries to open its WebSocket, and gets `{"ok": false, "error": "missing_scope"}` from `apps.connections.open`. Bolt logs a connection failure and retries forever; no events are ever received.
- **mechanism**: App-level tokens are created per-scope on the **Basic Information → App-Level Tokens** page. Socket Mode requires `connections:write`; the multi-install helper `apps.event.authorizations.list` requires `authorizations:read`. A token created for one purpose does not carry the other scope, and there is no way to add a scope to an existing app-level token — you generate a new one.
- **detect**: A read-only script cannot call `apps.connections.open` (it mints a connection, so it is a write). Instead, exercise the app-level token against the read method that shares its credential class: `POST https://slack.com/api/apps.event.authorizations.list` with `Authorization: Bearer xapp-...` and a dummy `event_context`. A response of `invalid_event_context` proves the token authenticates; `missing_scope` names the gap; `auth_mismatch` proves the token belongs to a different app. Combined with the manifest's `settings.socket_mode_enabled` (via `apps.manifest.export`), you can assert "Socket Mode is on but the app-level token cannot open connections."
- **repair**: In **Basic Information → App-Level Tokens**, generate a token with both `connections:write` and `authorizations:read` selected, store it as `SLACK_APP_TOKEN`, and restart. Old app-level tokens should be revoked from the same page once traffic has moved.
- **category**: Scopes and tokens
- **sources**: https://docs.slack.dev/apis/events-api/using-socket-mode · https://docs.slack.dev/reference/methods/apps.event.authorizations.list

## authorizations-read-missing

- **slug**: `authorizations-read-missing`
- **title**: authorizations:read absent, so multi-install events are wrong
- **symptom**: A distributed app installed in many workspaces handles each event exactly once — for one installation — and silently drops the others. Customers report "the bot only works for some people."
- **mechanism**: When an event is visible to more than one installation of your app, Slack sends **one** delivery carrying an `event_context` and an `authorizations` array truncated to a single entry, with `is_ext_shared` context omitted. The app is expected to call `apps.event.authorizations.list` with that `event_context` to enumerate all installations that should see the event. Without `authorizations:read` on an app-level token, that call is impossible and the app fans out to exactly one tenant.
- **detect**: Probe `apps.event.authorizations.list` with the app-level token and a placeholder `event_context`. `missing_scope` means the capability is absent; `invalid_event_context` means the scope is present and the token is fine. Combine with evidence that the app is multi-install: `auth.test` succeeding against tokens with different `team_id` values in your installation store, or `is_enterprise_install: true` on any install.
- **repair**: Generate an app-level token with `authorizations:read`, and in the event handler call `apps.event.authorizations.list?event_context=<payload.event_context>`, paginating via `response_metadata.next_cursor`, then process the event once per returned authorization. Single-workspace apps can ignore this entirely — the finding only matters once more than one installation exists.
- **category**: Scopes and tokens
- **sources**: https://docs.slack.dev/reference/methods/apps.event.authorizations.list · https://docs.slack.dev/apis/events-api/

## config-token-expired

- **slug**: `config-token-expired`
- **title**: The app configuration token expired after 12 hours
- **symptom**: The manifest-sync step in CI worked yesterday and fails today with `invalid_auth` or `token_expired` from `apps.manifest.export` / `apps.manifest.update`. Regenerating the token by hand fixes it until tomorrow.
- **mechanism**: App configuration tokens (used only by the `apps.manifest.*` and `tooling.tokens.*` families) are deliberately short-lived. They are issued as an access/refresh pair from the app management page and expire in 12 hours; the refresh token is redeemed via `tooling.tokens.rotate`, which returns a fresh pair. Teams that paste the access token into a CI secret and forget the rotate step get exactly one working day out of it.
- **detect**: Call `apps.manifest.export?app_id=<A...>` with the stored configuration token. `ok: true` means healthy; `token_expired` / `invalid_auth` means the pair needs rotating; `missing_scope` means the token lacks `app_configurations:read`; `app_not_found` or `invalid_app_id` means the token belongs to a different app account. Note the whole manifest-read branch of this audit is unavailable when this check fails — flag it so downstream manifest findings are reported as "not assessed" rather than "clean."
- **repair**: Store the **refresh** token in CI, not the access token, and call `POST https://slack.com/api/tooling.tokens.rotate` with `refresh_token=<...>` at the start of every run; persist the newly returned refresh token back to the secret store, since it is also single-use. Scope the token with `app_configurations:read` for audit-only use and `app_configurations:write` only in the pipeline that actually deploys the manifest. Note that `tooling.tokens.rotate` returns both a new access token and a new refresh token; writing back only one of them breaks the next run.
- **category**: Scopes and tokens
- **sources**: https://docs.slack.dev/reference/methods/apps.manifest.export · https://docs.slack.dev/reference/methods/tooling.tokens.rotate

---

# Channels and membership

## bot-not-in-channel

- **slug**: `bot-not-in-channel`
- **title**: not_in_channel: the bot was never invited to the channel
- **symptom**: `{"ok": false, "error": "not_in_channel"}` from `chat.postMessage`, `conversations.history`, `files.completeUploadExternal` or `conversations.kick`. The app is installed, the token is valid, the channel ID is right — and the bot simply is not a member. This is the single most-asked Slack API question on Stack Overflow, at 90k views.
- **mechanism**: Installing an app to a workspace does not join it to any channel. A bot must be explicitly invited (`/invite @app`) or must call `conversations.join` — which works only for **public** channels. Private channels can never be self-joined; a human must invite the bot. CI pipelines and Terraform-provisioned channels hit this constantly because channel creation and bot invitation are separate steps and only the first is automated.
- **detect**: `auth.test` → take `user_id` (the bot user, `U...`/`W...`). For each channel the app targets, call `conversations.members?channel=<C...>&limit=1000`, paginate `response_metadata.next_cursor`, and check membership. Cheaper for a full sweep: `users.conversations?user=<bot_user_id>&types=public_channel,private_channel,im,mpim&limit=1000` returns every conversation the bot belongs to in one paginated pass — diff the app's configured target channels against that set. Also read `conversations.info?channel=<C...>` and check `channel.is_member`, which reports membership directly for the calling token.
- **repair**: Invite the bot: in Slack, `/invite @YourApp` in the channel, or from the app itself `conversations.join` (public channels only, needs `channels:join`). For an automated pipeline, have the creating user call `conversations.invite` with `users=<bot_user_id>` immediately after `conversations.create`. As a last resort for public channels only, granting `chat:write.public` lets the app post without joining — but it cannot read history that way, so it does not fix `conversations.history`.
- **category**: Channels and membership
- **sources**: https://stackoverflow.com/questions/60198159 · https://github.com/slackapi/slack-github-action/issues/186 · https://docs.slack.dev/reference/methods/conversations.members

## channel-name-instead-of-id

- **slug**: `channel-name-instead-of-id`
- **title**: A channel name is passed where an ID is required
- **symptom**: `{"ok": false, "error": "channel_not_found"}` for a channel that visibly exists. The config says `channel: "#alerts"`. Some methods accept the name and some do not, so it works in one code path and fails in another — `chat.postMessage` tolerates `#alerts` while `files.completeUploadExternal`, `conversations.info` and `conversations.history` demand `C01ABCDE`.
- **mechanism**: Slack's canonical channel identifier is the `C`/`G`/`D` prefixed ID. `chat.postMessage` retains legacy name resolution for compatibility, which trains developers to think names are universal; the `conversations.*` and `files.*` families never accepted them. On Enterprise Grid, passing a name to an org-wide token returns `team_not_found` instead, because the name is ambiguous across workspaces. Channel names also change; IDs never do.
- **detect**: Scan every configured channel value for a leading `#` or for a string that does not match `^[CGD][A-Z0-9]{8,}$`. Then resolve it: paginate `conversations.list?types=public_channel,private_channel&exclude_archived=false&limit=1000` and match on `channel.name`. A configured name with no match is a hard failure; a name with a match is a latent failure waiting for the next rename. Note there is deliberately **no** name→ID lookup method, which is why this keeps happening.
- **repair**: Replace every channel name in configuration with its `id` from `conversations.list`, and keep the human-readable name only as a comment. If names must be supported for usability, resolve them **once at startup** into IDs and cache — resolving per-message means paginating `conversations.list` on every send, which is a Tier 2 method and will rate-limit.
- **category**: Channels and membership
- **sources**: https://github.com/slackapi/python-slack-sdk/issues/1326 · https://stackoverflow.com/questions/53519541 · https://github.com/slackapi/python-slack-sdk/issues/1503

## archived-channel-target

- **slug**: `archived-channel-target`
- **title**: is_archived: the target channel was archived months ago
- **symptom**: `{"ok": false, "error": "is_archived"}` from `chat.postMessage`, or `HTTP 410 Gone` with body `channel_is_archived` from an incoming webhook. Alerts stop arriving and nobody notices because the failure is on the sending side.
- **mechanism**: Archiving a channel makes it read-only forever; it is not deleted, so the ID still resolves and `conversations.info` still succeeds. Teams archive channels during reorganizations without auditing which integrations point at them. Webhooks fail with a real HTTP 410 here, which is one of the rare cases where a non-200 status actually surfaces the problem.
- **detect**: `conversations.info?channel=<C...>` → `channel.is_archived === true`. For a workspace-wide sweep, `conversations.list?exclude_archived=false&types=public_channel,private_channel&limit=1000` and collect every entry with `is_archived: true`, then intersect with your configured target channels. Also check `channel.is_general` on the survivors, which matters for the next entry.
- **repair**: Point the integration at a live channel, or unarchive the original (Slack UI → channel → **Unarchive channel**; there is no bot-callable unarchive for private channels). Add the `is_archived` assertion to your startup health check so an archive shows up as a boot failure rather than as silence.
- **category**: Channels and membership
- **sources**: https://docs.slack.dev/reference/methods/conversations.info · https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks · https://docs.slack.dev/reference/methods/chat.postMessage

## private-channel-invisible

- **slug**: `private-channel-invisible`
- **title**: channel_not_found because groups:read was never granted
- **symptom**: `channel_not_found` for a private channel that the developer is looking at on screen. Public channels work fine. `conversations.list` returns hundreds of channels and none of them is the one in question.
- **mechanism**: Slack splits conversation scopes by type: `channels:read`/`channels:history` cover public channels, `groups:read`/`groups:history` cover private channels, `im:*` covers DMs and `mpim:*` covers group DMs. A token with only the `channels:*` pair cannot see private conversations *at all* — they are not returned by `conversations.list`, and `conversations.info` on one returns `channel_not_found` rather than a permission error. The ambiguity is deliberate: Slack will not confirm that a private channel exists to a token that cannot see it.
- **detect**: Read `X-OAuth-Scopes` and check for `groups:read` (and `groups:history` if the app reads messages). Then call `conversations.list?types=private_channel&limit=1000`: if the scope is missing you get `missing_scope` with `needed: groups:read`; if the scope is present but the bot has not been invited to any private channel you get `ok: true` with an empty `channels` array. Those two outcomes need different repairs, so distinguish them. Finally, `conversations.info` on the specific ID returns `channel_not_found` when either condition holds.
- **repair**: Add `groups:read` (plus `groups:history` for reading, `groups:write` for membership changes) to **Bot Token Scopes** and reinstall. Then have a member of each private channel invite the bot — the scope grants the *ability* to see private channels the bot belongs to, not blanket visibility into all of them.
- **category**: Channels and membership
- **sources**: https://stackoverflow.com/questions/43268678 · https://github.com/slackapi/node-slack-sdk/issues/1124 · https://stackoverflow.com/questions/37690761

## channel-renamed-hardcoded

- **slug**: `channel-renamed-hardcoded`
- **title**: A hardcoded #channel name no longer resolves after a rename
- **symptom**: An integration that ran for two years stops on the day a team renames `#ops-alerts` to `#platform-alerts`. Error: `channel_not_found`. Nothing was deployed; nothing changed on your side.
- **mechanism**: Channel names in Slack are mutable and are not unique over time — the old name is released and can be claimed by a different channel. Any configuration that stores a name rather than an ID is a time bomb. The variant that is worse: someone creates a *new* channel with the old name, so the integration keeps working but starts posting into the wrong room.
- **detect**: For every configured channel name, resolve it against `conversations.list` and record the matching `id`. Then call `conversations.info?channel=<that id>` and compare `channel.name` against the configured string. Two findings fall out: (a) name resolves to nothing → renamed or deleted; (b) name resolves to an ID whose `channel.created` timestamp is much newer than the integration → the name was recycled onto a different channel. `conversations.info` also returns `channel.name_normalized` and `channel.previous_names[]` on some plans, which confirms a rename directly.
- **repair**: Store IDs, not names, in every configuration surface (env vars, Terraform, database rows, YAML). Where a name must remain in the UI for humans, resolve to an ID once and persist the ID alongside it. Add a startup assertion that the stored ID's current `name` still matches the expected label and warn — not fail — when it drifts.
- **category**: Channels and membership
- **sources**: https://docs.slack.dev/reference/methods/conversations.info · https://stackoverflow.com/questions/50106263 · https://stackoverflow.com/questions/40940327

## channel-converted-to-private

- **slug**: `channel-converted-to-private`
- **title**: A public channel went private and the bot lost access
- **symptom**: An integration reading a public channel's history starts returning `channel_not_found` or `not_in_channel`. The channel ID is unchanged and the channel still exists — an admin converted it to private.
- **mechanism**: Converting a public channel to private preserves the channel ID but changes which scopes govern it: reads that were authorized by `channels:read`/`channels:history` now require `groups:read`/`groups:history`. Membership is preserved for humans, and bots that were members stay members — but a bot relying on `chat:write.public` (post without joining) loses access entirely, since that only applies to public channels. The conversion is one-way in the Slack UI.
- **detect**: `conversations.info?channel=<C...>` → compare `channel.is_private`, `channel.is_group` and `channel.is_channel` against what the integration expects. A conversation with `is_private: true` that your configuration treats as public is the finding. Corroborate with `X-OAuth-Scopes`: if `groups:read` is absent, `conversations.info` will instead return `channel_not_found` for that same ID — the transition from "info works" to "info says not found" with no config change is itself the signal.
- **repair**: Add `groups:read` and `groups:history` to the bot's scopes and reinstall, then ensure the bot is an actual member (a human must invite it; private channels cannot be self-joined). If the app relied on `chat:write.public`, that path is gone — membership is now mandatory.
- **category**: Channels and membership
- **sources**: https://docs.slack.dev/reference/methods/conversations.info · https://github.com/slackapi/bolt-js/issues/1656 · https://docs.slack.dev/reference/scopes/

## membership-lost-silently

- **slug**: `membership-lost-silently`
- **title**: Someone removed the bot and posting stopped without an alert
- **symptom**: A daily digest quietly stops appearing. Logs show `not_in_channel` — but only if anyone reads the body, and the process exits 0 either way. Someone cleaned up channel members three weeks ago.
- **mechanism**: Any channel member can remove an app with `/kick @app` or via the channel's integrations panel; no notification goes to the app owner. Slack emits a `member_left_channel` event, but only if the app subscribed to it and only if the app's event delivery is healthy. Combined with [`http-200-ok-false`](#http-200-ok-false), the removal is invisible from both directions.
- **detect**: Run a periodic membership assertion rather than waiting for a send to fail. `users.conversations?user=<bot_user_id>&types=public_channel,private_channel&limit=1000`, paginated, gives the authoritative current set. Diff it against the expected set on every run and report removals. Per-channel, `conversations.info?channel=<C...>` → `channel.is_member === false` is the same finding at finer grain. Store the previous run's set so you can report *when* membership changed, not just that it did.
- **repair**: Re-invite the bot and, more importantly, subscribe to `member_left_channel` and `channel_left` events so the loss raises an alert in real time. Add the membership assertion to the same health check that validates the token, so channel access is verified before the first message of a run rather than discovered by its failure.
- **category**: Channels and membership
- **sources**: https://docs.slack.dev/reference/methods/users.conversations · https://docs.slack.dev/reference/events/member_left_channel · https://stackoverflow.com/questions/38209815

## dm-never-opened

- **slug**: `dm-never-opened`
- **title**: DMs fail because no IM conversation was ever opened
- **symptom**: `chat.postMessage` with `channel: "U01ABCDE"` (a user ID) returns `channel_not_found`, or works for some users and not others depending on whether they have ever DM'd the app.
- **mechanism**: A direct message is a conversation with its own `D`-prefixed ID, not a user ID. `chat.postMessage` will accept a `U...` and open the IM implicitly in many cases, but this is inconsistent — it fails for users who have never interacted with the app, for bots, and across the file-upload family which requires a real channel ID. The correct sequence is `conversations.open?users=<U...>` → take `channel.id` (a `D...`) → post to that.
- **detect**: Scan configured targets for `U`/`W`-prefixed values used where a channel is expected. To verify a DM exists, call `conversations.list?types=im&limit=1000` and check whether a conversation with the target `user` appears. Also confirm the scope: `im:write` is required to open a DM and `im:read`/`im:history` to enumerate or read them — check `X-OAuth-Scopes`. Separately, `conversations.info` on a `D...` id returns the IM's `user` field so you can confirm the mapping.
- **repair**: Call `conversations.open` with `users=<U...>` (needs `im:write`) and post to the returned `channel.id`. Cache the `D...` per user — the mapping is stable — rather than opening on every send. For group DMs pass a comma-separated `users` list and add `mpim:write`. Note that `conversations.open` is a write method, so a read-only auditor reports the gap rather than fixing it.
- **category**: Channels and membership
- **sources**: https://stackoverflow.com/questions/47753834 · https://github.com/slackapi/bolt-js/issues/365 · https://stackoverflow.com/questions/50235774

## dm-to-deactivated-user

- **slug**: `dm-to-deactivated-user`
- **title**: Messages are sent into DMs with deactivated accounts
- **symptom**: A notification service reports success for every send, but a growing fraction of recipients never respond. The DMs are going to accounts that were deactivated during offboarding. Some calls return `user_not_found` or `cannot_dm_bot`; many just succeed into a void.
- **mechanism**: Slack keeps the user record and the IM conversation after deactivation. Posting to an existing `D...` channel for a deactivated user often still returns `ok: true` — the message is written and nobody will ever read it. `conversations.open` for a deactivated user returns `user_not_found`. Apps that cached `D...` ids at signup and never re-validated accumulate dead recipients indefinitely.
- **detect**: Paginate `users.list?limit=200` and build the set of `id` where `deleted === true`. Intersect with your recipient table. For a single user, `users.info?user=<U...>` → `user.deleted === true`. Also flag `user.is_bot === true` (bots cannot receive DMs from other apps, giving `cannot_dm_bot`) and `user.is_restricted` / `user.is_ultra_restricted` (guests, which may lack access to the channels you reference in the message body).
- **repair**: Join your recipient list against `users.list` on a schedule and mark deactivated users inactive. Subscribe to the `user_change` event, which fires with `user.deleted: true` on deactivation, so the cleanup is event-driven. Filter `is_bot` and `is_app_user` out of any broadcast recipient set.
- **category**: Channels and membership
- **sources**: https://docs.slack.dev/reference/methods/users.list · https://docs.slack.dev/reference/events/user_change · https://stackoverflow.com/questions/56473604

## general-channel-restricted

- **slug**: `general-channel-restricted`
- **title**: posting_to_general_channel_denied on the default channel
- **symptom**: An incoming webhook returns `HTTP 403` with body `posting_to_general_channel_denied`, or `chat.postMessage` returns `restricted_action`. Only `#general` is affected; every other channel works.
- **mechanism**: Workspace admins can restrict who may post in the default channel (`#general` or its renamed equivalent) under **Settings & administration → Workspace settings → Permissions → Messaging**. Apps are commonly excluded by that policy. Because `#general` contains every member, it is the channel integrations most often default to — and the one most likely to be locked down.
- **detect**: `conversations.info?channel=<C...>` → `channel.is_general === true` identifies the default channel; flag any integration targeting it. `conversations.list` also exposes `is_general` so you can find it without knowing the name (it is not necessarily called "general"). The restriction itself is a workspace preference not exposed to a bot token, so the detection is "you are targeting the general channel," treated as a warning, plus the observed `restricted_action` / 403 when a send is attempted.
- **repair**: Post to a purpose-built channel instead of `#general` — this is better practice regardless of the restriction. If `#general` is genuinely required, an admin must relax **Workspace settings → Permissions → Messaging → People who can post in #general** to include apps, or add the app to the allowed posters.
- **category**: Channels and membership
- **sources**: https://stackoverflow.com/questions/55872067 · https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks · https://docs.slack.dev/reference/methods/conversations.info

## read-only-channel

- **slug**: `read-only-channel`
- **title**: restricted_action_read_only_channel: admins locked the channel
- **symptom**: `{"ok": false, "error": "restricted_action_read_only_channel"}` — or the sibling errors `restricted_action`, `restricted_action_thread_locked`. The bot is a member, has `chat:write`, and still cannot post.
- **mechanism**: Enterprise Grid and paid workspaces let admins mark a channel read-only, lock individual threads, or restrict posting to a named set of members. Announcement channels are the common case: everyone can read, a handful can write. The app's membership and scopes are both fine — the channel policy is the blocker, and it is invisible until a write is attempted.
- **detect**: This is a policy the bot token cannot query directly, so detection is symptom-based plus structural. Structural: `conversations.info?channel=<C...>` and inspect `channel.is_read_only` where the plan exposes it, and `channel.is_moved`/`channel.is_mpim` for context. Symptomatic: record any observed `restricted_action_read_only_channel`, `restricted_action_thread_locked`, `restricted_action_non_threadable_channel`, `restricted_action_thread_only_channel` or bare `restricted_action` from `chat.postMessage` and attribute it to channel policy rather than to scopes — the distinction matters because the repair is an admin action, not a code change.
- **repair**: Ask a workspace or channel admin to add the app to the channel's allowed posters (**Channel settings → Permissions → Posting permissions**), or move the integration to a channel without the restriction. No scope change will fix it.
- **category**: Channels and membership
- **sources**: https://docs.slack.dev/reference/methods/chat.postMessage · https://stackoverflow.com/questions/67603707 · https://stackoverflow.com/questions/55872067

## thread-only-or-non-threadable

- **slug**: `thread-only-or-non-threadable`
- **title**: Top-level or threaded posts are refused by channel policy
- **symptom**: `restricted_action_thread_only_channel` when posting a top-level message, or `restricted_action_non_threadable_channel` / `cannot_reply_to_message` when posting a reply. The same code works in every other channel.
- **mechanism**: Slack supports channel configurations that force all conversation into threads (so top-level posts are rejected) and, separately, channel and message types where threading is disabled entirely. An integration that always posts top-level, or always threads under a stored `ts`, will hit exactly one of these depending on the channel it is pointed at.
- **detect**: Symptom-based from the error string, plus a structural precheck: `conversations.info?channel=<C...>` reports channel type flags, and `conversations.history?channel=<C...>&limit=20` shows whether existing messages carry `thread_ts` and `reply_count` — a channel whose entire recent history is threaded under a small number of parents is a thread-only channel. Conversely a channel where no message has `reply_count` may not support threading. Record which posting mode the integration uses and flag the mismatch.
- **repair**: Match the channel's convention: in a thread-only channel, post under an existing `thread_ts` (or create the parent through the permitted path); in a non-threadable channel, drop `thread_ts` and post top-level. Make the posting mode configurable per target channel rather than global.
- **category**: Channels and membership
- **sources**: https://docs.slack.dev/reference/methods/chat.postMessage · https://docs.slack.dev/messaging/retrieving-messages

## slack-connect-external-channel

- **slug**: `slack-connect-external-channel`
- **title**: The channel is externally shared and posts leak outside the org
- **symptom**: Nothing errors. An internal alerting bot has been posting deploy failures, customer names and stack traces into a channel that is shared with a vendor, and has been for months. Occasionally a call returns `access_denied` or a Slack Connect sharing-blocked error on files.
- **mechanism**: Slack Connect lets a channel be shared with an external organization while keeping the same channel ID. From the app's perspective nothing changes — `chat.postMessage` succeeds exactly as before. Admins can separately block file, canvas and list sharing across Slack Connect, which produces `slack_connect_file_link_sharing_blocked` and friends, but plain messages flow freely. This is a data-egress problem that presents as a total absence of errors.
- **detect**: `conversations.info?channel=<C...>` → check `channel.is_ext_shared`, `channel.is_shared`, `channel.is_pending_ext_shared`, and `channel.is_org_shared`. Any target channel with `is_ext_shared: true` is externally visible. Enumerate members with `conversations.members` and resolve each with `users.info`; a member whose `team_id` differs from `auth.test`'s `team_id`, or whose `is_stranger`/`is_restricted` flag is set, is external. Sweep the whole workspace with `conversations.list?types=public_channel,private_channel&limit=1000` and report every `is_ext_shared` channel that any integration posts to.
- **repair**: Move sensitive integrations to internal-only channels, and add an assertion to the send path that refuses to post when `conversations.info` reports `is_ext_shared: true` for the target. Where external posting is intentional, redact payloads for that channel specifically. Admins can also restrict which channels may be shared externally under Slack Connect settings.
- **category**: Channels and membership
- **sources**: https://docs.slack.dev/reference/methods/conversations.info · https://docs.slack.dev/enterprise-grid/ · https://docs.slack.dev/reference/methods/chat.postMessage

## bot-in-too-many-channels

- **slug**: `bot-in-too-many-channels`
- **title**: The bot joined thousands of channels and every scan times out
- **symptom**: A nightly job that enumerates the bot's channels takes hours and eventually dies on `ratelimited`. The bot is a member of 4,000 channels because an onboarding automation invites it to every new one.
- **mechanism**: `users.conversations` and `conversations.list` are cursor-paginated with a maximum `limit` of 1000, and both sit on Tier 2 (20+ requests per minute). Enumerating a large workspace is dozens of requests; doing it per-message or per-run without caching burns the quota. Membership in thousands of channels also means the app receives `message.channels` events for all of them, which multiplies event volume and makes the 3-second ack budget much harder to hit.
- **detect**: Paginate `users.conversations?user=<bot_user_id>&types=public_channel,private_channel&limit=1000`, counting pages and total conversations, and time the sweep. Flag when the count exceeds a few hundred or the sweep needs more than a handful of pages. Cross-check total workspace size with `conversations.list?limit=1&exclude_archived=true` and read `response_metadata` plus `team.info` for context. Watch for `ratelimited` and the `Retry-After` header during the sweep — hitting it during a *read-only audit* is itself the finding.
- **repair**: Stop auto-inviting the bot to every channel; invite it only where it is needed. Cache the channel inventory with a TTL instead of re-enumerating per run, and refresh incrementally from `channel_created` / `channel_deleted` / `member_joined_channel` events. If the app must be in many channels, narrow event subscriptions from `message.channels` to `app_mention` so event volume tracks actual demand rather than membership.
- **category**: Channels and membership
- **sources**: https://docs.slack.dev/reference/methods/users.conversations · https://docs.slack.dev/apis/web-api/rate-limits · https://stackoverflow.com/questions/47762132

---

# Rate limits

## ratelimited-retry-after-ignored

- **slug**: `ratelimited-retry-after-ignored`
- **title**: ratelimited returned and Retry-After was never honored
- **symptom**: A backfill runs fine for ninety seconds then produces a wall of `{"ok": false, "error": "ratelimited"}` (or bare `HTTP 429`). The code retries immediately, which extends the penalty; the job never completes.
- **mechanism**: Slack rate-limits **per API method, per workspace, per app**, on a rolling one-minute window. When the window is exhausted it returns `429` — or a `200` body with `error: "ratelimited"` — carrying a `Retry-After` header in seconds. Hand-rolled clients almost never read that header, and naive exponential backoff without it either waits far too long or retries far too soon. A second trap: `Retry-After` is occasionally absent or unparseable, and clients that assume it is always present crash instead of backing off.
- **detect**: On every read call, capture the HTTP status, `body.error`, and the `Retry-After` response header. Any `error: "ratelimited"` or status `429` is the finding; log the header value alongside it. Slack also returns the throttled context on some responses — record `body.error` together with the method name and the `team_id` from `auth.test` so you can attribute the limit to the right workspace. During a read-only sweep, count how many of your own calls are throttled: a sweep that triggers throttling proves the app's normal traffic will too.
- **repair**: In the transport layer, on `429` or `error: "ratelimited"`, sleep for `Retry-After` seconds (defaulting to 30 if the header is missing or non-numeric) and retry, with a cap on attempts. Both official SDKs do this for you — `@slack/web-api` with `retryConfig`, `slack_sdk` with its built-in `RetryHandler` — so the strongest repair is to stop hand-rolling the client.
- **category**: Rate limits
- **sources**: https://docs.slack.dev/apis/web-api/rate-limits · https://github.com/slackapi/node-slack-sdk/issues/1421 · https://stackoverflow.com/questions/58316972

## non-marketplace-history-clamp

- **slug**: `non-marketplace-history-clamp`
- **title**: conversations.history clamped to 1/min and 15 objects
- **symptom**: A message-archiving integration that used to page through history at Tier 3 now returns 15 messages per call and `ratelimited` on the second call within a minute. Nothing in the code changed. A backfill that took an hour now takes weeks.
- **mechanism**: On **29 May 2025** Slack changed the rate limits for `conversations.history` and `conversations.replies` for commercially distributed apps that are **not** approved for the Slack Marketplace ("unlisted" apps). Those apps get **1 request per minute** and a maximum and default `limit` of **15 objects** per request, down from Tier 3 (50+/min) with `limit` up to 1000. It applied immediately to newly created unlisted apps and to net-new installations of existing unlisted apps, and rolled across existing installations between **2 September 2025** and **3 March 2026**. Internal customer-built apps are excluded.
- **detect**: Call `conversations.history?channel=<C...>&limit=200` on a channel the bot belongs to. If `messages.length` is capped at **15** despite requesting 200, the clamp is active. Confirm by issuing a second `conversations.history` call inside the same minute — a clamped app returns `error: "ratelimited"` with a `Retry-After` around 60. Contrast with a Tier 3 method such as `conversations.list?limit=200`, which will still return up to 200; that isolates the clamp to the history family rather than to a global throttle. Record `auth.test`'s `team_id` and the app's distribution state so the finding names the affected installs.
- **repair**: Three real options. (1) Submit the app to the Slack Marketplace and get it approved, which restores Tier 3. (2) If the app is used only inside one organization, reclassify it as an internal customer-built app rather than a distributed one — internal apps are exempt. (3) Redesign away from polling history: subscribe to `message.channels` / `message.groups` events and maintain your own store, so history reads become a rare backfill rather than the primary data path. Also drop any hardcoded `limit=1000` to `limit=15` so pagination logic does not silently assume larger pages.
- **category**: Rate limits
- **sources**: https://docs.slack.dev/changelog/2025/05/29/rate-limit-changes-for-non-marketplace-apps/ · https://docs.slack.dev/changelog/2025/06/03/rate-limits-clarity/ · https://docs.slack.dev/reference/methods/conversations.history

## postmessage-one-per-second

- **slug**: `postmessage-one-per-second`
- **title**: chat.postMessage bursts past one message per second per channel
- **symptom**: A fan-out job posts 200 alerts and roughly the first 60 land; the rest return `ratelimited`. Or an AI assistant streaming a reply via repeated `chat.update` calls stutters and throttles.
- **mechanism**: `chat.postMessage` is on Slack's **Special** tier: approximately **one message per second per channel**, with short bursts tolerated, plus a separate workspace-wide ceiling. `chat.update` shares the same practical ~1/sec envelope, which is why token-by-token streaming of LLM responses into a Slack message is not achievable at the rate people expect — it is the single most-upvoted rate-limit issue in the Bolt repos. The limit is per *channel*, so parallelizing across channels helps and parallelizing within one does not.
- **detect**: A read-only script cannot post, so detect the *shape* of the traffic rather than the throttle. Read recent history: `conversations.history?channel=<C...>&limit=200` and compute inter-message deltas from the `ts` values for messages where `bot_id` or `app_id` matches your app (`auth.test` gives the bot identity; history items carry `bot_id`, `app_id` and `bot_profile`). Runs of app-authored messages less than 1.0 seconds apart, or long uniform bursts, indicate a sender that will throttle under load. Bursts of near-identical `text` within the same second are the strongest signal.
- **repair**: Put a token-bucket limiter of 1 request/second **per channel** in front of the send path and queue rather than drop. Batch: replace N messages with one message containing N blocks (up to the 50-block ceiling), or post one parent and thread the rest. For streaming AI replies, update on a fixed cadence — every 1 to 2 seconds — rather than per token, and accept coarser granularity.
- **category**: Rate limits
- **sources**: https://docs.slack.dev/apis/web-api/rate-limits · https://github.com/slackapi/bolt-js/issues/2073 · https://stackoverflow.com/questions/71393951

## tier1-method-hammered

- **slug**: `tier1-method-hammered`
- **title**: A Tier 1 method is polled far above 1+ per minute
- **symptom**: One specific call throttles constantly while everything else is fine. The method sits on Tier 1 — roughly one request per minute with almost no burst allowance — and the code polls it in a loop.
- **mechanism**: Slack assigns methods to four tiers: Tier 1 (1+/min), Tier 2 (20+/min), Tier 3 (50+/min), Tier 4 (100+/min), plus Special. Tier 1 is reserved for expensive or rarely-needed operations, and developers routinely discover the tier only by hitting it. Because limits are per-method, one Tier 1 call in an otherwise healthy app produces a confusing partial failure rather than a global slowdown.
- **detect**: Instrument the audit's own calls: record method name, call count, elapsed window, and any `error: "ratelimited"` plus `Retry-After`. Any method that throttles at low call volume is Tier 1 or Special. Cross-reference against the documented tier on the method's reference page (each page states, e.g., "Tier 3: 50+ per minute"). For the app under audit, the read-only proxy is call-pattern analysis — if you can observe the app's traffic shape at all — plus a straight assertion that no Tier 1 method appears in a polling loop.
- **repair**: Move Tier 1 methods out of polling loops entirely: call them once at startup, cache aggressively with a long TTL, and refresh from events rather than by re-polling. Where a tier genuinely blocks the design, the fix is architectural — subscribe to the corresponding Events API event instead of asking Slack repeatedly.
- **category**: Rate limits
- **sources**: https://docs.slack.dev/apis/web-api/rate-limits · https://docs.slack.dev/reference/methods/

## invalid-limit

- **slug**: `invalid-limit`
- **title**: invalid_limit from asking for more than 1000 per page
- **symptom**: `{"ok": false, "error": "invalid_limit"}` from `conversations.list` or `users.list`. Someone tried `limit=5000` to avoid pagination.
- **mechanism**: Cursor-paginated methods cap `limit` below 1000 and reject anything higher outright. Some methods cap lower still — `conversations.history` for a non-Marketplace app caps at 15, and `users.list` is documented as "no more than 1000" but is unreliable near the top of that range and will time out on large workspaces. The error is thrown rather than silently clamped, so it is a hard failure.
- **detect**: Call each paginated read method with the app's configured `limit` and check for `body.error === "invalid_limit"`. Then probe the real ceiling: call with `limit=1000` and compare `channels.length` / `members.length` against the request — a returned page smaller than requested with a non-empty `response_metadata.next_cursor` means Slack clamped rather than errored, which is a different and quieter problem (see [`non-marketplace-history-clamp`](#non-marketplace-history-clamp)).
- **repair**: Set `limit` to 200 for `users.list` and 200–1000 for `conversations.list`, and always follow `response_metadata.next_cursor`. Smaller pages with correct pagination are strictly better than large pages that time out; Slack's own guidance recommends 200 for `users.list` on large workspaces.
- **category**: Rate limits
- **sources**: https://docs.slack.dev/reference/methods/conversations.list · https://docs.slack.dev/reference/methods/users.list · https://docs.slack.dev/apis/web-api/pagination

## pagination-not-followed

- **slug**: `pagination-not-followed`
- **title**: next_cursor is ignored so only the first page is ever seen
- **symptom**: The channel inventory has exactly 100 entries. The user directory has exactly 100. Nobody questions it until a channel that plainly exists is reported missing. No error is ever raised — `ok` is `true` every time.
- **mechanism**: Every `conversations.list`, `users.list`, `conversations.members`, `conversations.history`, `files.list` and `users.conversations` response is a *page*, defaulting to 100 items, with the continuation token in `response_metadata.next_cursor`. When `next_cursor` is a non-empty string there is more data. Code that reads `response.channels` and stops silently truncates the world, and because `ok` is `true` no error handling triggers. This is one of the most common silent data-loss bugs in Slack integrations.
- **detect**: Call each list method with the app's parameters and check whether `response_metadata.next_cursor` is a non-empty string. Then paginate fully yourself and compare the total against the first page — the delta is exactly the data the app is missing. A first page of exactly 100 (or exactly the configured `limit`) with a non-empty cursor is a near-certain truncation bug. Cross-check totals against `team.info` and against `users.list` counts for plausibility.
- **repair**: Loop: `while (cursor) { r = call({...params, cursor, limit: 200}); accumulate(r); cursor = r.response_metadata?.next_cursor || null; }`. Both official SDKs expose async iterators that do this — `for await (const page of client.paginate('conversations.list', {...}))` in Node, `for page in client.conversations_list(limit=200)` in Python. Never treat a single response as the complete set.
- **category**: Rate limits
- **sources**: https://docs.slack.dev/apis/web-api/pagination · https://stackoverflow.com/questions/28818809 · https://stackoverflow.com/questions/55041101

## invalid-cursor

- **slug**: `invalid-cursor`
- **title**: invalid_cursor: a stored cursor was replayed after expiry
- **symptom**: A resumable sync job fails on restart with `{"ok": false, "error": "invalid_cursor"}`. It worked when it was tested minutes after the previous run.
- **mechanism**: Slack's pagination cursors are opaque and time-limited. Persisting one to resume a long-running job hours or days later — or reusing a cursor issued for a *different* parameter set — produces `invalid_cursor`. The cursor encodes the query as well as the position, so changing `limit`, `types` or `exclude_archived` between pages invalidates it too.
- **detect**: Attempt the paginated read with any persisted cursor and check `body.error === "invalid_cursor"`. Also assert consistency: the parameters sent with a continuation must match the parameters that produced the cursor. A job that stores `next_cursor` in a database with a timestamp older than a few hours is a finding even before it errors.
- **repair**: Treat cursors as ephemeral — valid only for the duration of a single pagination loop. To resume across runs, checkpoint on a stable, meaningful key instead: `oldest`/`latest` timestamps for `conversations.history`, or the last-seen `id` for list methods, restarting pagination from the beginning with a narrowed time window. Never persist a cursor beyond the loop that created it.
- **category**: Rate limits
- **sources**: https://docs.slack.dev/apis/web-api/pagination · https://docs.slack.dev/reference/methods/conversations.history

## parallel-workers-share-quota

- **slug**: `parallel-workers-share-quota`
- **title**: Concurrent workers share one per-method quota and starve
- **symptom**: Scaling from 1 to 8 workers makes the job *slower*. Each worker has its own client and its own backoff, and together they saturate the per-method window; every worker spends most of its time in `Retry-After` sleeps.
- **mechanism**: The quota is keyed on **(method, workspace, app)** — not on process, host, or client instance. Ten replicas of the same app share one bucket. Worse, each replica's independent backoff resynchronizes them into a thundering herd: they all sleep for the same `Retry-After` and all retry at the same instant. Adding concurrency to a rate-limited API is negative work.
- **detect**: During the read-only sweep, observe whether `ratelimited` occurs at request rates far below the documented tier — that gap implies other clients of the same app are consuming the bucket. Confirm the shared identity: `auth.test` returns the same `team_id` and the tokens are the same app, so any other process using that token draws on the same quota. Where you can enumerate deployments, the count of replicas multiplied by their per-replica request rate against the method's tier is the arithmetic finding.
- **repair**: Centralize rate limiting: put a single shared token bucket (Redis, or a dedicated sender service) in front of Slack so the *app* respects the tier regardless of replica count. Add jitter to backoff so retries de-synchronize. Where throughput genuinely matters, parallelize across *channels* (for `chat.postMessage`, which is per-channel) rather than across workers hitting one method.
- **category**: Rate limits
- **sources**: https://docs.slack.dev/apis/web-api/rate-limits · https://github.com/slackapi/python-slack-sdk/issues/1693 · https://github.com/slackapi/java-slack-sdk/issues/1216

## message-limit-exceeded

- **slug**: `message-limit-exceeded`
- **title**: message_limit_exceeded: the workspace posting cap was hit
- **symptom**: `{"ok": false, "error": "message_limit_exceeded"}` — "Members on this team are sending too many messages." Distinct from `ratelimited`: it is not your app's quota, it is the workspace's aggregate.
- **mechanism**: Slack enforces a workspace-wide ceiling on message volume in addition to per-app rate limits. A runaway integration, a migration script, or several apps fanning out simultaneously can exhaust it, at which point *every* app in the workspace starts failing. Because the cause is collective, the app that observes the error is often not the app that caused it.
- **detect**: Capture `body.error === "message_limit_exceeded"` distinctly from `ratelimited` — conflating them sends the investigation to the wrong place. Corroborate with volume evidence a read token can gather: `conversations.history?channel=<C...>&limit=200` across the busiest target channels, counting app-authored messages (`bot_id` / `app_id` present) per minute from the `ts` values. A single app producing hundreds of messages per minute is the likely cause.
- **repair**: Find and throttle the offending sender — usually a loop posting per-item instead of per-batch. Batch aggressively (one message with many blocks), and add a global per-workspace send budget in the app so it cannot contribute to a workspace-wide outage. If the volume is legitimate, contact Slack; the workspace ceiling is not self-service.
- **category**: Rate limits
- **sources**: https://docs.slack.dev/reference/methods/chat.postMessage · https://docs.slack.dev/apis/web-api/rate-limits

## accesslimited-ip-allowlist

- **slug**: `accesslimited-ip-allowlist`
- **title**: accesslimited: the caller IP is outside the allowed range
- **symptom**: `{"ok": false, "error": "accesslimited"}` — "Access to this method is limited on the current network." The exact same token works from a laptop and fails from the production cluster, or vice versa.
- **mechanism**: Enterprise Grid administrators can restrict API access by IP range. When the calling host's egress address is outside the allowlist, Slack refuses the method regardless of token validity or scopes. Because cloud egress IPs change — NAT gateway replacement, new availability zone, a move from static egress to ephemeral — this appears as a sudden, total, environment-specific failure. The `invalid_auth` documentation also notes that requests "from an IP address disallowed from making the request" can surface there instead.
- **detect**: `auth.test` and any read method → `body.error === "accesslimited"`. Distinguish it from `invalid_auth` (bad token) by running the same token from a second network: a token that succeeds from one egress and returns `accesslimited` from another is conclusively an IP restriction, not a credential problem. Record the caller's public egress address alongside the result so the finding names the address to allowlist.
- **repair**: Have the Grid admin add the app's egress CIDR to the API allowlist (**Organization settings → Security → IP allowlisting**). On the app side, pin egress to a stable NAT gateway or static IP so the allowlist stays accurate, and treat egress-IP changes as a Slack-affecting change in your runbook.
- **category**: Rate limits
- **sources**: https://docs.slack.dev/reference/methods/chat.postMessage · https://stackoverflow.com/questions/55407744 · https://stackoverflow.com/questions/38759599

## retry-storm-from-event-retries

- **slug**: `retry-storm-from-event-retries`
- **title**: Event retries multiply API calls into a self-inflicted 429
- **symptom**: Under load, one incoming event becomes four (original plus three retries), each triggering the same outbound Slack calls, which throttle, which slows the handler, which misses the 3-second ack, which triggers more retries. The system converges on total failure and recovers only when traffic stops.
- **mechanism**: Slack retries an undelivered event up to three times — immediately, after one minute, and after five minutes — carrying `X-Slack-Retry-Num: 1..3` and `X-Slack-Retry-Reason`. A handler that does work *before* acking, and that has no idempotency key, performs that work once per delivery. Each duplicate consumes per-method quota, pushing the app closer to `ratelimited`, which lengthens handler time, which causes more timeouts. It is a feedback loop, but not a diverging one: the three-retry ceiling bounds the amplification, so the loop settles at a fixed miss rate rather than running away. Modelled out, an ordinary over-budget configuration settles near a 93% miss rate, a point or two under the 95% failure rate at which Slack disables the subscription outright, which is why these apps limp rather than stop. One of the most-reported production failures in the Bolt repos.
- **detect**: Do **not** detect this by counting duplicate app-authored messages in history — `duplicate-messages-no-dedupe` already owns that reading, and a second note doing the same clustering is a restatement. The distinct detection here is the amplification arithmetic: events times deliveries times calls per delivery, iterated against the per-method quota until it settles, and the finding is the settling point and how close it sits to the 95% disable threshold. Separately, any `ratelimited` observed during the audit compounds the finding.
- **repair**: Ack first, work after: return `200 OK` (Bolt: call `ack()`) as the first statement of the handler, then do the work asynchronously. Add idempotency keyed on `event.event_id` (stable across retries) — a short-TTL set in Redis is sufficient — and drop any event whose id has already been processed. Read `X-Slack-Retry-Num` and skip work entirely on retries where the original may have succeeded. On FaaS, ensure the platform does not freeze the process after the response returns; use a queue rather than post-response work.
- **category**: Rate limits
- **sources**: https://docs.slack.dev/apis/events-api/ · https://github.com/slackapi/bolt-python/issues/1302 · https://stackoverflow.com/questions/50715387

---

# Events and request URLs

## request-url-unverified

- **slug**: `request-url-unverified`
- **title**: The Request URL never passed the url_verification challenge
- **symptom**: The Slack app config shows a red "Your URL didn't respond with the value of the challenge parameter" next to the Request URL, and the app receives no events at all. Everything else about the app looks correct.
- **mechanism**: Before Slack will deliver events, it POSTs `{"type": "url_verification", "token": "...", "challenge": "<random>"}` to the candidate Request URL and requires the `challenge` value echoed back within 3 seconds — as `text/plain`, or as `{"challenge": "..."}` JSON. Frameworks that require authentication on all routes, that don't parse `application/json`, that redirect (Slack does not follow redirects for this), or that sit behind an API gateway rewriting the body, all fail the handshake. Because the failure is in the app config UI rather than in application logs, it is easy to leave broken.
- **detect**: With an app configuration token, `apps.manifest.export?app_id=<A...>` returns `settings.event_subscriptions.request_url` and `settings.event_subscriptions.bot_events[]`. A manifest with `bot_events` populated but no `request_url` — or with Socket Mode disabled and no `request_url` — means events cannot be delivered. Without a configuration token, the read-only proxy is behavioral: subscribe-worthy activity exists in the workspace (`conversations.history` shows messages and `app_mention`-shaped text) while the app has produced no responses; combine with `bots.info?bot=<bot_id>` and the absence of any app-authored messages in channels where it is a member.
- **repair**: Add a handler that runs *before* any auth middleware: if `body.type === "url_verification"`, respond `200` with `body.challenge` as plain text. Both Bolt receivers do this automatically, so the usual repair is to stop hand-rolling and mount `ExpressReceiver`/`FastAPI` adapters correctly. Then click **Retry** on the Event Subscriptions page and confirm the green "Verified" state.
- **category**: Events and request URLs
- **sources**: https://docs.slack.dev/apis/events-api/ · https://github.com/slackapi/bolt-js/issues/1135 · https://stackoverflow.com/questions/52872580

## event-subscriptions-auto-disabled

- **slug**: `event-subscriptions-auto-disabled`
- **title**: Slack disabled event delivery after sustained 5xx
- **symptom**: The app was working. After an outage it never recovers, even once the service is healthy again. Slack sent an email nobody read, and the Event Subscriptions page shows delivery disabled.
- **mechanism**: Slack monitors delivery success. If an app responds with errors on more than **95% of delivery attempts within a 60-minute window**, Slack temporarily disables the app's event subscriptions and notifies the app owner. Counted failures include SSL validation errors, responses slower than 3 seconds, too many redirects, and any non-2xx status. Crucially, delivery does **not** resume automatically when the service recovers — a human must re-enable it. A long deploy outage or a certificate expiry is enough to trip it.
- **detect**: With an app configuration token, `apps.manifest.export` reveals whether subscriptions are configured, though not their live enabled/disabled state. The reliable read-only detection is behavioral: establish that events *should* be arriving — `conversations.history?channel=<C...>&limit=100` shows recent human messages mentioning the bot, or `conversations.members` confirms the bot is present in active channels — and that the app has posted nothing in response for a period spanning many such messages. Compare the timestamp of the last app-authored message (`bot_id` matching `auth.test`'s `bot_id`) against the most recent inbound trigger; a large, growing gap is the signal.
- **repair**: Fix the underlying failure (certificate, timeout, 5xx), then go to **Event Subscriptions** in the app config and re-enable delivery. Add an external uptime check on the Request URL that alerts before Slack's 95%/60-minute threshold is reached, and make sure the endpoint returns 2xx quickly even when downstream dependencies are down — ack first, then fail internally.
- **category**: Events and request URLs
- **sources**: https://docs.slack.dev/apis/events-api/ · https://github.com/slackapi/bolt-python/issues/923

## three-second-timeout

- **slug**: `three-second-timeout`
- **title**: Handlers exceed 3 seconds and every event is retried
- **symptom**: Users see "We had some trouble connecting. Try again?" on modal submits, `operation_timeout` or `dispatch_failed` on slash commands, and every event handled two to four times. The work itself completes correctly — just too slowly.
- **mechanism**: Slack requires an HTTP 2xx within **three seconds** for every event, interaction and slash command. Anything slower is a failed delivery and is retried. Serverless cold starts, database lookups in the installation store, and synchronous outbound HTTP calls all blow the budget. On FaaS the problem compounds: many platforms freeze the process the moment the response is returned, so "ack then work asynchronously" silently drops the work unless it is handed to a queue.
- **detect**: Symptom-shaped, read from the workspace. Duplicate app-authored messages in `conversations.history` spaced at roughly 0s / 60s / 300s are the retry schedule's fingerprint (see [`retry-storm-from-event-retries`](#retry-storm-from-event-retries)). For interactions specifically, look for repeated identical modal-driven side effects — duplicate records posted back into a channel. Additionally, measure Slack's own view of your endpoint indirectly: if the app's messages consistently appear more than three seconds after the triggering human message's `ts`, the handler is doing work before acking.
- **repair**: Ack within milliseconds and defer everything else. In Bolt: `await ack()` as the first line, then push the job onto a queue (SQS, Redis, a background task) rather than awaiting it inline. Use `response_url` (valid for 30 minutes, up to 5 uses) to deliver the real answer after the ack. Pre-warm or avoid FaaS for latency-sensitive receivers, and move installation-store lookups behind a cache so they cannot eat the budget.
- **category**: Events and request URLs
- **sources**: https://docs.slack.dev/apis/events-api/ · https://github.com/slackapi/bolt-js/issues/361 · https://stackoverflow.com/questions/34896954

## duplicate-processing-on-retry

- **slug**: `duplicate-processing-on-retry`
- **title**: X-Slack-Retry-Num retries produce duplicate side effects
- **symptom**: One Slack message creates three Jira tickets, three PagerDuty incidents, or three identical replies. It happens only under load, which makes it maddening to reproduce.
- **mechanism**: Slack retries deliveries it believes failed, but "failed" means "no timely 2xx" — not "not processed." A handler that completes its work and then times out on the response has done the work *and* will be retried. Without an idempotency key the side effect happens once per delivery. `X-Slack-Retry-Num` (1–3) and `X-Slack-Retry-Reason` (`http_timeout`, `connection_failed`, `ssl_error`, `http_error`, `too_many_redirects`, `unknown_error`) identify retries, but several SDK receivers historically did not surface these headers to listeners, and Socket Mode drops the retry metadata entirely.
- **detect**: `conversations.history?channel=<C...>&limit=200` and cluster app-authored messages by identical or near-identical `text`/`blocks` within a 6-minute window. Report clusters of 2–4 with the characteristic 60s and 300s spacing. Because the duplicates are real messages in the workspace, this is one of the few app-side bugs that is fully visible to a read-only token. Also check `conversations.replies` for duplicated thread replies, which is the more common shape for bot responses.
- **repair**: Dedupe on `event.event_id`, which is stable across retries: store it in a set with a 10-minute TTL and return early on a hit. Additionally short-circuit when `X-Slack-Retry-Num` is present and the reason is `http_timeout`, since the original very likely succeeded. Make the downstream operation idempotent with a natural key (`event_id` as the external id on the created ticket) so even a missed dedupe cannot double-create.
- **category**: Events and request URLs
- **sources**: https://docs.slack.dev/apis/events-api/ · https://github.com/slackapi/bolt-python/issues/868 · https://github.com/slackapi/bolt-python/issues/1484

## no-event-subscriptions

- **slug**: `no-event-subscriptions`
- **title**: The app subscribes to zero events and reacts to nothing
- **symptom**: The bot is installed, in the channel, with valid scopes, and completely inert. Mentioning it does nothing. The developer is convinced the code is wrong; the code was never invoked.
- **mechanism**: Event subscriptions are opt-in per event type in the app configuration. Being in a channel does not cause Slack to send you its messages. Developers commonly add `app_mentions:read` (the *scope*) and assume that subscribes them to `app_mention` (the *event*) — the two are separate steps, and the scope only makes the event *available* to subscribe to.
- **detect**: With an app configuration token, `apps.manifest.export?app_id=<A...>` → `settings.event_subscriptions.bot_events[]` and `.user_events[]`. An empty array with a populated `oauth_config.scopes.bot` is the finding. Without a configuration token: confirm the bot is a member of active channels (`conversations.members`), confirm humans are addressing it (`conversations.history` containing `<@Uxxxx>` matching `auth.test`'s `user_id`), and confirm the bot has never replied — that triad implies no subscription or no delivery.
- **repair**: In **Event Subscriptions → Subscribe to bot events**, add the events the app handles: `app_mention` for mentions, `message.channels` / `message.groups` / `message.im` / `message.mpim` for messages by channel type, `member_joined_channel`, `reaction_added`, and so on. Then reinstall — adding an event that requires a new scope changes the token grant. In a manifest, populate `settings.event_subscriptions.bot_events`.
- **category**: Events and request URLs
- **sources**: https://docs.slack.dev/apis/events-api/ · https://stackoverflow.com/questions/42372079 · https://stackoverflow.com/questions/65797289

## event-scope-mismatch

- **slug**: `event-scope-mismatch`
- **title**: A subscribed event needs a scope the token never got
- **symptom**: The app receives `message.channels` but never `message.groups`, or receives mentions but not reactions. Some event types arrive and structurally similar ones never do, with no error anywhere.
- **mechanism**: The Events API is gated by the same object-oriented scope system as the Web API: you receive only the events that the authorizing token's scopes make visible. `message.groups` requires `groups:history`; `reaction_added` requires `reactions:read`; `file_created` requires `files:read`. The app configuration will happily let you subscribe to an event whose scope you later remove, or install with a reduced grant — and the result is simply that the event never arrives.
- **detect**: Diff two sets. Set A: subscribed events from `apps.manifest.export` → `settings.event_subscriptions.bot_events[]`. Set B: granted scopes from the `X-OAuth-Scopes` header. Map each event to its required scope (documented on each event's reference page) and report subscribed events whose scope is absent from B. Without a configuration token, invert it: for each event the code handles, assert the corresponding scope is present in `X-OAuth-Scopes` — a handler for `message.groups` in an app without `groups:history` is dead code.
- **repair**: Add the missing scope to **Bot Token Scopes** and reinstall. Note the direction of causality: adding the scope does not auto-subscribe the event, and subscribing the event does not auto-add the scope — both must be done. Keep them together in the manifest so they cannot drift.
- **category**: Events and request URLs
- **sources**: https://docs.slack.dev/apis/events-api/ · https://docs.slack.dev/reference/events/ · https://docs.slack.dev/reference/scopes/

## bot-message-echo-loop

- **slug**: `bot-message-echo-loop`
- **title**: The bot answers its own messages in an endless loop
- **symptom**: A channel fills with hundreds of identical bot messages in seconds. Slack rate-limits the app, which slows but does not stop the loop. Someone has to remove the bot from the channel to end it.
- **mechanism**: Subscribing to `message.channels` delivers **every** message in the channel, including messages posted by your own app. A handler that replies to any message replies to its own reply. Slack marks app-authored messages with `bot_id`, `app_id`, and `subtype: "bot_message"` (for legacy senders), but a handler matching only on `event.text` sees none of that. The loop is trivially reachable and is one of the classic first-week Slack bugs.
- **detect**: This one is perfectly visible from a read token. `conversations.history?channel=<C...>&limit=200` and look for long consecutive runs of messages whose `bot_id` equals `auth.test`'s `bot_id`, with sub-second `ts` deltas and repeating `text`. Report the longest run and the channels affected. `conversations.replies` shows the threaded variant. A run of more than a handful of consecutive self-authored messages with no intervening human message is the finding.
- **repair**: Guard the handler: ignore any event where `event.bot_id` is present, where `event.subtype === "bot_message"`, or where `event.user === <your bot user_id>`. Better, subscribe to `app_mention` instead of `message.channels` so you only receive messages that explicitly address the app — Bolt's `app.event('app_mention')` filters bot messages by default, while `app.message()` requires the guard.
- **category**: Events and request URLs
- **sources**: https://stackoverflow.com/questions/51419484 · https://docs.slack.dev/reference/events/message · https://docs.slack.dev/reference/events/app_mention

## message-subtypes-ignored

- **slug**: `message-subtypes-ignored`
- **title**: Edits, deletes and joins are processed as new messages
- **symptom**: Editing a message causes the bot to respond again. Someone joining a channel triggers the "new message" pipeline. Deleted messages are archived as if they were posted. A single user edit produces three archived copies.
- **mechanism**: The `message` event carries a `subtype` field for everything that is not a plain new message: `message_changed`, `message_deleted`, `channel_join`, `channel_leave`, `bot_message`, `thread_broadcast`, `file_share`, `message_replied`, `tombstone` and more. `message_changed` nests the real content under `event.message` and the prior version under `event.previous_message`, so code reading `event.text` on a `message_changed` gets `undefined` or the wrong field. Handlers that ignore `subtype` treat all of these as new user messages.
- **detect**: Read the workspace's own record. `conversations.history?channel=<C...>&limit=200` returns messages carrying `subtype` and, for edited messages, an `edited: {user, ts}` object. Count how many recent messages carry a `subtype` or an `edited` block — if the app's archive or reply log contains entries corresponding to those, it is not filtering. The clearest signal: app responses whose `ts` clusters immediately after a message's `edited.ts` rather than its original `ts`.
- **repair**: Branch on `subtype` explicitly. Handle `undefined` (a genuine new message) as the default; handle `message_changed` by reading `event.message.text` and comparing against `event.previous_message.text`; ignore `channel_join`, `channel_leave`, `bot_message` and `message_deleted` unless you specifically want them. In Bolt, `app.message()` already filters `bot_message` but not the others.
- **category**: Events and request URLs
- **sources**: https://docs.slack.dev/reference/events/message · https://docs.slack.dev/reference/methods/conversations.history

## app-mention-vs-message-double-fire

- **slug**: `app-mention-vs-message-double-fire`
- **title**: Both message.channels and app_mention fire, doubling replies
- **symptom**: Mentioning the bot in a channel produces exactly two replies, every time, deterministically. Not a retry — the pair arrives simultaneously.
- **mechanism**: When a user writes `@bot hello` in a channel the app is in, Slack delivers **two separate events**: `app_mention` (because the text mentions the app) and `message.channels` (because a message was posted in a channel the app subscribes to). An app subscribed to both, with a handler on each that replies, replies twice. This differs from retry duplication in that the two messages have essentially identical timestamps rather than 60s/300s spacing.
- **detect**: Two-part. Configuration: `apps.manifest.export` → check whether `settings.event_subscriptions.bot_events` contains **both** `app_mention` and any `message.*` variant. Behavioral: `conversations.history?channel=<C...>&limit=200` → find app-authored message pairs with identical or near-identical `text` whose `ts` differ by well under a second, each immediately following a human message containing `<@Uxxxx>`. Sub-second twins point at double subscription; 60-second twins point at retries. The spacing is the discriminator.
- **repair**: Subscribe to one or the other, not both, for the mention path. The usual shape: subscribe to `app_mention` for directed commands and, if you also need general message handling, guard the `message` handler to skip messages containing `<@` + your bot user id. In Bolt, register `app.event('app_mention')` and make `app.message()` explicitly exclude mentions.
- **category**: Events and request URLs
- **sources**: https://docs.slack.dev/reference/events/app_mention · https://docs.slack.dev/reference/events/message · https://github.com/slackapi/bolt-js/issues/914

## http-or-dead-tunnel-request-url

- **slug**: `http-or-dead-tunnel-request-url`
- **title**: The Request URL is http:// or a dead ngrok tunnel
- **symptom**: A production app's Request URL still points at `https://a1b2c3d4.ngrok.io/slack/events` from someone's laptop last March. Events go nowhere. Or the URL is `http://` and Slack refuses it outright at verification time.
- **mechanism**: Slack requires HTTPS with a valid, publicly trusted certificate for Request URLs and will not deliver over plain HTTP or to a certificate it cannot validate. Development tunnels (ngrok, localtunnel, Cloudflare Tunnel) satisfy the requirement while running, so a URL configured during development verifies successfully and then dies when the tunnel closes — leaving a permanently broken production app whose config *looks* correct. `ssl_error` appears in `X-Slack-Retry-Reason` when certificate validation fails mid-life, for instance after a certificate expires.
- **detect**: `apps.manifest.export?app_id=<A...>` → inspect `settings.event_subscriptions.request_url`, `settings.interactivity.request_url`, `settings.interactivity.message_menu_options_url`, and every `features.slash_commands[].url`. Flag any that (a) do not start with `https://`, (b) contain a known tunnel domain — `ngrok.io`, `ngrok-free.app`, `loca.lt`, `trycloudflare.com`, `serveo.net` — or (c) resolve to a private address. Then perform a plain unauthenticated `GET`/`HEAD` on each host to confirm it is reachable and presents a valid certificate; a connection failure or certificate error is conclusive.
- **repair**: Point every URL at the production hostname with a certificate from a public CA, and re-verify. Keep development in a separate Slack app entirely — Slack has no notion of environments, so the only clean separation is two apps with two manifests, one carrying the tunnel URL and one carrying production. Add certificate expiry to the same monitoring that watches the endpoint.
- **category**: Events and request URLs
- **sources**: https://docs.slack.dev/apis/events-api/ · https://stackoverflow.com/questions/57065187 · https://docs.slack.dev/reference/methods/apps.manifest.export

## multi-install-authorizations

- **slug**: `multi-install-authorizations`
- **title**: One event serves many installs and only one is handled
- **symptom**: In a shared channel, or on Enterprise Grid, a distributed app processes an event for one tenant and ignores the others. Customers report intermittent, tenant-specific gaps.
- **mechanism**: When an event is visible to several installations of the same app, Slack sends a **single** delivery with an `authorizations` array containing at most one entry, plus an `event_context`. The app must call `apps.event.authorizations.list` with that `event_context` to enumerate the rest. Apps built for a single workspace never encounter this and so never write the fan-out, which then breaks silently the day the app is installed somewhere shared.
- **detect**: Establish that the app is multi-install: distinct `team_id` values across `auth.test` calls in your installation store, or any install where `auth.test` returns `is_enterprise_install: true` / a non-null `enterprise_id`. Then verify the capability exists: `apps.event.authorizations.list` with the app-level token and a dummy `event_context` should return `invalid_event_context` (capability present) rather than `missing_scope` or `auth_mismatch`. Multi-install plus missing capability is the finding.
- **repair**: Add `authorizations:read` to an app-level token; in the event handler, call `apps.event.authorizations.list?event_context=<payload.event_context>` with cursor pagination and process the event once per returned authorization, selecting the right stored token for each `team_id`/`enterprise_id`. Bolt's `authorize` callback receives the enterprise and team ids for exactly this purpose.
- **category**: Events and request URLs
- **sources**: https://docs.slack.dev/reference/methods/apps.event.authorizations.list · https://docs.slack.dev/apis/events-api/ · https://github.com/slackapi/bolt-js/issues/1875

## rtm-legacy-still-used

- **slug**: `rtm-legacy-still-used`
- **title**: The app still runs on the retired RTM API
- **symptom**: A long-lived bot connects via `rtm.connect` (or the deprecated `rtm.start`) and works — until a scope change, a reinstall, or an app recreation, at which point `rtm.connect` returns `missing_scope` with `needed: client` and there is no way to grant `client` on a modern app.
- **mechanism**: The Real Time Messaging API predates granular scopes and requires the classic `client`/`bot` scope, which modern (post-2020) apps cannot request. Slack has kept RTM alive for existing classic apps but new apps cannot use it; Socket Mode is the supported replacement. Teams that recreate a classic app as a modern one discover the incompatibility only at runtime.
- **detect**: Read `X-OAuth-Scopes`: presence of the bare `client`, `bot`, or `read` scope indicates a classic app that can still use RTM; their absence in an app whose code calls `rtm.connect` is the finding. Directly, call `rtm.connect` — a modern app returns `missing_scope` with `needed` naming `client`, which is unambiguous. (Note `rtm.connect` opens a session, so treat this as a probe to run sparingly.) `apps.manifest.export` → `settings.socket_mode_enabled` tells you whether the supported replacement is configured.
- **repair**: Migrate to Socket Mode: enable it in **Socket Mode**, create an app-level token with `connections:write`, and switch the client to `@slack/socket-mode` / `SocketModeClient` (or Bolt with `socketMode: true`). Alternatively move to the HTTP Events API with a public Request URL. Either path requires event subscriptions to be configured — RTM delivered everything implicitly and the replacements do not.
- **category**: Events and request URLs
- **sources**: https://stackoverflow.com/questions/27833715 · https://stackoverflow.com/questions/54528038 · https://docs.slack.dev/apis/events-api/using-socket-mode

---

# Messaging and Block Kit

## invalid-blocks

- **slug**: `invalid-blocks`
- **title**: invalid_blocks: the Block Kit payload failed validation
- **symptom**: `{"ok": false, "error": "invalid_blocks"}` or `invalid_blocks_format`. The payload renders perfectly in Block Kit Builder, and Slack gives no indication of *which* block is at fault.
- **mechanism**: Slack validates the entire `blocks` array server-side and rejects the whole message on any violation, with a single opaque error. Common causes: `blocks` passed as an object rather than a JSON-encoded array; a `section` with neither `text` nor `fields`; an `image` block whose `image_url` Slack cannot fetch (unreachable host, auth-required, wrong content type) — which kills the entire message rather than falling back to `alt_text`; an `alt_text` longer than its limit; a `static_select` with zero options; duplicate `action_id` values within one message; or an unknown block `type` from a newer SDK than the workspace supports.
- **detect**: Symptom capture plus structural validation. Capture any observed `invalid_blocks` / `invalid_blocks_format` from send attempts. Structurally, read what the app has *successfully* posted with `conversations.history?channel=<C...>&limit=200`, which returns each message's `blocks` array as Slack stored it, and validate those against the Block Kit schema — the same generator produces both the good and the bad payloads. For image blocks specifically, extract every `image_url` from historical blocks and issue an unauthenticated `HEAD` to confirm it is publicly fetchable and returns an image content type; a URL that requires auth is the single most common `invalid_blocks` cause.
- **repair**: Validate against the Block Kit schema before sending, and log the offending payload on failure. Host images at a publicly reachable URL with a correct `Content-Type` (or upload to Slack and use the returned file). Ensure every `section` has `text` or `fields`, every `action_id`/`block_id` is unique within the message and under 255 characters, and every select has at least one option. Paste the failing payload into Block Kit Builder — it reports the specific violation Slack's API will not.
- **category**: Messaging and Block Kit
- **sources**: https://stackoverflow.com/questions/60344831 · https://github.com/slackapi/python-slack-sdk/issues/1782 · https://docs.slack.dev/reference/block-kit/blocks

## msg-blocks-too-long

- **slug**: `msg-blocks-too-long`
- **title**: More than 50 blocks in one message
- **symptom**: `{"ok": false, "error": "msg_blocks_too_long"}` on the reports that matter and success on the small ones. A digest that grew from 20 items to 60 breaks with no code change.
- **mechanism**: A message may contain at most **50 blocks**; modals and Home tabs allow **100**. There is also a total payload ceiling — reports of failures around 13,200 characters of block JSON are common — so a message can be under 50 blocks and still be rejected for size. Because the limit is on the *generated* payload rather than on the input, any code that maps a variable-length collection to one block per item is a latent failure that triggers on a busy day.
- **detect**: Read the app's own output: `conversations.history?channel=<C...>&limit=200` returns `message.blocks` for each app-authored message. Compute `blocks.length` and `JSON.stringify(blocks).length` per message and report the maximum and the distribution — a distribution whose tail approaches 50 blocks or ~12k characters is one busy day from breaking. For modals, `views.open` failures surface the same class. Capture any observed `msg_blocks_too_long` and `attachment_payload_limit_exceeded`.
- **repair**: Cap the block count in the generator, not at the call site: emit at most ~45 blocks and append a "showing N of M" footer with a link. For genuinely long content, post a parent message and thread the remainder (`thread_ts`), or upload the full content as a file snippet and post a summary. For 100-block modals, paginate the view with a "Next" button that calls `views.update`.
- **category**: Messaging and Block Kit
- **sources**: https://docs.slack.dev/block-kit/ · https://github.com/slackapi/bolt-js/issues/2509 · https://docs.slack.dev/reference/methods/chat.postMessage

## blocks-without-text-fallback

- **slug**: `blocks-without-text-fallback`
- **title**: Blocks with no text fallback, so notifications are blank
- **symptom**: Messages look right in the channel, but the mobile push notification and the desktop toast read "This content can't be displayed" or show only the app name. Sometimes the send itself fails with `no_text`.
- **mechanism**: `text` is not merely a legacy alternative to `blocks` — it is the fallback string Slack uses for push notifications, the channel list preview, screen readers, and any surface that cannot render Block Kit. When `blocks` is supplied without `text`, Slack accepts the message (or, with attachments in play, rejects it with `no_text`) and every notification surface degrades. Users experience this as "the bot's alerts are useless on mobile," which is rarely traced back to a missing field.
- **detect**: `conversations.history?channel=<C...>&limit=200`, filter to app-authored messages (`bot_id` matches `auth.test`), and count those where `blocks` is a non-empty array while `text` is absent, empty, or a placeholder like `"​"`/`"message"`. Report the ratio. Also check `attachments[].fallback` for messages still using attachments — the same principle applies there.
- **repair**: Always send `text` alongside `blocks`, set to a one-line human summary of the message ("3 deploys failed in prod"). It is never rendered when blocks display successfully, so it costs nothing visually. Make it a required argument in your message-builder function so it cannot be forgotten.
- **category**: Messaging and Block Kit
- **sources**: https://docs.slack.dev/reference/methods/chat.postMessage · https://stackoverflow.com/questions/42993602 · https://docs.slack.dev/block-kit/

## text-length-limits

- **slug**: `text-length-limits`
- **title**: A section text object exceeds 3000 characters
- **symptom**: `invalid_blocks` on long content, or messages that render truncated with no error. Log excerpts, stack traces and diff output are the usual triggers.
- **mechanism**: Block Kit enforces per-object character ceilings, and exceeding any one of them invalidates the whole message: `section.text.text` and each entry of `section.fields[]` cap at 3000 characters (with at most 10 fields); `header.text.text` at 150; `button.text.text` at 75; `context` elements at 75; `input.label` at 2000; option `text` at 75 and option `value` at 150; `block_id` and `action_id` at 255. Message `text` itself is capped around 40,000 characters and is truncated rather than rejected. Because the failure mode differs by field — some reject, some truncate — behavior is inconsistent and hard to reason about.
- **detect**: Read the app's posted messages via `conversations.history` and measure every text-bearing field in each stored `blocks` array against its documented ceiling. Report the maximum observed length per field type and flag anything within, say, 10% of a limit as at-risk. This catches the "it works until someone's stack trace is long" case before it fires. Capture any observed `invalid_blocks` alongside the payload for direct confirmation.
- **repair**: Truncate defensively in the message builder with an explicit ellipsis and a link to the full content: `text.slice(0, 2900) + "\n…truncated"`. For long logs, upload a snippet via the file API and post a short summary block referencing it, rather than inlining. Never interpolate unbounded user or system output directly into a block.
- **category**: Messaging and Block Kit
- **sources**: https://docs.slack.dev/reference/block-kit/blocks · https://docs.slack.dev/reference/block-kit/composition-objects · https://github.com/slackapi/slack-github-action/issues/448

## too-many-attachments

- **slug**: `too-many-attachments`
- **title**: More than 100 attachments on a single message
- **symptom**: `{"ok": false, "error": "too_many_attachments"}` or `attachment_payload_limit_exceeded`. Legacy code that maps one attachment per result item breaks once results exceed 100.
- **mechanism**: `chat.postMessage` allows a maximum of **100** attachments, and the serialized attachment payload has its own size ceiling. Attachments are the pre-Block-Kit formatting mechanism and Slack now describes them as legacy, but an enormous amount of existing integration code still uses them — particularly anything generated from a monitoring tool. There is a parallel limit of 10 `contact_cards`.
- **detect**: `conversations.history?channel=<C...>&limit=200` returns `message.attachments` for stored messages; compute `attachments.length` and the serialized size per app-authored message and report the maximum. Any app still emitting attachments at all is worth flagging for migration, since attachment rendering is deprioritized in modern Slack clients and `mrkdwn` inside attachments requires the extra `mrkdwn_in` field to work at all.
- **repair**: Cap the attachment count in the generator and summarize the overflow. Better, migrate to `blocks`: the modern equivalent of one attachment per item is one `section` per item, subject to the 50-block ceiling and the same "cap and summarize" discipline. Keep `attachments` only for the colored side-bar, which has no Block Kit equivalent.
- **category**: Messaging and Block Kit
- **sources**: https://docs.slack.dev/reference/methods/chat.postMessage · https://stackoverflow.com/questions/35117289 · https://docs.slack.dev/messaging/formatting-message-text

## no-text-empty-message

- **slug**: `no-text-empty-message`
- **title**: no_text: an empty message body was posted
- **symptom**: `{"ok": false, "error": "no_text"}` intermittently — usually when an upstream query returns zero rows and the template renders to an empty string.
- **mechanism**: `chat.postMessage` requires at least one of `text`, `blocks`, or `attachments` to carry content. An empty `text` with an empty `blocks: []` is rejected. The common path is a formatter that builds a string by concatenating results and produces `""` when there are none — the "no results" case is exactly the case nobody tests.
- **detect**: Capture observed `no_text` errors. Structurally, examine the app's stored messages in `conversations.history` for near-empty output: app-authored messages where `text` is whitespace-only and `blocks` is empty or contains only a divider — these are the successful siblings of the failing case and prove the generator can produce empty output. Also look for messages consisting solely of a header with no body.
- **repair**: Guard the send: if the rendered body is empty, either skip the send entirely (usually correct — nobody wants a daily "nothing happened" ping) or substitute an explicit "No results for <window>" string. Make the message-builder return `null` for empty content and have the sender treat `null` as a no-op.
- **category**: Messaging and Block Kit
- **sources**: https://docs.slack.dev/reference/methods/chat.postMessage · https://stackoverflow.com/questions/42993602

## cannot-reply-to-message

- **slug**: `cannot-reply-to-message`
- **title**: cannot_reply_to_message: threading onto a non-threadable post
- **symptom**: `{"ok": false, "error": "cannot_reply_to_message"}` when replying under a stored `thread_ts`. The parent exists and is visible in the channel.
- **mechanism**: Certain message types cannot host thread replies — some join/leave subtypes, tombstones from deleted messages, and messages in channels where threading is disabled. Additionally, `restricted_action_thread_locked` fires when an admin has locked the thread. An integration that stores a `ts` and threads under it indefinitely will eventually target a parent that has been deleted (leaving a tombstone) or locked.
- **detect**: For each stored `thread_ts` the app threads under, call `conversations.replies?channel=<C...>&ts=<thread_ts>&limit=1`. Errors `thread_not_found` or `message_not_found` mean the parent is gone; a returned parent with `subtype: "tombstone"` means it was deleted; a parent lacking `reply_count`/`replies` support in a channel whose other messages also lack them suggests threading is off. `conversations.history` around that `ts` confirms the parent's `subtype`.
- **repair**: Validate the parent with `conversations.replies` before threading and fall back to a top-level post when it fails. Store the parent `ts` with a TTL and re-establish a new parent when the old one is gone. Never assume a `ts` captured days ago is still a valid thread root.
- **category**: Messaging and Block Kit
- **sources**: https://docs.slack.dev/reference/methods/chat.postMessage · https://docs.slack.dev/reference/methods/conversations.replies

## thread-ts-is-a-reply

- **slug**: `thread-ts-is-a-reply`
- **title**: A reply ts is used as thread_ts, flattening the thread
- **symptom**: Threads appear "flat" — replies attach to the original parent rather than nesting under the intended message, or a reply chain unexpectedly restarts. No error is returned.
- **mechanism**: Slack threads are one level deep. If you pass the `ts` of a *reply* as `thread_ts`, Slack silently reparents it to that reply's own `thread_ts` — the original root — rather than erroring. Code that captures `response.ts` from a reply and threads under it therefore behaves differently from what the author intended, and does so silently. The distinguishing field is that a reply's own message object carries both `ts` (itself) and `thread_ts` (its root); a root has `thread_ts === ts` or no `thread_ts` at all.
- **detect**: `conversations.replies?channel=<C...>&ts=<root>&limit=200` returns the full thread. For each message check whether `thread_ts === ts` (root) or `thread_ts !== ts` (reply). Then examine the app's stored thread roots: any stored `thread_ts` that, when looked up in history, has `thread_ts !== ts` is a reply being used as a root. Also flag app-authored messages carrying `subtype: "thread_broadcast"` where broadcasting was probably unintended.
- **repair**: Always store the **root** `ts`. When capturing from a `chat.postMessage` response, use `response.ts` only if you posted the root; when responding to an event, use `event.thread_ts || event.ts`, which yields the root in both cases. Set `reply_broadcast: true` deliberately and rarely — it pushes the reply into the channel and surprises people.
- **category**: Messaging and Block Kit
- **sources**: https://docs.slack.dev/messaging/retrieving-messages · https://docs.slack.dev/reference/methods/conversations.replies · https://stackoverflow.com/questions/55656395

## chat-update-message-not-found

- **slug**: `chat-update-message-not-found`
- **title**: message_not_found: the ts being updated no longer exists
- **symptom**: `{"ok": false, "error": "message_not_found"}` from `chat.update` or `chat.delete`. The status message the bot has been editing for the last hour has vanished — someone deleted it, or the channel argument is wrong.
- **mechanism**: `chat.update` identifies a message by the pair (`channel`, `ts`) and both must match exactly. The common failures: the `ts` was captured from a different channel; the `ts` was stored with lost float precision (a Slack `ts` like `1701234567.123456` must be treated as a **string** — parsing it as a float loses digits and no longer matches); the message was deleted; or the message was posted by an incoming webhook, which returns no `ts` at all so there is nothing valid to store.
- **detect**: For each stored (channel, ts) pair the app updates, call `conversations.history?channel=<C...>&latest=<ts>&oldest=<ts>&inclusive=true&limit=1` and check that exactly one message is returned with a matching `ts`. Zero results means deleted or wrong channel. Additionally scan stored `ts` values for the float-precision fingerprint: a `ts` with fewer than six digits after the decimal point, or one that came back from a JSON parser as a number rather than a string, is corrupted.
- **repair**: Store `ts` as a string, everywhere, including in JSON columns and message queues — never as a float or a JS `number`. Store the `channel` id alongside it. Before updating, tolerate `message_not_found` by falling back to posting a fresh message and re-capturing its `ts`. For webhook-posted messages there is no update path at all; switch to `chat.postMessage` if you need to edit later.
- **category**: Messaging and Block Kit
- **sources**: https://stackoverflow.com/questions/46455540 · https://docs.slack.dev/reference/methods/chat.update · https://stackoverflow.com/questions/56291169

## cant-update-or-delete-message

- **slug**: `cant-update-or-delete-message`
- **title**: cant_update_message: the message belongs to another author
- **symptom**: `{"ok": false, "error": "cant_update_message"}` or `cant_delete_message`. The bot can edit its own posts but not the ones it "sent" through a webhook or as a different identity.
- **mechanism**: A message can only be edited or deleted by the identity that authored it. A bot token can modify messages authored by that bot; a user token can modify that user's messages. Messages posted with `username`/`icon_emoji` overrides still belong to the bot and are editable, but messages from an incoming webhook, from a different app, or from a human are not. Deleting *other people's* messages requires `chat:write` on a **user** token belonging to an admin, and even then is restricted by workspace policy.
- **detect**: `conversations.history?channel=<C...>&limit=200` and inspect each message's authorship fields: `bot_id`, `app_id`, `user`, and `bot_profile.id`. Compare against `auth.test`'s `bot_id` / `user_id`. Any message the app attempts to update whose `bot_id` differs from the app's own is unmodifiable. The check is exact and cheap, and it distinguishes this from [`chat-update-message-not-found`](#chat-update-message-not-found), where the message simply does not exist.
- **repair**: Only update messages the app itself posted, and record the authoring identity alongside the `ts`. For interactive updates in response to a button click, use the interaction's `response_url` with `replace_original: true` — that path can replace the original message regardless of the token used to post it, within a 30-minute / 5-use window. To delete a human's message you need an admin user token and `chat:write` on it.
- **category**: Messaging and Block Kit
- **sources**: https://stackoverflow.com/questions/55381314 · https://stackoverflow.com/questions/48370501 · https://docs.slack.dev/reference/methods/chat.delete

## ephemeral-user-not-in-channel

- **slug**: `ephemeral-user-not-in-channel`
- **title**: user_not_in_channel: ephemeral posts to a non-member
- **symptom**: `chat.postEphemeral` returns `{"ok": false, "error": "user_not_in_channel"}`, or returns `ok: true` with a `message_ts` and the user never sees anything.
- **mechanism**: An ephemeral message is rendered into a specific user's view of a specific channel. If that user is not a member of the channel, there is no view to render into. Ephemeral messages are also not persisted: they cannot be updated after the session, cannot be deleted, do not appear in `conversations.history`, and vanish when the client reloads. Apps that use them for anything the user must be able to come back to are misusing the primitive.
- **detect**: For each intended ephemeral recipient and channel, verify membership before sending: `conversations.members?channel=<C...>` (paginated) or `users.conversations?user=<U...>&types=public_channel,private_channel` and check for the channel. Confirm the user is active with `users.info?user=<U...>` → `deleted === false`. Capture observed `user_not_in_channel` errors. Separately, flag any app that relies on ephemeral messages for durable content, since a read-only audit will find those messages entirely absent from `conversations.history` — that absence is the design smell.
- **repair**: Check membership first and fall back to a DM (`conversations.open` then `chat.postMessage`) when the user is not in the channel. Reserve ephemeral messages for transient acknowledgements ("Got it, working on that…") and use a DM or a real channel message for anything the user needs to keep.
- **category**: Messaging and Block Kit
- **sources**: https://docs.slack.dev/reference/methods/chat.postEphemeral · https://stackoverflow.com/questions/47496747 · https://stackoverflow.com/questions/57323244

## scheduled-message-in-past

- **slug**: `scheduled-message-in-past`
- **title**: time_in_past: scheduled sends land behind the clock
- **symptom**: `{"ok": false, "error": "time_in_past"}` from `chat.scheduleMessage`, intermittently and usually near the boundary of a scheduling window. Or `invalid_time`, or `time_too_far` for anything beyond 120 days.
- **mechanism**: `post_at` is a Unix timestamp in **seconds**, must be in the future at the moment Slack processes it, and must be within 120 days. Failures come from passing milliseconds (JavaScript's `Date.now()` yields ms and produces an absurd future timestamp, or a past one after a naive divide), from timezone arithmetic that produces a local-time value interpreted as UTC, and from scheduling "now + 5 seconds" where queuing latency pushes the send past the target before Slack sees it.
- **detect**: `chat.scheduledMessages.list?limit=100` (needs the same `chat:write` family; read-only inspection of the queue) returns `scheduled_messages[]` with `post_at`, `date_created`, `channel_id` and `id`. Check every `post_at` for plausibility: values with 13 digits are milliseconds; values more than 120 days out will never fire; values very close to `date_created` are at risk. Capture observed `time_in_past` errors from the send path.
- **repair**: Compute `post_at` as `Math.floor(targetDate.getTime() / 1000)` and assert `post_at > now + 60` before sending. Do timezone math in UTC and convert only for display. For near-term sends, post immediately rather than scheduling — `chat.scheduleMessage` is for hours and days, not seconds.
- **category**: Messaging and Block Kit
- **sources**: https://docs.slack.dev/reference/methods/chat.scheduleMessage · https://docs.slack.dev/reference/methods/chat.scheduledMessages.list · https://stackoverflow.com/questions/41938045

## scheduled-messages-orphaned

- **slug**: `scheduled-messages-orphaned`
- **title**: Hundreds of scheduled messages queued and forgotten
- **symptom**: A reminder bot is redeployed with new logic and users start receiving *both* the new reminders and old ones scheduled by the previous version — including reminders for tasks that were completed weeks ago.
- **mechanism**: `chat.scheduleMessage` hands the message to Slack, which holds it for up to 120 days and delivers it regardless of what happens to your application in the meantime. Deleting the database row, redeploying, or even uninstalling and reinstalling the app does not cancel a scheduled message; only `chat.deleteScheduledMessage` with the returned `scheduled_message_id` does. Every deploy that changes scheduling logic without draining the queue leaves a tail of zombie sends.
- **detect**: `chat.scheduledMessages.list?limit=100` with cursor pagination, optionally filtered by `channel`, `oldest` and `latest`. Report the total count, the distribution of `post_at` into the future, and — critically — the count of scheduled messages whose `id` does **not** appear in your application's own records. Any queued message the app cannot account for is an orphan. A queue that keeps growing run over run indicates messages are being scheduled and never cancelled.
- **repair**: Persist every returned `scheduled_message_id` and cancel it with `chat.deleteScheduledMessage` when the underlying reason disappears. Add a reconciliation job that lists the queue, diffs against your records, and cancels the orphans. On deploys that change scheduling semantics, drain the queue as a migration step rather than leaving it to fire.
- **category**: Messaging and Block Kit
- **sources**: https://docs.slack.dev/reference/methods/chat.scheduledMessages.list · https://docs.slack.dev/reference/methods/chat.deleteScheduledMessage

## unfurl-domain-not-configured

- **slug**: `unfurl-domain-not-configured`
- **title**: Links never unfurl because no domain is registered
- **symptom**: The app implements a `link_shared` handler and it never fires. Links to the app's own product post as bare URLs with no preview. No error appears anywhere.
- **mechanism**: The `link_shared` event is delivered **only** for domains the app has explicitly registered under **Event Subscriptions → App unfurl domains**, and only when the app holds the `links:read` scope. Unfurling then requires `links:write` and a `chat.unfurl` call. Registering the domain, subscribing to `link_shared`, and holding both scopes are four separate steps, and missing any one produces total silence rather than an error. Slack also suppresses `link_shared` for links posted by the app itself and honors per-user unfurl preferences.
- **detect**: `apps.manifest.export?app_id=<A...>` → check `settings.event_subscriptions.bot_events` for `link_shared` and the unfurl domain list in the manifest. Check `X-OAuth-Scopes` for `links:read` (receive the event) and `links:write` (respond to it). Behaviorally, `conversations.history?channel=<C...>&limit=200` shows posted messages: entries containing URLs on the app's domain with no `attachments` and no unfurl metadata, in a channel where the app is present, confirm unfurling is not happening.
- **repair**: Register the domain (apex only — Slack matches the domain and its subdomains) under **Event Subscriptions → App unfurl domains**, add `links:read` and `links:write` to bot scopes, subscribe to `link_shared`, and reinstall. Then handle the event by calling `chat.unfurl` with `channel`, `ts`, and an `unfurls` map keyed by the exact URL string from the event.
- **category**: Messaging and Block Kit
- **sources**: https://docs.slack.dev/reference/events/link_shared · https://docs.slack.dev/reference/methods/chat.unfurl · https://docs.slack.dev/messaging/unfurling-links-in-messages

## trigger-id-expired

- **slug**: `trigger-id-expired`
- **title**: expired_trigger_id: the modal opened too late
- **symptom**: Clicking a button sometimes opens a modal and sometimes shows "We had some trouble connecting. Try again?". `views.open` returns `expired_trigger_id`, `exchanged_trigger_id`, or `invalid_trigger_id`. Reported failures occur well inside the documented 3-second window — several issues report expiry in under 500ms.
- **mechanism**: A `trigger_id` from an interaction payload is **single-use** and short-lived — nominally three seconds, in practice often less. Any work performed before `views.open` — a database read, an API call, a cold start — burns the budget. Reusing a `trigger_id` for a second `views.push` after already exchanging it gives `exchanged_trigger_id`. `view_submission` payloads contain a *new* `trigger_id` that must be used if you want to open a follow-up modal, and using the original one fails.
- **detect**: Purely symptom-based; a read token cannot inspect trigger state. Capture and classify: `expired_trigger_id` (too slow), `exchanged_trigger_id` (reused), `invalid_trigger_id` (malformed — the expected shape is `132456.7890123.abcdef`). The indirect workspace signal is the absence of expected side effects: modal-driven records that never appear despite users reporting they submitted the form. Measure the app's general ack latency from [`three-second-timeout`](#three-second-timeout) — an app that is slow to ack will also be slow to exchange triggers.
- **repair**: Call `views.open` as the **very first** action in the handler, before any I/O — open a lightweight "Loading…" modal immediately, then replace its content with `views.update` using the returned `view.id` once the data arrives. Never fetch before opening. For chained modals, use `views.push` with the `trigger_id` from the *current* payload, and for follow-ups after submission use the `trigger_id` on the `view_submission` payload.
- **category**: Messaging and Block Kit
- **sources**: https://docs.slack.dev/reference/methods/views.open · https://github.com/slackapi/node-slack-sdk/issues/597 · https://github.com/slackapi/bolt-js/issues/1662

## duplicate-messages-no-dedupe

- **slug**: `duplicate-messages-no-dedupe`
- **title**: The same message is posted repeatedly with no idempotency
- **symptom**: A channel accumulates the same alert three, five, ten times. Sometimes from event retries, sometimes from a job that reruns, sometimes from two replicas doing the same work. Slack has no built-in deduplication and posts every one.
- **mechanism**: `chat.postMessage` has no idempotency key. Unlike payment APIs, there is no `Idempotency-Key` header and no client-side token that Slack will honor to collapse repeats. Every call creates a new message. Any at-least-once delivery mechanism upstream — event retries, queue redelivery, cron overlap, multi-replica schedulers — therefore produces duplicate messages unless the application deduplicates before calling.
- **detect**: This is the most directly observable problem in the entire catalogue. `conversations.history?channel=<C...>&limit=200` per target channel; group app-authored messages by a hash of (`text` + serialized `blocks`) and report every group with more than one member, along with the `ts` spread. Classify by spacing: sub-second → double subscription or multi-replica; ~60s / ~300s → Slack event retries; hours → scheduler overlap. Report duplicate rate as a percentage of app-authored messages so the finding is quantified.
- **repair**: Deduplicate at the source with a natural idempotency key — `event.event_id` for event-driven sends, a business key (`incident_id` + `state`) for alerting. Keep a short-TTL set of already-sent keys and check before posting. For status that changes over time, post once and `chat.update` the same `ts` rather than posting again. For cron jobs, take a distributed lock so overlapping runs cannot both send.
- **category**: Messaging and Block Kit
- **sources**: https://github.com/slackapi/bolt-python/issues/764 · https://docs.slack.dev/reference/methods/chat.postMessage · https://github.com/slackapi/bolt-python/issues/1302

---

# Files and uploads

## files-upload-retired

- **slug**: `files-upload-retired`
- **title**: The retired files.upload method is still being called
- **symptom**: `{"ok": false, "error": "method_deprecated"}` — or, for apps created after 8 May 2024, failure from day one. Screenshot and report attachments stop working across a fleet of internal tools simultaneously.
- **mechanism**: Slack deprecated `files.upload` on 16 May 2024 (newly created apps blocked immediately) and sunset it for **all** apps on **12 November 2025** (the date was moved from an original 11 March 2025). The replacement is a three-call sequence: `files.getUploadURLExternal` to obtain a one-time upload URL and `file_id`, a plain `POST` of the bytes to that URL, then `files.completeUploadExternal` to register the file and share it into channels. The SDKs wrap this as `filesUploadV2` / `files_upload_v2`, which is where most of the migration pain now lives.
- **detect**: Call `files.upload` with no arguments and read the error: `method_deprecated` or `deprecated_endpoint` confirms the method is dead for this app; `no_file_data` or `missing_scope` would indicate it is still (temporarily) live. Corroborate with the manifest's app creation date and with `files.list?count=100` — an app whose most recent file is older than the cutover is very likely still on the dead path. Also scan for the `warning` field on responses, which carried deprecation notices before the sunset.
- **repair**: Migrate to the three-step flow. Minimum viable: `files.getUploadURLExternal?filename=<name>&length=<bytes>` → `POST` the raw bytes to `upload_url` → `files.completeUploadExternal?files=[{"id":"<file_id>","title":"<t>"}]&channel_id=<C...>&initial_comment=<text>`. Prefer the SDK helpers (`client.filesUploadV2({...})`) which handle sequencing and retries. Note `channel_id` in the new flow requires a channel **ID**; names and user IDs are rejected.
- **category**: Files and uploads
- **sources**: https://docs.slack.dev/changelog/2024/05/16/apps/ · https://docs.slack.dev/changelog/2024-04-a-better-way-to-upload-files-is-here-to-stay/ · https://github.com/slackapi/bolt-js/issues/2448

## incomplete-external-upload

- **slug**: `incomplete-external-upload`
- **title**: getUploadURLExternal was never completed, orphaning files
- **symptom**: The upload "succeeds" — no exception — and the file never appears in the channel. Sometimes a message posts with a broken reference. Sometimes `files.completeUploadExternal` returns `missing_scope` after the bytes have already been uploaded, leaving a half-created file and a message that mentions it.
- **mechanism**: The new upload flow is three network operations, and only the first and last are Slack Web API calls. A failure at any step leaves inconsistent state: bytes uploaded but never registered (an orphan `file_id` with no channel share), or registered but never shared. Because the SDK helper wraps the sequence, a `missing_scope` on the final call surfaces as an upload error even though the earlier steps succeeded. A known SDK bug also dropped per-call token overrides between steps, producing `not_authed` mid-sequence.
- **detect**: `files.list?count=100&types=all` (needs `files:read`) returns each file with `channels[]`, `groups[]`, `ims[]` and `shares`. Files where all of those are empty are **uploaded but never shared** — orphans. Report the count and total size. Cross-check `files.info?file=<F...>` for individual files referenced in messages: `file_not_found` on a `file_id` your app recorded proves the sequence broke. Also verify `X-OAuth-Scopes` contains `files:write` — the completion step needs it even though the byte upload does not.
- **repair**: Treat the three steps as a transaction: on failure at step 2 or 3, record the `file_id` and retry completion, or delete the orphan with `files.delete`. Ensure `files:write` is granted *before* the first step so the sequence cannot fail halfway. Pass the channel as an `ID` in `channel_id`. Use the SDK's `filesUploadV2` rather than hand-rolling, and pin a version past the token-propagation fixes.
- **category**: Files and uploads
- **sources**: https://github.com/slackapi/node-slack-sdk/issues/1620 · https://github.com/slackapi/node-slack-sdk/issues/1644 · https://docs.slack.dev/reference/methods/files.completeUploadExternal

## file-not-shared-to-channel

- **slug**: `file-not-shared-to-channel`
- **title**: Files upload successfully but appear in no channel
- **symptom**: `files.list` shows the files, the app logs success, and no human can find them. The files exist in the workspace, owned by the app, visible to nobody.
- **mechanism**: Uploading and sharing are separate concerns. `files.completeUploadExternal` shares only if `channel_id` is supplied; without it the file is created privately, owned by the uploading identity, with an empty `shares` object. The legacy `files.upload` had the same split via its `channels` parameter. Apps that upload first and intend to "post a link later" often never do, or post `permalink` which is inaccessible to anyone the file was not shared with.
- **detect**: `files.list?count=100&types=all` and inspect each entry's `shares` object — `shares.public` and `shares.private` maps are empty for unshared files — plus the legacy `channels[]`, `groups[]`, `ims[]` arrays. Report every file with no share target. `files.info?file=<F...>` gives the same per-file. A high proportion of unshared app-owned files is conclusive.
- **repair**: Pass `channel_id` (a `C`/`G`/`D` id) to `files.completeUploadExternal` at upload time, together with `initial_comment` for context. To share an already-uploaded file, post a message containing its `permalink` into the channel — Slack expands it and grants channel members access. Note `files.sharedPublicURL` is a different and riskier mechanism (see [`public-file-links-exposed`](#public-file-links-exposed)).
- **category**: Files and uploads
- **sources**: https://docs.slack.dev/reference/methods/files.completeUploadExternal · https://github.com/slackapi/python-slack-sdk/issues/1575 · https://docs.slack.dev/reference/methods/files.list

## file-not-visible

- **slug**: `file-not-visible`
- **title**: not_visible: the token cannot see a file it uploaded
- **symptom**: `{"ok": false, "error": "not_visible"}` from `files.info`, or `access_denied` on a Slack Connect file. The file id came out of an event payload, so it definitely exists.
- **mechanism**: File visibility follows conversation visibility. A file shared only into a private channel the bot is not a member of, a DM between two other people, or an externally shared Slack Connect channel is invisible to the app's token even though the app received a `file_shared` event referencing it (events carry ids more liberally than the API grants access). `not_visible` means "exists but not for you"; `file_not_found` means "no such file for this token." The distinction matters because one is fixed by membership and the other by a correct id.
- **detect**: `files.info?file=<F...>` and classify the error: `not_visible` → permission; `file_not_found` → wrong id or wrong workspace; `file_deleted` → gone; `access_denied` → Slack Connect restriction. For files you can see, `files.info` returns `channels[]`/`groups[]`/`ims[]` — cross-reference against `users.conversations` for the bot to confirm membership in at least one sharing conversation. Also check `X-OAuth-Scopes` for `files:read`.
- **repair**: Get the bot invited to the conversation where the file lives, or have the file shared into a channel the bot belongs to. Add `files:read` if absent. For Slack Connect, admins control file sharing across external channels — the errors `slack_connect_file_link_sharing_blocked` and `slack_connect_canvas_sharing_blocked` mean the policy, not your app, is the blocker.
- **category**: Files and uploads
- **sources**: https://docs.slack.dev/reference/methods/files.info · https://docs.slack.dev/reference/methods/files.list

## file-deleted-link-rot

- **slug**: `file-deleted-link-rot`
- **title**: file_deleted: stored file IDs point at deleted files
- **symptom**: An index or knowledge base built from Slack files returns `{"ok": false, "error": "file_deleted"}` for a growing share of entries. Message blocks that embed file permalinks render as broken.
- **mechanism**: Files are deleted by their owner, by admins during cleanup, or automatically by workspace file retention policy. The `file_id` remains a valid-looking string and every stored reference to it — in a database, in an already-posted message's blocks, in a search index — becomes dangling. Slack emits a `file_deleted` event, but only to apps subscribed to it with `files:read`.
- **detect**: Batch-verify stored ids with `files.info?file=<F...>` and count `file_deleted` versus `ok: true`. Report the dangling fraction and, if you store an ingestion timestamp, the decay rate. `files.list?count=100&ts_from=<epoch>` lets you compare "files Slack currently has" against "files you think exist" for a time window; the difference is deletion. Rising dangling counts over successive audits indicate retention is actively pruning.
- **repair**: Subscribe to the `file_deleted` event and remove references when it fires. Re-validate stored references on a schedule and tombstone the dead ones rather than surfacing broken links. If the content matters beyond Slack's retention window, copy the bytes to your own store at ingestion time using the authenticated `url_private_download` — Slack is not an archive.
- **category**: Files and uploads
- **sources**: https://docs.slack.dev/reference/methods/files.info · https://docs.slack.dev/reference/events/file_deleted

## file-download-without-auth

- **slug**: `file-download-without-auth`
- **title**: Downloading url_private without a bearer header yields HTML
- **symptom**: The downloader "succeeds" with a 200 and writes a file — which turns out to be Slack's HTML sign-in page, a few kilobytes of markup where a PDF should be. Image parsers fail with cryptic format errors.
- **mechanism**: `url_private` and `url_private_download` require an `Authorization: Bearer <token>` header. Fetching them without one returns **HTTP 200** with a login page rather than a 401 — the same 200-means-nothing trap as the Web API, in a different place. Anything that follows redirects and saves the body gets HTML. The related `permalink` is a web page, not the file, and `permalink_public` (only present after `files.sharedPublicURL`) points at a wrapper page rather than raw bytes.
- **detect**: `files.info?file=<F...>` returns `url_private`, `url_private_download`, `mimetype`, `filetype`, `size` and `permalink`. Fetch `url_private_download` **with** the bearer header and compare the returned `Content-Type` and byte length against the file's `mimetype` and `size` from the API. A response whose `Content-Type` is `text/html` while `mimetype` says `application/pdf`, or whose length is a few KB against a reported multi-MB `size`, is the unauthenticated-fetch failure. Repeat without the header to confirm the 200-with-HTML behavior.
- **repair**: Send `Authorization: Bearer <bot token>` on every fetch of `url_private` / `url_private_download`, and validate the response `Content-Type` against the API-reported `mimetype` before saving. Never use `permalink` as a download URL. Follow redirects only with the header preserved — some HTTP clients strip `Authorization` across redirects, which reproduces the bug.
- **category**: Files and uploads
- **sources**: https://stackoverflow.com/questions/36144761 · https://docs.slack.dev/reference/methods/files.info · https://stackoverflow.com/questions/57253156

## public-file-links-exposed

- **slug**: `public-file-links-exposed`
- **title**: Files were made public and are readable without Slack
- **symptom**: Nothing errors. An app called `files.sharedPublicURL` to get an embeddable image URL, and every file it has ever uploaded — including customer exports and screenshots containing credentials — is now readable by anyone with the link, indefinitely, with no Slack login.
- **mechanism**: `files.sharedPublicURL` flips a file to public and returns `permalink_public`, an unauthenticated URL. It is commonly reached for as a workaround for the fact that Block Kit `image_url` must be publicly fetchable and `url_private` is not. The setting persists until explicitly revoked with `files.revokePublicURL`, survives the file being unshared from every channel, and is not covered by channel permissions at all. Workspace admins can disable public file sharing entirely, which is the safe default many organizations do not know to set.
- **detect**: `files.list?count=100&types=all` with `files:read` returns each file's `public_url_shared` and `is_public` flags plus `permalink_public`. Report every file with `public_url_shared: true`, and sort by `size`/`created` so recent and large exposures surface first. Verify exposure empirically by fetching a `permalink_public` with **no** Authorization header — a 200 with real content confirms it. `files.info?file=<F...>` gives the same fields per file.
- **repair**: Call `files.revokePublicURL?file=<F...>` for every file that should not be public (needs `files:write`). Stop using public URLs to satisfy Block Kit images: host images on your own infrastructure, or upload to Slack and reference the file in the message so channel permissions apply. Ask an admin to disable public file sharing workspace-wide if the app has no legitimate need for it.
- **category**: Files and uploads
- **sources**: https://docs.slack.dev/reference/methods/files.sharedPublicURL · https://docs.slack.dev/reference/methods/files.revokePublicURL · https://stackoverflow.com/questions/57253156

## file-size-limit

- **slug**: `file-size-limit`
- **title**: Uploads over the 1 GB per-file ceiling are rejected
- **symptom**: Small attachments work, large ones fail — with `file_too_large`, an `internal_error`, a timeout on the byte upload, or a zero-byte file that appears in Slack with no content.
- **mechanism**: Slack caps individual files at 1 GB, and practical limits are much lower: the `length` parameter to `files.getUploadURLExternal` must match the actual byte count or the upload URL rejects the body, and multi-hundred-megabyte uploads time out well before the ceiling. Reports of failures above ~20 MB with the SDK helpers are common. Workspaces also have an aggregate storage quota on paid plans, and free plans limit total file storage — hitting either produces upload failures unrelated to the individual file's size.
- **detect**: `files.list?count=100&types=all` returns `size` in bytes per file; report the maximum and the distribution, and flag anything approaching the ceiling. Compare each file's reported `size` against what the app believes it uploaded — a mismatch means a truncated or mis-declared upload. `team.info` and, on Enterprise, `admin.usergroups`/analytics surfaces give workspace context. Zero-byte files in `files.list` (`size: 0`) are the clearest fingerprint of a broken byte upload.
- **repair**: Compute `length` from the actual byte count (not the string length, which differs for non-ASCII) and pass it exactly. For large artifacts, upload to object storage and post a link instead — Slack is a poor file server. Compress or split where the content genuinely belongs in Slack, and set generous client timeouts on the byte-upload step, which is a plain HTTP POST to a non-Slack host and does not inherit your Slack client's retry configuration.
- **category**: Files and uploads
- **sources**: https://docs.slack.dev/reference/methods/files.getUploadURLExternal · https://github.com/slackapi/python-slack-sdk/issues/1681 · https://docs.slack.dev/reference/methods/files.list

## file-retention-deletes-history

- **slug**: `file-retention-deletes-history`
- **title**: Workspace retention deletes files the app still references
- **symptom**: An audit trail built on Slack files develops holes at a fixed age — everything older than 90 days is `file_deleted`. Message history has the same shape: `conversations.history` returns fewer messages than expected for old ranges.
- **mechanism**: Workspace and Enterprise Grid admins set retention policies that automatically delete messages and files after a fixed period. Free plans additionally limit visible history. Neither is announced to apps; files and messages simply stop existing. An integration treating Slack as its system of record inherits the retention policy as its data-loss policy, usually without anyone deciding that.
- **detect**: Probe the horizon. `conversations.history?channel=<C...>&oldest=<epoch 1 year ago>&latest=<epoch 11 months ago>&limit=10` — an empty result for a channel that was demonstrably active then indicates retention (or the free-plan history limit). Do the same with `files.list?ts_from=<old>&ts_to=<older>&count=10`. Find the boundary by bisecting on `oldest`: the age at which results stop appearing is the effective retention window. Report that number. Batch-verify stored file ids with `files.info` and correlate the `file_deleted` fraction against age.
- **repair**: Copy anything that must persist into your own store at ingestion time — message text plus `ts`, and file bytes via the authenticated `url_private_download`. Ask admins for the actual retention setting so the app's expectations match reality, and document Slack as a transport rather than an archive. On Enterprise Grid, the Discovery and Audit Logs APIs exist for compliance retention and are the right tool when true retention is required.
- **category**: Files and uploads
- **sources**: https://docs.slack.dev/reference/methods/conversations.history · https://docs.slack.dev/reference/methods/files.list · https://docs.slack.dev/reference/methods/files.info

---

# Socket Mode and connections

## socket-mode-and-request-url-both-on

- **slug**: `socket-mode-and-request-url-both-on`
- **title**: Socket Mode and an HTTP Request URL are both configured
- **symptom**: Every event is handled twice in development and once in production, or vice versa. Two instances of the app — one local on Socket Mode, one deployed on HTTP — both act on the same events, producing duplicated messages and duplicated side effects.
- **mechanism**: Enabling Socket Mode switches event delivery to the WebSocket, but the previously configured Request URL remains stored in the app configuration. Teams that develop locally with Socket Mode and deploy with HTTP end up with both paths configured against a single app, and whichever processes are running receive the traffic. Because Slack has no notion of environments, one app configuration is shared by every environment that uses it.
- **detect**: `apps.manifest.export?app_id=<A...>` → read `settings.socket_mode_enabled` together with `settings.event_subscriptions.request_url` and `settings.interactivity.request_url`. `socket_mode_enabled: true` with a non-empty `request_url` is the finding. Corroborate behaviorally with `conversations.history?channel=<C...>&limit=200`: duplicate app-authored messages with sub-second `ts` spacing (not the 60s/300s retry pattern) point at two live delivery paths rather than at retries.
- **repair**: Pick one delivery mode per app. Create a **second Slack app** for development with Socket Mode enabled and no Request URL, and keep the production app on HTTP with Socket Mode off (or the reverse) — two manifests, two app ids, two token sets. Slack provides no environment separation, so app duplication is the supported pattern.
- **category**: Socket Mode and connections
- **sources**: https://docs.slack.dev/apis/events-api/using-socket-mode · https://stackoverflow.com/questions/57065187 · https://docs.slack.dev/reference/methods/apps.manifest.export

## socket-mode-blocks-distribution

- **slug**: `socket-mode-blocks-distribution`
- **title**: A Socket Mode app cannot be listed on the Marketplace
- **symptom**: An app built and tested with Socket Mode is submitted to the Slack Marketplace and rejected. The team discovers late that the entire delivery architecture must be rewritten before distribution is possible.
- **mechanism**: Slack does not permit Socket Mode apps in the public Marketplace — a distributed app must expose a public HTTPS Request URL. Socket Mode is designed for apps behind firewalls and for internal or org-ready deployment. Since Marketplace approval is also what restores full `conversations.history` rate limits for commercially distributed apps (see [`non-marketplace-history-clamp`](#non-marketplace-history-clamp)), this constraint compounds: a Socket Mode app that reads history is locked into the 1-request-per-minute clamp with no path out short of an architectural change.
- **detect**: `apps.manifest.export?app_id=<A...>` → `settings.socket_mode_enabled === true` combined with `settings.is_distributed` / the presence of a public OAuth redirect configuration indicates an app intended for distribution but built on Socket Mode. Corroborate with `auth.test` across your installation store: tokens for more than one `team_id` prove the app is already distributed. Socket Mode plus multiple external workspaces is the finding.
- **repair**: Move to the HTTP Events API before submission: stand up a public HTTPS Request URL, configure Event Subscriptions and Interactivity URLs, disable Socket Mode, and re-verify. Bolt supports both receivers, so the application code usually survives the change — it is the deployment that must gain a public endpoint. Keep Socket Mode for the internal development app.
- **category**: Socket Mode and connections
- **sources**: https://docs.slack.dev/apis/events-api/using-socket-mode · https://docs.slack.dev/changelog/2025/05/29/rate-limit-changes-for-non-marketplace-apps/

## connections-open-unusable

- **slug**: `connections-open-unusable`
- **title**: apps.connections.open is unusable with the token on hand
- **symptom**: The app starts, fails to obtain a WebSocket URL, and retries in a tight loop forever with no events delivered. Errors seen include `missing_scope`, `invalid_auth`, and `not_allowed_token_type`. In one known SDK bug the reconnect loop treats `missing_scope` as transient and never surfaces it.
- **mechanism**: `apps.connections.open` accepts **only** an app-level (`xapp-`) token carrying `connections:write`, passed in the Authorization header. A bot token gives `not_allowed_token_type`; an app-level token without the scope gives `missing_scope`; a token belonging to a different app gives an auth mismatch. The failure is at connection establishment, before any application code runs, so the app looks alive while being completely deaf.
- **detect**: A read-only script must not call `apps.connections.open` (it mints a connection). Probe the same credential through the read-only app-level method instead: `POST apps.event.authorizations.list` with `Authorization: Bearer <xapp-...>` and a dummy `event_context`. `invalid_event_context` → the token is a valid app-level token for this app; `missing_scope` → scopes are wrong; `auth_mismatch` → wrong app. Combine with `apps.manifest.export` → `settings.socket_mode_enabled: true`. Socket Mode enabled plus an app-level token that fails this probe is conclusive.
- **repair**: Generate an app-level token in **Basic Information → App-Level Tokens** with `connections:write` (add `authorizations:read` in the same token if the app is multi-install), set it as `SLACK_APP_TOKEN`, and assert the `xapp-` prefix at startup. Make the connection failure fatal rather than retried indefinitely, so a misconfigured token crashes the process instead of producing a silent no-op.
- **category**: Socket Mode and connections
- **sources**: https://docs.slack.dev/apis/events-api/using-socket-mode · https://github.com/slackapi/bolt-js/issues/1748 · https://github.com/slackapi/node-slack-sdk/issues/1495

## socket-connection-cap

- **slug**: `socket-connection-cap`
- **title**: More than 10 concurrent Socket Mode connections
- **symptom**: The app disconnects with reason `too_many_websockets` and then cannot reconnect. Interactive payloads — button clicks, modal submits — are silently lost while events still partly work. Reported even by teams running a single instance.
- **mechanism**: Slack allows an app **10** concurrent Socket Mode connections. Reconnects that do not cleanly close the previous socket leak server-side registrations, so a client behind NAT, or one whose force-close path is broken, accumulates phantom connections until the cap is reached — at which point new connections are refused and the surviving stale sockets receive payloads nobody is listening on. Because Slack routes each payload to *one* of the open connections unpredictably, a partially leaked set produces intermittent, maddening loss rather than a clean outage. Multiple replicas each opening a socket reach the cap much faster.
- **detect**: The connection count is not exposed to a read token, so detect the consequences. Behavioral: intermittent, non-deterministic loss of interactions while some events still arrive — visible as user-reported actions with no corresponding app-authored message in `conversations.history` for a fraction of attempts. Structural: `apps.manifest.export` → `socket_mode_enabled: true`, cross-referenced with the deployed replica count; replicas × sockets-per-replica approaching 10 is the arithmetic finding. Record any observed `too_many_websockets` disconnect reason from the app's logs where available.
- **repair**: Run **one** Socket Mode connection per app instance and a small, bounded number of instances — Socket Mode does not scale horizontally the way HTTP does. Ensure the client force-closes the old socket before opening a new one, and upgrade the SDK past the known close-path regressions. For real horizontal scale, move to the HTTP Events API behind a load balancer.
- **category**: Socket Mode and connections
- **sources**: https://github.com/slackapi/python-slack-sdk/issues/1940 · https://github.com/slackapi/node-slack-sdk/issues/1654 · https://docs.slack.dev/apis/events-api/using-socket-mode

## refresh-requested-unhandled

- **slug**: `refresh-requested-unhandled`
- **title**: refresh_requested disconnects are treated as crashes
- **symptom**: The process dies or logs a fatal error every few hours at seemingly random times. A supervisor restarts it, so events are lost only for the restart window and nobody investigates.
- **mechanism**: Slack deliberately refreshes Socket Mode connections every few hours. It sends a `disconnect` message with `reason: "refresh_requested"`, preceded by a `warning` roughly 10 seconds ahead so the client can open a replacement connection before the old one closes. A client that treats any disconnect as an error, or that closes and reopens serially rather than overlapping, drops payloads in the gap. The other documented reason, `link_disabled`, means Socket Mode was toggled off in the app config and reconnecting will never succeed.
- **detect**: Not directly visible to a read token. The workspace-side signature is periodic gaps: messages in `conversations.history` that should have triggered the app, clustered at regular multi-hour intervals with no corresponding app response, while the app responds normally in between. Establish the app's expected response pattern from healthy periods and report the periodic gaps. Structurally, confirm `settings.socket_mode_enabled: true` in the manifest so the finding is attributed to the right transport.
- **repair**: Handle `disconnect` by reason: on `refresh_requested` (and on the 10-second `warning`), open a **new** connection first and close the old one only after the new one receives `hello` — overlap, do not swap. On `link_disabled`, stop reconnecting and surface a configuration error. The official Socket Mode clients implement the overlap; the repair for most apps is to stop hand-rolling the WebSocket layer.
- **category**: Socket Mode and connections
- **sources**: https://docs.slack.dev/apis/events-api/using-socket-mode · https://github.com/slackapi/node-slack-sdk/issues/1243 · https://github.com/slackapi/bolt-js/issues/2496

## socket-mode-single-instance

- **slug**: `socket-mode-single-instance`
- **title**: Multiple replicas each open a socket and duplicate work
- **symptom**: Scaling the deployment from 1 to 3 pods causes every mention to be answered once — but sometimes twice, sometimes not at all. The behavior is non-deterministic and changes with pod restarts.
- **mechanism**: With several Socket Mode connections open, Slack routes each payload to one of them "without predictable distribution patterns." That is *not* a work queue: there is no consumer-group semantics, no acknowledgement-based redelivery to a different consumer, and no ordering guarantee. Some payloads land on a pod that is mid-restart and are lost; app-level retries or double subscription cause others to be handled twice. Teams reach for replicas expecting load balancing and get non-deterministic delivery instead.
- **detect**: Workspace-visible. `conversations.history?channel=<C...>&limit=200` for duplicate app-authored responses with sub-second spacing (multiple pods acting) interleaved with human messages that received **no** response at all (payload landed on a dead pod). The combination of duplicates *and* misses in the same channel is the distinctive fingerprint — retries produce duplicates without misses, and outages produce misses without duplicates. Quantify both rates.
- **repair**: Run Socket Mode as a singleton (one replica, restarted on failure) and put any real concurrency behind it in a queue that your own code controls. If the workload requires multiple processing nodes, keep one Socket Mode receiver that immediately enqueues payloads and scale the workers. For genuine multi-node ingress, switch to the HTTP Events API where a load balancer provides real distribution.
- **category**: Socket Mode and connections
- **sources**: https://docs.slack.dev/apis/events-api/using-socket-mode · https://github.com/slackapi/bolt-js/issues/2487 · https://github.com/slackapi/bolt-python/issues/445

## socket-mode-off-but-no-request-url

- **slug**: `socket-mode-off-but-no-request-url`
- **title**: Socket Mode is off and no Request URL replaced it
- **symptom**: Someone toggled Socket Mode off — to test HTTP delivery, or while preparing for distribution — and the app went completely silent. No errors anywhere; the app simply stops receiving anything.
- **mechanism**: Disabling Socket Mode does not fall back to anything. Event and interaction delivery requires exactly one configured transport: an open WebSocket, or a verified public Request URL. With Socket Mode off and no Request URL, Slack has nowhere to send payloads and drops them. The Socket Mode client, meanwhile, receives `link_disabled` on its next connection attempt and — if it treats that as transient — retries forever without surfacing the cause.
- **detect**: `apps.manifest.export?app_id=<A...>` and assert exactly one transport is configured: either `settings.socket_mode_enabled === true`, or a non-empty `settings.event_subscriptions.request_url`. Neither present, with a non-empty `settings.event_subscriptions.bot_events[]`, is the finding — the app declares events it can never receive. Confirm behaviorally: bot is a channel member, humans are mentioning it in `conversations.history`, and the bot has posted nothing since a specific timestamp.
- **repair**: Re-enable Socket Mode, or configure and verify a public HTTPS Request URL under **Event Subscriptions** and **Interactivity & Shortcuts**. Add a startup assertion in the app that reads its own manifest (with a configuration token) and refuses to boot when neither transport is configured, so the misconfiguration fails loudly at deploy time.
- **category**: Socket Mode and connections
- **sources**: https://docs.slack.dev/apis/events-api/using-socket-mode · https://docs.slack.dev/apis/events-api/ · https://docs.slack.dev/reference/methods/apps.manifest.export

## interactivity-not-enabled

- **slug**: `interactivity-not-enabled`
- **title**: Buttons render but no interaction payload is ever delivered
- **symptom**: Block Kit buttons and select menus appear correctly in the channel. Clicking one does nothing, or shows an error toast. Slash commands work; block actions produce `dispatch_failed`. The handler is never invoked.
- **mechanism**: Interactivity is configured separately from Events. An app can post interactive blocks with only `chat:write` — Slack renders them — but the payload produced by a click is delivered to the **Interactivity Request URL**, which is a distinct setting from the Events Request URL, or to the Socket Mode connection if that is on. With Interactivity toggled off, or with its URL unset or wrong, clicks go nowhere. The commonest shape: Events configured and verified, Interactivity never touched.
- **detect**: `apps.manifest.export?app_id=<A...>` → check `settings.interactivity.is_enabled` and `settings.interactivity.request_url` (and `message_menu_options_url` if external selects are used). `is_enabled: false`, or `true` with an empty/stale `request_url` while `socket_mode_enabled` is `false`, is the finding. Behaviorally: `conversations.history?channel=<C...>&limit=200` shows app-authored messages containing `blocks` with `type: "actions"` or accessory buttons, while the app has never posted any follow-up consistent with a click being handled.
- **repair**: Enable **Interactivity & Shortcuts** and set its Request URL to the same endpoint that handles events (Bolt serves both on one route by default), or rely on Socket Mode for both. Verify by clicking a button and confirming a payload arrives. Note the interactivity endpoint has the same 3-second ack requirement as events.
- **category**: Socket Mode and connections
- **sources**: https://github.com/slackapi/java-slack-sdk/issues/1189 · https://stackoverflow.com/questions/73738612 · https://docs.slack.dev/reference/methods/apps.manifest.export

---

# App configuration and manifests

## manifest-drift

- **slug**: `manifest-drift`
- **title**: The deployed manifest differs from the one in the repo
- **symptom**: The repository's `manifest.json` lists twelve scopes and four event subscriptions. The live app has nine scopes and two events, because someone fixed a production incident through the web UI eight months ago and never backported it. Nobody can say which is authoritative.
- **mechanism**: Slack app configuration is editable in two places — the web UI and the App Manifest API — and neither reconciles with the other. Any UI edit silently diverges from the checked-in manifest, and the next `apps.manifest.update` from CI silently reverts it. The drift is invisible until a reinstall applies whichever version happens to be live, at which point scopes or events disappear without any deploy having happened.
- **detect**: `apps.manifest.export?app_id=<A...>` with an app configuration token returns the live manifest as JSON. Normalize (sort keys and arrays) and diff against the repository's manifest. Report every difference in `oauth_config.scopes.bot[]`, `oauth_config.scopes.user[]`, `settings.event_subscriptions.bot_events[]`, `settings.interactivity`, `features.slash_commands[]`, and `settings.socket_mode_enabled`. Cross-check the *granted* scopes separately with `X-OAuth-Scopes` — a third value that can differ from both the repo manifest and the live manifest when the app has not been reinstalled since the last change.
- **repair**: Make the repository manifest authoritative: run `apps.manifest.update` from CI on every change, and add the export-and-diff check above as a build step that fails on drift. Where an emergency UI edit is unavoidable, require exporting the manifest back into the repo as part of closing the incident. Track three states explicitly — repo manifest, live manifest, granted token scopes — because they diverge independently.
- **category**: App configuration and manifests
- **sources**: https://docs.slack.dev/reference/methods/apps.manifest.export · https://github.com/slackapi/bolt-js/issues/2437 · https://docs.slack.dev/reference/manifests

## app-not-distributed

- **slug**: `app-not-distributed`
- **title**: The app is single-workspace and cannot be installed elsewhere
- **symptom**: The "Add to Slack" button produces an error, or the OAuth flow completes for the developer's own workspace and fails for everyone else. Public distribution was never activated.
- **mechanism**: A new Slack app is installable only in its development workspace until **Manage Distribution → Activate Public Distribution** is enabled, which requires a valid redirect URL, no hardcoded information in the install URL, and — for org-wide install — additional configuration. Teams build against a single workspace, then discover at launch that distribution is a separate gate with its own checklist.
- **detect**: `apps.manifest.export?app_id=<A...>` → inspect `settings.org_deploy_enabled`, `oauth_config.redirect_urls[]`, and the presence of distribution-related settings; an app with no `redirect_urls` cannot run a public OAuth flow. Empirically: `auth.test` across your installation store returns only one distinct `team_id`, which is consistent with (though not proof of) a non-distributed app. The combination — one workspace, no redirect URLs, a product intended for customers — is the finding.
- **repair**: In **Manage Distribution**, complete the checklist and activate public distribution; add every environment's OAuth redirect URL under **OAuth & Permissions → Redirect URLs**. For Enterprise Grid customers, additionally enable org-wide installation (`settings.org_deploy_enabled: true`) so admins can install once for the whole org. Implement an `installationStore` before flipping the switch — a distributed app needs per-workspace token storage, not an env var.
- **category**: App configuration and manifests
- **sources**: https://docs.slack.dev/reference/manifests · https://stackoverflow.com/questions/45523707 · https://docs.slack.dev/authentication/installing-with-oauth

## oauth-redirect-mismatch

- **slug**: `oauth-redirect-mismatch`
- **title**: bad_redirect_uri: the callback URL is not on the allow list
- **symptom**: `{"ok": false, "error": "bad_redirect_uri"}` from `oauth.v2.access`, or the user is bounced to a Slack error page mid-install. It works in staging and fails in production, or breaks the day a domain changes.
- **mechanism**: Slack validates the `redirect_uri` presented at the token-exchange step against the app's configured Redirect URLs, with exact-prefix matching that is sensitive to scheme, host, port, trailing slash and path. A frequent trap: when exactly one redirect URL is configured, Slack may accept an install that omits `redirect_uri` and then reject the exchange that includes it (or vice versa) — the parameter must be present-and-identical in both the authorize and the access call, or absent from both.
- **detect**: `apps.manifest.export?app_id=<A...>` → `oauth_config.redirect_urls[]`. Compare each entry against the URLs the deployed application actually uses, character for character. Flag: `http://` entries, `localhost` entries in a production app, trailing-slash mismatches, and any deployed environment whose callback URL has no matching prefix in the list. Capture observed `bad_redirect_uri` errors from install attempts.
- **repair**: Add the exact callback URL for every environment to **OAuth & Permissions → Redirect URLs**, including scheme and path, and pass the identical string as `redirect_uri` in **both** the authorize URL and the `oauth.v2.access` exchange. Keep the list in the manifest under `oauth_config.redirect_urls` so environments cannot drift.
- **category**: App configuration and manifests
- **sources**: https://stackoverflow.com/questions/52690878 · https://stackoverflow.com/questions/42167991 · https://docs.slack.dev/reference/methods/oauth.v2.access

## app-access-restricted

- **slug**: `app-access-restricted`
- **title**: app_access_restricted: an admin blocked the app for this user
- **symptom**: `{"ok": false, "error": "app_access_restricted"}` — "The user does not have permission to use this app." It works for most of the workspace and fails for a subset, or fails entirely in one customer's org.
- **mechanism**: Workspace and Grid admins can restrict which users or groups may use a given app, and can require app approval before installation. A user outside the permitted set triggers `app_access_restricted` on actions performed on their behalf. This is a policy decision made outside your app, often after installation, and it changes without notice.
- **detect**: Capture `body.error === "app_access_restricted"` and record the associated `user` id so the finding names who is affected. Resolve those users with `users.info?user=<U...>` and look for shared attributes — `is_restricted` / `is_ultra_restricted` (guests are commonly excluded), `team_id` differing on Grid, or membership of a particular usergroup via `usergroups.users.list`. On Enterprise Grid with `admin.apps:read`, `admin.apps.approved.list` and `admin.apps.restricted.list` show the app's approval status per workspace directly.
- **repair**: Ask an admin to grant the app to the affected users or groups (**Manage apps → the app → Permissions/Restrictions**), or to add the app to the approved list. On the app side, degrade gracefully: catch the error, tell the user their admin has restricted the app, and do not retry — retrying cannot succeed.
- **category**: App configuration and manifests
- **sources**: https://docs.slack.dev/reference/methods/chat.postMessage · https://docs.slack.dev/reference/methods/admin.apps.approved.list · https://docs.slack.dev/reference/methods/admin.apps.restricted.list

## messages-tab-disabled

- **slug**: `messages-tab-disabled`
- **title**: messages_tab_disabled: the App Home DM surface is off
- **symptom**: `{"ok": false, "error": "messages_tab_disabled"}` when DMing a user as the app, or users report "you cannot reply to this conversation" when they try to message the bot. The Messages tab shows a greyed-out composer.
- **mechanism**: App Home has three tabs — Home, Messages, About — and the Messages tab is **off by default**. It must be enabled in **App Home → Show Tabs → Messages Tab**, and a separate checkbox ("Allow users to send Slash commands and messages from the messages tab") controls whether users can reply. Apps built around DM interaction commonly ship with the tab disabled, so the bot can be messaged by nobody and, for some flows, cannot message at all.
- **detect**: `apps.manifest.export?app_id=<A...>` → `features.app_home.messages_tab_enabled` and `features.app_home.messages_tab_read_only_enabled`. `messages_tab_enabled: false` in an app that DMs users, or `messages_tab_read_only_enabled: true` in an app expecting replies, is the finding. Capture observed `messages_tab_disabled` errors. Behaviorally, `conversations.list?types=im` returning IMs with no inbound human messages in `conversations.history` supports the read-only case.
- **repair**: In **App Home**, enable the Messages tab and uncheck the read-only option so users can reply. In a manifest: `features.app_home.messages_tab_enabled: true` and `messages_tab_read_only_enabled: false`. Also subscribe to `message.im` so replies actually reach the app — enabling the tab alone does not deliver the messages.
- **category**: App configuration and manifests
- **sources**: https://stackoverflow.com/questions/67672427 · https://docs.slack.dev/reference/methods/chat.postMessage · https://docs.slack.dev/surfaces/app-home

## slash-command-not-registered

- **slug**: `slash-command-not-registered`
- **title**: A slash command in the code was never registered
- **symptom**: Typing `/deploy` in Slack returns "`/deploy` is not a valid command" or silently autocompletes to something else. The handler exists and is tested.
- **mechanism**: Slash commands are declared in the app configuration, not in code. Each command needs a name, a Request URL, and a reinstall to take effect — and command names are workspace-unique, so another app (or Slack itself) may already own `/deploy`, in which case yours is simply unavailable. Adding a handler in Bolt without adding the command to the manifest produces dead code.
- **detect**: `apps.manifest.export?app_id=<A...>` → `features.slash_commands[]`, each with `command`, `url`, `description`, `usage_hint` and `should_escape`. Diff the set of registered commands against the set the application handles. Report commands handled but not registered (dead handlers) and commands registered but not handled (which produce `dispatch_failed` for users). Also check each entry's `url` for the tunnel/HTTP problems in [`http-or-dead-tunnel-request-url`](#http-or-dead-tunnel-request-url).
- **repair**: Register every command under **Slash Commands** with the production Request URL, then reinstall the app — new commands require reinstallation. In a manifest, add them to `features.slash_commands[]` and deploy via `apps.manifest.update`. If the name collides with an existing command, pick a namespaced alternative (`/acme-deploy`).
- **category**: App configuration and manifests
- **sources**: https://docs.slack.dev/reference/manifests · https://github.com/slackapi/bolt-js/issues/579 · https://stackoverflow.com/questions/63665120

## incoming-webhook-dead

- **slug**: `incoming-webhook-dead`
- **title**: no_service: the incoming webhook was removed or disabled
- **symptom**: `HTTP 404` with the plain-text body `no_service` or `no_active_hooks`, or `HTTP 401` with `invalid_token`. Alerts stop. Unlike the Web API, this failure *does* produce a real error status — but only if anything checks it.
- **mechanism**: An incoming webhook URL is bound to a specific app installation, user and channel. Uninstalling the app, revoking the installing user's authorization, deleting the webhook configuration, or deactivating the installing user all kill the URL permanently. The URL string continues to look valid forever. Many teams paste webhook URLs into a dozen systems (CI, monitoring, cron) and have no inventory of where they live.
- **detect**: A read-only script can classify each configured webhook URL by its response body and status without posting anything meaningful — but note any request to a webhook *does* attempt a post, so this is at the edge of read-only. The purely read-only alternative: `apps.manifest.export?app_id=<A...>` → `oauth_config.scopes.bot[]` containing `incoming-webhook` tells you the app issues webhooks, and the OAuth install response's `incoming_webhook` object (`channel`, `channel_id`, `configuration_url`, `url`) is what your installation store should hold. Compare stored webhook records against live installs: any webhook whose owning installation now fails `auth.test` with `token_revoked` or `account_inactive` is dead.
- **repair**: Reinstall the app to mint a new webhook, or migrate off webhooks entirely to `chat.postMessage` with a bot token — a bot token survives the installing user leaving, and webhooks do not. Maintain an inventory mapping each webhook URL to the system that uses it, since rotation requires updating every consumer.
- **category**: App configuration and manifests
- **sources**: https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks · https://stackoverflow.com/questions/77158147 · https://stackoverflow.com/questions/63774839

## webhook-locked-to-one-channel

- **slug**: `webhook-locked-to-one-channel`
- **title**: The webhook posts to one fixed channel regardless of payload
- **symptom**: A payload sets `"channel": "#incidents"` and the message lands in `#general` anyway. Or it returns `channel_not_found`. The `channel` override that every old blog post demonstrates simply does not work.
- **mechanism**: Modern incoming webhooks (created through the Slack app model, post-2016) are permanently bound to the single channel chosen at install time. The legacy `channel` override in the payload is honored only by the old custom-integration webhooks and is ignored or rejected by app-based ones. Teams migrating from legacy integrations to apps discover their entire routing scheme silently collapses to one channel.
- **detect**: Compare the app's stored `incoming_webhook.channel_id` (from the OAuth install response) against the channels the sending code targets. If the code sets a `channel` field in webhook payloads at all, that is the finding — for an app-based webhook it is inert. Corroborate from the workspace: `conversations.history?channel=<the bound channel>&limit=200` shows messages that were clearly intended for other channels (routing keys, other teams' alerts) all arriving in one place.
- **repair**: Stop using incoming webhooks for multi-channel routing. Switch to `chat.postMessage` with a bot token and an explicit `channel` id per message — one token, any channel the bot can post to. If webhooks must stay, create one webhook per destination channel and route on your side, accepting that each is a separate secret to manage.
- **category**: App configuration and manifests
- **sources**: https://stackoverflow.com/questions/51467215 · https://stackoverflow.com/questions/41531123 · https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks

## webhook-invalid-payload

- **slug**: `webhook-invalid-payload`
- **title**: invalid_payload: the webhook body is malformed JSON
- **symptom**: `HTTP 400` with the plain-text body `invalid_payload`. Almost always from a shell script using `curl -d` with unescaped quotes, newlines, or interpolated variables containing `"`.
- **mechanism**: Incoming webhooks accept a JSON body and reject anything that fails to parse, with no indication of *where* it failed. The overwhelming source is string interpolation in shell, CI YAML, or templating: a commit message containing a double quote, a multi-line log fragment inserted without `\n` escaping, or a GitHub Actions expression substituted before the payload is parsed. A close sibling is `HTTP 400 no_text`, when the JSON parses but carries no `text`, `blocks` or `attachments`.
- **detect**: The failing payload is never persisted, so detection is symptom capture plus a survey of the successes. Capture status and body from any webhook send: `400 invalid_payload`, `400 no_text`, `403 action_prohibited`, `403 posting_to_general_channel_denied`, `404 no_service`/`no_active_hooks`, `410 channel_is_archived`, `401 invalid_token`. Separately, read what did get through — `conversations.history?channel=<bound channel>&limit=200` — and look for messages containing raw JSON fragments, stray backslashes, or truncation at the first quote, which is the fingerprint of a nearly-broken interpolation that happened to parse.
- **repair**: Build the JSON with a real serializer (`jq -n --arg text "$MSG" '{text:$text}'`, `json.dumps`, `JSON.stringify`) rather than string interpolation, and send it with `--data-binary @-`. Set `Content-Type: application/json`. Never interpolate untrusted text directly into a JSON literal. And check the HTTP status: unlike the Web API, webhooks return real 4xx codes, so a status check actually works here.
- **category**: App configuration and manifests
- **sources**: https://stackoverflow.com/questions/39925395 · https://stackoverflow.com/questions/31905260 · https://docs.slack.dev/messaging/sending-messages-using-incoming-webhooks

## legacy-workflow-steps

- **slug**: `legacy-workflow-steps`
- **title**: The app still ships retired Steps from Apps
- **symptom**: A Workflow Builder workflow containing the app's custom step stopped executing. The app's `workflow_step_execute` handler never fires. Subscribing to the event is no longer possible in the app configuration.
- **mechanism**: Slack retired legacy **Steps from Apps** on **26 September 2024**. From that date, workflows containing a legacy step stopped running, the steps themselves stopped working, and the associated events — `workflow_step_execute`, `workflow_published`, `workflow_unpublished`, `workflow_deleted`, `workflow_step_deleted` — could no longer be subscribed to. There is no direct migration path for legacy steps or for the workflows that used them; the replacement is the new workflow-step model, and workflows must be rebuilt by hand.
- **detect**: `apps.manifest.export?app_id=<A...>` → look for `features.workflow_steps[]` (legacy), and for any of the retired event names in `settings.event_subscriptions.bot_events[]`. Their presence in a live manifest is dead configuration. Also flag `X-OAuth-Scopes` containing `workflow.steps:execute`, which only legacy step apps hold.
- **repair**: Remove the legacy step definitions and retired event subscriptions from the manifest. Rebuild the capability as a modern workflow step (a custom function that Workflow Builder can call) so users can recreate their workflows, and communicate to affected users that the old workflows must be rebuilt — Slack provides no automated migration.
- **category**: App configuration and manifests
- **sources**: https://docs.slack.dev/changelog/2024/05/02/apps/ · https://docs.slack.dev/legacy/legacy-steps-from-apps/legacy-steps-from-apps-survival-guide-faq/ · https://github.com/slackapi/bolt-python/issues/1025

## deprecated-method-in-use

- **slug**: `deprecated-method-in-use`
- **title**: method_deprecated on a legacy channels.* or groups.* call
- **symptom**: `{"ok": false, "error": "method_deprecated"}` or `deprecated_endpoint`, or a `warning` field on an otherwise successful response. Old code calling `channels.list`, `groups.list`, `im.list`, `channels.history`, `rtm.start` or `files.upload`.
- **mechanism**: Slack replaced the per-type `channels.*` / `groups.*` / `im.*` / `mpim.*` families with the unified `conversations.*` API, deprecated `rtm.start` in favour of `rtm.connect`, and sunset `files.upload`. Deprecated methods typically pass through a phase where they still work but return a `warning`, then fail. Code written from old tutorials — of which there are a great many — starts on the deprecated path.
- **detect**: For each method the app calls, issue the read-only equivalent and inspect three fields: `body.error` for `method_deprecated` / `deprecated_endpoint`, `body.warning` for advance notice on still-working methods, and `response_metadata.warnings[]` which carries structured deprecation messages. Enumerate the app's method usage from its own history where possible; otherwise probe the known-deprecated set directly. Any non-empty `warning` on a successful call is a scheduled future outage.
- **repair**: Migrate to the `conversations.*` family: `channels.list`/`groups.list`/`im.list` → `conversations.list` with `types`; `channels.history`/`groups.history` → `conversations.history`; `channels.info` → `conversations.info`; `im.open` → `conversations.open`. Replace `rtm.start` with Socket Mode. Replace `files.upload` with the external-upload sequence. Then log `body.warning` at WARN level permanently so the next deprecation surfaces before it breaks.
- **category**: App configuration and manifests
- **sources**: https://docs.slack.dev/reference/methods/ · https://docs.slack.dev/reference/methods/conversations.list · https://docs.slack.dev/changelog/2024/05/16/apps/

## app-home-tab-disabled

- **slug**: `app-home-tab-disabled`
- **title**: The Home tab is published to but not enabled
- **symptom**: `views.publish` succeeds with `ok: true` and users see nothing — the app's profile shows no Home tab at all, or shows an empty one. No error anywhere.
- **mechanism**: The Home tab must be enabled in **App Home → Show Tabs → Home Tab**, and the app must subscribe to the `app_home_opened` event to know when to publish. An app that calls `views.publish` without the tab enabled gets a successful response for a surface nobody can reach. Additionally, the published view is per-user and per-installation, so publishing once at startup rather than on `app_home_opened` leaves most users with an empty tab.
- **detect**: `apps.manifest.export?app_id=<A...>` → `features.app_home.home_tab_enabled`. `false` in an app that calls `views.publish` is the finding. Also check `settings.event_subscriptions.bot_events[]` for `app_home_opened` — a Home tab without that subscription will be stale or empty for users who were not present when it was published. The 100-block modal/Home limit from [`msg-blocks-too-long`](#msg-blocks-too-long) applies here too.
- **repair**: Enable the Home tab in **App Home** (manifest: `features.app_home.home_tab_enabled: true`), subscribe to `app_home_opened`, and publish the view in that handler with `views.publish?user_id=<U...>&view=<json>`. Publish on every open rather than once, so the content reflects current state.
- **category**: App configuration and manifests
- **sources**: https://docs.slack.dev/surfaces/app-home · https://docs.slack.dev/reference/methods/views.publish · https://docs.slack.dev/reference/manifests

## app-uninstalled-orphan-install-record

- **slug**: `app-uninstalled-orphan-install-record`
- **title**: The installation store keeps rows for uninstalled workspaces
- **symptom**: A scheduled job iterates 400 installations and logs 120 `token_revoked` / `account_inactive` errors every run, forever. The error rate never improves. Metrics are dominated by dead tenants.
- **mechanism**: Slack emits `app_uninstalled` and `tokens_revoked` when an installation ends, but the SDK installation stores do not automatically delete the record — that is the app's job, and the most-upvoted request in the Bolt repo asks for it to be automatic. Additionally the two events arrive in a racy order, and `tokens_revoked` does not fire for partial revocations, so even apps that handle them leave residue. Dead rows accumulate, consuming quota on every sweep and drowning real errors.
- **detect**: Iterate the installation store and call `auth.test` per token, classifying results: `ok: true` (live), `token_revoked` (app removed), `account_inactive` (user or workspace deactivated), `token_expired` (rotation lapsed, potentially recoverable), `invalid_auth` (bad token). Report counts per class and the fraction of the store that is dead. Any non-trivial dead fraction is the finding; a dead fraction that is stable or growing across audits proves nothing is cleaning up.
- **repair**: Handle `app_uninstalled` and `tokens_revoked` by deleting the installation (and every derived record: scheduled messages, cached channel ids, webhook URLs). Add a reconciliation job that runs the `auth.test` sweep above and tombstones anything returning `token_revoked` or `account_inactive`. Keep `token_expired` separate — that one may be recoverable via refresh rather than deletion.
- **category**: App configuration and manifests
- **sources**: https://github.com/slackapi/bolt-js/issues/1203 · https://github.com/slackapi/bolt-js/issues/673 · https://docs.slack.dev/reference/events/tokens_revoked

---

# Enterprise Grid and admin

## workspace-token-in-grid

- **slug**: `workspace-token-in-grid`
- **title**: team_access_not_granted: the token is scoped to one workspace
- **symptom**: `{"ok": false, "error": "team_access_not_granted"}` — "The token used is not granted the specific workspace access required." The app works in the workspace it was installed to and fails for every other workspace in the same organization.
- **mechanism**: On Enterprise Grid, an app can be installed to a single workspace or org-wide. A workspace-scoped token carries access only to that workspace's conversations and users; calling it with a `channel` or `user` from a sibling workspace returns `team_access_not_granted`. Org-wide installs produce a token that spans workspaces but requires a `team_id` parameter on many methods to disambiguate — which single-workspace code never supplies.
- **detect**: `auth.test` → read `is_enterprise_install`, `enterprise_id`, `team_id` and `url`. An install with `is_enterprise_install: false` and a non-null `enterprise_id` is a workspace-scoped install inside a Grid org — the configuration that produces this error. Then attempt a read against a resource in another workspace (a channel id collected via `admin.conversations.search` or from an event payload) and observe `team_access_not_granted`. `team.info?team=<T...>` for a sibling workspace returns the same error on a workspace-scoped token.
- **repair**: Install the app org-wide (**Manage apps** at the organization level, with `settings.org_deploy_enabled: true` in the manifest), which mints a token valid across workspaces. Then pass `team_id` explicitly on methods that accept it, and key your installation store on `(enterprise_id, team_id)` rather than `team_id` alone. Where org-wide install is not possible, install per workspace and store one token each.
- **category**: Enterprise Grid and admin
- **sources**: https://docs.slack.dev/enterprise-grid/ · https://docs.slack.dev/reference/methods/conversations.list · https://github.com/slackapi/bolt-js/issues/1778

## org-wide-install-mishandled

- **slug**: `org-wide-install-mishandled`
- **title**: is_enterprise_install is true and team_id lookups break
- **symptom**: An org-wide install stores `team_id: null` or `"none"`, and every subsequent lookup misses. Events arrive with a `team_id` the store has never seen. Global shortcuts fail because `fetchInstallation` is called with a workspace id that has no row.
- **mechanism**: For an org-wide installation, `auth.test` returns `is_enterprise_install: true` with an `enterprise_id` and, depending on context, a null or placeholder `team_id`. Bolt's `installationStore` is queried with `(enterpriseId, teamId, isEnterpriseInstall)` and code that keys purely on `team_id` cannot find the row. Event payloads for org-wide apps carry `enterprise_id` and a per-workspace `team_id`, and on some clients the `team_id` is absent entirely — which is a documented source of Grid bugs in the Bolt repos.
- **detect**: `auth.test` per stored token and record `is_enterprise_install`, `enterprise_id`, `team_id`. Findings: any install where `is_enterprise_install: true` while your store's primary key is `team_id`; any install where `team_id` is null or the literal string `"none"`; and any store containing the same `team_id` for two different `enterprise_id`s, which proves keys collide. Use `admin.teams.list` (needs `admin.teams:read`) to enumerate the org's workspaces and confirm how many `team_id`s the single org-wide token must serve.
- **repair**: Key the installation store on `(enterprise_id, team_id, is_enterprise_install)`, storing `team_id` as null for org-wide installs, and implement lookup to fall back from a workspace-specific row to the org-wide row. In Bolt, implement both `fetchInstallation` and `deleteInstallation` against that composite key. Always read `enterprise_id` from the event payload rather than inferring it.
- **category**: Enterprise Grid and admin
- **sources**: https://github.com/slackapi/python-slack-sdk/issues/1639 · https://github.com/slackapi/bolt-js/issues/1944 · https://docs.slack.dev/reference/methods/auth.test

## enterprise-is-restricted

- **slug**: `enterprise-is-restricted`
- **title**: enterprise_is_restricted: the method is barred on Grid
- **symptom**: `{"ok": false, "error": "enterprise_is_restricted"}` — "The method cannot be called from an Enterprise." Code that works in every standalone workspace fails for the one Enterprise customer.
- **mechanism**: A number of Web API methods are simply not callable with an org-level token on Enterprise Grid; the organization-level equivalents live under `admin.*` and require different scopes and a user token. This appears in the error list for `chat.postMessage`, `conversations.history`, `conversations.list` and many others. Apps developed against a standard workspace encounter it only at their first Grid deployment, typically during a customer's evaluation.
- **detect**: `auth.test` → `enterprise_id` non-null identifies a Grid context. Then call each method the app depends on and check for `body.error === "enterprise_is_restricted"`. Report the specific methods affected, since the set varies. Distinguish carefully from `team_access_not_granted` (wrong workspace scope) and `org_login_required` (mid-migration) — all three appear on Grid and have different repairs.
- **repair**: Use the workspace-scoped token for workspace-scoped operations and reserve the org-level token for `admin.*` methods. Where an org-level equivalent exists (`admin.conversations.search` instead of `conversations.list` across the org), use it with the corresponding `admin.*:read` scope on an admin **user** token. Where none exists, iterate per workspace with per-workspace tokens.
- **category**: Enterprise Grid and admin
- **sources**: https://docs.slack.dev/reference/methods/chat.postMessage · https://docs.slack.dev/reference/methods/conversations.list · https://docs.slack.dev/enterprise-grid/

## org-login-required

- **slug**: `org-login-required`
- **title**: org_login_required during an Enterprise migration
- **symptom**: `{"ok": false, "error": "org_login_required"}` — "The workspace is undergoing an enterprise migration and will not be available until migration is complete." Everything fails for a customer for hours or days, then works again.
- **mechanism**: When a standalone workspace is migrated into an Enterprise Grid organization, its API surface is temporarily unavailable and its user and channel ids may change. Apps that treat the error as a permanent failure disable the customer; apps that retry aggressively hammer a workspace that cannot answer. After migration completes, user ids in particular may differ, so cached ids can be stale.
- **detect**: Capture `body.error === "org_login_required"` and, separately, `team_added_to_org` from `auth.test` and any read method. Both indicate migration; treat them as a distinct, temporary class. Record the first and last time each appeared per installation so the duration is visible. After the error clears, re-run `auth.test` and compare the returned `team_id`, `user_id` and `enterprise_id` against what was stored — changes confirm the migration completed and caches must be invalidated.
- **repair**: Treat `org_login_required` and `team_added_to_org` as retryable with a long, capped backoff (hours, not seconds) and suspend scheduled work for that installation rather than failing it. When the error clears, re-run `auth.test`, refresh `enterprise_id`/`team_id` in the installation store, and invalidate cached channel and user ids for that workspace.
- **category**: Enterprise Grid and admin
- **sources**: https://docs.slack.dev/reference/methods/chat.postMessage · https://docs.slack.dev/reference/methods/auth.test · https://docs.slack.dev/enterprise-grid/

## team-added-to-org

- **slug**: `team-added-to-org`
- **title**: team_added_to_org: the workspace is mid-migration to Grid
- **symptom**: `{"ok": false, "error": "team_added_to_org"}` — "The workspace associated with your request is currently undergoing migration to an Enterprise Organization." Distinct from `org_login_required` but similarly transient.
- **mechanism**: This error marks the window in which a workspace has been attached to an organization but the migration has not settled. During it, the workspace's identifiers are in flux: the workspace gains an `enterprise_id`, users gain org-level identities, and previously workspace-unique ids may be remapped. Apps caching user ids across the boundary produce `user_not_found` afterwards.
- **detect**: Capture `body.error === "team_added_to_org"` on any read method. Then, once calls succeed again, run a consistency check: `auth.test` for the current `enterprise_id`/`team_id`, and spot-check a sample of cached user ids with `users.info?user=<U...>` — a burst of `user_not_found` for ids that previously resolved confirms the remapping. `users.list` re-enumeration is the authoritative refresh.
- **repair**: Back off and suspend, as with `org_login_required`. On recovery, treat all cached Slack identifiers for that workspace as invalid: re-enumerate users via `users.list`, re-resolve channels via `conversations.list`, and re-key the installation store to include `enterprise_id`. Store your own stable user key (email, or your internal id) mapped to the Slack id so a remap is a re-resolution rather than data loss.
- **category**: Enterprise Grid and admin
- **sources**: https://docs.slack.dev/reference/methods/conversations.history · https://docs.slack.dev/enterprise-grid/ · https://github.com/slackapi/node-slack-sdk/issues/1705

## admin-method-needs-user-token

- **slug**: `admin-method-needs-user-token`
- **title**: admin.* calls fail because a bot token was used
- **symptom**: `{"ok": false, "error": "not_allowed_token_type"}` or `missing_scope` from `admin.apps.approved.list`, `admin.conversations.search`, `admin.users.list` or similar. The scope `admin.apps:read` is definitely granted.
- **mechanism**: Every `admin.*` method requires a **user** token belonging to an org owner or admin, carrying the matching `admin.*:read` or `admin.*:write` scope. These scopes cannot be granted to a bot token at all — they appear only under User Token Scopes. Apps that store a single token and use it everywhere fail on the admin surface specifically, and the error is a token-class error rather than an obviously-admin one.
- **detect**: `auth.test` on the token used for admin calls: a `bot_id` in the response means it is a bot token and no `admin.*` method will accept it. Read `X-OAuth-Scopes` on the **user** token and check for the `admin.*:read` scopes the app needs. Then call `admin.apps.approved.list?limit=1` with the user token and classify: `ok: true` (working), `not_an_admin` (right token class, wrong person), `feature_not_enabled` (wrong plan), `missing_scope` (scope absent), `not_allowed_token_type` (still a bot token).
- **repair**: Request the `admin.*:read` scopes under **User Token Scopes**, have an **org owner or admin** perform the installation so the resulting `authed_user.access_token` carries admin authority, and store that token separately from the bot token. Use it only for `admin.*` calls; use the bot token for everything else.
- **category**: Enterprise Grid and admin
- **sources**: https://docs.slack.dev/reference/methods/admin.apps.approved.list · https://docs.slack.dev/reference/scopes/ · https://stackoverflow.com/questions/71409815

## not-an-admin

- **slug**: `not-an-admin`
- **title**: not_an_admin: the installing user is not an org admin
- **symptom**: `{"ok": false, "error": "not_an_admin"}` — "This method is only accessible by org/workspace owners and admins." The token is a user token with the right scopes; the human behind it simply lacks the role.
- **mechanism**: `admin.*` scopes can be *granted* to a user token regardless of the user's role, but the methods check the user's actual admin status at call time. A developer installs the app with their own account, gets the scopes, and the calls still fail. Worse, a user who is an admin at install time can lose the role later, breaking the integration with no configuration change.
- **detect**: Call `admin.apps.approved.list?limit=1` (or `admin.teams.list?limit=1`) with the user token and check for `body.error === "not_an_admin"` — this is unambiguous. Corroborate the human's role: `users.info?user=<authed_user.id>` returns `user.is_admin`, `user.is_owner`, `user.is_primary_owner`. A token whose owner has `is_admin: false` will never satisfy an `admin.*` method. Also surface `is_admin` for the installer at install time so the problem is caught immediately.
- **repair**: Have an org owner or org admin re-run the installation so the user token belongs to a privileged account, and prefer a dedicated service account with the admin role over an individual's account so the integration survives role changes and departures. Assert `users.info(...).is_admin` at startup and fail loudly when it is false.
- **category**: Enterprise Grid and admin
- **sources**: https://docs.slack.dev/reference/methods/admin.apps.approved.list · https://docs.slack.dev/reference/methods/users.info

## feature-not-enabled

- **slug**: `feature-not-enabled`
- **title**: feature_not_enabled: admin APIs require an Enterprise plan
- **symptom**: `{"ok": false, "error": "feature_not_enabled"}` — "Returned when the Admin APIs feature is not enabled for this team." Everything is configured correctly; the customer is simply not on Enterprise Grid.
- **mechanism**: The `admin.*` families, the Audit Logs API, the Discovery API and SCIM provisioning are Enterprise Grid features. A Business+ or Pro workspace returns `feature_not_enabled` regardless of scopes or roles. Multi-tenant apps that offer admin-powered capabilities must degrade per customer rather than assuming availability, and often discover this only when a non-Enterprise customer signs up.
- **detect**: `auth.test` → a null `enterprise_id` strongly suggests a non-Grid workspace. Confirm capability directly by calling `admin.teams.list?limit=1` or `admin.apps.approved.list?limit=1` and checking for `feature_not_enabled`. Also read `team.info?team=<T...>` for plan context. Record per installation whether the admin surface is available, so features are gated on a measured fact rather than an assumption.
- **repair**: Feature-detect at install time and store the result. Gate admin-dependent functionality behind that flag and present a clear "requires Enterprise Grid" message rather than a stack trace. Provide non-admin fallbacks where possible — `conversations.list` instead of `admin.conversations.search`, `users.list` instead of `admin.users.list` — accepting the narrower scope of what a workspace token can see.
- **category**: Enterprise Grid and admin
- **sources**: https://docs.slack.dev/reference/methods/admin.apps.approved.list · https://docs.slack.dev/reference/methods/team.info · https://docs.slack.dev/enterprise-grid/

## app-restricted-by-admin

- **slug**: `app-restricted-by-admin`
- **title**: The app sits on the org restricted list, not the approved one
- **symptom**: Installation fails for a customer's users with a message about admin approval, or `app_access_restricted` appears for everyone in a particular workspace. The app is technically fine; an org admin has blocked it.
- **mechanism**: Enterprise Grid organizations can require app approval and maintain explicit approved and restricted lists, scoped either org-wide or per workspace. An app can be approved in one workspace of an org and restricted in another. Nothing notifies the app developer when the status changes — installs simply stop.
- **detect**: With an admin user token holding `admin.apps:read`: `admin.apps.approved.list?limit=100` and `admin.apps.restricted.list?limit=100`, both paginated with `cursor`, optionally scoped by `team_id` or `enterprise_id`. Check whether your `app_id` appears in either list, and in which workspaces. Also call `admin.apps.requests.list` to see pending approval requests that no admin has actioned — a common silent blocker. Without an admin token, the observable is the aggregate `app_access_restricted` rate for a given `team_id`.
- **repair**: Ask the org admin to approve the app (**Organization settings → Apps → Manage → Approved apps**), and to action any pending request in the requests queue. For a distributed app, add Marketplace listing or at minimum a security-review document, since restricted-by-default is a common Grid posture for unlisted apps. Handle `app_access_restricted` gracefully in the meantime.
- **category**: Enterprise Grid and admin
- **sources**: https://docs.slack.dev/reference/methods/admin.apps.approved.list · https://docs.slack.dev/reference/methods/admin.apps.restricted.list · https://docs.slack.dev/enterprise-grid/

## ekm-access-denied

- **slug**: `ekm-access-denied`
- **title**: ekm_access_denied: Enterprise Key Management blocked the write
- **symptom**: `{"ok": false, "error": "ekm_access_denied"}` — "Your message couldn't be sent because your admins have disabled sending messages to this channel." It affects specific channels or a whole workspace, intermittently, and no scope change helps.
- **mechanism**: Enterprise Key Management lets an organization hold its own encryption keys and revoke access at channel, workspace, or organization granularity. When a key is revoked or an EKM policy blocks a surface, Slack refuses reads and writes for that scope. It appears on `chat.postMessage` ("administrators have suspended the ability to post") and on `conversations.history`. It is a security control, not a bug, and the only remedy is administrative.
- **detect**: Capture `body.error === "ekm_access_denied"` and record the `channel` and `team_id`. Probe the extent: run `conversations.info` and `conversations.history?limit=1` across the app's target channels and map which are affected — channel-level, workspace-level, or org-level scope is inferable from that map. `auth.test` confirms the Grid context via `enterprise_id`.
- **repair**: Escalate to the customer's Slack administrators; EKM policy is controlled entirely on their side and no app-side change affects it. In the app, treat `ekm_access_denied` as a permanent per-channel failure rather than retrying, surface it distinctly in monitoring so it is not confused with a scope problem, and skip affected channels rather than blocking the run.
- **category**: Enterprise Grid and admin
- **sources**: https://docs.slack.dev/reference/methods/chat.postMessage · https://docs.slack.dev/reference/methods/conversations.history · https://docs.slack.dev/enterprise-grid/

## enterprise-id-not-stored

- **slug**: `enterprise-id-not-stored`
- **title**: Installs are keyed on team_id alone and collide across the org
- **symptom**: Two customers in the same Enterprise Grid organization overwrite each other's installation record. One tenant's messages go to the other's channels. A global shortcut resolves the wrong token.
- **mechanism**: `team_id` is unique within a Slack instance but the *installation* identity on Grid is the pair `(enterprise_id, team_id)` plus the `is_enterprise_install` flag. A store keyed on `team_id` alone cannot represent an org-wide install (whose `team_id` may be null) and cannot distinguish an org-wide install from a workspace install in the same org. Reports of "the same team id appears in different workspaces" on Grid are a recurring Bolt issue, and the failure mode is cross-tenant data leakage — the most serious class in this catalogue.
- **detect**: For every stored installation, call `auth.test` and record `(enterprise_id, team_id, is_enterprise_install, user_id, bot_id)`. Findings: (a) two rows with the same `team_id` but different `enterprise_id`; (b) any row with `is_enterprise_install: true` stored under a `team_id` key; (c) any row where `enterprise_id` is not persisted at all. Enumerate the org's workspaces with `admin.teams.list` (needs `admin.teams:read`) to size the collision surface. Any row whose stored key does not round-trip to the same `auth.test` result is a live cross-tenant risk.
- **repair**: Re-key the installation store on `(enterprise_id, team_id, is_enterprise_install)` with `enterprise_id` nullable for non-Grid workspaces, and migrate existing rows by re-running `auth.test` per token to populate the missing field. Implement lookup to prefer an exact workspace match and fall back to the org-wide row. In Bolt, this is exactly the `InstallationQuery` contract — implement `fetchInstallation` and `deleteInstallation` against all three fields rather than `teamId` alone.
- **category**: Enterprise Grid and admin
- **sources**: https://github.com/slackapi/bolt-js/issues/1875 · https://github.com/slackapi/python-slack-sdk/issues/1639 · https://docs.slack.dev/reference/methods/auth.test
