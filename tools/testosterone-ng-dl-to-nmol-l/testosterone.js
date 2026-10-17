(function () {
  "use strict";
  var M = window.ToolsMath;
  var $ = function (id) { return document.getElementById(id); };
  var ngInput = $("t-ngdl");
  var nmInput = $("t-nmoll");

  function show(ng, nm) {
    if (ng == null || nm == null) {
      $("out-line").textContent = "-";
      return;
    }
    $("out-line").textContent = M.fmt(ng, 1) + " ng/dL = " + M.fmt(nm, 2) + " nmol/L";
  }

  // Typing in one box fills the other. A blank or invalid box clears the other.
  ngInput.addEventListener("input", function () {
    var ng = ngInput.value === "" ? null : parseFloat(ngInput.value);
    var nm = M.ngdlToNmolL(ng);
    nmInput.value = nm == null ? "" : M.fmt(nm, 2);
    show(nm == null ? null : ng, nm);
  });

  nmInput.addEventListener("input", function () {
    var nm = nmInput.value === "" ? null : parseFloat(nmInput.value);
    var ng = M.nmolLToNgdl(nm);
    ngInput.value = ng == null ? "" : M.fmt(ng, 1);
    show(ng, ng == null ? null : nm);
  });

  ngInput.dispatchEvent(new Event("input"));
})();
