import React from "react";
import {
  Home,
  BookOpen,
  PlusCircle,
  Bookmark,
  TrendingUp,
  Search,
  Shield,
  Settings,
  ShieldCheck,
  LogOut,
  X
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { UserAvatar } from "./UserAvatar";

interface LeatherSpineNavProps {
  currentTab: string;
  onSelectTab: (tab: string) => void;
  pendingCommitmentsCount: number;
  isOpenMobile?: boolean;
  onCloseMobile?: () => void;
  onOpenProfile?: () => void;
}

export const LeatherSpineNav: React.FC<LeatherSpineNavProps> = ({
  currentTab,
  onSelectTab,
  pendingCommitmentsCount,
  isOpenMobile = false,
  onCloseMobile,
  onOpenProfile
}) => {
  const { user, logout } = useAuth();

  const navItems = [
    { id: "today", label: "Today", icon: Home },
    { id: "memories", label: "Memories", icon: BookOpen },
    { id: "add_memory", label: "Add Memory", icon: PlusCircle },
    { id: "commitments", label: "Commitments", icon: Bookmark, badge: pendingCommitmentsCount > 0 ? pendingCommitmentsCount : undefined },
    { id: "insights", label: "Insights", icon: TrendingUp },
    { id: "ask_diary", label: "Ask My Diary", icon: Search },
    { id: "privacy", label: "Privacy", icon: Shield },
    { id: "settings", label: "Settings", icon: Settings },
  ];

  if (user?.role === "admin") {
    navItems.push({ id: "admin", label: "Admin Console", icon: ShieldCheck, badge: 0 });
  }

  const handleItemClick = (id: string) => {
    onSelectTab(id);
    if (onCloseMobile) {
      onCloseMobile();
    }
  };

  const renderNavContent = (isMobileDrawer = false) => (
    <div className="flex flex-col justify-between h-full py-8 px-4 relative z-10">
      <div>
        {/* Brand Header */}
        <div className="px-2 mb-8 flex items-start justify-between">
          <div>
            <div className="flex items-center gap-2.5 mb-1">
              <svg className="w-7 h-7 text-[#dfba78]" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                <path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z" />
                <path d="M6 6h10" />
                <path d="M6 10h8" />
              </svg>
              <h1 className="text-xl font-serif-title font-semibold tracking-wide text-[#f7eee1]">
                LifeBook AI
              </h1>
            </div>
            <p className="text-[12px] text-[#caa777] italic font-serif-title tracking-tight ml-1">
              Your life, remembered.
            </p>
          </div>

          {isMobileDrawer && (
            <button
              onClick={onCloseMobile}
              className="p-1 rounded-lg text-amber-200/80 hover:text-white hover:bg-black/30 md:hidden"
            >
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        {/* Navigation Items */}
        <nav className="space-y-1.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = currentTab === item.id;

            return (
              <button
                key={item.id}
                onClick={() => handleItemClick(item.id)}
                className={`w-full flex items-center justify-between px-3.5 py-2.5 rounded-xl transition-all cursor-pointer text-[13.5px] ${
                  isActive
                    ? "bg-[#ded0b6] text-[#2c180e] font-bold shadow-md"
                    : "text-[#dac6b3]/85 hover:text-[#fff4e3] hover:bg-white/5 font-normal"
                }`}
              >
                <div className="flex items-center gap-3">
                  <Icon className={`w-4 h-4 ${isActive ? "text-[#2e190f]" : "text-[#cbb092]"}`} />
                  <span className="tracking-tight">{item.label}</span>
                </div>

                {item.badge !== undefined && item.badge > 0 && (
                  <span className={`w-4 h-4 rounded-full text-[10px] font-bold flex items-center justify-center shadow-xs ${
                    isActive ? "bg-[#d93829] text-white" : "bg-[#d93829] text-white"
                  }`}>
                    {item.badge}
                  </span>
                )}
              </button>
            );
          })}
        </nav>
      </div>

      {/* Bottom Calligraphic Motto & Leaf Branch */}
      <div className="px-2 pt-6 border-t border-[#462717]/80">
        <div className="text-center">
          <p className="text-base text-[#dfba78] font-handwriting leading-snug tracking-wide italic">
            A Better You<br />
            A More Meaningful Tomorrow.
          </p>

          {/* Delicate Laurel / Leaf Sprig */}
          <div className="flex justify-center mt-2 opacity-85">
            <svg className="w-16 h-5 text-[#caa777]" viewBox="0 0 100 24" fill="currentColor">
              <path d="M10 12 C 25 6, 40 8, 50 12 C 60 8, 75 6, 90 12 C 75 14, 60 16, 50 12 C 40 16, 25 14, 10 12 Z" opacity="0.25" />
              <circle cx="28" cy="9" r="2" />
              <circle cx="42" cy="7" r="1.8" />
              <circle cx="58" cy="7" r="1.8" />
              <circle cx="72" cy="9" r="2" />
              <path d="M20 13 Q 50 8 80 13" stroke="currentColor" strokeWidth="1.2" fill="none" />
            </svg>
          </div>
        </div>

        {/* Small Profile Pill & Signout */}
        <div className="flex items-center justify-between mt-5 pt-3 border-t border-white/10 px-1">
          <div
            onClick={onOpenProfile}
            className="flex items-center gap-2 cursor-pointer hover:opacity-85 transition-opacity"
            title="Click to view & edit your profile"
          >
            <UserAvatar user={user} size="xs" />
            <span className="text-[11px] text-[#caa777] font-medium truncate max-w-[85px]" title={user?.full_name || user?.name || user?.email || "LifeBook User"}>
              {user?.full_name || user?.name || user?.email?.split("@")[0] || "User"}
            </span>
          </div>
          <button
            onClick={logout}
            title="Sign out"
            className="text-[#caa777]/70 hover:text-amber-200 transition-colors p-1 cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );

  return (
    <>
      {/* Desktop Leather Spine Navigation with stitched border */}
      <aside className="hidden md:block w-52 lg:w-56 shrink-0 relative z-20 leather-spine select-none border-r border-[#432313]">
        <div className="absolute inset-1.5 leather-stitch-border pointer-events-none rounded-lg" />
        {renderNavContent(false)}
      </aside>

      {/* Mobile Drawer Overlay */}
      {isOpenMobile && (
        <div className="fixed inset-0 z-50 md:hidden flex animate-fade-in">
          <div
            onClick={onCloseMobile}
            className="fixed inset-0 bg-black/80 backdrop-blur-xs"
          />
          <aside className="relative z-10 w-64 max-w-[85vw] h-full leather-spine text-amber-100 flex flex-col justify-between select-none shadow-2xl overflow-y-auto">
            {renderNavContent(true)}
          </aside>
        </div>
      )}
    </>
  );
};
