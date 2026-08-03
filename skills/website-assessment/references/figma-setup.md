# Figma plugin — setup and use

The plugin builds the same slides as the PPTX, but as native Figma frames in
the user's own file, where they can be edited with real components.

## What it can and cannot do

Figma has two APIs and only one of them writes:

| | Can create frames/text/images? |
|---|---|
| Figma REST API / the Figma MCP connector | **No** — read only |
| Figma **Plugin** API (this plugin) | **Yes** |

So the deck cannot be generated remotely into a Figma file. It is generated
by a plugin the user runs inside their own Figma desktop app. That is the only
route that writes.

## One-time install

Development plugins require the **Figma desktop app** (Mac or Windows). Free on
any plan — no paid tier needed.

1. Save the `figma-plugin/` folder somewhere permanent — not Downloads.
2. Figma desktop → menu → **Plugins → Development → Import plugin from
   manifest…**
3. Select `figma-plugin/manifest.json`.
4. It now appears under Plugins → Development → **Crackwits Website
   Assessment**.

Each person on the team repeats this. To get one-click install for everyone,
publish it privately — that needs a Figma **Organization or Enterprise** plan
(Professional cannot publish private plugins).

## Fonts

The plugin loads **Urbanist** in Light, Regular, Medium, SemiBold, and Bold. If
Urbanist is not available in the file it falls back to Inter and warns in the
plugin window. Install Urbanist from Google Fonts (or enable it in the Figma
font picker) before the first run.

## Running an audit through it

1. Open the Figma file for the assessment.
2. Plugins → Development → Crackwits Website Assessment.
3. Drop `findings.json` into the first zone.
4. Drop every framed PNG into the second zone. The plugin matches them to
   slides by filename and tells you if any are missing.
5. Optionally drop `assets/brand.json` too — it overrides the built-in colours
   and layout, so retheming means editing one file rather than the plugin.
6. Set the frame size (default 3840×2160) and press **Build slides**.

Slides are created in a row at the current viewport, grouped and named
`<Client> — Assessment`.

The plugin makes no network requests; everything comes from the dropped files.

## What you get

Every slide is real Figma structure, not a flattened image:

- Findings panel is an auto-layout column — delete a card and the rest reflow
- Each card is auto-layout, so editing text resizes the card
- Tag row uses wrap layout, so adding a tag never overflows
- Markers are named `marker/01`… and can be dragged to reposition
- The screenshot is an image fill on a rectangle — swap it without rebuilding

## Using your own components instead

To have the plugin clone your master components rather than build cards from
scratch, replace the card-construction block in `code.js`:

```js
const master = await figma.importComponentByKeyAsync('<component-key>');
const card = master.createInstance();
// then set text on named layers:
card.findOne(n => n.name === 'observation').characters = f.observation;
```

Get a component key from Figma: right-click the component → Copy link → the key
is the last path segment. Requires the component to be published to a library.
