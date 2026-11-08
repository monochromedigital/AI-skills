// The steps for adding a cloud environment to tracking, opened from the
// Cloud environments panel. Names the console address and the file on the
// Mac that holds the lines to paste; never shows the key itself.

import { COPY, fill } from "../../content.js";
import { h, Text } from "../../ui.js";

export function CloudGuide(report) {
  const g = COPY.cloudGuide;
  const values = { host: report.cloudSetup?.host ?? "", file: report.cloudSetup?.envFile ?? "" };
  return h("div", { class: "guide" },
    Text({ text: g.intro, as: "p" }),
    h("ol", { class: "guide__steps" }, g.steps.map((step) => h("li", {}, fill(step, values)))),
    Text({ text: g.check, tone: "muted", size: "xs", as: "p" }),
    Text({ text: g.skill, tone: "muted", size: "xs", as: "p" }));
}
