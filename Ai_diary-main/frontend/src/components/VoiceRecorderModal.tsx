import React, { useState, useRef, useEffect } from "react";
import { Mic, Square, Play, RotateCcw, X, Sparkles, Volume2, Globe } from "lucide-react";
import { api } from "../services/api";
import { DiaryEntry } from "../types";

interface VoiceRecorderModalProps {
  isOpen: boolean;
  onClose: () => void;
  onEntryCreated: (entry: DiaryEntry) => void;
}

export const VoiceRecorderModal: React.FC<VoiceRecorderModalProps> = ({
  isOpen,
  onClose,
  onEntryCreated
}) => {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
  const [audioUrl, setAudioUrl] = useState<string | null>(null);
  const [transcript, setTranscript] = useState("");
  const [speechLang, setSpeechLang] = useState<string>("en-IN");
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<any>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animationFrameRef = useRef<number | null>(null);
  const audioContextRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const recognitionRef = useRef<any>(null);

  useEffect(() => {
    if (!isOpen) {
      cleanup();
    }
  }, [isOpen]);

  const cleanup = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== "inactive") {
      try {
        mediaRecorderRef.current.stop();
      } catch {}
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort();
      } catch {}
      recognitionRef.current = null;
    }
    clearInterval(timerRef.current);
    if (animationFrameRef.current) {
      cancelAnimationFrame(animationFrameRef.current);
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
    }
    setIsRecording(false);
    setRecordingTime(0);
    setAudioBlob(null);
    setAudioUrl(null);
    setTranscript("");
    setErrorMsg(null);
  };

  const startRecording = async () => {
    try {
      setErrorMsg(null);
      setTranscript("");
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

      // Setup Web Audio API Analyser for live waveform
      const audioCtx = new (window.AudioContext || (window as any).webkitAudioContext)();
      const analyser = audioCtx.createAnalyser();
      analyser.fftSize = 64;
      const source = audioCtx.createMediaStreamSource(stream);
      source.connect(analyser);

      audioContextRef.current = audioCtx;
      analyserRef.current = analyser;

      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
        setAudioUrl(URL.createObjectURL(blob));
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorder.start();

      // Start Browser Native Speech Recognition
      const SpeechRecognition =
        (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;

      if (SpeechRecognition) {
        try {
          const recognition = new SpeechRecognition();
          recognition.continuous = true;
          recognition.interimResults = true;
          recognition.lang = speechLang;

          let accumulated = "";

          recognition.onresult = (event: any) => {
            let interim = "";
            for (let i = event.resultIndex; i < event.results.length; ++i) {
              if (event.results[i].isFinal) {
                accumulated += event.results[i][0].transcript + " ";
              } else {
                interim += event.results[i][0].transcript;
              }
            }
            const fullText = (accumulated + interim).trim();
            if (fullText) {
              setTranscript(fullText);
            }
          };

          recognition.onerror = (e: any) => {
            if (e.error !== "no-speech") {
              console.warn("Speech recognition warning:", e.error);
            }
          };

          recognition.onend = () => {
            if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
              try {
                recognition.start();
              } catch {}
            }
          };

          recognition.start();
          recognitionRef.current = recognition;
        } catch (recErr) {
          console.warn("Speech recognition initialization fallback:", recErr);
        }
      }

      setIsRecording(true);

      // Start timer
      setRecordingTime(0);
      timerRef.current = setInterval(() => {
        setRecordingTime((prev) => prev + 1);
      }, 1000);

      // Start drawing waveform
      drawWaveform();
    } catch (err: any) {
      console.warn("Microphone access issue:", err);
      setErrorMsg("Microphone permission unavailable. Please allow microphone access or test with the sample audio button below.");
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      clearInterval(timerRef.current);
      if (animationFrameRef.current) {
        cancelAnimationFrame(animationFrameRef.current);
      }
    }
    if (recognitionRef.current) {
      try {
        recognitionRef.current.stop();
      } catch {}
    }
  };

  const drawWaveform = () => {
    if (!canvasRef.current || !analyserRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const renderFrame = () => {
      animationFrameRef.current = requestAnimationFrame(renderFrame);
      analyser.getByteFrequencyData(dataArray);

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const barWidth = (canvas.width / bufferLength) * 2;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height * 0.8;

        const gradient = ctx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
        gradient.addColorStop(0, "#15803d");
        gradient.addColorStop(1, "#84cc16");

        ctx.fillStyle = gradient;
        ctx.fillRect(x, (canvas.height - barHeight) / 2, barWidth - 1, barHeight || 3);

        x += barWidth + 1;
      }
    };

    renderFrame();
  };

  const handleSubmit = async () => {
    if (!audioBlob) return;
    setIsUploading(true);
    try {
      const entry = await api.submitVoice(audioBlob, "voice_memory.webm", transcript);
      onEntryCreated(entry);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to submit recording");
    } finally {
      setIsUploading(false);
    }
  };

  const handleSimulatedDemoAudio = async () => {
    setIsUploading(true);
    try {
      const dummyBlob = new Blob([new Uint8Array(1024)], { type: "audio/webm" });
      const sampleSpeech = "Had a great review meeting with the team today. We outlined next steps for the project launch and scheduled the follow-up for next Tuesday.";
      const entry = await api.submitVoice(dummyBlob, "simulated_reflection.webm", sampleSpeech);
      onEntryCreated(entry);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "Demo submission failed");
    } finally {
      setIsUploading(false);
    }
  };

  if (!isOpen) return null;

  const formatTime = (sec: number) => {
    const mins = Math.floor(sec / 60);
    const secs = sec % 60;
    return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4">
      <div className="bg-[#fbf7ee] border-2 border-[#cbb79a] rounded-2xl p-6 w-full max-w-md shadow-2xl relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-[#8a6e50] hover:text-[#3d2714] p-1"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="text-center mb-4">
          <div className="w-12 h-12 rounded-full bg-[#e8dac1] text-[#4d3319] flex items-center justify-center mx-auto mb-2 shadow-inner">
            <Mic className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-bold text-[#3d2817] font-serif-title">
            Record Daily Memory
          </h3>
          <p className="text-xs text-[#7d654c]">
            Speak your day naturally. LifeBook transcribes your speech in real time and crafts a warm first-person journal entry.
          </p>
        </div>

        {/* Language Selection */}
        <div className="flex items-center justify-center gap-1.5 mb-3">
          <Globe className="w-3.5 h-3.5 text-[#8a6849]" />
          <span className="text-[11px] text-[#7d654c] font-semibold mr-1">Language:</span>
          {[
            { id: "en-IN", label: "English (India)" },
            { id: "en-US", label: "English (US)" },
            { id: "ta-IN", label: "Tamil (தமிழ்)" }
          ].map((l) => (
            <button
              key={l.id}
              type="button"
              disabled={isRecording}
              onClick={() => setSpeechLang(l.id)}
              className={`text-[11px] px-2.5 py-1 rounded-full border transition-all cursor-pointer ${
                speechLang === l.id
                  ? "bg-[#3d2714] text-amber-100 border-[#3d2714] font-bold shadow-xs"
                  : "bg-[#f2e7d3] text-[#543b23] border-[#d8c5aa] hover:bg-[#eadecb]"
              } disabled:opacity-50`}
            >
              {l.label}
            </button>
          ))}
        </div>

        {/* Live Audio Waveform Canvas */}
        <div className="bg-[#f2e7d3] border border-[#d8c5aa] rounded-xl p-3.5 mb-3.5 flex flex-col items-center justify-center min-h-[100px]">
          <canvas
            ref={canvasRef}
            width={320}
            height={48}
            className="w-full max-w-[320px] h-[48px]"
          />

          <div className="mt-2 text-sm font-mono font-bold text-[#5c3e21]">
            {formatTime(recordingTime)}
          </div>

          {isRecording && (
            <div className="flex items-center gap-1.5 text-xs text-red-600 font-semibold animate-pulse mt-1">
              <span className="w-2 h-2 rounded-full bg-red-600" />
              <span>Recording microphone & transcribing speech...</span>
            </div>
          )}
        </div>

        {/* Live Speech Recognition Box (while recording) */}
        {isRecording && (
          <div className="mb-3.5 p-3.5 bg-emerald-50/90 border border-emerald-300 rounded-xl text-left shadow-inner transition-all">
            <div className="flex items-center justify-between mb-1.5">
              <span className="text-[11px] font-bold uppercase tracking-wider text-emerald-800 flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-600 animate-ping" />
                Live Speech Transcription
              </span>
              <span className="text-[10px] font-medium text-emerald-700 bg-emerald-100/80 px-2 py-0.5 rounded-full">
                Listening ({speechLang === "ta-IN" ? "Tamil" : speechLang === "en-IN" ? "Indian English" : "US English"})
              </span>
            </div>
            <p className="text-xs sm:text-sm font-serif-title text-[#1f351c] min-h-[44px] leading-relaxed italic">
              {transcript ? `"${transcript}"` : "Speak clearly into your microphone... your words will appear here live in real-time."}
            </p>
          </div>
        )}

        {/* Audio Player and Editable Transcript (after recording stops) */}
        {audioUrl && !isRecording && (
          <div className="mb-4 space-y-3">
            <div className="bg-[#eadecb] p-2.5 rounded-xl flex items-center justify-between">
              <div className="flex items-center gap-2 text-xs font-semibold text-[#543b23]">
                <Volume2 className="w-4 h-4 text-emerald-700" />
                <span>Audio Playback</span>
              </div>
              <audio src={audioUrl} controls className="h-8 max-w-[200px]" />
            </div>

            <div className="p-3 bg-white/95 border border-[#d8c5aa] rounded-xl text-left shadow-xs">
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-[11px] font-bold uppercase tracking-wider text-[#7d654c] flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-amber-600" />
                  Transcribed Words (Review or Edit)
                </span>
                <span className="text-[10px] text-emerald-700 font-semibold bg-emerald-50 px-2 py-0.5 rounded-md">
                  {transcript ? "Transcribed" : "Type notes if needed"}
                </span>
              </div>
              <textarea
                value={transcript}
                onChange={(e) => setTranscript(e.target.value)}
                placeholder="Transcribed voice text... You can also edit or add extra details here before sending to AI."
                rows={3}
                className="w-full text-xs sm:text-sm font-serif-title text-[#3d2714] bg-[#fbf7ee] p-2.5 rounded-lg border border-[#e2d2bc] focus:outline-none focus:ring-1 focus:ring-amber-700 resize-none leading-relaxed"
              />
            </div>
          </div>
        )}

        {errorMsg && (
          <div className="mb-4 p-2.5 rounded-lg bg-amber-50 border border-amber-200 text-xs text-amber-900">
            {errorMsg}
          </div>
        )}

        {/* Action Controls */}
        <div className="flex items-center justify-center gap-3 pt-1">
          {!isRecording && !audioBlob && (
            <button
              onClick={startRecording}
              className="flex items-center gap-2 px-6 py-2.5 rounded-full bg-emerald-700 hover:bg-emerald-800 text-white font-semibold text-sm shadow-md transition-all active:scale-95 cursor-pointer"
            >
              <Mic className="w-4 h-4" />
              <span>Start Speaking</span>
            </button>
          )}

          {isRecording && (
            <button
              onClick={stopRecording}
              className="flex items-center gap-2 px-6 py-2.5 rounded-full bg-red-600 hover:bg-red-700 text-white font-semibold text-sm shadow-md transition-all active:scale-95 animate-pulse cursor-pointer"
            >
              <Square className="w-4 h-4 fill-white" />
              <span>Finish Speaking</span>
            </button>
          )}

          {audioBlob && !isRecording && (
            <>
              <button
                onClick={startRecording}
                className="p-2.5 rounded-full bg-[#ebdcc4] hover:bg-[#decbb0] text-[#543b23] transition-colors cursor-pointer"
                title="Re-record"
              >
                <RotateCcw className="w-4 h-4" />
              </button>

              <button
                onClick={handleSubmit}
                disabled={isUploading}
                className="flex items-center gap-2 px-6 py-2.5 rounded-full bg-[#4a321d] hover:bg-[#342211] text-amber-100 font-semibold text-sm shadow-md transition-all active:scale-95 disabled:opacity-50 cursor-pointer"
              >
                <Sparkles className="w-4 h-4 text-amber-400" />
                <span>{isUploading ? "Processing Memory..." : "Understand with AI"}</span>
              </button>
            </>
          )}
        </div>

        {/* Hackathon Fast-Track Button */}
        <div className="mt-4 pt-3 border-t border-[#e5d5be] text-center">
          <button
            onClick={handleSimulatedDemoAudio}
            disabled={isUploading}
            className="text-xs text-[#8c6f52] hover:text-[#4d3319] underline font-medium cursor-pointer"
          >
            ✨ Or test with simulated voice sample
          </button>
        </div>
      </div>
    </div>
  );
};

