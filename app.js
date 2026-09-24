const calculators = document.querySelectorAll(".calculator");

const formatNumber = (value) => {
  if (!Number.isFinite(value)) return "--";
  return new Intl.NumberFormat("en-US", { maximumSignificantDigits: 8 }).format(value);
};

const calculate = async (form) => {
    const result = form.closest(".formula-card").querySelector(".result");
    const output = result.querySelector(".result-value");
    const values = Object.fromEntries(new FormData(form).entries());
    const target = values.target;
    delete values.target;
    const inputs = Object.entries(values).filter(([name]) => name !== target);
    form.querySelectorAll("input[name]").forEach((input) => {
      const field = input.closest("label");
      const isTarget = input.name === target;
      field.classList.toggle("calculated", isTarget);
      input.disabled = isTarget;
    });
    const hasInvalidInput = inputs.some(([, value]) => value === "" || !Number.isFinite(Number(value)));

    if (hasInvalidInput) {
      output.textContent = "--";
      result.classList.add("error");
      return;
    }

    result.querySelector("b").textContent = target === "initialVelocity" ? "u" : target === "finalVelocity" ? "v" : target === "acceleration" ? "a" : target === "displacement" ? "s" : "t";
    output.textContent = "...";
    result.classList.remove("error");

    try {
      const response = await fetch("/api/calculate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ formula: form.dataset.calculator, target, values: Object.fromEntries(inputs) })
      });
      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.error || "Calculation failed");
      }

      output.textContent = formatNumber(payload.value);
      result.querySelector("small").textContent = payload.unit;
    } catch (error) {
      output.textContent = error.message;
      result.classList.add("error");
    }
};

calculators.forEach((form) => {
  form.addEventListener("input", () => calculate(form));
  form.addEventListener("change", () => calculate(form));
  calculate(form);
});
