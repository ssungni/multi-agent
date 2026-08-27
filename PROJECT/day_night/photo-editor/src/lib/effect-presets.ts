import type { EffectPreset } from "@/types";

/**
 * CSS `filter` approximations of Reve-style presets. These are live,
 * real-time filters (not baked pixel textures like true halftone/grain
 * synthesis, which would need canvas/WebGL shaders) — a pragmatic v1
 * that keeps every preset genuinely interactive.
 */
export const EFFECT_PRESETS: EffectPreset[] = [
  // Textures
  { id: "cmyk-halftone", name: "CMYK Halftone", category: "textures", filter: "contrast(1.6) saturate(2.2) brightness(1.05)" },
  { id: "grain", name: "Grain", category: "textures", filter: "contrast(1.15) saturate(0.9) brightness(0.97)" },
  { id: "dither", name: "Dither", category: "textures", filter: "grayscale(1) contrast(1.8) brightness(1.1)" },
  { id: "texture-overlay", name: "Texture Overlay", category: "textures", filter: "contrast(1.2) sepia(0.15) saturate(1.1)" },
  { id: "stippling", name: "Stippling", category: "textures", filter: "grayscale(0.9) contrast(1.5)" },
  { id: "retro-handhold", name: "Retro Handhold", category: "textures", filter: "sepia(0.35) contrast(1.1) saturate(1.3) brightness(1.02)" },
  { id: "engraving", name: "Engraving", category: "textures", filter: "grayscale(1) contrast(2)" },
  { id: "risograph", name: "Risograph", category: "textures", filter: "saturate(2.5) contrast(1.1) hue-rotate(-8deg)" },
  { id: "engraving-pass", name: "Engraving Pass", category: "textures", filter: "grayscale(0.85) contrast(1.7) brightness(1.05)" },
  { id: "halftone-texture", name: "Halftone Texture", category: "textures", filter: "contrast(1.5) saturate(1.6) brightness(1.08)" },
  { id: "color-tile", name: "Color Tile", category: "textures", filter: "saturate(1.8) contrast(1.3)" },
  { id: "geomosaic", name: "Geomosaic", category: "textures", filter: "saturate(1.6) contrast(1.4) hue-rotate(6deg)" },

  // Light
  { id: "vignette", name: "Vignette", category: "light", filter: "brightness(0.97) contrast(1.1)" },
  { id: "zoom-blur", name: "Zoom Blur", category: "light", filter: "contrast(1.05) brightness(1.05) blur(0.3px)" },
  { id: "halation", name: "Halation", category: "light", filter: "brightness(1.12) contrast(0.95) saturate(1.15)" },
  { id: "light-leak", name: "Light Leak", category: "light", filter: "brightness(1.15) saturate(1.2) hue-rotate(8deg)" },
  { id: "motion-blur", name: "Motion Blur", category: "light", filter: "blur(0.6px) brightness(1.03)" },
  { id: "spin-blur", name: "Spin Blur", category: "light", filter: "blur(0.4px) contrast(1.05)" },
  { id: "faceted-glass", name: "Faceted Glass", category: "light", filter: "contrast(1.2) brightness(1.05) saturate(1.1)" },
  { id: "frosted-glass", name: "Frosted Glass", category: "light", filter: "blur(1.2px) brightness(1.08)" },
  { id: "glow", name: "Glow", category: "light", filter: "brightness(1.2) contrast(0.95) saturate(1.1)" },
  { id: "star-highlight", name: "Star Highlight", category: "light", filter: "brightness(1.15) contrast(1.1)" },
  { id: "sun-rays", name: "Sun Rays", category: "light", filter: "brightness(1.2) saturate(1.25) hue-rotate(-4deg)" },
  { id: "tilt-shift", name: "Tilt Shift", category: "light", filter: "saturate(1.3) contrast(1.15) blur(0.3px)" },
  { id: "chromatic-aberration", name: "Chromatic Aberration", category: "light", filter: "saturate(1.4) contrast(1.1) hue-rotate(3deg)" },
  { id: "heat-distortion", name: "Heat Distortion", category: "light", filter: "blur(0.5px) brightness(1.05) saturate(1.15)" },
  { id: "lens-flare", name: "Lens Flare", category: "light", filter: "brightness(1.25) contrast(0.92)" },
  { id: "bokeh", name: "Bokeh", category: "light", filter: "blur(0.8px) brightness(1.1) saturate(1.1)" },

  // Color
  { id: "deep-cine-2", name: "Deep Cine 2", category: "color", filter: "contrast(1.25) saturate(1.3) brightness(0.95) hue-rotate(-6deg)" },
  { id: "neon-day", name: "Neon Day", category: "color", filter: "saturate(1.8) contrast(1.15) brightness(1.05)" },
  { id: "neon-night", name: "Neon Night", category: "color", filter: "saturate(1.9) contrast(1.3) brightness(0.85) hue-rotate(-12deg)" },
  { id: "neon-port", name: "Neon Port", category: "color", filter: "saturate(1.7) hue-rotate(-10deg) brightness(1.02)" },
  { id: "sand-cine-3", name: "Sand Cine 3", category: "color", filter: "sepia(0.25) saturate(1.2) contrast(1.1)" },
  { id: "duotone", name: "Duotone", category: "color", filter: "grayscale(1) sepia(0.6) hue-rotate(200deg) saturate(3)" },
  { id: "clean-land", name: "Clean Land", category: "color", filter: "saturate(1.1) contrast(1.05) brightness(1.03)" },
  { id: "vivid-land-1", name: "Vivid Land 1", category: "color", filter: "saturate(1.6) contrast(1.15)" },
  { id: "vivid-land-2", name: "Vivid Land 2", category: "color", filter: "saturate(1.75) contrast(1.2) brightness(1.02)" },
  { id: "vivid-port", name: "Vivid Port", category: "color", filter: "saturate(1.5) contrast(1.1) brightness(1.05)" },
  { id: "warm-port", name: "Warm Port", category: "color", filter: "sepia(0.2) saturate(1.3) brightness(1.03)" },
  { id: "grit-mono", name: "Grit Mono", category: "color", filter: "grayscale(1) contrast(1.35) brightness(0.98)" },
  { id: "low-light", name: "Low Light", category: "color", filter: "brightness(0.8) contrast(1.2) saturate(0.9)" },
  { id: "punch-day", name: "Punch Day", category: "color", filter: "saturate(1.5) contrast(1.25) brightness(1.05)" },
  { id: "quiet-port", name: "Quiet Port", category: "color", filter: "saturate(0.85) contrast(0.95) brightness(1.02)" },
  { id: "soft-day", name: "Soft Day", category: "color", filter: "saturate(1.05) contrast(0.9) brightness(1.08)" },
  { id: "soft-port", name: "Soft Port", category: "color", filter: "saturate(0.95) contrast(0.92) brightness(1.05) sepia(0.08)" },
  { id: "story-mono", name: "Story Mono", category: "color", filter: "grayscale(1) contrast(1.1) brightness(1.05)" },
];

export function getEffectById(id: string | null): EffectPreset | undefined {
  if (!id) return undefined;
  return EFFECT_PRESETS.find((preset) => preset.id === id);
}
