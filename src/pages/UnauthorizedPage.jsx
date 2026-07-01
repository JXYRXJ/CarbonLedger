import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { ShieldAlert } from "lucide-react";

export default function UnauthorizedPage() {
  return (
    <div className="grid min-h-[70vh] place-items-center px-6">
      <div className="max-w-md text-center">
        <span className="mx-auto mb-4 grid h-12 w-12 place-items-center rounded-full bg-destructive/10 text-destructive">
          <ShieldAlert className="h-5 w-5" />
        </span>
        <h1 className="text-2xl font-semibold tracking-tight">Unauthorized</h1>
        <p className="mt-2 text-sm text-muted-foreground">You don't have access to this page. Contact your administrator if you believe this is a mistake.</p>
        <Button asChild className="mt-6"><Link to="/dashboard">Back to dashboard</Link></Button>
      </div>
    </div>
  );
}