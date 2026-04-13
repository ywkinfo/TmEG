import { useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";

import type { ReaderChapter } from "../lib/generated-data";
import { formatDateTime, formatPageRange, stripGuideDots } from "../lib/formatters";
import { enhanceReaderHtml } from "../lib/reader-html";

type ReaderArticleProps = {
  chapter: ReaderChapter;
  activeSectionId: string;
  builtAt: string;
};

export function ReaderArticle({ chapter, activeSectionId, builtAt }: ReaderArticleProps): JSX.Element {
  const articleRef = useRef<HTMLDivElement | null>(null);
  const heroRef = useRef<HTMLElement | null>(null);
  const [isOutlineOpen, setIsOutlineOpen] = useState(() => window.matchMedia("(min-width: 62rem)").matches);

  useEffect(() => {
    const mediaQuery = window.matchMedia("(min-width: 62rem)");
    const syncOutlineState = (): void => {
      setIsOutlineOpen(mediaQuery.matches);
    };

    syncOutlineState();
    mediaQuery.addEventListener("change", syncOutlineState);

    return () => {
      mediaQuery.removeEventListener("change", syncOutlineState);
    };
  }, [chapter.slug]);

  const headingDepthById = useMemo(() => {
    return new Map(chapter.headings.map((heading) => [heading.id, heading.depth]));
  }, [chapter.headings]);
  const enhancedHtml = useMemo(() => enhanceReaderHtml(chapter.html), [chapter.html]);

  useEffect(() => {
    const articleNode = articleRef.current;
    const heroNode = heroRef.current;

    if (!articleNode) {
      return;
    }

    for (const heading of articleNode.querySelectorAll("h2, h3")) {
      heading.textContent = stripGuideDots(heading.textContent);
    }

    for (const section of articleNode.querySelectorAll("section")) {
      section.classList.remove("is-target");
    }

    const targetId = activeSectionId || "overview";
    const targetElement =
      targetId === "overview"
        ? heroNode
        : articleNode.querySelector<HTMLElement>(`section[id="${CSS.escape(targetId)}"]`);

    if (!targetElement) {
      return;
    }

    if (targetId !== "overview") {
      targetElement.classList.add("is-target");
    }

    requestAnimationFrame(() => {
      targetElement.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, [activeSectionId, enhancedHtml]);

  return (
    <article className="reader-column">
      <header ref={heroRef} className="surface chapter-hero">
        <div className="chapter-hero-copy">
          <span className="eyebrow">{chapter.partTitle}</span>
          <h1>{chapter.displayTitle}</h1>
          <p>{chapter.summary}</p>
        </div>
        <div className="meta-grid">
          <div className="meta-card">
            <span className="meta-label">페이지</span>
            <strong>{formatPageRange(chapter.pageStart, chapter.pageEnd)}</strong>
          </div>
          <div className="meta-card">
            <span className="meta-label">pageCode</span>
            <strong>{chapter.pageCode || "미상"}</strong>
          </div>
          <div className="meta-card">
            <span className="meta-label">이미지</span>
            <strong>{chapter.hasImage ? `${chapter.imageCount}개 포함` : "없음"}</strong>
          </div>
          <div className="meta-card">
            <span className="meta-label">build</span>
            <strong>{formatDateTime(builtAt)}</strong>
          </div>
        </div>
      </header>

      <section className="surface chapter-outline" aria-label="현재 장 개요와 섹션 이동">
        <div className="outline-header">
          <div>
            <span className="eyebrow">Chapter outline</span>
            <h2>장 개요와 섹션 이동</h2>
          </div>
          <button
            type="button"
            className="outline-toggle"
            aria-expanded={isOutlineOpen}
            onClick={() => setIsOutlineOpen((current) => !current)}
          >
            {isOutlineOpen ? "접기" : "펼치기"}
          </button>
        </div>

        {isOutlineOpen ? (
          <nav className="outline-list" aria-label="현재 장 섹션 이동">
            {chapter.sectionCatalog.map((entry) => {
              const isActive = entry.sectionId === (activeSectionId || "overview");
              const depth = entry.sectionId === "overview" ? 2 : headingDepthById.get(entry.sectionId) ?? 3;

              return (
                <Link
                  key={`${chapter.slug}-${entry.sectionId}`}
                  to={entry.routePath}
                  className={`outline-link${isActive ? " is-active" : ""}`}
                  data-depth={depth}
                >
                  <span className="outline-link-title">{stripGuideDots(entry.sectionTitle)}</span>
                  <span className="outline-link-meta">{formatPageRange(entry.pageStart, entry.pageEnd)}</span>
                </Link>
              );
            })}
          </nav>
        ) : null}
      </section>

      <div ref={articleRef} className="surface reader-article" dangerouslySetInnerHTML={{ __html: enhancedHtml }} />
    </article>
  );
}
