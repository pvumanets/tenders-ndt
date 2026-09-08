import type { DragEvent } from "react";
import type { TeachBucket } from "../types";

/** Native HTML5 DnD — same pattern as ndt-personal `lib/dispatch/board-dnd.ts`. */
export const DRAG_MIME = "application/x-scout-tender-id";

export function createBoardDropHandlers(
  bucket: TeachBucket,
  onDropLot?: (tenderId: string, bucket: TeachBucket) => void,
) {
  return {
    onDragOver: (event: DragEvent) => {
      event.preventDefault();
      event.dataTransfer.dropEffect = "move";
    },
    onDrop: (event: DragEvent) => {
      event.preventDefault();
      const tenderId = event.dataTransfer.getData(DRAG_MIME);
      if (tenderId && onDropLot) {
        onDropLot(tenderId, bucket);
      }
    },
  };
}

export function createDragStartHandler(tenderId: string) {
  return (event: DragEvent) => {
    event.dataTransfer.setData(DRAG_MIME, tenderId);
    event.dataTransfer.effectAllowed = "move";
  };
}
