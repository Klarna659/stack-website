/* Sheet type switch for templates that come in two layouts (daily or weekly).
   Radios marked data-mode-switch choose which [data-mode-panel] is showing;
   only the showing layout is printed. Nothing is stored or sent. */
(function () {
  "use strict";

  var radios = document.querySelectorAll("[data-mode-switch]");
  var panels = document.querySelectorAll("[data-mode-panel]");
  if (!radios.length || !panels.length) return;

  function apply() {
    var chosen = null;
    for (var i = 0; i < radios.length; i++) if (radios[i].checked) chosen = radios[i].value;
    for (var j = 0; j < panels.length; j++) {
      panels[j].hidden = panels[j].getAttribute("data-mode-panel") !== chosen;
    }
  }

  for (var k = 0; k < radios.length; k++) radios[k].addEventListener("change", apply);
  apply();
})();
