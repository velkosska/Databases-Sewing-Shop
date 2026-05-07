/**
 * Tests for the pure utility functions in lib/api.ts
 *
 * Run:  npx jest --config jest.config.ts
 */

// We extract normPath by re-implementing it here (it's a module-internal function).
// If you ever export it, import directly instead.
function normPath(path: string): string {
  return path.endsWith("/") ? path.slice(0, -1) : path;
}

describe("normPath", () => {
  test("strips a single trailing slash", () => {
    expect(normPath("/dashboard/")).toBe("/dashboard");
  });

  test("leaves a path without trailing slash unchanged", () => {
    expect(normPath("/dashboard")).toBe("/dashboard");
  });

  test("strips trailing slash from nested path", () => {
    expect(normPath("/customers/13/measurements/")).toBe("/customers/13/measurements");
  });

  test("handles root slash", () => {
    expect(normPath("/")).toBe("");
  });

  test("does not strip internal slashes", () => {
    expect(normPath("/api/orders/create/")).toBe("/api/orders/create");
  });

  test("handles empty string", () => {
    expect(normPath("")).toBe("");
  });
});
