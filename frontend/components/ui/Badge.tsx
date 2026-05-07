import { clsx } from "clsx";

type Variant = "pending" | "in_production" | "completed" | "delivered" | "overdue" | "cancelled"
  | "unpaid" | "deposit" | "paid"
  | "urgent" | "high" | "normal" | "low"
  | "neutral";

const variants: Record<Variant, string> = {
  pending:       "bg-amber-50 text-amber-800 ring-amber-200",
  in_production: "bg-blue-50 text-blue-800 ring-blue-200",
  completed:     "bg-green-50 text-green-800 ring-green-200",
  delivered:     "bg-teal-50 text-teal-800 ring-teal-200",
  overdue:       "bg-red-50 text-red-800 ring-red-200",
  cancelled:     "bg-gray-100 text-gray-600 ring-gray-200",
  unpaid:        "bg-red-50 text-red-800 ring-red-200",
  deposit:       "bg-amber-50 text-amber-800 ring-amber-200",
  paid:          "bg-green-50 text-green-800 ring-green-200",
  urgent:        "bg-red-50 text-red-800 ring-red-200",
  high:          "bg-orange-50 text-orange-800 ring-orange-200",
  normal:        "bg-blue-50 text-blue-800 ring-blue-200",
  low:           "bg-gray-100 text-gray-600 ring-gray-200",
  neutral:       "bg-gray-100 text-gray-600 ring-gray-200",
};

const labels: Partial<Record<string, string>> = {
  pending:       "Pending",
  in_production: "In Production",
  completed:     "Completed",
  delivered:     "Delivered",
  unpaid:        "Unpaid",
  deposit:       "Deposit",
  paid:          "Paid",
  urgent:        "Urgent",
  high:          "High",
  normal:        "Normal",
  low:           "Low",
};

interface Props {
  value: string;
  override?: string;
  className?: string;
}

export function Badge({ value, override, className }: Props) {
  const key = value as Variant;
  const style = variants[key] ?? variants.neutral;
  const label = override ?? labels[value] ?? value.replace(/_/g, " ");
  return (
    <span className={clsx(
      "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ring-1 ring-inset",
      style, className
    )}>
      {label}
    </span>
  );
}
