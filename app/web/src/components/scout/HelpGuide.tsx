import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Paper,
  Stack,
  Typography,
} from "@mui/material";
import { copy } from "../../copy";
import { stripe } from "../../theme/palette";

type FaqId =
  | "why"
  | "day"
  | "logins"
  | "session"
  | "platforms"
  | "new"
  | "trouble";

const COOKIES_PANEL: FaqId = "session";

function P({ children }: { children: ReactNode }) {
  return (
    <Typography variant="body2" sx={{ color: stripe.text, lineHeight: 1.55 }}>
      {children}
    </Typography>
  );
}

function Subhead({ children }: { children: ReactNode }) {
  return (
    <Typography
      variant="body2"
      sx={{ fontWeight: 600, color: stripe.navy, pt: 0.75 }}
    >
      {children}
    </Typography>
  );
}

function Step({ n, children }: { n: number; children: ReactNode }) {
  return (
    <Typography variant="body2" sx={{ color: stripe.text, lineHeight: 1.55 }}>
      {n}. {children}
    </Typography>
  );
}

function FaqItem({
  id,
  question,
  expanded,
  onChange,
  children,
}: {
  id: FaqId;
  question: string;
  expanded: boolean;
  onChange: (id: FaqId | false) => void;
  children: ReactNode;
}) {
  return (
    <Accordion
      id={id === COOKIES_PANEL ? "help-cookies" : undefined}
      disableGutters
      elevation={0}
      expanded={expanded}
      onChange={(_, open) => onChange(open ? id : false)}
      sx={{
        scrollMarginTop: 72,
        "&:not(:last-of-type)": { mb: 1 },
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        aria-controls={`${id}-content`}
        id={`${id}-header`}
        sx={{
          px: 1.5,
          minHeight: 48,
          "& .MuiAccordionSummary-content": { my: 1.25 },
        }}
      >
        <Typography variant="subtitle1" sx={{ fontWeight: 600, color: stripe.navy }}>
          {question}
        </Typography>
      </AccordionSummary>
      <AccordionDetails sx={{ px: 1.5, pt: 0, pb: 1.75 }}>
        <Stack spacing={1}>{children}</Stack>
      </AccordionDetails>
    </Accordion>
  );
}

export default function HelpGuide({
  focusCookies = false,
  onOpenSettings,
}: {
  focusCookies?: boolean;
  onOpenSettings: () => void;
}) {
  const [expanded, setExpanded] = useState<FaqId | false>(
    focusCookies ? COOKIES_PANEL : "why",
  );

  useEffect(() => {
    if (!focusCookies) return;
    setExpanded(COOKIES_PANEL);
    const t = window.setTimeout(() => {
      const el = document.getElementById("help-cookies");
      if (el && typeof el.scrollIntoView === "function") {
        el.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    }, 50);
    return () => window.clearTimeout(t);
  }, [focusCookies]);

  return (
    <Paper
      elevation={0}
      sx={{
        p: 2.5,
        border: `1px solid ${stripe.border}`,
        borderRadius: 1,
        maxWidth: 840,
      }}
    >
      <Typography variant="body2" sx={{ color: stripe.textMuted, mb: 2, lineHeight: 1.5 }}>
        {copy.help_lead}
      </Typography>

      <FaqItem
        id="why"
        question={copy.help_faq_why_q}
        expanded={expanded === "why"}
        onChange={setExpanded}
      >
        <P>{copy.help_faq_why_a}</P>
      </FaqItem>

      <FaqItem
        id="day"
        question={copy.help_faq_day_q}
        expanded={expanded === "day"}
        onChange={setExpanded}
      >
        <P>{copy.help_faq_day_a1}</P>
        <P>{copy.help_faq_day_a2}</P>
      </FaqItem>

      <FaqItem
        id="logins"
        question={copy.help_faq_logins_q}
        expanded={expanded === "logins"}
        onChange={setExpanded}
      >
        <P>{copy.help_faq_logins_a1}</P>
        <P>{copy.help_faq_logins_a2}</P>
      </FaqItem>

      <FaqItem
        id="session"
        question={copy.help_faq_session_q}
        expanded={expanded === "session"}
        onChange={setExpanded}
      >
        <P>{copy.help_faq_session_what}</P>
        <P>{copy.help_faq_session_where}</P>
        <Subhead>{copy.help_faq_session_how_title}</Subhead>
        <Step n={1}>{copy.help_faq_session_how_1}</Step>
        <Step n={2}>{copy.help_faq_session_how_2}</Step>
        <Step n={3}>{copy.help_faq_session_how_3}</Step>
        <Subhead>{copy.help_faq_session_when_title}</Subhead>
        <Step n={1}>{copy.help_faq_session_when_1}</Step>
        <Step n={2}>{copy.help_faq_session_when_2}</Step>
        <Step n={3}>{copy.help_faq_session_when_3}</Step>
        <Box sx={{ pt: 0.5 }}>
          <Button size="small" variant="outlined" onClick={onOpenSettings}>
            {copy.help_open_settings}
          </Button>
        </Box>
      </FaqItem>

      <FaqItem
        id="platforms"
        question={copy.help_faq_platforms_q}
        expanded={expanded === "platforms"}
        onChange={setExpanded}
      >
        <P>{copy.help_faq_platforms_a1}</P>
        <P>{copy.help_faq_platforms_a2}</P>
      </FaqItem>

      <FaqItem
        id="new"
        question={copy.help_faq_new_q}
        expanded={expanded === "new"}
        onChange={setExpanded}
      >
        <P>{copy.help_faq_new_intro}</P>
        <Step n={1}>{copy.help_faq_new_1}</Step>
        <Step n={2}>{copy.help_faq_new_2}</Step>
        <Step n={3}>{copy.help_faq_new_3}</Step>
        <Step n={4}>{copy.help_faq_new_4}</Step>
        <Step n={5}>{copy.help_faq_new_5}</Step>
        <P>{copy.help_faq_new_order}</P>
        <P>{copy.help_faq_new_forbid}</P>
      </FaqItem>

      <FaqItem
        id="trouble"
        question={copy.help_faq_trouble_q}
        expanded={expanded === "trouble"}
        onChange={setExpanded}
      >
        <Subhead>{copy.help_faq_trouble_start_h}</Subhead>
        <P>{copy.help_faq_trouble_start}</P>
        <Subhead>{copy.help_faq_trouble_session_h}</Subhead>
        <P>{copy.help_faq_trouble_session}</P>
        <Subhead>{copy.help_faq_trouble_empty_h}</Subhead>
        <P>{copy.help_faq_trouble_empty}</P>
        <Subhead>{copy.help_faq_trouble_ai_h}</Subhead>
        <P>{copy.help_faq_trouble_ai}</P>
      </FaqItem>
    </Paper>
  );
}
