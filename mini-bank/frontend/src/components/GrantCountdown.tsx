import { useEffect, useState } from "react";
import { Chip } from "@mui/material";

function formatRemaining(ms: number): string {
  if (ms <= 0) return "wygasł";
  const totalSec = Math.floor(ms / 1000);
  const min = Math.floor(totalSec / 60);
  const sec = totalSec % 60;
  return `${min}m ${sec.toString().padStart(2, "0")}s`;
}

export function GrantCountdown({ expiresAt }: { expiresAt: string }) {
  const target = new Date(expiresAt).getTime();
  const [remaining, setRemaining] = useState(target - Date.now());

  useEffect(() => {
    const handle = setInterval(() => setRemaining(target - Date.now()), 1000);
    return () => clearInterval(handle);
  }, [target]);

  const expired = remaining <= 0;
  return (
    <Chip
      label={expired ? "wygasł" : `do końca: ${formatRemaining(remaining)}`}
      color={expired ? "default" : remaining < 60_000 ? "warning" : "success"}
      size="small"
    />
  );
}
