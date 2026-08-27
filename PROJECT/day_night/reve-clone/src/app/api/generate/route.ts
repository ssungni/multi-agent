import { NextResponse } from "next/server";
import OpenAI from "openai";

import type { AspectRatio } from "@/types";

const PORTRAIT_RATIOS: AspectRatio[] = ["3:4", "9:16"];

function sizeForRatio(ratio: AspectRatio): "1024x1024" | "1024x1536" | "1536x1024" {
  if (ratio === "1:1") return "1024x1024";
  if (PORTRAIT_RATIOS.includes(ratio)) return "1024x1536";
  return "1536x1024";
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
  const prompt = typeof body.prompt === "string" ? body.prompt.trim() : "";
  const ratio: AspectRatio = body.ratio;
  const count = Math.min(Math.max(Number(body.count) || 1, 1), 10);

  if (!prompt) {
    return NextResponse.json({ error: "프롬프트를 입력해 주세요." }, { status: 400 });
  }

  const size = sizeForRatio(ratio);
  const [width, height] = size.split("x").map(Number);

  try {
    const client = new OpenAI({ apiKey });
    const result = await client.images.generate({
      model: "gpt-image-1",
      prompt,
      size,
      n: count,
      quality: "medium",
    });

    const images = (result.data ?? [])
      .filter((img) => img.b64_json)
      .map((img) => ({
        url: `data:image/png;base64,${img.b64_json}`,
        width,
        height,
      }));

    return NextResponse.json({ images });
  } catch (err) {
    const message =
      err instanceof OpenAI.APIError ? err.message : "이미지 생성 중 오류가 발생했습니다.";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
