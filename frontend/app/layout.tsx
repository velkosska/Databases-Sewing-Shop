import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/ui/Sidebar";
import { I18nProvider } from "@/lib/i18n";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Sewing Shop",
  description: "Order tracking, production, and customer management.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-[#F2F2F2]">
        <I18nProvider>
          <Sidebar />
          <div className="ml-[72px] min-h-screen flex flex-col">
            {children}
          </div>
        </I18nProvider>
      </body>
    </html>
  );
}
