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

/** Get filtered deals from cache for instant load on city/category/bank pages. */
export function getCachedDealsFiltered(
  filter: { city?: string; category?: string; bank?: string }
): unknown[] | null {
  const cached = getCachedDeals();
  if (!cached?.discounts?.length) return null;
  const deals = cached.discounts as Array<{
    city?: string;
    category?: string;
    bank?: string;
  }>;
  let filtered = deals;
  if (filter.city) {
    const c = filter.city.toLowerCase();
    filtered = filtered.filter((d) => (d.city ?? "").toLowerCase() === c);
  }
  if (filter.category) {
    const cat = filter.category.toLowerCase();
    filtered = filtered.filter((d) => (d.category ?? "").toLowerCase() === cat);
  }
  if (filter.bank) {
    const b = filter.bank.toLowerCase();
    filtered = filtered.filter((d) => (d.bank ?? "").toLowerCase() === b);
  }
  return filtered.length ? filtered : null;
}
