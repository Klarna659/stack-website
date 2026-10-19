(function () {
  "use strict";
  var M = window.ToolsMath;
  var $ = function (id) { return document.getElementById(id); };

  function localISO() {
    var d = new Date();
    return d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
  }
  $("s-date").value = localISO();

  function fmtDate(iso) {
    return new Intl.DateTimeFormat("en-US", { weekday: "short", month: "short", day: "numeric", year: "numeric", timeZone: "UTC" })
      .format(new Date(iso + "T00:00:00Z"));
  }

  function plural(n, word) { return n + " " + word + (n === 1 ? "" : "s"); }

  function duration(min) {
    var h = Math.floor(min / 60);
    var m = Math.round(min - h * 60);
    if (m === 0) return plural(h, "hour");
    if (h === 0) return plural(m, "minute");
    return plural(h, "hour") + " " + plural(m, "minute");
  }

  function dayNote(dayOffset) {
    if (dayOffset <= 0) return "";
    return dayOffset === 1 ? " (next day)" : " (" + dayOffset + " days later)";
  }

  function setError(msg) {
    var box = $("s-error");
    box.className = msg ? "form-error" : "";
    box.textContent = msg || "";
  }

  function render(count, unit, rows, note) {
    $("out-count").textContent = count;
    $("out-unit").textContent = unit;
    var list = $("out-list");
    list.textContent = "";
    rows.forEach(function (r) {
      var line = document.createElement("div");
      line.className = "row-line";
      var label = document.createElement("span");
      label.textContent = r[0];
      var value = document.createElement("b");
      value.textContent = r[1];
      line.appendChild(label);
      line.appendChild(value);
      list.appendChild(line);
    });
    $("out-note").textContent = note || "";
  }

  function clearOutputs() { render("-", "times", [], ""); }

  function applyMode() {
    var mode = $("s-mode").value;
    var fields = document.querySelectorAll("[data-for]");
    for (var i = 0; i < fields.length; i++) {
      fields[i].hidden = fields[i].getAttribute("data-for").split(" ").indexOf(mode) === -1;
    }
    $("s-time-label").textContent = mode === "days" ? "Time of day (optional)" : "First time";
  }

  function blank(ids) {
    return ids.some(function (id) { return $(id).value === ""; });
  }

  function calc() {
    var mode = $("s-mode").value;
    var use24 = $("s-fmt").value === "24";
    var clock = function (min) { return M.formatClock(min, use24); };
    var result;

    if (mode === "hours") {
      if (blank(["s-hours", "s-time"])) { setError(null); clearOutputs(); return; }
      result = M.timesEveryNHours({ first: $("s-time").value, hours: parseFloat($("s-hours").value) });
      if (result.error) { setError(result.error); clearOutputs(); return; }
      setError(null);
      var gap = duration(result.stepMinutes);
      var rows = result.times.map(function (t, i) {
        return ["Time " + (i + 1), clock(t.clock) + dayNote(t.dayOffset)];
      });
      var note = result.repeatsDaily
        ? "The same times repeat every day."
        : "24 hours is not a whole number of " + gap + ", so the times move each day. After the last time listed, the next one is " +
          clock(result.next.clock) + dayNote(result.next.dayOffset) + ".";
      render(String(result.times.length), "times in 24 hours, " + gap + " apart", rows, note);
      return;
    }

    if (mode === "days") {
      if (blank(["s-days", "s-date"])) { setError(null); clearOutputs(); return; }
      result = M.datesEveryNDays({ firstDateISO: $("s-date").value, days: parseFloat($("s-days").value), count: 8 });
      if (result.error) { setError(result.error); clearOutputs(); return; }
      setError(null);
      var timeMin = M.parseClock($("s-time").value);
      var drows = result.dates.map(function (iso, i) {
        return ["Dose " + (i + 1), fmtDate(iso) + (timeMin == null ? "" : " at " + clock(timeMin))];
      });
      var n = parseFloat($("s-days").value);
      render(String(result.dates.length), "dates shown, every " + plural(n, "day"), drows,
        "Dates are counted on the calendar, so months, years and leap days roll over correctly.");
      return;
    }

    if (blank(["s-times", "s-wake", "s-bed"])) { setError(null); clearOutputs(); return; }
    result = M.timesPerDay({ times: parseFloat($("s-times").value), wake: $("s-wake").value, bed: $("s-bed").value });
    if (result.error) { setError(result.error); clearOutputs(); return; }
    setError(null);
    var prows = result.times.map(function (t, i) {
      return ["Time " + (i + 1), clock(t.clock) + dayNote(t.dayOffset)];
    });
    var count = result.times.length;
    render(String(count), count === 1 ? "time a day, at your wake time" : "times a day, " + duration(result.gapMinutes) + " apart",
      prows, count === 1 ? "" : "The first time is your wake time and the last is your bed time. The rest are spaced evenly between them.");
  }

  ["s-mode", "s-hours", "s-days", "s-date", "s-time", "s-times", "s-wake", "s-bed", "s-fmt"].forEach(function (id) {
    $(id).addEventListener("input", calc);
    $(id).addEventListener("change", calc);
  });
  $("s-mode").addEventListener("change", applyMode);

  applyMode();
  calc();
})();
