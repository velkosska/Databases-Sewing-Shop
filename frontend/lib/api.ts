// Server-side: call Django directly (uses DJANGO_INTERNAL_URL in production). Client-side: use Next.js rewrites (/api/*).
const SERVER_BASE = process.env.DJANGO_INTERNAL_URL ?? "http://127.0.0.1:8000";
const CLIENT_BASE = "";

function base() {
  return typeof window === "undefined" ? SERVER_BASE : CLIENT_BASE;
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

export class DjangoOfflineError extends Error {
  constructor() {
    super("Django server is not running. Start it with: python manage.py runserver");
    this.name = "DjangoOfflineError";
  }
}

// Strip trailing slash so server-side and client-side (proxy) paths are identical
function normPath(path: string) {
  return path.endsWith("/") ? path.slice(0, -1) : path;
}

async function get<T>(path: string): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${base()}/api${normPath(path)}`, {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    if (msg.includes("ECONNREFUSED") || msg.includes("fetch failed")) {
      throw new DjangoOfflineError();
    }
    throw err;
  }
  if (!res.ok) throw new ApiError(res.status, `API ${res.status}: ${path}`);
  return res.json();
}

async function post<T>(path: string, body: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(`${base()}/api${normPath(path)}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Accept: "application/json" },
      body: JSON.stringify(body),
    });
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : String(err);
    if (msg.includes("ECONNREFUSED") || msg.includes("fetch failed")) {
      throw new DjangoOfflineError();
    }
    throw err;
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new ApiError(res.status, (err as { error?: string }).error ?? `API error ${res.status}`);
  }
  return res.json();
}

export const api = { get, post };

// ── Types ──────────────────────────────────────────────────────────────────

export interface OrderRow {
  id: number;
  customer_id: number;
  customer_name: string;
  customer_initials: string;
  garment: string;
  color: string;
  order_date: string | null;
  due_date: string | null;
  assigned_to: string;
  priority: string;
  status: string;
  payment_status: string;
  total_price: number | null;
}

export interface DashboardData {
  stats: {
    all: number; pending: number; in_production: number;
    overdue: number; completed: number; delivered: number;
  };
  revenue: { total: number; deposit: number; balance_outstanding: number; };
  kpi_changes: {
    orders:  number | null;
    revenue: number | null;
    pending: number | null;
    balance: number | null;
  };
  charts: {
    monthly_orders: Array<{ month: string; orders: number }>;
    weekly_revenue: Array<{ day: string; revenue: number }>;
  };
  low_stock: Array<{
    id: number; name: string; color: string | null;
    stock_quantity: number; low_stock_threshold: number;
  }>;
  orders: OrderRow[];
  last_updated: string;
}

export interface CatalogueItem {
  id: number; source: string; name: string;
  garment_types: string[]; base_price: number;
  price_hint: string; requires_measurements: boolean;
}

export interface Employee { id: number; name: string; role: string; }

export interface Customer {
  id: number; name: string; phone: string;
  email: string; address: string; order_count: number;
}

export interface Material {
  id: number; name: string; color: string;
  unit_price: number; stock_quantity: number | null; is_low_stock: boolean;
}

export interface TicketCard {
  id: number; order_id: number; customer: string; garment: string;
  color: string; assigned_to: string | null; assigned_employee_id: number | null;
  priority: string; deadline: string | null; is_overdue: boolean;
  current_stage: string; stage_count: number;
  status: string; notes?: string;
}

export interface BoardData {
  board: { pending: TicketCard[]; in_progress: TicketCard[]; done: TicketCard[]; };
  employees: Employee[];
}

export interface DeliveryRow {
  id: number;
  order_id: number;
  customer_name: string;
  recipient_name: string;
  delivery_method: string | null;
  delivery_method_label: string;
  delivered: boolean;
  delivered_at: string | null;
  comments: string;
}

export interface DeliveriesData {
  deliveries: DeliveryRow[];
}

export interface CustomerDetail {
  id: number; first_name: string; last_name: string; full_name: string;
  phone: string; email: string; address: string; notes: string;
  created_at: string | null; total_spent: number;
  orders: Array<{
    id: number; order_date: string | null; due_date: string | null;
    status: string; payment_status: string; total_price: number | null;
    items: Array<{
      id: number; garment_type: string; catalogue_name: string | null;
      quantity: number; final_price: number | null; color: string | null;
    }>;
  }>;
  measurements: {
    bust: number | null; waist: number | null; hips: number | null;
    shoulder: number | null; sleeve: number | null; length: number | null;
    inseam: number | null; neck: number | null; notes: string | null;
    recorded_at: string;
  } | null;
}
