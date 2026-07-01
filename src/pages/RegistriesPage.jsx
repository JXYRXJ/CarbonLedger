import { useState } from "react";
import PageHeader from "@/components/common/PageHeader.jsx";
import SearchBar from "@/components/common/SearchBar.jsx";
import QueryState from "@/components/common/QueryState.jsx";
import EmptyState from "@/components/common/EmptyState.jsx";
import RegistryCard from "@/components/domain/RegistryCard.jsx";
import Pagination from "@/components/common/Pagination.jsx";
import { useRegistries } from "@/hooks/useRegistries.js";
import { Database } from "lucide-react";

export default function RegistriesPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 12;
  const query = useRegistries({ search, page, pageSize });

  const items = Array.isArray(query.data) ? query.data : query.data?.items || [];
  const total = query.data?.total ?? items.length;

  return (
    <div className="space-y-6">
      <PageHeader title="Registries" description="Accredited carbon credit registries." />
      <div className="max-w-md">
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search registries..." />
      </div>
      <QueryState
        query={query}
        isEmpty={() => items.length === 0}
        empty={<EmptyState icon={Database} title="No registries" description="Once registries are onboarded they will appear here." />}
      >
        {() => (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((r) => <RegistryCard key={r.id} registry={r} />)}
            </div>
            <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
          </>
        )}
      </QueryState>
    </div>
  );
}