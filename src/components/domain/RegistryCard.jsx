import { Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Globe, ExternalLink } from "lucide-react";

export default function RegistryCard({ registry }) {
  const r = registry || {};
  return (
    <Card className="group flex h-full flex-col gap-3 p-5 transition-all hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <Link to={`/registries/${r.id}`} className="block">
            <h3 className="truncate text-base font-semibold text-foreground group-hover:text-primary">{r.name || "Unnamed"}</h3>
          </Link>
          <p className="mt-0.5 text-xs text-muted-foreground">{r.country || "—"}</p>
        </div>
        {r.accreditation && <Badge variant="secondary" className="bg-primary/10 text-primary">{r.accreditation}</Badge>}
      </div>
      <p className="line-clamp-2 text-sm text-muted-foreground">{r.description || "No description provided."}</p>
      <div className="mt-auto flex items-center justify-between pt-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1">
          <Globe className="h-3.5 w-3.5" /> {r.projectsCount ?? 0} projects
        </span>
        {r.website && (
          <a href={r.website} target="_blank" rel="noreferrer" className="inline-flex items-center gap-1 text-primary hover:underline">
            Website <ExternalLink className="h-3 w-3" />
          </a>
        )}
      </div>
    </Card>
  );
}