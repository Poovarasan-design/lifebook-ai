import React, { useState } from "react";
import {
  X,
  Settings,
  Sparkles,
  Bot,
  Mic,
  Bell,
  Volume2,
  Sliders,
  Check,
  User,
  SlidersHorizontal
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { api } from "../services/api";

interface SettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenProfile?: () => void;
}

export const SettingsModal: React.FC<SettingsModalProps> = ({
  isOpen,
  onClose,
  onOpenProfile
}) => {
  if (!isOpen) return null;

  const { user, refreshUser } = useAuth();

  const [aiProvider, setAiProvider] = useState<string>("gemini");
  const [geminiModel, setGeminiModel] = useState<string>("gemini-2.5-flash");
  const [defaultTone, setDefaultTone] = useState<string>("reflective");
  const [speechEngine, setSpeechEngine] = useState<string>("local");
  const [ragTopK, setRagTopK] = useState<number>(5);
  const [saved, setSaved] = useState(false);

  const handleSavePreferences = async () => {
    try {
      await api.updateMe({
        preferences: {
          ...(user?.preferences || {}),
          default_tone: defaultTone,
          ai_provider_preference: aiProvider,
          speech_engine: speechEngine,
          rag_top_k: ragTopK
        }
      });
      await refreshUser();
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      console.error("Failed to save settings", err);
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
            <Settings className="w-6 h-6 text-amber-300" />
          </div>
          <div>
            <h3 className="text-xl font-bold text-[#3d2817] font-serif-title flex items-center gap-2">
              Application Settings
            </h3>
            <p className="text-xs text-[#7d654c]">
              Personalize your AI intelligence engine, memory voice, and diary preferences.
            </p>
          </div>
        </div>

        {saved && (
          <div className="mb-4 p-2.5 rounded-xl bg-emerald-50 border border-emerald-300 text-xs text-emerald-800 flex items-center gap-2 animate-in fade-in">
            <Check className="w-4 h-4 text-emerald-600" />
            <span className="font-medium">Settings saved successfully!</span>
          </div>
        )}

        {/* Quick Profile Summary Card */}
        <div className="mb-5 bg-gradient-to-br from-[#f5ede0] to-[#ebdcc4] p-3.5 rounded-xl border border-[#d8c5aa] flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-full bg-[#462d1b] text-amber-100 flex items-center justify-center font-bold text-sm shadow-sm">
              {user?.full_name?.charAt(0) || user?.email?.charAt(0)?.toUpperCase() || "U"}
            </div>
            <div>
              <p className="text-xs font-bold text-[#352012]">{user?.full_name || "LifeBook Author"}</p>
              <p className="text-[11px] text-[#785e46]">{user?.email}</p>
            </div>
          </div>
          {onOpenProfile && (
            <button
              onClick={() => {
                onClose();
                onOpenProfile();
              }}
              className="text-xs font-semibold px-3 py-1.5 rounded-lg bg-[#ded0b8] hover:bg-[#d0c0a5] text-[#3d2714] transition-colors cursor-pointer"
            >
              Edit Profile
            </button>
          )}
        </div>

        {/* AI Intelligence Provider Setting */}
        <div className="space-y-3 mb-5 bg-[#f6eee0] p-4 rounded-xl border border-[#dbc7ad]">
          <div className="flex items-center gap-1.5 mb-1">
            <Bot className="w-4 h-4 text-[#8a5d3b]" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#634327]">
              AI Provider & Intelligence Engine
            </h4>
          </div>

          <div className="grid grid-cols-3 gap-2">
            {[
              { id: "gemini", name: "Google Gemini", badge: "Active", desc: "gemini-2.5-flash" },
              { id: "openrouter", name: "OpenRouter", badge: "Fallback", desc: "GPT-4o Mini" },
              { id: "local", name: "Local Engine", badge: "Zero-Cloud", desc: "Offline rule-based" },
            ].map((prov) => (
              <button
                key={prov.id}
                type="button"
                onClick={() => setAiProvider(prov.id)}
                className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer flex flex-col justify-between ${
                  aiProvider === prov.id
                    ? "bg-[#382012] text-amber-100 border-[#573620] shadow-md scale-[1.02]"
                    : "bg-white/80 text-[#4a3421] border-[#dfd0ba] hover:bg-white"
                }`}
              >
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider opacity-75 block">
                    {prov.badge}
                  </span>
                  <span className="text-xs font-bold mt-0.5 block">{prov.name}</span>
                </div>
                <span className="text-[10px] opacity-70 mt-1 block truncate">{prov.desc}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Default Diary Tone */}
        <div className="space-y-3 mb-5 bg-[#f6eee0] p-4 rounded-xl border border-[#dbc7ad]">
          <div className="flex items-center gap-1.5 mb-1">
            <Sparkles className="w-4 h-4 text-[#8a5d3b]" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#634327]">
              Default Diary Draft Tone
            </h4>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
            {[
              { id: "reflective", label: "Reflective", emoji: "🌿" },
              { id: "narrative", label: "Narrative", emoji: "📖" },
              { id: "poetic", label: "Poetic", emoji: "✨" },
              { id: "minimal", label: "Minimalist", emoji: "🖋️" },
            ].map((tone) => (
              <button
                key={tone.id}
                type="button"
                onClick={() => setDefaultTone(tone.id)}
                className={`py-2 px-2.5 rounded-xl border text-xs font-medium text-center transition-all cursor-pointer flex items-center justify-center gap-1.5 ${
                  defaultTone === tone.id
                    ? "bg-[#432717] text-amber-100 border-[#613d27] shadow-sm"
                    : "bg-white/80 text-[#543b24] border-[#ded1be] hover:bg-white"
                }`}
              >
                <span>{tone.emoji}</span>
                <span>{tone.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Speech-to-Text Audio Provider */}
        <div className="space-y-3 mb-5 bg-[#f6eee0] p-4 rounded-xl border border-[#dbc7ad]">
          <div className="flex items-center gap-1.5 mb-1">
            <Mic className="w-4 h-4 text-[#8a5d3b]" />
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#634327]">
              Voice & Audio Transcription
            </h4>
          </div>

          <div className="grid grid-cols-2 gap-2">
            {[
              { id: "local", name: "Fast Browser Speech", desc: "Instant real-time stream" },
              { id: "whisper", name: "Server Whisper / AI", desc: "Deep acoustic transcription" },
            ].map((stt) => (
              <button
                key={stt.id}
                type="button"
                onClick={() => setSpeechEngine(stt.id)}
                className={`p-2.5 rounded-xl border text-left transition-all cursor-pointer ${
                  speechEngine === stt.id
                    ? "bg-[#432717] text-amber-100 border-[#613d27] shadow-sm"
                    : "bg-white/80 text-[#543b24] border-[#ded1be] hover:bg-white"
                }`}
              >
                <p className="text-xs font-bold">{stt.name}</p>
                <p className="text-[10px] opacity-75 mt-0.5">{stt.desc}</p>
              </button>
            ))}
          </div>
        </div>

        {/* Memory Retrieval & RAG Sensitivity */}
        <div className="space-y-2 mb-6 bg-[#fbf7ee] p-3.5 rounded-xl border border-[#ded0bb]">
          <div className="flex items-center justify-between text-xs font-bold text-[#3d2714]">
            <span className="flex items-center gap-1.5">
              <SlidersHorizontal className="w-3.5 h-3.5 text-amber-800" />
              <span>RAG Memory Retrieval Depth</span>
            </span>
            <span className="px-2 py-0.5 rounded-md bg-[#ebdcc4] text-[#4a301b] font-bold">
              Top {ragTopK} memories
            </span>
          </div>
          <input
            type="range"
            min={3}
            max={10}
            step={1}
            value={ragTopK}
            onChange={(e) => setRagTopK(Number(e.target.value))}
            className="w-full accent-amber-800 cursor-pointer"
          />
          <p className="text-[11px] text-[#7d654c]">
            Controls how many deeply relevant past memories the AI consults during search and reflection.
          </p>
        </div>

        {/* Save Changes Button */}
        <div className="flex justify-end gap-3 pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-[#543820] bg-[#eadecb] hover:bg-[#ded0bb] transition-colors cursor-pointer"
          >
            Close
          </button>
          <button
            onClick={handleSavePreferences}
            className="px-5 py-2 rounded-xl text-xs font-bold text-amber-100 bg-[#352012] hover:bg-[#251509] shadow-md transition-all active:scale-[0.99] cursor-pointer"
          >
            Save Settings
          </button>
        </div>
      </div>
    </div>
  );
};
