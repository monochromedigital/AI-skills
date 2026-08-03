# Nonprofits, charities, schools, and universities

**Conversion here** is a donation, a volunteer signup, an enrolment, an
application, or a service accessed. Two audiences usually share one site and
pull in opposite directions: the people who fund the organisation and the
people it exists to serve. Naming that tension is often the most valuable
structural finding in the deck.

Framing matters more on this type than any other. These organisations are
under-resourced by design, and an audit that reads as a pile-on will not be
acted on. State the constraint honestly and prioritise ruthlessly.

## What must be captured

1. Homepage
2. **The donation flow**, every step to the payment screen — or for education,
   the application/enquiry flow
3. A programme, service, or course page
4. About / impact / annual report page
5. Get involved / volunteer page
6. Contact page
7. For education: admissions, fees, term dates, and prospectus request
8. For charities: the page a service user would need, if the organisation
   delivers direct services
9. Donation flow at 390×844 mobile — most donation traffic is mobile

## The donation flow

Audit this the way you would audit an ecommerce checkout, because it is one.

- Donate is reachable from every page, in the header, in one click
- Suggested amounts anchored sensibly, with the middle option framed as
  typical. Amounts tied to concrete outcomes ("£25 buys a week of meals")
  outperform bare numbers — cite Anchoring where it applies
- Monthly is offered alongside one-off, and the recurring option is not the
  pre-selected default without disclosure
- Field count minimal. Address is needed only where tax relief requires it,
  and that should be explained at the point of asking
- Gift aid or local tax-relief mechanism explained in one sentence, not a
  paragraph of tax law
- Payment methods appropriate to the donor base, including wallets — mobile
  donors abandon card forms at high rates
- Processing fees disclosed honestly; the "cover the fee" option, if present,
  is opt-in not pre-ticked
- Confirmation states where the money goes and what happens next
- The flow does not leave the site's design mid-way. A third-party payment
  page with a different identity breaks trust at the worst moment

## Trust and accountability

Donors and parents are both making a high-trust decision with no product to
inspect.

- Charity registration number, legal status, and regulator visible
- Financial transparency: annual report, and a plain statement of where money
  goes. A percentage is more persuasive than a PDF
- Impact stated with evidence and dates, not perpetual aspiration
- Real photographs, consented and dignified — this is an ethical finding as
  well as a design one. Flag imagery that depicts beneficiaries without agency
- Named leadership and governance
- For schools: inspection reports, results, and safeguarding policy findable

## Education specifics

- The applicant journey is time-bound: deadlines, term dates, and open days
  are the top tasks in season and must be current
- Fees stated, with the full picture — tuition plus what else
- Prospectus obtainable without a form that asks for more than an address
- Course pages state entry requirements, duration, cost, and what the student
  ends up able to do
- Parent and student are different audiences with different questions; check
  both are served
- Current students and prospective students need separate routes — the portal
  link buried under a marketing site is a daily friction for thousands

## Type-specific notes per category

**Copy / Content** — beneficiary-facing content must be written at a genuinely
accessible reading level, and often in more than one language. Check the gap
between fundraising language and service-user language; if the site only
speaks to donors, that is the finding.

**UX Design** — the two-audience problem. Map the donor path and the
service-user path separately and check neither is buried under the other.

**Development** — these sites are frequently volunteer-built and accreted over
years. Be specific about what is worth fixing versus what needs replacing, and
say which is which — an underfunded team needs sequencing more than a list.

**SEO** — `NonprofitType` / `EducationalOrganization` structured data,
`Course` markup for education, `Event` for open days and fundraisers. Google
Ad Grants eligibility depends on site quality for eligible charities and is
worth flagging as a concrete consequence.

**Accessibility** — the audience is disproportionately likely to include
disabled users, and for public-funded education a statutory duty usually
applies. Frame WCAG failures as exclusion from the service, which on this type
is the organisation's own mission failing. Check the donation form specifically:
it is often a third-party embed nobody has tested.

**CRO** — donation and enrolment are the conversions. The most common finding
is that the site explains the cause thoroughly and then makes giving hard.

## Severity calls specific to this type

Treat as **Critical**:

- Any step of the donation flow that fails or loses data
- Recurring donation pre-selected without clear disclosure
- Fee-cover option pre-ticked
- Charity registration or regulator details absent
- Deadlines, term dates, or fees out of date in season
- Donation form inaccessible by keyboard or screen reader
- Safeguarding or service-user emergency information hard to find

## Benchmarks to look up live

- Current donation-page conversion and mobile abandonment benchmarks for the
  sector
- One-off vs recurring conversion rates, and average gift by channel
- The regulator's guidance for the client's jurisdiction (registration display
  requirements, fundraising codes)
- For education: the statutory publication requirements schools in that
  jurisdiction must meet on their website — these are specific, checkable, and
  frequently unmet, which makes them high-value findings
- Two peer organisations of similar size: compare donation flows step for step
