import { Briefcase, Building2, ChevronDown, GraduationCap, Search, Sparkles, User } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { useApp } from "../context/AppContext";
import type { Profile } from "../types";

export const PROFILE_ICONS: Record<string, typeof User> = {
  "graduation-cap": GraduationCap, briefcase: Briefcase, search: Search, "building-2": Building2, sparkles: Sparkles,
};

export function ProfileIcon({ icon, size = 16 }: { icon: string; size?: number }) {
  const I = PROFILE_ICONS[icon] ?? User;
  return <I size={size} />;
}

export default function ProfileSwitcher() {
  const { profiles, activeProfile, switchProfile, notify } = useApp();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const h = (e: MouseEvent) => { if (!ref.current?.contains(e.target as Node)) setOpen(false); };
    document.addEventListener("mousedown", h);
    return () => document.removeEventListener("mousedown", h);
  }, []);

  const pick = async (p: Profile) => {
    setOpen(false);
    if (p.is_active) return;
    await switchProfile(p.key);
    notify(`Switched to ${p.name}. The same emails were re-ranked for this profile.`);
  };

  return (
    <div className="relative" ref={ref}>
      <button className="btn-outline !px-2.5 sm:!px-3" onClick={() => setOpen(!open)} aria-haspopup="menu" aria-expanded={open}>
        <span className="flex h-6 w-6 items-center justify-center rounded-full bg-brand-100 text-brand-700 dark:bg-brand-900/50 dark:text-brand-200">
          <ProfileIcon icon={activeProfile?.icon ?? "user"} size={13} />
        </span>
        <span className="hidden max-w-[120px] truncate sm:inline">{activeProfile?.name ?? "Profile"}</span>
        <ChevronDown size={14} />
      </button>
      {open && (
        <div role="menu" className="card absolute right-0 z-30 mt-2 w-72 animate-pop p-1.5 shadow-xl">
          <p className="px-3 py-2 text-xs font-semibold text-slate-500">Demo profile. Switching re-ranks the same emails.</p>
          {profiles.map((p) => (
            <button key={p.key} role="menuitemradio" aria-checked={p.is_active} onClick={() => pick(p)}
              className={`flex w-full items-start gap-3 rounded-xl px-3 py-2.5 text-left hover:bg-slate-50 dark:hover:bg-slate-800 ${p.is_active ? "bg-brand-50 dark:bg-brand-900/30" : ""}`}>
              <span className="mt-0.5 text-brand-600 dark:text-brand-300"><ProfileIcon icon={p.icon} /></span>
              <span><span className="block text-sm font-bold">{p.name}</span><span className="block text-xs text-slate-500">{p.description}</span></span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
