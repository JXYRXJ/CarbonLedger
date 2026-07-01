import { Link } from "react-router-dom";
import { Leaf } from "lucide-react";

export default function Logo({ to = "/", className = "" }) {
  return (
    <Link to={to} className={`group inline-flex items-center gap-2 ${className}`}>
      <span className="grid h-8 w-8 place-items-center rounded-lg bg-gradient-to-br from-primary to-secondary text-primary-foreground shadow-sm transition-transform group-hover:scale-105">
        <Leaf className="h-4 w-4" />
      </span>
      <span className="text-base font-semibold tracking-tight text-foreground">
        CarbonLedger
      </span>
    </Link>
  );
}
