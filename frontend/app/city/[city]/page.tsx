import CityPageClient from "./CityPageClient";

export function generateStaticParams() {
  return [{ city: "karachi" }];
}

export default function CityPage({ params }: { params: { city: string } }) {
  return <CityPageClient city={params.city} />;
}
