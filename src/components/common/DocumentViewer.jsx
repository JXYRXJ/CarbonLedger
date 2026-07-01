import { FileText, ExternalLink, Download } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export default function DocumentViewer({ documents = [] }) {
  if (!documents.length) {
    return <p className="text-sm text-muted-foreground">No documents available.</p>;
  }
  return (
    <div className="grid gap-3 sm:grid-cols-2">
      {documents.map((d, i) => (
        <Card key={i} className="flex items-center justify-between gap-3 p-4">
          <div className="flex min-w-0 items-center gap-3">
            <span className="grid h-9 w-9 shrink-0 place-items-center rounded-lg bg-primary/10 text-primary">
              <FileText className="h-4 w-4" />
            </span>
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-foreground">{d.name || d.title}</p>
              <p className="text-xs text-muted-foreground">{d.type || d.size || "Document"}</p>
            </div>
          </div>
          <div className="flex gap-1">
            {d.url && (
              <Button asChild variant="ghost" size="icon" aria-label="Open">
                <a href={d.url} target="_blank" rel="noreferrer"><ExternalLink className="h-4 w-4" /></a>
              </Button>
            )}
            {d.downloadUrl && (
              <Button asChild variant="ghost" size="icon" aria-label="Download">
                <a href={d.downloadUrl}><Download className="h-4 w-4" /></a>
              </Button>
            )}
          </div>
        </Card>
      ))}
    </div>
  );
}