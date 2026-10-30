import React, { useState, useEffect } from "react";
import { X, Image as ImageIcon, Plus, Calendar, Tag, ZoomIn, Sparkles } from "lucide-react";
import { api } from "../services/api";
import { PhotoItem } from "../types";

interface PhotosModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenPhotoEntry: () => void;
}

export const PhotosModal: React.FC<PhotosModalProps> = ({
  isOpen,
  onClose,
  onOpenPhotoEntry
}) => {
  if (!isOpen) return null;

  const [photos, setPhotos] = useState<PhotoItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>("All");
  const [lightboxPhoto, setLightboxPhoto] = useState<PhotoItem | null>(null);

  useEffect(() => {
    async function loadPhotos() {
      try {
        setLoading(true);
        const data = await api.getPhotos();
        setPhotos(data);
      } catch (err) {
        console.error("Failed to load photos:", err);
      } finally {
        setLoading(false);
      }
    }
    loadPhotos();
  }, []);

  const categories = ["All", ...Array.from(new Set(photos.map((p) => p.category).filter(Boolean)))];

  const filteredPhotos = selectedCategory === "All"
    ? photos
    : photos.filter((p) => p.category === selectedCategory);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-xs p-4 sm:p-6 select-none animate-fadeIn">
      <div className="bg-[#fcf8f0] border-2 border-[#cfbeaa] rounded-2xl w-full max-w-5xl h-[88vh] shadow-2xl flex flex-col relative overflow-hidden">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 px-6 py-4 border-b border-[#e5d5be] bg-[#f5ecda]">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-[#80502c]/10 border border-[#80502c]/30 flex items-center justify-center text-[#80502c]">
              <ImageIcon className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h3 className="text-xl font-bold font-serif-title text-[#3a2514]">
                  Photo Memories & Scrapbook
                </h3>
                <span className="px-2 py-0.5 rounded-full bg-[#ebdcc4] text-[#4d3319] text-xs font-semibold">
                  {photos.length} photos
                </span>
              </div>
              <p className="text-xs text-[#705439]">
                Visual moments captured across your daily journeys, milestones, and reflections.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                onClose();
                onOpenPhotoEntry();
              }}
              className="px-3 py-1.5 bg-[#80502c] hover:bg-[#663d1e] text-[#f7eedc] rounded-lg text-xs font-medium flex items-center gap-1.5 shadow-sm transition-all cursor-pointer"
            >
              <Plus className="w-4 h-4" />
              <span>Add Photo Memory</span>
            </button>
            <button
              onClick={onClose}
              className="p-1.5 text-[#8c7155] hover:text-[#382312] rounded-lg hover:bg-black/5 transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Category Filter Pills */}
        <div className="px-6 py-2.5 bg-[#faf4e8] border-b border-[#ebdcc4] flex items-center gap-1.5 overflow-x-auto text-xs">
          <Tag className="w-3.5 h-3.5 text-[#8a6849] mr-1 shrink-0" />
          {categories.map((cat) => (
            <button
              key={cat}
              onClick={() => setSelectedCategory(cat)}
              className={`px-3 py-1 rounded-full whitespace-nowrap transition-all cursor-pointer ${
                selectedCategory === cat
                  ? "bg-[#80502c] text-[#fbf7ee] font-semibold shadow-xs"
                  : "bg-white/60 text-[#73563a] hover:bg-white border border-[#e0cfba]"
              }`}
            >
              {cat}
            </button>
          ))}
        </div>

        {/* Photos Grid / Scrapbook View */}
        <div className="flex-1 p-6 overflow-y-auto bg-[#f8f3ea]">
          {loading ? (
            <div className="h-full flex items-center justify-center text-sm text-[#8a6849]">
              <Sparkles className="w-5 h-5 animate-spin mr-2" />
              Opening Photo Album...
            </div>
          ) : filteredPhotos.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8">
              <div className="w-16 h-16 rounded-full bg-[#f0e3ce] flex items-center justify-center text-[#8a6849] mb-3">
                <ImageIcon className="w-8 h-8" />
              </div>
              <h4 className="text-base font-bold text-[#3d2714] font-serif-title mb-1">
                No Photos in this Category
              </h4>
              <p className="text-xs text-[#705439] max-w-sm mb-4">
                Capture snapshots of people, food, projects, or travels and attach them directly to your memories.
              </p>
              <button
                onClick={() => {
                  onClose();
                  onOpenPhotoEntry();
                }}
                className="px-4 py-2 bg-[#80502c] text-[#fbf7ee] rounded-lg text-xs font-semibold cursor-pointer"
              >
                Upload First Photo
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-6">
              {filteredPhotos.map((photo, idx) => (
                <div
                  key={photo.id}
                  onClick={() => setLightboxPhoto(photo)}
                  className={`group relative bg-white p-3 pt-3 pb-4 rounded shadow-md border border-[#d8c8b4] transform transition-all duration-300 hover:-translate-y-1 hover:shadow-xl hover:rotate-0 cursor-pointer ${
                    idx % 3 === 0 ? "-rotate-1" : idx % 3 === 1 ? "rotate-1" : "-rotate-2"
                  }`}
                >
                  {/* Washi Tape Corner Decoration */}
                  <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-16 h-4 bg-[#e8d8be]/80 border-t border-b border-[#cfbeaa] shadow-xs transform -rotate-1 pointer-events-none opacity-85" />

                  {/* Polaroid Image */}
                  <div className="relative aspect-4/3 overflow-hidden rounded bg-[#1e140d] mb-2.5">
                    <img
                      src={photo.url}
                      alt={photo.title}
                      className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-105"
                      onError={(e) => {
                        (e.target as HTMLImageElement).src =
                          "https://images.unsplash.com/photo-1522071820081-009f0129c71c?w=500&auto=format&fit=crop&q=80";
                      }}
                    />
                    <div className="absolute inset-0 bg-black/30 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white">
                      <ZoomIn className="w-6 h-6 drop-shadow-md" />
                    </div>
                    {photo.category && (
                      <span className="absolute bottom-1.5 left-1.5 px-2 py-0.5 rounded bg-black/65 text-white text-[10px] font-medium backdrop-blur-xs">
                        {photo.category}
                      </span>
                    )}
                  </div>

                  {/* Handwriting Caption */}
                  <div className="space-y-1">
                    <h4 className="text-xs font-bold text-[#352010] font-serif-title truncate group-hover:text-amber-900 transition-colors">
                      {photo.title}
                    </h4>
                    <p className="text-[11px] text-[#6b5038] font-handwriting line-clamp-2 leading-tight">
                      "{photo.caption || photo.title}"
                    </p>
                    <div className="flex items-center justify-between text-[10px] text-[#8f755c] pt-1 border-t border-[#f0e3ce]">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        {photo.date}
                      </span>
                      {photo.mood && (
                        <span className="capitalize text-amber-800 font-medium">
                          ✨ {photo.mood}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Polaroid Lightbox Modal */}
        {lightboxPhoto && (
          <div
            onClick={() => setLightboxPhoto(null)}
            className="fixed inset-0 z-60 bg-black/85 backdrop-blur-sm flex items-center justify-center p-4"
          >
            <div
              onClick={(e) => e.stopPropagation()}
              className="bg-white p-4 pb-6 rounded-lg max-w-xl w-full shadow-2xl border-4 border-[#efe7d8] relative"
            >
              <button
                onClick={() => setLightboxPhoto(null)}
                className="absolute top-2 right-2 p-1.5 rounded-full bg-black/50 text-white hover:bg-black/70 cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>

              <div className="rounded overflow-hidden bg-black mb-4 max-h-[60vh] flex items-center justify-center">
                <img
                  src={lightboxPhoto.url}
                  alt={lightboxPhoto.title}
                  className="max-h-[60vh] w-auto object-contain"
                />
              </div>

              <div className="px-2">
                <div className="flex items-center justify-between mb-1">
                  <h3 className="text-base font-bold font-serif-title text-[#2b180a]">
                    {lightboxPhoto.title}
                  </h3>
                  <span className="text-xs text-[#8a6849] font-medium">
                    {lightboxPhoto.date}
                  </span>
                </div>
                <p className="text-sm font-handwriting text-[#5a3f28] leading-relaxed mb-3">
                  "{lightboxPhoto.caption}"
                </p>
                <div className="flex items-center gap-2 text-xs">
                  <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-900 font-medium">
                    📍 {lightboxPhoto.category}
                  </span>
                  {lightboxPhoto.mood && (
                    <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-900 font-medium">
                      Mood: {lightboxPhoto.mood}
                    </span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
