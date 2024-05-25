import math

from enum import Enum
from typing import Union
from functools import cached_property
from itertools import product
from time import sleep

Vector = tuple[int, int]


def get_color_sequence(r: int, g: int, b: int) -> str:
    return f"\x1B[38;2;{r};{g};{b}m"


class Color(Enum):
    BLANK = get_color_sequence(255, 255, 255)
    CYAN = get_color_sequence(0, 255, 255)
    ORANGE = get_color_sequence(255, 165, 0)
    YELLOW = get_color_sequence(255, 255, 0)
    RED = get_color_sequence(255, 0, 0)
    PURPLE = get_color_sequence(128, 0, 128)
    GREEN = get_color_sequence(0, 255, 0)


ENDC = "\033[0m"


class Direction(Enum):
    VERTICAL = 0
    HORIZONTAL = 1


class Orientation(Enum):
    UP = 0
    DOWN = 1
    LEFT = 2
    RIGHT = 3


X, Y = 0, 1


class Node:
    char = "o"

    def __init__(self, color: Color, position: Vector) -> None:
        self.color = color
        self.position = position

    def get_neighbors(
        self, map_: "Map", inbound_dir: Union[Direction, None] = None
    ) -> list["Node"]:
        raise NotImplementedError

    def __eq__(self, __value: object) -> bool:
        return (
            self.color == __value.color
            and self.position == __value.position
            and self.__class__ is __value.__class__
        )

    def __hash__(self) -> int:
        return hash((self.color, self.position, self.__class__.__name__))

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.position} {self.color}>"

    def clone(self) -> "Node":
        return self.__class__(self.color, self.position)

    def get_targets(self, map_: "Map", new_color: Color) -> list[Vector]:
        """Excluding self"""
        return []

    def raycast(
        self, map_: "Map", direction: Orientation, pass_through: bool = True
    ) -> list[Vector]:
        if direction is Orientation.UP:
            delta = (0, -1)
        elif direction is Orientation.DOWN:
            delta = (0, 1)
        elif direction is Orientation.LEFT:
            delta = (-1, 0)
        else:
            delta = (1, 0)
        result = []
        x, y = self.position[X] + delta[X], self.position[Y] + delta[Y]
        while (
            x >= min(map_.x)
            and x <= max(map_.x)
            and y >= min(map_.y)
            and y <= max(map_.y)
        ):
            if not pass_through and (x, y) not in map_.all_nodes:
                break
            if (x, y) in map_.all_nodes and not isinstance(
                map_.all_nodes[(x, y)], Blank
            ):
                result.append((x, y))
            x, y = x + delta[X], y + delta[Y]

        return result

    def get_neighbor_in_direction(
        self, map_: "Map", direction: Orientation
    ) -> Union[Vector, None]:
        neighbor = self.raycast(map_, direction, pass_through=False)
        neighbor = next((v for v in neighbor), None)
        if neighbor and isinstance(map_.nodes[neighbor], LineNode):
            line_node: LineNode = map_.nodes[neighbor]
            if line_node.direction is get_direction(self.position, line_node.position):
                return neighbor
            else:
                return None
        else:
            return neighbor

    @property
    def colored_char(self) -> str:
        return f"{self.color.value}{self.char}{ENDC}"


class Blank(Node):
    char = "."


class BasicNode(Node):
    def get_neighbors(
        self, map_: "Map", inbound_dir: Union[Direction, None] = None
    ) -> list[Node]:
        result = []
        if inbound_dir is Direction.VERTICAL or inbound_dir is None:
            result.append(self.get_neighbor_in_direction(map_, Orientation.UP))
            result.append(self.get_neighbor_in_direction(map_, Orientation.DOWN))
        if inbound_dir is Direction.HORIZONTAL or inbound_dir is None:
            result.append(self.get_neighbor_in_direction(map_, Orientation.LEFT))
            result.append(self.get_neighbor_in_direction(map_, Orientation.RIGHT))
        result = [map_.nodes[pos] for pos in result if pos is not None]
        return result


class SquareNode(Node):
    char = "#"

    def get_neighbors(
        self, map_: "Map", inbound_dir: Union[Direction, None] = None
    ) -> list[Node]:
        result = []
        result.append(self.get_neighbor_in_direction(map_, Orientation.UP))
        result.append(self.get_neighbor_in_direction(map_, Orientation.DOWN))
        result.append(self.get_neighbor_in_direction(map_, Orientation.LEFT))
        result.append(self.get_neighbor_in_direction(map_, Orientation.RIGHT))
        result = [map_.nodes[pos] for pos in result if pos is not None]
        return result


