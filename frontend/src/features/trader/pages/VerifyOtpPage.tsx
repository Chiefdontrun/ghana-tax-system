import { ChangeEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import { Alert, Button } from "@/components/ui";
import { useTraderAuth } from "../hooks/useTraderAuth";

const CODE_LENGTH = 6;
const RESEND_COOLDOWN_SECONDS = 60;
const OTP_EXPIRY_MINUTES = 5;

function secondsLeft(until: number) {
  return Math.max(0, Math.ceil((until - Date.now()) / 1000));
}

function formatSeconds(total: number) {
  const minutes = Math.floor(total / 60).toString().padStart(2, "0");
  const seconds = (total % 60).toString().padStart(2, "0");
  return `${minutes}:${seconds}`;
}

export default function VerifyOtpPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const phoneNumber = (location.state as { phone_number?: string } | null)?.phone_number;

  const { verifyOtp, requestOtp, isLoading, error } = useTraderAuth();
  
  const [digits, setDigits] = useState(Array(CODE_LENGTH).fill(""));
  const [timeLeft, setTimeLeft] = useState(OTP_EXPIRY_MINUTES * 60);
  const [resendLeft, setResendLeft] = useState(RESEND_COOLDOWN_SECONDS);
  const [notice, setNotice] = useState<string | null>(null);
  
  const inputRefs = useRef<Array<HTMLInputElement | null>>([]);
  const expiryTimeRef = useRef<number>(Date.now() + OTP_EXPIRY_MINUTES * 60 * 1000);

  useEffect(() => {
    if (!phoneNumber) {
      navigate("/trader/login", { replace: true, state: { message: "Please enter your phone number first." } });
      return;
    }

    const tick = () => {
      const remaining = secondsLeft(expiryTimeRef.current);
      setTimeLeft(remaining);
      setResendLeft((current) => Math.max(0, current - 1));
      if (remaining <= 0) {
        navigate("/trader/login", { replace: true, state: { message: "Verification expired. Please sign in again." } });
      }
    };

    tick();
    const timer = window.setInterval(tick, 1000);
    inputRefs.current[0]?.focus();
    return () => window.clearInterval(timer);
  }, [navigate, phoneNumber]);

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
    if (code.length !== CODE_LENGTH || !phoneNumber) return;
    
    try {
      await verifyOtp(phoneNumber, code);
      // Navigation is handled in hook
    } catch (err: any) {
      // remaining attempts would be read from err if backend returns it
      // B1's backend ValidationError could include `remaining_attempts` 
      // but if we are generic, we just display the error.
    }
  };

  const handleResend = async () => {
    if (!phoneNumber) return;
    await requestOtp(phoneNumber);
    setDigits(Array(CODE_LENGTH).fill(""));
    setNotice("A new verification code has been sent.");
    setResendLeft(RESEND_COOLDOWN_SECONDS);
    
    // Reset expiry timer since a new code was generated
    expiryTimeRef.current = Date.now() + OTP_EXPIRY_MINUTES * 60 * 1000;
    setTimeLeft(OTP_EXPIRY_MINUTES * 60);
    
    inputRefs.current[0]?.focus();
  };

  if (!phoneNumber) return null;

  return (
    <div className="min-h-screen bg-cu-bg flex items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="bg-white rounded-xl border border-cu-border shadow-card-md overflow-hidden">
          <div className="bg-cu-red px-6 py-5 text-center">
            <p className="text-white font-bold text-sm tracking-wide leading-tight">DISTRICT ASSEMBLY - REVENUE UNIT</p>
            <p className="text-white/70 text-xs mt-0.5">Trader Portal Verification</p>
          </div>

          <div className="px-6 py-7">
            <h1 className="text-lg font-bold text-cu-text mb-2 text-center">Enter Verification Code</h1>
            <p className="text-sm text-cu-muted text-center mb-6">Sent to {phoneNumber}</p>

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
            </div>

            <Button type="button" variant="primary" size="lg" fullWidth isLoading={isLoading} disabled={code.length !== CODE_LENGTH} onClick={submitCode}>
              Verify
            </Button>

            <div className="mt-4 flex items-center justify-between gap-3">
              <Button type="button" variant="ghost" size="sm" onClick={() => navigate("/trader/login", { replace: true })}>
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
