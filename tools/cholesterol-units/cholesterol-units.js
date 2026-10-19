(function () {
  "use strict";
  var M = window.ToolsMath;
  var $ = function (id) { return document.getElementById(id); };
  var mgInput = $("c-mgdl");
  var mmolInput = $("c-mmol");
  var lastEdited = "mg";

  function kind() {
    return document.querySelector('input[name="c-kind"]:checked').value;
  }

  function factorText() {
    var f = kind() === "triglycerides" ? M.TRIGLYCERIDES_MGDL_PER_MMOLL : M.CHOLESTEROL_MGDL_PER_MMOLL;
    return "1 mmol/L = " + f + " mg/dL";
  }

  function show(mg, mmol) {
    $("out-factor").textContent = factorText();
    if (mg == null || mmol == null) {
      $("out-line").textContent = "-";
      return;
    }
    $("out-line").textContent = M.fmt(mg, 1) + " mg/dL = " + M.fmt(mmol, 2) + " mmol/L";
  }

  function fromMg() {
    var mg = mgInput.value === "" ? null : parseFloat(mgInput.value);
    var mmol = M.lipidMgdlToMmolL(mg, kind());
    mmolInput.value = mmol == null ? "" : M.fmt(mmol, 2);
    show(mmol == null ? null : mg, mmol);
  }

  function fromMmol() {
    var mmol = mmolInput.value === "" ? null : parseFloat(mmolInput.value);
    var mg = M.lipidMmolLToMgdl(mmol, kind());
    mgInput.value = mg == null ? "" : M.fmt(mg, 1);
    show(mg, mg == null ? null : mmol);
  }

  mgInput.addEventListener("input", function () { lastEdited = "mg"; fromMg(); });
  mmolInput.addEventListener("input", function () { lastEdited = "mmol"; fromMmol(); });

  // Changing the type keeps the number the person typed last and redoes the other box.
  var kinds = document.querySelectorAll('input[name="c-kind"]');
  for (var i = 0; i < kinds.length; i++) {
    kinds[i].addEventListener("change", function () { if (lastEdited === "mg") fromMg(); else fromMmol(); });
  }

  fromMg();
})();
