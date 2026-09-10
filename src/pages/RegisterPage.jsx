import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { ArrowRight, Check, X } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/contexts/AuthContext.jsx";

const schema = z.object({
  firstName: z.string().min(1, "First name is required"),
  lastName: z.string().min(1, "Last name is required"),
  companyName: z.string().min(2, "Company name is required"),
  registrationNumber: z.string().min(3, "Registration number must be at least 3 characters"),
  country: z.string().min(2, "Country is required"),
  email: z.string().email("Enter a valid email address"),
  password: z
    .string()
    .min(8, "Password must be at least 8 characters")
    .regex(/[A-Z]/, "Must contain at least one uppercase letter")
    .regex(/[a-z]/, "Must contain at least one lowercase letter")
    .regex(/[0-9]/, "Must contain at least one number")
    .regex(/[!@#$%^&*(),.?":{}|<>]/, "Must contain at least one special character"),
  confirmPassword: z.string(),
  industry: z.string().max(80).optional().or(z.literal("")),
  website: z.string().optional().refine((val) => {
    if (!val || !val.trim()) return true;
    try {
      const urlToTest = /^https?:\/\//i.test(val.trim()) ? val.trim() : `https://${val.trim()}`;
      new URL(urlToTest);
      return true;
    } catch {
      return false;
    }
  }, "Enter a valid website (e.g. acme.com)"),
  walletAddress: z.string().optional().refine((val) => {
    if (!val || !val.trim()) return true;
    return /^0x[a-fA-F0-9]{40}$/.test(val.trim());
  }, "Must be a valid 42-character Ethereum address (0x...)"),
}).refine((d) => d.password === d.confirmPassword, {
  path: ["confirmPassword"], message: "Passwords don't match",
});

const normalizeWebsite = (val) => {
  if (!val || !val.trim()) return undefined;
  const trimmed = val.trim();
  if (!/^https?:\/\//i.test(trimmed)) {
    return `https://${trimmed}`;
  }
  return trimmed;
};

const getErrorMessage = (e) => {
  const data = e?.response?.data;
  if (!data) return e?.message || "Unable to create account";

  if (Array.isArray(data.errors) && data.errors.length > 0) {
    const detailList = data.errors.map((err) => {
      if (typeof err === "string") return err;
      if (err?.message) return `${err.field ? `${err.field}: ` : ""}${err.message}`;
      return JSON.stringify(err);
    }).join(". ");
    return `${data.message ? `${data.message}: ` : ""}${detailList}`;
  }

  return data.message || data.detail || "Unable to create account";
};

export default function RegisterPage() {
  const { register: registerUser, loading, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [passwordFocus, setPasswordFocus] = useState(false);

  useEffect(() => { if (isAuthenticated) navigate("/dashboard", { replace: true }); }, [isAuthenticated, navigate]);

  const { register, handleSubmit, watch, formState: { errors } } = useForm({ resolver: zodResolver(schema), mode: "onChange" });

  const passwordVal = watch("password", "");
  const pwdCriteria = [
    { label: "8+ characters", met: passwordVal.length >= 8 },
    { label: "Uppercase letter (A-Z)", met: /[A-Z]/.test(passwordVal) },
    { label: "Lowercase letter (a-z)", met: /[a-z]/.test(passwordVal) },
    { label: "Number (0-9)", met: /[0-9]/.test(passwordVal) },
    { label: "Special character (!@#$%^&*)", met: /[!@#$%^&*(),.?":{}|<>]/.test(passwordVal) },
  ];

  const onSubmit = async (values) => {
    try {
      await registerUser({
        first_name: values.firstName.trim(),
        last_name: values.lastName.trim(),
        company_name: values.companyName.trim(),
        registration_number: values.registrationNumber.trim(),
        country: values.country.trim(),
        email: values.email.trim(),
        password: values.password,
        industry: values.industry?.trim() || undefined,
        website: normalizeWebsite(values.website),
        wallet_address: values.walletAddress?.trim() || undefined,
      });
      toast.success("Account created successfully");
      navigate("/dashboard", { replace: true });
    } catch (e) {
      toast.error(getErrorMessage(e));
    }
  };

  return (
    <div className="mx-auto flex min-h-[80vh] max-w-md flex-col justify-center px-6 py-16">
      <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.4 }}>
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">Create your account</h1>
        <p className="mt-2 text-sm text-muted-foreground">Get started with CarbonLedger in minutes.</p>

        <form onSubmit={handleSubmit(onSubmit)} className="mt-8 space-y-5">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="firstName">First name</Label>
              <Input id="firstName" placeholder="Jane" {...register("firstName")} />
              {errors.firstName && <p className="text-xs text-[color:var(--danger)]">{errors.firstName.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="lastName">Last name</Label>
              <Input id="lastName" placeholder="Doe" {...register("lastName")} />
              {errors.lastName && <p className="text-xs text-[color:var(--danger)]">{errors.lastName.message}</p>}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="companyName">Company name</Label>
            <Input id="companyName" placeholder="Acme Corp" {...register("companyName")} />
            {errors.companyName && <p className="text-xs text-[color:var(--danger)]">{errors.companyName.message}</p>}
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="registrationNumber">Registration number</Label>
              <Input id="registrationNumber" placeholder="CO-1234567-X" {...register("registrationNumber")} />
              {errors.registrationNumber && <p className="text-xs text-[color:var(--danger)]">{errors.registrationNumber.message}</p>}
            </div>
            <div className="space-y-2">
              <Label htmlFor="country">Country</Label>
              <Input id="country" placeholder="United States" {...register("country")} />
              {errors.country && <p className="text-xs text-[color:var(--danger)]">{errors.country.message}</p>}
            </div>
          </div>
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="industry">Industry</Label>
              <Input id="industry" placeholder="Technology" {...register("industry")} />
            </div>
            <div className="space-y-2">
              <Label htmlFor="website">Website</Label>
              <Input id="website" placeholder="acme.com" {...register("website")} />
              {errors.website && <p className="text-xs text-[color:var(--danger)]">{errors.website.message}</p>}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="walletAddress">Wallet address (optional)</Label>
            <Input id="walletAddress" placeholder="0x71C..." {...register("walletAddress")} />
            {errors.walletAddress && <p className="text-xs text-[color:var(--danger)]">{errors.walletAddress.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Work email</Label>
            <Input id="email" type="email" placeholder="you@company.com" {...register("email")} />
            {errors.email && <p className="text-xs text-[color:var(--danger)]">{errors.email.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input
              id="password"
              type="password"
              placeholder="Strong password required"
              {...register("password")}
              onFocus={() => setPasswordFocus(true)}
            />
            {errors.password && <p className="text-xs text-[color:var(--danger)]">{errors.password.message}</p>}
            {(passwordFocus || passwordVal) && (
              <div className="rounded-lg border border-border/50 bg-muted/30 p-2.5 text-xs space-y-1 mt-1.5">
                <p className="font-medium text-muted-foreground mb-1">Password requirements:</p>
                {pwdCriteria.map((c, i) => (
                  <div key={i} className={`flex items-center gap-1.5 ${c.met ? "text-emerald-500" : "text-muted-foreground"}`}>
                    {c.met ? <Check className="h-3.5 w-3.5 flex-shrink-0" /> : <X className="h-3.5 w-3.5 flex-shrink-0 opacity-40" />}
                    <span>{c.label}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="confirmPassword">Confirm password</Label>
            <Input id="confirmPassword" type="password" placeholder="Re-enter password" {...register("confirmPassword")} />
            {errors.confirmPassword && <p className="text-xs text-[color:var(--danger)]">{errors.confirmPassword.message}</p>}
          </div>
          <Button type="submit" disabled={loading} className="w-full bg-primary text-primary-foreground hover:bg-primary/90">
            {loading ? "Creating account…" : (<>Create account <ArrowRight className="ml-1.5 h-4 w-4" /></>)}
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-primary hover:underline">Sign in</Link>
        </p>
      </motion.div>
    </div>
  );
}

