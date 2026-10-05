import React, { useState, useEffect, useRef } from "react";
import {
  X,
  User as UserIcon,
  Mail,
  Camera,
  Check,
  LogOut,
  Loader2,
  Upload,
  Image as ImageIcon,
  Trash2,
  Sparkles
} from "lucide-react";
import { useAuth } from "../contexts/AuthContext";
import { UserAvatar } from "./UserAvatar";

interface ProfileModalProps {
  isOpen: boolean;
  onClose: () => void;
}

const PRESET_AVATARS = [
  { label: "Letter Initial", url: "", icon: "🔤" },
  { label: "Quill & Ink", url: "https://images.unsplash.com/photo-1455390582262-044cdead277a?w=160&h=160&fit=crop&crop=faces", icon: "✒️" },
  { label: "Vintage Camera", url: "https://images.unsplash.com/photo-1516035069371-29a1b244cc32?w=160&h=160&fit=crop&crop=faces", icon: "📷" },
  { label: "Botanical Leaf", url: "https://images.unsplash.com/photo-1448375240586-882707db888b?w=160&h=160&fit=crop&crop=faces", icon: "🌿" },
  { label: "Starlit Night", url: "https://images.unsplash.com/photo-1506703719100-a0f3a48c0f86?w=160&h=160&fit=crop&crop=faces", icon: "🌌" },
  { label: "Morning Coffee", url: "https://images.unsplash.com/photo-1509042239860-f550ce710b93?w=160&h=160&fit=crop&crop=faces", icon: "☕" }
];

