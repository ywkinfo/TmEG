const GENERATED_FILES = {
  manifest: new URL("../public/generated/manifest.json", import.meta.url),
  documentData: new URL("../public/generated/document-data.json", import.meta.url),
  searchIndex: new URL("../public/generated/search-index.json", import.meta.url),
  explorationIndex: new URL("../public/generated/exploration-index.json", import.meta.url),
};

const CATEGORY_LABELS = {
  "related-law": "관련 법령",
  requirements: "적용 요건",
  caution: "유의사항",
  timing: "판단 시점",
  case: "사례·예시",
  supplement: "보충기준",
  procedure: "절차",
  "non-traditional-mark": "비전통 상표",
};

const state = {
  manifest: null,
  documentData: null,
  searchIndex: [],
  explorationIndex: [],
  currentChapterId: null,
  activeSectionId: "overview",
  activeCategory: "",
  query: "",
  pendingScrollTarget: "",
};

const elements = {
  heroMeta: document.querySelector("#hero-meta"),
  tocPanel: document.querySelector("#toc-panel"),
  readerPanel: document.querySelector("#reader-panel"),
  utilityPanel: document.querySelector("#utility-panel"),
  searchInput: document.querySelector("#search-input"),
  searchReset: document.querySelector("#search-reset"),
};

