import { useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { motion } from "framer-motion";
import { ArrowRight } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/contexts/AuthContext.jsx";

const schema = z.object({
  firstName: z.string().min(1, "First name is required"),
  lastName: z.string().min(1, "Last name is required"),
  companyName: z.string().min(2, "Company name is required"),
  registrationNumber: z.string().min(2, "Registration number is required"),
  country: z.string().min(2, "Country is required"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Use at least 8 characters"),
  confirmPassword: z.string(),
  industry: z.string().max(80).optional().or(z.literal("")),
  website: z.string().url("Enter a valid URL").optional().or(z.literal("")),
  walletAddress: z.string().max(255).optional().or(z.literal("")),
}).refine((d) => d.password === d.confirmPassword, {
  path: ["confirmPassword"], message: "Passwords don't match",
});

export default function RegisterPage() {
  const { register: registerUser, loading, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  useEffect(() => { if (isAuthenticated) navigate("/dashboard", { replace: true }); }, [isAuthenticated, navigate]);

  const { register, handleSubmit, formState: { errors } } = useForm({ resolver: zodResolver(schema) });

  const onSubmit = async (values) => {
    try {
      await registerUser({
        first_name: values.firstName,
        last_name: values.lastName,
        company_name: values.companyName,
        registration_number: values.registrationNumber,
        country: values.country,
        email: values.email,
        password: values.password,
        industry: values.industry?.trim() || undefined,
        website: values.website?.trim() || undefined,
        wallet_address: values.walletAddress?.trim() || undefined,
      });
      toast.success("Account created");
      navigate("/dashboard", { replace: true });
    } catch (e) {
      toast.error(e?.response?.data?.message || "Unable to create account");
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
              <Input id="website" placeholder="https://acme.com" {...register("website")} />
              {errors.website && <p className="text-xs text-[color:var(--danger)]">{errors.website.message}</p>}
            </div>
          </div>
          <div className="space-y-2">
            <Label htmlFor="walletAddress">Wallet address (optional)</Label>
            <Input id="walletAddress" placeholder="0x71C..." {...register("walletAddress")} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Work email</Label>
            <Input id="email" type="email" placeholder="you@company.com" {...register("email")} />
            {errors.email && <p className="text-xs text-[color:var(--danger)]">{errors.email.message}</p>}
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" placeholder="At least 8 characters" {...register("password")} />
            {errors.password && <p className="text-xs text-[color:var(--danger)]">{errors.password.message}</p>}
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
