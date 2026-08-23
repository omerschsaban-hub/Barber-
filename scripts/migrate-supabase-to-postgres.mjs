import pg from "pg";

const { Client } = pg;
const sourceUrl = process.env.SUPABASE_URL;
const sourceKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
const targetUrl = process.env.DATABASE_URL;
if (!sourceUrl || !sourceKey || !targetUrl) {
  throw new Error("SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY and DATABASE_URL are required");
}

const tables = [
  "projects","machines","gauges","features","inspections","measurements","prediction_runs","calibration_observations","experiments","provenance_events",
  "opportunity_graphs","graph_nodes","graph_edges","agent_runs","loop_runs","ml_models","prediction_events","next_experiments","reverification_recommendations",
  "source_records","measurement_mappings","geometry_assets","audit_events","production_drift_observations","service_wear_observations","geometry_features",
  "model_validation_runs","engineering_runs","import_batches","risk_results","system_identification_models","agent_policies","engineering_decisions",
  "inspection_exports","inspection_imports","data_sources","data_observations","collection_runs","data_quality_checks","improvement_candidates","flywheel_checkpoints",
  "analytics_events","analytics_sessions","profiles",
];

const client = new Client({ connectionString: targetUrl, ssl: { rejectUnauthorized: false } });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

function quoteIdent(value) {
  return `"${value.replaceAll('"', '""')}"`;
}

async function fetchRows(table, offset) {
  const url = new URL(`${sourceUrl.replace(/\/$/, "")}/rest/v1/${table}`);
  url.searchParams.set("select", "*");
  url.searchParams.set("limit", "1000");
  url.searchParams.set("offset", String(offset));
  const response = await fetch(url, {
    headers: { apikey: sourceKey, Authorization: `Bearer ${sourceKey}` },
  });
  if (!response.ok) throw new Error(`Supabase ${table} ${response.status}: ${await response.text()}`);
  return response.json();
}

await client.connect();
try {
  await client.query("select pg_advisory_lock(hashtext('fabrient:supabase-migration'))");
  await client.query("begin");

  for (const table of tables) {
    let offset = 0;
    let total = 0;
    for (;;) {
      const rows = await fetchRows(table, offset);
      if (!rows.length) break;
      const columns = Object.keys(rows[0]);
      const values = [];
      const tuples = rows.map((row) => {
        const placeholders = columns.map((_, i) => `$${values.length + i + 1}`);
        for (const column of columns) values.push(row[column]);
        return `(${placeholders.join(",")})`;
      });
      const sql = `insert into ${quoteIdent(table)} (${columns.map(quoteIdent).join(",")}) values ${tuples.join(",")} on conflict do nothing`;
      await client.query(sql, values);
      total += rows.length;
      offset += rows.length;
      if (rows.length < 1000) break;
      await sleep(50);
    }
    console.log(`${table}: ${total}`);
  }

  await client.query("commit");
} catch (error) {
  await client.query("rollback").catch(() => {});
  throw error;
} finally {
  await client.query("select pg_advisory_unlock(hashtext('fabrient:supabase-migration'))").catch(() => {});
  await client.end();
}
