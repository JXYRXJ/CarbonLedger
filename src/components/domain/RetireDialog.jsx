import { useEffect, useState } from "react";
import {
  Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { useRetire } from "@/hooks/useRetirements.js";
import { fmtNumber } from "@/lib/format.js";
import { toast } from "sonner";

export default function RetireDialog({ holding, open, onOpenChange }) {
  const [qty, setQty] = useState(1);
  const [reason, setReason] = useState("");
  const retire = useRetire();
  useEffect(() => { if (open) { setQty(1); setReason(""); } }, [open]);

  const available = Number(holding?.availableCredits || 0);

  const submit = async () => {
    if (!holding) return;
    if (qty < 1 || qty > available) { toast.error("Invalid quantity"); return; }
    if (!reason.trim()) { toast.error("Reason is required"); return; }
    try {
      await retire.mutateAsync({ batchId: holding.batch?.id || holding.batchId, quantity: Number(qty), reason: reason.trim() });
      toast.success("Retirement submitted");
      onOpenChange(false);
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Retirement failed");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Retire Credits</DialogTitle>
          <DialogDescription>
            Retiring permanently removes credits from circulation and anchors proof on-chain.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-1.5">
            <Label>Quantity (available {fmtNumber(available)})</Label>
            <Input type="number" min={1} max={available} value={qty} onChange={(e) => setQty(e.target.value)} />
          </div>
          <div className="space-y-1.5">
            <Label>Reason</Label>
            <Textarea rows={3} value={reason} onChange={(e) => setReason(e.target.value)} placeholder="e.g. Scope 1 emissions offset for FY2025" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>Cancel</Button>
          <Button onClick={submit} disabled={retire.isPending}>Confirm Retirement</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}