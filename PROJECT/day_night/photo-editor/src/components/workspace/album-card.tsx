"use client";

import { useState } from "react";
import { Trash2Icon } from "lucide-react";

import { Input } from "@/components/ui/input";
import { useWorkspaceStore } from "@/store/use-workspace-store";
import type { Album } from "@/types";

function timeAgo(ts: number): string {
  const minutes = Math.floor((Date.now() - ts) / 60000);
  if (minutes < 1) return "방금 전";
  if (minutes < 60) return `${minutes}분 전`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}시간 전`;
  const days = Math.floor(hours / 24);
  return `${days}일 전`;
}

export function AlbumCard({ album }: { album: Album }) {
  const session = useWorkspaceStore((s) => s.sessions[album.id]);
  const openAlbum = useWorkspaceStore((s) => s.openAlbum);
  const renameAlbum = useWorkspaceStore((s) => s.renameAlbum);
  const deleteAlbum = useWorkspaceStore((s) => s.deleteAlbum);

  const [isEditing, setIsEditing] = useState(false);
  const [nameValue, setNameValue] = useState(album.name);

  function commitRename() {
    renameAlbum(album.id, nameValue);
    setIsEditing(false);
  }

  function handleDelete(e: React.MouseEvent) {
    e.stopPropagation();
    if (window.confirm(`"${album.name}"을(를) 삭제할까요?`)) {
      deleteAlbum(album.id);
    }
  }

  return (
    <div className="group flex flex-col gap-2">
      <div
        role="button"
        tabIndex={0}
        onClick={() => openAlbum(album.id)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            openAlbum(album.id);
          }
        }}
        className="relative flex aspect-square w-full cursor-pointer items-center justify-center overflow-hidden rounded-xl bg-neutral-100"
      >
        {session?.imageUrl ? (
          // eslint-disable-next-line @next/next/no-img-element
          <img src={session.imageUrl} alt={album.name} className="h-full w-full object-cover" />
        ) : (
          <span className="text-4xl font-light text-neutral-300">+</span>
        )}
        <button
          type="button"
          onClick={handleDelete}
          aria-label="앨범 삭제"
          className="absolute top-2 right-2 hidden size-7 items-center justify-center rounded-full bg-black/60 text-white group-hover:flex"
        >
          <Trash2Icon className="size-3.5" />
        </button>
      </div>

      {isEditing ? (
        <Input
          autoFocus
          value={nameValue}
          onChange={(e) => setNameValue(e.target.value)}
          onBlur={commitRename}
          onKeyDown={(e) => {
            if (e.key === "Enter") commitRename();
            if (e.key === "Escape") setIsEditing(false);
          }}
          className="h-7 text-sm"
        />
      ) : (
        <button
          type="button"
          onClick={() => {
            setNameValue(album.name);
            setIsEditing(true);
          }}
          className="truncate text-left text-sm font-medium hover:underline"
        >
          {album.name}
        </button>
      )}
      <span className="text-xs text-muted-foreground">{timeAgo(album.updatedAt)}</span>
    </div>
  );
}
