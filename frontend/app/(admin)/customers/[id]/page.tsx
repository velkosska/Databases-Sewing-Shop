import { api, CustomerDetail, DjangoOfflineError } from "@/lib/api";
import { Navbar } from "@/components/ui/Navbar";
import { Badge } from "@/components/ui/Badge";
import { notFound } from "next/navigation";
import Link from "next/link";
import OfflineError from "@/components/ui/OfflineError";

export const dynamic = "force-dynamic";

function nameToHsl(name: string) {
  let h = 0;
  for (let i = 0; i < name.length; i++) h = name.charCodeAt(i) + ((h << 5) - h);
  return `hsl(${Math.abs(h % 360)}, 56%, 42%)`;
}

function initials(name: string) {
  const p = name.trim().split(" ");
  return (p[0][0] + (p[1]?.[0] ?? "")).toUpperCase();
}

const MEAS_FIELDS = [
  { key: "bust", label: "Bust" }, { key: "waist", label: "Waist" },
  { key: "hips", label: "Hips" }, { key: "shoulder", label: "Shoulder" },
  { key: "sleeve", label: "Sleeve" }, { key: "length", label: "Length" },
  { key: "inseam", label: "Inseam" }, { key: "neck", label: "Neck" },
] as const;

export default async function CustomerPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  let customer: CustomerDetail;
  try {
    customer = await api.get<CustomerDetail>(`/customers/${id}/`);
  } catch (err) {
    if (err instanceof DjangoOfflineError) return <OfflineError />;
    notFound();
  }

  const initStr = initials(customer.full_name);

  return (
    <>
      <Navbar title={customer.full_name} />
      <main className="px-6 py-6 space-y-5 max-w-5xl">

        {/* Header card */}
        <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm p-5">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div className="flex items-center gap-4">
              <span
                className="w-14 h-14 rounded-2xl flex items-center justify-center text-white font-extrabold text-lg shadow-lg"
                style={{ background: nameToHsl(customer.full_name) }}
              >
                {initStr}
              </span>
              <div>
                <h1 className="text-xl font-bold text-[#111827]">{customer.full_name}</h1>
                <p className="text-sm text-[#848484] mt-0.5">
                  Customer since {customer.created_at
                    ? new Date(customer.created_at).toLocaleDateString("en-GB", { year: "numeric", month: "long" })
                    : "—"}
                </p>
              </div>
            </div>
            <div className="flex gap-2 flex-wrap">
              <Link href="/" className="rounded-xl border border-[#e5e7eb] bg-white px-3.5 py-2 text-sm font-semibold text-[#848484] hover:border-[#8324FF] hover:text-[#8324FF] transition-colors">
                Dashboard
              </Link>
              <a
                href={`${process.env.NEXT_PUBLIC_DJANGO_URL ?? "http://127.0.0.1:8000"}/admin/shop/customer/${customer.id}/change/`}
                target="_blank" rel="noopener noreferrer"
                className="rounded-xl border border-[#e5e7eb] bg-white px-3.5 py-2 text-sm font-semibold text-[#848484] hover:border-[#8324FF] hover:text-[#8324FF] transition-colors"
              >
                Edit in Admin
              </a>
              <Link
                href="/orders/new"
                className="rounded-xl bg-[#8324FF] hover:bg-[#9b47ff] px-3.5 py-2 text-sm font-semibold text-white shadow-lg shadow-purple-500/25 transition-all"
              >
                + New Order
              </Link>
            </div>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {[
            { label: "Total Orders",  value: customer.orders.length,                      accent: "#8324FF" },
            { label: "Total Spent",   value: `$${customer.total_spent.toFixed(2)}`,        accent: "#30D3FF" },
            { label: "Active Orders", value: customer.orders.filter(o => !["completed","delivered"].includes(o.status)).length, accent: "#FFC430" },
            { label: "Measurements",  value: customer.measurements ? "On file" : "None",   accent: customer.measurements ? "#22c55e" : "#848484" },
          ].map(({ label, value, accent }) => (
            <div key={label} className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm px-4 py-4">
              <p className="text-xs font-semibold text-[#848484] uppercase tracking-wider mb-1">{label}</p>
              <p className="text-2xl font-extrabold" style={{ color: accent }}>{value}</p>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">

          {/* Order history */}
          <div className="md:col-span-2 space-y-3">
            <h2 className="font-bold text-[#111827] text-base">Order History</h2>
            {customer.orders.length === 0 ? (
              <div className="rounded-2xl border-2 border-dashed border-[#e5e7eb] p-8 text-center text-[#848484] text-sm">
                No orders yet.
              </div>
            ) : customer.orders.map(order => (
              <div key={order.id} className="rounded-2xl border border-[#e5e7eb] bg-white p-4 hover:border-[#8324FF]/30 hover:shadow-sm transition-all">
                <div className="flex items-center justify-between mb-2">
                  <a
                    href={`${process.env.NEXT_PUBLIC_DJANGO_URL ?? "http://127.0.0.1:8000"}/admin/shop/order/${order.id}/change/`}
                    target="_blank" rel="noopener noreferrer"
                    className="font-bold text-[#111827] hover:text-[#8324FF] transition-colors text-sm"
                  >
                    Order #{order.id}
                  </a>
                  <Badge value={order.status} />
                </div>
                <div className="flex flex-wrap gap-3 text-xs text-[#848484] mb-2">
                  <span>{order.order_date ? new Date(order.order_date).toLocaleDateString("en-GB") : "—"}</span>
                  {order.due_date && <span>Due: {new Date(order.due_date).toLocaleDateString("en-GB")}</span>}
                  {order.total_price != null && (
                    <span className="font-bold text-[#111827]">${order.total_price.toFixed(2)}</span>
                  )}
                  <Badge value={order.payment_status} />
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {order.items.slice(0, 5).map(it => (
                    <span key={it.id} className="text-xs bg-[#f3ebff] text-[#8324FF] rounded-full px-2.5 py-0.5 font-medium">
                      {it.garment_type || it.catalogue_name || "Item"}
                    </span>
                  ))}
                  {order.items.length > 5 && (
                    <span className="text-xs text-[#848484]">+{order.items.length - 5} more</span>
                  )}
                </div>
              </div>
            ))}
          </div>

          {/* Right sidebar */}
          <div className="space-y-4">
            {/* Measurements */}
            <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm p-4">
              <h2 className="font-bold text-[#111827] text-sm mb-3">Measurements</h2>
              {customer.measurements ? (
                <>
                  <p className="text-xs text-[#848484] mb-3">
                    Recorded {new Date(customer.measurements.recorded_at).toLocaleDateString("en-GB", { year: "numeric", month: "short", day: "numeric" })}
                  </p>
                  <div className="divide-y divide-[#f3f4f6]">
                    {MEAS_FIELDS.filter(f => customer.measurements![f.key] != null).map(({ key, label }) => (
                      <div key={key} className="flex justify-between py-1.5">
                        <span className="text-xs text-[#848484]">{label}</span>
                        <span className="text-xs font-bold text-[#111827]">{customer.measurements![key]} cm</span>
                      </div>
                    ))}
                  </div>
                  {customer.measurements.notes && (
                    <p className="mt-2 text-xs text-[#848484] italic">{customer.measurements.notes}</p>
                  )}
                </>
              ) : (
                <p className="text-sm text-[#848484]">No measurements on file.</p>
              )}
            </div>

            {/* Contact */}
            <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm p-4">
              <h2 className="font-bold text-[#111827] text-sm mb-3">Contact</h2>
              <div className="space-y-2 text-sm">
                {[
                  { label: "Phone",   value: customer.phone },
                  { label: "Email",   value: customer.email },
                  { label: "Address", value: customer.address },
                ].filter(({ value }) => value).map(({ label, value }) => (
                  <div key={label} className="flex gap-2">
                    <span className="text-[#848484] w-14 flex-shrink-0 text-xs mt-0.5">{label}</span>
                    <span className="text-[#111827] text-sm font-medium">{value}</span>
                  </div>
                ))}
              </div>
            </div>

            {customer.notes && (
              <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm p-4">
                <h2 className="font-bold text-[#111827] text-sm mb-2">Notes</h2>
                <p className="text-sm text-[#848484] whitespace-pre-wrap">{customer.notes}</p>
              </div>
            )}
          </div>

        </div>
      </main>
    </>
  );
}
