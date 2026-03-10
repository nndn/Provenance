"""Provenance data model — Node, Edge, BlastRadius, ValidationReport, Context."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

NodeType = Literal["requirement", "constraint", "question"]
EdgeType = Literal["depends-on", "implements", "blocked-by"]


@dataclass
class Node:
    slug: str
    type: NodeType
    domain: str
    file: str
    statement: str
    planned: bool = False
    provenance: str = ""
    assumptions: list[str] = field(default_factory=list)
    code_refs: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    blocked_by: list[str] = field(default_factory=list)


@dataclass
class Edge:
    from_slug: str
    to_slug: str
    type: EdgeType


@dataclass
class BlastRadius:
    root: str
    direct_dependents: list[Node]
    transitive_slugs: list[str]
    all_code_paths: list[str]
    assumptions_in_path: list[tuple[str, str]]
    planned_in_path: list[Node]


@dataclass
class ValidationReport:
    errors: list[str]
    warnings: list[str]
    clean: list[str]


@dataclass
class Context:
    title: str
    purpose: str
    hard_constraints: list[str]
    domain_map: dict[str, str]  # domain -> path
