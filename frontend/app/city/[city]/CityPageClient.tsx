"use client";

import { useEffect, useState } from "react";

import DealCard from "../../../components/DealCard";
import { type Discount, fetchDiscounts } from "../../../lib/api";

export default function CityPageClient({ city }: { city: string }) {
  const [discounts, setDiscounts] = useState<Discount[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      const data = await fetchDiscounts({ city });
      setDiscounts(data.results || []);
      setLoading(false);
    };
    load();
  }, [city]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">City Deals: {city}</h1>
        <p className="text-sm text-muted">
          Explore the latest discounts available in {city}.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {loading && (
          <div className="col-span-full rounded-xl border border-dashed border-border/60 bg-white/5 p-6 text-sm text-muted backdrop-blur">
            Loading deals…
          </div>
        )}
        {!loading && discounts.map((deal) => (
          <DealCard key={deal.discount_id} {...deal} />
        ))}
        {!loading && !discounts.length && (
          <div className="rounded-lg border border-border/60 bg-white/5 p-6 text-sm text-muted backdrop-blur">
            No discounts found for this city yet.
          </div>
        )}
      </div>
    </div>
  );
}
