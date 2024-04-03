from tkinter import Toplevel, Canvas, messagebox, Button

from PIL import ImageGrab

from . import Selection


class ScreenSelector:
    def __init__(self, screen_selection, device_key):
        self.screen_selection: Selection = screen_selection
        px = ImageGrab.grab()
        self.screen_width = int(px.width / 4)
        self.screen_height = int(px.height / 4)
        self.root = Toplevel()
        self.root.title(device_key)
        self.canvas = Canvas(self.root, width=self.screen_width, height=self.screen_height)
        self.canvas.pack()
        self.selected_circles = []
        self.__draw_grid()
        self.__add_submit_button()

    def __draw_grid(self):
        self.circle_ids = {}
        circle_radius = 20
        for x in range(circle_radius + 10, self.screen_width - 10, int(self.screen_width / 16)):
            for y in range(circle_radius + 10, self.screen_height, int(self.screen_height / 9)):
                circle = self.canvas.create_oval(x - circle_radius, y - circle_radius,
                                                 x + circle_radius, y + circle_radius,
                                                 fill='white', outline='gray')
                self.circle_ids[circle] = (x, y)
                self.canvas.tag_bind(circle, '<ButtonPress-1>', self.__on_circle_click)

    def __on_circle_click(self, event):
        circle_id = self.canvas.find_closest(event.x, event.y)[0]
        circle_color = 'red'
        if len(self.selected_circles) != 0:
            last_circle_id = self.selected_circles[-1]
            if circle_id == last_circle_id:
                self.canvas.itemconfig(circle_id, fill='white')
                self.selected_circles.remove(circle_id)
                if len(self.selected_circles) > 1:
                    self.canvas.itemconfig(self.selected_circles[-1], fill='red')
                elif len(self.selected_circles) == 1:
                    self.canvas.itemconfig(self.selected_circles[-1], fill='green')
                return
            elif circle_id not in [last_circle_id - 1, last_circle_id + 1, last_circle_id + 9, last_circle_id - 9]:
                return
            elif circle_id in self.selected_circles:
                return
            if len(self.selected_circles) > 1:
                self.canvas.itemconfig(last_circle_id, fill='blue')
        else:
            circle_color = 'green'
        self.canvas.itemconfig(circle_id, fill=circle_color)
        self.selected_circles.append(circle_id)

    def __add_submit_button(self):
        submit_button = Button(self.root, text="Submit", command=self.submit_selection)
        submit_button.pack()

    def submit_selection(self):
        if len(self.selected_circles) < 2:
            messagebox.showwarning("No valid selection", "Please select two or more circles.")
            return
        self.screen_selection.set_selection(list(map(
            lambda x: (self.circle_ids[x][0] * 4, self.circle_ids[x][1] * 4),
            self.selected_circles)))
        self.root.destroy()
        self.root.update()
        self.root.quit()

    def run(self):
        self.root.wait_window()
