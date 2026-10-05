import React, { useState } from "react";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../services/api";
import {
  Eye,
  EyeOff,
  Sparkles,
  BookOpen,
  AlertCircle,
  CheckCircle2,
  ArrowRight
} from "lucide-react";

export const AuthScreen: React.FC = () => {
  const { login, register } = useAuth();

  const [mode, setMode] = useState<"login" | "register" | "forgot">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [name, setName] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Password strength check
  const hasMinLength = password.length >= 8;
  const hasLetter = /[A-Za-z]/.test(password);
  const hasNumberOrSymbol = /[0-9!@#$%^&*(),.?":{}|<>]/.test(password);
  const isPasswordStrong = hasMinLength && hasLetter && hasNumberOrSymbol;

  const handleQuickDemoLogin = async () => {
    setError(null);
    setLoading(true);
    try {
      await login("jothiram@lifebook.ai", "LifeBook2026!");
    } catch (err: any) {
      setError(err.message || "Demo sign in failed");
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccessMessage(null);

    if (!email.trim()) {
      setError("Please enter your email address");
      return;
    }

    if (mode === "login") {
      if (!password) {
        setError("Please enter your password");
        return;
      }
      setLoading(true);
      try {
        await login(email.trim(), password);
      } catch (err: any) {
        setError(err.message || "Invalid email or password");
      } finally {
        setLoading(false);
      }
    } else if (mode === "register") {
      if (!name.trim()) {
        setError("Please enter your full name");
        return;
      }
      if (!isPasswordStrong) {
        setError("Password must be at least 8 characters with a letter and a number or symbol");
        return;
      }
      if (password !== confirmPassword) {
        setError("Passwords do not match");
        return;
      }
      setLoading(true);
      try {
        await register(email.trim(), password, name.trim(), confirmPassword);
      } catch (err: any) {
        setError(err.message || "Registration failed. Please check your information.");
      } finally {
        setLoading(false);
      }
    } else if (mode === "forgot") {
      setLoading(true);
      try {
        const res = await api.forgotPassword(email.trim());
        setSuccessMessage(res.message);
      } catch (err: any) {
        setError(err.message || "Failed to process password reset");
      } finally {
        setLoading(false);
      }
    }
  };

  return (
    <div className="min-h-screen desk-surface text-[#2c2016] flex items-center justify-center p-3 sm:p-6 lg:p-10 font-sans antialiased relative overflow-hidden select-text">
      {/* Background Ambience Accessories */}
      <div className="hidden lg:block fixed top-8 right-12 z-10 pointer-events-none transform rotate-3">
        <div className="sticky-note p-3.5 w-40 rounded-xs text-center font-handwriting text-[#46331a] relative shadow-lg">
          <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 w-3.5 h-3.5 rounded-full bg-gradient-to-br from-amber-200 via-amber-400 to-amber-700 shadow-md border border-amber-900/40" />
          <p className="text-base font-bold leading-snug">
            "Your story deserves to be remembered."
          </p>
          <p className="text-sm font-bold mt-1">✨</p>
        </div>
      </div>

      <div className="hidden lg:flex fixed bottom-6 left-8 z-10 pointer-events-none items-end gap-0">
        <div className="transform -rotate-6 bg-[#f7eedc] p-2.5 pb-4 rounded-xs shadow-md border border-[#dfceb7] w-34 text-center font-handwriting text-[#4a341e] relative -mr-10 mb-1.5">
          <p className="text-xs font-bold leading-tight">
            Every Page<br />
            Has A<br />
            Beginning. :)
          </p>
        </div>
        <div className="w-28 h-28 rounded-full bg-gradient-to-br from-[#f5ede2] via-[#e8dcce] to-[#d8c8b5] p-2.5 shadow-[0_18px_38px_rgba(0,0,0,0.85),inset_0_2px_4px_rgba(255,255,255,0.7),inset_0_-2px_4px_rgba(0,0,0,0.18)] border-2 border-[#caa777]/60 flex items-center justify-center relative z-10 transition-transform duration-500 hover:scale-105">
          <img
            src="/assets/coffee_cup.png"
            alt="Coffee with latte art"
            className="w-full h-full object-contain rounded-full shadow-[0_6px_14px_rgba(0,0,0,0.25)]"
          />
        </div>
      </div>

      {/* Main Journal Authentication Book Cover */}
      <div className="w-full max-w-[840px] book-outer-casing rounded-2xl overflow-hidden leather-outer-frame flex flex-col md:flex-row relative z-20 my-auto shadow-2xl">
        
        {/* Left Leather Spine Section */}
        <div className="w-full md:w-72 leather-spine p-8 flex flex-col justify-between text-amber-100 relative border-b md:border-b-0 md:border-r border-[#432313] select-none">
          <div className="absolute inset-2 leather-stitch-border pointer-events-none rounded-lg" />
          
          <div className="relative z-10">
            {/* Logo */}
            <div className="flex items-center gap-3 mb-2">
              <svg className="w-8 h-8 text-[#dfba78]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z" />
                <path d="M6 6h10" />
                <path d="M6 10h8" />
              </svg>
              <h1 className="text-2xl font-serif-title font-semibold tracking-wide text-[#f8efe2]">
                LifeBook AI
              </h1>
            </div>
            <p className="text-xs text-[#caa777] italic font-serif-title tracking-tight ml-1">
              Your life, remembered.
            </p>

            <div className="mt-8 space-y-3">
              <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 text-xs text-[#eedec8] leading-relaxed">
                <p className="font-semibold text-[#f8efe2] mb-1">📖 Handcrafted Digital Diary</p>
                <p className="text-[11px] text-[#dac2a7]">
                  Multimodal memory capture, intelligent life insights, habits & commitments tracking.
                </p>
              </div>

              <div className="p-3.5 rounded-xl bg-white/5 border border-white/10 text-xs text-[#eedec8] leading-relaxed">
                <p className="font-semibold text-[#f8efe2] mb-1">🔒 Private & Secure</p>
                <p className="text-[11px] text-[#dac2a7]">
                  Every memory, person, place, and goal is isolated strictly to your account.
                </p>
              </div>
            </div>
          </div>

          <div className="relative z-10 mt-8 pt-4 border-t border-white/10 text-center">
            <p className="text-base text-[#dfba78] font-handwriting leading-snug tracking-wide italic">
              A Better You<br />
              A More Meaningful Tomorrow.
            </p>
          </div>
        </div>

        {/* Right Journal Paper Form Section */}
        <div className="flex-1 journal-left-page p-6 sm:p-10 flex flex-col justify-center">
          {/* Header */}
          <div className="mb-5">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl sm:text-3xl font-serif-title font-bold text-[#2a170f]">
                {mode === "login" && "Welcome back"}
                {mode === "register" && "Create your LifeBook"}
                {mode === "forgot" && "Reset Password"}
              </h2>
              <span className="text-amber-700 text-lg">✒️</span>
            </div>
            <p className="text-xs sm:text-sm text-[#725943] mt-1 font-serif-title">
              {mode === "login" && "Sign in to open your digital journal and memories."}
              {mode === "register" && "Begin recording your life stories, photos, and insights."}
              {mode === "forgot" && "Enter your email to receive secure recovery instructions."}
            </p>
          </div>

          {/* Error Banner */}
          {error && (
            <div className="mb-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-800 text-xs flex items-center gap-2 animate-in fade-in">
              <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
              <span>{error}</span>
            </div>
          )}

          {/* Success Banner */}
          {successMessage && (
            <div className="mb-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2 animate-in fade-in">
              <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
              <span>{successMessage}</span>
            </div>
          )}

          {/* Email / Password Form */}
          <form onSubmit={handleSubmit} className="space-y-3.5">
            {mode === "register" && (
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[#6b4f35] mb-1">
                  Full Name
                </label>
                <input
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Arun Sharma"
                  className="w-full px-3.5 py-2.5 bg-white/90 border border-[#dfd0bb] rounded-xl text-xs sm:text-sm text-[#2c190f] placeholder-[#a68c74] focus:outline-none focus:border-[#7d5635] shadow-2xs transition-colors"
                  required
                />
              </div>
            )}

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#6b4f35] mb-1">
                Email Address
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="name@example.com"
                className="w-full px-3.5 py-2.5 bg-white/90 border border-[#dfd0bb] rounded-xl text-xs sm:text-sm text-[#2c190f] placeholder-[#a68c74] focus:outline-none focus:border-[#7d5635] shadow-2xs transition-colors"
                required
              />
            </div>

            {mode !== "forgot" && (
              <div>
                <div className="flex items-center justify-between mb-1">
                  <label className="text-xs font-bold uppercase tracking-wider text-[#6b4f35]">
                    Password
                  </label>
                  {mode === "login" && (
                    <button
                      type="button"
                      onClick={() => {
                        setMode("forgot");
                        setError(null);
                        setSuccessMessage(null);
                      }}
                      className="text-[11px] text-[#8c6742] hover:text-[#381f10] hover:underline cursor-pointer"
                    >
                      Forgot password?
                    </button>
                  )}
                </div>
                <div className="relative">
                  <input
                    type={showPassword ? "text" : "password"}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••"
                    className="w-full px-3.5 py-2.5 pr-10 bg-white/90 border border-[#dfd0bb] rounded-xl text-xs sm:text-sm text-[#2c190f] placeholder-[#a68c74] focus:outline-none focus:border-[#7d5635] shadow-2xs transition-colors"
                    required
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-[#8c6742] hover:text-[#381f10] p-1 cursor-pointer"
                    title={showPassword ? "Hide password" : "Show password"}
                  >
                    {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                  </button>
                </div>
                {mode === "register" && (
                  <p className={`text-[10px] mt-1 ${isPasswordStrong ? "text-emerald-700" : "text-[#8a6849]"}`}>
                    Minimum 8 characters with at least one letter and one number or symbol.
                  </p>
                )}
              </div>
            )}

            {mode === "register" && (
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[#6b4f35] mb-1">
                  Confirm Password
                </label>
                <input
                  type={showPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full px-3.5 py-2.5 bg-white/90 border border-[#dfd0bb] rounded-xl text-xs sm:text-sm text-[#2c190f] placeholder-[#a68c74] focus:outline-none focus:border-[#7d5635] shadow-2xs transition-colors"
                  required
                />
              </div>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-2.5 px-4 bg-[#352012] hover:bg-[#251509] text-amber-100 font-bold text-xs sm:text-sm rounded-xl shadow-md transition-all active:scale-[0.99] flex items-center justify-center gap-2 cursor-pointer disabled:opacity-60 border border-[#52301a]"
            >
              {loading ? (
                <span>
                  {mode === "login" && "Signing in..."}
                  {mode === "register" && "Creating account..."}
                  {mode === "forgot" && "Sending reset link..."}
                </span>
              ) : (
                <>
                  <span>
                    {mode === "login" && "Sign In"}
                    {mode === "register" && "Create Account"}
                    {mode === "forgot" && "Send Reset Link"}
                  </span>
                  <ArrowRight className="w-4 h-4 text-amber-300" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Login Option */}
          {mode === "login" && (
            <div className="mt-3 text-center">
              <button
                type="button"
                onClick={handleQuickDemoLogin}
                className="text-[11px] font-semibold text-[#8c6742] hover:text-[#381f10] hover:underline cursor-pointer"
              >
                ⚡ Quick Demo Sign-in (Jothiram)
              </button>
            </div>
          )}

          {/* Mode Switchers */}
          <div className="mt-5 pt-3.5 border-t border-[#ebdcc4] text-center text-xs text-[#70553e]">
            {mode === "login" && (
              <p>
                Don't have an account?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setMode("register");
                    setError(null);
                    setSuccessMessage(null);
                  }}
                  className="font-bold text-[#352012] hover:underline cursor-pointer ml-1"
                >
                  Create account
                </button>
              </p>
            )}

            {mode === "register" && (
              <p>
                Already have a LifeBook?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setMode("login");
                    setError(null);
                    setSuccessMessage(null);
                  }}
                  className="font-bold text-[#352012] hover:underline cursor-pointer ml-1"
                >
                  Sign in
                </button>
              </p>
            )}

            {mode === "forgot" && (
              <p>
                Remembered your password?{" "}
                <button
                  type="button"
                  onClick={() => {
                    setMode("login");
                    setError(null);
                    setSuccessMessage(null);
                  }}
                  className="font-bold text-[#352012] hover:underline cursor-pointer ml-1"
                >
                  Back to Sign In
                </button>
              </p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};
