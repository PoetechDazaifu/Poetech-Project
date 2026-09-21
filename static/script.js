const state = { tag: "", location: "" };
let wordcloudObjectUrl = null;

const results = document.getElementById("results");
const loading = document.getElementById("loading");
const wordcloud = document.getElementById("wordcloud");
const searchInput = document.getElementById("search-input");
const sourceSelect = document.getElementById("source-select");

function filters(page = 1) {
  return {
    query: searchInput.value.trim(),
    tag: state.tag,
    source: sourceSelect.value,
    location: state.location,
    page,
  };
}

async function postJson(url, body) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({}));
    throw new Error(payload.error || "リクエストに失敗しました。");
  }
  return response;
}

function setLoading(isLoading) {
  loading.classList.toggle("d-none", !isLoading);
  loading.setAttribute("aria-hidden", String(!isLoading));
}

function clearResults() {
  results.replaceChildren();
}

function renderMessage(message, className = "") {
  clearResults();
  const paragraph = document.createElement("p");
  paragraph.className = className;
  paragraph.textContent = message;
  results.appendChild(paragraph);
}

function renderPoems(poems, insertBefore = null) {
  const fragment = document.createDocumentFragment();
  poems.forEach((poem) => {
    const item = document.createElement("article");
    item.className = "result-item";
    const poemText = document.createElement("p");
    const strong = document.createElement("strong");
    strong.textContent = poem["句"];
    poemText.appendChild(strong);
    const metadata = document.createElement("p");
    const tags = Array.isArray(poem["AIタグ"]) ? poem["AIタグ"] : [poem["AIタグ"]];
    metadata.textContent = `データ元: ${poem["データ元"]} | 年齢: ${poem["年齢"] || "不明"} | 居住地分類: ${poem["居住地分類"] || "不明"} | AIタグ: ${tags.join(", ")}`;
    item.append(poemText, metadata);
    fragment.appendChild(item);
  });
  if (insertBefore) {
    results.insertBefore(fragment, insertBefore);
  } else {
    results.appendChild(fragment);
  }
}

function setFilterButtonState() {
  document.querySelectorAll("[data-tag]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.tag === state.tag));
  });
  document.querySelectorAll("[data-location]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.location === state.location));
  });
}

function createFilterButton(container, type, facet) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `btn ${type === "tag" ? "tag-button" : "location-button"}`;
  button.dataset[type] = facet.value;
  button.setAttribute("aria-pressed", "false");
  button.textContent = `${facet.value} (${facet.count})`;
  button.addEventListener("click", () => {
    state[type] = state[type] === facet.value ? "" : facet.value;
    setFilterButtonState();
    search();
  });
  container.appendChild(button);
}

async function loadFacets() {
  try {
    const response = await fetch("/facets");
    if (!response.ok) throw new Error("絞り込み候補を取得できませんでした。");
    const payload = await response.json();
    payload.sources.forEach((facet) => {
      const option = document.createElement("option");
      option.value = facet.value;
      option.textContent = `${facet.value} (${facet.count})`;
      sourceSelect.appendChild(option);
    });
    const tagButtons = document.getElementById("tag-buttons");
    const locationButtons = document.getElementById("location-buttons");
    payload.tags.forEach((facet) => createFilterButton(tagButtons, "tag", facet));
    payload.locations.forEach((facet) => createFilterButton(locationButtons, "location", facet));
  } catch (error) {
    renderMessage(error.message, "text-danger");
  }
}

async function updateWordcloud(currentFilters) {
  if (!currentFilters.query && !currentFilters.tag && !currentFilters.source && !currentFilters.location) {
    if (wordcloudObjectUrl) URL.revokeObjectURL(wordcloudObjectUrl);
    wordcloudObjectUrl = null;
    wordcloud.src = wordcloud.dataset.defaultSrc;
    return;
  }
  const response = await postJson("/wordcloud", currentFilters);
  const nextUrl = URL.createObjectURL(await response.blob());
  if (wordcloudObjectUrl) URL.revokeObjectURL(wordcloudObjectUrl);
  wordcloudObjectUrl = nextUrl;
  wordcloud.src = nextUrl;
}

async function loadMore(currentFilters, total, button) {
  button.disabled = true;
  try {
    const response = await postJson("/search", currentFilters);
    const payload = await response.json();
    renderPoems(payload.items, button);
    if (!payload.items.length || payload.page * payload.page_size >= total) {
      button.remove();
      return;
    }
    button.textContent = `もっと見る (残り ${total - payload.page * payload.page_size} 件)`;
    button.onclick = () => loadMore({ ...currentFilters, page: currentFilters.page + 1 }, total, button);
    button.disabled = false;
  } catch (error) {
    button.disabled = false;
    button.textContent = "再試行";
  }
}

async function search() {
  const currentFilters = filters();
  setLoading(true);
  try {
    const response = await postJson("/search", currentFilters);
    const payload = await response.json();
    clearResults();
    if (!payload.items.length) {
      renderMessage("該当する句が見つかりませんでした。");
    } else {
      const count = document.createElement("p");
      count.className = "fw-bold";
      count.textContent = `検索結果: ${payload.total} 件`;
      results.appendChild(count);
      renderPoems(payload.items);
      if (payload.total > payload.items.length) {
        const button = document.createElement("button");
        button.type = "button";
        button.className = "btn btn-outline-secondary w-100 mt-2";
        button.textContent = `もっと見る (残り ${payload.total - payload.items.length} 件)`;
        button.onclick = () => loadMore({ ...currentFilters, page: 2 }, payload.total, button);
        results.appendChild(button);
      }
    }
    await updateWordcloud(currentFilters);
  } catch (error) {
    renderMessage(error.message || "検索中にエラーが発生しました。", "text-danger");
  } finally {
    setLoading(false);
  }
}

document.getElementById("search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  search();
});

document.getElementById("clear-button").addEventListener("click", () => {
  state.tag = "";
  state.location = "";
  searchInput.value = "";
  sourceSelect.value = "";
  setFilterButtonState();
  clearResults();
  if (wordcloudObjectUrl) URL.revokeObjectURL(wordcloudObjectUrl);
  wordcloudObjectUrl = null;
  wordcloud.src = wordcloud.dataset.defaultSrc;
});

document.getElementById("show-all-button").addEventListener("click", () => {
  state.tag = "";
  state.location = "";
  searchInput.value = "";
  sourceSelect.value = "";
  setFilterButtonState();
  search();
});

loadFacets();
