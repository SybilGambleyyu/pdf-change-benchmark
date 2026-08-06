"""A process-bound public-JSON PDFFence stand-in for adapter tests."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    """Emit the public truth associated with a fixture candidate path."""

    command = sys.argv[1]
    candidate = Path(sys.argv[3])
    truth = json.loads((candidate.parent / "truth.json").read_text(encoding="utf-8"))
    if command == "diff":
        print(
            json.dumps(
                {
                    "changes": [
                        {"kind": kind} for kind in truth["expected_change_kinds"]
                    ]
                }
            )
        )
        return 0
    if command == "check":
        print(
            json.dumps(
                {
                    "findings": [
                        {"rule_id": rule_id}
                        for rule_id in truth["expected_policy_rule_ids"]
                    ]
                }
            )
        )
        return 1 if truth["expected_policy_rule_ids"] else 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
