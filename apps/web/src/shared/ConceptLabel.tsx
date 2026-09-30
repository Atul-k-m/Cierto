// Persistent disclosure on every host replica (PRODUCT.md guardrail).
export function ConceptLabel({ brand, className }: { brand: string; className?: string }) {
  return (
    <p className={className} role="note">
      Concept demo · not affiliated with {brand}
    </p>
  )
}
