/* Stack split-S mark — locked brand geometry, verbatim from
   docs/growth/logo_round4/cairn_strata/hero_layouts.html (r 32, spine 55°,
   L 22, stroke 26). Do not alter. Fixed colours regardless of theme: a
   #5FBFB3 tile with a white S (docs/growth/brand_world/site_final.html).
   Renders into every `.brand-mark[data-mark]` on the page. */
(function () {
  function sq(n) {
    n = n || 5;
    var d = "";
    for (var i = 0; i <= 360; i += 2) {
      var t = (i * Math.PI) / 180, c = Math.cos(t), s = Math.sin(t);
      d += (i ? "L" : "M") +
        (100 + 100 * Math.sign(c) * Math.pow(Math.abs(c), 2 / n)).toFixed(2) + " " +
        (100 + 100 * Math.sign(s) * Math.pow(Math.abs(s), 2 / n)).toFixed(2);
    }
    return d + "Z";
  }
  function sp(r, phi, L) {
    var p = (phi * Math.PI) / 180, d = [Math.cos(p), Math.sin(p)];
    var M1 = [100 - (L / 2) * d[0], 100 - (L / 2) * d[1]];
    var M2 = [100 + (L / 2) * d[0], 100 + (L / 2) * d[1]];
    var C1 = [M1[0] + r * Math.sin(p), M1[1] - r * Math.cos(p)];
    var C2 = [M2[0] - r * Math.sin(p), M2[1] + r * Math.cos(p)];
    var T1 = [C1[0], C1[1] - r], T2 = [C2[0], C2[1] + r];
    return "M 240 " + T1[1] + " L " + T1[0] + " " + T1[1] +
      " A " + r + " " + r + " 0 0 0 " + M1[0] + " " + M1[1] +
      " L " + M2[0] + " " + M2[1] +
      " A " + r + " " + r + " 0 0 1 " + T2[0] + " " + T2[1] +
      " L -40 " + T2[1];
  }
  var __u = 0;
  function mark(block, gap, n) {
    block = block || "#5FBFB3"; gap = gap || "#FAF8F4"; n = n || 5;
    var id = "stackmk" + __u++;
    return '<svg width="100%" height="100%" viewBox="0 0 200 200" aria-hidden="true">' +
      '<defs><clipPath id="' + id + '"><path d="' + sq(n) + '"/></clipPath></defs>' +
      '<path d="' + sq(n) + '" fill="' + block + '"/>' +
      '<g clip-path="url(#' + id + ')"><path d="' + sp(32, 55, 22) + '" fill="none" stroke="' + gap + '" stroke-width="26"/></g>' +
      "</svg>";
  }
  function paint() {
    document.querySelectorAll("[data-mark]").forEach(function (el) {
      if (el.getAttribute("data-mark-done")) return;
      el.innerHTML = mark(el.getAttribute("data-block"), el.getAttribute("data-gap"));
      el.setAttribute("data-mark-done", "1");
    });
  }
  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", paint);
  } else {
    paint();
  }
})();
