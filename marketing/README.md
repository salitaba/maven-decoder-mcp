# Marketing

Working notes, not published content. Nothing here is shipped by the package.

## Execution order

Each step feeds the next. Do not reorder — steps 3 and 4 both consume the asset from
step 1, and step 5 must land before any traffic does.

1. **[demo-script.md](demo-script.md)** — record `docs/demo.gif`. Blocks everything else.
2. **README rewrite** — done. Hook, one-liner, and skill-first install are at the top of
   the root `README.md`; uncomment the image line once the GIF exists.
3. **[distribution-sweep.md](distribution-sweep.md)** — ~10 directory submissions.
4. **[enterprise-post.md](enterprise-post.md)** — the private-mirror post.
5. **[good-first-issues.md](good-first-issues.md)** — file 15 issues plus CONTRIBUTING.md.
6. **Benchmark** — see below. Separate effort, separate repo, only when the rest has shipped.

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
