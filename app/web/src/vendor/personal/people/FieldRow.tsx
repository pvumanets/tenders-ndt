import { Box, Typography } from "@mui/material";
import type { ReactNode } from "react";
import { personProfileTokens } from "../../../theme/person-profile";

export interface FieldRowProps {
  label: string;
  children: ReactNode;
  empty?: boolean;
}

/** Vendored from personal PersonFieldRow (ADR-018). */
export default function FieldRow({ label, children, empty }: FieldRowProps) {
  return (
    <Box sx={{ mb: 2, "&:last-child": { mb: 0 } }}>
      <Typography component="div" sx={{ ...personProfileTokens.fieldLabel, mb: 0.25 }}>
        {label}
      </Typography>
      <Box
        sx={
          empty
            ? undefined
            : {
                "& .MuiTypography-root": personProfileTokens.fieldValue,
              }
        }
      >
        {children}
      </Box>
    </Box>
  );
}
