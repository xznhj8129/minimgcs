# instruments.py
import math
import pygame
from PyQt5.QtWidgets import QLabel, QVBoxLayout, QWidget
from PyQt5.QtGui import QImage, QPixmap
from shared_data import shared_data

class ArtificialHorizonIndicator(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        #self.setFixedSize(400, 300)
        self.horizon_surface = pygame.Surface((400, 300))
        self.horizon_label = QLabel(self)
        self.initUI()

    def initUI(self):
        layout = QVBoxLayout(self)
        layout.addWidget(self.horizon_label)
        self.setLayout(layout)
        pygame.init()
        self.update_horizon()

    def draw_horizon(self, pitch, roll):
        center_x = 200
        center_y = 150

        # Blue sky and green ground
        self.horizon_surface.fill((0, 0, 255))
        pygame.draw.rect(self.horizon_surface, (0, 255, 0), (0, center_y, 400, 150))

        # Calculate horizon line points
        roll_rad = math.radians(roll)
        pitch_rad = math.radians(pitch)
        horizon_y = center_y + math.tan(pitch_rad) * center_y
        roll_offset = math.tan(roll_rad) * center_x

        points = [
            (0, horizon_y - roll_offset),
            (400, horizon_y + roll_offset),
            (400, 300),
            (0, 300)
        ]

        pygame.draw.polygon(self.horizon_surface, (0, 255, 0), points)

        # Draw horizon line
        pygame.draw.line(self.horizon_surface, (255, 255, 255), (0, horizon_y - roll_offset), (400, horizon_y + roll_offset), 2)

    def draw_aircraft_symbol(self):
        center_x = 200
        center_y = 150

        # Aircraft symbol
        pygame.draw.line(self.horizon_surface, (255, 255, 255), (center_x - 10, center_y), (center_x + 10, center_y), 2)
        pygame.draw.line(self.horizon_surface, (255, 255, 255), (center_x, center_y - 10), (center_x, center_y + 10), 2)

    def draw_markings(self, pitch, roll, heading, speed, vspd):
        center_x = 200
        center_y = 150

        # Pitch markings
        for i in range(-90, 91, 10):
            offset_y = center_y - i * 10 + pitch * 10
            if 0 <= offset_y <= 300:
                pygame.draw.line(self.horizon_surface, (255, 255, 255), (center_x - 20, offset_y), (center_x + 20, offset_y), 2)
                font = pygame.font.Font(None, 24)
                text = font.render(f"{i}°", True, (255, 255, 255))
                self.horizon_surface.blit(text, (center_x + 25, offset_y - 10))

    def update_horizon(self):
        pitch = shared_data.pitch * -180 / math.pi
        roll = shared_data.roll * 180 / math.pi
        heading = shared_data.yaw * 180 / math.pi
        speed = shared_data.gspd
        vspd = shared_data.vspd

        self.draw_horizon(pitch, roll)
        self.draw_aircraft_symbol()
        self.draw_markings(pitch, roll, heading, speed, vspd)

        horizon_bytes = pygame.image.tostring(self.horizon_surface, 'RGB')
        horizon_image = QImage(horizon_bytes, 400, 300, QImage.Format_RGB888)
        self.horizon_label.setPixmap(QPixmap.fromImage(horizon_image))

    def update(self):
        self.update_horizon()
