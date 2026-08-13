import { Button, type ButtonProps } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { stripe } from "../../../theme/palette";

export type CardTextButtonEmphasis = "default" | "primary";

export interface CardTextButtonProps extends ButtonProps {
  emphasis?: CardTextButtonEmphasis;
}

/** Vendored from personal CardTextButton. */
export default function CardTextButton({
  emphasis = "default",
  sx,
  ...props
}: CardTextButtonProps) {
  const theme = useTheme();
  const { cardLink } = theme.density.button;
  const isPrimary = emphasis === "primary";

  return (
    <Button
      variant="text"
      {...props}
      sx={{
        alignSelf: "flex-start",
        justifyContent: "flex-start",
        width: "auto",
        minWidth: 0,
        minHeight: "unset",
        height: "auto",
        lineHeight: cardLink.lineHeight,
        fontSize: `${cardLink.fontSize}px`,
        padding: cardLink.padding,
        color: isPrimary ? stripe.blurple : stripe.textMuted,
        textTransform: "none",
        "&:hover": {
          color: isPrimary ? stripe.blurpleHover : stripe.blurple,
          bgcolor: "transparent",
        },
        "&.Mui-disabled": {
          color: isPrimary ? stripe.blurple : stripe.textMuted,
          opacity: 0.5,
        },
        ...sx,
      }}
    />
  );
}
