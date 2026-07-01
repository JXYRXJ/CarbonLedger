export default function SectionHeader({ eyebrow, title, description, align = "center" }) {
  const alignment = align === "left" ? "text-left items-start" : "text-center items-center mx-auto";
  return (
    <div className={`flex max-w-2xl flex-col gap-3 ${alignment}`}>
      {eyebrow && (
        <span className="inline-flex w-fit items-center rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground">
          {eyebrow}
        </span>
      )}
      <h2 className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
        {title}
      </h2>
      {description && (
        <p className="text-base leading-relaxed text-muted-foreground">{description}</p>
      )}
    </div>
  );
}
