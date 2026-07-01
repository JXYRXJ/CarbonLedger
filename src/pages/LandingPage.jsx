import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ArrowRight, Database, ShoppingBag, Fingerprint, Recycle, ShieldCheck, FileCheck,
  Sparkles, Lock, BarChart3,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import {
  Accordion, AccordionContent, AccordionItem, AccordionTrigger,
} from "@/components/ui/accordion";
import SectionHeader from "@/components/common/SectionHeader.jsx";
import AnimatedCounter from "@/components/common/AnimatedCounter.jsx";

const fadeUp = {
  hidden: { opacity: 0, y: 16 },
  show: (i = 0) => ({ opacity: 1, y: 0, transition: { duration: 0.5, delay: i * 0.06, ease: "easeOut" } }),
};

const features = [
  { icon: Database, title: "Carbon Asset Registry", desc: "Single source of truth for projects, credit batches, and serial numbers across registries." },
  { icon: ShoppingBag, title: "Carbon Marketplace", desc: "Discover, price, and trade verified credits with deep liquidity and institutional controls." },
  { icon: Fingerprint, title: "Ownership Tracking", desc: "Immutable chain of custody from issuance through every transfer to retirement." },
  { icon: Recycle, title: "Retirement Management", desc: "Programmatic retirement workflows with audit-ready certificates and disclosures." },
  { icon: ShieldCheck, title: "Blockchain Verification", desc: "Tamper-evident records anchored on-chain, verifiable by counterparties and auditors." },
  { icon: FileCheck, title: "Compliance & Audit", desc: "Built-in policy controls, role-based access, and complete activity audit trails." },
];

const steps = ["Registry", "Projects", "Credit Batches", "Ownership", "Marketplace", "Retirement"];

const faqs = [
  { q: "How does CarbonLedger ensure credit integrity?", a: "Every credit batch is anchored on-chain with cryptographic proofs, and our verification pipeline reconciles registry data continuously." },
  { q: "Which standards and registries are supported?", a: "We support Verra (VCS), Gold Standard, ACR, CAR, Puro.earth, and ICR, with additional registries onboarded quarterly." },
  { q: "Can we connect existing portfolios?", a: "Yes — import holdings via API or CSV. Ownership history reconciles automatically with on-chain records." },
  { q: "Is the platform compliant with enterprise security?", a: "CarbonLedger is SOC 2 Type II and ISO 27001 certified, with SSO, SCIM, and role-based access controls." },
  { q: "How does retirement work?", a: "Retirement instructions are recorded on-chain and synced to source registries, producing immutable certificates for disclosure." },
];

