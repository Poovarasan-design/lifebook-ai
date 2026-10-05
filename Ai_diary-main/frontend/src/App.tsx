import React, { useState, useEffect } from "react";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import { api } from "./services/api";
import { DiaryEntry, Commitment, Routine, NotificationItem } from "./types";
import { LeatherSpineNav } from "./components/LeatherSpineNav";
import { JournalLeftPage } from "./components/JournalLeftPage";
import { JournalRightPage } from "./components/JournalRightPage";
import { VoiceRecorderModal } from "./components/VoiceRecorderModal";
import { TextEntryModal } from "./components/TextEntryModal";
import { PhotoEntryModal } from "./components/PhotoEntryModal";
import { DraftReviewModal } from "./components/DraftReviewModal";
import { LifeGraphModal } from "./components/LifeGraphModal";
import { PhotosModal } from "./components/PhotosModal";
import { InsightsModal } from "./components/InsightsModal";
import { CalendarMemoriesModal } from "./components/CalendarMemoriesModal";
import { AskLifeBookWidget } from "./components/AskLifeBookWidget";
import { SettingsModal } from "./components/SettingsModal";
import { PrivacyModal } from "./components/PrivacyModal";
import { CinematicLoader } from "./components/CinematicLoader";
import { AdminModal } from "./components/AdminModal";
import { ProfileModal } from "./components/ProfileModal";
import { UserAvatar } from "./components/UserAvatar";
import { AuthScreen } from "./components/AuthScreen";
import { Menu, BookOpen } from "lucide-react";

