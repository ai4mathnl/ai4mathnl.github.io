# ai4mathnl.github.io

Website for the workshop **Shaping the Future of Mathematics with AI**,
Thursday 3 December 2026, 13:00-18:00, CWI Amsterdam.

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
via the `image:` line in `index.html`'s front matter. Regenerate it if the
title, date or venue change.

## Opening registration

Registration uses a Microsoft Form in TU Delft's Microsoft 365. Its embed URL
(in Forms: **Collect responses > `</>`**, the `src="..."` value) sits in
`workshop.registration_form_url` in `_config.yml`. While it is set, the form is
embedded on `/register/` and the front page shows a "Register" button. Empty it
to close registration: both pages then say registration is not open.

The form must be set to **Anyone can respond**, or everyone outside TU Delft is
asked to sign in and cannot register.

## Local preview

```bash
bundle install
bundle exec jekyll serve
```
