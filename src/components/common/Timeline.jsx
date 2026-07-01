import { Circle } from "lucide-react";

export default function Timeline({ items = [] }) {
  if (!items.length) return null;
  return (
    <ol className="relative space-y-6 border-l border-border pl-6">
      {items.map((it, i) => (
        <li key={i} className="relative">
          <span className="absolute -left-[27px] top-1 grid h-4 w-4 place-items-center rounded-full bg-card ring-2 ring-primary/40">
            <Circle className="h-2 w-2 fill-primary text-primary" />
          </span>
          <p className="text-xs uppercase tracking-wide text-muted-foreground">{it.date}</p>
          <p className="mt-0.5 text-sm font-medium text-foreground">{it.title}</p>
          {it.description && <p className="mt-0.5 text-sm text-muted-foreground">{it.description}</p>}
        </li>
      ))}
    </ol>
  );
}