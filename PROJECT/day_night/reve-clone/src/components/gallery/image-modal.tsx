"use client";

import Image from "next/image";
import { DownloadIcon, FolderInputIcon, Trash2Icon } from "lucide-react";

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { MoveToAlbumMenu } from "@/components/gallery/move-to-album-menu";
import { useGalleryStore } from "@/store/use-gallery-store";

export function ImageModal() {
  const selectedImageId = useGalleryStore((s) => s.selectedImageId);
  const image = useGalleryStore((s) =>
    s.images.find((img) => img.id === s.selectedImageId)
  );
  const selectImage = useGalleryStore((s) => s.selectImage);
  const deleteImage = useGalleryStore((s) => s.deleteImage);

  const open = Boolean(selectedImageId) && Boolean(image);

  function handleDelete() {
    if (!image) return;
    deleteImage(image.id);
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !next && selectImage(null)}>
      <DialogContent className="max-w-2xl! p-0">
        {image && (
          <>
            <div className="relative max-h-[70vh] overflow-hidden rounded-t-xl bg-muted">
              <Image
                src={image.url}
                alt={image.prompt}
                width={image.width}
                height={image.height}
                className="mx-auto max-h-[70vh] w-auto object-contain"
              />
            </div>
            <DialogHeader className="px-4 pt-1">
              <DialogTitle className="sr-only">이미지 상세보기</DialogTitle>
              <DialogDescription className="text-sm text-foreground">
                {image.prompt}
              </DialogDescription>
              <p className="text-xs text-muted-foreground">비율 {image.ratio}</p>
            </DialogHeader>
            <DialogFooter>
              <Button
                variant="destructive"
                onClick={handleDelete}
                className="gap-1.5"
              >
                <Trash2Icon />
                삭제
              </Button>
              <MoveToAlbumMenu
                imageId={image.id}
                currentAlbumId={image.albumId}
                triggerElement={<Button variant="outline" className="gap-1.5" />}
              >
                <FolderInputIcon />
                다른 앨범으로
              </MoveToAlbumMenu>
              <Button
                className="gap-1.5"
                nativeButton={false}
                render={
                  <a
                    href={image.url}
                    download={`${image.id}.jpg`}
                    target="_blank"
                    rel="noreferrer"
                  />
                }
              >
                <DownloadIcon />
                다운로드
              </Button>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
