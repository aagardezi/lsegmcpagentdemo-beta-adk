from dataclasses import dataclass


@dataclass
class ResearchConfiguration:

    # gemini_model: str = "gemini-flash-latest"
    # gemini_model: str = "gemini-2.5-flash-preview-09-2025"
    gemini_flash_model: str = "gemini-2.5-flash"
    gemini_pro_model: str = "gemini-2.5-pro"
    gemini_model: str = "gemini-2.5-flash"
    gemini31_model: str = "gemini-2.5-pro"
    gemini_3_pro_model: str = "gemini-2.5-pro"




config = ResearchConfiguration()
