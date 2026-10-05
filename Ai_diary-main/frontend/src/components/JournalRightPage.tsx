import React from "react";
import {
  Search,
  Bell,
  Calendar,
  Utensils,
  BookOpen,
  Send,
  Briefcase,
  MoreVertical,
  RotateCw,
  Bookmark
} from "lucide-react";
import { Commitment, Routine, NotificationItem, User } from "../types";
import { UserAvatar } from "./UserAvatar";

interface JournalRightPageProps {
  user: User | null;
  searchQuery: string;
  onSearchChange: (q: string) => void;
  pendingCommitments: Commitment[];
  routines?: Routine[];
  onMarkDone: (id: string) => void;
  onViewAllCommitments: () => void;
  onViewAllRoutines: () => void;
  notifications: NotificationItem[];
  showNotifications: boolean;
  onToggleNotifications: () => void;
  onMarkNotificationRead?: (id: string) => void;
  onMarkAllNotificationsRead?: () => void;
  onDismissNotification?: (id: string) => void;
  selectedMood: string;
  onSelectMood: (m: string) => void;
  onOpenPhotos?: () => void;
  onOpenCalendar?: () => void;
  onThisDay?: any;
  onOpenProfile?: () => void;
}

export const JournalRightPage: React.FC<JournalRightPageProps> = ({
  user,
  searchQuery,
  onSearchChange,
  pendingCommitments,
  routines = [],
  onMarkDone,
  onViewAllCommitments,
  onViewAllRoutines,
  notifications,
  showNotifications,
  onToggleNotifications,
  onMarkNotificationRead,
  onMarkAllNotificationsRead,
  onDismissNotification,
  selectedMood,
  onSelectMood,
  onOpenPhotos,
  onOpenCalendar,
  onThisDay,
  onOpenProfile,
}) => {
  const unreadCount = notifications.filter((n) => !n.is_read).length;

  return (
    <section className="flex-1 p-5 sm:p-7 md:p-8 lg:p-9 space-y-6 overflow-y-auto">
      {/* Top Search Bar, Notification & User Avatar */}
      <div className="flex items-center justify-between gap-3 pb-2">
        {/* Pill Search Input */}
        <div className="flex-1 relative max-w-md">
          <Search className="w-4 h-4 text-[#9c826b] absolute left-3.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => onSearchChange(e.target.value)}
            placeholder="Search your memories..."
            className="w-full pl-10 pr-4 py-2 bg-white/90 border border-[#ded1be] rounded-full text-xs text-[#2c190f] placeholder-[#9c826b] focus:outline-none focus:border-[#825c38] shadow-2xs transition-all"
          />
        </div>

        {/* Notification Bell */}
        <div className="relative">
          <button
            onClick={onToggleNotifications}
            className="p-2 rounded-full hover:bg-[#ede1ce] text-[#694c34] transition-colors relative cursor-pointer"
            title="Notifications & Reminders"
          >
            <Bell className="w-5 h-5" />
            {unreadCount > 0 && (
              <span className="absolute top-1 right-1 min-w-[16px] h-4 px-1 bg-[#d93829] text-white text-[9px] font-bold rounded-full flex items-center justify-center ring-2 ring-[#faf5eb] shadow-xs">
                {unreadCount > 9 ? "9+" : unreadCount}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="absolute right-0 top-11 w-80 bg-white rounded-2xl shadow-2xl border border-[#d5c2a7] p-3.5 z-40 space-y-2.5 animate-in fade-in">
              <div className="flex items-center justify-between border-b border-[#ebdcc4] pb-2">
                <div className="flex items-center gap-1.5">
                  <h4 className="text-xs font-bold text-[#352010]">Notifications & Alerts</h4>
                  {unreadCount > 0 && (
                    <span className="px-1.5 py-0.5 rounded-full bg-red-100 text-red-700 text-[10px] font-bold">
                      {unreadCount} new
                    </span>
                  )}
                </div>
                {unreadCount > 0 && onMarkAllNotificationsRead && (
                  <button
                    onClick={onMarkAllNotificationsRead}
                    className="text-[10px] font-semibold text-[#8c6742] hover:text-[#381f10] hover:underline cursor-pointer"
                  >
                    Mark all read
                  </button>
                )}
              </div>

              <div className="max-h-64 overflow-y-auto space-y-2 pr-0.5">
                {notifications.length > 0 ? (
                  notifications.map((n) => {
                    const isUnread = !n.is_read;
                    const stage = n.metadata_json?.reminder_stage || "";
                    const priority = n.metadata_json?.priority || "";
                    const isHighPriority = priority === "high" || stage === "overdue" || stage === "due";

                    return (
                      <div
                        key={n.id}
                        className={`text-xs p-2.5 rounded-xl border transition-all ${
                          isUnread
                            ? isHighPriority
                              ? "bg-red-50/70 border-red-200 shadow-2xs"
                              : "bg-amber-50/80 border-amber-200 shadow-2xs"
                            : "bg-zinc-50 border-zinc-200 opacity-75"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-1.5">
                          <div className="flex-1">
                            <div className="flex items-center gap-1.5 mb-0.5">
                              {stage === "overdue" && (
                                <span className="px-1.5 py-0.2 rounded bg-red-600 text-white text-[9px] font-bold uppercase">
                                  Overdue
                                </span>
                              )}
                              {stage === "due" && (
                                <span className="px-1.5 py-0.2 rounded bg-amber-600 text-white text-[9px] font-bold uppercase">
                                  Due Soon
                                </span>
                              )}
                              {stage === "upcoming" && (
                                <span className="px-1.5 py-0.2 rounded bg-blue-600 text-white text-[9px] font-bold uppercase">
                                  Upcoming
                                </span>
                              )}
                              <p className="font-semibold text-[#2f1b0e] leading-snug">{n.title}</p>
                            </div>
                            <p className="text-[11px] text-[#5e442d] leading-normal">{n.message}</p>
                          </div>

                          <div className="flex items-center gap-1 shrink-0">
                            {isUnread && onMarkNotificationRead && (
                              <button
                                onClick={() => onMarkNotificationRead(n.id)}
                                title="Mark as read"
                                className="text-[10px] px-1.5 py-0.5 rounded bg-white border border-[#d8c5aa] text-[#5e442d] hover:bg-[#f2e7d5] cursor-pointer"
                              >
                                Read
                              </button>
                            )}
                            {onDismissNotification && (
                              <button
                                onClick={() => onDismissNotification(n.id)}
                                title="Dismiss"
                                className="text-zinc-400 hover:text-red-600 p-0.5 cursor-pointer text-xs"
                              >
                                ×
                              </button>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <p className="text-xs text-zinc-500 italic p-3 text-center">
                    All caught up! No pending notifications.
                  </p>
                )}
              </div>
            </div>
          )}
        </div>

        {/* User's Avatar Badge (Letter or Custom Photo) */}
        <UserAvatar
          user={user}
          size="md"
          onClick={onOpenProfile}
          title="Click to view & edit your profile"
        />
      </div>

      {/* "Things that need your attention" Section */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-amber-800 text-sm">📌</span>
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#7e6248]">
              Things that need your attention
            </h3>
            {pendingCommitments.length > 0 && (
              <span className="w-4 h-4 rounded-full bg-[#d93829] text-white text-[10px] font-bold flex items-center justify-center shadow-xs">
                {pendingCommitments.length}
              </span>
            )}
          </div>
          <button
            onClick={onViewAllCommitments}
            className="text-xs font-semibold text-[#8a6849] hover:text-[#311c0f] transition-colors cursor-pointer"
          >
            View all →
          </button>
        </div>

        {pendingCommitments.length === 0 ? (
          <div className="bg-[#faf6ee] border border-dashed border-[#d8c7ad] rounded-xl p-5 text-center">
            <Bookmark className="w-5 h-5 text-[#9a785b] mx-auto mb-1.5 opacity-60" />
            <p className="text-xs font-semibold text-[#4a3525]">No pending commitments</p>
            <p className="text-[11px] text-[#7d6550] mt-0.5">
              As you write your diary entries, LifeBook automatically detects promises, meetings, and tasks.
            </p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {pendingCommitments.slice(0, 3).map((comm, idx) => {
              const isRed = idx === 0;
              return (
                <div
                  key={comm.id}
                  className={`p-3.5 rounded-xl border flex items-center justify-between gap-3 transition-all ${
                    isRed
                      ? "bg-[#fef2f0] border-[#fbd4ce]"
                      : "bg-[#fdf7ed] border-[#f5e3c8]"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 mt-0.5 ${
                        isRed ? "bg-[#fde2dd] text-[#cf3827]" : "bg-[#fcedd7] text-[#b87628]"
                      }`}
                    >
                      {isRed ? (
                        <Send className="w-3.5 h-3.5" />
                      ) : (
                        <Briefcase className="w-3.5 h-3.5" />
                      )}
                    </div>
                    <div>
                      <h4 className="text-xs font-bold text-[#2a170f]">
                        {comm.description}
                      </h4>
                      {comm.project && (
                        <p className="text-[11px] text-[#705545] mt-0.5">
                          {comm.project}
                        </p>
                      )}
                      {comm.due_date && (
                        <div className="flex items-center gap-1 text-[10px] font-semibold mt-1">
                          <Calendar
                            className={`w-3 h-3 ${isRed ? "text-[#cf3827]" : "text-[#705545]"}`}
                          />
                          <span className={isRed ? "text-[#cf3827]" : "text-[#705545]"}>
                            {comm.due_date}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>

                  <div className="flex items-center gap-1.5 shrink-0">
                    <button
                      onClick={() => onMarkDone(comm.id)}
                      className="px-3 py-1 bg-white hover:bg-emerald-50 text-[#301d12] hover:text-emerald-800 text-xs font-semibold rounded-full border border-[#ded0be] shadow-2xs transition-colors cursor-pointer"
                    >
                      Mark Done
                    </button>
                    <button className="text-[#967d66] hover:text-[#352010] p-1 cursor-pointer">
                      <MoreVertical className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* "Your Routines" Section */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="text-emerald-800 text-sm">🌱</span>
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#7e6248]">
              Your routines
            </h3>
          </div>
          <button
            onClick={onViewAllRoutines}
            className="text-xs font-semibold text-[#8a6849] hover:text-[#311c0f] transition-colors cursor-pointer"
          >
            View all →
          </button>
        </div>

        {routines && routines.length > 0 ? (
          <div className="bg-[#f0f6ef] border border-[#cfdfce] rounded-2xl p-4 shadow-xs space-y-3">
            {/* Main Routine Row */}
            <div className="flex items-center justify-between gap-3">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-[#d7ecd7] text-[#2b6d39] flex items-center justify-center shrink-0">
                  <Utensils className="w-5 h-5" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#223922]">
                    {routines[0].title}
                  </h4>
                  <p className="text-[11px] text-[#486248]">
                    {routines[0].location || routines[0].activity} {routines[0].details ? `• ${routines[0].details}` : ""}
                  </p>
                  <p className="text-[10px] text-[#5e7c5e] font-medium mt-0.5 flex items-center gap-1">
                    <RotateCw className="w-2.5 h-2.5" />
                    <span>{routines[0].occurrence_count || 1} occurrences observed</span>
                  </p>
                </div>
              </div>

              {/* Confidence Circular Gauge */}
              <div className="w-[52px] h-[52px] rounded-full border-[3px] border-[#3b7b54] bg-white flex flex-col items-center justify-center shadow-xs shrink-0">
                <span className="text-xs font-bold text-[#223922] leading-none">
                  {Math.round((routines[0].confidence || 0.85) * 100)}%
                </span>
                <span className="text-[7.5px] font-bold text-[#486248] uppercase tracking-tight mt-0.5 leading-none">
                  Confidence
                </span>
              </div>
            </div>

            {/* Connected Deviation Sub-Card if prompt exists */}
            {routines[0].deviation_prompt && (
              <div
                onClick={onViewAllRoutines}
                className="pt-2 border-t border-dashed border-[#b6cdb4] flex items-start gap-2.5 cursor-pointer hover:opacity-90 transition-opacity"
              >
                <div className="w-6 h-6 rounded-md bg-[#e3eedf] text-[#3b7b54] flex items-center justify-center shrink-0 mt-0.5">
                  <BookOpen className="w-3.5 h-3.5" />
                </div>
                <div>
                  <p className="text-xs font-bold text-[#243a24]">
                    Deviation Noticed
                  </p>
                  <p className="text-[11px] text-[#486248] leading-relaxed mt-0.5">
                    {routines[0].deviation_prompt}
                  </p>
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="bg-[#f0f6ef] border border-[#cfdfce] rounded-2xl p-5 text-center">
            <div className="w-10 h-10 rounded-full bg-[#d7ecd7] text-[#2b6d39] flex items-center justify-center mx-auto mb-2">
              <RotateCw className="w-5 h-5" />
            </div>
            <p className="text-xs font-bold text-[#223922]">Learning Your Natural Rhythms</p>
            <p className="text-[11px] text-[#486248] mt-1 leading-relaxed max-w-sm mx-auto">
              LifeBook automatically discovers recurring habits, favorite spots, and routines as you add your memories over time.
            </p>
          </div>
        )}
      </div>

      {/* "On This Day" Section */}
      <div className="space-y-2.5">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <BookOpen className="w-3.5 h-3.5 text-[#8a6849]" />
            <h3 className="text-xs font-bold uppercase tracking-wider text-[#7e6248]">
              On This Day
            </h3>
          </div>
          <button
            onClick={onOpenCalendar}
            className="text-xs font-semibold text-[#8a6849] hover:text-[#311c0f] transition-colors cursor-pointer"
          >
            View more →
          </button>
        </div>

        {onThisDay ? (
          <div
            onClick={onOpenCalendar}
            className="bg-[#fcf8f0] border border-[#e2d4be] rounded-2xl p-4 shadow-xs flex flex-col sm:flex-row gap-4 items-center cursor-pointer hover:border-[#caa777] transition-all"
          >
            {/* Polaroid Frame */}
            <div className="polaroid-frame shrink-0 w-32 sm:w-36 transform rotate-1 relative">
              <img
                src={onThisDay.photo_url || "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?w=300&auto=format&fit=crop&q=80"}
                alt={onThisDay.title || "Memory"}
                className="w-full h-22 object-cover rounded-xs"
              />
              <p className="text-[11px] font-handwriting text-center text-[#543b23] mt-1 font-bold truncate px-1">
                {onThisDay.title || "A Look Back"}
              </p>
            </div>

            {/* Excerpt */}
            <div className="flex-1 space-y-1">
              <p className="text-[10px] font-bold text-[#8c6f56] uppercase tracking-wider">
                {onThisDay.entry_date ? new Date(onThisDay.entry_date).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" }) : "Anniversary"}
              </p>
              <h4 className="text-sm font-serif-title font-bold text-[#2a170f]">
                {onThisDay.title || "Past Memory"}
              </h4>
              <p className="text-xs text-[#523d2b] leading-relaxed font-serif-title line-clamp-2">
                {onThisDay.snippet || onThisDay.generated_content || onThisDay.raw_text || "Reflecting back on this day in your journey."}
              </p>
              <div className="pt-1">
                <span className="px-2 py-0.5 rounded-md bg-[#ebdcc4] text-[#523d2b] text-[10px] font-medium">
                  {onThisDay.category || "Personal"}
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div
            onClick={onOpenCalendar}
            className="bg-[#fcf8f0] border border-dashed border-[#e2d4be] rounded-2xl p-5 text-center cursor-pointer hover:border-[#caa777] transition-all"
          >
            <Calendar className="w-5 h-5 text-[#9a785b] mx-auto mb-1.5 opacity-60" />
            <p className="text-xs font-semibold text-[#4a3525]">No memories on this calendar date yet</p>
            <p className="text-[11px] text-[#7d6550] mt-0.5">
              As the years go by, memories you write today will resurface here on this exact day.
            </p>
          </div>
        )}
      </div>
    </section>
  );
};
