import math
import os
import re
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Triangle
from kivy.metrics import dp
from kivy.core.window import Window
from kivy.core.clipboard import Clipboard
from kivy.utils import get_color_from_hex

Window.clearcolor = get_color_from_hex("#0A0A0A")
RED = get_color_from_hex("#E50914")
DARK = get_color_from_hex("#1A1A1A")
DARK_LIGHT = get_color_from_hex("#2A2A2A")
GRAY = get_color_from_hex("#888888")
WHITE = get_color_from_hex("#FFFFFF")

_FONT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sadaf_font.ttf")
BRAND_FONT = _FONT_PATH if os.path.exists(_FONT_PATH) else "Roboto"

FUNCS = ['sin', 'cos', 'tan', 'log', 'ln', '√']
OPS = ['=', '+', '-', '×', '÷', '^']
SPECIAL = ['MC', 'MR', 'M+', 'M-', 'COPY', 'C', 'DEL', 'RAD']


def fmt(value):
    if isinstance(value, int):
        return str(value)
    if value.is_integer():
        return str(int(value))
    text = str(round(value, 10))
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    return text


class Heart(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._draw, size=self._draw)
        self._draw()

    def _draw(self, *args):
        self.canvas.clear()
        s = min(self.width, self.height)
        x = self.x + (self.width - s) / 2
        y = self.y + (self.height - s) / 2
        with self.canvas:
            Color(*RED)
            Ellipse(pos=(x, y + 0.4 * s), size=(0.5 * s, 0.5 * s))
            Ellipse(pos=(x + 0.5 * s, y + 0.4 * s), size=(0.5 * s, 0.5 * s))
            Triangle(points=[x + 0.073 * s, y + 0.473 * s,
                             x + 0.927 * s, y + 0.473 * s,
                             x + 0.5 * s, y + 0.046 * s])
            Triangle(points=[x + 0.073 * s, y + 0.473 * s,
                             x + 0.927 * s, y + 0.473 * s,
                             x + 0.5 * s, y + 0.65 * s])


class CalculatorEngine:
    def __init__(self):
        self.is_rad = True

    def calculate(self, expression):
        try:
            exp = expression.replace('×', '*').replace('÷', '/').replace('^', '**')
            exp = exp.replace('π', str(math.pi)).replace('%', '/100')
            exp = exp.replace('√', 'sqrt')
            exp = re.sub(r'(\d)\(', r'\1*(', exp)
            allowed_names = {k: getattr(math, k) for k in
                             ['sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'sqrt', 'exp',
                              'factorial', 'radians', 'degrees', 'pi', 'e']}
            allowed_names['ln'] = math.log
            allowed_names['log'] = math.log10

            if not self.is_rad:
                exp = exp.replace('sin', 'sin_r').replace('cos', 'cos_r').replace('tan', 'tan_r')
                allowed_names['sin_r'] = lambda x: math.sin(math.radians(x))
                allowed_names['cos_r'] = lambda x: math.cos(math.radians(x))
                allowed_names['tan_r'] = lambda x: math.tan(math.radians(x))

            result = eval(exp, {"__builtins__": {}}, allowed_names)
            return fmt(result)
        except Exception:
            return "Error"


class SadafCalculatorApp(App):
    title = "SADAF Calculator"

    def build(self):
        self.engine = CalculatorEngine()
        self.expression = ""
        self.memory = 0.0

        root = BoxLayout(orientation='vertical', padding=10, spacing=8)

        header = BoxLayout(orientation='horizontal', size_hint_y=0.12, spacing=dp(12))
        heart = Heart(size_hint=(None, None), size=(dp(40), dp(40)),
                      pos_hint={'center_y': 0.5})
        name = Label(text="SADAF", font_name=BRAND_FONT, font_size='48sp',
                     color=RED, size_hint_x=None)
        name.bind(texture_size=lambda inst, val: setattr(inst, 'width', val[0]))
        header.add_widget(Widget())
        header.add_widget(heart)
        header.add_widget(name)
        header.add_widget(Widget())
        root.add_widget(header)

        root.add_widget(Label(text="LUXURY EDITION  |  SCIENTIFIC", font_name=BRAND_FONT,
                              font_size='10sp', color=GRAY, size_hint_y=0.03))

        self.result_label = Label(text="0", font_size='42sp', color=WHITE,
                                  size_hint_y=0.2, bold=True)
        self.status_label = Label(text="", font_size='13sp', color=GRAY, size_hint_y=0.04)
        root.add_widget(self.result_label)
        root.add_widget(self.status_label)

        buttons = [
            ['MC', 'MR', 'M+', 'M-', 'COPY'],
            ['RAD', '(', ')', 'C', 'DEL'],
            ['sin', 'cos', 'tan', '√', '^'],
            ['7', '8', '9', '÷', 'log'],
            ['4', '5', '6', '×', 'ln'],
            ['1', '2', '3', '-', 'π'],
            ['0', '.', '%', '+', '='],
        ]

        grid = GridLayout(cols=5, spacing=8, size_hint_y=0.61)
        for row in buttons:
            for text in row:
                btn = Button(text=text, font_size='16sp', background_normal='',
                             background_color=DARK, color=WHITE)
                if text in OPS:
                    btn.background_color = RED
                elif text in SPECIAL:
                    btn.background_color = DARK_LIGHT
                btn.bind(on_press=self.on_button_press)
                grid.add_widget(btn)

        root.add_widget(grid)
        return root

    def current_value(self):
        if not self.expression:
            return 0.0
        try:
            return float(self.engine.calculate(self.expression))
        except ValueError:
            return None

    def show(self):
        self.result_label.text = self.expression if self.expression else "0"

    def on_button_press(self, instance):
        text = instance.text
        if self.expression == "Error":
            self.expression = ""
        self.status_label.text = ""

        if text == 'C':
            self.expression = ""
        elif text == 'DEL':
            self.expression = self.expression[:-1]
        elif text == '=':
            self.expression = self.engine.calculate(self.expression)
        elif text in ('RAD', 'DEG'):
            self.engine.is_rad = not self.engine.is_rad
            instance.text = "RAD" if self.engine.is_rad else "DEG"
            return
        elif text == 'MC':
            self.memory = 0.0
            self.status_label.text = "Memory cleared"
            return
        elif text == 'MR':
            m = fmt(self.memory)
            self.expression += "(%s)" % m if self.memory < 0 else m
        elif text in ('M+', 'M-'):
            v = self.current_value()
            if v is None:
                self.status_label.text = "Error"
                return
            self.memory += v if text == 'M+' else -v
            self.status_label.text = "Memory: " + fmt(self.memory)
            return
        elif text == 'COPY':
            try:
                Clipboard.copy(self.result_label.text)
                self.status_label.text = "Copied: " + self.result_label.text
            except Exception:
                self.status_label.text = "Copy failed"
            return
        elif text in FUNCS:
            self.expression += text + "("
        else:
            self.expression += text

        self.show()


if __name__ == '__main__':
    SadafCalculatorApp().run()
