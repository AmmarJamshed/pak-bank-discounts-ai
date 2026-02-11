type DealCardProps = {
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

const sanitizeText = (value: string | null | undefined, strict = false) => {
  if (!value) return "";
  const cleaned = value
    .replace(/\uFFFD/g, "")
    .replace(/[\u0000-\u001F\u007F-\u009F]/g, "")
    .replace(/[^\x20-\x7E]+/g, "")
    .replace(/\s+/g, " ")
    .trim();

  if (!cleaned) return "";

  const letters = cleaned.replace(/[^A-Za-z]/g, "").length;
  const digits = cleaned.replace(/[^0-9]/g, "").length;
  const total = cleaned.replace(/\s/g, "").length;
  const readableRatio = total ? (letters + digits) / total : 0;

  const minLetters = strict ? 4 : 2;
  const minRatio = strict ? 0.75 : 0.65;

  if (total < 3 || letters < minLetters || readableRatio < minRatio) {
    return "";
  }

  return cleaned;
};

const truncateText = (value: string, max: number) => {
  if (value.length <= max) return value;
  return `${value.slice(0, max - 1)}…`;
};

const initialsFrom = (value: string) =>
  value
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((chunk) => chunk[0]?.toUpperCase())
    .join("");

export default function DealCard({
  merchant,
  city,
  category,
  merchant_image_url,
  discount_percent,
  bank,
  card_name,
  card_type,
  valid_to,
  conditions
}: DealCardProps) {
  const safeMerchant = sanitizeText(merchant, true) || "Unknown merchant";
  const safeCategory = sanitizeText(category, true) || "Uncategorized";
  const safeCity = sanitizeText(city, true) || "Unknown city";
  const safeBank = sanitizeText(bank, true) || "Bank";
  const safeCard = sanitizeText(card_name, true) || "Card";
  const safeType = sanitizeText(card_type, true) || "Credit/Debit";
  const safeConditions = truncateText(sanitizeText(conditions), 120);

  return (
    <div className="group relative overflow-hidden rounded-2xl border border-border/60 bg-white/5 p-5 shadow-[0_0_30px_rgba(34,211,238,0.08)] backdrop-blur transition hover:-translate-y-0.5 hover:border-accent/60 hover:shadow-[0_0_40px_rgba(124,58,237,0.2)]">
      <div className="absolute right-0 top-4 rounded-l-full bg-primary px-4 py-2 text-sm font-semibold text-white shadow-[0_0_16px_rgba(124,58,237,0.5)]">
        {discount_percent}% OFF
      </div>
      <div className="inline-flex rounded-full bg-primary/15 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-primary">
        {safeCategory}
      </div>
      <div className="mt-4 flex items-center gap-3">
        <div className="relative h-14 w-14 overflow-hidden rounded-2xl border border-white/10 bg-white/10">
          {merchant_image_url ? (
            <img
              src={merchant_image_url}
              alt={safeMerchant}
              className="h-full w-full object-cover"
              loading="lazy"
              referrerPolicy="no-referrer"
            />
          ) : (
            <div className="flex h-full w-full items-center justify-center text-sm font-semibold text-ink/80">
              {initialsFrom(safeMerchant) || "PB"}
            </div>
          )}
        </div>
        <div>
          <h3 className="text-lg font-semibold text-ink">{safeMerchant}</h3>
          <p className="text-xs text-muted">Verified partner</p>
        </div>
      </div>
      <div className="mt-3 flex flex-wrap gap-2 text-xs font-medium text-muted">
        <span className="rounded-full bg-surface/70 px-3 py-1 text-ink/80">
          {safeCity}
        </span>
        <span className="rounded-full bg-surface/70 px-3 py-1 text-ink/80">
          {safeType}
        </span>
      </div>
      <div className="mt-5 flex items-center justify-between">
        <div className="rounded-lg bg-surface/70 px-3 py-2 text-xs font-semibold uppercase tracking-wide text-muted">
          Redeemable with
        </div>
        <div className="rounded-full bg-primary/15 px-3 py-2 text-xs font-semibold text-primary">
          {safeBank} · {safeCard}
        </div>
      </div>
      {valid_to && (
        <p className="mt-3 text-xs text-muted">Valid till {valid_to}</p>
      )}
      {safeConditions && (
        <p className="mt-2 text-xs text-muted">{safeConditions}</p>
      )}
    </div>
  );
}
