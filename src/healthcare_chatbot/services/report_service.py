import csv
import os

import PyPDF2
import docx

from healthcare_chatbot.utils.helpers import language_text, normalize_language, repair_mojibake
from healthcare_chatbot.services.ai_service import get_disease_prediction

def read_pdf(file_path):
    try:
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF: {str(e)}")
        return None


def read_docx(file_path):
    try:
        doc = docx.Document(file_path)
        text = ""
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
        return text
    except Exception as e:
        print(f"Error reading DOCX: {str(e)}")
        return None


def read_txt(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="latin-1") as file:
                return file.read()
        except Exception as e:
            print(f"Error reading TXT: {str(e)}")
            return None


def read_csv(file_path):
    try:
        text = []
        with open(file_path, "r", encoding="utf-8") as file:
            csv_reader = csv.reader(file)
            for row in csv_reader:
                text.append(", ".join(row))
        return "\n".join(text)
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="latin-1") as file:
                csv_reader = csv.reader(file)
                text = []
                for row in csv_reader:
                    text.append(", ".join(row))
                return "\n".join(text)
        except Exception as e:
            print(f"Error reading CSV: {str(e)}")
            return None


def read_report_file(file_path):
    readers = {
        ".pdf": read_pdf,
        ".doc": read_docx,
        ".docx": read_docx,
        ".txt": read_txt,
        ".csv": read_csv,
    }
    file_ext = os.path.splitext(file_path)[1].lower()
    reader = readers.get(file_ext)
    if not reader:
        return None
    return reader(file_path)


def process_lab_report(file_path, language="english"):
    language = normalize_language(language, "english")
    file_ext = os.path.splitext(file_path)[1].lower()
    if file_ext not in {".pdf", ".doc", ".docx", ".txt", ".csv"}:
        return "Unsupported file format. Please upload PDF, DOC, DOCX, TXT, or CSV files."

    report_content = read_report_file(file_path)
    if report_content is None:
        return "Error reading file. Please ensure the file is not corrupted and try again."

    prompt_templates = {
        "english": "This is a laboratory report. Please analyze deficiencies, explain them, and suggest diet improvements:\n\n{content}",
        "gujarati": "Aa laboratory report chhe. Krupaya khamio nu vishleshan karo, samjavo, ane aahar sambandhit salah aapo. Reply in Gujarati.\n\n{content}",
        "hindi": "Yeh laboratory report hai. Kripya kami ka vishleshan karein, samjhayen, aur aahar sambandhit salah dein. Reply in Hindi.\n\n{content}",
    }
    prompt = language_text(language, prompt_templates).format(content=report_content)
    return get_disease_prediction(repair_mojibake(prompt), language, is_lab_report=True)
