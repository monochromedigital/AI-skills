// Overlays: tooltip, confirm dialog and toasts. Generic like ui.js; they take
// every word they show as an argument.

import { Button, h, Icon, tokenNumber } from "./ui.js";

// ── overlays ────────────────────────────────────────────────────────────────
let tooltipEl;
export const tooltip = {
  show(lines, x, y) {
    tooltipEl ??= document.body.appendChild(h("div", { class: "tooltip", role: "tooltip" }));
    tooltipEl.replaceChildren(...[].concat(lines).map((line, i) => h("div", { class: i ? "tooltip__sub" : "tooltip__main" }, line)));
    const offset = tokenNumber(document.documentElement, "--tooltip-offset");
    tooltipEl.classList.add("is-visible");
    const { width, height } = tooltipEl.getBoundingClientRect();
    const left = Math.min(x + offset, window.innerWidth - width - offset);
    const top = y - height - offset < 0 ? y + offset : y - height - offset;
    tooltipEl.style.setProperty("--x", `${Math.max(offset, left)}px`);
    tooltipEl.style.setProperty("--y", `${top}px`);
  },
  hide() {
    tooltipEl?.classList.remove("is-visible");
  },
};

export function confirmDialog({ title, body, confirmLabel, cancelLabel, danger = true }) {
  return new Promise((resolve) => {
    const dialog = h("dialog", { class: "dialog" },
      h("form", { method: "dialog", class: "dialog__form" },
        h("h2", { class: "dialog__title" }, title),
        h("p", { class: "dialog__body" }, body),
        h("div", { class: "dialog__actions" },
          Button({ label: cancelLabel, variant: "ghost", type: "submit" }),
          h("button", { class: ["button", danger ? "button--danger" : "button--primary", "button--md"], value: "confirm", type: "submit" }, confirmLabel))));
    dialog.addEventListener("close", () => {
      resolve(dialog.returnValue === "confirm");
      dialog.remove();
    });
    document.body.append(dialog);
    dialog.showModal();
  });
}

let toastStack;
export function toast({ text, tone = "neutral", icon = "dot", closeLabel }) {
  toastStack ??= document.body.appendChild(h("div", { class: "toasts", role: "status", "aria-live": "polite" }));
  const message = h("div", { class: "toast__text" }, text);
  const detail = h("pre", { class: "toast__log", hidden: true });
  const lead = h("span", { class: "toast__icon" }, Icon(icon, "sm"));
  const el = h("div", { class: ["toast", `toast--${tone}`] }, lead,
    h("div", { class: "toast__main" }, message, detail),
    Button({ icon: "x", variant: "ghost", size: "sm", title: closeLabel, onClick: () => el.remove() }));
  toastStack.prepend(el);
  return {
    update({ text: next, tone: nextTone, icon: nextIcon, log }) {
      if (next) message.textContent = next;
      if (nextTone) el.className = `toast toast--${nextTone}`;
      if (nextIcon) lead.replaceChildren(Icon(nextIcon, "sm"));
      if (log) {
        detail.textContent = log;
        detail.hidden = false;
      }
    },
    close: () => el.remove(),
  };
}

/** Ask for one line of text. Resolves to the trimmed text, or null on cancel. */
export function promptDialog({ title, label, confirmLabel, cancelLabel }) {
  return new Promise((resolve) => {
    const input = h("input", { class: ["control", "control--wide"], type: "text", "aria-label": label, placeholder: label, required: true });
    const dialog = h("dialog", { class: "dialog" },
      h("form", { method: "dialog", class: "dialog__form" },
        h("h2", { class: "dialog__title" }, title),
        h("div", { class: "dialog__body" }, input),
        h("div", { class: "dialog__actions" },
          h("button", { class: ["button", "button--ghost", "button--md"], value: "cancel", type: "submit", formnovalidate: true }, cancelLabel),
          h("button", { class: ["button", "button--primary", "button--md"], value: "confirm", type: "submit" }, confirmLabel))));
    dialog.addEventListener("close", () => {
      resolve(dialog.returnValue === "confirm" && input.value.trim() ? input.value.trim() : null);
      dialog.remove();
    });
    document.body.append(dialog);
    dialog.showModal();
    input.focus();
  });
}

/**
 * A side panel over the page. It is not a modal <dialog>: a modal sits in the
 * browser's top layer, above every dropdown, tooltip and toast appended to the
 * body, and those must stay usable from inside the panel.
 */
export function Drawer({ title, subtitle, body, closeLabel, onClose }) {
  const close = () => {
    document.removeEventListener("keydown", onKey);
    root.remove();
    onClose?.();
  };
  const onKey = (e) => { if (e.key === "Escape" && !e.defaultPrevented) close(); };
  const panel = h("aside", { class: "drawer", role: "dialog", "aria-modal": "true", "aria-label": title, tabindex: -1 },
    h("header", { class: "drawer__head" },
      h("div", { class: "drawer__titles" }, h("h2", { class: "drawer__title" }, title), subtitle ? h("div", { class: "drawer__sub" }, subtitle) : null),
      Button({ icon: "x", variant: "ghost", size: "sm", title: closeLabel, onClick: close })),
    h("div", { class: "drawer__body" }, body));
  const root = h("div", { class: "drawer-layer" }, h("div", { class: "drawer__backdrop", onClick: close }), panel);
  document.addEventListener("keydown", onKey);
  document.body.append(root);
  panel.focus();
  return { close };
}
