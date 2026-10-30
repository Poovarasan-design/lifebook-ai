import React from "react";
import {
  Mic,
  PenTool,
  Image as ImageIcon,
  Edit2,
  MapPin,
  User as UserIcon,
  Briefcase,
  Utensils,
  Lightbulb,
  BookOpen,
  Sparkles,
  Calendar,
  MoreHorizontal
} from "lucide-react";
import { DiaryEntry, User } from "../types";
import { ProcessingTracker } from "./ProcessingTracker";

interface JournalLeftPageProps {
  user: User | null;
  activeEntry: DiaryEntry | null;
  onOpenVoice: () => void;
  onOpenText: () => void;
  onOpenPhoto: () => void;
  onOpenReview: () => void;
  onTellMeMore: () => void;
  onRetryProcessing?: () => void;
  onRegenerate?: (tone?: string) => Promise<void> | void;
  isRegenerating?: boolean;
  onOpenPhotos?: () => void;
  onOpenGraph?: () => void;
  onOpenCalendar?: () => void;
}

export const JournalLeftPage: React.FC<JournalLeftPageProps> = ({
  user,
  activeEntry,
  onOpenVoice,
  onOpenText,
  onOpenPhoto,
  onOpenReview,
  onTellMeMore,
  onRetryProcessing,
  onRegenerate,
  isRegenerating = false,
  onOpenPhotos,
  onOpenGraph,
  onOpenCalendar,
}) => {
  const firstName = user?.full_name?.split(" ")[0] || "Friend";
  const today = new Date();
  const dayName = today.toLocaleDateString("en-US", { weekday: "long" });
  const formattedDate = today.toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" });
  const currentHour = today.getHours();
  const greetingTime = currentHour < 12 ? "Good morning" : currentHour < 17 ? "Good afternoon" : "Good evening";

  const entryEntities = (activeEntry as any)?.entities || {};
  const people: string[] = entryEntities.people || [];
  const places: string[] = entryEntities.places || [];
  const activities: string[] = entryEntities.activities || [];
  const hasExtractedEntities = people.length > 0 || places.length > 0 || activities.length > 0;

  return (
    <section className="flex-1 p-5 sm:p-7 md:p-8 lg:p-9 space-y-6 overflow-y-auto">
      {/* Top Date Header & Handwritten Greeting */}
      <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-2">
        <div>
          <h2 className="text-3xl sm:text-4xl font-serif-title font-bold text-[#26170d] tracking-tight">
            {dayName}
          </h2>
          <div
            onClick={onOpenCalendar}
            className="group inline-flex items-center gap-1.5 cursor-pointer hover:opacity-85 transition-opacity mt-0.5"
            title="Open Life Calendar"
          >
            <p className="text-sm font-serif-title text-[#765c45]">
              {formattedDate}
            </p>
            <Calendar className="w-3.5 h-3.5 text-[#8c6e51] group-hover:text-amber-900" />
          </div>
        </div>

        {/* Handwritten Cursive Greeting & Sun Doodle */}
        <div className="flex items-center gap-2 self-start sm:self-auto sm:text-right">
          <div>
            <p className="text-lg font-handwriting text-[#533923] font-bold leading-tight">
              {greetingTime}, {firstName}!
            </p>
            <p className="text-base font-handwriting text-[#684b31] leading-tight">
              Here's what your life looks like today.
            </p>
          </div>
          {/* Hand-drawn sunshine doodle */}
          <div className="text-amber-500 shrink-0 ml-1">
            <svg className="w-8 h-8" viewBox="0 0 36 36" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round">
              <circle cx="18" cy="18" r="6" fill="#fde68a" stroke="#d97706" />
              <line x1="18" y1="4" x2="18" y2="8" stroke="#d97706" />
              <line x1="18" y1="28" x2="18" y2="32" stroke="#d97706" />
              <line x1="4" y1="18" x2="8" y2="18" stroke="#d97706" />
              <line x1="28" y1="18" x2="32" y2="18" stroke="#d97706" />
              <line x1="8" y1="8" x2="11" y2="11" stroke="#d97706" />
              <line x1="25" y1="25" x2="28" y2="28" stroke="#d97706" />
              <line x1="8" y1="28" x2="11" y2="25" stroke="#d97706" />
              <line x1="25" y1="11" x2="28" y2="8" stroke="#d97706" />
            </svg>
          </div>
        </div>
      </div>

      {/* Hero Card: "What happened today?" */}
      <div className="bg-[#edf4eb] border border-[#cfdfcc] rounded-2xl p-5 shadow-xs">
        <div className="text-center mb-3">
          <h3 className="text-base sm:text-lg font-bold text-[#233c20] font-serif-title">
            What happened today?
          </h3>
          <p className="text-xs text-[#506e4a] mt-0.5">
            Talk, write or add a photo. I'll take care of the rest.
          </p>
        </div>

        {/* Waveform and Microphone Button */}
        <div className="flex items-center justify-center gap-4 my-2">
          {/* Left waveform equalizer */}
          <div className="flex items-center gap-1 h-8">
            {[10, 18, 14, 26, 12, 20, 8].map((h, i) => (
              <span
                key={i}
                style={{ height: `${h}px` }}
                className="w-1 bg-[#86b579] rounded-full"
              />
            ))}
          </div>

          {/* Central Green Microphone Button */}
          <button
            onClick={onOpenVoice}
            className="w-14 h-14 rounded-full bg-[#3b7b54] hover:bg-[#326a48] text-white flex items-center justify-center shadow-md transition-all hover:scale-105 active:scale-95 group border-2 border-emerald-400/40 cursor-pointer"
            title="Tap to speak"
          >
            <Mic className="w-6 h-6 group-hover:animate-pulse" />
          </button>

          {/* Right waveform equalizer */}
          <div className="flex items-center gap-1 h-8">
            {[8, 20, 12, 26, 14, 18, 10].map((h, i) => (
              <span
                key={i}
                style={{ height: `${h}px` }}
                className="w-1 bg-[#86b579] rounded-full"
              />
            ))}
          </div>
        </div>

        <p className="text-[11px] font-bold text-[#3b7b54] text-center mb-4">
          Tap to speak
        </p>

        {/* Three Pill Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-2.5 pt-1">
          <button
            onClick={onOpenText}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white/90 hover:bg-white text-xs font-semibold text-[#2f4f27] border border-[#c4d7be] shadow-2xs transition-colors cursor-pointer"
          >
            <PenTool className="w-3.5 h-3.5 text-[#3b7b54]" />
            <span>Write a memory</span>
          </button>

          <button
            onClick={onOpenPhoto}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white/90 hover:bg-white text-xs font-semibold text-[#2f4f27] border border-[#c4d7be] shadow-2xs transition-colors cursor-pointer"
          >
            <ImageIcon className="w-3.5 h-3.5 text-[#3b7b54]" />
            <span>Add a photo</span>
          </button>

          <button
            onClick={onOpenText}
            className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-white/90 hover:bg-white text-xs font-semibold text-[#2f4f27] border border-[#c4d7be] shadow-2xs transition-colors cursor-pointer"
          >
            <MoreHorizontal className="w-3.5 h-3.5 text-[#6b8b63]" />
            <span>Example</span>
          </button>
        </div>
      </div>

      {/* Active Entry Processing Tracker (if entry being drafted) */}
      {activeEntry && activeEntry.status !== "COMPLETED" && (
        <ProcessingTracker
          status={activeEntry.status}
          history={activeEntry.status_history || []}
          entryId={activeEntry.id}
          onRetry={onRetryProcessing}
        />
      )}

      {/* Today's Diary / Entry Section */}
      {activeEntry ? (
        <div className="space-y-6">
          <div className="bg-[#fcf8f0] border border-[#e2d4be] rounded-2xl p-5 shadow-xs relative">
            {/* Section Header */}
            <div className="flex items-center justify-between mb-4 border-b border-[#ebdcc4] pb-2.5">
              <div className="flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-[#8a6849]" />
                <h3 className="text-xs font-bold uppercase tracking-wider text-[#8a6849]">
                  Today's Diary
                </h3>
                {isRegenerating && (
                  <span className="text-[10px] text-amber-800 bg-amber-100/90 border border-amber-300 px-2 py-0.5 rounded-full font-medium flex items-center gap-1 animate-pulse">
                    <Sparkles className="w-2.5 h-2.5" /> AI Rewriting...
                  </span>
                )}
              </div>
              <button
                onClick={onOpenReview}
                className="flex items-center gap-1 text-xs text-[#8a6849] hover:text-[#3d2511] font-semibold transition-colors cursor-pointer"
              >
                <Edit2 className="w-3.5 h-3.5" />
                <span>Edit</span>
              </button>
            </div>

            {/* Diary Content Row */}
            <div className="flex flex-col sm:flex-row gap-5 items-start">
              {/* Authentic Polaroid Photo Frame if photo exists */}
              {activeEntry.photo_urls && activeEntry.photo_urls.length > 0 && (
                <div
                  onClick={onOpenPhotos}
                  className="polaroid-frame shrink-0 w-36 sm:w-40 transform -rotate-2 cursor-pointer self-center sm:self-start"
                  title="Click to view photo scrapbook"
                >
                  <img
                    src={activeEntry.photo_urls[0]}
                    alt={activeEntry.title || "Diary Photo"}
                    className="w-full h-28 object-cover rounded-xs"
                  />
                  <p className="text-[12px] font-handwriting text-center text-[#4a341e] mt-1.5 font-bold truncate px-1">
                    {activeEntry.title || "Memory"}
                  </p>
                </div>
              )}

              {/* Narrative Text */}
              <div className="flex-1 space-y-2.5">
                <h4 className="text-lg font-serif-title font-bold text-[#29190e]">
                  {activeEntry.title || "Untitled Memory"}
                </h4>
                <p className="text-xs sm:text-sm text-[#473322] leading-relaxed font-serif-title whitespace-pre-wrap">
                  {activeEntry.generated_content || activeEntry.raw_text}
                </p>

                {/* Entity Tags */}
                <div className="flex flex-wrap gap-1.5 pt-2">
                  {activeEntry.category && (
                    <span className="px-2.5 py-1 rounded-md bg-[#ddf1ec] text-[#185348] text-[11px] font-medium">
                      {activeEntry.category}
                    </span>
                  )}
                  {activeEntry.mood && (
                    <span className="px-2.5 py-1 rounded-md bg-[#fceecc] text-[#7a4b12] text-[11px] font-semibold capitalize">
                      ✨ {activeEntry.mood}
                    </span>
                  )}
                  {places.map((place) => (
                    <span
                      key={place}
                      onClick={onOpenGraph}
                      className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#dbe8f7] text-[#1c4876] text-[11px] font-semibold cursor-pointer hover:bg-blue-200 transition-colors"
                      title="View in People & Places"
                    >
                      <MapPin className="w-3 h-3 text-[#1c4876]" /> {place}
                    </span>
                  ))}
                  {people.map((person) => (
                    <span
                      key={person}
                      onClick={onOpenGraph}
                      className="flex items-center gap-1 px-2.5 py-1 rounded-md bg-[#dbe8f7] text-[#1c4876] text-[11px] font-semibold cursor-pointer hover:bg-blue-200 transition-colors"
                      title="View in People & Places"
                    >
                      <UserIcon className="w-3 h-3 text-[#1c4876]" /> {person}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          </div>

          {/* "AI Understood" - Only show when entities are detected */}
          {hasExtractedEntities && (
            <div className="space-y-2">
              <div className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-[#82654a]">
                <BookOpen className="w-3.5 h-3.5 text-[#82654a]" />
                <span>AI understood</span>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {people.length > 0 && (
                  <div className="p-3 rounded-xl bg-[#f2e7d5]/90 border border-[#dfceb7]">
                    <span className="text-[10px] font-bold text-[#1f4e82] uppercase flex items-center gap-1 mb-1">
                      <UserIcon className="w-3 h-3" /> People
                    </span>
                    <p className="text-xs font-semibold text-[#321e10]">{people.join(", ")}</p>
                  </div>
                )}

                {places.length > 0 && (
                  <div className="p-3 rounded-xl bg-[#f2e7d5]/90 border border-[#dfceb7]">
                    <span className="text-[10px] font-bold text-[#20693a] uppercase flex items-center gap-1 mb-1">
                      <MapPin className="w-3 h-3" /> Places
                    </span>
                    <p className="text-xs font-semibold text-[#321e10]">{places.join(", ")}</p>
                  </div>
                )}

                {activities.length > 0 && (
                  <div className="p-3 rounded-xl bg-[#f2e7d5]/90 border border-[#dfceb7]">
                    <span className="text-[10px] font-bold text-[#8f551b] uppercase flex items-center gap-1 mb-1">
                      <Utensils className="w-3 h-3" /> Activities
                    </span>
                    <p className="text-xs font-semibold text-[#321e10]">{activities.join(", ")}</p>
                  </div>
                )}

                <div className="p-3 rounded-xl bg-[#f2e7d5]/90 border border-[#dfceb7]">
                  <span className="text-[10px] font-bold text-[#5c3e7d] uppercase flex items-center gap-1 mb-1">
                    <Briefcase className="w-3 h-3" /> Category
                  </span>
                  <p className="text-xs font-semibold text-[#321e10]">{activeEntry.category || "Personal"}</p>
                </div>
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-[#faf5eb] border border-dashed border-[#d8c5aa] rounded-2xl p-8 sm:p-10 text-center space-y-4 shadow-xs">
          <div className="w-14 h-14 rounded-full bg-[#f0e4cf] text-[#785b40] flex items-center justify-center mx-auto shadow-inner">
            <BookOpen className="w-7 h-7" />
          </div>
          <div className="space-y-1.5 max-w-md mx-auto">
            <h3 className="text-xl font-serif-title font-bold text-[#2d1b0f]">
              Your LifeBook is Ready
            </h3>
            <p className="text-xs sm:text-sm text-[#664c37] leading-relaxed font-serif-title">
              Capture your day's thoughts, conversations, or memorable events above. LifeBook will organize your memories, commitments, and relationships automatically.
            </p>
          </div>
          <div className="flex flex-wrap items-center justify-center gap-3 pt-2">
            <button
              onClick={onOpenVoice}
              className="px-4 py-2 bg-[#8b5a2b] hover:bg-[#724820] text-amber-50 font-semibold text-xs rounded-xl shadow-xs transition-colors flex items-center gap-2 cursor-pointer"
            >
              <Mic className="w-4 h-4" />
              <span>Record Voice Entry</span>
            </button>
            <button
              onClick={onOpenText}
              className="px-4 py-2 bg-[#f4ebe0] hover:bg-[#eadecc] text-[#4d3420] font-semibold text-xs rounded-xl border border-[#d3be9f] transition-colors flex items-center gap-2 cursor-pointer"
            >
              <PenTool className="w-4 h-4" />
              <span>Write Text Entry</span>
            </button>
          </div>
        </div>
      )}
    </section>
  );
};
