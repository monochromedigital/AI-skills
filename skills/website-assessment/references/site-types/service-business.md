# Service businesses

Local services, trades, clinics, law and accountancy firms, agencies,
consultancies, restaurants with bookings — anywhere the site sells work
performed by people.

**Conversion here** is a qualified enquiry: a call, a form, a booking, a
WhatsApp message, a direction lookup. Most of these are invisible to
analytics, so the audit argues from friction, not from funnel data.

This is the type the base skill was implicitly written for, so much of
`categories.md` already fits. What follows is what it still misses.

## What must be captured

1. Homepage
2. **Two service pages** — the highest-value service and one of the others
3. Contact page, with the form visible
4. The booking flow, if one exists, to the confirmation step
5. About / team page
6. A location page, if the business serves multiple areas
7. Pricing page or the place where pricing is avoided
8. Homepage and one service page at 390×844 mobile
9. The Google Business Profile as it appears in search — for most local
   service businesses this is the real homepage

## The enquiry path

Everything on a service site is instrumental to one moment: the visitor
decides to make contact. Audit the whole path.

- Phone number in the header, tappable on mobile, and not an image
- Opening hours and current open/closed state where urgency exists
- Response-time expectation stated ("we reply within one working day")
- More than one contact route — some visitors will not use a form, others
  will not call
- The form asks for what is needed to reply, and nothing else. Every extra
  field is a percentage of enquiries
- No required field the visitor cannot answer yet (budget, exact service,
  preferred date before they know availability)
- Confirmation after submitting says what happens next and by when. A page
  reload with a green tick is the minimum; silence is a lost enquiry
- WhatsApp / messaging where the market uses it
- Map and directions accurate, with parking or access notes for a physical
  location

## Service pages

- One page per service, not one page listing all services. The service page
  is the landing page for the search that matters
- Each page states: what it is, who it is for, what it costs or how cost is
  determined, what happens first, how long it takes
- Price transparency — a range, a starting-from, or an honest explanation of
  why it varies. Silence on price is the most common reason a visitor leaves
  a service site, and "call for a quote" is not an answer
- Proof specific to *that* service: a case, a photo, a named testimonial
- The CTA on a service page is the enquiry for that service, carried through
  to the form so the visitor does not restate it

## Trust — the deciding factor

Service buyers are choosing a person, not a product. Trust findings on this
type are CRO findings, not decoration.

- Real photographs of real people and real work; stock imagery of a generic
  office actively costs credibility
- Named team members with credentials relevant to the service
- Licences, registrations, insurance, professional body membership
- Testimonials attributed to a real person and situation, not "J.S., happy client"
- Reviews visible on the site *and* consistent with the Google profile
- Physical address and registration details, not just a form
- Case studies with a before and an outcome

## Type-specific notes per category

**Copy / Content** — the homepage headline names the service and the place
("Family dentistry in Achrafieh"), not a feeling. Service names match what
customers search for, not internal or industry terminology.

**UX Design** — the top three tasks are almost always: understand a service,
work out cost, make contact. Anything that adds a click to those is a finding.

**Development** — click-to-call, click-to-map, and click-to-WhatsApp should be
native links; a JavaScript handler that fails silently on mobile is Critical.

**SEO** — local is the whole game: `LocalBusiness` structured data with
address, hours, and geo; NAP consistent between site, Google Business Profile,
and directories; a real page per service *and* per location, not one page with
40 towns listed. Check the Google Business Profile is claimed and complete.

**Accessibility** — booking widgets and third-party scheduling embeds are the
usual failure, and they are usually excluded from the client's own testing
because they are someone else's product. Audit them anyway; the visitor cannot
tell the difference. Forms need real labels; phone fields need `tel` input types.

**CRO** — the single most common finding on this type is that the contact
route is present but not *continuously* present. A visitor who decides to
enquire on a service page should not have to navigate to do it.

## Severity calls specific to service businesses

Treat as **Critical**:

- Phone number not tappable on mobile
- Enquiry form with no confirmation state
- A form field that blocks submission and cannot be honestly answered
- Opening hours absent or contradicted between site and Google profile
- A CTA for a service the business does not offer, or a booking link that 404s
- Address wrong or inconsistent with the map pin

## Benchmarks to look up live

- Form-field count vs completion rate — the standard finding needs a number
  behind it
- Local pack / local SEO ranking factor summaries for the current year
- Average response-time expectations in the client's sector
- The three competitors the client names: capture their service pages and
  compare price transparency and proof directly. On this type, competitor
  comparison is more persuasive than any global benchmark
