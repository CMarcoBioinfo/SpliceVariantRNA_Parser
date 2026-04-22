import PySimpleGUI as sg


class CanvasTable:
    def __init__(self, canvas, columns, data, row_height=25, col_width=150):
        self.canvas = canvas
        self.columns = columns
        self.data = data

        self.row_height = row_height
        self.col_width = col_width

        self.selected_row = None
        self.scroll_offset = 0

        # Bind scroll + click
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<MouseWheel>", self._on_scroll)

    # -----------------------------
    # PUBLIC API
    # -----------------------------
    def update_data(self, new_data):
        self.data = new_data
        self.draw()

    def get_selected_index(self):
        return self.selected_row

    # -----------------------------
    # DRAWING
    # -----------------------------
    def draw(self):
        c = self.canvas
        c.delete("all")

        self._draw_header()
        self._draw_rows()

    def _draw_header(self):
        c = self.canvas
        y = 0

        for i, col in enumerate(self.columns):
            x = i * self.col_width
            c.create_rectangle(x, y, x + self.col_width, y + self.row_height,
                               fill="#E0E0E0", outline="black")
            c.create_text(x + 5, y + self.row_height // 2,
                          anchor="w", text=col)

    def _draw_rows(self):
        c = self.canvas
        start_y = self.row_height

        visible_data = self.data[self.scroll_offset:]

        for r, row in enumerate(visible_data):
            y = start_y + r * self.row_height

            for i, col in enumerate(self.columns):
                x = i * self.col_width

                fill = "#CCE5FF" if r + self.scroll_offset == self.selected_row else "white"

                c.create_rectangle(x, y, x + self.col_width, y + self.row_height,
                                   fill=fill, outline="black")
                c.create_text(x + 5, y + self.row_height // 2,
                              anchor="w", text=str(row[i]))

    # -----------------------------
    # EVENTS
    # -----------------------------
    def _on_click(self, event):
        y = event.y

        # Ignore header
        if y < self.row_height:
            return

        row_index = (y - self.row_height) // self.row_height
        row_index += self.scroll_offset

        if 0 <= row_index < len(self.data):
            self.selected_row = row_index
            self.draw()

    def _on_scroll(self, event):
        if event.delta < 0:
            self.scroll_offset = min(self.scroll_offset + 1, max(0, len(self.data) - 1))
        else:
            self.scroll_offset = max(self.scroll_offset - 1, 0)

        self.draw()
