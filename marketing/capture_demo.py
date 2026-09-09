#!/usr/bin/env python3
"""Re-capture the raw tool output behind the demo GIF and the README table.

Run this before changing any number in render_demo.py or the README. It calls the
real server tools; results land in /tmp/maven-decoder-demo/.

    .venv/bin/python marketing/capture_demo.py

Needs network on first run (downloads jsoup 1.23.2 into the decoder cache, never
into ~/.m2). Prints the exact figures quoted in the README.
"""

import asyncio
import json
from pathlib import Path

from maven_decoder_mcp.maven_decoder_server import MavenDecoderServer

OUT = Path("/tmp/maven-decoder-demo")
GROUP, ARTIFACT = "org.jsoup", "jsoup"
V1, V2 = "1.17.2", "1.23.2"


async def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    server = MavenDecoderServer()

    diff = json.loads((await server._compare_versions(GROUP, ARTIFACT, V1, V2))[0].text)
    (OUT / "compare_versions.json").write_text(json.dumps(diff, indent=2))

    api = diff["comparison"]["api_changes"]
    print(f"{GROUP}:{ARTIFACT}  {V1} -> {V2}")
    for key in (
        "breaking_changes",
        "members_removed",
        "members_added",
        "classes_with_api_changes",
        "classes_compared",
        "compatible",
    ):
        print(f"  {key:26} {api[key]}")

    print("\n  removed members (as declared):")
    shown = 0
    for change in api["changes"]:
        removed = change.get("methods_removed") or []
        if not removed:
            continue
        print(f"    {change['class_name']}")
        for sig in removed[:3]:
            print(f"       - {sig}")
        shown += 1
        if shown >= 6:
            break

    info = json.loads(
        (
            await server._extract_class_info(
                GROUP, ARTIFACT, V2, class_pattern="Jsoup"
            )
        )[0].text
    )
    (OUT / "extract_class_info.json").write_text(json.dumps(info, indent=2))

    print("\n  org.jsoup.Jsoup public API (from bytecode):")
    for method in info["classes"][0]["methods"]:
        sig = method["signature"]
        if sig.startswith("public static"):
            print(f"    {sig}")

    print(f"\nraw output written to {OUT}")


if __name__ == "__main__":
    asyncio.run(main())
