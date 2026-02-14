"use client";

import { useCallback, useEffect, useState } from "react";

import DealCard from "../components/DealCard";
import Filters from "../components/Filters";
import SearchBar from "../components/SearchBar";
import { getCachedDeals, setCachedDeals } from "../lib/cache";
import { type Discount, fetchBanks, fetchDiscounts } from "../lib/api";

const hasActiveFilters = (c: {
  city: string;
  category: string;
  cardType: string;
  cardTier: string;
  bank: string;
  query: string;
}) => !!(c.city || c.category || c.cardType || c.cardTier || c.bank || c.query);

export default function HomePage() {
  const [discounts, setDiscounts] = useState<Discount[]>([]);
  const [city, setCity] = useState("");
  const [category, setCategory] = useState("");
  const [cardType, setCardType] = useState("");
  const [cardTier, setCardTier] = useState("");
  const [bank, setBank] = useState("");
  const [banks, setBanks] = useState<string[]>([]);
  const [query, setQuery] = useState("");

  const [loading, setLoading] = useState(true);
  const [loadError, setLoadError] = useState(false);
  const [backendError, setBackendError] = useState<string | null>(null);

  const loadDiscounts = useCallback(async () => {
    const cached = getCachedDeals();
    const noFilters = !hasActiveFilters({ city, category, cardType, cardTier, bank, query });

    if (noFilters && cached?.discounts?.length) {
      setDiscounts(cached.discounts as Discount[]);
      if (cached.banks?.length) setBanks(cached.banks);
      setLoading(false);
    } else {
      setLoading(true);
    }
    setLoadError(false);
    setBackendError(null);

    const data = await fetchDiscounts({
      city,
      category,
      card_type: cardType,
      card_tier: cardTier,
      bank,
      intent: query,
    });
    const results = (data.results || []) as Discount[];
    if (!data.error) {
      setDiscounts(results);
      if (results.length > 0 && noFilters) {
        setCachedDeals(results, banks.length ? banks : (cached?.banks ?? []));
      }
    }
    setLoading(false);
    if (data.error) setBackendError(data.error);
    if (results.length === 0 && noFilters && !data.error) setLoadError(true);
  }, [city, category, cardType, cardTier, bank, query, banks.length]);

  useEffect(() => {
    const cached = getCachedDeals();
    if (cached?.discounts?.length && !hasActiveFilters({ city, category, cardType, cardTier, bank, query })) {
      setDiscounts(cached.discounts as Discount[]);
      if (cached.banks?.length) setBanks(cached.banks);
    }
  }, []);

  useEffect(() => {
    loadDiscounts();
  }, [city, category, cardType, cardTier, bank]);

  useEffect(() => {
    const loadBanks = async () => {
      const cached = getCachedDeals();
      if (cached?.banks?.length) setBanks(cached.banks);
      const data = await fetchBanks();
      const names = (data.results || [])
        .map((item: { name: string }) => item.name)
        .filter(Boolean);
      setBanks(names);
    };
    loadBanks();
  }, []);

  return (
    <div className="space-y-8">
      <section className="rounded-3xl border border-border/60 bg-white/5 px-6 py-8 shadow-[0_0_40px_rgba(16,185,129,0.08)] backdrop-blur md:px-10">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div className="max-w-2xl">
            <p className="text-sm font-semibold uppercase tracking-wide text-accent">
              Discount radar
            </p>
            <h1 className="mt-2 text-3xl font-semibold text-ink md:text-4xl">
              Find the best card discounts around you
            </h1>
            <p className="mt-3 text-muted">
              Search by city, category, or card to see live deals across Pakistan —
              refreshed by AI and SERP-powered scraping.
            </p>
          </div>
          <div className="rounded-2xl border border-accent/30 bg-white/10 px-4 py-3 text-sm text-muted shadow-[0_0_20px_rgba(34,211,238,0.25)]">
            <span className="font-semibold text-ink">{discounts.length}</span> deals
            available right now
          </div>
        </div>

        <div className="mt-6 flex flex-col gap-4 lg:flex-row lg:items-center">
          <SearchBar value={query} onChange={setQuery} onSubmit={loadDiscounts} />
          <Filters
            city={city}
            category={category}
            cardType={cardType}
            cardTier={cardTier}
            bank={bank}
            banks={banks}
            onChange={(field, value) => {
              if (field === "city") setCity(value);
              if (field === "category") setCategory(value);
              if (field === "cardType") setCardType(value);
              if (field === "cardTier") setCardTier(value);
              if (field === "bank") setBank(value);
            }}
          />
        </div>
      </section>

      <section className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold text-ink">Top Discounts</h2>
            <p className="text-sm text-muted">
              Pick a deal, see the card, and plan your next visit.
            </p>
          </div>
          <a href="/ai-assistant" className="text-sm font-semibold text-accent">
            Ask the AI assistant →
          </a>
        </div>
        <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
          {discounts.map((deal) => (
            <DealCard key={deal.discount_id} {...deal} />
          ))}
          {loading && (
            <>
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="h-64 animate-pulse rounded-2xl border border-border/60 bg-white/5"
                />
              ))}
              <div className="col-span-full rounded-xl border border-dashed border-border/60 bg-white/5 p-4 text-center text-sm text-muted backdrop-blur">
                Loading deals… (first load may take 30–60s)
              </div>
            </>
          )}
          {!loading && !discounts.length && (
            <div className="rounded-xl border border-dashed border-border/60 bg-white/5 p-6 text-sm text-muted backdrop-blur">
              {(loadError || backendError) ? (
                <div className="space-y-3">
                  <p>
                    {backendError ||
                      "No deals loaded. The backend may be starting or the scraper hasn't run yet."}
                  </p>
                  <p className="text-xs">
                    If this persists, the backend may be cold-starting (30–60s). Trigger the scraper:{" "}
                    <code className="rounded bg-surface/50 px-1">
                      curl -X POST {(process.env.NEXT_PUBLIC_API_BASE_URL || "YOUR_BACKEND_URL").replace(/\/$/, "")}/admin/trigger-scrape
                    </code>
                    . Check{" "}
                    <a
                      href={`${(process.env.NEXT_PUBLIC_API_BASE_URL || "https://pak-bank-backend-637y.onrender.com").replace(/\/$/, "")}/health`}
                      target="_blank"
                      rel="noreferrer"
                      className="text-accent underline"
                    >
                      backend health
                    </a>
                    .
                  </p>
                  <button
                    type="button"
                    onClick={loadDiscounts}
                    className="rounded-xl bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:brightness-110"
                  >
                    Retry loading deals
                  </button>
                </div>
              ) : (
                <p>
                  No discounts found yet. Trigger a scrape from the backend or
                  adjust filters.
                </p>
              )}
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
