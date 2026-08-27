"use client";

import { useState } from "react";
import { ArrowRightIcon, Loader2Icon, UserIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useWorkspaceStore } from "@/store/use-workspace-store";
import { SAMPLE_START_IMAGES } from "@/lib/sample-images";

export function StartScreen() {
  const [prompt, setPrompt] = useState("");
  const [isStartingImage, setIsStartingImage] = useState<string | null>(null);
  const createAlbum = useWorkspaceStore((s) => s.createAlbum);
  const goToWorkspace = useWorkspaceStore((s) => s.goToWorkspace);
  const setPendingPrompt = useWorkspaceStore((s) => s.setPendingPrompt);
  const setPendingImageFile = useWorkspaceStore((s) => s.setPendingImageFile);

  // Album creation flips `view` to "editor", which mounts EditorShell and
  // triggers AppRoot's session-load effect. That effect resets the editor
  // store, so any prompt/image we want auto-applied must be queued as a
  // "pending" action for AppRoot to run *after* loading finishes — calling
  // sendChatMessage/uploadImage directly here would race the reset and lose
  // the very state it just set.
  function handleStart() {
    if (prompt.trim()) setPendingPrompt(prompt.trim());
    createAlbum();
  }

  async function handleStartWithImage(url: string) {
    setIsStartingImage(url);
    try {
      const blob = await fetch(url).then((r) => r.blob());
      const file = new File([blob], "sample.jpg", { type: blob.type || "image/jpeg" });
      setPendingImageFile(file);
      createAlbum();
    } finally {
      setIsStartingImage(null);
    }
  }

  return (
    <div className="flex h-full flex-col bg-neutral-50">
      <div className="flex items-center justify-between px-6 py-5">
        <span className="text-xl font-bold tracking-tight">Reve</span>
        <Button
          size="icon"
          variant="secondary"
          aria-label="내 프로젝트"
          className="rounded-full"
          onClick={goToWorkspace}
        >
          <UserIcon />
        </Button>
      </div>

      <div className="flex flex-col items-center gap-6 px-6 pt-16">
        <h1 className="text-3xl font-medium text-neutral-500">무엇을 만드실 건가요?</h1>

        <div className="flex w-full max-w-xl items-center gap-2 rounded-full border border-border bg-white px-2 py-2 shadow-sm">
          <Input
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleStart();
            }}
            placeholder="레브에게 물어보세요"
            className="h-9 flex-1 rounded-full border-none bg-transparent shadow-none focus-visible:ring-0"
          />
          <Button onClick={handleStart} className="gap-1.5 rounded-full">
            Start
            <ArrowRightIcon />
          </Button>
        </div>
      </div>

      <div className="mt-16 flex-1 overflow-hidden px-6">
        <p className="mb-4 text-center text-sm text-muted-foreground">Start with this image</p>
        <div className="flex gap-3 overflow-x-auto pb-6">
          {SAMPLE_START_IMAGES.map((url) => (
            <button
              key={url}
              type="button"
              onClick={() => handleStartWithImage(url)}
              disabled={isStartingImage !== null}
              className="relative h-72 w-56 shrink-0 overflow-hidden rounded-xl bg-neutral-200 transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={url} alt="" className="h-full w-full object-cover" />
              {isStartingImage === url && (
                <div className="absolute inset-0 flex items-center justify-center bg-black/30">
                  <Loader2Icon className="size-6 animate-spin text-white" />
                </div>
              )}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
