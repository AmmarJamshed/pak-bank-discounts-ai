type FiltersProps = {
  city: string;
  category: string;
  cardType: string;
  cardTier: string;
  bank: string;
  banks: string[];
  onChange: (
    field: "city" | "category" | "cardType" | "cardTier" | "bank",
    value: string
  ) => void;
};

const cities = [
  "Karachi",
  "Lahore",
  "Islamabad",
  "Rawalpindi",
  "Faisalabad",
  "Multan",
  "Peshawar"
];

const categories = [
  "Food",
  "Retail",
  "Fashion",
  "Travel",
  "Medical",
  "Electronics",
  "Grocery",
  "Entertainment"
];

const cardTypes = ["Card", "Credit", "Debit"];
const cardTiers = ["Basic", "Classic", "Gold", "Platinum", "Signature", "Infinite"];

export default function Filters({
  city,
  category,
  cardType,
  cardTier,
  bank,
  banks,
  onChange
}: FiltersProps) {
  return (
    <div className="flex flex-wrap gap-3">
      <select
        value={city}
        onChange={(event) => onChange("city", event.target.value)}
        className="rounded-2xl border border-border/60 bg-white/5 px-4 py-3 text-sm text-ink shadow-sm backdrop-blur placeholder:text-muted/80 focus:border-primary focus:outline-none"
      >
        <option value="">All Cities</option>
        {cities.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
      <select
        value={category}
        onChange={(event) => onChange("category", event.target.value)}
        className="rounded-2xl border border-border/60 bg-white/5 px-4 py-3 text-sm text-ink shadow-sm backdrop-blur placeholder:text-muted/80 focus:border-primary focus:outline-none"
      >
        <option value="">All Categories</option>
        {categories.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
      <select
        value={bank}
        onChange={(event) => onChange("bank", event.target.value)}
        className="rounded-2xl border border-border/60 bg-white/5 px-4 py-3 text-sm text-ink shadow-sm backdrop-blur placeholder:text-muted/80 focus:border-primary focus:outline-none"
      >
        <option value="">All Banks</option>
        {banks.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
      <select
        value={cardType}
        onChange={(event) => onChange("cardType", event.target.value)}
        className="rounded-2xl border border-border/60 bg-white/5 px-4 py-3 text-sm text-ink shadow-sm backdrop-blur placeholder:text-muted/80 focus:border-primary focus:outline-none"
      >
        <option value="">Card Category</option>
        {cardTypes.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
      <select
        value={cardTier}
        onChange={(event) => onChange("cardTier", event.target.value)}
        className="rounded-2xl border border-border/60 bg-white/5 px-4 py-3 text-sm text-ink shadow-sm backdrop-blur placeholder:text-muted/80 focus:border-primary focus:outline-none"
      >
        <option value="">Card Tier</option>
        {cardTiers.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
    </div>
  );
}
