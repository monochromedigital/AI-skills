# Categories, severity, and what to look for

This file is the floor — the checks that hold for every website. It is not the
whole audit. Read it first, then read the one file in `site-types/` that
matches the site you are auditing; that file adds the checks a generic
checklist cannot know about, and defines what conversion means here.

Seven categories. Every finding carries at least one; two or three is common
(a weak CTA is often `UX Design` + `CRO`, a red-on-green active state is
`UI Design` + `Accessibility`). Never tag more than three — the pill row stops
scanning cleanly.

| Tag | Colour | It answers |
|---|---|---|
| Copy / Content | `#1E8FD9` | Do the words do their job? |
| UX Design | `#DF6630` | Can people complete the task? |
| UI Design | `#5C8B63` | Does it look considered and consistent? |
| Development | `#866FBC` | Is it built to be maintained and to perform? |
| SEO | `#D7586C` | Can it be found and understood by search? |
| Accessibility | `#7D797E` | Can everyone use it? |
| CRO | `#2E8F86` | Does it turn visitors into whatever this site exists to produce? |

## Choosing between adjacent tags

These four pairs cause most mis-tagging:

- **UX vs UI** — UX is *can they do the thing*; UI is *does it look right*. A
  button nobody can find is UX. A button that clashes with the palette is UI.
  A button that is both hard to find *and* ugly gets both tags.
- **UX vs CRO** — UX is task completion for any goal; CRO is specifically the
  site's own defining outcome — an order, a signup, an enquiry, a donation, a
  completed application. "The form has 14 fields" is UX. "The form asks for a
  phone number before the user knows the price" is CRO.
- **Copy vs SEO** — Copy is whether a human understands it. SEO is whether a
  crawler does. A vague H1 is usually both.
- **Development vs UI** — if a designer could fix it in Figma it is UI. If it
  needs a code or CMS change — hard-coded content, no component reuse, layout
  breaking at a breakpoint — it is Development.

## Copy / Content

- Headline states what the organisation does, not what it feels about itself
- Value proposition visible without scrolling
- Reading level suits the actual audience; jargon defined or removed
- CTA labels describe the outcome ("Book an appointment"), not the mechanism ("Submit")
- No promises the site cannot keep (a CTA to a service that does not exist)
- Consistent terminology — the same service is not called three different things
- Dates, fees, hours, requirements are current and stated once, authoritatively
- Error and empty states are written, not left to the browser default
- Content that changes (news, hours, holidays) is not hard-coded into a page

## UX Design

- Navigation labels match the user's words, not the org chart
- The top 3 user tasks are reachable in one click from the homepage
- Page order follows the decision the user is making, not the internal hierarchy
- Forms ask only what is needed at that step; long forms are broken into steps
- Feedback after every action — loading, success, failure
- Search exists where the content volume needs it, and returns useful results
- Back/breadcrumb behaviour is predictable; no dead ends
- Mobile: thumb-reachable primary actions, no horizontal scroll, tap targets ≥44px
- Redundant controls removed (a Home link when the logo already goes home)

## UI Design

- One type scale, applied consistently; no more than 2 families
- Spacing follows a system; sections are not arbitrarily different heights
- Visual hierarchy makes the primary action the most prominent thing on screen
- Colour is used with intent — one accent, not five competing ones
- Imagery is consistent in treatment, crop, and quality
- Components look the same everywhere they appear
- Density is even; no page is dramatically heavier than its neighbours
- Icons carry labels unless universally understood

## Development

- Responsive across breakpoints, not just at the three common widths
- Images sized and formatted for their display size; modern formats used
- Page weight and request count reasonable; no single blocking megabyte
- Content that should be CMS-managed is not hard-coded in templates
- Components reused rather than duplicated per page
- No console errors, no broken links, no mixed content
- Third-party scripts justified — each one costs load time
- Caching, compression, and lazy loading in place

## SEO

