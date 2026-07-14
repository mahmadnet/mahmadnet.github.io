# Profile page design system

This is the internal visual standard for the `mahmadnet.github.io` profile home.
It follows GitHub's information density without reproducing inert controls.

## Foundations

- **Typography:** system sans-serif; 12px metadata, 14px UI, 16px body, 20px
  emphasis, 24px profile headings, and 32px reserved display text.
- **Spacing:** a 4px base scale exposed as `--space-*` tokens.
- **Geometry:** 6px radii, 1px borders, 32px controls, a 56px header, a 76rem
  content width, and a 16rem desktop sidebar.
- **Color:** white/subtle-gray canvases, near-black text, GitHub-blue links and
  focus, gray secondary actions, GitHub-green contribution/success states, and
  salmon reserved for a future selected tab. Dark mode preserves these roles.

## Components

- The profile sidebar contains identity and short factual modules separated by
  muted borders. Tags are metadata, not controls.
- Panels use restrained padding. The About panel alone uses a subtle header.
- Work cards form two columns on desktop and one column on small screens.
- The real contribution calendar keeps five semantic intensity levels and
  scrolls horizontally instead of shrinking below a readable cell size.
- The timeline contains real monthly totals and sanitized public-event
  aggregates. It never exposes repository names, commit messages, or URLs.
- Neutral actions use gray; green is reserved for real primary/success roles.

## Responsive and accessibility rules

The layout stacks below 48rem and work cards stack below 36rem. Preserve one
`h1`, ordered section headings, visible keyboard focus, meaningful local image
alternatives, AA text contrast, reduced-motion support, and no page-level mobile
overflow.
