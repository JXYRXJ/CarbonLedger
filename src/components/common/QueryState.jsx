import { Skeleton } from "@/components/ui/skeleton";
import EmptyState from "./EmptyState.jsx";
import ErrorState from "./ErrorState.jsx";

export default function QueryState({
  query, isEmpty, skeleton, empty, children,
}) {
  if (query.isLoading) return skeleton || (
    <div className="space-y-3">
      {[0,1,2,3].map((i) => <Skeleton key={i} className="h-20 w-full rounded-xl" />)}
    </div>
  );
  if (query.isError) return (
    <ErrorState
      title="Could not load data"
      description={query.error?.response?.data?.detail || query.error?.message || "Please try again."}
      onRetry={() => query.refetch()}
    />
  );
  const data = query.data;
  const emptyCheck = typeof isEmpty === "function"
    ? isEmpty(data)
    : Array.isArray(data) ? data.length === 0 : !data;
  if (emptyCheck) return empty || <EmptyState title="No data" description="Nothing to display yet." />;
  return children(data);
}