import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import PageHeader from "@/components/common/PageHeader.jsx";
import { Card } from "@/components/ui/card";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { settingsApi } from "@/services/settingsApi.js";
import WalletCard from "@/components/domain/WalletCard.jsx";
import { useWallet, useConnectWallet, useDisconnectWallet } from "@/hooks/useWallet.js";
import { toast } from "sonner";

const profileSchema = z.object({
  firstName: z.string().min(1, "Required").max(80),
  lastName: z.string().min(1, "Required").max(80),
  email: z.string().email(),
  companyName: z.string().max(120).optional().or(z.literal("")),
  industry: z.string().max(80).optional().or(z.literal("")),
  country: z.string().max(80).optional().or(z.literal("")),
  website: z.string().url("Invalid URL").optional().or(z.literal("")),
  emailDomain: z.string().max(80).optional().or(z.literal("")),
});

const passwordSchema = z.object({
  currentPassword: z.string().min(8, "Min 8 characters"),
  newPassword: z.string().min(8, "Min 8 characters").max(128),
  confirm: z.string().min(8),
}).refine((d) => d.newPassword === d.confirm, { path: ["confirm"], message: "Passwords don't match" });

function ProfileForm() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["settings-profile"], queryFn: settingsApi.getProfile });
  const form = useForm({ resolver: zodResolver(profileSchema), defaultValues: { firstName: "", lastName: "", email: "", companyName: "", industry: "", country: "", website: "", emailDomain: "" } });
  useEffect(() => {
    if (q.data) {
      form.reset({
        firstName: q.data?.user?.first_name || "",
        lastName: q.data?.user?.last_name || "",
        email: q.data?.user?.email || "",
        companyName: q.data?.company?.name || "",
        industry: q.data?.company?.industry || "",
        country: q.data?.company?.country || "",
        website: q.data?.company?.website || "",
        emailDomain: q.data?.company?.email_domain || "",
      });
    }
  }, [q.data]); // eslint-disable-line
  const save = useMutation({
    mutationFn: async (values) => {
      await settingsApi.updateProfile({ first_name: values.firstName, last_name: values.lastName, email: values.email });
      const companyPayload = {
        name: values.companyName || undefined,
        industry: values.industry || undefined,
        country: values.country || undefined,
        website: values.website || undefined,
        email_domain: values.emailDomain || undefined,
      };
      if (Object.values(companyPayload).some(Boolean)) {
        await settingsApi.updateCompany(companyPayload);
      }
      return values;
    },
    onSuccess: () => { toast.success("Profile updated"); qc.invalidateQueries({ queryKey: ["settings-profile"] }); },
    onError: (e) => toast.error(e?.response?.data?.detail || "Failed"),
  });
  return (
    <Card className="max-w-2xl p-6">
      <form className="space-y-4" onSubmit={form.handleSubmit((v) => save.mutate(v))}>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5"><Label>First name</Label><Input {...form.register("firstName")} />{form.formState.errors.firstName && <p className="text-xs text-destructive">{form.formState.errors.firstName.message}</p>}</div>
          <div className="space-y-1.5"><Label>Last name</Label><Input {...form.register("lastName")} />{form.formState.errors.lastName && <p className="text-xs text-destructive">{form.formState.errors.lastName.message}</p>}</div>
        </div>
        <div className="space-y-1.5"><Label>Email</Label><Input type="email" {...form.register("email")} />{form.formState.errors.email && <p className="text-xs text-destructive">{form.formState.errors.email.message}</p>}</div>
        <div className="space-y-1.5"><Label>Company name</Label><Input {...form.register("companyName")} />{form.formState.errors.companyName && <p className="text-xs text-destructive">{form.formState.errors.companyName.message}</p>}</div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5"><Label>Industry</Label><Input {...form.register("industry")} /></div>
          <div className="space-y-1.5"><Label>Email domain</Label><Input {...form.register("emailDomain")} /></div>
        </div>
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5"><Label>Country</Label><Input {...form.register("country")} /></div>
          <div className="space-y-1.5"><Label>Website</Label><Input {...form.register("website")} />{form.formState.errors.website && <p className="text-xs text-destructive">{form.formState.errors.website.message}</p>}</div>
        </div>
        <div className="flex justify-end"><Button type="submit" disabled={save.isPending}>Save changes</Button></div>
      </form>
    </Card>
  );
}

function PasswordForm() {
  const form = useForm({ resolver: zodResolver(passwordSchema), defaultValues: { currentPassword: "", newPassword: "", confirm: "" } });
  const save = useMutation({
    mutationFn: (values) => settingsApi.changePassword({ old_password: values.currentPassword, new_password: values.newPassword }),
    onSuccess: () => { toast.success("Password updated"); form.reset(); },
    onError: (e) => toast.error(e?.response?.data?.detail || "Failed"),
  });
  return (
    <Card className="max-w-2xl p-6">
      <form className="space-y-4" onSubmit={form.handleSubmit((v) => save.mutate(v))}>
        <div className="space-y-1.5"><Label>Current password</Label><Input type="password" {...form.register("currentPassword")} />{form.formState.errors.currentPassword && <p className="text-xs text-destructive">{form.formState.errors.currentPassword.message}</p>}</div>
        <div className="space-y-1.5"><Label>New password</Label><Input type="password" {...form.register("newPassword")} />{form.formState.errors.newPassword && <p className="text-xs text-destructive">{form.formState.errors.newPassword.message}</p>}</div>
        <div className="space-y-1.5"><Label>Confirm new password</Label><Input type="password" {...form.register("confirm")} />{form.formState.errors.confirm && <p className="text-xs text-destructive">{form.formState.errors.confirm.message}</p>}</div>
        <div className="flex justify-end"><Button type="submit" disabled={save.isPending}>Update password</Button></div>
      </form>
    </Card>
  );
}

