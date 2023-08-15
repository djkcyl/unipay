import qrcode
import base64


from pathlib import Path
from starlette import status
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File
from fastapi.responses import RedirectResponse
from pyzbar.pyzbar import decode
from PIL import Image
from io import BytesIO
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates


from .db import get_unipay, add_unipay

ALIPAY_REGEX = r"^https://qr\.alipay\.com/[A-Za-z0-9]+"
WECHATPAY_REGEX = r"^wxp://[A-Za-z0-9\-]+"
BASE_PATH = Path(__file__).parent

app = FastAPI()
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
async def decode_qr(file: UploadFile = File(...)):
    contents = await file.read()

    try:
        image = Image.open(BytesIO(contents))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid image")

    decoded = decode(image)
    decoded_data = [d.data.decode("utf-8") for d in decoded]

    if decoded_data:
        return {"data": decoded_data}
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No QR found in the uploaded image")


@app.post("/create")
async def create_unipay(alipay: str = Form(..., regex=ALIPAY_REGEX), wechatpay: str = Form(..., regex=WECHATPAY_REGEX)):
    unipay = add_unipay(alipay, wechatpay)
    return Unipay(
        short_id=str(unipay.short_id),
        alipay=str(unipay.alipay),
        wechatpay=str(unipay.wechatpay),
        scan_count=int(str(unipay.scan_count)),
    )
