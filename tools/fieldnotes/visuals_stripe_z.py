#!/usr/bin/env python3
"""Diagrams for the /stripe/ field notes, batch Z.

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

V["stripe/send-invoice-without-days-until-due"] = {
    "flow_intro": (
        "The script reads the terms off every send_invoice subscription and the "
        "due dates off the invoices they have already produced, so the "
        "configuration and the damage it has done are one report."
    ),
    "diagram_problem": D.chain(
        "szdud-p",
        "An invoiced subscription with no days_until_due producing invoices that never age",
        "Nothing in the chain errors. The invoice is simply never owed, so no "
        "part of the past due machinery has a date to measure from.",
        [
            ("Subscription created", "send_invoice, no terms"),
            ("Invoice finalized", "due_date null"),
            ("Emailed once", "no payment attempt"),
            ("Never overdue", "no anchor to pass"),
            ("No reminder", "receivable ages unseen"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "szdud-f",
        "Sorting invoiced subscriptions by their payment terms",
        "Zero is a real term and null is a missing one. A truthiness check "
        "collapses them and reports a working subscription as broken.",
        ("GET /v1/subscriptions", "collection_method=send_invoice"),
        [
            ("Terms inside the period", "due_date is set, leave it", "good"),
            ("days_until_due is 0", "due on receipt, deliberate", "plain"),
            ("Terms past the period", "next invoice beats this one", "bad"),
            ("days_until_due is null", "set terms, then reminders", "bad"),
        ],
    ),
}

V["stripe/draft-invoices-blocked-by-tax-location"] = {
    "flow_intro": (
        "The script reads the finalization error and the automatic tax fields "
        "off every draft, then rolls the findings up by customer, because the "
        "thing that needs fixing is an address rather than an invoice."
    ),
    "diagram_problem": D.chain(
        "sztlk-p",
        "A renewal invoice refused at finalization because the customer location cannot be resolved",
        "The subscription stays active throughout, so the customer keeps their "
        "access while no bill is ever sent.",
        [
            ("Renewal invoice", "created on schedule"),
            ("Tax calculation", "location unresolvable"),
            ("Finalize refused", "customer_tax_location_invalid"),
            ("Stays draft", "no number, no PDF"),
            ("Nothing collected", "subscription still active"),
        ],
        fail_at=1,
        loop=(3, 0, "every cycle adds another stuck draft"),
    ),
    "diagram_fix": D.branch(
        "sztlk-f",
        "Sorting draft invoices by what the tax fields actually recorded",
        "The disabled reason is read before the status: an invoice Stripe let "
        "through untaxed costs more than one that stuck.",
        ("GET /v1/invoices", "status=draft, tax fields read"),
        [
            ("customer_tax_location_invalid", "fix the address, then finalize", "bad"),
            ("tax disabled at finalization", "bills untaxed, no draft left", "bad"),
            ("requires_location_inputs", "no attempt failed yet, one will", "bad"),
            ("auto_advance false", "stranded, not tax blocked", "plain"),
            ("No tax error recorded", "leave it alone", "good"),
        ],
    ),
}

V["stripe/automatic-tax-requires-location-inputs"] = {
    "flow_intro": (
        "The script reads every invoice in a bounded window rather than only the "
        "drafts, because the invoices that already finalized untaxed are the "
        "half that cannot be repaired and the half that cost money."
    ),
    "diagram_problem": D.chain(
        "szrli-p",
        "A cohort of customers billed untaxed because Stripe Tax could not place them",
        "Stripe Tax is enabled and most invoices calculate correctly, so the "
        "share that never calculated at all is a number nobody has.",
        [
            ("Customer created", "email, no address"),
            ("Invoice raised", "automatic_tax enabled"),
            ("Calculation stops", "requires_location_inputs"),
            ("Tax dropped", "invoice finalizes untaxed"),
            ("Paid and frozen", "tax lines immutable"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "szrli-f",
        "Sorting invoices by what the automatic tax calculation reported",
        "Whether the invoice has left draft decides between a customer to fix "
        "and a credit note to write.",
        ("GET /v1/invoices", "created[gte] window, all statuses"),
        [
            ("disabled at finalization", "billed untaxed, already paid", "bad"),
            ("requires_location_inputs, open", "frozen, credit note only", "bad"),
            ("requires_location_inputs, draft", "fix the customer address", "bad"),
            ("status failed", "Stripe side, retry first", "plain"),
            ("status complete", "zero tax is a registration question", "good"),
        ],
    ),
}

V["stripe/missing-customer-tax-ids-b2b-eu"] = {
    "flow_intro": (
        "The script reads the tax IDs frozen onto each paid invoice, then checks "
        "the verification status of the ones that exist, because an unconfirmed "
        "VAT number counts as coverage in every list except an audit."
    ),
    "diagram_problem": D.chain(
        "szvat-p",
        "An EU business charged local VAT because no tax ID was attached to the customer",
        "Every step succeeds. The only trace is an empty array on a document "
        "that should have carried a VAT number and a reverse charge notice.",
        [
            ("Checkout without tax ID", "collection never enabled"),
            ("Customer looks B2C", "no tax ID on file"),
            ("VAT added", "reverse charge skipped"),
            ("Invoice finalized", "tax IDs frozen on it"),
            ("Buyer cannot reclaim", "invoice rejected"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "szvat-f",
        "Sorting paid EU invoices by tax ID and by the VAT actually charged",
        "No ID with VAT charged is money the buyer did not owe. No ID with no "
        "VAT is a missing registration, and a different team's work.",
        ("GET /v1/invoices", "status=paid, EU customer_address"),
        [
            ("Verified tax ID", "reverse charge available", "good"),
            ("customer_tax_exempt reverse", "already handled", "good"),
            ("ID present, unverified", "VIES did not confirm it", "bad"),
            ("No ID, VAT charged", "business billed as a consumer", "bad"),
            ("No ID, no VAT", "registration question instead", "plain"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
