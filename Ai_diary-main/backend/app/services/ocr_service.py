import io
import os
import shutil
import logging
from typing import Optional
from PIL import Image

logger = logging.getLogger(__name__)

class OCRService:
    """
    Lightweight OCR Extraction Service.
    Extracts readable printed/handwritten text from uploaded photo memories.
    Integrates directly with LifeBook memory and RAG indexing.
    """

    def __init__(self):
        self._tesseract_available: Optional[bool] = None
        self._find_and_configure_tesseract()

    def _find_and_configure_tesseract(self) -> Optional[str]:
        """
        Locates the Tesseract executable dynamically without requiring hardcoded paths.
        Checks system PATH, common Windows install directories, and environment variables.
        """
        try:
            import pytesseract
        except ImportError:
            self._tesseract_available = False
            return None

        # 1. Check if 'tesseract' is already in PATH
        cmd = shutil.which("tesseract")
        if cmd:
            pytesseract.pytesseract.tesseract_cmd = cmd
            self._tesseract_available = True
            logger.info(f"Tesseract found on PATH: {cmd}")
            return cmd

        # 2. Check standard Windows installation paths
        standard_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            os.path.expandvars(r"%LOCALAPPDATA%\Programs\Tesseract-OCR\tesseract.exe"),
            os.path.expandvars(r"%USERPROFILE%\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
        ]

        for p in standard_paths:
            if os.path.isfile(p):
                pytesseract.pytesseract.tesseract_cmd = p
                self._tesseract_available = True
                logger.info(f"Tesseract found at: {p}")
                return p

        self._tesseract_available = False
        return None

    def is_tesseract_available(self) -> bool:
        if self._tesseract_available is None:
            self._find_and_configure_tesseract()
        return bool(self._tesseract_available)

    def extract_text_from_image(self, image_bytes: bytes, filename: Optional[str] = None) -> str:
        """
        Extracts OCR text from raw image bytes.
        Falls back safely to empty string if no readable text is found.
        """
        if not image_bytes or len(image_bytes) < 10:
            return ""

        extracted_text = ""

        # 1. Try pytesseract if available
        if self.is_tesseract_available():
            try:
                import pytesseract
                img = Image.open(io.BytesIO(image_bytes))
                text = pytesseract.image_to_string(img)
                if text and text.strip():
                    extracted_text = text.strip()
                    logger.info(f"Pytesseract extracted {len(extracted_text)} chars")
                    return extracted_text
            except Exception as e:
                logger.debug(f"Pytesseract execution failed: {e}")

        # 2. Check PIL image metadata / text comments / basic heuristics
        try:
            img = Image.open(io.BytesIO(image_bytes))
            info = getattr(img, "info", {})
            if isinstance(info, dict):
                for k in ["Description", "UserComment", "ImageDescription", "Comment"]:
                    val = info.get(k)
                    if val and isinstance(val, (str, bytes)):
                        if isinstance(val, bytes):
                            try:
                                val = val.decode("utf-8", errors="ignore")
                            except Exception:
                                val = ""
                        if val.strip():
                            extracted_text = val.strip()
                            return extracted_text
        except Exception as e:
            logger.debug(f"PIL inspection failed: {e}")

        return extracted_text

ocr_service = OCRService()

