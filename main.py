from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.graphics import Color, Ellipse, RoundedRectangle
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.clock import Clock

# Set Window to black for that OLED iPhone look
Window.clearcolor = (0, 0, 0, 1)

class IOSButton(ButtonBehavior, Label):
    def __init__(self, text="", bg=(0.2, 0.2, 0.2, 1), txt=(1, 1, 1, 1), is_wide=False, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.color = txt
        self.bg_color = bg
        self.original_bg = bg
        self.is_wide = is_wide
        self.font_size = dp(32)
        self.bind(pos=self.draw_bg, size=self.draw_bg)

    def draw_bg(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            if not self.is_wide:
                # iPhone buttons are perfect circles
                side = min(self.width, self.height)
                Ellipse(pos=(self.center_x - side/2, self.center_y - side/2), size=(side, side))
            else:
                # Zero button is a pill shape
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(50)])

    def on_press(self):
        # Brighten button color slightly on tap
        self.bg_color = [min(1, c * 1.5) for c in self.original_bg[:3]] + [1]
        self.draw_bg()

    def on_release(self):
        self.bg_color = self.original_bg
        self.draw_bg()

class iPhoneCalculator(App):
    def build(self):
        self.expression = "0"
        self.current_op = None
        self.last_val = ""
        self.new_entry = True
        self.active_op_btn = None

        self.root = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(12))

        # 1. Display (Dynamic Scaling)
        self.display = Label(
            text="0",
            font_size=dp(85),
            size_hint_y=0.35,
            halign='right',
            valign='bottom',
            color=(1, 1, 1, 1)
        )
        self.display.bind(size=self.display.setter('text_size'))
        self.root.add_widget(self.display)

        # Button Colors
        c_grey = (0.65, 0.65, 0.65, 1) # Light grey (top row)
        c_dark = (0.2, 0.2, 0.2, 1)     # Dark grey (numbers)
        c_orange = (1, 0.62, 0.04, 1)  # iOS Orange
        
        # 2. Key Grid
        layout = BoxLayout(orientation='vertical', spacing=dp(12), size_hint_y=0.65)
        
        rows = [
            [("AC", c_grey, (0,0,0,1)), ("+/-", c_grey, (0,0,0,1)), ("%", c_grey, (0,0,0,1)), ("÷", c_orange, (1,1,1,1))],
            [("7", c_dark, (1,1,1,1)), ("8", c_dark, (1,1,1,1)), ("9", c_dark, (1,1,1,1)), ("×", c_orange, (1,1,1,1))],
            [("4", c_dark, (1,1,1,1)), ("5", c_dark, (1,1,1,1)), ("6", c_dark, (1,1,1,1)), ("-", c_orange, (1,1,1,1))],
            [("1", c_dark, (1,1,1,1)), ("2", c_dark, (1,1,1,1)), ("3", c_dark, (1,1,1,1)), ("+", c_orange, (1,1,1,1))],
        ]

        for r in rows:
            row_box = BoxLayout(spacing=dp(12))
            for txt, bg, f_color in r:
                btn = IOSButton(text=txt, bg=bg, txt=f_color)
                btn.bind(on_release=self.on_touch)
                row_box.add_widget(btn)
            layout.add_widget(row_box)

        # 3. Special Bottom Row
        bottom = BoxLayout(spacing=dp(12))
        zero = IOSButton(text="0", bg=c_dark, txt=(1,1,1,1), is_wide=True, size_hint_x=2.2)
        zero.halign = 'left'
        zero.valign = 'middle'
        zero.padding = [dp(35), 0]
        zero.bind(size=lambda s, v: setattr(s, 'text_size', s.size))
        
        dot = IOSButton(text=".", bg=c_dark)
        equal = IOSButton(text="=", bg=c_orange)

        for b in [zero, dot, equal]:
            b.bind(on_release=self.on_touch)
            bottom.add_widget(b)
        
        layout.add_widget(bottom)
        self.root.add_widget(layout)
        return self.root

    def on_touch(self, instance):
        val = instance.text

        if val.isdigit() or val == ".":
            # If we were highlighting an operator, reset it
            self.clear_operator_highlight()
            
            if self.new_entry:
                self.expression = val if val != "." else "0."
                self.new_entry = False
            else:
                if val == "." and "." in self.expression: return
                if len(self.expression) < 9: # iPhone digit limit
                    self.expression += val
            
            self.update_screen(self.expression)
            self.get_btn("AC").text = "C"

        elif val in ["AC", "C"]:
            self.expression = "0"
            self.last_val = ""
            self.current_op = None
            self.new_entry = True
            self.update_screen("0")
            instance.text = "AC"
            self.clear_operator_highlight()

        elif val in ["+", "-", "×", "÷"]:
            self.clear_operator_highlight()
            self.last_val = self.expression
            self.current_op = val
            self.new_entry = True
            
            # Invert colors: Orange becomes White, Text becomes Orange
            instance.original_bg = (1, 1, 1, 1)
            instance.color = (1, 0.62, 0.04, 1)
            instance.draw_bg()
            self.active_op_btn = instance

        elif val == "=":
            if not self.current_op: return
            self.clear_operator_highlight()
            try:
                op = self.current_op.replace("×", "*").replace("÷", "/")
                res = eval(f"{float(self.last_val)}{op}{float(self.expression)}")
                # Format: remove .0 for integers
                self.expression = str(int(res) if res % 1 == 0 else round(res, 8))
                self.update_screen(self.expression)
                self.new_entry = True
            except:
                self.update_screen("Error")

    def clear_operator_highlight(self):
        if self.active_op_btn:
            self.active_op_btn.original_bg = (1, 0.62, 0.04, 1)
            self.active_op_btn.color = (1, 1, 1, 1)
            self.active_op_btn.draw_bg()
            self.active_op_btn = None

    def update_screen(self, val):
        # iPhone font-shrinking logic
        length = len(val)
        if length > 6:
            self.display.font_size = dp(85 - (length * 4))
        else:
            self.display.font_size = dp(85)
        self.display.text = val

    def get_btn(self, text):
        # Helper to find a specific button for label updates
        for row in self.root.children[0].children:
            if isinstance(row, BoxLayout):
                for b in row.children:
                    if b.text in ["AC", "C"]: return b
        return None

if __name__ == '__main__':
    iPhoneCalculator().run()
