import { api, CatalogueItem, Employee, Material, DjangoOfflineError } from "@/lib/api";
import { Navbar } from "@/components/ui/Navbar";
import { OrderWizardClient } from "./OrderWizardClient";
import OfflineError from "@/components/ui/OfflineError";

export const dynamic = "force-dynamic";

export default async function NewOrderPage({
  searchParams,
}: {
  searchParams: Promise<{ from?: string }>;
}) {
  const { from } = await searchParams;
  const fromAdmin = from === "admin";

  let catalogueRes: { catalogue: CatalogueItem[] };
  let employeesRes: { employees: Employee[] };
  let customersRes: { customers: Array<{ id: number; name: string; phone: string; email: string; address: string; order_count: number }> };
  let materialsRes: { materials: Material[] };

  try {
    [catalogueRes, employeesRes, customersRes, materialsRes] = await Promise.all([
      api.get<{ catalogue: CatalogueItem[] }>("/catalogue/"),
      api.get<{ employees: Employee[] }>("/employees/"),
      api.get<{ customers: Array<{ id: number; name: string; phone: string; email: string; address: string; order_count: number }> }>("/customers/"),
      api.get<{ materials: Material[] }>("/materials/"),
    ]);
  } catch (err) {
    if (err instanceof DjangoOfflineError) return <OfflineError />;
    throw err;
  }

  return (
    <>
      <Navbar title="New Order" />
      <OrderWizardClient
        catalogue={catalogueRes.catalogue}
        employees={employeesRes.employees}
        customers={customersRes.customers}
        materials={materialsRes.materials}
        fromAdmin={fromAdmin}
      />
    </>
  );
}
