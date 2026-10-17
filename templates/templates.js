/* Printable templates: everything runs in the page. Nothing typed here is sent
   anywhere or stored. Each typed value is mirrored into a plain text copy that
   only shows in print, so long entries wrap instead of being cut off. */
(function () {
  "use strict";

  var sheet = document.querySelector(".sheet");
  if (!sheet) return;

  function formatDate(v) {
    var m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(v || "");
    if (!m) return v || "";
    var d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
    try {
      return d.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
    } catch (e) {
      return v;
    }
  }

  function mirrorOf(el) {
    var next = el.nextElementSibling;
    return next && next.classList.contains("print-val") ? next : null;
  }

  function sync(el) {
    var span = mirrorOf(el);
    if (!span) return;
    span.textContent = el.type === "date" ? formatDate(el.value) : el.value;
  }

  function addMirrors(root) {
    var fields = root.querySelectorAll('input:not([type="checkbox"]), textarea');
    for (var i = 0; i < fields.length; i++) {
      var el = fields[i];
      if (mirrorOf(el)) continue;
      var span = document.createElement("div");
      span.className = "print-val";
      span.setAttribute("aria-hidden", "true");
      el.parentNode.insertBefore(span, el.nextSibling);
      sync(el);
    }
  }

  sheet.addEventListener("input", function (e) {
    if (e.target && e.target.matches && e.target.matches('input:not([type="checkbox"]), textarea')) sync(e.target);
  });
  sheet.addEventListener("change", function (e) {
    if (e.target && e.target.matches && e.target.matches('input[type="date"]')) sync(e.target);
  });

  addMirrors(sheet);
  sheet.classList.add("has-mirrors");

  var printBtn = document.querySelector("[data-print]");
  if (printBtn) printBtn.addEventListener("click", function () { window.print(); });

  var addBtn = document.querySelector("[data-add-row]");
  if (addBtn) {
    addBtn.addEventListener("click", function () {
      var body = sheet.querySelector("tbody");
      var rows = body.querySelectorAll("tr");
      var clone = rows[rows.length - 1].cloneNode(true);
      var old = clone.querySelectorAll(".print-val");
      for (var i = 0; i < old.length; i++) old[i].remove();
      var fields = clone.querySelectorAll("input, textarea");
      for (var j = 0; j < fields.length; j++) {
        if (fields[j].type === "checkbox") fields[j].checked = false;
        else fields[j].value = "";
        var label = fields[j].getAttribute("aria-label");
        if (label) fields[j].setAttribute("aria-label", label.replace(/\d+$/, String(rows.length + 1)));
      }
      body.appendChild(clone);
      addMirrors(clone);
      var first = clone.querySelector("input, textarea");
      if (first) first.focus();
    });
  }

  var clearBtn = document.querySelector("[data-clear]");
  if (clearBtn) {
    clearBtn.addEventListener("click", function () {
      if (!window.confirm("Clear everything you typed on this page?")) return;
      var fields = sheet.querySelectorAll("input, textarea");
      for (var i = 0; i < fields.length; i++) {
        if (fields[i].type === "checkbox") fields[i].checked = false;
        else fields[i].value = "";
        sync(fields[i]);
      }
    });
  }
})();
