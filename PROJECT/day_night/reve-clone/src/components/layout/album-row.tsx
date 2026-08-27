"use client";

import { useState } from "react";
import { PencilIcon, Trash2Icon } from "lucide-react";

import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useGalleryStore } from "@/store/use-gallery-store";
import type { Album } from "@/types";

export function AlbumRow({
  album,
  count,
  isActive,
}: {
  album: Album;
  count: number;
  isActive: boolean;
}) {
  const albumCount = useGalleryStore((s) => s.albums.length);
  const setActiveAlbum = useGalleryStore((s) => s.setActiveAlbum);
  const renameAlbum = useGalleryStore((s) => s.renameAlbum);
  const deleteAlbum = useGalleryStore((s) => s.deleteAlbum);

  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(album.name);

  function startEditing() {
    setEditValue(album.name);
    setIsEditing(true);
  }

  function commitRename() {
    renameAlbum(album.id, editValue);
    setIsEditing(false);
  }

  function handleDelete() {
    const confirmed = window.confirm(
      `"${album.name}" 앨범을 삭제할까요? 포함된 이미지 ${count}장도 함께 삭제됩니다.`
    );
    if (confirmed) deleteAlbum(album.id);
  }

  if (isEditing) {
    return (
      <div className="flex items-center gap-1 px-0.5 py-0.5">
        <Input
          autoFocus
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onBlur={commitRename}
          onKeyDown={(e) => {
            if (e.key === "Enter") commitRename();
            if (e.key === "Escape") setIsEditing(false);
          }}
          className="h-7 flex-1 text-xs"
        />
      </div>
    );
  }

  return (
    <div
      className={cn(
        "group flex items-center gap-0.5 rounded-lg pr-1 pl-0.5 text-sm transition-colors",
        isActive
          ? "bg-sidebar-accent text-sidebar-accent-foreground"
          : "hover:bg-sidebar-accent/60"
      )}
    >
      <button
        onClick={() => setActiveAlbum(album.id)}
        className="flex min-w-0 flex-1 items-center justify-between rounded-md px-2 py-1.5 text-left"
      >
        <span className="truncate">{album.name}</span>
        <span className="ml-2 shrink-0 text-xs text-muted-foreground">{count}</span>
      </button>
      <Button
        variant="ghost"
        size="icon-xs"
        aria-label="앨범 이름 변경"
        onClick={startEditing}
        className="shrink-0 opacity-0 group-hover:opacity-100"
      >
        <PencilIcon />
      </Button>
      <Button
        variant="ghost"
        size="icon-xs"
        aria-label="앨범 삭제"
        disabled={albumCount <= 1}
        onClick={handleDelete}
        className="shrink-0 opacity-0 group-hover:opacity-100"
      >
        <Trash2Icon />
      </Button>
    </div>
  );
}
