import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { EvidenceRail } from '../components/EvidenceRail';

export function ProductDetail({ id, onClose, onGraph }: { id: string; onClose: () => void; onGraph: () => void }) {
  const [data, setData] = useState<any>();
  const [error, setError] = useState<string>();

  useEffect(() => {
    api.product(id).then(setData).catch((requestError) => setError(requestError.message));
  }, [id]);

  if (error) return <main className="state failure">Product evidence unavailable: {error}</main>;
  if (!data) return <main className="state">Loading evidence chain…</main>;

  const groups = Object.entries(
    data.evidence.reduce((all: Record<string, any[]>, item: any) => {
      (all[item.attribute.field_name] ??= []).push(item);
      return all;
    }, {}),
  );
  const disagreements = data.contradictions.filter((item: any) => item?.left && item?.right);

  return <main className="detail">
    <button className="text-button" onClick={onClose}>← Catalog</button>
    <header>
      <div><p className="eyebrow">Resolved product</p><h1>{data.product.resolved_name}</h1><code>{data.product.mpn || 'No MPN extracted'}</code></div>
      <dl><div><dt>sources</dt><dd>{data.documents.length}</dd></div><div><dt>cluster confidence</dt><dd>{Math.round(data.product.cluster_confidence * 100)}%</dd></div></dl>
      <button onClick={onGraph}>View provenance graph</button>
    </header>
    {groups.map(([field, evidence]: any) => <section className="field" key={field}><h2>{field.replace('_', ' ')}</h2><EvidenceRail evidence={evidence} /></section>)}
    <section className="contradictions">
      <h2>Source disagreements</h2>
      {disagreements.length ? <ul>{disagreements.map((item: any, index: number) => <li key={index}><code>{String(item.left).slice(0, 8)} ↔ {String(item.right).slice(0, 8)}</code><span>{item.resolution_status}: {item.reason}</span></li>)}</ul> : <p>No contradictory controlled values detected across sources.</p>}
    </section>
  </main>;
}
