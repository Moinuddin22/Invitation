/* Shared invitation behaviour: intro, stars, scroll reveal, countdown, RSVP UX.
   Theme-agnostic - themes opt in via markup (#intro, [data-stars], .reveal, #countdown). */
(() => {
  "use strict";
  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const $ = (sel, root = document) => root.querySelector(sel);

  /* ---------- Intro overlay ---------- */
  function initIntro() {
    const intro = $("#intro");
    const btn = $("#open-invite");
    if (!intro || !btn) return;

    document.body.classList.add("locked");
    btn.focus();

    btn.addEventListener("click", () => {
      intro.classList.add("opening");
      const finish = () => {
        intro.classList.add("gone");
        document.body.classList.remove("locked");
        $("#main")?.focus({ preventScroll: true });
      };
      if (reducedMotion) return finish();
      // Wait for whatever exit transition the theme defined.
      intro.addEventListener("transitionend", (e) => e.target === intro && finish(), { once: true });
      setTimeout(finish, 1500); // safety net if no transition fires
    });
  }

  /* ---------- Twinkling stars (only where a theme asks) ---------- */
  function initStars() {
    const host = $("[data-stars]");
    if (!host || reducedMotion) return;
    const count = Number(host.dataset.stars) || 30;
    const frag = document.createDocumentFragment();
    for (let i = 0; i < count; i++) {
      const s = document.createElement("span");
      s.className = "star";
      s.style.left = `${Math.random() * 100}%`;
      s.style.top = `${Math.random() * 65}%`;
      s.style.animationDelay = `${-Math.random() * 3.5}s`;
      frag.appendChild(s);
    }
    host.appendChild(frag);
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
      { threshold: 0.12 }
    );
    els.forEach((el) => io.observe(el));
  }

  /* ---------- Countdown ---------- */
  function initCountdown() {
    const root = $("#countdown");
    if (!root) return;
    const target = new Date(root.dataset.target).getTime();
    const units = { days: 86400000, hours: 3600000, minutes: 60000, seconds: 1000 };
    const els = Object.fromEntries(
      Object.keys(units).map((u) => [u, root.querySelector(`[data-unit="${u}"]`)])
    );
    const tick = () => {
      let diff = Math.max(0, target - Date.now());
      for (const [unit, ms] of Object.entries(units)) {
        const val = Math.floor(diff / ms);
        diff -= val * ms;
        els[unit].textContent = String(val).padStart(2, "0");
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
      if (e.target.name === "attending" && guestWrap) guestWrap.hidden = e.target.value === "no";
    });

    document.body.addEventListener("htmx:afterRequest", (e) => {
      if (e.detail.elt === form && e.detail.xhr.status === 200) form.remove();
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
    initStars();
    initReveal();
    initCountdown();
    initRsvp();
  });
})();
