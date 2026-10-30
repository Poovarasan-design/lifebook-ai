import React, { useState, useEffect, useRef } from "react";
import { Sparkles, X, Send, Volume2, VolumeX, HelpCircle, BookOpen } from "lucide-react";
import { api } from "../services/api";
import { useAuth } from "../contexts/AuthContext";
import { ForgettingItem, RAGSource } from "../types";

interface Message {
  sender: "ai" | "user";
  text: string;
  forgettingItems?: ForgettingItem[];
  sourceEntryId?: string;
  sources?: RAGSource[];
  isGrounded?: boolean;
}

export const AskLifeBookWidget: React.FC = () => {
  const { user } = useAuth();
  const firstName = user?.full_name?.split(" ")[0] || "Friend";

  const [isOpen, setIsOpen] = useState(true);
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [speakingIndex, setSpeakingIndex] = useState<number | null>(null);
  const synthRef = useRef<SpeechSynthesis | null>(null);

  const [messages, setMessages] = useState<Message[]>([
    {
      sender: "ai",
      text: `Hi ${firstName}! 👋\nWhat would you like to remember today?`
    }
  ]);

  useEffect(() => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      synthRef.current = window.speechSynthesis;
    }
    return () => {
      if (synthRef.current) {
        synthRef.current.cancel();
      }
    };
  }, []);

  const handleSpeak = (text: string, index: number) => {
    if (!synthRef.current) return;

    if (speakingIndex === index) {
      synthRef.current.cancel();
      setSpeakingIndex(null);
      return;
    }

    synthRef.current.cancel();
    const cleanSpeech = text
      .replace(/[•*#_`~]/g, " ")
      .replace(/https?:\/\/\S+/g, "")
      .replace(/\s+/g, " ")
      .trim();

    const utterance = new SpeechSynthesisUtterance(cleanSpeech);
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    const voices = synthRef.current.getVoices();
    const preferredVoice = voices.find(
      (v) => v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("Samantha"))
    ) || voices.find((v) => v.lang.startsWith("en"));

    if (preferredVoice) {
      utterance.voice = preferredVoice;
    }

    utterance.onend = () => setSpeakingIndex(null);
    utterance.onerror = () => setSpeakingIndex(null);

    setSpeakingIndex(index);
    synthRef.current.speak(utterance);
  };

  // Universal suggested questions
  const referenceQuestions = [
    "What am I forgetting?",
    "What did I do yesterday?",
    "What are my pending commitments?",
    "Summarize my week so far.",
    "Read today's diary."
  ];

  const handleAsk = async (textToAsk: string) => {
    if (!textToAsk.trim()) return;
    const userMsg = textToAsk.trim();
    setMessages((prev) => [...prev, { sender: "user", text: userMsg }]);
    setQuery("");
    setLoading(true);

    try {
      const res = await api.askQuestion(userMsg);
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: res.answer,
          sourceEntryId: res.source_entry_id,
          forgettingItems: res.forgetting_items && res.forgetting_items.length > 0 ? res.forgetting_items : undefined,
          // RAG Task 3 fields
          sources: res.sources && res.sources.length > 0 ? res.sources : undefined,
          isGrounded: res.is_grounded,
        }
      ]);
    } catch (err: any) {
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: "I couldn't complete that search right now. Please try again."
        }
      ]);
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteCommitment = async (item: ForgettingItem) => {
    try {
      await api.completeCommitment(item.id);
      setMessages((prev) => [
        ...prev,
        {
          sender: "ai",
          text: `✓ Marked "${item.title}" as Done in your diary.`
        }
      ]);
    } catch (err) {
      console.error(err);
    }
  };

  if (!isOpen) {
    return (
      <button
        onClick={() => setIsOpen(true)}
        className="fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-40 flex items-center gap-2 px-4 py-2.5 rounded-full bg-[#1e252b] text-white shadow-2xl hover:bg-[#151a1e] transition-all hover:scale-105 border border-slate-700/80 cursor-pointer"
      >
        <Sparkles className="w-4 h-4 text-amber-400" />
        <span className="text-xs font-bold tracking-wide">Ask LifeBook</span>
      </button>
    );
  }

  return (
    <div className="fixed bottom-3 right-3 sm:bottom-6 sm:right-8 z-40 w-[92vw] sm:w-[320px] bg-[#1a2128]/95 backdrop-blur-md text-white rounded-2xl shadow-[0_20px_50px_rgba(0,0,0,0.85)] border border-slate-700/80 flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-5">
      {/* Header matching dark card in reference */}
      <div className="flex items-center justify-between px-4 py-3 bg-[#242d36]/90 border-b border-slate-700/60">
        <div className="flex items-center gap-2">
          <Sparkles className="w-4 h-4 text-amber-400" />
          <h4 className="text-xs font-bold tracking-wide text-zinc-100">
            Ask LifeBook
          </h4>
        </div>
        <button
          onClick={() => setIsOpen(false)}
          className="text-zinc-400 hover:text-white p-1 rounded-md hover:bg-white/10 cursor-pointer transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Messages Scroll Area */}
      <div className="p-3.5 max-h-72 overflow-y-auto space-y-3 text-xs">
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex flex-col ${m.sender === "user" ? "items-end" : "items-start"}`}
          >
            <div className="relative group max-w-[92%]">
              <div
                className={`px-3.5 py-2.5 rounded-xl leading-relaxed whitespace-pre-line ${
                  m.sender === "user"
                    ? "bg-[#2d7d52] text-white font-medium shadow-sm"
                    : "bg-[#252f38] text-zinc-100 border border-slate-700/60 shadow-xs"
                }`}
              >
                {m.text}
              </div>

              {/* TTS Listen button */}
              {m.sender === "ai" && (
                <div className="flex items-center gap-1.5 mt-1 ml-1">
                  <button
                    onClick={() => handleSpeak(m.text, idx)}
                    className={`flex items-center gap-1 px-2 py-0.5 rounded-md text-[10px] font-medium transition-all ${
                      speakingIndex === idx
                        ? "bg-emerald-600/30 text-emerald-300 border border-emerald-500/50 animate-pulse"
                        : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-800"
                    }`}
                  >
                    {speakingIndex === idx ? (
                      <>
                        <VolumeX className="w-3 h-3 text-emerald-400" />
                        <span>Stop</span>
                      </>
                    ) : (
                      <>
                        <Volume2 className="w-3 h-3 text-emerald-400" />
                        <span>Listen</span>
                      </>
                    )}
                  </button>
                </div>
              )}
            </div>

            {/* RAG Memory Sources — shown for grounded answers */}
            {m.sender === "ai" && m.sources && m.sources.length > 0 && (
              <div className="w-full mt-2 space-y-1">
                <p className="text-[10px] text-zinc-500 font-medium ml-0.5 mb-1">📚 From your memories:</p>
                {m.sources.map((src) => (
                  <div
                    key={src.chunk_id}
                    className="flex items-start gap-2 px-2.5 py-1.5 rounded-lg bg-[#1e2830] border border-slate-700/50 text-[10px] text-zinc-300 hover:bg-[#242f3c] transition-colors"
                    title={src.snippet || src.title || ""}
                  >
                    <BookOpen className="w-3 h-3 text-amber-400/70 shrink-0 mt-0.5" />
                    <div className="flex-1 min-w-0">
                      <span className="font-medium text-zinc-200 truncate block">
                        {src.title || "Memory"}
                      </span>
                      {src.date && (
                        <span className="text-zinc-500">
                          {src.citation} · {src.date.slice(0, 10)}
                        </span>
                      )}
                    </div>
                    {src.score > 0 && (
                      <span className="text-[9px] text-emerald-500/70 shrink-0">
                        {Math.round(src.score * 100)}%
                      </span>
                    )}
                  </div>
                ))}
              </div>
            )}

            {/* Render Forgetting Items Cards if present */}
            {m.forgettingItems && m.forgettingItems.length > 0 && (
              <div className="w-full mt-2 space-y-2">
                {m.forgettingItems.map((item) => (
                  <div
                    key={item.id}
                    className="p-2.5 rounded-lg bg-[#252f38] border border-slate-700/80 text-xs"
                  >
                    <div className="flex items-start justify-between gap-1 mb-1">
                      <span className="font-semibold text-emerald-400">
                        {item.title}
                      </span>
                      {item.due_date && (
                        <span className="text-[10px] text-amber-300 bg-amber-950/60 px-1.5 py-0.5 rounded border border-amber-800/40 shrink-0">
                          {item.due_date}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-zinc-300 mb-2">{item.description}</p>
                    <button
                      onClick={() => handleCompleteCommitment(item)}
                      className="px-2.5 py-1 bg-emerald-600 hover:bg-emerald-500 text-white rounded text-[10px] font-semibold transition-colors cursor-pointer"
                    >
                      Mark Done
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}

        {loading && (
          <div className="flex items-center gap-2 text-zinc-400 text-xs italic">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>Searching memories...</span>
          </div>
        )}
      </div>

      {/* Suggested Reference Pills */}
      <div className="px-3 py-2 bg-[#202830]/90 border-t border-slate-700/60 flex flex-col gap-1.5">
        {referenceQuestions.map((q, idx) => (
          <button
            key={idx}
            onClick={() => handleAsk(q)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#28333e] hover:bg-[#32404e] text-[11px] text-zinc-200 border border-slate-700/50 transition-colors text-left cursor-pointer group"
          >
            <HelpCircle className="w-3.5 h-3.5 text-amber-400/80 shrink-0 group-hover:text-amber-300" />
            <span className="truncate">{q}</span>
          </button>
        ))}
      </div>

      {/* Input box with send button */}
      <div className="p-2.5 bg-[#242d36] border-t border-slate-700/60 flex items-center gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleAsk(query)}
          placeholder="Ask anything..."
          className="flex-1 bg-[#1a2128] text-white placeholder-zinc-400 text-xs px-3 py-2 rounded-xl border border-slate-600 focus:outline-none focus:border-emerald-500"
        />
        <button
          onClick={() => handleAsk(query)}
          className="p-2 rounded-xl bg-[#2e7d53] hover:bg-[#256844] text-white transition-colors cursor-pointer"
        >
          <Send className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
};
