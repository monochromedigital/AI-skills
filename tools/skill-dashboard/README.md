# Skills dashboard

A local page that lists every skill on this Mac, counts how often each one is
used across all Claude Code sessions (and in which projects and sessions),
groups skills (SEO, Front-end, Marketing, ...), shows the most recently added
ones, flags skills and plugins with a newer version, and shows every MCP
server's connection status. From the page you can update, uninstall or install
skills one at a time or in bulk, move them between groups, check all MCP
servers and sign in to one again.

```bash
python3 tools/skill-dashboard/server.py
```

Then open http://127.0.0.1:4477. Python 3 standard library only; nothing to install.

## What it counts

- **Uses**: every time the model calls a skill, plus every `/skill-name` you type.
  Read from Claude Code's session transcripts in `~/.claude/projects`, including
  subagents, desktop-app sessions and terminal sessions, in every project.
- **Not counted**: cloud sessions (claude.ai/code, `claude --cloud`) and
  claude.ai chats. They run on Anthropic's machines and leave no transcript here.

Claude Code deletes terminal transcripts after 30 days, so each use is copied
into `~/.claude/skill-usage/events.jsonl`, which nothing prunes. The copy
happens whenever the page loads, and at every session start once the hook
below is installed.

## Projects, sessions and groups

- **Projects**: the folder each session ran in. The Projects card lists them;
  click one to filter the table to the skills used there.
- **Sessions**: click a skill's name (or "View details" in its ⋯ menu) to see
  the projects it was used in and its recent sessions, named by the title you
  gave the session or the one Claude Code generated.
- **Groups**: every skill starts in a group from the rules in `config.json`
  (`groups`, first matching pattern wins). Move skills with ⋯ → Move to group,
  or select several and use Move to group in the bulk bar; "New group…" makes
  your own. Your choices are saved in `~/.claude/skill-usage/groups.json`, so
  new default rules never overwrite them.
- **Recently added**: the first date each skill was seen, seeded from its
  folder's creation date or its plugin's install date, kept in `seen.json`.

## Where each skill's updates come from

| Source | Folder | Update check |
|---|---|---|
| Plugin | `~/.claude/plugins` | Installed version vs the marketplace on GitHub (and the local copy) |
| Personal | `~/.claude/skills` | This repo's copy of the same skill, or a GitHub path listed in `updates.upstream` |
| claude.ai | `~/.claude/skills/synced` | Synced by Claude Code itself; compared with this repo only |
| This repo | `skills/` | Listed as "Not installed" when nothing installed shares its name |

To track a hand-installed skill against its GitHub source, add it to
`config.json`:

```json
"upstream": {
  "skill-name": { "repo": "owner/repo", "path": "skills/skill-name/SKILL.md" }
}
```

## Actions and what they do

| Button | Runs |
|---|---|
| Update (plugin) | `claude plugin marketplace update <marketplace>` then `claude plugin update <plugin>@<marketplace>` |
| Remove plugin | `claude plugin uninstall <plugin>@<marketplace>` (removes all of that plugin's skills) |
| Uninstall (personal skill) | Moves the folder to `~/.claude/skill-usage/trash`; Restore puts it back |
| Update from repo | Moves the installed copy to the trash, then copies `skills/<name>` in |
| Install | Copies `skills/<name>` into `~/.claude/skills` |
| Check all | `claude mcp list` (health-checks every server, takes a few seconds) |
| Sign in | `claude mcp login <server>` (opens your browser) |

Select rows with the checkboxes (or a whole group with its header checkbox)
to update, install, move or uninstall them together. A plugin can't lose a
single skill, so selected plugin skills become one update or removal per
plugin, and the confirmation names every plugin it would remove.

Skills synced from claude.ai can only be turned off on claude.ai, so they get a
link instead. Plugin changes take effect in new Claude Code sessions.

The server listens on 127.0.0.1 only, rejects other hostnames and origins, and
every action needs a token that only the dashboard page receives.

## Cost

The cost panels show what this Mac's Claude Code replies would cost at
Anthropic API list prices (`pricing` in `config.json`, dated). You pay a flat
plan fee, so read it as a way to compare projects and sessions, not a bill.
Claude.ai chats in the browser aren't stored on the Mac, so they never appear.

The **Period** menu at the top of the section switches between months (bars
per day) and All time (bars per month); the projects, sessions and cost
breakdown follow it. `plan.monthlyFee` in `config.json` (now $100) is what you
pay each month, so the heading can say how the API-price figure compares. The
"API cost, last 7 days" tile at the top of the page always shows the rolling
week.

`costLeaveOut` in `config.json` lists folders whose token cost is someone
else's: now `~/Desktop/Code/CRK` (Crackwits client work, which Crackwits pays
for). Replies from those folders and their subfolders are left out of every
cost figure, and their token rows are never uploaded to the online console.
Skill uses there still count everywhere else on the page. Add a folder to the
list to leave it out too.

