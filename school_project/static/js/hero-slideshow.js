// Homepage hero slideshow — auto-advances on a timer, no user controls
// needed (this is a background showcase, not a browsable gallery, so we
// keep it simple: no dependency, no arrows/dots, just a fade timer).
document.addEventListener("DOMContentLoaded", function () {
    var container = document.querySelector("[data-hero-slideshow]");
    if (!container) return;

    var slides = Array.prototype.slice.call(container.querySelectorAll("[data-hero-slide]"));
    if (slides.length <= 1) return; // nothing to advance between

    var current = 0;
    var INTERVAL_MS = 5000;

    setInterval(function () {
        slides[current].classList.remove("is-active");
        current = (current + 1) % slides.length;
        slides[current].classList.add("is-active");
    }, INTERVAL_MS);
});
