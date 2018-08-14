import random

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.graphics.context_instructions import Color
from kivy.graphics.instructions import InstructionGroup
from kivy.graphics.vertex_instructions import Rectangle
from kivy.lang import Builder
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen

Window.size = (400, 700)
Builder.load_file('graphic.kv')


class NullBlock(ButtonBehavior, Image):
    index_x, index_y = 0, 0
    c = ""

    def __init__(self, **kwargs):
        super(NullBlock, self).__init__(**kwargs)

    def destroy(self):
        return

    def look_for_black(self):
        return


class Block(NullBlock):
    block_up, block_down, block_right, block_left, block_up2, block_down2, block_right2, block_left2 \
        = NullBlock(), NullBlock(), NullBlock(), NullBlock(), NullBlock(), NullBlock(), NullBlock(), NullBlock()

    def __init__(self, c, x, y, **kwargs):
        super(Block, self).__init__(**kwargs)
        self.index_x = x
        self.index_y = y
        self.c = c
        self.load_source()

    def on_press(self):
        parent = self.parent.parent.parent
        parent.block_pressed(self)
        if self.parent.parent.parent.is_bomb_drag:
            parent.add_bomb(-1)
            self.blow()
            parent.bomb_unactive()

    def blow(self):
        parent = self.parent.parent.parent
        y = self.index_y
        x = self.index_x
        parent.blocks[y + 1][x].destroy()
        parent.blocks[y - 1][x].destroy()
        parent.blocks[y][x + 1].destroy()
        parent.blocks[y][x - 1].destroy()
        parent.blocks[y + 1][x - 1].destroy()
        parent.blocks[y - 1][x - 1].destroy()
        parent.blocks[y + 1][x + 1].destroy()
        parent.blocks[y - 1][x + 1].destroy()
        self.destroy()

    def check_line(self, blockup1, blockup2, blockdown1, blockdown2):
        parent = self.parent.parent.parent

        blocks_to_destroy = []

        if blockup1 is not None and blockdown1 is not None and self.c == blockup1.c and self.c == blockdown1.c:
            if blockup2 is not None and self.c == blockup2.c:
                blocks_to_destroy.append(blockup2)
                parent.add_bomb()

            blocks_to_destroy.append(blockup1)
            blocks_to_destroy.append(self)
            blocks_to_destroy.append(blockdown1)

            if blockdown2 is not None and self.c == blockdown2.c:
                blocks_to_destroy.append(blockdown2)
                parent.add_bomb()

        if blockup1 is not None and blockup2 is not None and self.c == blockup1.c and self.c == blockup2.c:
            blocks_to_destroy.append(blockup2)
            blocks_to_destroy.append(blockup1)
            blocks_to_destroy.append(self)

        if blockdown1 is not None and blockdown2 is not None and self.c == blockdown1.c and self.c == blockdown2.c:
            blocks_to_destroy.append(self)
            blocks_to_destroy.append(blockdown1)
            blocks_to_destroy.append(blockdown2)

        return blocks_to_destroy

    def look_for_line(self, destroy=True, look_for_black=True):
        parent = self.parent.parent.parent
        x = self.index_x
        y = self.index_y
        up, down, right, left, up2, down2, right2, left2 \
            = None, None, None, None, None, None, None, None
        if x > 0:
            left = parent.blocks[y][x - 1]
            if x > 1:
                left2 = parent.blocks[y][x - 2]
        if x < parent.board_size - 1:
            right = parent.blocks[y][x + 1]
            if x < parent.board_size - 2:
                right2 = parent.blocks[y][x + 2]
        if y > 0:
            up = parent.blocks[y - 1][x]
            if y > 1:
                up2 = parent.blocks[y - 2][x]
        if y < parent.board_size - 1:
            down = parent.blocks[y + 1][x]
            if y < parent.board_size - 2:
                down2 = parent.blocks[y + 2][x]
        horizontal_blocks = self.check_line(left, left2, right, right2)
        vertical_blocks = self.check_line(up, up2, down, down2)
        blocks_to_destroy = horizontal_blocks + vertical_blocks
        if len(blocks_to_destroy) > 0:
            if destroy:
                for block in blocks_to_destroy:
                    if look_for_black:
                        block.look_for_black()
                    block.destroy()
            return True
        return False

    def look_for_black(self):
        parent = self.parent.parent.parent
        if not self.index_y >= parent.board_size - 1:
            if parent.blocks[self.index_y + 1][self.index_x].c == "black":
                parent.game_over()
        if not self.index_y <= 0:
            if parent.blocks[self.index_y - 1][self.index_x].c == "black":
                parent.game_over()
        if not self.index_x >= parent.board_size - 1:
            if parent.blocks[self.index_y][self.index_x + 1].c == "black":
                parent.game_over()
        if not self.index_x <= 0:
            if parent.blocks[self.index_y][self.index_x - 1].c == "black":
                parent.game_over()

    def fall(self, dt):
        parent = self.parent.parent.parent
        if self.index_y > 0:
            if self.c == "white":
                block_above = parent.blocks[self.index_y - 1][self.index_x]
                self.swap_colors(block_above, False)
                Clock.schedule_once(block_above.fall, 0.0)
        self.check_is_destroyed()

    def destroy(self):
        Clock.schedule_once(self.set_to_destroyed, 0.2)

    def set_to_destroyed(self, dt):
        self.set_color("white")
        Clock.schedule_once(self.fall, 0.05)
        self.parent.parent.parent.add_score(10)

    def move(self, direction):
        swap_block = self.get_block_by_direction(direction)
        self.swap_colors(swap_block)
        self.parent.parent.parent.last_touched_block = None

    def swap_colors(self, swap_block, look=True):
        swap_block_color = swap_block.c
        swap_block.set_color(self.c)
        self.set_color(swap_block_color)
        if look:
            swap_block_looking = swap_block.look_for_line()
            self_looking = self.look_for_line()
            if not swap_block_looking and not self_looking:
                self.swap_colors(swap_block, False)

    def check_is_destroyed(self):
        if self.c == "white":
            self.randomize_color()

    def check_color(self):
        self.check_block_nearby()
        parent = self.parent.parent.parent
        x1 = parent.blocks[self.index_y][self.index_x - 1].c
        x2 = parent.blocks[self.index_y][self.index_x - 2].c
        y1 = parent.blocks[self.index_y - 1][self.index_x].c
        y2 = parent.blocks[self.index_y - 2][self.index_x].c

        if self.c == x1 and self.c == x2:
            self.randomize_color()
        if self.c == y1 and self.c == y2:
            self.randomize_color()

    def randomize_color(self):
        parent = self.parent.parent.parent
        if parent.actual_chance_for_black < 30:
            available_colors = [x for x in parent.colors if x != self.c]
            c = random.choice(available_colors)
            self.set_color(c)
        else:
            self.set_color("black")
            parent.actual_chance_for_black = 0
        parent.actual_chance_for_black += 1

    def check_block_nearby(self):
        parent = self.parent.parent.parent
        x = self.index_x
        y = self.index_y
        if x > 0:
            self.block_left = parent.blocks[y][x - 1]
            if x > 1:
                self.block_left2 = parent.blocks[y][x - 2]
        if x < parent.board_size - 1:
            self.block_right = parent.blocks[y][x + 1]
            if x < parent.board_size - 2:
                self.block_right2 = parent.blocks[y][x + 2]
        if y > 0:
            self.block_up = parent.blocks[y - 1][x]
            if y > 1:
                self.block_up2 = parent.blocks[y - 2][x]
        if y < parent.board_size - 1:
            self.block_down = parent.blocks[y + 1][x]
            if y < parent.board_size - 2:
                self.block_down2 = parent.blocks[y + 2][x]

    def set_color(self, c):
        self.c = c
        self.load_source()

    def get_block_by_direction(self, direction):
        parent = self.parent.parent.parent
        swap_block_y = self.index_y
        swap_block_x = self.index_x

        if direction == "up" and self.index_y > 0:
            swap_block_y -= 1
        elif direction == "down" and self.index_y < parent.board_size - 1:
            swap_block_y += 1
        elif direction == "left" and self.index_x > 0:
            swap_block_x -= 1
        elif direction == "right" and self.index_x < parent.board_size - 1:
            swap_block_x += 1

        return parent.blocks[swap_block_y][swap_block_x]

    def print_index(self):
        print("y: " + str(self.index_y) + " x: " + str(self.index_x))

    def load_source(self):
        self.source = "img/blocks/" + str(self.c) + "_block.png"


