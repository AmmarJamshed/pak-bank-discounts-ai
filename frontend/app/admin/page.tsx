"use client";

import { useEffect, useState } from "react";

import {
  fetchAdminAnalytics,
  fetchAdminInsights,
  fetchAdminTrends
} from "../../lib/api";

type Analytics = {
  total_discounts: number;
  average_discount: number;
  top_categories: { category: string; count: number }[];
  top_cities: { city: string; count: number }[];
  top_banks: { bank: string; count: number }[];
  expiring_soon: number;
};

export default function AdminPage() {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [trends, setTrends] = useState<{ series: { week: string; count: number }[]; forecast_next_week: number } | null>(null);
  const [insights, setInsights] = useState<{ banks: any[] } | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const [analyticsData, trendsData, insightsData] = await Promise.all([
        fetchAdminAnalytics(),
        fetchAdminTrends(),
        fetchAdminInsights()
      ]);
      setAnalytics(analyticsData);
      setTrends(trendsData);
      setInsights(insightsData);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load analytics");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  if (loading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-semibold">Admin Analytics</h1>
          <p className="mt-2 text-sm text-muted">Loading analytics…</p>
        </div>
        <div className="grid gap-4 md:grid-cols-4">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="h-20 animate-pulse rounded-lg border bg-white/20" />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-2xl font-semibold">Admin Analytics</h1>
          <p className="mt-2 rounded-lg border border-amber-500/50 bg-amber-500/10 p-4 text-sm text-amber-700 dark:text-amber-400">
            {error}
          </p>
          <button
            type="button"
            onClick={load}
            className="mt-4 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-white hover:brightness-110"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-semibold">Admin Analytics</h1>
        <p className="text-sm text-muted">
          Monitor discount trends, affiliate readiness, and bank-wise insights.
        </p>
      </div>

      {analytics && (
        <div className="grid gap-4 md:grid-cols-4">
          <div className="rounded-lg border bg-white p-4">
            <p className="text-xs text-muted">Total Discounts</p>
            <p className="text-xl font-semibold">{analytics.total_discounts}</p>
          </div>
          <div className="rounded-lg border bg-white p-4">
            <p className="text-xs text-muted">Average Discount</p>
            <p className="text-xl font-semibold">{analytics.average_discount}%</p>
          </div>
          <div className="rounded-lg border bg-white p-4">
            <p className="text-xs text-muted">Expiring Soon</p>
            <p className="text-xl font-semibold">{analytics.expiring_soon}</p>
          </div>
          <div className="rounded-lg border bg-white p-4">
            <p className="text-xs text-muted">Forecast Next Week</p>
            <p className="text-xl font-semibold">
              {trends?.forecast_next_week ?? 0}
            </p>
          </div>
        </div>
      )}

      {analytics && (
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-lg border bg-white p-4">
            <h3 className="text-sm font-semibold">Top Categories</h3>
            <ul className="mt-2 text-sm text-muted">
              {analytics.top_categories.map((item) => (
                <li key={item.category}>
                  {item.category}: {item.count}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-lg border bg-white p-4">
            <h3 className="text-sm font-semibold">Top Cities</h3>
            <ul className="mt-2 text-sm text-muted">
              {analytics.top_cities.map((item) => (
                <li key={item.city}>
                  {item.city}: {item.count}
                </li>
              ))}
            </ul>
          </div>
          <div className="rounded-lg border bg-white p-4">
            <h3 className="text-sm font-semibold">Top Banks</h3>
            <ul className="mt-2 text-sm text-muted">
              {analytics.top_banks.map((item) => (
                <li key={item.bank}>
                  {item.bank}: {item.count}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {trends && (
        <div className="rounded-lg border bg-white p-4">
          <h3 className="text-sm font-semibold">Discount Trend</h3>
          <div className="mt-2 grid gap-2 text-sm text-muted">
            {(trends.series ?? []).map((point) => (
              <div key={point.week} className="flex items-center justify-between">
                <span>{point.week}</span>
                <span>{point.count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {insights && (
        <div className="rounded-lg border bg-white p-4">
          <h3 className="text-sm font-semibold">Bank-wise Insights</h3>
          <div className="mt-2 grid gap-2 text-sm text-muted">
            {(insights.banks ?? []).map((bank) => (
              <div
                key={bank.bank}
                className="flex flex-wrap items-center justify-between gap-2"
              >
                <span>{bank.bank}</span>
                <span>{bank.discount_count} deals</span>
                <span>{bank.total_discount_value} total discount</span>
                <span>{bank.category_coverage} categories</span>
                <span>
                  {bank.affiliate_ready ? "Affiliate Ready" : "Growing"}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
