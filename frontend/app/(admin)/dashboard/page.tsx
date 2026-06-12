import { api, DashboardData, isBackendUnavailable } from "@/lib/api";
import { Navbar } from "@/components/ui/Navbar";
import { DashboardClient } from "./DashboardClient";
import OfflineError from "@/components/ui/OfflineError";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let data: DashboardData;
  try {
    data = await api.get<DashboardData>("/dashboard/");
  } catch (err) {
    if (isBackendUnavailable(err)) {
      return (
        <OfflineError message="No se pudo cargar el panel. Comprueba que Django está en marcha en Railway, DATABASE_URL apunta a Supabase, y migrate se ha ejecutado." />
      );
    }
    throw err;
  }
  return (
    <>
      <Navbar title="Dashboard" />
      <DashboardClient data={data} />
    </>
  );
}
