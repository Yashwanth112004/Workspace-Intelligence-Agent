# 🛡️ WIA Provenance & Trustworthiness Model

In AI code intelligence, hallucinated or unverified claims lead to broken developer trust. WIA enforces a strict **Source Provenance Model** where all extracted facts and answers are traceable to physical code coordinates.

---

## 🏷️ Provenance Classification

```
   ┌────────────────────────────────────────────────────────┐
   │ 1. DETERMINISTIC_FACT                                  │
   │    • Extracted directly via AST parser & visitors      │
   │    • File path, line numbers, exact signatures         │
   │    • 100% confidence, verifiable against source disk   │
   └────────────────────────────────────────────────────────┘
                               ▲
   ┌───────────────────────────┴────────────────────────────┐
   │ 2. LLM_SUMMARY                                         │
   │    • Bottom-up hierarchical aggregation of facts       │
   │    • Derived directly from Level 1 function summaries  │
   │    • Traceable to specific module components           │
   └────────────────────────────────────────────────────────┘
                               ▲
   ┌───────────────────────────┴────────────────────────────┐
   │ 3. LLM_INFERENCE                                       │
   │    • High-level reasoning, recommendations, guidance   │
   │    • Clearly demarcated from deterministic facts       │
   └────────────────────────────────────────────────────────┘
```

---

## 📑 Clickable Citation Model

Every context snippet and response from WIA attaches structured citation records:
```json
{
  "file_path": "backend/app/services/parser/ast_parser.py",
  "start_line": 13,
  "end_line": 35,
  "chunk_type": "function",
  "evidence_type": "DETERMINISTIC_FACT",
  "score": 0.982
}
```

In the **VS Code Extension**, clicking any citation button instantly opens the target file and jumps the editor cursor to the exact line range.
