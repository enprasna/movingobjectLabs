const calculators = document.querySelectorAll(".calculator");

const formatNumber = (value) => {
  if (!Number.isFinite(value)) return "--";
  return new Intl.NumberFormat("en-US", { maximumSignificantDigits: 8 }).format(value);
};

calculators.forEach((form) => {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const result = form.closest(".formula-card").querySelector(".result");
    const output = result.querySelector("strong");
    const values = Object.fromEntries(new FormData(form).entries());
    const hasInvalidInput = Object.values(values).some((value) => value === "" || !Number.isFinite(Number(value)));

    if (hasInvalidInput) {
      output.textContent = "Enter both values";
      result.classList.add("error");
      return;
    }

    output.textContent = "Calculating...";
    result.classList.remove("error");

    try {
      const response = await fetch("/api/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ formula: form.dataset.calculator, values })
      });
      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || "Calculation failed");
      }

      output.innerHTML = `${formatNumber(payload.value)} <small>${payload.unit}</small>`;
    } catch (error) {
      output.textContent = error.message === "No real velocity for these values" ? error.message : "Python server unavailable";
      result.classList.add("error");
    }
  });
});
