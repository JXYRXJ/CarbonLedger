import { useState } from "react";
import PageHeader from "@/components/common/PageHeader.jsx";
import SearchBar from "@/components/common/SearchBar.jsx";
import QueryState from "@/components/common/QueryState.jsx";
import EmptyState from "@/components/common/EmptyState.jsx";
import TransactionTable from "@/components/domain/TransactionTable.jsx";
import Pagination from "@/components/common/Pagination.jsx";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useTransactions } from "@/hooks/useTransactions.js";
import { ArrowLeftRight, Download } from "lucide-react";
import { toast } from "sonner";

const SORTS = [
  { v: "newest", l: "Newest" },
  { v: "oldest", l: "Oldest" },
  { v: "amount_desc", l: "Amount: High to Low" },
];

export default function TransactionsPage() {
  const [search, setSearch] = useState("");
  const [sort, setSort] = useState("newest");
  const [page, setPage] = useState(1);
  const pageSize = 20;
  const query = useTransactions({ search, sort, page, pageSize });
  const items = Array.isArray(query.data) ? query.data : query.data?.items || [];
  const total = query.data?.total ?? items.length;
  return (
    <div className="space-y-6">
      <PageHeader
        title="Transactions"
        description="Settled trades with blockchain audit trail."
        actions={<Button variant="outline" onClick={() => toast.info("Export coming soon")}><Download className="h-4 w-4" /> Export</Button>}
      />
      <div className="flex flex-wrap items-center gap-3">
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search transactions..." className="flex-1 min-w-[240px]" />
        <Select value={sort} onValueChange={(v) => { setSort(v); setPage(1); }}>
          <SelectTrigger className="w-[200px]"><SelectValue /></SelectTrigger>
          <SelectContent>{SORTS.map((o) => <SelectItem key={o.v} value={o.v}>{o.l}</SelectItem>)}</SelectContent>
        </Select>
      </div>
      <QueryState query={query} isEmpty={() => items.length === 0}
        empty={<EmptyState icon={ArrowLeftRight} title="No transactions" description="No settled trades yet." />}
      >
        {() => (
          <>
            <TransactionTable rows={items} />
            <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
          </>
        )}
      </QueryState>
    </div>
  );
}