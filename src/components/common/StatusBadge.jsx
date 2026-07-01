import { Badge } from "@/components/ui/badge";

const MAP = {
  active: { label: "Active", cls: "bg-[color:var(--success)]/10 text-[color:var(--success)]" },
  pending: { label: "Pending", cls: "bg-[color:var(--warning)]/10 text-[color:var(--warning)]" },
  completed: { label: "Completed", cls: "bg-[color:var(--success)]/10 text-[color:var(--success)]" },
  cancelled: { label: "Cancelled", cls: "bg-muted text-muted-foreground" },
  failed: { label: "Failed", cls: "bg-[color:var(--danger)]/10 text-[color:var(--danger)]" },
  retired: { label: "Retired", cls: "bg-primary/10 text-primary" },
  listed: { label: "Listed", cls: "bg-accent/10 text-accent" },
  verified: { label: "Verified", cls: "bg-[color:var(--success)]/10 text-[color:var(--success)]" },
  draft: { label: "Draft", cls: "bg-muted text-muted-foreground" },
  confirmed: { label: "Confirmed", cls: "bg-[color:var(--success)]/10 text-[color:var(--success)]" },
  unconfirmed: { label: "Unconfirmed", cls: "bg-[color:var(--warning)]/10 text-[color:var(--warning)]" },
};

export default function StatusBadge({ status, children, className = "" }) {
  const key = String(status || "").toLowerCase();
  const m = MAP[key] || { label: status || "—", cls: "bg-muted text-muted-foreground" };
  return (
    <Badge className={`${m.cls} hover:${m.cls} border-0 ${className}`}>
      {children || m.label}
    </Badge>
  );
}