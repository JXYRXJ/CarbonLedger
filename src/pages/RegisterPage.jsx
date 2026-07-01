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
  companyName: z.string().min(2, "Company name is required"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Use at least 8 characters"),
  confirmPassword: z.string(),
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
        companyName: values.companyName,
        email: values.email,
        password: values.password,
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
          <div className="space-y-2">
            <Label htmlFor="companyName">Company name</Label>
            <Input id="companyName" placeholder="Acme Corp" {...register("companyName")} />
            {errors.companyName && <p className="text-xs text-[color:var(--danger)]">{errors.companyName.message}</p>}
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
