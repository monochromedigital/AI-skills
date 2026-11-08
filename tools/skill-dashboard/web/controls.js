// Custom dropdown (single choice, optional search) and three-dots menu, both
// drawn by the page instead of the operating system. Generic: they take every
// label they show as an argument.

import { closePopover, isOpenFor, navigable, openPopover } from "./popover.js";
import { h, Icon } from "./ui.js";

const Item = ({ role, icon, label, aside, selected, danger, disabled, title, onClick }) =>
  h("li", { role, tabindex: -1, class: ["popover__item", danger && "is-danger"], title,
    "aria-selected": role === "option" ? String(Boolean(selected)) : null,
    "aria-disabled": disabled ? "true" : null, onClick: disabled ? null : onClick },
  h("span", { class: "popover__icon" }, icon ? Icon(icon, "sm") : null),
  h("span", { class: "popover__label" }, label),
  aside != null ? h("span", { class: "popover__aside" }, aside) : null);

const Separator = () => h("li", { role: "separator", class: "popover__sep" });

/**
 * Open a single-choice list beside `anchor`.
 * options: [{ value, label, count }]; extra: [{ label, icon, onSelect }] shown
 * under a line, for things like "New group…".
 */
export function openListbox(anchor, { label, options, value, onPick, searchLabel, searchMin = Infinity, extra = [] }) {
  const list = h("ul", { class: "popover__list", role: "listbox", "aria-label": label });
  const pick = (fn) => () => { closePopover({ restoreFocus: true }); fn(); };
  const render = (query = "") => {
    const q = query.trim().toLowerCase();
    const shown = options.filter((o) => !q || o.label.toLowerCase().includes(q));
    list.replaceChildren(
      ...shown.map((o) => Item({ role: "option", label: o.label, aside: o.count, selected: o.value === value,
        icon: o.value === value ? "check" : null, onClick: pick(() => onPick(o.value)) })),
      ...(extra.length ? [Separator(), ...extra.map((x) => Item({ role: "option", label: x.label, icon: x.icon, onClick: pick(x.onSelect) }))] : []));
  };
  const search = options.length >= searchMin
    ? h("input", { class: "popover__search", type: "search", placeholder: searchLabel, "aria-label": searchLabel,
      onInput: (e) => render(e.target.value),
      onKeydown: (e) => { if (e.key === "ArrowDown") { e.preventDefault(); list.querySelector("[role=option]")?.focus(); } } })
    : null;
  render();
  const panel = h("div", { class: "popover--list" }, search, list);
  openPopover(anchor, panel);
  navigable(panel, "[role=option]");
  (search ?? list.querySelector('[aria-selected="true"]') ?? list.querySelector("[role=option]"))?.focus();
}

/** A button that shows the current choice and opens the list. */
export function Dropdown({ label, options, value, onChange, searchLabel, searchMin, prefix }) {
  const chosen = options.find((o) => o.value === value) ?? options[0];
  const button = h("button", {
    type: "button", class: ["dropdown", chosen !== options[0] && "is-set"], title: label, "data-focus-key": label,
    "aria-haspopup": "listbox", "aria-expanded": "false", "aria-label": label,
    onClick: () => (isOpenFor(button) ? closePopover()
      : openListbox(button, { label, options, value, onPick: onChange, searchLabel, searchMin })),
  },
  prefix ? h("span", { class: "dropdown__prefix" }, prefix) : null,
  h("span", { class: "dropdown__value" }, chosen?.label ?? label),
  Icon("chevron-down", "sm"));
  return button;
}

/** Open a menu beside `anchor`. items: [{ label, icon, onSelect, danger, disabled, hint } | { separator: true }]. */
export function openMenu(anchor, { label, items }) {
  const list = h("ul", { class: "popover__list", role: "menu", "aria-label": label },
    items.filter(Boolean).map((item) => (item.separator ? Separator() : Item({
      role: "menuitem", label: item.label, icon: item.icon, danger: item.danger, disabled: item.disabled,
      title: item.hint, aside: item.disabled ? item.hint : null,
      onClick: () => { closePopover(); item.onSelect?.(anchor); },
    }))));
  const panel = h("div", { class: "popover--menu" }, list);
  openPopover(anchor, panel);
  navigable(panel, "[role=menuitem]");
  list.querySelector('[role=menuitem]:not([aria-disabled="true"])')?.focus();
}

/** The three-dots button. `items` is a function so the menu is built when opened. */
export function Menu({ label, items, icon = "more" }) {
  const button = h("button", {
    type: "button", class: "icon-button", title: label, "aria-label": label,
    "aria-haspopup": "menu", "aria-expanded": "false",
    onClick: (e) => {
      e.stopPropagation();
      if (isOpenFor(button)) closePopover();
      else openMenu(button, { label, items: items() });
    },
  }, Icon(icon));
  return button;
}
