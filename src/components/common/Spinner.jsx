import { Loader2 } from "lucide-react";
export default function Spinner({ className = "" }) {
  return <Loader2 className={`h-5 w-5 animate-spin text-muted-foreground ${className}`} />;
}
