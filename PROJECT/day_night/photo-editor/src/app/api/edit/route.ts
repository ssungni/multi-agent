import { NextResponse } from "next/server";
import OpenAI, { toFile } from "openai";

import { editImage } from "@/lib/traced-openai";

function decodeDataUrl(dataUrl: string): { buffer: Buffer; mime: string } {
  const match = /^data:(image\/\w+);base64,(.+)$/.exec(dataUrl);
  if (!match) throw new Error("올바르지 않은 이미지 데이터입니다.");
  const [, mime, base64] = match;
  return { buffer: Buffer.from(base64, "base64"), mime };
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
  const imageDataUrl = typeof body.imageDataUrl === "string" ? body.imageDataUrl : "";

  if (!prompt || !imageDataUrl) {
    return NextResponse.json({ error: "이미지와 편집 요청을 모두 입력해 주세요." }, { status: 400 });
  }

  try {
    const { buffer, mime } = decodeDataUrl(imageDataUrl);
    const ext = mime.split("/")[1] === "jpeg" ? "jpg" : mime.split("/")[1];
    const file = await toFile(buffer, `image.${ext}`, { type: mime });

    const result = await editImage({
      model: "gpt-image-1",
      image: file,
      prompt,
      size: "auto",
      quality: "medium",
    });

    const b64 = result.data?.[0]?.b64_json;
    if (!b64) {
      throw new Error("이미지 편집 결과가 비어 있습니다.");
    }

    return NextResponse.json({ url: `data:image/png;base64,${b64}` });
  } catch (err) {
    const message =
      err instanceof OpenAI.APIError ? err.message : "이미지 편집 중 오류가 발생했습니다.";
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
