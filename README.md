# mahmadnet.github.io

This repository publishes Muhammad Ahmad's public GitHub overview at
`https://mahmadnet.github.io/`. The page is inspired by useful GitHub profile
patterns but uses a personal information hierarchy and silver-sage visual
system.

## Page implementation

The root page uses semantic HTML and responsive CSS with no client-side
JavaScript, package manager, framework, bundler, analytics, tracking, cookies,
external fonts, or third-party page assets. The approved portrait is stored
locally at `assets/avatar.jpg`; the design system is documented in
[`DESIGN.md`](DESIGN.md).

The public interface includes:

- a concise profile summary and CSS-only GitHub achievement medallions;
- one allowlisted public build, `mahmadnet.github.io`;
- the real rolling-year contribution calendar with derived pace metrics; and
- twelve reconciled monthly activity summaries, with nine available through a
  native HTML disclosure control.

## Factual GitHub snapshot

The daily maintenance workflow uses only official GitHub sources:

- the public contribution fragment for exact daily calendar cells;
- REST profile and repository endpoints for public facts;
- the public profile page for Pro status and achievement names; and
- one authenticated GraphQL request for uniform monthly totals covering
  commits, pull requests, reviews, issues, repositories created, and restricted
  contributions.

Restricted contributions are displayed only as aggregate counts. Private
repository names, commit messages, source responses, social links, and
unapproved project data are never persisted. The updater allowlists
`mahmadnet.github.io` as the only repository that may be rendered by name or
linked.

Run the tests and a validation-only live refresh locally with:

```powershell
$env:GITHUB_TOKEN = gh auth token
python -m unittest discover -s tests
python scripts/update_profile.py --dry-run
```

## Publishing

- Repository: `https://github.com/mahmadnet/mahmadnet.github.io`
- Production: `https://mahmadnet.github.io/`
- Default branch: `main`
- GitHub Pages source: repository root (`/`) on `main`

Pages publishes static root files directly. The maintenance workflow updates
generated regions of `index.html`; it does not deploy the site or change Pages
settings.

## Development policy

Keep the repository focused on this user-site page and its documentation. Do
not add a custom domain, redirects, copied portfolio content, unapproved project
links, client-side JavaScript, external page assets, or unrelated deployment
configuration. Validate the updater, privacy allowlist, generated markup,
contrast, and complete diff before commit-related work. Staging, committing,
pushing, and Pages-setting changes require explicit approval.
