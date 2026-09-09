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

**Exception — the MCP Server Registry.** Its schema caps `description` at 100 characters
and the field is plain text, so backticks and the em-dash render literally. `server.json`
carries a deliberately forked 94-character variant:

> Lets AI agents read the real source of any Maven dependency, decompiled from ~/.m2 or Central.

That fork is intentional. Do not "fix" the two copies into agreement — the prose version
stays everywhere that has no length cap and renders Markdown.

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

`server.json` now exists at the repo root and validates against the
`2025-12-11` schema. Publishing also requires namespace ownership proof for
`io.github.salitaba`, done via GitHub OAuth in the `mcp-publisher` CLI.

Two ownership markers must be in the **published artifacts**, not merely in git — the
registry reads the npm tarball and the PyPI sdist:

- `"mcpName": "io.github.salitaba/maven-decoder-mcp"` in `package.json` (npm)
- `<!-- mcp-name: io.github.salitaba/maven-decoder-mcp -->` as the first line of
  `README.md` (PyPI; it lands in both the sdist README and `PKG-INFO`)

Both are committed, so a release cut after that commit carries them. Editing them alone
publishes nothing — cut a release per `RELEASING.md` first, then run `mcp-publisher`.

The version to record is **1.3.1** — what is actually on PyPI and npm. Do not read it out
of `pyproject.toml` or `package.json`; those say `1.3.0` by design. Per `RELEASING.md`,
the git tag is the single source of truth and the release workflow rewrites all three
manifests from the tag at build time, so the in-repo copies lag deliberately. Take the
version from `git tag --list | tail -1`.

## Targets

Ordered by leverage, not alphabetically. Do them over several days, not one afternoon.

| # | Target | Route | Notes | Status |
|---|---|---|---|---|
| 1 | MCP Server Registry | `mcp-publisher` CLI + `server.json` | Upstream of several directories. `server.json` exists and validates. Blocked only on releasing a version whose npm tarball and PyPI sdist carry the ownership markers. | ☐ |
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
