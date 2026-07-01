import { Card } from "@/components/ui/card";
import { fmtNumber } from "@/lib/format.js";

export default function OwnershipCard({ entries = [] }) {
  if (!entries.length) {
    return <p className="text-sm text-muted-foreground">No ownership records yet.</p>;
  }
  const total = entries.reduce((s, e) => s + Number(e.credits || 0), 0) || 1;
  return (
    <div className="space-y-3">
      {entries.map((e, i) => {
        const pct = (Number(e.credits || 0) / total) * 100;
        return (
          <Card key={i} className="p-4">
            <div className="flex items-center justify-between text-sm">
              <span className="font-medium text-foreground">{e.owner?.companyName || e.ownerName || "—"}</span>
              <span className="text-muted-foreground">{fmtNumber(e.credits)} credits</span>
            </div>
            <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted">
              <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
            </div>
            <p className="mt-1 text-xs text-muted-foreground">{pct.toFixed(1)}%</p>
          </Card>
        );
      })}
    </div>
  );
}