import { test } from "node:test";
import assert from "node:assert/strict";
import ToolsMath from "./tools-math.js";

const {
  fmt,
  toMg,
  mgToUnit,
  unitMismatchMessage,
  deadSpaceMismatchMessage,
  vialMgFromInputs,
  parseISODate,
  formatISODate,
  addDaysUTC,
  doseDateAt,
  runOutCalc,
  halfLifeToHours,
  amountAtTime,
  steadyStatePeak,
  steadyStateTrough,
  peakTroughRatio,
  timeToSteadyStateHours,
  concentrationMgPerMl,
  mlForDose,
  unitsToDraw,
  syringeWarning,
  dosesPerVial,
  reconstitute,
  daysOfSupply,
  iuToMcg,
  mcgToIu,
  ngdlToNmolL,
  nmolLToNgdl
} = ToolsMath;

// ------------------------------------------------------------- formatting
test("fmt never turns a whole number into a truncated one (the historical bug)", () => {
  assert.equal(fmt(20, 0), "20");
  assert.equal(fmt(20, 1), "20");
  assert.equal(fmt(20, 2), "20");
  assert.equal(fmt(100, 1), "100");
  assert.equal(fmt(10, 3), "10");
  assert.equal(fmt(2.5, 2), "2.5");
  assert.equal(fmt(2.5, 1), "2.5");
  assert.equal(fmt(0, 1), "0");
});

// -------------------------------------------------------- unit conversion
test("mcg <-> mg conversion", () => {
  assert.equal(toMg(500, "mcg", null), 0.5);
  assert.equal(toMg(2, "mg", null), 2);
  assert.equal(mgToUnit(0.5, "mcg", null), 500);
});

test("IU conversion requires a user-supplied factor", () => {
  assert.equal(toMg(100, "iu", 20), 5);
  assert.equal(toMg(100, "iu", null), null); // refuse to guess
  assert.equal(toMg(100, "iu", 0), null);
  assert.equal(mgToUnit(5, "iu", 20), 100);
});

test("unitMismatchMessage refuses IU without a factor, allows mg/mcg freely", () => {
  assert.equal(unitMismatchMessage("mg", "mcg", null), null);
  assert.notEqual(unitMismatchMessage("mg", "iu", null), null);
  assert.equal(unitMismatchMessage("iu", "mg", 20), null);
  assert.notEqual(unitMismatchMessage("iu", "mg", 0), null);
});

test("deadSpaceMismatchMessage refuses waste volume without a concentration", () => {
  assert.notEqual(deadSpaceMismatchMessage("amount", 0.05), null);
  assert.equal(deadSpaceMismatchMessage("amount", 0), null);
  assert.equal(deadSpaceMismatchMessage("volume", 0.05), null);
});

test("vialMgFromInputs handles both vial modes", () => {
  assert.equal(vialMgFromInputs("amount", { amount: 5, unit: "mg" }), 5);
  assert.equal(vialMgFromInputs("amount", { amount: 5000, unit: "mcg" }), 5);
  assert.equal(vialMgFromInputs("volume", { ml: 2, concMgPerMl: 2.5 }), 5);
  assert.equal(vialMgFromInputs("volume", { ml: 0, concMgPerMl: 2.5 }), null);
});

// ------------------------------------------------------------------ dates
test("date round-trip and day arithmetic", () => {
  const ms = parseISODate("2026-03-15");
  assert.equal(formatISODate(ms), "2026-03-15");
  assert.equal(formatISODate(addDaysUTC(ms, 20)), "2026-04-04");
  assert.equal(parseISODate("not-a-date"), null);
});

test("doseDateAt: daily crosses a leap day correctly", () => {
  const start = parseISODate("2028-02-27"); // 2028 is a leap year
  assert.equal(formatISODate(doseDateAt(start, { type: "daily" }, 0)), "2028-02-27");
  assert.equal(formatISODate(doseDateAt(start, { type: "daily" }, 1)), "2028-02-28");
  assert.equal(formatISODate(doseDateAt(start, { type: "daily" }, 2)), "2028-02-29"); // leap day
  assert.equal(formatISODate(doseDateAt(start, { type: "daily" }, 3)), "2028-03-01");
});

test("doseDateAt: every-N-days across a month end", () => {
  const start = parseISODate("2026-01-30");
  assert.equal(formatISODate(doseDateAt(start, { type: "everyNDays", n: 3 }, 1)), "2026-02-02");
});

