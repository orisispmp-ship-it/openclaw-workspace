#!/usr/bin/env python3
"""PDF Compressor - 용량은 줄이고 화질은 유지"""

import os
import threading
import uuid
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

import fitz  # PyMuPDF

app = Flask(__name__)

BASE_DIR = Path(__file__).parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

JOBS: dict[str, dict] = {}  # job_id -> { status, progress, ... }

# ── Allowed extensions ──────────────────────────────────────────
ALLOWED = {".pdf"}

def _allowed_file(name: str) -> bool:
    return Path(name).suffix.lower() in ALLOWED

def _human_size(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    elif n < 1024 * 1024:
        return f"{n / 1024:.1f} KB"
    elif n < 1024 * 1024 * 1024:
        return f"{n / 1024 / 1024:.1f} MB"
    return f"{n / 1024 / 1024 / 1024:.2f} GB"

# ── Compression engine ─────────────────────────────────────────
def _count_images(doc: fitz.Document) -> int:
    """Count unique image xrefs in the document."""
    seen = set()
    for i in range(doc.page_count):
        for img in doc.get_page_images(i):
            seen.add(img[0])
    return len(seen)


def _compress_pdf_job(job_id: str, src: Path, quality: str):
    """Run compression in a background thread, updating JOBS[job_id]."""
    dst = OUTPUT_DIR / f"{job_id}_compressed.pdf"
    orig_size = src.stat().st_size
    try:
        job = JOBS[job_id]
        job["status"] = "processing"
        job["progress"] = 0
        job["message"] = "PDF 열기..."

        doc = fitz.open(str(src))
        total = doc.page_count
        if total == 0:
            raise ValueError("PDF에 페이지가 없습니다.")

        img_count_before = _count_images(doc)

        # Quality settings
        quality_map = {
            "high":   (85, 300),    # (quality, dpi_threshold)
            "medium": (70, 200),    # ⭐ default
            "low":    (55, 150),
            "verylow":(35, 100),
        }
        quality_val, dpi_thresh = quality_map.get(quality, (70, 200))

        # ── Step 1: Rewrite images ─────────────────────────
        job["progress"] = 10
        job["message"] = "이미지 재압축 중..."

        # rewrite_images handles DPI-based downscaling + JPEG recompression
        doc.rewrite_images(
            dpi_threshold=dpi_thresh,   # images above this DPI get processed
            quality=quality_val,         # JPEG quality 0-100
            lossy=True,
            lossless=True,
            bitonal=True,
            color=True,
            gray=True,
        )

        # ── Step 2: Save with full compression ─────────────
        job["progress"] = 70
        job["message"] = "파일 저장 중..."

        doc.save(
            str(dst),
            garbage=4,             # aggressive unused-object removal
            deflate=True,          # compress all streams
            clean=True,            # clean/sanitize
            pretty=False,
            incremental=False,
        )
        doc.close()

        new_size = dst.stat().st_size
        ratio = (1 - new_size / orig_size) * 100 if orig_size else 0

        JOBS[job_id].update({
            "status": "done",
            "progress": 100,
            "message": f"완료!",
            "output_name": dst.name,
            "output_size": new_size,
            "output_size_hr": _human_size(new_size),
            "orig_size": orig_size,
            "orig_size_hr": _human_size(orig_size),
            "ratio": round(ratio, 1),
            "quality": quality,
        })
    except Exception as e:
        import traceback
        JOBS[job_id].update({
            "status": "error",
            "message": str(e),
        })
        # Clean up partial output
        if dst.exists():
            dst.unlink()


# ── Routes ──────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory(str(BASE_DIR), "index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    """Upload PDF → start compression job → return job_id."""
    if "file" not in request.files:
        return jsonify({"error": "파일이 없습니다."}), 400
    f = request.files["file"]
    if not f.filename or not _allowed_file(f.filename):
        return jsonify({"error": "PDF 파일만 업로드 가능합니다."}), 400

    quality = request.form.get("quality", "medium")
    if quality not in ("high", "medium", "low", "verylow"):
        quality = "medium"

    job_id = uuid.uuid4().hex[:12]
    src = UPLOAD_DIR / f"{job_id}.pdf"
    f.save(str(src))

    orig_size = src.stat().st_size
    JOBS[job_id] = {
        "status": "queued",
        "progress": 0,
        "message": "대기 중...",
        "orig_name": f.filename,
        "orig_size": orig_size,
        "orig_size_hr": _human_size(orig_size),
        "quality": quality,
    }

    # Start in background thread
    t = threading.Thread(
        target=_compress_pdf_job,
        args=(job_id, src, quality),
        daemon=True,
    )
    t.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def status(job_id: str):
    job = JOBS.get(job_id)
    if job is None:
        return jsonify({"error": "알 수 없는 작업 ID"}), 404
    return jsonify(job)


@app.route("/api/download/<job_id>")
def download(job_id: str):
    job = JOBS.get(job_id)
    if job is None or job["status"] != "done":
        return jsonify({"error": "다운로드할 수 없습니다."}), 404
    out_name = job.get("output_name")
    if not out_name:
        return jsonify({"error": "출력 파일 없음"}), 404
    return send_from_directory(
        str(OUTPUT_DIR),
        out_name,
        as_attachment=True,
        download_name=job.get("orig_name", "compressed.pdf").replace(".pdf", "_compressed.pdf"),
    )


@app.route("/api/clear/<job_id>", methods=["POST"])
def clear_job(job_id: str):
    """작업 정보만 삭제. 원본과 결과물은 파일로 남깁니다."""
    JOBS.pop(job_id, None)
    return jsonify({"ok": True})


# ── Run ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    import webbrowser
    port = 5000
    print(f"PDF Compressor 실행 중 → http://127.0.0.1:{port}")
    webbrowser.open(f"http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
