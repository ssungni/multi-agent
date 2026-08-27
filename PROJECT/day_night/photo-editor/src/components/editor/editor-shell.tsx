"use client";

import { useEditorStore } from "@/store/use-editor-store";
import { TopBar } from "@/components/editor/top-bar";
import { CanvasStage } from "@/components/editor/canvas-stage";
import { UploadDropzone } from "@/components/editor/upload-dropzone";
import { Toolbar } from "@/components/editor/toolbar";
import { RightSidebar } from "@/components/sidebar/right-sidebar";

export function EditorShell() {
  const imageUrl = useEditorStore((s) => s.imageUrl);

  return (
    <div className="flex h-full flex-1 overflow-hidden">
      <div className="relative flex flex-1 flex-col overflow-hidden bg-neutral-100">
        <TopBar />
        <div className="relative flex flex-1 overflow-hidden">
          {imageUrl ? <CanvasStage /> : <UploadDropzone />}
          {imageUrl && <Toolbar />}
        </div>
      </div>
      <RightSidebar />
    </div>
  );
}
