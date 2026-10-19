(function () {
  "use strict";
  var M = window.ToolsMath;
  var $ = function (id) { return document.getElementById(id); };
  var mgInput = $("g-mgdl");
  var mmolInput = $("g-mmol");

  function show(mg, mmol) {
    if (mg == null || mmol == null) {
      $("out-line").textContent = "-";
      return;
    }
    $("out-line").textContent = M.fmt(mg, 1) + " mg/dL = " + M.fmt(mmol, 2) + " mmol/L";
  }

  // Typing in one box fills the other. A blank or invalid box clears the other.
  mgInput.addEventListener("input", function () {
    var mg = mgInput.value === "" ? null : parseFloat(mgInput.value);
    var mmol = M.glucoseMgdlToMmolL(mg);
    mmolInput.value = mmol == null ? "" : M.fmt(mmol, 2);
    show(mmol == null ? null : mg, mmol);
  });

  mmolInput.addEventListener("input", function () {
    var mmol = mmolInput.value === "" ? null : parseFloat(mmolInput.value);
    var mg = M.glucoseMmolLToMgdl(mmol);
    mgInput.value = mg == null ? "" : M.fmt(mg, 1);
    show(mg, mg == null ? null : mmol);
  });

  mgInput.dispatchEvent(new Event("input"));
})();
