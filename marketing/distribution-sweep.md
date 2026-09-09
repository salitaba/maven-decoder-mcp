# Distribution sweep

Zero cost, permanent, compounding. One afternoon of work.

The demo GIF exists (`docs/demo.gif`), so listings that render the README's first image
now have one. Nothing here is blocked.

**Routes below were verified on 2026-09-09.** Directory tooling changes often; if a
submission route disagrees with this file, trust the directory and update this file.

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

## Do this first: publish to the official registry

`modelcontextprotocol/servers` **retired its community list**. Its CONTRIBUTING.md now
routes third-party servers to the [MCP Server Registry](https://github.com/modelcontextprotocol/registry),
and several downstream directories seed from that registry. So it is not one of ten
equal targets — it is the upstream one, and it is the only target here that needs a code
change first.

Publishing requires a `server.json` at the repo root, which this repo does not have. It
also requires namespace ownership proof for `io.github.salitaba`, done via GitHub OAuth
in the `mcp-publisher` CLI.

Blocking detail before you publish: **the version is inconsistent.** `package.json`,
`pyproject.toml`, and `maven_decoder_mcp/__init__.py` all say `1.3.0`, but the most
recent commit is `release: v1.3.1`. The registry records a version and people file bugs
against it. Reconcile that first — a registry entry pointing at a version that does not
exist is worse than no entry.

## Targets

Ordered by leverage, not alphabetically. Do them over several days, not one afternoon.

| # | Target | Route | Notes | Status |
|---|---|---|---|---|
| 1 | MCP Server Registry | `mcp-publisher` CLI + `server.json` | Upstream of several directories. Needs `server.json` and the version fix. | ☐ |
| 2 | `punkpeye/awesome-mcp-servers` | PR to `main`, `README.md` | 94k stars, the highest-traffic list. Format is strict — see below. | ☐ |
| 3 | Glama MCP directory | web submit / auto-index | Also issues the badge that `punkpeye` entries carry. Do before #2 so the badge URL resolves. | ☐ |
| 4 | `wong2/awesome-mcp-servers` | PR to `main`, `## Community Servers` | 4.3k stars. Different format from #2 — do not paste the same line. | ☐ |
| 5 | mcp.so | web submit | ☐ |
| 6 | PulseMCP | web submit | ☐ |
| 7 | mcpservers.org | web submit | ☐ |
| 8 | Smithery | registry submit | Verify whether it wants a hosted endpoint; this server is stdio/local. | ☐ |
| 9 | Cursor MCP directory | submit | Repo already ships `cursor_mcp_config_template.json`. Link it. | ☐ |
| 10 | skills.sh | already indexed | Badge in README. | ☑ |
| — | `modelcontextprotocol/servers` | **do not file** | List retired; PR gets closed unread. Superseded by #1. | ✗ |

## Exact copy per format

### `punkpeye/awesome-mcp-servers` — under `### 💻 Developer Tools`

Entries carry a Glama badge and legend emoji: 🐍 Python, 🏠 local service, 🍎 macOS,
🪟 Windows, 🐧 Linux. Alphabetical by `owner/repo`, so this lands between the `ma…` and
`mc…` entries.

```markdown
- [salitaba/maven-decoder-mcp](https://github.com/salitaba/maven-decoder-mcp) [![salitaba/maven-decoder-mcp MCP server](https://glama.ai/mcp/servers/salitaba/maven-decoder-mcp/badges/score.svg)](https://glama.ai/mcp/servers/salitaba/maven-decoder-mcp) 🐍 🏠 🍎 🪟 🐧 - Lets AI agents read the actual source of any Maven dependency — decompiles jars from `~/.m2` or Maven Central, and diffs versions for breaking changes. Works on artifacts with no sources jar via `javap`, and against a private Nexus or Artifactory. `npx skills add https://github.com/salitaba/maven-decoder-mcp --skill maven-code-search`
```

Two things about that list before you file:

- Its CONTRIBUTING.md asks automated agents to append `🤖🤖🤖` to the PR title to opt into
  fast-track merging. If a human writes the PR, do not use it.
- A near neighbor already exists: `mcurmi05/vdiff` — "Breaking-change diffs for npm
  packages so coding agents stop writing code against outdated API knowledge." Same
  thesis, different ecosystem. That is fine, and it is evidence the category is real.
  Do not describe this project as the only one doing it.

### `wong2/awesome-mcp-servers` — under `## Community Servers`

Different convention: bold display name, no badge, no emoji, short description,
alphabetical by display name.

```markdown
- **[Maven Decoder](https://github.com/salitaba/maven-decoder-mcp)** - Read the actual source of any Maven dependency — decompile jars from `~/.m2` or Maven Central, and diff versions for breaking changes.
```

### Web submit forms (mcp.so, PulseMCP, mcpservers.org, Glama)

- **Name:** `maven-decoder-mcp`
- **Repo:** `https://github.com/salitaba/maven-decoder-mcp`
- **Category:** Developer Tools (fall back to Code Intelligence; never "Java")
- **Description:** the verbatim one-liner above
- **Install:** `npx skills add https://github.com/salitaba/maven-decoder-mcp --skill maven-code-search`
- **Transport:** stdio, local
- **Language:** Python
- **License:** MIT

## Lead with the skill, not the server

`npx skills add ...` is one command with no JSON config, no venv, no Python/Node decision.
The MCP server is the payload; the skill is the front door. The README now orders it this
way — keep directory submissions consistent with that.

## PR etiquette

- One line added, alphabetical placement, match the surrounding format exactly
- No self-promotional adjectives in the PR body
- Do not open PRs to ten lists in the same hour from the same account; it reads as spam
  and maintainers talk to each other
