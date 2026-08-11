import { Product } from '../api/client';
import { Status } from '../components/Status';

export function Catalog({
  products,
  loading,
  error,
  onSelect,
}: {
  products: Product[];
  loading: boolean;
  error?: string;
  onSelect: (id: string) => void;
}) {
  if (loading) return <div className="state">Loading graph catalog…</div>;
  if (error) return <div className="state failure">Catalog unavailable: {error}</div>;
  if (!products.length) return <div className="state">No products match the current evidence query.</div>;

  return (
    <table>
      <thead>
        <tr>
          <th>Status</th><th>Product</th><th>Category</th><th>Sources</th>
          <th>Contradictions</th><th>Plausibility</th><th>Citations</th><th>Evidence</th>
        </tr>
      </thead>
      <tbody>
        {products.map((product) => (
          <tr key={product.id}>
            <td><Status kind={product.implausible ? 'invalid' : product.unverified ? 'review' : 'confirmed'} label={product.implausible ? 'invalid' : product.unverified ? 'review' : 'confirmed'} /></td>
            <td><strong>{product.resolved_name}</strong><code>{product.mpn || '—'}</code></td>
            <td>{product.category}</td>
            <td><code>{product.sources}</code></td>
            <td><code>{product.contradictions || '—'}</code></td>
            <td>{product.implausible ? 'needs review' : 'plausible'}</td>
            <td>{product.unverified ? 'unverified' : 'verified'}</td>
            <td><button className="open-evidence" onClick={() => onSelect(product.id)}>Open evidence →</button></td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
