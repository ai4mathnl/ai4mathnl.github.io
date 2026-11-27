# ai4mathnl.github.io

Website for the **AI4Math Workshop: Shaping the Future of Mathematics with AI**,
Friday 4 December 2026, 09:30-15:00, CWI Amsterdam.

Published at <https://ai4math.nl/> by GitHub Pages (Jekyll, built from the
`main` branch). The old <https://ai4mathnl.github.io/> address redirects there.
The custom domain is set in GitHub's Pages settings, which keeps the `CNAME`
file at the repository root in step.

## Editing

| What | Where |
|------|-------|
| Date, time, venue, registration form | `_config.yml` (`workshop:` block) |
| Programme | `_data/program.yml` |
| Organisers | `_data/organisers.yml` |
| Page text | `index.html` |
| Registration page | `register.html` (served at `/register/`) |
| Vision document page | `vision.html` (served at `/vision/`); its content is generated, see below |
| Styling | `assets/css/site.css` (not `style.css`: the default GitHub Pages theme writes its own file to that name) |
| Calendar file offered by "Add to calendar" | `calendar.ics` (reads `_config.yml`) |
| Logos, icons, sharing card | `assets/img/` |

The sharing card (`assets/img/social-card.png`) is never shown on the page: it
is what LinkedIn, Slack, WhatsApp and the like display when the link is posted,
via the `image:` line in `index.html`'s front matter. It reads the title, date,
time and venue from `_config.yml`, so regenerate it whenever those change:

```bash
pip install pillow font-hanken-grotesk
python3 tools/social_card.py
```

## Opening registration

Registration and payment run through CWI's store. The product page URL sits in
`workshop.registration_url` in `_config.yml`, with the price in
`workshop.registration_fee`. While the URL is set, `/register/` shows a button
to the store and the front page shows a "Register" button. Empty the URL to
close registration: both pages then say registration is temporarily closed.

The store sends `X-Frame-Options: DENY`, so it cannot be embedded in the page;
`/register/` links out to it instead.

CWI also publishes a copy of this page at
<https://www.cwi.nl/en/research/computational-imaging/events/ai4math-workshop-shaping-the-future-of-mathematics-with-ai/>.
It is maintained separately, so changes to the text here have to be passed on
to CWI by hand.

## Updating the vision document

`/vision/` shows the vision document that is written in LaTeX in a separate
repository. Its text is never edited here: `tools/vision_to_site.py` converts
`vision.tex` and copies the compiled PDF that the page offers for download.
Compile `vision.tex` first, then run:

```bash
python3 tools/vision_to_site.py path/to/vision.tex
```

While `vision_draft` in `_config.yml` is true, the page says prominently that
the text is a draft for discussion at the workshop. For the final version, set
it to false and take "draft" out of the description in `vision.html`'s front
matter.

Commit the three files the script writes: `_includes/vision-body.html`,
`_data/vision.json` (title, authors, date, section titles) and
the PDF in `assets/`, which is named after the version and date in the document's `\date` line, as in
`AIM2027FutureOfMathVision - v1 - 27-11-2026.pdf`, and replaces the previous
copy. The date on
the page is the day the PDF was compiled. The list under "What will be
discussed?" on the front page is made of the section titles, so it follows the
document as well.

The script understands only the LaTeX that the document uses, and stops with a
message when it meets anything else, so that nothing reaches the page garbled.
It also stops at editorial notes (`\tim{...}`, `\christoph{...}`); pass
`--draft` to show them highlighted on the page for a preview that is not
published. Footnotes are collected in a "Notes" list at the end of the page.

## Local preview

```bash
bundle install
bundle exec jekyll serve
```
