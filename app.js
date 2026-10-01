/* Mercado Garmendia — catálogo ligero. Búsqueda local sin servidor. */
(function () {
  "use strict";

  var index = null;

  function norm(s) {
    return String(s || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
  }

  function fmt(n) {
    return "$" + Number(n).toFixed(2);
  }

  function loadIndex() {
    fetch("search-index.json", { headers: { Accept: "application/json" } })
      .then(function (r) { return r.json(); })
      .then(function (d) { index = Array.isArray(d) ? d : []; })
      .catch(function () { index = []; });
  }

  function render(results) {
    var box = document.getElementById("results");
    if (!box) return;
    box.textContent = "";
    if (!results.length) {
      var e = document.createElement("p");
      e.className = "empty";
      e.textContent = "Sin resultados.";
      box.appendChild(e);
      return;
    }
    results.slice(0, 50).forEach(function (it) {
      var a = document.createElement("a");
      a.className = "result";
      a.href = it.url;
      var name = document.createElement("div");
      name.className = "r-name";
      name.textContent = it.n;
      var meta = document.createElement("div");
      meta.className = "r-meta";
      meta.textContent = fmt(it.p) + (it.u ? " / " + it.u : "") + " · " + it.v + " (" + it.l + ")";
      a.appendChild(name);
      a.appendChild(meta);
      box.appendChild(a);
    });
  }

  function search(q) {
    var nq = norm(q);
    if (!nq || !index) { render([]); return; }
    var terms = nq.split(/\s+/).filter(Boolean);
    var results = index.filter(function (it) {
      var hay = norm(it.n + " " + it.v + " " + it.l);
      return terms.every(function (t) { return hay.indexOf(t) !== -1; });
    });
    render(results);
  }

  document.addEventListener("DOMContentLoaded", function () {
    var input = document.getElementById("q");
    if (input) {
      loadIndex();
      input.addEventListener("input", function () { search(input.value); });
    }
    if ("serviceWorker" in navigator) {
      navigator.serviceWorker.register("sw.js").catch(function () {});
    }
  });
})();
