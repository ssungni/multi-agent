import { NextResponse } from "next/server";
import OpenAI from "openai";

import { generateImage } from "@/lib/traced-openai";

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

  if (!prompt) {
    return NextResponse.json({ error: "프롬프트를 입력해 주세요." }, { status: 400 });
  }

  try {
    const result = await generateImage({
      model: "gpt-image-1",
      prompt,
      size: "1024x1024",
      n: 1,
      quality: "medium",
    });

    const b64 = result.data?.[0]?.b64_json;
    if (!b64) {
      throw new Error("이미지 생성 결과가 비어 있습니다.");
    }

    return NextResponse.json({ url: `data:image/png;base64,${b64}`, width: 1024, height: 1024 });
  } catch (err) {
    const message =
      err instanceof OpenAI.APIError ? err.message : "이미지 생성 중 오류가 발생했습니다.";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
