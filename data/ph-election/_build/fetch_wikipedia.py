#!/usr/bin/env python3
"""2022 Philippine national election results, via Wikipedia's transcription.

    .venv/bin/python data/ph-election/_build/fetch_wikipedia.py

The source chain here is weaker than every other project in this repository, and
the page says so in the open rather than burying it in a method note.

The primary record is the Congress canvass. Wikipedia cites it precisely -- a
Senate PDF at legacy.senate.gov.ph -- and both that host and comelec.gov.ph
return 403 to anything that is not a browser. There is no open COMELEC API. So
the figures below are Wikipedia's transcription of the canvass, and the primary
URLs are carried through to the page so a reader can check them by hand.

Three things make that auditable rather than merely convenient:

* Every row records the revision id it came from. Wikipedia is editable, and a
  number that cannot be tied to a revision cannot be rechecked later.
* The results templates are structured (one key per candidate), so the parse is
  a key lookup rather than table scraping.
* Regional tables ARE scraped, and are therefore reconciled against the national
  totals in checks.sql. A wikitext parse that goes wrong almost never goes wrong
  in a way that still sums correctly, so the reconciliation is the real
  guarantee, not the parser.
"""
import csv
import json
import os
import re
import ssl
import urllib.parse
import urllib.request

OUT = os.path.join(os.path.dirname(__file__), "..")
API = "https://en.wikipedia.org/w/api.php"
UA = "allanninal.dev research (contact via github.com/allanninal)"
ARTICLE = "2022 Philippine presidential election"
TEMPLATES = {
    "president": "Template:2022 Philippine presidential election results",
    "vice_president": "Template:2022 Philippine vice presidential election results",
}


def get(page):
    q = urllib.parse.urlencode({"action": "parse", "page": page,
                                "prop": "wikitext|revid", "format": "json",
                                "formatversion": "2"})
    req = urllib.request.Request(API + "?" + q, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=120,
                                context=ssl.create_default_context()) as r:
        d = json.loads(r.read())
    if "parse" not in d:
        raise SystemExit("Wikipedia returned no parse for %r: %s"
                         % (page, d.get("error", d)))
    return d["parse"]["wikitext"], d["parse"]["revid"]


# A wikitable cell may carry attributes before its value, separated by a
# second pipe:  | bgcolor="#fe18a3" |{{white|2,451,454}}
# Left in place, the hex colour's digits are glued onto the vote count by
# num(), turning Robredo's 2,451,454 in Bicol into 1,832,451,454 -- and the
# region then fails to reconcile by 1.8 billion. Attributes are stripped
# before anything else touches the cell.
ATTR = re.compile(r'^\s*(?:[A-Za-z-]+\s*=\s*(?:"[^"]*"|\'[^\']*\'|\S+)\s*)+\|(?!\|)')


def strip_attrs(cell):
    prev = None
    while prev != cell:
        prev = cell
        cell = ATTR.sub('', cell, count=1)
    return cell

# Templates whose payload IS the value, and must be unwrapped rather than
# stripped. The winning candidate's cell in every regional table is a
# {{party color cell|...}} followed by a {{white|...}} wrapping the bolded
# vote count. Deleting every template removes the count itself, and the next
# number in the row -- the runner-up -- silently slides into its place. That
# produced a table in which Marcos lost Ilocos, which is how this was caught.
KEEP = ("white", "black", "nowrap", "nobold", "small")


def clean(s):
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S)
    s = re.sub(r"<ref[^>]*/>", "", s)
    s = re.sub(r"\{\{efn\|.*?\}\}", "", s, flags=re.S)
    s = re.sub(r"\{\{[Ss]ortname\|([^|}]*)\|([^|}]*)(?:\|[^}]*)?\}\}", r"\1 \2", s)
    for _ in range(4):                        # wrappers can nest
        s = re.sub(r"\{\{\s*(?:%s)\s*\|([^{}]*)\}\}" % "|".join(KEEP),
                   r"\1", s, flags=re.I)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]|]*)\]\]", r"\1", s)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = s.replace(chr(39) * 3, "").replace(chr(39) * 2, "")
    s = re.sub(r"\|\s*color\d+\s*=\s*#\w+", "", s)
    return re.sub(r"\s+", " ", s).strip()

def num(s):
    s = re.sub(r"[^\d]", "", s or "")
    return int(s) if s else None


