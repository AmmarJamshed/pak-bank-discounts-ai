"use client";

import { useEffect, useState } from "react";
import { fetchMaintenanceStatus } from "../lib/api";

export default function MaintenanceBanner() {
  const [status, setStatus] = useState<{ maintenance: boolean; message: string | null } | null>(null);

  useEffect(() => {
    const check = async () => {
      const s = await fetchMaintenanceStatus();
      setStatus(s);
    };
    check();
    const id = setInterval(check, 60_000);
    return () => clearInterval(id);
  }, []);

  if (!status?.maintenance || !status.message) return null;

  return (
    <div className="sticky top-0 z-[60] border-b border-amber-400/40 bg-amber-500/30 px-4 py-2.5 text-center text-sm font-semibold text-amber-950 backdrop-blur">
      {status.message}
    </div>
  );
}
