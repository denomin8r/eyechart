import numpy as np
import os
from PIL import Image, ImageDraw, ImageFont
from abc import abstractmethod

from generator import RandomGenerator, SequenceGenerator


class EyeChart:

    A4_WIDTH_MM = 297
    A4_HEIGHT_MM = 209
    MM_PER_INCH = 25.4
    TABLE_WIDTH = 173
    V_OFFSET_MM_RIGHT = 40
    D_OFFSET_MM_LEFT = 30

    @abstractmethod
    def symbol_renderers(self):
        pass

    @abstractmethod
    def standard_symbols(self):
        pass

    @abstractmethod
    def line_lengths(self):
        pass

    @staticmethod
    def v_values():
        return [
            0.1, 0.2, 0.3,
            0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
            1.0, 1.5, 2.0, 3.0, 4.0, 5.0,
        ]

    def draw_symbol(self, image: Image.Image, x:int, y:int, size, symbol):

        self.symbol_renderers()[symbol](image, x, y, size)

    @staticmethod
    def x_positions(n, width, height, v):
        size = 7 / v
        space = (EyeChart.TABLE_WIDTH - n * size) / (n - 1)
        return [
            (((EyeChart.A4_WIDTH_MM - EyeChart.TABLE_WIDTH) / 2 + (size + space) * k) / EyeChart.A4_WIDTH_MM * width)
            for k in range(n)
        ], size / EyeChart.A4_HEIGHT_MM * height

    def symbol_generator(self, generator_name):
        """
        Returns a Generator that yields successive symbols to print to the eyechar.

        :param str generator_name:
        :return:
        """
        if 'standard' == generator_name:
            return SequenceGenerator(sequence=self.standard_symbols())
        elif 'shifted' == generator_name:
            global_shift = np.random.randint(0, len(self.standard_symbols()), 1)[0]
            return SequenceGenerator(sequence=self.standard_symbols(), global_shift=global_shift)
        elif 'global_shuffle' == generator_name:
            return SequenceGenerator(sequence=self.standard_symbols(), shuffle='global')
        elif 'line_shuffle' == generator_name:
            return SequenceGenerator(sequence=self.standard_symbols(), shuffle='line')
        elif 'shifted_line_shuffle' == generator_name:
            global_shift = np.random.randint(0, len(self.standard_symbols()), 1)[0]
            return SequenceGenerator(sequence=self.standard_symbols(), global_shift=global_shift, shuffle='line')
        elif 'random' == generator_name:
            return RandomGenerator(n_symbols=len(self.symbol_renderers()))
        elif 'smart_random' == generator_name:
            return RandomGenerator(n_symbols=len(self.symbol_renderers()), smart=True)
        else:
            raise NotImplementedError(generator_name)

    def draw_sheet(self, width, height, offsets, ns, vs, generator):

        image = Image.new('RGB', (width, height), color='white')
        draw = ImageDraw.Draw(image)

        fontsize = int(4.2 / EyeChart.A4_HEIGHT_MM * height)

        # https://stackoverflow.com/questions/43060479/how-to-get-the-font-pixel-height-using-pil-imagefont
        font = ImageFont.truetype(os.path.join('fonts', 'bookman.ttf'), fontsize)
        ascent, descent = font.getmetrics()

        y_coord = 0
        for offset, n, v in zip(offsets, ns, vs):
            y_coord += offset / EyeChart.A4_HEIGHT_MM * height
            x_coords, size = EyeChart.x_positions(n, width, height, v)
            symbols = generator.next_symbols(n)
            for x, symbol in zip(x_coords, symbols):
                self.draw_symbol(image, x, y_coord, size, symbol)

            if symbols:
                d_text = ('D = %.1f' % (5.0 / v)).replace('.', ',')
                v_text = ('V = %.1f' % v).replace('.', ',')
                _, (_, d_offset_y) = font.font.getsize(d_text)
                _, (_, v_offset_y) = font.font.getsize(v_text)
                draw.text((EyeChart.D_OFFSET_MM_LEFT / EyeChart.A4_WIDTH_MM * width,
                           y_coord + size / 2 - (ascent - d_offset_y) / 2), d_text, (0, 0, 0), font=font)
                draw.text(((EyeChart.A4_WIDTH_MM - EyeChart.V_OFFSET_MM_RIGHT) / EyeChart.A4_WIDTH_MM * width,
                           y_coord + size / 2 - (ascent - v_offset_y) / 2), v_text, (0, 0, 0), font=font)

            y_coord += size

        return image

    def draw_sheet_1(self, width, height, generator):
        return self.draw_sheet(width=width, height=height, offsets=[20, 23, 23],
                               ns=self.line_lengths()[:3], vs=self.v_values()[:3], generator=generator)

    def draw_sheet_2(self, width, height, generator):
        return self.draw_sheet(width, height, [14, 23, 23, 23, 23, 23],
                               self.line_lengths()[3:9], vs=self.v_values()[3:9], generator=generator)

    def draw_sheet_3(self, width, height, generator):
        lengths = self.line_lengths()[9:]
        image = self.draw_sheet(width, height, [13, 23, 23, 36, 23, 23][:len(lengths)],
                                ns=lengths, vs=self.v_values()[:len(lengths)], generator=generator)

        draw = ImageDraw.Draw(image)
        draw.rectangle(((1. / EyeChart.A4_WIDTH_MM * width, 28. / EyeChart.A4_HEIGHT_MM * height),
                        ((EyeChart.A4_WIDTH_MM - 6.) / EyeChart.A4_WIDTH_MM * width,
                         28.7 / EyeChart.A4_HEIGHT_MM * height)),
                       fill='black')
        draw.line(((1. / EyeChart.A4_WIDTH_MM * width, 98. / EyeChart.A4_HEIGHT_MM * height),
                   ((EyeChart.A4_WIDTH_MM - 6.) / EyeChart.A4_WIDTH_MM * width, 98. / EyeChart.A4_HEIGHT_MM * height)),
                  fill='black')

        return image

    @staticmethod
    def save_image(image, filename):
        head, tail = os.path.split(filename)
        if head:
            if not os.path.exists(head):
                os.makedirs(head)
        image.save(filename)

    def save(self, generator_name, dpi=600, filename='sheet.png', single=False):

        generator = self.symbol_generator(generator_name)

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


