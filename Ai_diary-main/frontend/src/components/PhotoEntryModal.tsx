import React, { useState } from "react";
import { X, Image as ImageIcon, Sparkles, Upload } from "lucide-react";
import { api } from "../services/api";
import { DiaryEntry } from "../types";

interface PhotoEntryModalProps {
  isOpen: boolean;
  onClose: () => void;
  onEntryCreated: (entry: DiaryEntry) => void;
}

export const PhotoEntryModal: React.FC<PhotoEntryModalProps> = ({
  isOpen,
  onClose,
  onEntryCreated
}) => {
  if (!isOpen) return null;

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [caption, setCaption] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  };

  const handleSubmit = async () => {
    if (!selectedFile) return;
    setIsSubmitting(true);
    setErrorMsg(null);
    try {
      const entry = await api.submitPhoto(selectedFile, caption);
      onEntryCreated(entry);
      onClose();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to upload photo");
    } finally {
      setIsSubmitting(false);
    }
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

        <div className="flex items-center gap-2 mb-4">
          <div className="p-2 rounded-lg bg-[#ebdcc4] text-[#543820]">
            <ImageIcon className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-lg font-bold text-[#3d2817] font-serif-title">
              Add Photo Memory
            </h3>
            <p className="text-xs text-[#7d654c]">
              Upload a picture from your day. AI extracts scenes, context, and objects.
            </p>
          </div>
        </div>

        {errorMsg && (
          <div className="mb-4 p-2.5 rounded-lg bg-red-50 border border-red-200 text-xs text-red-800">
            {errorMsg}
          </div>
        )}

        <div className="mb-4">
          {previewUrl ? (
            <div className="relative rounded-xl overflow-hidden border border-[#d8c5aa] bg-black/5 max-h-56 flex items-center justify-center">
              <img src={previewUrl} alt="Upload preview" className="object-cover w-full max-h-56" />
              <button
                onClick={() => {
                  setSelectedFile(null);
                  setPreviewUrl(null);
                }}
                className="absolute top-2 right-2 p-1 rounded-full bg-black/70 text-white hover:bg-black"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <label className="border-2 border-dashed border-[#cbb79a] hover:border-[#543820] rounded-xl p-8 flex flex-col items-center justify-center cursor-pointer bg-white/40 hover:bg-white/70 transition-colors">
              <Upload className="w-8 h-8 text-[#8a6e50] mb-2" />
              <span className="text-xs font-semibold text-[#543820]">Choose photo or drag here</span>
              <span className="text-[10px] text-[#9c8266] mt-1">PNG, JPG, WEBP up to 10MB</span>
              <input type="file" accept="image/*" onChange={handleFileChange} className="hidden" />
            </label>
          )}
        </div>

        <input
          type="text"
          value={caption}
          onChange={(e) => setCaption(e.target.value)}
          placeholder="Caption or note (e.g., Sunset by the lake, Team dinner)..."
          className="w-full px-3.5 py-2.5 bg-white border border-[#d8c5aa] rounded-xl text-xs text-[#3d2714] placeholder-[#a6927d] mb-4 focus:outline-none focus:border-[#543820]"
        />

        <div className="flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-xl text-xs font-semibold text-[#7d654c] hover:bg-[#ebdcc4]"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={isSubmitting || !selectedFile}
            className="flex items-center gap-1.5 px-5 py-2.5 rounded-xl text-xs font-bold text-white bg-[#543820] hover:bg-[#3d2714] shadow-md transition-all active:scale-95 disabled:opacity-50"
          >
            <Sparkles className="w-4 h-4 text-amber-300" />
            <span>{isSubmitting ? "Uploading..." : "Save Photo Memory"}</span>
          </button>
        </div>
      </div>
    </div>
  );
};