function NotificationsForm() {
  const qc = useQueryClient();
  const q = useQuery({ queryKey: ["settings-notifications"], queryFn: settingsApi.getNotifications });
  const [state, setState] = useState({ emailUpdates: true, orderUpdates: true, retirementUpdates: true, marketingEmails: false });
  useEffect(() => { if (q.data) setState({ ...state, ...q.data }); }, [q.data]); // eslint-disable-line
  const save = useMutation({
    mutationFn: settingsApi.updateNotifications,
    onSuccess: () => { toast.success("Preferences saved"); qc.invalidateQueries({ queryKey: ["settings-notifications"] }); },
    onError: (e) => toast.error(e?.response?.data?.detail || "Failed"),
  });
  const Row = ({ k, label, desc }) => (
    <div className="flex items-center justify-between gap-4 border-b border-border py-3 last:border-0">
      <div><p className="text-sm font-medium">{label}</p><p className="text-xs text-muted-foreground">{desc}</p></div>
      <Switch checked={!!state[k]} onCheckedChange={(v) => setState((p) => ({ ...p, [k]: v }))} />
    </div>
  );
  return (
    <Card className="max-w-2xl p-6">
      <Row k="emailUpdates" label="Email updates" desc="Product news and platform announcements." />
      <Row k="orderUpdates" label="Order updates" desc="Status changes for your marketplace orders." />
      <Row k="retirementUpdates" label="Retirement updates" desc="Certificate and on-chain confirmations." />
      <Row k="marketingEmails" label="Marketing emails" desc="Occasional offers and partner content." />
      <div className="flex justify-end pt-4"><Button onClick={() => save.mutate(state)} disabled={save.isPending}>Save preferences</Button></div>
    </Card>
  );
}

function ThemeForm() {
  const [theme, setTheme] = useState(() => (typeof document !== "undefined" && document.documentElement.classList.contains("dark") ? "dark" : "light"));
  const apply = (t) => {
    setTheme(t);
    const root = document.documentElement;
    if (t === "dark") root.classList.add("dark"); else root.classList.remove("dark");
    try { localStorage.setItem("cl_theme", t); } catch { /* noop */ }
  };
  return (
    <Card className="max-w-2xl p-6">
      <p className="text-sm font-medium">Appearance</p>
      <p className="text-xs text-muted-foreground">Choose how CarbonLedger looks for you.</p>
      <div className="mt-4 flex gap-2">
        <Button variant={theme === "light" ? "default" : "outline"} onClick={() => apply("light")}>Light</Button>
        <Button variant={theme === "dark" ? "default" : "outline"} onClick={() => apply("dark")}>Dark</Button>
      </div>
    </Card>
  );
}

function ConnectedWallet() {
  const walletQ = useWallet();
  const connect = useConnectWallet();
  const disconnect = useDisconnectWallet();
  return (
    <WalletCard
      wallet={walletQ.data}
      onConnect={async () => { try { await connect.mutateAsync({}); toast.success("Connect requested"); } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); } }}
      onDisconnect={async () => { try { await disconnect.mutateAsync(); toast.success("Disconnected"); } catch (e) { toast.error(e?.response?.data?.detail || "Failed"); } }}
      connecting={connect.isPending}
      disconnecting={disconnect.isPending}
    />
  );
}

function SecurityPanel() {
  return (
    <Card className="max-w-2xl p-6 space-y-3 text-sm">
      <p className="font-medium">Security</p>
      <p className="text-muted-foreground">Two-factor authentication and session management will be available soon. Contact support to revoke active sessions.</p>
    </Card>
  );
}

export default function SettingsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const tab = searchParams.get("tab") || "profile";

  return (
    <div className="space-y-6">
      <PageHeader title="Settings" description="Manage your company profile, notifications, and security." />
      <Tabs value={tab} onValueChange={(val) => setSearchParams({ tab: val })}>
        <TabsList className="flex-wrap">
          <TabsTrigger value="profile">Company Profile</TabsTrigger>
          <TabsTrigger value="password">Password</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
          <TabsTrigger value="wallet">Connected Wallet</TabsTrigger>
          <TabsTrigger value="security">Security</TabsTrigger>
          <TabsTrigger value="theme">Theme</TabsTrigger>
        </TabsList>
        <TabsContent value="profile"><ProfileForm /></TabsContent>
        <TabsContent value="password"><PasswordForm /></TabsContent>
        <TabsContent value="notifications"><NotificationsForm /></TabsContent>
        <TabsContent value="wallet"><ConnectedWallet /></TabsContent>
        <TabsContent value="security"><SecurityPanel /></TabsContent>
        <TabsContent value="theme"><ThemeForm /></TabsContent>
      </Tabs>
    </div>
  );
}