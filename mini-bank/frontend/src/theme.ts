import { createTheme } from "@mui/material";

export const theme = createTheme({
  palette: {
    mode: "light",
    primary: { main: "#c8102e" },
    secondary: { main: "#2b3036" },
    background: { default: "#f6f7f9" },
  },
  typography: {
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  },
  shape: { borderRadius: 8 },
});
