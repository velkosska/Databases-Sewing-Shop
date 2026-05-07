import { api, DashboardData, DjangoOfflineError } from "@/lib/api";
import { Navbar } from "@/components/ui/Navbar";
import { DashboardClient } from "./DashboardClient";
import OfflineError from "@/components/ui/OfflineError";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  let data: DashboardData;
  try {
    data = await api.get<DashboardData>("/dashboard/");
  } catch (err) {
    if (err instanceof DjangoOfflineError) return <OfflineError />;
    throw err;
  }
  return (
    <>
      <Navbar title="Dashboard" />
      <DashboardClient data={data} />
    </>
  );
}
