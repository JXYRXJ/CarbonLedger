import PageHeader from "@/components/common/PageHeader.jsx";
import AnalyticsCard from "@/components/domain/AnalyticsCard.jsx";
import EmptyState from "@/components/common/EmptyState.jsx";
import {
  usePortfolioGrowth, useCreditsTraded, useCreditsRetired,
  useMarketplaceVolume, useCountryDistribution, useProjectTypes,
} from "@/hooks/useAnalytics.js";
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis, Tooltip, CartesianGrid,
  BarChart, Bar, PieChart, Pie, Cell, Legend, LineChart, Line,
} from "recharts";
import { BarChart3 } from "lucide-react";

const PALETTE = ["#0F766E", "#14B8A6", "#22D3EE", "#6366F1", "#A78BFA", "#F59E0B", "#EF4444"];

function asArray(d) { return Array.isArray(d) ? d : d?.items || []; }

function ChartEmpty() {
  return <div className="grid h-64 place-items-center text-sm text-muted-foreground">No data available</div>;
}

export default function AnalyticsPage() {
  const growth = usePortfolioGrowth();
  const traded = useCreditsTraded();
  const retired = useCreditsRetired();
  const volume = useMarketplaceVolume();
  const countries = useCountryDistribution();
  const types = useProjectTypes();

  const growthData = asArray(growth.data);
  const tradedData = asArray(traded.data);
  const retiredData = asArray(retired.data);
  const volumeData = asArray(volume.data);
  const countryData = asArray(countries.data);
  const typesData = asArray(types.data);

  return (
    <div className="space-y-6">
      <PageHeader title="Analytics" description="Insights across your portfolio and the marketplace." />
      <div className="grid gap-4 lg:grid-cols-2">
        <AnalyticsCard title="Portfolio Growth" description="Cumulative value over time" loading={growth.isLoading}>
          {growthData.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={growthData}>
                <defs><linearGradient id="g1" x1="0" x2="0" y1="0" y2="1"><stop offset="0%" stopColor="#0F766E" stopOpacity={0.4} /><stop offset="100%" stopColor="#0F766E" stopOpacity={0} /></linearGradient></defs>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Area type="monotone" dataKey="value" stroke="#0F766E" fill="url(#g1)" />
              </AreaChart>
            </ResponsiveContainer>
          ) : <ChartEmpty />}
        </AnalyticsCard>

        <AnalyticsCard title="Credits Traded" description="Volume by period" loading={traded.isLoading}>
          {tradedData.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={tradedData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Bar dataKey="credits" fill="#14B8A6" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <ChartEmpty />}
        </AnalyticsCard>

        <AnalyticsCard title="Credits Retired" description="Retirements over time" loading={retired.isLoading}>
          {retiredData.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <LineChart data={retiredData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Line type="monotone" dataKey="credits" stroke="#0F766E" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          ) : <ChartEmpty />}
        </AnalyticsCard>

        <AnalyticsCard title="Marketplace Volume" description="Trading volume (USD)" loading={volume.isLoading}>
          {volumeData.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={volumeData}>
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Area type="monotone" dataKey="volume" stroke="#6366F1" fill="#6366F1" fillOpacity={0.15} />
              </AreaChart>
            </ResponsiveContainer>
          ) : <ChartEmpty />}
        </AnalyticsCard>

        <AnalyticsCard title="Country Distribution" description="Credits by country" loading={countries.isLoading}>
          {countryData.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <PieChart>
                <Pie data={countryData} dataKey="value" nameKey="name" innerRadius={60} outerRadius={100} paddingAngle={2}>
                  {countryData.map((_, i) => <Cell key={i} fill={PALETTE[i % PALETTE.length]} />)}
                </Pie>
                <Tooltip /><Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : <ChartEmpty />}
        </AnalyticsCard>

        <AnalyticsCard title="Project Types" description="Breakdown by category" loading={types.isLoading}>
          {typesData.length ? (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={typesData} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" opacity={0.15} />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" tick={{ fontSize: 11 }} width={120} />
                <Tooltip />
                <Bar dataKey="value" fill="#0F766E" radius={[0,4,4,0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <ChartEmpty />}
        </AnalyticsCard>
      </div>
    </div>
  );
}