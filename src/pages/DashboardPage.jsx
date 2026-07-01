import { motion } from "framer-motion";
import {
  Wallet, Layers, Recycle, ShoppingBag, ShieldCheck, Activity,
} from "lucide-react";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import PageHeader from "@/components/common/PageHeader.jsx";
import MetricCard from "@/components/common/MetricCard.jsx";
import { useAuth } from "@/contexts/AuthContext.jsx";

export default function DashboardPage() {
  const { user } = useAuth();
  const greeting = user?.companyName ? `Welcome, ${user.companyName}` : "Welcome";

  const metrics = [
    { label: "Portfolio Value", value: "—", icon: Wallet, hint: "USD equivalent" },
    { label: "Credits Owned", value: "—", icon: Layers, hint: "tCO₂e" },
    { label: "Credits Retired", value: "—", icon: Recycle, hint: "Year to date" },
    { label: "Marketplace Activity", value: "—", icon: ShoppingBag, hint: "Last 30 days" },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title={greeting}
        description="Your carbon portfolio at a glance."
        actions={<Badge variant="secondary" className="bg-primary/10 text-primary">Live</Badge>}
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((m) => <MetricCard key={m.label} {...m} loading />)}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="lg:col-span-2">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-foreground">Portfolio performance</h3>
                <p className="text-xs text-muted-foreground">Connect your data source to start tracking.</p>
              </div>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="mt-6 space-y-3">
              <Skeleton className="h-48 w-full rounded-lg" />
              <div className="grid grid-cols-3 gap-3">
                <Skeleton className="h-14 rounded-lg" />
                <Skeleton className="h-14 rounded-lg" />
                <Skeleton className="h-14 rounded-lg" />
              </div>
            </div>
          </Card>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.45 }}>
          <Card className="h-full p-6">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-semibold text-foreground">Compliance status</h3>
              <ShieldCheck className="h-4 w-4 text-[color:var(--success)]" />
            </div>
            <div className="mt-4 space-y-3">
              {["SOC 2 Type II", "ISO 27001", "GDPR", "On-chain anchoring"].map((c) => (
                <div key={c} className="flex items-center justify-between rounded-lg border border-border bg-card/60 px-3 py-2.5">
                  <span className="text-sm text-foreground">{c}</span>
                  <Badge className="bg-[color:var(--success)]/10 text-[color:var(--success)] hover:bg-[color:var(--success)]/10">Active</Badge>
                </div>
              ))}
            </div>
          </Card>
        </motion.div>
      </section>

      <section>
        <Card className="p-6">
          <div className="flex items-center justify-between">
            <h3 className="text-base font-semibold text-foreground">Recent activity</h3>
            <span className="text-xs text-muted-foreground">Last 24 hours</span>
          </div>
          <div className="mt-4 space-y-3">
            {[0,1,2,3].map((i) => (
              <div key={i} className="flex items-center gap-4 rounded-lg border border-border bg-card/60 p-3">
                <Skeleton className="h-9 w-9 rounded-full" />
                <div className="min-w-0 flex-1 space-y-2">
                  <Skeleton className="h-3 w-2/3" />
                  <Skeleton className="h-3 w-1/3" />
                </div>
                <Skeleton className="h-3 w-16" />
              </div>
            ))}
          </div>
        </Card>
      </section>
    </div>
  );
}
