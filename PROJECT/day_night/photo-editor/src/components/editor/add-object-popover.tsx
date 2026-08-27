"use client";

import { useState } from "react";
import { SendIcon, XIcon } from "lucide-react";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";

export function AddObjectPopover({
  x,
  y,
  onSubmit,
  onCancel,
}: {
  x: number;
  y: number;
  onSubmit: (prompt: string) => void;
  onCancel: () => void;
}) {
  const [value, setValue] = useState("");

  function handleSubmit() {
    if (!value.trim()) return;
    onSubmit(value.trim());
  }

  return (
    <div
      className="absolute z-10 flex w-64 -translate-x-1/2 flex-col gap-2 rounded-xl border border-border bg-popover p-2 shadow-lg"
      style={{ left: `${x * 100}%`, top: `${y * 100}%` }}
      onClick={(e) => e.stopPropagation()}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-muted-foreground">이 위치에 추가할 객체</span>
        <button type="button" onClick={onCancel} className="text-muted-foreground hover:text-foreground">
          <XIcon className="size-3.5" />
        </button>
      </div>
      <div className="flex items-center gap-1.5">
        <Input
          autoFocus
          value={value}
          onChange={(e) => setValue(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleSubmit();
            if (e.key === "Escape") onCancel();
          }}
          placeholder="예: 빨간 풍선"
          className="h-8 text-xs"
        />
        <Button size="icon-sm" onClick={handleSubmit} aria-label="추가">
          <SendIcon />
        </Button>
      </div>
    </div>
  );
}
