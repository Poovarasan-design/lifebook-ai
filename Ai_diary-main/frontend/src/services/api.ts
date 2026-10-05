import {
  User,
  DiaryEntry,
  Commitment,
  Routine,
  LifeGraphData,
  ForgettingResponse,
  ConversationalAnswer,
  NotificationItem,
  SystemMetrics,
  AuditLogItem,
  PhotoItem,
  PeopleAndPlacesData,
  InsightsData,
  TodayAssistantData,
  EntityHistoryData,
  CalendarResponse
} from "../types";


const API_BASE = import.meta.env.VITE_API_BASE_URL || "/api/v1";

function getHeaders(isFormData = false): HeadersInit {
  const token = localStorage.getItem("lifebook_token");
  const headers: Record<string, string> = {};
  if (!isFormData) {
    headers["Content-Type"] = "application/json";
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}


export const api = {
  // Auth
  async login(email: string, password: string): Promise<{ access_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Login failed" }));
      throw new Error(err.detail || "Invalid credentials");
    }
    const data = await res.json();
    localStorage.setItem("lifebook_token", data.access_token);
    localStorage.setItem("lifebook_user", JSON.stringify(data.user));
    return data;
  },

  async register(email: string, password: string, full_name: string, confirm_password?: string): Promise<{ access_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name, confirm_password: confirm_password || password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Registration failed" }));
      throw new Error(err.detail || "Registration failed");
    }
    const data = await res.json();
    localStorage.setItem("lifebook_token", data.access_token);
    localStorage.setItem("lifebook_user", JSON.stringify(data.user));
    return data;
  },

  async loginWithGoogle(payload: { id_token?: string; code?: string; redirect_uri?: string }): Promise<{ access_token: string; user: User }> {
    const res = await fetch(`${API_BASE}/auth/google`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Google authentication failed" }));
      throw new Error(err.detail || "Google authentication failed");
    }
    const data = await res.json();
    localStorage.setItem("lifebook_token", data.access_token);
    localStorage.setItem("lifebook_user", JSON.stringify(data.user));
    return data;
  },

  async getGoogleAuthUrl(): Promise<{ url: string; client_id?: string }> {
    const res = await fetch(`${API_BASE}/auth/google/url`);
    if (!res.ok) throw new Error("Failed to get Google login URL");
    return res.json();
  },

  async forgotPassword(email: string): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE}/auth/forgot-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Password reset request failed" }));
      throw new Error(err.detail || "Password reset request failed");
    }
    return res.json();
  },

  async resetPassword(token: string, new_password: string): Promise<{ message: string }> {
    const res = await fetch(`${API_BASE}/auth/reset-password`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, new_password })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Password reset failed" }));
      throw new Error(err.detail || "Password reset failed");
    }
    return res.json();
  },

  async logout(): Promise<void> {
    try {
      await fetch(`${API_BASE}/auth/logout`, {
        method: "POST",
        headers: getHeaders()
      });
    } catch {
      // Ignore network errors on logout
    } finally {
      localStorage.removeItem("lifebook_token");
      localStorage.removeItem("lifebook_user");
    }
  },

  async getMe(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/me`, { headers: getHeaders() });
    if (!res.ok) {
      // Fallback to /users/me
      const fallback = await fetch(`${API_BASE}/users/me`, { headers: getHeaders() });
      if (!fallback.ok) throw new Error("Failed to load user");
      return fallback.json();
    }
    const user = await res.json();
    localStorage.setItem("lifebook_user", JSON.stringify(user));
    return user;
  },

  async updateProfile(payload: { full_name?: string; avatar_url?: string }): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/profile`, {
      method: "PUT",
      headers: getHeaders(),
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to update profile" }));
      throw new Error(err.detail || "Failed to update profile");
    }
    const updatedUser = await res.json();
    localStorage.setItem("lifebook_user", JSON.stringify(updatedUser));
    return updatedUser;
  },

  async uploadAvatar(file: File): Promise<User> {
    const formData = new FormData();
    formData.append("file", file);
    const res = await fetch(`${API_BASE}/auth/avatar`, {
      method: "POST",
      headers: getHeaders(true),
      body: formData
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to upload avatar" }));
      throw new Error(err.detail || "Failed to upload avatar");
    }
    const updatedUser = await res.json();
    localStorage.setItem("lifebook_user", JSON.stringify(updatedUser));
    return updatedUser;
  },

  async deleteAvatar(): Promise<User> {
    const res = await fetch(`${API_BASE}/auth/avatar`, {
      method: "DELETE",
      headers: getHeaders()
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to delete avatar" }));
      throw new Error(err.detail || "Failed to delete avatar");
    }
    const updatedUser = await res.json();
    localStorage.setItem("lifebook_user", JSON.stringify(updatedUser));
    return updatedUser;
  },

  async updateMe(data: { full_name?: string; preferences?: Record<string, any> }): Promise<User> {
    const res = await fetch(`${API_BASE}/users/me`, {
      method: "PATCH",
      headers: getHeaders(),
      body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error("Failed to update profile");
    return res.json();
  },

  // Diary Ingestion
  async submitText(raw_text: string, title?: string, category?: string, mood?: string): Promise<DiaryEntry> {
    const res = await fetch(`${API_BASE}/diary/text`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ raw_text, title, category, mood })
    });
    if (!res.ok) throw new Error("Failed to submit text memory");
    return res.json();
  },

  async submitVoice(audioBlob: Blob, filename = "voice.webm", transcript?: string): Promise<DiaryEntry> {
    const formData = new FormData();
    formData.append("file", audioBlob, filename);
    if (transcript && transcript.trim()) {
      formData.append("transcript", transcript.trim());
    }
    const res = await fetch(`${API_BASE}/diary/voice`, {
      method: "POST",
      headers: getHeaders(true),
      body: formData
    });
    if (!res.ok) throw new Error("Failed to upload voice memory");
    return res.json();
  },

  async submitPhoto(imageFile: File, caption?: string): Promise<DiaryEntry> {
    const formData = new FormData();
    formData.append("file", imageFile);
    if (caption) formData.append("caption", caption);
    const res = await fetch(`${API_BASE}/diary/photo`, {
      method: "POST",
      headers: getHeaders(true),
      body: formData
    });
    if (!res.ok) throw new Error("Failed to upload photo memory");
    return res.json();
  },

  async getEntryStatus(entryId: string): Promise<any> {
    const res = await fetch(`${API_BASE}/diary/${entryId}/status`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to get status");
    return res.json();
  },

  async retryEntryProcessing(entryId: string): Promise<DiaryEntry> {
    const res = await fetch(`${API_BASE}/diary/${entryId}/retry`, {
      method: "POST",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to retry processing");
    return res.json();
  },

  async regenerateEntry(entryId: string, tone = "reflective", instructions?: string): Promise<DiaryEntry> {
    const res = await fetch(`${API_BASE}/diary/${entryId}/regenerate`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ tone, instructions })
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: "Failed to regenerate diary" }));
      throw new Error(err.detail || "Failed to regenerate diary");
    }
    return res.json();
  },

  async confirmEntry(entryId: string, confirmedTitle?: string, confirmedContent?: string, disambiguationResolution?: Record<string, string>): Promise<DiaryEntry> {
    const res = await fetch(`${API_BASE}/diary/${entryId}/confirm`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({
        confirmed_title: confirmedTitle,
        confirmed_content: confirmedContent,
        disambiguation_resolution: disambiguationResolution
      })
    });
    if (!res.ok) throw new Error("Failed to confirm entry");
    return res.json();
  },

  async getEntries(): Promise<DiaryEntry[]> {
    const res = await fetch(`${API_BASE}/diary`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to fetch entries");
    return res.json();
  },

  // Photos & Gallery
  async getPhotos(): Promise<PhotoItem[]> {
    const res = await fetch(`${API_BASE}/diary/photos`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load photos");
    return res.json();
  },

  // Life Graph & People/Places
  async getLifeGraph(): Promise<LifeGraphData> {
    const res = await fetch(`${API_BASE}/life-graph`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load life graph");
    return res.json();
  },

  async getPeopleAndPlaces(): Promise<PeopleAndPlacesData> {
    const res = await fetch(`${API_BASE}/life-graph/entities`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load people and places");
    return res.json();
  },

  // Commitments
  async getCommitments(status?: string): Promise<Commitment[]> {
    const url = status ? `${API_BASE}/commitments?status=${status}` : `${API_BASE}/commitments`;
    const res = await fetch(url, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load commitments");
    return res.json();
  },

  async completeCommitment(id: string): Promise<Commitment> {
    const res = await fetch(`${API_BASE}/commitments/${id}/complete`, {
      method: "POST",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to complete commitment");
    return res.json();
  },

  async rescheduleCommitment(id: string, newDueDate: string): Promise<Commitment> {
    const res = await fetch(`${API_BASE}/commitments/${id}/reschedule?new_due_date=${encodeURIComponent(newDueDate)}`, {
      method: "POST",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to reschedule");
    return res.json();
  },

  async dismissCommitment(id: string): Promise<Commitment> {
    const res = await fetch(`${API_BASE}/commitments/${id}/dismiss`, {
      method: "POST",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to dismiss");
    return res.json();
  },

  // Routines
  async getRoutines(): Promise<Routine[]> {
    const res = await fetch(`${API_BASE}/routines`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to fetch routines");
    return res.json();
  },

  async handleRoutineDeviation(routineId: string, action: string, note?: string): Promise<Routine> {
    const res = await fetch(`${API_BASE}/routines/${routineId}/action`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ action, note })
    });
    if (!res.ok) throw new Error("Failed to respond to deviation");
    return res.json();
  },

  async getInsights(): Promise<InsightsData> {
    const res = await fetch(`${API_BASE}/routines/insights`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to fetch insights");
    return res.json();
  },

  // Search & "What am I forgetting?"
  async askQuestion(query: string): Promise<ConversationalAnswer> {
    const res = await fetch(`${API_BASE}/search`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify({ query })
    });
    if (!res.ok) throw new Error("Failed to ask question");
    return res.json();
  },

  async whatAmIForgetting(): Promise<ForgettingResponse> {
    const res = await fetch(`${API_BASE}/search/forgetting`, {
      method: "POST",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to retrieve forgetting assistant");
    return res.json();
  },

  // Memories & Calendar
  async getOnThisDay(): Promise<any> {
    const res = await fetch(`${API_BASE}/memories/on-this-day`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load On This Day memory");
    return res.json();
  },

  async getCalendarActivities(year = 2026, month = 9): Promise<CalendarResponse> {
    const res = await fetch(`${API_BASE}/memories/calendar?year=${year}&month=${month}`, {
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to load calendar activities");
    return res.json();
  },

  // Proactive Today Assistant (Phase 4)
  async getTodayAssistant(): Promise<TodayAssistantData> {
    const res = await fetch(`${API_BASE}/assistant/today`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load today assistant briefing");
    return res.json();
  },

  // Notifications
  async getNotifications(): Promise<NotificationItem[]> {
    const res = await fetch(`${API_BASE}/notifications`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load notifications");
    return res.json();
  },

  async markNotificationRead(id: string): Promise<any> {
    const res = await fetch(`${API_BASE}/notifications/${id}/read`, {
      method: "POST",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to mark notification as read");
    return res.json();
  },

  async markAllNotificationsRead(): Promise<any> {
    const res = await fetch(`${API_BASE}/notifications/read-all`, {
      method: "POST",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to mark all notifications as read");
    return res.json();
  },

  async dismissNotification(id: string): Promise<any> {
    const res = await fetch(`${API_BASE}/notifications/${id}`, {
      method: "DELETE",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to dismiss notification");
    return res.json();
  },

  // Life Graph History (Phase 6)
  async getPersonHistory(name: string): Promise<EntityHistoryData> {
    const res = await fetch(`${API_BASE}/life-graph/person/${encodeURIComponent(name)}/history`, {
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to load person history");
    return res.json();
  },

  async getProjectHistory(name: string): Promise<EntityHistoryData> {
    const res = await fetch(`${API_BASE}/life-graph/project/${encodeURIComponent(name)}/history`, {
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to load project history");
    return res.json();
  },

  async getPlaceHistory(name: string): Promise<EntityHistoryData> {
    const res = await fetch(`${API_BASE}/life-graph/place/${encodeURIComponent(name)}/history`, {
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to load place history");
    return res.json();
  },

  async getEntityHistory(type: string, name: string): Promise<EntityHistoryData> {
    const res = await fetch(`${API_BASE}/life-graph/entity-history?type=${type}&name=${encodeURIComponent(name)}`, {
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to load entity history");
    return res.json();
  },

  // Admin
  async getAdminMetrics(): Promise<SystemMetrics> {
    const res = await fetch(`${API_BASE}/admin/metrics`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load admin metrics");
    return res.json();
  },

  async getAdminAudit(): Promise<AuditLogItem[]> {
    const res = await fetch(`${API_BASE}/admin/audit`, { headers: getHeaders() });
    if (!res.ok) throw new Error("Failed to load audit logs");
    return res.json();
  },

  // Export & Delete
  async exportData(): Promise<any> {
    const res = await fetch(`${API_BASE}/users/me/export`, {
      method: "POST",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to export data");
    return res.json();
  },

  async deleteAccount(): Promise<any> {
    const res = await fetch(`${API_BASE}/users/me`, {
      method: "DELETE",
      headers: getHeaders()
    });
    if (!res.ok) throw new Error("Failed to delete account");
    return res.json();
  }
};

