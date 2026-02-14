import Link from "next/link";
import "../styles/globals.css";
import MaintenanceBanner from "../components/MaintenanceBanner";

export const metadata = {
  title: "Pak Bank Discounts Intelligence",
  description: "Pakistan's unified bank discount intelligence portal."
};

export default function RootLayout({
  children
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen">
        <MaintenanceBanner />
        <header className="sticky top-0 z-50 border-b border-border/60 bg-surface/70 backdrop-blur">
          <div className="mx-auto flex max-w-6xl items-center justify-between px-4 py-4">
            <Link href="/" className="flex items-center gap-2 text-lg font-semibold text-ink">
              <span className="grid h-8 w-8 place-items-center rounded-full bg-primary text-white shadow-[0_0_16px_rgba(124,58,237,0.6)]">
                PB
              </span>
              Pak Bank Discounts
            </Link>
            <nav className="hidden items-center gap-6 text-sm font-medium text-muted md:flex">
              <Link href="/ai-assistant" className="transition hover:text-accent" prefetch>
                AI Assistant
              </Link>
              <Link href="/city/karachi" className="transition hover:text-accent" prefetch>
                Cities
              </Link>
              <Link href="/category/food" className="transition hover:text-accent" prefetch>
                Categories
              </Link>
              <Link href="/admin" className="transition hover:text-accent" prefetch>
                Admin
              </Link>
            </nav>
          </div>
        </header>
        <main className="mx-auto max-w-6xl px-4 py-8">{children}</main>
      </body>
    </html>
  );
}
