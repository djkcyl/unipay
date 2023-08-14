import qrcode
import base64

from pathlib import Path
from starlette import status
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from fastapi.templating import Jinja2Templates


from .db import get_unipay, add_unipay


app = FastAPI()
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


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
async def root():
    return {"message": "Hello World"}


from fastapi import Request


@app.get("/{shortid}")
async def get_unipay_by_id(request: Request, shortid: str):
    unipay = get_unipay(shortid)

    if not unipay:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unipay not found")

    user_agent = request.headers.get("User-Agent", "").lower()

    # If Alipay client, redirect to Alipay URL
    if "alipayclient" in user_agent:
        return RedirectResponse(url=unipay.alipay)

    alipay_qr = generate_qr(unipay.alipay)
    wechatpay_qr = generate_qr(unipay.wechatpay)

    # If WeChat client, show only WeChat QR code
    if "micromessenger" in user_agent:
        return templates.TemplateResponse("wechatpay.html", {"request": request, "wechatpay_qr": wechatpay_qr})

    # For other clients, show both QR codes
    return templates.TemplateResponse(
        "unipay.html", {"request": request, "alipay_qr": alipay_qr, "wechatpay_qr": wechatpay_qr}
    )


@app.put("/create")
async def create_unipay(unipay_req: UnipayCreate):
    unipay = add_unipay(unipay_req.alipay, unipay_req.wechatpay)
    return Unipay(
        short_id=unipay.short_id, alipay=unipay.alipay, wechatpay=unipay.wechatpay, scan_count=unipay.scan_count
    )
