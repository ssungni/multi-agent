"use client";

import { AlertCircleIcon, Loader2Icon, SparklesIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { RatioSelect } from "@/components/prompt/ratio-select";
import { CountSelect } from "@/components/prompt/count-select";
import { useGalleryStore } from "@/store/use-gallery-store";

export function PromptBar() {
  const prompt = useGalleryStore((s) => s.prompt);
  const setPrompt = useGalleryStore((s) => s.setPrompt);
  const isGenerating = useGalleryStore((s) => s.isGenerating);
  const generationError = useGalleryStore((s) => s.generationError);
  const generateImages = useGalleryStore((s) => s.generateImages);

  function handleGenerate() {
    void generateImages();
  }

  return (
    <div className="border-b border-border bg-background px-6 py-4">
      <div className="mx-auto flex max-w-4xl flex-col gap-2.5">
        <Textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
              e.preventDefault();
              handleGenerate();
            }
          }}
          placeholder="만들고 싶은 이미지를 설명해 주세요... (예: 안개 낀 새벽 숲 속의 사슴, 시네마틱 라이팅)"
          rows={2}
          className="resize-none text-sm"
        />
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <RatioSelect />
            <CountSelect />
          </div>
          <Button onClick={handleGenerate} disabled={!prompt.trim() || isGenerating} className="gap-1.5">
            {isGenerating ? (
              <>
                <Loader2Icon className="animate-spin" />
                생성 중...
              </>
            ) : (
              <>
                <SparklesIcon />
                생성하기
              </>
            )}
          </Button>
        </div>
        {generationError && (
          <p className="flex items-center gap-1.5 text-xs text-destructive">
            <AlertCircleIcon className="size-3.5" />
            {generationError}
          </p>
        )}
      </div>
    </div>
  );
}
