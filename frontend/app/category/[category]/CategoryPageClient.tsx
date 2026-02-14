"use client";

import { useEffect, useState } from "react";

import DealCard from "../../../components/DealCard";
import { getCachedDealsFiltered } from "../../../lib/cache";
import { type Discount, fetchDiscounts } from "../../../lib/api";

export default function CategoryPageClient({
  category,
}: {
  category: string;
}) {
  const [discounts, setDiscounts] = useState<Discount[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const cached = getCachedDealsFiltered({ category });
    if (cached?.length) {
      setDiscounts(cached as Discount[]);
      setLoading(false);
    } else {
      setLoading(true);
    }
    const load = async () => {
      const data = await fetchDiscounts({ category });
      const results = (data.results || []) as Discount[];
      setDiscounts(results);
      setLoading(false);
    };
    load();
  }, [category]);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border/60 bg-white/5 p-6 shadow-[0_0_30px_rgba(34,211,238,0.08)] backdrop-blur">
        <p className="text-sm font-semibold uppercase tracking-wide text-accent">
          Category spotlight
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-ink md:text-3xl">
          {category} discounts
        </h1>
        <p className="mt-2 text-sm text-muted">
          Explore offers in {category} across Pakistan, powered by live scraping
          and verified card deals.
        </p>
      </div>
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {loading && (
          <div className="col-span-full rounded-xl border border-dashed border-border/60 bg-white/5 p-6 text-sm text-muted backdrop-blur">
            Loading deals…
          </div>
        )}
        {!loading && discounts.map((deal) => (
          <DealCard key={deal.discount_id} {...deal} />
        ))}
        {!loading && !discounts.length && (
          <div className="rounded-xl border border-dashed border-border/60 bg-white/5 p-6 text-sm text-muted backdrop-blur">
            No discounts found for this category yet.
          </div>
        )}
      </div>
    </div>
  );
}
