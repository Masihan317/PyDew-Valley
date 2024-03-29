import pygame
from settings import *
from pytmx.util_pygame import load_pygame
from support import *
from random import choice

class SoilTile(pygame.sprite.Sprite):
  def __init__(self, pos, surf, groups) -> None:
    super().__init__(groups)
    self.image = surf
    self.rect = self.image.get_rect(topleft = pos)
    self.z = LAYERS["soil"]

class WaterTile(pygame.sprite.Sprite):
  def __init__(self, pos, surf, groups) -> None:
    super().__init__(groups)
    self.image = surf
    self.rect = self.image.get_rect(topleft = pos)
    self.z = LAYERS["soil water"]

class Plant(pygame.sprite.Sprite):
  def __init__(self, plant_type, groups, soil, check_watered) -> None:
    super().__init__(groups)

    # setup
    self.plant_type = plant_type
    self.frames = import_folder(resource_path(f"./graphics/fruit/{plant_type}"))
    self.soil = soil
    self.check_watered = check_watered

    # plant growth
    self.age = 0
    self.max_age = len(self.frames) - 1
    self.grow_speed = GROW_SPEED[plant_type]
    self.ready = False

    # sprite setup
    self.image = self.frames[self.age]
    self.y_offset = -16 if plant_type == "corn" else -8
    self.rect = self.image.get_rect(midbottom = soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))
    self.z = LAYERS["ground plant"]

  def grow(self):
    if self.check_watered(self.rect.center):
      self.age += self.grow_speed

      if int(self.age) > 0:
        self.z = LAYERS["main"]
        self.hitbox = self.rect.copy().inflate(-26, -self.rect.height * 0.4)

      if self.age >= self.max_age:
        self.age = self.max_age
        self.ready = True

      self.image = self.frames[int(self.age)]
      self.rect = self.image.get_rect(midbottom = self.soil.rect.midbottom + pygame.math.Vector2(0, self.y_offset))

