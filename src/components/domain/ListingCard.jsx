import { Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { fmtCurrency, fmtNumber } from "@/lib/format.js";
import { MapPin } from "lucide-react";

export default function ListingCard({ listing, onPurchase }) {
  const l = listing || {};
  return (
    <Card className="flex h-full flex-col gap-4 p-5 transition-all hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between gap-2">
        <div className="min-w-0">
          <p className="text-xs uppercase tracking-wide text-muted-foreground">{l.batch?.batchNumber || l.batchNumber || "Batch"}</p>
          <h3 className="mt-0.5 truncate text-base font-semibold text-foreground">{l.project?.name || l.projectName || "—"}</h3>
        </div>
        {l.verificationStandard && (
          <Badge variant="secondary" className="bg-primary/10 text-primary">{l.verificationStandard}</Badge>
        )}
      </div>
      <dl className="grid grid-cols-2 gap-3 text-sm">
        <div>
          <dt className="text-xs text-muted-foreground">Seller</dt>
          <dd className="truncate font-medium text-foreground">{l.seller?.companyName || l.sellerName || "—"}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">Country</dt>
          <dd className="flex items-center gap-1 truncate font-medium text-foreground">
            <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
            {l.country || l.project?.country || "—"}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">Available</dt>
          <dd className="font-medium text-foreground">{fmtNumber(l.availableCredits)}</dd>
        </div>
        <div>
          <dt className="text-xs text-muted-foreground">Price / credit</dt>
          <dd className="font-semibold text-primary">{fmtCurrency(l.pricePerCredit)}</dd>
        </div>
      </dl>
      <div className="mt-auto flex gap-2 pt-2">
        <Button asChild variant="outline" className="flex-1">
          <Link to={`/batches/${l.batch?.id || l.batchId}`}>Details</Link>
        </Button>
        <Button className="flex-1" onClick={() => onPurchase?.(l)}>Purchase</Button>
      </div>
    </Card>
  );
}