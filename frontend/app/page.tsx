"use client";

import { useEffect, useState } from "react";

import DealCard from "../components/DealCard";
import Filters from "../components/Filters";
import SearchBar from "../components/SearchBar";
import { fetchBanks, fetchDiscounts } from "../lib/api";

type Discount = {
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

export default function HomePage() {
  const [discounts, setDiscounts] = useState<Discount[]>([]);
  const [city, setCity] = useState("");
  const [category, setCategory] = useState("");
  const [cardType, setCardType] = useState("");
  const [cardTier, setCardTier] = useState("");
  const [bank, setBank] = useState("");
  const [banks, setBanks] = useState<string[]>([]);
  const [query, setQuery] = useState("");

  const loadDiscounts = async () => {
    const data = await fetchDiscounts({
      city,
      category,
      card_type: cardType,
      card_tier: cardTier,
      bank,
      intent: query
    });
    setDiscounts(data.results || []);
  };

  useEffect(() => {
    loadDiscounts();
  }, [city, category, cardType, cardTier, bank]);

  useEffect(() => {
    const loadBanks = async () => {
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
          {!discounts.length && (
            <div className="rounded-xl border border-dashed border-border/60 bg-white/5 p-6 text-sm text-muted backdrop-blur">
              No discounts found yet. Trigger a scrape from the backend or adjust
              filters.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
