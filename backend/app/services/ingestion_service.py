import os
import glob
import re
import logging
from typing import List, Dict, Any

logger = logging.getLogger("lumina.ingestion")

class IngestionService:
    """
    Service responsible for reading, chunking (with overlap)
    and ingesting business knowledge documents in PDF, Word (.docx), TXT, and Markdown (.md).
    """

    SUPPORTED_EXTENSIONS = [".pdf", ".docx", ".doc", ".txt", ".md"]

    def __init__(self, data_dir: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initializes the ingestion service.
        :param data_dir: Directory containing business knowledge files.
        :param chunk_size: Maximum desired character size per chunk.
        :param chunk_overlap: Number of overlapping characters between chunks.
        """
        self.data_dir = data_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    @staticmethod
    def extract_text_from_file(file_path: str) -> str:
        """
        Extracts clean text content from PDF, DOCX, TXT, or MD files.
        """
        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            try:
                from pypdf import PdfReader
                reader = PdfReader(file_path)
                pages_text = []
                for page_idx, page in enumerate(reader.pages):
                    text = page.extract_text()
                    if text:
                        pages_text.append(text.strip())
                return "\n\n".join(pages_text)
            except Exception as e:
                logger.error("Error extracting text from PDF '%s': %s", file_path, str(e))
                return ""

        elif ext in [".docx", ".doc"]:
            try:
                import docx
                doc = docx.Document(file_path)
                paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
                # Also extract table text
                for table in doc.tables:
                    for row in table.rows:
                        row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                        if row_text:
                            paragraphs.append(row_text)
                return "\n\n".join(paragraphs)
            except Exception as e:
                logger.error("Error extracting text from DOCX '%s': %s", file_path, str(e))
                return ""

        else:
            # Plain text / Markdown
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    return f.read()
            except Exception as e:
                logger.error("Error reading text file '%s': %s", file_path, str(e))
                return ""

    def load_documents(self) -> List[Dict[str, str]]:
        """
        Reads all supported files (.pdf, .docx, .txt, .md) present in data_dir.
        :return: List of dictionaries containing 'source' (file name) and 'content'.
        """
        documents = []
        if not os.path.exists(self.data_dir):
            return documents

        for file_name in os.listdir(self.data_dir):
            file_path = os.path.join(self.data_dir, file_name)
            if not os.path.isfile(file_path):
                continue
            ext = os.path.splitext(file_name)[1].lower()
            if ext not in self.SUPPORTED_EXTENSIONS:
                continue

            content = self.extract_text_from_file(file_path)
            if content.strip():
                documents.append({
                    "source": file_name,
                    "content": content
                })
                logger.info("Loaded document '%s' (%d chars)", file_name, len(content))

        return documents

    def _compute_clean_overlap(self, text: str) -> str:
        """
        Computes clean overlap text respecting word and newline boundaries to prevent word fragmentation.
        """
        if len(text) <= self.chunk_overlap:
            return text.strip()
        raw_overlap = text[-self.chunk_overlap:]
        first_break = max(raw_overlap.find("\n"), raw_overlap.find(" "))
        if first_break != -1 and first_break < len(raw_overlap) - 1:
            return raw_overlap[first_break + 1:].strip()
        return raw_overlap.strip()

    def create_chunks(self, documents: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Splits documents respecting logical sections or paragraphs.
        :param documents: Loaded documents.
        :return: List of structured chunks with text and metadata.
        """
        chunks = []
        chunk_counter = 0

        for doc in documents:
            text = doc["content"]
            source = doc["source"]

            # Extract main document title if present (# Title)
            main_title = ""
            title_match = re.match(r'^#\s+(.+)\n', text)
            if title_match:
                main_title = title_match.group(1).strip()
                text = text[title_match.end():].strip()

            # Split primarily by sub-headers (## or ###) or double line breaks
            sections = re.split(r'\n(?=#{1,3}\s)', text) if "#" in text else text.split("\n\n\n")

            for section in sections:
                section_text = section.strip()
                if not section_text:
                    continue

                if main_title and not section_text.startswith("#"):
                    section_text = f"# {main_title}\n\n{section_text}"

                if len(section_text) > self.chunk_size:
                    paragraphs = section_text.split("\n\n")
                    sub_chunk = ""
                    for p in paragraphs:
                        if len(sub_chunk) + len(p) + 2 <= self.chunk_size:
                            sub_chunk = f"{sub_chunk}\n\n{p}".strip()
                        else:
                            if sub_chunk:
                                chunks.append({
                                    "id": f"{source}_chunk_{chunk_counter}",
                                    "text": sub_chunk,
                                    "metadata": {"source": source}
                                })
                                chunk_counter += 1
                                overlap = self._compute_clean_overlap(sub_chunk)
                                sub_chunk = f"{overlap}\n\n{p}".strip()
                            else:
                                sub_chunk = p.strip()
                    if sub_chunk:
                        chunks.append({
                            "id": f"{source}_chunk_{chunk_counter}",
                            "text": sub_chunk,
                            "metadata": {"source": source}
                        })
                        chunk_counter += 1
                else:
                    chunks.append({
                        "id": f"{source}_chunk_{chunk_counter}",
                        "text": section_text,
                        "metadata": {"source": source}
                    })
                    chunk_counter += 1

        return chunks