class SoilLayer:
  def __init__(self, all_sprites, collision_sprites) -> None:

    # sprite groups
    self.all_sprites = all_sprites
    self.collision_sprites = collision_sprites
    self.soil_sprites = pygame.sprite.Group()
    self.water_sprites = pygame.sprite.Group()
    self.plant_sprites = pygame.sprite.Group()

    # graphics
    self.soil_surfs = import_folder_dict(resource_path("./graphics/soil/"))
    self.water_surfs = import_folder(resource_path("./graphics/soil_water"))

    self.create_soil_grid()
    self.create_hit_rects()

    # sounds
    self.hoe_sound = pygame.mixer.Sound(resource_path("./audio/hoe.wav"))
    self.hoe_sound.set_volume(0.1)

    self.plant_sound = pygame.mixer.Sound(resource_path("./audio/plant.wav"))
    self.hoe_sound.set_volume(0.1)

  def create_soil_grid(self):
    ground = pygame.image.load(resource_path("./graphics/world/ground.png"))
    h_tiles, v_tiles = ground.get_width() // TILE_SIZE, ground.get_height() // TILE_SIZE

    self.grid = [[[] for col in range(h_tiles)] for row in range(v_tiles)]
    for x, y, _ in load_pygame(resource_path("./data/map.tmx")).get_layer_by_name("Farmable").tiles():
      self.grid[y][x].append("F")

  def create_hit_rects(self):
    self.hit_rects = []
    for index_row, row in enumerate(self.grid):
      for index_col, cell in enumerate(row):
        if "F" in cell:
          x = index_col * TILE_SIZE
          y = index_row * TILE_SIZE
          rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
          self.hit_rects.append(rect)

  def get_hit(self, point):
    for rect in self.hit_rects:
      if rect.collidepoint(point):
        self.hoe_sound.play()

        x = rect.x // TILE_SIZE
        y = rect.y // TILE_SIZE
        if "F" in self.grid[y][x]:
          self.grid[y][x].append("X")
          self.create_soil_tiles()
          if self.raining:
            self.water_all()

  def water(self, target_pos):
    for soil_sprite in self.soil_sprites.sprites():
      if soil_sprite.rect.collidepoint(target_pos):

        # add an entry to the soil grid -> "W"
        x = soil_sprite.rect.x // TILE_SIZE
        y = soil_sprite.rect.y // TILE_SIZE
        self.grid[y][x].append("W")

        # create a water sprite
        WaterTile(
          pos = soil_sprite.rect.topleft,
          surf = choice(self.water_surfs),
          groups = [self.all_sprites, self.water_sprites]
        )

  def water_all(self):
    for index_row, row in enumerate(self.grid):
      for index_col, cell in enumerate(row):
        if "X" in cell and "W" not in cell:
          cell.append("W")
          x = index_col * TILE_SIZE
          y = index_row * TILE_SIZE
          WaterTile((x, y), choice(self.water_surfs), [self.all_sprites, self.water_sprites])

  def remove_water(self):

    # destroy all water sprites
    for sprite in self.water_sprites.sprites():
      sprite.kill()

    # clean up the grid
    for row in self.grid:
      for cell in row:
        if "W" in cell:
          cell.remove("W")

  def check_watered(self, pos):
    x = pos[0] // TILE_SIZE
    y = pos[1] // TILE_SIZE
    cell = self.grid[y][x]
    is_watered = "W" in cell
    return is_watered

  def plant_seed(self, target_pos, seed):
    for soil_sprite in self.soil_sprites.sprites():
      if soil_sprite.rect.collidepoint(target_pos):
        self.plant_sound.play()

        x = soil_sprite.rect.x // TILE_SIZE
        y = soil_sprite.rect.y // TILE_SIZE

        if "P" not in self.grid[y][x]:
          self.grid[y][x].append("P")
          Plant(seed, [self.all_sprites, self.plant_sprites, self.collision_sprites], soil_sprite, self.check_watered)

  def update_plants(self):
    for plant in self.plant_sprites.sprites():
      plant.grow()

  def create_soil_tiles(self):
    self.soil_sprites.empty()
    for index_row, row in enumerate(self.grid):
      for index_col, cell in enumerate(row):
        if "X" in cell:

          # tile options
          top = "X" in self.grid[index_row - 1][index_col]
          bottom = "X" in self.grid[index_row + 1][index_col]
          right = "X" in self.grid[index_row][index_col + 1]
          left = "X" in self.grid[index_row][index_col - 1]

          tile_type = "o"

          # all sides
          if all((top, bottom, left, right)): tile_type = "x"

          # horizontal tiles only
          if left and not any((top, right, bottom)): tile_type = "r"
          if right and not any((top, left, bottom)): tile_type = "l"
          if left and right and not any((top, bottom)): tile_type = "lr"

          # vertical tiles only
          if top and not any((left, right, bottom)): tile_type = "b"
          if bottom and not any((left, right, top)): tile_type = "t"
          if top and bottom and not any((left, right)): tile_type = "tb"

          # corners
          if left and bottom and not any((right, top)): tile_type = "tr"
          if right and bottom and not any((left, top)): tile_type = "tl"
          if left and top and not any((right, bottom)): tile_type = "br"
          if right and top and not any((left, bottom)): tile_type = "bl"

          # t shapes
          if all((top, bottom, right)) and not left: tile_type = "tbr"
          if all((top, bottom, left)) and not right: tile_type = "tbl"
          if all((left, right, top)) and not bottom: tile_type = "lrb"
          if all((left, right, bottom)) and not top: tile_type = "lrt"

          SoilTile(
            pos = (index_col * TILE_SIZE, index_row * TILE_SIZE),
            surf = self.soil_surfs[tile_type],
            groups = [self.all_sprites, self.soil_sprites]
          )