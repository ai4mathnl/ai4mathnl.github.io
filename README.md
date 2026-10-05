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
| Styling | `assets/css/style.css` |
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

## Local preview

```bash
bundle install
bundle exec jekyll serve
```
