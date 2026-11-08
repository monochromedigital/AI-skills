// One floating panel at a time, anchored to the control that opened it.
// Dropdowns and menus (controls.js) both sit on this: it places the panel,
// keeps it in the viewport, closes it on an outside click or Escape, and
// gives its items arrow-key navigation.

import { tokenNumber } from "./ui.js";

let current = null;

export const isOpenFor = (anchor) => current?.anchor === anchor;

function place(anchor, panel) {
  const gap = tokenNumber(document.documentElement, "--popover-gap");
  const a = anchor.getBoundingClientRect();
  panel.style.setProperty("--anchor-width", `${a.width}px`);
  const p = panel.getBoundingClientRect();
  const fitsBelow = a.bottom + gap + p.height <= window.innerHeight;
  const top = fitsBelow ? a.bottom + gap : Math.max(gap, a.top - gap - p.height);
  // Line up with the anchor's left edge, or its right edge when that would run off screen.
  const left = a.left + p.width + gap > window.innerWidth ? a.right - p.width : a.left;
  panel.style.setProperty("--x", `${Math.max(gap, left)}px`);
  panel.style.setProperty("--y", `${top}px`);
}

export function closePopover({ restoreFocus = false } = {}) {
  if (!current) return;
  const { anchor, panel, teardown } = current;
  current = null;
  teardown();
  panel.remove();
  anchor.setAttribute("aria-expanded", "false");
  if (restoreFocus) anchor.focus();
}

export function openPopover(anchor, panel) {
  closePopover();
  panel.classList.add("popover");
  document.body.append(panel);
  const reposition = () => place(anchor, panel);
  const onPointer = (e) => {
    if (!panel.contains(e.target) && !anchor.contains(e.target)) closePopover();
  };
  // Capture phase, so Escape closes the popover before a drawer behind it sees the key.
  const onKey = (e) => {
    if (e.key !== "Escape") return;
    e.preventDefault();
    closePopover({ restoreFocus: true });
  };
  document.addEventListener("pointerdown", onPointer, true);
  document.addEventListener("keydown", onKey, true);
  window.addEventListener("resize", reposition);
  window.addEventListener("scroll", reposition, true);
  current = {
    anchor, panel,
    teardown: () => {
      document.removeEventListener("pointerdown", onPointer, true);
      document.removeEventListener("keydown", onKey, true);
      window.removeEventListener("resize", reposition);
      window.removeEventListener("scroll", reposition, true);
    },
  };
  anchor.setAttribute("aria-expanded", "true");
  reposition();
}

/** Arrow keys, Home and End move between items; Enter or Space picks; Tab leaves. */
export function navigable(panel, selector) {
  const items = () => [...panel.querySelectorAll(selector)].filter((el) => el.getAttribute("aria-disabled") !== "true");
  panel.addEventListener("keydown", (e) => {
    const list = items();
    const index = list.indexOf(document.activeElement);
    const go = (i) => {
      e.preventDefault();
      list[(i + list.length) % list.length]?.focus();
    };
    if (e.key === "ArrowDown") go(index + 1);
    else if (e.key === "ArrowUp") go(index < 0 ? list.length - 1 : index - 1);
    else if (e.key === "Home") go(0);
    else if (e.key === "End") go(list.length - 1);
    else if ((e.key === "Enter" || e.key === " ") && index >= 0) {
      e.preventDefault();
      list[index].click();
    } else if (e.key === "Tab") closePopover();
  });
}
