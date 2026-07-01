import { AlertTriangle } from "lucide-react";
import { Button } from "@/components/ui/button";

export default function ErrorState({ title = "Something went wrong", description, onRetry }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-border bg-card p-12 text-center">
      <span className="mb-4 grid h-12 w-12 place-items-center rounded-full bg-destructive/10 text-destructive">
        <AlertTriangle className="h-5 w-5" />
      </span>
      <h3 className="text-base font-semibold text-foreground">{title}</h3>
      {description && <p className="mt-1 max-w-sm text-sm text-muted-foreground">{description}</p>}
      {onRetry && (
        <Button onClick={onRetry} variant="outline" className="mt-4">Try again</Button>
      )}
    </div>
  );
}
