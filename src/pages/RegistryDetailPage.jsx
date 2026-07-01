import { useParams, Link } from "react-router-dom";
import PageHeader from "@/components/common/PageHeader.jsx";
import QueryState from "@/components/common/QueryState.jsx";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useRegistry } from "@/hooks/useRegistries.js";
import ProjectCard from "@/components/domain/ProjectCard.jsx";
import { Globe, MapPin, ShieldCheck, ExternalLink } from "lucide-react";
import { fmtNumber } from "@/lib/format.js";

export default function RegistryDetailPage() {
  const { id } = useParams();
  const query = useRegistry(id);
  return (
    <div className="space-y-6">
      <QueryState query={query} isEmpty={(d) => !d}>
        {(r) => (
          <>
            <PageHeader
              title={r.name}
              description={r.description}
              actions={
                r.website && (
                  <Button asChild variant="outline"><a href={r.website} target="_blank" rel="noreferrer">Website <ExternalLink className="h-4 w-4" /></a></Button>
                )
              }
            />
            <div className="grid gap-4 sm:grid-cols-3">
              <Card className="p-5">
                <div className="flex items-center gap-2 text-xs text-muted-foreground"><MapPin className="h-4 w-4" /> Country</div>
                <p className="mt-2 text-base font-semibold">{r.country || "—"}</p>
              </Card>
              <Card className="p-5">
                <div className="flex items-center gap-2 text-xs text-muted-foreground"><ShieldCheck className="h-4 w-4" /> Accreditation</div>
                <p className="mt-2 text-base font-semibold">{r.accreditation || "—"}</p>
              </Card>
              <Card className="p-5">
                <div className="flex items-center gap-2 text-xs text-muted-foreground"><Globe className="h-4 w-4" /> Projects</div>
                <p className="mt-2 text-base font-semibold">{fmtNumber(r.projectsCount ?? r.projects?.length)}</p>
              </Card>
            </div>
            {r.stats && (
              <Card className="p-5">
                <h3 className="text-sm font-semibold">Statistics</h3>
                <div className="mt-3 grid gap-4 sm:grid-cols-3">
                  {Object.entries(r.stats).map(([k, v]) => (
                    <div key={k}>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">{k}</p>
                      <p className="mt-0.5 text-base font-semibold">{typeof v === "number" ? fmtNumber(v) : String(v)}</p>
                    </div>
                  ))}
                </div>
              </Card>
            )}
            {Array.isArray(r.projects) && r.projects.length > 0 && (
              <div>
                <div className="mb-3 flex items-center justify-between">
                  <h3 className="text-base font-semibold">Associated projects</h3>
                  <Button asChild variant="link"><Link to="/projects">View all</Link></Button>
                </div>
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                  {r.projects.map((p) => <ProjectCard key={p.id} project={p} />)}
                </div>
              </div>
            )}
          </>
        )}
      </QueryState>
    </div>
  );
}