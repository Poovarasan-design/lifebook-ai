import React from "react";
import { Sparkles, BookOpen } from "lucide-react";

interface CinematicLoaderProps {
  message?: string;
  submessage?: string;
}

export const CinematicLoader: React.FC<CinematicLoaderProps> = ({
  message = "Opening your personal LifeBook...",
  submessage = "Gathering your memories, reflections, and insights"
}) => {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center overflow-hidden bg-[#180e08] select-none">
      {/* Background Ambient Glow & Vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,rgba(110,65,35,0.45)_0%,rgba(20,11,6,0.95)_75%,#0c0603_100%)] pointer-events-none" />
      
      {/* Subtle Star / Dust Sparkles */}
      <div className="absolute inset-0 bg-[radial-gradient(#d4af37_1px,transparent_1px)] [background-size:32px_32px] opacity-15 pointer-events-none" />

      {/* Main Cinematic Container */}
      <div className="relative z-10 flex flex-col items-center max-w-md px-6 text-center">
        
        {/* Animated Ornate Book & Compass Emblem */}
        <div className="relative w-28 h-28 mb-8 flex items-center justify-center">
          
          {/* Outer Pulsing Golden Ring */}
          <div className="absolute inset-0 rounded-full border border-amber-500/25 animate-ping opacity-30" />
          
          {/* Rotating Celestial Astrolabe Ring */}
          <div className="absolute inset-1 rounded-full border border-dashed border-amber-400/40 animate-[spin_12s_linear_infinite]" />
          
          {/* Reverse Rotating Inner Ring */}
          <div className="absolute inset-3 rounded-full border-2 border-t-amber-300 border-r-transparent border-b-amber-600/50 border-l-transparent animate-[spin_6s_linear_infinite_reverse]" />

          {/* Central Glowing Medallion */}
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-[#3b2011] via-[#24130a] to-[#120804] border-2 border-amber-400/60 shadow-[0_0_35px_rgba(223,186,120,0.35)] flex items-center justify-center transform transition-transform duration-700 animate-pulse">
            <svg
              className="w-8 h-8 text-[#dfba78] drop-shadow-[0_2px_8px_rgba(223,186,120,0.6)]"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
            >
              <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z" />
              <path d="M6 6h10" />
              <path d="M6 10h8" />
              <circle cx="12" cy="15" r="1.5" fill="currentColor" opacity="0.8" />
            </svg>
          </div>

          {/* Floating Stardust Accent */}
          <div className="absolute -top-1 -right-1 text-amber-300 animate-bounce">
            <Sparkles className="w-4 h-4" />
          </div>
        </div>

        {/* Brand Title */}
        <div className="mb-2">
          <h1 className="text-2xl sm:text-3xl font-serif-title font-semibold tracking-wider text-[#fcf5eb] drop-shadow-md">
            LifeBook AI
          </h1>
          <p className="text-xs text-[#caa777] font-serif-title italic tracking-wide mt-0.5">
            Your life, remembered.
          </p>
        </div>

        {/* Dynamic Status Text */}
        <div className="mt-4 mb-6">
          <p className="text-sm font-medium text-[#ebd7be] tracking-wide animate-pulse">
            {message}
          </p>
          <p className="text-[11px] text-[#a88d71] italic mt-1 max-w-xs leading-relaxed">
            {submessage}
          </p>
        </div>

        {/* Luxury Gold Shimmer Progress Bar */}
        <div className="w-48 h-1 bg-[#2c1a11] rounded-full overflow-hidden border border-amber-900/40 relative">
          <div className="absolute inset-y-0 left-0 bg-gradient-to-r from-amber-600 via-amber-300 to-amber-600 rounded-full w-24 animate-[shimmer_1.8s_ease-in-out_infinite]" />
        </div>

        {/* Bottom Inspirational Motto */}
        <p className="text-xs text-[#dfba78]/70 font-handwriting tracking-wide mt-8 italic">
          "Every day is a page in the history of you."
        </p>
      </div>
    </div>
  );
};
