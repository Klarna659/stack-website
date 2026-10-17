(function () {
  "use strict";
  var M = window.ToolsMath;
  var $ = function (id) { return document.getElementById(id); };
  var SVG_NS = "http://www.w3.org/2000/svg";

  function el(tag, attrs) {
    var n = document.createElementNS(SVG_NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  function setError(msg) {
    var box = $("s-error");
    box.className = msg ? "form-error" : "";
    box.textContent = msg || "";
  }

  function selectedMode() {
    return document.querySelector('input[name="s-mode"]:checked').value;
  }

  function updateModeVisibility() {
    var mode = selectedMode();
    $("s-conc-fields").hidden = mode !== "conc";
    $("s-mix-fields").hidden = mode !== "mix";
  }

  // A plain barrel with a fill line at pct of its length, graduations every
  // tenth, and a muted fill if the draw is larger than the barrel.
  function renderSyringe(pct, overshoot) {
    var svg = $("syringe-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    var barrelX = 20, barrelY = 30, barrelW = 260, barrelH = 30;
    svg.appendChild(el("rect", { x: barrelX, y: barrelY, width: barrelW, height: barrelH, rx: 6, fill: "none", stroke: "var(--line)", "stroke-width": 2 }));
    var fillW = barrelW * Math.max(0, Math.min(1, pct));
    svg.appendChild(el("rect", {
      x: barrelX + (barrelW - fillW), y: barrelY + 3, width: fillW, height: barrelH - 6, rx: 4,
      fill: overshoot ? "var(--dim)" : "var(--gold)", opacity: overshoot ? 0.5 : 1
    }));
    svg.appendChild(el("rect", { x: barrelX - 14, y: barrelY - 4, width: 14, height: barrelH + 8, rx: 3, fill: "none", stroke: "var(--line)", "stroke-width": 2 }));
    svg.appendChild(el("rect", { x: barrelX + barrelW, y: barrelY + 10, width: 26, height: 10, fill: "none", stroke: "var(--line)", "stroke-width": 2 }));
    for (var i = 0; i <= 10; i++) {
      var gx = barrelX + (barrelW * i) / 10;
      svg.appendChild(el("line", { x1: gx, x2: gx, y1: barrelY, y2: barrelY + (i % 5 === 0 ? 10 : 6), stroke: "var(--dim)", "stroke-width": 1 }));
    }
  }

  function calc() {
    var conc;
    if (selectedMode() === "conc") {
      conc = parseFloat($("s-conc").value);
    } else {
      conc = M.concentrationMgPerMl(parseFloat($("s-mix-mg").value), parseFloat($("s-mix-ml").value));
    }

    var doseMg = M.toMg(parseFloat($("s-dose").value), $("s-dose-unit").value, null);
    var barrelUnits = parseInt($("s-syringe").value, 10);
    $("syr-max").textContent = barrelUnits + " u";

    if (!(conc > 0) || !(doseMg > 0)) {
      setError(null);
      $("out-units").textContent = "-";
      $("out-vol").textContent = "-";
      $("out-conc").textContent = "-";
      renderSyringe(0, false);
      return;
    }

    var units = M.unitsToDraw(doseMg, conc);
    var ml = M.mlForDose(doseMg, conc);
    setError(M.syringeWarning(units, barrelUnits));
    $("out-units").textContent = M.fmt(units, 1);
    $("out-vol").textContent = M.fmt(ml, 3) + " mL";
    $("out-conc").textContent = M.fmt(conc, 2) + " mg/mL";
    renderSyringe(units / barrelUnits, units > barrelUnits);
  }

  document.querySelectorAll('input[name="s-mode"]').forEach(function (r) {
    r.addEventListener("change", function () { updateModeVisibility(); calc(); });
  });
  ["s-conc", "s-mix-mg", "s-mix-ml", "s-dose", "s-dose-unit", "s-syringe"].forEach(function (id) {
    $(id).addEventListener("input", calc);
    $(id).addEventListener("change", calc);
  });

  updateModeVisibility();
  calc();
})();
