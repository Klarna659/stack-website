(function () {
  "use strict";
  var M = window.ToolsMath;
  var $ = function (id) { return document.getElementById(id); };

  function localISO() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
  $("v-start").value = localISO();

  function fmtDate(iso) {
    if (!iso) return "-";
    var d = new Date(iso + "T00:00:00Z");
    return new Intl.DateTimeFormat("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric", timeZone: "UTC" }).format(d);
  }

  function selectedVialMode() {
    return document.querySelector('input[name="vial-mode"]:checked').value;
  }

  function selectedWeekdays() {
    return Array.prototype.slice.call(document.querySelectorAll("#freq-weekdays-field input:checked")).map(function (el) { return Number(el.value); });
  }

  // The IU-per-mg field only matters once a unit above is set to IU.
  function updateIuVisibility() {
    var vialUnit = selectedVialMode() === "amount" ? $("v-amount-unit").value : "mg";
    $("iu-factor-field").hidden = !(vialUnit === "iu" || $("v-dose-unit").value === "iu");
  }

  function updateModeVisibility() {
    var mode = selectedVialMode();
    $("vial-amount-fields").hidden = mode !== "amount";
    $("vial-volume-fields").hidden = mode !== "volume";
    updateIuVisibility();
  }

  function updateFreqVisibility() {
    var freq = $("v-freq").value;
    $("freq-n-field").hidden = !(freq === "everyNDays" || freq === "timesPerWeek");
    $("freq-weekdays-field").hidden = freq !== "weekdays";
    $("freq-n-label").textContent = freq === "everyNDays" ? "Every how many days" : "How many times a week";
  }

  function buildFrequency() {
    var freq = $("v-freq").value;
    var n = parseInt($("v-freq-n").value, 10) || 1;
    if (freq === "daily") return { type: "daily" };
    if (freq === "everyNDays") return { type: "everyNDays", n: n };
    if (freq === "timesPerWeek") return { type: "timesPerWeek", n: n };
    if (freq === "weekdays") return { type: "weekdays", days: selectedWeekdays() };
    return null;
  }

  function setError(msg) {
    var box = $("v-error");
    box.className = msg ? "form-error" : "";
    box.textContent = msg || "";
  }

  function clearOutputs() {
    $("out-doses").textContent = "-";
    $("out-last").textContent = "-";
    $("out-runout").textContent = "-";
    $("out-reorder").textContent = "-";
  }

  function calc() {
    var mode = selectedVialMode();
    var doseUnit = $("v-dose-unit").value;
    var vialUnit = mode === "amount" ? $("v-amount-unit").value : "mg";
    var iuPerMg = parseFloat($("v-iu-per-mg").value);
    if (!isFinite(iuPerMg)) iuPerMg = null;

    var mismatch = M.unitMismatchMessage(vialUnit, doseUnit, iuPerMg);
    if (mismatch) { setError(mismatch); clearOutputs(); return; }

    var waste = parseFloat($("v-waste").value) || 0;
    var deadSpaceMismatch = M.deadSpaceMismatchMessage(mode, waste);
    if (deadSpaceMismatch) { setError(deadSpaceMismatch); clearOutputs(); return; }

    var vialMg;
    var concMgPerMl = null;
    if (mode === "amount") {
      vialMg = M.vialMgFromInputs("amount", { amount: parseFloat($("v-amount").value), unit: vialUnit, iuPerMg: iuPerMg });
    } else {
      concMgPerMl = parseFloat($("v-conc").value);
      vialMg = M.vialMgFromInputs("volume", { ml: parseFloat($("v-ml").value), concMgPerMl: concMgPerMl });
    }

    var doseMg = M.toMg(parseFloat($("v-dose").value), doseUnit, iuPerMg);
    var wasteMg = waste > 0 && concMgPerMl > 0 ? waste * concMgPerMl : 0;

    setError(null);
    if (!(vialMg > 0) || !(doseMg > 0)) { clearOutputs(); return; }

    var result = M.runOutCalc({
      vialMg: vialMg,
      doseMg: doseMg,
      wasteMgPerDraw: wasteMg,
      frequency: buildFrequency(),
      startDateISO: $("v-start").value,
      leadDays: parseFloat($("v-lead").value)
    });

    if (result.error) { setError(result.error); clearOutputs(); return; }

    $("out-doses").textContent = M.fmt(result.fullDoses, 0);
    $("out-last").textContent = fmtDate(result.lastDoseDate);
    $("out-runout").textContent = fmtDate(result.runOutDate);
    $("out-reorder").textContent = fmtDate(result.reorderByDate);
  }

  document.querySelectorAll('input[name="vial-mode"]').forEach(function (el) {
    el.addEventListener("change", function () { updateModeVisibility(); calc(); });
  });
  $("v-freq").addEventListener("change", function () { updateFreqVisibility(); calc(); });
  document.querySelectorAll("#freq-weekdays-field input").forEach(function (el) {
    el.addEventListener("change", calc);
  });
  ["v-amount", "v-amount-unit", "v-ml", "v-conc", "v-dose", "v-dose-unit", "v-iu-per-mg", "v-freq-n", "v-start", "v-waste", "v-lead"].forEach(function (id) {
    $(id).addEventListener("input", calc);
    $(id).addEventListener("change", calc);
  });
  $("v-amount-unit").addEventListener("change", updateIuVisibility);
  $("v-dose-unit").addEventListener("change", updateIuVisibility);

  updateModeVisibility();
  updateFreqVisibility();
  calc();
})();
