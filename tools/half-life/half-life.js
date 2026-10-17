(function () {
  "use strict";
  var M = window.ToolsMath;
  var $ = function (id) { return document.getElementById(id); };
  var SVG_NS = "http://www.w3.org/2000/svg";

  function setError(msg) {
    var box = $("h-error");
    box.className = msg ? "form-error" : "";
    box.textContent = msg || "";
  }

  function el(tag, attrs) {
    var n = document.createElementNS(SVG_NS, tag);
    for (var k in attrs) n.setAttribute(k, attrs[k]);
    return n;
  }

  function renderCurve(points, intervalHours, halfLifeUnit) {
    var svg = $("curve-svg");
    while (svg.firstChild) svg.removeChild(svg.firstChild);
    if (!points.length) return;

    var W = 640, H = 260, padL = 34, padR = 12, padT = 14, padB = 26;
    var maxT = points[points.length - 1].t;
    var maxP = Math.max.apply(null, points.map(function (p) { return p.percent; })) * 1.12 || 1;

    function x(t) { return padL + (t / maxT) * (W - padL - padR); }
    function y(p) { return H - padB - (p / maxP) * (H - padT - padB); }

    // One reference line: the size of a single dose.
    if (maxP >= 100) {
      var refY = y(100);
      svg.appendChild(el("line", { x1: padL, x2: W - padR, y1: refY, y2: refY, "class": "ref-line" }));
      var refLabel = el("text", { x: 4, y: refY - 5, "class": "axis-cap" });
      refLabel.textContent = "1 dose";
      svg.appendChild(refLabel);
    }

    var d = points.map(function (p, i) { return (i === 0 ? "M" : "L") + x(p.t).toFixed(1) + "," + y(p.percent).toFixed(1); }).join(" ");
    svg.appendChild(el("path", { d: d, "class": "thread" }));

    // dose ticks along the baseline
    var i = 0;
    while (i * intervalHours <= maxT + 1e-9) {
      svg.appendChild(el("circle", { cx: x(i * intervalHours), cy: H - padB, r: 2.6, "class": "dose-tick" }));
      i++;
    }

    var unitLabel = halfLifeUnit === "days" ? "days" : "hours";
    var endLabel = el("text", { x: W - padR, y: H - 6, "class": "axis-cap", "text-anchor": "end" });
    endLabel.textContent = M.fmt(halfLifeUnit === "days" ? maxT / 24 : maxT, 0) + " " + unitLabel;
    svg.appendChild(endLabel);
    var startLabel = el("text", { x: padL, y: H - 6, "class": "axis-cap" });
    startLabel.textContent = "0";
    svg.appendChild(startLabel);
  }

  function calc() {
    var halfLifeHours = M.halfLifeToHours(parseFloat($("h-halflife").value), $("h-halflife-unit").value);
    var intervalHours = M.halfLifeToHours(parseFloat($("h-interval").value), $("h-interval-unit").value);
    var doseAmount = parseFloat($("h-dose").value);
    var numDoses = parseInt($("h-count").value, 10);

    $("h-halflife-hint").textContent = halfLifeHours > 0 ? ("= " + M.fmt(halfLifeHours, 1) + " hours") : "";

    if (!(halfLifeHours > 0) || !(intervalHours > 0) || !(doseAmount > 0) || !(numDoses > 0)) {
      setError("Enter a half-life, a dose, an interval and a number of doses, all greater than zero.");
      return;
    }
    setError(null);

    var ratio = M.peakTroughRatio(intervalHours, halfLifeHours);
    var peak = M.steadyStatePeak(intervalHours, halfLifeHours);
    var trough = M.steadyStateTrough(intervalHours, halfLifeHours);
    var tss = M.timeToSteadyStateHours(halfLifeHours);

    $("out-ratio").textContent = M.fmt(ratio, ratio >= 10 ? 0 : 2) + "x";
    $("out-peak").textContent = M.fmt(peak * 100, 0) + "% of one dose";
    $("out-trough").textContent = M.fmt(trough * 100, 0) + "% of one dose";
    $("out-tss").textContent = tss >= 48
      ? (M.fmt(tss / 24, 1) + (tss / 24 === 1 ? " day" : " days"))
      : (M.fmt(tss, 1) + (tss === 1 ? " hour" : " hours"));

    var points = M.buildCurve(doseAmount, intervalHours, halfLifeHours, numDoses, 220);
    renderCurve(points, intervalHours, $("h-halflife-unit").value);
  }

  ["h-halflife", "h-halflife-unit", "h-dose", "h-interval", "h-interval-unit", "h-count"].forEach(function (id) {
    $(id).addEventListener("input", calc);
    $(id).addEventListener("change", calc);
  });

  document.querySelectorAll("#h-presets button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      $("h-halflife").value = btn.getAttribute("data-hl");
      $("h-halflife-unit").value = btn.getAttribute("data-unit");
      calc();
    });
  });

  calc();
})();
