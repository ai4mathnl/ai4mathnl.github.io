# ai4mathnl.github.io

Website for the workshop **A Vision on the Future of Mathematics with AI**,
Thursday 3 December 2026, 13:00-17:00, CWI Amsterdam.

Published at <https://ai4mathnl.github.io/> by GitHub Pages (Jekyll, built from
the `main` branch).

## Editing

| What | Where |
|------|-------|
| Date, time, venue, registration link | `_config.yml` (`workshop:` block) |
| Programme | `_data/program.yml` |
| Page text | `index.html` |
| Styling | `assets/css/style.css` |

Registration link: set `workshop.registration_url` in `_config.yml` and the
"Register" button replaces the "not open yet" notice automatically.

## Local preview

```bash
bundle install
bundle exec jekyll serve
```
