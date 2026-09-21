"""Create a candidate Figure 1 without modifying the manuscript."""

from math import atan2, cos, pi, sin
from pathlib import Path
from reportlab.lib.colors import HexColor, white
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas

OUT = Path(__file__).resolve().parent / "figure1_preview"
OUT.mkdir(exist_ok=True)

INK = HexColor("#181818")
GRID = HexColor("#C5C5C5")
MID = HexColor("#777777")
ORANGE = HexColor("#D55E00")
PALE = HexColor("#F5F5F5")
ROW = HexColor("#ECECEC")
HEADER = HexColor("#D8D8D8")


def arrow(c, x1, y1, x2, y2, color=INK, width=1.3, head=7):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.line(x1, y1, x2, y2)
    angle = atan2(y2 - y1, x2 - x1)
    c.line(x2, y2, x2 + head * cos(angle + 2.55), y2 + head * sin(angle + 2.55))
    c.line(x2, y2, x2 + head * cos(angle - 2.55), y2 + head * sin(angle - 2.55))


def double_arrow(c, x1, y, x2):
    arrow(c, x1, y, x2, y, width=0.8, head=5)
    arrow(c, x2, y, x1, y, width=0.8, head=5)


def draw_geometry(c, x0, y0, width, height):
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x0, y0 + height - 12, "(a) Simulated geometry and source direction")

    plot_x, plot_y = x0 + 38, y0 + 35
    plot_w, plot_h = width - 55, height - 65
    xmin, xmax, ymin, ymax = -0.072, 0.082, -0.070, 0.071

    def px(v):
        return plot_x + (v - xmin) / (xmax - xmin) * plot_w

    def py(v):
        return plot_y + (v - ymin) / (ymax - ymin) * plot_h

    c.setStrokeColor(GRID)
    c.setLineWidth(0.45)
    xticks = [-0.05, -0.025, 0, 0.025, 0.05, 0.075]
    yticks = [-0.06, -0.04, -0.02, 0, 0.02, 0.04, 0.06]
    for value in xticks:
        c.line(px(value), plot_y, px(value), plot_y + plot_h)
    for value in yticks:
        c.line(plot_x, py(value), plot_x + plot_w, py(value))

    c.setStrokeColor(INK)
    c.setLineWidth(0.8)
    c.line(plot_x, plot_y, plot_x + plot_w, plot_y)
    c.line(plot_x, plot_y, plot_x, plot_y + plot_h)
    c.setFont("Helvetica", 7.5)
    for value in xticks:
        c.line(px(value), plot_y, px(value), plot_y - 3)
        c.drawCentredString(px(value), plot_y - 12, f"{value:.3f}" if value else "0.000")
    for value in yticks:
        c.line(plot_x - 3, py(value), plot_x, py(value))
        c.drawRightString(plot_x - 6, py(value) - 2.5, f"{value:.2f}" if value else "0.00")
    c.setFont("Helvetica", 8.5)
    c.drawCentredString(plot_x + plot_w / 2, plot_y - 24, "x (m)")
    c.saveState()
    c.translate(plot_x - 29, plot_y + plot_h / 2)
    c.rotate(90)
    c.drawCentredString(0, -3, "y (m)")
    c.restoreState()

    scale = min(plot_w / (xmax - xmin), plot_h / (ymax - ymin))
    cx, cy = px(0), py(0)
    c.setStrokeColor(INK)
    c.setLineWidth(1.05)
    c.circle(cx, cy, 0.05 * scale, stroke=1, fill=0)

    points = [(px(0.05 * cos(a * pi / 180)), py(0.05 * sin(a * pi / 180))) for a in [90, 210, 330]]
    path = c.beginPath()
    path.moveTo(*points[0])
    for point in points[1:] + points[:1]:
        path.lineTo(*point)
    c.setStrokeColor(HexColor("#333333"))
    c.drawPath(path, stroke=1, fill=0)

    c.setFillColor(INK)
    for index, (mx, my) in enumerate(points, start=1):
        c.circle(mx, my, 3.8, stroke=0, fill=1)
        c.setFont("Helvetica", 8.5)
        c.drawString(mx + 5, my + 2, f"M{index}")
    c.circle(cx, cy, 2.7, stroke=0, fill=1)

    c.setDash(3, 2)
    c.setLineWidth(0.8)
    c.line(cx, cy, points[0][0], points[0][1])
    c.setDash()
    c.setFillColor(white)
    c.rect(cx - 35, cy + 19, 54, 13, stroke=0, fill=1)
    c.setFillColor(INK)
    c.setFont("Helvetica", 8.2)
    c.drawString(cx - 31, cy + 22, "R = 5 cm")

    left, right = points[1], points[2]
    dim_y = py(-0.057)
    c.setStrokeColor(MID)
    c.setLineWidth(0.6)
    c.line(left[0], left[1], left[0], dim_y + 2)
    c.line(right[0], right[1], right[0], dim_y + 2)
    double_arrow(c, left[0], dim_y, right[0])
    c.setFillColor(INK)
    c.setFont("Helvetica", 7.8)
    c.drawCentredString((left[0] + right[0]) / 2, dim_y - 11, "pair spacing = 8.66 cm")

    # 37.37 degrees is one of the twelve tested directions. The true range is
    # 1.5 m, so the arrow is explicitly marked as schematic.
    theta = 37.37 * pi / 180
    ex, ey = px(0.073 * cos(theta)), py(0.073 * sin(theta))
    arrow(c, cx, cy, ex, ey, color=ORANGE, width=1.65, head=8)
    c.saveState()
    c.setFillColor(HexColor("#A84300"))
    c.setFont("Helvetica", 7.7)
    c.translate(px(0.026), py(0.030))
    c.rotate(37.37)
    c.drawString(0, 0, "source direction (schematic)")
    c.restoreState()


