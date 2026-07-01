import { useState } from "react";
import PageHeader from "@/components/common/PageHeader.jsx";
import SearchBar from "@/components/common/SearchBar.jsx";
import QueryState from "@/components/common/QueryState.jsx";
import EmptyState from "@/components/common/EmptyState.jsx";
import BatchCard from "@/components/domain/BatchCard.jsx";
import Pagination from "@/components/common/Pagination.jsx";
import { useBatches } from "@/hooks/useBatches.js";
import { Layers } from "lucide-react";

export default function BatchesPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 12;
  const query = useBatches({ search, page, pageSize });
  const items = Array.isArray(query.data) ? query.data : query.data?.items || [];
  const total = query.data?.total ?? items.length;
  return (
    <div className="space-y-6">
      <PageHeader title="Credit Batches" description="All credit batches issued across registries." />
      <div className="max-w-md">
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search batches..." />
      </div>
      <QueryState query={query} isEmpty={() => items.length === 0}
        empty={<EmptyState icon={Layers} title="No batches" description="There are no credit batches to display yet." />}
      >
        {() => (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((b) => <BatchCard key={b.id} batch={b} />)}
            </div>
            <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
          </>
        )}
      </QueryState>
    </div>
  );
}