def fix_coords(tup1, tup2):
    x1, y1 = tup1
    x2, y2 = tup2
    min_coord = (min(x1, x2), min(y1, y2))
    max_coord = (max(x1, x2), max(y1, y2))
    return min_coord, max_coord


class DChart(EyeChart):

    @staticmethod
    def draw_d(image:Image.Image, x, y, size):
        font = ImageFont.truetype(os.path.join('fonts', 'bookman.ttf'), size)
        draw = ImageDraw.Draw(image)
        draw.text(xy=(x, y), text="D", fill='black', font=font)

    @staticmethod
    def draw_d_turn_cw(image_main:Image.Image, x, y, size):
        x, y = int(x), int(y)
        font = ImageFont.truetype(os.path.join('fonts', 'bookman.ttf'), size)
        draw = ImageDraw.Draw(image_main)
        left, top, right, bottom = draw.textbbox(xy=(x, 0), font=font, text='D')
        d_image = Image.new('RGB', (int(right - left), int(bottom - top)), color='white')
        d_draw = ImageDraw.Draw(d_image)
        d_draw.text(xy=(0,0), text="D", font=font, fill='black')
        d_image.rotate(90, expand=1)
        image_main.paste(d_image, (x, y))

    @staticmethod
    def draw_d_upside_down(draw, x, y, size):
        width = size / 5
        draw.rectangle(fix_coords((x + size - width, y), (x + size, y + size)), fill='black')
        draw.rectangle(fix_coords((x, y), (x + size - width, y + width)), fill='black')
        draw.rectangle(fix_coords((x, y + 2 * width), (x + size - width, y + 3 * width)), fill='black')
        draw.rectangle(fix_coords((x, y + 4 * width), (x + size - width, y + size)), fill='black')

    @staticmethod
    def draw_d_turn_ccw(draw, x, y, size):
        width = size / 5
        draw.rectangle(fix_coords((x, y + size), (x + size, y + size - width)), fill='black')
        draw.rectangle(fix_coords((x, y + size - width), (x + width, y)), fill='black')
        draw.rectangle(fix_coords((x + 2 * width, y + size - width), (x + 3 * width, y)), fill='black')
        draw.rectangle(fix_coords((x + 4 * width, y + size - width), (x + size, y)), fill='black')

    def symbol_renderers(self):
        return [DChart.draw_d,
                DChart.draw_d_turn_cw,
                DChart.draw_d_turn_ccw,
                DChart.draw_d_upside_down]

    def standard_symbols(self):
        # Е=0, М=1, Э=2, Ш=3
        return [0, 3,                       # Е Ш
                2, 1, 0,                    # Э М Е
                1, 3, 0, 2,                 # М Ш Е Э

                3, 2, 0, 1, 3,              # Ш Э Е М Ш
                2, 1, 0, 2, 1, 0,           # Э М Е Э М Е
                1, 3, 2, 3, 1, 3,           # М Ш Э Ш М Ш
                2, 0, 1, 3, 1, 0, 2,        # Э Е М Ш М Е Э
                3, 0, 3, 1, 0, 2, 3,        # Ш Е Ш М Е Э Ш
                1, 3, 2, 0, 2, 3, 0,        # М Ш Э Е Э Ш Е

                0, 1, 0, 2, 3, 1, 0, 2,     # Е М Е Э Ш М Е Э
                2, 1, 0, 2, 1, 0, 3, 1,     # Э М Е Э М Е Ш М
                1, 3, 2, 1, 3, 2, 0, 3]     # М Ш Э М Ш Э Е Ш

    def line_lengths(self):
        return [2, 3, 4,
                5, 6, 6, 7, 7, 7,
                8, 8, 8]
