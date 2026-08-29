#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch G.

Same two shapes as the rest of the site: the problem is a chain that breaks at
one step, the fix is a branch, because every script in this section classifies
what it finds rather than guessing. Drawn in Stripe indigo.

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

V["stripe/draft-invoices-never-finalized"] = {
    "flow_intro": (
        "The script pages drafts older than the cutoff and reads three fields on "
        "each one, because whether an invoice is waiting, stranded or blocked "
        "decides which of three different repairs it needs."
    ),
    "diagram_problem": D.chain(
        "sdinf-p",
        "A draft invoice that never finalizes and therefore is never billed",
        "A draft has no number, no PDF and no hosted page, so the customer was "
        "never asked for the money and nothing anywhere is late.",
        [
            ("Invoice created", "auto_advance false"),
            ("No schedule", "automatically_finalizes_at null"),
            ("Never finalized", "no number, no PDF"),
            ("Never sent", "customer never asked"),
            ("Revenue short", "found in a report"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "sdinf-f",
        "Sorting old draft invoices by whether anything will ever finalize them",
        "The repair differs by state: finalize, hand it back to Stripe, fix the "
        "customer, or delete a draft that should never have existed.",
        ("GET /v1/invoices", "status=draft, created[lt] cutoff"),
        [
            ("Finalization scheduled", "leave it alone", "good"),
            ("amount_due is zero", "clutter, delete it", "plain"),
            ("auto_advance false", "stranded, finalize it", "bad"),
            ("Scheduled time passed", "read last_finalization_error", "bad"),
        ],
    ),
}

V["stripe/open-invoices-past-due-date"] = {
    "flow_intro": (
        "The script pages open invoices for the send_invoice collection method and "
        "compares due_date itself, because Stripe offers no server side filter for "
        "the one field that defines overdue."
    ),
    "diagram_problem": D.chain(
        "soipd-p",
        "An invoiced customer going unchased because reminders were never enabled",
        "send_invoice means Stripe emails the invoice and waits. Reminders and the "
        "past due subscription action are opt in.",
        [
            ("Invoice finalized", "emailed once"),
            ("Due date passes", "status stays open"),
            ("No reminder", "setting never enabled"),
            ("No status change", "nothing to alert on"),
            ("Aged receivable", "found at audit"),
        ],
        fail_at=1,
        loop=(4, 1, "the next cycle invoices again"),
    ),
    "diagram_fix": D.branch(
        "soipd-f",
        "Sorting open invoices by how far past their due date they have drifted",
        "Past 60 days no built in reminder will ever be sent, so enabling them "
        "today does nothing for that invoice.",
        ("GET /v1/invoices", "status=open, send_invoice"),
        [
            ("Within terms", "current, nothing to do", "good"),
            ("No due_date at all", "can never be overdue", "bad"),
            ("Under 30 days late", "inside the reminder window", "bad"),
            ("Over 60 days late", "chase by hand or write off", "bad"),
        ],
    ),
}

V["stripe/dunning-retries-exhausted"] = {
    "flow_intro": (
        "The script reads attempt_count and next_payment_attempt together, because "
        "the same attempt count means Stripe has given up or that a customer needs "
        "to send a new card, depending entirely on the second field."
    ),
    "diagram_problem": D.chain(
        "sdre-p",
        "Dunning finishing its retries with nobody told that it stopped",
        "The last failure looks exactly like the earlier ones. What marks the end "
        "is an attempt that is never scheduled, and absence fires no event.",
        [
            ("Card expires", "renewal declines"),
            ("Smart Retries run", "8 tries, 2 weeks"),
            ("Last retry fails", "next_payment_attempt null"),
            ("Status still open", "no event for the ending"),
            ("Access continues", "invoices keep stacking"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "sdre-f",
        "Sorting open invoices by attempt count and by the next scheduled attempt",
        "Four states out of two fields, and each one goes to a different person.",
        ("GET /v1/invoices", "status=open, charge_automatically"),
        [
            ("Few tries, one scheduled", "dunning is running", "good"),
            ("Many tries, none scheduled", "exhausted, decide", "bad"),
            ("Many tries, one scheduled", "hard decline, ask for a card", "bad"),
            ("Zero tries, none scheduled", "never charged at all", "bad"),
        ],
    ),
}

V["stripe/automatic-tax-disabled-everywhere"] = {
    "flow_intro": (
        "The script counts active subscriptions with tax switched off, then takes "
        "the countries from the invoices those subscriptions actually produced, "
        "because the countries are what turn a missing field into an exposure."
    ),
    "diagram_problem": D.chain(
        "satd-p",
        "Subscriptions billing without automatic tax while invoicing abroad",
        "Nothing errors. The payment succeeds, the invoice is delivered, and the "
        "total is simply missing a line.",
        [
            ("Create call omits it", "automatic_tax defaults false"),
            ("Tax enabled in Dashboard", "existing subs unchanged"),
            ("Invoices bill untaxed", "EU, UK, AU customers"),
            ("Payments succeed", "no error anywhere"),
            ("Liability compounds", "every month"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "satd-f",
        "Sorting an account by tax coverage and by where it is actually invoicing",
        "The same missing field is a backlog note in one market and a compounding "
        "liability across several.",
        ("GET /v1/subscriptions", "plus countries from paid invoices"),
        [
            ("Enabled everywhere", "covered", "good"),
            ("Off, one home country", "check your registrations", "plain"),
            ("Off, no address on file", "tax cannot be computed", "bad"),
            ("Off, invoicing the EU or UK", "backfill and take advice", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
