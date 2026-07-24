# Copyright 2026 Google LLC
import sys
from unittest.mock import MagicMock, AsyncMock
import pytest
from google.genai import types

# Early mocking to prevent genai.Client initialization error during import
import google.genai
google.genai.Client = MagicMock()

from lseg_market_agent.pdf_generator import create_pdf_report
import base64

PNG_BYTES = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

class MockArtifact:
    def __init__(self, data):
        self.inline_data = MagicMock()
        self.inline_data.data = data

@pytest.mark.asyncio
async def test_create_pdf_report_fallback_sorting_mixed() -> None:
    tool_context = AsyncMock()
    artifacts_in_session = [
        "random_file.txt",
        "media__older_no_time.png",
        "20260724_010000.png",
        "media__20260724_030000.png",
        "20260724_020000.png",
        "media__another_no_time.png",
    ]
    tool_context.list_artifacts.return_value = artifacts_in_session
    loaded_filenames = []
    async def mock_load_artifact(filename):
        loaded_filenames.append(filename)
        if filename == "missing_image.png":
            return None
        return MockArtifact(PNG_BYTES)
    tool_context.load_artifact.side_effect = mock_load_artifact
    
    await create_pdf_report(
        markdown_content="# Test",
        image_paths=["missing_image.png"],
        artifact_name="test_output.pdf",
        tool_context=tool_context
    )
    # With sequential fallback, first missing image maps to index 0 of sorted pngs (media__another_no_time.png)
    assert loaded_filenames[-1] == "media__another_no_time.png"

@pytest.mark.asyncio
async def test_create_pdf_report_fallback_sorting_only_no_time() -> None:
    tool_context = AsyncMock()
    artifacts_in_session = [
        "media__apple.png",
        "media__banana.png",
    ]
    tool_context.list_artifacts.return_value = artifacts_in_session
    loaded_filenames = []
    async def mock_load_artifact(filename):
        loaded_filenames.append(filename)
        if filename == "missing_image.png":
            return None
        return MockArtifact(PNG_BYTES)
    tool_context.load_artifact.side_effect = mock_load_artifact
    
    await create_pdf_report(
        markdown_content="# Test",
        image_paths=["missing_image.png"],
        artifact_name="test_output.pdf",
        tool_context=tool_context
    )
    assert loaded_filenames[-1] == "media__apple.png"

@pytest.mark.asyncio
async def test_create_pdf_report_fallback_sorting_only_timestamps() -> None:
    tool_context = AsyncMock()
    artifacts_in_session = [
        "20260724_020000.png",
        "20260724_010000.png",
        "20260724_030000.png",
    ]
    tool_context.list_artifacts.return_value = artifacts_in_session
    loaded_filenames = []
    async def mock_load_artifact(filename):
        loaded_filenames.append(filename)
        if filename == "missing_image.png":
            return None
        return MockArtifact(PNG_BYTES)
    tool_context.load_artifact.side_effect = mock_load_artifact
    
    await create_pdf_report(
        markdown_content="# Test",
        image_paths=["missing_image.png"],
        artifact_name="test_output.pdf",
        tool_context=tool_context
    )
    assert loaded_filenames[-1] == "20260724_010000.png"


@pytest.mark.asyncio
async def test_create_pdf_report_fallback_sequential_mapping() -> None:
    tool_context = AsyncMock()
    artifacts_in_session = [
        "media__1.png",
        "media__0.png", # Out of order to test sorting
        "media__2.png",
    ]
    tool_context.list_artifacts.return_value = artifacts_in_session
    loaded_filenames = []
    async def mock_load_artifact(filename):
        loaded_filenames.append(filename)
        if filename in ["missing1.png", "missing2.png"]:
            return None
        return MockArtifact(PNG_BYTES)
    tool_context.load_artifact.side_effect = mock_load_artifact
    
    await create_pdf_report(
        markdown_content="# Test",
        image_paths=["missing1.png", "missing2.png"],
        artifact_name="test_output.pdf",
        tool_context=tool_context
    )
    
    expected_calls = [
        "missing1.png",
        "media__0.png", # first sorted
        "missing2.png",
        "media__1.png"  # second sorted
    ]
    assert loaded_filenames == expected_calls
