# Marketing

Working notes, not published content. Nothing here is shipped by the package.

## Execution order

Each step feeds the next. Do not reorder — steps 3 and 4 both consume the asset from
step 1, and step 5 must land before any traffic does.

Status current as of 2026-09-16. Check it against the live repo before trusting it — this
list has gone stale before.

1. **[demo-script.md](demo-script.md)** — ☑ done. `docs/demo.gif` exists and is embedded
   in the root `README.md` at line 12. Reuse it in the post and the submissions.
2. **README rewrite** — ☑ done, including the image line, which is already uncommented.
3. **[distribution-sweep.md](distribution-sweep.md)** — ◐ **in progress, and now the
   critical path.** Registry, Glama and skills.sh are live; `punkpeye` PR is filed and
   awaiting review; `wong2` is blocked on upstream interaction limits and needs a manual
   browser open. mcp.so, PulseMCP, mcpservers.org and the Cursor directory are web forms
   nobody has filled in yet. Smithery is deliberately skipped.
4. **[enterprise-post.md](enterprise-post.md)** — ☐ drafted, unpublished. Hold it until
   step 3's listings land, so the traffic spike has somewhere to arrive.
5. **[good-first-issues.md](good-first-issues.md)** — ☑ done, ahead of schedule and out of
   order: all 15 issues were filed and 14 closed before step 3 delivered any traffic, so
   the tracker was drained by the maintainer rather than by contributors. Only
   [#4](https://github.com/salitaba/maven-decoder-mcp/issues/4) is still open.
6. **Benchmark** — ☐ see below. Separate effort, separate repo, only when the rest has
   shipped. Still correctly deferred.

Steps 1, 2 and 5 are finished; the folder's remaining value is entirely in step 3, then 4.

## The benchmark (deferred, deliberately)

A `java-api-hallucination-bench` repo measuring how often models invent Java library API
signatures, with and without this tool. The elegant part is that ground truth is free:
`extract_class_info` and `extract_method_info` read exact signatures out of bytecode, so
the answer key generates itself with no human labeling.

Question types that punish memory rather than reasoning:

- **Existence** — does `X` have method `y(Z)` in version N, including methods removed later
- **Signature** — exact parameter types and return type
- **Version delta** — which public members were removed between N and M
- **Trap set** — methods present in an *adjacent* version only

**Why it is last.** Benchmark-flavored marketing invites scrutiny you do not control, and
this one benchmarks an uncomfortable claim: that model memory is unreliable. Any sloppy
methodology detail turns the discussion into a teardown of your method rather than a
conversation about the tool.

Two non-negotiables if it ships:

- Publish the harness and the full question set, not just scores. An unreproducible
  benchmark gets dismantled in the comments, and the dismantling becomes the story.
- State the sample size in the headline. "20 libraries, N questions" is armor. An
  unstated limit is the thing you get dunked on.

### Scope, if you pick it up

This is weeks, not an afternoon, and it is the only item in this folder that builds a
differentiator rather than a channel. Two competitors now occupy the "read Maven
dependencies" description — `terseprompts/jarp-mcp` and `tangcent/maven-indexer-mcp` —
so the distribution work in step 3 is increasingly a race on a crowded line, while this
is not.

A defensible v1 is smaller than it sounds:

1. Pick ~20 libraries with real version churn and a public Central presence.
2. Generate the answer key with `extract_class_info` / `extract_method_info`. No human
   labeling — that is the whole trick, and it is what makes the sample size cheap to grow.
3. Ship the four question types above. The trap set is the one that produces a quotable
   number; do not drop it for being fiddly.
4. Run one model with the tool and without it. One model, one delta. Resist a matrix —
   a grid of six models is where this turns into a month and an argument about
   per-model fairness.
5. Publish harness, question set and raw outputs in the same commit as the number.

**Decision gate before starting:** if you cannot commit to publishing the full question
set, do not start. A withheld question set is the failure mode that converts this from
evidence into a target, and the teardown becomes the story instead of the tool.
