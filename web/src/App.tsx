import { useEffect, useState } from "react";
import { Link, Navigate, Route, Routes, useLocation, useMatch } from "react-router-dom";

import { ExplorationPanel } from "./components/ExplorationPanel";
import { ReaderArticle } from "./components/ReaderArticle";
import { TocPanel } from "./components/TocPanel";
import { TopbarSearch } from "./components/TopbarSearch";
import type { ReaderData } from "./lib/generated-data";
import { loadGeneratedData, resolveCanonicalChapterRoute } from "./lib/generated-data";
import { formatDateTime, formatPageRange, stripGuideDots } from "./lib/formatters";

type LoadState =
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "ready"; data: ReaderData };

function useBodyScrollLock(locked: boolean): void {
  useEffect(() => {
    if (!locked) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      document.body.style.overflow = previousOverflow;
    };
  }, [locked]);
}

function HomePage({ data }: { data: ReaderData }): JSX.Element {
  return (
    <div className="page-stack">
      <section className="surface landing-hero">
        <div className="chapter-hero-copy">
          <span className="eyebrow">상표심사기준 웹앱 리더</span>
          <h1>상표심사기준을 언제 어디서나 쉽게 참조할 수 있도록 웹앱 형태로 정리해 제공하는 페이지입니다.</h1>
          <p>
            특히, 복잡한 상표심사기준 관련 보조 참고자료는{" "}
            <a
              className="landing-copy-link"
              href="https://notebooklm.google.com/notebook/a5eb446a-1308-440e-bacd-dd59f9ee8bbf"
              target="_blank"
              rel="noreferrer"
            >
              Google NotebookLM 노트북
            </a>
            을 활용해 보세요. 방대한 데이터 속에서 필요한 정보를 AI가 신속하게 찾아내고 분석해 주어 심사 기준을 더욱
            스마트하고 효율적으로 파악할 수 있습니다.
          </p>
          <p>
            인하우스 팀의 해외 출원 등 전문적인 브랜드 관리 정보는{" "}
            <a
              className="landing-copy-link"
              href="https://ywkinfo.github.io/glotm/"
              target="_blank"
              rel="noreferrer"
            >
              GloTm 인하우스 팀을 위한 cross-border trademark operating guide
            </a>
            에서 함께 확인해 주세요.
          </p>
          <p>
            이 사이트의 운영자 및 출원·상담·강연 및 심층 연구에 관한 자세한 안내는{" "}
            <a className="landing-copy-link" href="https://ywkinfo.github.io" target="_blank" rel="noreferrer">
              ywkinfo.github.io
            </a>
            에서 확인하실 수 있습니다.
          </p>
        </div>
        <div className="meta-grid">
          <div className="meta-card">
            <span className="meta-label">동기화 시각</span>
            <strong>{formatDateTime(data.manifest.syncedAt)}</strong>
          </div>
          <div className="meta-card">
            <span className="meta-label">챕터 수</span>
            <strong>{data.meta.chapterCount}</strong>
          </div>
          <div className="meta-card">
            <span className="meta-label">페이지 수</span>
            <strong>{data.meta.pageCount}</strong>
          </div>
          <div className="meta-card">
            <span className="meta-label">탐색 태그</span>
            <strong>{data.explorationCounts.length}</strong>
          </div>
        </div>
      </section>

      <section className="content-grid">
        <div className="reader-column">
          {data.parts.map((part) => (
            <section key={part.id} className="surface catalog-section">
              <div className="section-heading">
                <span className="eyebrow">{part.label}</span>
                <h2>{part.title}</h2>
              </div>
              <div className="chapter-card-grid">
                {part.chapters.map((chapter) => (
                  <Link key={chapter.slug} to={chapter.sectionCatalog[0]?.routePath} className="chapter-card">
                    <span className="result-kicker">{stripGuideDots(chapter.partTitle)}</span>
                    <strong>{chapter.displayTitle}</strong>
                    <p>{chapter.summary}</p>
                    <div className="chapter-card-meta">
                      <span>{formatPageRange(chapter.pageStart, chapter.pageEnd)}</span>
                      <span>{chapter.tocItemCount}개 항목</span>
                      <span>{chapter.hasImage ? `이미지 ${chapter.imageCount}개` : "텍스트 중심"}</span>
                    </div>
                  </Link>
                ))}
              </div>
            </section>
          ))}
        </div>

        <ExplorationPanel
          title="전체 탐색 요약"
          entries={data.explorationEntries}
          emptyMessage="탐색 태그가 붙은 항목이 아직 없습니다."
        />
      </section>
    </div>
  );
}

