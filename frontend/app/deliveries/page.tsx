import { api, DeliveriesData, DjangoOfflineError } from "@/lib/api";
import { Navbar } from "@/components/ui/Navbar";
import OfflineError from "@/components/ui/OfflineError";
import { DeliveriesClient } from "./DeliveriesClient";

export const dynamic = "force-dynamic";

export default async function DeliveriesPage() {
  let data: DeliveriesData;
  try {
    data = await api.get<DeliveriesData>("/deliveries/");
  } catch (err) {
    if (err instanceof DjangoOfflineError) return <OfflineError />;
    throw err;
  }
  return (
    <>
      <Navbar />
      <DeliveriesClient deliveries={data.deliveries} />
    </>
  );
}
