"use client";
import React, { useState } from "react";
import Link from "next/link";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  LineChart, Line, CartesianGrid,
} from "recharts";
import { DashboardData, OrderRow } from "@/lib/api";
import { DJANGO_URL } from "@/lib/django";
import { useI18n } from "@/lib/i18n";

const STATUS_TAB_KEYS = [
  { key: "all",           labelKey: "tab_all"           },
  { key: "pending",       labelKey: "tab_pending"       },
  { key: "in_production", labelKey: "tab_in_production" },
  { key: "completed",     labelKey: "tab_completed"     },
  { key: "delivered",     labelKey: "tab_delivered"     },
] as const;

const STATUS_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
  pending:       { bg: "bg-yellow-50",  text: "text-yellow-700",  dot: "bg-yellow-400" },
  in_production: { bg: "bg-blue-50",    text: "text-blue-700",    dot: "bg-blue-500" },
  completed:     { bg: "bg-green-50",   text: "text-green-700",   dot: "bg-green-500" },
  delivered:     { bg: "bg-purple-50",  text: "text-purple-700",  dot: "bg-[#8324FF]" },
};

const PAY_COLORS: Record<string, { bg: string; text: string }> = {
  unpaid:  { bg: "bg-red-50",    text: "text-red-600" },
  deposit: { bg: "bg-yellow-50", text: "text-yellow-700" },
  paid:    { bg: "bg-green-50",  text: "text-green-700" },
};

const STATUS_LABEL_KEYS: Record<string, "status_pending"|"status_in_production"|"status_completed"|"status_delivered"> = {
  pending:       "status_pending",
  in_production: "status_in_production",
  completed:     "status_completed",
  delivered:     "status_delivered",
};
const PAY_LABEL_KEYS: Record<string, "pay_unpaid"|"pay_deposit"|"pay_paid"> = {
  unpaid:  "pay_unpaid",
  deposit: "pay_deposit",
  paid:    "pay_paid",
};

function StatusBadge({ value }: { value: string }) {
  const { t } = useI18n();
  const c = STATUS_COLORS[value] ?? { bg: "bg-gray-100", text: "text-gray-600", dot: "bg-gray-400" };
  const labelKey = STATUS_LABEL_KEYS[value];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold ${c.bg} ${c.text}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${c.dot}`} />
      {labelKey ? t(labelKey) : value.replace("_", " ").replace(/\b\w/g, l => l.toUpperCase())}
    </span>
  );
}

function PayBadge({ value }: { value: string }) {
  const { t } = useI18n();
  const c = PAY_COLORS[value] ?? { bg: "bg-gray-100", text: "text-gray-600" };
  const labelKey = PAY_LABEL_KEYS[value];
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold ${c.bg} ${c.text}`}>
      {labelKey ? t(labelKey) : value.replace(/\b\w/g, l => l.toUpperCase())}
    </span>
  );
}


type SortField = "order_date" | "due_date" | "total_price" | "customer_name" | "status" | "payment_status";
type SortDir = "asc" | "desc";

function SortIcon({ field, active, dir }: { field: string; active: boolean; dir: SortDir }) {
  if (!active) return (
    <svg className="w-3 h-3 opacity-30 ml-1 inline-block" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M7 16V4m0 0L3 8m4-4l4 4M17 8v12m0 0l4-4m-4 4l-4-4" />
    </svg>
  );
  return dir === "asc" ? (
    <svg className="w-3 h-3 ml-1 inline-block text-[#8324FF]" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" />
    </svg>
  ) : (
    <svg className="w-3 h-3 ml-1 inline-block text-[#8324FF]" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
    </svg>
  );
}

