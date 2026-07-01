import { Link } from "react-router-dom";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { MapPin, Leaf } from "lucide-react";

export default function ProjectCard({ project }) {
  const p = project || {};
  return (
    <Card className="group flex h-full flex-col gap-3 p-5 transition-all hover:-translate-y-0.5 hover:shadow-md">
      <div className="flex items-start justify-between gap-3">
        <Link to={`/projects/${p.id}`} className="min-w-0">
          <h3 className="truncate text-base font-semibold text-foreground group-hover:text-primary">{p.name || "Untitled"}</h3>
          <p className="mt-0.5 text-xs text-muted-foreground">{p.registry?.name || p.registryName || "—"}</p>
        </Link>
        {p.verificationStandard && (
          <Badge variant="secondary" className="bg-primary/10 text-primary">{p.verificationStandard}</Badge>
        )}
      </div>
      <p className="line-clamp-2 text-sm text-muted-foreground">{p.description || "No description provided."}</p>
      <div className="mt-auto flex items-center justify-between pt-2 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1"><MapPin className="h-3.5 w-3.5" /> {p.country || "—"}</span>
        <span className="inline-flex items-center gap-1"><Leaf className="h-3.5 w-3.5" /> {p.projectType || "—"}</span>
      </div>
    </Card>
  );
}