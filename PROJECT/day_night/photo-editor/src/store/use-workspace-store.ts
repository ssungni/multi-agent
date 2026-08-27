import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { Album, AppView, SerializedSession } from "@/types";

interface WorkspaceState {
  view: AppView;
  projectName: string;
  albums: Album[];
  sessions: Record<string, SerializedSession>;
  activeAlbumId: string | null;

  pendingPrompt: string | null;
  pendingImageFile: File | null;
  setPendingPrompt: (prompt: string | null) => void;
  setPendingImageFile: (file: File | null) => void;

  renameProject: (name: string) => void;
  goToStart: () => void;
  goToWorkspace: () => void;
  createAlbum: (name?: string) => string;
  openAlbum: (id: string) => void;
  renameAlbum: (id: string, name: string) => void;
  deleteAlbum: (id: string) => void;
  saveActiveSession: (session: SerializedSession) => void;
  getActiveSession: () => SerializedSession | undefined;
}

const safeStorage = {
  getItem: (name: string) => {
    try {
      return localStorage.getItem(name);
    } catch {
      return null;
    }
  },
  setItem: (name: string, value: string) => {
    try {
      localStorage.setItem(name, value);
    } catch (err) {
      console.warn("작업 공간 상태를 저장하지 못했습니다 (저장공간이 부족할 수 있습니다):", err);
    }
  },
  removeItem: (name: string) => {
    try {
      localStorage.removeItem(name);
    } catch {
      // ignore
    }
  },
};

let newAlbumCounter = 0;

export const useWorkspaceStore = create<WorkspaceState>()(
  persist(
    (set, get) => ({
      view: "start",
      projectName: "My Project",
      albums: [],
      sessions: {},
      activeAlbumId: null,

      pendingPrompt: null,
      pendingImageFile: null,
      setPendingPrompt: (prompt) => set({ pendingPrompt: prompt }),
      setPendingImageFile: (file) => set({ pendingImageFile: file }),

      renameProject: (name) => {
        const trimmed = name.trim();
        if (!trimmed) return;
        set({ projectName: trimmed });
      },

      goToStart: () => set({ view: "start", activeAlbumId: null }),
      goToWorkspace: () => set({ view: "workspace", activeAlbumId: null }),

      createAlbum: (name) => {
        newAlbumCounter += 1;
        const id = crypto.randomUUID();
        const now = Date.now();
        const album: Album = {
          id,
          name: name?.trim() || `New album ${newAlbumCounter}`,
          createdAt: now,
          updatedAt: now,
        };
        set((state) => ({
          albums: [album, ...state.albums],
          activeAlbumId: id,
          view: "editor",
        }));
        return id;
      },

      openAlbum: (id) => set({ activeAlbumId: id, view: "editor" }),

      renameAlbum: (id, name) => {
        const trimmed = name.trim();
        if (!trimmed) return;
        set((state) => ({
          albums: state.albums.map((a) =>
            a.id === id ? { ...a, name: trimmed, updatedAt: Date.now() } : a
          ),
        }));
      },

      deleteAlbum: (id) => {
        set((state) => {
          const sessions = { ...state.sessions };
          delete sessions[id];
          return {
            albums: state.albums.filter((a) => a.id !== id),
            sessions,
            activeAlbumId: state.activeAlbumId === id ? null : state.activeAlbumId,
            view: state.activeAlbumId === id ? "workspace" : state.view,
          };
        });
      },

      saveActiveSession: (session) => {
        const { activeAlbumId } = get();
        if (!activeAlbumId) return;
        set((state) => ({
          sessions: { ...state.sessions, [activeAlbumId]: session },
          albums: state.albums.map((a) =>
            a.id === activeAlbumId ? { ...a, updatedAt: Date.now() } : a
          ),
        }));
      },

      getActiveSession: () => {
        const { activeAlbumId, sessions } = get();
        return activeAlbumId ? sessions[activeAlbumId] : undefined;
      },
    }),
    {
      name: "photo-editor-workspace",
      storage: createJSONStorage(() => safeStorage),
      partialize: (state) => ({
        projectName: state.projectName,
        albums: state.albums,
        sessions: state.sessions,
      }),
    }
  )
);
