import CategoryPageClient from "./CategoryPageClient";

export function generateStaticParams() {
  return [{ category: "food" }];
}

export default function CategoryPage({
  params,
}: {
  params: { category: string };
}) {
  return <CategoryPageClient category={params.category} />;
}
