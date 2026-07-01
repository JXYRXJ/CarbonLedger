import { motion } from "framer-motion";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export default function MetricCard({ label, value, delta, icon: Icon, loading, hint }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35, ease: "easeOut" }}
    >
      <Card className="group relative overflow-hidden p-5 transition-all hover:-translate-y-0.5 hover:shadow-md">
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <p className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              {label}
            </p>
            {loading ? (
              <Skeleton className="h-8 w-32" />
            ) : (
              <p className="text-2xl font-semibold tracking-tight text-foreground">{value}</p>
            )}
            {hint && !loading && (
              <p className="text-xs text-muted-foreground">{hint}</p>
            )}
          </div>
          {Icon && (
            <span className="grid h-9 w-9 place-items-center rounded-lg bg-primary/10 text-primary">
              <Icon className="h-4 w-4" />
            </span>
          )}
        </div>
        {delta && !loading && (
          <p className={`mt-3 text-xs font-medium ${delta.positive ? "text-[color:var(--success)]" : "text-[color:var(--danger)]"}`}>
            {delta.positive ? "▲" : "▼"} {delta.value}
          </p>
        )}
      </Card>
    </motion.div>
  );
}