- One H1 per page, describing the page; heading levels do not skip
- Title tag 50–60 chars, unique per page, front-loaded with the topic
- Meta description 140–160 chars, written to earn a click
- URLs readable and stable
- Canonical set; no accidental noindex
- Internal links use descriptive anchor text, not "click here"
- Structured data where it applies (Organization, LocalBusiness, FAQ, Event)
- Images have descriptive alt text and sensible filenames
- `lang` (and `dir` for Arabic/Hebrew) set correctly, including on alternate versions
- Multilingual: hreflang correct, and the translated page actually exists

## Accessibility

Anchor to WCAG 2.2 AA. Cite the ratio and the threshold — the number is what
makes the finding undeniable.

- Text contrast ≥4.5:1 (≥3:1 for text ≥24px, or ≥18.66px bold)
- Non-text contrast ≥3:1 for interactive boundaries and meaningful graphics
- Colour is never the only carrier of meaning — check red/green pairs
  specifically, since deuteranopia and protanopia are the most common forms
- Every interactive element reachable and operable by keyboard
- Visible focus indicator that is not suppressed by a CSS reset
- Form fields have real labels, not placeholder-only
- Images have alt text; decorative images have `alt=""`
- Landmarks present (`header`, `nav`, `main`, `footer`); one `main`
- Tap targets ≥24×24 CSS px minimum, 44×44 recommended
- Motion respects `prefers-reduced-motion`
- Language attribute set so screen readers pronounce correctly

## CRO

**Define the conversion before writing a single CRO finding.** It is not
always an enquiry. Order, trial signup, demo booked, enquiry, donation,
application, subscription, booking, listing created, task completed — the
site-type file states which one applies. A CRO finding that optimises for the
wrong outcome is worse than no finding, and a client spots it immediately.

These hold whatever the conversion is:

- One primary action per screen; competing CTAs de-emphasised
- The route to the conversion is visible at all times, not buried in a footer
- Trust signals near the point of decision — credentials, testimonials, real
  photos, verification, financial transparency, whatever this audience needs
  in order to commit
- Friction removed before the commitment point; ask for the sensitive detail
  later. Nothing is requested before the visitor knows what they are getting
- Cost — money, time, or data — is disclosed before the visitor invests effort,
  never at the last step
- Objections answered on the page where they arise, not on a separate FAQ
- Proof of what happens next, and when, wherever the visitor must wait
- Exit points minimised on conversion pages
- The path from "interested" to "committed" is countable and short — count it,
  and put the number in the finding

Then read the site-type file for the conversion path that actually matters
here, and audit that path step by step.

## Severity

| Level | Test | Use for |
|---|---|---|
| **Critical** | Blocks a user from completing a core task, excludes a group of users, or actively loses enquiries | WCAG failures that exclude people, broken flows, dead CTAs, content that is wrong |
| **Moderate** | Measurably degrades the experience but has a workaround | Weak hierarchy, dense pages, slow loads, unclear labels |
| **Minor** | Polish; worth doing but nothing breaks | Redundant links, inconsistent spacing, small copy improvements |

Be disciplined. If everything is Critical, the client fixes nothing. A healthy
audit is roughly 10–20% Critical, 50% Moderate, the rest Minor.

## Psychology principles

Cite a principle only when it genuinely explains the finding — one per finding
at most, and on maybe a third of findings overall. A cited principle should
make the client think "ah, that's *why*". Read the `psychology-of-design` skill
for the full catalogue; the ones that recur in website audits are:

| Finding pattern | Principle |
|---|---|
| Too many nav items, too many options, long dropdowns | Hick's Law |
| Dense page, everything the same weight | Cognitive Load |
| Primary action not obvious | Visual Hierarchy, Fitts's Law |
| CTA ignored because it looks like an ad | Banner Blindness |
| No testimonials or credentials near the decision | Social Proof |
| Pricing presented without a reference point | Anchoring Bias |
| Long form abandoned | Progressive Disclosure, Cognitive Load |
| User does not know what happens next | External Trigger, Feedback |
| Everything shouts, so nothing stands out | Von Restorff Effect |

Do not manufacture urgency or fake scarcity as a recommendation. If a client
asks for it, offer the honest alternative that achieves the same goal.
