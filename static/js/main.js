// PlayNest — global interactions

document.addEventListener("DOMContentLoaded", () => {
  // Navbar scroll state
  const navbar = document.querySelector(".pn-navbar");
  if (navbar) {
    const onScroll = () => navbar.classList.toggle("scrolled", window.scrollY > 30);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
  }

  // AOS
  if (window.AOS) {
    AOS.init({ duration: 700, once: true, offset: 60, easing: "ease-out-cubic" });
  }

  // GSAP hero entrance
  if (window.gsap) {
    gsap.from(".hero-eyebrow", { y: 20, opacity: 0, duration: 0.7, delay: 0.1 });
    gsap.from(".hero-title-line", {
      y: 40, opacity: 0, duration: 0.9, stagger: 0.12, delay: 0.2, ease: "power3.out",
    });
    gsap.from(".hero-sub", { y: 20, opacity: 0, duration: 0.8, delay: 0.55 });
    gsap.from(".hero-cta", { y: 20, opacity: 0, duration: 0.8, delay: 0.7, stagger: 0.1 });
    gsap.from(".hero-scroll-indicator", { opacity: 0, duration: 1, delay: 1.1 });
  }

  // Animated counters
  const counters = document.querySelectorAll("[data-counter]");
  if (counters.length) {
    const animateCounter = (el) => {
      const target = parseFloat(el.dataset.counter);
      const suffix = el.dataset.suffix || "";
      const decimals = el.dataset.counter.includes(".") ? 1 : 0;
      const duration = 1600;
      const start = performance.now();
      const step = (now) => {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        const value = target * eased;
        el.textContent = decimals ? value.toFixed(1) + suffix : Math.floor(value).toLocaleString() + suffix;
        if (progress < 1) requestAnimationFrame(step);
      };
      requestAnimationFrame(step);
    };

    const io = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          animateCounter(entry.target);
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.4 });

    counters.forEach((c) => io.observe(c));
  }

  // Auto-dismiss flash toasts
  document.querySelectorAll(".flash-toast").forEach((toast, i) => {
    setTimeout(() => {
      toast.style.transition = "opacity 0.4s ease, transform 0.4s ease";
      toast.style.opacity = "0";
      toast.style.transform = "translateX(20px)";
      setTimeout(() => toast.remove(), 400);
    }, 6000 + i * 300);
  });

  // Favourite toggle (turf cards + detail page)
  document.querySelectorAll("[data-fav-btn]").forEach((btn) => {
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      e.stopPropagation();
      const turfId = btn.dataset.favBtn;
      try {
        const res = await fetch(`/turfs/${turfId}/favourite`, { method: "POST" });
        if (res.status === 401) {
          window.location.href = `/login?next=${encodeURIComponent(window.location.pathname + window.location.search)}`;
          return;
        }
        const data = await res.json();
        
        // Sync all buttons for this turf ID on the page
        document.querySelectorAll(`[data-fav-btn="${turfId}"]`).forEach((b) => {
          b.classList.toggle("active", data.is_favourite);
          const icon = b.querySelector("i");
          if (icon) {
            if (data.is_favourite) {
              icon.className = "fa-solid fa-heart text-danger";
            } else {
              icon.className = "fa-regular fa-heart";
            }
          }
        });
      } catch (err) {
        console.error("Favourite toggle failed", err);
      }
    });
  });

  // Mobile nav toggle
  const navToggle = document.querySelector(".pn-nav-toggle");
  const navMenu = document.querySelector(".pn-nav-menu");
  if (navToggle && navMenu) {
    navToggle.addEventListener("click", () => navMenu.classList.toggle("open"));
  }

  // Password visibility toggle
  document.querySelectorAll(".btn-toggle-password").forEach((btn) => {
    btn.addEventListener("click", () => {
      const container = btn.closest(".position-relative");
      if (!container) return;
      const input = container.querySelector("input");
      if (!input) return;
      const isPassword = input.type === "password";
      input.type = isPassword ? "text" : "password";
      const icon = btn.querySelector("i");
      if (icon) {
        icon.className = isPassword ? "fa-regular fa-eye-slash" : "fa-regular fa-eye";
      }
    });
  });
});
