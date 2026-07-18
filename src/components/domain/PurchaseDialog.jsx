import { useMemo, useState, useEffect } from "react";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { fmtCurrency, fmtNumber } from "@/lib/format.js";
import { useBuy } from "@/hooks/useMarketplace.js";
import { toast } from "sonner";

export default function PurchaseDialog({ listing, open, onOpenChange }) {
  const [qty, setQty] = useState(1);
  const buy = useBuy();
  useEffect(() => { if (open) setQty(1); }, [open]);
  const available = Number(listing?.availableCredits || 0);
  const price = Number(listing?.pricePerCredit || 0);
  const total = useMemo(() => Math.max(0, Number(qty) || 0) * price, [qty, price]);

  const submit = async () => {
    if (!listing) return;
    if (qty < 1 || qty > available) { toast.error("Invalid quantity"); return; }
    try {
      await buy.mutateAsync({ listing_id: listing.id, requested_credits: Number(qty) });
      toast.success("Purchase submitted");
      onOpenChange(false);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Purchase failed");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Purchase Credits</DialogTitle>
          <DialogDescription>
            {listing ? `${listing.project?.name || listing.projectName || "Batch"} · ${fmtCurrency(price)} / credit` : ""}
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>Quantity (max {fmtNumber(available)})</Label>
            <Input type="number" min={1} max={available} value={qty} onChange={(e) => setQty(e.target.value)} />
          </div>
          <div className="rounded-lg border border-border bg-muted/40 p-3 text-sm">
            <div className="flex items-center justify-between">
              <span className="text-muted-foreground">Estimated cost</span>
              <span className="font-semibold text-primary">{fmtCurrency(total)}</span>
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={submit} disabled={buy.isPending}>Submit Purchase</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}