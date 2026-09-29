/* ============================================================================
   tools-math.js — pure functions for Stack's standalone calculator pages.
   No DOM access, no globals besides the single export below. Safe to load
   with a <script> tag (attaches window.ToolsMath) or `require()`/`import`
   from Node (module.exports).
   ========================================================================== */
(function (root) {
  "use strict";

  var MCG_PER_MG = 1000;
  var U100_UNITS_PER_ML = 100; // U-100 insulin syringe: 100 units = 1 mL
  var MS_PER_DAY = 86400000;
  var SYRINGE_BARRELS = { "100": 100, "50": 50, "30": 30 };

  // ------------------------------------------------------------- formatting
  // Strips trailing zeros after a decimal point ONLY — never touches a whole
  // number with no decimal point. The historical bug: applying /0+$/ to a
  // bare integer string ("20") strips its own trailing zero and prints "2".
  function fmt(n, decimals) {
    if (n === null || n === undefined || !isFinite(n)) return null;
    var s = n.toFixed(decimals == null ? 0 : decimals);
    if (s.indexOf(".") === -1) return s; // whole number: never touch it
    s = s.replace(/0+$/, "").replace(/\.$/, "");
    return s === "" || s === "-" ? "0" : s;
  }

  // -------------------------------------------------------- unit conversion
  // unit: "mg" | "mcg" | "iu". IU requires an explicit iuPerMg factor supplied
  // by the caller (there is no universal IU-to-mg ratio — it's compound
  // specific) — we refuse to guess.
  function toMg(amount, unit, iuPerMg) {
    if (amount == null || !isFinite(amount) || amount < 0) return null;
    if (unit === "mg") return amount;
    if (unit === "mcg") return amount / MCG_PER_MG;
    if (unit === "iu") {
      if (iuPerMg == null || !isFinite(iuPerMg) || iuPerMg <= 0) return null;
      return amount / iuPerMg;
    }
    return null;
  }

  function mgToUnit(mg, unit, iuPerMg) {
    if (mg == null || !isFinite(mg)) return null;
    if (unit === "mg") return mg;
    if (unit === "mcg") return mg * MCG_PER_MG;
    if (unit === "iu") {
      if (iuPerMg == null || !isFinite(iuPerMg) || iuPerMg <= 0) return null;
      return mg * iuPerMg;
    }
    return null;
  }

  // Plain-sentence refusal for a unit combination we cannot safely resolve.
  // Returns null when the combination is fine.
  function unitMismatchMessage(vialUnit, doseUnit, iuPerMg) {
    var needsFactor = vialUnit === "iu" || doseUnit === "iu";
    if (needsFactor && !(iuPerMg > 0)) {
      return "We can't compare IU to mg without knowing how many IU are in a milligram for this compound. Enter that conversion factor, or switch both fields to mg or mcg.";
    }
    return null;
  }

  // Vial contents cannot be reduced to mg without a concentration; dead-space
  // waste (a volume) cannot be subtracted without one either.
  function deadSpaceMismatchMessage(vialMode, deadSpaceMl) {
    if (deadSpaceMl > 0 && vialMode !== "volume") {
      return "We can't subtract wasted volume without knowing the vial's concentration. Switch “what's in the vial” to mL at a concentration, or leave wasted-per-draw blank.";
    }
    return null;
  }

  function vialMgFromInputs(mode, opts) {
    opts = opts || {};
    if (mode === "amount") return toMg(opts.amount, opts.unit, opts.iuPerMg);
    if (mode === "volume") {
      if (!(opts.ml > 0) || !(opts.concMgPerMl > 0)) return null;
      return opts.ml * opts.concMgPerMl;
    }
    return null;
  }

  // --------------------------------------------------------------- dates
  // Dates are handled as UTC-midnight millisecond timestamps internally so
  // that adding whole days never trips over DST — every "day" is exactly
  // 86,400,000 ms, and month/leap-year rollover is native Date.UTC behaviour.
  function parseISODate(s) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(s || ""));
    if (!m) return null;
    var ms = Date.UTC(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    return isNaN(ms) ? null : ms;
  }

  function formatISODate(ms) {
    if (ms == null || !isFinite(ms)) return null;
    var d = new Date(ms);
    var y = d.getUTCFullYear();
    var mo = String(d.getUTCMonth() + 1).padStart(2, "0");
    var da = String(d.getUTCDate()).padStart(2, "0");
    return y + "-" + mo + "-" + da;
  }

  function addDaysUTC(ms, days) {
    return ms + days * MS_PER_DAY;
  }

  // Returns the UTC-ms timestamp of the (index+1)-th dose (index is 0-based),
  // per the frequency descriptor:
  //   { type: "daily" }
  //   { type: "everyNDays", n }
  //   { type: "timesPerWeek", n }        — n doses spread evenly across a 7-day week
  //   { type: "weekdays", days: [0..6] } — 0 = Sunday .. 6 = Saturday (JS getUTCDay)
  function doseDateAt(startMs, frequency, index) {
    if (startMs == null || !frequency || index < 0) return null;
    switch (frequency.type) {
      case "daily":
        return addDaysUTC(startMs, index);
      case "everyNDays":
        if (!(frequency.n > 0)) return null;
        return addDaysUTC(startMs, index * frequency.n);
      case "timesPerWeek": {
        var n = frequency.n;
        if (!(n > 0)) return null;
        var week = Math.floor(index / n);
        var posInWeek = index % n;
        var dayOffset = week * 7 + Math.round((posInWeek * 7) / n);
        return addDaysUTC(startMs, dayOffset);
      }
      case "weekdays": {
        var days = (frequency.days || []).slice().sort(function (a, b) { return a - b; });
        if (!days.length) return null;
        var startDow = new Date(startMs).getUTCDay();
        var found = 0;
        var offset = 0;
        var maxIter = 20000; // ~54 years of daily stepping — plenty of headroom
        while (maxIter-- > 0) {
          var dow = (startDow + offset) % 7;
          if (days.indexOf(dow) !== -1) {
            if (found === index) return addDaysUTC(startMs, offset);
            found++;
          }
          offset++;
        }
        return null;
      }
      default:
        return null;
    }
  }

  // ------------------------------------------------------------- run-out
  // params: { vialMg, doseMg, wasteMgPerDraw, frequency, startDateISO, leadDays }
  function runOutCalc(params) {
    params = params || {};
    if (!(params.vialMg > 0)) return { error: "Enter how much is in the vial." };
    if (!(params.doseMg > 0)) return { error: "Enter your dose amount." };
    var startMs = parseISODate(params.startDateISO);
    if (startMs == null) return { error: "Enter a valid first-dose date." };

    var waste = params.wasteMgPerDraw > 0 ? params.wasteMgPerDraw : 0;
    var perDraw = params.doseMg + waste;
    var fullDoses = Math.floor((params.vialMg + 1e-9) / perDraw);
    if (fullDoses < 1) {
      return { error: "This vial doesn't hold even one full dose at that amount." };
    }

    var leadDays = params.leadDays != null && isFinite(params.leadDays) ? params.leadDays : 10;
    var lastMs = doseDateAt(startMs, params.frequency, fullDoses - 1);
    var runOutMs = doseDateAt(startMs, params.frequency, fullDoses);
    if (lastMs == null || runOutMs == null) {
      return { error: "Enter a valid schedule (how often you dose)." };
    }
    var reorderMs = addDaysUTC(runOutMs, -leadDays);

    return {
      error: null,
      fullDoses: fullDoses,
      lastDoseDate: formatISODate(lastMs),
      runOutDate: formatISODate(runOutMs),
      reorderByDate: formatISODate(reorderMs)
    };
  }

  // ---------------------------------------------------------- half-life
  function halfLifeToHours(value, unit) {
    if (!(value > 0)) return null;
    if (unit === "hours") return value;
    if (unit === "days") return value * 24;
    return null;
  }

  // Superposition of first-order decay: sums the decaying contribution of
  // every dose already given by time tHours (doses given at 0, tau, 2*tau...
  // up to numDoses total).
  function amountAtTime(tHours, doseMg, intervalHours, halfLifeHours, numDoses) {
    if (!(halfLifeHours > 0) || !(intervalHours > 0) || !(doseMg > 0) || !(numDoses > 0)) return 0;
    if (tHours < 0) return 0;
    var total = 0;
    var maxK = Math.min(numDoses - 1, Math.floor(tHours / intervalHours + 1e-9));
    for (var k = 0; k <= maxK; k++) {
      var dt = tHours - k * intervalHours;
      if (dt < 0) continue;
      total += doseMg * Math.pow(2, -dt / halfLifeHours);
    }
    return total;
  }

  // Relative to a single dose = 1. Peak = the level right after a dose lands
  // once the regimen has reached steady state; trough = right before the next.
  function steadyStatePeak(intervalHours, halfLifeHours) {
    if (!(intervalHours > 0) || !(halfLifeHours > 0)) return null;
    var r = Math.pow(2, -intervalHours / halfLifeHours);
    return 1 / (1 - r);
  }

  function steadyStateTrough(intervalHours, halfLifeHours) {
    var peak = steadyStatePeak(intervalHours, halfLifeHours);
    if (peak == null) return null;
    var r = Math.pow(2, -intervalHours / halfLifeHours);
    return peak * r;
  }

  function peakTroughRatio(intervalHours, halfLifeHours) {
    if (!(intervalHours > 0) || !(halfLifeHours > 0)) return null;
    return Math.pow(2, intervalHours / halfLifeHours);
  }

  // The rule of thumb: 5 half-lives ≈ 97% of the way to steady state
  // (2^-5 = 1/32 ≈ 3.1% still to go).
  function timeToSteadyStateHours(halfLifeHours) {
    if (!(halfLifeHours > 0)) return null;
    return 5 * halfLifeHours;
  }

  // Samples the curve as { t, amount, percent } points, percent expressed
  // relative to the size of ONE dose (never a blood level, never advice).
  function buildCurve(doseMg, intervalHours, halfLifeHours, numDoses, numPoints) {
    if (!(halfLifeHours > 0) || !(intervalHours > 0) || !(doseMg > 0) || !(numDoses > 0)) return [];
    var n = numPoints > 1 ? numPoints : 200;
    var tail = halfLifeHours * 3;
    var endHours = intervalHours * (numDoses - 1) + tail;
    var points = [];
    for (var i = 0; i < n; i++) {
      var t = (endHours * i) / (n - 1);
      var amt = amountAtTime(t, doseMg, intervalHours, halfLifeHours, numDoses);
      points.push({ t: t, amount: amt, percent: (amt / doseMg) * 100 });
    }
    return points;
  }

  // ------------------------------------------------------------- syringe
  function concentrationMgPerMl(vialMg, vialMl) {
    if (!(vialMg > 0) || !(vialMl > 0)) return null;
    return vialMg / vialMl;
  }

  function mlForDose(doseMg, concMgPerMl) {
    if (!(doseMg > 0) || !(concMgPerMl > 0)) return null;
    return doseMg / concMgPerMl;
  }

  function unitsToDraw(doseMg, concMgPerMl) {
    var ml = mlForDose(doseMg, concMgPerMl);
    return ml == null ? null : ml * U100_UNITS_PER_ML;
  }

  function syringeWarning(units, barrelUnits) {
    if (units == null || !(barrelUnits > 0)) return null;
    if (units > barrelUnits) {
      return "That dose doesn't fit this syringe. Use a more concentrated mix or a bigger syringe.";
    }
    if (units < 1) {
      return "Under 1 unit is hard to measure accurately on this syringe. Consider a more dilute mix or a smaller syringe.";
    }
    return null;
  }

  var api = {
    MCG_PER_MG: MCG_PER_MG,
    U100_UNITS_PER_ML: U100_UNITS_PER_ML,
    SYRINGE_BARRELS: SYRINGE_BARRELS,
    fmt: fmt,
    toMg: toMg,
    mgToUnit: mgToUnit,
    unitMismatchMessage: unitMismatchMessage,
    deadSpaceMismatchMessage: deadSpaceMismatchMessage,
    vialMgFromInputs: vialMgFromInputs,
    parseISODate: parseISODate,
    formatISODate: formatISODate,
    addDaysUTC: addDaysUTC,
    doseDateAt: doseDateAt,
    runOutCalc: runOutCalc,
    halfLifeToHours: halfLifeToHours,
    amountAtTime: amountAtTime,
    steadyStatePeak: steadyStatePeak,
    steadyStateTrough: steadyStateTrough,
    peakTroughRatio: peakTroughRatio,
    timeToSteadyStateHours: timeToSteadyStateHours,
    buildCurve: buildCurve,
    concentrationMgPerMl: concentrationMgPerMl,
    mlForDose: mlForDose,
    unitsToDraw: unitsToDraw,
    syringeWarning: syringeWarning
  };

  if (typeof module !== "undefined" && module.exports) {
    module.exports = api;
  } else {
    root.ToolsMath = api;
  }
})(typeof window !== "undefined" ? window : globalThis);
