/* BG5HLC · 站点交互
   四件事：主题切换、图片放大、通联筛选排序、相册按年筛选。
   没有框架，也没有构建步骤，改完刷新就生效。 */

(() => {
  "use strict";

  const THEME_KEY = "bg5hlc-theme";
  const root = document.documentElement;

  /* ── 日夜切换：自动 → 浅色 → 深色 ─────────────────────── */

  const themeButton = document.getElementById("theme-toggle");
  if (themeButton) {
    const MODES = ["auto", "light", "dark"];
    const media = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
    const labels = {
      auto: themeButton.dataset.labelAuto || "Auto",
      light: themeButton.dataset.labelLight || "Light",
      dark: themeButton.dataset.labelDark || "Dark",
    };

    const effective = (mode) => (mode === "auto" ? (media && media.matches ? "dark" : "light") : mode);

    const paint = (mode) => {
      root.setAttribute("data-theme-mode", mode);
      root.setAttribute("data-theme", effective(mode));
      themeButton.title = labels[mode] || mode;
      const meta = document.querySelector('meta[name="theme-color"]');
      if (meta) meta.setAttribute("content", effective(mode) === "dark" ? "#0f1a14" : "#f6ecd9");
    };

    let mode = root.getAttribute("data-theme-mode");
    if (!MODES.includes(mode)) mode = "auto";
    paint(mode);

    themeButton.addEventListener("click", () => {
      mode = MODES[(MODES.indexOf(mode) + 1) % MODES.length];
      paint(mode);
      try {
        localStorage.setItem(THEME_KEY, mode);
      } catch (error) {
        /* 隐私模式下忽略 */
      }
    });

    // 「自动」模式下跟随系统实时切换
    const onSystemChange = () => {
      if (mode === "auto") paint("auto");
    };
    if (media) {
      if (media.addEventListener) media.addEventListener("change", onSystemChange);
      else if (media.addListener) media.addListener(onSystemChange);
    }
  }

  /* ── 图片放大 ─────────────────────────────────────────── */

  const lightbox = document.getElementById("lightbox");
  if (lightbox) {
    const image = document.getElementById("lightbox-img");
    const caption = document.getElementById("lightbox-cap");
    const closeButton = lightbox.querySelector(".lightbox-close");
    let opener = null;

    const open = (anchor) => {
      opener = anchor;
      image.src = anchor.getAttribute("href") || "";
      const thumb = anchor.querySelector("img");
      image.alt = thumb ? thumb.alt : "";
      caption.textContent = anchor.dataset.caption || "";
      lightbox.hidden = false;
      document.body.classList.add("is-locked");
      closeButton.focus();
    };

    const close = () => {
      lightbox.hidden = true;
      document.body.classList.remove("is-locked");
      image.removeAttribute("src");
      if (opener) {
        opener.focus();
        opener = null;
      }
    };

    document.addEventListener("click", (event) => {
      const anchor = event.target.closest("[data-lightbox]");
      if (anchor) {
        event.preventDefault();
        open(anchor);
        return;
      }
      if (lightbox.hidden) return;
      if (event.target === lightbox || event.target.closest(".lightbox-close")) close();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !lightbox.hidden) close();
    });
  }

  /* ── 通联记录：筛选与排序 ─────────────────────────────── */

  const logTable = document.getElementById("log");
  if (logTable) {
    const rows = Array.from(logTable.querySelectorAll("tbody tr"));
    const search = document.getElementById("qso-search");
    const band = document.getElementById("qso-band");
    const mode = document.getElementById("qso-mode");
    const reset = document.getElementById("qso-reset");
    const count = document.getElementById("qso-count");
    const emptyTip = document.getElementById("log-empty");
    const tools = document.querySelector(".log-tools");
    const template = (tools && tools.dataset.count) || "{n}";

    const applyFilters = () => {
      const query = (search ? search.value : "").trim().toLowerCase();
      const wantBand = band ? band.value : "";
      const wantMode = mode ? mode.value : "";
      let shown = 0;

      for (const row of rows) {
        const haystack = row.dataset.search || "";
        const match =
          (!query || haystack.includes(query)) &&
          (!wantBand || row.dataset.band === wantBand) &&
          (!wantMode || row.dataset.mode === wantMode);
        row.hidden = !match;
        if (match) shown += 1;
      }

      if (count) count.textContent = template.replace("{n}", shown);
      if (emptyTip) emptyTip.hidden = shown !== 0;
    };

    if (search) search.addEventListener("input", applyFilters);
    if (band) band.addEventListener("change", applyFilters);
    if (mode) mode.addEventListener("change", applyFilters);

    if (reset) {
      reset.addEventListener("click", () => {
        if (search) search.value = "";
        if (band) band.value = "";
        if (mode) mode.value = "";
        applyFilters();
        if (search) search.focus();
      });
    }

    applyFilters();

    const headers = Array.from(logTable.querySelectorAll("th[data-key]"));
    const sortRows = (key, direction) => {
      const body = logTable.tBodies[0];
      if (!body) return;
      const factor = direction === "ascending" ? 1 : -1;
      const sorted = rows.slice().sort((a, b) => {
        const left = a.dataset[key] || "";
        const right = b.dataset[key] || "";
        return left.localeCompare(right, "zh-CN", { numeric: true }) * factor;
      });
      const fragment = document.createDocumentFragment();
      sorted.forEach((row) => fragment.appendChild(row));
      body.appendChild(fragment);
    };

    headers.forEach((th) => {
      const button = th.querySelector(".th-btn");
      if (!button) return;
      button.addEventListener("click", () => {
        const direction = th.getAttribute("aria-sort") === "ascending" ? "descending" : "ascending";
        headers.forEach((other) => other.removeAttribute("aria-sort"));
        th.setAttribute("aria-sort", direction);
        sortRows(th.dataset.key, direction);
      });
    });
  }

  /* ── 相册：按年份筛选 ─────────────────────────────────── */

  const yearSelect = document.getElementById("gallery-year");
  if (yearSelect) {
    const groups = Array.from(document.querySelectorAll(".year-group"));
    const count = document.getElementById("gallery-count");
    const tools = document.querySelector(".gallery-tools");
    const template = (tools && tools.dataset.count) || "{n}";

    yearSelect.addEventListener("change", () => {
      const year = yearSelect.value;
      let shown = 0;
      groups.forEach((group) => {
        const match = !year || group.dataset.year === year;
        group.hidden = !match;
        if (match) shown += group.querySelectorAll(".card").length;
      });
      if (count) count.textContent = template.replace("{n}", shown);
    });
  }

  /* ── ASCII 频谱瀑布 ───────────────────────────────────── */

  const waterfallEl = document.getElementById("waterfall");
  if (waterfallEl) {
    const RAMP = " .·:-=+*#%@";
    const PEAKS = [
      [0.16, 0.03, 1.0, 0],
      [0.44, 0.046, 0.85, 1.4],
      [0.74, 0.028, 0.95, 2.6],
      [0.9, 0.055, 0.55, 3.8],
    ];
    const COLS = 42;
    const ROWS = 13;
    const calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

    const makeRow = (moment) => {
      let line = "";
      for (let x = 0; x < COLS; x += 1) {
        const p = x / (COLS - 1);
        let value = 0.04 + Math.random() * 0.07;
        for (const [freq, width, amp, phase] of PEAKS) {
          let distance = Math.abs(p - freq);
          distance = Math.min(distance, 1 - distance);
          value += amp * Math.exp(-(distance * distance) / (2 * width * width)) *
            (0.65 + 0.35 * Math.sin(moment * 0.9 + phase));
        }
        line += RAMP[Math.min(RAMP.length - 1, Math.max(0, Math.floor(value * RAMP.length)))];
      }
      return line;
    };

    const rows = [];
    for (let i = 0; i < ROWS; i += 1) rows.push(makeRow(i * 0.28));

    const paint = () => {
      waterfallEl.innerHTML = rows
        .map((row, index) => {
          const opacity = (0.28 + (0.72 * index) / (ROWS - 1)).toFixed(2);
          return '<span style="opacity:' + opacity + '">' + row + "</span>";
        })
        .join("");
    };

    paint();

    if (!calm) {
      let tick = ROWS;
      setInterval(() => {
        rows.shift();
        rows.push(makeRow(tick * 0.28));
        tick += 1;
        paint();
      }, 130);
    }
  }

  /* ── 滚动揭示（没有 IntersectionObserver 就直接显示） ──── */

  const revealEls = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
  if (revealEls.length) {
    if (!("IntersectionObserver" in window)) {
      revealEls.forEach((el) => el.classList.add("in"));
    } else {
      const io = new IntersectionObserver(
        (entries) => {
          entries.forEach((entry) => {
            if (entry.isIntersecting) {
              entry.target.classList.add("in");
              io.unobserve(entry.target);
            }
          });
        },
        { threshold: 0.08, rootMargin: "0px 0px -40px 0px" }
      );
      revealEls.forEach((el) => io.observe(el));
    }
  }
})();
