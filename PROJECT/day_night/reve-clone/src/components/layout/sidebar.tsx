"use client";

import { useState } from "react";
import { ImagesIcon, PlusIcon } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { AlbumRow } from "@/components/layout/album-row";
import { useGalleryStore } from "@/store/use-gallery-store";

export function Sidebar() {
  const albums = useGalleryStore((s) => s.albums);
  const images = useGalleryStore((s) => s.images);
  const activeAlbumId = useGalleryStore((s) => s.activeAlbumId);
  const createAlbum = useGalleryStore((s) => s.createAlbum);

  const [isCreating, setIsCreating] = useState(false);
  const [newAlbumName, setNewAlbumName] = useState("");

  function handleCreateAlbum() {
    createAlbum(newAlbumName);
    setNewAlbumName("");
    setIsCreating(false);
  }

  return (
    <aside className="flex h-full w-64 shrink-0 flex-col border-r border-border bg-sidebar text-sidebar-foreground">
      <div className="flex items-center gap-2 px-4 py-4">
        <div className="flex size-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <ImagesIcon className="size-4" />
        </div>
        <span className="text-sm font-semibold">Reve Clone</span>
      </div>

      <div className="flex items-center justify-between px-4 pt-2 pb-1">
        <span className="text-xs font-medium text-muted-foreground">앨범</span>
        <Button
          variant="ghost"
          size="icon-xs"
          onClick={() => setIsCreating((v) => !v)}
          aria-label="새 앨범 만들기"
        >
          <PlusIcon />
        </Button>
      </div>

      {isCreating && (
        <div className="flex items-center gap-1.5 px-4 pb-2">
          <Input
            autoFocus
            value={newAlbumName}
            onChange={(e) => setNewAlbumName(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter") handleCreateAlbum();
              if (e.key === "Escape") setIsCreating(false);
            }}
            placeholder="앨범 이름"
            className="h-7 text-xs"
          />
          <Button size="xs" onClick={handleCreateAlbum}>
            추가
          </Button>
        </div>
      )}

      <nav className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-4">
        {albums.map((album) => {
          const count = images.filter((img) => img.albumId === album.id).length;
          return (
            <AlbumRow
              key={album.id}
              album={album}
              count={count}
              isActive={album.id === activeAlbumId}
            />
          );
        })}
      </nav>
    </aside>
  );
}