class SquareButton(ButtonBehavior, Image):
    def __init__(self, **kwargs):
        super(SquareButton, self).__init__(**kwargs)


class MenuScreen(Screen):
    high_score = 0

    light_color = (.8, .8, .8, 1)
    dark_color = (.1, .1, .1, 1)

    def __init__(self, **kwargs):
        super(MenuScreen, self).__init__(**kwargs)
        self.color = True

        self.set_color(self.color)

    def change_theme(self):
        self.color = not self.color
        self.set_color(self.color)

    def set_color(self, color):
        if color:
            Window.clearcolor = self.light_color
        else:
            Window.clearcolor = self.dark_color

    def set_score(self, score):
        self.high_score = score
        self.high_score_label.text = str(score)


class PlayScreen(Screen):
    all_colors = ["red", "blue", "green", "yellow", "orange", "purple", "turquoise", "pink"]
    colors = []
    blocks = []
    touch_accuracy = 30
    board_size = 8
    color_count = 6

    score = 0
    bombs_count = 0

    last_x = 0
    last_y = 0
    actually_x = 0
    actually_y = 0
    last_touched_block = None
    actual_chance_for_black = 0
    game_active = True
    is_bomb_drag = False

    def __init__(self, **kwargs):
        super(PlayScreen, self).__init__(**kwargs)
        self.lose_info = FloatLayout(pos_hint={'center_x': .5, 'center_y': .5}, size_hint=(1, 1))
        self.lose_info.add_widget(Image(source="img/game_over.png", pos_hint={'center_x': .5, 'center_y': .5}))
        self.lose_info.add_widget(Label(text="Tap to try again", font_size=20, pos_hint={'center_x': .5, 'center_y': .2}))
        self.canvas.add(Color(0, 0, 0, 0.3))
        self.shadow = Rectangle(size=(Window.width, Window.height))
        self.start_game()

    def bomb_drag(self):
        if not self.is_bomb_drag and self.bombs_count > 0:
            self.bomb_active()
        else:
            self.bomb_unactive()

    def bomb_active(self):
        self.is_bomb_drag = True
        self.bomb.size_hint_x = .25

    def bomb_unactive(self):
        self.is_bomb_drag = False
        self.bomb.size_hint_x = .22

    def add_score(self, amount):
        self.score += amount
        self.score_board.text = str(self.score)

    def add_bomb(self, amount=1):
        self.bombs_count += amount
        self.bomb_label.text = str(self.bombs_count)

    def block_pressed(self, block):
        self.last_touched_block = block

    def start_game(self):
        self.colors = self.all_colors[0:self.color_count]
        self.blocks = []
        self.board.clear_widgets()
        self.board.cols = self.board_size
        for y in range(self.board_size):
            self.blocks.append([])
            for x in range(self.board_size):
                self.blocks[y].append(Block(random.choice(self.colors), x, y))

        for x in range(self.board_size):
            for block in self.blocks[x]:
                self.board.add_widget(block)

        for y in self.blocks:
            for x in y:
                x.check_color()

    def game_over(self):
        menu = self.manager.get_screen('menu')
        self.game_active = False
        self.canvas.add(self.shadow)
        self.add_widget(self.lose_info)

        if self.score > menu.high_score:
            menu.set_score(self.score)

    def try_again(self):
        self.remove_widget(self.lose_info)
        self.canvas.remove(self.shadow)
        self.score = 0
        self.score_board.text = str(self.score)
        self.bombs_count = 0
        self.bomb_label.text = str(self.bombs_count)
        self.bomb_unactive()
        self.game_active = True
        self.start_game()

    def on_touch_down(self, touch):
        if self.game_active:
            self.last_x = touch.pos[0]
            self.last_y = touch.pos[1]
        else:
            self.try_again()

        super(PlayScreen, self).on_touch_down(touch)

    def on_touch_up(self, touch):
        if self.last_touched_block is not None and self.game_active:
            self.actually_x = touch.pos[0]
            self.actually_y = touch.pos[1]
            dif_x = self.actually_x - self.last_x
            dif_y = self.actually_y - self.last_y

            direction = ""
            if dif_y > self.touch_accuracy:
                direction = "up"
            elif dif_y < -self.touch_accuracy:
                direction = "down"
            elif dif_x > self.touch_accuracy:
                direction = "right"
            elif dif_x < -self.touch_accuracy:
                direction = "left"
            else:
                return

            self.last_touched_block.move(direction)
        super(PlayScreen, self).on_touch_up(touch)


