(function () {
  "use strict";
  var M = window.ToolsMath;
  var $ = function (id) { return document.getElementById(id); };

  function localISO() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
  $("d-start").value = localISO();

  function fmtDate(iso) {
    if (!iso) return "-";
    return new Intl.DateTimeFormat("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric", timeZone: "UTC" })
      .format(new Date(iso + "T00:00:00Z"));
  }

  function setError(msg) {
    var box = $("d-error");
    box.className = msg ? "form-error" : "";
    box.textContent = msg || "";
  }

  function clearOutputs() {
    $("out-days").textContent = "-";
    $("out-days-unit").textContent = "days of supply";
    $("out-covered").textContent = "-";
    $("out-runout").textContent = "-";
    $("out-reorder").textContent = "-";
    $("out-doses").textContent = "-";
  }

  function updateFreq() {
    var mode = $("d-freq").value;
    $("d-freq-label").textContent = mode === "everyNDays" ? "Every how many days" : "How many times a day";
  }

  function calc() {
    var mode = $("d-freq").value;
    var result = M.daysOfSupply({
      onHand: parseFloat($("d-onhand").value),
      perDose: parseFloat($("d-perdose").value),
      schedule: { type: mode, n: parseFloat($("d-freq-n").value) },
      startDateISO: $("d-start").value,
      leadDays: parseFloat($("d-lead").value)
    });

    if (result.error) {
      // Blank or zero fields are normal while typing; only say something once
      // every field has a number in it.
      var filled = ["d-onhand", "d-perdose", "d-freq-n"].every(function (id) { return parseFloat($(id).value) > 0; });
      setError(filled ? result.error : null);
      clearOutputs();
      return;
    }
    setError(null);
    $("out-days").textContent = M.fmt(result.days, 0);
    $("out-days-unit").textContent = result.days === 1 ? "day of supply" : "days of supply";
    $("out-covered").textContent = fmtDate(result.coveredThroughDate);
    $("out-runout").textContent = fmtDate(result.runOutDate);
    $("out-reorder").textContent = fmtDate(result.reorderByDate);
    $("out-doses").textContent = M.fmt(result.totalDoses, 0);
  }

  ["d-onhand", "d-perdose", "d-freq", "d-freq-n", "d-start", "d-lead"].forEach(function (id) {
    $(id).addEventListener("input", calc);
    $(id).addEventListener("change", calc);
  });
  $("d-freq").addEventListener("change", updateFreq);

  updateFreq();
  calc();
})();
