import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { Card } from "@/components/ui/card";
import { fmtDateTime, fmtNumber, truncate } from "@/lib/format.js";
import { ExternalLink } from "lucide-react";

export default function RetirementTable({ rows = [] }) {
  return (
    <Card className="overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Batch</TableHead>
            <TableHead className="text-right">Quantity</TableHead>
            <TableHead>Date</TableHead>
            <TableHead>Reason</TableHead>
            <TableHead>Blockchain</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {rows.map((r) => (
            <TableRow key={r.id}>
              <TableCell>{r.batch?.batchNumber || r.batchNumber || "—"}</TableCell>
              <TableCell className="text-right">{fmtNumber(r.quantity)}</TableCell>
              <TableCell>{fmtDateTime(r.createdAt || r.date)}</TableCell>
              <TableCell className="max-w-[18rem] truncate">{r.reason || "—"}</TableCell>
              <TableCell>
                {r.transactionHash ? (
                  <a href={`#${r.transactionHash}`} className="inline-flex items-center gap-1 font-mono text-[11px] text-primary hover:underline">
                    {truncate(r.transactionHash, 6)} <ExternalLink className="h-3 w-3" />
                  </a>
                ) : "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </Card>
  );
}