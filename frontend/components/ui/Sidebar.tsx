"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useI18n, TKey } from "@/lib/i18n";

const NAV_DEFS: { href: string; labelKey: TKey; external?: boolean; icon: React.ReactNode }[] = [
  {
    href: "/",
    labelKey: "nav_dashboard",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-5 h-5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
      </svg>
    ),
  },
  {
    href: "/orders/new",
    labelKey: "nav_new_order",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-5 h-5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 4v16m8-8H4" />
      </svg>
    ),
  },
  {
    href: "/production",
    labelKey: "nav_production",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-5 h-5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
      </svg>
    ),
  },
  {
    href: "/deliveries",
    labelKey: "nav_deliveries",
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-5 h-5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 17a2 2 0 11-4 0 2 2 0 014 0zM19 17a2 2 0 11-4 0 2 2 0 014 0z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M13 17V6h5l3 5v6h-2m-14 0H4V9l3-5h9" />
      </svg>
    ),
  },
  {
    href: "http://127.0.0.1:8000/admin/",
    labelKey: "nav_admin",
    external: true,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-5 h-5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
];

const BOTTOM_DEFS: { href: string; labelKey: TKey; external?: boolean; icon: React.ReactNode }[] = [
  {
    href: "http://127.0.0.1:8000/admin/",
    labelKey: "nav_settings",
    external: true,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.8} className="w-5 h-5">
        <path strokeLinecap="round" strokeLinejoin="round" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
      </svg>
    ),
  },
];

export function Sidebar() {
  const path = usePathname();
  const { t } = useI18n();

  function isActive(href: string) {
    if (href === "/") return path === "/";
    return path.startsWith(href);
  }

  function NavItem({ href, labelKey, icon, external }: typeof NAV_DEFS[0]) {
    const label = t(labelKey);
    const active = isActive(href);
    const cls = `group relative flex items-center justify-center w-11 h-11 rounded-xl transition-all ${
      active
        ? "bg-[#8324FF] text-white shadow-lg shadow-purple-500/30"
        : "text-[#848484] hover:bg-white/10 hover:text-white"
    }`;
    const tooltip = (
      <span className="absolute left-full ml-3 hidden group-hover:block bg-[#111827] text-white text-xs font-medium px-2 py-1 rounded-lg whitespace-nowrap z-50 pointer-events-none shadow-lg">
        {label}
      </span>
    );
    if (external) {
      return (
        <a href={href} target="_blank" rel="noopener noreferrer" className={cls} title={label}>
          {icon}{tooltip}
        </a>
      );
    }
    return (
      <Link href={href} className={cls} title={label}>
        {icon}{tooltip}
      </Link>
    );
  }

  return (
    <aside className="fixed left-0 top-0 h-screen w-[72px] bg-[#111827] flex flex-col items-center py-5 z-40">
      {/* Logo */}
      <div className="w-10 h-10 rounded-xl bg-[#8324FF] flex items-center justify-center mb-8 shadow-lg shadow-purple-500/30 flex-shrink-0">
        <svg viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth={2} className="w-5 h-5">
          <path strokeLinecap="round" strokeLinejoin="round" d="M14.121 14.121L19 19m-7-7l7-7m-7 7l-2.879 2.879M12 12L9.121 9.121m0 5.758a3 3 0 10-4.243 4.243 3 3 0 004.243-4.243zm0-5.758a3 3 0 10-4.243-4.243 3 3 0 004.243 4.243z" />
        </svg>
      </div>

      <nav className="flex flex-col gap-2 flex-1">
        {NAV_DEFS.map(item => <NavItem key={item.href} {...item} />)}
      </nav>

      <div className="flex flex-col gap-2 mt-4">
        {BOTTOM_DEFS.map(item => <NavItem key={item.href} {...item} />)}
        <div className="w-9 h-9 rounded-full bg-gradient-to-br from-[#8324FF] to-[#FF77E6] flex items-center justify-center text-white text-xs font-bold mt-2 cursor-pointer" title="Profile">
          SS
        </div>
      </div>
    </aside>
  );
}
