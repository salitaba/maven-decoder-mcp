# Your AI agent can't see your company's internal artifacts. Here's the fix.

*Draft. Target: r/java, dev.to, Hacker News. Title stands as-is — no "Show HN", it reads*
*as a problem post rather than a launch, which has a higher ceiling.*

---

Ask your coding agent about `com.contoso.platform:payments-client` and watch what happens.

It will answer. Confidently. It will produce method names that sound exactly right,
because they follow every naming convention it has ever seen. They will also be invented,
because that artifact:

- was never in any training set
- is on no public index
- almost certainly ships without a sources jar

So the agent is least reliable in exactly the place your code is most proprietary. In a
typical enterprise Java service, half the dependency tree is internal artifacts published
to a corporate Nexus or Artifactory. That half is invisible.

## Point it at your mirror

`maven-decoder-mcp` is an MCP server that reads Maven artifacts — local, remote, or
internal — and hands the real source to the agent. Aiming it at a private repository is
three environment variables:

```bash
export MAVEN_REMOTE_REPOS="https://nexus.corp/repository/maven-public"
export MAVEN_REMOTE_USERNAME=builder
export MAVEN_REMOTE_PASSWORD=secret
```

### On those credentials — read this before you paste it into `.zshrc`

Basic-auth credentials in environment variables leak in ways that are easy to forget:
shell history, `/proc/<pid>/environ` and `ps e` output on shared hosts, CI job logs, and
crash dumps. That is a real exposure, not a theoretical one, and a repository credential
is often broader-scoped than people assume.

Do not `export` these in a shell rc file. Prefer, in rough order:

1. Your MCP client's own secret store, if it has one
2. A `.env` file with `chmod 600`, owned by your user, git-ignored
3. A read-only Nexus service account scoped to the repositories you actually need —
   never your personal SSO-backed credential

If your organization has a secrets policy, this is a case it covers. Follow it rather
than this list.

## The part that matters: no sources jar

Internal artifacts are usually published as bytecode only. Nobody wires up
`maven-source-plugin` for a service client used by four teams.

That is the normal case, not the edge case, and it is handled:

```
The sources jar is missing for com.contoso.platform:payments-client. What methods does it expose?
```

`extract_class_info` falls back to `javap` internally and returns parsed fields, methods,
bytecode version, and optional verbose bytecode output. The agent reads what is actually
compiled into the jar instead of guessing from the artifact name.

The same machinery answers upgrade questions. Point `compare_versions` at two releases of
a public library and it reports the actual delta rather than a recollection of one —
`org.jsoup:jsoup` 1.17.2 to 1.23.2 is 45 breaking changes across 47 of 115 classes:

![Comparing jsoup 1.17.2 with 1.23.2](../docs/demo.gif)

Members are compared as declared, so one that moved to a supertype is listed as removed
even when it stays callable. The tool says so in its own output rather than leaving you
to discover it.

## Bonus for gRPC shops

`extract_jar_resource` pulls text resources straight out of the jar — including `.proto`
files, `META-INF/services` entries, and other metadata.

If your internal contracts ship as protos inside artifacts, your agent can now read the
actual service definitions rather than a summary of them.

## Will it break my builds?

Three specific answers, because this is the question that decides adoption in a
regulated shop:

**It does not touch `~/.m2`.** Downloads land in a separate cache
(`MAVEN_DECODER_CACHE_DIR`, else `$XDG_CACHE_HOME/maven-decoder-mcp/repository`, else
`~/.cache/maven-decoder-mcp/repository`) that uses the standard Maven layout. Your Maven and Gradle builds resolve from an
untouched local repository. Every response carries an `origin` field
(`local-repository` or `remote-cache`) so you always know where a result came from.

**Downloads are checksum-verified.** Artifacts are checked against the repository's
published SHA-1 (`MAVEN_VERIFY_CHECKSUM`, on by default), with a size ceiling via
`MAVEN_MAX_DOWNLOAD_SIZE`.

**Network access is one flag away from off.**

```bash
MAVEN_OFFLINE=true        # no network access at all, local repository only
MAVEN_AUTO_DOWNLOAD=false # keep search, never auto-download
```

If your security review says the agent gets no egress, it still works against whatever
is already on disk.

## Try it

```bash
npx skills add https://github.com/salitaba/maven-decoder-mcp --skill maven-code-search
```

---

**Publish-ready.** Pre-flight done:

- GIF embedded after the "no sources jar" section. The relative path works on GitHub;
  on dev.to and Reddit, upload the image to the host and replace the link.
- Artifact name is `com.contoso.platform:payments-client`. Contoso is Microsoft's
  reserved fictional company, and `com.contoso*` returns 0 hits on Maven Central, so it
  cannot collide with a real publisher.
- Every env var checked against `maven_decoder_mcp/config.py`, not the README:
  `MAVEN_REMOTE_REPOS`, `MAVEN_REMOTE_USERNAME`, `MAVEN_REMOTE_PASSWORD`,
  `MAVEN_OFFLINE`, `MAVEN_AUTO_DOWNLOAD` (default true), `MAVEN_VERIFY_CHECKSUM`
  (default true), `MAVEN_MAX_DOWNLOAD_SIZE`, `MAVEN_DECODER_CACHE_DIR`. SHA-1
  verification is `maven_central.py:480`; cache resolution is `config.py:182`.

Re-check the env var list if `config.py` changes before you post.
