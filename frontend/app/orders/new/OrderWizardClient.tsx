"use client";
import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import { clsx } from "clsx";
import { CatalogueItem, Customer, Employee, Material } from "@/lib/api";
import { DJANGO_URL } from "@/lib/django";
import { useI18n } from "@/lib/i18n";

interface Props {
  catalogue: CatalogueItem[];
  employees: Employee[];
  customers: Array<{ id: number; name: string; phone: string; email: string; address: string; order_count: number }>;
  materials: Material[];
  fromAdmin?: boolean;
}

interface OrderItem {
  catalogue_item_id: string;
  catalogue_source: string;
  garment_type: string;
  color_fabric: string;
  unit_price: string;
  quantity: number;
  item_notes: string;
  assigned_employee_id: string;
  price_overridden: boolean;
  requires_measurements: boolean;
  measurements: Record<string, string | null>;
}

interface Measurements {
  bust: string; waist: string; hips: string; shoulder: string;
  sleeve: string; length: string; inseam: string; neck: string; notes: string;
}

const MEAS_FIELDS: (keyof Measurements)[] = ["bust","waist","hips","shoulder","sleeve","length","inseam","neck"];

const STEP_KEYS = [
  { n: 1, labelKey: "step1_label" as const, descKey: "step1_desc" as const },
  { n: 2, labelKey: "step2_label" as const, descKey: "step2_desc" as const },
  { n: 3, labelKey: "step3_label" as const, descKey: "step3_desc" as const },
  { n: 4, labelKey: "step4_label" as const, descKey: "step4_desc" as const },
];

function money(v: string | number) {
  return `$${Number(v || 0).toFixed(2)}`;
}

function nameToHsl(name: string) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h);
  return `hsl(${Math.abs(h % 360)}, 56%, 42%)`;
}

function initials(name: string) {
  const p = name.trim().split(" ");
  return (p[0][0] + (p[1]?.[0] ?? "")).toUpperCase();
}

function emptyItem(): OrderItem {
  return {
    catalogue_item_id: "", catalogue_source: "catalogue_item",
    garment_type: "", color_fabric: "", unit_price: "0.00",
    quantity: 1, item_notes: "", assigned_employee_id: "",
    price_overridden: false, requires_measurements: true,
    measurements: {},
  };
}