export const AppContent: React.FC = () => {
  const { user, isAuthenticated, loading } = useAuth();

  // Navigation State
  const [currentTab, setCurrentTab] = useState("today");
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mobilePageTab, setMobilePageTab] = useState<"left" | "right">("left");

  // Modals
  const [calendarModalOpen, setCalendarModalOpen] = useState(false);
  const [voiceModalOpen, setVoiceModalOpen] = useState(false);
  const [textModalOpen, setTextModalOpen] = useState(false);
  const [photoModalOpen, setPhotoModalOpen] = useState(false);
  const [photosModalOpen, setPhotosModalOpen] = useState(false);
  const [insightsModalOpen, setInsightsModalOpen] = useState(false);
  const [graphModalOpen, setGraphModalOpen] = useState(false);
  const [settingsModalOpen, setSettingsModalOpen] = useState(false);
  const [privacyModalOpen, setPrivacyModalOpen] = useState(false);
  const [adminModalOpen, setAdminModalOpen] = useState(false);
  const [reviewModalOpen, setReviewModalOpen] = useState(false);
  const [profileModalOpen, setProfileModalOpen] = useState(false);

  // Active Data
  const [entries, setEntries] = useState<DiaryEntry[]>([]);
  const [activeEntry, setActiveEntry] = useState<DiaryEntry | null>(null);
  const [commitments, setCommitments] = useState<Commitment[]>([]);
  const [routines, setRoutines] = useState<Routine[]>([]);
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [showNotifications, setShowNotifications] = useState(false);
  const [onThisDay, setOnThisDay] = useState<any>(null);

  // Search input state
  const [searchQuery, setSearchQuery] = useState("");

  // Mood selection
  const [selectedMood, setSelectedMood] = useState<string>("fulfilled");

  useEffect(() => {
    if (user) {
      loadData();
    } else {
      setEntries([]);
      setActiveEntry(null);
      setCommitments([]);
      setRoutines([]);
      setNotifications([]);
      setOnThisDay(null);
    }
  }, [user]);

  const loadData = async () => {
    try {
      const [allEntries, allCommitments, allRoutines, allNotifs, otd] = await Promise.all([
        api.getEntries().catch(() => []),
        api.getCommitments().catch(() => []),
        api.getRoutines().catch(() => []),
        api.getNotifications().catch(() => []),
        api.getOnThisDay().catch(() => null)
      ]);

      setEntries(allEntries);
      if (allEntries.length > 0) {
        setActiveEntry(allEntries[0]);
      }
      setCommitments(allCommitments);
      setRoutines(allRoutines);
      setNotifications(allNotifs);
      setOnThisDay(otd);
    } catch (err) {
      console.error("Failed to load initial data", err);
    }
  };

  const handleEntryCreated = (newEntry: DiaryEntry) => {
    setActiveEntry(newEntry);
    setEntries((prev) => [newEntry, ...prev]);

    // Poll status until DRAFTED or USER_REVIEW
    let attempts = 0;
    const interval = setInterval(async () => {
      attempts++;
      try {
        const statusRes = await api.getEntryStatus(newEntry.id);
        setActiveEntry((prev) => prev ? {
          ...prev,
          status: statusRes.status,
          status_history: statusRes.history,
          title: statusRes.title || prev.title,
          generated_content: statusRes.generated_content || prev.generated_content,
          disambiguation: statusRes.disambiguation
        } : null);

        if (statusRes.status === "USER_REVIEW" || statusRes.status === "DRAFTED") {
          clearInterval(interval);
          setReviewModalOpen(true);
        } else if (statusRes.status === "COMPLETED" || attempts > 20) {
          clearInterval(interval);
        }
      } catch (e) {
        clearInterval(interval);
      }
    }, 1500);
  };

  const [isRegenerating, setIsRegenerating] = useState(false);

  const handleRetryProcessing = async () => {
    if (!activeEntry) return;
    try {
      const updated = await api.retryEntryProcessing(activeEntry.id);
      handleEntryCreated(updated);
    } catch (e) {
      console.error("Retry processing failed:", e);
    }
  };

  const handleRegenerateEntry = async (tone = "reflective") => {
    let targetEntry = activeEntry;
    if (!targetEntry && entries.length > 0) {
      targetEntry = entries[0];
    }
    if (!targetEntry) {
      return;
    }

    setIsRegenerating(true);
    try {
      const updated = await api.regenerateEntry(targetEntry.id, tone);
      setActiveEntry(updated);
      setEntries((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
    } catch (e) {
      console.error("Regeneration failed:", e);
    } finally {
      setIsRegenerating(false);
    }
  };

  const handleEntryConfirmed = async (updated: DiaryEntry) => {
    setActiveEntry(updated);
    setEntries((prev) => prev.map((e) => (e.id === updated.id ? updated : e)));
    const comms = await api.getCommitments().catch(() => []);
    setCommitments(comms);
  };

  const handleMarkDone = async (id: string) => {
    try {
      await api.completeCommitment(id);
      setCommitments((prev) =>
        prev.map((c) => (c.id === id ? { ...c, status: "COMPLETED" } : c))
      );
    } catch (err) {
      console.error(err);
    }
  };

  const handleMarkNotificationRead = async (id: string) => {
    try {
      await api.markNotificationRead(id);
      setNotifications((prev) =>
        prev.map((n) => (n.id === id ? { ...n, is_read: true } : n))
      );
    } catch (err) {
      console.error("Failed to mark notification read", err);
    }
  };

  const handleMarkAllNotificationsRead = async () => {
    try {
      await api.markAllNotificationsRead();
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (err) {
      console.error("Failed to mark all notifications read", err);
    }
  };

  const handleDismissNotification = async (id: string) => {
    try {
      await api.dismissNotification(id);
      setNotifications((prev) => prev.filter((n) => n.id !== id));
    } catch (err) {
      console.error("Failed to dismiss notification", err);
    }
  };

  const handleNavSelect = (tab: string) => {
    setCurrentTab(tab);
    setMobileMenuOpen(false);
    if (tab === "graph") setGraphModalOpen(true);
    else if (tab === "photos") setPhotosModalOpen(true);
    else if (tab === "insights") setInsightsModalOpen(true);
    else if (tab === "memories") setCalendarModalOpen(true);
    else if (tab === "privacy") setPrivacyModalOpen(true);
    else if (tab === "settings") setSettingsModalOpen(true);
    else if (tab === "admin") setAdminModalOpen(true);
    else if (tab === "add_memory") setVoiceModalOpen(true);
    else if (tab === "commitments") setMobilePageTab("right");
    else if (tab === "today") setMobilePageTab("left");
  };

  const pendingCommitments = commitments.filter((c) => c.status === "PENDING");

  if (loading) {
    return (
      <CinematicLoader
        message="Opening your personal LifeBook..."
        submessage="Illuminating your memories, reflections, and life journey"
      />
    );
  }

  if (!isAuthenticated || !user) {
    return <AuthScreen />;
  }

  return (
    <div className="min-h-screen desk-surface text-[#2c2016] flex items-center justify-center p-2 sm:p-4 md:p-6 lg:p-8 font-sans antialiased relative overflow-x-hidden select-text">
      {/* ======================================================== */}
      {/* DESK ENVIRONMENT ACCESSORIES MATCHING REFERENCE IMAGE    */}
      {/* ======================================================== */}

      {/* 1. TOP-RIGHT PINNED STICKY NOTE */}
      <div className="hidden lg:block fixed top-6 right-6 xl:right-10 z-10 pointer-events-none transform rotate-3">
        <div className="sticky-note p-3.5 w-38 xl:w-42 rounded-xs text-center font-handwriting text-[#46331a] relative shadow-lg">
          {/* Brass Pushpin */}
          <div className="absolute -top-2.5 left-1/2 -translate-x-1/2 w-3.5 h-3.5 rounded-full bg-gradient-to-br from-amber-200 via-amber-400 to-amber-700 shadow-md border border-amber-900/40" />
          <p className="text-base font-bold leading-snug">
            "Small moments make a big life."
          </p>
          <p className="text-sm font-bold mt-0.5">:)</p>
        </div>
      </div>

      {/* 2. BOTTOM-LEFT COFFEE CUP ON NOTEPAD */}
      <div className="hidden lg:flex fixed bottom-3 left-4 xl:left-8 z-10 pointer-events-none items-end gap-0">
        {/* Folded paper note */}
        <div className="transform -rotate-6 bg-[#f7eedc] p-2.5 pb-4 rounded-xs shadow-md border border-[#dfceb7] w-32 xl:w-36 text-center font-handwriting text-[#4a341e] relative -mr-10 mb-1.5">
          <p className="text-xs xl:text-sm font-bold leading-tight">
            Good Stories<br />
            Build<br />
            A Better<br />
            You. :)
          </p>
        </div>

        {/* Real Ceramic Coffee Cup with Latte Art on Ceramic Saucer */}
        <div className="w-24 h-24 xl:w-28 xl:h-28 rounded-full shadow-[0_15px_30px_rgba(0,0,0,0.85)] border-2 border-[#b8a088]/40 relative z-10 bg-[#e8ded1] flex items-center justify-center p-1">
          <img
            src="/assets/coffee_cup.png"
            alt="Coffee with latte art"
            className="w-full h-full object-contain rounded-full drop-shadow-md"
          />
        </div>
      </div>

      {/* 3. BOTANICAL LEAF BRANCH BESIDE LEATHER SPINE */}
      <div className="hidden xl:block fixed top-1/3 left-4 2xl:left-8 z-25 pointer-events-none transform -rotate-12 opacity-90 drop-shadow-md">
        <svg className="w-14 h-32 text-[#5b7a54]" viewBox="0 0 60 140" fill="currentColor">
          <path d="M30 140 Q 28 80 30 10" stroke="#486342" strokeWidth="2.5" fill="none" />
          <ellipse cx="20" cy="30" rx="9" ry="5" transform="rotate(-30 20 30)" />
          <ellipse cx="40" cy="45" rx="10" ry="5" transform="rotate(25 40 45)" />
          <ellipse cx="18" cy="65" rx="11" ry="6" transform="rotate(-35 18 65)" />
          <ellipse cx="42" cy="80" rx="11" ry="6" transform="rotate(30 42 80)" />
          <ellipse cx="19" cy="100" rx="10" ry="5" transform="rotate(-25 19 100)" />
          <ellipse cx="40" cy="115" rx="9" ry="5" transform="rotate(20 40 115)" />
          <ellipse cx="30" cy="12" rx="7" ry="4" transform="rotate(80 30 12)" />
        </svg>
      </div>

      {/* 4. LUXURIOUS FOUNTAIN PEN ON BOTTOM DESK */}
      <div className="hidden xl:block fixed bottom-3 left-1/2 -translate-x-1/2 z-10 pointer-events-none transform -rotate-6 drop-shadow-2xl">
        <div className="w-56 h-3.5 bg-gradient-to-r from-[#151210] via-[#2c1d14] to-[#120f0e] rounded-full shadow-2xl border border-yellow-600/50 relative flex items-center">
          <div className="absolute right-14 w-2 h-3.5 bg-gradient-to-b from-yellow-300 via-yellow-500 to-yellow-600" />
          <div className="absolute left-6 -top-0.5 w-16 h-1 bg-yellow-400 rounded-sm shadow-sm" />
          <div className="absolute -right-2.5 w-3.5 h-2.5 bg-gradient-to-r from-yellow-500 to-yellow-300 transform rotate-45 border-r border-t border-yellow-200" />
        </div>
      </div>

      {/* ======================================================== */}
      {/* THE PHYSICAL OPEN BOOK CASING (LEATHER COVER + TWO PAGES) */}
      {/* ======================================================== */}
      <div className="w-full max-w-[1240px] book-outer-casing rounded-2xl overflow-hidden leather-outer-frame flex flex-col md:flex-row relative z-20 my-auto">
        
        {/* Mobile Top App Bar (visible on small screens) */}
        <div className="md:hidden flex items-center justify-between px-4 py-3 bg-[#2d180d] text-amber-100 border-b border-[#4d2816]">
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-1.5 rounded-lg bg-black/30 text-amber-200"
              title="Open Navigation"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="flex items-center gap-1.5">
              <BookOpen className="w-5 h-5 text-amber-400" />
              <span className="font-bold text-base font-book-brand tracking-wide text-amber-200">
                LifeBook AI
              </span>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => setVoiceModalOpen(true)}
              className="px-3 py-1 bg-[#3b7b54] text-white rounded-full text-xs font-semibold"
            >
              + Speak
            </button>
            <UserAvatar
              user={user}
              size="xs"
              onClick={() => setProfileModalOpen(true)}
              className="cursor-pointer hover:scale-105 transition-transform"
            />
          </div>
        </div>

        {/* Mobile Page Tab Switcher */}
        <div className="lg:hidden flex items-center bg-[#ebdcc4] border-b border-[#d8c7ad] p-1.5 gap-1.5">
          <button
            onClick={() => setMobilePageTab("left")}
            className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-bold transition-all text-center ${
              mobilePageTab === "left"
                ? "bg-[#faf5eb] text-[#352010] shadow-xs"
                : "text-[#70553e]"
            }`}
          >
            📖 Today's Diary
          </button>
          <button
            onClick={() => setMobilePageTab("right")}
            className={`flex-1 py-1.5 px-3 rounded-lg text-xs font-bold transition-all text-center flex items-center justify-center gap-1.5 ${
              mobilePageTab === "right"
                ? "bg-[#faf5eb] text-[#352010] shadow-xs"
                : "text-[#70553e]"
            }`}
          >
            <span>📋 Tasks & Routines</span>
            {pendingCommitments.length > 0 && (
              <span className="px-1.5 py-0.2 bg-[#d93829] text-white text-[10px] rounded-full">
                {pendingCommitments.length}
              </span>
            )}
          </button>
        </div>

        {/* Left Leather Spine Navigation Sidebar */}
        <LeatherSpineNav
          currentTab={currentTab}
          onSelectTab={handleNavSelect}
          pendingCommitmentsCount={pendingCommitments.length}
          isOpenMobile={mobileMenuOpen}
          onCloseMobile={() => setMobileMenuOpen(false)}
          onOpenProfile={() => setProfileModalOpen(true)}
        />

        {/* Double Open Journal Pages (Left Page and Right Page) */}
        <main className="flex-1 journal-spread-container paper-stack-edge flex flex-col lg:flex-row divide-y lg:divide-y-0 lg:divide-x divide-[#e2d3bb] book-gutter-crease min-h-[82vh] lg:min-h-[840px] max-h-[92vh]">
          {/* Left Page */}
          <div className={`${mobilePageTab === "left" ? "block" : "hidden"} lg:block flex-1 journal-left-page overflow-y-auto`}>
            <JournalLeftPage
              user={user}
              activeEntry={activeEntry}
              onOpenVoice={() => setVoiceModalOpen(true)}
              onOpenText={() => setTextModalOpen(true)}
              onOpenPhoto={() => setPhotoModalOpen(true)}
              onOpenReview={() => setReviewModalOpen(true)}
              onRetryProcessing={handleRetryProcessing}
              onRegenerate={handleRegenerateEntry}
              isRegenerating={isRegenerating}
              onOpenPhotos={() => setPhotosModalOpen(true)}
              onOpenGraph={() => setGraphModalOpen(true)}
              onOpenCalendar={() => setCalendarModalOpen(true)}
              onTellMeMore={() => setInsightsModalOpen(true)}
            />
          </div>

          {/* Right Page */}
          <div className={`${mobilePageTab === "right" ? "block" : "hidden"} lg:block flex-1 journal-right-page overflow-y-auto`}>
            <JournalRightPage
              user={user}
              searchQuery={searchQuery}
              onSearchChange={setSearchQuery}
              pendingCommitments={pendingCommitments}
              routines={routines}
              onMarkDone={handleMarkDone}
              onViewAllCommitments={() => setGraphModalOpen(true)}
              onViewAllRoutines={() => setInsightsModalOpen(true)}
              onOpenPhotos={() => setPhotosModalOpen(true)}
              onOpenCalendar={() => setCalendarModalOpen(true)}
              notifications={notifications}
              showNotifications={showNotifications}
              onToggleNotifications={() => setShowNotifications(!showNotifications)}
              onMarkNotificationRead={handleMarkNotificationRead}
              onMarkAllNotificationsRead={handleMarkAllNotificationsRead}
              onDismissNotification={handleDismissNotification}
              selectedMood={selectedMood}
              onSelectMood={setSelectedMood}
              onThisDay={onThisDay}
              onOpenProfile={() => setProfileModalOpen(true)}
            />
          </div>
        </main>
      </div>

      {/* Floating "Ask LifeBook" Assistant Widget */}
      <AskLifeBookWidget />

      {/* All Modal Overlays */}
      <CalendarMemoriesModal
        isOpen={calendarModalOpen}
        onClose={() => setCalendarModalOpen(false)}
        onOpenAddMemory={() => setVoiceModalOpen(true)}
        onViewPhoto={() => setPhotosModalOpen(true)}
      />
      <VoiceRecorderModal
        isOpen={voiceModalOpen}
        onClose={() => setVoiceModalOpen(false)}
        onEntryCreated={handleEntryCreated}
      />
      <TextEntryModal
        isOpen={textModalOpen}
        onClose={() => setTextModalOpen(false)}
        onEntryCreated={handleEntryCreated}
      />
      <PhotoEntryModal
        isOpen={photoModalOpen}
        onClose={() => setPhotoModalOpen(false)}
        onEntryCreated={handleEntryCreated}
      />
      <DraftReviewModal
        isOpen={reviewModalOpen}
        entry={activeEntry}
        onClose={() => setReviewModalOpen(false)}
        onConfirmed={handleEntryConfirmed}
      />
      <LifeGraphModal
        isOpen={graphModalOpen}
        onClose={() => setGraphModalOpen(false)}
      />
      <PhotosModal
        isOpen={photosModalOpen}
        onClose={() => setPhotosModalOpen(false)}
        onOpenPhotoEntry={() => setPhotoModalOpen(true)}
      />
      <InsightsModal
        isOpen={insightsModalOpen}
        onClose={() => setInsightsModalOpen(false)}
        onRoutineUpdated={loadData}
      />
      <PrivacyModal
        isOpen={privacyModalOpen}
        onClose={() => setPrivacyModalOpen(false)}
      />
      <SettingsModal
        isOpen={settingsModalOpen}
        onClose={() => setSettingsModalOpen(false)}
        onOpenProfile={() => setProfileModalOpen(true)}
      />
      <AdminModal
        isOpen={adminModalOpen}
        onClose={() => setAdminModalOpen(false)}
      />
      <ProfileModal
        isOpen={profileModalOpen}
        onClose={() => setProfileModalOpen(false)}
      />
    </div>
  );
};

export function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
