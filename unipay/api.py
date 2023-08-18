import qrcode
import base64
import numpy as np

from typing import Optional
from pathlib import Path
from starlette import status
from pyzxing import BarCodeReader
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Request, Form, UploadFile
from fastapi.responses import RedirectResponse
from PIL import Image
from io import BytesIO
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates


from .db import get_unipay, add_unipay

ALIPAY_REGEX = r"^https://qr\.alipay\.com/[A-Za-z0-9]+"
WECHATPAY_REGEX = r"^wxp://[A-Za-z0-9\-]+"
BASE_PATH = Path(__file__).parent
MAX_SIZE = 10 * 1024 * 1024

app = FastAPI()
qr_reader = BarCodeReader()
app.mount("/assets", StaticFiles(directory=str(BASE_PATH / "assets")), name="assets")
templates = Jinja2Templates(directory=str(BASE_PATH / "templates"))


class Unipay(BaseModel):
    short_id: str
    alipay: str
    wechatpay: str
    scan_count: int


class UnipayCreate(BaseModel):
    alipay: str
    wechatpay: str


def generate_qr(data: str) -> str:
    """Generate a data URI for the given data using QR code."""
    img = qrcode.make(data)

    # Convert the image to PNG and then to a Data URI
    from io import BytesIO

    buffered = BytesIO()
    img.save(buffered)
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return f"data:image/png;base64,{img_str}"


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/{shortid}")
async def get_unipay_by_id(request: Request, shortid: str):
    unipay = get_unipay(shortid)

    if not unipay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unipay not found")

    user_agent = request.headers.get("User-Agent", "").lower()

    # If Alipay client, redirect to Alipay URL
    if "alipayclient" in user_agent:
        return RedirectResponse(url=str(unipay.alipay))

    alipay_qr = generate_qr(str(unipay.alipay))
    wechatpay_qr = generate_qr(str(unipay.wechatpay))

    # If WeChat client, show only WeChat QR code
    if "micromessenger" in user_agent:
        return templates.TemplateResponse("wechatpay.html", {"request": request, "wechatpay_qr": wechatpay_qr})

    # For other clients, show both QR codes
    return templates.TemplateResponse(
        "unipay.html", {"request": request, "alipay_qr": alipay_qr, "wechatpay_qr": wechatpay_qr}
    )


@app.post("/decode")
async def decode_qr(file: UploadFile):
    contents = await file.read()

    try:
        image = Image.open(BytesIO(contents))
        image_array = np.array(image)
        decoded = qr_reader.decode_array(image_array)
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image")

    decoded_data = [d["parsed"].decode("utf-8") for d in decoded if d]

    if decoded_data:
        return {"data": decoded_data}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No QR found in the uploaded image")


@app.post("/create")
async def create_unipay(
    alipay: str = Form(..., regex=ALIPAY_REGEX),
    wechatpay: str = Form(..., regex=WECHATPAY_REGEX),
    shortid: Optional[str] = Form(None, min_length=2, max_length=8, regex=r"^[A-Za-z0-9]+$"),
):
    unipay = add_unipay(alipay, wechatpay, shortid)
    return Unipay(
        short_id=str(unipay.short_id),
        alipay=str(unipay.alipay),
        wechatpay=str(unipay.wechatpay),
        scan_count=int(str(unipay.scan_count)),
    )
