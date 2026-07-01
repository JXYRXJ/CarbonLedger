import { useState } from "react";
import { Link } from "react-router-dom";
import PageHeader from "@/components/common/PageHeader.jsx";
import MetricCard from "@/components/common/MetricCard.jsx";
import QueryState from "@/components/common/QueryState.jsx";
import EmptyState from "@/components/common/EmptyState.jsx";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { usePortfolio, usePortfolioSummary } from "@/hooks/usePortfolio.js";
import { Wallet, Layers, ShoppingBag, Recycle, CheckSquare, Plus } from "lucide-react";
import RetireDialog from "@/components/domain/RetireDialog.jsx";
import { fmtCurrency, fmtNumber } from "@/lib/format.js";

export default function PortfolioPage() {
  const summaryQ = usePortfolioSummary();
  const portfolioQ = usePortfolio();
  const [retireFor, setRetireFor] = useState(null);

  const s = summaryQ.data || {};
  const metrics = [
    { label: "Portfolio Value", value: fmtCurrency(s.portfolioValue), icon: Wallet, loading: summaryQ.isLoading },
    { label: "Owned Credits", value: fmtNumber(s.ownedCredits), icon: Layers, loading: summaryQ.isLoading },
    { label: "Available", value: fmtNumber(s.availableCredits), icon: CheckSquare, loading: summaryQ.isLoading },
    { label: "Listed", value: fmtNumber(s.listedCredits), icon: ShoppingBag, loading: summaryQ.isLoading },
    { label: "Retired", value: fmtNumber(s.retiredCredits), icon: Recycle, loading: summaryQ.isLoading },
  ];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Portfolio"
        description="Your holdings, listings, and retirements."
        actions={<Button asChild><Link to="/listings/create"><Plus className="h-4 w-4" /> Create Listing</Link></Button>}
      />
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
        {metrics.map((m) => <MetricCard key={m.label} {...m} />)}
      </section>
      <QueryState
        query={portfolioQ}
        isEmpty={(d) => !(Array.isArray(d) ? d.length : d?.items?.length)}
        empty={<EmptyState icon={Layers} title="No holdings yet" description="Purchase credits from the marketplace to build your portfolio." action={<Button asChild><Link to="/marketplace">Browse marketplace</Link></Button>} />}
      >
        {(d) => {
          const rows = Array.isArray(d) ? d : d.items || [];
          return (
            <Card className="overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Batch</TableHead>
                    <TableHead>Project</TableHead>
                    <TableHead className="text-right">Owned</TableHead>
                    <TableHead className="text-right">Available</TableHead>
                    <TableHead className="text-right">Current Value</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((h) => (
                    <TableRow key={h.id || h.batch?.id}>
                      <TableCell className="font-medium">{h.batch?.batchNumber || h.batchNumber || "—"}</TableCell>
                      <TableCell className="truncate max-w-[18rem]">{h.batch?.project?.name || h.projectName || "—"}</TableCell>
                      <TableCell className="text-right">{fmtNumber(h.ownedCredits)}</TableCell>
                      <TableCell className="text-right">{fmtNumber(h.availableCredits)}</TableCell>
                      <TableCell className="text-right font-semibold text-primary">{fmtCurrency(h.currentValue)}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex justify-end gap-1">
                          <Button asChild variant="ghost" size="sm"><Link to={`/batches/${h.batch?.id || h.batchId}`}>View</Link></Button>
                          <Button asChild variant="ghost" size="sm"><Link to={`/listings/create?holding=${h.id || h.batch?.id}`}>List</Link></Button>
                          <Button variant="ghost" size="sm" onClick={() => setRetireFor(h)}>Retire</Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </Card>
          );
        }}
      </QueryState>
      <RetireDialog holding={retireFor} open={!!retireFor} onOpenChange={(o) => !o && setRetireFor(null)} />
    </div>
  );
}