#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch AB.

The same two shapes as the rest of the site: the problem is a chain that breaks
at one step, the fix is a branch, because every script in this section sorts what
it finds rather than answering yes or no. Drawn in Stripe indigo.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further: visuals.py imports several of these
# modules in one process, and a theme left set would silently retint whichever
# section happened to be imported next.
BRAND = "#635BFF"
D.set_theme(BRAND)

V = {}

V["stripe/connect-platform-missing-account-updated"] = {
    "flow_intro": (
        "The script cannot read the scope of a destination, because Stripe does not "
        "return it. So it reads the one thing that is returned, the subscribed event "
        "types, and reports the gap it can prove rather than the one it can guess."
    ),
    "diagram_problem": D.chain(
        "scpm-p",
        "Connected account events with no Connect scoped destination to arrive at",
        "Nothing fails. The events are simply never addressed to the platform, so "
        "there is no delivery to retry and no error rate to alert on.",
        [
            ("Endpoint created", "account scoped"),
            ("account.updated added", "accepted, looks right"),
            ("Seller verification lapses", "charges_enabled false"),
            ("Event goes elsewhere", "no matching destination"),
            ("Platform UI still live", "seller finds out first"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "scpm-f",
        "Sorting a platform by whether connected account events have a destination",
        "The endpoint object never returns the connect flag, so a wildcard "
        "subscription is genuinely unanswerable and is reported as such.",
        ("GET /v1/webhook_endpoints", "plus one page of /v1/accounts"),
        [
            ("Both signals subscribed", "covered", "good"),
            ("account.updated only", "departures invisible", "bad"),
            ("Wildcard only", "inconclusive, open Workbench", "plain"),
            ("Neither subscribed", "create a connect=true endpoint", "bad"),
        ],
    ),
}

V["stripe/current-deadline-passes-unwatched"] = {
    "flow_intro": (
        "The script turns one timestamp into two things a person can act on: days "
        "remaining, so the list has an order, and the calendar date, so the accounts "
        "that will fail together appear together."
    ),
    "diagram_problem": D.chain(
        "scdp-p",
        "A cohort of connected accounts breaking on one morning at the deadline",
        "The accounts that cross a threshold are the ones doing well, so the list of "
        "accounts about to be disabled is the list you least want disabled.",
        [
            ("Volume threshold crossed", "a good week"),
            ("Deadline set silently", "no capability changes"),
            ("Boolean check green", "nothing is disabled yet"),
            ("Date arrives", "fields move to past_due"),
            ("Nine accounts at once", "same missing field"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "scdp-f",
        "Sorting connected accounts by how many days are left on the deadline",
        "A deadline with nothing currently due is Stripe checking what it holds. "
        "Putting it on the chase list is how the chase list stops being read.",
        ("GET /v1/accounts", "current_deadline against today"),
        [
            ("No deadline, nothing due", "clear", "good"),
            ("Deadline, nothing due", "verifying, nobody to chase", "plain"),
            ("Inside 14 days", "email the link this week", "bad"),
            ("Date already passed", "an incident, read past_due", "bad"),
        ],
    ),
}

V["stripe/external-account-errored"] = {
    "flow_intro": (
        "The script reads the destination rather than the payouts, then spends two "
        "extra calls only where the status already says payouts stopped, so the "
        "corroboration is cheap enough to run across every account."
    ),
    "diagram_problem": D.chain(
        "seae-p",
        "A frozen bank account halting payouts while the failure count stays flat",
        "The metric everyone watches goes quiet exactly because the problem became "
        "permanent. Flat is what recovery looks like, and it is not recovery.",
        [
            ("Bank details go stale", "one payout fails"),
            ("Destination set errored", "Stripe stops trying"),
            ("No further failures", "read as recovered"),
            ("Balance grows", "payouts_enabled still true"),
            ("Seller reconciles", "eight weeks later"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "seae-f",
        "Sorting payout destinations by the status Stripe has put them in",
        "Three statuses halt payouts for three different reasons, and each needs a "
        "different conversation with the account holder.",
        ("GET external_accounts", "status, plus balance if halted"),
        [
            ("new or validated", "payouts can be sent", "good"),
            ("errored", "attach a NEW account, not an edit", "bad"),
            ("verification_failed", "holder details did not match", "bad"),
            ("token deactivated", "re-link through the bank", "bad"),
        ],
    ),
}

V["stripe/platform-paused-payouts-left-on"] = {
    "flow_intro": (
        "The script looks for one string, and refuses to claim accounts disabled for "
        "any other reason, because the failure being described here started with "
        "somebody treating a deliberate pause as a missing field."
    ),
    "diagram_problem": D.chain(
        "sppl-p",
        "A platform pause outliving the investigation that caused it",
        "Nothing external ever prompts the reversal. The decision lives in a ticket "
        "system that has no connection to Stripe.",
        [
            ("Risk pauses the seller", "disabled_reason set"),
            ("In flight payouts pend", "up to 10 days"),
            ("Payouts canceled", "funds return to balance"),
            ("Investigation closes", "nobody unpauses"),
            ("Six months of funds", "found at year end"),
        ],
        fail_at=3,
    ),
    "diagram_fix": D.branch(
        "sppl-f",
        "Sorting connected accounts by whether the platform paused them itself",
        "An onboarding link sent to a paused seller gets completed perfectly and "
        "changes nothing, because no field was ever missing.",
        ("GET /v1/accounts", "disabled_reason, plus canceled payouts"),
        [
            ("Not paused, no residue", "nothing to do", "good"),
            ("platform_paused", "Dashboard only, no API", "bad"),
            ("Canceled, not paused now", "re-issue the payouts", "bad"),
            ("Another disabled_reason", "a different note entirely", "plain"),
        ],
    ),
}

V["stripe/issuing-cardholder-requirements-past-due"] = {
    "flow_intro": (
        "The script starts at the cardholder rather than the card, counts the "
        "inactive cards behind each one, and tallies the decline reasons, because "
        "those three facts together say whether the block is what you think it is."
    ),
    "diagram_problem": D.chain(
        "sicr-p",
        "An Issuing card that will not activate because of a field on the cardholder",
        "The object that fails is not the object that is wrong, and the reason is "
        "two arrays away from the card in anyone's hand.",
        [
            ("Card issued", "status inactive by default"),
            ("Terms never shown", "acceptance ip and date missing"),
            ("Activation blocked", "nothing said on the card"),
            ("Every authorization declines", "instantly, at the reader"),
            ("Escalated as hardware", "reason sits in request_history"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sicr-f",
        "Sorting cardholders by what is actually missing before the ticket is written",
        "A terms checkbox and a passport scan are the same shape of finding and "
        "completely different work.",
        ("GET issuing/cardholders", "past_due, plus inactive card counts"),
        [
            ("Clean and active", "nothing blocking", "good"),
            ("Terms acceptance only", "capture ip and date", "bad"),
            ("Identity fields due", "documents from a person", "bad"),
            ("Clean, cards inactive", "nobody called activate", "plain"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
