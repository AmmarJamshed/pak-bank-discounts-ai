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

export default function CityPage() {
  const params = useParams<{ city: string }>();
  const [discounts, setDiscounts] = useState<Discount[]>([]);

  useEffect(() => {
    const load = async () => {
      const data = await fetchDiscounts({ city: params.city });
      setDiscounts(data.results || []);
    };
    load();
  }, [params.city]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-ink">City Deals: {params.city}</h1>
        <p className="text-sm text-muted">
          Explore the latest discounts available in {params.city}.
        </p>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        {discounts.map((deal) => (
          <DealCard key={deal.discount_id} {...deal} />
        ))}
        {!discounts.length && (
          <div className="rounded-lg border border-border/60 bg-white/5 p-6 text-sm text-muted backdrop-blur">
            No discounts found for this city yet.
          </div>
        )}
      </div>
    </div>
  );
}
