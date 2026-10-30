import React from "react";
import { CheckCircle2, Circle, Loader2, AlertCircle } from "lucide-react";
import { StatusHistoryItem } from "../types";

interface ProcessingTrackerProps {
  status: string;
  history: StatusHistoryItem[];
  compact?: boolean;
  entryId?: string;
  onRetry?: () => void;
}

const STAGES = [
  { key: "RECEIVED", label: "Captured" },
  { key: "SAVED", label: "Saved" },
  { key: "TRANSCRIBING", label: "Transcribing" },
  { key: "EXTRACTING", label: "Understanding" },
  { key: "DRAFTED", label: "Drafted" },
  { key: "USER_REVIEW", label: "User Review" },
  { key: "CONFIRMED", label: "Confirmed" },
  { key: "GRAPH_UPDATED", label: "Life Graph" },
  { key: "INDEXED", label: "Search Index" },
  { key: "COMPLETED", label: "Completed" },
];

export const ProcessingTracker: React.FC<ProcessingTrackerProps> = ({
  status,
  history,
  compact = false,
  entryId,
  onRetry
}) => {
  const currentStageIndex = STAGES.findIndex((s) => s.key === status);
  const isFailed = status === "FAILED" || status === "ENRICHMENT_PENDING";
  const [retrying, setRetrying] = React.useState(false);

  const handleRetryClick = async () => {
    if (onRetry) {
      setRetrying(true);
      try {
        await onRetry();
      } finally {
        setRetrying(false);
      }
    }
  };

  return (
    <div className="bg-[#f5ecda] border border-[#d9c7ab] rounded-xl p-4 shadow-sm">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 mb-3 border-b border-[#e5d5be] pb-2">
        <h4 className="text-xs font-bold uppercase tracking-wider text-[#705439] flex items-center gap-2">
          <span>Processing Lifecycle</span>
          <span className={`text-[11px] font-medium px-2 py-0.5 rounded-full ${
            isFailed
              ? "bg-amber-100 text-amber-900 border border-amber-300"
              : status === "COMPLETED"
              ? "bg-emerald-100 text-emerald-800"
              : "bg-[#ebdcc4] text-[#4d3319]"
          }`}>
            Backend: <strong>{status}</strong>
          </span>
        </h4>
        {history.length > 0 && (
          <span className="text-[11px] text-[#8c6f52] truncate max-w-xs">
            {history[history.length - 1].message}
          </span>
        )}
      </div>

      {/* Stage Flow Badges */}
      <div className="flex flex-wrap items-center gap-1.5 sm:gap-2">
        {STAGES.map((stage, idx) => {
          let state: "completed" | "current" | "pending" = "pending";

          if (currentStageIndex >= idx || status === "COMPLETED") {
            if (currentStageIndex === idx && status !== "COMPLETED") {
              state = "current";
            } else {
              state = "completed";
            }
          }

          return (
            <div
              key={stage.key}
              className={`flex items-center gap-1.5 px-2 py-1 rounded-md border text-[11px] font-medium whitespace-nowrap transition-all ${
                state === "completed"
                  ? "bg-emerald-50/90 border-emerald-300 text-emerald-800"
                  : state === "current"
                  ? "bg-amber-100 border-amber-400 text-amber-900 font-semibold shadow-xs ring-1 ring-amber-300/60"
                  : "bg-white/50 border-[#e3d3bd] text-[#9c8266]"
              }`}
            >
              {state === "completed" && (
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
              )}
              {state === "current" && (
                <Loader2 className="w-3.5 h-3.5 text-amber-600 animate-spin shrink-0" />
              )}
              {state === "pending" && (
                <Circle className="w-3 h-3 text-[#bfaea0] shrink-0" />
              )}

              <span>{stage.label}</span>
            </div>
          );
        })}
      </div>

      {isFailed && (
        <div className="mt-3 p-3 rounded-lg bg-amber-50 border border-amber-300 flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 text-xs text-amber-900">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
            <span>
              Raw memory is safely saved. AI pipeline can be re-run immediately with OpenRouter.
            </span>
          </div>
          {onRetry && (
            <button
              onClick={handleRetryClick}
              disabled={retrying}
              className="px-3 py-1 bg-amber-700 hover:bg-amber-800 text-white rounded-md text-xs font-medium shrink-0 flex items-center gap-1.5 cursor-pointer shadow-xs disabled:opacity-50"
            >
              {retrying ? (
                <Loader2 className="w-3 h-3 animate-spin" />
              ) : (
                <span>Re-run AI Enrichment</span>
              )}
            </button>
          )}
        </div>
      )}
    </div>
  );
};

