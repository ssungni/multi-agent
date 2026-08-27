"use client";

import { useRef, useState } from "react";
import { ArrowLeftIcon, DownloadIcon, Redo2Icon, Undo2Icon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useEditorStore } from "@/store/use-editor-store";
import { useWorkspaceStore } from "@/store/use-workspace-store";

export function TopBar() {
  const imageUrl = useEditorStore((s) => s.imageUrl);
  const history = useEditorStore((s) => s.history);
  const future = useEditorStore((s) => s.future);
  const undo = useEditorStore((s) => s.undo);
  const redo = useEditorStore((s) => s.redo);
  const uploadImage = useEditorStore((s) => s.uploadImage);

  const projectName = useWorkspaceStore((s) => s.projectName);
  const activeAlbumId = useWorkspaceStore((s) => s.activeAlbumId);
  const albums = useWorkspaceStore((s) => s.albums);
  const renameAlbum = useWorkspaceStore((s) => s.renameAlbum);
  const goToWorkspace = useWorkspaceStore((s) => s.goToWorkspace);

  const album = albums.find((a) => a.id === activeAlbumId);

  const [isEditingName, setIsEditingName] = useState(false);
  const [nameValue, setNameValue] = useState(album?.name ?? "");

  const fileInputRef = useRef<HTMLInputElement>(null);

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (file) void uploadImage(file);
  }

  function commitRename() {
    if (activeAlbumId) renameAlbum(activeAlbumId, nameValue);
    setIsEditingName(false);
  }

  return (
    <div className="flex items-center justify-between border-b border-border px-3 py-2.5">
      <div className="flex min-w-0 items-center gap-1.5 text-sm text-muted-foreground">
        <Button size="icon-xs" variant="ghost" aria-label="작업 공간으로" onClick={goToWorkspace}>
          <ArrowLeftIcon />
        </Button>
        <span className="truncate">{projectName}</span>
        <span>/</span>
        {isEditingName ? (
          <Input
            autoFocus
            value={nameValue}
            onChange={(e) => setNameValue(e.target.value)}
            onBlur={commitRename}
            onKeyDown={(e) => {
              if (e.key === "Enter") commitRename();
              if (e.key === "Escape") setIsEditingName(false);
            }}
            className="h-7 w-40 text-sm"
          />
        ) : (
          <button
            type="button"
            onClick={() => {
              setNameValue(album?.name ?? "");
              setIsEditingName(true);
            }}
            className="truncate font-medium text-foreground hover:underline"
          >
            {album?.name ?? "Untitled"}
          </button>
        )}
      </div>

      <div className="flex items-center gap-1">
        {imageUrl ? (
          <>
            <Button
              size="icon-sm"
              variant="ghost"
              aria-label="실행 취소"
              disabled={history.length === 0}
              onClick={undo}
            >
              <Undo2Icon />
            </Button>
            <Button
              size="icon-sm"
              variant="ghost"
              aria-label="다시 실행"
              disabled={future.length === 0}
              onClick={redo}
            >
              <Redo2Icon />
            </Button>
            <Button
              size="icon-sm"
              variant="ghost"
              aria-label="다운로드"
              nativeButton={false}
              render={<a href={imageUrl} download="edited-image.png" />}
            >
              <DownloadIcon />
            </Button>
          </>
        ) : (
          <Button variant="outline" className="rounded-full" onClick={() => fileInputRef.current?.click()}>
            Upload
          </Button>
        )}
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
