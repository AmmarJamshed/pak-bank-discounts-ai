const API_BASE =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

async function safeFetchJson(url: string) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  try {
    const response = await fetch(url, {
      cache: "no-store",
      signal: controller.signal
    });
    if (!response.ok) {
      throw new Error(`Request failed: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("API request failed:", url, error);
    return { results: [] };
  } finally {
    clearTimeout(timeout);
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
  return safeFetchJson(url.toString());
}

export async function fetchBanks() {
  return safeFetchJson(`${API_BASE}/banks`);
}

export async function fetchAdminAnalytics() {
  return safeFetchJson(`${API_BASE}/admin/analytics`);
}

export async function fetchAdminInsights() {
  return safeFetchJson(`${API_BASE}/admin/insights`);
}

export async function fetchAdminTrends() {
  return safeFetchJson(`${API_BASE}/admin/trends`);
}
