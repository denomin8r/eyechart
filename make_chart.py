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

    def __init__(self):
        pass

    @staticmethod
    def draw_d_degrees(image_main, x, y, size, degrees):
        """

        :param Image.Image image_main:
        :param int x:
        :param int y:
        :param size:
        :param int degrees:
        :return None:
        """
        draw_main = ImageDraw.Draw(image_main)

        font_d = ImageFont.truetype(os.path.join('fonts', 'bookman.ttf'), size)
        left, top, right, bottom = draw_main.textbbox(xy=(0, 0), font=font_d, text="D")
        image_d = Image.new(mode='RGB', size=(int(right - left), int(bottom - top)), color='white')
        draw_d = ImageDraw.Draw(image_d)
        draw_d.text(xy=(0, -top), text="D", font=font_d, fill='black')

        image_d = image_d.rotate(angle=degrees, expand=1)
        image_main.paste(image_d, (x, y))

    @staticmethod
    def draw_symbol(image: Image.Image, x, y, size, dir_index):
        degrees = (dir_index * 90) % 360
        EyeChart.draw_d_degrees(image, int(x), int(y), size, degrees=degrees)

    # TODO adjust size and x-coords of letters
    @staticmethod
    def x_positions(n, width, height, v):
        size = 7 / v
        space = (EyeChart.TABLE_WIDTH - n * size) / (n - 1)
        return [
            (((EyeChart.A4_WIDTH_MM - EyeChart.TABLE_WIDTH) / 2 + (size + space) * k) / EyeChart.A4_WIDTH_MM * width)
            for k in range(n)
        ], size / EyeChart.A4_HEIGHT_MM * height

    @staticmethod
    def save_image(image, filename):
        head, tail = os.path.split(filename)
        if head:
            if not os.path.exists(head):
                os.makedirs(head)
        image.save(filename)

    def save(self, dpi=600, filename='sheet.png', single=False):

        generator = RandomGenerator(n_symbols=4, smart=True)

        width = int(EyeChart.A4_WIDTH_MM * dpi / EyeChart.MM_PER_INCH)
        height = int(EyeChart.A4_HEIGHT_MM * dpi / EyeChart.MM_PER_INCH)

        # Printing on a single page
        if single:
            result = Image.new('RGB', (width, 3 * height))
            for i, method in enumerate([self.draw_sheet_1, self.draw_sheet_2, self.draw_sheet_3]):
                image = method(width, height, generator)
                result.paste(im=image, box=(0, i * height))
            EyeChart.save_image(result, filename)
            print('File %s saved' % filename)
        else:
            file, ext = os.path.splitext(filename)
            assert ext, 'Filename should contain an extension'

            for i, method in enumerate([self.draw_sheet_1, self.draw_sheet_2, self.draw_sheet_3]):
                image = method(width, height, generator)
                image_name = '%s%d%s' % (file, i + 1, ext)
                EyeChart.save_image(image, image_name)
                print('File %s saved' % image_name)


    def draw_sheet(self, width, height, offsets, num_symbols_per_line, v_values_per_line, generator):

        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)

        fontsize = int(4.2 / EyeChart.A4_HEIGHT_MM * height)

        # https://stackoverflow.com/questions/43060479/how-to-get-the-font-pixel-height-using-pil-imagefont
        font = ImageFont.truetype(os.path.join('fonts', 'bookman.ttf'), fontsize)
        ascent, descent = font.getmetrics()

        y_coord = 0
        for offset, num_symbols, v_value in zip(offsets, num_symbols_per_line, v_values_per_line):
            y_coord += offset / EyeChart.A4_HEIGHT_MM * height
            x_coords, size = EyeChart.x_positions(num_symbols, width, height, v_value)
            line_symbols = generator.next_symbols(num_symbols)

            for x, symbol in zip(x_coords, line_symbols):
                self.draw_symbol(image, x, y_coord, size, symbol)

            d_text = ('D = %.1f' % (5.0 / v_value)).replace('.', ',')
            v_text = ('V = %.1f' % v_value).replace('.', ',')
            _, (_, d_offset_y) = font.font.getsize(d_text)
            _, (_, v_offset_y) = font.font.getsize(v_text)
            draw.text((EyeChart.D_OFFSET_MM_LEFT / EyeChart.A4_WIDTH_MM * width,
                       y_coord + size / 2 - (ascent - d_offset_y) / 2), d_text, (0, 0, 0), font=font)
            draw.text(((EyeChart.A4_WIDTH_MM - EyeChart.V_OFFSET_MM_RIGHT) / EyeChart.A4_WIDTH_MM * width,
                       y_coord + size / 2 - (ascent - v_offset_y) / 2), v_text, (0, 0, 0), font=font)

            y_coord += size

        return image

    def draw_sheet_1(self, width, height, generator):
        return self.draw_sheet(width=width, height=height,
                               offsets=self.offsets()[:3],
                               num_symbols_per_line=self.line_lengths()[:3],
                               v_values_per_line=self.v_values()[:3],
                               generator=generator)

    def draw_sheet_2(self, width, height, generator):
        return self.draw_sheet(width, height,
                               offsets=self.offsets()[3:9],
                               num_symbols_per_line=self.line_lengths()[3:9],
                               v_values_per_line=self.v_values()[3:9],
                               generator=generator)

    def draw_sheet_3(self, width, height, generator):
        lengths = self.line_lengths()[9:]
        image = self.draw_sheet(width, height,
                                offsets=self.offsets()[:len(lengths)],
                                num_symbols_per_line=lengths,
                                v_values_per_line=self.v_values()[:len(lengths)],
                                generator=generator)

        draw = ImageDraw.Draw(image)
        draw.rectangle(((1. / EyeChart.A4_WIDTH_MM * width, 28. / EyeChart.A4_HEIGHT_MM * height),
                        ((EyeChart.A4_WIDTH_MM - 6.) / EyeChart.A4_WIDTH_MM * width,
                         28.7 / EyeChart.A4_HEIGHT_MM * height)),
                       fill='black')
        draw.line(((1. / EyeChart.A4_WIDTH_MM * width, 98. / EyeChart.A4_HEIGHT_MM * height),
                   ((EyeChart.A4_WIDTH_MM - 6.) / EyeChart.A4_WIDTH_MM * width, 98. / EyeChart.A4_HEIGHT_MM * height)),
                  fill='black')

        return image

    # TODO what kind of offsets? Horizontal? Vertical?
    @staticmethod
    def offsets():
        return [
            20, 23, 23,
            14, 23, 23, 23, 23, 23,
            13, 23, 23, 36, 23, 23,
        ]

    @ staticmethod
    def standard_symbols():
        # Е=0, М=1, Э=2, Ш=3
        return [
            0, 3,  # Е Ш
            2, 1, 0,  # Э М Е
            1, 3, 0, 2,  # М Ш Е Э

            3, 2, 0, 1, 3,  # Ш Э Е М Ш
            2, 1, 0, 2, 1, 0,  # Э М Е Э М Е
            1, 3, 2, 3, 1, 3,  # М Ш Э Ш М Ш
            2, 0, 1, 3, 1, 0, 2,  # Э Е М Ш М Е Э
            3, 0, 3, 1, 0, 2, 3,  # Ш Е Ш М Е Э Ш
            1, 3, 2, 0, 2, 3, 0,  # М Ш Э Е Э Ш Е

            0, 1, 0, 2, 3, 1, 0, 2,  # Е М Е Э Ш М Е Э
            2, 1, 0, 2, 1, 0, 3, 1,  # Э М Е Э М Е Ш М
            1, 3, 2, 1, 3, 2, 0, 3   # М Ш Э М Ш Э Е Ш
        ]

    @staticmethod
    def v_values():
        return [
            0.1, 0.2, 0.3,
            0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
            1.0, 1.5, 2.0, 3.0, 4.0, 5.0,
        ]

    @staticmethod
    def line_lengths():
        return [2, 3, 4,
                5, 6, 6, 7, 7, 7,
                8, 8, 8]
