// PlayNest — OTP verification UX

document.addEventListener("DOMContentLoaded", () => {
  const wrap = document.querySelector(".otp-inputs");
  const hidden = document.getElementById("otp_code");
  const form = document.getElementById("otpForm");
  if (!wrap || !hidden || !form) return;

  let isSubmitting = false;

  form.addEventListener("submit", (e) => {
    if (isSubmitting) {
      e.preventDefault();
      return false;
    }
    isSubmitting = true;
    const btn = form.querySelector('button[type="submit"]');
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = 'Verifying... <i class="fa-solid fa-spinner fa-spin ms-1"></i>';
    }
  });

  const boxes = [...wrap.querySelectorAll("input")];

  function sync() {
    hidden.value = boxes.map((b) => b.value).join("");
  }

  function submitIfComplete() {
    sync();
    if (!isSubmitting && hidden.value.length === 6 && boxes.every((b) => b.value.length === 1)) {
      if (typeof form.requestSubmit === "function") {
        form.requestSubmit();
      } else {
        form.submit();
      }
    }
  }

  boxes.forEach((box, i) => {
    box.addEventListener("input", () => {
      box.value = box.value.replace(/\D/g, "").slice(0, 1);
      if (box.value && boxes[i + 1]) boxes[i + 1].focus();
      sync();
      submitIfComplete();
    });

    box.addEventListener("keydown", (e) => {
      if (e.key === "Backspace" && !box.value && boxes[i - 1]) {
        boxes[i - 1].focus();
      }
    });

    box.addEventListener("paste", (e) => {
      e.preventDefault();
      const text = (e.clipboardData.getData("text") || "").replace(/\D/g, "").slice(0, boxes.length);
      text.split("").forEach((ch, idx) => {
        if (boxes[idx]) boxes[idx].value = ch;
      });
      sync();
      const next = boxes[Math.min(text.length, boxes.length - 1)];
      if (next) next.focus();
      submitIfComplete();
    });
  });

  if (boxes[0]) boxes[0].focus();

  // Resend countdown
  const resendBtn = document.getElementById("resendBtn");
  const countdownEl = document.getElementById("resendCountdown");
  let remaining = parseInt(resendBtn?.dataset.wait || "0", 10);

  function tick() {
    if (remaining <= 0) {
      if (resendBtn) { resendBtn.disabled = false; }
      if (countdownEl) countdownEl.textContent = "";
      return;
    }
    if (countdownEl) countdownEl.textContent = `Resend available in ${remaining}s`;
    if (resendBtn) resendBtn.disabled = true;
    remaining -= 1;
    setTimeout(tick, 1000);
  }
  tick();
});

