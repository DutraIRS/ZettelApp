// Small touches for phones; every page works without it.
// - The header's menus (<details>) close when one of their links is followed (an in-page link
//   such as #features would otherwise leave the menu open over the page), on Escape, and when
//   another one opens.
// - A screenshot's link opens the picture being shown: the dark one in dark mode.
(function () {
  "use strict";
  var menus = document.querySelectorAll("details.menu, details.lang-switch, details.docs-menu");

  function closeAll(except) {
    for (var i = 0; i < menus.length; i++) {
      if (menus[i] !== except) menus[i].open = false;
    }
  }

  for (var i = 0; i < menus.length; i++) {
    menus[i].addEventListener("toggle", function (event) {
      if (event.target.open) closeAll(event.target);
    });
    menus[i].addEventListener("click", function (event) {
      if (event.target.closest && event.target.closest("a[href]")) this.open = false;
    });
  }

  document.addEventListener("keydown", function (event) {
    if (event.key !== "Escape") return;
    for (var i = 0; i < menus.length; i++) {
      if (menus[i].open) {
        menus[i].open = false;
        menus[i].querySelector("summary").focus();
      }
    }
  });

  var shots = document.querySelectorAll("a.shot-link");
  for (var j = 0; j < shots.length; j++) {
    shots[j].addEventListener("click", function () {
      var img = this.querySelector("img");
      if (img && img.currentSrc) this.href = img.currentSrc;
    });
  }
})();
