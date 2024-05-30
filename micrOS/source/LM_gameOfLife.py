class GoL:
    """
    Conway's game of life
        1. Birth: A dead cell with exactly three live neighbors becomes a live cell in the next generation.
        2. Survival: A live cell with two or three live neighbors remains alive in the next generation.
        3. Death: A live cell with fewer than two live neighbors dies of underpopulation, or with more than three live neighbors dies
                  of overpopulation, in the next generation.
    """
    GOL = None
    CSTM_CONF = None

    def __init__(self, height=16, width=32, custom_conf=None):
        self.height = height
        self.width = width
        self.matrix = [[0] * width for _ in range(height)]
        self.__next_delta = []
        if isinstance(custom_conf, tuple):
            GoL.CSTM_CONF = custom_conf

    def clean(self):
        """
        Clean data matrix - empty state
        """
        self.matrix = [[0] * self.width for _ in range(self.height)]

    def add_cells(self, x, y, cells):
        """
        Add living cells
        """
        for line_index, line_data in enumerate(cells):
            for ix, v in enumerate(line_data):
                self.matrix[y+line_index][ix+x] = v

    def init_conf(self):
        """
        Contains default cells setup
        Default: 16x32 px
        Configuration of Game of life:
        - simulation end is stationary (detection->restart) + reset function
        """
        if GoL.CSTM_CONF is None:
            # SET DEFAULT CONFIG
            # Spaceship (Copperhead)
            cells = ((0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0),
                     (0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0),
                     (0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0),
                     (1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0),
                     (1, 1, 0, 1, 0, 0, 0, 0, 0, 1, 1, 0, 0),
                     (0, 0, 0, 1, 1, 0, 0, 0, 1, 0, 0, 1, 0),
                     (0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 1, 0),
                     (0, 0, 0, 0, 0, 1, 0, 1, 1, 0, 0, 0, 0))
            self.add_cells(1, 4, cells)
            # Oscillator (my Blinker Star)
            cells = ((1, 1, 1, 1, 1),)
            self.add_cells(25, 5, cells)
            # Spaceship (Glider)
            cells = ((0, 1, 0),
                     (0, 0, 1),
                     (1, 1, 1))
            self.add_cells(16, 5, cells)
        else:
            # SET CUSTOM (USER) CONFIG
            try:
                pos = GoL.CSTM_CONF[0]
                cells = GoL.CSTM_CONF[1:]
                self.add_cells(x=pos[0], y=pos[1], cells=cells)
            except Exception as e:
                GoL.CSTM_CONF = None        # Fallback to default config
                raise Exception(e)

    def next_gen(self):
        """
        Create next generation of cells - line-by-line on self.matrix
        """
        action = False
        for line_index, line_data in enumerate(self.matrix):
            for x, v in enumerate(line_data):
                # action:       Birth                              OR         Death
                action |= self._birth(x=x, y=line_index) if v == 0 else self._death(x=x, y=line_index)
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
            except Exception:
                # List index aut of range ... matrix edges issue
                pass
        return neighbours

    def _birth(self, x, y):
        """
        Dead Cell x,y
            1. Birth: A dead cell with exactly three live neighbors becomes a live cell in the next generation.
        """
        neighbours = self._get_neighbours(x, y)
        # Birth - died cell has exactly 3 neighbours -> birth
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
        # Survival - live cell has exactly 2 or 3 neighbours OR -> death
        if neighbours not in (2, 3):
            self.__next_delta.append((x, y, 0))
            return True
        # Underpopulation/loneliness - live cell has less than 2 neighbour -> death
        if neighbours < 2:
            self.__next_delta.append((x, y, 0))
            return True
        # Overpopulation - live cell has more than 3 neighbours -> death
        if neighbours > 3:
            self.__next_delta.append((x, y, 0))
            return True
        return False

"""
Custom config usage:

def my_config(add_cells):
    # custom cells
    cells = ((10,10),(1,0,0),(0,1,1),(0,0,1))
    load(w=32, h=16, custom=cells)
    
    matrix = []
    while matrix is not None:
        matrix = next_gen(raw=True, w=32, h=16)
        print(matrix)
"""

def load(w=32, h=16, custom=None):
    """
    Init Conway's Game of Life
    :param w: width of display (pixel)
    :param h: height of display (pixel)
    :param custom: custom initial set, example: ((10,10),(1,0,0),(0,1,1),(0,0,1))
    Init and store GoL instance, inject default cells
    """
    if GoL.GOL is None:
        GoL.GOL = GoL(height=h, width=w, custom_conf=custom)     # Init GoL class
        GoL.GOL.init_conf()                                      # Set default configuration
        return f'Init Game of Life: X:{w}Y:{h}'
    return f'Game of Life was already inited: X:{GoL.GOL.width}Y:{GoL.GOL.height}'


def next_gen(raw=False, w=32, h=16):
    """
    Main Game of Life function
        Get Next Generation of cells (with auto load and GoL reinit)
    :param raw: Output type (raw:True -> matrix), (raw:False formatted output)
    :param w: width of display (pixel) - auto init
    :param h: height of display (pixel) - auto init
    return change of life matrix or None if there is no change (on None, restart feature: call reset())
    """
    if GoL.GOL is None:
        load(w=w, h=h)
    matrix = GoL.GOL.next_gen()
    if raw:
        return matrix               # Matrix / None (no change)
    if matrix is None:
        return 'GoL No changes'
    return '\n'.join([" ".join(['.' if r == 0 else "●" for r in row]) for row in matrix])


def reset():
    """
    Reset life table - set default
    """
    if GoL.GOL is not None:
        GoL.GOL.clean()
        GoL.GOL.init_conf()
        return 'GoL reset'
    return 'GoL skip reset'


def help(widgets=False):
    """
    [i] micrOS LM naming convention - built-in help message
    :return tuple:
        (widgets=False) list of functions implemented by this application
        (widgets=True) list of widget json for UI generation
    """
    return 'load w=32 h=16 custom=None', 'next_gen w=32 h=16 raw=False', 'reset'