(function () {
  const hero = document.getElementById("hero-slideshow");
  if (!hero) return;

  const slides = Array.from(hero.querySelectorAll(".hero__slide"));
  const dots = Array.from(hero.querySelectorAll(".hero__dot"));
  if (slides.length <= 1) return;

  const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  if (reducedMotion) return;

  const intervalMs = parseInt(hero.dataset.interval || "6000", 10);
  let current = 0;
  let timer = null;
  let paused = false;

  function show(index) {
    current = (index + slides.length) % slides.length;
    slides.forEach((slide, i) => {
      slide.classList.toggle("hero__slide--active", i === current);
    });
    dots.forEach((dot, i) => {
      dot.classList.toggle("hero__dot--active", i === current);
      dot.setAttribute("aria-selected", i === current ? "true" : "false");
    });
  }

  function next() {
    if (!paused) show(current + 1);
  }

  function startTimer() {
    stopTimer();
    timer = window.setInterval(next, intervalMs);
  }

  function stopTimer() {
    if (timer !== null) {
      window.clearInterval(timer);
      timer = null;
    }
  }

  dots.forEach((dot) => {
    dot.addEventListener("click", () => {
      show(parseInt(dot.dataset.index, 10));
      startTimer();
    });
  });

  const pauseTarget = hero.querySelector(".hero__slides");
  if (pauseTarget) {
    pauseTarget.addEventListener("mouseenter", () => {
      paused = true;
    });

    pauseTarget.addEventListener("mouseleave", () => {
      paused = false;
    });

    pauseTarget.addEventListener("focusin", () => {
      paused = true;
    });

    pauseTarget.addEventListener("focusout", (event) => {
      if (!pauseTarget.contains(event.relatedTarget)) {
        paused = false;
      }
    });
  }

  startTimer();
})();
