import type { Components, Theme } from "@mui/material/styles";
import { density } from "./density";
import { semantic, stripe } from "./palette";
import { stripeShadows } from "./shadows";
import { stripeScrollbarGlobalCss } from "./scrollbars";

const { font, weight, control, chip, input, button, tab, radius, selection } = density;

export function buildComponents(): Components<Omit<Theme, "components">> {
  return {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          WebkitFontSmoothing: "antialiased",
          MozOsxFontSmoothing: "grayscale",
          backgroundColor: stripe.surfaceSubtle,
        },
        ...stripeScrollbarGlobalCss,
      },
    },
    MuiButtonBase: {
      defaultProps: {
        disableRipple: true,
      },
    },
    MuiButton: {
      defaultProps: {
        disableElevation: true,
      },
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: weight.regular,
          fontSize: `${font.md}px`,
          borderRadius: button.radius,
          minHeight: control.md,
          padding: button.padding,
          boxShadow: "none",
          "&:hover": { boxShadow: "none" },
        },
        contained: {
          backgroundColor: stripe.blurple,
          color: "#fff",
          "&:hover": { backgroundColor: stripe.blurpleHover },
        },
        outlined: {
          backgroundColor: stripe.surface,
          borderColor: stripe.border,
          color: stripe.text,
          "&:hover": {
            backgroundColor: stripe.surfaceSubtle,
            borderColor: stripe.borderHover,
          },
        },
        text: {
          color: stripe.blurple,
          "&:hover": { backgroundColor: stripe.blurpleSoft },
        },
        sizeSmall: {
          minHeight: control.sm,
          fontSize: `${font.sm}px`,
          padding: "0 10px",
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          color: stripe.textMuted,
          borderRadius: button.radius,
          boxSizing: "border-box",
          "&:hover": { backgroundColor: stripe.surfaceSubtle, color: stripe.text },
        },
        sizeSmall: {
          width: control.sm,
          height: control.sm,
          minWidth: control.sm,
          minHeight: control.sm,
          padding: 0,
        },
        sizeMedium: {
          width: control.md,
          height: control.md,
          minWidth: control.md,
          minHeight: control.md,
          padding: 0,
        },
      },
    },
    MuiOutlinedInput: {
      styleOverrides: {
        root: {
          borderRadius: button.radius,
          backgroundColor: stripe.surface,
          fontSize: `${font.md}px`,
          minHeight: control.md,
          "& .MuiOutlinedInput-notchedOutline": {
            borderColor: stripe.border,
          },
          "&:hover .MuiOutlinedInput-notchedOutline": {
            borderColor: stripe.borderHover,
          },
          "&.Mui-focused .MuiOutlinedInput-notchedOutline": {
            borderColor: stripe.blurple,
            borderWidth: 1,
          },
          "&.Mui-focused": {
            boxShadow: stripeShadows.focusRing,
          },
        },
        input: {
          padding: input.padding,
          lineHeight: `${font.md + 5}px`,
          height: "auto",
          boxSizing: "border-box",
        },
      },
    },
    MuiInputLabel: {
      styleOverrides: {
        root: {
          fontSize: `${font.sm}px`,
          color: stripe.textMuted,
          "&.Mui-focused": { color: stripe.blurple },
          "&.MuiInputLabel-outlined:not(.MuiInputLabel-shrink)": {
            transform: "translate(10px, 8px) scale(1)",
          },
          "&.MuiInputLabel-outlined.MuiInputLabel-shrink": {
            left: 5,
            transform: "translate(10px, -9px) scale(0.75)",
          },
        },
      },
    },
    MuiPaper: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          backgroundImage: "none",
          border: `1px solid ${stripe.border}`,
          borderRadius: radius.md,
        },
      },
    },
    MuiCard: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          borderRadius: radius.md,
          border: `1px solid ${stripe.border}`,
          boxShadow: stripeShadows.none,
          backgroundColor: stripe.surface,
          "&:hover": {
            boxShadow: stripeShadows.sm,
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          borderRadius: 9999,
          fontSize: `${chip.fontSize}px`,
          fontWeight: weight.regular,
          height: chip.height,
        },
        filled: {
          backgroundColor: stripe.surfaceSubtle,
          color: stripe.text,
        },
        outlined: {
          borderColor: stripe.border,
          color: stripe.textMuted,
          backgroundColor: stripe.surface,
        },
        colorPrimary: {
          backgroundColor: stripe.blurpleSoft,
          color: stripe.blurple,
          border: "none",
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: `1px solid ${stripe.border}`,
          fontSize: `${font.md}px`,
          color: stripe.text,
          padding: "8px 12px",
        },
        head: {
          fontWeight: weight.medium,
          color: stripe.textMuted,
          backgroundColor: stripe.surfaceSubtle,
          fontSize: `${font.sm}px`,
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: { minHeight: tab.minHeight },
        indicator: {
          backgroundColor: stripe.blurple,
          height: 2,
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: weight.regular,
          fontSize: `${font.md}px`,
          minHeight: tab.minHeight,
          color: stripe.textMuted,
          "&.Mui-selected": { color: stripe.text },
        },
      },
    },
    MuiToggleButtonGroup: {
      styleOverrides: {
        root: {
          backgroundColor: stripe.surface,
          border: `1px solid ${stripe.border}`,
          borderRadius: radius.md,
          padding: 2,
          gap: 2,
        },
        grouped: {
          border: "none",
          borderRadius: `${button.radius}px !important`,
          margin: 0,
        },
      },
    },
    MuiToggleButton: {
      styleOverrides: {
        root: {
          textTransform: "none",
          fontWeight: weight.regular,
          fontSize: `${font.sm}px`,
          color: stripe.textMuted,
          border: "none",
          borderRadius: button.radius,
          minHeight: control.sm,
          padding: "4px 12px",
          "&.Mui-selected": {
            backgroundColor: stripe.blurpleSoft,
            color: stripe.blurple,
            "&:hover": { backgroundColor: stripe.blurpleSoft },
          },
          "&:hover": { backgroundColor: stripe.surfaceSubtle },
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: ({ ownerState }) => ({
          borderRadius: radius.md,
          border: `1px solid ${stripe.border}`,
          boxShadow: "none",
          fontSize: `${font.md}px`,
          ...(ownerState.severity === "info" && {
            backgroundColor: stripe.infoSoft,
            color: stripe.text,
            borderLeft: `3px solid ${stripe.info}`,
          }),
          ...(ownerState.severity === "warning" && {
            backgroundColor: semantic.warning30dSoft,
            color: stripe.text,
            borderLeft: `3px solid ${stripe.warning}`,
          }),
          ...(ownerState.severity === "error" && {
            backgroundColor: semantic.critical50dSoft,
            color: stripe.text,
            borderLeft: `3px solid ${stripe.critical}`,
          }),
          ...(ownerState.severity === "success" && {
            backgroundColor: semantic.activeSoft,
            color: stripe.text,
            borderLeft: `3px solid ${stripe.success}`,
          }),
        }),
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          borderRadius: radius.lg,
          border: `1px solid ${stripe.border}`,
          boxShadow: stripeShadows.dialog,
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          fontSize: `${font.xl}px`,
          fontWeight: weight.medium,
          color: stripe.navy,
          padding: "16px 20px 8px",
        },
      },
    },
    MuiDialogContent: {
      styleOverrides: {
        root: {
          padding: "8px 24px 16px",
        },
      },
    },
    MuiDialogActions: {
      styleOverrides: {
        root: {
          padding: "12px 24px 20px",
          gap: 8,
        },
      },
    },
    MuiAppBar: {
      defaultProps: {
        elevation: 0,
      },
      styleOverrides: {
        root: {
          backgroundColor: stripe.surface,
          color: stripe.text,
          borderBottom: `1px solid ${stripe.border}`,
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: stripe.surface,
          borderRight: `1px solid ${stripe.border}`,
          boxShadow: "none",
        },
      },
    },
    MuiDivider: {
      styleOverrides: {
        root: {
          borderColor: stripe.border,
        },
      },
    },
    MuiBreadcrumbs: {
      styleOverrides: {
        root: {
          fontSize: `${font.sm}px`,
          color: stripe.textMuted,
        },
      },
    },
    MuiLink: {
      styleOverrides: {
        root: {
          color: stripe.blurple,
          textDecoration: "none",
          "&:hover": { textDecoration: "underline" },
        },
      },
    },
    MuiMenu: {
      styleOverrides: {
        paper: {
          borderRadius: radius.md,
          boxShadow: stripeShadows.md,
          border: `1px solid ${stripe.border}`,
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          fontSize: `${font.md}px`,
          borderRadius: 4,
          margin: "2px 6px",
          "&:hover": { backgroundColor: stripe.surfaceSubtle },
        },
      },
    },
    MuiAccordion: {
      styleOverrides: {
        root: {
          border: `1px solid ${stripe.border}`,
          borderRadius: `${radius.md}px !important`,
          boxShadow: "none",
          "&:before": { display: "none" },
          "&.Mui-expanded": { margin: 0 },
        },
      },
    },
    MuiSnackbar: {
      styleOverrides: {
        root: {
          "& .MuiPaper-root": {
            borderRadius: radius.md,
            boxShadow: stripeShadows.md,
          },
        },
      },
    },
    MuiAvatar: {
      styleOverrides: {
        root: {
          borderRadius: radius.sm,
          fontSize: `${font.xs}px`,
          fontWeight: weight.medium,
        },
      },
    },
    MuiCheckbox: {
      defaultProps: {
        size: "small",
      },
      styleOverrides: {
        root: {
          color: stripe.borderHover,
          padding: selection.padding,
          "&.Mui-checked": { color: stripe.blurple },
          "& .MuiSvgIcon-root": {
            fontSize: selection.icon,
          },
        },
      },
    },
    MuiRadio: {
      defaultProps: {
        size: "small",
      },
      styleOverrides: {
        root: {
          color: stripe.borderHover,
          padding: selection.padding,
          "&.Mui-checked": { color: stripe.blurple },
          "& .MuiSvgIcon-root": {
            fontSize: selection.icon,
          },
        },
      },
    },
    MuiSwitch: {
      defaultProps: {
        size: "small",
      },
      styleOverrides: {
        switchBase: {
          "&.Mui-checked": {
            color: stripe.blurple,
            "& + .MuiSwitch-track": {
              backgroundColor: stripe.blurple,
              opacity: 0.5,
            },
          },
        },
        track: {
          opacity: 1,
          backgroundColor: stripe.border,
        },
      },
    },
    MuiFormControlLabel: {
      styleOverrides: {
        root: {
          marginLeft: 0,
          marginRight: 0,
          gap: 4,
        },
        label: {
          fontSize: `${font.md}px`,
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          borderRadius: button.radius,
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: stripe.navy,
          fontSize: `${font.xs}px`,
          borderRadius: radius.sm,
          padding: "4px 8px",
        },
      },
    },
    MuiCircularProgress: {
      styleOverrides: {
        root: {
          color: stripe.blurple,
        },
      },
    },
    MuiSkeleton: {
      defaultProps: {
        animation: "wave",
      },
      styleOverrides: {
        root: {
          backgroundColor: stripe.border,
          transform: "none",
        },
        rounded: {
          borderRadius: radius.sm,
        },
        text: {
          borderRadius: radius.sm,
        },
      },
    },
  };
}