## The online console: https://console.monochrome.digital

A read-only copy of the dashboard on Cloudflare (account "Monochrome"), built
from three parts in `cloud/`:

- **D1 database** `monochrome-console`: skill uses, token usage per reply,
  session titles, model prices (for the cost view) and the latest dashboard
  snapshot per Mac. Tables are in `cloud/migrations/`.
- **Worker** `monochrome-console` (`cloud/src/worker.js`) with two addresses:
  - `console.monochrome.digital` serves the page and its data. Data is only
    served to people Cloudflare Access has signed in; until Access is set up
    (the `ACCESS_*` vars in `wrangler.jsonc`), every data request is refused.
  - `monochrome-console.monochrome-digital.workers.dev` only accepts uploads
    (`POST /api/ingest/<kind>`) carrying the upload key. Nothing is readable there.
- **Cloudflare Access** in front of `console.monochrome.digital`. Sign-in is
  either your Cloudflare account or a one-time code emailed to you, but only
  addresses in the policy **Monochrome console - Johnny only** get in. To let a
  teammate in, add their email to that policy (Zero Trust → Access controls →
  Policies); the emailed code is how they sign in.

Day to day:
- `python3 tools/skill-dashboard/cloud_sync.py` sends new rows and a fresh
  snapshot; the Claude app's scheduled task **Monochrome console: daily sync**
  runs it every morning (or at the app's next launch). Re-sending is harmless:
  the database ignores rows it already has.
- `cd tools/skill-dashboard/cloud && npm run deploy` publishes page or Worker
  changes (it rebuilds `cloud/public` from `web/` first). `npm run migrate`
  applies new database migrations.
- The upload key is in `~/.claude/skill-usage/secrets.json` (owner-only) and
  set on the Worker as the `INGEST_TOKEN` secret. It is never in the repo.

### Database write limit

D1's free plan allows 100,000 written rows a day (reset at midnight UTC), and
each index on a table adds one more write per row. A normal day is a few
thousand. The risk is a Mac's first upload, which sends its whole history: if
it hits the limit, the sync stops with "exceeded D1's free tier daily row
write limit" and carries on from where it stopped the next day
(`cloud-state.json` records each batch sent). Session titles are only sent
when new or renamed, for the same reason.

`migrations/0002_fewer_token_indexes.sql` drops three indexes nothing reads.
Run `npm run migrate` in `cloud/` once if it hasn't been applied (it couldn't
be on 8 Nov because that day's limit was already used up).

### Add your other laptop

Each Mac uploads under its own id and name (`~/.claude/skill-usage/machine.json`,
created on the first sync). On the other Mac:

1. **Get the code.** Clone this repo (the dashboard lives on the
   `skill-dashboard` branch until it's merged), or copy the
   `tools/skill-dashboard` folder across. It needs only `python3` and Claude
   Code; `cloud/` and `npm` are only for deploying, which one Mac is enough for.
2. **Copy the upload key.** AirDrop `~/.claude/skill-usage/secrets.json` from
   this Mac into the same folder there, then lock it to your user:
   `chmod 600 ~/.claude/skill-usage/secrets.json`. Don't send it by email or chat.
3. **First sync.** `python3 tools/skill-dashboard/cloud_sync.py`. It reads that
   Mac's transcripts and uploads its history; a long history may take two days
   because of the write limit above.
4. **Daily sync.** In the Claude app there: Scheduled → New task, every day,
   with the prompt `cd "<repo>/tools/skill-dashboard" && python3 cloud_sync.py`.
5. **Optional:** the session-start hook below, so nothing is lost to the
   30-day transcript cleanup.

The console opens on the Mac that synced most recently. Once a second Mac has
uploaded a snapshot, a **Mac** picker appears in the header, listing each Mac
with its last sync; choosing one loads that Mac's snapshot. The list comes from
`/api/machines` (behind the same sign-in), and the page only reads it online,
so the local dashboard never shows the picker.

## Where the data lives

No database. Everything is plain files on this Mac in `~/.claude/skill-usage/`,
written by `ledger.py` from Claude Code's own transcripts:

| File | Holds |
|---|---|
| `events.jsonl` | One line per skill use: skill, time, project, session, how it was called |
| `tokens.jsonl` | One line per Claude reply: model, input/output/cache tokens, project, session (for the cost view) |
| `sessions.json` | Session titles (yours, else the generated one) |
| `seen.json` | The date each skill was first seen ("Recently added") |
| `groups.json` | Your own groups and group moves |
| `state.json` | How far each transcript has been read, so syncs only read new lines |
| `remote-cache.json`, `mcp-status.json` | Last GitHub update check and MCP health check |
| `trash/` | Uninstalled personal skills, restorable from the page |
| `machine.json` | This Mac's id and name for the online console |
| `cloud-state.json` | How many rows have already been sent to the online console |
| `secrets.json` | The upload key for the online console (owner-only, never in git) |

Each Mac also sends its rows to the online console's database (Cloudflare D1,
see above), which is what lets two Macs, and later teammates, share one history.

## Keep the history while the page is closed (optional)

Add this entry to the `SessionStart` list in `~/.claude/settings.json` (done
on the main Mac on 8 Nov 2026). It copies new uses in the background each time
a session starts:

```json
{
  "hooks": [
    {
      "type": "command",
      "command": "f=\"/Users/johnny/Desktop/Code/Monochrome/Claude/AI-skills/tools/skill-dashboard/ledger.py\"; [ -f \"$f\" ] && python3 \"$f\" --quiet; exit 0",
      "async": true,
      "timeout": 120
    }
  ]
}
```

Change the path if the repo moves. Without the hook, uses are still copied
each time you open the page; you only lose terminal sessions older than 30
days that happened while the page was never opened.

## Files

| File | Job |
|---|---|
| `config.json` | Every path, port, window and threshold |
| `ledger.py` | Copies skill uses and session titles out of transcripts (`--quiet` for the hook) |
| `inventory.py` | Lists skills by source and checks for updates |
| `mcp.py` | Parses `claude mcp list`; runs `claude mcp login` |
| `groups.py` | Group rules and your own group choices |
| `usage.py` | Per-project and per-session breakdowns |
| `actions.py` | The page's actions (single, bulk, groups), each re-checked against a fresh listing |
| `cost.py` | API-equivalent cost per day, project, session and token kind; applies `costLeaveOut` |
| `report.py` | Joins it all into the JSON the page renders |
| `server.py` | Local server, security checks, background jobs |
| `export.py` | Builds the read-only snapshot and the page without data |
| `cloud_sync.py` | Sends new rows and the snapshot to the online console |
| `build_site.py` | Writes the page into `cloud/public` for deploys |
| `cloud/` | The Cloudflare Worker, its config and database migrations |
| `web/` | The page: `tokens.css` → `ui.js`, `popover.js`, `controls.js` (dropdowns, menus), `overlays.js`, `charts.js` → `features/dashboard/` → `app.js` + `handlers.js`; all text in `content.js` and `copy-table.js` |

`python3 ~/.claude/skills/atomic-design/scripts/check_atomic.py tools/skill-dashboard`
checks the page code against the atomic-design rules (`atomic.config.json`
maps the folders).
