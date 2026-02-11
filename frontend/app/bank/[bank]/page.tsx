import BankPageClient from "./BankPageClient";

export function generateStaticParams() {
  return [{ bank: "hbl" }];
}

export default function BankPage({ params }: { params: { bank: string } }) {
  return <BankPageClient bank={params.bank} />;
}
