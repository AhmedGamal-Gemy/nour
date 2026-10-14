// graph-first: strict mode for the nour knowledge graph.
//
// Once per session, the first read of an indexed project doc (or the first
// repo-wide grep) is denied with instructions to run one `graphify query`
// first. Everything after that proceeds. This can never strand an agent:
// the very next call is allowed.
//
// Why this exists: the graphify reminder plugin only nudges. Instructions in
// AGENTS.md say "query first", but nothing enforces it. Policies cannot do it
// either — they are stateless, and the grep permission check matches the
// *regex*, not the file, so there is no way to say "consult the graph before
// searching these files". A stateful hook is the only mechanism that can.
//
// Design notes:
// - Reads of AGENTS.md are EXEMPT: it is the session bootstrap file, and the
//   harness may read it before any agent exists to run a query.
// - Reads under graphify-out/ are EXEMPT: the report is a sanctioned fallback
//   that AGENTS.md itself prescribes for broad architecture questions.
// - edit/write/patch are NEVER touched: enforcement must not block modifying
//   the docs, only reading around them without orientation.
// - Only fires when graphify-out/graph.json exists in this location, so
//   worktrees and other projects are unaffected.
// - Mirrors upstream graphify's Claude strict mode (_READ_DENY): deny once,
//   then allow. See graphify cli.py in the uv tool install.
import { existsSync } from "fs";
import { join } from "path";

const hasGraph = (directory) =>
  existsSync(join(directory, "graphify-out", "graph.json"));

// Indexed corpus, per .graphifyignore: PLAN.md, AGENTS.md, research/00-FINDINGS.md.
// AGENTS.md is exempt (bootstrap). graphify-out/ is exempt (sanctioned fallback).
const INDEXED_READ = [/PLAN\.md$/i, /research\/00-FINDINGS\.md$/i, /research\/0\d-.*\.md$/i];
const EXEMPT_READ = [/AGENTS\.md$/i, /graphify-out\//i];

const DENY_MESSAGE =
  "graph-first: this project has a knowledge graph that covers this file. " +
  "Run one `graphify query \"<your question>\"` FIRST to orient yourself, then " +
  "re-issue this call — it will be allowed. This block fires at most once per " +
  "session; reading raw files to modify or debug specific lines is fine after " +
  "one query.";

const location = [...import.meta.url].reduce(
  (hash, ch) => (Math.imul(hash, 31) + ch.charCodeAt(0)) >>> 0,
  7
);
// Shared with the reminder plugin's record so one query satisfies both.
const enforced = (globalThis.__graphFirstEnforced ??= new Set());

function inputText(input) {
  if (!input || typeof input !== "object") return "";
  const parts = [];
  for (const v of Object.values(input)) {
    if (typeof v === "string") parts.push(v);
    else if (Array.isArray(v))
      parts.push(v.filter((x) => typeof x === "string").join(" "));
  }
  return parts.join(" ");
}

function shouldDeny(tool, input) {
  if (tool === "read") {
    const p = typeof input?.path === "string" ? input.path : inputText(input);
    if (!p) return false;
    if (EXEMPT_READ.some((re) => re.test(p))) return false;
    return INDEXED_READ.some((re) => re.test(p));
  }
  if (tool === "grep") {
    // A repo-wide grep (no path) searches the indexed docs too.
    // A scoped grep is only interesting when it names an indexed doc.
    const p = inputText(input);
    if (!p) return true;
    if (EXEMPT_READ.some((re) => re.test(p))) return false;
    if (INDEXED_READ.some((re) => re.test(p))) return true;
    const hasScope = /(path|include|dir|file)/i.test(JSON.stringify(Object.keys(input || {})));
    return !hasScope;
  }
  return false;
}

export default {
  id: `graph-first-${location.toString(16)}`,

  async setup(ctx) {
    await ctx.tool.hook("execute.before", (event) => {
      if (event.tool !== "read" && event.tool !== "grep") return;
      if (enforced.has(event.sessionID)) return;
      if (!hasGraph(ctx.location.directory)) return;
      if (!shouldDeny(event.tool, event.input)) return;

      enforced.add(event.sessionID);
      throw new Error(DENY_MESSAGE);
    });
  },
};
