"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { clsx } from "clsx";
import { SERVICES } from "./constants";
import { LandingNavbar } from "./Navbar";
import { FloatingWhatsApp } from "./FloatingWhatsApp";
import {
  createCustomerOrder,
  fetchCatalogue,
  type CustomerOrderItem,
  type CustomerMeasurements,
} from "@/lib/customerOrder";
import type { CatalogueItem } from "@/lib/api";

const MEAS_FIELDS: (keyof CustomerMeasurements)[] = [
  "bust", "waist", "hips", "shoulder", "sleeve", "length", "inseam", "neck",
];

const MEAS_LABELS: Record<keyof CustomerMeasurements, string> = {
  bust: "Contorno pecho",
  waist: "Cintura",
  hips: "Cadera",
  shoulder: "Hombro",
  sleeve: "Manga",
  length: "Largo",
  inseam: "Entrepierna",
  neck: "Cuello",
  notes: "Notas de medidas",
};

const SERVICES_NEED_MEASUREMENTS = new Set([
  "Reducción de tallas",
  "Modificación de ropa de hogar",
  "Arreglo de prendas de motoristas",
]);

function itemNeedsMeasurements(serviceType: string, catalogueItem?: CatalogueItem): boolean {
  if (catalogueItem?.requires_measurements) return true;
  return SERVICES_NEED_MEASUREMENTS.has(serviceType);
}

function hasMeasurementValues(meas: CustomerMeasurements): boolean {
  return Object.entries(meas).some(([, v]) => v.trim() !== "");
}

function emptyItem(): CustomerOrderItem {
  return {
    service_type: "",
    catalogue_item_id: "",
    catalogue_source: "catalogue_item",
    garment_type: "",
    color_fabric: "",
    item_notes: "",
    quantity: 1,
  };
}

function emptyMeasurements(): CustomerMeasurements {
  return { bust: "", waist: "", hips: "", shoulder: "", sleeve: "", length: "", inseam: "", neck: "", notes: "" };
}

function InfoBubbleIcon() {
  return (
    <svg className="landing-info-bubble__icon" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  );
}

function InfoBubble({ title, children }: { title?: string; children: React.ReactNode }) {
  return (
    <aside className="landing-info-bubble" role="note">
      <InfoBubbleIcon />
      <div>
        {title && <p className="landing-info-bubble__title">{title}</p>}
        {children}
      </div>
    </aside>
  );
}

