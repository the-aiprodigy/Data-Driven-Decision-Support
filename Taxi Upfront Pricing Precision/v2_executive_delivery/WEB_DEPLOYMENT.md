# Live hosting (GitHub Pages)

1. Push branch to GitHub.
2. Merge PR to `main` (or use `gh-pages` branch).
3. In repo settings: **Pages** → Source: `Deploy from a branch`.
4. Select branch `main` and folder `/Taxi Upfront Pricing Precision/v2_executive_delivery` if supported, otherwise move `interactive_report_v2.html` to `/docs` and choose `/docs`.
5. Access live URL after build completes.

Recommended fallback:
- Keep a copy at `/docs/interactive_report_v2.html` for deterministic Pages hosting.
