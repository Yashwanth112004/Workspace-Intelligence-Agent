"""Dependency conflict and version inconsistency detector."""

from dataclasses import asdict, dataclass
from wia.analyzers.dependency.manifest_parser import DependencyItem


@dataclass
class DependencyConflict:
    """Represents a detected version conflict or duplicate dependency entry."""

    package_name: str
    conflict_type: str  # "version_mismatch", "duplicate_entry"
    reason: str
    affected_manifests: list[str]

    def to_dict(self) -> dict:
        """Convert DependencyConflict to serializable dictionary."""
        return asdict(self)


class ConflictDetector:
    """Detects version mismatches and duplicate conflicting package definitions."""

    @classmethod
    def detect_conflicts(cls, dependencies: list[DependencyItem]) -> list[DependencyConflict]:
        """Group dependencies by ecosystem and package name to detect version conflicts."""
        grouped: dict[tuple[str, str], list[DependencyItem]] = {}
        for item in dependencies:
            key = (item.ecosystem, item.name.lower())
            grouped.setdefault(key, []).append(item)

        conflicts: list[DependencyConflict] = []

        for (ecosystem, pkg_name), items in grouped.items():
            if len(items) <= 1:
                continue

            specs = {it.version_spec for it in items}
            manifests = [it.manifest_path for it in items]

            if len(specs) > 1:
                conflicts.append(
                    DependencyConflict(
                        package_name=items[0].name,
                        conflict_type="version_mismatch",
                        reason=f"Package '{items[0].name}' has conflicting specs: {', '.join(specs)}",
                        affected_manifests=manifests,
                    )
                )
            else:
                conflicts.append(
                    DependencyConflict(
                        package_name=items[0].name,
                        conflict_type="duplicate_entry",
                        reason=f"Package '{items[0].name}' is declared multiple times in: {', '.join(manifests)}",
                        affected_manifests=manifests,
                    )
                )

        return conflicts
