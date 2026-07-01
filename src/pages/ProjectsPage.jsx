import { useState } from "react";
import PageHeader from "@/components/common/PageHeader.jsx";
import SearchBar from "@/components/common/SearchBar.jsx";
import QueryState from "@/components/common/QueryState.jsx";
import EmptyState from "@/components/common/EmptyState.jsx";
import ProjectCard from "@/components/domain/ProjectCard.jsx";
import Pagination from "@/components/common/Pagination.jsx";
import { useProjects } from "@/hooks/useProjects.js";
import { Leaf } from "lucide-react";

export default function ProjectsPage() {
  const [search, setSearch] = useState("");
  const [page, setPage] = useState(1);
  const pageSize = 12;
  const query = useProjects({ search, page, pageSize });
  const items = Array.isArray(query.data) ? query.data : query.data?.items || [];
  const total = query.data?.total ?? items.length;
  return (
    <div className="space-y-6">
      <PageHeader title="Carbon Projects" description="Verified climate projects across the network." />
      <div className="max-w-md">
        <SearchBar value={search} onChange={(v) => { setSearch(v); setPage(1); }} placeholder="Search projects..." />
      </div>
      <QueryState
        query={query}
        isEmpty={() => items.length === 0}
        empty={<EmptyState icon={Leaf} title="No projects" description="No carbon projects match your filters." />}
      >
        {() => (
          <>
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {items.map((p) => <ProjectCard key={p.id} project={p} />)}
            </div>
            <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
          </>
        )}
      </QueryState>
    </div>
  );
}