export const ProfileModal: React.FC<ProfileModalProps> = ({ isOpen, onClose }) => {
  if (!isOpen) return null;

  const { user, updateProfile, uploadAvatar, deleteAvatar, logout } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || user?.name || "");
  const [avatarUrl, setAvatarUrl] = useState(user?.avatar_url || "");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [localPreviewUrl, setLocalPreviewUrl] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [saving, setSaving] = useState(false);
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (user) {
      setFullName(user.full_name || user.name || "");
      setAvatarUrl(user.avatar_url || "");
      setSelectedFile(null);
      setLocalPreviewUrl(null);
    }
  }, [user, isOpen]);

  // Clean up object URL on unmount or file change
  useEffect(() => {
    return () => {
      if (localPreviewUrl && localPreviewUrl.startsWith("blob:")) {
        URL.revokeObjectURL(localPreviewUrl);
      }
    };
  }, [localPreviewUrl]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    processSelectedFile(file);
  };

  const processSelectedFile = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setError("Please select a valid image file (PNG, JPG, WEBP, GIF).");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("Image size exceeds the 10MB limit. Please choose a smaller photo.");
      return;
    }

    setError(null);
    setSelectedFile(file);
    const objectUrl = URL.createObjectURL(file);
    setLocalPreviewUrl(objectUrl);
    setAvatarUrl(objectUrl);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) {
      processSelectedFile(file);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleSelectPreset = (url: string) => {
    setSelectedFile(null);
    setLocalPreviewUrl(null);
    setAvatarUrl(url);
    setError(null);
  };

  const handleResetToInitial = () => {
    setSelectedFile(null);
    setLocalPreviewUrl(null);
    setAvatarUrl("");
    setError(null);
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!fullName.trim()) {
      setError("Full name cannot be empty.");
      return;
    }

    setSaving(true);
    setError(null);
    try {
      if (selectedFile) {
        // 1. Upload chosen local image file
        await uploadAvatar(selectedFile);
        // 2. Update name if changed
        if (fullName.trim() !== (user?.full_name || user?.name)) {
          await updateProfile({ full_name: fullName.trim() });
        }
      } else if (!avatarUrl) {
        // User explicitly reset avatar to initial badge
        if (user?.avatar_url) {
          await deleteAvatar();
        }
        await updateProfile({
          full_name: fullName.trim(),
          avatar_url: ""
        });
      } else {
        // User selected a preset or kept existing avatar
        await updateProfile({
          full_name: fullName.trim(),
          avatar_url: avatarUrl.startsWith("blob:") ? undefined : avatarUrl
        });
      }

      setSavedSuccess(true);
      setTimeout(() => {
        setSavedSuccess(false);
        onClose();
      }, 1100);
    } catch (err: any) {
      setError(err.message || "Failed to update profile. Please try again.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-xs p-4 animate-in fade-in">
      <div className="bg-[#faf5eb] border-2 border-[#caa777] rounded-2xl w-full max-w-md shadow-2xl overflow-hidden relative text-[#2c1a0e] max-h-[92vh] flex flex-col">
        {/* Header Ribbon */}
        <div className="leather-spine px-6 py-3.5 flex items-center justify-between text-amber-100 border-b border-[#432313] relative select-none shrink-0">
          <div className="flex items-center gap-2.5">
            <UserIcon className="w-5 h-5 text-[#dfba78]" />
            <h3 className="text-base sm:text-lg font-serif-title font-bold text-[#f8efe2]">
              Your Profile
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-full text-amber-200/70 hover:text-amber-100 hover:bg-white/10 transition-colors cursor-pointer"
            title="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Scrollable Form Body */}
        <form onSubmit={handleSave} className="p-5 sm:p-6 space-y-4 sm:space-y-5 overflow-y-auto flex-1">
          {/* Avatar Preview & Local Upload Card */}
          <div className="flex flex-col items-center gap-3">
            <div className="relative group">
              <UserAvatar
                name={fullName || "User"}
                avatarUrl={localPreviewUrl || avatarUrl}
                size="xl"
                className="ring-4 ring-[#e5d5be] shadow-md"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                className="absolute bottom-0 right-0 p-1.5 bg-[#3e2516] hover:bg-[#28150a] text-amber-200 rounded-full border-2 border-[#faf5eb] shadow-md transition-transform hover:scale-110 cursor-pointer"
                title="Choose photo from device"
              >
                <Camera className="w-4 h-4" />
              </button>
            </div>

            <p className="text-xs text-[#82644a] italic text-center">
              {selectedFile
                ? `Local photo selected: ${selectedFile.name}`
                : avatarUrl
                ? "Custom profile photo active"
                : "Displaying your initials badge"}
            </p>

            {/* Hidden Native File Input */}
            <input
              type="file"
              ref={fileInputRef}
              accept="image/png,image/jpeg,image/jpg,image/webp,image/gif"
              onChange={handleFileChange}
              className="hidden"
            />

            {/* Local Device Photo Picker Area */}
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={`w-full p-3.5 rounded-xl border-2 border-dashed transition-all flex flex-col items-center justify-center gap-2 text-center ${
                isDragging
                  ? "border-amber-600 bg-amber-50/80 scale-[0.99]"
                  : "border-[#d8c5ad] bg-[#f4ebd9]/60 hover:bg-[#f4ebd9]"
              }`}
            >
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => fileInputRef.current?.click()}
                  className="px-4 py-2 bg-[#3e2516] hover:bg-[#28150a] text-amber-100 rounded-xl text-xs font-bold shadow-xs hover:shadow-md transition-all flex items-center gap-1.5 cursor-pointer active:scale-95 border border-[#5a361e]"
                >
                  <Upload className="w-3.5 h-3.5 text-amber-300" />
                  <span>Choose Photo from Device</span>
                </button>

                {(avatarUrl || selectedFile) && (
                  <button
                    type="button"
                    onClick={handleResetToInitial}
                    className="px-3 py-2 bg-white/80 hover:bg-white text-[#6b4728] border border-[#d8c5ad] rounded-xl text-xs font-semibold transition-colors flex items-center gap-1 cursor-pointer"
                    title="Reset to Initial Badge"
                  >
                    <Trash2 className="w-3.5 h-3.5 text-red-600" />
                    <span>Reset</span>
                  </button>
                )}
              </div>

              <p className="text-[11px] text-[#856b54]">
                or drag & drop your photo here (PNG, JPG, WEBP up to 10MB)
              </p>
            </div>

            {/* Journal Themed Presets */}
            <div className="w-full bg-[#f3e9d8] p-3 rounded-xl border border-[#ded0bc] space-y-2">
              <label className="block text-[11px] font-bold uppercase tracking-wider text-[#6e4e33]">
                Or Choose a Journal Theme
              </label>
              <div className="grid grid-cols-3 gap-2">
                {PRESET_AVATARS.map((preset) => {
                  const isSelected = !selectedFile && preset.url === avatarUrl;
                  return (
                    <button
                      key={preset.label}
                      type="button"
                      onClick={() => handleSelectPreset(preset.url)}
                      className={`px-2 py-2 rounded-lg text-xs font-medium border flex items-center justify-center gap-1.5 transition-all cursor-pointer ${
                        isSelected
                          ? "bg-[#382112] text-amber-200 border-[#693e21] shadow-xs"
                          : "bg-white/80 hover:bg-white text-[#4a3423] border-[#ded0bc]"
                      }`}
                    >
                      <span>{preset.icon}</span>
                      <span className="truncate">{preset.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Form Fields */}
          <div className="space-y-3.5">
            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#6e4e33] mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                placeholder="Your Name"
                className="w-full px-3.5 py-2.5 bg-white border border-[#ded0bb] rounded-xl text-xs sm:text-sm text-[#2c190f] focus:outline-none focus:border-[#7d5635] shadow-2xs"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold uppercase tracking-wider text-[#6e4e33] mb-1">
                Email Address
              </label>
              <div className="flex items-center gap-2 px-3.5 py-2.5 bg-[#ece0ce]/60 border border-[#ded0bb] rounded-xl text-xs sm:text-sm text-[#664d36]">
                <Mail className="w-4 h-4 text-[#8a6e54] shrink-0" />
                <span className="truncate">{user?.email}</span>
                <span className="ml-auto text-[10px] uppercase font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full">
                  Verified
                </span>
              </div>
            </div>
          </div>

          {/* Error & Success Messages */}
          {error && (
            <div className="p-2.5 rounded-xl bg-red-100 border border-red-200 text-red-800 text-xs">
              {error}
            </div>
          )}

          {savedSuccess && (
            <div className="p-2.5 rounded-xl bg-emerald-100 border border-emerald-300 text-emerald-800 text-xs flex items-center justify-center gap-1.5 font-semibold">
              <Check className="w-4 h-4" /> Profile updated successfully!
            </div>
          )}

          {/* Action Buttons */}
          <div className="pt-2 flex items-center justify-between gap-3">
            <button
              type="button"
              onClick={() => {
                logout();
                onClose();
              }}
              className="px-3.5 py-2 rounded-xl border border-red-200 bg-red-50 hover:bg-red-100 text-red-800 text-xs font-semibold flex items-center gap-1.5 transition-colors cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>Sign Out</span>
            </button>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-3.5 py-2 rounded-xl border border-[#d2c0aa] text-[#5e432c] hover:bg-[#ede0ce] text-xs font-semibold transition-colors cursor-pointer"
              >
                Cancel
              </button>

              <button
                type="submit"
                disabled={saving}
                className="px-5 py-2 rounded-xl bg-[#352012] hover:bg-[#251509] text-amber-100 font-bold text-xs sm:text-sm shadow-md transition-all active:scale-95 disabled:opacity-60 flex items-center gap-1.5 cursor-pointer border border-[#52301a]"
              >
                {saving ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin text-amber-300" />
                    <span>Saving...</span>
                  </>
                ) : (
                  <>
                    <Check className="w-4 h-4 text-amber-300" />
                    <span>Save Changes</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
};
