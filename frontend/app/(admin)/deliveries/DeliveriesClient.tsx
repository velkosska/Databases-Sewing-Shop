"use client";
import { DeliveryRow } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { adminUrl } from "@/lib/django";

// Fixed locale + IANA TZ so SSR (Node) and client match; default aligns with Django TIME_ZONE (Europe/Madrid).
const DISPLAY_TZ =
  typeof process !== "undefined" &&
  typeof process.env.NEXT_PUBLIC_SHOP_TIMEZONE === "string" &&
  process.env.NEXT_PUBLIC_SHOP_TIMEZONE
    ? process.env.NEXT_PUBLIC_SHOP_TIMEZONE
    : "Europe/Madrid";

const DELIVERED_AT_FORMAT = new Intl.DateTimeFormat("en-US", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: DISPLAY_TZ,
});

export function DeliveriesClient({ deliveries }: { deliveries: DeliveryRow[] }) {
  const { t } = useI18n();

  function fmtDt(iso: string | null) {
    if (!iso) return "—";
    try {
      const d = new Date(iso);
      if (Number.isNaN(d.getTime())) return iso;
      return DELIVERED_AT_FORMAT.format(d);
    } catch {
      return iso;
    }
  }

  return (
    <div className="p-6 space-y-6 max-w-[1200px]">
      <div>
        <h1 className="text-2xl font-bold text-[#111827]">{t("del_title")}</h1>
        <p className="text-sm text-[#848484] mt-1">{t("del_subtitle")}</p>
      </div>

      <div className="bg-white rounded-2xl border border-[#e5e7eb] shadow-sm overflow-hidden">
        {deliveries.length === 0 ? (
          <div className="p-12 text-center text-[#848484] text-sm space-y-2">
            <p>{t("del_empty")}</p>
            <p className="text-xs max-w-md mx-auto">{t("del_hint")}</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="bg-[#fafafa] text-left text-[#848484] text-xs font-semibold uppercase tracking-wider border-b border-[#e5e7eb]">
                  <th className="px-5 py-3">{t("del_col_order")}</th>
                  <th className="px-4 py-3">{t("del_col_customer")}</th>
                  <th className="px-4 py-3">{t("del_col_recipient")}</th>
                  <th className="px-4 py-3">{t("del_col_method")}</th>
                  <th className="px-4 py-3">{t("del_col_status")}</th>
                  <th className="px-4 py-3">{t("del_col_when")}</th>
                  <th className="px-4 py-3 text-right">{t("del_col_actions")}</th>
                </tr>
              </thead>
              <tbody>
                {deliveries.map(d => (
                  <tr key={d.id} className="border-b border-[#f3f4f6] hover:bg-[#fafafa]">
                    <td className="px-5 py-3.5 font-semibold text-[#111827]">#{d.order_id}</td>
                    <td className="px-4 py-3.5 text-[#111827]">{d.customer_name}</td>
                    <td className="px-4 py-3.5 text-[#848484]">{d.recipient_name || "—"}</td>
                    <td className="px-4 py-3.5 text-[#111827]">
                      {d.delivery_method_label || d.delivery_method || "—"}
                    </td>
                    <td className="px-4 py-3.5">
                      <span className={`inline-flex px-2 py-0.5 rounded-full text-xs font-semibold ${
                        d.delivered ? "bg-green-50 text-green-700" : "bg-amber-50 text-amber-800"
                      }`}>
                        {d.delivered ? t("del_chip_done") : t("del_chip_pending")}
                      </span>
                    </td>
                    <td className="px-4 py-3.5 text-[#848484] whitespace-nowrap">{fmtDt(d.delivered_at)}</td>
                    <td className="px-4 py-3.5 text-right">
                      <a
                        href={adminUrl(`shop/delivery/${d.id}/change/`)}
                        target="_blank" rel="noopener noreferrer"
                        className="text-xs font-semibold text-[#8324FF] hover:underline"
                      >
                        {t("del_open_admin")}
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
