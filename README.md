# ai4mathnl.github.io

Website for the workshop **Shaping the Future of Mathematics with AI**,
Thursday 3 December 2026, 13:00-17:00, CWI Amsterdam.

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

Create the Google Form, then in Forms choose **Send > `<>`** and copy the
`src="..."` value. Paste it into `workshop.registration_form_url` in
`_config.yml`. That one change embeds the form on `/register/` and turns the
"not open yet" notice on the front page into a "Register" button. Leave it
empty and both pages say registration has not opened, so the page is safe to
publish before the form exists.

## Local preview

```bash
bundle install
bundle exec jekyll serve
```
