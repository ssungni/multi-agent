import { create } from "zustand";

import { getImageNaturalSize } from "@/lib/get-image-size";
import type {
  ChatMessage,
  DetectedLayer,
  DrawStroke,
  PlacedImageLayer,
  Rect,
  SerializedSession,
  TextLayer,
  ToolId,
} from "@/types";

interface EditorState {
  imageUrl: string | null;
  history: string[];
  future: string[];

  isSegmenting: boolean;
  isBusy: boolean;
  errorMessage: string | null;

  layers: DetectedLayer[];
  selectedLayerId: string | null;

  activeTool: ToolId;
  drawColor: string;
  drawSize: number;
  isErasing: boolean;
  strokes: DrawStroke[];

  textLayers: TextLayer[];
  placedImages: PlacedImageLayer[];

  spotlightRect: Rect | null;

  effectsPanelOpen: boolean;
  effectsBeforeOpen: string | null;
  activeEffectId: string | null;

  chatMessages: ChatMessage[];
  chatInput: string;

  setChatInput: (value: string) => void;
  sendChatMessage: () => Promise<void>;

  uploadImage: (file: File) => Promise<void>;
  runSegmentation: () => Promise<void>;
  selectLayer: (id: string | null) => void;

  setActiveTool: (tool: ToolId) => void;
  setDrawColor: (color: string) => void;
  setDrawSize: (size: number) => void;
  setIsErasing: (value: boolean) => void;
  addStroke: (stroke: DrawStroke) => void;
  removeStroke: (id: string) => void;

  addTextLayer: (x: number, y: number) => string;
  updateTextLayer: (id: string, patch: Partial<TextLayer>) => void;
  removeTextLayer: (id: string) => void;

  addPlacedImage: (url: string, x: number, y: number, width: number, height: number) => void;
  removePlacedImage: (id: string) => void;

  addObjectAt: (prompt: string, x: number, y: number) => Promise<void>;

  setSpotlightRect: (rect: Rect | null) => void;

  openEffectsPanel: () => void;
  setActiveEffect: (id: string | null) => void;
  confirmEffects: () => void;
  cancelEffects: () => void;

  undo: () => void;
  redo: () => void;

  serializeSession: () => SerializedSession;
  loadSession: (session: SerializedSession | undefined) => void;
}

const BLANK_SESSION: SerializedSession = {
  imageUrl: null,
  history: [],
  future: [],
  layers: [],
  textLayers: [],
  placedImages: [],
  strokes: [],
  activeEffectId: null,
  chatMessages: [],
};

function readFileAsDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result as string);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(file);
  });
}

