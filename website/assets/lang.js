(function () {
  "use strict";
  var KEY = "zettelapp-lang";
  var PREFIXES = {"": ["en"], "es": ["es"], "pt-br": ["pt"], "fr": ["fr"], "de": ["de"], "it": ["it"], "ru": ["ru"], "zh-cn": ["zh"], "ja": ["ja"], "ko": ["ko"], "ar": ["ar"]};
  var TRANSLATED = ["index", "what-is-zettelkasten", "tutorial", "getting-started", "notes-and-links", "link-suggestions", "graph-and-insights", "review-and-anki", "zotero", "ai-assistant", "mcp-server", "export-import", "keyboard-shortcuts", "privacy-and-security", "faq"];
  var FOLDERS = "es|pt\-br|fr|de|it|ru|zh\-cn|ja|ko|ar";

  function currentFolder(path) {
    var m = path.match(new RegExp("/(" + FOLDERS + ")(?:/|$)"));
    return m ? m[1] : "";
  }

  function targetPath(path, folder) {
    var docsRe = new RegExp("^(.*?)(?:/(" + FOLDERS + "))?/docs/(?:([a-z0-9-]+)\\.html)?$", "i");
    var m = path.match(docsRe);
    if (m) {
      var stem = m[3] || "index"; // m[2] is the language folder, if any
      if (folder && TRANSLATED.indexOf(stem) === -1) {
        return m[1] + "/" + folder + "/docs/";
      }
      return m[1] + (folder ? "/" + folder : "") + "/docs/" + stem + ".html";
    }
    var homeRe = new RegExp("^(.*?)(?:/(" + FOLDERS + "))?/(?:index\\.html)?$", "i");
    var hm = path.match(homeRe);
    if (hm) {
      return hm[1] + (folder ? "/" + folder + "/" : "/");
    }
    return null;
  }

  function detect() {
    var prefs = navigator.languages && navigator.languages.length
      ? navigator.languages
      : [navigator.language || "en"];
    for (var i = 0; i < prefs.length; i++) {
      var primary = String(prefs[i]).split("-")[0].toLowerCase();
      for (var folder in PREFIXES) {
        if (PREFIXES[folder].indexOf(primary) !== -1) return folder;
      }
    }
    return "";
  }

  try {
    var path = location.pathname;
    var here = currentFolder(path);
    var stored = localStorage.getItem(KEY);
    if (stored === null) {
      var want = detect();
      if (want !== here) {
        var dest = targetPath(path, want);
        if (dest && dest !== path) {
          localStorage.setItem(KEY, want);
          location.replace(dest + location.search + location.hash);
          return;
        }
      }
      localStorage.setItem(KEY, here);
    } else if (stored !== here) {
      localStorage.setItem(KEY, here);
    }
  } catch (e) {
    /* Storage blocked (e.g. private browsing): skip silently, no redirect. */
  }
})();
