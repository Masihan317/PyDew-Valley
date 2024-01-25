import os
import sys
import pygame

def resource_path(relative_path):
  try:
  # PyInstaller creates a temp folder and stores path in _MEIPASS
    base_path = sys._MEIPASS
  except Exception:
    base_path = os.path.abspath(".")

  return os.path.join(base_path, relative_path)

def import_folder(path):
  surface_list = []

  for _, _, img_files in os.walk(path):
    img_files = sorted(img_files)
    for image in img_files:
      full_path = path + "/" + image
      image_surf = pygame.image.load(full_path).convert_alpha()
      surface_list.append(image_surf)

  return surface_list

def import_folder_dict(path):

  surface_dict = {}

  for _, _, img_files in os.walk(path):
    for image in img_files:
      full_path = path + "/" + image
      image_surf = pygame.image.load(full_path).convert_alpha()
      surface_dict[image.split(".")[0]] = image_surf

  return surface_dict

