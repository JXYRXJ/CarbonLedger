import { useParams } from "react-router-dom";
import { useState } from "react";
import PageHeader from "@/components/common/PageHeader.jsx";
import QueryState from "@/components/common/QueryState.jsx";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import {
  useBatch, useBatchOwnership, useBatchTransactions, useBatchRetirements,
} from "@/hooks/useBatches.js";
import StatusBadge from "@/components/common/StatusBadge.jsx";
import OwnershipCard from "@/components/domain/OwnershipCard.jsx";
import TransactionTable from "@/components/domain/TransactionTable.jsx";
import RetirementTable from "@/components/domain/RetirementTable.jsx";
import Timeline from "@/components/common/Timeline.jsx";
import DocumentViewer from "@/components/common/DocumentViewer.jsx";
import PurchaseDialog from "@/components/domain/PurchaseDialog.jsx";
import { fmtNumber } from "@/lib/format.js";

export default function BatchDetailPage() {
  const { id } = useParams();
  const batchQ = useBatch(id);
  const ownersQ = useBatchOwnership(id);
  const txQ = useBatchTransactions(id);
  const retQ = useBatchRetirements(id);
  const [open, setOpen] = useState(false);

  return (
    <div className="space-y-6">
      <QueryState query={batchQ} isEmpty={(d) => !d}>
        {(b) => (
          <>
            <PageHeader
              title={b.batchNumber || `Batch ${b.id}`}
              description={b.project?.name || b.projectName}
              actions={<>
                <StatusBadge status={b.status} />
                {b.listing && <Button onClick={() => setOpen(true)}>Purchase</Button>}
              </>}
            />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Card className="p-5"><p className="text-xs uppercase text-muted-foreground">Vintage</p><p className="mt-2 text-lg font-semibold">{b.vintageYear || "—"}</p></Card>
              <Card className="p-5"><p className="text-xs uppercase text-muted-foreground">Total</p><p className="mt-2 text-lg font-semibold">{fmtNumber(b.totalCredits)}</p></Card>
              <Card className="p-5"><p className="text-xs uppercase text-muted-foreground">Remaining</p><p className="mt-2 text-lg font-semibold">{fmtNumber(b.remainingCredits)}</p></Card>
              <Card className="p-5"><p className="text-xs uppercase text-muted-foreground">Standard</p><p className="mt-2 text-lg font-semibold">{b.verificationStandard || "—"}</p></Card>
            </div>

            <Tabs defaultValue="overview" className="w-full">
              <TabsList>
                <TabsTrigger value="overview">Overview</TabsTrigger>
                <TabsTrigger value="ownership">Ownership</TabsTrigger>
                <TabsTrigger value="transactions">Transactions</TabsTrigger>
                <TabsTrigger value="retirements">Retirements</TabsTrigger>
              </TabsList>
              <TabsContent value="overview" className="space-y-4">
                {b.description && (
                  <Card className="p-6">
                    <h3 className="text-sm font-semibold">About</h3>
                    <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-muted-foreground">{b.description}</p>
                  </Card>
                )}
                {Array.isArray(b.timeline) && b.timeline.length > 0 && (
                  <Card className="p-6">
                    <h3 className="mb-4 text-sm font-semibold">Timeline</h3>
                    <Timeline items={b.timeline} />
                  </Card>
                )}
                {Array.isArray(b.documents) && (
                  <Card className="p-6">
                    <h3 className="mb-3 text-sm font-semibold">Documents</h3>
                    <DocumentViewer documents={b.documents} />
                  </Card>
                )}
              </TabsContent>
              <TabsContent value="ownership">
                <QueryState query={ownersQ} isEmpty={(d) => !(Array.isArray(d) ? d.length : d?.items?.length)}>
                  {(d) => <OwnershipCard entries={Array.isArray(d) ? d : d.items || []} />}
                </QueryState>
              </TabsContent>
              <TabsContent value="transactions">
                <QueryState query={txQ} isEmpty={(d) => !(Array.isArray(d) ? d.length : d?.items?.length)}>
                  {(d) => <TransactionTable rows={Array.isArray(d) ? d : d.items || []} />}
                </QueryState>
              </TabsContent>
              <TabsContent value="retirements">
                <QueryState query={retQ} isEmpty={(d) => !(Array.isArray(d) ? d.length : d?.items?.length)}>
                  {(d) => <RetirementTable rows={Array.isArray(d) ? d : d.items || []} />}
                </QueryState>
              </TabsContent>
            </Tabs>

            <PurchaseDialog listing={b.listing} open={open} onOpenChange={setOpen} />
          </>
        )}
      </QueryState>
    </div>
  );
}