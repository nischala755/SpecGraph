from __future__ import annotations
import os
import json
from dataclasses import asdict
from neo4j import GraphDatabase
from app.domain.models import Product, SourceDocument, ExtractedAttribute, Job, JobDocument

class GraphRepository:
    def __init__(self, uri: str | None = None, username: str | None = None, password: str | None = None):
        self.driver = GraphDatabase.driver(uri or os.getenv("NEO4J_URI", "bolt://localhost:7687"), auth=(username or os.getenv("NEO4J_USERNAME", "neo4j"), password or os.getenv("NEO4J_PASSWORD", "change-me")))
        self.database = os.getenv("NEO4J_DATABASE") or None
    def _session(self): return self.driver.session(database=self.database)
    def close(self): self.driver.close()
    def check(self) -> bool:
        try:
            self.driver.verify_connectivity(); return True
        except Exception: return False
    def initialize(self):
        statements=["CREATE CONSTRAINT product_id IF NOT EXISTS FOR (n:Product) REQUIRE n.id IS UNIQUE", "CREATE CONSTRAINT source_id IF NOT EXISTS FOR (n:SourceDocument) REQUIRE n.id IS UNIQUE", "CREATE INDEX attribute_field IF NOT EXISTS FOR (n:AttributeValue) ON (n.field_name)", "CREATE INDEX product_category IF NOT EXISTS FOR (n:Product) ON (n.category)"]
        with self._session() as s:
            for q in statements: s.run(q)
    def clear(self):
        with self._session() as s: s.run("MATCH (n) DETACH DELETE n")
    def save_job(self, job: Job):
        with self._session() as s:
            s.run("MERGE (j:IngestionJob {id:$id}) SET j.state=$state,j.error=$error,j.documents=$documents", id=job.id, state=job.state, error=job.error, documents=json.dumps([asdict(d) for d in job.documents]))
    def load_job(self, job_id: str) -> Job | None:
        with self._session() as s: row=s.run("MATCH (j:IngestionJob {id:$id}) RETURN j", id=job_id).single()
        if not row: return None
        node=row["j"]; return Job(id=node["id"], state=node["state"], error=node.get("error"), documents=[JobDocument(**document) for document in json.loads(node["documents"])])
    def save_product(self, product: Product):
        with self._session() as s:
            s.run("MERGE (p:Product {id:$id}) SET p.resolved_name=$name,p.category=$category,p.mpn=$mpn,p.cluster_confidence=$confidence", id=product.id,name=product.resolved_name,category=product.category,mpn=product.mpn,confidence=product.cluster_confidence)
            for d in product.documents:
                s.run("MERGE (d:SourceDocument {id:$id}) SET d.raw_text=$raw,d.filename=$filename,d.source_type=$type,d.reliability_tier=$tier WITH d MATCH (p:Product {id:$pid}) MERGE (p)-[:RESOLVED_FROM {similarity_score:$score}]->(d)",id=d.id,raw=d.raw_text,filename=d.filename,type=d.source_type,tier=d.reliability_tier,pid=product.id,score=product.cluster_confidence)
            for a in product.attributes:
                s.run("MERGE (a:AttributeValue {id:$id}) SET a.field_name=$field,a.value=$value,a.unit=$unit,a.citation_span=$span,a.citation_verified=$verified,a.verification_score=$score,a.source_context=$context,a.extraction_confidence=$confidence,a.plausibility_status=$status,a.plausibility_reason=$reason WITH a MATCH (p:Product {id:$pid}),(d:SourceDocument {id:$source}) MERGE (p)-[:HAS_ATTRIBUTE]->(a) MERGE (a)-[:EXTRACTED_FROM]->(d)",id=a.id,field=a.field_name,value=a.value,unit=a.unit,span=a.citation_span,verified=a.citation_verified,score=a.verification_score,context=a.source_context,confidence=a.extraction_confidence,status=a.plausibility_status,reason=a.plausibility_reason,pid=product.id,source=a.source_id)
            for c in product.contradictions:
                s.run("MATCH (a:AttributeValue {id:$left}),(b:AttributeValue {id:$right}) MERGE (a)-[r:CONTRADICTS]->(b) SET r.resolution_status=$status,r.reason=$reason",left=c["left"],right=c["right"],status=c["resolution_status"],reason=c["reason"])
    def products(self, search: str | None = None) -> list[dict]:
        query="MATCH (p:Product) OPTIONAL MATCH (p)-[:RESOLVED_FROM]->(d) OPTIONAL MATCH (p)-[:HAS_ATTRIBUTE]->(a) WITH p, count(DISTINCT d) AS sources, collect(DISTINCT a) AS attrs OPTIONAL MATCH (p)-[:HAS_ATTRIBUTE]->(x)-[:CONTRADICTS]-() WITH p,sources,attrs,count(DISTINCT x) AS contradictions RETURN p{.*},sources,attrs,contradictions, any(a IN attrs WHERE a.plausibility_status='implausible') AS implausible, any(a IN attrs WHERE a.citation_verified=false) AS unverified ORDER BY p.resolved_name"
        with self._session() as s:
            rows=[dict(r) for r in s.run(query)]
        if search:
            norm=''.join(ch for ch in search.lower() if ch.isalnum())
            def matches(row):
                values=[row['p'].get('resolved_name',''),row['p'].get('mpn',''),row['p'].get('category','')]
                for attr in row['attrs']: values += [attr.get('field_name',''), str(attr.get('value',''))]
                return norm in ''.join(ch for ch in ''.join(values).lower() if ch.isalnum())
            rows=[r for r in rows if matches(r)]
        return [{"id":r["p"]["id"],"resolved_name":r["p"]["resolved_name"],"category":r["p"]["category"],"mpn":r["p"].get("mpn"),"cluster_confidence":r["p"]["cluster_confidence"],"sources":r["sources"],"contradictions":r["contradictions"],"implausible":r["implausible"],"unverified":r["unverified"]} for r in rows]
    def product(self, pid: str) -> dict | None:
        query="MATCH (p:Product {id:$id}) OPTIONAL MATCH (p)-[:RESOLVED_FROM]->(d) OPTIONAL MATCH (p)-[:HAS_ATTRIBUTE]->(a)-[:EXTRACTED_FROM]->(source) OPTIONAL MATCH (a)-[c:CONTRADICTS]->(other) RETURN p{.*} AS product, collect(DISTINCT d{.*}) AS documents, collect(DISTINCT {attribute:a{.*},source:source{.*}}) AS evidence, collect(DISTINCT {left:a.id,right:other.id,resolution_status:c.resolution_status,reason:c.reason}) AS contradictions"
        with self._session() as s: r=s.run(query,id=pid).single()
        return dict(r) if r else None
    def graph(self, pid: str) -> dict:
        data=self.product(pid)
        if not data: return {"nodes":[],"links":[]}
        nodes=[{"id":pid,"type":"Product","label":data["product"]["resolved_name"]}]; links=[]
        for d in data["documents"]:
            nodes.append({"id":d["id"],"type":"SourceDocument","label":d["filename"]}); links.append({"source":pid,"target":d["id"],"type":"RESOLVED_FROM"})
        for e in data["evidence"]:
            a=e["attribute"]; nodes.append({"id":a["id"],"type":"AttributeValue","label":f"{a['field_name']}: {a['value']} {a.get('unit') or ''}"}); links += [{"source":pid,"target":a["id"],"type":"HAS_ATTRIBUTE"},{"source":a["id"],"target":e["source"]["id"],"type":"EXTRACTED_FROM"}]
        return {"nodes":nodes,"links":links}
