import type { MouseEventHandler } from "react";
import TuneIcon from "@mui/icons-material/Tune";
import { Badge, Button } from "@mui/material";

export interface FilterTriggerButtonProps {
  label?: string;
  onClick?: MouseEventHandler<HTMLButtonElement>;
  badgeContent?: number;
  size?: "small" | "medium" | "large";
}

/** Vendored from ndt-personal FilterTriggerButton. */
export default function FilterTriggerButton({
  label = "Фильтры",
  onClick,
  badgeContent = 0,
  size = "small",
}: FilterTriggerButtonProps) {
  return (
    <Badge
      badgeContent={badgeContent}
      color="primary"
      invisible={badgeContent <= 0}
      max={9}
      sx={{ "& .MuiBadge-badge": { fontSize: 10, height: 16, minWidth: 16 } }}
    >
      <Button
        variant="outlined"
        size={size}
        startIcon={<TuneIcon sx={{ fontSize: 16 }} />}
        onClick={onClick}
        sx={{ flexShrink: 0 }}
      >
        {label}
      </Button>
    </Badge>
  );
}
