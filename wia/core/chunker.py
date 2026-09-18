"""Workspace-aware semantic code chunker."""

import hashlib
import re
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class SemanticChunk:
    """Represents a semantic structural chunk of source code or documentation."""

    chunk_id: str
    file_path: str
    content: str
    chunk_type: str  # "class", "function", "module", "config", "block"
    symbol_name: str
    line_start: int
    line_end: int
    content_hash: str

    def to_dict(self) -> dict:
        """Convert semantic chunk to serializable dictionary."""
        return asdict(self)


class WorkspaceChunker:
    """Splits source code and documents into structural semantic chunks."""

    @classmethod
    def compute_hash(cls, content: str) -> str:
        """Compute SHA-256 hash for chunk content."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def chunk_file(cls, file_path: str | Path, content: str) -> list[SemanticChunk]:
        """Split file content into semantic chunks based on definitions and line blocks."""
        path_str = str(file_path).replace("\\", "/")
        lines = content.splitlines()
        if not lines:
            return []

        chunks: list[SemanticChunk] = []
        fn_class_pattern = re.compile(r"^\s*(class|def|async def|function|const|class)\s+([A-Za-z0-9_]+)")

        current_block: list[str] = []
        block_start = 1
        current_symbol = ""
        current_type = "block"

        for line_num, line in enumerate(lines, start=1):
            match = fn_class_pattern.match(line)
            if match:
                if current_block:
                    block_content = "\n".join(current_block).strip()
                    if block_content:
                        c_hash = cls.compute_hash(block_content)
                        c_id = f"{path_str}#{block_start}-{line_num-1}:{c_hash}"
                        chunks.append(
                            SemanticChunk(
                                chunk_id=c_id,
                                file_path=path_str,
                                content=block_content,
                                chunk_type=current_type,
                                symbol_name=current_symbol,
                                line_start=block_start,
                                line_end=line_num - 1,
                                content_hash=c_hash,
                            )
                        )
                current_block = [line]
                block_start = line_num
                current_type = "class" if match.group(1) == "class" else "function"
                current_symbol = match.group(2)
            else:
                current_block.append(line)

        if current_block:
            block_content = "\n".join(current_block).strip()
            if block_content:
                c_hash = cls.compute_hash(block_content)
                c_id = f"{path_str}#{block_start}-{len(lines)}:{c_hash}"
                chunks.append(
                    SemanticChunk(
                        chunk_id=c_id,
                        file_path=path_str,
                        content=block_content,
                        chunk_type=current_type if current_symbol else "module",
                        symbol_name=current_symbol,
                        line_start=block_start,
                        line_end=len(lines),
                        content_hash=c_hash,
                    )
                )

        return chunks
