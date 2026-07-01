import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { listingApi } from "@/services/listingApi.js";
import { usePortfolio } from "@/hooks/usePortfolio.js";
import PageHeader from "@/components/common/PageHeader.jsx";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { toast } from "sonner";

const schema = z.object({
  ownershipId: z.string().min(1, "Select a holding"),
  creditsToSell: z.coerce.number().int().positive("Must be positive"),
  pricePerCredit: z.coerce.number().positive("Must be positive"),
  description: z.string().max(1000).optional().or(z.literal("")),
});

export default function CreateListingPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const portfolioQ = usePortfolio();
  const items = Array.isArray(portfolioQ.data) ? portfolioQ.data : portfolioQ.data?.items || [];

  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: { ownershipId: "", creditsToSell: 1, pricePerCredit: 1, description: "" },
  });

  const create = useMutation({
    mutationFn: listingApi.create,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["marketplace"] });
      qc.invalidateQueries({ queryKey: ["portfolio"] });
      toast.success("Listing created");
      navigate("/marketplace");
    },
    onError: (e) => toast.error(e?.response?.data?.detail || "Failed to create listing"),
  });

  const onSubmit = (values) => create.mutate(values);

  return (
    <div className="space-y-6">
      <PageHeader title="Create Listing" description="List a portion of your holdings for sale." />
      <Card className="max-w-2xl p-6">
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-5">
          <div className="space-y-1.5">
            <Label>Holding</Label>
            <Select value={form.watch("ownershipId")} onValueChange={(v) => form.setValue("ownershipId", v, { shouldValidate: true })}>
              <SelectTrigger><SelectValue placeholder="Select a holding" /></SelectTrigger>
              <SelectContent>
                {items.map((h) => (
                  <SelectItem key={h.id || h.batch?.id} value={String(h.id || h.batch?.id)}>
                    {(h.batch?.batchNumber || h.batchNumber) + " · " + (h.availableCredits ?? 0) + " available"}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            {form.formState.errors.ownershipId && <p className="text-xs text-destructive">{form.formState.errors.ownershipId.message}</p>}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-1.5">
              <Label>Credits to sell</Label>
              <Input type="number" min={1} {...form.register("creditsToSell")} />
              {form.formState.errors.creditsToSell && <p className="text-xs text-destructive">{form.formState.errors.creditsToSell.message}</p>}
            </div>
            <div className="space-y-1.5">
              <Label>Price per credit (USD)</Label>
              <Input type="number" step="0.01" min={0.01} {...form.register("pricePerCredit")} />
              {form.formState.errors.pricePerCredit && <p className="text-xs text-destructive">{form.formState.errors.pricePerCredit.message}</p>}
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>Description (optional)</Label>
            <Textarea rows={4} {...form.register("description")} placeholder="Add context for buyers..." />
          </div>
          <div className="flex justify-end gap-2 pt-2">
            <Button type="button" variant="outline" onClick={() => navigate(-1)}>Cancel</Button>
            <Button type="submit" disabled={create.isPending}>Submit Listing</Button>
          </div>
        </form>
      </Card>
    </div>
  );
}