// Gallery album slideshows. Each element with [data-slideshow] runs its own
// independent slideshow — no dependency, no framework, since this is a
// single small interaction repeated across cards.
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-slideshow]").forEach(function (album) {
        var slides = Array.prototype.slice.call(album.querySelectorAll("[data-slide]"));
        var dots = Array.prototype.slice.call(album.querySelectorAll("[data-slide-dot]"));
        var counter = album.querySelector("[data-slide-current]");
        var prevBtn = album.querySelector("[data-slide-prev]");
        var nextBtn = album.querySelector("[data-slide-next]");
        var current = 0;

        if (slides.length <= 1) return; // nothing to page through

        function show(index) {
            current = (index + slides.length) % slides.length;
            slides.forEach(function (slide, i) {
                slide.classList.toggle("is-active", i === current);
            });
            dots.forEach(function (dot, i) {
                dot.classList.toggle("is-active", i === current);
            });
            if (counter) counter.textContent = current + 1;
        }

        if (prevBtn) prevBtn.addEventListener("click", function () { show(current - 1); });
        if (nextBtn) nextBtn.addEventListener("click", function () { show(current + 1); });
        dots.forEach(function (dot, i) {
            dot.addEventListener("click", function () { show(i); });
        });
    });
});
