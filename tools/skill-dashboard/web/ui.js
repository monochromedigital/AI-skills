// Atoms and molecules. Generic building blocks: they take text and data as
// arguments, know nothing about skills, and style themselves only through
// classes defined in app.css (which reads tokens.css).

const SVG_NS = "http://www.w3.org/2000/svg";

export function h(tag, props = {}, ...children) {
  const el = document.createElement(tag);
  applyProps(el, props);
  append(el, children);
  return el;
}

export function svg(tag, props = {}, ...children) {
  const el = document.createElementNS(SVG_NS, tag);
  applyProps(el, props);
  append(el, children);
  return el;
}

function applyProps(el, props) {
  for (const [key, value] of Object.entries(props || {})) {
    if (value == null || value === false) continue;
    if (key === "class") el.setAttribute("class", Array.isArray(value) ? value.filter(Boolean).join(" ") : value);
    else if (key === "vars") for (const [name, v] of Object.entries(value)) el.style.setProperty(name, v);
    else if (key.startsWith("on") && typeof value === "function") el.addEventListener(key.slice(2).toLowerCase(), value);
    else if (key === "text") el.textContent = value;
    else el.setAttribute(key, value === true ? "" : value);
  }
}

function append(el, children) {
  for (const child of children.flat(Infinity)) {
    if (child == null || child === false) continue;
    el.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
}

/** Read a unitless number token such as --chart-height from the cascade. */
export function tokenNumber(el, name) {
  return parseFloat(getComputedStyle(el).getPropertyValue(name)) || 0;
}

// ── icons (24px grid, stroked) ──────────────────────────────────────────────
const ICONS = {
  check: "M5 12.5l4.5 4.5L19 7.5",
  "arrow-up": "M12 19V5M5.5 11.5L12 5l6.5 6.5",
  alert: "M12 8v5M12 16.5v.5M10.3 3.9L2.6 17.4A2 2 0 004.3 20.4h15.4a2 2 0 001.7-3L13.7 3.9a2 2 0 00-3.4 0z",
  dot: "M12 12h.01",
  cloud: "M7 18a4 4 0 01-.6-7.96A6 6 0 0118 9a4.5 4.5 0 01-.5 9H7z",
  minus: "M6 12h12",
  plus: "M12 6v12M6 12h12",
  question: "M9.5 9a2.5 2.5 0 114 2c-.9.6-1.5 1.2-1.5 2.3M12 17h.01",
  refresh: "M20 11a8 8 0 10-2.3 5.7M20 4v7h-7",
  x: "M6 6l12 12M18 6L6 18",
  external: "M14 4h6v6M20 4l-9 9M18 14v5a1 1 0 01-1 1H5a1 1 0 01-1-1V7a1 1 0 011-1h5",
  key: "M15 7a4 4 0 11-3.8 5.2L4 19.5V22h3v-2h2v-2h2l1.2-1.2A4 4 0 0115 7z",
  pause: "M9 6v12M15 6v12",
  box: "M4 8l8-4 8 4-8 4-8-4zM4 8v8l8 4 8-4V8",
  more: "M5 12h.01M12 12h.01M19 12h.01",
  "chevron-down": "M6 9l6 6 6-6",
  "chevron-right": "M9 6l6 6-6 6",
  "chevron-up": "M6 15l6-6 6 6",
  info: "M12 11v5M12 8h.01M12 3a9 9 0 100 18 9 9 0 000-18z",
  folder: "M3 7a2 2 0 012-2h4l2 2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V7z",
  copy: "M9 9h10v10H9zM5 15V5h10",
  trash: "M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 002 2h6a2 2 0 002-2l1-12M9 7V4h6v3",
  download: "M12 4v11M7 10l5 5 5-5M5 20h14",
};

export function Icon(name, size = "md") {
  return svg("svg", { class: ["icon", `icon--${size}`], viewBox: "0 0 24 24", "aria-hidden": "true" },
    svg("path", { d: ICONS[name] || ICONS.dot }));
}

// ── atoms ───────────────────────────────────────────────────────────────────
export const Badge = ({ text, tone = "neutral", title }) =>
  h("span", { class: ["badge", `badge--${tone}`], title }, text);

export const StatusPill = ({ text, tone, icon, title }) =>
  h("span", { class: ["status", `status--${tone}`], title }, Icon(icon, "sm"), h("span", { class: "status__text" }, text));

export function Button({ label, variant = "secondary", icon, onClick, disabled, title, size = "md", type = "button" }) {
  return h("button", { type, class: ["button", `button--${variant}`, `button--${size}`], onClick, disabled, title },
    icon ? Icon(icon, "sm") : null, label ? h("span", {}, label) : null);
}

export function IconButton({ icon, label, onClick, className }) {
  return h("button", { type: "button", class: ["icon-button", className], "aria-label": label, title: label, onClick }, Icon(icon));
}

/** onChange(checked, { shift }) — the click event, not change, so a shift-click can select a range. */
export function Checkbox({ label, checked, indeterminate, onChange }) {
  const box = h("input", { type: "checkbox", class: "checkbox", "aria-label": label, checked,
    onClick: (e) => { e.stopPropagation(); onChange(e.target.checked, { shift: e.shiftKey }); } });
  box.indeterminate = Boolean(indeterminate);
  return box;
}

export const LinkButton = ({ label, href, icon = "external" }) =>
  h("a", { class: ["button", "button--ghost", "button--sm"], href, target: "_blank", rel: "noopener noreferrer" },
    h("span", {}, label), Icon(icon, "sm"));

export const Text = ({ text, tone = "secondary", size = "sm", as = "span", title }) =>
  h(as, { class: ["text", `text--${tone}`, `text--${size}`], title }, text);

export const Code = (text) => h("code", { class: "code" }, text);

export function Select({ label, options, value, onChange }) {
  return h("select", { class: "control", "aria-label": label, onChange: (e) => onChange(e.target.value) },
    options.map((o) => h("option", { value: o.value, selected: o.value === value }, o.label)));
}

export function SearchInput({ label, value, onInput }) {
  return h("input", { class: ["control", "control--search"], type: "search", placeholder: label, "data-focus-key": label,
    "aria-label": label, value, onInput: (e) => onInput(e.target.value) });
}

// ── molecules ───────────────────────────────────────────────────────────────
export function StatTile({ label, value, sub, tone }) {
  return h("div", { class: ["stat", tone && `stat--${tone}`] },
    h("div", { class: "stat__label" }, label),
    h("div", { class: "stat__value" }, value),
    sub ? h("div", { class: "stat__sub" }, sub) : null);
}

export function Panel({ title, caption, actions, body, className }) {
  return h("section", { class: ["panel", className] },
    h("header", { class: "panel__head" },
      h("div", {}, h("h2", { class: "panel__title" }, title), caption ? h("p", { class: "panel__caption" }, caption) : null),
      actions ? h("div", { class: "panel__actions" }, actions) : null),
    h("div", { class: "panel__body" }, body));
}

export const EmptyState = (text) => h("p", { class: "empty" }, text);

export function ListRow({ lead, title, meta, trail }) {
  return h("li", { class: "row" },
    lead ? h("div", { class: "row__lead" }, lead) : null,
    h("div", { class: "row__main" }, h("div", { class: "row__title" }, title),
      meta ? h("div", { class: "row__meta", title: typeof meta === "string" ? meta : null }, meta) : null),
    trail ? h("div", { class: "row__trail" }, trail) : null);
}
