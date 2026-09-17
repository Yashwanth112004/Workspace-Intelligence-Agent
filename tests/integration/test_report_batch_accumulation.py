"""End-to-end integration tests for persistent batch-by-batch report generation."""

import tempfile
from pathlib import Path
from wia.services.indexing_service import IndexingService
from wia.storage.repository import IndexRepository
from wia.utils.report_generator import ReportGenerator
from wia.core.index_model import BatchRecord


def test_batch_accumulation_and_report_persistence():
    """Test multi-batch accumulation, persistent index updates, and report generation."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)

        src_dir = tmp_path / "src"
        src_dir.mkdir(parents=True, exist_ok=True)

        # 1. Create Batch 1 files (5 files)
        for i in range(1, 6):
            (src_dir / f"service_{i}.py").write_text(
                f'"""Service module {i}."""\n\ndef execute_{i}():\n    return {i}\n',
                encoding="utf-8",
            )

        # Index with batch size = 2 -> generates Batch 1, Batch 2, Batch 3
        res1 = IndexingService.index_workspace(tmp_path, batch_size=2)
        assert res1.success

        index1 = IndexRepository.load_index(tmp_path)
        assert index1 is not None
        assert len(index1.batches) >= 3
        assert len(index1.get_indexed_files()) == 5

        # Generate HTML report
        out_html_path = tmp_path / ".wia" / "report.html"
        report_file1 = ReportGenerator.generate_html_report(index1, output_path=out_html_path)
        assert report_file1.exists()
        html_content1 = report_file1.read_text(encoding="utf-8")

        assert "Batch 1" in html_content1
        assert "Batch 2" in html_content1
        assert "service_1.py" in html_content1
        assert "service_5.py" in html_content1

        # 2. Add Batch 2 files (5 more files)
        for i in range(6, 11):
            (src_dir / f"service_{i}.py").write_text(
                f'"""Service module {i}."""\n\ndef execute_{i}():\n    return {i}\n',
                encoding="utf-8",
            )

        res2 = IndexingService.index_workspace(tmp_path, batch_size=2)
        assert res2.success

        index2 = IndexRepository.load_index(tmp_path)
        assert index2 is not None
        assert len(index2.batches) >= 5
        assert len(index2.get_indexed_files()) == 10

        report_file2 = ReportGenerator.generate_html_report(index2, output_path=out_html_path)
        html_content2 = report_file2.read_text(encoding="utf-8")

        # Verify old batches (Batch 1, Batch 2) AND new batches persist and accumulate
        assert "Batch 1" in html_content2
        assert "Batch 2" in html_content2
        assert "Batch 4" in html_content2
        assert "service_1.py" in html_content2
        assert "service_10.py" in html_content2

        # 3. Simulate process reload & browser refresh
        reloaded_index = IndexRepository.load_index(tmp_path)
        assert reloaded_index is not None
        reloaded_report = ReportGenerator.generate_html_report(reloaded_index, output_path=out_html_path)
        html_reloaded = reloaded_report.read_text(encoding="utf-8")

        assert "Batch 1" in html_reloaded
        assert "service_1.py" in html_reloaded
        assert "service_10.py" in html_reloaded

        # 4. Simulate a failed batch
        reloaded_index.batches.append(
            BatchRecord(
                batch_id="Batch Failed",
                status="FAILED",
                file_paths=["broken.py"],
                error_message="Simulated SyntaxError in AST parser",
                failure_stage="File Processing",
            )
        )
        IndexRepository.save_index(tmp_path, reloaded_index)

        failed_report_file = ReportGenerator.generate_html_report(reloaded_index, output_path=out_html_path)
        html_failed = failed_report_file.read_text(encoding="utf-8")

        # Verify completed batches remain intact and failed batch is reported
        assert "Batch 1" in html_failed
        assert "Batch Failed" in html_failed
        assert "Simulated SyntaxError" in html_failed
