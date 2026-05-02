"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Briefcase, Users, Zap, BarChart3 } from "lucide-react";

const navItems = [
  { label: "Jobs", href: "/dashboard", icon: Briefcase },
  { label: "Candidates", href: "/candidates", icon: Users },
];

export default function Sidebar() {
  const pathname = usePathname();

  const isActive = (href: string) => {
    if (href === "/dashboard") return pathname === "/dashboard" || pathname.startsWith("/jobs");
    if (href === "/candidates") return pathname.startsWith("/candidates");
    return pathname.startsWith(href);
  };

  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="sidebar-logo-mark">
          <div className="sidebar-logo-icon">M</div>
          <div className="sidebar-logo-text">
            Match<span>IQ</span>
          </div>
        </div>
        <div style={{ fontSize: 11, color: "var(--text-faint)", marginTop: 4, paddingLeft: 46 }}>
          AI Matching Engine
        </div>
      </div>

      {/* Nav */}
      <nav className="sidebar-nav">
        <div className="nav-section-label">Workspace</div>
        {navItems.map(({ label, href, icon: Icon }) => (
          <Link key={href} href={href} className={`nav-item ${isActive(href) ? "active" : ""}`}>
            <Icon size={16} />
            {label}
          </Link>
        ))}

        <div className="nav-section-label" style={{ marginTop: 8 }}>Pipeline</div>
        <div className="nav-item" style={{ cursor: "default", opacity: 0.5 }}>
          <BarChart3 size={16} />
          Analytics
          <span style={{ marginLeft: "auto", fontSize: 10, background: "var(--surface-2)", padding: "1px 6px", borderRadius: 99, color: "var(--text-faint)" }}>soon</span>
        </div>
        <div className="nav-item" style={{ cursor: "default", opacity: 0.5 }}>
          <Zap size={16} />
          Bulk Match
          <span style={{ marginLeft: "auto", fontSize: 10, background: "var(--surface-2)", padding: "1px 6px", borderRadius: 99, color: "var(--text-faint)" }}>soon</span>
        </div>
      </nav>

      {/* Footer badge */}
      <div className="sidebar-footer">
        <div className="sidebar-badge">
          <div className="sidebar-badge-dot" />
          <div className="sidebar-badge-text">All systems online</div>
        </div>
      </div>
    </aside>
  );
}
