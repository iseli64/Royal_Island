""" Quest - An epic journey.

Simple demo that demonstrates PyTMX and pyscroll.

requires pygame and pytmx.

https://github.com/bitcraft/pytmx

pip install pytmx
"""
from __future__ import annotations

from pathlib import Path
from typing import List

import pygame
from pygame.locals import K_UP, K_DOWN, K_LEFT, K_RIGHT, K_MINUS, K_EQUALS, K_ESCAPE
from pygame.locals import KEYDOWN, VIDEORESIZE, QUIT
from pytmx.util_pygame import load_pygame

import pyscroll
import pyscroll.data
from pyscroll.group import PyscrollGroup

import random
import glob

# define configuration variables here
CURRENT_DIR = Path(__file__).parent
RESOURCES_DIR = CURRENT_DIR / "graphics"
HERO_MOVE_SPEED = 200  # pixels per second


# simple wrapper to keep the screen resizeable
def init_screen(width: int, height: int) -> pygame.Surface:
    screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
    return screen


# make loading images a little easier
def load_image(filename: str) -> pygame.Surface:
    return pygame.image.load(str(RESOURCES_DIR / filename))


class Character(pygame.sprite.Sprite):
    """Our Hero

    The Hero has three collision rects, one for the whole sprite "rect" and
    "old_rect", and another to check collisions with walls, called "feet".

    The position list is used because pygame rects are inaccurate for
    positioning sprites; because the values they get are 'rounded down'
    as integers, the sprite would move faster moving left or up.

    Feet is 1/2 as wide as the normal rect, and 8 pixels tall.  This size size
    allows the top of the sprite to overlap walls.  The feet rect is used for
    collisions, while the 'rect' rect is used for drawing.

    There is also an old_rect that is used to reposition the sprite if it
    collides with level walls.
    """

    def __init__(self, name="player_00") -> None:
        super().__init__()
        self.name = name
        self.moving_direction = 0
        self.image = load_image(Path('sprites').joinpath(name + ".png")).convert_alpha()
        self.velocity = [0, 0]
        self._position = [0.0, 0.0]
        self._old_position = self.position
        self.rect = self.image.get_rect()
        self.feet = pygame.Rect(0, 0, self.rect.width * 0.5, 8)

    @property
    def position(self) -> List[float]:
        return list(self._position)

    @position.setter
    def position(self, value: List[float]) -> None:
        self._position = list(value)

    def update(self, dt: float) -> None:
        self._old_position = self._position[:]
        self._position[0] += self.velocity[0] * dt
        self._position[1] += self.velocity[1] * dt
        self.rect.topleft = self._position
        self.feet.midbottom = self.rect.midbottom

    def move_back(self, dt: float) -> None:
        """If called after an update, the sprite can move back"""
        self._position = self._old_position
        self.rect.topleft = self._position
        self.feet.midbottom = self.rect.midbottom

class GameMap:
    map_path = RESOURCES_DIR.joinpath('map') 
    def __init__(self, map, screen, zoom=2, clamp_camera=False, characters=None, hero=None, hero_x=None, hero_y=None):
        tmx_data = load_pygame(self.map_path.joinpath(map))

        self.screen = screen
        """zones = where other island residents are.
        houses = where items are.
        obstacles = ocean 
        """
        self.obstacles = []
        self.houses = []
        self.houses_objs = []
        self.zones = []
        self.zones_objs = []
        self.characters = []
        self.hero_start_position = None

        for layer in tmx_data.layers:
            if layer.name == 'obstacle':
                for obj in layer:
                    self.obstacles.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
            elif layer.name == 'houses':
                for obj in layer:
                    self.houses.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
                    self.houses_objs.append(obj)
            elif layer.name == 'zones':
                for obj in layer:
                    self.zones.append(pygame.Rect(obj.x, obj.y, obj.width, obj.height))
                    self.zones_objs.append(obj)
            elif layer.name == 'hero_start_position':
                for obj in layer:
                    self.hero_start_position = (obj.x, obj.y)
        
        # houses are also exits



        # create new data source for pyscroll
        map_data = pyscroll.data.TiledMapData(tmx_data)

        # create new renderer (camera)
        self.map_layer = pyscroll.BufferedRenderer(
            map_data, screen.get_size(), clamp_camera=clamp_camera, tall_sprites=1
        )
        self.map_layer.zoom = zoom

        # pyscroll supports layered rendering.  our map has 3 'under' layers
        # layers begin with 0, so the layers are 0, 1, and 2.
        # since we want the sprite to be on top of layer 1, we set the default
        # layer for sprites as 2
        self.group = PyscrollGroup(map_layer=self.map_layer, default_layer=2)

        
        self.hero = hero if hero else Character()

        if hero_x and hero_y:
            self.hero._position[0] += hero_x
            self.hero._position[1] += hero_y
        else:
            # put the hero in the center of the map
            self.hero.position = self.map_layer.map_rect.center

        # add our hero to the group
        self.group.add(self.hero)

        if characters:
            self.add_characters(characters)

            for character in self.characters:
                self.group.add(character)

    @property
    def zoom(self):
        return self.map_layer.zoom

    @zoom.setter
    def zoom (self, value: int):
        self.map_layer.zoom = value

    @property
    def clamp_camera(self):
        return self.map_data.clamp_camera

    @clamp_camera.setter
    def clamp_camera(self, value: bool):
        self.map_layer.clamp_camera = value

    def add_characters(self, characters):
        for character in characters:
            self.characters.append(Character(name=character['name']))
            self.characters[-1]._position[0] = character['x']
            self.characters[-1]._position[1] = character['y']
    
            self.group.add(self.characters[-1])

    def draw(self) -> None:

        # center the map/screen on our Hero
    
        self.group.center(self.hero.rect.center)

    # draw the map and all sprites
        self.group.draw(self.screen)

    def move_characters(self) -> None:
        for character in self.characters:
            if random.randint(0, 100) < 70:
                character.moving_direction = 0
            else: 
                character.moving_direction = random.choice([1, 2, 3, 4])
            
            if random.randint(0, 150) == 0:
                if character.moving_direction == 4:
                    character.velocity[0] = HERO_MOVE_SPEED
                elif character.moving_direction == 3:
                    character.velocity[0] = -HERO_MOVE_SPEED
                else:
                    character.velocity[0] =0

                if character.moving_direction == 2:
                    character.velocity[1] = HERO_MOVE_SPEED
                elif character.moving_direction == 1:
                    character.velocity[1] == -HERO_MOVE_SPEED
                else: 
                    character.velocity[1] = 0


    def update(self, dt, current_map) -> str:
        
        map_name = current_map
        
        """Tasks that occur over time should be handled here"""
        self.group.update(dt)

        # check if the sprite's feet are colliding with wall
        # sprite must have a rect called feet, and move_back method,
        # otherwise this will fail
        for sprite in self.group.sprites():
            if sprite.feet.collidelist(self.obstacles) > -1:
                sprite.move_back(dt)
            
            house_collision = sprite.feet.collidelist(self.houses)
        
            if house_collision > -1 and sprite.name == "Player_00":
                map_name = self.houses_objs[house_collision].name

        return map_name        




