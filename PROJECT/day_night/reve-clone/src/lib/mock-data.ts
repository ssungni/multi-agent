import { ASPECT_RATIOS, type Album, type AspectRatio, type GeneratedImage } from "@/types";

export const MOCK_ALBUMS: Album[] = [
  { id: "album-portraits", name: "인물 초상화" },
  { id: "album-landscapes", name: "풍경" },
  { id: "album-concept", name: "컨셉 아트" },
];

function ratioSize(ratio: AspectRatio) {
  const found = ASPECT_RATIOS.find((r) => r.value === ratio);
  return found ? { w: found.w, h: found.h } : { w: 512, h: 512 };
}

export function placeholderImageUrl(seed: string, ratio: AspectRatio) {
  const { w, h } = ratioSize(ratio);
  return `https://picsum.photos/seed/${seed}/${w}/${h}`;
}

const SEED_PROMPTS = [
  "안개 낀 새벽 숲 속의 사슴, 시네마틱 라이팅",
  "네온이 반사되는 비 오는 도쿄 뒷골목",
  "따뜻한 오후 햇살이 드는 도서관 창가",
  "사막 위로 떠오르는 거대한 보름달",
  "미니멀한 스칸디나비아 스타일의 거실",
  "구름 위를 나는 증기기관 비행선",
];

let seedCounter = 0;
function nextSeed() {
  seedCounter += 1;
  return seedCounter;
}

export function createMockImage(albumId: string, prompt: string, ratio: AspectRatio): GeneratedImage {
  const seed = nextSeed();
  const { w, h } = ratioSize(ratio);
  return {
    id: `img-${seed}`,
    albumId,
    url: placeholderImageUrl(`reve-seed-${seed}`, ratio),
    prompt,
    ratio,
    width: w,
    height: h,
    createdAt: Date.now(),
  };
}

export function createInitialImages(): GeneratedImage[] {
  const ratios: AspectRatio[] = ["1:1", "3:4", "4:3", "9:16", "16:9"];
  const images: GeneratedImage[] = [];

  MOCK_ALBUMS.forEach((album, albumIdx) => {
    const count = 4 + albumIdx;
    for (let i = 0; i < count; i++) {
      const ratio = ratios[(albumIdx + i) % ratios.length];
      const prompt = SEED_PROMPTS[(albumIdx + i) % SEED_PROMPTS.length];
      images.push(createMockImage(album.id, prompt, ratio));
    }
  });

  return images;
}