export const useEditorStore = create<EditorState>((set, get) => ({
  imageUrl: null,
  history: [],
  future: [],

  isSegmenting: false,
  isBusy: false,
  errorMessage: null,

  layers: [],
  selectedLayerId: null,

  activeTool: "select",
  drawColor: "#ef4444",
  drawSize: 8,
  isErasing: false,
  strokes: [],

  textLayers: [],
  placedImages: [],

  spotlightRect: null,

  effectsPanelOpen: false,
  effectsBeforeOpen: null,
  activeEffectId: null,

  chatMessages: [],
  chatInput: "",

  setChatInput: (value) => set({ chatInput: value }),

  sendChatMessage: async () => {
    const { chatInput, imageUrl, isBusy } = get();
    const prompt = chatInput.trim();
    if (!prompt || isBusy) return;

    const userMessage: ChatMessage = {
      id: crypto.randomUUID(),
      role: "user",
      content: prompt,
      createdAt: Date.now(),
    };

    set((state) => ({
      chatMessages: [...state.chatMessages, userMessage],
      chatInput: "",
      isBusy: true,
      errorMessage: null,
    }));

    try {
      if (!imageUrl) {
        const response = await fetch("/api/generate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ prompt }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error ?? "이미지 생성 중 오류가 발생했습니다.");

        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "이미지를 생성했어요.",
          createdAt: Date.now(),
        };
        set((state) => ({
          imageUrl: data.url,
          isBusy: false,
          chatMessages: [...state.chatMessages, assistantMessage],
        }));
        void get().runSegmentation();
      } else {
        const response = await fetch("/api/edit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ imageDataUrl: imageUrl, prompt }),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error ?? "이미지 편집 중 오류가 발생했습니다.");

        const assistantMessage: ChatMessage = {
          id: crypto.randomUUID(),
          role: "assistant",
          content: "요청하신 대로 이미지를 수정했어요.",
          createdAt: Date.now(),
        };
        set((state) => ({
          history: [...state.history, state.imageUrl!],
          future: [],
          imageUrl: data.url,
          isBusy: false,
          selectedLayerId: null,
          chatMessages: [...state.chatMessages, assistantMessage],
        }));
        void get().runSegmentation();
      }
    } catch (err) {
      set({
        isBusy: false,
        errorMessage: err instanceof Error ? err.message : "요청 처리 중 오류가 발생했습니다.",
      });
    }
  },

  uploadImage: async (file) => {
    const dataUrl = await readFileAsDataUrl(file);
    set({
      imageUrl: dataUrl,
      history: [],
      future: [],
      layers: [],
      selectedLayerId: null,
      strokes: [],
      textLayers: [],
      placedImages: [],
      activeEffectId: null,
      errorMessage: null,
    });
    void get().runSegmentation();
  },

  runSegmentation: async () => {
    const { imageUrl } = get();
    if (!imageUrl) return;

    set({ isSegmenting: true });
    try {
      const { width, height } = await getImageNaturalSize(imageUrl);
      const response = await fetch("/api/segment", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ imageDataUrl: imageUrl, width, height }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error ?? "객체 감지 중 오류가 발생했습니다.");

      set({ layers: data.layers, isSegmenting: false });
    } catch (err) {
      set({
        isSegmenting: false,
        errorMessage: err instanceof Error ? err.message : "객체 감지 중 오류가 발생했습니다.",
      });
    }
  },

  selectLayer: (id) => set({ selectedLayerId: id }),

  setActiveTool: (tool) => set({ activeTool: tool, spotlightRect: null }),
  setDrawColor: (color) => set({ drawColor: color }),
  setDrawSize: (size) => set({ drawSize: size }),
  setIsErasing: (value) => set({ isErasing: value }),
  addStroke: (stroke) => set((state) => ({ strokes: [...state.strokes, stroke] })),
  removeStroke: (id) =>
    set((state) => ({
      strokes: state.strokes.filter((s) => s.id !== id),
      selectedLayerId: state.selectedLayerId === id ? null : state.selectedLayerId,
    })),

  addTextLayer: (x, y) => {
    const id = crypto.randomUUID();
    const layer: TextLayer = { id, x, y, text: "Text", color: "#ffffff", fontSize: 32 };
    set((state) => ({ textLayers: [...state.textLayers, layer] }));
    return id;
  },
  updateTextLayer: (id, patch) => {
    set((state) => ({
      textLayers: state.textLayers.map((t) => (t.id === id ? { ...t, ...patch } : t)),
    }));
  },
  removeTextLayer: (id) => {
    set((state) => ({ textLayers: state.textLayers.filter((t) => t.id !== id) }));
  },

  addPlacedImage: (url, x, y, width, height) => {
    const layer: PlacedImageLayer = { id: crypto.randomUUID(), url, x, y, width, height };
    set((state) => ({ placedImages: [...state.placedImages, layer] }));
  },
  removePlacedImage: (id) => {
    set((state) => ({ placedImages: state.placedImages.filter((p) => p.id !== id) }));
  },

  addObjectAt: async (prompt, x, y) => {
    const { imageUrl, isBusy } = get();
    if (!imageUrl || !prompt.trim() || isBusy) return;

    set({ isBusy: true, errorMessage: null });
    const positionHint = `이미지의 가로 ${Math.round(x * 100)}%, 세로 ${Math.round(
      y * 100
    )}% 위치 근처에 다음 객체를 자연스럽게 추가해줘: ${prompt.trim()}`;

    try {
      const response = await fetch("/api/edit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ imageDataUrl: imageUrl, prompt: positionHint }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error ?? "객체 추가 중 오류가 발생했습니다.");

      set((state) => ({
        history: [...state.history, state.imageUrl!],
        future: [],
        imageUrl: data.url,
        isBusy: false,
        selectedLayerId: null,
      }));
      void get().runSegmentation();
    } catch (err) {
      set({
        isBusy: false,
        errorMessage: err instanceof Error ? err.message : "객체 추가 중 오류가 발생했습니다.",
      });
    }
  },

  setSpotlightRect: (rect) => set({ spotlightRect: rect }),

  openEffectsPanel: () =>
    set((state) => ({ effectsPanelOpen: true, effectsBeforeOpen: state.activeEffectId })),
  setActiveEffect: (id) => set({ activeEffectId: id }),
  confirmEffects: () => set({ effectsPanelOpen: false, effectsBeforeOpen: null }),
  cancelEffects: () =>
    set((state) => ({
      effectsPanelOpen: false,
      activeEffectId: state.effectsBeforeOpen,
      effectsBeforeOpen: null,
    })),

  undo: () => {
    const { history, imageUrl } = get();
    if (history.length === 0 || !imageUrl) return;
    const previous = history[history.length - 1];
    set((state) => ({
      imageUrl: previous,
      history: state.history.slice(0, -1),
      future: [imageUrl, ...state.future],
      selectedLayerId: null,
    }));
    void get().runSegmentation();
  },

  redo: () => {
    const { future, imageUrl } = get();
    if (future.length === 0 || !imageUrl) return;
    const next = future[0];
    set((state) => ({
      imageUrl: next,
      future: state.future.slice(1),
      history: [...state.history, imageUrl],
      selectedLayerId: null,
    }));
    void get().runSegmentation();
  },

  serializeSession: () => {
    const state = get();
    return {
      imageUrl: state.imageUrl,
      history: state.history,
      future: state.future,
      layers: state.layers,
      textLayers: state.textLayers,
      placedImages: state.placedImages,
      strokes: state.strokes,
      activeEffectId: state.activeEffectId,
      chatMessages: state.chatMessages,
    };
  },

  loadSession: (session) => {
    const s = session ?? BLANK_SESSION;
    set({
      imageUrl: s.imageUrl,
      history: s.history,
      future: s.future,
      layers: s.layers,
      textLayers: s.textLayers,
      placedImages: s.placedImages,
      strokes: s.strokes,
      activeEffectId: s.activeEffectId,
      chatMessages: s.chatMessages,
      selectedLayerId: null,
      activeTool: "select",
      isSegmenting: false,
      isBusy: false,
      errorMessage: null,
      spotlightRect: null,
      effectsPanelOpen: false,
      effectsBeforeOpen: null,
      chatInput: "",
    });
  },
}));
