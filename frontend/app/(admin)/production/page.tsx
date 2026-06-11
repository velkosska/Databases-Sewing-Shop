import { api, BoardData, DjangoOfflineError } from "@/lib/api";
import { Navbar } from "@/components/ui/Navbar";
import { ProductionBoardClient } from "./ProductionBoardClient";
import OfflineError from "@/components/ui/OfflineError";

export const dynamic = "force-dynamic";

export default async function ProductionPage() {
  let data: BoardData;
  try {
    data = await api.get<BoardData>("/production/board/");
  } catch (err) {
    if (err instanceof DjangoOfflineError) return <OfflineError />;
    throw err;
  }
  return (
    <>
      <Navbar title="Production Board" />
      <ProductionBoardClient data={data} />
    </>
  );
}
