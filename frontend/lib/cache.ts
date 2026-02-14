/** Client-side cache for instant deal load (survives backend cold start). */

const CACHE_KEY = "pak-bank-deals-cache";
const CACHE_MAX_AGE_MS = 7 * 24 * 60 * 60 * 1000; // 7 days - use cached as fallback

export type CachedDeals = {
  discounts: unknown[];
  banks: string[];
  fetchedAt: number;
};

export function getCachedDeals(): CachedDeals | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return null;
    const data = JSON.parse(raw) as CachedDeals;
    if (!data.discounts || !Array.isArray(data.discounts)) return null;
    return data;
  } catch {
    return null;
  }
}

export function setCachedDeals(discounts: unknown[], banks: string[]): void {
  if (typeof window === "undefined") return;
  try {
    const data: CachedDeals = {
      discounts,
      banks: Array.isArray(banks) ? banks : [],
      fetchedAt: Date.now(),
    };
    localStorage.setItem(CACHE_KEY, JSON.stringify(data));
  } catch {
    // ignore quota / private mode
  }
}

export function isCacheStale(cached: CachedDeals): boolean {
  return Date.now() - cached.fetchedAt > CACHE_MAX_AGE_MS;
}
