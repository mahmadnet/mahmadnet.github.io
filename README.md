# mahmadnet.github.io

This repository publishes Muhammad Ahmad's public GitHub overview at
`https://mahmadnet.github.io/`. The page uses factual GitHub data in a restrained,
personal profile rather than reproducing GitHub's application interface.

## Page implementation

The root page uses semantic HTML and responsive CSS with no client-side
JavaScript, package manager, framework, bundler, analytics, tracking, cookies,
external fonts, or third-party runtime assets. The approved portrait and the
original Arctic Code Vault Contributor badge are stored locally in `assets/`.
The visual system is documented in [`DESIGN.md`](DESIGN.md).

The public interface includes:

- a concise profile summary and one curated GitHub achievement;
- one allowlisted public build, `mahmadnet.github.io`;
- the real rolling-year contribution calendar with derived pace metrics; and
- twelve reconciled monthly activity summaries, with nine available through a
  native HTML disclosure control.

## Factual GitHub snapshot

The daily maintenance workflow uses only official GitHub sources:

- the public contribution fragment for exact daily calendar cells;
- the REST profile endpoint for public account facts;
- the REST repositories endpoint for the allowlisted public build; and
- one authenticated GraphQL request for uniform monthly totals covering
  commits, pull requests, reviews, issues, repositories created, and restricted
  contributions.

The Arctic Code Vault Contributor badge is a curated local copy of GitHub's
original 296×296 PNG. It is not refreshed by the updater and is not hotlinked.
Its SHA-256 is
`A808F9CD62C9D699C2274F0D4615D1AFBDE3A4051CBB5BEAA20DF2E6F38AC038`.

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
only the factual generated regions of `index.html`; it does not deploy the site
or change Pages settings.

## Development policy

Keep the repository focused on this user-site page and its documentation. Do
not add a custom domain, redirects, copied portfolio content, unapproved project
links, client-side JavaScript, external runtime assets, or unrelated deployment
configuration. Validate the updater, privacy allowlist, local assets, generated
markup, contrast, and complete diff before commit-related work. Staging,
committing, pushing, and Pages-setting changes require explicit approval.
