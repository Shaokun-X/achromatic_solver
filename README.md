## Achromatic Solver

[Achromatic](https://www.studiogoya.co/achromatic/) is a challenging puzzle game. This python script can solve any puzzle that appears in the game, or that respects the same rules but not in the game.


### Requirement
Python 3.6 +
Terminal that supports [ANSI escape code](https://en.wikipedia.org/wiki/ANSI_escape_code)

### Usage

Define the puzzle:

```python
    map_ = Map(
        [
            BasicNode(Color.PURPLE, (1, 1)),
            BasicNode(Color.YELLOW, (2, 1)),
            TriangleNode(Color.GREEN, (3, 1)),
            BasicNode(Color.RED, (4, 1)),
            BasicNode(Color.GREEN, (5, 1)),
            BasicNode(Color.YELLOW, (6, 1)),

            BasicNode(Color.RED, (2, 2)),
            DiamondNode(Color.CYAN, (3, 2)),
            BasicNode(Color.PURPLE, (4, 2)),

            BasicNode(Color.RED, (1, 3)),
            BasicNode(Color.PURPLE, (2, 3)),
            TriangleNode(Color.GREEN, (3, 3)),
            BasicNode(Color.RED, (4, 3)),
            LineNode(Color.RED, (5, 3), Direction.HORIZONTAL),

            LineNode(Color.YELLOW, (3, 4), Direction.VERTICAL),
            BasicNode(Color.PURPLE, (4, 4)),
            BasicNode(Color.RED, (5, 4)),
        ]
    )
```

You can also add your favorite colors:

```python
class Color(Enum):
    BLANK = get_color_sequence(255, 255, 255)
    CYAN = get_color_sequence(0, 255, 255)
    ORANGE = get_color_sequence(255, 165, 0)
    YELLOW = get_color_sequence(255, 255, 0)
    RED = get_color_sequence(255, 0, 0)
    PURPLE = get_color_sequence(128, 0, 128)
    GREEN = get_color_sequence(0, 255, 0)
    MY_FAV = get_color_sequence(111, 222, 33)
```

Then simply run the scripts:
```shell
$ python solve.py
```
