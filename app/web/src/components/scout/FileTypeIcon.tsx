import { Box, Tooltip, Typography } from "@mui/material";
import { stripe } from "../../theme/palette";

const SIZE = 18;

type FileKind = "pdf" | "doc" | "xls" | "img" | "zip" | "other";

const KIND_STYLE: Record<FileKind, { label: string; bg: string; fg: string }> = {
  pdf: { label: "PDF", bg: stripe.critical, fg: "#fff" },
  doc: { label: "DOC", bg: stripe.info, fg: "#fff" },
  xls: { label: "XLS", bg: stripe.success, fg: "#fff" },
  img: { label: "IMG", bg: stripe.blurple, fg: "#fff" },
  zip: { label: "ZIP", bg: stripe.warning, fg: stripe.navy },
  other: { label: "FILE", bg: stripe.borderHover, fg: stripe.navy },
};

function extOf(name: string): string {
  const i = name.lastIndexOf(".");
  return i >= 0 ? name.slice(i + 1).toLowerCase() : "";
}

function kindOf(ext: string): FileKind {
  if (ext === "pdf") return "pdf";
  if (ext === "doc" || ext === "docx" || ext === "rtf" || ext === "odt") return "doc";
  if (ext === "xls" || ext === "xlsx" || ext === "csv" || ext === "ods") return "xls";
  if (ext === "png" || ext === "jpg" || ext === "jpeg" || ext === "webp" || ext === "gif") {
    return "img";
  }
  if (ext === "zip" || ext === "rar" || ext === "7z") return "zip";
  return "other";
}

/** 16–18px colored badge by file extension — not a large MUI glyph. */
export default function FileTypeIcon({
  fileName,
  size = SIZE,
}: {
  fileName: string;
  size?: number;
}) {
  const ext = extOf(fileName);
  const kind = kindOf(ext);
  const style = KIND_STYLE[kind];
  const title = ext ? ext.toUpperCase() : style.label;

  return (
    <Tooltip title={title} describeChild>
      <Box
        component="span"
        role="img"
        aria-label={title}
        sx={{
          display: "inline-flex",
          width: size,
          height: size,
          flexShrink: 0,
          borderRadius: "3px",
          bgcolor: style.bg,
          alignItems: "center",
          justifyContent: "center",
          lineHeight: 0,
        }}
      >
        <Typography
          component="span"
          sx={{
            fontSize: style.label.length > 3 ? 6 : size <= 16 ? 6 : 7,
            fontWeight: 700,
            color: style.fg,
            letterSpacing: 0,
            lineHeight: 1,
            whiteSpace: "nowrap",
          }}
        >
          {style.label}
        </Typography>
      </Box>
    </Tooltip>
  );
}
