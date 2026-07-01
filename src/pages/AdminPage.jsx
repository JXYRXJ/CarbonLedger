import PageHeader from "@/components/common/PageHeader.jsx";
import MetricCard from "@/components/common/MetricCard.jsx";
import QueryState from "@/components/common/QueryState.jsx";
import EmptyState from "@/components/common/EmptyState.jsx";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import StatusBadge from "@/components/common/StatusBadge.jsx";
import TransactionTable from "@/components/domain/TransactionTable.jsx";
import {
  useAdminOverview, useAdminUsers, useAdminRegistries, useAdminProjects,
  useAdminListings, useAdminTransactions, useAdminApprovals,
} from "@/hooks/useAdmin.js";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { adminApi } from "@/services/adminApi.js";
import { fmtCurrency, fmtDateTime, fmtNumber } from "@/lib/format.js";
import { Building2, Users, ShoppingBag, ListChecks, Recycle, ArrowLeftRight, BarChart3, ShieldCheck } from "lucide-react";
import { toast } from "sonner";

function asRows(d) { return Array.isArray(d) ? d : d?.items || []; }

function SimpleTable({ query, columns, empty }) {
  return (
    <QueryState query={query} isEmpty={(d) => !asRows(d).length} empty={empty}>
      {(d) => (
        <Card className="overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow>{columns.map((c) => <TableHead key={c.key} className={c.className}>{c.label}</TableHead>)}</TableRow>
            </TableHeader>
            <TableBody>
              {asRows(d).map((row) => (
                <TableRow key={row.id}>
                  {columns.map((c) => <TableCell key={c.key} className={c.cellClassName}>{c.render ? c.render(row) : row[c.key] ?? "—"}</TableCell>)}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Card>
      )}
    </QueryState>
  );
}

function ApprovalsTab() {
  const qc = useQueryClient();
  const query = useAdminApprovals();
  const approve = useMutation({ mutationFn: adminApi.approve, onSuccess: () => { toast.success("Approved"); qc.invalidateQueries({ queryKey: ["admin-approvals"] }); }, onError: (e) => toast.error(e?.response?.data?.detail || "Failed") });
  const reject = useMutation({ mutationFn: adminApi.reject, onSuccess: () => { toast.success("Rejected"); qc.invalidateQueries({ queryKey: ["admin-approvals"] }); }, onError: (e) => toast.error(e?.response?.data?.detail || "Failed") });
  return (
    <QueryState query={query} isEmpty={(d) => !asRows(d).length}
      empty={<EmptyState icon={ShieldCheck} title="No pending approvals" description="You're all caught up." />}
    >
      {(d) => (
        <div className="space-y-3">
          {asRows(d).map((a) => (
            <Card key={a.id} className="flex items-start justify-between gap-4 p-5">
              <div>
                <p className="text-xs uppercase tracking-wide text-muted-foreground">{a.type}</p>
                <p className="mt-0.5 text-sm font-semibold">{a.title || a.subject || a.id}</p>
                {a.description && <p className="mt-1 text-sm text-muted-foreground">{a.description}</p>}
              </div>
              <div className="flex gap-2">
                <Button variant="outline" onClick={() => reject.mutate(a.id)} disabled={reject.isPending}>Reject</Button>
                <Button onClick={() => approve.mutate(a.id)} disabled={approve.isPending}>Approve</Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </QueryState>
  );
}

export default function AdminPage() {
  const overviewQ = useAdminOverview();
  const usersQ = useAdminUsers();
  const registriesQ = useAdminRegistries();
  const projectsQ = useAdminProjects();
  const listingsQ = useAdminListings();
  const txQ = useAdminTransactions();
  const o = overviewQ.data || {};

  return (
    <div className="space-y-6">
      <PageHeader title="Admin" description="Platform operations and oversight." />
      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        <MetricCard label="Pending Listings" value={fmtNumber(o.pendingListings)} icon={ListChecks} loading={overviewQ.isLoading} />
        <MetricCard label="Published Listings" value={fmtNumber(o.publishedListings)} icon={ShoppingBag} loading={overviewQ.isLoading} />
        <MetricCard label="Companies" value={fmtNumber(o.companies)} icon={Building2} loading={overviewQ.isLoading} />
        <MetricCard label="Marketplace Volume" value={fmtCurrency(o.marketplaceVolume)} icon={BarChart3} loading={overviewQ.isLoading} />
        <MetricCard label="Credits Traded" value={fmtNumber(o.creditsTraded)} icon={ArrowLeftRight} loading={overviewQ.isLoading} />
        <MetricCard label="Credits Retired" value={fmtNumber(o.creditsRetired)} icon={Recycle} loading={overviewQ.isLoading} />
      </section>
      <Tabs defaultValue="users">
        <TabsList className="flex-wrap">
          <TabsTrigger value="users">Users</TabsTrigger>
          <TabsTrigger value="registries">Registries</TabsTrigger>
          <TabsTrigger value="projects">Projects</TabsTrigger>
          <TabsTrigger value="listings">Listings</TabsTrigger>
          <TabsTrigger value="transactions">Transactions</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="approvals">Approvals</TabsTrigger>
        </TabsList>
        <TabsContent value="users">
          <SimpleTable
            query={usersQ}
            empty={<EmptyState icon={Users} title="No users" description="No users in the system yet." />}
            columns={[
              { key: "companyName", label: "Company", render: (r) => r.companyName || r.name || "—" },
              { key: "email", label: "Email" },
              { key: "role", label: "Role", render: (r) => <StatusBadge status={r.role === "ADMIN" ? "active" : "verified"}>{r.role || "—"}</StatusBadge> },
              { key: "createdAt", label: "Joined", render: (r) => fmtDateTime(r.createdAt) },
            ]}
          />
        </TabsContent>
        <TabsContent value="registries">
          <SimpleTable
            query={registriesQ}
            empty={<EmptyState icon={Building2} title="No registries" description="No registries onboarded yet." />}
            columns={[
              { key: "name", label: "Name" },
              { key: "country", label: "Country" },
              { key: "accreditation", label: "Accreditation" },
              { key: "projectsCount", label: "Projects", render: (r) => fmtNumber(r.projectsCount) },
            ]}
          />
        </TabsContent>
        <TabsContent value="projects">
          <SimpleTable
            query={projectsQ}
            empty={<EmptyState icon={Building2} title="No projects" description="No projects to display." />}
            columns={[
              { key: "name", label: "Name" },
              { key: "registry", label: "Registry", render: (r) => r.registry?.name || r.registryName || "—" },
              { key: "country", label: "Country" },
              { key: "verificationStandard", label: "Standard" },
            ]}
          />
        </TabsContent>
        <TabsContent value="listings">
          <SimpleTable
            query={listingsQ}
            empty={<EmptyState icon={ShoppingBag} title="No listings" description="No listings to display." />}
            columns={[
              { key: "id", label: "ID", render: (r) => <span className="font-mono text-xs">{r.id}</span> },
              { key: "batch", label: "Batch", render: (r) => r.batch?.batchNumber || r.batchNumber || "—" },
              { key: "seller", label: "Seller", render: (r) => r.seller?.companyName || r.sellerName || "—" },
              { key: "availableCredits", label: "Available", render: (r) => fmtNumber(r.availableCredits) },
              { key: "pricePerCredit", label: "Price", render: (r) => fmtCurrency(r.pricePerCredit) },
              { key: "status", label: "Status", render: (r) => <StatusBadge status={r.status} /> },
            ]}
          />
        </TabsContent>
        <TabsContent value="transactions">
          <QueryState query={txQ} isEmpty={(d) => !asRows(d).length}
            empty={<EmptyState icon={ArrowLeftRight} title="No transactions" description="No transactions yet." />}
          >
            {(d) => <TransactionTable rows={asRows(d)} />}
          </QueryState>
        </TabsContent>
        <TabsContent value="analytics">
          <Card className="p-6 text-sm text-muted-foreground">
            Visit the <a href="/analytics" className="text-primary hover:underline">Analytics</a> page for full platform metrics.
          </Card>
        </TabsContent>
        <TabsContent value="approvals"><ApprovalsTab /></TabsContent>
      </Tabs>
    </div>
  );
}