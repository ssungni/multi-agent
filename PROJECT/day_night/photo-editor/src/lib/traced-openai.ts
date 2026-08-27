import OpenAI from "openai";
import { traceable } from "langsmith/traceable";
import { wrapOpenAI } from "langsmith/wrappers/openai";

function getClient() {
  return new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
}

/** Chat Completions calls (used for segmentation) get full LangSmith LLM-run tracing. */
export function getTracedChatClient() {
  return wrapOpenAI(getClient());
}

/**
 * `wrapOpenAI` only instruments chat/completions/responses, not the Images
 * API, so images.generate/edit are traced manually here. `processInputs`
 * strips the raw image file from edit calls so multi-MB binaries never get
 * pushed into LangSmith, and `processOutputs` logs metadata only (not the
 * base64 payload) to keep traces lean.
 */
export const generateImage = traceable(
  async (params: OpenAI.Images.ImageGenerateParamsNonStreaming) => getClient().images.generate(params),
  {
    name: "openai.images.generate",
    run_type: "tool",
    processOutputs: (output: OpenAI.Images.ImagesResponse) => ({
      created: output.created,
      image_count: output.data?.length ?? 0,
    }),
  }
);

export const editImage = traceable(
  async (params: OpenAI.Images.ImageEditParamsNonStreaming) => getClient().images.edit(params),
  {
    name: "openai.images.edit",
    run_type: "tool",
    processInputs: (inputs: Record<string, unknown>) => {
      const rest = { ...inputs };
      delete rest.image;
      return rest;
    },
    processOutputs: (output: OpenAI.Images.ImagesResponse) => ({
      created: output.created,
      image_count: output.data?.length ?? 0,
    }),
  }
);
