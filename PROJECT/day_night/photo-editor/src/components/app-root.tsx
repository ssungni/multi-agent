"use client";

import { useEffect, useRef } from "react";

import { useWorkspaceStore } from "@/store/use-workspace-store";
import { useEditorStore } from "@/store/use-editor-store";
import { StartScreen } from "@/components/start/start-screen";
import { WorkspaceScreen } from "@/components/workspace/workspace-screen";
import { EditorShell } from "@/components/editor/editor-shell";

export function AppRoot() {
  const view = useWorkspaceStore((s) => s.view);
  const activeAlbumId = useWorkspaceStore((s) => s.activeAlbumId);
  const getActiveSession = useWorkspaceStore((s) => s.getActiveSession);
  const saveActiveSession = useWorkspaceStore((s) => s.saveActiveSession);
  const loadSession = useEditorStore((s) => s.loadSession);
  const serializeSession = useEditorStore((s) => s.serializeSession);

  const loadedAlbumIdRef = useRef<string | null>(null);

  // Load the album's saved session whenever we enter editor view for a
  // (newly) active album, then apply any pending prompt/image queued by the
  // start screen. This must run after the reset above, not before, or the
  // pending action's state gets wiped by this same load.
  useEffect(() => {
    if (view !== "editor" || !activeAlbumId) return;
    if (loadedAlbumIdRef.current === activeAlbumId) return;
    loadedAlbumIdRef.current = activeAlbumId;
    loadSession(getActiveSession());

    const workspaceState = useWorkspaceStore.getState();
    const pendingPrompt = workspaceState.pendingPrompt;
    const pendingImageFile = workspaceState.pendingImageFile;

    if (pendingPrompt) {
      workspaceState.setPendingPrompt(null);
      useEditorStore.getState().setChatInput(pendingPrompt);
      void useEditorStore.getState().sendChatMessage();
    } else if (pendingImageFile) {
      workspaceState.setPendingImageFile(null);
      void useEditorStore.getState().uploadImage(pendingImageFile);
    }
  }, [view, activeAlbumId, getActiveSession, loadSession]);

  const imageUrl = useEditorStore((s) => s.imageUrl);
  const history = useEditorStore((s) => s.history);
  const future = useEditorStore((s) => s.future);
  const layers = useEditorStore((s) => s.layers);
  const textLayers = useEditorStore((s) => s.textLayers);
  const placedImages = useEditorStore((s) => s.placedImages);
  const strokes = useEditorStore((s) => s.strokes);
  const activeEffectId = useEditorStore((s) => s.activeEffectId);
  const chatMessages = useEditorStore((s) => s.chatMessages);

  // Persist editor state back into the workspace store on every meaningful
  // change so leaving the editor (or reloading) never loses work.
  useEffect(() => {
    if (view !== "editor" || !activeAlbumId) return;
    if (loadedAlbumIdRef.current !== activeAlbumId) return;
    saveActiveSession(serializeSession());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    view,
    activeAlbumId,
    imageUrl,
    history,
    future,
    layers,
    textLayers,
    placedImages,
    strokes,
    activeEffectId,
    chatMessages,
  ]);

  if (view === "start") return <StartScreen />;
  if (view === "workspace") return <WorkspaceScreen />;
  return <EditorShell />;
}
