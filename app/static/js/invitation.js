/* Invitation interactions: intro, petals, stars, reveal, countdown, RSVP UX.
   Theme-agnostic: themes opt in via data attributes. */
(() => {
  "use strict";
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (sel, root = document) => root.querySelector(sel);

  /* ---------- Palace-door intro ---------- */
  function initIntro() {
    const intro = $("#intro");
    const btn = $("#open-invite");
    if (!intro || !btn) return;

    document.body.classList.add("locked");
    btn.focus();

    btn.addEventListener("click", () => {
      intro.classList.add("opening");
      burstPetals(40);
      const finish = () => {
        intro.classList.add("gone");
        document.body.classList.remove("locked");
        $("#main")?.focus({ preventScroll: true });
      };
      reducedMotion ? finish() : setTimeout(finish, 1600);
    });
  }

  /* ---------- Falling petals ---------- */
  const petalHost = $("#petals");
  const petalKind = document.body.dataset.petals === "jasmine" ? "jasmine" : "";
  function spawnPetal() {
    if (!petalHost || reducedMotion) return;
    const p = document.createElement("span");
    p.className = Math.random() < 0.3 ? "petal gold" : `petal ${petalKind}`;
    p.style.left = `${Math.random() * 100}vw`;
    p.style.setProperty("--drift", `${(Math.random() - 0.5) * 200}px`);
    p.style.animationDuration = `${6 + Math.random() * 6}s`;
    petalHost.appendChild(p);
    p.addEventListener("animationend", () => p.remove());
  }
  function burstPetals(n) {
    for (let i = 0; i < n; i++) setTimeout(spawnPetal, i * 60);
  }
  function initPetals() {
    if (reducedMotion) return;
    const isSmall = window.innerWidth < 640;
    setInterval(spawnPetal, isSmall ? 1400 : 800);
  }

  /* ---------- Twinkling stars (only where a theme asks for them) ---------- */
  function initStars() {
    const host = $("[data-stars]");
    if (!host) return;
    const count = Number(host.dataset.stars) || 30;
    for (let i = 0; i < count; i++) {
      const s = document.createElement("span");
      s.className = "star";
      s.style.left = `${Math.random() * 100}%`;
      s.style.top = `${Math.random() * 70}%`;
      s.style.animationDelay = `${-Math.random() * 3}s`;
      host.appendChild(s);
    }
  }

  /* ---------- Scroll reveal ---------- */
  function initReveal() {
    const els = document.querySelectorAll(".reveal");
    if (!("IntersectionObserver" in window) || reducedMotion) {
      els.forEach((el) => el.classList.add("visible"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) =>
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("visible");
            io.unobserve(e.target);
          }
        }),
      { threshold: 0.15 }
    );
    els.forEach((el) => io.observe(el));
  }

  /* ---------- Countdown ---------- */
  function initCountdown() {
    const root = $("#countdown");
    if (!root) return;
    const target = new Date(root.dataset.target).getTime();
    const units = {
      days: 86400000, hours: 3600000, minutes: 60000, seconds: 1000,
    };
    const tick = () => {
      let diff = Math.max(0, target - Date.now());
      for (const [unit, ms] of Object.entries(units)) {
        const val = Math.floor(diff / ms);
        diff -= val * ms;
        const el = root.querySelector(`[data-unit="${unit}"]`);
        if (el) el.textContent = String(val).padStart(2, "0");
      }
    };
    tick();
    setInterval(tick, 1000);
  }

  /* ---------- RSVP UX ---------- */
  function initRsvp() {
    const form = $("#rsvp-area form");
    const guestWrap = $("#guest-wrap");
    if (!form) return;

    form.addEventListener("change", (e) => {
      if (e.target.name === "attending" && guestWrap) {
        guestWrap.hidden = e.target.value === "no";
      }
    });

    document.body.addEventListener("htmx:afterRequest", (e) => {
      if (e.detail.elt === form && e.detail.xhr.status === 200) {
        form.remove();
        burstPetals(30);
      }
    });

    // htmx 2 doesn't swap 4xx responses by default; we want validation errors shown.
    document.body.addEventListener("htmx:beforeSwap", (e) => {
      if (e.detail.xhr.status === 422) {
        e.detail.shouldSwap = true;
        e.detail.isError = false;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", () => {
    $("#main")?.setAttribute("tabindex", "-1");
    initIntro();
    initPetals();
    initStars();
    initReveal();
    initCountdown();
    initRsvp();
  });
})();