class OptionButton(Button):
    def __init__(self, option, **kwargs):
        super(OptionButton, self).__init__(**kwargs)
        self.option = option

        self.text = str(option)
        self.font_size = 17
        self.background_color = (.3, .5, 1, .8)


class SettingsScreen(Screen):
    board_size_options = [4, 6, 8, 10, 15]
    colors_count_options = [4, 5, 6, 7, 8]

    board_size = 8
    color_count = 6

    board_size_btn = None
    color_count_btn = None

    def __init__(self, **kwargs):
        super(SettingsScreen, self).__init__(**kwargs)
        for size in self.board_size_options:
            btn = OptionButton(size)
            btn.bind(on_press=self.change_board)
            if size == self.board_size:
                btn.disabled = True
                self.board_size_btn = btn
            self.board_size_grid.add_widget(btn)

        for size in self.colors_count_options:
            btn = OptionButton(size)
            btn.bind(on_press=self.change_color)
            if size == self.color_count:
                btn.disabled = True
                self.color_count_btn = btn
            self.colors_count_grid.add_widget(btn)

    def save(self):
        print("SAVING")

    def change_board(self, instance):
        play_screen = self.manager.get_screen('play')
        if self.board_size != instance.option:
            self.board_size_btn.disabled = False
            self.board_size = instance.option

            instance.disabled = True
            self.board_size_btn = instance

            play_screen.board_size = self.board_size
            play_screen.try_again()

    def change_color(self, instance):
        play_screen = self.manager.get_screen('play')
        if self.color_count != instance.option:
            self.color_count_btn.disabled = False
            self.color_count = instance.option

            instance.disabled = True
            self.color_count_btn = instance

            play_screen.color_count = self.color_count
            play_screen.try_again()


class InfoScreen(Screen):
    def __init__(self, **kwargs):
        super(InfoScreen, self).__init__(**kwargs)


sm = ScreenManager()
sm.add_widget(MenuScreen(name='menu'))
sm.add_widget(PlayScreen(name='play'))
sm.add_widget(SettingsScreen(name='settings'))
sm.add_widget(InfoScreen(name='info'))


class Decode(App):
    def build(self):
        return sm


if __name__ == '__main__':
    Decode().run()