test("doseDateAt: specific weekdays vs every-N-days diverge", () => {
  const start = parseISODate("2026-01-01"); // a Thursday
  const weekdaySeq = [0, 1, 2, 3].map((i) =>
    formatISODate(doseDateAt(start, { type: "weekdays", days: [1, 3, 5] }, i))
  );
  assert.deepEqual(weekdaySeq, ["2026-01-02", "2026-01-05", "2026-01-07", "2026-01-09"]);

  const everyNSeq = [0, 1, 2, 3].map((i) =>
    formatISODate(doseDateAt(start, { type: "everyNDays", n: 2 }, i))
  );
  assert.deepEqual(everyNSeq, ["2026-01-01", "2026-01-03", "2026-01-05", "2026-01-07"]);
  assert.notDeepEqual(weekdaySeq, everyNSeq);
});

test("doseDateAt: N times a week spreads evenly", () => {
  const start = parseISODate("2026-01-05");
  const seq = [0, 1, 2, 3].map((i) => formatISODate(doseDateAt(start, { type: "timesPerWeek", n: 2 }, i)));
  assert.deepEqual(seq, ["2026-01-05", "2026-01-09", "2026-01-12", "2026-01-16"]);
});

// --------------------------------------------------------------- run-out
test("runOutCalc: basic daily schedule", () => {
  const r = runOutCalc({
    vialMg: 50,
    doseMg: 10,
    frequency: { type: "daily" },
    startDateISO: "2028-02-27",
    leadDays: 10
  });
  assert.equal(r.error, null);
  assert.equal(r.fullDoses, 5);
  assert.equal(r.lastDoseDate, "2028-03-02"); // crosses the leap day
  assert.equal(r.runOutDate, "2028-03-03");
  assert.equal(r.reorderByDate, "2028-02-22");
});

test("runOutCalc: dead-space waste per draw shortens the vial", () => {
  const withWaste = runOutCalc({
    vialMg: 25,
    doseMg: 2,
    wasteMgPerDraw: 0.25,
    frequency: { type: "daily" },
    startDateISO: "2026-01-01",
    leadDays: 5
  });
  assert.equal(withWaste.fullDoses, 11); // 25 / 2.25 = 11.11 -> floor 11
  assert.equal(withWaste.runOutDate, "2026-01-12");

  const withoutWaste = runOutCalc({
    vialMg: 25,
    doseMg: 2,
    frequency: { type: "daily" },
    startDateISO: "2026-01-01",
    leadDays: 5
  });
  assert.equal(withoutWaste.fullDoses, 12); // 25 / 2 = 12.5 -> floor 12
});

test("runOutCalc: refuses a vial that can't hold one full dose", () => {
  const r = runOutCalc({ vialMg: 1, doseMg: 5, frequency: { type: "daily" }, startDateISO: "2026-01-01" });
  assert.ok(r.error);
});

test("runOutCalc: reorder-by defaults to 10 days lead time", () => {
  const r = runOutCalc({
    vialMg: 30,
    doseMg: 10,
    frequency: { type: "daily" },
    startDateISO: "2026-06-01"
  });
  assert.equal(r.runOutDate, "2026-06-04");
  assert.equal(r.reorderByDate, "2026-05-25");
});

// --------------------------------------------------------------- half-life
test("halfLifeToHours converts days to hours", () => {
  assert.equal(halfLifeToHours(7, "days"), 168);
  assert.equal(halfLifeToHours(8, "hours"), 8);
  assert.equal(halfLifeToHours(0, "hours"), null);
});

test("amountAtTime: superposition at known points (dose=1, interval=halfLife=24h)", () => {
  // Single dose at t=0: after one half-life it's exactly half.
  assert.equal(amountAtTime(0, 1, 24, 24, 2), 1);
  assert.equal(amountAtTime(24, 1, 24, 24, 2), 1.5); // 0.5 left of dose 1 + 1 fresh from dose 2
  // At t=48: dose 1 (given at t=0) has decayed two half-lives -> 0.25;
  // dose 2 (given at t=24) has decayed one half-life -> 0.5. Total 0.75.
  assert.ok(Math.abs(amountAtTime(48, 1, 24, 24, 2) - 0.75) < 1e-9);
});

