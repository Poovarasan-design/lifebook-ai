import React, { useState, useEffect } from "react";
import { User } from "../types";

interface UserAvatarProps {
  user?: User | null;
  name?: string;
  avatarUrl?: string | null;
  size?: "xs" | "sm" | "md" | "lg" | "xl";
  className?: string;
  onClick?: () => void;
  title?: string;
}

const sizeClasses = {
  xs: "w-6 h-6 text-xs",
  sm: "w-8 h-8 text-sm",
  md: "w-9 h-9 text-base",
  lg: "w-12 h-12 text-xl",
  xl: "w-20 h-20 text-3xl"
};

export const UserAvatar: React.FC<UserAvatarProps> = ({
  user,
  name,
  avatarUrl,
  size = "md",
  className = "",
  onClick,
  title
}) => {
  const [imageError, setImageError] = useState(false);

  const resolvedName = name || user?.full_name || user?.name || user?.email || "User";
  const initial = resolvedName.trim().charAt(0).toUpperCase() || "U";
  const effectiveAvatar = avatarUrl !== undefined ? avatarUrl : user?.avatar_url;

  useEffect(() => {
    setImageError(false);
  }, [effectiveAvatar]);

  const showImage = effectiveAvatar && !imageError;

  return (
    <div
      onClick={onClick}
      title={title || resolvedName}
      className={`rounded-full shrink-0 select-none flex items-center justify-center overflow-hidden border-2 border-[#caa777] shadow-sm transition-transform ${
        onClick ? "cursor-pointer hover:scale-105" : ""
      } ${sizeClasses[size]} ${className}`}
    >
      {showImage ? (
        <img
          src={effectiveAvatar}
          alt={resolvedName}
          className="w-full h-full object-cover"
          onError={() => setImageError(true)}
        />
      ) : (
        <div className="w-full h-full bg-gradient-to-br from-[#733f1f] via-[#522911] to-[#2a1306] flex items-center justify-center font-serif-title font-bold text-[#fde68a] shadow-[inset_0_1px_2px_rgba(255,255,255,0.25)]">
          <span>{initial}</span>
        </div>
      )}
    </div>
  );
};
