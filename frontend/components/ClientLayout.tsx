"use client";

import { usePathname } from "next/navigation";
import Sidebar from "@/components/Sidebar";

export default function ClientLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isLandingPage = pathname === "/";

  if (isLandingPage) {
    return <main className="w-full bg-white text-slate-900">{children}</main>;
  }

  return (
    <div className="app-shell bg-white text-slate-900">
      <Sidebar />
      <main className="main-content flex-1">{children}</main>
    </div>
  );
}
