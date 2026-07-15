# Profile overview design system

This document defines the visual and information standard for Ahmad's public
`mahmadnet.github.io` profile. The page keeps GitHub's useful profile,
contribution, achievement, and activity concepts while using a
quieter personal presentation.

## Design principles

- Prefer factual content, direct labels, and clear hierarchy over decorative UI.
- Keep the light canvas true white; use neutral gray structure and silver-sage
  only for actions, links, focus, achievements, and contribution data.
- Use consistent section headings and flat bordered panels where containment
  clarifies the content.
- Avoid gradients, glows, floating cards, oversized radii, pill-heavy metadata,
  decorative eyebrow labels, and hover movement.
- Use the system font stack and standard 400, 500, and 600 weights.

## Information hierarchy

The 56px masthead contains a linked 32px MA logo and `@mahmadnet` identity on
the left, with a native menu for the real About, Contributions, and Activity
anchors on the right.
The desktop body uses a 14rem identity sidebar and a flexible factual content
column within a 72rem container:

1. Ahmad's profile identity, primary GitHub action, and one curated achievement.
2. About: a standard section with a concise introductory panel.
3. Contribution map: rolling-year cells and derived pace metrics.
4. Activity overview: sanitized events across twelve calendar months.

The footer uses the static convention `© 2026 Ahmad`, with the year represented
by a semantic `time` element.

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

- The supplied MA logo is a cleaned local SVG derivative. It retains the
  original 1300×1300 geometry and uses theme-aware neutral fields, borders,
  and silver-sage symbols.
- The logo and username form one internal home link with a clear accessible
  name. Masthead navigation uses a native `details` disclosure, compact text
  anchors, sage hover/focus treatment, and no simulated routes.
- About uses the same section heading and flat panel pattern as adjacent content.
  Its third element is one generated sentence summarizing rolling contributions,
  active days, and the longest streak.
- The primary action is the strongest sage surface; ordinary metadata remains
  neutral.
- Contribution insights form one compact definition row separated by rules,
  not individual dashboard cards.
- Activity is an open vertical timeline. Month labels are quiet chronological
  separators, while each event is one comparable factual sentence with an
  optional date or range.
- Exactly six activity events are initially visible. Earlier events use one
  separated native `details` control labeled “See more activity.” When open,
  the control follows the revealed events and reads “See less activity”; it is
  omitted when unnecessary.
- The achievement area is singular and static. It displays GitHub's original
  Arctic Code Vault Contributor PNG at 56×56 with adjacent readable text.

## Data and privacy semantics

The contribution map is a rolling-year analytical view. Activity uses the
current month plus the previous eleven calendar months and follows GitHub's
public Overview pagination. Supported summaries are commits across a repository
count, repositories created, pull requests opened or reviewed, issues opened,
and aggregate contributions.

Only event type, count, repository count where needed for grammar, month, and an
optional date label enter the sanitized model. Repository names, URLs, source
HTML, commit messages, and public/private wording never enter rendered activity.
Unknown events, invalid pagination, incomplete history, or a mismatch with the
calendar fail before `index.html` is modified.

## Responsive behavior

Above 48rem the page uses two columns and a sticky sidebar. At 48rem and below,
the identity becomes a compact horizontal block followed by the action,
achievement, and main content. The masthead menu is used at every viewport;
its right-aligned dropdown is constrained to the available viewport width.
At 36rem and below, panels tighten and event dates stack under their summaries.
The contribution calendar keeps its intrinsic width and scrolls within its
labeled region; the document must not create horizontal overflow.

## Accessibility

- Use one `h1`, ordered section headings, descriptive image alternatives, and
  native disclosure semantics.
- Keep a visible three-pixel focus ring and WCAG AA text contrast in both themes.
- Never rely on color alone for contribution meaning; retain titles, labels,
  totals, and the intensity legend.
- Respect `prefers-reduced-motion`; motion is limited to color transitions.
