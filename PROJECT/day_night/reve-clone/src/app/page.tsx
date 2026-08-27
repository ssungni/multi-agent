import { PromptBar } from "@/components/prompt/prompt-bar";
import { MasonryGrid } from "@/components/gallery/masonry-grid";
import { ImageModal } from "@/components/gallery/image-modal";

export default function Home() {
  return (
    <>
      <PromptBar />
      <div className="flex-1 overflow-y-auto px-6 py-5">
        <MasonryGrid />
      </div>
      <ImageModal />
    </>
  );
}
