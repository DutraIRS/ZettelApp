// Offer the downloads for the visitor's system. The page shows the Windows buttons (and a
// link to every release) by default, so it works without JavaScript; on a 64-bit Linux desktop
// this shows the Linux buttons instead: the .deb first (Debian, Ubuntu, Mint and most desktops),
// or the portable .tar.gz first on distributions that don't use .deb packages. On Android it
// shows the Google Play button instead, once the site has one (see GOOGLE_PLAY_LISTED in
// tools/website.py); until then Android visitors see the default buttons.
(function () {
  "use strict";
  var ua = navigator.userAgent || "";
  var platform = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || "";
  var system = platform + " " + ua;
  if (/android/i.test(system)) {
    var play = document.querySelectorAll('.actions[data-os="android"]');
    if (!play.length) return;
    var desktop = document.querySelectorAll('.actions[data-os="windows"]');
    for (var k = 0; k < desktop.length; k++) desktop[k].hidden = true;
    for (var m = 0; m < play.length; m++) play[m].hidden = false;
    return;
  }
  if (!/linux/i.test(system) || /android|cros/i.test(system)) return; // phones and Chromebooks too
  if (/aarch64|arm/i.test(system)) return; // the Linux builds are x86-64 only
  var noDeb = /fedora|red hat|centos|rocky|alma|opensuse|suse|arch|manjaro|endeavour|gentoo|nixos|alpine|void/i
    .test(ua);
  var windows = document.querySelectorAll('.actions[data-os="windows"]');
  var linux = document.querySelectorAll('.actions[data-os="linux"]');
  for (var i = 0; i < windows.length; i++) windows[i].hidden = true;
  for (var j = 0; j < linux.length; j++) {
    var box = linux[j];
    box.hidden = false;
    if (noDeb) {
      var deb = box.querySelector('[data-pkg="deb"]');
      var tar = box.querySelector('[data-pkg="tar"]');
      if (deb && tar) {
        deb.className = "button secondary";
        tar.className = "button primary";
        box.insertBefore(tar, deb);
      }
    }
  }
})();
