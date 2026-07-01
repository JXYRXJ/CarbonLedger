import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import StatusBadge from "@/components/common/StatusBadge.jsx";
import { fmtCurrency, fmtDateTime, fmtNumber, truncate } from "@/lib/format.js";
import { Card } from "@/components/ui/card";
import { ExternalLink } from "lucide-react";

export default function TransactionTable({ rows = [] }) {
  return (
    <Card className="overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Transaction</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Buyer</TableHead>
            <TableHead>Seller</TableHead>
            <TableHead>Batch</TableHead>
            <TableHead className="text-right">Quantity</TableHead>
            <TableHead className="text-right">Price</TableHead>
            <TableHead className="text-right">Total</TableHead>
            <TableHead>Chain</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((t) => (
            <TableRow key={t.id}>
              <TableCell className="font-mono text-xs">{truncate(t.id, 6)}</TableCell>
              <TableCell>{fmtDateTime(t.createdAt || t.date)}</TableCell>
              <TableCell className="truncate max-w-[10rem]">{t.buyer?.companyName || t.buyerName || "—"}</TableCell>
              <TableCell className="truncate max-w-[10rem]">{t.seller?.companyName || t.sellerName || "—"}</TableCell>
              <TableCell className="truncate max-w-[8rem]">{t.batch?.batchNumber || t.batchNumber || "—"}</TableCell>
              <TableCell className="text-right">{fmtNumber(t.quantity)}</TableCell>
              <TableCell className="text-right">{fmtCurrency(t.pricePerCredit)}</TableCell>
              <TableCell className="text-right font-medium">{fmtCurrency(t.total ?? (t.pricePerCredit * t.quantity))}</TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <StatusBadge status={t.blockchainStatus || (t.transactionHash ? "confirmed" : "unconfirmed")} />
                  {t.transactionHash && (
                    <a href={`#${t.transactionHash}`} className="inline-flex items-center gap-1 font-mono text-[11px] text-primary hover:underline">
                      {truncate(t.transactionHash, 6)} <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
}