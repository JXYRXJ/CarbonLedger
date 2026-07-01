import Logo from "@/components/common/Logo.jsx";

const groups = [
  { title: "Platform", links: ["Registry", "Marketplace", "Portfolio", "Retirement"] },
  { title: "Company", links: ["About", "Customers", "Careers", "Contact"] },
  { title: "Resources", links: ["Documentation", "API", "Changelog", "Security"] },
  { title: "Legal", links: ["Privacy", "Terms", "Compliance", "SLA"] },
];

export default function Footer() {
  return (
    <footer className="border-t border-border bg-card">
      <div className="mx-auto max-w-7xl px-6 py-14">
        <div className="grid gap-10 md:grid-cols-[1.4fr_repeat(4,1fr)]">
          <div className="space-y-3">
            <Logo />
            <p className="max-w-xs text-sm text-muted-foreground">
              Enterprise carbon asset management with blockchain transparency.
            </p>
          </div>
          {groups.map((g) => (
            <div key={g.title}>
              <h4 className="text-xs font-semibold uppercase tracking-wide text-foreground">{g.title}</h4>
              <ul className="mt-3 space-y-2">
                {g.links.map((l) => (
                  <li key={l}>
                    <a className="text-sm text-muted-foreground hover:text-foreground" href="#">{l}</a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
        <div className="mt-12 flex flex-col items-center justify-between gap-3 border-t border-border pt-6 text-xs text-muted-foreground sm:flex-row">
          <p>© {new Date().getFullYear()} CarbonLedger. All rights reserved.</p>
          <p>SOC 2 Type II · ISO 27001 · GDPR</p>
        </div>
      </div>
    </footer>
  );
}
