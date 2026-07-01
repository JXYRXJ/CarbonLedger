import { useParams } from "react-router-dom";
import PageHeader from "@/components/common/PageHeader.jsx";
import QueryState from "@/components/common/QueryState.jsx";
import { Card } from "@/components/ui/card";
import { useProject } from "@/hooks/useProjects.js";
import DocumentViewer from "@/components/common/DocumentViewer.jsx";
import { MapPin, ShieldCheck, Calendar, Building2 } from "lucide-react";
import { fmtNumber } from "@/lib/format.js";

const Info = ({ icon: Icon, label, value }) => (
  <Card className="p-5">
    <div className="flex items-center gap-2 text-xs text-muted-foreground"><Icon className="h-4 w-4" /> {label}</div>
    <p className="mt-2 text-base font-semibold">{value ?? "—"}</p>
  </Card>
);

export default function ProjectDetailPage() {
  const { id } = useParams();
  const query = useProject(id);
  return (
    <div className="space-y-6">
      <QueryState query={query} isEmpty={(d) => !d}>
        {(p) => (
          <>
            <PageHeader title={p.name} description={p.projectType} />
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              <Info icon={Building2} label="Registry" value={p.registry?.name || p.registryName} />
              <Info icon={MapPin} label="Country" value={p.country} />
              <Info icon={ShieldCheck} label="Standard" value={p.verificationStandard} />
              <Info icon={Calendar} label="Vintage Years" value={Array.isArray(p.vintageYears) ? p.vintageYears.join(", ") : p.vintageYears} />
            </div>
            {p.description && (
              <Card className="p-6">
                <h3 className="text-sm font-semibold">About this project</h3>
                <p className="mt-2 whitespace-pre-line text-sm leading-relaxed text-muted-foreground">{p.description}</p>
              </Card>
            )}
            {p.stats && (
              <Card className="p-6">
                <h3 className="text-sm font-semibold">Statistics</h3>
                <div className="mt-3 grid gap-4 sm:grid-cols-3">
                  {Object.entries(p.stats).map(([k, v]) => (
                    <div key={k}>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">{k}</p>
                      <p className="mt-0.5 text-base font-semibold">{typeof v === "number" ? fmtNumber(v) : String(v)}</p>
                    </div>
                  ))}
                </div>
              </Card>
            )}
            <Card className="p-6">
              <h3 className="mb-3 text-sm font-semibold">Documents</h3>
              <DocumentViewer documents={p.documents || []} />
            </Card>
          </>
        )}
      </QueryState>
    </div>
  );
}