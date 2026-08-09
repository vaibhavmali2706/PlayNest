// PlayNest — booking page interactions

document.addEventListener("DOMContentLoaded", () => {
  const root = document.querySelector("[data-booking-root]");
  if (!root) return;

  const turfId = root.dataset.turfId;
  const pricePerHour = parseFloat(root.dataset.price);
  const sports = JSON.parse(root.dataset.sports || "[]");

  const dateChips = document.querySelectorAll(".date-chip");
  const slotGrid = document.getElementById("slotGrid");
  const sportSelect = document.getElementById("sportSelect");
  const durationSelect = document.getElementById("durationSelect");
  const summaryPanel = document.getElementById("bookingSummary");
  const confirmBtn = document.getElementById("confirmBtn");
  const hiddenDate = document.getElementById("hiddenDate");
  const hiddenSlot = document.getElementById("hiddenSlot");

  let selectedDate = root.dataset.preselectDate;
  let selectedSlot = null;

  async function loadSlots(date) {
    slotGrid.innerHTML = `<div class="skeleton" style="height:44px;grid-column:span 3;"></div>`.repeat(6);
    selectedSlot = null;
    updateSummary();

    try {
      const res = await fetch(`/book/${turfId}/slots?date=${date}`);
      const data = await res.json();
      if (data.restricted) {
        slotGrid.innerHTML = `
          <div class="p-3 small" style="border-radius: var(--radius-sm); background: rgba(248,113,113,0.1); border: 1px solid rgba(248,113,113,0.25); color: var(--pn-danger); grid-column: 1 / -1;">
            <i class="fa-solid fa-circle-exclamation me-2"></i> ${data.message}
          </div>
        `;
        return;
      }
      renderSlots(data.slots);
    } catch (err) {
      slotGrid.innerHTML = `<p class="text-gray small">Couldn't load slots. Please try again.</p>`;
    }
  }

  function renderSlots(slots) {
    if (!slots.length) {
      slotGrid.innerHTML = `<p class="text-gray small">No slots available for this date.</p>`;
      return;
    }
    slotGrid.innerHTML = "";
    slots.forEach((slot) => {
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "slot-btn" + (slot.available ? "" : " taken");
      btn.textContent = slot.start;
      btn.disabled = !slot.available;
      btn.addEventListener("click", () => {
        document.querySelectorAll(".slot-btn.selected").forEach((b) => b.classList.remove("selected"));
        btn.classList.add("selected");
        selectedSlot = slot.start;
        updateSummary();
      });
      slotGrid.appendChild(btn);
    });
  }

  function updateSummary() {
    const duration = parseFloat(durationSelect.value);
    const sport = sportSelect.value;
    const total = Math.round(pricePerHour * duration);

    hiddenDate.value = selectedDate;
    hiddenSlot.value = selectedSlot || "";

    const ready = selectedDate && selectedSlot && sport;
    confirmBtn.disabled = !ready;

    summaryPanel.innerHTML = `
      <div class="pp-field">
        <div class="lbl">Sport</div>
        <div class="val">${sport || "—"}</div>
      </div>
      <div class="pp-field">
        <div class="lbl">Date</div>
        <div class="val">${selectedDate || "—"}</div>
      </div>
      <div class="pp-field">
        <div class="lbl">Time</div>
        <div class="val">${selectedSlot ? selectedSlot + " · " + duration + "h" : "—"}</div>
      </div>
      <div class="perforation my-3"></div>
      <div class="d-flex justify-content-between align-items-center">
        <span class="text-gray">Total</span>
        <span class="turf-price">₹${total}</span>
      </div>
    `;
  }

  dateChips.forEach((chip) => {
    chip.addEventListener("click", () => {
      dateChips.forEach((c) => c.classList.remove("selected"));
      chip.classList.add("selected");
      selectedDate = chip.dataset.date;
      loadSlots(selectedDate);
    });
  });

  sportSelect.addEventListener("change", updateSummary);
  durationSelect.addEventListener("change", updateSummary);

  loadSlots(selectedDate);
});
