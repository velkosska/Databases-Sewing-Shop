import { Sidebar } from "@/components/ui/Sidebar";
import { I18nProvider } from "@/lib/i18n";

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  return (
    <I18nProvider>
      <div className="min-h-screen bg-[#F2F2F2]">
        <Sidebar />
        <div className="ml-[72px] min-h-screen flex flex-col">{children}</div>
      </div>
    </I18nProvider>
  );
}
