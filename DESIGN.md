# Profile overview design system

This document defines the internal visual and information standard for the
`mahmadnet.github.io` public profile overview. The page borrows GitHub's useful
information density and contribution concepts without reproducing GitHub's
application chrome.

## Information hierarchy

The masthead identifies the page as Muhammad Ahmad's public GitHub overview.
The desktop layout uses a compact identity sidebar and a wider factual content
column:

1. Profile identity, primary GitHub action, Pro status, and achievements.
2. About: the approved builder statement and stable public-account facts.
3. Current public build: the single allowlisted featured repository.
4. Contribution map: the rolling-year calendar and derived pace metrics.
5. Activity overview: twelve comparable calendar months, with three visible
   and nine disclosed through native `details`/`summary` markup.

Descriptive topics, strengths, and generic capability cards are intentionally
excluded so that the sidebar and main column do not repeat each other.

## Foundations

### Color roles

The palette is a personal silver-sage interpretation of a GitHub-like neutral
interface. Components consume semantic variables rather than literal colors.

| Role | Light | Dark | Use |
| --- | --- | --- | --- |
| Canvas | `#f7f9f8` | `#0e1311` | Page background |
| Surface | `#ffffff` | `#141a17` | Primary panels |
| Subtle surface | `#eef2f0` | `#1a221e` | Supporting UI |
| Border | `#cbd4d0` | `#34413b` | Panel and control edges |
| Text | `#202623` | `#e7ece9` | Primary copy |
| Muted text | `#66716c` | `#9ba8a2` | Supporting metadata |
| Accent | `#496b60` | `#91b3a7` | Links, actions, focus, selected data |
| Accent soft | `#e4ece8` | `#1d2c27` | Notes and highlighted surfaces |

Contribution levels use five ordered values, `--c0` through `--c4`, from an
inactive silver-gray to the strongest sage. Color is supplemented by accessible
text, titles, totals, and metric labels; it is never the only carrier of meaning.

### Typography

The system font stack keeps the page native and asset-free. Type roles are
12px, 14px, 16px, 20px, 24px, and 32px. Body copy uses 16px/1.5; supporting
metadata uses 12px or 14px; section headings use 20px or 24px. Weight and size,
not ornamental styling, establish hierarchy.

### Spacing and shape

Spacing follows a 4px scale (`--space-1` through `--space-12`). Panels use
8–10px radii, one-pixel borders, restrained shadow, and compact padding. The
content width is 74rem, the sidebar is 15rem, and layout gaps remain large
enough to separate concepts without reducing information density.

## Components

### Masthead

A CSS monogram, handle, and quiet page label form a slim personal masthead.
There are no fake menus, search controls, tabs, or GitHub logo assets.

### Profile sidebar

The approved local portrait anchors the identity block. The action is visually
primary but has one public destination: the GitHub profile. Achievement
medallions are CSS-only, use short decorative initials with adjacent readable
names, and safely accommodate future achievement names.

### Repository card

Only `mahmadnet.github.io` may be rendered by name or linked. The card presents
its public description, primary language, update date, and its place within the
public-repository total. No general repository feed is created.

### Contribution map

The map reproduces factual daily counts from the official rolling-year
contribution fragment. It includes month and weekday labels, an intensity
legend, last-updated metadata, and these derived values:

- active contribution days;
- longest consecutive-day streak;
- busiest day;
- busiest month; and
- average contributions per active day.

The calendar may scroll horizontally inside its panel; the document itself must
not create horizontal overflow.

### Activity overview

Each of the current month and previous eleven calendar months uses the same six
rows: commits, pull requests, reviews, issues, repositories created, and private
contributions. Zero values remain visible in a subdued state for direct
comparison. Restricted contributions are an aggregate only and never reveal
names or details.

## Responsive behavior

Above 48rem the page uses a two-column profile layout and a sticky sidebar. At
48rem and below the profile becomes a compact horizontal identity followed by
the main content. At 36rem and below panels tighten, metrics reduce columns,
and controls remain full-width where useful. The contribution calendar retains
its intrinsic width and scrolls within its labeled region.

## Accessibility and interaction

- HTML follows one `h1` with ordered section headings.
- Every interactive element has a visible silver-sage focus ring.
- Links are distinguishable without relying only on color.
- The activity expansion uses keyboard-accessible native disclosure markup.
- The avatar has descriptive alternative text; decorative marks are hidden.
- Light and dark foreground/background combinations meet WCAG AA for normal
  text.
- Motion is minimal and disabled under `prefers-reduced-motion: reduce`.
- Automatic dark mode follows `prefers-color-scheme` and preserves semantic
  token roles.

## Data and privacy boundaries

Generated regions are replaced atomically by the standard-library updater.
Only official GitHub sources are accepted. Stored output is limited to public
profile facts, the approved featured repository, achievement names, calendar
cells, dates, and sanitized aggregates. Raw responses, commit messages, social
links, unapproved repository names, and private project details must never
enter the page or repository.
