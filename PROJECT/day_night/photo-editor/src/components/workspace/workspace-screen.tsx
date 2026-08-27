"use client";

import { useState } from "react";
import { ChevronDownIcon, PlusIcon, SearchIcon, SparklesIcon, UserIcon } from "lucide-react";

import { cn } from "@/lib/utils";
import { Input } from "@/components/ui/input";
import { useWorkspaceStore } from "@/store/use-workspace-store";
import { AlbumCard } from "@/components/workspace/album-card";

export function WorkspaceScreen() {
  const projectName = useWorkspaceStore((s) => s.projectName);
  const renameProject = useWorkspaceStore((s) => s.renameProject);
  const albums = useWorkspaceStore((s) => s.albums);
  const createAlbum = useWorkspaceStore((s) => s.createAlbum);
  const goToStart = useWorkspaceStore((s) => s.goToStart);

  const [tab, setTab] = useState<"albums" | "references">("albums");
  const [isEditingName, setIsEditingName] = useState(false);
  const [nameValue, setNameValue] = useState(projectName);

  function commitRename() {
    renameProject(nameValue);
    setIsEditingName(false);
  }

  return (
    <div className="flex h-full flex-col overflow-y-auto bg-white px-8 py-6">
      <button
        type="button"
        onClick={goToStart}
        className="mb-6 flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
      >
        <SparklesIcon className="size-4" />
        {projectName}
      </button>

      <div className="mb-6 flex items-center gap-3">
        <div className="flex size-12 items-center justify-center rounded-2xl bg-gradient-to-br from-neutral-700 to-neutral-400 text-lg font-semibold text-white">
          <UserIcon className="size-5" />
        </div>
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
            className="h-9 max-w-xs text-xl font-semibold"
          />
        ) : (
          <button
            type="button"
            onClick={() => {
              setNameValue(projectName);
              setIsEditingName(true);
            }}
            className="flex items-center gap-1 text-xl font-semibold hover:opacity-80"
          >
            {projectName}
            <ChevronDownIcon className="size-4 text-muted-foreground" />
          </button>
        )}
      </div>

      <div className="mb-6 flex items-center justify-between border-b border-border">
        <div className="flex gap-6">
          <button
            type="button"
            onClick={() => setTab("albums")}
            className={cn(
              "border-b-2 pb-2 text-sm font-medium",
              tab === "albums" ? "border-foreground text-foreground" : "border-transparent text-muted-foreground"
            )}
          >
            Albums
          </button>
          <button
            type="button"
            onClick={() => setTab("references")}
            className={cn(
              "border-b-2 pb-2 text-sm font-medium",
              tab === "references"
                ? "border-foreground text-foreground"
                : "border-transparent text-muted-foreground"
            )}
          >
            References
          </button>
        </div>
        <div className="flex items-center gap-3 pb-2 text-sm text-muted-foreground">
          <span className="flex items-center gap-0.5">
            By newest <ChevronDownIcon className="size-3.5" />
          </span>
          <span className="flex items-center gap-0.5">
            All <ChevronDownIcon className="size-3.5" />
          </span>
          <SearchIcon className="size-4" />
        </div>
      </div>

      {tab === "albums" ? (
        <div className="grid grid-cols-2 gap-5 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5">
          <div className="flex flex-col gap-2">
            <button
              type="button"
              onClick={() => createAlbum()}
              className="flex aspect-square w-full flex-col items-center justify-center gap-2 rounded-xl bg-neutral-100 text-muted-foreground hover:bg-neutral-200"
            >
              <PlusIcon className="size-6" />
            </button>
            <span className="text-sm font-medium">New album</span>
            <span className="-mt-1.5 text-xs text-muted-foreground">Create images and videos</span>
          </div>
          {albums.map((album) => (
            <AlbumCard key={album.id} album={album} />
          ))}
        </div>
      ) : (
        <p className="py-12 text-center text-sm text-muted-foreground">
          참고 이미지가 없습니다.
        </p>
      )}
    </div>
  );
}
