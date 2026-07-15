import { useLocation } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Input, Button, Alert } from "@/components/ui";
import { useTraderAuth } from "../hooks/useTraderAuth";

const schema = z.object({
  phone_number: z.string().min(10, "Enter a valid phone number"),
});

type FormValues = z.infer<typeof schema>;

export default function LoginPage() {
  const { requestOtp, isLoading, error } = useTraderAuth();
  const location = useLocation();
  const stateMessage = (location.state as { message?: string } | null)?.message;

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<FormValues>({ resolver: zodResolver(schema), mode: "onTouched" });

  const onSubmit = async (values: FormValues) => {
    await requestOtp(values.phone_number);
  };

  return (
    <div className="min-h-screen bg-cu-bg flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        {/* Card */}
        <div className="bg-white rounded-xl border border-cu-border shadow-card-md overflow-hidden">
          {/* Header strip */}
          <div className="bg-cu-red px-6 py-5 flex flex-col items-center gap-3 text-center">
            {/* Emblem placeholder */}
            <div className="h-14 w-14 rounded-full bg-white/20 border-2 border-white/50 flex items-center justify-center">
              <svg viewBox="0 0 40 40" className="h-9 w-9 text-white" fill="currentColor">
                <circle cx="20" cy="20" r="18" fill="none" stroke="currentColor" strokeWidth="1.5" />
                <polygon points="20,6 23.5,15 33,15 25.5,21 28.5,30 20,24.5 11.5,30 14.5,21 7,15 16.5,15" opacity="0.95" />
              </svg>
            </div>
            <div>
              <p className="text-white font-bold text-sm tracking-wide leading-tight">
                DISTRICT ASSEMBLY – REVENUE UNIT
              </p>
              <p className="text-white/70 text-xs mt-0.5">Trader Portal</p>
            </div>
          </div>

          {/* Form */}
          <div className="px-6 py-7">
            <h1 className="text-lg font-bold text-cu-text mb-6 text-center">Sign In</h1>

            {stateMessage && (
              <Alert variant="info" className="mb-5">
                {stateMessage}
              </Alert>
            )}

            {error && (
              <Alert variant="error" className="mb-5">
                {error}
              </Alert>
            )}

            <form onSubmit={handleSubmit(onSubmit)} noValidate className="space-y-4">
              <Input
                label="Phone Number"
                type="tel"
                placeholder="024 400 0000"
                required
                autoComplete="tel"
                error={errors.phone_number?.message}
                {...register("phone_number")}
              />
              <Button
                type="submit"
                variant="primary"
                size="lg"
                fullWidth
                isLoading={isLoading}
                className="mt-2"
              >
                Continue
              </Button>
            </form>

            <p className="mt-6 text-center text-xs text-cu-muted">
              Enter the phone number registered with your TIN to receive a verification code.
            </p>
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-cu-muted">
          &copy; {new Date().getFullYear()} Ghana District Assembly Revenue Unit
        </p>
      </div>
    </div>
  );
}
