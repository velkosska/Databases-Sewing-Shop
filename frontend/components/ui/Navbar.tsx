"use client";
import { useI18n } from "@/lib/i18n";

interface Props {
  title?: string;
}

export function Navbar({ title }: Props) {
  const { lang, setLang } = useI18n();

  return (
    <header className="sticky top-0 z-30 bg-white border-b border-[#e5e7eb] px-6 h-16 flex items-center justify-between gap-4 shadow-sm">
      {/* Title */}
      {title && (
        <h1 className="text-lg font-bold text-[#111827] whitespace-nowrap">{title}</h1>
      )}

      {/* Right side */}
      <div className="flex items-center gap-3 flex-shrink-0">

        {/* Language switcher */}
        <div className="flex items-center bg-[#F2F2F2] rounded-xl border border-[#e5e7eb] p-0.5">
          <button
            onClick={() => setLang("en")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              lang === "en"
                ? "bg-[#8324FF] text-white shadow-sm"
                : "text-[#848484] hover:text-[#111827]"
            }`}
          >
            <span className="text-sm leading-none">🇬🇧</span>
            EN
          </button>
          <button
            onClick={() => setLang("es")}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${
              lang === "es"
                ? "bg-[#8324FF] text-white shadow-sm"
                : "text-[#848484] hover:text-[#111827]"
            }`}
          >
            <span className="text-sm leading-none">🇪🇸</span>
            ES
          </button>
        </div>

        {/* Notification bell */}
        <button className="relative w-9 h-9 rounded-xl border border-[#e5e7eb] bg-white flex items-center justify-center text-[#848484] hover:border-[#8324FF] hover:text-[#8324FF] transition">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
          </svg>
        </button>

        {/* Avatar */}
        <div className="flex items-center gap-2 cursor-pointer">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-[#8324FF] to-[#FF77E6] flex items-center justify-center text-white text-xs font-bold">
            SS
          </div>
          <div className="hidden sm:block">
            <p className="text-sm font-semibold text-[#111827] leading-none">Sewing Shop</p>
            <p className="text-xs text-[#848484] leading-none mt-0.5">Admin</p>
          </div>
          <svg className="w-4 h-4 text-[#848484]" fill="none" stroke="currentColor" strokeWidth={2} viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
          </svg>
        </div>
      </div>
    </header>
  );
}
