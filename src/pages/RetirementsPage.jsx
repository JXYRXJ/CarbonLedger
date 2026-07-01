import PageHeader from "@/components/common/PageHeader.jsx";
import MetricCard from "@/components/common/MetricCard.jsx";
import QueryState from "@/components/common/QueryState.jsx";
import EmptyState from "@/components/common/EmptyState.jsx";
import RetirementTable from "@/components/domain/RetirementTable.jsx";
import { useRetirements, useRetirementStats } from "@/hooks/useRetirements.js";
import { Recycle, Award, DollarSign } from "lucide-react";
import { fmtCurrency, fmtNumber } from "@/lib/format.js";

export default function RetirementsPage() {
  const statsQ = useRetirementStats();
  const listQ = useRetirements();
  const s = statsQ.data || {};
  return (
    <div className="space-y-6">
      <PageHeader title="Retirements" description="Permanent retirements anchored on-chain." />
      <section className="grid gap-4 sm:grid-cols-3">
        <MetricCard label="Total Retired" value={fmtNumber(s.totalRetired)} icon={Recycle} loading={statsQ.isLoading} hint="tCO₂e" />
        <MetricCard label="Retired Value" value={fmtCurrency(s.retiredValue)} icon={DollarSign} loading={statsQ.isLoading} />
        <MetricCard label="Certificates" value={fmtNumber(s.certificates)} icon={Award} loading={statsQ.isLoading} />
      </section>
      <QueryState query={listQ} isEmpty={(d) => !(Array.isArray(d) ? d.length : d?.items?.length)}
        empty={<EmptyState icon={Recycle} title="No retirements" description="Retire credits from your portfolio to generate certificates." />}
      >
        {(d) => <RetirementTable rows={Array.isArray(d) ? d : d.items || []} />}
      </QueryState>
    </div>
  );
}