export function CustomerOrderForm() {
  const [step, setStep] = useState(1);
  const [catalogue, setCatalogue] = useState<CatalogueItem[]>([]);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successOrderId, setSuccessOrderId] = useState<number | null>(null);

  const [customer, setCustomer] = useState({
    first_name: "",
    last_name: "",
    phone: "",
    email: "",
    address: "",
    notes: "",
  });

  const [items, setItems] = useState<CustomerOrderItem[]>([emptyItem()]);
  const [dueDate, setDueDate] = useState("");
  const [orderNotes, setOrderNotes] = useState("");
  const [deliveryMethod, setDeliveryMethod] = useState<"pickup" | "home_delivery">("pickup");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [measurements, setMeasurements] = useState<CustomerMeasurements>(emptyMeasurements());
  const [showMeasurementsForm, setShowMeasurementsForm] = useState(false);

  useEffect(() => {
    fetchCatalogue().then(setCatalogue).catch(() => setCatalogue([]));
  }, []);

  useEffect(() => {
    if (step !== 3) setShowMeasurementsForm(false);
  }, [step]);

  const needsMeasurements = items.some((it) => {
    const cat = catalogue.find((c) => String(c.id) === it.catalogue_item_id);
    return itemNeedsMeasurements(it.service_type, cat);
  });

  function updateItem(index: number, patch: Partial<CustomerOrderItem>) {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, ...patch } : it)));
  }

  function onCataloguePick(index: number, catId: string) {
    const cat = catalogue.find((c) => String(c.id) === catId);
    updateItem(index, {
      catalogue_item_id: catId,
      catalogue_source: cat?.source ?? "catalogue_item",
      service_type: cat?.name ?? items[index].service_type,
      garment_type: items[index].garment_type || cat?.name || "",
    });
  }

  function validateStep(): string | null {
    if (step === 1) {
      if (!customer.first_name.trim() || !customer.last_name.trim()) return "Nombre y apellidos son obligatorios.";
      if (!customer.phone.trim()) return "El teléfono es obligatorio para contactarte.";
    }
    if (step === 2) {
      if (items.some((it) => !it.service_type)) return "Elige un tipo de servicio para cada prenda.";
      if (items.some((it) => !it.garment_type.trim())) return "Describe la prenda (por ejemplo: pantalón, vestido).";
    }
    if (step === 3 && deliveryMethod === "home_delivery" && !deliveryAddress.trim()) {
      return "Indica la dirección de entrega.";
    }
    return null;
  }

  function nextStep() {
    const err = validateStep();
    if (err) {
      setError(err);
      return;
    }
    setError(null);
    setStep((s) => Math.min(4, s + 1));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function submit() {
    const err = validateStep();
    if (err) {
      setError(err);
      return;
    }
    setSubmitting(true);
    setError(null);

    const measPayload = Object.fromEntries(
      Object.entries(measurements).map(([k, v]) => [k, v.trim() ? v : null]),
    );

    try {
      const result = await createCustomerOrder({
        source: "web",
        new_customer: {
          first_name: customer.first_name.trim(),
          last_name: customer.last_name.trim(),
          phone: customer.phone.trim(),
          email: customer.email.trim(),
          address: customer.address.trim(),
          notes: customer.notes.trim(),
        },
        items: items.map((it) => {
          const cat = catalogue.find((c) => String(c.id) === it.catalogue_item_id);
          const needsMeas = itemNeedsMeasurements(it.service_type, cat);
          const includeMeas = needsMeas || hasMeasurementValues(measurements);
          return {
            catalogue_item_id: it.catalogue_item_id ? Number(it.catalogue_item_id) : null,
            catalogue_source: cat?.source ?? it.catalogue_source,
            service_type: it.service_type,
            garment_type: it.garment_type.trim() || it.service_type,
            color_fabric: it.color_fabric.trim(),
            unit_price: cat ? String(cat.base_price) : "0",
            quantity: it.quantity,
            item_notes: it.item_notes.trim(),
            requires_measurements: needsMeas,
            measurements: includeMeas ? measPayload : {},
          };
        }),
        due_date: dueDate || null,
        priority: "normal",
        order_notes: orderNotes.trim(),
        internal_notes: "",
        delivery_method: deliveryMethod,
        delivery_address: deliveryAddress.trim(),
        delivery_date: null,
        deposit_method: "",
        deposit_amount: "0",
        measurements: needsMeasurements || hasMeasurementValues(measurements) ? measPayload : {},
      });
      setSuccessOrderId(result.order_id);
      window.scrollTo({ top: 0, behavior: "smooth" });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Error de red. ¿Está encendido el servidor?");
      setSubmitting(false);
    }
  }

  if (successOrderId) {
    return (
      <div className="landing-root min-h-screen">
        <LandingNavbar />
        <main className="mx-auto max-w-lg px-5 py-24 text-center">
          <div className="landing-feature-card p-8">
            <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
              <svg className="w-7 h-7" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24" aria-hidden>
                <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="font-[family-name:var(--font-playfair)] text-2xl text-[var(--landing-ink)]">
              ¡Pedido recibido!
            </h1>
            <p className="mt-4 text-[var(--landing-muted)] leading-relaxed">
              Tu solicitud <strong>#{successOrderId}</strong> ya está en el taller. Paqui revisará los detalles y te
              contactará para confirmar presupuesto y fecha.
            </p>
            <Link href="/" className="landing-btn landing-btn--primary mt-8 min-h-12 inline-flex w-full">
              Volver al inicio
            </Link>
          </div>
        </main>
        <FloatingWhatsApp />
      </div>
    );
  }

  return (
    <div className="landing-root min-h-screen pb-16">
      <LandingNavbar />

      <main className="mx-auto max-w-2xl px-5 pt-24 sm:px-8">
        <Link href="/" className="text-sm text-[var(--landing-muted)] hover:text-[var(--landing-accent-deep)]">
          ← Volver al inicio
        </Link>
        <h1 className="mt-4 font-[family-name:var(--font-playfair)] text-3xl text-[var(--landing-ink)]">
          Hacer pedido
        </h1>
        <p className="mt-2 text-[var(--landing-muted)]">
          Cuéntanos qué necesitas. Los mismos datos que Paqui registraría en el taller — sin compromiso hasta confirmar
          presupuesto.
        </p>

        {/* Step indicator */}
        <ol className="mt-8 flex gap-2" aria-label="Pasos del formulario">
          {[1, 2, 3, 4].map((n) => (
            <li
              key={n}
              className={clsx(
                "h-1.5 flex-1 rounded-full transition-colors",
                step >= n ? "bg-[var(--landing-accent-deep)]" : "bg-[var(--landing-border)]",
              )}
              aria-current={step === n ? "step" : undefined}
            />
          ))}
        </ol>
        <p className="mt-2 text-xs text-[var(--landing-muted)]">Paso {step} de 4</p>

        {error && (
          <div className="mt-6 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700" role="alert">
            {error}
          </div>
        )}

        <div className="mt-8 space-y-6">
          {/* Step 1 — Contacto */}
          {step === 1 && (
            <div className="landing-order-card space-y-4">
              <h2 className="font-semibold text-[var(--landing-ink)]">Tus datos de contacto</h2>
              <div className="grid gap-4 sm:grid-cols-2">
                <label className="block">
                  <span className="text-xs font-medium text-[var(--landing-muted)]">Nombre *</span>
                  <input
                    className="landing-input mt-1"
                    value={customer.first_name}
                    onChange={(e) => setCustomer((p) => ({ ...p, first_name: e.target.value }))}
                    autoComplete="given-name"
                  />
                </label>
                <label className="block">
                  <span className="text-xs font-medium text-[var(--landing-muted)]">Apellidos *</span>
                  <input
                    className="landing-input mt-1"
                    value={customer.last_name}
                    onChange={(e) => setCustomer((p) => ({ ...p, last_name: e.target.value }))}
                    autoComplete="family-name"
                  />
                </label>
              </div>
              <label className="block">
                <span className="text-xs font-medium text-[var(--landing-muted)]">Teléfono / WhatsApp *</span>
                <input
                  type="tel"
                  className="landing-input mt-1"
                  value={customer.phone}
                  onChange={(e) => setCustomer((p) => ({ ...p, phone: e.target.value }))}
                  autoComplete="tel"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-[var(--landing-muted)]">Email (opcional)</span>
                <input
                  type="email"
                  className="landing-input mt-1"
                  value={customer.email}
                  onChange={(e) => setCustomer((p) => ({ ...p, email: e.target.value }))}
                  autoComplete="email"
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-[var(--landing-muted)]">Dirección (opcional)</span>
                <input
                  className="landing-input mt-1"
                  value={customer.address}
                  onChange={(e) => setCustomer((p) => ({ ...p, address: e.target.value }))}
                  autoComplete="street-address"
                />
              </label>
            </div>
          )}

          {/* Step 2 — Prendas / servicios */}
          {step === 2 && (
            <div className="space-y-6">
              {items.map((item, index) => (
                <div key={index} className="landing-order-card space-y-4">
                  <div className="flex items-center justify-between">
                    <h2 className="font-semibold text-[var(--landing-ink)]">
                      {items.length > 1 ? `Prenda ${index + 1}` : "Tu pedido"}
                    </h2>
                    {items.length > 1 && (
                      <button
                        type="button"
                        className="text-xs text-red-600 hover:underline"
                        onClick={() => setItems((p) => p.filter((_, i) => i !== index))}
                      >
                        Quitar
                      </button>
                    )}
                  </div>
                  <label className="block">
                    <span className="text-xs font-medium text-[var(--landing-muted)]">Tipo de servicio *</span>
                    <select
                      className="landing-input mt-1"
                      value={item.service_type}
                      onChange={(e) => updateItem(index, { service_type: e.target.value })}
                    >
                      <option value="">Selecciona…</option>
                      {SERVICES.map((s) => (
                        <option key={s.title} value={s.title}>
                          {s.title}
                        </option>
                      ))}
                    </select>
                  </label>
                  {catalogue.length > 0 && (
                    <label className="block">
                      <span className="text-xs font-medium text-[var(--landing-muted)]">Del catálogo (opcional)</span>
                      <select
                        className="landing-input mt-1"
                        value={item.catalogue_item_id}
                        onChange={(e) => onCataloguePick(index, e.target.value)}
                      >
                        <option value="">—</option>
                        {catalogue.map((c) => (
                          <option key={c.id} value={c.id}>
                            {c.name}
                            {c.base_price > 0 ? ` (desde ${c.base_price} €)` : ""}
                          </option>
                        ))}
                      </select>
                    </label>
                  )}
                  <label className="block">
                    <span className="text-xs font-medium text-[var(--landing-muted)]">¿Qué prenda es? *</span>
                    <input
                      className="landing-input mt-1"
                      placeholder="Ej.: pantalón de vestir, vestido de fiesta…"
                      value={item.garment_type}
                      onChange={(e) => updateItem(index, { garment_type: e.target.value })}
                    />
                  </label>
                  <label className="block">
                    <span className="text-xs font-medium text-[var(--landing-muted)]">Color / tejido</span>
                    <input
                      className="landing-input mt-1"
                      placeholder="Ej.: azul marino, lana, piel…"
                      value={item.color_fabric}
                      onChange={(e) => updateItem(index, { color_fabric: e.target.value })}
                    />
                  </label>
                  <label className="block">
                    <span className="text-xs font-medium text-[var(--landing-muted)]">Detalles del arreglo</span>
                    <textarea
                      rows={3}
                      className="landing-input mt-1 resize-none"
                      placeholder="Cuéntanos qué necesitas: cremallera rota, entallar, largo…"
                      value={item.item_notes}
                      onChange={(e) => updateItem(index, { item_notes: e.target.value })}
                    />
                  </label>
                </div>
              ))}
              <button
                type="button"
                className="landing-btn landing-btn--ghost w-full min-h-12"
                onClick={() => setItems((p) => [...p, emptyItem()])}
              >
                + Añadir otra prenda
              </button>
            </div>
          )}

          {/* Step 3 — Fechas, entrega, medidas */}
          {step === 3 && (
            <div className="landing-order-card space-y-5">
              <h2 className="font-semibold text-[var(--landing-ink)]">Plazos y entrega</h2>

              <InfoBubble title="Plazos de entrega">
                <p>Cada prenda es distinta, así que el plazo depende del tipo de trabajo:</p>
                <ul>
                  <li>Arreglos sencillos (dobladillos, ajustes pequeños): 2–5 días laborables.</li>
                  <li>Prendas con varios arreglos o trabajos más complejos: 4–8 días laborables.</li>
                  <li>
                    Servicio urgente: algunos arreglos, como dobladillos de pantalones, pueden entregarse el mismo día
                    con un suplemento del 5&nbsp;% sobre el valor del arreglo.
                  </li>
                </ul>
                <p>
                  Paqui confirmará la fecha exacta y el presupuesto al revisar la prenda. Si tienes prisa, indícalo en
                  las notas del pedido.
                </p>
              </InfoBubble>

              <label className="block">
                <span className="text-xs font-medium text-[var(--landing-muted)]">¿Para cuándo lo necesitas?</span>
                <input
                  type="date"
                  className="landing-input mt-1"
                  value={dueDate}
                  onChange={(e) => setDueDate(e.target.value)}
                />
              </label>
              <label className="block">
                <span className="text-xs font-medium text-[var(--landing-muted)]">Notas generales del pedido</span>
                <textarea
                  rows={2}
                  className="landing-input mt-1 resize-none"
                  value={orderNotes}
                  onChange={(e) => setOrderNotes(e.target.value)}
                  placeholder="Urgencia, preferencias, horario para llamarte…"
                />
              </label>
              <div className="space-y-2">
                <p className="text-xs font-medium text-[var(--landing-muted)]">Recogida</p>
                {(
                  [
                    { key: "pickup" as const, label: "Recoger en el puesto (San Enrique, 16)", desc: "Te avisamos cuando esté listo" },
                    { key: "home_delivery" as const, label: "Entrega a domicilio", desc: "Paqui confirmará si es posible" },
                  ] as const
                ).map(({ key, label, desc }) => (
                  <button
                    key={key}
                    type="button"
                    onClick={() => setDeliveryMethod(key)}
                    className={clsx(
                      "w-full rounded-xl border px-4 py-3 text-left transition min-h-12",
                      deliveryMethod === key
                        ? "border-[var(--landing-accent-deep)] bg-[var(--landing-accent-soft)]"
                        : "border-[var(--landing-border)] hover:border-[var(--landing-accent)]",
                    )}
                  >
                    <span className="block text-sm font-semibold text-[var(--landing-ink)]">{label}</span>
                    <span className="block text-xs text-[var(--landing-muted)]">{desc}</span>
                  </button>
                ))}
              </div>
              {deliveryMethod === "home_delivery" && (
                <>
                  <InfoBubble>
                    <p>
                      <strong>¡Perfecto!</strong> Ten en cuenta que la entrega a domicilio lleva un pequeño coste
                      adicional según la distancia. No te preocupes, Paqui te escribirá por WhatsApp en cuanto reciba
                      tu pedido para darte todos los detalles y confirmar la entrega.
                    </p>
                  </InfoBubble>
                  <label className="block">
                    <span className="text-xs font-medium text-[var(--landing-muted)]">Dirección de entrega *</span>
                    <input
                      className="landing-input mt-1"
                      value={deliveryAddress}
                      onChange={(e) => setDeliveryAddress(e.target.value)}
                    />
                  </label>
                </>
              )}
              <div className="pt-2 border-t border-[var(--landing-border)] space-y-4">
                <InfoBubble>
                  <p>
                    <strong>Las medidas son opcionales.</strong> Si no las conoces o no las tienes a mano, no te
                    preocupes — Paqui las tomará en el taller cuando entregues la prenda.
                  </p>
                </InfoBubble>
                {!showMeasurementsForm ? (
                  <button
                    type="button"
                    onClick={() => setShowMeasurementsForm(true)}
                    className="landing-btn landing-btn--ghost w-full min-h-12 text-sm font-medium"
                  >
                    Conozco mis medidas
                  </button>
                ) : (
                  <>
                    <h3 className="text-sm font-semibold text-[var(--landing-ink)]">Medidas (cm)</h3>
                    <p className="text-xs text-[var(--landing-muted)]">
                      Recomendadas para este tipo de servicio. Si no las tienes a mano, Paqui las tomará en el taller.
                    </p>
                    <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-4">
                      {MEAS_FIELDS.map((f) => (
                        <label key={f} className="block">
                          <span className="text-xs text-[var(--landing-muted)]">{MEAS_LABELS[f]}</span>
                          <input
                            type="number"
                            step="0.5"
                            className="landing-input mt-1"
                            value={measurements[f]}
                            onChange={(e) => setMeasurements((p) => ({ ...p, [f]: e.target.value }))}
                          />
                        </label>
                      ))}
                    </div>
                    <label className="block mt-3">
                      <span className="text-xs text-[var(--landing-muted)]">{MEAS_LABELS.notes}</span>
                      <textarea
                        rows={2}
                        className="landing-input mt-1 resize-none"
                        value={measurements.notes}
                        onChange={(e) => setMeasurements((p) => ({ ...p, notes: e.target.value }))}
                      />
                    </label>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Step 4 — Resumen */}
          {step === 4 && (
            <div className="landing-order-card space-y-4 text-sm">
              <h2 className="font-semibold text-[var(--landing-ink)] text-base">Resumen</h2>
              <div>
                <p className="text-xs font-medium text-[var(--landing-muted)]">Contacto</p>
                <p className="text-[var(--landing-ink)]">
                  {customer.first_name} {customer.last_name} · {customer.phone}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium text-[var(--landing-muted)]">Prendas</p>
                <ul className="mt-1 space-y-2">
                  {items.map((it, i) => (
                    <li key={i} className="rounded-lg bg-[var(--landing-surface)] p-3">
                      <strong>{it.service_type}</strong> — {it.garment_type}
                      {it.color_fabric && <span className="text-[var(--landing-muted)]"> ({it.color_fabric})</span>}
                      {it.item_notes && <p className="text-xs text-[var(--landing-muted)] mt-1">{it.item_notes}</p>}
                    </li>
                  ))}
                </ul>
              </div>
              {dueDate && (
                <p>
                  <span className="text-[var(--landing-muted)]">Fecha deseada: </span>
                  {dueDate}
                </p>
              )}
              <p>
                <span className="text-[var(--landing-muted)]">Recogida: </span>
                {deliveryMethod === "pickup" ? "En el puesto" : deliveryAddress}
              </p>
              <p className="text-xs text-[var(--landing-muted)] border-t border-[var(--landing-border)] pt-4">
                El precio final lo confirma Paqui contigo. Este pedido aparecerá en su panel como pendiente de revisión.
              </p>
            </div>
          )}
        </div>

        <div className="mt-8 flex justify-between gap-4">
          <button
            type="button"
            onClick={() => {
              setStep((s) => Math.max(1, s - 1));
              setError(null);
            }}
            className={clsx("landing-btn landing-btn--ghost min-h-12 px-6", step === 1 && "invisible")}
          >
            Atrás
          </button>
          {step < 4 ? (
            <button type="button" onClick={nextStep} className="landing-btn landing-btn--primary min-h-12 px-8">
              Continuar
            </button>
          ) : (
            <button
              type="button"
              onClick={submit}
              disabled={submitting}
              className={clsx(
                "landing-btn landing-btn--primary min-h-12 px-8",
                submitting && "opacity-60 cursor-not-allowed",
              )}
            >
              {submitting ? "Enviando…" : "Enviar pedido"}
            </button>
          )}
        </div>
      </main>
      <FloatingWhatsApp />
    </div>
  );
}
