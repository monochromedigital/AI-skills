// Page layer: redraw part of the page without losing the reader's place.

/** Run `redraw`, then put back the scroll of the element `scroller()` returns and
 *  the focus on whichever control inside `root` had the same data-focus-key. */
export function keepPlace(root, scroller, redraw) {
  const scroll = scroller()?.scrollTop ?? 0;
  const focusKey = root.contains(document.activeElement) ? document.activeElement.dataset.focusKey : null;
  redraw();
  const wrap = scroller();
  if (wrap) wrap.scrollTop = scroll;
  const again = focusKey && [...root.querySelectorAll("[data-focus-key]")].find((el) => el.dataset.focusKey === focusKey);
  if (!again) return;
  again.focus();
  if (again.setSelectionRange) again.setSelectionRange(again.value.length, again.value.length);
}
