"use client";
import { useState } from "react";
import { clsx } from "clsx";
import { BoardData, TicketCard } from "@/lib/api";
import { useI18n } from "@/lib/i18n";
import { adminUrl } from "@/lib/django";

const PRIORITY_DOT: Record<string, string> = {
  urgent: "bg-red-500",
  high:   "bg-[#FF863F]",
  normal: "bg-[#30D3FF]",
  low:    "bg-[#848484]",
};

const COLUMNS = [
  { key: "pending",     labelKey: "prod_pending"     as const, accentBg: "bg-[#fff9e8]", accentText: "text-[#FFC430]", accentBorder: "border-[#FFC430]/30", countBg: "bg-[#FFC430]" },
  { key: "in_progress", labelKey: "prod_in_progress" as const, accentBg: "bg-[#e8fafe]", accentText: "text-[#30D3FF]", accentBorder: "border-[#30D3FF]/30", countBg: "bg-[#30D3FF]" },
  { key: "done",        labelKey: "prod_done"        as const, accentBg: "bg-green-50",  accentText: "text-green-600", accentBorder: "border-green-200",     countBg: "bg-green-500"  },
] as const;

function TicketCardEl({ ticket, onOpen }: { ticket: TicketCard; onOpen: (t: TicketCard) => void }) {
  const { t } = useI18n();
  return (
    <button
      onClick={() => onOpen(ticket)}
      className={clsx(
        "w-full rounded-2xl border bg-white p-4 text-left shadow-sm transition-all hover:-translate-y-0.5 hover:shadow-md",
        ticket.is_overdue ? "border-red-300" : "border-[#e5e7eb]"
      )}
    >
      <div className="flex items-start justify-between gap-2 mb-3">
        <span className={clsx("font-bold text-sm", ticket.is_overdue ? "text-red-600" : "text-[#111827]")}>
          {ticket.garment}
        </span>
        <span className={clsx(
          "w-2 h-2 rounded-full flex-shrink-0 mt-1",
          PRIORITY_DOT[ticket.priority] ?? "bg-gray-300"
        )} />
      </div>

      <div className="text-xs text-[#848484] space-y-0.5 mb-3">
        <div className="font-medium text-[#111827]">{ticket.customer}</div>
        <div>Order #{ticket.order_id}{ticket.color ? ` · ${ticket.color}` : ""}</div>
      </div>

      <div className="flex items-center justify-between">
        <span className="text-xs bg-[#F2F2F2] text-[#848484] rounded-full px-2.5 py-1 font-medium truncate max-w-[120px]">
          {ticket.current_stage}
        </span>
        <span className={clsx(
          "text-xs font-semibold",
          ticket.is_overdue ? "text-red-500" : ticket.deadline ? "text-[#FFC430]" : "text-[#848484]"
        )}>
          {ticket.is_overdue ? t("prod_overdue") : ticket.deadline ? ticket.deadline : t("prod_no_deadline")}
        </span>
      </div>

      {ticket.assigned_to && (
        <div className="mt-2.5 flex items-center gap-1.5">
          <div className="w-5 h-5 rounded-full bg-gradient-to-br from-[#8324FF] to-[#FF77E6] flex items-center justify-center text-white text-[9px] font-bold flex-shrink-0">
            {ticket.assigned_to.charAt(0).toUpperCase()}
          </div>
          <span className="text-xs text-[#848484] truncate">{ticket.assigned_to}</span>
        </div>
      )}
    </button>
  );
}

