import React, { useState, useEffect } from "react";
import {
  X,
  Calendar as CalendarIcon,
  Sparkles,
  Trophy,
  ChevronLeft,
  ChevronRight,
  Clock,
  MapPin,
  Users,
  CheckCircle2,
  AlertCircle,
  BookOpen,
  Image as ImageIcon,
  PlusCircle,
  Smile,
  Heart,
  ExternalLink
} from "lucide-react";
import { api } from "../services/api";
import { CalendarResponse, CalendarDayData, SpecialMemoryItem } from "../types";

interface CalendarMemoriesModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenAddMemory?: () => void;
  onViewPhoto?: (url: string) => void;
}

const MONTHS = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December"
];

const currentYear = new Date().getFullYear();
const YEARS = [currentYear - 2, currentYear - 1, currentYear, currentYear + 1];

const WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export const CalendarMemoriesModal: React.FC<CalendarMemoriesModalProps> = ({
  isOpen,
  onClose,
  onOpenAddMemory,
  onViewPhoto,
}) => {
  if (!isOpen) return null;

  const now = new Date();
  const [activeTab, setActiveTab] = useState<"calendar" | "monthly" | "yearly">("calendar");
  const [selectedYear, setSelectedYear] = useState<number>(now.getFullYear());
  const [selectedMonth, setSelectedMonth] = useState<number>(now.getMonth() + 1); // 1-indexed
  const [data, setData] = useState<CalendarResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedDayNum, setSelectedDayNum] = useState<number>(now.getDate());

  const fetchCalendar = async (year: number, month: number) => {
    try {
      setLoading(true);
      const res = await api.getCalendarActivities(year, month);
      setData(res);
      // If the selected day doesn't exist in the month, default to 1st
      const daysCount = res.days.length;
      if (selectedDayNum > daysCount) {
        setSelectedDayNum(1);
      }
    } catch (err) {
      console.error("Failed to fetch calendar data:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (isOpen) {
      fetchCalendar(selectedYear, selectedMonth);
    }
  }, [isOpen, selectedYear, selectedMonth]);

  const handlePrevMonth = () => {
    if (selectedMonth === 1) {
      setSelectedMonth(12);
      setSelectedYear((prev) => prev - 1);
    } else {
      setSelectedMonth((prev) => prev - 1);
    }
  };

  const handleNextMonth = () => {
    if (selectedMonth === 12) {
      setSelectedMonth(1);
      setSelectedYear((prev) => prev + 1);
    } else {
      setSelectedMonth((prev) => prev + 1);
    }
  };

  // Find currently selected day object
  const currentDayData: CalendarDayData | undefined = data?.days.find(
    (d) => d.day === selectedDayNum
  );

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 md:p-6 bg-black/75 backdrop-blur-xs animate-fadeIn">
      {/* Outer Vintage Book Frame */}
      <div className="relative w-full max-w-5xl bg-[#fbf7ee] rounded-2xl shadow-2xl border-4 border-[#3d200e] overflow-hidden flex flex-col max-h-[92vh]">
        
        {/* Leather Top Header */}
        <div className="px-6 py-4 bg-[#3d200e] text-amber-100 flex items-center justify-between border-b-2 border-amber-900/50">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-800/80 border border-amber-600 flex items-center justify-center text-amber-300 shadow-inner">
              <CalendarIcon className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-xl font-bold font-serif-title tracking-wide text-amber-200">
                  Memories & Life Calendar
                </h2>
                <span className="px-2 py-0.5 rounded-full bg-amber-500/20 text-amber-300 text-[10px] font-semibold border border-amber-500/30">
                  {selectedYear}
                </span>
              </div>
              <p className="text-xs text-amber-300/70 font-handwriting">
                Chronicle of daily moments, monthly milestones & special annual memories
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-amber-300/80 hover:text-white hover:bg-black/30 transition-colors"
            title="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="px-6 pt-3 bg-[#f5ecda] border-b border-[#ddcdb6] flex items-center gap-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab("calendar")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-t-lg transition-colors border-t-2 ${
              activeTab === "calendar"
                ? "bg-[#fbf7ee] text-[#352010] border-amber-700 shadow-xs"
                : "text-[#785b41] border-transparent hover:text-[#352010]"
            }`}
          >
            <CalendarIcon className="w-4 h-4 text-amber-800" />
            <span>Daily Activity Calendar</span>
          </button>

          <button
            onClick={() => setActiveTab("monthly")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-t-lg transition-colors border-t-2 ${
              activeTab === "monthly"
                ? "bg-[#fbf7ee] text-[#352010] border-amber-700 shadow-xs"
                : "text-[#785b41] border-transparent hover:text-[#352010]"
            }`}
          >
            <Sparkles className="w-4 h-4 text-amber-600" />
            <span>Monthly Specials</span>
            {data && data.monthly_specials?.length > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-amber-600 text-white text-[10px] font-bold">
                {data.monthly_specials.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("yearly")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-t-lg transition-colors border-t-2 ${
              activeTab === "yearly"
                ? "bg-[#fbf7ee] text-[#352010] border-amber-700 shadow-xs"
                : "text-[#785b41] border-transparent hover:text-[#352010]"
            }`}
          >
            <Trophy className="w-4 h-4 text-yellow-600" />
            <span>Yearly Specials & Annual Story</span>
            {data && data.yearly_specials?.length > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-yellow-700 text-white text-[10px] font-bold">
                {data.yearly_specials.length}
              </span>
            )}
          </button>
        </div>

        {/* Year / Month Selector Bar */}
        <div className="px-6 py-2.5 bg-[#f0e4cf] border-b border-[#e0d0b8] flex flex-wrap items-center justify-between gap-3 text-xs">
          <div className="flex items-center gap-2">
            <button
              onClick={handlePrevMonth}
              className="p-1 rounded-md bg-[#e3d3bd] hover:bg-[#d5c2a7] text-[#4a321d] transition-colors"
              title="Previous Month"
            >
              <ChevronLeft className="w-4 h-4" />
            </button>

            {/* Month Dropdown */}
            <select
              value={selectedMonth}
              onChange={(e) => setSelectedMonth(Number(e.target.value))}
              className="px-3 py-1 rounded-md bg-white border border-[#c9b79c] font-bold text-[#352010] shadow-2xs focus:outline-hidden"
            >
              {MONTHS.map((m, idx) => (
                <option key={m} value={idx + 1}>
                  {m}
                </option>
              ))}
            </select>

            {/* Year Selector */}
            <select
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              className="px-3 py-1 rounded-md bg-white border border-[#c9b79c] font-bold text-[#352010] shadow-2xs focus:outline-hidden"
            >
              {YEARS.map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>

            <button
              onClick={handleNextMonth}
              className="p-1 rounded-md bg-[#e3d3bd] hover:bg-[#d5c2a7] text-[#4a321d] transition-colors"
              title="Next Month"
            >
              <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                setSelectedYear(2026);
                setSelectedMonth(9);
                setSelectedDayNum(10);
              }}
              className="px-2.5 py-1 rounded-md bg-amber-800 text-amber-100 hover:bg-amber-900 font-semibold shadow-2xs text-[11px] transition-colors"
            >
              Jump to September 10, 2026
            </button>
          </div>
        </div>

        {/* Modal Body */}
        <div className="flex-1 overflow-y-auto p-4 sm:p-6 bg-[#fbf7ee]">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-3 text-[#7a5e45]">
              <div className="w-8 h-8 border-3 border-amber-600 border-t-transparent rounded-full animate-spin" />
              <p className="font-serif-title font-medium">Unfolding memories calendar...</p>
            </div>
          ) : (
            <>
              {/* TAB 1: CALENDAR & DAILY ACTIVITIES */}
              {activeTab === "calendar" && data && (
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                  {/* Left Calendar Grid (7 cols) */}
                  <div className="lg:col-span-7 bg-[#f8f2e4] p-4 sm:p-5 rounded-2xl border border-[#ddcdb6] shadow-sm">
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="font-serif-title font-bold text-lg text-[#352010]">
                        {data.month_name} {data.year}
                      </h3>
                      <div className="flex items-center gap-3 text-[11px] text-[#785b41]">
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-emerald-600" />
                          Memory
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="w-2 h-2 rounded-full bg-amber-600" />
                          Task
                        </span>
                        <span className="flex items-center gap-1">
                          <span className="text-yellow-600 font-bold">⭐</span>
                          Special
                        </span>
                      </div>
                    </div>

                    {/* Weekday headers */}
                    <div className="grid grid-cols-7 gap-1.5 mb-2 text-center text-[11px] font-bold text-[#8a6849] uppercase tracking-wider">
                      {WEEKDAYS.map((day) => (
                        <div key={day} className="py-1">
                          {day}
                        </div>
                      ))}
                    </div>

                    {/* Days Grid */}
                    <div className="grid grid-cols-7 gap-1.5">
                      {/* Empty padding for first weekday (0 = Mon, 6 = Sun) */}
                      {Array.from({ length: data.first_weekday }).map((_, idx) => (
                        <div
                          key={`empty-${idx}`}
                          className="h-16 rounded-xl bg-transparent opacity-30 border border-transparent"
                        />
                      ))}

                      {/* Month Days */}
                      {data.days.map((dayObj) => {
                        const isSelected = selectedDayNum === dayObj.day;
                        return (
                          <div
                            key={`day-${dayObj.day}`}
                            onClick={() => setSelectedDayNum(dayObj.day)}
                            className={`h-16 sm:h-18 p-1.5 rounded-xl flex flex-col justify-between cursor-pointer transition-all border ${
                              isSelected
                                ? "bg-[#fff7e6] border-amber-600 shadow-md ring-2 ring-amber-600/30 transform -translate-y-0.5"
                                : dayObj.has_entry
                                ? "bg-white border-[#d8c7b0] hover:border-amber-400 hover:shadow-2xs"
                                : "bg-[#f3ead7]/60 border-[#e5d8c3] hover:bg-white hover:border-[#cbba9f]"
                            }`}
                          >
                            {/* Day Header */}
                            <div className="flex items-center justify-between">
                              <span
                                className={`text-xs font-bold leading-none ${
                                  isSelected
                                    ? "text-amber-900"
                                    : dayObj.has_entry
                                    ? "text-[#352010]"
                                    : "text-[#8a6849]"
                                }`}
                              >
                                {dayObj.day}
                              </span>

                              {dayObj.is_special && (
                                <span
                                  className="text-[11px] leading-none"
                                  title={dayObj.special_badge || "Special Day"}
                                >
                                  ⭐
                                </span>
                              )}
                            </div>

                            {/* Indicator Badges */}
                            <div className="space-y-1">
                              {dayObj.has_entry && (
                                <div className="flex items-center gap-1">
                                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 shrink-0" />
                                  <span className="text-[9px] font-semibold text-emerald-900 truncate">
                                    {dayObj.entries_count === 1
                                      ? "Story"
                                      : `${dayObj.entries_count} stories`}
                                  </span>
                                </div>
                              )}

                              {dayObj.commitments_count > 0 && (
                                <div className="flex items-center gap-1">
                                  <span className="w-1.5 h-1.5 rounded-full bg-amber-600 shrink-0" />
                                  <span className="text-[9px] font-medium text-amber-900 truncate">
                                    {dayObj.commitments_count} task
                                  </span>
                                </div>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Right Side Inspector: Activities for Selected Day */}
                  <div className="lg:col-span-5 bg-white p-5 rounded-2xl border border-[#ddcdb6] shadow-sm flex flex-col justify-between">
                    <div>
                      {/* Date Badge */}
                      <div className="border-b border-[#ebdcc4] pb-3 mb-4">
                        <span className="text-[10px] font-bold text-amber-800 uppercase tracking-widest">
                          Day Chronicle
                        </span>
                        <h4 className="text-xl font-serif-title font-bold text-[#352010]">
                          {data.month_name} {selectedDayNum}, {data.year}
                        </h4>
                        <p className="text-xs text-[#785b41] font-handwriting mt-0.5">
                          {currentDayData?.is_special
                            ? `✨ Special Milestone: ${currentDayData.special_badge}`
                            : currentDayData?.has_entry
                            ? "Documented life moments & commitments"
                            : "Quiet day in your journal"}
                        </p>
                      </div>

                      {/* Entries on this day */}
                      <div className="space-y-4 max-h-[50vh] overflow-y-auto pr-1">
                        {currentDayData && currentDayData.entries.length > 0 ? (
                          <div className="space-y-3">
                            <h5 className="text-xs font-bold uppercase tracking-wider text-[#785b41] flex items-center gap-1.5">
                              <BookOpen className="w-3.5 h-3.5 text-amber-700" />
                              Written Memories ({currentDayData.entries.length})
                            </h5>

                            {currentDayData.entries.map((entry) => (
                              <div
                                key={entry.id}
                                className="p-3.5 rounded-xl bg-[#fdfaf3] border border-[#e2d4be] space-y-2 relative shadow-2xs"
                              >
                                {entry.mood && (
                                  <span className="inline-block px-2 py-0.5 rounded-md bg-emerald-100 text-emerald-800 text-[10px] font-bold uppercase tracking-wider mr-2">
                                    {entry.mood}
                                  </span>
                                )}
                                <span className="inline-block px-2 py-0.5 rounded-md bg-[#ede0cb] text-[#543b23] text-[10px] font-semibold">
                                  {entry.category}
                                </span>

                                <h6 className="text-sm font-bold font-serif-title text-[#352010]">
                                  {entry.title}
                                </h6>

                                <p className="text-xs text-[#523d2b] leading-relaxed line-clamp-4">
                                  {entry.generated_content || entry.raw_text}
                                </p>

                                {/* Photos preview */}
                                {entry.photo_urls && entry.photo_urls.length > 0 && (
                                  <div className="flex gap-2 pt-1">
                                    {entry.photo_urls.map((photo, i) => (
                                      <img
                                        key={i}
                                        src={photo}
                                        alt="Day Memory"
                                        onClick={() => onViewPhoto && onViewPhoto(photo)}
                                        className="w-14 h-14 object-cover rounded-lg border border-[#c9b79c] cursor-pointer hover:opacity-90 shadow-2xs"
                                      />
                                    ))}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        ) : null}

                        {/* Commitments on this day */}
                        {currentDayData && currentDayData.commitments.length > 0 ? (
                          <div className="space-y-2 pt-2">
                            <h5 className="text-xs font-bold uppercase tracking-wider text-[#785b41] flex items-center gap-1.5">
                              <CheckCircle2 className="w-3.5 h-3.5 text-amber-700" />
                              Tasks & Commitments ({currentDayData.commitments.length})
                            </h5>

                            {currentDayData.commitments.map((c) => (
                              <div
                                key={c.id}
                                className="p-2.5 rounded-lg bg-[#fff9ee] border border-[#ebdcc4] flex items-start justify-between gap-2 text-xs"
                              >
                                <div>
                                  <p className="font-semibold text-[#352010]">{c.description}</p>
                                  <div className="flex flex-wrap items-center gap-1.5 mt-0.5">
                                    {c.project && (
                                      <span className="text-[10px] text-amber-800 font-medium">
                                        Project: {c.project}
                                      </span>
                                    )}
                                    {c.activity_thread && (
                                      <span className="px-1.5 py-0.2 rounded bg-amber-100 text-amber-800 text-[9px] font-semibold border border-amber-200">
                                        🧵 {c.activity_thread}
                                      </span>
                                    )}
                                  </div>
                                  {c.next_action && (
                                    <p className="text-[10px] text-amber-900 font-medium mt-1 bg-amber-50/80 px-1.5 py-0.5 rounded border border-amber-200/50">
                                      ⚡ Next: {c.next_action}
                                    </p>
                                  )}
                                </div>
                                <span
                                  className={`px-1.5 py-0.5 rounded text-[9px] font-bold shrink-0 ${
                                    c.status === "COMPLETED"
                                      ? "bg-emerald-100 text-emerald-800"
                                      : "bg-amber-200/70 text-amber-900"
                                  }`}
                                >
                                  {c.status}
                                </span>
                              </div>
                            ))}
                          </div>
                        ) : null}

                        {/* If nothing on this day */}
                        {(!currentDayData ||
                          (currentDayData.entries.length === 0 &&
                            currentDayData.commitments.length === 0)) && (
                          <div className="py-12 text-center text-[#8a6849] space-y-3">
                            <div className="w-12 h-12 rounded-full bg-[#f5ecda] border border-[#ddcdb6] flex items-center justify-center mx-auto text-[#6b4c33]">
                              <BookOpen className="w-6 h-6" />
                            </div>
                            <p className="text-sm font-serif-title font-medium">
                              No journal memories on this day.
                            </p>
                            <p className="text-xs text-[#8c6e51] font-handwriting max-w-xs mx-auto">
                              Every quiet day carries unseen reflections waiting to be captured.
                            </p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Bottom CTA to add memory */}
                    <div className="pt-4 mt-3 border-t border-[#ebdcc4] flex justify-end">
                      <button
                        onClick={() => {
                          onClose();
                          if (onOpenAddMemory) onOpenAddMemory();
                        }}
                        className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-amber-800 hover:bg-amber-900 text-white text-xs font-bold shadow-xs transition-colors"
                      >
                        <PlusCircle className="w-4 h-4" />
                        Write Memory For Today
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 2: MONTHLY SPECIALS */}
              {activeTab === "monthly" && data && (
                <div className="space-y-6">
                  <div className="flex items-center justify-between border-b border-[#e2d4be] pb-3">
                    <div>
                      <h3 className="font-serif-title font-bold text-xl text-[#352010]">
                        Curated Specials of {data.month_name} {data.year}
                      </h3>
                      <p className="text-xs text-[#785b41] font-handwriting mt-0.5">
                        Handpicked defining moments, hackathon milestones, and creative triumphs
                      </p>
                    </div>
                    <span className="px-3 py-1 rounded-full bg-amber-200 text-amber-900 text-xs font-bold border border-amber-300">
                      {data.monthly_specials.length} Highlight Moments
                    </span>
                  </div>

                  {/* Grid of Polaroid Special Cards */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {data.monthly_specials.map((special) => (
                      <div
                        key={special.id}
                        className="bg-white p-4 rounded-2xl border border-[#d5c3aa] shadow-md relative hover:shadow-lg transition-all group"
                      >
                        {/* Washi Tape Accent */}
                        <div className="washi-tape absolute -top-2.5 left-8 w-20 h-5 transform -rotate-1 rounded-xs border border-amber-900/10 shadow-2xs pointer-events-none" />

                        <div className="relative rounded-xl overflow-hidden mb-3.5 border border-[#dfd0ba]">
                          <img
                            src={special.photo_url}
                            alt={special.title}
                            className="w-full h-44 object-cover group-hover:scale-102 transition-transform duration-300"
                          />
                          <div className="absolute top-2 left-2 px-2.5 py-1 rounded-md bg-black/70 backdrop-blur-xs text-amber-200 text-[11px] font-bold shadow-xs">
                            {special.badge}
                          </div>
                          <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/60 text-white text-[10px]">
                            {special.category}
                          </div>
                        </div>

                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] font-bold text-amber-800 uppercase tracking-wider">
                              {special.date}
                            </span>
                            <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 text-[10px] font-bold capitalize">
                              {special.mood}
                            </span>
                          </div>

                          <h4 className="text-base font-bold font-serif-title text-[#352010]">
                            {special.title}
                          </h4>

                          <p className="text-xs text-[#543b23] leading-relaxed line-clamp-3">
                            {special.summary}
                          </p>

                          {special.people && special.people.length > 0 && (
                            <div className="flex items-center gap-1.5 pt-1 text-[11px] text-[#785b41]">
                              <Users className="w-3.5 h-3.5 text-amber-700" />
                              <span>With: </span>
                              <div className="flex flex-wrap gap-1">
                                {special.people.map((p, idx) => (
                                  <span
                                    key={idx}
                                    className="px-1.5 py-0.5 rounded bg-[#f3e7d5] text-[#4a321d] font-semibold text-[10px]"
                                  >
                                    {p}
                                  </span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB 3: YEARLY SPECIALS & ANNUAL STORY */}
              {activeTab === "yearly" && data && (
                <div className="space-y-6">
                  {/* Annual Story Reflection Banner */}
                  <div className="p-6 rounded-2xl bg-gradient-to-br from-[#3d200e] via-[#4d2811] to-[#301809] text-amber-100 border-2 border-amber-900/50 shadow-lg relative overflow-hidden">
                    <div className="relative z-10 max-w-3xl space-y-3">
                      <div className="flex items-center gap-2 text-amber-400">
                        <Trophy className="w-5 h-5" />
                        <span className="text-xs font-bold uppercase tracking-widest">
                          Annual Chronicle
                        </span>
                      </div>

                      <h3 className="text-2xl sm:text-3xl font-serif-title font-bold text-amber-200">
                        The Story of {selectedYear}
                      </h3>

                      <p className="text-sm sm:text-base leading-relaxed text-amber-100/90 font-handwriting italic">
                        "{data.annual_story}"
                      </p>
                    </div>

                    {/* Faded Background Decal */}
                    <div className="absolute -right-8 -bottom-8 opacity-10 pointer-events-none text-amber-200">
                      <Trophy className="w-48 h-48" />
                    </div>
                  </div>

                  {/* Yearly Milestones Header */}
                  <div className="flex items-center justify-between border-b border-[#e2d4be] pb-2 pt-2">
                    <h4 className="font-serif-title font-bold text-lg text-[#352010]">
                      Defining Milestones of {selectedYear}
                    </h4>
                    <span className="text-xs text-[#785b41] font-semibold">
                      {data.yearly_specials.length} Grand Highlights
                    </span>
                  </div>

                  {/* Grid of Yearly Specials */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {data.yearly_specials.map((item) => (
                      <div
                        key={item.id}
                        className="bg-white p-5 rounded-2xl border-2 border-[#ddcdb6] shadow-md flex flex-col justify-between hover:border-amber-600 transition-colors group"
                      >
                        <div>
                          <div className="relative rounded-xl overflow-hidden mb-3 border border-[#dfd0ba]">
                            <img
                              src={item.photo_url}
                              alt={item.title}
                              className="w-full h-44 object-cover group-hover:scale-102 transition-transform duration-300"
                            />
                            <div className="absolute top-2 left-2 px-2.5 py-1 rounded-md bg-amber-950/85 text-amber-200 text-xs font-bold border border-amber-700/50 shadow-xs">
                              {item.badge}
                            </div>
                            <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/60 text-white text-[10px]">
                              {item.category}
                            </div>
                          </div>

                          <div className="flex items-center justify-between text-xs text-[#8a6849] font-bold mb-1">
                            <span>{item.date}</span>
                            <span className="text-emerald-800 capitalize">{item.mood}</span>
                          </div>

                          <h5 className="text-base font-bold font-serif-title text-[#352010] mb-2">
                            {item.title}
                          </h5>

                          <p className="text-xs text-[#523d2b] leading-relaxed">
                            {item.summary}
                          </p>
                        </div>

                        {item.people && item.people.length > 0 && (
                          <div className="flex items-center gap-1.5 pt-3 mt-3 border-t border-[#eee2cf] text-[11px] text-[#785b41]">
                            <Users className="w-3.5 h-3.5 text-amber-700" />
                            <span>People: </span>
                            <div className="flex flex-wrap gap-1">
                              {item.people.map((p, i) => (
                                <span
                                  key={i}
                                  className="px-1.5 py-0.5 rounded bg-[#f5ecd8] text-[#3d2315] font-semibold text-[10px]"
                                >
                                  {p}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Vintage Stitched Bottom Footer */}
        <div className="px-6 py-3 bg-[#ede0cb] border-t border-[#d8c7b0] flex items-center justify-between text-xs text-[#785b41]">
          <span className="font-handwriting font-bold">
            LifeBook AI • Memories & Personal Chronicle
          </span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 rounded-lg bg-[#3d200e] text-amber-100 hover:bg-[#2c1508] font-bold transition-colors"
          >
            Close Book
          </button>
        </div>
      </div>
    </div>
  );
};
