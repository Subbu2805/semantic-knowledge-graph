#!/usr/bin/env python3
"""Runs every request in use-cases/catalog.json against a live Solr and checks its expectations.

Exit code is non-zero if any use case errors or fails an expectation, so this doubles
as a post-deploy health / regression check.

Usage: scripts/smoke_test.py [use-case-id ...]
Env:   SOLR_URL (default http://localhost:8983/solr)
"""
import json
import os
import sys
import time
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOLR_URL = os.environ.get("SOLR_URL", "http://localhost:8983/solr").rstrip("/")


def run(core, request, timeout=30):
    req = urllib.request.Request(f"{SOLR_URL}/{core}/rel", data=json.dumps(request).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def nodes_of_type(nodes, type_):
    for node in nodes or []:
        if node.get("type") == type_:
            yield node
        for value in node.get("values", []):
            yield from nodes_of_type(value.get("compare"), type_)


def check(expectation, data):
    nodes = list(nodes_of_type(data, expectation["type"]))
    if not nodes:
        return f"no '{expectation['type']}' node in response"
    n = expectation.get("in_top", 10 ** 6)
    tops = [[v["name"] for v in node.get("values", [])[:n]] for node in nodes]
    if "any_of" in expectation and not any(set(expectation["any_of"]) & set(t) for t in tops):
        return f"expected one of {expectation['any_of']} in top {n} {expectation['type']}, got {tops}"
    if "none_of" in expectation and any(set(expectation["none_of"]) & set(t) for t in tops):
        return f"expected none of {expectation['none_of']} in top {n} {expectation['type']}, got {tops}"
    for name in expectation.get("negative", []):
        scores = [v["relatedness"] for node in nodes for v in node.get("values", []) if v["name"] == name]
        if not scores or any(s >= 0 for s in scores):
            return f"expected negative relatedness for {name}, got {scores}"
    return None


def main(ids):
    with open(os.path.join(ROOT, "use-cases", "catalog.json")) as f:
        cases = json.load(f)["use_cases"]
    if ids:
        cases = [c for c in cases if c["id"] in ids]
    failures = 0
    for case in cases:
        start = time.time()
        try:
            data = run(case["core"], case["request"]).get("data", [])
            errors = [e for e in (check(x, data) for x in case.get("expect", [])) if e]
        except (urllib.error.URLError, ValueError) as e:
            body = e.read().decode(errors="replace")[:300] if isinstance(e, urllib.error.HTTPError) else ""
            errors = [f"request failed: {e} {body}".strip()]
        ms = (time.time() - start) * 1000
        status = "FAIL" if errors else "PASS"
        failures += bool(errors)
        print(f"{status}  {case['id']:<30} {ms:7.1f} ms")
        for err in errors:
            print(f"      {err}")
    print(f"\n{len(cases) - failures}/{len(cases)} use cases passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
