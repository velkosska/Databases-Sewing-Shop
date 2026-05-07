(function () {
  "use strict";

  // Parse price from an option label like "Service Name  —  $25.00"
  function parseCatalogueItemOption(optionText) {
    // Matches "Name  —  $25.00" or "Name — $25.00"
    const match = String(optionText || "").match(/\$([0-9]+(?:\.[0-9]{1,2})?)(?:\s*)$/);
    if (!match) {
      // Fallback: legacy "(ServiceName) ($25.00)"
      const legacy = String(optionText || "").match(/^(.*)\s\(\$([0-9]+(?:\.[0-9]{1,2})?)\)$/);
      if (!legacy) return { name: "", basePrice: null };
      return { name: legacy[1].trim(), basePrice: parseFloat(legacy[2]) };
    }
    return {
      name: optionText.split(/\s*[—\-]\s*\$/)[0].trim(),
      basePrice: parseFloat(match[1]),
    };
  }

  function money(value) {
    return Number(value || 0).toFixed(2);
  }

  function parsePrice(value) {
    const n = parseFloat(String(value || "0").replace(",", "."));
    return isFinite(n) ? n : 0;
  }

  // ── Inline row behaviour ───────────────────────────────────────────────
  function attachRowBehavior(row) {
    if (!row || row.dataset.orderFlowBound === "true") return;

    // Support both catalogue_item (new) and catalogue (legacy) selects
    const catItemSelect = row.querySelector('select[name$="-catalogue_item"]');
    const catLegacySelect = row.querySelector('select[name$="-catalogue"]');
    const catalogueSelect = catItemSelect || catLegacySelect;

    const garmentInput = row.querySelector('input[name$="-garment_type"]');
    const quantityInput = row.querySelector('input[name$="-quantity"]');
    const unitPriceInput = row.querySelector('input[name$="-unit_price"]');
    const finalPriceInput = row.querySelector('input[name$="-final_price"]');
    let badge = row.querySelector(".order-flow-chip");

    if (!catalogueSelect || !quantityInput || !finalPriceInput) return;

    if (finalPriceInput) {
      finalPriceInput.addEventListener("input", function () {
        finalPriceInput.dataset.autofilled = "false";
        if (badge) { badge.className = "order-flow-chip modified"; badge.textContent = "Price modified"; }
      });
    }

    function applyAutoFill(forcePrice) {
      const selected = catalogueSelect.options[catalogueSelect.selectedIndex];
      const data = parseCatalogueItemOption(selected ? selected.text : "");
      if (!data.name || data.basePrice === null) return;

      if (garmentInput && !garmentInput.value.trim()) garmentInput.value = data.name;

      if (unitPriceInput && (!unitPriceInput.value || unitPriceInput.dataset.autofilled === "true")) {
        unitPriceInput.value = money(data.basePrice);
        unitPriceInput.dataset.autofilled = "true";
      }

      const quantity = parseInt(quantityInput.value || "1", 10);
      const linePrice = (isNaN(quantity) ? 1 : quantity) * data.basePrice;
      const canReplacePrice =
        forcePrice ||
        !finalPriceInput.value ||
        finalPriceInput.dataset.autofilled === "true";

      if (canReplacePrice) {
        finalPriceInput.value = money(linePrice);
        finalPriceInput.dataset.autofilled = "true";
        if (badge) { badge.className = "order-flow-chip autofilled"; badge.textContent = "✓ Price autofilled"; }
      }
      refreshOrderTotalPreview();
    }

    catalogueSelect.addEventListener("change", function () { applyAutoFill(true); });
    quantityInput.addEventListener("change", function () { applyAutoFill(false); });

    applyAutoFill(false);

    if (!badge) {
      badge = document.createElement("span");
      badge.className = "order-flow-chip autofilled";
      badge.textContent = "✓ Price autofilled";
      finalPriceInput.insertAdjacentElement("afterend", badge);
    }

    row.dataset.orderFlowBound = "true";
  }

  function bindRows() {
    document.querySelectorAll(".dynamic-items, .form-row").forEach(attachRowBehavior);
  }

  // ── Standalone OrderItem form ─────────────────────────────────────────
  function bindStandaloneOrderItemForm() {
    const catItemSelect = document.getElementById("id_catalogue_item");
    const catLegacySelect = document.getElementById("id_catalogue");
    const catalogueSelect = catItemSelect || catLegacySelect;

    const garmentInput = document.getElementById("id_garment_type");
    const quantityInput = document.getElementById("id_quantity");
    const unitPriceInput = document.getElementById("id_unit_price");
    const finalPriceInput = document.getElementById("id_final_price");

    if (!catalogueSelect || !finalPriceInput) return;
    if (catalogueSelect.dataset.orderFlowBound === "true") return;

    if (finalPriceInput) {
      finalPriceInput.addEventListener("input", function () {
        finalPriceInput.dataset.autofilled = "false";
      });
    }

    function applyAutoFill(forcePrice) {
      const selected = catalogueSelect.options[catalogueSelect.selectedIndex];
      const data = parseCatalogueItemOption(selected ? selected.text : "");
      if (!data.name || data.basePrice === null) return;

      if (garmentInput && !garmentInput.value.trim()) garmentInput.value = data.name;

      if (unitPriceInput && (!unitPriceInput.value || unitPriceInput.dataset.autofilled === "true")) {
        unitPriceInput.value = money(data.basePrice);
        unitPriceInput.dataset.autofilled = "true";
      }

      const quantity = parseInt(quantityInput ? quantityInput.value || "1" : "1", 10);
      const linePrice = (isNaN(quantity) ? 1 : quantity) * data.basePrice;
      const canReplacePrice =
        forcePrice || !finalPriceInput.value || finalPriceInput.dataset.autofilled === "true";

      if (canReplacePrice) {
        finalPriceInput.value = money(linePrice);
        finalPriceInput.dataset.autofilled = "true";
      }
    }

    catalogueSelect.addEventListener("change", function () { applyAutoFill(true); });
    if (quantityInput) quantityInput.addEventListener("change", function () { applyAutoFill(false); });

    applyAutoFill(false);
    catalogueSelect.dataset.orderFlowBound = "true";
  }

  // ── Order total preview panel ─────────────────────────────────────────
  function refreshOrderTotalPreview() {
    let total = 0;
    document.querySelectorAll(".dynamic-items, .form-row").forEach(function (row) {
      const deleteInput = row.querySelector('input[name$="-DELETE"]');
      if (deleteInput && deleteInput.checked) return;
      const qty = parsePrice(row.querySelector('input[name$="-quantity"]')?.value || "1");
      const price = parsePrice(row.querySelector('input[name$="-final_price"]')?.value || "0");
      total += qty > 0 ? price : 0;
    });

    const totalInput = document.getElementById("id_total_price");
    const label = document.getElementById("order-flow-total");
    if (label) label.textContent = money(total);
    if (totalInput && (!totalInput.value || totalInput.dataset.autofilled === "true")) {
      totalInput.value = money(total);
      totalInput.dataset.autofilled = "true";
    }
  }

  // ── Smart Order Flow panel ────────────────────────────────────────────
  function buildOrderPanel() {
    const customerInput = document.getElementById("id_customer");
    const firstFieldset = document.querySelector("fieldset.module, fieldset");
    if (!customerInput || !firstFieldset || document.getElementById("order-flow-panel")) return;

    const panel = document.createElement("div");
    panel.id = "order-flow-panel";
    panel.className = "order-flow-panel";
    panel.innerHTML = [
      "<h3>Smart Order Flow</h3>",
      '<div class="order-flow-grid">',
      '<div class="order-flow-kpi"><span>Customer</span><strong id="order-flow-customer">Not selected</strong></div>',
      '<div class="order-flow-kpi"><span>Previous Orders</span><strong id="order-flow-orders">—</strong></div>',
      '<div class="order-flow-kpi"><span>Live Total</span><strong>$<span id="order-flow-total">0.00</span></strong></div>',
      '<div class="order-flow-kpi"><span>Contact</span><strong id="order-flow-phone">—</strong></div>',
      "</div>",
      '<div id="order-flow-meta" style="margin-top:8px;font-size:12px;color:#475569;"></div>',
    ].join("");
    firstFieldset.parentNode.insertBefore(panel, firstFieldset);

    function updateCustomerSnapshot() {
      const id = customerInput.value;
      if (!id) {
        document.getElementById("order-flow-customer").textContent = "Not selected";
        document.getElementById("order-flow-orders").textContent = "—";
        document.getElementById("order-flow-phone").textContent = "—";
        document.getElementById("order-flow-meta").textContent = "";
        return;
      }
      fetch("/shop/api/customer/" + id + "/snapshot/")
        .then(r => r.ok ? r.json() : null)
        .then(data => {
          if (!data) return;
          document.getElementById("order-flow-customer").textContent = data.name;
          document.getElementById("order-flow-orders").textContent = data.orders_count || "0";
          document.getElementById("order-flow-phone").textContent = data.phone || "—";
          const meta = [data.email, data.address].filter(Boolean).join(" | ");
          document.getElementById("order-flow-meta").textContent = meta || "";
        });
    }

    customerInput.addEventListener("change", updateCustomerSnapshot);
    updateCustomerSnapshot();

    const totalInput = document.getElementById("id_total_price");
    if (totalInput) {
      totalInput.addEventListener("input", function () { totalInput.dataset.autofilled = "false"; });
    }
    refreshOrderTotalPreview();
  }

  // ── Init ─────────────────────────────────────────────────────────────
  document.addEventListener("DOMContentLoaded", function () {
    buildOrderPanel();
    bindRows();
    bindStandaloneOrderItemForm();
    refreshOrderTotalPreview();

    // Bind new inline rows added via "Add another…"
    document.querySelector(".add-row a")?.addEventListener("click", function () {
      window.setTimeout(function () { bindRows(); refreshOrderTotalPreview(); }, 80);
    });

    // MutationObserver fallback for dynamically added rows
    if (document.body) {
      new MutationObserver(function () {
        bindRows();
        bindStandaloneOrderItemForm();
        refreshOrderTotalPreview();
      }).observe(document.body, { childList: true, subtree: true });
    }

    document.body.addEventListener("input", function (e) {
      if (
        e.target.matches('input[name$="-final_price"]') ||
        e.target.matches('input[name$="-quantity"]') ||
        e.target.matches('input[name="total_price"]')
      ) {
        refreshOrderTotalPreview();
      }
    });
  });
})();
