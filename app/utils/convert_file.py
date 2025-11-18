from pdf2image import convert_from_path
import subprocess
import base64
import os
from ..ml.ocr import extract_question_from_image

def parse_document(path: str, tmp_dir: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".docx":
        pdf_path = docx_to_pdf(path, tmp_dir)
        image_paths = pdf_to_images(pdf_path, tmp_dir)
        return images_to_text(image_paths)

    elif ext == ".pdf":
        image_paths = pdf_to_images(path, tmp_dir)
        return images_to_text(image_paths)

    elif ext in ["jpeg","png"]:
        # 单张图片直接 OCR
        return extract_question_from_image(path)

    else:
        raise ValueError("Unsupported file format")


def docx_to_pdf(input_path, tmp_dir: str):
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    output_path = os.path.join(tmp_dir, base_name + ".pdf")
    soffice = r"C:\Program Files\LibreOffice\program\soffice.exe"
    cmd = [
        soffice,
        "--headless",
        "--convert-to", "pdf",
        "--outdir", tmp_dir,
        input_path
    ]
    subprocess.run(cmd, check=True)
    return output_path

def pdf_to_images(input_path, tmp_dir: str):
    poppler_path = r"D:\pooler\Release-24.08.0-0\poppler-24.08.0\Library\bin"
    images = convert_from_path(input_path, dpi=300, poppler_path=poppler_path)
    output_paths = []
    for i, image in enumerate(images):
        out = os.path.join(tmp_dir, f"page_{i}.png")
        image.save(out,"PNG")
        output_paths.append(out)
    return output_paths

def images_to_text(input_paths):
    results = []
    for page_path in input_paths:
        text = extract_question_from_image(page_path)
        results.append(text)
    final_text = "\n\n".join(results)
    return final_text