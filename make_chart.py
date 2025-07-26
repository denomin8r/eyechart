import os
from PIL import Image, ImageDraw, ImageFont
import logging
from generator import RandomGenerator


logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class EyeChart:
    CANVAS_WIDTH_MM = 297
    CANVAS_HEIGHT_MM = 418
    TABLE_WIDTH_MM = 173
    TABLE_START_X = (CANVAS_WIDTH_MM - TABLE_WIDTH_MM) / 2
    V_OFFSET_MM_RIGHT = 40
    D_OFFSET_MM_LEFT = 30
    INCREMENTAL_Y_OFFSETS = [
        20, 20, 23, 23,
        14, 23, 23, 23, 23, 23,
    ]
    V_VALUES = [
        0.075, 0.1, 0.2, 0.3,
        0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
    ]
    LINE_LENGTHS = [
        1, 2, 3, 4,
        5, 6, 6, 7, 7, 7,
    ]


def expand2square(image:Image.Image) -> Image.Image:
    width, height = image.size
    if width == height:
        return image
    elif width > height:
        result = Image.new(image.mode, (width, width), "white")
        result.paste(image, (0, (width - height) // 2))
        return result
    else:
        result = Image.new(image.mode, (height, height), "white")
        result.paste(image, ((height - width) // 2, 0))
        return result


def draw_symbol_d_degrees(image_main: Image.Image, font_obj,  dir_index:int) -> Image.Image:
    degrees = (dir_index * 90) % 360
    draw_main = ImageDraw.Draw(image_main)
    left, top, right, bottom = draw_main.textbbox(xy=(0, 0), font=font_obj, text="D")
    image_d = Image.new(mode='RGB', size=(int(right - left), int(bottom - top)), color='white')
    draw_d = ImageDraw.Draw(image_d)
    draw_d.text(xy=(0, -top), text="D", font=font_obj, fill='black')
    image_d = expand2square(image_d)
    image_d = image_d.rotate(angle=degrees, expand=1)
    return image_d


def save_image(image, filename):
    head, tail = os.path.split(filename)
    if head:
        if not os.path.exists(head):
            os.makedirs(head)
    image.save(filename)


def x_positions(num_symbols, symbol_w) -> list:
    """
    Return list of x_coordinates for the current line
    """
    FIXED_GAP = 20
    leftover_table_space = EyeChart.TABLE_WIDTH_MM - (symbol_w * num_symbols)
    gap_w = 0 if num_symbols == 1 else min(leftover_table_space / num_symbols - 1, FIXED_GAP)
    occupied_table_space = (num_symbols * symbol_w) + (gap_w * (num_symbols - 1))
    start_x = EyeChart.TABLE_START_X + ((EyeChart.TABLE_WIDTH_MM - occupied_table_space) / 2)
    return [(start_x + (k * (gap_w + symbol_w))) for k in range(num_symbols)]


def draw_symbols_to_canvas(image, im_width, im_height, symbol_generator):
    draw = ImageDraw.Draw(image)
    fontsize = int(4.2 / EyeChart.CANVAS_HEIGHT_MM * im_height)

    # https://stackoverflow.com/questions/43060479/how-to-get-the-font-pixel-height-using-pil-imagefont
    font = ImageFont.truetype(os.path.join('fonts', 'bookman.ttf'), fontsize)
    ascent, descent = font.getmetrics()

    y = 0
    for line_y_offset, num_symbols, line_v_value in zip(
            EyeChart.INCREMENTAL_Y_OFFSETS,
            EyeChart.LINE_LENGTHS,
            EyeChart.V_VALUES):
        # Get y coordinate for symbols in this line
        y += line_y_offset / EyeChart.CANVAS_HEIGHT_MM * im_height

        # Get the size of the symbols we are adding to this line
        # TODO fix how the size is set for writing symbols
        size = 7 / line_v_value
        font_obj = ImageFont.truetype(os.path.join('fonts', 'bookman.ttf'), size)

        # Make the symbols
        symbol_indices = symbol_generator.next_symbols(num_symbols)
        symbols = []
        for i in symbol_indices:
            symbols.append(draw_symbol_d_degrees(image, font_obj, i))

        symbol_w, symbol_h = symbols[0].size

        x_coords = x_positions(num_symbols, symbol_w)
        for x, sym in zip(x_coords, symbols):
            image.paste(sym, (int(x), int(y)))

        # TODO refactor all the rest to place D and V text
        d_text = ('D = %.1f' % (5.0 / line_v_value)).replace('.', ',')
        v_text = ('V = %.1f' % line_v_value).replace('.', ',')
        _, (_, d_offset_y) = font.font.getsize(d_text)
        _, (_, v_offset_y) = font.font.getsize(v_text)
        draw.text((EyeChart.D_OFFSET_MM_LEFT / EyeChart.CANVAS_WIDTH_MM * im_width,
                   y + size / 2 - (ascent - d_offset_y) / 2), d_text, (0, 0, 0), font=font)
        draw.text(((EyeChart.CANVAS_WIDTH_MM - EyeChart.V_OFFSET_MM_RIGHT) / EyeChart.CANVAS_WIDTH_MM * im_width,
                   y + size / 2 - (ascent - v_offset_y) / 2), v_text, (0, 0, 0), font=font)

        # TODO change how y_coord is adjusted
        y += symbol_h

    return image


def save(dpi=600, filename='sheet.png'):
    MM_PER_INCH = 25.4
    symbol_generator = RandomGenerator(n_symbols=4)

    width = int(EyeChart.CANVAS_WIDTH_MM * dpi / MM_PER_INCH)
    height = int(EyeChart.CANVAS_HEIGHT_MM * dpi / MM_PER_INCH)

    # Printing on a single page
    canvas = Image.new('RGB', (width, height), color="white")
    draw_symbols_to_canvas(canvas, width, height, symbol_generator)
    save_image(canvas, filename)
    print('File %s saved' % filename)
