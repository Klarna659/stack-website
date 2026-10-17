(function () {
  "use strict";
  var M = window.ToolsMath;
  var $ = function (id) { return document.getElementById(id); };

  function setWarning(msg) {
    var box = $("c-warn");
    box.className = msg ? "form-error" : "";
    box.textContent = msg || "";
  }

  function calc() {
    var vialMg = M.toMg(parseFloat($("c-mg").value), $("c-mg-unit").value, null);
    var waterMl = parseFloat($("c-ml").value);
    var doseMg = M.toMg(parseFloat($("c-dose").value), $("c-dose-unit").value, null);
    var barrel = parseInt($("c-syr").value, 10);
    $("syr-max").textContent = barrel + " u";

    var r = M.reconstitute({ vialMg: vialMg, waterMl: waterMl, doseMg: doseMg, barrelUnits: barrel });
    if (r.error) {
      $("out-units").textContent = "-";
      $("out-conc").textContent = "-";
      $("out-vol").textContent = "-";
      $("out-count").textContent = "-";
      $("syr-fill").style.width = "0%";
      setWarning(null);
      return;
    }

    $("out-units").textContent = M.fmt(r.units, 1);
    $("out-conc").textContent = r.concMgPerMl >= 1
      ? M.fmt(r.concMgPerMl, 2) + " mg/mL"
      : M.fmt(r.concMgPerMl * 1000, 0) + " mcg/mL";
    $("out-vol").textContent = M.fmt(r.mlPerDose, 3) + " mL";
    $("out-count").textContent = r.dosesInVial >= 1 ? M.fmt(r.dosesInVial, 0) : "less than 1";
    $("syr-fill").style.width = Math.max(0, Math.min(100, (r.units / barrel) * 100)) + "%";
    setWarning(r.warning);
  }

  ["c-mg", "c-mg-unit", "c-ml", "c-dose", "c-dose-unit", "c-syr"].forEach(function (id) {
    $(id).addEventListener("input", calc);
    $(id).addEventListener("change", calc);
  });
  calc();
})();
