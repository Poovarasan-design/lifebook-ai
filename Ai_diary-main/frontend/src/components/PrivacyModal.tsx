import React, { useState } from "react";
import {
  X,
  Shield,
  ShieldCheck,
  Lock,
  Download,
  Trash2,
  Check,
  AlertTriangle,
  EyeOff,
  Cpu,
  Database,
  Key
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../services/api";

interface PrivacyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const PrivacyModal: React.FC<PrivacyModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const { user, refreshUser, logout } = useAuth();
  const [preferences, setPreferences] = useState({
    routine_learning: user?.preferences?.routine_learning ?? true,
    location_analysis: user?.preferences?.location_analysis ?? true,
    photo_analysis: user?.preferences?.photo_analysis ?? true,
    ai_personalization: user?.preferences?.ai_personalization ?? true,
    morning_briefing: user?.preferences?.morning_briefing ?? true,
  });
  const [saved, setSaved] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const togglePref = async (key: keyof typeof preferences) => {
    const updated = { ...preferences, [key]: !preferences[key] };
    setPreferences(updated);
    try {
      await api.updateMe({ preferences: updated });
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 2000);
    } catch (err) {
      console.error(err);
    }
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const data = await api.exportData();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `lifebook_export_${new Date().toISOString().split("T")[0]}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export failed", err);
    } finally {
      setIsExporting(false);
    }
  };

  const handleDeleteAccount = async () => {
    try {
      await api.deleteAccount();
      logout();
      onClose();
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/65 backdrop-blur-xs p-3 sm:p-4">
      <div className="bg-[#fbf7ee] border-2 border-[#cbb79a] rounded-2xl p-5 sm:p-6 w-full max-w-lg shadow-2xl relative max-h-[90vh] overflow-y-auto">
        
        {/* Close Button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-[#8a6e50] hover:text-[#3d2714] p-1.5 rounded-lg hover:bg-black/5 transition-colors cursor-pointer"
        >
          <X className="w-5 h-5" />
        </button>

        {/* Modal Header */}
        <div className="flex items-center gap-3 mb-4 pb-3 border-b border-[#e5d8c3]">
          <div className="p-2.5 rounded-xl bg-gradient-to-br from-[#4a2e18] to-[#2c1a0e] text-[#f7eee1] shadow-md">
            <ShieldCheck className="w-6 h-6 text-emerald-400" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-[#3d2817] font-serif-title flex items-center gap-2">
              Privacy & Data Sovereignty
            </h3>
            <p className="text-xs text-[#7d654c]">
              Complete ownership, zero third-party tracking, and end-to-end user isolation.
            </p>
          </div>
        </div>

        {saved && (
          <div className="mb-4 p-2.5 rounded-xl bg-emerald-50 border border-emerald-300 text-xs text-emerald-800 flex items-center gap-2 animate-in fade-in">
            <Check className="w-4 h-4 text-emerald-600" />
            <span className="font-medium">Privacy preferences updated successfully!</span>
          </div>
        )}

        {/* Security & Data Isolation Card */}
        <div className="mb-5 bg-gradient-to-br from-[#f2e7d5] to-[#ebdcc4] p-3.5 rounded-xl border border-[#d8c5aa] space-y-2">
          <div className="flex items-center gap-2 text-xs font-bold text-[#442c19] uppercase tracking-wider">
            <Lock className="w-3.5 h-3.5 text-amber-700" />
            <span>Guaranteed User Isolation</span>
          </div>
          <p className="text-[11.5px] text-[#5c432d] leading-relaxed">
            Your life memories, audio recordings, OCR extracts, and Life Graph connections are strictly scoped to your authenticated account (<span className="font-semibold text-[#3d2714]">{user?.email}</span>). No cross-user access or data leaking is permitted.
          </p>
        </div>

        {/* AI Processing Controls */}
        <div className="space-y-3 mb-5 bg-[#f6eee0] p-4 rounded-xl border border-[#dbc7ad]">
          <div className="flex items-center gap-1.5 mb-2">
            <Cpu className="w-4 h-4 text-[#8a5d3b]" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#634327]">
              AI Processing & Intelligence Toggles
            </h4>
          </div>

          {[
            {
              key: "routine_learning",
              label: "Habit & Routine Learning",
              desc: "Detect recurring patterns to provide proactive assistance and notice deviations."
            },
            {
              key: "location_analysis",
              label: "Location & Travel Context",
              desc: "Extract visited cities/places and adapt routine insights while traveling."
            },
            {
              key: "photo_analysis",
              label: "Multimodal & Photo OCR",
              desc: "Extract readable text, places, and visual scenes from uploaded diary photos."
            },
            {
              key: "ai_personalization",
              label: "AI Reflection Personalization",
              desc: "Tailor diary draft tone and connect today's memories with past life milestones."
            },
            {
              key: "morning_briefing",
              label: "Morning Digest & Proactive Insights",
              desc: "Surface relevant past memories, upcoming commitments, and today's summary."
            }
          ].map((item) => {
            const isEnabled = preferences[item.key as keyof typeof preferences];
            return (
              <div
                key={item.key}
                className="flex items-center justify-between py-2 border-b border-[#e6d8c4] last:border-b-0 gap-3"
              >
                <div className="pr-2">
                  <p className="text-xs font-semibold text-[#3d2714]">{item.label}</p>
                  <p className="text-[11px] text-[#7d654c] leading-tight mt-0.5">{item.desc}</p>
                </div>
                <button
                  onClick={() => togglePref(item.key as keyof typeof preferences)}
                  className={`w-11 h-6 flex items-center rounded-full p-1 transition-all shrink-0 cursor-pointer ${
                    isEnabled ? "bg-emerald-700 justify-end" : "bg-zinc-400 justify-start"
                  }`}
                  title={isEnabled ? "Click to disable" : "Click to enable"}
                >
                  <div className="w-4 h-4 rounded-full bg-white shadow-md transform transition-transform" />
                </button>
              </div>
            );
          })}
        </div>

        {/* Data Portability & Export */}
        <div className="space-y-3 mb-5 bg-[#fbf7ee] p-3.5 rounded-xl border border-[#ded0bb]">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="flex items-center gap-1.5 text-xs font-bold text-[#3d2714]">
                <Database className="w-3.5 h-3.5 text-amber-800" />
                <span>Export Entire Diary Archive</span>
              </div>
              <p className="text-[11px] text-[#7d654c] mt-0.5">
                Download an offline JSON package of all entries, commitments, routines, and graph links.
              </p>
            </div>
            <button
              onClick={handleExport}
              disabled={isExporting}
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#462d1b] hover:bg-[#311c0f] text-amber-100 transition-colors shrink-0 shadow-sm cursor-pointer disabled:opacity-60"
            >
              <Download className="w-3.5 h-3.5 text-amber-300" />
              <span>{isExporting ? "Exporting..." : "Export JSON"}</span>
            </button>
          </div>
        </div>

        {/* Danger Zone: Account Deletion */}
        <div className="border border-red-200 bg-red-50/70 p-3.5 rounded-xl space-y-2">
          <div className="flex items-center justify-between gap-3">
            <div>
              <p className="text-xs font-bold text-red-900 flex items-center gap-1.5">
                <Trash2 className="w-3.5 h-3.5 text-red-600" />
                <span>Delete Account & Erase All Memories</span>
              </p>
              <p className="text-[11px] text-red-700 mt-0.5">
                Permanently destroys your diary entries, audio files, photo tags, and life graph.
              </p>
            </div>
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-bold bg-red-600 hover:bg-red-700 text-white transition-colors shrink-0 shadow-sm cursor-pointer"
            >
              <span>Delete</span>
            </button>
          </div>
        </div>

        {/* Deletion Confirmation Modal */}
        {showDeleteConfirm && (
          <div className="absolute inset-0 bg-[#fbf7ee]/95 backdrop-blur-xs p-6 rounded-2xl flex flex-col justify-center items-center text-center z-20 animate-in fade-in">
            <div className="p-3 rounded-full bg-red-100 text-red-600 mb-3 shadow-inner">
              <AlertTriangle className="w-10 h-10" />
            </div>
            <h4 className="text-base font-bold text-red-900 mb-1">Permanently Delete Account?</h4>
            <p className="text-xs text-[#705439] mb-5 max-w-xs leading-relaxed">
              This action is immediate and cannot be undone. All recorded stories, audio transcriptions, photo metadata, and entity connections will be completely erased.
            </p>
            <div className="flex items-center gap-3">
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-4 py-2 rounded-xl text-xs font-semibold text-[#543820] bg-[#eadecb] hover:bg-[#ded0bb] transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                className="px-4 py-2 rounded-xl text-xs font-bold text-white bg-red-700 hover:bg-red-800 shadow-md transition-colors cursor-pointer"
              >
                Yes, Permanently Erase
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
