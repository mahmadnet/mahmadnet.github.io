# Profile overview design system

This document defines the visual and information standard for the public
`mahmadnet.github.io` profile. The page keeps GitHub's useful profile,
repository, contribution, and activity concepts while using a quieter personal
presentation.

## Design principles

- Prefer factual content, direct labels, and clear hierarchy over decorative UI.
- Keep the light canvas true white; use neutral gray structure and silver-sage
  only for actions, links, focus, achievements, and contribution data.
- Use open sections and separators before adding panels. Reserve borders for
  repository, calendar, and activity structures that benefit from containment.
- Avoid gradients, glows, floating cards, oversized radii, pill-heavy metadata,
  decorative eyebrow labels, and hover movement.
- Use the system font stack and standard 400, 500, and 600 weights.

## Information hierarchy

The 56px masthead contains a restrained 28px monogram, `@mahmadnet`, and the
quiet “Public GitHub overview” label. The desktop body uses a 14rem identity
sidebar and a flexible factual content column within a 72rem container:

1. Profile identity, primary GitHub action, and one curated achievement.
2. About statement and stable public-account facts.
3. Current public build: the single allowlisted featured repository.
4. Contribution map: rolling-year cells and derived pace metrics.
5. Activity overview: twelve comparable months, with three visible and nine in
   native `details`/`summary` markup.

## Color system

### Light

| Role | Value |
| --- | --- |
| Canvas and primary surface | `#ffffff` |
| Subtle surface | `#f6f8fa` |
| Primary text | `#1f2328` |
| Muted text | `#59636e` |
| Border / quiet border | `#d0d7de` / `#e6e9ec` |
| Accent / hover | `#365f53` / `#294a41` |
| Accent-soft surface | `#edf4f1` |
| Contribution levels | `#eff2f1`, `#bac9c4`, `#809b92`, `#52796d`, `#2f574b` |

### Dark

| Role | Value |
| --- | --- |
| Canvas | `#0d1117` |
| Surface / subtle surface | `#151b23` / `#1f2630` |
| Primary text | `#f0f3f6` |
| Muted text | `#9198a1` |
| Border / quiet border | `#3d444d` / `#2b3139` |
| Accent / hover | `#9abdad` / `#b0cec2` |
| Accent-soft surface | `#1d2d28` |
| Contribution levels | `#1c2421`, `#2e4940`, `#4c6f64`, `#6f9588`, `#9abdad` |

Automatic dark mode follows `prefers-color-scheme`. Semantic variables retain
the same meaning in both themes.

## Typography, spacing, and shape

The system font stack is `-apple-system`, BlinkMacSystemFont, Segoe UI,
Helvetica, Arial, sans-serif. Type roles are 12px, 14px, 16px, 20px, 24px, and
32px, with restrained tracking and 1.2–1.5 line heights. Spacing follows a 4px
scale. Controls and panels use 6–8px radii, one-pixel borders, and no panel
shadows.

## Component conventions

- The monogram is an outlined typographic mark, not a logo asset or decorative
  badge.
- The About section is open content with a quiet bottom separator.
- The primary action is the strongest sage surface; ordinary metadata remains
  neutral.
- The repository card uses one flat border, a rectangular count label, and a
  restrained metadata footer.
- Contribution insights form one compact definition row separated by rules,
  not individual dashboard cards.
- Activity months retain identical metric rows and subdued zero values for
  direct comparison.
- The achievement area is singular and static. It displays GitHub's original
  Arctic Code Vault Contributor PNG at 56×56 with adjacent readable text. The
  asset is local, unchanged, and never replaced by CSS initials.

## Responsive behavior

Above 48rem the page uses two columns and a sticky sidebar. At 48rem and below,
the identity becomes a compact horizontal block followed by the action,
achievement, and main content. At 36rem and below, contained data panels tighten
without adding padding to the open About section. The contribution calendar
keeps its intrinsic width and scrolls within its labeled region; the document
must not create horizontal overflow.

## Accessibility and privacy

- Use one `h1`, ordered section headings, descriptive image alternatives, and
  native disclosure semantics.
- Keep a visible three-pixel focus ring and WCAG AA text contrast in both themes.
- Never rely on color alone for contribution meaning; retain titles, labels,
  totals, and the intensity legend.
- Respect `prefers-reduced-motion`; motion is limited to color transitions.
- Generated regions are replaced atomically using official GitHub sources.
- Stored generated output is limited to approved public facts, the featured
  repository, calendar cells, dates, and sanitized aggregates. Raw responses,
  commit messages, social links, unapproved repository names, and private
  project details must never enter the page or repository.
