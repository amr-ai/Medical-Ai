(() => {
  const prefersReducedMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)")?.matches;

  function qs(sel, root = document) {
    return root.querySelector(sel);
  }
  function qsa(sel, root = document) {
    return Array.from(root.querySelectorAll(sel));
  }

  // Sticky glass topbar state
  const topbar = document.querySelector("[data-topbar]");
  const onScroll = () => {
    if (!topbar) return;
    topbar.classList.toggle("is-scrolled", window.scrollY > 8);
  };
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // Smooth scroll to anchors
  qsa("[data-scrollto]").forEach((a) => {
    a.addEventListener("click", (e) => {
      const href = a.getAttribute("href");
      if (!href || !href.startsWith("#")) return;
      const el = document.getElementById(href.slice(1));
      if (!el) return;
      e.preventDefault();
      el.scrollIntoView({ behavior: prefersReducedMotion ? "auto" : "smooth", block: "start" });
    });
  });

  // Scroll reveal
  const revealEls = qsa(".reveal");
  if (revealEls.length) {
    const io = new IntersectionObserver(
      (entries) => {
        for (const ent of entries) {
          if (ent.isIntersecting) {
            ent.target.classList.add("is-visible");
            io.unobserve(ent.target);
          }
        }
      },
      { threshold: 0.12 }
    );
    revealEls.forEach((el) => io.observe(el));
  }

  // Segmented control + conditional sections
  const segmented = qs("[data-segmented]");
  const inputMethodField = qs("input[name='input_method']");
  const sectionUpload = qs("[data-section='upload']");
  const sectionManual = qs("[data-section='manual']");
  const fileInput = qs("input[type='file'][name='file']");
  const manualTypeWrap = qs("[data-manual-type]");
  const reportTypeField = qs("input[name='report_type']");
  const manualGroups = qsa("[data-manual-group]");
  const manualInputs = qsa("[data-manual-input]");

  function setMethod(method) {
    if (inputMethodField) inputMethodField.value = method;

    qsa("[data-segment]", segmented || document).forEach((btn) => {
      btn.classList.toggle("is-active", btn.getAttribute("data-segment") === method);
    });

    if (sectionUpload) {
      sectionUpload.hidden = method !== "upload";
      sectionUpload.style.display = method === "upload" ? "" : "none";
    }
    if (sectionManual) {
      sectionManual.hidden = method !== "manual";
      sectionManual.style.display = method === "manual" ? "" : "none";
    }

    if (fileInput) fileInput.required = method === "upload";
    // Manual fields are required only when manual mode is selected.
    if (method !== "manual") {
      manualInputs.forEach((el) => {
        el.required = false;
      });
      if (reportTypeField) reportTypeField.required = false;
    } else {
      if (reportTypeField) reportTypeField.required = true;
      const activeType = reportTypeField?.value || "cbc";
      manualInputs.forEach((el) => {
        el.required = el.getAttribute("data-manual-input") === activeType;
      });
    }
  }

  if (segmented && inputMethodField && sectionUpload && sectionManual) {
    qsa("[data-segment]", segmented).forEach((btn) => {
      btn.addEventListener("click", () => setMethod(btn.getAttribute("data-segment")));
    });
    setMethod(inputMethodField.value || "upload");
  }

  // Manual report type toggle (CBC / CKD / Liver)
  function setManualType(type) {
    if (reportTypeField) reportTypeField.value = type;

    qsa("[data-manual-segment]", manualTypeWrap || document).forEach((btn) => {
      btn.classList.toggle("is-active", btn.getAttribute("data-manual-segment") === type);
    });

    manualGroups.forEach((g) => {
      const active = g.getAttribute("data-manual-group") === type;
      g.hidden = !active;
      g.classList.toggle("is-active", active);
      if (active) {
        g.classList.remove("is-enter");
        // trigger animation
        window.requestAnimationFrame(() => g.classList.add("is-enter"));
      }
    });

    // If manual mode is active, update required flags.
    if (inputMethodField?.value === "manual") {
      manualInputs.forEach((el) => {
        el.required = el.getAttribute("data-manual-input") === type;
      });
      if (reportTypeField) reportTypeField.required = true;
    }
  }

  if (manualTypeWrap && reportTypeField && manualGroups.length) {
    qsa("[data-manual-segment]", manualTypeWrap).forEach((btn) => {
      btn.addEventListener("click", () => setManualType(btn.getAttribute("data-manual-segment")));
    });
    setManualType(reportTypeField.value || "cbc");
  }

  // Dropzone UX
  const dropzone = qs("[data-dropzone]");
  const filePill = qs("[data-filepill]");
  const fileNameEl = qs("[data-filename]");
  const fileMetaEl = qs("[data-filemeta]");
  const fileBtn = qs("[data-filebtn]");

  function prettyBytes(bytes) {
    if (!Number.isFinite(bytes)) return "";
    const units = ["B", "KB", "MB", "GB"];
    let i = 0;
    let val = bytes;
    while (val >= 1024 && i < units.length - 1) {
      val /= 1024;
      i++;
    }
    return `${val.toFixed(val >= 10 || i === 0 ? 0 : 1)} ${units[i]}`;
  }

  function setFilePill(file) {
    if (!filePill || !fileNameEl || !fileMetaEl) return;
    if (!file) {
      filePill.classList.remove("is-visible");
      return;
    }
    fileNameEl.textContent = file.name;
    const ext = (file.name.split(".").pop() || "").toUpperCase();
    fileMetaEl.textContent = `${ext} • ${prettyBytes(file.size)}`;
    filePill.classList.add("is-visible");
  }

  if (fileInput) {
    fileInput.addEventListener("change", () => setFilePill(fileInput.files?.[0] || null));
  }

  if (dropzone && fileInput) {
    if (fileBtn) fileBtn.addEventListener("click", () => fileInput.click());

    const onDragOver = (e) => {
      e.preventDefault();
      dropzone.classList.add("is-dragover");
    };
    const onDragLeave = () => dropzone.classList.remove("is-dragover");
    const onDrop = (e) => {
      e.preventDefault();
      dropzone.classList.remove("is-dragover");
      const file = e.dataTransfer?.files?.[0];
      if (!file) return;
      fileInput.files = e.dataTransfer.files;
      setFilePill(file);
    };
    dropzone.addEventListener("dragover", onDragOver);
    dropzone.addEventListener("dragleave", onDragLeave);
    dropzone.addEventListener("drop", onDrop);
  }

  // Premium loading overlay for analysis submit
  const form = qs("form[data-analyze-form]");
  const overlay = qs("[data-overlay]");
  const steps = qsa("[data-step]");
  let stepIdx = 0;
  let stepTimer = null;

  function startSteps() {
    if (!overlay) return;
    overlay.classList.add("is-visible");
    stepIdx = 0;
    steps.forEach((s) => s.classList.remove("is-active"));
    if (steps[0]) steps[0].classList.add("is-active");

    if (stepTimer) window.clearInterval(stepTimer);
    stepTimer = window.setInterval(() => {
      stepIdx = Math.min(stepIdx + 1, Math.max(steps.length - 1, 0));
      steps.forEach((s, i) => s.classList.toggle("is-active", i === stepIdx));
    }, 1200);
  }

  if (form && overlay) {
    form.addEventListener("submit", () => {
      startSteps();
    });
  }

  // Result confidence progress animation
  const bar = qs("[data-progressbar]");
  if (bar) {
    const pct = Number(bar.getAttribute("data-progressbar")) || 0;
    window.requestAnimationFrame(() => {
      bar.style.width = `${Math.max(0, Math.min(100, pct))}%`;
    });
  }
})();