class TurretNode(BasicNode):
    char = "+"

    def __init__(
        self, color: Color, position: tuple[int, int], orientations: list[Orientation]
    ) -> None:
        super().__init__(color, position)
        self.orientations = orientations

    def get_neighbors(
        self, map_: "Map", inbound_dir: Union[Direction, None] = None
    ) -> list[Node]:
        return super().get_neighbors(map_, inbound_dir)

    def get_targets(self, map_: "Map", new_color: Color) -> list[Vector]:
        """Excluding self"""
        result = []
        for direction in self.orientations:
            result.extend(self.raycast(map_, direction))
        return result

    def clone(self) -> "Node":
        return TurretNode(self.color, self.position, self.orientations)


class LineNode(Node):
    char = "~"

    def __init__(
        self, color: Color, position: tuple[int, int], direction: Direction
    ) -> None:
        super().__init__(color, position)
        self.direction = direction

    def get_neighbors(
        self, map_: "Map", inbound_dir: Union[Direction, None] = None
    ) -> list[Node]:
        result = []
        if inbound_dir is not None and inbound_dir is not self.direction:
            return result

        if self.direction is Direction.VERTICAL:
            result.append(self.get_neighbor_in_direction(map_, Orientation.UP))
            result.append(self.get_neighbor_in_direction(map_, Orientation.DOWN))
        if self.direction is Direction.HORIZONTAL:
            result.append(self.get_neighbor_in_direction(map_, Orientation.LEFT))
            result.append(self.get_neighbor_in_direction(map_, Orientation.RIGHT))
        result = [map_.nodes[pos] for pos in result if pos is not None]
        return result

    def clone(self) -> "Node":
        return LineNode(self.color, self.position, self.direction)


class DiamondNode(BasicNode):
    char = "*"

    def get_targets(self, map_: "Map", new_color: Color) -> list[Vector]:
        """Excluding self"""
        visited = set()
        unvisited = [self.position]
        while unvisited:
            current = unvisited.pop(0)
            visited.add(current)
            neighbors = [
                nb
                for nb in self.get_color_neighbors(current, map_)
                if nb not in visited
            ]
            unvisited.extend(neighbors)
        return [pos for pos in visited if pos != self.position]

    def get_color_neighbors(self, pos: Vector, map_: "Map") -> list[Vector]:
        up = pos[X], pos[Y] - 1
        down = pos[X], pos[Y] + 1
        left = pos[X] - 1, pos[Y]
        right = pos[X] + 1, pos[Y]

        result = []
        for dir_ in [up, down, left, right]:
            if dir_ in map_.nodes and map_.nodes[dir_].color is self.color:
                result.append(dir_)
        return result


class TriangleNode(BasicNode):
    char = "^"

    def get_targets(self, map_: "Map", new_color: Color) -> list[Vector]:
        return [
            n.position
            for n in map_.nodes.values()
            if isinstance(n, TriangleNode) and n != self and n.color != new_color
        ]


class AreaNode(BasicNode):
    char = "@"

    def get_targets(self, map_: "Map", new_color: Color) -> list[Vector]:
        neighbors = self.get_surrounding_neighbors(map_)
        return [
            pos for pos in neighbors
            if map_.nodes[pos].color != new_color
        ]
    
    def get_surrounding_neighbors(self, map_: "Map") -> list[Vector]:
        result = []
        for i, j in product(range(-1, 2), range(-1, 2)):
            if i == 0 and j ==0:
                continue
            neighbor = self.position[X] + i, self.position[Y] + j
            if neighbor in map_.nodes:
                result.append(neighbor)
        return result



class Map:
    def __init__(self, data: list[Node]) -> None:
        # all nodes includes blanks
        self.all_nodes: dict[Vector, Node] = {n.position: n for n in data}
        self.nodes: dict[Vector, Node] = {
            n.position: n for n in data if not isinstance(n, Blank)
        }

    @property
    def is_solved(self) -> bool:
        return len(set(node.color for node in self.nodes.values())) == 1

    @property
    def entrophy(self) -> int:
        count = {}
        for node in self.nodes.values():
            count[node.color] = count.get(node.color, 0) + 1
        return len(count), math.prod(count.values())

    def __hash__(self) -> int:
        sorted_nodes = list(self.all_nodes.values())
        sorted_nodes.sort(key=lambda n: n.position)
        return hash(tuple(sorted_nodes))

    def __eq__(self, __value: object) -> bool:
        return hash(self) == hash(__value)

    def clone(self):
        return Map([n.clone() for n in self.all_nodes.values()])

    def get_actions(self) -> set["Action"]:
        actions: set[Action] = set()
        for node in self.nodes.values():
            start_point = node.position
            start_color = node.color
            # skip the nodes of the same color
            first_neighbors = [
                n for n in node.get_neighbors(self) if n.color != node.color
            ]
            for first_neighbor in first_neighbors:
                middle_color = first_neighbor.color
                action = Action((start_point, first_neighbor.position))
                visited: set[Node] = {node, first_neighbor}
                direction = get_direction(start_point, first_neighbor.position)
                a = explore(
                    self,
                    start_color,
                    middle_color,
                    direction,
                    visited,
                    first_neighbor,
                    action,
                )
                actions.update(a)
        return actions

    @cached_property
    def x(self) -> list[int]:
        return [pos[X] for pos in self.nodes]

    @cached_property
    def y(self) -> list[int]:
        return [pos[Y] for pos in self.nodes]

    @cached_property
    def width(self) -> int:
        return max(self.x) - min(self.x) + 1

    @cached_property
    def height(self) -> int:
        return max(self.y) - min(self.y) + 1

    def draw(self):
        result = ""
        for j in range(self.height):
            for i in range(self.width):
                pos = i + min(self.x), j + min(self.y)
                if pos in self.all_nodes:
                    result += self.all_nodes[pos].colored_char
                else:
                    result += " "
            result += "\n"
        print(result)