def parse_results(w):
    """{cand_n: (name, party, votes)} plus valid/invalid/electorate/source."""
    field = lambda k: (re.search(r"\|\s*%s\s*=\s*([^\n|]*)" % k, w) or [None, ""])[1] \
        if re.search(r"\|\s*%s\s*=\s*([^\n|]*)" % k, w) else ""
    cands = []
    for n in range(1, 25):
        c = re.search(r"\|\s*cand%d\s*=\s*(.+)" % n, w)
        v = re.search(r"\|\s*votes%d\s*=\s*([\d,]+)" % n, w)
        p = re.search(r"\|\s*party%d\s*=\s*(.+)" % n, w)
        if not (c and v):
            continue
        cands.append((n, clean(c.group(1)), clean(p.group(1)) if p else "",
                      num(v.group(1))))
    if not cands:
        raise SystemExit("results template parsed but no candidates found -- "
                         "the template's parameter naming changed")
    meta = {}
    for k in ("valid", "invalid", "electorate"):
        m = re.search(r"\|\s*%s\s*=\s*([\d,]+)" % k, w)
        meta[k] = num(m.group(1)) if m else None
    m = re.search(r"\|\s*source\s*=\s*(.+)", w)
    meta["source_note"] = clean(m.group(1))[:300] if m else ""
    urls = re.findall(r"https?://[^\s\]]+", w)
    meta["primary_urls"] = " ; ".join(dict.fromkeys(urls))[:500]
    return cands, meta


def fnum(s):
    """Parse a table cell that may be a count (2,552,114) or a share (84.69)."""
    t = re.sub(r"[^\d.]", "", s or "")
    if not t or t.count(".") > 1:
        return None
    try:
        return float(t)
    except ValueError:
        return None

def region_rows(w, caption, start_from=0):
    """[(area, [votes per candidate], total)] from a 'Result per X' table."""
    i = w.find("|+" + caption, start_from)
    if i < 0:
        return None, None, -1
    start = w.rindex("{|", 0, i)
    end = w.find("\n|}", start)
    tbl = w[start:end]
    names = re.findall(r'! colspan="2"[^|]*\|\s*\[\[[^\]]*\|([^\]]+)\]\]', tbl)
    if not names:
        names = re.findall(r'! colspan="2"[^|]*\|\s*\[\[([^\]|]+)\]\]', tbl)
    out = []
    for block in tbl.split("\n|-")[1:]:
        cells = [clean(strip_attrs(c)) for c in re.split(r"\n\s*\|", block)]
        cells = [c for c in cells if c]
        if len(cells) < 5:
            continue
        area = cells[0]
        if not area or area.lower().startswith(("total", "region", "island", "!")):
            continue
        nums = [fnum(c) for c in cells[1:] if fnum(c) is not None]
        if len(nums) < 5:
            continue
        out.append((area, nums))
    return names, out, end


def write(name, cols, rows):
    with open(os.path.join(OUT, name), "w", newline="") as fh:
        wr = csv.writer(fh)
        wr.writerow(cols)
        wr.writerows(rows)
    print("wrote %s (%d rows)" % (name, len(rows)))