test("steady-state peak/trough ratio matches 2^(tau/halfLife)", () => {
  const peak = steadyStatePeak(24, 24);
  const trough = steadyStateTrough(24, 24);
  assert.ok(Math.abs(peak - 2) < 1e-9);
  assert.ok(Math.abs(trough - 1) < 1e-9);
  assert.ok(Math.abs(peakTroughRatio(24, 24) - 2) < 1e-9);
  assert.ok(Math.abs(peak / trough - peakTroughRatio(24, 24)) < 1e-9);
});

test("time to ~97% steady state is 5 half-lives", () => {
  assert.equal(timeToSteadyStateHours(24), 120);
  assert.equal(timeToSteadyStateHours(168), 840);
});

// ----------------------------------------------------------------- syringe
test("concentration and mL-for-dose arithmetic", () => {
  assert.equal(concentrationMgPerMl(10, 2), 5);
  assert.equal(mlForDose(2.5, 5), 0.5);
});

test("U-100 units: 1 unit = 0.01 mL", () => {
  assert.equal(unitsToDraw(2, 10), 20); // 0.2 mL * 100
  assert.equal(unitsToDraw(0.5, 5), 10); // 0.1 mL * 100
});

test("U-100 units formatting never drops a trailing zero (the reconstitution bug)", () => {
  const units = unitsToDraw(10, 5); // 2 mL -> 200 units territory checked separately; use a clean 20u case
  assert.equal(fmt(unitsToDraw(2, 10), 0), "20");
  assert.equal(fmt(unitsToDraw(1, 1), 0), "100");
});

test("syringeWarning flags under 1 unit and over-barrel doses", () => {
  assert.equal(syringeWarning(20, 100), null);
  assert.ok(syringeWarning(0.5, 100));
  assert.ok(syringeWarning(150, 100));
});

// ---------------------------------------------------------- reconstitution
test("reconstitute: 5 mg in 2 mL, 0.25 mg draw -> 2.5 mg/mL, 0.1 mL, 10 units, 20 doses", () => {
  const r = reconstitute({ vialMg: 5, waterMl: 2, doseMg: 0.25, barrelUnits: 100 });
  assert.equal(r.error, null);
  assert.equal(r.concMgPerMl, 2.5);
  assert.equal(fmt(r.mlPerDose, 3), "0.1");
  assert.equal(fmt(r.units, 1), "10");
  assert.equal(r.dosesInVial, 20);
  assert.equal(r.warning, null);
});

test("reconstitute: a mcg draw converted by toMg; whole-number units keep their zeros", () => {
  const r = reconstitute({ vialMg: 10, waterMl: 1, doseMg: toMg(2000, "mcg", null), barrelUnits: 100 });
  assert.equal(fmt(r.units, 1), "20");
  assert.equal(r.dosesInVial, 5);
});

test("reconstitute: warns when the draw does not fit the syringe or is under 1 unit", () => {
  assert.ok(reconstitute({ vialMg: 5, waterMl: 0.5, doseMg: 4, barrelUnits: 30 }).warning); // 40 units on a 30-unit barrel
  assert.ok(reconstitute({ vialMg: 5, waterMl: 5, doseMg: 0.005, barrelUnits: 100 }).warning); // 0.5 unit
});

test("reconstitute: refuses missing or zero inputs", () => {
  assert.ok(reconstitute({ vialMg: 0, waterMl: 2, doseMg: 1 }).error);
  assert.ok(reconstitute({ vialMg: 5, waterMl: 0, doseMg: 1 }).error);
  assert.ok(reconstitute({ vialMg: 5, waterMl: 2, doseMg: 0 }).error);
  assert.ok(reconstitute().error);
});

test("dosesPerVial floors and survives float noise", () => {
  assert.equal(dosesPerVial(5, 0.25), 20);
  assert.equal(dosesPerVial(1, 0.1), 10);
  assert.equal(dosesPerVial(0.3, 0.1), 3); // 0.3 / 0.1 is 2.9999999999999996 without the epsilon
  assert.equal(dosesPerVial(5, 2), 2);
  assert.equal(dosesPerVial(0, 1), null);
});

// --------------------------------------------------------- days of supply
test("daysOfSupply: 60 on hand, 1 each, twice a day -> 30 days", () => {
  const r = daysOfSupply({ onHand: 60, perDose: 1, schedule: { type: "perDay", n: 2 }, startDateISO: "2026-10-17", leadDays: 7 });
  assert.equal(r.error, null);
  assert.equal(r.totalDoses, 60);
  assert.equal(r.days, 30);
  assert.equal(r.coveredThroughDate, "2026-11-15");
  assert.equal(r.runOutDate, "2026-11-16");
  assert.equal(r.reorderByDate, "2026-11-09");
});

