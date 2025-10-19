import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
import io
import numpy as np


def generate_bas_usage_chart(data: dict) -> bytes:
    labels = list(data.keys())
    sizes = list(data.values())

    
    colors = [
        '#004d99', 
        '#007acc', 
        '#00aaff',
        '#66ccff', 
        '#99e6ff',  
        '#cceeff',  
        '#f0f8ff',  
        '#ffffff'   
    ]

    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(8, 8))

    wedges, texts, autotexts = ax.pie(
        sizes, 
        labels=labels, 
        autopct='%1.1f%%',
        startangle=90,
        colors=colors[:len(labels)],
        wedgeprops=dict(width=0.3, edgecolor='w')
    )

    ax.set_title("Применение БАС", fontsize=16, fontweight='bold')

    ax.legend(wedges, labels, loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

    ax.axis('equal')

    buf = io.BytesIO()
    plt.savefig(buf, format='PNG', dpi=150, bbox_inches='tight')
    buf.seek(0)

    image_bytes = buf.getvalue()

    plt.close(fig)

    return image_bytes


from PIL import Image, ImageDraw, ImageFont
import io

def generate_flights_cards(flights_data: list) -> bytes:
    card_width = 300
    card_height = 180
    padding = 10
    cols = 2 
    rows = 3

    total_width = cols * (card_width + padding) - padding
    total_height = rows * (card_height + padding) - padding

    img = Image.new("RGB", (total_width, total_height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
        font_text = ImageFont.truetype("DejaVuSans.ttf", 12)
        font_small = ImageFont.truetype("DejaVuSans.ttf", 10)
    except OSError:
        try:
            font_title = ImageFont.truetype("Arial.ttf", 14)
            font_text = ImageFont.truetype("Arial.ttf", 12)
            font_small = ImageFont.truetype("Arial.ttf", 10)
        except OSError:
            font_title = ImageFont.load_default()
            font_text = ImageFont.load_default()
            font_small = ImageFont.load_default()

    card_bg = "#f5f5f5"
    text_color = "#333333"
    accent_color = "#007acc"

    for i, flight in enumerate(flights_data[:6]):  
        row = i // cols
        col = i % cols

        x = col * (card_width + padding)
        y = row * (card_height + padding)

        draw.rectangle(
            [x, y, x + card_width, y + card_height],
            fill=card_bg,
            outline="#dddddd",
            width=2
        )

        draw.text((x + 10, y + 10), flight["date"], fill=text_color, font=font_title)

        draw.text((x + 10, y + 35), "Вылет", fill=text_color, font=font_text)
        draw.text((x + 10, y + 50), flight["departure_time"], fill=text_color, font=font_small)

        draw.text((x + 100, y + 40), "→", fill=accent_color, font=font_title)

        draw.text((x + 140, y + 35), "Прилёт", fill=text_color, font=font_text)
        draw.text((x + 140, y + 50), flight["arrival_time"], fill=text_color, font=font_small)

        draw.text((x + 10, y + 80), flight["duration"], fill=text_color, font=font_text)

    
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_regions_table(regions_data: list) -> bytes:

    header_height = 40
    row_height = 50
    padding = 10
    cols = 6 
    rows = len(regions_data) + 1  

    col_widths = [180, 100, 120, 100, 120, 80] 

    total_width = sum(col_widths) + (cols - 1) * padding
    total_height = header_height + rows * row_height

    img = Image.new("RGB", (total_width, total_height), "white")
    draw = ImageDraw.Draw(img)

    try:
        font_header = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
        font_row = ImageFont.truetype("DejaVuSans.ttf", 12)
    except IOError:
        font_header = ImageFont.load_default()
        font_row = ImageFont.load_default()

    header_bg = "#f0f0f0"
    row_bg_1 = "#ffffff"
    row_bg_2 = "#f8f8f8"

    headers = ["Регион", "Полёты", "Длительность (ч)", "Ср. Время", "Рост", "Плотность"]

    x = 0
    for i, header in enumerate(headers):
        draw.rectangle(
            [x, 0, x + col_widths[i], header_height],
            fill=header_bg,
            outline="#cccccc"
        )
        draw.text((x + 5, 10), header, fill="black", font=font_header)
        x += col_widths[i] + padding

    y = header_height
    for i, region in enumerate(regions_data):
        bg_color = row_bg_1 if i % 2 == 0 else row_bg_2

        x = 0
        for j, col_name in enumerate(headers):
            draw.rectangle(
                [x, y, x + col_widths[j], y + row_height],
                fill=bg_color,
                outline="#dddddd"
            )

            value = ""
            if col_name == "Регион":
                value = f"#{region['rank']} {region['name']}"
            elif col_name == "Полёты":
                value = str(region.get('flights', '—'))
            elif col_name == "Длительность (ч)":
                value = str(region.get('duration_hours', '—'))
            elif col_name == "Ср. Время":
                value = region.get('avg_time', '—')
            elif col_name == "Рост":
                growth = region.get('growth', '—')
                color = "green" if "+" in str(growth) else "red" if "-" in str(growth) else "black"
                draw.text((x + 5, y + 15), growth, fill=color, font=font_row)
                x += col_widths[j] + padding
                continue
            elif col_name == "Плотность":
                value = str(region.get('density', '—'))

            draw.text((x + 5, y + 15), value, fill="black", font=font_row)
            x += col_widths[j] + padding

        y += row_height

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def generate_flights_trend_chart(data: list, stats: dict) -> bytes:
    dates = [item["date"] for item in data]
    flights = [item["flights"] for item in data]

    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(10, 6))

    line_color = '#007acc'     
    fill_color = '#e6f2ff'     
    bg_color = 'white'

    ax.plot(dates, flights, color=line_color, linewidth=2)
    ax.fill_between(dates, flights, color=fill_color, alpha=0.8)

 
    ax.grid(True, linestyle='--', alpha=0.5)


    ax.set_title("Динамика полётов", fontsize=16, fontweight='bold', color='#333333')
    ax.set_ylabel("Количество полётов", fontsize=12, color='#333333')
    ax.set_xticks(ax.get_xticks()[::5])
   
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)


    ax.set_facecolor(bg_color)
    ax.text(0.95, 0.95, "За месяц", transform=ax.transAxes,
            fontsize=10, ha='right', va='top', color='#666666',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor='lightgray'))


    buf = io.BytesIO()
    plt.savefig(buf, format='PNG', dpi=150, bbox_inches='tight')
    plt.close(fig)

    chart_img = Image.open(buf)
    width, height = chart_img.size

    card_height = 120
    total_height = height + card_height + 20 
    final_img = Image.new("RGB", (width, total_height), "white")
    final_img.paste(chart_img, (0, 0))

    draw = ImageDraw.Draw(final_img)

    try:
        font_title = ImageFont.truetype("DejaVuSans-Bold.ttf", 14)
        font_value = ImageFont.truetype("DejaVuSans.ttf", 32)
        font_unit = ImageFont.truetype("DejaVuSans.ttf", 16)
    except:
        font_title = ImageFont.load_default()
        font_value = ImageFont.load_default()
        font_unit = ImageFont.load_default()

    card_width = width // 3
    y_pos = height + 10

    cards = [
        ("Среднее время", str(stats.get("avg_time", "—")), "мин"),
        ("Соотношение\nроста к падению", str(stats.get("growth_ratio", "—")), ""),
        ("Общее число\nполётов", str(stats.get("total_flights", "—")), "")
    ]

    for i, (title, value, unit) in enumerate(cards):
        x_pos = i * card_width
        draw.rectangle(
            [x_pos, y_pos, x_pos + card_width - 10, y_pos + card_height],
            outline="#dddddd",
            fill="white"
        )
        draw.text((x_pos + 20, y_pos + 20), title, fill="#333333", font=font_title)
        draw.text((x_pos + 20, y_pos + 60), value, fill="#007acc", font=font_value)
        if unit:
            draw.text((x_pos + 20 + 50, y_pos + 60), unit, fill="#666666", font=font_unit)

    buf_final = io.BytesIO()
    final_img.save(buf_final, format="PNG")
    return buf_final.getvalue()