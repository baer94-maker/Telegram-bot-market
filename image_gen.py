import io
import httpx
from PIL import Image, ImageDraw, ImageFont

FONT_BOLD = "/system/fonts/NotoSerif-Bold.ttf"
FONT_REGULAR = "/system/fonts/NotoSerif-Regular.ttf"
WIDTH = 1000
HEIGHT = 1000


def _load_font(size: int, bold: bool = True):
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def _parse_card(card_text: str) -> dict:
    result = {"title": "", "utp": "", "advantages": []}
    lines = card_text.split("\n")
    current_section = None

    for line in lines:
        line = line.strip()
        if not line:
            continue
        if "НАЗВАНИЕ" in line:
            current_section = "title"
            continue
        elif "УНИКАЛЬНОЕ" in line or "УТП" in line:
            current_section = "utp"
            continue
        elif "ПРЕИМУЩЕСТВА" in line:
            current_section = "advantages"
            continue
        elif any(x in line for x in ["ОПИСАНИЕ", "SEO", "СЛАЙД", "ФОТО", "КОНЕЦ", "==="]):
            current_section = None
            continue

        if current_section == "title" and not result["title"]:
            result["title"] = line
        elif current_section == "utp" and not result["utp"]:
            result["utp"] = line
        elif current_section == "advantages":
            clean = line.lstrip("•-– ").strip()
            if clean and len(result["advantages"]) < 4:
                result["advantages"].append(clean)

    return result


def _wrap_text(text: str, font, max_width: int, draw: ImageDraw.ImageDraw) -> list:
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if bbox[2] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def _shadow(draw, text, x, y, font, fill):
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0))
    draw.text((x, y), text, font=font, fill=fill)


async def download_photo(bot_token: str, file_id: str):
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://api.telegram.org/bot{bot_token}/getFile",
                params={"file_id": file_id},
            )
            resp.raise_for_status()
            file_path = resp.json()["result"]["file_path"]
            resp2 = await client.get(
                f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
            )
            resp2.raise_for_status()
            return resp2.content
    except Exception as e:
        print(f"Ошибка скачивания фото: {e}")
        return None


def generate_slide_image(card_text: str, photo_bytes=None) -> bytes:
    data = _parse_card(card_text)

    # --- Фон ---
    if photo_bytes:
        try:
            product_img = Image.open(io.BytesIO(photo_bytes)).convert("RGB")
            img_w, img_h = product_img.size
            scale = max(WIDTH / img_w, HEIGHT / img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            product_img = product_img.resize((new_w, new_h), Image.LANCZOS)
            left = (new_w - WIDTH) // 2
            top = (new_h - HEIGHT) // 2
            product_img = product_img.crop(
                (left, top, left + WIDTH, top + HEIGHT)
            )
            img = product_img.copy().convert("RGBA")
        except Exception:
            img = Image.new("RGBA", (WIDTH, HEIGHT), (15, 15, 40, 255))
    else:
        img = Image.new("RGBA", (WIDTH, HEIGHT), (15, 15, 40, 255))

    # --- Градиент сверху ---
    top_overlay = Image.new("RGBA", (WIDTH, 220), (0, 0, 0, 0))
    d = ImageDraw.Draw(top_overlay)
    for y in range(220):
        alpha = int(210 * (1 - y / 220))
        d.line([(0, y), (WIDTH, y)], fill=(0, 0, 20, alpha))
    img.alpha_composite(top_overlay, (0, 0))

    # --- Градиент снизу ---
    bottom_h = 530
    bottom_overlay = Image.new("RGBA", (WIDTH, bottom_h), (0, 0, 0, 0))
    d2 = ImageDraw.Draw(bottom_overlay)
    for y in range(bottom_h):
        alpha = int(245 * (y / bottom_h))
        d2.line([(0, y), (WIDTH, y)], fill=(0, 0, 20, alpha))
    img.alpha_composite(bottom_overlay, (0, HEIGHT - bottom_h))

    img = img.convert("RGB")
    draw = ImageDraw.Draw(img)

    MARGIN = 50
    TEXT_WIDTH = WIDTH - MARGIN * 2

    font_title = _load_font(44, bold=True)
    font_label = _load_font(24, bold=True)
    font_utp = _load_font(28, bold=False)
    font_adv = _load_font(26, bold=False)
    font_badge = _load_font(20, bold=False)

    # --- НАЗВАНИЕ вверху ---
    title = data["title"] or "Название товара"
    title_lines = _wrap_text(title, font_title, TEXT_WIDTH, draw)
    y = 28
    for line in title_lines[:2]:
        _shadow(draw, line, MARGIN, y, font_title, fill=(255, 225, 50))
        bbox = draw.textbbox((MARGIN, y), line, font=font_title)
        y += (bbox[3] - bbox[1]) + 8

    # --- Жёлтая линия ---
    y_sep = HEIGHT - 510
    draw.rectangle(
        [(MARGIN, y_sep), (WIDTH - MARGIN, y_sep + 3)],
        fill=(255, 200, 0)
    )

    # --- УТП ---
    y = y_sep + 18
    draw.text((MARGIN, y), "УТП", font=font_label, fill=(255, 200, 0))
    y += 34

    utp = data["utp"] or "Уникальное торговое предложение"
    if len(utp) > 150:
        utp = utp[:147] + "..."
    for line in _wrap_text(utp, font_utp, TEXT_WIDTH, draw)[:3]:
        _shadow(draw, line, MARGIN, y, font_utp, fill=(210, 210, 255))
        bbox = draw.textbbox((MARGIN, y), line, font=font_utp)
        y += (bbox[3] - bbox[1]) + 6
    y += 18

    # --- Разделитель ---
    draw.rectangle(
        [(MARGIN, y), (WIDTH - MARGIN, y + 1)],
        fill=(80, 80, 160)
    )
    y += 16

    # --- ПРЕИМУЩЕСТВА ---
    draw.text((MARGIN, y), "Преимущества", font=font_label, fill=(100, 255, 150))
    y += 34

    advantages = data["advantages"]
    if not advantages:
        advantages = ["Высокое качество", "Удобство использования", "Отличная цена"]

    for adv in advantages[:4]:
        if y > 945:
            break
        if len(adv) > 80:
            adv = adv[:77] + "..."
        for line in _wrap_text(f"• {adv}", font_adv, TEXT_WIDTH, draw)[:2]:
            _shadow(draw, line, MARGIN, y, font_adv, fill=(200, 255, 215))
            bbox = draw.textbbox((MARGIN, y), line, font=font_adv)
            y += (bbox[3] - bbox[1]) + 4
        y += 8

    # --- Бейдж ---
    badge = "Marketplace Card Bot"
    b_bbox = draw.textbbox((0, 0), badge, font=font_badge)
    bw = b_bbox[2] + 20
    bh = b_bbox[3] + 10
    bx = WIDTH - bw - 16
    by = HEIGHT - bh - 12
    draw.rectangle([bx, by, bx + bw, by + bh], fill=(0, 0, 0))
    draw.text((bx + 10, by + 5), badge, font=font_badge, fill=(130, 130, 190))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.getvalue()