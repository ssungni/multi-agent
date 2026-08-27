"use client";

import { LayoutGridIcon } from "lucide-react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { IMAGE_COUNTS } from "@/types";
import { useGalleryStore } from "@/store/use-gallery-store";

export function CountSelect() {
  const count = useGalleryStore((s) => s.count);
  const setCount = useGalleryStore((s) => s.setCount);

  return (
    <Select value={String(count)} onValueChange={(value) => setCount(Number(value))}>
      <SelectTrigger size="sm" className="min-w-[76px]">
        <LayoutGridIcon className="text-muted-foreground" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {IMAGE_COUNTS.map((n) => (
          <SelectItem key={n} value={String(n)}>
            {n}장
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