export function ProductionBoardClient({ data }: { data: BoardData }) {
  const { t } = useI18n();
  const { board, employees } = data;
  const allTickets: TicketCard[] = [
    ...board.pending.map(t => ({ ...t, status: "pending" })),
    ...board.in_progress.map(t => ({ ...t, status: "in_progress" })),
    ...board.done.map(t => ({ ...t, status: "done" })),
  ];
  const [tickets, setTickets] = useState<TicketCard[]>(allTickets);
  const [priority, setPriority] = useState<string>("all");
  const [employee, setEmployee] = useState<string>("all");
  const [selected, setSelected] = useState<TicketCard | null>(null);
  const [statusChanging, setStatusChanging] = useState(false);

  const filtered = tickets.filter((t: TicketCard) => {
    if (priority !== "all" && t.priority !== priority) return false;
    if (employee !== "all" && String(t.assigned_employee_id) !== employee) return false;
    return true;
  });

  const countFor = (key: string) => filtered.filter((t: TicketCard) => t.status === key).length;

  async function changeStatus(ticket: TicketCard, newStatus: string) {
    setStatusChanging(true);
    try {
      await fetch(`/api/tickets/${ticket.id}/status/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status: newStatus }),
      });
      const updated = { ...ticket, status: newStatus };
      setTickets(prev => prev.map(t => t.id === ticket.id ? updated : t));
      setSelected(updated);
    } finally {
      setStatusChanging(false);
    }
  }

  return (
    <div className="p-6 space-y-5">

      {/* Filters */}
      <div className="flex flex-wrap gap-3 items-center">
        <div className="relative">
          <svg className="absolute left-3 top-1/2 -translate-y-1/2 w-3.5 h-3.5 text-[#848484]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2a1 1 0 01-.293.707L13 13.414V19a1 1 0 01-.553.894l-4 2A1 1 0 017 21v-7.586L3.293 6.707A1 1 0 013 6V4z" />
          </svg>
          <select
            value={priority}
            onChange={e => setPriority(e.target.value)}
            className="pl-8 pr-8 py-2 rounded-xl border border-[#e5e7eb] bg-white text-sm text-[#111827] focus:outline-none focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 transition appearance-none cursor-pointer"
          >
            <option value="all">{t("prod_all_priorities")}</option>
            {(["urgent","high","normal","low"] as const).map(k => (
              <option key={k} value={k}>{t(`prio_${k}`)}</option>
            ))}
          </select>
        </div>

        <select
          value={employee}
          onChange={e => setEmployee(e.target.value)}
          className="px-3 py-2 rounded-xl border border-[#e5e7eb] bg-white text-sm text-[#111827] focus:outline-none focus:border-[#8324FF] focus:ring-2 focus:ring-[#8324FF]/10 transition appearance-none cursor-pointer"
        >
          <option value="all">{t("prod_all_employees")}</option>
          {employees.map(emp => (
            <option key={emp.id} value={String(emp.id)}>{emp.name}</option>
          ))}
        </select>

        <span className="ml-auto text-xs text-[#848484] font-medium">{filtered.length} {t("prod_tickets")}</span>
      </div>

      {/* Board */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {COLUMNS.map(col => {
          const colTickets = filtered.filter((t: TicketCard) => t.status === col.key);
          return (
            <div key={col.key} className="flex flex-col gap-3">
              {/* Column header */}
              <div className={clsx("flex items-center justify-between rounded-2xl border px-4 py-3", col.accentBg, col.accentBorder)}>
                <span className={clsx("font-bold text-sm", col.accentText)}>{t(col.labelKey)}</span>
                <span className={clsx("w-6 h-6 rounded-full flex items-center justify-center text-white text-xs font-bold", col.countBg)}>
                  {countFor(col.key)}
                </span>
              </div>

              {/* Cards */}
              <div className="space-y-2.5">
                {colTickets.length === 0 ? (
                  <div className="rounded-2xl border-2 border-dashed border-[#e5e7eb] p-6 text-center text-xs text-[#848484]">
                    {t("prod_no_tickets")}
                  </div>
                ) : colTickets.map(t => (
                  <TicketCardEl key={t.id} ticket={t} onOpen={setSelected} />
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Detail modal */}
      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4"
          onClick={() => setSelected(null)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6 space-y-4"
            onClick={e => e.stopPropagation()}
          >
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-bold text-[#111827]">{selected.garment}</h3>
                <p className="text-sm text-[#848484] mt-0.5">
                  {selected.customer} · Order #{selected.order_id}
                </p>
              </div>
              <button onClick={() => setSelected(null)} className="p-1.5 rounded-lg hover:bg-[#F2F2F2] text-[#848484] transition-colors">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-sm">
              {[
                { label: t("expand_priority"),   value: t(`prio_${selected.priority}` as "prio_urgent"|"prio_high"|"prio_normal"|"prio_low") ?? selected.priority },
                { label: "Stage",                value: selected.current_stage },
                { label: t("expand_assigned"),   value: selected.assigned_to || t("unassigned") },
                { label: t("expand_due_date"),   value: selected.deadline || t("not_set") },
              ].map(({ label, value }) => (
                <div key={label} className="bg-[#F2F2F2] rounded-xl px-3 py-2">
                  <p className="text-xs text-[#848484] mb-0.5">{label}</p>
                  <p className="font-semibold text-[#111827]">{value}</p>
                </div>
              ))}
            </div>

            {selected.notes && (
              <div className="bg-[#F2F2F2] rounded-xl px-3 py-2 text-sm">
                <p className="text-xs text-[#848484] mb-1">{t("prod_notes")}</p>
                <p className="text-[#111827]">{selected.notes}</p>
              </div>
            )}

            {/* Status change */}
            <div>
              <p className="text-xs font-semibold text-[#848484] uppercase tracking-wider mb-2">{t("prod_move_to")}</p>
              <div className="flex gap-2 flex-wrap">
                {COLUMNS.map(col => (
                  <button
                    key={col.key}
                    disabled={selected.status === col.key || statusChanging}
                    onClick={() => changeStatus(selected, col.key)}
                    className={clsx(
                      "flex-1 py-2 rounded-xl text-sm font-semibold transition-all border",
                      selected.status === col.key
                        ? "bg-[#8324FF] text-white border-[#8324FF] shadow-lg shadow-purple-500/25"
                        : "bg-white text-[#848484] border-[#e5e7eb] hover:border-[#8324FF] hover:text-[#8324FF]"
                    )}
                  >
                    {t(col.labelKey)}
                  </button>
                ))}
              </div>
            </div>

            <a
              href={adminUrl(`shop/workticket/${selected.id}/change/`)}
              target="_blank"
              rel="noopener noreferrer"
              className="block w-full text-center text-xs text-[#848484] hover:text-[#8324FF] transition-colors mt-1"
            >
              {t("prod_edit_admin")}
            </a>
          </div>
        </div>
      )}
    </div>
  );
}
