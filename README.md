# mahmadnet.github.io

This repository publishes Ahmad's public GitHub overview at
`https://mahmadnet.github.io/`. The page uses factual GitHub data in a
restrained personal profile rather than reproducing GitHub's application
interface.

## Page implementation

The root page uses semantic HTML and responsive CSS with no client-side
JavaScript, package manager, framework, bundler, analytics, tracking, cookies,
external fonts, or third-party runtime assets. The approved portrait and the
original Arctic Code Vault Contributor badge are stored locally in `assets/`.
The visual system is documented in [`DESIGN.md`](DESIGN.md).

The public interface includes:

- a concise Ahmad profile summary and one curated GitHub achievement;
- a concise, structured About panel with a generated rolling-year summary;
- the real rolling-year contribution calendar with derived pace metrics; and
- a sanitized event timeline covering the current month and previous eleven
  calendar months, with the latest six events visible.

## Factual GitHub snapshot

The daily maintenance workflow uses only official public GitHub sources:

- the rolling-year contribution fragment for exact daily calendar cells;
- the paginated public Overview contribution fragments for timeline events.

The updater follows and validates GitHub's month pagination, accepts only known
contribution event summaries, and reconciles every month's event counts against
the contribution calendar before changing the page. It converts GitHub's
restricted aggregate source entry to the neutral label “N contributions.”

Repository names and URLs may be read transiently from a source fragment but
are discarded before the sanitized event model is created. Raw responses,
commit messages, social links, email addresses, repository names, and
private-project details are never persisted.

The Arctic Code Vault Contributor badge is a curated local copy of GitHub's
original 296×296 PNG. It is not refreshed by the updater and is not hotlinked.
Its SHA-256 is
`A808F9CD62C9D699C2274F0D4615D1AFBDE3A4051CBB5BEAA20DF2E6F38AC038`.

Run the tests and a validation-only live refresh locally with:

```powershell
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
configuration. Validate the updater, privacy boundary, local assets, generated
markup, contrast, and complete diff before commit-related work. Staging,
committing, pushing, and Pages-setting changes require explicit approval.
