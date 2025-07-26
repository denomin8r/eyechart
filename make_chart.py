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

    A4_WIDTH_MM = 297
    A4_HEIGHT_MM = 209
    MM_PER_INCH = 25.4
    TABLE_WIDTH = 173
    V_OFFSET_MM_RIGHT = 40
    D_OFFSET_MM_LEFT = 30
    INCREMENTAL_Y_OFFSETS = [
        20, 23, 23,
        14, 23, 23, 23, 23, 23,
    ]
    V_VALUES = [
        0.1, 0.2, 0.3,
        0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
    ]
    LINE_LENGTHS = [
        2, 3, 4,
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


def draw_d_degrees(image_main: Image.Image, x:int, y:int, size, degrees:int) -> None:
    draw_main = ImageDraw.Draw(image_main)

    font_d = ImageFont.truetype(os.path.join('fonts', 'bookman.ttf'), size)
    left, top, right, bottom = draw_main.textbbox(xy=(0, 0), font=font_d, text="D")
    image_d = Image.new(mode='RGB', size=(int(right - left), int(bottom - top)), color='white')
    draw_d = ImageDraw.Draw(image_d)
    draw_d.text(xy=(0, -top), text="D", font=font_d, fill='black')
    image_d = expand2square(image_d)

    image_d = image_d.rotate(angle=degrees, expand=1)
    image_main.paste(image_d, (x, y))


def draw_symbol(image: Image.Image, x, y, size, dir_index):
    degrees = (dir_index * 90) % 360
    draw_d_degrees(image, int(x), int(y), size, degrees=degrees)


def save_image(image, filename):
    head, tail = os.path.split(filename)
    if head:
        if not os.path.exists(head):
            os.makedirs(head)
    image.save(filename)


def draw_sheet(im_width, im_height, y_offsets, num_symbols_per_line, v_values_per_line, generator):
    image = Image.new('RGB', (im_width, im_height), color='white')
    draw = ImageDraw.Draw(image)

    fontsize = int(4.2 / EyeChart.A4_HEIGHT_MM * im_height)

    # https://stackoverflow.com/questions/43060479/how-to-get-the-font-pixel-height-using-pil-imagefont
    font = ImageFont.truetype(os.path.join('fonts', 'bookman.ttf'), fontsize)
    ascent, descent = font.getmetrics()

    y_coord = 0
    for line_y_offset, num_symbols, line_v_value in zip(y_offsets, num_symbols_per_line, v_values_per_line):
        y_coord += line_y_offset / EyeChart.A4_HEIGHT_MM * im_height
        x_coords, size = x_positions(num_symbols, im_width, im_height, line_v_value)
        line_symbols = generator.next_symbols(num_symbols)

        for x_coord, symbol in zip(x_coords, line_symbols):
            draw_symbol(image, x_coord, y_coord, size, symbol)

        d_text = ('D = %.1f' % (5.0 / line_v_value)).replace('.', ',')
        v_text = ('V = %.1f' % line_v_value).replace('.', ',')
        _, (_, d_offset_y) = font.font.getsize(d_text)
        _, (_, v_offset_y) = font.font.getsize(v_text)
        draw.text((EyeChart.D_OFFSET_MM_LEFT / EyeChart.A4_WIDTH_MM * im_width,
                   y_coord + size / 2 - (ascent - d_offset_y) / 2), d_text, (0, 0, 0), font=font)
        draw.text(((EyeChart.A4_WIDTH_MM - EyeChart.V_OFFSET_MM_RIGHT) / EyeChart.A4_WIDTH_MM * im_width,
                   y_coord + size / 2 - (ascent - v_offset_y) / 2), v_text, (0, 0, 0), font=font)

        y_coord += size

    return image


def draw_sheet_1(width, height, generator):
    return draw_sheet(im_width=width, im_height=height,
                      y_offsets=EyeChart.INCREMENTAL_Y_OFFSETS[:3],
                      num_symbols_per_line=EyeChart.LINE_LENGTHS[:3],
                      v_values_per_line=EyeChart.V_VALUES[:3],
                      generator=generator)

def draw_sheet_2(width, height, generator):
    return draw_sheet(width, height,
                      y_offsets=EyeChart.INCREMENTAL_Y_OFFSETS[3:9],
                      num_symbols_per_line=EyeChart.LINE_LENGTHS[3:9],
                      v_values_per_line=EyeChart.V_VALUES[3:9],
                      generator=generator)


def save(dpi=600, filename='sheet.png'):

    symbol_generator = RandomGenerator(n_symbols=4)

    width = int(EyeChart.A4_WIDTH_MM * dpi / EyeChart.MM_PER_INCH)
    height = int(EyeChart.A4_HEIGHT_MM * dpi / EyeChart.MM_PER_INCH)

    # Printing on a single page
    result = Image.new('RGB', (width, 2 * height))
    for i, method in enumerate([draw_sheet_1, draw_sheet_2]):
        image = method(width, height, symbol_generator)
        result.paste(im=image, box=(0, i * height))
    save_image(result, filename)
    print('File %s saved' % filename)


def x_positions(num_symbols, width, height, v):
    """
    :return:    x-coordinates, size
    """
    fontsize_multiplier = 1.7
    size = 7 / v
    space = (EyeChart.TABLE_WIDTH - num_symbols * size) / (num_symbols - 1)
    return [
        (((EyeChart.A4_WIDTH_MM - EyeChart.TABLE_WIDTH) / 2 + (size + space) * k) / EyeChart.A4_WIDTH_MM * width)
        for k in range(num_symbols)
    ], size / EyeChart.A4_HEIGHT_MM * height * fontsize_multiplier
