const ALL_TIERS = ["Basic", "Classic", "Gold", "Platinum", "Signature", "Infinite"];

type FiltersProps = {
  city: string;
  category: string;
  cardType: string;
  cardTier: string;
  bank: string;
  card: string;
  banks: string[];
  cards: { card_name: string; bank: string }[];
  /** Tiers available for current bank+cardType (empty = show all) */
  availableTiers: string[];
  onChange: (
    field: "city" | "category" | "cardType" | "cardTier" | "bank" | "card",
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
  "Peshawar",
  "Quetta",
  "Hyderabad",
  "Sialkot",
  "Gujranwala",
  "Bahawalpur",
  "Sargodha",
  "Sukkur",
  "Larkana",
  "Mingora",
  "Muzaffarabad",
  "Mirpur",
  "Abbottabad",
  "Dera Ismail Khan"
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

const cardTypes = ["Credit", "Debit"];

export default function Filters({
  city,
  category,
  cardType,
  cardTier,
  bank,
  card,
  banks,
  cards,
  availableTiers,
  onChange
}: FiltersProps) {
  const cardTiersToShow = availableTiers.length > 0 ? availableTiers : ALL_TIERS;
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
      {bank && cards.length > 0 && (
        <select
          value={card}
          onChange={(event) => onChange("card", event.target.value)}
          className="rounded-2xl border border-border/60 bg-white/5 px-4 py-3 text-sm text-ink shadow-sm backdrop-blur placeholder:text-muted/80 focus:border-primary focus:outline-none"
        >
          <option value="">My Card (All)</option>
          {cards.map((c) => (
            <option key={c.card_name} value={c.card_name}>
              {c.card_name}
            </option>
          ))}
        </select>
      )}
      <select
        value={cardType}
        onChange={(event) => onChange("cardType", event.target.value)}
        className="rounded-2xl border border-border/60 bg-white/5 px-4 py-3 text-sm text-ink shadow-sm backdrop-blur placeholder:text-muted/80 focus:border-primary focus:outline-none"
      >
        <option value="">Card Type</option>
        {cardTypes.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
      <select
        value={cardTiersToShow.includes(cardTier) ? cardTier : ""}
        onChange={(event) => onChange("cardTier", event.target.value)}
        className="rounded-2xl border border-border/60 bg-white/5 px-4 py-3 text-sm text-ink shadow-sm backdrop-blur placeholder:text-muted/80 focus:border-primary focus:outline-none"
      >
        <option value="">Card Tier</option>
        {cardTiersToShow.map((item) => (
          <option key={item} value={item}>
            {item}
          </option>
        ))}
      </select>
    </div>
  );
}
