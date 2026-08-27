"use client";

import { useRef, useState } from "react";
import { UploadIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { useEditorStore } from "@/store/use-editor-store";

export function UploadDropzone() {
  const uploadImage = useEditorStore((s) => s.uploadImage);
  const [isDragOver, setIsDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (file) void uploadImage(file);
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setIsDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) void uploadImage(file);
  }

  return (
    <div className="flex flex-1 items-center justify-center">
      <button
        type="button"
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setIsDragOver(true);
        }}
        onDragLeave={() => setIsDragOver(false)}
        onDrop={handleDrop}
        className={cn(
          "flex flex-col items-center gap-3 rounded-xl px-16 py-12 text-neutral-400 transition-colors",
          isDragOver && "bg-neutral-200/60 text-neutral-600"
        )}
      >
        <UploadIcon className="size-8" />
        <span className="text-lg">Upload and edit</span>
      </button>
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
