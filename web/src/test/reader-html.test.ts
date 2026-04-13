import { describe, expect, it } from "vitest";

import { enhanceReaderHtml } from "../lib/reader-html";

describe("enhanceReaderHtml", () => {
  it("wraps generated tables in a horizontal scroll container", () => {
    const html = "<section id=\"overview\"><table><tbody><tr><td>A</td></tr></tbody></table></section>";

    const enhanced = enhanceReaderHtml(html);

    expect(enhanced).toContain('<div class="reader-table-scroll"><table>');
    expect(enhanced).toContain("</table></div>");
  });

  it("leaves non-table markup unchanged", () => {
    const html = "<section id=\"overview\"><p>text only</p></section>";

    expect(enhanceReaderHtml(html)).toBe(html);
  });
});
