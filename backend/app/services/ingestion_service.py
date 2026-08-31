import os
import glob
import re
from typing import List, Dict, Any

class IngestionService:
    """
    Servicio encargado de la lectura, fragmentación (chunking con solapamiento) 
    e ingesta de los documentos de conocimiento del negocio.
    """

    def __init__(self, data_dir: str, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Inicializa el servicio de ingesta.
        :param data_dir: Directorio donde se encuentran los archivos .md del negocio.
        :param chunk_size: Tamaño máximo deseado de caracteres por fragmento.
        :param chunk_overlap: Cantidad de caracteres de solapamiento entre fragmentos.
        """
        self.data_dir = data_dir
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def load_documents(self) -> List[Dict[str, str]]:
        """
        Lee todos los archivos Markdown (.md) presentes en el directorio data_dir.
        :return: Lista de diccionarios conteniendo 'source' (nombre del archivo) y 'content'.
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

    def create_chunks(self, documents: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """
        Fragmenta los documentos respetando secciones lógicas (encabezados de Markdown # / ## / ###)
        o párrafos grandes, asegurando que tablas y bloques semánticos se mantengan íntegros.
        :param documents: Documentos cargados.
        :return: Lista de fragmentos estructurados con texto y metadatos.
        """
        chunks = []
        chunk_counter = 0

        for doc in documents:
            text = doc["content"]
            source = doc["source"]

            # Dividir principalmente por encabezados Markdown (## o #)
            sections = re.split(r'\n(?=#{1,3}\s)', text)
            
            for section in sections:
                section_text = section.strip()
                if not section_text:
                    continue

                # Si la sección excede el tamaño máximo, dividir por párrafos
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
                                overlap = sub_chunk[-self.chunk_overlap:] if len(sub_chunk) > self.chunk_overlap else sub_chunk
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
