"use client";

import { RatioIcon } from "lucide-react";

import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ASPECT_RATIOS, type AspectRatio } from "@/types";
import { useGalleryStore } from "@/store/use-gallery-store";

export function RatioSelect() {
  const ratio = useGalleryStore((s) => s.ratio);
  const setRatio = useGalleryStore((s) => s.setRatio);

  return (
    <Select value={ratio} onValueChange={(value) => setRatio(value as AspectRatio)}>
      <SelectTrigger size="sm" className="min-w-[92px]">
        <RatioIcon className="text-muted-foreground" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        {ASPECT_RATIOS.map((r) => (
          <SelectItem key={r.value} value={r.value}>
            {r.value}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}
