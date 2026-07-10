import { ChangeEvent, KeyboardEvent, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Alert, Button } from "@/components/ui";
import { useAdminAuth } from "../hooks/useAdminAuth";

const CODE_LENGTH = 6;
const RESEND_COOLDOWN_SECONDS = 60;

function secondsLeft(until: number) {
  return Math.max(0, Math.ceil((until - Date.now()) / 1000));
}

function formatSeconds(total: number) {
  const minutes = Math.floor(total / 60).toString().padStart(2, "0");
  const seconds = (total % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export default function VerifyOtpPage() {
  const navigate = useNavigate();
  const { verifyOtp, resendOtp, getPendingOtpSession, clearPendingOtpSession, isLoading, error, remainingAttempts } = useAdminAuth();
  const [digits, setDigits] = useState(Array(CODE_LENGTH).fill(""));
  const [timeLeft, setTimeLeft] = useState(0);
  const [resendLeft, setResendLeft] = useState(RESEND_COOLDOWN_SECONDS);
  const [notice, setNotice] = useState<string | null>(null);
  const inputRefs = useRef<Array<HTMLInputElement | null>>([]);
  const pending = useMemo(() => getPendingOtpSession(), [getPendingOtpSession]);

  useEffect(() => {
    if (!pending) {
      navigate("/admin/login", { replace: true, state: { message: "Verification expired. Please sign in again." } });
      return;
    }

    const tick = () => {
      const remaining = secondsLeft(Math.min(pending.expiresAt, pending.otpExpiresAt));
      setTimeLeft(remaining);
      setResendLeft((current) => Math.max(0, current - 1));
      if (remaining <= 0) {
        clearPendingOtpSession();
        navigate("/admin/login", { replace: true, state: { message: "Verification expired. Please sign in again." } });
      }
    };

    tick();
    const timer = window.setInterval(tick, 1000);
    inputRefs.current[0]?.focus();
    return () => window.clearInterval(timer);
  }, [clearPendingOtpSession, navigate, pending]);

  const code = digits.join("");

  const updateDigit = (index: number, value: string) => {
    const nextChar = value.replace(/\D/g, "").slice(-1);
    const next = [...digits];
    next[index] = nextChar;
    setDigits(next);
    if (nextChar && index < CODE_LENGTH - 1) {
      inputRefs.current[index + 1]?.focus();
    }
  };

  const handlePaste = (value: string) => {
    const chars = value.replace(/\D/g, "").slice(0, CODE_LENGTH).split("");
    if (!chars.length) return;
    const next = Array(CODE_LENGTH).fill("");
    chars.forEach((char, index) => {
      next[index] = char;
    });
    setDigits(next);
    inputRefs.current[Math.min(chars.length, CODE_LENGTH - 1)]?.focus();
  };

  const handleKeyDown = (index: number, event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === "Backspace" && !digits[index] && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const submitCode = async () => {
    if (code.length !== CODE_LENGTH) return;
    await verifyOtp(code);
  };

  const handleResend = async () => {
    const session = await resendOtp();
    setDigits(Array(CODE_LENGTH).fill(""));
    setNotice("A new verification code has been sent.");
    setResendLeft(RESEND_COOLDOWN_SECONDS);
    setTimeLeft(secondsLeft(Math.min(session.expiresAt, session.otpExpiresAt)));
    inputRefs.current[0]?.focus();
  };

  if (!pending) return null;

  return (
    <div className="min-h-screen bg-cu-bg flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="bg-white rounded-xl border border-cu-border shadow-card-md overflow-hidden">
          <div className="bg-cu-red px-6 py-5 text-center">
            <p className="text-white font-bold text-sm tracking-wide leading-tight">DISTRICT ASSEMBLY - REVENUE UNIT</p>
            <p className="text-white/70 text-xs mt-0.5">Two-Factor Verification</p>
          </div>

          <div className="px-6 py-7">
            <h1 className="text-lg font-bold text-cu-text mb-2 text-center">Enter Verification Code</h1>
            <p className="text-sm text-cu-muted text-center mb-6">Sent to {pending.email}</p>

            {notice && (
              <Alert variant="success" className="mb-5">
                {notice}
              </Alert>
            )}
            {error && (
              <Alert variant="error" className="mb-5">
                {error}
              </Alert>
            )}

            <div className="grid grid-cols-6 gap-2 mb-4">
              {digits.map((digit, index) => (
                <input
                  key={index}
                  ref={(node) => {
                    inputRefs.current[index] = node;
                  }}
                  value={digit}
                  inputMode="numeric"
                  pattern="[0-9]*"
                  maxLength={1}
                  autoComplete={index === 0 ? "one-time-code" : "off"}
                  aria-label={`Digit ${index + 1}`}
                  onChange={(event: ChangeEvent<HTMLInputElement>) => updateDigit(index, event.target.value)}
                  onPaste={(event) => {
                    event.preventDefault();
                    handlePaste(event.clipboardData.getData("text"));
                  }}
                  onKeyDown={(event) => handleKeyDown(index, event)}
                  className="h-12 w-full rounded-md border border-cu-border text-center text-lg font-semibold text-cu-text focus:outline-none focus:ring-2 focus:ring-cu-red focus:border-cu-red"
                />
              ))}
            </div>

            <div className="flex items-center justify-between text-xs text-cu-muted mb-5">
              <span>Expires in {formatSeconds(timeLeft)}</span>
              {remainingAttempts !== null && <span>{remainingAttempts} attempts left</span>}
            </div>

            <Button type="button" variant="primary" size="lg" fullWidth isLoading={isLoading} disabled={code.length !== CODE_LENGTH} onClick={submitCode}>
              Verify
            </Button>

            <div className="mt-4 flex items-center justify-between gap-3">
              <Button type="button" variant="ghost" size="sm" onClick={() => navigate("/admin/login", { replace: true })}>
                Back to Login
              </Button>
              <Button type="button" variant="secondary" size="sm" disabled={resendLeft > 0 || isLoading} onClick={handleResend}>
                {resendLeft > 0 ? `Resend ${resendLeft}s` : "Resend"}
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