def main():
    cand_rows, meta_rows = [], []
    for race, tpl in TEMPLATES.items():
        w, rev = get(tpl)
        src = "Wikipedia %s (revid %s)" % (tpl, rev)
        cands, meta = parse_results(w)
        total = sum(c[3] for c in cands)
        for n, name, party, votes in cands:
            cand_rows.append([race, n, name, party, votes,
                              round(100.0 * votes / meta["valid"], 4)
                              if meta["valid"] else "", rev, src])
        print("  %-15s %2d candidates, %s valid votes, %s electorate"
              % (race, len(cands), format(meta["valid"] or 0, ","),
                 format(meta["electorate"] or 0, ",")))
        if meta["valid"] and abs(total - meta["valid"]) > 0:
            print("     note: candidate votes sum to %s against a stated valid "
                  "total of %s (difference %s)"
                  % (format(total, ","), format(meta["valid"], ","),
                     format(total - meta["valid"], ",")))
        for k in ("valid", "invalid", "electorate"):
            meta_rows.append([race, k, meta[k], "", rev, src])
        meta_rows.append([race, "candidate_votes_sum", total, "", rev, src])
        meta_rows.append([race, "turnout_pct",
                          round(100.0 * ((meta["valid"] or 0) + (meta["invalid"] or 0))
                                / meta["electorate"], 4) if meta["electorate"] else "",
                          "valid + invalid over electorate", rev, src])
        meta_rows.append([race, "primary_source_urls", "", meta["primary_urls"],
                          rev, src])

    write("ph_election_candidates.csv",
          ["race", "rank", "candidate", "party", "votes", "share_of_valid_pct",
           "revid", "source"], cand_rows)
    # Regional tables live in the article, not the templates.
    w, rev = get(ARTICLE)
    src = "Wikipedia %s (revid %s)" % (ARTICLE, rev)
    regions, disc, cursor = [], [], 0
    for race in ("president", "vice_president"):
        names, rows, cursor = region_rows(w, "Result per region", cursor)
        if not rows:
            print("  %s: no region table found" % race)
            continue
        for area, nums in rows:
            votes = nums[0:-2:2]
            shares = nums[1:-2:2]
            total = nums[-2]
            # Named candidates are taken as published; "Others" is DERIVED as
            # the remainder. Every named cell in every region reconciles with
            # its own stated share to within 0.05 points, but three "Others"
            # cells do not -- IV-B states 7.44% against a computed 12.94%, and
            # VI and VII disagree by about a point each in opposite directions.
            # Trusting the published Others makes those regions fail to add up;
            # deriving it makes every region sum exactly to its stated total and
            # keeps the disagreement visible in the coverage file instead of
            # inside a chart.
            named = 0
            for k, v in enumerate(votes):
                label = names[k] if k < len(names) else None
                if label is None:
                    continue
                named += v
                regions.append([race, area, label, int(v), int(total),
                                "published", rev, src])
                stated = shares[k] if k < len(shares) else None
                if stated is not None and total and abs(100.0 * v / total - stated) > 0.05:
                    disc.append([race, area, label, int(v), stated,
                                 round(100.0 * v / total, 2), rev, src])
            if len(votes) > len(names):
                published_other = votes[len(names)]
                stated = shares[len(names)] if len(shares) > len(names) else None
                if stated is not None and total and \
                        abs(100.0 * published_other / total - stated) > 0.05:
                    disc.append([race, area, "Others (published, not used)",
                                 int(published_other), stated,
                                 round(100.0 * published_other / total, 2), rev, src])
                regions.append([race, area, "Others", int(total - named), int(total),
                                "derived as total minus named", rev, src])
        print("  %-15s %d regions parsed" % (race, len(rows)))
    # How much of the national vote the regional table actually accounts for.
    # The presidential table's eighteen rows sum to 97.79% of the valid vote it
    # itself declares in its total row -- about 1.18 million votes are simply not
    # in any row. The vice-presidential table sums exactly. That gap is a
    # property of the source, not of this parse, and it means regional figures
    # must never be presented as adding up to the national result.
    valid = {r[0]: r[2] for r in meta_rows if r[1] == "valid"}
    for race in ("president", "vice_president"):
        got = sum(v for k, (rc, area, cand, v, tot, basis, rv, sr)
                  in enumerate((tuple(x) for x in regions)) if rc == race
                  and cand != "Others") \
            + sum(x[3] for x in regions if x[0] == race and x[2] == "Others")
        meta_rows.append([race, "regional_table_votes", got, "", "", ""])
        if valid.get(race):
            meta_rows.append([
                race, "regional_coverage_pct", round(100.0 * got / valid[race], 2),
                "share of the national valid vote present in the regional table",
                "", ""])
            print("  %-15s regional table covers %.2f%% of the national valid vote"
                  % (race, 100.0 * got / valid[race]))

    write("ph_election_totals.csv",
          ["race", "metric", "value", "note", "revid", "source"], meta_rows)

    write("ph_election_regions.csv",
          ["race", "region", "candidate", "votes", "region_total", "basis",
           "revid", "source"], regions)
    write("ph_election_source_discrepancies.csv",
          ["race", "region", "candidate", "published_votes", "published_share_pct",
           "share_implied_by_votes_pct", "revid", "source"], disc)
    if disc:
        print("  %d source cell(s) where the published vote and the published "
              "share disagree -- see ph_election_source_discrepancies.csv" % len(disc))


if __name__ == "__main__":
    main()
