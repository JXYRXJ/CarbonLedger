import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Wallet, Copy, Check } from "lucide-react";
import { useState } from "react";
import StatusBadge from "@/components/common/StatusBadge.jsx";
import { truncate } from "@/lib/format.js";
import { toast } from "sonner";

export default function WalletCard({ wallet, onConnect, onDisconnect, connecting, disconnecting }) {
  const [copied, setCopied] = useState(false);
  const w = wallet || {};
  const copy = async () => {
    if (!w.address) return;
    try { await navigator.clipboard.writeText(w.address); setCopied(true); toast.success("Address copied"); setTimeout(() => setCopied(false), 1500); }
    catch { toast.error("Copy failed"); }
  };
  return (
    <Card className="p-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <span className="grid h-10 w-10 place-items-center rounded-lg bg-primary/10 text-primary">
            <Wallet className="h-5 w-5" />
          </span>
          <div>
            <p className="text-sm font-semibold text-foreground">Connected Wallet</p>
            <p className="text-xs text-muted-foreground">{w.network || "Network not set"}</p>
          </div>
        </div>
        <StatusBadge status={w.connected ? "active" : "unconfirmed"}>
          {w.connected ? "Connected" : "Not connected"}
        </StatusBadge>
      </div>
      <div className="mt-5 rounded-lg border border-border bg-muted/40 p-3">
        <p className="text-xs uppercase tracking-wide text-muted-foreground">Address</p>
        <div className="mt-1 flex items-center justify-between gap-2">
          <code className="truncate font-mono text-sm">{w.address ? truncate(w.address, 10) : "—"}</code>
          {w.address && (
            <Button variant="ghost" size="icon" onClick={copy} aria-label="Copy address">
              {copied ? <Check className="h-4 w-4 text-[color:var(--success)]" /> : <Copy className="h-4 w-4" />}
            </Button>
          )}
        </div>
      </div>
      <div className="mt-5 flex gap-2">
        {w.connected ? (
          <Button variant="outline" onClick={onDisconnect} disabled={disconnecting}>Disconnect</Button>
        ) : (
          <Button onClick={onConnect} disabled={connecting}>Connect Wallet</Button>
        )}
      </div>
    </Card>
  );
}