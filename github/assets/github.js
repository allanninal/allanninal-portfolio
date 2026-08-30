/* Field notes — code tabs, copy, and a small syntax highlighter.
   No external dependencies so the pages stay self contained and fast. */
(function () {
  "use strict";

  function esc(s) {
    return s.replace(/[&<>]/g, function (c) {
      return c === "&" ? "&amp;" : c === "<" ? "&lt;" : "&gt;";
    });
  }

  var PY_KW = "def class return if elif else for while in not and or import from as with try except finally raise pass continue break lambda yield global nonlocal assert del is None True False async await print";
  var JS_KW = "const let var function return if else for while do switch case break continue new class extends super this typeof instanceof in of try catch finally throw await async yield import from export default delete void null undefined true false";

  function wordRe(list) {
    return new RegExp("^(?:" + list.trim().split(/\s+/).join("|") + ")\\b");
  }

  function highlight(code, lang) {
    var isPy = lang === "python";
    var kwRe = wordRe(isPy ? PY_KW : JS_KW);
    var comRe = isPy ? /^#[^\n]*/ : /^(?:\/\/[^\n]*|\/\*[\s\S]*?\*\/)/;
    var strRe = /^(?:'(?:\\.|[^'\\])*'|"(?:\\.|[^"\\])*"|`(?:\\.|[^`\\])*`)/;
    var numRe = /^\b\d[\d_]*\.?\d*\b/;
    var fnRe = /^[A-Za-z_]\w*(?=\s*\()/;
    var idRe = /^[A-Za-z_]\w*/;
    var out = "";
    var i = 0;
    while (i < code.length) {
      var rest = code.slice(i), m;
      if ((m = comRe.exec(rest))) { out += '<span class="tok-com">' + esc(m[0]) + "</span>"; }
      else if ((m = strRe.exec(rest))) { out += '<span class="tok-str">' + esc(m[0]) + "</span>"; }
      else if ((m = numRe.exec(rest))) { out += '<span class="tok-num">' + esc(m[0]) + "</span>"; }
      else if ((m = kwRe.exec(rest))) { out += '<span class="tok-kw">' + esc(m[0]) + "</span>"; }
      else if ((m = fnRe.exec(rest))) { out += '<span class="tok-fn">' + esc(m[0]) + "</span>"; }
      else if ((m = idRe.exec(rest))) { out += esc(m[0]); }
      else { out += esc(rest[0]); m = [rest[0]]; }
      i += m[0].length;
    }
    return out;
  }

  function paint() {
    var blocks = document.querySelectorAll("pre > code[class*='language-']");
    blocks.forEach(function (el) {
      if (el.dataset.painted) return;
      var lang = /language-(python)/.test(el.className) ? "python" : "javascript";
      el.innerHTML = highlight(el.textContent, lang);
      el.dataset.painted = "1";
    });
  }

  function wireTabs() {
    document.querySelectorAll("[data-code]").forEach(function (block) {
      var tabs = block.querySelectorAll(".code-tab");
      var panes = block.querySelectorAll(".code-pane");
      tabs.forEach(function (tab) {
        tab.addEventListener("click", function () {
          var lang = tab.dataset.lang;
          tabs.forEach(function (t) { t.setAttribute("aria-selected", String(t.dataset.lang === lang)); });
          panes.forEach(function (p) { p.setAttribute("data-active", String(p.dataset.lang === lang)); });
        });
      });
      var copy = block.querySelector(".code-block__copy");
      if (copy) {
        copy.addEventListener("click", function () {
          var active = block.querySelector('.code-pane[data-active="true"] code');
          if (!active) return;
          navigator.clipboard.writeText(active.textContent).then(function () {
            var old = copy.textContent;
            copy.textContent = "Copied";
            setTimeout(function () { copy.textContent = old; }, 1400);
          });
        });
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", function () { paint(); wireTabs(); });
  } else { paint(); wireTabs(); }
})();
