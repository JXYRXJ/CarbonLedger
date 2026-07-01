import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Filter } from "lucide-react";

export default function FilterPanel({ title = "Filters", children, actions }) {
  return (
    <Card className="p-5">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Filter className="h-4 w-4 text-muted-foreground" />
          <Label className="text-sm font-semibold">{title}</Label>
        </div>
        {actions}
      </div>
      <div className="space-y-4">{children}</div>
    </Card>
  );
}