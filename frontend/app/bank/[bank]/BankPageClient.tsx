"use client";

import { useEffect, useState } from "react";

import DealCard from "../../../components/DealCard";
import { type Discount, fetchDiscounts } from "../../../lib/api";

export default function BankPageClient({ bank }: { bank: string }) {
  const [discounts, setDiscounts] = useState<Discount[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      const data = await fetchDiscounts({ bank });
      setDiscounts(data.results || []);
      setLoading(false);
    };
    load();
  }, [bank]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">Bank Deals: {bank}</h1>
        <p className="text-sm text-muted">
          Browse exclusive offers from {bank}.
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
            No discounts found for this bank yet.
          </div>
        )}
      </div>
    </div>
  );
}
