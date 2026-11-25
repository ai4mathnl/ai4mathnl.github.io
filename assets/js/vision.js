// Fold-outs on /vision/. The page reads fine without this file: every fold-out
// is a native <details>. This adds the "Expand all" button, opens the fold-out
// that a link points into, and opens everything for printing.
(function () {
  var folds = Array.prototype.slice.call(document.querySelectorAll(".vision details"));
  var button = document.querySelector("[data-vision-toggle]");

  function allOpen() {
    return folds.every(function (fold) { return fold.open; });
  }

  function setAll(open) {
    folds.forEach(function (fold) { fold.open = open; });
  }

  if (button && folds.length) {
    var sync = function () {
      button.textContent = allOpen() ? "Collapse all" : "Expand all";
    };
    button.hidden = false;
    button.addEventListener("click", function () { setAll(!allOpen()); });
    folds.forEach(function (fold) { fold.addEventListener("toggle", sync); });
    sync();
  }

  // A link to a statement opens its fold-out; a link to something inside a
  // closed fold-out (a note's way back to the text, say) opens that one.
  function reveal() {
    var target = document.getElementById(decodeURIComponent(location.hash.slice(1)));
    if (!target) return;
    var own = target.classList.contains("statement") && target.querySelector("details");
    if (own) own.open = true;
    for (var el = target.parentElement; el; el = el.parentElement) {
      if (el.tagName === "DETAILS") el.open = true;
    }
    target.scrollIntoView();
  }

  window.addEventListener("hashchange", reveal);
  if (location.hash) reveal();

  // Paper has no fold-outs: print everything, then put the page back.
  var before = null;
  window.addEventListener("beforeprint", function () {
    before = folds.map(function (fold) { return fold.open; });
    setAll(true);
  });
  window.addEventListener("afterprint", function () {
    if (before) folds.forEach(function (fold, i) { fold.open = before[i]; });
    before = null;
  });
})();
