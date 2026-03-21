import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, Http404


def serve_frontend(request, path=""):
    dist_dir = Path(settings.FRONTEND_DIST_DIR)
    if not dist_dir.exists():
        raise Http404("前端 dist 目录不存在")

    normalized_path = path.strip("/")
    requested_file = dist_dir / normalized_path if normalized_path else dist_dir / "index.html"

    if requested_file.exists() and requested_file.is_file():
        content_type, encoding = mimetypes.guess_type(requested_file.name)
        response = FileResponse(open(requested_file, "rb"), content_type=content_type)
        if encoding:
            response["Content-Encoding"] = encoding
        return response

    # Vue Router history 模式：非文件请求统一回退到 index.html
    if not normalized_path or "." not in Path(normalized_path).name:
        index_file = dist_dir / "index.html"
        if not index_file.exists():
            raise Http404("前端入口文件不存在")

        return FileResponse(open(index_file, "rb"), content_type="text/html; charset=utf-8")

    raise Http404("前端静态资源不存在")