export default function LandingPage() {
  return (
    <div className="flex flex-col">
      {/* HERO */}
      <section className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(60%_60%_at_50%_0%,oklch(0.95_0.04_180)_0%,transparent_60%)]" />
        <div className="mx-auto max-w-7xl px-6 pb-20 pt-20 sm:pt-28">
          <motion.div
            initial="hidden" animate="show" variants={fadeUp}
            className="mx-auto max-w-3xl text-center"
          >
            <span className="inline-flex items-center gap-2 rounded-full border border-border bg-card px-3 py-1 text-xs font-medium text-muted-foreground shadow-sm">
              <Sparkles className="h-3.5 w-3.5 text-primary" /> New · Programmatic retirement API
            </span>
            <h1 className="mt-6 text-balance text-4xl font-semibold tracking-tight text-foreground sm:text-6xl">
              Enterprise Carbon Asset Management <span className="bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">Built for Modern Organizations</span>
            </h1>
            <p className="mx-auto mt-5 max-w-2xl text-pretty text-lg leading-relaxed text-muted-foreground">
              Manage, trade, verify, and retire carbon credit assets with full blockchain transparency.
              CarbonLedger gives sustainability teams an institutional-grade platform for the entire credit lifecycle.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Button asChild size="lg" className="bg-primary text-primary-foreground hover:bg-primary/90">
                <Link to="/register">Get Started <ArrowRight className="ml-1.5 h-4 w-4" /></Link>
              </Button>
              <Button asChild size="lg" variant="outline">
                <a href="#platform">View Platform</a>
              </Button>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 32 }} animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 0.2, ease: "easeOut" }}
            className="relative mx-auto mt-16 max-w-5xl"
          >
            <div className="relative rounded-2xl border border-border bg-card p-2 shadow-2xl shadow-primary/10">
              <div className="rounded-xl border border-border bg-background">
                <div className="flex items-center gap-1.5 border-b border-border px-4 py-2.5">
                  <span className="h-2.5 w-2.5 rounded-full bg-[color:var(--danger)]/70" />
                  <span className="h-2.5 w-2.5 rounded-full bg-[color:var(--warning)]/70" />
                  <span className="h-2.5 w-2.5 rounded-full bg-[color:var(--success)]/70" />
                  <span className="ml-3 text-xs text-muted-foreground">app.carbonledger.io/dashboard</span>
                </div>
                <div className="grid grid-cols-12 gap-4 p-5">
                  <div className="col-span-3 hidden flex-col gap-2 lg:flex">
                    {["Dashboard","Registry","Marketplace","Portfolio","Retirement","Analytics"].map((s, i) => (
                      <div key={s} className={`flex h-8 items-center rounded-md px-3 text-xs ${i===0?"bg-primary/10 text-primary font-medium":"text-muted-foreground"}`}>{s}</div>
                    ))}
                  </div>
                  <div className="col-span-12 lg:col-span-9">
                    <div className="grid grid-cols-3 gap-3">
                      {[
                        { k: "Portfolio Value", v: "$12.4M", d: "+8.2%" },
                        { k: "Credits Owned", v: "248,930", d: "+1,204" },
                        { k: "Retired", v: "62,100", d: "YTD" },
                      ].map((c) => (
                        <div key={c.k} className="rounded-lg border border-border bg-card p-3">
                          <p className="text-[10px] uppercase tracking-wide text-muted-foreground">{c.k}</p>
                          <p className="mt-1 text-lg font-semibold text-foreground">{c.v}</p>
                          <p className="text-[10px] text-[color:var(--success)]">{c.d}</p>
                        </div>
                      ))}
                    </div>
                    <div className="mt-4 h-40 rounded-lg border border-border bg-gradient-to-br from-primary/10 via-transparent to-accent/10" />
                    <div className="mt-4 grid grid-cols-2 gap-3">
                      <div className="h-24 rounded-lg border border-border bg-card" />
                      <div className="h-24 rounded-lg border border-border bg-card" />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* TRUSTED */}
      <section className="border-y border-border bg-card/50 py-10">
        <div className="mx-auto max-w-7xl px-6">
          <p className="text-center text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Trusted by sustainability teams at leading organizations
          </p>
          <div className="mt-6 grid grid-cols-2 items-center gap-6 opacity-70 sm:grid-cols-3 md:grid-cols-6">
            {["Helio","Northwind","Vertex","Atlas","Lumen","Quantum"].map((n) => (
              <div key={n} className="text-center text-lg font-semibold tracking-tight text-muted-foreground">{n}</div>
            ))}
          </div>
        </div>
      </section>

      {/* FEATURES */}
      <section id="platform" className="py-24">
        <div className="mx-auto max-w-7xl px-6">
          <SectionHeader
            eyebrow="Platform"
            title="Everything you need to manage carbon at scale"
            description="Built end-to-end for the carbon lifecycle — from registry intake through retirement and disclosure."
          />
          <div className="mt-14 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f, i) => (
              <motion.div key={f.title} custom={i} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-80px" }} variants={fadeUp}>
                <Card className="group h-full p-6 transition-all hover:-translate-y-1 hover:shadow-lg">
                  <span className="inline-grid h-10 w-10 place-items-center rounded-lg bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-primary-foreground">
                    <f.icon className="h-5 w-5" />
                  </span>
                  <h3 className="mt-4 text-base font-semibold text-foreground">{f.title}</h3>
                  <p className="mt-1.5 text-sm leading-relaxed text-muted-foreground">{f.desc}</p>
                </Card>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="solutions" className="border-t border-border bg-card/40 py-24">
        <div className="mx-auto max-w-7xl px-6">
          <SectionHeader eyebrow="How it works" title="The complete carbon credit lifecycle" description="One transparent workflow from issuance to retirement, anchored on-chain at every step." />
          <div className="mt-14 grid gap-3 md:grid-cols-6">
            {steps.map((s, i) => (
              <motion.div key={s} custom={i} initial="hidden" whileInView="show" viewport={{ once: true, margin: "-60px" }} variants={fadeUp}>
                <div className="relative rounded-xl border border-border bg-card p-5">
                  <span className="text-xs font-semibold text-muted-foreground">Step {i + 1}</span>
                  <p className="mt-1 text-sm font-semibold text-foreground">{s}</p>
                  <div className="mt-3 h-1 w-full rounded-full bg-muted">
                    <div className="h-1 rounded-full bg-gradient-to-r from-primary to-secondary" style={{ width: `${((i+1)/steps.length)*100}%` }} />
                  </div>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* STATS */}
      <section className="py-24">
        <div className="mx-auto max-w-7xl px-6">
          <SectionHeader eyebrow="Platform statistics" title="Trusted scale, measurable impact" />
          <div className="mt-14 grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
            {[
              { label: "Credits under management", value: 12400000, suffix: "+" },
              { label: "Verified retirements", value: 2840000, suffix: "" },
              { label: "Registries integrated", value: 14, suffix: "" },
              { label: "Enterprise customers", value: 320, suffix: "+" },
            ].map((s) => (
              <Card key={s.label} className="p-6 text-center">
                <p className="text-3xl font-semibold tracking-tight text-foreground sm:text-4xl">
                  <AnimatedCounter value={s.value} suffix={s.suffix} />
                </p>
                <p className="mt-2 text-sm text-muted-foreground">{s.label}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* SECURITY */}
      <section id="resources" className="border-t border-border bg-card/40 py-24">
        <div className="mx-auto grid max-w-7xl gap-12 px-6 lg:grid-cols-2">
          <div>
            <SectionHeader align="left" eyebrow="Security & Compliance" title="Audit-ready by design" description="Every action is logged, every credit is verifiable. CarbonLedger gives auditors and counterparties cryptographic certainty without sacrificing performance." />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            {[
              { icon: Lock, t: "SOC 2 Type II", d: "Independently audited security controls." },
              { icon: ShieldCheck, t: "On-chain anchoring", d: "Tamper-evident records for every transaction." },
              { icon: BarChart3, t: "Full audit trail", d: "Immutable activity logs for every user action." },
              { icon: FileCheck, t: "Disclosure ready", d: "Export reports aligned with CDP, TCFD, GHG." },
            ].map((b) => (
              <Card key={b.t} className="p-5">
                <span className="inline-grid h-9 w-9 place-items-center rounded-lg bg-accent/10 text-[color:var(--accent)]">
                  <b.icon className="h-4 w-4" />
                </span>
                <p className="mt-3 text-sm font-semibold text-foreground">{b.t}</p>
                <p className="mt-1 text-xs text-muted-foreground">{b.d}</p>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="about" className="py-24">
        <div className="mx-auto max-w-3xl px-6">
          <SectionHeader eyebrow="FAQ" title="Frequently asked questions" />
          <Accordion type="single" collapsible className="mt-10 divide-y divide-border rounded-xl border border-border bg-card">
            {faqs.map((f, i) => (
              <AccordionItem key={i} value={`item-${i}`} className="border-0 px-5">
                <AccordionTrigger className="text-left text-sm font-medium text-foreground">{f.q}</AccordionTrigger>
                <AccordionContent className="text-sm text-muted-foreground">{f.a}</AccordionContent>
              </AccordionItem>
            ))}
          </Accordion>
        </div>
      </section>

      {/* CTA */}
      <section className="pb-24">
        <div className="mx-auto max-w-7xl px-6">
          <div className="relative overflow-hidden rounded-3xl border border-border bg-gradient-to-br from-primary to-secondary p-12 text-center text-primary-foreground shadow-xl">
            <div className="pointer-events-none absolute inset-0 opacity-20 [background:radial-gradient(40%_60%_at_80%_0%,white,transparent)]" />
            <h3 className="text-3xl font-semibold tracking-tight sm:text-4xl">
              Bring institutional rigor to your carbon strategy
            </h3>
            <p className="mx-auto mt-3 max-w-xl text-sm/relaxed text-primary-foreground/85">
              Start managing your portfolio in minutes. No legacy procurement required.
            </p>
            <div className="mt-7 flex flex-wrap items-center justify-center gap-3">
              <Button asChild size="lg" variant="secondary" className="bg-white text-primary hover:bg-white/90">
                <Link to="/register">Get Started</Link>
              </Button>
              <Button asChild size="lg" variant="outline" className="border-white/30 bg-transparent text-white hover:bg-white/10">
                <Link to="/login">Sign in</Link>
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