test("daysOfSupply: a leftover partial day does not count (61 pills, twice a day)", () => {
  const r = daysOfSupply({ onHand: 61, perDose: 1, schedule: { type: "perDay", n: 2 }, startDateISO: "2026-10-17" });
  assert.equal(r.days, 30);
});

test("daysOfSupply: several per dose, and fractions of a unit", () => {
  assert.equal(daysOfSupply({ onHand: 30, perDose: 2, schedule: { type: "perDay", n: 1 }, startDateISO: "2026-01-01" }).days, 15);
  assert.equal(daysOfSupply({ onHand: 30, perDose: 0.5, schedule: { type: "perDay", n: 1 }, startDateISO: "2026-01-01" }).days, 60);
});

test("daysOfSupply: every N days counts each dose as N days", () => {
  const r = daysOfSupply({ onHand: 10, perDose: 1, schedule: { type: "everyNDays", n: 3 }, startDateISO: "2026-01-01", leadDays: 5 });
  assert.equal(r.days, 30);
  assert.equal(r.runOutDate, "2026-01-31");
  assert.equal(r.coveredThroughDate, "2026-01-30");
  assert.equal(r.reorderByDate, "2026-01-26");
});

test("daysOfSupply: crosses a leap day and defaults the reorder lead to 7 days", () => {
  const r = daysOfSupply({ onHand: 5, perDose: 1, schedule: { type: "perDay", n: 1 }, startDateISO: "2028-02-27" });
  assert.equal(r.runOutDate, "2028-03-03");
  assert.equal(r.reorderByDate, "2028-02-25");
});

test("daysOfSupply: refuses bad input", () => {
  const ok = { onHand: 30, perDose: 1, schedule: { type: "perDay", n: 1 }, startDateISO: "2026-01-01" };
  assert.ok(daysOfSupply({ ...ok, onHand: 0 }).error);
  assert.ok(daysOfSupply({ ...ok, perDose: 0 }).error);
  assert.ok(daysOfSupply({ ...ok, schedule: { type: "perDay", n: 0 } }).error);
  assert.ok(daysOfSupply({ ...ok, startDateISO: "nope" }).error);
  assert.ok(daysOfSupply({ ...ok, onHand: 1, perDose: 2 }).error); // under one full dose
  assert.ok(daysOfSupply({ ...ok, onHand: 3, schedule: { type: "perDay", n: 4 } }).error); // under one full day
  assert.ok(daysOfSupply().error);
});

// ------------------------------------------------------------- vitamin D
test("vitamin D: 1 mcg = 40 IU, both directions", () => {
  assert.equal(iuToMcg(1000), 25);
  assert.equal(iuToMcg(40), 1);
  assert.equal(mcgToIu(25), 1000);
  assert.equal(mcgToIu(0.5), 20);
  assert.equal(iuToMcg(0), 0);
});

test("vitamin D: round trip returns the starting number, bad input returns null", () => {
  assert.equal(mcgToIu(iuToMcg(2000)), 2000);
  assert.equal(iuToMcg(-1), null);
  assert.equal(iuToMcg(NaN), null);
  assert.equal(mcgToIu(null), null);
  assert.equal(mcgToIu(Infinity), null);
});

// ----------------------------------------------------------- testosterone
test("testosterone: ng/dL -> nmol/L divides by 28.84", () => {
  assert.equal(fmt(ngdlToNmolL(300), 1), "10.4");
  assert.equal(fmt(ngdlToNmolL(28.84), 2), "1");
  assert.equal(ngdlToNmolL(0), 0);
});

test("testosterone: nmol/L -> ng/dL multiplies by 28.84", () => {
  assert.equal(fmt(nmolLToNgdl(10), 1), "288.4");
  assert.equal(fmt(nmolLToNgdl(1), 2), "28.84");
});

test("testosterone: multiplying by 0.0347 agrees to within 0.1 percent", () => {
  assert.ok(Math.abs(ngdlToNmolL(500) - 500 * 0.0347) / ngdlToNmolL(500) < 0.001);
});

test("testosterone: round trip and bad input", () => {
  assert.ok(Math.abs(nmolLToNgdl(ngdlToNmolL(450)) - 450) < 1e-9);
  assert.equal(ngdlToNmolL(-5), null);
  assert.equal(nmolLToNgdl(undefined), null);
});
