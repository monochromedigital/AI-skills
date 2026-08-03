# Corporate, institutional, and government sites

Corporate groups, holding companies, manufacturers, embassies, ministries,
associations, and public bodies. Sites where nothing is sold and the visitor
is usually a journalist, a candidate, an investor, a partner, a regulator, or
a citizen who needs one specific fact.

**Conversion here** is task completion and reputation. Someone arrived to
*find something* or to *form a judgement*. The audit measures whether they
left with the fact and with the right impression.

Do not import CRO logic wholesale onto this type. "Add a sticky Book Now bar"
is a nonsense finding for a ministry. The CRO tag still applies, but it means
completed contact, completed application, completed download — the
institution's own conversion.

## What must be captured

1. Homepage
2. About / who we are
3. **The top task page** — for an embassy that is visas or consular services,
   for a manufacturer it is products or distributors, for a listed company it
   is investor relations
4. News / press room, including one article
5. Contact page
6. Careers, if present
7. Any form-bearing service page (application, request, registration)
8. A downloads or documents page, if the site distributes PDFs
9. Homepage and the top task page at 390×844 mobile
10. The alternate-language version of the homepage, if the site is multilingual

## The audience problem

Corporate sites fail by being organised around the organisation. The most
valuable finding on this type is usually structural: the site describes the
institution's internal divisions where the visitor thinks in tasks.

- Name the visitor groups the site actually serves, then check each has an
  obvious route from the homepage
- Navigation labels use the visitor's words. "Consular Section" is the org
  chart; "Apply for a visa" is the task
- The top three tasks are reachable in one click. On most institutional sites
  the top task is buried three levels deep under a departmental heading
- Announcements and news are not a substitute for a permanent page. A visa fee
  change published only as a news post is a content-governance failure
- Search exists and works, because on a large institutional site it is how
  most people navigate. Test it with a real question

## Information accuracy and governance

On this type, out-of-date content is not a minor issue — it is the reputational
risk the whole site exists to avoid.

- Every fee, requirement, deadline, hour, and holiday is current, dated, and
  stated once. The same fact appearing on three pages with two values is a
  Critical finding
- Documents dated and versioned; superseded PDFs removed, not left indexed
- News items dated; a press room whose latest item is two years old actively
  signals abandonment
- Contact details for each department current and monitored
- Emergency or urgent-notice mechanism exists and is not hard-coded

## Type-specific notes per category

**Copy / Content** — plain language is the standard, especially for public
bodies where a legal duty may apply. Check reading level against the actual
audience, not against the drafter's comfort. Procedures written as numbered
steps, not as paragraphs of regulation. Requirements stated as a checklist the
visitor can act on.

**UX Design** — forms are the risk. Institutional forms are long, official,
and often unfinishable in one sitting; check whether progress can be saved,
whether required documents are listed *before* the form starts, and whether
errors are recoverable.

**UI Design** — brand consistency across sub-sites and departments. Large
institutions usually have three visual identities running simultaneously; the
finding is the inconsistency, not any one of them.

**Development** — PDF-first content delivery is the classic institutional
failure: information that should be a web page ships as a scanned PDF, which
is unsearchable, unresponsive, and inaccessible. Also check that content
requiring frequent change is CMS-managed rather than baked into templates.

**SEO** — `Organization` or `GovernmentOrganization` structured data;
FAQ markup on procedure pages. For multilingual sites, `hreflang` correctness
and — the failure that recurs everywhere — whether the translated page
actually exists rather than redirecting to the default language. Check `lang`
and `dir` are correct on every language version, including RTL.

**Accessibility** — this is where the type is most exposed. Public sector
bodies in many jurisdictions have a statutory accessibility duty; a WCAG 2.2
AA failure is a compliance finding, not a usability one, and should be framed
that way. Scanned PDFs with no text layer are the most common breach. Check
whether an accessibility statement exists — its absence is itself a finding
where the duty applies.

**CRO** — read as *task conversion*: can the citizen complete the application,
can the journalist find the press contact, can the candidate apply. Count the
steps and name the drop-off point.

## Severity calls specific to this type

Treat as **Critical**:

- Any published fee, requirement, deadline, or opening hour that is wrong or
  self-contradictory across pages
- A required service form that cannot be completed or submitted
- Scanned image-only PDFs carrying essential information
- A language version whose links resolve to the default language
- Missing accessibility statement where a statutory duty applies
- Emergency or safety information that is out of date

## Benchmarks and research to look up live

- The accessibility legislation in force for the client's jurisdiction and
  sector, and the standard it references — cite the instrument by name
- Plain-language or web standards published by the relevant government body
- Two or three peer institutions of comparable size and mandate — for embassies
  and ministries this is far more persuasive than any commercial benchmark.
  Capture how a peer handles the same top task and put it side by side
