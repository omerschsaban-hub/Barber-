export type EngineeringProfile = {
  nominal_mm: number;
  material: string;
  machine: string;
  process_temperature_c: number;
  ambient_temperature_c: number;
  shrinkage_pct: number;
  shrinkage_uncertainty_pct: number;
  tolerance_mm: number;
};

export const ENGINEERING_PROFILE_KEY = 'fabrient-engineering-profile-v2';

export const ENGINEERING_PROFILE_DEFAULTS: EngineeringProfile = {
  nominal_mm: 40,
  material: 'PETG',
  machine: 'Not set',
  process_temperature_c: 245,
  ambient_temperature_c: 23,
  shrinkage_pct: 0.5,
  shrinkage_uncertainty_pct: 0.15,
  tolerance_mm: 0.4,
};

export function loadEngineeringProfile(): EngineeringProfile | null {
  if (typeof window === 'undefined') return null;
  try {
    const raw = window.localStorage.getItem(ENGINEERING_PROFILE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) return null;
    return { ...ENGINEERING_PROFILE_DEFAULTS, ...parsed } as EngineeringProfile;
  } catch {
    return null;
  }
}

export function saveEngineeringProfile(profile: EngineeringProfile): boolean {
  if (typeof window === 'undefined') return false;
  try {
    window.localStorage.setItem(ENGINEERING_PROFILE_KEY, JSON.stringify(profile));
    return true;
  } catch {
    return false;
  }
}
