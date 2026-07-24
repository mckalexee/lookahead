/* Lookahead client runtime: live countdowns, live event state, next-refresh
   date, and scroll reveal. Recomputes from the viewer's local clock on load
   and every 60 seconds, so the page stays correct between weekly rebuilds. */

(function () {
  "use strict";

  document.documentElement.classList.add("js");

  var MS_DAY = 86400000;

  function localMidnight(d) {
    return new Date(d.getFullYear(), d.getMonth(), d.getDate());
  }

  /* Days from today (viewer-local) to a YYYY-MM-DD date. 0 = today. */
  function daysUntil(iso) {
    var p = iso.split("-");
    var target = new Date(+p[0], +p[1] - 1, +p[2]);
    return Math.round((target - localMidnight(new Date())) / MS_DAY);
  }

  function setState(el, state) {
    el.classList.remove("state-active", "state-upcoming", "state-ended");
    el.classList.add("state-" + state);
  }

  function updateEvents() {
    var events = document.querySelectorAll(".event[data-start], .event[data-end]");
    for (var i = 0; i < events.length; i++) {
      var ev = events[i];
      var start = ev.getAttribute("data-start");
      var end = ev.getAttribute("data-end");
      var count = ev.querySelector("[data-countdown]");
      var state, text;

      if (start && daysUntil(start) > 0) {
        state = "upcoming";
        var ds = daysUntil(start);
        text = ds === 1 ? "in 1d" : "in " + ds + "d";
      } else if (end && daysUntil(end) < 0) {
        state = "ended";
        text = "ended";
      } else {
        state = "active";
        if (end) {
          var de = daysUntil(end);
          text = de === 0 ? "ends today" : de === 1 ? "1d left" : de + "d left";
        } else {
          text = "now";
        }
      }

      setState(ev, state);
      if (count) count.textContent = text;
    }
  }

  function updateNeeds() {
    var cards = document.querySelectorAll(".needs-card[data-deadline]");
    for (var i = 0; i < cards.length; i++) {
      var card = cards[i];
      var d = daysUntil(card.getAttribute("data-deadline"));
      var count = card.querySelector("[data-countdown]");
      if (count) count.textContent = d < 0 ? "past" : d === 0 ? "today" : d + "d";
      card.classList.toggle("is-past", d < 0);
    }
  }

  function updateNextRefresh() {
    var el = document.querySelector("[data-next-refresh]");
    if (!el) return;
    var now = new Date();
    var add = (8 - now.getDay()) % 7 || 7; /* next Monday, never today */
    var next = new Date(now.getFullYear(), now.getMonth(), now.getDate() + add);
    el.textContent = next.toLocaleDateString("en-US", {
      weekday: "short",
      month: "short",
      day: "numeric"
    });
  }

  function tick() {
    updateEvents();
    updateNeeds();
    updateNextRefresh();
  }

  tick();
  setInterval(tick, 60000);

  /* Game filter tabs. State lives in the URL hash (#pokemon-go) so a
     filtered view survives reload and can be linked. "Needs you" and the
     changelog always stay visible; only game sections filter. */
  var tabs = document.querySelectorAll(".game-tabs .tab");
  var games = document.querySelectorAll(".game[data-game]");

  function applyFilter() {
    if (!tabs.length) return;
    var hash = location.hash.replace("#", "") || "all";
    var known = false;
    for (var i = 0; i < tabs.length; i++) {
      if (tabs[i].getAttribute("data-tab") === hash) known = true;
    }
    if (!known) hash = "all";
    for (var i = 0; i < tabs.length; i++) {
      var on = tabs[i].getAttribute("data-tab") === hash;
      tabs[i].classList.toggle("is-active", on);
      if (on) tabs[i].setAttribute("aria-current", "true");
      else tabs[i].removeAttribute("aria-current");
    }
    for (var i = 0; i < games.length; i++) {
      var show = hash === "all" || games[i].getAttribute("data-game") === hash;
      games[i].classList.toggle("is-hidden", !show);
      if (show) games[i].classList.add("revealed");
    }
  }

  window.addEventListener("hashchange", applyFilter);
  applyFilter();

  /* Clicking a game header focuses that game. The All tab is the way back. */
  if (tabs.length) {
    for (var i = 0; i < games.length; i++) {
      (function (section) {
        var head = section.querySelector(".game-head");
        if (!head) return;
        head.addEventListener("click", function (e) {
          if (e.target.closest("a")) return;
          location.hash = section.getAttribute("data-game");
        });
      })(games[i]);
    }
  }

  /* Scroll reveal. Skipped entirely under reduced motion: the CSS also
     neutralizes .reveal there, so content is never left hidden. */
  var reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var targets = document.querySelectorAll(".reveal");

  if (reduced || !("IntersectionObserver" in window)) {
    for (var i = 0; i < targets.length; i++) targets[i].classList.add("revealed");
  } else {
    var io = new IntersectionObserver(
      function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting) {
            entry.target.classList.add("revealed");
            io.unobserve(entry.target);
          }
        });
      },
      { rootMargin: "0px 0px -8% 0px", threshold: 0.05 }
    );
    targets.forEach(function (t) { io.observe(t); });
  }
})();
