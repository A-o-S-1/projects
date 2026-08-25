// Small, dependency-free slideshow for gallery albums.
document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll("[data-slideshow]").forEach(function (slideshow) {
        var slides = Array.from(slideshow.querySelectorAll("[data-slide]"));
        var dots = Array.from(slideshow.querySelectorAll("[data-slide-dot]"));
        var counter = slideshow.querySelector("[data-slide-counter]");
        var previous = slideshow.querySelector("[data-slide-prev]");
        var next = slideshow.querySelector("[data-slide-next]");
        var current = 0;

        if (slides.length < 2) return;

        function show(index) {
            current = (index + slides.length) % slides.length;
            slides.forEach(function (slide, i) {
                var active = i === current;
                slide.classList.toggle("is-active", active);
                slide.setAttribute("aria-hidden", active ? "false" : "true");
            });
            dots.forEach(function (dot, i) {
                var active = i === current;
                dot.classList.toggle("is-active", active);
                dot.setAttribute("aria-current", active ? "true" : "false");
            });
            if (counter) counter.textContent = (current + 1) + " / " + slides.length;
        }

        previous.addEventListener("click", function () { show(current - 1); });
        next.addEventListener("click", function () { show(current + 1); });
        dots.forEach(function (dot) {
            dot.addEventListener("click", function () { show(Number(dot.dataset.slideDot)); });
        });

        slideshow.addEventListener("keydown", function (event) {
            if (event.key === "ArrowLeft") show(current - 1);
            if (event.key === "ArrowRight") show(current + 1);
        });
    });
});
