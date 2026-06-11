import type { Metadata } from "next";
import { CustomerOrderForm } from "@/components/landing/CustomerOrderForm";

export const metadata: Metadata = {
  title: "Hacer pedido",
  description: "Pide arreglo o confección en Costuras de Paqui. Te confirmamos presupuesto en menos de 24 horas.",
};

export default function PedidoPage() {
  return <CustomerOrderForm />;
}
