/* BG5HLC · 首页 v2
   两件事：日夜主题切换、ASCII 通联动画。
   通联筛选、SSTV、相册等功能在各自的旧页面里，不在这里。 */

(() => {
  "use strict";

  /* ── 日夜主题 ─────────────────────────────────────────── */

  const root = document.documentElement;
  const themeButton = document.getElementById("theme-toggle");

  if (themeButton) {
    const labels = {
      light: themeButton.dataset.labelLight || "Switch to dark",
      dark: themeButton.dataset.labelDark || "Switch to light",
    };
    const meta = document.querySelector('meta[name="theme-color"]');

    const paint = (theme) => {
      root.setAttribute("data-theme", theme);
      root.setAttribute("data-theme-mode", theme);
      const label = labels[theme] || theme;
      themeButton.setAttribute("aria-label", label);
      if (meta) meta.setAttribute("content", theme === "dark" ? "#111614" : "#f6f4ef");
    };

    paint(root.getAttribute("data-theme") === "dark" ? "dark" : "light");

    themeButton.addEventListener("click", () => {
      const next = root.getAttribute("data-theme") === "dark" ? "light" : "dark";
      paint(next);
      try {
        localStorage.setItem("bg5hlc-theme", next);
      } catch (error) {
        /* 隐私模式下忽略 */
      }
    });
  }

  /* ── ASCII 双人通联动画 ───────────────────────────────── */

  const FRAMES = [
    {
      label: "1/4 · CQ CQ DE BG5HLC K",
      lines: [
        "          .----.      [ IONOSPHERE ]      .----.          ",
        "         (  *   ) ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~(      )         ",
        "     |    '----'                          '----'    |     ",
        "   --|--  )))   CQ CQ CQ DE BG5HLC K              --|--   ",
        "     |  )))                                         |     ",
        "   [===]    O_                                    [===]   ",
        "   |TX |   /|\\  _                                 |RX |   ",
        "  _|___|_  / \\ [Key]                             _|___|_  ",
        "  BG5HLC (Hangzhou)                              JA1KWF   ",
      ],
    },
    {
      label: "2/4 · IONOSPHERE PATH · 7.030 MHz",
      lines: [
        "          .----.      [ IONOSPHERE ]      .----.          ",
        "         (      ) ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~(  *   )         ",
        "     |    '----'      ·-·-  7.030MHz      '----'    |     ",
        "   --|--                                      ((( --|--   ",
        "     |                                          ((( |     ",
        "   [===]    _O                                   ! _O     ",
        "   |RX |   /|\\                                    /|\\     ",
        "  _|___|_  / \\                                    / \\     ",
        "  BG5HLC (Hangzhou)                              JA1KWF   ",
      ],
    },
    {
      label: "3/4 · JA1KWF · RST 599",
      lines: [
        "          .----.      [ IONOSPHERE ]      .----.          ",
        "         (      ) ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~(  *   )         ",
        "     |    '----'                          '----'    |     ",
        "   --|--                 BG5HLC DE JA1KWF 599 ((( --|--   ",
        "     |                                        (((   |     ",
        "   [===]    _O                                   _O       ",
        "   |RX |   /|\\                                _  /|\\      ",
        "  _|___|_  / \\                              [Key]/ \\      ",
        "  BG5HLC (Hangzhou)                              JA1KWF   ",
      ],
    },
    {
      label: "4/4 · QSL CONFIRMED · TU 73",
      lines: [
        "          .----.      [ IONOSPHERE ]      .----.          ",
        "         (  *   ) ~ ~ ~ ~ * 73 * ~ ~ ~ ~ (  *   )         ",
        "     |    '----'                          '----'    |     ",
        "   --|--  )))      QSL CONFIRMED · TU 73!     ((( --|--   ",
        "     |                                              |     ",
        "   [===]   \\O/                                   \\O/      ",
        "   |73!|    |                                     |       ",
        "  _|___|_  / \\                                   / \\      ",
        "  BG5HLC (Hangzhou)                              JA1KWF   ",
      ],
    },
  ];

  const canvas = document.getElementById("ascii-canvas");
  const status = document.getElementById("ascii-status");
  const pauseButton = document.getElementById("ascii-pause");
  const stepButton = document.getElementById("ascii-step");

  if (canvas) {
    const reduceMotion =
      window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const pauseLabel = (pauseButton && pauseButton.dataset.pause) || "Pause";
    const playLabel = (pauseButton && pauseButton.dataset.play) || "Play";

    let index = 0;
    let playing = !reduceMotion;

    const render = () => {
      const frame = FRAMES[index % FRAMES.length];
      canvas.innerHTML = frame.lines
        .map((line) =>
          line
            .replace(/(\)\)\)|\(\(\(|\* 73 \*)/g, '<span class="c-wave">$1</span>')
            .replace(
              /(CQ CQ CQ DE BG5HLC K|BG5HLC DE JA1KWF 599|QSL CONFIRMED · TU 73!)/g,
              '<span class="c-msg">$1</span>'
            )
            .replace(/(\[ IONOSPHERE \])/g, '<span class="c-sky">$1</span>')
            .replace(/(BG5HLC \(Hangzhou\)|JA1KWF)/g, '<span class="c-call">$1</span>')
        )
        .join("\n");
      if (status) status.textContent = frame.label;
    };

    if (pauseButton) {
      pauseButton.textContent = playing ? pauseLabel : playLabel;
      pauseButton.addEventListener("click", () => {
        playing = !playing;
        pauseButton.textContent = playing ? pauseLabel : playLabel;
      });
    }

    if (stepButton) {
      stepButton.addEventListener("click", () => {
        index += 1;
        render();
      });
    }

    render();

    if (!reduceMotion) {
      setInterval(() => {
        if (!playing) return;
        index += 1;
        render();
      }, 1200);
    }
  }

  /* ── QSL 灯箱 ─────────────────────────────────────────── */

  const lightbox = document.getElementById("lightbox-v2");
  if (lightbox) {
    const image = document.getElementById("lightbox-v2-img");
    const caption = document.getElementById("lightbox-v2-cap");
    const closeButton = lightbox.querySelector(".lightbox-v2-close");
    let opener = null;

    const open = (anchor) => {
      opener = anchor;
      image.src = anchor.getAttribute("href") || "";
      const thumb = anchor.querySelector("img");
      image.alt = thumb ? thumb.alt : "";
      if (caption) caption.textContent = anchor.dataset.caption || "";
      lightbox.hidden = false;
      document.documentElement.classList.add("is-locked");
      if (closeButton) closeButton.focus();
    };

    const close = () => {
      lightbox.hidden = true;
      document.documentElement.classList.remove("is-locked");
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
      if (event.target === lightbox || event.target.closest(".lightbox-v2-close")) close();
    });

    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && !lightbox.hidden) close();
    });
  }

  /* ── QSL / SSTV 年份筛选 ───────────────────────────────── */

  const yearSelect = document.getElementById("gallery-year");
  if (yearSelect) {
    const groups = Array.from(document.querySelectorAll(".year-group"));
    const countLabel = document.getElementById("gallery-count");
    const tools = document.querySelector(".filter-bar");
    const template = (tools && tools.dataset.count) || "{n}";

    yearSelect.addEventListener("change", () => {
      const year = yearSelect.value;
      let shown = 0;
      groups.forEach((group) => {
        const match = !year || group.dataset.year === year;
        group.hidden = !match;
        if (match) shown += group.querySelectorAll(".qsl-card, .sstv-card").length;
      });
      if (countLabel) countLabel.textContent = template.replace("{n}", shown);
    });
  }

  /* ── 通联筛选与排序 ───────────────────────────────────── */

  const qsoGrid = document.getElementById("qso-grid");
  if (qsoGrid) {
    const cards = Array.from(qsoGrid.querySelectorAll(".qso-card"));
    const search = document.getElementById("qso-search");
    const band = document.getElementById("qso-band");
    const mode = document.getElementById("qso-mode");
    const sort = document.getElementById("qso-sort");
    const reset = document.getElementById("qso-reset");
    const count = document.getElementById("qso-count");
    const tools = document.querySelector(".filter-bar");
    const template = (tools && tools.dataset.count) || "{n} / {total}";
    const total = cards.length;

    const applyFilters = () => {
      const query = (search ? search.value : "").trim().toLowerCase();
      const wantBand = band ? band.value : "";
      const wantMode = mode ? mode.value : "";
      let shown = 0;

      cards.forEach((card) => {
        const text = card.dataset.search || "";
        const match =
          (!query || text.includes(query)) &&
          (!wantBand || card.dataset.band === wantBand) &&
          (!wantMode || card.dataset.mode === wantMode);
        card.hidden = !match;
        if (match) shown += 1;
      });

      if (count) {
        count.textContent = template
          .replace("{n}", shown)
          .replace("{total}", total);
      }
    };

    const sortCards = () => {
      if (!sort) return;
      const value = sort.value || "date-desc";
      const sorted = cards.slice().sort((a, b) => {
        if (value === "call") {
          return (a.dataset.call || "").localeCompare(b.dataset.call || "", "zh-CN", {
            numeric: true,
          });
        }
        const left = `${a.dataset.date || ""} ${a.dataset.time || ""}`;
        const right = `${b.dataset.date || ""} ${b.dataset.time || ""}`;
        const result = left.localeCompare(right, "zh-CN", { numeric: true });
        return value === "date-asc" ? result : -result;
      });
      sorted.forEach((card) => qsoGrid.appendChild(card));
      applyFilters();
    };

    if (search) search.addEventListener("input", applyFilters);
    if (band) band.addEventListener("change", applyFilters);
    if (mode) mode.addEventListener("change", applyFilters);
    if (sort) sort.addEventListener("change", sortCards);

    if (reset) {
      reset.addEventListener("click", () => {
        if (search) search.value = "";
        if (band) band.value = "";
        if (mode) mode.value = "";
        if (sort) sort.value = "date-desc";
        sortCards();
      });
    }

    applyFilters();
  }
})();
