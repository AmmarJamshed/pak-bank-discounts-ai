type SearchBarProps = {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
};

export default function SearchBar({ value, onChange, onSubmit }: SearchBarProps) {
  return (
    <div className="flex flex-1 gap-2">
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder="Search discounts, banks, or areas..."
        className="w-full rounded-2xl border border-border/60 bg-white/5 px-4 py-3 text-sm text-ink shadow-sm backdrop-blur placeholder:text-muted/80 focus:border-primary focus:outline-none"
      />
      <button
        onClick={onSubmit}
        className="rounded-2xl bg-primary px-5 py-3 text-sm font-semibold text-white shadow-[0_0_20px_rgba(124,58,237,0.45)] transition hover:brightness-110"
      >
        Search
      </button>
    </div>
  );
}
