#!/usr/bin/env python3
"""Diagrams for the /twilio/ field notes, batch N.

The four brand states either side of a plain FAILED: the wait that never ends,
the suspension that cascades down, the one code behind most Standard brand
rejections, and the approval that still leaves you throttled. Same two shapes as
the rest of the site, drawn in Twilio red.

No em dashes inside SVG text. One mis-sniffed encoding turns a single character
into three mojibake ones inside an image, where nothing will catch it.
"""
import diagrams as D

# Set before the diagrams below are built, restored at the bottom of the module.
# Every diagram here is constructed at import time, so the theme has to be active
# across exactly this file and no further.
BRAND = "#F22F46"
D.set_theme(BRAND)

V = {}

V["twilio/a2p-brand-stuck-pending-review"] = {
    "flow_intro": (
        "The classifier takes the current time as an argument rather than reading "
        "the clock, because the only evidence of this problem is arithmetic on "
        "date_created and a test has to be able to pick the day."
    ),
    "diagram_problem": D.chain(
        "tbstall-p",
        "A brand submitted five weeks ago that nobody knows is still waiting",
        "Nothing here returns an error. The callback fired into a service that "
        "was not deployed yet, and a missed callback looks exactly like a review "
        "still running.",
        [
            ("Brand submitted", "status PENDING"),
            ("Callback fires once", "endpoint returns 502"),
            ("Nobody polls", "no error to find"),
            ("No campaign can attach", "tcr_id still null"),
            ("Every US send 30034", "launch date passes"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tbstall-f",
        "Sorting brands by which wait they are in and how long it has run",
        "PENDING and IN_REVIEW are not the same wait. One is a support ticket "
        "past a week; the other is a human doing their job.",
        ("GET BrandRegistrations", "status, date_created, tcr_id"),
        [
            ("PENDING under 7 days", "validation still running", "good"),
            ("IN_REVIEW, any age", "manual vetting, wait", "plain"),
            ("PENDING over 7 days", "stuck, raise a ticket", "bad"),
            ("Two brands, one bundle", "duplicate, 30898 next", "bad"),
        ],
    ),
}

V["twilio/a2p-brand-suspended"] = {
    "flow_intro": (
        "The script reads two resources and joins them on brand_registration_sid, "
        "because a suspended object on its own cannot tell you whether it is the "
        "cause or the consequence."
    ),
    "diagram_problem": D.chain(
        "tbsusp-p",
        "Four Messaging Services failing at once for one brand suspension",
        "The code arrives at the campaign and the decision was made at the brand, "
        "so four teams start four investigations into one cause.",
        [
            ("Brand suspended", "compliance review"),
            ("Cascade downward", "every campaign with it"),
            ("Sends return 30033", "campaign suspended"),
            ("Campaign edit refused", "21729, not a hint"),
            ("Brand edit refused", "21731, still no reason"),
        ],
        fail_at=0,
    ),
    "diagram_fix": D.branch(
        "tbsusp-f",
        "Sorting suspensions by which layer actually changed state",
        "A suspended brand over campaigns still reading VERIFIED is the same "
        "cascade, caught before the campaign resource updated.",
        ("Brands joined to campaigns", "on brand_registration_sid"),
        [
            ("Brand APPROVED, none suspended", "nothing to do", "good"),
            ("Campaign only", "read its errors[]", "plain"),
            ("Brand and campaigns", "cascade, brand first", "bad"),
            ("Brand only, so far", "sends fail anyway", "bad"),
        ],
    ),
}

V["twilio/a2p-brand-tax-id-legal-name-mismatch"] = {
    "flow_intro": (
        "The script prints the Customer Profile bundle rather than following it "
        "into an edit, because the repair is a person correcting a business "
        "record against a tax filing and no script should do that on a schedule."
    ),
    "diagram_problem": D.chain(
        "tbein-p",
        "A brand rejected because the trading name is not the legal name",
        "Every value submitted is correct as far as the people submitting it "
        "know. The registry compares against the IRS file and nothing else.",
        [
            ("Profile submitted", "the name everyone uses"),
            ("Registry looks up EIN", "against public records"),
            ("Legal name differs", "suffix, address or DBA"),
            ("Brand FAILED 30799", "unable to verify"),
            ("Resubmitted unchanged", "same lookup, same answer"),
        ],
        fail_at=2,
    ),
    "diagram_fix": D.branch(
        "tbein-f",
        "Sorting brand failures by whether identity was the thing that failed",
        "The error is on the brand and the data is on the Trust Hub profile, so "
        "the object to read is never the object to edit.",
        ("GET the brand, read errors[]", "code, fields, bundle sid"),
        [
            ("APPROVED and verified", "identity matched", "good"),
            ("FAILED on another code", "a different profile", "plain"),
            ("30799 with fields", "edit exactly those", "bad"),
            ("30799, no fields", "name, address, tax id", "bad"),
        ],
    ),
}

V["twilio/a2p-brand-missing-secondary-vetting"] = {
    "flow_intro": (
        "brand_score is tested against null rather than for truthiness, because "
        "the scale starts at zero: a score of 0 is the lowest trust rating there "
        "is, and it is not the same as never having been vetted."
    ),
    "diagram_problem": D.chain(
        "tbvet-p",
        "An approved brand queueing behind a throughput ceiling nobody set",
        "Every status field reads successfully. The problem is a number that is "
        "absent rather than a field that is wrong.",
        [
            ("Brand APPROVED", "registration complete"),
            ("Vetting never ran", "skip flag set at creation"),
            ("brand_score null", "no trust rating"),
            ("Carriers floor the MPS", "lowest tier"),
            ("Sends queue under load", "reads as slowness"),
        ],
        fail_at=1,
    ),
    "diagram_fix": D.branch(
        "tbvet-f",
        "Sorting approved brands by whether a score was ever expected",
        "Sole Proprietor and Low-Volume Standard brands are correctly scoreless. "
        "Flagging them buries the Standard brand that lost its vetting.",
        ("Brand plus its Vettings", "type, score, vetting_status"),
        [
            ("brand_score present", "0 counts, scale starts there", "good"),
            ("Not a Standard brand", "never scored, by design", "plain"),
            ("Standard, no vetting", "request it, MPS is floored", "bad"),
            ("Vetting FAILED", "approved and untrusted", "bad"),
        ],
    ),
}

# Back to the default so an import after this one is unaffected.
D.reset_theme()
