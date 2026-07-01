import PageHeader from "@/components/common/PageHeader.jsx";
import WalletCard from "@/components/domain/WalletCard.jsx";
import QueryState from "@/components/common/QueryState.jsx";
import EmptyState from "@/components/common/EmptyState.jsx";
import { Card } from "@/components/ui/card";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { useWallet, useWalletTransactions, useConnectWallet, useDisconnectWallet } from "@/hooks/useWallet.js";
import { fmtDateTime, truncate } from "@/lib/format.js";
import StatusBadge from "@/components/common/StatusBadge.jsx";
import { Wallet } from "lucide-react";
import { toast } from "sonner";

export default function WalletPage() {
  const walletQ = useWallet();
  const txQ = useWalletTransactions();
  const connect = useConnectWallet();
  const disconnect = useDisconnectWallet();

  const handleConnect = async () => {
    try {
      // smart-contract integration is not yet implemented; server-side may handle address binding
      await connect.mutateAsync({});
      toast.success("Wallet connection requested");
    } catch (e) {
      toast.error(e?.response?.data?.detail || "Connect failed");
    }
  };
  const handleDisconnect = async () => {
    try { await disconnect.mutateAsync(); toast.success("Wallet disconnected"); }
    catch (e) { toast.error(e?.response?.data?.detail || "Disconnect failed"); }
  };

  return (
    <div className="space-y-6">
      <PageHeader title="Wallet" description="Manage your blockchain wallet and view on-chain activity." />
      <QueryState query={walletQ} isEmpty={() => false}>
        {(w) => (
          <WalletCard
            wallet={w}
            onConnect={handleConnect}
            onDisconnect={handleDisconnect}
            connecting={connect.isPending}
            disconnecting={disconnect.isPending}
          />
        )}
      </QueryState>

      <div>
        <h3 className="mb-3 text-base font-semibold">Recent blockchain transactions</h3>
        <QueryState query={txQ} isEmpty={(d) => !(Array.isArray(d) ? d.length : d?.items?.length)}
          empty={<EmptyState icon={Wallet} title="No on-chain activity" description="Connect a wallet to start anchoring activity on-chain." />}
        >
          {(d) => {
            const rows = Array.isArray(d) ? d : d.items || [];
            return (
              <Card className="overflow-hidden">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Hash</TableHead>
                      <TableHead>Type</TableHead>
                      <TableHead>Date</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {rows.map((t) => (
                      <TableRow key={t.hash || t.id}>
                        <TableCell className="font-mono text-xs">{truncate(t.hash || t.id, 8)}</TableCell>
                        <TableCell>{t.type || "—"}</TableCell>
                        <TableCell>{fmtDateTime(t.createdAt || t.date)}</TableCell>
                        <TableCell><StatusBadge status={t.status} /></TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </Card>
            );
          }}
        </QueryState>
      </div>
    </div>
  );
}