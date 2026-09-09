# Distribution sweep

Zero cost, permanent, compounding. One afternoon of work.

**Do this after the demo GIF exists** — most directories render the README's first image,
and a listing without one converts far worse.

## The one-line description

Use this verbatim everywhere. Consistency makes the project recognizable across lists.

> Lets AI agents read the actual source of any Maven dependency — decompiles jars from
> `~/.m2` or Maven Central, and diffs versions for breaking changes.

Avoid "comprehensive", "powerful", "advanced". In a list of 400 entries those words are
invisible; a concrete verb is not.

## Category placement

Submit under **developer tools / code intelligence**, not "Java".

The audience is not "people who use Java" — it is "people whose agent hallucinates API
signatures". Java is the mechanism, not the pitch.

## Targets

| Target | Mechanism | Status |
|---|---|---|
| `punkpeye/awesome-mcp-servers` | PR, one line under Dev Tools | ☐ |
| `modelcontextprotocol/servers` community list | PR | ☐ |
| `wong2/awesome-mcp-servers` | PR | ☐ |
| mcp.so | web submit | ☐ |
| mcpservers.org | web submit | ☐ |
| Glama MCP directory | web submit | ☐ |
| PulseMCP | web submit | ☐ |
| Smithery | registry submit | ☐ |
| Cursor MCP directory | submit | ☐ |
| skills.sh | already indexed (badge in README) | ☑ |

Verify each URL and its current submission process before filing — directory tooling and
submission routes change often, and a stale PR template gets closed unread.

## Lead with the skill, not the server

`npx skills add ...` is one command with no JSON config, no venv, no Python/Node decision.
The MCP server is the payload; the skill is the front door. The README now orders it this
way — keep directory submissions consistent with that.

## PR etiquette

- One line added, alphabetical placement, match the surrounding format exactly
- No self-promotional adjectives in the PR body
- Do not open PRs to ten lists in the same hour from the same account; it reads as spam
  and maintainers talk to each other
