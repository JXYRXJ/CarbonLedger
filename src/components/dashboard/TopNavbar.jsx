import { useNavigate } from "react-router-dom";
import { Bell, Menu, Search } from "lucide-react";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu, DropdownMenuContent, DropdownMenuItem,
  DropdownMenuLabel, DropdownMenuSeparator, DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuth } from "@/contexts/AuthContext.jsx";

export default function TopNavbar({ onOpenMobile }) {
  const navigate = useNavigate();
  const { user, logout } = useAuth();
  const initials = (user?.companyName || user?.email || "C L")
    .split(" ").map((p) => p[0]).slice(0, 2).join("").toUpperCase();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/85 px-4 backdrop-blur-xl sm:px-6">
      <button
        onClick={onOpenMobile}
        className="grid h-9 w-9 place-items-center rounded-md border border-border lg:hidden"
        aria-label="Open sidebar"
      >
        <Menu className="h-4 w-4" />
      </button>
      <div className="relative hidden max-w-md flex-1 sm:block">
        <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input placeholder="Search registry, assets, orders…" className="pl-9" />
      </div>
      <div className="ml-auto flex items-center gap-2">
        <button
          onClick={() => navigate("/settings?tab=notifications")}
          className="relative grid h-9 w-9 place-items-center rounded-md border border-border hover:bg-muted"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          <span className="absolute right-2 top-2 h-1.5 w-1.5 rounded-full bg-[color:var(--accent)]" />
        </button>
        <DropdownMenu>
          <DropdownMenuTrigger className="flex items-center gap-3 rounded-md p-1.5 pr-3 hover:bg-muted">
            <Avatar className="h-8 w-8">
              <AvatarFallback className="bg-primary text-primary-foreground text-xs">{initials}</AvatarFallback>
            </Avatar>
            <div className="hidden text-left sm:block">
              <p className="text-sm font-medium leading-tight text-foreground">
                {user?.companyName || "Your Company"}
              </p>
              <p className="text-xs text-muted-foreground">{user?.email}</p>
            </div>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <DropdownMenuLabel>My Account</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate("/settings?tab=profile")}>Profile</DropdownMenuItem>
            <DropdownMenuItem onClick={() => navigate("/settings?tab=notifications")}>Settings</DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout}>Log out</DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
}
