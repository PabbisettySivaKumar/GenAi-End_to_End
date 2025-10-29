"""
router/pdf_render.py
API endpoint to render highlighted PDF pages as images.
"""

from fastapi import APIRouter, Response
from pydantic import BaseModel
from services.pdf_utils import highlight_text_on_page
import tempfile
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pdf", tags=["PDF"])


class HighlightRequest(BaseModel):
    pdf_path: str
    page_num: int
    snippet: str


@router.post("/highlight")
def render_highlight(req: HighlightRequest):
    """
    Given a PDF path, page number, and text snippet,
    highlights that snippet on the page and returns the rendered image (PNG).
    """
    logger.info(f"Rendering highlight for {req.pdf_path}, page {req.page_num}")

    try:
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
        highlight_text_on_page(req.pdf_path, req.page_num, req.snippet, tmp.name)
        with open(tmp.name, "rb") as f:
            img_bytes = f.read()
        os.remove(tmp.name)
        return Response(content=img_bytes, media_type="image/png")
    except Exception as e:
        logger.error(f"Error rendering highlight: {e}")
        return Response(content=str(e), media_type="text/plain", status_code=500)
