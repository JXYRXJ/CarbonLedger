import { useState } from "react";
import PageHeader from "@/components/common/PageHeader.jsx";
import QueryState from "@/components/common/QueryState.jsx";
import EmptyState from "@/components/common/EmptyState.jsx";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Card } from "@/components/ui/card";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import StatusBadge from "@/components/common/StatusBadge.jsx";
import { useOrders } from "@/hooks/useOrders.js";
import { fmtCurrency, fmtDateTime, fmtNumber, truncate } from "@/lib/format.js";
import { ListOrdered } from "lucide-react";

function OrdersTable({ status }) {
  const query = useOrders(status ? { status } : undefined);
  return (
    <QueryState query={query} isEmpty={(d) => !(Array.isArray(d) ? d.length : d?.items?.length)}
      empty={<EmptyState icon={ListOrdered} title="No orders" description={`No ${status || ""} orders to display.`} />}
    >
      {(d) => {
        const rows = Array.isArray(d) ? d : d.items || [];
        return (
          <Card className="overflow-hidden">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Order ID</TableHead>
                  <TableHead>Listing</TableHead>
                  <TableHead>Buyer</TableHead>
                  <TableHead className="text-right">Quantity</TableHead>
                  <TableHead className="text-right">Price</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Created</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((o) => (
                  <TableRow key={o.id}>
                    <TableCell className="font-mono text-xs">{truncate(o.id, 6)}</TableCell>
                    <TableCell className="truncate max-w-[14rem]">{o.listing?.batchNumber || o.listingId || "—"}</TableCell>
                    <TableCell className="truncate max-w-[12rem]">{o.buyer?.companyName || o.buyerName || "—"}</TableCell>
                    <TableCell className="text-right">{fmtNumber(o.quantity)}</TableCell>
                    <TableCell className="text-right">{fmtCurrency(o.total ?? o.pricePerCredit * o.quantity)}</TableCell>
                    <TableCell><StatusBadge status={o.status} /></TableCell>
                    <TableCell>{fmtDateTime(o.createdAt)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        );
      }}
    </QueryState>
  );
}

export default function OrdersPage() {
  const [tab, setTab] = useState("all");
  return (
    <div className="space-y-6">
      <PageHeader title="Purchase Orders" description="Track the lifecycle of your marketplace orders." />
      <Tabs value={tab} onValueChange={setTab}>
        <TabsList>
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="pending">Pending</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
          <TabsTrigger value="cancelled">Cancelled</TabsTrigger>
          <TabsTrigger value="failed">Failed</TabsTrigger>
        </TabsList>
        <TabsContent value="all"><OrdersTable /></TabsContent>
        <TabsContent value="pending"><OrdersTable status="pending" /></TabsContent>
        <TabsContent value="completed"><OrdersTable status="completed" /></TabsContent>
        <TabsContent value="cancelled"><OrdersTable status="cancelled" /></TabsContent>
        <TabsContent value="failed"><OrdersTable status="failed" /></TabsContent>
      </Tabs>
    </div>
  );
}