def get_direction(v1: Vector, v2: Vector) -> Direction:
    if v1[X] == v2[X]:
        return Direction.VERTICAL
    return Direction.HORIZONTAL


def explore(
    map_: Map,
    start_color: Color,
    middle_color: Color,
    direction: Direction,
    visited: set[Vector],
    node: Node,
    action: "Action",
) -> set["Action"]:
    # print(visited)
    actions = set()
    if node.color == start_color:
        actions.add(action)
    else:
        neighbors = [
            n
            for n in node.get_neighbors(map_, direction)
            if n not in visited and n.color in {middle_color, start_color}
        ]
        for neighbor in neighbors:
            next_direction = get_direction(node.position, neighbor.position)
            neighbor_actions = explore(
                map_,
                start_color,
                middle_color,
                next_direction,
                {neighbor, *visited},
                neighbor,
                action.extend(
                    (neighbor.position,),
                ),
            )
            actions.update(neighbor_actions)
    return actions


class Action:
    def __init__(self, path: tuple[Vector]) -> None:
        self.path = path

    def apply_to(self, map_: Map) -> Map:
        color = map_.nodes[self.path[0]].color
        result = map_.clone()
        target_batches = [set(self.path[1:-1])]
        while target_batches:
            batch = target_batches.pop(0)
            next_batch: set[Vector] = set()
            for target in batch:
                node = result.nodes[target]
                next_batch.update(node.get_targets(result, color))
            for target in batch:
                node = result.nodes[target]
                node.color = color
            if next_batch:
                target_batches.append(next_batch)
        return result

    def extend(self, ext: tuple[Vector]) -> "Action":
        return Action((*self.path, *ext))

    def __eq__(self, __value: object) -> bool:
        return self.path == __value.path or self.path == tuple(reversed(__value.path))

    def __hash__(self) -> int:
        if self.path[0] > self.path[-1]:
            return hash(tuple(reversed(self.path)))
        return hash(self.path)

    def __str__(self) -> str:
        return f"<Action {str(self.path)}>"

    def __repr__(self) -> str:
        return str(self)


def solve(map_: Map, actions: list[Action], visited: set[Map]):
    # sleep(0.01)
    # print(actions)
    # map_.draw()

    visited.add(map_)
    if map_.is_solved:
        return actions

    action_neighbor_mapping = {
        action: action.apply_to(map_) for action in map_.get_actions()
    }
    # sort by entrophy and length of action
    action_neighbor_mapping = dict(
        sorted(
            action_neighbor_mapping.items(),
            key=lambda x: (x[1].entrophy, len(x[0].path)),
        )
    )

    for action, neighbor in action_neighbor_mapping.items():
        if neighbor not in visited:
            solution = solve(neighbor, [*actions, action], visited.copy())
            if solution:
                return solution
    return None


def draw_solution(map_: Map, actions: list[Action]):
    m = map_.clone()
    for k, action in enumerate(actions):
        print(f">>>>>>>>> {k+1} >>>>>>>>>")
        result = ""
        for j in range(m.height):
            for i in range(m.width):
                pos = (i + min(m.x), j + min(m.y))
                if pos in action.path:
                    if pos == action.path[0]:
                        char = "S"
                    elif pos == action.path[-1]:
                        char = "E"
                    else:
                        char = "-"
                    result += f"{m.all_nodes[pos].color.value}{char}{ENDC}"
                elif pos in m.all_nodes:
                    char = m.all_nodes[pos].char
                    result += f"{m.all_nodes[pos].color.value}{char}{ENDC}"
                else:
                    result += " "
            result += "\n"
        m = action.apply_to(m)
        print(result)


def main():
    """
    initialize map
    while not solved:
        find one viable action

    """
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
    map_.draw()
    sol = solve(map_, [], set())
    if sol:
        draw_solution(map_, sol)
    else:
        print("No solution")


if __name__ == "__main__":
    main()
