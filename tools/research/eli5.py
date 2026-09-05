#!/usr/bin/env python3
"""Splice ELI5-rewritten prose into a blog post, and score its reading level.

Usage:
  eli5.py splice <post.html> <new-prose.html>   # replace the article-content prose
  eli5.py sub <post.html> <new subtitle text>   # replace the <p class="subtitle">
  eli5.py score <post.html> [...]               # Flesch ease / grade / words-per-sentence
"""
import html
import re
import sys

OPEN = '<div class="article-content">'
CLOSE = '<div class="project-link-box">'


def splice(path, prose_path):
    s = open(path).read()
    i = s.find(OPEN)
    j = s.find(CLOSE)
    if i < 0 or j < 0 or j < i:
        sys.exit(f"markers not found in {path}")
    prose = open(prose_path).read().rstrip() + "\n\n                "
    out = s[: i + len(OPEN)] + "\n" + prose + s[j:]
    open(path, "w").write(out)
    print(f"spliced {path}: {j - i} chars -> {len(prose)}")


def sub(path, text):
    s = open(path).read()
    new = f'<p class="subtitle">{text}</p>'
    out, n = re.subn(r'<p class="subtitle">.*?</p>', new, s, count=1, flags=re.S)
    if not n:
        sys.exit(f"no subtitle in {path}")
    open(path, "w").write(out)
    print(f"subtitle set in {path}")


def syllables(w):
    w = re.sub(r"[^a-z]", "", w.lower())
    if not w:
        return 0
    n, prev = 0, False
    for c in w:
        cur = c in "aeiouy"
        if cur and not prev:
            n += 1
        prev = cur
    if w.endswith("e") and n > 1:
        n -= 1
    return max(n, 1)


def body_text(path):
    s = open(path).read()
    i, j = s.find(OPEN), s.find(CLOSE)
    if i >= 0 and j > i:
        s = s[i:j]
    s = re.sub(r"<script.*?</script>", " ", s, flags=re.S)
    s = re.sub(r"<style.*?</style>", " ", s, flags=re.S)
    # Not prose, and scoring it as prose is a category error. The
    # Supabase/AWS post is 91 KB of which 33 KB is two <pre> blocks and 11 KB is
    # fourteen tables -- nearly half the document. Read as running text that
    # scored 63.2 ease and grade 7.1 and failed, while the actual prose passes.
    # A shell command has no reading level; a price table has no sentences.
    for tag in ("pre", "table", "code", "figure", "svg"):
        s = re.sub(r"<%s\b.*?</%s>" % (tag, tag), " ", s, flags=re.S | re.I)
    # block boundaries end a sentence, else list items and headings merge
    # into one giant run and inflate words-per-sentence. Cell and row ends are
    # here as a fallback: a table that escapes the strip above would otherwise
    # collapse an entire row into one sentence, which is how a 154-word
    # "sentence" appeared in the diagnostics.
    s = re.sub(r"</(p|li|h[1-6]|div|ol|ul|blockquote|td|th|tr|dt|dd|figcaption)>",
               ". ", s)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", html.unescape(s))
    return re.sub(r"(\.\s*)+\.", ".", s)


def score(paths):
    print(f"{'file':34}{'words':>7}{'w/sent':>8}{'ease':>7}{'grade':>7}  flag")
    eases, grades = [], []
    for p in paths:
        t = body_text(p)
        sents = [x for x in re.split(r"[.!?]+", t) if len(x.split()) > 2]
        words = re.findall(r"[A-Za-z']+", t)
        if not sents or not words:
            print(f"{p:34}{'-':>7}")
            continue
        W, S = len(words), len(sents)
        Y = sum(syllables(w) for w in words)
        ease = 206.835 - 1.015 * (W / S) - 84.6 * (Y / W)
        grade = 0.39 * (W / S) + 11.8 * (Y / W) - 15.59
        eases.append(ease)
        grades.append(grade)
        flag = "ok" if ease >= 70 and grade <= 6 else "MISS"
        name = p.split("/")[-1]
        print(f"{name:34}{W:>7}{W/S:>8.1f}{ease:>7.1f}{grade:>7.1f}  {flag}")
        if flag == "MISS":
            # Both formulas take words-per-sentence and syllables-per-word. Only
            # the first is a writing choice; the second is largely fixed by the
            # subject, because a product name has the syllables it has. So report
            # the sentence length each target would need at this syllable load.
            # The Supabase/AWS post needs 5.2 words per sentence to reach ease 70
            # -- a telegram, not prose -- because "Supabase" is four syllables and
            # appears forty-one times. Saying so beats leaving a permanent MISS
            # that invites someone to keep shortening sentences that are already
            # short enough.
            spw = Y / W
            need_ease = (206.835 - 84.6 * spw - 70) / 1.015
            need_grade = (6 + 15.59 - 11.8 * spw) / 0.39
            def phrase(n):
                return f"{n:.1f} w/sent" if n >= 3 else "unreachable at any length"
            print(f"{'':34}{'':>7}{'':>8}  at {spw:.3f} syllables/word this needs "
                  f"{phrase(need_ease)} for ease 70, "
                  f"{phrase(need_grade)} for grade 6")
    if eases:
        eases.sort()
        grades.sort()
        m = len(eases) // 2
        print(f"\nmedian ease {eases[m]:.1f}  median grade {grades[m]:.1f}  n={len(eases)}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "splice":
        splice(sys.argv[2], sys.argv[3])
    elif cmd == "sub":
        sub(sys.argv[2], " ".join(sys.argv[3:]))
    elif cmd == "score":
        score(sys.argv[2:])
    else:
        sys.exit(__doc__)
