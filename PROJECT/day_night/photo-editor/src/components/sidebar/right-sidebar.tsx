"use client";

import { cn } from "@/lib/utils";
import { useEditorStore } from "@/store/use-editor-store";
import { LayerTree } from "@/components/sidebar/layer-tree";
import { ChatBox } from "@/components/sidebar/chat-box";
import { EffectsPanel } from "@/components/sidebar/effects-panel";

export function RightSidebar() {
  const imageUrl = useEditorStore((s) => s.imageUrl);
  const effectsPanelOpen = useEditorStore((s) => s.effectsPanelOpen);
  const errorMessage = useEditorStore((s) => s.errorMessage);
  const chatMessages = useEditorStore((s) => s.chatMessages);

  if (effectsPanelOpen) {
    return (
      <aside className="flex h-full w-96 shrink-0 flex-col border-l border-border bg-background">
        <EffectsPanel />
      </aside>
    );
  }

  return (
    <aside className="flex h-full w-96 shrink-0 flex-col border-l border-border bg-background">
      <div className="flex items-center gap-4 px-4 py-4">
        <span className="text-sm font-semibold">Create</span>
        {imageUrl && <span className="text-sm font-semibold">Edit</span>}
      </div>

      <div className="flex-1 overflow-y-auto">
        {!imageUrl ? (
          <div className="px-6 py-6 text-center">
            <p className="mb-4 text-xs text-muted-foreground">
              {new Date().toLocaleDateString("en-US", {
                month: "long",
                day: "numeric",
                year: "numeric",
              })}
            </p>
            <p className="text-left text-sm leading-relaxed text-foreground">
              Create by describing what you want to generate or upload your own photo to edit.
            </p>
            <p className="mt-3 text-left text-sm font-medium">Where do you want to start?</p>
          </div>
        ) : (
          <LayerTree />
        )}

        {chatMessages.length > 0 && (
          <div className="flex flex-col gap-2 px-4 py-3">
            {chatMessages.map((message) => (
              <div
                key={message.id}
                className={cn(
                  "max-w-[85%] rounded-xl px-3 py-2 text-sm",
                  message.role === "user"
                    ? "self-end bg-primary text-primary-foreground"
                    : "self-start bg-muted text-foreground"
                )}
              >
                {message.content}
              </div>
            ))}
          </div>
        )}

        {errorMessage && <p className="px-4 py-2 text-xs text-destructive">{errorMessage}</p>}
      </div>

      <ChatBox />
    </aside>
  );
}
