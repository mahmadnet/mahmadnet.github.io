# mahmadnet.github.io

This repository publishes Muhammad Ahmad's lightweight public profile home at
`https://mahmadnet.github.io/`. It also reserves the standard GitHub Pages user
namespace for approved project sites.

## Page implementation

The root page uses semantic HTML and responsive CSS with no client-side
JavaScript, package manager, framework, bundler, analytics, tracking, cookies,
external fonts, or third-party page assets. The approved portrait is stored
locally at `assets/avatar.jpg`. Visual conventions are documented in
[`DESIGN.md`](DESIGN.md).

## Public activity snapshot

A scheduled maintenance workflow reads only official public GitHub endpoints
and updates marked regions of `index.html` with rolling-year contribution data
and aggregate recent public activity. Repository names, commit messages, project
links, and source responses are not written to the page or retained. The public
Events API is recent and bounded, so the timeline is a summary rather than a
complete history.

Validate live data without writing the page with:

```powershell
python scripts/update_profile.py --dry-run
```

## Publishing

- Repository: `https://github.com/mahmadnet/mahmadnet.github.io`
- Production: `https://mahmadnet.github.io/`
- Default branch: `main`
- GitHub Pages source: repository root (`/`) on `main`

Pages publishes the static root files directly. The activity workflow maintains
page data only; it does not deploy the site or change Pages settings.

## Development policy

Keep the repository focused on this user-site page and its documentation. Do
not add a custom domain, redirects, copied portfolio content, unapproved project
links, client-side JavaScript, external page assets, or unrelated deployment
configuration. Staging, committing, pushing, and Pages-setting changes require
explicit approval.
