import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Database, Layers, ShoppingBag, Briefcase, ListOrdered,
  ArrowLeftRight, Recycle, BarChart3, Wallet, Settings, ShieldCheck, LogOut, X,
} from "lucide-react";
import Logo from "@/components/common/Logo.jsx";
import { useAuth } from "@/contexts/AuthContext.jsx";

const NAV = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/registry", label: "Registry", icon: Database },
  { to: "/assets", label: "Assets", icon: Layers },
  { to: "/marketplace", label: "Marketplace", icon: ShoppingBag },
  { to: "/portfolio", label: "Portfolio", icon: Briefcase },
  { to: "/orders", label: "Orders", icon: ListOrdered },
  { to: "/transactions", label: "Transactions", icon: ArrowLeftRight },
  { to: "/retirement", label: "Retirement", icon: Recycle },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/wallet", label: "Wallet", icon: Wallet },
  { to: "/settings", label: "Settings", icon: Settings },
];

function NavItem({ item }) {
  const Icon = item.icon;
  return (
    <NavLink
      to={item.to}
      end={item.end}
      className={({ isActive }) =>
        `group flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors ${
          isActive
            ? "bg-primary/10 text-primary"
            : "text-muted-foreground hover:bg-muted hover:text-foreground"
        }`
      }
    >
      <Icon className="h-4 w-4 shrink-0" />
      <span className="truncate">{item.label}</span>
    </NavLink>
  );
}

function SidebarContent({ onClose }) {
  const { user, logout } = useAuth();
  const isAdmin = user?.role === "ADMIN";
  return (
    <div className="flex h-full flex-col">
      <div className="flex h-16 items-center justify-between border-b border-sidebar-border px-5">
        <Logo to="/dashboard" />
        {onClose && (
          <button onClick={onClose} className="grid h-8 w-8 place-items-center rounded-md hover:bg-muted lg:hidden" aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        )}
      </div>
      <nav className="flex-1 space-y-1 overflow-y-auto p-3">
        {NAV.map((item) => <NavItem key={item.to} item={item} />)}
        {isAdmin && <NavItem item={{ to: "/admin", label: "Admin", icon: ShieldCheck }} />}
      </nav>
      <div className="border-t border-sidebar-border p-3">
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
        >
          <LogOut className="h-4 w-4" />
          Logout
        </button>
      </div>
    </div>
  );
}

export default function Sidebar({ mobileOpen, onCloseMobile }) {
  return (
    <>
      <aside className="hidden w-64 shrink-0 border-r border-sidebar-border bg-sidebar lg:block">
        <SidebarContent />
      </aside>
      {mobileOpen && (
        <div className="fixed inset-0 z-50 lg:hidden">
          <div className="absolute inset-0 bg-foreground/40" onClick={onCloseMobile} />
          <aside className="absolute left-0 top-0 h-full w-72 bg-sidebar shadow-xl animate-in slide-in-from-left">
            <SidebarContent onClose={onCloseMobile} />
          </aside>
        </div>
      )}
    </>
  );
}
