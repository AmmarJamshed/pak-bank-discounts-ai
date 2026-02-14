const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type Discount = {
  discount_id: number;
  merchant: string;
  city: string;
  category: string;
  merchant_image_url?: string | null;
  discount_percent: number;
  bank: string;
  card_name: string;
  card_type: string;
  valid_to?: string | null;
  conditions?: string | null;
};

export type FetchResult<T> =
  | { results: T[]; error?: never }
  | { results: T[]; error: string };

async function fetchWithTimeout(url: string, timeoutMs = 90000) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(url, {
      cache: "no-store",
      signal: controller.signal
    });
    if (!response.ok) throw new Error(`Request failed: ${response.status}`);
    return await response.json();
  } finally {
    clearTimeout(timeout);
  }
}

async function safeFetchJson<T = unknown>(
  url: string
): Promise<FetchResult<T>> {
  try {
    const data = await fetchWithTimeout(url);
    return { results: (data.results ?? []) as T[] };
  } catch (error) {
    const msg =
      error instanceof Error
        ? error.name === "AbortError"
          ? "Request timed out — backend may be starting (try again in 30s)"
          : error.message
        : "Connection failed";
    console.error("API request failed:", url, error);
    return { results: [], error: msg };
  }
}

export async function fetchDiscounts(params: Record<string, string>) {
  const url = new URL(`${API_BASE}/discounts`);
  if (!params.limit) {
    url.searchParams.set("limit", "5000");
  }
  Object.entries(params).forEach(([key, value]) => {
    if (value) {
      url.searchParams.set(key, value);
    }
  });
  return safeFetchJson<Discount>(url.toString());
}

export async function fetchBanks() {
  return safeFetchJson<{ name: string }>(`${API_BASE}/banks`);
}

export async function fetchAdminAnalytics() {
  try {
    return await fetchWithTimeout(`${API_BASE}/admin/analytics`);
  } catch {
    return null;
  }
}

export async function fetchAdminInsights() {
  try {
    return await fetchWithTimeout(`${API_BASE}/admin/insights`);
  } catch {
    return null;
  }
}

export async function fetchAdminTrends() {
  try {
    return await fetchWithTimeout(`${API_BASE}/admin/trends`);
  } catch {
    return null;
  }
}

export type MaintenanceStatus = { maintenance: boolean; message: string | null };

export async function fetchMaintenanceStatus(): Promise<MaintenanceStatus> {
  try {
    const data = await fetchWithTimeout(`${API_BASE}/admin/maintenance`, 5000);
    return {
      maintenance: Boolean(data?.maintenance),
      message: data?.message ?? null,
    };
  } catch {
    return { maintenance: false, message: null };
  }
}
