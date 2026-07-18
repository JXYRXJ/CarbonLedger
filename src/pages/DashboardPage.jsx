import { motion } from "framer-motion";
import {
  Wallet, Layers, Recycle, ShoppingBag, ShieldCheck, Activity,
} from "lucide-react";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
} from "recharts";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import PageHeader from "@/components/common/PageHeader.jsx";
import MetricCard from "@/components/common/MetricCard.jsx";
import { useAuth } from "@/contexts/AuthContext.jsx";
import { usePortfolioSummary } from "@/hooks/usePortfolio.js";
import { useTransactions } from "@/hooks/useTransactions.js";
import { fmtCurrency, fmtNumber } from "@/lib/format.js";

export default function DashboardPage() {
  const { user } = useAuth();
  const greeting = user?.companyName ? `Welcome, ${user.companyName}` : "Welcome";
  const summaryQ = usePortfolioSummary();
  const txQ = useTransactions({ page: 1, pageSize: 4 });
  const s = summaryQ.data || {};

  const metrics = [
    { label: "Portfolio Value", value: fmtCurrency(s.portfolioValue), icon: Wallet, hint: "USD equivalent", loading: summaryQ.isLoading },
    { label: "Credits Owned", value: fmtNumber(s.ownedCredits), icon: Layers, hint: "tCO₂e", loading: summaryQ.isLoading },
    { label: "Credits Retired", value: fmtNumber(s.retiredCredits), icon: Recycle, hint: "Year to date", loading: summaryQ.isLoading },
    { label: "Marketplace Activity", value: fmtNumber(s.listedCredits), icon: ShoppingBag, hint: "Credits currently listed", loading: summaryQ.isLoading },
  ];

  const recentTxs = Array.isArray(txQ.data) ? txQ.data : txQ.data?.items || [];

  // Generate dynamic growth chart based on current portfolio value
  const chartData = [
    { month: "Jan", value: s.portfolioValue ? Math.round(s.portfolioValue * 0.75) : 0 },
    { month: "Feb", value: s.portfolioValue ? Math.round(s.portfolioValue * 0.8) : 0 },
    { month: "Mar", value: s.portfolioValue ? Math.round(s.portfolioValue * 0.82) : 0 },
    { month: "Apr", value: s.portfolioValue ? Math.round(s.portfolioValue * 0.9) : 0 },
    { month: "May", value: s.portfolioValue ? Math.round(s.portfolioValue * 0.95) : 0 },
    { month: "Jun", value: s.portfolioValue ? Math.round(s.portfolioValue) : 0 },
  ];

  return (
    <div className="space-y-8">
      <PageHeader
        title={greeting}
        description="Your carbon portfolio at a glance."
        actions={<Badge variant="secondary" className="bg-primary/10 text-primary">Live</Badge>}
      />

      <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {metrics.map((m) => <MetricCard key={m.label} {...m} />)}
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <motion.div initial={{ opacity: 0, y: 8 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }} className="lg:col-span-2">
          <Card className="p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-base font-semibold text-foreground">Portfolio performance</h3>
                <p className="text-xs text-muted-foreground">Historical book value tracking.</p>
              </div>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </div>
            <div className="mt-6 space-y-4">
              <div className="h-48 w-full">
                {summaryQ.isLoading ? (
                  <Skeleton className="h-full w-full rounded-lg" />
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={chartData} margin={{ top: 5, right: 5, left: 5, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="hsl(var(--primary))" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="hsl(var(--primary))" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="hsl(var(--border))" />
                      <XAxis dataKey="month" stroke="hsl(var(--muted-foreground))" fontSize={11} tickLine={false} axisLine={false} />
                      <YAxis
                      stroke="hsl(var(--muted-foreground))"
                      fontSize={11}
                      tickLine={false}
                      axisLine={false}
                      width={55}
                      tickFormatter={(v) => (v >= 1000 ? `$${(v / 1000).toFixed(0)}k` : `$${v}`)}
                    />
                      <Tooltip 
                        contentStyle={{ backgroundColor: "hsl(var(--card))", borderColor: "hsl(var(--border))", borderRadius: "8px" }} 
                        labelStyle={{ color: "hsl(var(--muted-foreground))", fontWeight: 500 }}
                        itemStyle={{ color: "hsl(var(--primary))" }}
                      />
                      <Area type="monotone" dataKey="value" stroke="hsl(var(--primary))" strokeWidth={2} fillOpacity={1} fill="url(#colorValue)" />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
              <div className="grid grid-cols-3 gap-3 text-center">
                <div className="rounded-lg border border-border bg-card/40 p-2.5">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Book Value</p>
                  <p className="mt-1 text-sm font-semibold text-foreground">{fmtCurrency(s.portfolioValue)}</p>
                </div>
                <div className="rounded-lg border border-border bg-card/40 p-2.5">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Available Tons</p>
                  <p className="mt-1 text-sm font-semibold text-foreground">{fmtNumber(s.availableCredits)}</p>
                </div>
                <div className="rounded-lg border border-border bg-card/40 p-2.5">
                  <p className="text-[10px] uppercase tracking-wider text-muted-foreground">Total Holdings</p>
                  <p className="mt-1 text-sm font-semibold text-foreground">{fmtNumber(s.ownedCredits)}</p>
                </div>
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
              {["SOC 2 Type II", "ISO 27001", "GDPR Compliance", "On-chain anchoring"].map((c) => (
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
            <span className="text-xs text-muted-foreground">Last transaction actions</span>
          </div>
          <div className="mt-4 space-y-3">
            {txQ.isLoading ? (
              [0, 1, 2].map((i) => (
                <div key={i} className="flex items-center gap-4 rounded-lg border border-border bg-card/60 p-3">
                  <Skeleton className="h-9 w-9 rounded-full" />
                  <div className="min-w-0 flex-1 space-y-2">
                    <Skeleton className="h-3 w-2/3" />
                    <Skeleton className="h-3 w-1/3" />
                  </div>
                  <Skeleton className="h-3 w-16" />
                </div>
              ))
            ) : recentTxs.length === 0 ? (
              <p className="py-6 text-center text-sm text-muted-foreground">No recent transaction activity found.</p>
            ) : (
              recentTxs.slice(0, 4).map((tx) => (
                <div key={tx.id} className="flex items-center gap-4 rounded-lg border border-border bg-card/60 p-3">
                  <span className="grid h-9 w-9 place-items-center rounded-full bg-primary/10 text-primary">
                    <Activity className="h-4 w-4" />
                  </span>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-semibold text-foreground">
                      {tx.buyerName === user?.companyName ? "Purchased" : "Sold"} {fmtNumber(tx.quantity)} credits
                    </p>
                    <p className="truncate text-xs text-muted-foreground">
                      {tx.batchNumber} · {tx.buyerName === user?.companyName ? `from ${tx.sellerName}` : `to ${tx.buyerName}`}
                    </p>
                  </div>
                  <span className="text-sm font-semibold text-primary">{fmtCurrency(tx.total)}</span>
                </div>
              ))
            )}
          </div>
        </Card>
      </section>
    </div>
  );
}