function stripGuideDots(value) {
  return String(value || "")
    .replace(/·+/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function normalizeText(value) {
  return stripGuideDots(value).toLowerCase();
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function formatDateTime(value) {
  if (!value) {
    return "미상";
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("ko-KR", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(parsed);
}

function formatPageRange(start, end) {
  if (!start && !end) {
    return "페이지 미상";
  }
  if (start === end || !end) {
    return `p.${start}`;
  }
  return `p.${start}-${end}`;
}

function getCurrentChapter() {
  return (
    state.documentData?.chapters.find((chapter) => chapter.id === state.currentChapterId) ?? null
  );
}

function getTocGroups() {
  const chapters = state.documentData?.chapters ?? [];
  const groups = [];
  for (const chapter of chapters) {
    const partTitle = stripGuideDots(chapter.partTitle);
    const currentGroup = groups[groups.length - 1];
    if (!currentGroup || currentGroup.partTitle !== partTitle) {
      groups.push({ partTitle, chapters: [chapter] });
      continue;
    }
    currentGroup.chapters.push(chapter);
  }
  return groups;
}

function getCurrentChapterEntries() {
  const chapter = getCurrentChapter();
  if (!chapter) {
    return [];
  }
  return state.searchIndex.filter((entry) => entry.chapterSlug === chapter.slug);
}

function getSearchResults() {
  const query = normalizeText(state.query);
  if (!query) {
    return [];
  }

  return state.searchIndex
    .map((entry) => {
      const sectionTitle = normalizeText(entry.sectionTitle);
      const chapterTitle = normalizeText(entry.chapterTitle);
      const haystack = normalizeText(
        `${entry.sectionTitle} ${entry.chapterTitle} ${entry.partTitle} ${entry.excerpt} ${entry.text}`
      );
      let score = 0;
      if (sectionTitle.includes(query)) {
        score += 5;
      }
      if (chapterTitle.includes(query)) {
        score += 3;
      }
      if (normalizeText(entry.excerpt).includes(query)) {
        score += 2;
      }
      if (haystack.includes(query)) {
        score += 1;
      }
      return score > 0 ? { entry, score } : null;
    })
    .filter(Boolean)
    .sort((left, right) => {
      if (right.score !== left.score) {
        return right.score - left.score;
      }
      return (left.entry.pageStart ?? 0) - (right.entry.pageStart ?? 0);
    })
    .slice(0, 40)
    .map(({ entry }) => entry);
}

function getCategoryCounts() {
  const counts = new Map();
  for (const entry of state.explorationIndex) {
    for (const category of entry.categories ?? []) {
      counts.set(category, (counts.get(category) ?? 0) + 1);
    }
  }
  return [...counts.entries()].sort((left, right) => {
    if (right[1] !== left[1]) {
      return right[1] - left[1];
    }
    return left[0].localeCompare(right[0], "ko");
  });
}

function getCategoryEntries() {
  if (!state.activeCategory) {
    return [];
  }
  return state.explorationIndex
    .filter((entry) => (entry.categories ?? []).includes(state.activeCategory))
    .slice(0, 24);
}

function buildHash(chapterId, sectionId) {
  const params = new URLSearchParams();
  if (chapterId) {
    params.set("chapter", chapterId);
  }
  if (sectionId) {
    params.set("section", sectionId);
  }
  const serialized = params.toString();
  return serialized ? `#${serialized}` : "";
}

function syncHash() {
  const nextHash = buildHash(state.currentChapterId, state.activeSectionId);
  if (window.location.hash !== nextHash) {
    history.replaceState(null, "", `${window.location.pathname}${window.location.search}${nextHash}`);
  }
}

function applyHashSelection() {
  const params = new URLSearchParams(window.location.hash.replace(/^#/, ""));
  const chapterId = params.get("chapter");
  const sectionId = params.get("section");
  if (!chapterId) {
    return;
  }
  const chapter = state.documentData?.chapters.find((item) => item.id === chapterId);
  if (!chapter) {
    return;
  }
  state.currentChapterId = chapter.id;
  state.activeSectionId = sectionId || "overview";
}

function selectLocation(chapterId, sectionId = "overview", shouldScroll = true) {
  state.currentChapterId = chapterId;
  state.activeSectionId = sectionId;
  state.pendingScrollTarget = shouldScroll ? sectionId : "";
  state.activeCategory = "";
  syncHash();
  render();
}

function renderHeroMeta() {
  const manifest = state.manifest;
  const documentMeta = state.documentData?.meta;
  if (!manifest || !documentMeta) {
    elements.heroMeta.innerHTML = "";
    return;
  }

  elements.heroMeta.innerHTML = `
    <div class="meta-card">
      <span class="meta-label">동기화 시각</span>
      <strong>${escapeHtml(formatDateTime(manifest.syncedAt))}</strong>
    </div>
    <div class="meta-card">
      <span class="meta-label">챕터 수</span>
      <strong>${escapeHtml(String(documentMeta.chapterCount))}</strong>
    </div>
    <div class="meta-card">
      <span class="meta-label">검색 엔트리</span>
      <strong>${escapeHtml(String(state.searchIndex.length))}</strong>
    </div>
    <div class="meta-card">
      <span class="meta-label">탐색 태그</span>
      <strong>${escapeHtml(String(getCategoryCounts().length))}</strong>
    </div>
  `;
}

function renderToc() {
  const currentChapter = getCurrentChapter();
  elements.tocPanel.innerHTML = getTocGroups()
    .map(
      (group) => `
        <section class="toc-group">
          <h3>${escapeHtml(group.partTitle)}</h3>
          <div class="toc-list">
            ${group.chapters
              .map((chapter) => {
                const isActive = currentChapter?.id === chapter.id;
                return `
                  <button
                    class="toc-link ${isActive ? "is-active" : ""}"
                    type="button"
                    data-chapter-id="${escapeHtml(chapter.id)}"
                  >
                    <span class="toc-title">${escapeHtml(stripGuideDots(chapter.title))}</span>
                    <span class="toc-meta">${escapeHtml(
                      formatPageRange(chapter.pageStart, chapter.pageEnd)
                    )}</span>
                  </button>
                `;
              })
              .join("")}
          </div>
        </section>
      `
    )
    .join("");
}

function renderReader() {
  const chapter = getCurrentChapter();
  if (!chapter) {
    elements.readerPanel.innerHTML = `
      <div class="empty-state">
        <h3>표시할 챕터가 없습니다</h3>
        <p>먼저 generated JSON을 동기화한 뒤 다시 열어 주세요.</p>
      </div>
    `;
    return;
  }

  const headingLinks = [
    {
      id: "overview",
      title: "개요",
      depth: 2,
    },
    ...chapter.headings.map((heading) => ({
      id: heading.id,
      title: stripGuideDots(heading.title),
      depth: heading.depth,
    })),
  ];

  elements.readerPanel.innerHTML = `
    <article class="reader-article-shell">
      <header class="reader-heading">
        <p class="panel-kicker">${escapeHtml(stripGuideDots(chapter.partTitle))}</p>
        <h3>${escapeHtml(stripGuideDots(chapter.title))}</h3>
        <p class="reader-summary">${escapeHtml(chapter.summary)}</p>
        <div class="reader-meta-row">
          <span>${escapeHtml(formatPageRange(chapter.pageStart, chapter.pageEnd))}</span>
          <span>pageCode ${escapeHtml(chapter.pageCode || "미상")}</span>
          <span>built ${escapeHtml(formatDateTime(state.documentData.meta.builtAt))}</span>
        </div>
      </header>
      <nav class="section-nav" aria-label="현재 장 섹션 이동">
        ${headingLinks
          .map(
            (heading) => `
              <button
                type="button"
                class="section-jump ${state.activeSectionId === heading.id ? "is-active" : ""}"
                data-section-id="${escapeHtml(heading.id)}"
                data-chapter-id="${escapeHtml(chapter.id)}"
              >
                ${escapeHtml(heading.title)}
              </button>
            `
          )
          .join("")}
      </nav>
      <div class="reader-article">${chapter.html}</div>
    </article>
  `;

  const article = elements.readerPanel.querySelector(".reader-article");
  if (!article) {
    return;
  }

  const targetId = state.activeSectionId || "overview";
  const target = article.querySelector(`#${CSS.escape(targetId)}`);
  if (target) {
    target.classList.add("is-target");
    if (state.pendingScrollTarget) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }
  state.pendingScrollTarget = "";
}

function renderUtility() {
  const currentChapter = getCurrentChapter();
  const currentChapterEntries = getCurrentChapterEntries();
  const searchResults = getSearchResults();
  const categoryCounts = getCategoryCounts();
  const categoryEntries = getCategoryEntries();
  const isSearching = Boolean(state.query);

  elements.utilityPanel.innerHTML = `
    <section class="utility-block">
      <div class="utility-title-row">
        <h3>${isSearching ? "검색 결과" : "현재 장 바로가기"}</h3>
        <span class="utility-count">${isSearching ? `${searchResults.length}건` : `${currentChapterEntries.length}개`}</span>
      </div>
      <div class="result-list">
        ${
          isSearching
            ? searchResults
                .map(
                  (entry) => `
                    <button
                      type="button"
                      class="result-card"
                      data-chapter-id="${escapeHtml(entry.chapterSlug)}"
                      data-section-id="${escapeHtml(entry.sectionId)}"
                    >
                      <span class="result-kicker">${escapeHtml(stripGuideDots(entry.partTitle))}</span>
                      <strong>${escapeHtml(stripGuideDots(entry.sectionTitle))}</strong>
                      <span>${escapeHtml(stripGuideDots(entry.chapterTitle))}</span>
                      <p>${escapeHtml(entry.excerpt)}</p>
                      <span class="result-meta">${escapeHtml(
                        formatPageRange(entry.pageStart, entry.pageEnd)
                      )}</span>
                    </button>
                  `
                )
                .join("")
            : currentChapterEntries
                .slice(0, 24)
                .map(
                  (entry) => `
                    <button
                      type="button"
                      class="result-card compact"
                      data-chapter-id="${escapeHtml(currentChapter?.id || entry.chapterSlug)}"
                      data-section-id="${escapeHtml(entry.sectionId)}"
                    >
                      <strong>${escapeHtml(stripGuideDots(entry.sectionTitle))}</strong>
                      <span class="result-meta">${escapeHtml(
                        formatPageRange(entry.pageStart, entry.pageEnd)
                      )}</span>
                    </button>
                  `
                )
                .join("")
        }
      </div>
      ${
        isSearching && searchResults.length === 0
          ? `<p class="helper-copy">검색 결과가 없습니다. 다른 장 제목이나 본문 일부를 시도해 보세요.</p>`
          : ""
      }
    </section>

    <section class="utility-block">
      <div class="utility-title-row">
        <h3>중요 정보 탐색</h3>
        <span class="utility-count">${state.activeCategory ? escapeHtml(CATEGORY_LABELS[state.activeCategory] || state.activeCategory) : "태그 선택"}</span>
      </div>
      <div class="chip-grid">
        ${categoryCounts
          .map(
            ([category, count]) => `
              <button
                type="button"
                class="filter-chip ${state.activeCategory === category ? "is-active" : ""}"
                data-category="${escapeHtml(category)}"
              >
                ${escapeHtml(CATEGORY_LABELS[category] || category)}
                <span>${escapeHtml(String(count))}</span>
              </button>
            `
          )
          .join("")}
      </div>
      ${
        state.activeCategory
          ? `
            <div class="result-list">
              ${categoryEntries
                .map(
                  (entry) => `
                    <button
                      type="button"
                      class="result-card"
                      data-chapter-id="${escapeHtml(entry.id.includes("-overview") ? entry.id : findChapterIdBySection(entry.id))}"
                      data-section-id="${escapeHtml(entry.id)}"
                    >
                      <span class="result-kicker">${escapeHtml(stripGuideDots(entry.partTitle))}</span>
                      <strong>${escapeHtml(stripGuideDots(entry.title))}</strong>
                      <span>${escapeHtml(stripGuideDots(entry.chapterTitle))}</span>
                      <p>${escapeHtml(entry.excerpt)}</p>
                      <span class="result-meta">${escapeHtml(
                        formatPageRange(entry.pageStart, entry.pageEnd)
                      )}</span>
                    </button>
                  `
                )
                .join("")}
            </div>
          `
          : `<p class="helper-copy">탐색 태그를 누르면 관련 섹션을 빠르게 모아볼 수 있습니다.</p>`
      }
    </section>
  `;
}

function findChapterIdBySection(sectionId) {
  const matchingEntry = state.searchIndex.find((entry) => entry.sectionId === sectionId);
  return matchingEntry?.chapterSlug || state.currentChapterId || "";
}

function render() {
  renderHeroMeta();
  renderToc();
  renderReader();
  renderUtility();
}

function renderFatal(error) {
  const message = error instanceof Error ? error.message : String(error);
  elements.heroMeta.innerHTML = "";
  elements.tocPanel.innerHTML = "";
  elements.utilityPanel.innerHTML = "";
  elements.readerPanel.innerHTML = `
    <div class="empty-state error-state">
      <h3>리더 데이터를 불러오지 못했습니다</h3>
      <p>${escapeHtml(message)}</p>
      <p><code>npm run web:prepare</code> 후 <code>http://localhost:4317</code>에서 다시 확인해 주세요.</p>
    </div>
  `;
}

async function fetchJson(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`${url.pathname} 응답 실패 (${response.status})`);
  }
  return response.json();
}

async function loadApp() {
  try {
    const [manifest, documentData, searchIndex, explorationIndex] = await Promise.all([
      fetchJson(GENERATED_FILES.manifest),
      fetchJson(GENERATED_FILES.documentData),
      fetchJson(GENERATED_FILES.searchIndex),
      fetchJson(GENERATED_FILES.explorationIndex),
    ]);

    state.manifest = manifest;
    state.documentData = documentData;
    state.searchIndex = searchIndex;
    state.explorationIndex = explorationIndex;
    state.currentChapterId = documentData.chapters[0]?.id ?? null;
    applyHashSelection();
    render();
  } catch (error) {
    renderFatal(error);
  }
}

elements.searchInput.addEventListener("input", (event) => {
  state.query = event.target.value.trim();
  renderUtility();
});

elements.searchReset.addEventListener("click", () => {
  state.query = "";
  state.activeCategory = "";
  elements.searchInput.value = "";
  renderUtility();
});

elements.tocPanel.addEventListener("click", (event) => {
  const button = event.target.closest("[data-chapter-id]");
  if (!button) {
    return;
  }
  selectLocation(button.dataset.chapterId, "overview", false);
});

elements.readerPanel.addEventListener("click", (event) => {
  const button = event.target.closest("[data-section-id][data-chapter-id]");
  if (!button) {
    return;
  }
  selectLocation(button.dataset.chapterId, button.dataset.sectionId);
});

elements.utilityPanel.addEventListener("click", (event) => {
  const categoryButton = event.target.closest("[data-category]");
  if (categoryButton) {
    state.activeCategory =
      state.activeCategory === categoryButton.dataset.category ? "" : categoryButton.dataset.category;
    renderUtility();
    return;
  }

  const locationButton = event.target.closest("[data-chapter-id][data-section-id]");
  if (!locationButton) {
    return;
  }
  selectLocation(locationButton.dataset.chapterId, locationButton.dataset.sectionId);
});

window.addEventListener("hashchange", () => {
  if (!state.documentData) {
    return;
  }
  applyHashSelection();
  render();
});

loadApp();
