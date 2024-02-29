class GoL:
    """
    Conway's game of life
        1. Birth: A dead cell with exactly three live neighbors becomes a live cell in the next generation.
        2. Survival: A live cell with two or three live neighbors remains alive in the next generation.
        3. Death: A live cell with fewer than two live neighbors dies of underpopulation, or with more than three live neighbors dies
                  of overpopulation, in the next generation.
    """
    GOL = None

    def __init__(self, height=16, width=32):
        self.height = height
        self.width = width
        self.matrix = [[0] * width for _ in range(height)]
        self.__next_delta = []

    def add_cells(self, x, y, cells):
        """
        Add living cells
        """
        for line_index, line_data in enumerate(cells):
            for ix, v in enumerate(line_data):
                self.matrix[y+line_index][ix+x] = v

    def _next_gen(self):
        """
        Create next generation of cells - line-by-line on self.matrix
        """
        action = False
        dead_cells = [(y, tuple((x for x, v in enumerate(raw) if v == 0))) for y, raw in enumerate(self.matrix) if 0 in raw]
        # Birth
        for cell in dead_cells:
            line_index, column_idxs = cell
            for col_idx in column_idxs:
                action |= self._birth(x=col_idx, y=line_index)
        live_cells = [(line_index, tuple((x for x, v in enumerate(raw) if v == 1))) for line_index, raw in enumerate(self.matrix) if 1 in raw]
        # Death
        for cell in live_cells:
            line_index, column_idxs = cell
            for col_idx in column_idxs:
                action |= self._death(x=col_idx, y=line_index)
        if action:
            # Commit changes - next generation of cells
            for x, y, v in self.__next_delta:
                self.matrix[y][x] = v
            self.__next_delta = []      # Clean delta after dump/commit
            return self.matrix
        return None

    def _get_neighbours(self, x, y):
        """
        Check selected cell neighbours
        """
        neighbours = 0
        check_mask = ((-1, -1), (-1, 0), (-1, +1), (0, -1), (0, +1), (+1, -1), (+1, 0), (+1, +1))

        for mask in check_mask:
            y_offset, x_offset = mask
            check_x, check_y = x+x_offset, y+y_offset
            if check_x < 0 or check_y < 0:
                continue
            try:
                state = self.matrix[check_y][check_x]
                neighbours += state
            except Exception as e:
                pass
        return neighbours

    def _birth(self, x, y):
        """
        Dead Cell x,y
            1. Birth: A dead cell with exactly three live neighbors becomes a live cell in the next generation.
        """
        neighbours = self._get_neighbours(x, y)
        if neighbours == 3:
            self.__next_delta.append((x, y, 1))
            return True
        return False

    def _death(self, x, y):
        """
        Live Cell x,y
            2. Survival: A live cell with two or three live neighbors remains alive in the next generation.
            3. Death: A live cell with fewer than two live neighbors dies of underpopulation, or with more than three live neighbors dies
                      of overpopulation, in the next generation.
        """
        neighbours = self._get_neighbours(x, y)
        # Survival - if not delete
        if not (neighbours == 2 or neighbours == 3):
            self.__next_delta.append((x, y, 0))
            return True
        # Underpopulation/loneliness - less then 2 neighbour
        if neighbours < 2:
            self.__next_delta.append((x, y, 0))
            return True
        # Overpopulation - more then 3 neighbours
        if neighbours > 3:
            self.__next_delta.append((x, y, 0))
            return True
        return False


def _default():
    """
    Contains default cells setup
    Default: 16x32 px
    """
    # Spaceship (Copperhead)
    cells = ((0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0),
             (0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0),
             (0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0),
             (1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0),
             (1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0),
             (0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0),
             (0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0),
             (0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0))
    GoL.GOL.add_cells(1, 4, cells)
    # Oscillator (my Blinker Star)
    cells = ((1, 1, 1, 1, 1),)
    GoL.GOL.add_cells(25, 5, cells)
    # Spaceship (Glider)
    cells = ((0, 1, 0),
             (0, 0, 1),
             (1, 1, 1))
    GoL.GOL.add_cells(16, 5, cells)


def load_n_init(w=32, h=16):
    """
    Init Conway's Game of Life
    :param w: width of display (pixel)
    :param h: height of display (pixel)
    Init and store GoL instance, inject default cells
    """
    if GoL.GOL is None:
        GoL.GOL = GoL(height=h, width=w)
        _default()
        return f'Init Game of Life: X:{w}Y:{h}'
    return f'Game of Life was already inited: X:{GoL.GOL.width}Y:{GoL.GOL.height}'


def next_gen(raw=False):
    """
    Get Next Generation of cells
    :param raw: Output type (raw:True -> matrix), (raw:False formatted output)
    return change of life matrix or None if there is no change
    """
    if GoL.GOL is None:
        load_n_init()
    matrix = GoL.GOL._next_gen()
    if raw:
        return matrix
    if matrix is None:
        return 'GoL No changes'
    return '\n'.join([" ".join(['.' if r == 0 else "●" for r in row]) for row in matrix])


def reset():
    """
    Reset life table - set default
    """
    del GoL.GOL
    GoL.GOL = None
    return 'GoL reset'


def help():
    return 'load_n_init w=32 h=16', 'next_gen raw=False', 'reset'