"""
Text extraction utilities for PDF and DOCX files.
"""
import os
from pathlib import Path
from typing import Optional
import pypdf
import docx2txt
from utils.config import settings

class TextExtractor:
    """Extract text from PDF and DOCX files."""
    
    @staticmethod
    def extract_from_pdf(file_path: str) -> dict:
        """
        Extract text from PDF file.
        Returns dict with 'text', 'page_count', and 'metadata'.
        """
        try:
            text_parts = []
            metadata = {}
            
            with open(file_path, 'rb') as file:
                pdf_reader = pypdf.PdfReader(file)
                page_count = len(pdf_reader.pages)
                
                # Extract metadata
                if pdf_reader.metadata:
                    metadata = {
                        'title': pdf_reader.metadata.get('/Title', ''),
                        'author': pdf_reader.metadata.get('/Author', ''),
                        'subject': pdf_reader.metadata.get('/Subject', ''),
                    }
                
                # Extract text from each page
                for page_num, page in enumerate(pdf_reader.pages, start=1):
                    try:
                        page_text = page.extract_text()
                        if page_text.strip():
                            text_parts.append(f"--- Page {page_num} ---\n{page_text}")
                    except Exception as e:
                        print(f"Error extracting text from page {page_num}: {e}")
                        continue
            
            full_text = "\n\n".join(text_parts)
            
            return {
                'text': full_text,
                'page_count': page_count,
                'metadata': metadata,
                'success': True
            }
        except Exception as e:
            return {
                'text': '',
                'page_count': 0,
                'metadata': {},
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def extract_from_docx(file_path: str) -> dict:
        """
        Extract text from DOCX file.
        Returns dict with 'text' and 'metadata'.
        """
        try:
            # Extract text using docx2txt
            text = docx2txt.process(file_path)
            
            # Try to get metadata using python-docx
            metadata = {}
            try:
                import docx
                doc = docx.Document(file_path)
                if doc.core_properties:
                    metadata = {
                        'title': doc.core_properties.title or '',
                        'author': doc.core_properties.author or '',
                        'subject': doc.core_properties.subject or '',
                    }
            except:
                pass
            
            return {
                'text': text,
                'page_count': None,  # DOCX doesn't have pages
                'metadata': metadata,
                'success': True
            }
        except Exception as e:
            return {
                'text': '',
                'page_count': None,
                'metadata': {},
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def extract_text(file_path: str, file_type: str) -> dict:
        """
        Extract text from file based on type.
        
        Args:
            file_path: Path to the file
            file_type: File extension (pdf, docx)
        
        Returns:
            dict with extracted text and metadata
        """
        file_type = file_type.lower().lstrip('.')
        
        if file_type == 'pdf':
            return TextExtractor.extract_from_pdf(file_path)
        elif file_type == 'docx':
            return TextExtractor.extract_from_docx(file_path)
        else:
            return {
                'text': '',
                'page_count': None,
                'metadata': {},
                'success': False,
                'error': f'Unsupported file type: {file_type}'
            }
    
    @staticmethod
    def clean_text(text: str) -> str:
        """
        Clean extracted text by removing excessive whitespace,
        normalizing line breaks, etc.
        """
        if not text:
            return ""
        
        # Remove excessive whitespace
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            cleaned_line = ' '.join(line.split())
            if cleaned_line:
                cleaned_lines.append(cleaned_line)
        
        return '\n'.join(cleaned_lines)