def draw_controls(c, x0, y0, width, height):
    c.setFillColor(INK)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(x0, y0 + height - 12, "(b) Matched simulation controls")

    table_x, table_y, table_w, row_h = x0 + 4, y0 + 67, width - 8, 34
    col = [0, 0.43, 0.715, 1.0]
    rows = [
        ("Category", "Condition 1", "Condition 2"),
        ("Arrival construction", "Fractional (F)", "Rounded (Q)"),
        ("Source history", "Steady (S)", "Onset (O)"),
        ("Propagation", "Direct (D)", "Reflected (R)"),
    ]
    for row_index, row in enumerate(rows):
        y = table_y + row_h * (3 - row_index)
        c.setFillColor(HEADER if row_index == 0 else (PALE if row_index % 2 else ROW))
        c.setStrokeColor(MID)
        c.setLineWidth(0.6)
        c.rect(table_x, y, table_w, row_h, stroke=1, fill=1)
        for boundary in col[1:-1]:
            c.line(table_x + table_w * boundary, y, table_x + table_w * boundary, y + row_h)
        c.setFillColor(INK)
        c.setFont("Helvetica-Bold" if row_index == 0 else "Helvetica", 8.5)
        for column_index, value in enumerate(row):
            c.drawString(table_x + table_w * col[column_index] + 7, y + 12, value)

    c.setFont("Helvetica", 8.2)
    c.drawCentredString(x0 + width / 2, y0 + 33, "Eight combinations share each source and noise record")


def draw_figure(c, x, y, width, height):
    left_width = width * 0.43
    gap = 18
    draw_geometry(c, x, y, left_width, height)
    draw_controls(c, x + left_width + gap, y, width - left_width - gap, height)


asset_path = OUT / "fig1_geometry_controls_candidate.pdf"
asset_width, asset_height = 540, 226
c = canvas.Canvas(str(asset_path), pagesize=(asset_width, asset_height))
draw_figure(c, 8, 4, asset_width - 16, asset_height - 8)
c.showPage()
c.save()

preview_path = OUT / "fig1_geometry_controls_preview.pdf"
page_width, page_height = 720, 430
c = canvas.Canvas(str(preview_path), pagesize=(page_width, page_height))
c.setFillColor(white)
c.rect(0, 0, page_width, page_height, stroke=0, fill=1)
draw_figure(c, 28, 158, page_width - 56, 242)
c.setFillColor(INK)
c.setFont("Times-Bold", 10)
c.drawString(28, 133, "Figure 1.")
caption = (
    "Microphone geometry and matched simulation controls. (a) Layout of the equilateral "
    "three-microphone array with circumradius R = 5 cm and inter-microphone spacing of 8.66 cm. "
    "The microphone coordinates are drawn to scale; the arrow shows one tested source azimuth "
    "and is not drawn to the 1.5 m source distance. (b) The three matched binary controls form "
    "eight combinations. Within each scene and recording, every combination uses identical source "
    "and microphone-noise samples. Onset denotes one source startup at the beginning of the complete recording."
)


def wrapped_lines(text, font, size, max_width):
    lines, current = [], []
    for word in text.split():
        proposed = " ".join(current + [word])
        if current and stringWidth(proposed, font, size) > max_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))
    return lines


c.setFont("Times-Roman", 10)
line_y = 133
prefix_width = stringWidth("Figure 1. ", "Times-Bold", 10)
for index, line in enumerate(wrapped_lines(caption, "Times-Roman", 10, page_width - 56)):
    if index == 0:
        c.drawString(28 + prefix_width, line_y, line)
    else:
        line_y -= 13
        c.drawString(28, line_y, line)
c.showPage()
c.save()

print(asset_path)
print(preview_path)
