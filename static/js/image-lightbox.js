(function () {
  const openBtn = document.getElementById("detail-image-open");
  const dialog = document.getElementById("image-lightbox");
  const closeBtn = document.getElementById("lightbox-close");
  const lightboxImg = document.getElementById("lightbox-image");

  if (!openBtn || !dialog || !lightboxImg) return;

  function openLightbox() {
    const fullSrc = openBtn.dataset.fullSrc;
    if (fullSrc) {
      lightboxImg.src = fullSrc;
    }
    if (typeof dialog.showModal === "function") {
      dialog.showModal();
    }
  }

  function closeLightbox() {
    if (dialog.open) {
      dialog.close();
    }
  }

  openBtn.addEventListener("click", openLightbox);

  if (closeBtn) {
    closeBtn.addEventListener("click", closeLightbox);
  }

  dialog.addEventListener("click", (event) => {
    if (event.target === dialog) {
      closeLightbox();
    }
  });

})();
