import { Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import StatusBadge from "@/components/common/StatusBadge.jsx";
import { fmtNumber } from "@/lib/format.js";

export default function BatchCard({ batch }) {
  const b = batch || {};
  const total = Number(b.totalCredits || 0);
  const remaining = Number(b.remainingCredits || 0);
  const pct = total > 0 ? Math.min(100, (remaining / total) * 100) : 0;
  return (
    <Card className="group flex h-full flex-col gap-3 p-5 transition-all hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between gap-2">
        <Link to={`/batches/${b.id}`} className="min-w-0">
          <h3 className="truncate text-base font-semibold text-foreground group-hover:text-primary">
            {b.batchNumber || b.id}
          </h3>
          <p className="truncate text-xs text-muted-foreground">{b.project?.name || b.projectName || "—"}</p>
        </Link>
        <StatusBadge status={b.status} />
      </div>
      <dl className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <dt className="text-xs text-muted-foreground">Vintage</dt>
          <dd className="font-medium text-foreground">{b.vintageYear || "—"}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">Standard</dt>
          <dd className="font-medium text-foreground">{b.verificationStandard || "—"}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">Total</dt>
          <dd className="font-medium text-foreground">{fmtNumber(total)}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">Remaining</dt>
          <dd className="font-medium text-foreground">{fmtNumber(remaining)}</dd>
        </div>
      </dl>
      <div className="mt-auto pt-2">
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${pct}%` }} />
        </div>
        <p className="mt-1.5 text-xs text-muted-foreground">{pct.toFixed(0)}% available</p>
      </div>
    </Card>
  );
}