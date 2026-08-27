"use client";

import { useRef } from "react";
import { ArrowUpIcon, AtSignIcon, PaperclipIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useEditorStore } from "@/store/use-editor-store";

export function ChatBox() {
  const chatInput = useEditorStore((s) => s.chatInput);
  const setChatInput = useEditorStore((s) => s.setChatInput);
  const sendChatMessage = useEditorStore((s) => s.sendChatMessage);
  const isBusy = useEditorStore((s) => s.isBusy);
  const uploadImage = useEditorStore((s) => s.uploadImage);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleSend() {
    void sendChatMessage();
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (file) void uploadImage(file);
  }

  return (
    <div className="border-t border-border p-3">
      <div className="rounded-2xl border border-border bg-muted/40 p-2">
        <Textarea
          value={chatInput}
          onChange={(e) => setChatInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          placeholder="Ask Reve"
          rows={1}
          className="min-h-8 resize-none border-none bg-transparent p-1 shadow-none focus-visible:ring-0"
        />
        <div className="flex items-center justify-between pt-1">
          <div className="flex items-center gap-1 text-muted-foreground">
            <Button
              size="icon-xs"
              variant="ghost"
              aria-label="이미지 첨부"
              onClick={() => fileInputRef.current?.click()}
            >
              <PaperclipIcon />
            </Button>
            <Button size="icon-xs" variant="ghost" aria-label="멘션">
              <AtSignIcon />
            </Button>
            <span className="ml-0.5 size-4 rounded-full bg-[conic-gradient(from_90deg,#f87171,#facc15,#4ade80,#60a5fa,#c084fc,#f87171)]" />
          </div>
          <Button
            size="icon-sm"
            className="rounded-full"
            aria-label="보내기"
            disabled={!chatInput.trim() || isBusy}
            onClick={handleSend}
          >
            <ArrowUpIcon />
          </Button>
        </div>
      </div>
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        className="hidden"
        onChange={handleFileChange}
      />
    </div>
  );
}
