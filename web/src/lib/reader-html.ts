const TABLE_OPEN_RE = /<table\b([^>]*)>/g;
const TABLE_CLOSE_RE = /<\/table>/g;

export function enhanceReaderHtml(html: string): string {
  if (!html || !html.includes("<table")) {
    return html;
  }

  return html
    .replace(TABLE_OPEN_RE, '<div class="reader-table-scroll"><table$1>')
    .replace(TABLE_CLOSE_RE, "</table></div>");
}
