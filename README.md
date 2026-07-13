# mahmadnet.github.io

This is the public GitHub Pages user-site repository for the
[`mahmadnet`](https://github.com/mahmadnet) GitHub account. Its primary purpose is
to reserve and serve the standard user-site namespace so approved project sites
can be published at `https://mahmadnet.github.io/<repository>/`.

## Portfolio relationship

The full portfolio is maintained separately in the private
`mahmadnet/mahmadnet-website` repository and is published at its canonical URL,
`https://www.mahmad.net`.

This repository does not contain a copy of the portfolio and must not claim,
redirect to, or configure the `www.mahmad.net` custom domain. In particular, it
must not contain a `CNAME` file.

## Repository and deployment

- Local path: `D:\Workspace\Development\GitHub\mahmadnet.github.io`
- GitHub repository: `https://github.com/mahmadnet/mahmadnet.github.io`
- Production URL: `https://mahmadnet.github.io/`
- Default branch: `main`
- GitHub Pages source: the repository root (`/`) on `main`
- Build process: none; GitHub Pages publishes the static files directly

No deployment workflow is required while direct branch publishing remains
available and correctly configured.

## Current status

The landing page is intentionally deferred pending a separate design and
implementation approval. `index.html` and `styles.css` are deliberately empty,
so the root website is expected to remain blank and non-functional for now.

## Development policy

Future work should remain a lightweight, semantic, accessible static page. Do
not introduce a package manager, framework, bundler, build step, JavaScript,
analytics, tracking, cookies, external fonts, third-party assets, duplicated
portfolio content, automatic redirects, or unapproved project links without
explicit approval.

Before implementation, inspect the repository and live Pages configuration.
After changes, validate the structure and content, confirm the domain boundary,
run `git diff --check`, and review the complete diff. Staging, committing,
pushing, and changes to GitHub Pages settings require explicit approval.
