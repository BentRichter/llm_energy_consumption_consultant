import pymupdf

ZOOM_FACTOR = 2.0


def pdf_to_images(pdf_bytes: bytes) -> list[bytes]:
    """Convert each page of a PDF to JPEG bytes."""
    doc = pymupdf.open(stream=pdf_bytes, filetype="pdf")
    images = []
    mat = pymupdf.Matrix(ZOOM_FACTOR, ZOOM_FACTOR)

    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("jpeg")
        images.append(img_bytes)

    doc.close()
    return images
