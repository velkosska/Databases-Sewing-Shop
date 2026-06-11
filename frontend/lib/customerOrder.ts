import type { CatalogueItem } from "@/lib/api";

export interface CustomerOrderItem {
  service_type: string;
  catalogue_item_id: string;
  catalogue_source: string;
  garment_type: string;
  color_fabric: string;
  item_notes: string;
  quantity: number;
}

export interface CustomerMeasurements {
  bust: string;
  waist: string;
  hips: string;
  shoulder: string;
  sleeve: string;
  length: string;
  inseam: string;
  neck: string;
  notes: string;
}

export interface CreateCustomerOrderPayload {
  source: "web";
  new_customer: {
    first_name: string;
    last_name: string;
    phone: string;
    email: string;
    address: string;
    notes: string;
  };
  items: Array<{
    catalogue_item_id: number | null;
    catalogue_source: string;
    service_type: string;
    garment_type: string;
    color_fabric: string;
    unit_price: string;
    quantity: number;
    item_notes: string;
    requires_measurements: boolean;
    measurements: Record<string, string | null>;
  }>;
  due_date: string | null;
  priority: string;
  order_notes: string;
  internal_notes: string;
  delivery_method: "pickup" | "home_delivery";
  delivery_address: string;
  delivery_date: string | null;
  deposit_method: string;
  deposit_amount: string;
  measurements: Record<string, string | null>;
}

export interface CreateOrderResponse {
  ok: boolean;
  order_id: number;
  total_price: number;
  customer_name: string;
}

export async function createCustomerOrder(payload: CreateCustomerOrderPayload): Promise<CreateOrderResponse> {
  const res = await fetch("/api/orders/create/", {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(payload),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.error ?? "No se pudo enviar el pedido.");
  }
  return data;
}

export async function fetchCatalogue(): Promise<CatalogueItem[]> {
  const res = await fetch("/api/catalogue", { headers: { Accept: "application/json" } });
  if (!res.ok) return [];
  const data = await res.json();
  return data.catalogue ?? [];
}