function ChapterPage({ data }: { data: ReaderData }): JSX.Element {
  const location = useLocation();
  const sectionMatch = useMatch("/chapter/:chapterSlug/:sectionId");
  const chapterMatch = useMatch("/chapter/:chapterSlug");
  const chapterSlug = sectionMatch?.params.chapterSlug ?? chapterMatch?.params.chapterSlug ?? "";
  const requestedSectionId = sectionMatch?.params.sectionId;

  const chapter = data.chapterMap.get(chapterSlug);
  if (!chapter) {
    return <Navigate to="/" replace />;
  }

  const chapterRoute = resolveCanonicalChapterRoute(chapter, requestedSectionId);
  if (location.pathname !== chapterRoute.canonicalPath) {
    return <Navigate to={chapterRoute.canonicalPath} replace />;
  }

  return (
    <div className="page-stack">
      <ReaderArticle chapter={chapter} activeSectionId={chapterRoute.activeSectionId} builtAt={data.meta.builtAt} />
    </div>
  );
}

function ReaderShell({ data }: { data: ReaderData }): JSX.Element {
  const location = useLocation();
  const sectionMatch = useMatch("/chapter/:chapterSlug/:sectionId");
  const chapterMatch = useMatch("/chapter/:chapterSlug");
  const chapterSlug = sectionMatch?.params.chapterSlug ?? chapterMatch?.params.chapterSlug ?? null;
  const currentChapter = chapterSlug ? data.chapterMap.get(chapterSlug) ?? null : null;
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  useBodyScrollLock(isDrawerOpen);

  useEffect(() => {
    setIsDrawerOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const title = currentChapter ? `${currentChapter.displayTitle} · TmEG Reader` : "TmEG Reader";
    document.title = title;
  }, [currentChapter]);

  return (
    <div className="app-shell">
      <header className="topbar">
        <div className="topbar-row">
          <button type="button" className="menu-button" onClick={() => setIsDrawerOpen(true)} aria-label="목차 열기">
            목차
          </button>
          <Link to="/" className="brand-block">
            <span className="eyebrow">TmEG Reader</span>
            <strong>{currentChapter?.displayTitle ?? "상표심사기준"}</strong>
          </Link>
        </div>
        <TopbarSearch
          searchEntries={data.searchEntries}
          chapters={data.chapters}
          onFocusSearch={() => setIsDrawerOpen(false)}
        />
      </header>

      <div className="layout-frame">
        <aside className="rail surface rail-desktop">
          <div className="section-heading compact">
            <span className="eyebrow">Contents</span>
            <h2>목차</h2>
          </div>
          <TocPanel parts={data.parts} currentChapter={currentChapter} />
        </aside>

        <main className="main-panel">
          <Routes>
            <Route path="/" element={<HomePage data={data} />} />
            <Route path="/chapter/:chapterSlug" element={<ChapterPage data={data} />} />
            <Route path="/chapter/:chapterSlug/:sectionId" element={<ChapterPage data={data} />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>

      <div className={`drawer-shell${isDrawerOpen ? " is-open" : ""}`} aria-hidden={!isDrawerOpen}>
        <button type="button" className="drawer-backdrop" onClick={() => setIsDrawerOpen(false)} aria-label="목차 닫기" />
        <aside className="drawer-panel surface">
          <div className="drawer-header">
            <div>
              <span className="eyebrow">Contents</span>
              <h2>모바일 목차</h2>
            </div>
            <button type="button" className="close-button" onClick={() => setIsDrawerOpen(false)}>
              닫기
            </button>
          </div>
          <TocPanel parts={data.parts} currentChapter={currentChapter} onNavigate={() => setIsDrawerOpen(false)} />
        </aside>
      </div>
    </div>
  );
}

export function App(): JSX.Element {
  const [state, setState] = useState<LoadState>({ status: "loading" });

  useEffect(() => {
    let cancelled = false;

    loadGeneratedData()
      .then((data) => {
        if (!cancelled) {
          setState({ status: "ready", data });
        }
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          const message = error instanceof Error ? error.message : String(error);
          setState({ status: "error", message });
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (state.status === "loading") {
    return (
      <div className="status-shell">
        <div className="surface status-card">
          <span className="eyebrow">Loading</span>
          <h1>generated JSON을 reader shell에 맞춰 조립하고 있습니다.</h1>
        </div>
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="status-shell">
        <div className="surface status-card error-state">
          <span className="eyebrow">Reader error</span>
          <h1>리더 데이터를 불러오지 못했습니다.</h1>
          <p>{state.message}</p>
          <p>
            먼저 <code>npm run web:prepare</code>로 generated 계약을 동기화한 뒤, 새 번들 앱을 다시 열어 주세요.
          </p>
        </div>
      </div>
    );
  }

  return <ReaderShell data={state.data} />;
}
