"""Public fixture contracts and adapter score models."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FixtureTruth:
    """A public, non-content-bearing fixture expectation."""

    schema_version: int
    fixture_id: str
    category: str
    description: str
    expected_change_kinds: tuple[str, ...]
    expected_policy_rule_ids: tuple[str, ...]

    def public_dict(self) -> dict[str, object]:
        """Return the stable public truth projection."""

        return {
            "schema_version": self.schema_version,
            "id": self.fixture_id,
            "category": self.category,
            "description": self.description,
            "expected_change_kinds": list(self.expected_change_kinds),
            "expected_policy_rule_ids": list(self.expected_policy_rule_ids),
        }


@dataclass(frozen=True)
class FixtureScore:
    """Observed public output for one fixture."""

    fixture_id: str
    expected_change_kinds: tuple[str, ...]
    observed_change_kinds: tuple[str, ...]
    expected_policy_rule_ids: tuple[str, ...]
    observed_policy_rule_ids: tuple[str, ...]

    @property
    def passed(self) -> bool:
        """Return whether the adapter exactly matched public expectations."""

        return (
            self.expected_change_kinds == self.observed_change_kinds
            and self.expected_policy_rule_ids == self.observed_policy_rule_ids
        )

    def public_dict(self) -> dict[str, object]:
        """Return a public-safe scoring record."""

        return {
            "id": self.fixture_id,
            "passed": self.passed,
            "expected_change_kinds": list(self.expected_change_kinds),
            "observed_change_kinds": list(self.observed_change_kinds),
            "expected_policy_rule_ids": list(self.expected_policy_rule_ids),
            "observed_policy_rule_ids": list(self.observed_policy_rule_ids),
        }


@dataclass(frozen=True)
class ScoreReport:
    """A complete adapter score report."""

    fixture_scores: tuple[FixtureScore, ...]

    @property
    def passed_count(self) -> int:
        """Return the count of exact fixture matches."""

        return sum(score.passed for score in self.fixture_scores)

    def public_dict(self) -> dict[str, object]:
        """Return a stable, public-safe score report."""

        return {
            "fixture_count": len(self.fixture_scores),
            "passed_count": self.passed_count,
            "failed_count": len(self.fixture_scores) - self.passed_count,
            "fixtures": [score.public_dict() for score in self.fixture_scores],
        }
