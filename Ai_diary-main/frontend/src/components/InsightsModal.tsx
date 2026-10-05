import React, { useState, useEffect } from "react";
import {
  X,
  TrendingUp,
  Clock,
  MapPin,
  Utensils,
  AlertCircle,
  CheckCircle2,
  Sparkles,
  Calendar,
  Users,
  Activity,
  Smile,
  ShieldAlert,
  ArrowRight,
  RefreshCw
} from "lucide-react";
import { api } from "../services/api";
import { Routine, InsightsData } from "../types";

interface InsightsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onRoutineUpdated?: () => void;
}

export const InsightsModal: React.FC<InsightsModalProps> = ({
  isOpen,
  onClose,
  onRoutineUpdated
}) => {
  if (!isOpen) return null;

  const [activeTab, setActiveTab] = useState<"routines" | "mood" | "frequency" | "observations">("routines");
  const [data, setData] = useState<InsightsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [actingRoutineId, setActingRoutineId] = useState<string | null>(null);
  const [deviationNote, setDeviationNote] = useState("");
  const [showNoteInput, setShowNoteInput] = useState<string | null>(null);

  const fetchInsights = async () => {
    try {
      setLoading(true);
      const res = await api.getInsights();
      setData(res);
    } catch (err) {
      console.error("Failed to load insights:", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInsights();
  }, [isOpen]);

  const handleDeviationAction = async (routineId: string, action: string, note?: string) => {
    try {
      setActingRoutineId(routineId);
      await api.handleRoutineDeviation(routineId, action, note);
      setShowNoteInput(null);
      setDeviationNote("");
      await fetchInsights();
      if (onRoutineUpdated) onRoutineUpdated();
    } catch (err) {
      console.error("Failed to handle deviation action:", err);
    } finally {
      setActingRoutineId(null);
    }
  };

  const activeDeviations = data?.routines.filter((r) => r.deviation_active) || [];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4 animate-fade-in">
      <div className="bg-[#fbf7ee] border-2 border-[#8c6541] rounded-2xl w-full max-w-4xl max-h-[92vh] flex flex-col shadow-[0_20px_50px_rgba(0,0,0,0.6)] overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 bg-[#ede0cb] border-b border-[#ddcdb6] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2.5 rounded-xl bg-amber-100/90 text-amber-900 border border-amber-300/80 shadow-xs">
              <TrendingUp className="w-6 h-6 text-[#784f27]" />
            </div>
            <div>
              <h2 className="text-xl font-bold font-serif-title text-[#352010]">
                LifeBook Insights & Routines
              </h2>
              <p className="text-xs text-[#6e5138]">
                Habit cadence tracking, deviation analysis, and proactive life balance metrics
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-[#8a6849] hover:text-[#352010] hover:bg-[#dfd0ba] transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Navigation Tabs */}
        <div className="px-6 pt-3 bg-[#f5ecda] border-b border-[#ddcdb6] flex items-center gap-2 overflow-x-auto">
          <button
            onClick={() => setActiveTab("routines")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-t-lg transition-colors border-t-2 ${
              activeTab === "routines"
                ? "bg-[#fbf7ee] text-[#352010] border-amber-700 shadow-xs"
                : "text-[#785b41] border-transparent hover:text-[#352010]"
            }`}
          >
            <Clock className="w-4 h-4" />
            <span>Routines & Habits</span>
            {activeDeviations.length > 0 && (
              <span className="px-1.5 py-0.5 rounded-full bg-amber-500 text-white text-[10px] font-bold">
                {activeDeviations.length}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab("mood")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-t-lg transition-colors border-t-2 ${
              activeTab === "mood"
                ? "bg-[#fbf7ee] text-[#352010] border-amber-700 shadow-xs"
                : "text-[#785b41] border-transparent hover:text-[#352010]"
            }`}
          >
            <Smile className="w-4 h-4" />
            <span>Mood & Wellbeing</span>
          </button>

          <button
            onClick={() => setActiveTab("frequency")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-t-lg transition-colors border-t-2 ${
              activeTab === "frequency"
                ? "bg-[#fbf7ee] text-[#352010] border-amber-700 shadow-xs"
                : "text-[#785b41] border-transparent hover:text-[#352010]"
            }`}
          >
            <Users className="w-4 h-4" />
            <span>People & Places Cadence</span>
          </button>

          <button
            onClick={() => setActiveTab("observations")}
            className={`flex items-center gap-2 px-4 py-2.5 text-xs font-bold rounded-t-lg transition-colors border-t-2 ${
              activeTab === "observations"
                ? "bg-[#fbf7ee] text-[#352010] border-amber-700 shadow-xs"
                : "text-[#785b41] border-transparent hover:text-[#352010]"
            }`}
          >
            <Sparkles className="w-4 h-4" />
            <span>AI Life Observations</span>
          </button>
        </div>

        {/* Content Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="py-20 flex flex-col items-center justify-center gap-3 text-[#8a6849]">
              <RefreshCw className="w-7 h-7 animate-spin" />
              <p className="text-sm font-semibold">Synthesizing personal insights...</p>
            </div>
          ) : (
            <>
              {/* TAB 1: ROUTINES & HABITS */}
              {activeTab === "routines" && (
                <div className="space-y-6">
                  {/* Deviation Alert Card */}
                  {activeDeviations.length > 0 && (
                    <div className="p-4 rounded-xl bg-[#fff8ea] border-2 border-amber-300 shadow-xs space-y-3">
                      <div className="flex items-start gap-3">
                        <AlertCircle className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
                        <div>
                          <h4 className="text-sm font-bold text-amber-950">
                            Active Routine Deviation Detected
                          </h4>
                          <p className="text-xs text-amber-900 mt-0.5 leading-relaxed">
                            {activeDeviations[0].deviation_prompt ||
                              "You missed or altered your usual habitual pattern today."}
                          </p>
                        </div>
                      </div>

                      {showNoteInput === activeDeviations[0].id ? (
                        <div className="space-y-2 pt-2 border-t border-amber-200">
                          <label className="text-[11px] font-bold text-amber-900 block">
                            How did your routine change?
                          </label>
                          <div className="flex gap-2">
                            <input
                              type="text"
                              value={deviationNote}
                              onChange={(e) => setDeviationNote(e.target.value)}
                              placeholder="e.g. Switched to dinner with friends instead..."
                              className="flex-1 px-3 py-1.5 rounded-lg border border-amber-300 bg-white text-xs text-amber-950 focus:outline-none"
                            />
                            <button
                              onClick={() =>
                                handleDeviationAction(activeDeviations[0].id, "changed", deviationNote)
                              }
                              disabled={actingRoutineId === activeDeviations[0].id}
                              className="px-3 py-1.5 bg-amber-700 hover:bg-amber-800 text-white rounded-lg text-xs font-bold shadow-2xs"
                            >
                              Save Change
                            </button>
                            <button
                              onClick={() => setShowNoteInput(null)}
                              className="px-2.5 py-1.5 text-xs text-amber-800 hover:bg-amber-100 rounded-lg"
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      ) : (
                        <div className="flex flex-wrap gap-2 pt-2 border-t border-amber-200">
                          <button
                            onClick={() =>
                              handleDeviationAction(activeDeviations[0].id, "skipped")
                            }
                            disabled={actingRoutineId === activeDeviations[0].id}
                            className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-bold transition-colors shadow-2xs"
                          >
                            ✓ Skipped today (Keep routine)
                          </button>
                          <button
                            onClick={() => setShowNoteInput(activeDeviations[0].id)}
                            className="px-3 py-1.5 bg-white hover:bg-amber-50 text-amber-900 border border-amber-300 rounded-lg text-xs font-semibold transition-colors"
                          >
                            ✎ I changed this habit
                          </button>
                          <button
                            onClick={() =>
                              handleDeviationAction(activeDeviations[0].id, "disable_routine")
                            }
                            disabled={actingRoutineId === activeDeviations[0].id}
                            className="px-3 py-1.5 bg-white hover:bg-red-50 text-red-800 border border-red-200 rounded-lg text-xs font-medium transition-colors"
                          >
                            Don't treat this as routine
                          </button>
                        </div>
                      )}
                    </div>
                  )}

                  {/* Routines Grid */}
                  <div>
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[#8a6849] mb-3">
                      Tracked Habit Cadences ({data?.routines.length || 0})
                    </h3>

                    {data?.routines && data.routines.length > 0 ? (
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        {data.routines.map((routine) => {
                          const confPct = Math.round(routine.confidence * 100);
                          return (
                            <div
                              key={routine.id}
                              className="p-4 rounded-xl bg-[#ede0cb]/70 border border-[#ddcdb6] space-y-3 relative group hover:border-[#c5b095] transition-all"
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div className="flex items-center gap-3">
                                  <div className="w-10 h-10 rounded-full bg-emerald-100 border border-emerald-300 flex items-center justify-center text-emerald-800 shrink-0">
                                    <Utensils className="w-5 h-5" />
                                  </div>
                                  <div>
                                    <h4 className="text-sm font-bold text-[#352010]">
                                      {routine.title}
                                    </h4>
                                    <p className="text-xs text-[#6e5138]">
                                      {routine.activity}
                                    </p>
                                  </div>
                                </div>

                                <div className="w-12 h-12 rounded-full border-4 border-emerald-500 bg-white flex flex-col items-center justify-center shadow-xs shrink-0">
                                  <span className="text-[11px] font-bold text-emerald-800 leading-none">
                                    {confPct}%
                                  </span>
                                  <span className="text-[7px] text-zinc-500 uppercase">
                                    Conf
                                  </span>
                                </div>
                              </div>

                              <div className="text-xs text-[#5c422c] space-y-1 bg-[#f5ecda] p-2.5 rounded-lg border border-[#e2d2ba]">
                                {routine.location && (
                                  <p className="flex items-center gap-1.5 text-[11px]">
                                    <MapPin className="w-3.5 h-3.5 text-amber-700" />
                                    <span>{routine.location}</span>
                                  </p>
                                )}
                                <p className="flex items-center gap-1.5 text-[11px]">
                                  <Calendar className="w-3.5 h-3.5 text-amber-700" />
                                  <span>Pattern: Every {routine.pattern} ({routine.frequency})</span>
                                </p>
                                <p className="text-[10px] text-[#7d6046] mt-1">
                                  Observed {routine.occurrence_count} recurring times
                                </p>
                              </div>

                              {routine.deviation_active && (
                                <div className="p-2 rounded bg-amber-100/90 text-amber-900 text-[11px] font-medium border border-amber-300 flex items-center justify-between">
                                  <span>Deviation ongoing today</span>
                                  <span className="text-[10px] underline cursor-pointer" onClick={() => setActiveTab("routines")}>
                                    Resolve ↑
                                  </span>
                                </div>
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="p-8 text-center bg-[#ede0cb]/40 border border-dashed border-[#dfd0ba] rounded-xl text-[#7a5e45]">
                        <p className="text-sm font-medium">No active routines detected yet.</p>
                        <p className="text-xs text-[#9a7e65] mt-1">
                          As you log repeated memories (like regular lunch spots or study habits), LifeBook AI automatically constructs your routine graph.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* TAB 2: MOOD & WELLBEING */}
              {activeTab === "mood" && (
                <div className="space-y-6">
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                    <div className="p-4 rounded-xl bg-[#ede0cb]/80 border border-[#ddcdb6] text-center">
                      <span className="text-xs text-[#7a5e45] uppercase font-bold tracking-wider">
                        Total Memories
                      </span>
                      <p className="text-3xl font-bold font-serif-title text-[#352010] mt-1">
                        {data?.total_memories || 0}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-center">
                      <span className="text-xs text-emerald-800 uppercase font-bold tracking-wider">
                        Active Habits
                      </span>
                      <p className="text-3xl font-bold font-serif-title text-emerald-900 mt-1">
                        {data?.routines.length || 0}
                      </p>
                    </div>

                    <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-center">
                      <span className="text-xs text-amber-800 uppercase font-bold tracking-wider">
                        Open Commitments
                      </span>
                      <p className="text-3xl font-bold font-serif-title text-amber-900 mt-1">
                        {data?.commitments_summary.pending || 0}
                      </p>
                    </div>
                  </div>

                  {/* Mood Distribution */}
                  <div className="p-5 rounded-xl bg-[#f5ecda] border border-[#ddcdb6] space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[#8a6849]">
                      Emotional & Energy Tone Distribution
                    </h3>

                    <div className="space-y-2.5">
                      {data?.mood_distribution && Object.keys(data.mood_distribution).length > 0 ? (
                        Object.entries(data.mood_distribution).map(([mood, count]) => {
                          const total = data.total_memories || 1;
                          const pct = Math.round((count / total) * 100);
                          return (
                            <div key={mood} className="space-y-1">
                              <div className="flex justify-between text-xs font-medium text-[#4a3420]">
                                <span className="capitalize font-bold">{mood}</span>
                                <span>{count} memories ({pct}%)</span>
                              </div>
                              <div className="w-full bg-[#dfd0ba] h-2.5 rounded-full overflow-hidden">
                                <div
                                  className="bg-amber-700 h-2.5 rounded-full transition-all duration-500"
                                  style={{ width: `${Math.max(pct, 10)}%` }}
                                />
                              </div>
                            </div>
                          );
                        })
                      ) : (
                        <p className="text-xs text-[#8c6e51]">
                          Mood data will populate automatically as you record reflections.
                        </p>
                      )}
                    </div>
                  </div>

                  {/* Categories Breakdown */}
                  <div className="p-5 rounded-xl bg-[#f5ecda] border border-[#ddcdb6] space-y-3">
                    <h3 className="text-xs font-bold uppercase tracking-wider text-[#8a6849]">
                      Journal Category Breakdown
                    </h3>
                    <div className="flex flex-wrap gap-2">
                      {data?.category_distribution &&
                        Object.entries(data.category_distribution).map(([cat, count]) => (
                          <div
                            key={cat}
                            className="px-3 py-1.5 rounded-lg bg-white border border-[#dfd0ba] text-xs font-semibold text-[#4a3420] flex items-center gap-2 shadow-2xs"
                          >
                            <span>{cat}</span>
                            <span className="px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-900 text-[10px]">
                              {count}
                            </span>
                          </div>
                        ))}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 3: PEOPLE & PLACES FREQUENCY */}
              {activeTab === "frequency" && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {/* People */}
                  <div className="p-5 rounded-xl bg-[#f5ecda] border border-[#ddcdb6] space-y-4">
                    <div className="flex items-center gap-2 border-b border-[#dfd0ba] pb-2">
                      <Users className="w-4 h-4 text-blue-700" />
                      <h3 className="text-xs font-bold uppercase tracking-wider text-blue-900">
                        Top People Mentioned
                      </h3>
                    </div>

                    <div className="space-y-2.5">
                      {data?.top_people && data.top_people.length > 0 ? (
                        data.top_people.map((p, idx) => (
                          <div
                            key={p.name}
                            className="flex items-center justify-between p-2.5 rounded-lg bg-white border border-[#dfd0ba] shadow-2xs"
                          >
                            <div className="flex items-center gap-2.5">
                              <span className="w-6 h-6 rounded-full bg-blue-100 text-blue-800 text-xs font-bold flex items-center justify-center">
                                {idx + 1}
                              </span>
                              <span className="text-xs font-bold text-[#352010]">{p.name}</span>
                            </div>
                            <span className="text-xs font-semibold text-blue-900 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                              {p.count} shared moments
                            </span>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-[#8c6e51]">No entities cataloged yet.</p>
                      )}
                    </div>
                  </div>

                  {/* Places */}
                  <div className="p-5 rounded-xl bg-[#f5ecda] border border-[#ddcdb6] space-y-4">
                    <div className="flex items-center gap-2 border-b border-[#dfd0ba] pb-2">
                      <MapPin className="w-4 h-4 text-emerald-700" />
                      <h3 className="text-xs font-bold uppercase tracking-wider text-emerald-900">
                        Top Places Visited
                      </h3>
                    </div>

                    <div className="space-y-2.5">
                      {data?.top_places && data.top_places.length > 0 ? (
                        data.top_places.map((place, idx) => (
                          <div
                            key={place.name}
                            className="flex items-center justify-between p-2.5 rounded-lg bg-white border border-[#dfd0ba] shadow-2xs"
                          >
                            <div className="flex items-center gap-2.5">
                              <span className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-800 text-xs font-bold flex items-center justify-center">
                                {idx + 1}
                              </span>
                              <span className="text-xs font-bold text-[#352010]">
                                {place.name}
                              </span>
                            </div>
                            <span className="text-xs font-semibold text-emerald-900 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                              {place.count} visits
                            </span>
                          </div>
                        ))
                      ) : (
                        <p className="text-xs text-[#8c6e51]">No locations cataloged yet.</p>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* TAB 4: AI OBSERVATIONS */}
              {activeTab === "observations" && (
                <div className="space-y-4">
                  <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 flex items-start gap-3">
                    <Sparkles className="w-5 h-5 text-amber-700 shrink-0 mt-0.5" />
                    <div>
                      <h4 className="text-xs font-bold text-amber-950 uppercase tracking-wide">
                        LifeBook AI Proactive Insights
                      </h4>
                      <p className="text-xs text-amber-900 mt-0.5 leading-relaxed">
                        These observations are synthesized autonomously from your diary cadence, extracted commitments, and life graph connections.
                      </p>
                    </div>
                  </div>

                  <div className="space-y-3">
                    {data?.ai_observations && data.ai_observations.length > 0 ? (
                      data.ai_observations.map((obs, idx) => (
                        <div
                          key={idx}
                          className="p-4 rounded-xl bg-white border border-[#dfd0ba] shadow-2xs flex items-start gap-3"
                        >
                          <div className="w-6 h-6 rounded-full bg-[#f5ecda] text-[#785b41] text-xs font-bold flex items-center justify-center shrink-0 mt-0.5">
                            {idx + 1}
                          </div>
                          <p className="text-xs md:text-sm text-[#352010] leading-relaxed font-serif-title">
                            {obs}
                          </p>
                        </div>
                      ))
                    ) : (
                      <p className="text-xs text-[#8c6e51]">No observations generated yet.</p>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 bg-[#ede0cb] border-t border-[#ddcdb6] flex justify-between items-center text-xs text-[#70553d]">
          <span>LifeBook AI Pattern Engine</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-[#4a3420] hover:bg-[#352414] text-white rounded-lg font-bold text-xs shadow-2xs transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
