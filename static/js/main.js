// Article Blog — main UI script (dependency-free)
document.addEventListener("DOMContentLoaded", function () {
  // Smooth-scroll to top when navigating pagination / view toggles.
  document.querySelectorAll(".pagination a, .view-toggle .button").forEach(function (a) {
    a.addEventListener("click", function (e) {
      e.preventDefault();
      var target = a.getAttribute("href");
      if (target) {
        if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
          window.location.href = target;
        } else {
          window.scrollTo({ top: 0, behavior: "smooth" });
          setTimeout(function () { window.location.href = target; }, 220);
        }
      }
    });
  });

  // Live markdown preview in the admin article form.
  var source = document.getElementById("content_md");
  var preview = document.getElementById("markdown-preview");
  if (source && preview) {
    var update = function () {
      preview.textContent = source.value.slice(0, 2000) +
        (source.value.length > 2000 ? "\n…" : "");
    };
    source.addEventListener("input", update);
    update();
  }
});