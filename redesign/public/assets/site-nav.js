/* allanninal.dev — unified site navigation behaviour.
   No dependencies; safe to load on any page. Everything degrades to plain
   links if JavaScript never runs: the drawer and panels start hidden, so the
   only cost is that the grouped sections are unreachable — which is why every
   grouped destination also has a top-level link. */
(function () {
  'use strict';

  var root = document.querySelector('.anx-root');
  if (!root) return;

  var burger = root.querySelector('.anx-burger');
  var drawer = root.querySelector('.anx-drawer');

  function setExpanded(btn, open) {
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    var panel = document.getElementById(btn.getAttribute('aria-controls'));
    if (panel) panel.hidden = !open;
  }

  /* ── Desktop dropdowns ──────────────────────────────────────────────── */
  var menuButtons = [].slice.call(root.querySelectorAll('[data-anx-menu]'));

  function closeMenus(except) {
    menuButtons.forEach(function (btn) {
      if (btn !== except) setExpanded(btn, false);
    });
  }

  menuButtons.forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      e.preventDefault();
      var open = btn.getAttribute('aria-expanded') === 'true';
      closeMenus(btn);
      setExpanded(btn, !open);
    });
  });

  document.addEventListener('click', function (e) {
    if (!root.contains(e.target)) closeMenus();
    else if (!e.target.closest || !e.target.closest('.anx-menu')) closeMenus();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape' && e.key !== 'Esc') return;
    var openMenu = menuButtons.filter(function (b) {
      return b.getAttribute('aria-expanded') === 'true';
    })[0];
    if (openMenu) {
      setExpanded(openMenu, false);
      openMenu.focus();
      return;
    }
    if (burger && burger.getAttribute('aria-expanded') === 'true') {
      setExpanded(burger, false);
      burger.focus();
    }
  });

  /* ── Mobile drawer ──────────────────────────────────────────────────── */
  if (burger && drawer) {
    burger.addEventListener('click', function () {
      setExpanded(burger, burger.getAttribute('aria-expanded') !== 'true');
    });

    /* A drawer left open across the 1024px breakpoint would reappear the next
       time the viewport narrowed, out of sync with the button. */
    var wide = window.matchMedia('(min-width: 1024px)');
    var onChange = function (e) {
      if (e.matches) setExpanded(burger, false);
    };
    if (wide.addEventListener) wide.addEventListener('change', onChange);
    else if (wide.addListener) wide.addListener(onChange);

    /* Same-page anchors do not navigate, so the drawer has to close itself. */
    drawer.addEventListener('click', function (e) {
      var link = e.target.closest && e.target.closest('a[href]');
      if (link && link.getAttribute('href').indexOf('#') === 0) {
        setExpanded(burger, false);
      }
    });
  }

  /* ── Drawer accordions ──────────────────────────────────────────────── */
  [].slice.call(root.querySelectorAll('[data-anx-acc]')).forEach(function (btn) {
    btn.addEventListener('click', function () {
      setExpanded(btn, btn.getAttribute('aria-expanded') !== 'true');
    });
  });
})();
