"""
Switch Trust Guardrails & Static AST Security Verification Layer.
Audits autonomous agent patches before human approval or hotfix deployment.
"""
from __future__ import annotations

import ast
import re
from dataclasses import dataclass, asdict
from typing import Any, Dict, List


FORBIDDEN_CALLS = {"eval", "exec", "compile", "__import__", "os.system", "subprocess.Popen"}
SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"AAH[A-Za-z0-9_-]{30,}"),
    re.compile(r"BEGIN (RSA|OPENSSH|EC) PRIVATE KEY"),
]


@dataclass
class GuardrailAuditReport:
    passed: bool
    trust_score: float
    ast_valid: bool
    forbidden_calls_found: List[str]
    secrets_leaked: bool
    diff_lines_added: int
    diff_lines_removed: int
    checks: List[Dict[str, Any]]
    policy_id: str = "switch-trust-prod-v2"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def audit_patch(candidate_source: str, unified_diff: str) -> GuardrailAuditReport:
    """
    Performs deterministic AST & security guardrail verification on a candidate Python patch.
    """
    forbidden_found: List[str] = []
    ast_valid = True
    try:
        tree = ast.parse(candidate_source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name) and node.func.id in FORBIDDEN_CALLS:
                    forbidden_found.append(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    attr_chain = f"{getattr(node.func.value, 'id', '')}.{node.func.attr}"
                    if attr_chain in FORBIDDEN_CALLS:
                        forbidden_found.append(attr_chain)
    except SyntaxError as exc:
        ast_valid = False
        forbidden_found.append(f"SyntaxError:{exc.lineno}")

    secrets_leaked = any(pat.search(candidate_source) for pat in SECRET_PATTERNS)

    added = sum(
        1 for line in unified_diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )
    removed = sum(
        1 for line in unified_diff.splitlines()
        if line.startswith("-") and not line.startswith("---")
    )
    bounded_blast_radius = (added + removed) <= 45

    checks = [
        {
            "name": "Python AST Syntax & Parse Integrity",
            "status": "PASS" if ast_valid else "FAIL",
            "detail": "AST parsed cleanly with 0 syntax errors" if ast_valid else "SyntaxError in candidate patch",
        },
        {
            "name": "Switch Trust Forbidden Execution Gate",
            "status": "PASS" if not forbidden_found else "FAIL",
            "detail": "0 unsafe dynamic calls (eval/exec/os.system)" if not forbidden_found else f"Blocked: {', '.join(forbidden_found)}",
        },
        {
            "name": "Credential & Token DLP Scan",
            "status": "PASS" if not secrets_leaked else "FAIL",
            "detail": "No hardcoded tokens or private keys in diff" if not secrets_leaked else "Secret pattern detected",
        },
        {
            "name": "Minimal Blast-Radius Policy (<=45 LOC)",
            "status": "PASS" if bounded_blast_radius else "WARN",
            "detail": f"+{added} / -{removed} lines modified within surgical threshold",
        },
    ]

    passed = ast_valid and not forbidden_found and not secrets_leaked
    trust_score = 99.4 if passed and bounded_blast_radius else (82.0 if passed else 12.0)

    return GuardrailAuditReport(
        passed=passed,
        trust_score=trust_score,
        ast_valid=ast_valid,
        forbidden_calls_found=forbidden_found,
        secrets_leaked=secrets_leaked,
        diff_lines_added=added,
        diff_lines_removed=removed,
        checks=checks,
    )

