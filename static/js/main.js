/**
 * SkillSwap — vanilla JS (mobile nav, dropdowns)
 */
(function () {
  function ready(fn) {
    if (document.readyState !== "loading") {
      fn();
    } else {
      document.addEventListener("DOMContentLoaded", fn);
    }
  }

  ready(function () {
    document.querySelectorAll("[data-nav-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        var id = btn.getAttribute("data-nav-toggle");
        var panel = id ? document.getElementById(id) : null;
        if (panel) {
          panel.classList.toggle("is-open");
        }
      });
    });

    document.querySelectorAll("[data-dropdown-toggle]").forEach(function (btn) {
      btn.addEventListener("click", function (e) {
        e.preventDefault();
        e.stopPropagation();
        var id = btn.getAttribute("data-dropdown-toggle");
        var menu = id ? document.getElementById(id) : null;
        if (!menu) return;
        document.querySelectorAll(".ss-dropdown-menu.is-open").forEach(function (m) {
          if (m !== menu) m.classList.remove("is-open");
        });
        menu.classList.toggle("is-open");
      });
    });

    document.addEventListener("click", function () {
      document.querySelectorAll(".ss-dropdown-menu.is-open").forEach(function (m) {
        m.classList.remove("is-open");
      });
    });

    document.querySelectorAll(".ss-dropdown-menu").forEach(function (menu) {
      menu.addEventListener("click", function (e) {
        e.stopPropagation();
      });
    });

    /* Admin / generic tab panels: [data-tab-toggle] and [data-tab-panel] */
    function setActiveTab(tabId) {
      document.querySelectorAll("[data-tab-panel]").forEach(function (panel) {
        var show = panel.getAttribute("data-tab-panel") === tabId;
        panel.classList.toggle("hidden", !show);
      });
      document.querySelectorAll("[data-tab-toggle]").forEach(function (b) {
        var active = b.getAttribute("data-tab-toggle") === tabId;
        b.classList.toggle("ss-tab-active", active);
      });
    }

    var tabButtons = document.querySelectorAll("[data-tab-toggle]");
    if (tabButtons.length) {
      var first = tabButtons[0].getAttribute("data-tab-toggle");
      setActiveTab(first);
      tabButtons.forEach(function (btn) {
        btn.addEventListener("click", function (e) {
          e.preventDefault();
          var id = btn.getAttribute("data-tab-toggle");
          if (id) setActiveTab(id);
        });
      });
    }
  });
})();
