# scripts/ui/canvas_table.py

class CanvasTable:
    def __init__(self, canvas, columns, data):
        self.canvas = canvas
        self.columns = columns
        self.data = data

        # Dimensions
        self.col_width = 150
        self.row_height = 25

    # --- Dessin complet ---
    def draw(self):
        self.canvas.delete("all")
        self.draw_header()
        self.draw_filters()
        self.draw_rows()

    # --- Header ligne 1 ---
    def draw_header(self):
        for i, col in enumerate(self.columns):
            x = i * self.col_width
            self.canvas.create_rectangle(
                x, 0, x + self.col_width, self.row_height,
                fill="#E0E0E0"
            )
            self.canvas.create_text(
                x + 5, 12, anchor="w", text=col
            )

    # --- Header ligne 2 (filtres) ---
    def draw_filters(self):
        y = self.row_height
        for i, col in enumerate(self.columns):
            x = i * self.col_width
            self.canvas.create_rectangle(
                x, y, x + self.col_width, y + self.row_height,
                fill="#F0F0F0"
            )
            self.canvas.create_text(
                x + 5, y + 12, anchor="w", text="[ filtre ]"
            )

    # --- Lignes ---
    def draw_rows(self):
        start_y = self.row_height * 2
        for r, row in enumerate(self.data):
            y = start_y + r * self.row_height
            for i, col in enumerate(self.columns):
                x = i * self.col_width
                self.canvas.create_rectangle(
                    x, y, x + self.col_width, y + self.row_height,
                    fill="white"
                )
                self.canvas.create_text(
                    x + 5, y + 12, anchor="w", text=str(row[i])
                )
