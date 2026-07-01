import { Card } from "@/components/ui/card";
import StatusBadge from "@/components/common/StatusBadge.jsx";
import { fmtCurrency, fmtDateTime, fmtNumber } from "@/lib/format.js";

export default function OrderCard({ order }) {
  const o = order || {};
  return (
    <Card className="p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">Order</p>
          <h3 className="mt-0.5 truncate font-mono text-sm text-foreground">{o.id || o.orderId}</h3>
        </div>
        <StatusBadge status={o.status} />
      </div>
      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div><dt className="text-xs text-muted-foreground">Quantity</dt><dd>{fmtNumber(o.quantity)}</dd></div>
        <div><dt className="text-xs text-muted-foreground">Total</dt><dd className="font-semibold text-primary">{fmtCurrency(o.total ?? o.pricePerCredit * o.quantity)}</dd></div>
        <div><dt className="text-xs text-muted-foreground">Created</dt><dd>{fmtDateTime(o.createdAt)}</dd></div>
        <div><dt className="text-xs text-muted-foreground">Buyer</dt><dd className="truncate">{o.buyer?.companyName || o.buyerName || "—"}</dd></div>
      </dl>
    </Card>
  );
}