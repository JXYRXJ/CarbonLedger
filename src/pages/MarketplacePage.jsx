import { useState } from "react";
import PageHeader from "@/components/common/PageHeader.jsx";
import SearchBar from "@/components/common/SearchBar.jsx";
import FilterPanel from "@/components/common/FilterPanel.jsx";
import QueryState from "@/components/common/QueryState.jsx";
import EmptyState from "@/components/common/EmptyState.jsx";
import ListingCard from "@/components/domain/ListingCard.jsx";
import PurchaseDialog from "@/components/domain/PurchaseDialog.jsx";
import Pagination from "@/components/common/Pagination.jsx";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { useMarketplace } from "@/hooks/useMarketplace.js";
import { ShoppingBag } from "lucide-react";

const SORTS = [
  { v: "newest", l: "Newest" },
  { v: "price_asc", l: "Price: Low to High" },
  { v: "price_desc", l: "Price: High to Low" },
  { v: "credits_desc", l: "Most Available" },
];

export default function MarketplacePage() {
  const [filters, setFilters] = useState({
    search: "", registry: "", country: "", projectType: "", vintageYear: "",
    minPrice: "", maxPrice: "", minCredits: "", sort: "newest",
  });
  const [page, setPage] = useState(1);
  const [active, setActive] = useState(null);
  const pageSize = 12;

  const query = useMarketplace({ ...filters, page, pageSize });
  const items = Array.isArray(query.data) ? query.data : query.data?.items || [];
  const total = query.data?.total ?? items.length;

  const set = (k) => (v) => { setFilters((p) => ({ ...p, [k]: v })); setPage(1); };
  const reset = () => { setFilters({ search: "", registry: "", country: "", projectType: "", vintageYear: "", minPrice: "", maxPrice: "", minCredits: "", sort: "newest" }); setPage(1); };

  return (
    <div className="space-y-6">
      <PageHeader title="Marketplace" description="Discover and purchase verified carbon credits." />

      <div className="grid gap-6 lg:grid-cols-[280px_minmax(0,1fr)]">
        <FilterPanel actions={<Button variant="ghost" size="sm" onClick={reset}>Reset</Button>}>
          <div className="space-y-1.5"><Label>Registry</Label><Input value={filters.registry} onChange={(e) => set("registry")(e.target.value)} placeholder="e.g. Verra" /></div>
          <div className="space-y-1.5"><Label>Country</Label><Input value={filters.country} onChange={(e) => set("country")(e.target.value)} placeholder="e.g. Brazil" /></div>
          <div className="space-y-1.5"><Label>Project Type</Label><Input value={filters.projectType} onChange={(e) => set("projectType")(e.target.value)} placeholder="e.g. Reforestation" /></div>
          <div className="space-y-1.5"><Label>Vintage Year</Label><Input type="number" value={filters.vintageYear} onChange={(e) => set("vintageYear")(e.target.value)} placeholder="2024" /></div>
          <div className="grid grid-cols-2 gap-2">
            <div className="space-y-1.5"><Label>Min $</Label><Input type="number" value={filters.minPrice} onChange={(e) => set("minPrice")(e.target.value)} /></div>
            <div className="space-y-1.5"><Label>Max $</Label><Input type="number" value={filters.maxPrice} onChange={(e) => set("maxPrice")(e.target.value)} /></div>
          </div>
          <div className="space-y-1.5"><Label>Min Credits</Label><Input type="number" value={filters.minCredits} onChange={(e) => set("minCredits")(e.target.value)} /></div>
        </FilterPanel>

        <div className="space-y-4">
          <div className="flex flex-wrap items-center gap-3">
            <SearchBar value={filters.search} onChange={set("search")} placeholder="Search listings..." className="flex-1 min-w-[240px]" />
            <Select value={filters.sort} onValueChange={set("sort")}>
              <SelectTrigger className="w-[200px]"><SelectValue /></SelectTrigger>
              <SelectContent>
                {SORTS.map((o) => <SelectItem key={o.v} value={o.v}>{o.l}</SelectItem>)}
              </SelectContent>
            </Select>
          </div>
          <QueryState query={query} isEmpty={() => items.length === 0}
            empty={<EmptyState icon={ShoppingBag} title="No listings found" description="Adjust your filters to see more results." />}
          >
            {() => (
              <>
                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                  {items.map((l) => <ListingCard key={l.id} listing={l} onPurchase={setActive} />)}
                </div>
                <Pagination page={page} pageSize={pageSize} total={total} onPageChange={setPage} />
              </>
            )}
          </QueryState>
        </div>
      </div>

      <PurchaseDialog listing={active} open={!!active} onOpenChange={(o) => !o && setActive(null)} />
    </div>
  );
}