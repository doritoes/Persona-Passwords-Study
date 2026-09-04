#!/usr/bin/env bun
/**
 * Re-run HIBP Pwned Passwords checks against a credentials CSV and produce
 * checked_<name>.csv (per-row pwned flag) + checked_<name>.report (summary,
 * broken down by persona "sector" from personas.json).
 *
 * Usage:
 *   bun run check_hibp_report.ts <credentials.csv> <personas.json> [--delay-ms=200]
 */

import { readFileSync, writeFileSync } from "fs";
import { createHash } from "crypto";
import { basename, dirname, extname, join } from "path";

interface Row {
  user_id: string;
  password: string;
}

interface Persona {
  personal_email?: string;
  work_lanid?: string;
  sector?: string;
}

function parseArgs() {
  const positional = process.argv.slice(2).filter(a => !a.startsWith("--"));
  const flags = Object.fromEntries(
    process.argv
      .slice(2)
      .filter(a => a.startsWith("--"))
      .map(a => {
        const [k, v] = a.replace(/^--/, "").split("=");
        return [k, v ?? "true"];
      })
  );
  const [credentialsPath, personasPath] = positional;
  if (!credentialsPath || !personasPath) {
    console.error("Usage: bun run check_hibp_report.ts <credentials.csv> <personas.json> [--delay-ms=200]");
    process.exit(1);
  }
  return { credentialsPath, personasPath, delayMs: Number(flags["delay-ms"] ?? 200) };
}

function parseCsv(text: string): Row[] {
  const lines = text.trim().split(/\r?\n/);
  const headers = lines[0].split(",").map(h => h.replace(/^"|"$/g, ""));
  return lines.slice(1).map(line => {
    const fields = line.match(/"(?:[^"\\]|\\.)*"|[^,]+/g) ?? [];
    const row: Record<string, string> = {};
    headers.forEach((h, i) => {
      row[h] = (fields[i] ?? "").replace(/^"|"$/g, "");
    });
    return row as unknown as Row;
  });
}

function csvEscape(v: string): string {
  return `"${v.replace(/"/g, '""')}"`;
}

function sleep(ms: number) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

const prefixCache = new Map<string, string>();

async function fetchRange(prefix: string): Promise<string> {
  const cached = prefixCache.get(prefix);
  if (cached) return cached;

  while (true) {
    const res = await fetch(`https://api.pwnedpasswords.com/range/${prefix}`);
    if (res.status === 200) {
      const text = await res.text();
      prefixCache.set(prefix, text);
      return text;
    }
    if (res.status === 429) {
      const wait = Number(res.headers.get("retry-after") ?? "2");
      console.log(`--- Rate limited. Sleeping ${wait}s... ---`);
      await sleep(wait * 1000);
      continue;
    }
    throw new Error(`HIBP request failed: ${res.status}`);
  }
}

const pwnedCountCache = new Map<string, number>();

async function getPwnedCount(password: string): Promise<number> {
  if (!password) return 0;
  const cached = pwnedCountCache.get(password);
  if (cached !== undefined) return cached;

  const sha1 = createHash("sha1").update(password, "utf-8").digest("hex").toUpperCase();
  const prefix = sha1.slice(0, 5);
  const suffix = sha1.slice(5);

  const body = await fetchRange(prefix);
  let count = 0;
  for (const line of body.split(/\r?\n/)) {
    const [h, c] = line.split(":");
    if (h === suffix) {
      count = Number(c);
      break;
    }
  }
  pwnedCountCache.set(password, count);
  return count;
}

async function main() {
  const { credentialsPath, personasPath, delayMs } = parseArgs();

  const rows = parseCsv(readFileSync(credentialsPath, "utf-8"));
  const personas: Persona[] = JSON.parse(readFileSync(personasPath, "utf-8"));

  const sectorByUser = new Map<string, string>();
  for (const p of personas) {
    if (p.personal_email && p.sector) sectorByUser.set(p.personal_email, p.sector);
    if (p.work_lanid && p.sector) sectorByUser.set(p.work_lanid, p.sector);
  }

  const dir = dirname(credentialsPath);
  const ext = extname(credentialsPath);
  const base = basename(credentialsPath, ext);
  const checkedCsvPath = join(dir, `checked_${base}${ext}`);
  const reportPath = join(dir, `checked_${base}.report`);

  const checkedLines = [`"user_id","password","pwned"`];
  const bySector = new Map<string, { total: number; pwned: number }>();
  const pwnedPasswords = new Set<string>();
  let pwnedCount = 0;
  let unmatched = 0;

  for (const [i, row] of rows.entries()) {
    const count = await getPwnedCount(row.password);
    const isPwned = count > 0;
    checkedLines.push(`${csvEscape(row.user_id)},${csvEscape(row.password)},${csvEscape(isPwned ? "True" : "False")}`);

    if (isPwned) {
      pwnedCount++;
      pwnedPasswords.add(row.password);
      console.log(`⚠️  PWNED: ${row.user_id}`);
    } else {
      console.log(`✅ SAFE: ${row.user_id}`);
    }

    const sector = sectorByUser.get(row.user_id);
    if (!sector) {
      unmatched++;
    } else {
      const entry = bySector.get(sector) ?? { total: 0, pwned: 0 };
      entry.total++;
      if (isPwned) entry.pwned++;
      bySector.set(sector, entry);
    }

    if (i < rows.length - 1) await sleep(delayMs);
  }

  writeFileSync(checkedCsvPath, checkedLines.join("\n") + "\n", "utf-8");

  const totalCount = rows.length;
  const overallPct = totalCount > 0 ? (pwnedCount / totalCount * 100).toFixed(2) : "0.00";
  const sectorRows = [...bySector.entries()].sort(
    (a, b) => b[1].pwned / b[1].total - a[1].pwned / a[1].total
  );

  const report: string[] = [];
  report.push("=".repeat(40));
  report.push("FINAL SECURITY REPORT");
  report.push("=".repeat(40));
  report.push(`Total Passwords Checked: ${totalCount}`);
  report.push(`Pwned Passwords Found:  ${pwnedCount}`);
  report.push(`Overall Compromise Rate: ${overallPct}%`);
  if (unmatched > 0) {
    report.push(`(warning: ${unmatched} rows had no matching persona for sector lookup)`);
  }
  report.push("");
  if (sectorRows.length > 0) {
    report.push("Sector Compromise Rate:");
    for (const [sector, { total, pwned }] of sectorRows) {
      const pct = (pwned / total * 100).toFixed(2);
      report.push(`  ${sector.padEnd(14)} ${pct.padStart(6)}%  (${pwned}/${total})`);
    }
    report.push("");
  }
  report.push("List of Compromised Passwords:");
  for (const p of [...pwnedPasswords].sort((a, b) => a.localeCompare(b))) {
    report.push(` - ${p}`);
  }
  report.push("");

  writeFileSync(reportPath, report.join("\n"), "utf-8");

  console.log("\n" + report.slice(0, 6).join("\n"));
  console.log(`\nResults saved to: ${checkedCsvPath}`);
  console.log(`Report saved to: ${reportPath}`);
}

main();