export function OrderWizardClient({ catalogue, employees, customers, materials, fromAdmin }: Props) {
  const router = useRouter();
  const { t } = useI18n();
  const [step, setStep] = useState(1);
  const [selectedCustomer, setSelectedCustomer] = useState<typeof customers[0] | null>(null);
  const [isNewCustomer, setIsNewCustomer] = useState(false);
  const [newCust, setNewCust] = useState({ first_name:"",last_name:"",phone:"",email:"",address:"",notes:"" });
  const [customerSearch, setCustomerSearch] = useState("");
  const [showDropdown, setShowDropdown] = useState(false);
  const [items, setItems] = useState<OrderItem[]>([emptyItem()]);
  const [dueDate, setDueDate] = useState("");
  const [priority, setPriority] = useState("normal");
  const [orderNotes, setOrderNotes] = useState("");
  const [measurements, setMeasurements] = useState<Measurements>({ bust:"",waist:"",hips:"",shoulder:"",sleeve:"",length:"",inseam:"",neck:"",notes:"" });
  const [measPrefilled, setMeasPrefilled] = useState(false);
  const [measFromDate, setMeasFromDate] = useState<string | null>(null);
  const [deliveryMethod, setDeliveryMethod] = useState<"pickup"|"home_delivery">("pickup");
  const [deliveryAddress, setDeliveryAddress] = useState("");
  const [deliveryDate, setDeliveryDate] = useState("");
  const [depositMethod, setDepositMethod] = useState("cash");
  const [depositAmount, setDepositAmount] = useState("0");
  const [internalNotes, setInternalNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const searchRef = useRef<HTMLDivElement>(null);

  // Close dropdown on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (searchRef.current && !searchRef.current.contains(e.target as Node)) setShowDropdown(false);
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  const filteredCustomers = customers.filter(c => {
    const q = customerSearch.toLowerCase();
    return !q || c.name.toLowerCase().includes(q) || c.phone.includes(q) || c.email.toLowerCase().includes(q);
  }).slice(0, 12);

  function selectCustomer(c: typeof customers[0]) {
    setSelectedCustomer(c);
    setIsNewCustomer(false);
    setShowDropdown(false);
    setCustomerSearch("");
    setDeliveryAddress(c.address);
    // Try to pre-fill measurements from previous orders; silently skip on any error
    fetch(`/api/customers/${c.id}/measurements/`)
      .then(r => { if (!r.ok) return null; return r.json(); })
      .then((data: Record<string,unknown> | null) => {
        if (data && data.from_order_date) {
          setMeasurements({
            bust:     String(data.bust     ?? ""),
            waist:    String(data.waist    ?? ""),
            hips:     String(data.hips     ?? ""),
            shoulder: String(data.shoulder ?? ""),
            sleeve:   String(data.sleeve   ?? ""),
            length:   String(data.length   ?? ""),
            inseam:   String(data.inseam   ?? ""),
            neck:     String(data.neck     ?? ""),
            notes:    String(data.notes    ?? ""),
          });
          setMeasPrefilled(true);
          setMeasFromDate(data.from_order_date as string);
        }
      })
      .catch(() => {
        // Backend unreachable — customer is still selected, measurements stay blank
      });
  }

  // Item helpers
  function updateItem(idx: number, patch: Partial<OrderItem>) {
    setItems(prev => prev.map((it, i) => i === idx ? { ...it, ...patch } : it));
  }

  function selectCatalogueItem(idx: number, itemId: string) {
    const cat = catalogue.find(c => String(c.id) === itemId);
    if (!cat) { updateItem(idx, { catalogue_item_id: "" }); return; }
    const types = cat.garment_types.length > 0 ? cat.garment_types : [cat.name];
    updateItem(idx, {
      catalogue_item_id: itemId,
      catalogue_source: cat.source,
      unit_price: cat.base_price.toFixed(2),
      garment_type: types.length === 1 ? types[0] : "",
      price_overridden: false,
      requires_measurements: cat.requires_measurements,
    });
  }

  function addItem() { setItems(prev => [...prev, emptyItem()]); }
  function removeItem(idx: number) {
    if (items.length <= 1) return;
    setItems(prev => prev.filter((_, i) => i !== idx));
  }

  const subtotal = items.reduce((s, it) => s + Number(it.unit_price || 0) * it.quantity, 0);
  const deposit = Number(depositAmount || 0);
  const balance = Math.max(subtotal - deposit, 0);

  // Validation
  function nextStep() {
    setError(null);
    if (step === 1) {
      if (!selectedCustomer && !isNewCustomer) { setError("Please select or register a customer."); return; }
      if (isNewCustomer && (!newCust.first_name || !newCust.last_name)) { setError("First and last name are required."); return; }
    }
    if (step === 2) {
      if (items.some(it => !it.catalogue_item_id)) { setError("Please select a service for each item."); return; }
    }
    setStep(s => Math.min(4, s + 1));
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  async function submit() {
    setSubmitting(true);
    setError(null);
    try {
      const payload = {
        customer_id: selectedCustomer?.id ?? null,
        new_customer: isNewCustomer ? newCust : null,
        items: items.map(it => ({
          ...it,
          measurements: it.requires_measurements ? Object.fromEntries(
            Object.entries(measurements).map(([k,v]) => [k, v || null])
          ) : {},
        })),
        due_date: dueDate || null,
        priority,
        order_notes: orderNotes,
        internal_notes: internalNotes,
        delivery_method: deliveryMethod,
        delivery_address: deliveryAddress,
        delivery_date: deliveryDate || null,
        deposit_method: depositMethod,
        deposit_amount: depositAmount || "0",
        measurements: Object.fromEntries(
          Object.entries(measurements).map(([k,v]) => [k, v || null])
        ),
      };
      const res = await fetch("/api/orders/create/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) { setError(data.error ?? "Failed to create order."); setSubmitting(false); return; }
      if (fromAdmin) {
        window.location.href = `${DJANGO_URL}/admin/shop/order/`;
      } else {
        router.push("/");
      }
    } catch (e) {
      setError("Network error. Is the Django server running?");
      setSubmitting(false);
    }
  }

  const needsMeasurements = items.some(it => it.requires_measurements);

  return (
    <div className="flex min-h-[calc(100vh-64px)]">

      {/* Sidebar */}
      <aside className="w-64 bg-[#111827] text-slate-300 flex-shrink-0 flex flex-col p-5 sticky top-16 h-[calc(100vh-64px)] overflow-y-auto">
        <div className="mb-6">
          <h2 className="text-white font-bold text-base">{t("wiz_title")}</h2>
          <p className="text-slate-400 text-xs mt-0.5">{t("wiz_subtitle")}</p>
          {fromAdmin && (
            <a
              href={`${DJANGO_URL}/admin/shop/order/`}
              className="mt-2 inline-flex items-center gap-1 text-xs text-slate-400 hover:text-white transition-colors"
            >
              <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18" />
              </svg>
              {t("wiz_back_admin")}
            </a>
          )}
        </div>

        {/* Step nav */}
        <nav className="space-y-1.5 flex-1">
          {STEP_KEYS.map(({ n, labelKey, descKey }) => (
            <button
              key={n}
              onClick={() => n < step && setStep(n)}
              className={clsx(
                "w-full flex items-center gap-3 rounded-xl px-3 py-2.5 text-left transition-colors",
                step === n ? "bg-[#8324FF]/20 text-white" : n < step ? "text-emerald-300 hover:bg-white/10 cursor-pointer" : "text-slate-500 cursor-default"
              )}
            >
              <span className={clsx(
                "w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold flex-shrink-0",
                step === n ? "bg-[#8324FF] text-white" : n < step ? "bg-emerald-900 text-emerald-300" : "bg-[#374151] text-slate-500"
              )}>
                {n < step ? "✓" : n}
              </span>
              <div>
                <div className="font-semibold text-sm">{t(labelKey)}</div>
                <div className="text-xs opacity-70">{t(descKey)}</div>
              </div>
            </button>
          ))}
        </nav>

        {/* Live summary */}
        <div className="mt-5 pt-4 border-t border-white/10 space-y-2 text-sm">
          <p className="text-xs uppercase tracking-wide text-slate-500 font-semibold">{t("wiz_summary")}</p>
          {[
            { label: t("wiz_customer"), value: selectedCustomer?.name ?? (isNewCustomer ? `${newCust.first_name} ${newCust.last_name}`.trim() || "New" : "—") },
            { label: t("wiz_items"),    value: String(items.length) },
            { label: t("wiz_subtotal"), value: money(subtotal) },
            { label: t("wiz_deposit"),  value: money(deposit) },
          ].map(({ label, value }) => (
            <div key={label} className="flex justify-between">
              <span className="text-slate-400">{label}</span>
              <span className="text-white font-medium truncate ml-2 max-w-[120px] text-right">{value}</span>
            </div>
          ))}
          <div className="flex justify-between pt-2 border-t border-white/10 mt-1">
            <span className="text-slate-300 font-semibold">{t("wiz_balance")}</span>
            <span className="text-[#FFC430] font-bold">{money(balance)}</span>
          </div>
        </div>
      </aside>

      {/* Main — centered column */}
      <main className="flex-1 bg-[#F2F2F2] overflow-y-auto">
        <div className="max-w-2xl mx-auto px-6 py-8 space-y-5">

          {error && (
            <div className="rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700 font-medium flex items-center gap-2">
              <svg className="w-4 h-4 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/></svg>
              {error}
            </div>
          )}

          {/* Step heading */}
          <div className="text-center">
            <div className="inline-flex items-center gap-2 bg-[#f3ebff] text-[#8324FF] text-xs font-bold px-3 py-1.5 rounded-full mb-3">
              <span className="w-4 h-4 bg-[#8324FF] text-white rounded-full flex items-center justify-center text-[10px]">{step}</span>
              Step {step} of 4
            </div>
            <h1 className="text-2xl font-bold text-[#111827]">
              {step === 1 ? t("s1_title") : step === 2 ? t("s2_title") : step === 3 ? t("s3_title") : t("s4_title")}
            </h1>
            <p className="text-sm text-[#848484] mt-1">
              {step === 1 ? t("s1_subtitle") : step === 2 ? t("s2_subtitle") : step === 3 ? t("s3_subtitle") : t("s4_subtitle")}
            </p>
          </div>

          {/* ── Step 1: Customer ── */}
          {step === 1 && (
            <div className="space-y-4">
              {!selectedCustomer && !isNewCustomer && (
                <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm p-5">
                  <p className="text-xs font-bold text-[#848484] uppercase tracking-wider mb-3">{t("s1_find_card")}</p>
                  <div ref={searchRef} className="relative">
                    <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#848484]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/>
                    </svg>
                    <input
                      type="text"
                      value={customerSearch}
                      placeholder={t("s1_search_ph")}
                      className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition"
                      onChange={e => { setCustomerSearch(e.target.value); setShowDropdown(true); }}
                      onFocus={() => setShowDropdown(true)}
                    />
                    {showDropdown && (
                      <div className="absolute top-full left-0 right-0 bg-white border border-[#e5e7eb] rounded-2xl shadow-xl z-50 max-h-64 overflow-y-auto mt-1">
                        {filteredCustomers.length === 0 ? (
                          <div className="px-4 py-6 text-sm text-[#848484] text-center">{t("s1_no_customer")}</div>
                        ) : filteredCustomers.map(c => (
                          <button
                            key={c.id}
                            className="w-full flex items-center justify-between px-4 py-3 hover:bg-[#f3ebff] transition-colors border-b border-[#f3f4f6] last:border-0 text-left first:rounded-t-2xl last:rounded-b-2xl"
                            onClick={() => selectCustomer(c)}
                          >
                            <div className="flex items-center gap-2.5">
                              <div
                                className="w-7 h-7 rounded-full flex items-center justify-center text-white text-xs font-bold flex-shrink-0"
                                style={{ background: nameToHsl(c.name) }}
                              >
                                {initials(c.name)}
                              </div>
                              <div>
                                <div className="font-semibold text-sm text-[#111827]">{c.name}</div>
                                <div className="text-xs text-[#848484]">{c.phone || t("s1_no_phone")}{c.email ? ` · ${c.email}` : ""}</div>
                              </div>
                            </div>
                            <span className="text-xs bg-[#f3ebff] text-[#8324FF] font-semibold rounded-full px-2.5 py-0.5 ml-2 flex-shrink-0">
                              {c.order_count} {t("s1_prev_orders")}
                            </span>
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                  <p className="text-xs text-[#848484] mt-2">{t("s1_hint")}</p>
                </div>
              )}

              {selectedCustomer && (
                <div className="bg-white rounded-2xl border-2 border-[#8324FF]/30 shadow-sm p-5">
                  <div className="flex items-center gap-3">
                    <span
                      className="w-11 h-11 rounded-xl flex-shrink-0 flex items-center justify-center text-white text-sm font-bold shadow"
                      style={{ background: nameToHsl(selectedCustomer.name) }}
                    >
                      {initials(selectedCustomer.name)}
                    </span>
                    <div className="flex-1">
                      <div className="font-bold text-[#111827]">{selectedCustomer.name}</div>
                      <div className="text-xs text-[#848484] mt-0.5 flex flex-wrap gap-2">
                        {selectedCustomer.phone && <span>{selectedCustomer.phone}</span>}
                        {selectedCustomer.email && <span>{selectedCustomer.email}</span>}
                        <span className="text-[#8324FF] font-medium">{selectedCustomer.order_count} {t("s1_prev_orders")}</span>
                      </div>
                    </div>
                    <button onClick={() => setSelectedCustomer(null)} className="text-xs font-semibold text-[#848484] hover:text-[#8324FF] border border-[#e5e7eb] hover:border-[#8324FF] px-3 py-1.5 rounded-lg transition-colors">
                      {t("s1_change")}
                    </button>
                  </div>
                </div>
              )}

              {!isNewCustomer && !selectedCustomer && (
                <div className="text-center text-sm text-[#848484]">
                  {t("s1_no_customer")}{" "}
                  <button onClick={() => setIsNewCustomer(true)} className="text-[#8324FF] font-semibold hover:underline">
                    {t("s1_register")}
                  </button>
                </div>
              )}

              {isNewCustomer && (
                <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm p-5 space-y-4">
                  <div className="flex items-center justify-between">
                    <p className="text-xs font-bold text-[#848484] uppercase tracking-wider">{t("s1_new_title")}</p>
                    <button onClick={() => setIsNewCustomer(false)} className="text-xs text-[#848484] hover:text-[#8324FF] font-semibold transition-colors">
                      {t("s1_cancel")}
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    {([
                      { key: "first_name", labelKey: "s1_first_name" as const, required: true  as const, type: "text",  placeholder: "Ana" },
                      { key: "last_name",  labelKey: "s1_last_name"  as const, required: true  as const, type: "text",  placeholder: "García" },
                      { key: "phone",      labelKey: "s1_phone"      as const, required: false as const, type: "tel",   placeholder: "+34 600 000 000" },
                      { key: "email",      labelKey: "s1_email"      as const, required: false as const, type: "email", placeholder: "ana@example.com" },
                    ]).map(({ key, labelKey, required, type, placeholder }) => (
                      <div key={key}>
                        <label className="block text-xs font-semibold text-[#848484] mb-1.5">
                          {t(labelKey)}{required && <span className="text-red-500 ml-0.5">*</span>}
                        </label>
                        <input
                          type={type}
                          inputMode={key === "phone" ? "tel" : undefined}
                          placeholder={placeholder}
                          value={newCust[key as keyof typeof newCust]}
                          onChange={e => {
                            let val = e.target.value;
                            if (key === "phone") val = val.replace(/[^\d+\-() ]/g, "");
                            setNewCust(p => ({ ...p, [key]: val }));
                          }}
                          className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition"
                        />
                      </div>
                    ))}
                    <div className="col-span-2">
                      <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s1_address")}</label>
                      <input type="text" placeholder="Calle Mayor 1, Madrid" value={newCust.address}
                        onChange={e => setNewCust(p => ({ ...p, address: e.target.value }))}
                        className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition" />
                    </div>
                    <div className="col-span-2">
                      <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s1_notes_pref")}</label>
                      <textarea placeholder="Fitting preferences, fabric sensitivities…" value={newCust.notes}
                        onChange={e => setNewCust(p => ({ ...p, notes: e.target.value }))} rows={2}
                        className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition resize-none" />
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Step 2: Items ── */}
          {step === 2 && (
            <div className="space-y-4">
              {items.map((item, idx) => {
                const cat = catalogue.find(c => String(c.id) === item.catalogue_item_id);
                const types = cat ? (cat.garment_types.length > 0 ? cat.garment_types : [cat.name]) : [];
                return (
                  <div key={idx} className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm p-5">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-2">
                        <span className="w-6 h-6 rounded-full bg-[#8324FF] text-white text-xs font-bold flex items-center justify-center">{idx + 1}</span>
                        <span className="text-sm font-bold text-[#111827]">{t("s2_item")} {idx + 1}</span>
                      </div>
                      {items.length > 1 && (
                        <button onClick={() => removeItem(idx)} className="text-xs text-red-500 border border-red-200 rounded-lg px-2.5 py-1 hover:bg-red-50 transition-colors font-medium">
                          {t("s2_remove")}
                        </button>
                      )}
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div className="col-span-2">
                        <label className="block text-xs font-semibold text-[#848484] mb-1.5">
                          {t("s2_service")} <span className="text-red-500">*</span>
                        </label>
                        <select value={item.catalogue_item_id} onChange={e => selectCatalogueItem(idx, e.target.value)}
                          className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition">
                          <option value="">{t("s2_choose")}</option>
                          {catalogue.map(c => (
                            <option key={c.id} value={c.id}>{c.name.split("  —")[0]}  —  ${c.base_price.toFixed(2)}</option>
                          ))}
                        </select>
                        {cat?.price_hint && <p className="text-xs text-[#848484] mt-1">{cat.price_hint}</p>}
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s2_garment")}</label>
                        {types.length > 1 ? (
                          <select value={item.garment_type} onChange={e => updateItem(idx, { garment_type: e.target.value })}
                            className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition">
                            <option value="">{t("s2_select_type")}</option>
                            {types.map(tp => <option key={tp} value={tp}>{tp}</option>)}
                          </select>
                        ) : (
                          <input type="text" value={item.garment_type} onChange={e => updateItem(idx, { garment_type: e.target.value })}
                            placeholder="e.g. Dress"
                            className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition" />
                        )}
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s2_material")}</label>
                        <input type="text" value={item.color_fabric} onChange={e => updateItem(idx, { color_fabric: e.target.value })}
                          placeholder="e.g. Navy linen"
                          className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition" />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s2_qty")}</label>
                        <input type="number" min={1} value={item.quantity} onChange={e => updateItem(idx, { quantity: Number(e.target.value) || 1 })}
                          className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition" />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s2_unit_price")}</label>
                        <input type="number" step="0.01" min={0} value={item.unit_price}
                          onChange={e => updateItem(idx, { unit_price: e.target.value, price_overridden: true })}
                          className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition" />
                        {item.catalogue_item_id && (
                          <span className={clsx("inline-block mt-1.5 text-xs rounded-full px-2.5 py-0.5 font-semibold",
                            item.price_overridden ? "bg-amber-50 text-amber-700 ring-1 ring-amber-200" : "bg-green-50 text-green-700 ring-1 ring-green-200")}>
                            {item.price_overridden ? t("s2_modified") : t("s2_auto")}
                          </span>
                        )}
                      </div>
                      <div>
                        <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s2_assign")}</label>
                        <select value={item.assigned_employee_id} onChange={e => updateItem(idx, { assigned_employee_id: e.target.value })}
                          className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition">
                          <option value="">{t("s2_assign_later")}</option>
                          {employees.map(e => <option key={e.id} value={e.id}>{e.name}{e.role ? ` (${e.role})` : ""}</option>)}
                        </select>
                      </div>
                      <div className="col-span-2">
                        <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s2_notes")}</label>
                        <textarea rows={2} value={item.item_notes} onChange={e => updateItem(idx, { item_notes: e.target.value })}
                          placeholder={t("s2_notes_ph")}
                          className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition resize-none" />
                      </div>
                    </div>
                    <div className="mt-3 pt-3 border-t border-[#f3f4f6] flex justify-between items-center">
                      <span className="text-xs text-[#848484]">{t("s2_line_total")}</span>
                      <span className="font-bold text-[#8324FF]">${(Number(item.unit_price || 0) * item.quantity).toFixed(2)}</span>
                    </div>
                  </div>
                );
              })}

              <button onClick={addItem} className="w-full rounded-2xl border-2 border-dashed border-[#e5e7eb] py-4 text-sm font-semibold text-[#848484] hover:border-[#8324FF] hover:text-[#8324FF] hover:bg-[#f3ebff]/40 transition-colors">
                {t("s2_add_item")}
              </button>

              <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm p-5 space-y-4">
                <p className="text-xs font-bold text-[#848484] uppercase tracking-wider">{t("s2_settings")}</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s2_due_date")}</label>
                    <input type="date" value={dueDate} onChange={e => setDueDate(e.target.value)}
                      className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("expand_priority")}</label>
                    <select value={priority} onChange={e => setPriority(e.target.value)}
                      className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none">
                      <option value="low">{t("prio_low")}</option>
                      <option value="normal">{t("prio_normal")}</option>
                      <option value="high">{t("prio_high")}</option>
                      <option value="urgent">{t("prio_urgent")}</option>
                    </select>
                  </div>
                  <div className="col-span-2">
                    <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s2_order_notes")}</label>
                    <textarea rows={2} value={orderNotes} onChange={e => setOrderNotes(e.target.value)}
                      placeholder={t("s2_order_notes_ph")}
                      className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none resize-none" />
                  </div>
                </div>
              </div>

              {/* Totals bar */}
              <div className="bg-[#111827] rounded-2xl p-4 grid grid-cols-3 gap-3 text-center">
                {[
                  { label: t("wiz_subtotal"),  value: money(subtotal), accent: false },
                  { label: t("wiz_deposit"),   value: money(deposit),  accent: false },
                  { label: t("wiz_balance"),   value: money(balance),  accent: true  },
                ].map(({ label, value, accent }) => (
                  <div key={label}>
                    <div className="text-xs text-slate-400 mb-0.5">{label}</div>
                    <div className={clsx("font-extrabold text-lg", accent ? "text-[#FFC430]" : "text-white")}>{value}</div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* ── Step 3: Measurements ── */}
          {step === 3 && (
            <div className="space-y-4">
              {!needsMeasurements ? (
                <div className="bg-white rounded-2xl border-2 border-dashed border-[#e5e7eb] p-10 text-center">
                  <div className="w-12 h-12 bg-[#f3ebff] rounded-2xl flex items-center justify-center mx-auto mb-3">
                    <svg className="w-6 h-6 text-[#8324FF]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7"/>
                    </svg>
                  </div>
                  <p className="text-[#111827] text-sm font-bold">{t("s3_none_needed")}</p>
                  <p className="text-[#848484] text-xs mt-1">{t("s3_none_desc")}</p>
                </div>
              ) : (
                <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm p-5 space-y-4">
                  {measPrefilled && (
                    <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-xs text-emerald-700 font-medium flex items-center gap-2">
                      <svg className="w-3.5 h-3.5 flex-shrink-0" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
                      {t("s3_prefilled")} {measFromDate}. {t("s3_update_hint")}
                    </div>
                  )}
                  <div className="grid grid-cols-4 gap-3">
                    {MEAS_FIELDS.map(f => (
                      <div key={f} className={measPrefilled && measurements[f] ? "ring-2 ring-emerald-200 rounded-xl" : ""}>
                        <label className="block text-xs font-semibold text-[#848484] mb-1.5 capitalize">
                          {t(`meas_${f}` as "meas_bust"|"meas_waist"|"meas_hips"|"meas_shoulder"|"meas_sleeve"|"meas_length"|"meas_inseam"|"meas_neck")}
                        </label>
                        <input type="number" step="0.5" placeholder={t("cust_cm")}
                          value={measurements[f]}
                          onChange={e => setMeasurements(p => ({ ...p, [f]: e.target.value }))}
                          className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-2 py-2 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition" />
                      </div>
                    ))}
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s3_meas_notes")}</label>
                    <textarea rows={2} value={measurements.notes} onChange={e => setMeasurements(p => ({ ...p, notes: e.target.value }))}
                      placeholder={t("s3_meas_notes_ph")}
                      className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none resize-none" />
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ── Step 4: Delivery & Payment ── */}
          {step === 4 && (
            <div className="space-y-4">
              <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm p-5 space-y-3">
                <p className="text-xs font-bold text-[#848484] uppercase tracking-wider">{t("s4_delivery_method")}</p>
                {([
                  { key: "pickup",        labelKey: "s4_pickup" as const,  descKey: "s4_pickup_desc" as const },
                  { key: "home_delivery", labelKey: "s4_home"   as const,  descKey: "s4_home_desc"   as const },
                ] as const).map(({ key, labelKey, descKey }) => (
                  <button key={key} onClick={() => setDeliveryMethod(key as typeof deliveryMethod)}
                    className={clsx(
                      "w-full flex items-center gap-3 rounded-xl border-2 px-4 py-3.5 text-left transition-all",
                      deliveryMethod === key ? "border-[#8324FF] bg-[#f3ebff]" : "border-[#e5e7eb] hover:border-[#8324FF]/30 bg-[#F2F2F2]"
                    )}
                  >
                    <div className={clsx("w-4 h-4 rounded-full border-2 flex-shrink-0 transition-all",
                      deliveryMethod === key ? "border-[#8324FF] bg-[#8324FF]" : "border-[#848484]")} />
                    <div>
                      <div className={clsx("font-semibold text-sm", deliveryMethod === key ? "text-[#8324FF]" : "text-[#111827]")}>{t(labelKey)}</div>
                      <div className="text-xs text-[#848484]">{t(descKey)}</div>
                    </div>
                  </button>
                ))}
              </div>

              {deliveryMethod === "home_delivery" && (
                <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm p-5 space-y-3">
                  <p className="text-xs font-bold text-[#848484] uppercase tracking-wider">{t("s4_delivery_details")}</p>
                  <div>
                    <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s4_del_address")}</label>
                    <input type="text" value={deliveryAddress} onChange={e => setDeliveryAddress(e.target.value)}
                      placeholder={t("s4_del_address_ph")}
                      className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none" />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s4_del_date")}</label>
                    <input type="date" value={deliveryDate} onChange={e => setDeliveryDate(e.target.value)}
                      className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none" />
                  </div>
                </div>
              )}

              <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm p-5 space-y-3">
                <p className="text-xs font-bold text-[#848484] uppercase tracking-wider">{t("s4_payment")}</p>
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s4_dep_method")}</label>
                    <select value={depositMethod} onChange={e => setDepositMethod(e.target.value)}
                      className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none">
                      <option value="cash">{t("s4_cash")}</option>
                      <option value="card">{t("s4_card")}</option>
                      <option value="transfer">{t("s4_transfer")}</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-[#848484] mb-1.5">{t("s4_amount_today")}</label>
                    <input type="number" step="0.01" min={0} value={depositAmount}
                      onChange={e => setDepositAmount(e.target.value)}
                      className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none" />
                  </div>
                </div>
                <div className="bg-[#111827] rounded-2xl p-4 grid grid-cols-3 gap-3 text-center mt-2">
                  {[
                    { label: t("s4_order_total"),     value: money(subtotal) },
                    { label: t("s4_deposit_today"),   value: money(deposit) },
                    { label: t("s4_balance_pickup"),  value: money(balance), accent: true },
                  ].map(({ label, value, accent }) => (
                    <div key={label}>
                      <div className="text-xs text-slate-400 mb-0.5">{label}</div>
                      <div className={clsx("font-extrabold text-lg", accent ? "text-[#FFC430]" : "text-white")}>{value}</div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm p-5">
                <label className="block text-xs font-bold text-[#848484] uppercase tracking-wider mb-2">{t("s4_internal_notes")}</label>
                <textarea rows={3} value={internalNotes} onChange={e => setInternalNotes(e.target.value)}
                  placeholder={t("s4_internal_ph")}
                  className="w-full rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] px-3 py-2.5 text-sm focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none resize-none" />
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-between pt-5 border-t border-[#e5e7eb]">
          <button
            onClick={() => { setStep(s => Math.max(1, s - 1)); setError(null); }}
            style={{ visibility: step === 1 ? "hidden" : "visible" }}
            className="rounded-xl border border-[#e5e7eb] bg-white px-4 py-2 text-sm font-semibold text-[#848484] hover:border-[#8324FF] hover:text-[#8324FF] transition-colors"
          >
            {t("wiz_back")}
          </button>
          <div className="flex items-center gap-3">
            <span className="text-xs text-[#848484]">Step {step} of 4</span>
            {step < 4 ? (
              <button
                onClick={nextStep}
                className="rounded-xl bg-[#8324FF] hover:bg-[#9b47ff] px-5 py-2 text-sm font-semibold text-white shadow-lg shadow-purple-500/25 transition-all"
              >
                {t("wiz_continue")}
              </button>
            ) : (
              <button
                onClick={submit}
                disabled={submitting}
                className={clsx(
                  "rounded-xl px-5 py-2 text-sm font-semibold text-white transition-all shadow-lg",
                  submitting ? "bg-gray-400 cursor-not-allowed" : "bg-[#8324FF] hover:bg-[#9b47ff] shadow-purple-500/25"
                )}
              >
                {submitting ? t("wiz_saving") : t("wiz_save")}
              </button>
            )}
          </div>{/* end inner flex */}
          </div>{/* end actions bar */}
        </div>{/* end centered col */}
      </main>
    </div>
  );
}
