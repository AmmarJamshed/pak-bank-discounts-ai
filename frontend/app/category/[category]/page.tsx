"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";

import DealCard from "../../../components/DealCard";
import { fetchDiscounts } from "../../../lib/api";

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

export default function CategoryPage() {
  const params = useParams<{ category: string }>();
  const [discounts, setDiscounts] = useState<Discount[]>([]);

  useEffect(() => {
    const load = async () => {
      const data = await fetchDiscounts({ category: params.category });
      setDiscounts(data.results || []);
    };
    load();
  }, [params.category]);

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-border/60 bg-white/5 p-6 shadow-[0_0_30px_rgba(34,211,238,0.08)] backdrop-blur">
        <p className="text-sm font-semibold uppercase tracking-wide text-accent">
          Category spotlight
        </p>
        <h1 className="mt-2 text-2xl font-semibold text-ink md:text-3xl">
          {params.category} discounts
        </h1>
        <p className="mt-2 text-sm text-muted">
          Explore offers in {params.category} across Pakistan, powered by live
          scraping and verified card deals.
        </p>
      </div>
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
        {discounts.map((deal) => (
          <DealCard key={deal.discount_id} {...deal} />
        ))}
        {!discounts.length && (
          <div className="rounded-xl border border-dashed border-border/60 bg-white/5 p-6 text-sm text-muted backdrop-blur">
            No discounts found for this category yet.
          </div>
        )}
      </div>
    </div>
  );
}
