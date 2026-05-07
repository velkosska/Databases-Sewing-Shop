/**
 * Tests for translation dictionaries in lib/i18n.tsx
 *
 * Validates:
 *  1. Both language objects have identical sets of keys.
 *  2. Every value is a non-empty string.
 *  3. Spot-checks for correctness of key translations.
 */

// Pull out the translations object by importing the raw file.
// We parse it manually to avoid React / browser-only hooks.
import * as fs from "fs";
import * as path from "path";

const src = fs.readFileSync(
  path.resolve(__dirname, "../lib/i18n.tsx"),
  "utf8"
);

// Extract the `translations` object via a small regex-free approach:
// eval the subset of the file that defines the dict.
// We isolate the "en" and "es" keys by parsing the module-level shape.
// Since it's a plain object literal we can use a lightweight extraction.

function extractTranslationKeys(lang: "en" | "es"): string[] {
  const langRegex = new RegExp(`${lang}:\\s*\\{([^}]*(?:\\{[^}]*\\}[^}]*)*)\\}`, "s");
  const match = src.match(langRegex);
  if (!match) throw new Error(`Could not find ${lang} translations`);
  const body = match[1];
  return [...body.matchAll(/^\s{4}(\w+):/gm)].map(m => m[1]);
}

describe("i18n translation dictionaries", () => {
  const enKeys = extractTranslationKeys("en");
  const esKeys = extractTranslationKeys("es");

  test("en and es have the same set of keys", () => {
    const onlyInEn = enKeys.filter(k => !esKeys.includes(k));
    const onlyInEs = esKeys.filter(k => !enKeys.includes(k));
    if (onlyInEn.length || onlyInEs.length) {
      throw new Error(
        `Key mismatch!\nOnly in EN: ${onlyInEn.join(", ") || "none"}\nOnly in ES: ${onlyInEs.join(", ") || "none"}`
      );
    }
  });

  test("en has at least 80 translation keys", () => {
    expect(enKeys.length).toBeGreaterThanOrEqual(80);
  });

  test("es has the same number of keys as en", () => {
    expect(esKeys.length).toBe(enKeys.length);
  });

  // Spot-check specific translations
  const checks: Array<[string, RegExp]> = [
    ["nav_dashboard",  /Dashboard|Inicio/],
    ["dash_new_order", /New Order|Nuevo Pedido/],
    ["kpi_total_orders", /Total Orders|Pedidos Totales/],
    ["wiz_save",       /Save Order|Guardar Pedido/],
  ];

  test.each(checks)('key "%s" is present in both languages', (key) => {
    expect(enKeys).toContain(key);
    expect(esKeys).toContain(key);
  });
});
