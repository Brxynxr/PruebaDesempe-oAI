import os
import glob
import re
from typing import List, Dict, Any

class IngestionService:
    """
    Service responsible for reading, chunking (with overlap)
    and ingesting the business knowledge documents.
    """

    def __init__(self, data_dir: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initializes the ingestion service.
        :param data_dir: Directory containing the business .md files.
        :param chunk_size: Maximum desired character size per chunk.
        :param chunk_overlap: Number of overlapping characters between chunks.
        """
        self.data_dir = data_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_documents(self) -> List[Dict[str, str]]:
        """
        Reads all Markdown (.md) files present in the data_dir directory.
        :return: List of dictionaries containing 'source' (file name) and 'content'.
        """
        documents = []
        pattern = os.path.join(self.data_dir, "*.md")
        files = glob.glob(pattern)

        for file_path in files:
            file_name = os.path.basename(file_path)
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                documents.append({
                    "source": file_name,
                    "content": content
                })
        return documents

    def _compute_clean_overlap(self, text: str) -> str:
        """
        Computes clean overlap text respecting word and newline boundaries to prevent word fragmentation.
        """
        if len(text) <= self.chunk_overlap:
            return text.strip()
        raw_overlap = text[-self.chunk_overlap:]
        # Find first whitespace or newline in raw_overlap to start on a clean boundary
        first_break = max(raw_overlap.find("\n"), raw_overlap.find(" "))
        if first_break != -1 and first_break < len(raw_overlap) - 1:
            return raw_overlap[first_break + 1:].strip()
        return raw_overlap.strip()

    def create_chunks(self, documents: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Splits documents respecting logical sections (Markdown headers # / ## / ###)
        or large paragraphs, ensuring tables and semantic blocks remain intact.
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

            # Split primarily by sub-headers (## or ###)
            sections = re.split(r'\n(?=#{2,3}\s)', text)

            for section in sections:
                section_text = section.strip()
                if not section_text:
                    continue

                # Prepend main document title context to section if not already present
                if main_title and not section_text.startswith("#"):
                    section_text = f"# {main_title}\n\n{section_text}"

                # If the section exceeds the maximum size, split by paragraphs
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
