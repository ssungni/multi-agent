import { NextResponse } from "next/server";
import OpenAI from "openai";

import { getTracedChatClient } from "@/lib/traced-openai";
import type { DetectedLayer, Rect } from "@/types";

const PART_PROPERTIES = {
  label: {
    type: "string",
    description: "Short lowercase noun for the object or part, e.g. 'lion', 'head', 'wheel'",
  },
  x: { type: "number", description: "left edge of bounding box, in pixels" },
  y: { type: "number", description: "top edge of bounding box, in pixels" },
  width: { type: "number", description: "box width, in pixels" },
  height: { type: "number", description: "box height, in pixels" },
} as const;

const SEGMENT_SCHEMA = {
  name: "object_detection",
  strict: true,
  schema: {
    type: "object",
    properties: {
      objects: {
        type: "array",
        maxItems: 30,
        items: {
          type: "object",
          properties: {
            ...PART_PROPERTIES,
            parts: {
              type: "array",
              maxItems: 20,
              description:
                "Identifiable sub-parts of this object (e.g. head, torso, arms for a person), " +
                "empty array if none apply.",
              items: {
                type: "object",
                properties: PART_PROPERTIES,
                required: ["label", "x", "y", "width", "height"],
                additionalProperties: false,
              },
            },
          },
          required: ["label", "x", "y", "width", "height", "parts"],
          additionalProperties: false,
        },
      },
    },
    required: ["objects"],
    additionalProperties: false,
  },
} as const;

interface DetectedPart {
  label: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface DetectedObject extends DetectedPart {
  parts: DetectedPart[];
}

const MIN_PX = 3;

function toNormalizedBBox(part: DetectedPart, imageWidth: number, imageHeight: number): Rect {
  const minW = MIN_PX / imageWidth;
  const minH = MIN_PX / imageHeight;
  const x = Math.max(0, Math.min(1, part.x / imageWidth));
  const y = Math.max(0, Math.min(1, part.y / imageHeight));
  return {
    x,
    y,
    width: Math.max(minW, Math.min(1 - x, part.width / imageWidth)),
    height: Math.max(minH, Math.min(1 - y, part.height / imageHeight)),
  };
}

export async function POST(request: Request) {
  const apiKey = process.env.OPENAI_API_KEY;
  if (!apiKey) {
    return NextResponse.json(
      { error: "OPENAI_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인해 주세요." },
      { status: 500 }
    );
  }

  const body = await request.json();
  const imageDataUrl = typeof body.imageDataUrl === "string" ? body.imageDataUrl : "";
  const imageWidth = Number(body.width);
  const imageHeight = Number(body.height);

  if (!imageDataUrl) {
    return NextResponse.json({ error: "이미지가 없습니다." }, { status: 400 });
  }
  if (!imageWidth || !imageHeight) {
    return NextResponse.json({ error: "이미지 크기 정보가 없습니다." }, { status: 400 });
  }

  try {
    const client = getTracedChatClient();
    const completion = await client.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "user",
          content: [
            {
              type: "text",
              text:
                `This image is ${imageWidth}px wide and ${imageHeight}px tall (top-left origin). ` +
                "Detect all identifiable objects in this image as comprehensively as possible. " +
                "For each object, provide its bounding box in pixel coordinates (x, y, width, " +
                "height) using the exact pixel dimensions given above. Detect not only standalone " +
                "objects such as people, animals, vehicles, furniture, and tools, but also " +
                "meaningful parts of those objects as nested entries in that object's `parts` " +
                "array whenever they are visually distinguishable. For example, if a person is " +
                "detected, also detect individual body parts such as the head, face, eyes, nose, " +
                "mouth, ears, neck, shoulders, arms, hands, fingers, torso, legs, feet, shoes, hat, " +
                "glasses, and any other identifiable components as parts of that person. Likewise, " +
                "for animals or inanimate objects, detect significant parts whenever possible (e.g., " +
                "a car's wheels, doors, windows, headlights, etc.) as parts of that object. Exclude " +
                "background regions, shadows, reflections, textures, and non-semantic patterns. Only " +
                "detect meaningful objects and their identifiable components, with a pixel bounding " +
                "box for each.",
            },
            { type: "image_url", image_url: { url: imageDataUrl } },
          ],
        },
      ],
      response_format: { type: "json_schema", json_schema: SEGMENT_SCHEMA },
    });

    const raw = completion.choices[0]?.message?.content;
    if (!raw) throw new Error("객체 감지 결과가 비어 있습니다.");

    const parsed = JSON.parse(raw) as { objects: DetectedObject[] };

    const layers: DetectedLayer[] = [
      { id: "layer-root", name: "Uploaded image", bbox: { x: 0, y: 0, width: 1, height: 1 } },
    ];

    parsed.objects.forEach((obj, i) => {
      const objectId = `layer-obj-${i}`;
      layers.push({
        id: objectId,
        name: obj.label,
        bbox: toNormalizedBBox(obj, imageWidth, imageHeight),
        parentId: "layer-root",
      });
      (obj.parts ?? []).forEach((part, j) => {
        layers.push({
          id: `${objectId}-part-${j}`,
          name: part.label,
          bbox: toNormalizedBBox(part, imageWidth, imageHeight),
          parentId: objectId,
        });
      });
    });

    layers.push({
      id: "layer-background",
      name: "background",
      bbox: { x: 0, y: 0, width: 1, height: 1 },
      isBackground: true,
      parentId: "layer-root",
    });

    return NextResponse.json({ layers });
  } catch (err) {
    const message =
      err instanceof OpenAI.APIError ? err.message : "객체 감지 중 오류가 발생했습니다.";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
