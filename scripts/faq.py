#!/usr/bin/env python3
"""Regenerates the FAQ block and its FAQPage JSON-LD from ONE source.

Why this exists: the page previously carried a FAQPage with six questions that
appeared nowhere on the page, and prices in prose drift away from the prices the
builder charges. Both halves are written here, from the numbers in `CFG`, so
they cannot disagree. After changing a price in CFG, run:

    python3 scripts/faq.py

It rewrites what is between the FAQ:START/END and FAQ-LD:START/END markers in
index.html and fails loudly if the two halves ever stop matching.
"""
import io, json, re, sys, math, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
HTML = ROOT / 'index.html'
src = io.open(HTML, encoding='utf-8').read()


def cfg():
    """Read the builder's own price book rather than retyping it."""
    raw = re.search(r'const CFG=\{(.*?)\};', src, re.S).group(1)
    num = lambda k: float(re.search(k + r'\s*:\s*([0-9.]+)', raw).group(1))
    tr = re.search(r'transfer:\{sjd:([0-9.]+),csl:([0-9.]+)\}', raw)
    return dict(tax=num('taxRate'), deposit=num('depositRate'),
                sjd=float(tr.group(1)), csl=float(tr.group(2)),
                chef=num('chefMeal'), barman=num('barman'), yacht=num('yacht'),
                grocery=num('grocery'), decor=num('decor'),
                night=num('nightBase'), late=num('nightLate'))


C = cfg()
usd = lambda n: '$' + format(int(round(n)), ',d')

# The default weekend the builder itself opens with: 10 guests, 3 nights,
# San Jose, one chef dinner, one night out.
GUESTS = 10
vehicles = math.ceil(GUESTS / 11)
full_sub = (C['decor'] + C['chef'] + C['barman'] + C['sjd'] * 2 * vehicles
            + C['grocery'] + C['yacht'] + C['night'] * vehicles)
full_total = full_sub * (1 + C['tax'])
full_per = full_total / GUESTS

# The smallest thing worth calling a weekend: the chef and the airport rides.
lean_total = (C['chef'] + C['sjd'] * 2 * vehicles) * (1 + C['tax'])
lean_per = lean_total / GUESTS

QA = [
 ("How much does a bachelorette party in Cabo cost?",
  f"For ten guests, everything switched on — welcome decor, a private chef dinner, "
  f"the barman with the margarita buffet, round-trip airport transfers, the villa "
  f"stocked before you land, three hours on a yacht and a night out — the weekend "
  f"comes to {usd(full_total)} with tax, or <strong>{usd(full_per)} per guest</strong>. "
  f"Take only the chef and the airport rides and it is {usd(lean_total)}, "
  f"{usd(lean_per)} each. The villa is yours and is not in these numbers."),

 ("How much does each guest pay?",
  f"That is the number the menu above shows you, live, before you commit to "
  f"anything. Set your dates and your headcount, tap the pieces you want, and the "
  f"per-guest split updates as you go. Nobody has to work it out on a group chat "
  f"at midnight. Tax of {C['tax']*100:.1f}% is already inside the figure; "
  f"gratuity is not."),

 ("How far ahead do we need to book?",
  "Less than you think. We have put a chef in a villa with <strong>eight hours' "
  "notice</strong>. What genuinely needs months is the handful of dates the whole "
  "town wants at once — December 31 above all, and the week around it. If your "
  "weekend falls there, write to us now, not in November."),

 ("How many nights does a Cabo bachelorette usually run?",
  "Three or four. Two is an expensive way to spend most of your time in a van, "
  "and past five the group starts splitting up. Three nights is what the menu "
  "opens on because it is what most groups end up choosing: a welcome dinner, a "
  "day on the water, and one night out."),

 ("When is the cheapest time to come?",
  "September and early October. The town is at its emptiest and the prices are "
  "the lowest of the year. It is also hurricane season, and we will say so plainly "
  "rather than let you find out in August — it is a real trade, and worth making "
  "with open eyes. From November the town fills up and does not empty again "
  "until after Easter."),

 ("Villa or hotel?",
  "Villa, for a group. A hotel gives you rooms; a villa gives you a kitchen, a "
  "pool and a table long enough to seat everyone, which is where the weekend "
  "actually happens. One thing worth knowing before you book: a few communities "
  "— <strong>Montecristo and Novaispania among them</strong> — do not let outside "
  "chefs in and require you to use their own. Beautiful houses, but the kitchen "
  "is not yours. Ask us before you sign, and we will tell you what a given address "
  "allows."),

 ("San José del Cabo or Cabo San Lucas?",
  f"San José is quieter, closer to the airport and better for a group that wants "
  f"long dinners; Cabo San Lucas is the marina, the clubs and the noise. Round-trip "
  f"transfers run {usd(C['sjd'])} per vehicle to San José and {usd(C['csl'])} to "
  f"Cabo San Lucas, so it barely moves the budget — choose on how you want the "
  f"nights to feel, not on the transfer."),

 ("Can you handle a group bigger than twelve?",
  "Yes, and you should tell us the real number early. The chef, barman, grocery, "
  "yacht and decor packages are priced up to twelve, and airport vehicles carry "
  "eleven with luggage, so beyond that we add a second chef, a second vehicle, or "
  "a bigger boat. None of it is a problem. All of it is easier with notice."),
]

detail = "\n".join(
  f'      <details class="qa">\n'
  f'        <summary>{q}</summary>\n'
  f'        <div class="qa-a"><p>{a}</p></div>\n'
  f'      </details>'
  for q, a in QA)

visible = f"""<!-- FAQ:START (generated by scripts/faq.py - do not hand-edit) -->
<section class="band" id="faq" style="padding-top:90px;padding-bottom:96px">
  <div class="wrap">
    <div class="sec-head reveal" style="max-width:40rem"><span class="eyebrow">Before you ask</span><h2 class="display">The questions everyone asks.</h2>
      <p>Straight answers, with our own numbers in them.</p></div>
    <div class="qa-list reveal">
{detail}
    </div>
  </div>
</section>
<!-- FAQ:END -->"""

strip = lambda t: re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', t)).strip()
ld = {"@context": "https://schema.org", "@type": "FAQPage",
      "url": "https://cabobachelorette.privatechefloscabos.com/",
      "mainEntity": [{"@type": "Question", "name": q,
                      "acceptedAnswer": {"@type": "Answer", "text": strip(a)}}
                     for q, a in QA]}
jsonld = ('<!-- FAQ-LD:START (generated by scripts/faq.py - do not hand-edit) -->'
          '<script type="application/ld+json">'
          + json.dumps(ld, ensure_ascii=False, separators=(',', ':'))
          + '</script><!-- FAQ-LD:END -->')


def swap(text, start, end, block):
    i, j = text.index(start), text.index(end) + len(end)
    return text[:i] + block + text[j:]


out = swap(src, '<!-- FAQ:START', '<!-- FAQ:END -->', visible)
out = swap(out, '<!-- FAQ-LD:START', '<!-- FAQ-LD:END -->', jsonld)

# Parity: every question and answer in the markup must be readable on the page.
for q, a in QA:
    assert q in out, q
    assert strip(a) in json.dumps(ld, ensure_ascii=False), q
io.open(HTML, 'w', encoding='utf-8').write(out)
print(f'FAQ: {len(QA)} questions, both halves from CFG.')
print(f'  full weekend {usd(full_total)} = {usd(full_per)}/guest | lean {usd(lean_total)} = {usd(lean_per)}/guest')