class QuestGame:
    """This class is a basic game.

    This class will load data, create a pyscroll group, a hero object.
    It also reads input and moves the Hero around the map.
    Finally, it uses a pyscroll group to render the map and Hero.
    """

    map_path = RESOURCES_DIR.joinpath('map').joinpath('island_map.tmx')

    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen

        # true while running
        self.running = False

        # Characters
        characters = [
            {"name": "ariel_00", "x": 1335, "y": 600},
            {"name": "aladdin_00", "x": 322, "y": 450},
            {"name": "tiana_00", "x": 1208, "y": 328},
            {"name": "pirategirl_00", "x": 834, "y": 954},
        ]

        #maps
        maps = glob.glob('**/*.tmx', recursive=True)
        self.maps = {}
        for map in maps:
            map_name = Path(map).name
            self.maps[map_name] = GameMap(map_name, screen, hero=Character())

            if map_name == 'island_map.tmx':
                self.maps[map_name].add_characters(characters)
            else:
                self.maps[map_name].hero._position[0] = self.maps[map_name].hero_start_position[0]
                self.maps[map_name].hero._position[1] = self.maps[map_name].hero_start_position[1]
                self.maps[map_name].zoom = 1
                self.maps[map_name].clamp_camera = True

            self.current_map = 'island_map.tmx'

        
    def handle_input(self) -> None:
        """Handle pygame input events"""
        poll = pygame.event.poll

        event = poll()
        while event:
            if event.type == QUIT:
                self.running = False
                break

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.running = False
                    break

                elif event.key == K_EQUALS:
                    self.maps[self.current_map].map_layer.zoom += 0.25

                elif event.key == K_MINUS:
                    value = self.maps[self.current_map].map_layer.zoom - 0.25
                    if value > 0:
                        self.maps[self.current_map].map_layer.zoom = value

            # this will be handled if the window is resized
            elif event.type == VIDEORESIZE:
                self.screen = init_screen(event.w, event.h)
                self.maps[self.current_map].map_layer.set_size((event.w, event.h))

            event = poll()

        # using get_pressed is slightly less accurate than testing for events
        # but is much easier to use.
        pressed = pygame.key.get_pressed()
        if pressed[K_UP]:
            self.maps[self.current_map].hero.velocity[1] = -HERO_MOVE_SPEED
        elif pressed[K_DOWN]:
            self.maps[self.current_map].hero.velocity[1] = HERO_MOVE_SPEED
        else:
            self.maps[self.current_map].hero.velocity[1] = 0

        if pressed[K_LEFT]:
            self.maps[self.current_map].hero.velocity[0] = -HERO_MOVE_SPEED
        elif pressed[K_RIGHT]:
            self.maps[self.current_map].hero.velocity[0] = HERO_MOVE_SPEED
        else:
            self.maps[self.current_map].hero.velocity[0] = 0

    
    def run(self):
        """Run the game loop"""
        clock = pygame.time.Clock()
        self.running = True

        from collections import deque

        times = deque(maxlen=30)

        try:
            while self.running:
                dt = clock.tick() / 1000.0
                times.append(clock.get_fps())

                self.handle_input()
                self.maps[self.current_map].move_characters()
                
                new_map = self.maps[self.current_map].update(dt, self.current_map)
                if new_map != self.current_map:
                    if self.maps[new_map].hero_start_position:
                        self.maps[new_map].hero._position[0] = self.maps[new_map].hero_start_position[0]
                        self.maps[new_map].hero._position[1] = self.maps[new_map].hero_start_position[1]
                
                    self.current_map = new_map
                
                self.maps[self.current_map].draw()
                pygame.display.flip()

        except KeyboardInterrupt:
            self.running = False


def main() -> None:
    pygame.init()
    pygame.font.init()
    screen = init_screen(800, 600)
    pygame.display.set_caption("Quest - An epic journey.")

    try:
        game = QuestGame(screen)
        game.run()
    except KeyboardInterrupt:
        pass
    finally:
        pygame.quit()


if __name__ == "__main__":
    main()