export function DashboardClient({ data }: { data: DashboardData }) {
  const [activeTab, setActiveTab] = useState("all");
  const [expandedRow, setExpandedRow] = useState<number | null>(null);
  const [sortField, setSortField] = useState<SortField>("order_date");
  const [sortDir, setSortDir] = useState<SortDir>("desc");
  const [search, setSearch] = useState("");
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const [visibleCount, setVisibleCount] = useState(10);
  const { t } = useI18n();

  const { stats, revenue, kpi_changes, charts, orders, low_stock } = data;

  function fmtChange(v: number | null): { change: string; up: boolean } {
    if (v === null) return { change: t("kpi_no_data"), up: true };
    const sign = v >= 0 ? "+" : "";
    return { change: `${sign}${v}% ${t("kpi_vs_last_month")}`, up: v >= 0 };
  }

  function handleSort(field: SortField) {
    if (sortField === field) {
      setSortDir(d => d === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDir("desc");
    }
    setExpandedRow(null);
    setVisibleCount(10);
  }

  const hasFilters = search.trim() || fromDate || toDate;

  const filtered = (activeTab === "all" ? orders : orders.filter(o => o.status === activeTab))
    .filter(o => {
      if (search.trim() && !o.customer_name.toLowerCase().includes(search.trim().toLowerCase())) return false;
      if (fromDate && o.order_date && o.order_date < fromDate) return false;
      if (toDate   && o.order_date && o.order_date > toDate)   return false;
      return true;
    })
    .slice()
    .sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case "order_date":   cmp = (a.order_date ?? "").localeCompare(b.order_date ?? ""); break;
        case "due_date":     cmp = (a.due_date ?? "9999-99-99").localeCompare(b.due_date ?? "9999-99-99"); break;
        case "total_price":  cmp = (a.total_price ?? 0) - (b.total_price ?? 0); break;
        case "customer_name": cmp = a.customer_name.localeCompare(b.customer_name); break;
        case "status":       cmp = a.status.localeCompare(b.status); break;
        case "payment_status": cmp = a.payment_status.localeCompare(b.payment_status); break;
      }
      return sortDir === "asc" ? cmp : -cmp;
    });

  const kpis = [
    {
      label: t("kpi_total_orders"), value: stats.all,
      ...fmtChange(kpi_changes.orders),
      color: "#8324FF", bg: "#f3ebff",
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>,
    },
    {
      label: t("kpi_revenue"), value: `$${revenue.total.toFixed(0)}`,
      ...fmtChange(kpi_changes.revenue),
      color: "#30D3FF", bg: "#e8fafe",
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>,
    },
    {
      label: t("kpi_pending"), value: stats.pending,
      label2: `${stats.overdue} ${t("kpi_overdue")}`,
      ...fmtChange(kpi_changes.pending),
      color: "#FFC430", bg: "#fff9e8",
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>,
    },
    {
      label: t("kpi_balance_due"), value: `$${revenue.balance_outstanding.toFixed(0)}`,
      ...fmtChange(kpi_changes.balance),
      color: "#FF863F", bg: "#fff3eb",
      icon: <svg className="w-5 h-5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z"/></svg>,
    },
  ];

  return (
    <div className="p-6 space-y-6">

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[#111827]">{t("dash_title")}</h1>
          <p className="text-sm text-[#848484] mt-0.5">{t("dash_subtitle")}</p>
        </div>
        <Link
          href="/orders/new"
          className="flex items-center gap-2 bg-[#8324FF] hover:bg-[#9b47ff] text-white text-sm font-semibold px-4 py-2.5 rounded-xl shadow-lg shadow-purple-500/25 transition-all"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
          </svg>
          {t("dash_new_order")}
        </Link>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
        {kpis.map(({ label, value, change, up, color, bg, icon }) => (
          <div key={label} className="bg-white rounded-2xl p-5 shadow-sm border border-[#e5e7eb] hover:shadow-md transition-shadow">
            <div className="flex items-start justify-between mb-4">
              <div>
                <p className="text-xs font-semibold text-[#848484] uppercase tracking-wider">{label}</p>
                <p className="text-2xl font-bold text-[#111827] mt-1">{value}</p>
              </div>
              <div className="w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0" style={{ background: bg, color }}>
                {icon}
              </div>
            </div>
            <div className={`inline-flex items-center gap-1 text-xs font-semibold px-2 py-0.5 rounded-full ${up ? "bg-green-50 text-green-600" : "bg-yellow-50 text-yellow-600"}`}>
              {up ? (
                <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M5 15l7-7 7 7" /></svg>
              ) : (
                <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" /></svg>
              )}
              {change}
            </div>
          </div>
        ))}
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Monthly Orders Bar Chart */}
        <div className="lg:col-span-2 bg-white rounded-2xl p-5 shadow-sm border border-[#e5e7eb]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-[#111827]">{t("chart_monthly")}</h2>
              <p className="text-xs text-[#848484] mt-0.5">{t("chart_monthly_sub")}</p>
            </div>
            <span className="text-xs bg-[#f3ebff] text-[#8324FF] font-semibold px-2.5 py-1 rounded-full">2026</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={charts.monthly_orders} barSize={22}>
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: "#848484" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#848484" }} axisLine={false} tickLine={false} width={24} />
              <Tooltip
                cursor={{ fill: "#f3ebff" }}
                contentStyle={{ borderRadius: 10, border: "1px solid #e5e7eb", fontSize: 12 }}
              />
              <Bar dataKey="orders" fill="#8324FF" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Weekly Revenue Line Chart */}
        <div className="bg-white rounded-2xl p-5 shadow-sm border border-[#e5e7eb]">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-base font-bold text-[#111827]">{t("chart_revenue")}</h2>
              <p className="text-xs text-[#848484] mt-0.5">{t("chart_revenue_sub")}</p>
            </div>
            <span className="text-xs bg-[#e8fafe] text-[#30D3FF] font-semibold px-2.5 py-1 rounded-full">Live</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={charts.weekly_revenue}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="day" tick={{ fontSize: 11, fill: "#848484" }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: "#848484" }} axisLine={false} tickLine={false} width={36} />
              <Tooltip
                contentStyle={{ borderRadius: 10, border: "1px solid #e5e7eb", fontSize: 12 }}
              />
              <Line type="monotone" dataKey="revenue" stroke="#8324FF" strokeWidth={2.5} dot={{ r: 3, fill: "#8324FF" }} activeDot={{ r: 5 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Low stock alert */}
      {low_stock.length > 0 && (
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-[#e5e7eb]">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-7 h-7 rounded-lg bg-red-50 flex items-center justify-center">
              <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <h3 className="text-sm font-bold text-[#111827]">{t("low_stock_title")}</h3>
            <span className="ml-auto text-xs bg-red-50 text-red-600 font-semibold px-2 py-0.5 rounded-full">{low_stock.length} {t("low_stock_items")}</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {low_stock.map(m => (
              <a
                key={m.id}
                href={`${DJANGO_URL}/admin/shop/material/${m.id}/change/`}
                target="_blank" rel="noopener noreferrer"
                className="flex items-center gap-1.5 bg-red-50 hover:bg-red-100 text-red-700 text-xs font-medium px-3 py-1.5 rounded-full transition-colors"
              >
                {m.name}{m.color ? ` (${m.color})` : ""} — {m.stock_quantity} {t("low_stock_left")}
              </a>
            ))}
          </div>
        </div>
      )}

      {/* Order management table */}
      <div className="bg-white rounded-2xl shadow-sm border border-[#e5e7eb]">
        {/* Table header */}
        <div className="px-5 pt-5 pb-0">
          <div className="flex items-center justify-between mb-4 flex-wrap gap-3">
            <div>
              <h2 className="text-base font-bold text-[#111827]">{t("orders_title")}</h2>
              <p className="text-xs text-[#848484] mt-0.5">{filtered.length} {t("tab_all").toLowerCase()}</p>
            </div>
            <Link href="/orders/new" className="text-xs font-semibold text-[#8324FF] hover:underline">
              {t("orders_add")}
            </Link>
          </div>

          {/* Search + date range filter */}
          <div className="flex flex-wrap items-center gap-2 mb-4">
            <div className="relative flex-1 min-w-[180px]">
              <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#848484]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-4.35-4.35M17 11A6 6 0 115 11a6 6 0 0112 0z"/>
              </svg>
              <input
                type="text"
                value={search}
                onChange={e => { setSearch(e.target.value); setExpandedRow(null); setVisibleCount(10); }}
                placeholder={t("filter_search_ph")}
                className="w-full pl-8 pr-3 py-2 text-sm rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition"
              />
            </div>
            <div className="flex items-center gap-1.5">
              <label className="text-xs font-semibold text-[#848484] whitespace-nowrap">{t("filter_from")}</label>
              <input
                type="date"
                value={fromDate}
                onChange={e => { setFromDate(e.target.value); setExpandedRow(null); setVisibleCount(10); }}
                className="py-2 px-2.5 text-sm rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition"
              />
            </div>
            <div className="flex items-center gap-1.5">
              <label className="text-xs font-semibold text-[#848484] whitespace-nowrap">{t("filter_to")}</label>
              <input
                type="date"
                value={toDate}
                onChange={e => { setToDate(e.target.value); setExpandedRow(null); setVisibleCount(10); }}
                className="py-2 px-2.5 text-sm rounded-xl border border-[#e5e7eb] bg-[#F2F2F2] focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 outline-none transition"
              />
            </div>
            {hasFilters && (
              <button
                onClick={() => { setSearch(""); setFromDate(""); setToDate(""); setExpandedRow(null); setVisibleCount(10); }}
                className="flex items-center gap-1 text-xs font-semibold text-[#848484] hover:text-[#8324FF] bg-[#F2F2F2] hover:bg-[#f3ebff] border border-[#e5e7eb] hover:border-[#8324FF]/30 px-3 py-2 rounded-xl transition-colors"
              >
                <svg className="w-3 h-3" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12"/></svg>
                {t("filter_clear")}
              </button>
            )}
          </div>

          {/* Status tabs */}
          <div className="flex gap-1 overflow-x-auto pb-0 -mb-px">
            {STATUS_TAB_KEYS.map(tab => {
              const count = tab.key === "all" ? stats.all : orders.filter(o => o.status === tab.key).length;
              return (
                <button
                  key={tab.key}
                  onClick={() => { setActiveTab(tab.key); setVisibleCount(10); setExpandedRow(null); }}
                  className={`flex-shrink-0 flex items-center gap-1.5 px-4 py-2.5 text-sm font-semibold rounded-t-xl border-b-2 transition-all ${
                    activeTab === tab.key
                      ? "bg-[#8324FF] text-white border-[#8324FF]"
                      : "text-[#848484] border-transparent hover:text-[#111827] hover:bg-[#F2F2F2]"
                  }`}
                >
                  {t(tab.labelKey)}
                  <span className={`text-xs px-1.5 py-0.5 rounded-full font-bold ${
                    activeTab === tab.key ? "bg-white/20 text-white" : "bg-[#F2F2F2] text-[#848484]"
                  }`}>
                    {count}
                  </span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-y border-[#e5e7eb] bg-[#F2F2F2]">
                {([
                  { key: "customer_name",   label: t("col_customer"), align: "left",  px: "px-5" },
                  { key: null,              label: t("col_items"),    align: "left",  px: "px-4" },
                  { key: "order_date",      label: t("col_date"),     align: "left",  px: "px-4" },
                  { key: "due_date",        label: t("col_due"),      align: "left",  px: "px-4" },
                  { key: "status",          label: t("col_status"),   align: "left",  px: "px-4" },
                  { key: "payment_status",  label: t("col_payment"),  align: "left",  px: "px-4" },
                  { key: "total_price",     label: t("col_total"),    align: "right", px: "px-4" },
                ] as const).map(({ key, label, align, px }) => (
                  <th
                    key={label}
                    className={`${px} py-3 text-${align} text-xs font-semibold uppercase tracking-wider select-none ${
                      key ? "cursor-pointer hover:text-[#8324FF] transition-colors" : ""
                    } ${key && sortField === key ? "text-[#8324FF]" : "text-[#848484]"}`}
                    onClick={() => key && handleSort(key as SortField)}
                  >
                    {label}
                    {key && <SortIcon field={key} active={sortField === key} dir={sortDir} />}
                  </th>
                ))}
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody className="divide-y divide-[#f3f4f6]">
              {filtered.length === 0 ? (
                <tr>
                  <td colSpan={8} className="px-5 py-12 text-center text-[#848484] text-sm">
                    {t("no_orders")}
                  </td>
                </tr>
              ) : filtered.slice(0, visibleCount).map((order: OrderRow) => {
                const isExpanded = expandedRow === order.id;
                return (
                  <React.Fragment key={order.id}>
                    <tr
                      className={`group hover:bg-[#fafafa] cursor-pointer transition-colors ${isExpanded ? "bg-[#fafafa]" : ""}`}
                      onClick={() => setExpandedRow(isExpanded ? null : order.id)}
                    >
                      <td className="px-5 py-3.5">
                        <div className="flex items-center gap-2.5">
                          <div
                            className="w-8 h-8 rounded-full flex-shrink-0 flex items-center justify-center text-white text-xs font-bold"
                            style={{ background: `hsl(${Math.abs([...order.customer_name].reduce((h, c) => c.charCodeAt(0) + ((h << 5) - h), 0)) % 360}, 56%, 42%)` }}
                          >
                            {order.customer_initials}
                          </div>
                          <div>
                            <p className="font-semibold text-[#111827]">{order.customer_name}</p>
                            <p className="text-xs text-[#848484]">#{order.id}</p>
                          </div>
                        </div>
                      </td>
                      <td className="px-4 py-3.5">
                        <span className="text-[#111827] font-medium">{order.garment}</span>
                        {order.color && <span className="text-xs text-[#848484] ml-1">· {order.color}</span>}
                      </td>
                      <td className="px-4 py-3.5 text-[#848484] whitespace-nowrap">
                        {order.order_date ? new Date(order.order_date).toLocaleDateString("en-GB", { day: "numeric", month: "short" }) : "—"}
                      </td>
                      <td className="px-4 py-3.5 text-[#848484] whitespace-nowrap">
                        {order.due_date ? new Date(order.due_date).toLocaleDateString("en-GB", { day: "numeric", month: "short" }) : "—"}
                      </td>
                      <td className="px-4 py-3.5"><StatusBadge value={order.status} /></td>
                      <td className="px-4 py-3.5"><PayBadge value={order.payment_status} /></td>
                      <td className="px-4 py-3.5 text-right font-bold text-[#111827]">
                        {order.total_price != null ? `$${Number(order.total_price).toFixed(2)}` : "—"}
                      </td>
                      <td className="px-4 py-3.5">
                        <div className="flex items-center gap-1.5 justify-end opacity-0 group-hover:opacity-100 transition-opacity">
                          <a
                            href={`${DJANGO_URL}/admin/shop/order/${order.id}/change/`}
                            target="_blank" rel="noopener noreferrer"
                            onClick={e => e.stopPropagation()}
                            className="p-1.5 rounded-lg hover:bg-[#f3ebff] hover:text-[#8324FF] text-[#848484] transition-colors"
                            title="Edit in admin"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                            </svg>
                          </a>
                          <Link
                            href={`/customers/${order.customer_id}`}
                            onClick={e => e.stopPropagation()}
                            className="p-1.5 rounded-lg hover:bg-[#f3ebff] hover:text-[#8324FF] text-[#848484] transition-colors"
                            title="Customer profile"
                          >
                            <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                              <path strokeLinecap="round" strokeLinejoin="round" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                            </svg>
                          </Link>
                          <button className="p-1.5 rounded-lg hover:bg-[#f3ebff] hover:text-[#8324FF] text-[#848484] transition-colors">
                            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                              <circle cx="5" cy="12" r="1.5" /><circle cx="12" cy="12" r="1.5" /><circle cx="19" cy="12" r="1.5" />
                            </svg>
                          </button>
                        </div>
                      </td>
                    </tr>
                    {isExpanded && (
                      <tr className="bg-[#fafafa]">
                        <td colSpan={8} className="px-5 pb-4">
                          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2 border-t border-[#f0f0f0]">
                            {[
                              { label: t("expand_assigned"),   value: order.assigned_to || t("unassigned") },
                              {
                                label: t("expand_priority"),
                                value: (() => {
                                  const raw = order.priority ?? "normal";
                                  const base = typeof raw === "string" ? raw : String(raw);
                                  const s = (base || "normal").toLowerCase();
                                  return s.charAt(0).toUpperCase() + s.slice(1);
                                })(),
                              },
                              { label: t("expand_order_date"), value: order.order_date ? new Date(order.order_date).toLocaleDateString("en-GB") : "—" },
                              { label: t("expand_due_date"),   value: order.due_date   ? new Date(order.due_date).toLocaleDateString("en-GB") : t("not_set") },
                            ].map(({ label, value }) => (
                              <div key={label}>
                                <p className="text-xs text-[#848484] mb-0.5">{label}</p>
                                <p className="text-sm font-semibold text-[#111827]">{value}</p>
                              </div>
                            ))}
                          </div>
                        </td>
                      </tr>
                    )}
                  </React.Fragment>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Show more / result count footer */}
        {filtered.length > 0 && (
          <div className="px-5 py-6 border-t border-[#f3f4f6] flex flex-col items-center gap-3">
            <p className="text-xs text-[#848484]">
              {Math.min(visibleCount, filtered.length)} / {filtered.length}
            </p>
            {visibleCount < filtered.length ? (
              <button
                onClick={() => setVisibleCount(v => v + 10)}
                className="flex items-center gap-2 text-sm font-bold text-white bg-[#8324FF] hover:bg-[#9b47ff] px-8 py-2.5 rounded-2xl transition-all duration-200"
                style={{ boxShadow: "0 0 18px 4px rgba(131,36,255,0.45), 0 2px 8px rgba(131,36,255,0.25)" }}
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2.5} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                </svg>
                {t("show_more")}
              </button>
            ) : visibleCount > 10 && (
              <button
                onClick={() => { setVisibleCount(10); setExpandedRow(null); }}
                className="text-xs font-semibold text-[#848484] hover:text-[#8324FF] transition-colors"
              >
                {t("show_less")}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
