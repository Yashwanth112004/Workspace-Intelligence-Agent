"""Unit tests for Jupyter Notebook parser and notebook explanation."""

import json
from pathlib import Path
from wia.analyzers.code.notebook_parser import NotebookParser
from wia.core.index_model import WorkspaceIndex
from wia.core.metadata import FileRecord, IndexingStatus
from wia.knowledge.graph import WorkspaceGraph
from wia.services.explanation_service import ExplanationService


def test_notebook_parser_extraction(tmp_path: Path):
    nb_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": ["# Data Analysis Pipeline\n", "This notebook analyzes customer churn."],
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "source": [
                    "import pandas as pd\n",
                    "import numpy as np\n",
                    "from sklearn.linear_model import LogisticRegression\n",
                    "\n",
                    "def train_churn_model(df):\n",
                    "    '''Train logistic regression model.'''\n",
                    "    model = LogisticRegression()\n",
                    "    return model\n",
                ],
                "outputs": [
                    {"output_type": "stream", "text": ["Training completed in 0.42s\n"]}
                ],
            },
            {
                "cell_type": "code",
                "execution_count": 2,
                "source": [
                    "class ChurnEvaluator:\n",
                    "    def evaluate(self, y_true, y_pred):\n",
                    "        return 0.95\n",
                ],
                "outputs": [],
            }
        ],
        "metadata": {
            "kernelspec": {"name": "python3"},
            "language_info": {"name": "python"}
        },
        "nbformat": 4,
        "nbformat_minor": 2,
    }

    nb_file = tmp_path / "analysis.ipynb"
    nb_file.write_text(json.dumps(nb_content), encoding="utf-8")

    analysis = NotebookParser.parse_file(nb_file)
    assert analysis.total_cells == 3
    assert analysis.markdown_cells_count == 1
    assert analysis.code_cells_count == 2
    assert "Data Analysis Pipeline" in analysis.purpose_summary
    assert "pandas" in analysis.all_imports
    assert "numpy" in analysis.all_imports
    assert any(s.name == "train_churn_model" for s in analysis.all_symbols)
    assert any(s.name == "ChurnEvaluator" for s in analysis.all_symbols)
    assert any("stdout" in out for out in analysis.cells[1].outputs_summary)


def test_explain_notebook(tmp_path: Path):
    nb_content = {
        "cells": [
            {
                "cell_type": "markdown",
                "source": ["# Model Training Tutorial"],
            },
            {
                "cell_type": "code",
                "execution_count": 1,
                "source": ["def fit():\n    pass\n"],
                "outputs": [],
            }
        ],
        "metadata": {
            "kernelspec": {"name": "python3"},
            "language_info": {"name": "python"}
        },
    }

    nb_file = tmp_path / "tutorial.ipynb"
    nb_file.write_text(json.dumps(nb_content), encoding="utf-8")

    index = WorkspaceIndex(
        workspace_path=str(tmp_path),
        files={
            "tutorial.ipynb": FileRecord(
                relative_path="tutorial.ipynb",
                file_size=len(json.dumps(nb_content)),
                modified_time=1.0,
                extension=".ipynb",
                language="Jupyter Notebook",
                file_type="Notebook",
                indexing_status=IndexingStatus.INDEXED,
            )
        }
    )

    graph = WorkspaceGraph()
    graph.build_from_index(index)

    explanation = ExplanationService.explain_target("tutorial.ipynb", index, graph)
    assert "WIA Notebook Explanation" in explanation
    assert "Model Training Tutorial" in explanation
    assert "fit" in explanation
