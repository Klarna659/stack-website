(function () {
  "use strict";
  var M = window.ToolsMath;
  var $ = function (id) { return document.getElementById(id); };
  var iuInput = $("vd-iu");
  var mcgInput = $("vd-mcg");

  function show(iu, mcg) {
    if (iu == null || mcg == null) {
      $("out-line").textContent = "-";
      return;
    }
    $("out-line").textContent = M.fmt(iu, 2) + " IU = " + M.fmt(mcg, 3) + " mcg";
  }

  // Typing in one box fills the other. A blank or invalid box clears the other.
  iuInput.addEventListener("input", function () {
    var iu = iuInput.value === "" ? null : parseFloat(iuInput.value);
    var mcg = M.iuToMcg(iu);
    mcgInput.value = mcg == null ? "" : M.fmt(mcg, 3);
    show(mcg == null ? null : iu, mcg);
  });

  mcgInput.addEventListener("input", function () {
    var mcg = mcgInput.value === "" ? null : parseFloat(mcgInput.value);
    var iu = M.mcgToIu(mcg);
    iuInput.value = iu == null ? "" : M.fmt(iu, 2);
    show(iu, iu == null ? null : mcg);
  });

  iuInput.dispatchEvent(new Event("input"));
})();
