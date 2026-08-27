import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import { MOCK_ALBUMS, createInitialImages } from "@/lib/mock-data";
import type { Album, AspectRatio, GeneratedImage } from "@/types";

interface GenerateApiImage {
  url: string;
  width: number;
  height: number;
}

interface GalleryState {
  albums: Album[];
  images: GeneratedImage[];
  activeAlbumId: string;
  selectedImageId: string | null;
  prompt: string;
  ratio: AspectRatio;
  count: number;
  isGenerating: boolean;
  generationError: string | null;

  setPrompt: (value: string) => void;
  setRatio: (value: AspectRatio) => void;
  setCount: (value: number) => void;
  setActiveAlbum: (albumId: string) => void;
  createAlbum: (name: string) => void;
  renameAlbum: (albumId: string, name: string) => void;
  deleteAlbum: (albumId: string) => void;
  selectImage: (imageId: string | null) => void;
  deleteImage: (imageId: string) => void;
  moveImage: (imageId: string, targetAlbumId: string) => void;
  generateImages: () => Promise<void>;
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
      console.warn("갤러리 상태를 저장하지 못했습니다 (저장공간이 부족할 수 있습니다):", err);
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

export const useGalleryStore = create<GalleryState>()(
  persist(
    (set, get) => ({
      albums: MOCK_ALBUMS,
      images: createInitialImages(),
      activeAlbumId: MOCK_ALBUMS[0].id,
      selectedImageId: null,
      prompt: "",
      ratio: "1:1",
      count: 4,
      isGenerating: false,
      generationError: null,

      setPrompt: (value) => set({ prompt: value }),
      setRatio: (value) => set({ ratio: value }),
      setCount: (value) => set({ count: value }),

      setActiveAlbum: (albumId) => set({ activeAlbumId: albumId }),

      createAlbum: (name) => {
        const trimmed = name.trim();
        if (!trimmed) return;
        const album: Album = { id: `album-${Date.now()}`, name: trimmed };
        set((state) => ({
          albums: [...state.albums, album],
          activeAlbumId: album.id,
        }));
      },

      renameAlbum: (albumId, name) => {
        const trimmed = name.trim();
        if (!trimmed) return;
        set((state) => ({
          albums: state.albums.map((album) =>
            album.id === albumId ? { ...album, name: trimmed } : album
          ),
        }));
      },

      deleteAlbum: (albumId) => {
        const { albums, activeAlbumId } = get();
        if (albums.length <= 1) return;
        const remaining = albums.filter((album) => album.id !== albumId);

        set((state) => ({
          albums: remaining,
          images: state.images.filter((img) => img.albumId !== albumId),
          activeAlbumId: activeAlbumId === albumId ? remaining[0].id : activeAlbumId,
          selectedImageId:
            state.images.find((img) => img.id === state.selectedImageId)?.albumId === albumId
              ? null
              : state.selectedImageId,
        }));
      },

      selectImage: (imageId) => set({ selectedImageId: imageId }),

      deleteImage: (imageId) => {
        set((state) => ({
          images: state.images.filter((img) => img.id !== imageId),
          selectedImageId: state.selectedImageId === imageId ? null : state.selectedImageId,
        }));
      },

      moveImage: (imageId, targetAlbumId) => {
        set((state) => ({
          images: state.images.map((img) =>
            img.id === imageId ? { ...img, albumId: targetAlbumId } : img
          ),
        }));
      },

      generateImages: async () => {
        const { prompt, ratio, count, activeAlbumId } = get();
        const trimmedPrompt = prompt.trim();
        if (!trimmedPrompt || get().isGenerating) return;

        set({ isGenerating: true, generationError: null });

        try {
          const response = await fetch("/api/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: trimmedPrompt, ratio, count }),
          });

          const data = await response.json();

          if (!response.ok) {
            throw new Error(data.error ?? "이미지 생성 중 오류가 발생했습니다.");
          }

          const newImages: GeneratedImage[] = (data.images as GenerateApiImage[]).map((img) => ({
            id: crypto.randomUUID(),
            albumId: activeAlbumId,
            url: img.url,
            prompt: trimmedPrompt,
            ratio,
            width: img.width,
            height: img.height,
            createdAt: Date.now(),
          }));

          set((state) => ({
            images: [...newImages, ...state.images],
            isGenerating: false,
          }));
        } catch (err) {
          set({
            isGenerating: false,
            generationError: err instanceof Error ? err.message : "이미지 생성 중 오류가 발생했습니다.",
          });
        }
      },
    }),
    {
      name: "reve-gallery-storage",
      storage: createJSONStorage(() => safeStorage),
      partialize: (state) => ({
        albums: state.albums,
        images: state.images,
        activeAlbumId: state.activeAlbumId,
      }),
    }
  )
);
