"use client";

import type { Rect } from "@/types";

const HANDLE_POSITIONS = [
  "-top-1.5 -left-1.5",
  "-top-1.5 -right-1.5",
  "-bottom-1.5 -left-1.5",
  "-bottom-1.5 -right-1.5",
];

export function BoundingBox({ name, bbox }: { name: string; bbox: Rect }) {
  const { x, y, width, height } = bbox;

  return (
    <div
      className="pointer-events-none absolute border-2 border-blue-500"
      style={{
        left: `${x * 100}%`,
        top: `${y * 100}%`,
        width: `${width * 100}%`,
        height: `${height * 100}%`,
      }}
    >
      {HANDLE_POSITIONS.map((pos) => (
        <span
          key={pos}
          className={`absolute ${pos} size-3 rounded-[2px] border border-blue-500 bg-white`}
        />
      ))}
      <span className="absolute right-0 -bottom-6 rounded bg-neutral-900/85 px-2 py-0.5 text-xs whitespace-nowrap text-white">
        {name}
      </span>
      <button
        type="button"
        className="pointer-events-auto absolute bottom-2 left-1/2 -translate-x-1/2 rounded-full bg-neutral-900/85 px-3 py-1 text-xs text-white hover:bg-neutral-900"
      >
        Edit
      </button>
    </div>
  );
}
