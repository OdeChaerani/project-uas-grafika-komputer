import pygame
import numpy as np
import math
import random
import time

# ============ Pengaturan Pygame ============
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
SIM_SIZE = 600
INFO_WIDTH = SCREEN_WIDTH - SIM_SIZE
FPS = 60
pygame.init()

# Tambahkan bendera SCALED untuk rendering yang lebih baik dan penanganan alpha
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Simulasi Deforestasi 2D")
clock = pygame.time.Clock()

# ========== WARNA (Diadaptasi untuk tampilan yang lebih halus) ==========
COLOR_WHITE = (255, 255, 255)
COLOR_BLACK = (0, 0, 0)
COLOR_DARK_BLUE = (28, 42, 52) 
COLOR_UI_DARK = (40, 60, 74) 
COLOR_UI_BORDER = (85, 120, 140)
COLOR_UI_HIGHLIGHT = (140, 190, 220) 
COLOR_BUTTON_NORMAL = (60, 90, 110)
COLOR_BUTTON_HOVER = (80, 120, 140)
COLOR_BUTTON_DANGER = (200, 60, 60)
COLOR_BUTTON_DANGER_HOVER = (230, 80, 80)
COLOR_BUTTON_SAFE = (70, 200, 70)
COLOR_BUTTON_SAFE_HOVER = (90, 220, 90)
COLOR_BUTTON_RESET = (200, 150, 50)
COLOR_BUTTON_RESET_HOVER = (230, 180, 70)

# Terrain Colors
COLOR_SOIL = (150, 90, 40) 
COLOR_DEFORESTED = (160, 100, 50)
COLOR_HEALTHY_GRASS = (90, 180, 80) 
COLOR_CANOPY_BASE = (30, 100, 40) 
COLOR_STUMP_TOP = (180, 130, 90)

# Disaster/Water Colors
COLOR_WARNING = (255, 165, 0)
COLOR_DANGER = (255, 50, 50)
COLOR_SAFE = (70, 200, 70)
COLOR_WATER = (90, 140, 180) 
COLOR_DEEP_WATER = (60, 100, 130) 
COLOR_DRY = (180, 120, 80) 
COLOR_RAIN = (120, 180, 220, 150) 
COLOR_FLOOD = (50, 100, 160) 
COLOR_STORM_CLOUD = (40, 50, 60, 180) # Awan gelap untuk hujan

# ============ Font (Dikecilkan) ============
font_name = pygame.font.match_font('segoeui') or pygame.font.match_font('arial')
FONT_SMALL = pygame.font.Font(font_name, 16) 
FONT_MEDIUM = pygame.font.Font(font_name, 20) 
FONT_LARGE = pygame.font.Font(font_name, 30) 
FONT_TINY = pygame.font.Font(font_name, 12)

# ============ Kelas Tombol UI ============
class Button:
    def __init__(self, x, y, w, h, text, font, color, hover_color, action):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.action = action
        self.is_hovered = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return self.action
        return None

    def draw(self, surface):
        current_color = self.hover_color if self.is_hovered else self.color
        
        # Gambar bayangan/border (sedikit)
        # Catatan: pygame.draw.rect mendukung border_radius
        pygame.draw.rect(surface, COLOR_BLACK, self.rect.inflate(2, 2), border_radius=5)
        
        # Gambar tombol
        # Catatan: pygame.draw.rect mendukung border_radius
        pygame.draw.rect(surface, current_color, self.rect, border_radius=5)
        
        # Teks tombol
        text_surf = self.font.render(self.text, True, COLOR_WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        surface.blit(text_surf, text_rect)

# ============ Utilitas Drawing ============
def clamp(v, a, b): return max(a, min(b, v))

def lerp_color(c1, c2, t):
    t = clamp(t, 0, 1)
    return (int(c1[0]+(c2[0]-c1[0])*t), int(c1[1]+(c2[1]-c1[1])*t), int(c1[2]+(c2[2]-c1[2])*t))

def draw_shadow(surf, x, y, width, scale=1.0):
    w = int(width * scale)
    h = int(width * 0.25 * scale)
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.ellipse(s, (0, 0, 0, 60), (0, 0, w, h))
    surf.blit(s, (x - w//2, y - h//2 + 5))

def smooth_noise(x, seed=12345):
    """Interpolasi cosinus sederhana untuk nilai noise yang halus."""
    t = x % 1
    t = t * t * (3 - 2 * t)
    
    # Fungsi hash sederhana
    def hash_func(val):
        return (val * 15731 + seed + 1376312589) & 0x7fffffff

    n0 = hash_func(int(x)) 
    n1 = hash_func(int(x) + 1)
    
    # Normalisasi ke [0, 1]
    val0 = (n0 / 2147483647.0) 
    val1 = (n1 / 2147483647.0)

    return val0 * (1 - t) + val1 * t

# ============ Kelas Partikel 2D ============
class Particle:
    def __init__(self, x, y, color, lifetime, size_range=(2, 5), gravity=300.0, vel_y_range=(-150, -80)):
        self.pos = np.array([x, y], dtype=float)
        self.vel = np.array([random.uniform(-50, 50), random.uniform(*vel_y_range)], dtype=float) 
        self.color = color
        self.lifetime = lifetime
        self.age = 0
        self.size = random.uniform(*size_range)
        self.gravity = gravity
    
    def update(self, dt_ms):
        dt = dt_ms / 1000.0
        self.age += dt
        self.vel[1] += self.gravity * dt
        self.pos += self.vel * dt
        return self.age < self.lifetime
    
    def draw(self, surface):
        alpha = int(255 * (1.0 - (self.age / self.lifetime)))
        if len(self.color) == 4:
            color_with_alpha = self.color[:3] + (min(255, alpha + self.color[3]),)
        else:
             color_with_alpha = self.color + (alpha,)

        try:
            size_int = int(self.size * 2) + 1
            temp_surface = pygame.Surface((size_int, size_int), pygame.SRCALPHA)
            temp_surface.fill((0, 0, 0, 0))
            pygame.draw.circle(temp_surface, color_with_alpha, 
                             (size_int // 2, size_int // 2), int(self.size))
            surface.blit(temp_surface, (self.pos[0] - self.size, self.pos[1] - self.size))
        except:
            if alpha > 128:
                 pygame.draw.circle(surface, self.color[:3], (int(self.pos[0]), int(self.pos[1])), int(self.size))

class RainDrop(Particle):
    def __init__(self, x, y, size):
        super().__init__(x, y, COLOR_RAIN, random.uniform(0.5, 1.5), size_range=(size, size), 
                         gravity=1500.0, vel_y_range=(300, 500)) 
        # Kecepatan hujan yang lebih miring ke kanan (untuk visual)
        self.vel = np.array([random.uniform(50, 100), random.uniform(300, 500)], dtype=float)
        
    def draw(self, surface):
        start_pos = self.pos
        # Garis hujan miring
        end_pos = self.pos + np.array([-10, 20]) 
        pygame.draw.line(surface, self.color[:3], (int(start_pos[0]), int(start_pos[1])), 
                         (int(end_pos[0]), int(end_pos[1])), 1)

class Cloud:
    def __init__(self, x, y, size, speed, color):
        self.x = x
        self.y = y
        self.size = size
        self.speed = speed
        self.color = color
        self.width = self.size * 2
        self.height = self.size * 0.8
    
    def update(self, dt_ms):
        dt = dt_ms / 1000.0
        self.x += self.speed * dt
        if self.x > SIM_SIZE + self.width:
            self.x = -self.width
            self.y = random.uniform(0, SIM_SIZE * 0.2)
            self.size = random.uniform(50, 150)
            self.width = self.size * 2
            self.height = self.size * 0.8
            
    def draw(self, surface):
        s = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        s.fill((0, 0, 0, 0))
        
        # Gambar bentuk awan. Menghapus 'border_radius' karena tidak didukung oleh ellipse.
        pygame.draw.ellipse(s, self.color, (0, 0, self.width, self.height))
        pygame.draw.circle(s, self.color, (int(self.width * 0.25), int(self.height * 0.5)), int(self.height * 0.7))
        pygame.draw.circle(s, self.color, (int(self.width * 0.75), int(self.height * 0.6)), int(self.height * 0.8))
        
        surface.blit(s, (self.x - self.width / 2, self.y - self.height / 2))

# ============ Kelas Utama Simulasi 2D ============
class DeforestationSimulation:
    def __init__(self):
        self.terrain_grid = 20
        self.cell_size = SIM_SIZE // self.terrain_grid
        
        # States untuk visual bencana
        self.quake_offset_x = 0
        self.quake_offset_y = 0
        self.lightning_active = 0.0 # Durasi kilat
        
        self.initialize_state()
        self.setup_ui() 
        print("Simulasi Deforestasi 2D dengan gaya halus telah diinisialisasi.")
        
    def initialize_state(self):
        """Mengatur ulang semua variabel simulasi ke kondisi awal."""
        self.deforestation_map = np.ones((self.terrain_grid, self.terrain_grid)) * 0.9 
        self.erosion_risk = 0.0
        self.particles = []
        self.rain_particles = [] 
        self.trees = [] 
        self.stumps = [] 
        self.river_path = set() 
        self.river_flooded_path = set() 
        self.river_width_grid = 2 
        
        self.disaster_active = False
        self.disaster_type = None
        self.disaster_timer = 0
        self.disaster_cooldown = 0
        self.disaster_visual_intensity = 0.0 
        self.warning_flash = 0.0
        
        self.is_raining = False
        self.rain_timer = 0.0 
        self.rain_duration = 5.0 # Durasi hujan yang lebih panjang
        
        self.total_disasters = 0
        self.trees_lost_to_disaster = 0
        
        # Diperbanyak: 5 Awan
        self.clouds = [
            Cloud(random.uniform(0, SIM_SIZE), random.uniform(10, 80), random.uniform(80, 150), random.uniform(20, 50), (200, 200, 200, 150)),
            Cloud(random.uniform(0, SIM_SIZE), random.uniform(50, 120), random.uniform(100, 200), random.uniform(10, 30), (220, 220, 220, 120)),
            Cloud(random.uniform(0, SIM_SIZE), random.uniform(20, 100), random.uniform(70, 130), random.uniform(15, 40), (210, 210, 210, 130)),
            Cloud(random.uniform(0, SIM_SIZE), random.uniform(60, 140), random.uniform(90, 180), random.uniform(25, 55), (230, 230, 230, 100)),
            Cloud(random.uniform(0, SIM_SIZE), random.uniform(0, 50), random.uniform(60, 120), random.uniform(10, 25), (190, 190, 190, 160)),
        ]

        self.initialize_forest()
        self.current_mode = 'plant_single' # Mode default
        
    def reset_simulation(self):
        """Memanggil inisialisasi status untuk mengatur ulang simulasi."""
        self.initialize_state()
        print("\n=== SIMULASI DIRESET KE KONDISI AWAL ===")


    def setup_ui(self):
        """Membuat dan menyimpan objek tombol UI sekali (tanpa posisi Y tetap)."""
        self.buttons = []
        
        # Posisi relatif di panel info (SIM_SIZE hingga SCREEN_WIDTH)
        x_start_panel = SIM_SIZE + 10 
        width_max = INFO_WIDTH - 20 
        button_h = 35 
        
        # Posisi Y akan ditetapkan secara dinamis di draw_info_panel
        DUMMY_Y = 0 
        
        # Tombol 1: Tanam Pohon
        btn_plant = Button(x_start_panel, DUMMY_Y, width_max, button_h, 
                           "🌱 Tanam Pohon (Mode Klik)", FONT_SMALL, 
                           COLOR_BUTTON_SAFE, COLOR_BUTTON_SAFE_HOVER, 'plant_single')
        self.buttons.append(btn_plant)
        
        # Tombol 2: Tebang Pohon Tunggal
        btn_cut = Button(x_start_panel, DUMMY_Y, width_max, button_h, 
                         "🔪 Tebang Pohon (Mode Klik)", FONT_SMALL, 
                         COLOR_BUTTON_NORMAL, COLOR_BUTTON_HOVER, 'cut_single')
        self.buttons.append(btn_cut)
        
        # Tombol 3: Tebang 20%
        btn_cut_mass = Button(x_start_panel, DUMMY_Y, width_max, button_h, 
                              "🔥 Tebang 20% Pohon (Massal)", FONT_SMALL, 
                              COLOR_BUTTON_DANGER, COLOR_BUTTON_DANGER_HOVER, 'cut_mass')
        self.buttons.append(btn_cut_mass)

        # Tombol 4: Reset Simulasi (lebih tinggi 5px)
        btn_reset = Button(x_start_panel, DUMMY_Y, width_max, button_h + 5, 
                           "🔄 RESET SIMULASI", FONT_MEDIUM, 
                           COLOR_BUTTON_RESET, COLOR_BUTTON_RESET_HOVER, 'reset')
        self.buttons.append(btn_reset)

    def _reposition_buttons(self, y_start):
        """Reposisi tombol berdasarkan posisi Y yang diberikan."""
        current_y = y_start
        button_spacing = 8 # Spasi vertikal antar tombol
        
        # Tombol 1: Tanam Pohon (H: 35)
        self.buttons[0].rect.y = current_y
        current_y += self.buttons[0].rect.height + button_spacing
        
        # Tombol 2: Tebang Pohon Tunggal (H: 35)
        self.buttons[1].rect.y = current_y
        current_y += self.buttons[1].rect.height + button_spacing
        
        # Tombol 3: Tebang 20% (H: 35)
        self.buttons[2].rect.y = current_y
        current_y += self.buttons[2].rect.height + button_spacing

        # Tombol 4: Reset Simulasi (H: 40)
        current_y += 10 # Spasi ekstra sebelum tombol reset
        self.buttons[3].rect.y = current_y
        current_y += self.buttons[3].rect.height + button_spacing 
        
        return current_y # Mengembalikan posisi Y setelah tombol terakhir

    def initialize_river(self):
        """Membuat jalur sungai yang meliuk dari kiri atas ke kanan bawah."""
        start_i, start_j = 1, 1 # Top-left start
        end_i, end_j = self.terrain_grid - 2, self.terrain_grid - 2 # Bottom-right end

        noise_scale = 0.2
        amplitude = 5
        current_j = start_j
        
        center_path = set()
        
        for i in range(start_i, end_i + 1):
            # Hitung noise offset
            noise_val = smooth_noise(i * noise_scale) 
            
            # Interpolasi target j secara diagonal
            j_trend = int(start_j + (end_j - start_j) * ((i - start_i) / (end_i - start_i)))
            
            # Terapkan noise untuk berkelok-kelok
            j_offset = int((noise_val * 2 - 1) * amplitude)
            next_j = max(1, min(self.terrain_grid - 2, j_trend + j_offset))

            # Isi sel di antara current_j dan next_j
            for j_step in range(min(current_j, next_j), max(current_j, next_j) + 1):
                center_path.add((i, j_step))

            current_j = next_j
        
        full_river_area = set()
        max_river_width_grid = self.river_width_grid
        
        for j in range(self.terrain_grid):
            for i in range(self.terrain_grid):
                min_dist_sq = float('inf')
                
                for ri, rj in center_path:
                    dist_sq = (i - ri)**2 + (j - rj)**2
                    min_dist_sq = min(min_dist_sq, dist_sq)
                
                if min_dist_sq <= max_river_width_grid**2:
                    full_river_area.add((i, j))

        self.river_path = full_river_area
        
        for (i, j) in self.river_path:
            self.deforestation_map[j, i] = 0.0 # Pastikan sungai tidak memiliki vegetasi

    def initialize_forest(self):
        self.initialize_river() 
        for _ in range(200): 
            gx = random.randint(1, self.terrain_grid - 2)
            gy = random.randint(1, self.terrain_grid - 2)
            
            if (gx, gy) not in self.river_path:
                self.add_tree_by_grid(gx, gy)
        self.update_erosion_risk()
    
    def grid_to_pixel(self, gx, gy):
        x = gx * self.cell_size + self.cell_size // 2
        y = gy * self.cell_size + self.cell_size // 2
        return x, y
        
    def add_tree_by_grid(self, gx, gy):
        if (gx, gy) in self.river_path:
            return
        
        if any(t['gx'] == gx and t['gy'] == gy for t in self.trees):
            return

        px, py = self.grid_to_pixel(gx, gy)
        self.trees.append({'x': px, 'y': py, 'gx': gx, 'gy': gy, 'health': 1.0, 'is_dying': False})
        self.stumps = [s for s in self.stumps if s['gx'] != gx or s['gy'] != gy]

        for i in range(-1, 2):
            for j in range(-1, 2):
                nx, ny = gx + i, gy + j
                if 0 <= nx < self.terrain_grid and 0 <= ny < self.terrain_grid:
                    if (nx, ny) not in self.river_path:
                        if i == 0 and j == 0:
                            self.deforestation_map[ny, nx] = 1.0
                        else:
                            self.deforestation_map[ny, nx] = max(self.deforestation_map[ny, nx], 0.7)

        self.update_erosion_risk()
    
    def remove_tree_by_pixel(self, px, py):
        if not self.trees:
            return False
        
        min_dist_sq = float('inf')
        nearest_idx = -1
        
        for i, tree_data in enumerate(self.trees):
            dist_sq = (tree_data['x'] - px)**2 + (tree_data['y'] - py)**2
            if dist_sq < min_dist_sq:
                min_dist_sq = dist_sq
                nearest_idx = i
        
        if nearest_idx >= 0 and min_dist_sq < (self.cell_size * 1.5)**2: 
            tree_data = self.trees.pop(nearest_idx)
            
            self.stumps.append({'x': tree_data['x'], 'y': tree_data['y'], 
                                'gx': tree_data['gx'], 'gy': tree_data['gy']})

            self.create_debris_effect(tree_data['x'], tree_data['y'], 
                                      color_tuple=(120, 80, 40), size_range=(3, 7))
            
            gx, gy = tree_data['gx'], tree_data['gy']
            
            for i in range(-1, 2):
                for j in range(-1, 2):
                    nx, ny = gx + i, gy + j
                    if 0 <= nx < self.terrain_grid and 0 <= ny < self.terrain_grid:
                        if (nx, ny) not in self.river_path:
                            if i == 0 and j == 0:
                                self.deforestation_map[ny, nx] = 0.0
                            else:
                                self.deforestation_map[ny, nx] = min(self.deforestation_map[ny, nx], 0.3)
            
            self.update_erosion_risk()
            return True
        return False

    def remove_20_percent_trees(self):
        if not self.trees:
            return

        num_to_remove = int(len(self.trees) * 0.20)
        trees_removed = 0

        trees_to_remove = random.sample(self.trees, min(num_to_remove, len(self.trees)))
        
        temp_trees = self.trees[:]
        new_trees = []
        
        for tree_data in temp_trees:
            if tree_data in trees_to_remove:
                self.stumps.append({'x': tree_data['x'], 'y': tree_data['y'], 
                                    'gx': tree_data['gx'], 'gy': tree_data['gy']})

                self.create_debris_effect(tree_data['x'], tree_data['y'], 
                                          color_tuple=(120, 80, 40), size_range=(3, 7))
                
                gx, gy = tree_data['gx'], tree_data['gy']
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        nx, ny = gx + i, gy + j
                        if 0 <= nx < self.terrain_grid and 0 <= ny < self.terrain_grid:
                            if (nx, ny) not in self.river_path:
                                if i == 0 and j == 0:
                                    self.deforestation_map[ny, nx] = 0.0
                                else:
                                    self.deforestation_map[ny, nx] = min(self.deforestation_map[ny, nx], 0.3)
                trees_removed += 1
            else:
                new_trees.append(tree_data)

        self.trees = new_trees
        self.update_erosion_risk()
        print(f"!!! Penebangan Massal: {trees_removed} pohon ditebang (20% dari total) !!!")

    def update_erosion_risk(self):
        non_river_area = 0
        total_non_river_coverage = 0
        for j in range(self.terrain_grid):
            for i in range(self.terrain_grid):
                if (i, j) not in self.river_path:
                    non_river_area += 1
                    total_non_river_coverage += self.deforestation_map[j, i]
        
        if non_river_area > 0:
            forest_coverage = total_non_river_coverage / non_river_area
        else:
            forest_coverage = 0.0

        self.erosion_risk = 1.0 - forest_coverage
        self.erosion_risk = clamp(self.erosion_risk, 0.0, 1.0)
        
        if self.erosion_risk < 0.3:
            self.warning_level = 0
        elif self.erosion_risk < 0.5:
            self.warning_level = 1
        elif self.erosion_risk < 0.7:
            self.warning_level = 2
        else:
            self.warning_level = 3
    
    def update(self, dt_ms):
        dt = dt_ms / 1000.0
        self.warning_flash = (self.warning_flash + dt * 3) % (2 * math.pi)
        self.lightning_active = max(0.0, self.lightning_active - dt)
        
        # Update Clouds
        for cloud in self.clouds:
            cloud.update(dt_ms)
            
        self.particles = [p for p in self.particles if p.update(dt_ms)]
        self.rain_particles = [p for p in self.rain_particles if p.update(dt_ms)]
        
        if self.is_raining:
            self.rain_timer += dt
            
            # Pemicu kilat yang lebih realistis
            if random.random() < 0.005 and self.lightning_active == 0.0: 
                self.lightning_active = 0.1 # Kilat berlangsung 0.1 detik
                self.quake_offset_x = random.uniform(-3, 3) 
                self.quake_offset_y = random.uniform(-3, 3)
            
            # Spawn hujan
            if random.random() < 0.8:
                self.rain_particles.append(RainDrop(random.randint(0, SIM_SIZE), 
                                                 random.randint(0, SIM_SIZE), 
                                                 random.uniform(1, 2)))
            
            if self.rain_timer >= self.rain_duration:
                self.is_raining = False
                self.rain_timer = 0.0
                self.disaster_active = True
                self.disaster_timer = random.uniform(5, 8)
                self.total_disasters += 1
                self.disaster_visual_intensity = 1.0
                self.execute_disaster(is_wet_phase=True)
                print(f"!!! BENCANA AKTIF: {self.disaster_type.upper()} !!!")
            return 

        if self.disaster_active:
            self.disaster_timer -= dt
            self.disaster_visual_intensity = max(0.0, min(1.0, self.disaster_timer / 7.0)) 
            
            if self.lightning_active > 0:
                # Guncangan karena kilat yang baru saja terjadi
                pass
            elif self.disaster_type == 'earthquake':
                self.quake_offset_x = random.uniform(-5, 5) * self.disaster_visual_intensity
                self.quake_offset_y = random.uniform(-5, 5) * self.disaster_visual_intensity
            else:
                self.quake_offset_x = 0
                self.quake_offset_y = 0

            if self.disaster_timer <= 0:
                self.disaster_active = False
                self.disaster_cooldown = 10.0
                self.disaster_visual_intensity = 0.0
                self.river_flooded_path.clear()
                self.quake_offset_x = 0
                self.quake_offset_y = 0
        else:
            self.disaster_cooldown = max(0, self.disaster_cooldown - dt)
            self.quake_offset_x = 0
            self.quake_offset_y = 0
            
            if self.disaster_cooldown <= 0:
                prob = 0
                if self.erosion_risk > 0.7:
                    prob = 0.005 
                elif self.erosion_risk > 0.5:
                    prob = 0.001 
                    
                if random.random() < prob:
                    self.trigger_disaster()
        
    def trigger_disaster(self):
        disaster_types = []
        if self.erosion_risk > 0.5:
            disaster_types.extend(['landslide', 'flood'])
        if self.erosion_risk > 0.7:
            disaster_types.extend(['earthquake', 'drought'])
        self.disaster_type = random.choice(disaster_types) if disaster_types else None
        
        if self.disaster_type:
            if self.disaster_type in ['landslide', 'flood']:
                self.is_raining = True
                self.rain_timer = 0.0
                print(f"\n[WEATHER WARNING] Hujan lebat mendekati area. Risiko {self.disaster_type.upper()}!")
            else:
                self.disaster_active = True
                self.disaster_timer = random.uniform(5, 8)
                self.total_disasters += 1
                self.disaster_visual_intensity = 1.0
                self.execute_disaster(is_wet_phase=False)
                print(f"\n!!! BENCANA AKTIF: {self.disaster_type.upper()} !!!")
    
    def execute_disaster(self, is_wet_phase):
        self.river_flooded_path.clear()
        if self.disaster_type == 'landslide':
            self.landslide_effect()
        elif self.disaster_type == 'flood':
            self.flood_effect(is_wet_phase)
        elif self.disaster_type == 'earthquake':
            self.earthquake_effect()
        elif self.disaster_type == 'drought':
            self.drought_effect()
        self.update_erosion_risk()

    def landslide_effect(self):
        self.river_flooded_path = self.get_flooded_area(radius=1)
        trees_killed = 0
        center_gx = random.randint(3, self.terrain_grid - 4)
        center_gy = random.randint(3, self.terrain_grid - 4)
        radius_grid = 4 
        
        for i in range(center_gx - radius_grid, center_gx + radius_grid + 1):
            for j in range(center_gy - radius_grid, center_gy + radius_grid + 1):
                if 0 <= i < self.terrain_grid and 0 <= j < self.terrain_grid:
                    if math.sqrt((i - center_gx)**2 + (j - center_gy)**2) < radius_grid:
                        
                        if (i, j) not in self.river_path and (i, j) not in self.river_flooded_path:
                            self.deforestation_map[j, i] = 0.0
                        
                        px, py = self.grid_to_pixel(i, j)
                        self.create_debris_effect(px, py, color_tuple=COLOR_SOIL, size_range=(3, 6), count=random.randint(1, 3))
        
        new_trees = []
        for t in self.trees:
            if math.sqrt((t['gx'] - center_gx)**2 + (t['gy'] - center_gy)**2) < radius_grid:
                self.stumps.append({'x': t['x'], 'y': t['y'], 'gx': t['gx'], 'gy': t['gy']})
                self.create_debris_effect(t['x'], t['y'], color_tuple=(50, 150, 50), size_range=(4, 6))
                trees_killed += 1
            else:
                new_trees.append(t)
        
        self.trees = new_trees
        self.trees_lost_to_disaster += trees_killed
        print(f"     >>> Tanah longsor menghancurkan {trees_killed} pohon!")

    def flood_effect(self, is_wet_phase):
        self.river_flooded_path = self.get_flooded_area(radius=5) 
        trees_killed = 0
        
        for t in self.trees:
            is_in_flood = (t['gx'], t['gy']) in self.river_flooded_path
            
            if is_in_flood or random.random() < 0.05:
                t['health'] *= 0.7 
                t['is_dying'] = True
            
            if t['health'] < 0.15:
                trees_killed += 1
                t['is_dying'] = False
                self.trees_lost_to_disaster += 1
                self.stumps.append({'x': t['x'], 'y': t['y'], 'gx': t['gx'], 'gy': t['gy']})

                for i in range(-1, 2):
                    for j in range(-1, 2):
                        nx, ny = t['gx'] + i, t['gy'] + j
                        if 0 <= nx < self.terrain_grid and 0 <= ny < self.terrain_grid:
                            if (nx, ny) not in self.river_path:
                                self.deforestation_map[ny, nx] = min(self.deforestation_map[ny, nx], 0.1)

        self.trees = [t for t in self.trees if t['health'] >= 0.15]
        self.deforestation_map *= 0.90
        print(f"     >>> Banjir merusak pohon, {trees_killed} pohon mati!")

    def earthquake_effect(self):
        trees_killed = 0
        new_trees = []

        for t in self.trees:
            if random.random() > 0.8:
                trees_killed += 1
                self.stumps.append({'x': t['x'], 'y': t['y'], 'gx': t['gx'], 'gy': t['gy']})
                self.create_debris_effect(t['x'], t['y'], color_tuple=(150, 150, 150), size_range=(5, 10), count=15)
                
                for i in range(-1, 2):
                    for j in range(-1, 2):
                        nx, ny = t['gx'] + i, t['gy'] + j
                        if 0 <= nx < self.terrain_grid and 0 <= ny < self.terrain_grid:
                            if (nx, ny) not in self.river_path:
                                self.deforestation_map[ny, nx] = min(self.deforestation_map[ny, nx], 0.1)
            else:
                new_trees.append(t)

        self.trees = new_trees
        self.trees_lost_to_disaster += trees_killed
        print(f"     >>> Gempa menghancurkan {trees_killed} pohon!")
    
    def drought_effect(self):
        self.drought_river_width = 1.0
        trees_killed = 0
        
        for t in self.trees:
            if random.random() < 0.4:  
                t['health'] *= 0.6
                t['is_dying'] = True 
            
            if t['health'] < 0.15:
                trees_killed += 1
                t['is_dying'] = False
                self.trees_lost_to_disaster += 1
                self.stumps.append({'x': t['x'], 'y': t['y'], 'gx': t['gx'], 'gy': t['gy']})

                for i in range(-1, 2):
                    for j in range(-1, 2):
                        nx, ny = t['gx'] + i, t['gy'] + j
                        if 0 <= nx < self.terrain_grid and 0 <= ny < self.terrain_grid:
                            if (nx, ny) not in self.river_path:
                                self.deforestation_map[ny, nx] = min(self.deforestation_map[ny, nx], 0.1)

        self.trees = [t for t in self.trees if t['health'] >= 0.15]
        self.deforestation_map *= 0.85 
        print(f"     >>> Kekeringan membunuh {trees_killed} pohon! Sungai mengering.")


    def get_flooded_area(self, radius=2):
        flooded_set = set()
        for i, j in self.river_path:
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    nx, ny = i + dx, j + dy
                    if 0 <= nx < self.terrain_grid and 0 <= ny < self.terrain_grid:
                        # Tambahkan faktor erosi untuk menentukan area banjir yang lebih besar
                        erosion_factor = self.erosion_risk * 3
                        effective_radius = radius + erosion_factor
                        if math.sqrt(dx**2 + dy**2) <= effective_radius:
                            flooded_set.add((nx, ny))
        return flooded_set

    def create_debris_effect(self, x, y, color_tuple, size_range, count=10):
        for _ in range(count):
            self.particles.append(Particle(
                x + random.uniform(-10, 10),
                y + random.uniform(-10, 10),
                color_tuple, 
                random.uniform(0.5, 1.5),
                size_range
            ))
    
    def is_river_cell(self, i, j):
        if (i, j) not in self.river_path:
            return False
        drought_active = self.disaster_active and self.disaster_type == 'drought'
        effective_river_radius = self.river_width_grid
        if drought_active:
            # Sungai hampir kering
            effective_river_radius = 0.5 

        min_dist_sq = float('inf')
        for ri, rj in self.river_path:
            dist_sq = (i - ri)**2 + (j - rj)**2
            min_dist_sq = min(min_dist_sq, dist_sq)
        
        return math.sqrt(min_dist_sq) <= effective_river_radius

    def get_vegetation_coverage(self, i, j):
        def get_v(r, c):
            if 0 <= r < self.terrain_grid and 0 <= c < self.terrain_grid:
                if (c, r) in self.river_path or (c, r) in self.river_flooded_path: 
                    return 0.0 
                return self.deforestation_map[r, c]
            
            r_clamped = clamp(r, 0, self.terrain_grid - 1)
            c_clamped = clamp(c, 0, self.terrain_grid - 1)
            return self.deforestation_map[r_clamped, c_clamped]

        v00 = get_v(j, i)
        v10 = get_v(j, i + 1)
        v01 = get_v(j + 1, i)
        v11 = get_v(j + 1, i + 1)

        return (v00 + v10 + v01 + v11) / 4.0

    def draw_terrain_smooth(self, surface):
        base_color = COLOR_DEFORESTED
        pygame.draw.rect(surface, base_color, (0, 0, SIM_SIZE, SIM_SIZE))
        
        for j in range(self.terrain_grid):
            for i in range(self.terrain_grid):
                vegetation = self.get_vegetation_coverage(i, j)
                color = lerp_color(COLOR_DEFORESTED, COLOR_HEALTHY_GRASS, vegetation)
                
                if self.disaster_active and self.disaster_type == 'drought':
                    intensity = self.disaster_visual_intensity
                    color = lerp_color(color, COLOR_DRY, intensity)

                rect = pygame.Rect(i * self.cell_size, j * self.cell_size, self.cell_size, self.cell_size)
                poly_points = [rect.topleft, rect.topright, rect.bottomright, rect.bottomleft]
                pygame.draw.polygon(surface, color, poly_points)

        for j in range(self.terrain_grid):
            for i in range(self.terrain_grid):
                rect = pygame.Rect(i * self.cell_size, j * self.cell_size, self.cell_size, self.cell_size)
                
                is_river_flow = (i, j) in self.river_path 
                is_flooded = (i, j) in self.river_flooded_path and self.disaster_active and self.disaster_type in ['flood', 'landslide']
                drought_active = self.disaster_active and self.disaster_type == 'drought'
                
                if is_river_flow or is_flooded:
                    base_water = COLOR_WATER
                    if is_flooded:
                        # Visual banjir yang lebih dinamis
                        base_water = lerp_color(COLOR_FLOOD, (100, 150, 200), math.sin(time.time() * 3 + i + j) * 0.1 + 0.5) 
                    elif drought_active and not self.is_river_cell(i, j):
                        continue 
                        
                    wave_offset = 15 * math.sin(time.time() * 5 + i * 0.5 + j * 0.3)
                    r = int(base_water[0] + wave_offset * 0.1)
                    g = int(base_water[1] + wave_offset * 0.1)
                    b = int(base_water[2] + wave_offset * 0.1)
                    
                    final_color = (r, g, b)
                    pygame.draw.rect(surface, final_color, rect)
                
                elif drought_active and (i, j) in self.river_path:
                    # Sungai kering menjadi tanah
                    pygame.draw.rect(surface, COLOR_DRY, rect)
                    
        if self.lightning_active > 0:
            # Kilat: overlay putih terang
            flash_surface = pygame.Surface((SIM_SIZE, SIM_SIZE), pygame.SRCALPHA)
            alpha = int(255 * (self.lightning_active / 0.1))
            flash_surface.fill((255, 255, 255, alpha))
            surface.blit(flash_surface, (0, 0))

    def draw_stumps_2d(self, surface):
        stump_color = (130, 90, 60)
        stump_top_color = COLOR_STUMP_TOP
        
        for stump in self.stumps:
            scale = 0.5
            stump_height = self.cell_size * 0.3 * scale
            stump_width = self.cell_size * 0.5 * scale

            draw_shadow(surface, stump['x'], stump['y'], stump_width * 2, scale=1.0)
            
            trunk_rect = pygame.Rect(stump['x'] - stump_width/2, stump['y'] - stump_height, 
                                     stump_width, stump_height)
            pygame.draw.ellipse(surface, stump_color, trunk_rect) 

            top_rect = pygame.Rect(stump['x'] - stump_width/2, stump['y'] - stump_height - 5, 
                                   stump_width, stump_height * 0.5)
            pygame.draw.ellipse(surface, stump_top_color, top_rect) 

            for r in range(1, int(stump_width/4)):
                 pygame.draw.ellipse(surface, (100, 60, 30), top_rect.inflate(-r*2, -r), 1)

    def draw_trees_2d(self, surface):
        # Gabungkan tunggul dan pohon untuk pengurutan kedalaman
        render_list = sorted(self.stumps + self.trees, key=lambda t: t['y'])
        
        # Basis untuk variasi warna (hijau yang lebih gelap dan lebih terang)
        DARK_GREEN = (20, 80, 30)
        LIGHT_GREEN = (50, 150, 60)

        for item in render_list:
            if 'health' not in item:
                continue

            tree_data = item
            health = tree_data['health']
            scale = 0.5 + health * 0.5

            radius_base = self.cell_size * 0.7 * scale
            trunk_height = self.cell_size * 0.8 * scale
            trunk_width = self.cell_size * 0.25 * scale
            
            draw_shadow(surface, tree_data['x'], tree_data['y'], radius_base * 1.5)

            trunk_col = (120, 80, 40)
            tw_b, tw_t, th = trunk_width, trunk_width * 0.5, trunk_height
            pygame.draw.polygon(surface, trunk_col, [
                (tree_data['x'] - tw_b / 2, tree_data['y']), 
                (tree_data['x'] + tw_b / 2, tree_data['y']), 
                (tree_data['x'] + tw_t / 2, tree_data['y'] - th), 
                (tree_data['x'] - tw_t / 2, tree_data['y'] - th)
            ])
            
            if health < 0.5:
                t = health / 0.5 
                canopy_color_base = lerp_color(COLOR_DRY, COLOR_CANOPY_BASE, t)
            else:
                canopy_color_base = COLOR_CANOPY_BASE
            
            canopy_y = int(tree_data['y'] - trunk_height) 
            radius = int(radius_base)
            
            # --- Perubahan untuk Dimensi Warna Stabil ---
            # Pola lapisan (semakin besar radius, semakin terang/cerah)
            layer_config = [
                # Lapisan Bawah (Paling gelap, paling besar)
                (0, 0, 1.0, 0.0), 
                # Lapisan Tengah-Bawah (Sedikit lebih terang)
                (-0.4, -0.3, 0.7, 0.2), 
                # Lapisan Tengah-Atas (Sedang)
                (0.4, -0.3, 0.7, 0.1), 
                # Lapisan Atas (Paling cerah, paling kecil)
                (-0.1, -0.6, 0.6, 0.4), 
                (0.3, -0.7, 0.5, 0.3)
            ]
            
            for dx, dy, r_scale, t_lerp in layer_config:
                r = int(radius * r_scale)
                cx = int(tree_data['x'] + dx * radius)
                cy = int(canopy_y + dy * radius)
                
                # Interpolasi warna berdasarkan t_lerp untuk variasi dimensi:
                # Warna bervariasi antara DARK_GREEN dan LIGHT_GREEN, tergantung posisi lapisan
                
                # Ciptakan warna hijau yang bervariasi, berdasarkan canopy_color_base
                mixed_green = (
                    int(canopy_color_base[0] * (1 - t_lerp) + LIGHT_GREEN[0] * t_lerp),
                    int(canopy_color_base[1] * (1 - t_lerp) + LIGHT_GREEN[1] * t_lerp),
                    int(canopy_color_base[2] * (1 - t_lerp) + LIGHT_GREEN[2] * t_lerp)
                )

                # Clamp untuk memastikan nilai RGB tetap valid
                layer_color = (
                    clamp(mixed_green[0], DARK_GREEN[0], LIGHT_GREEN[0]),
                    clamp(mixed_green[1], DARK_GREEN[1], LIGHT_GREEN[1]),
                    clamp(mixed_green[2], DARK_GREEN[2], LIGHT_GREEN[2])
                )
                
                pygame.draw.circle(surface, layer_color, (cx, cy), r)
            
            if health < 0.8:
                bar_w, bar_h = 30 * scale, 4 
                bar_x, bar_y = tree_data['x'] - bar_w//2, tree_data['y'] - trunk_height - 10
                pygame.draw.rect(surface, (100, 0, 0), (bar_x, bar_y, bar_w, bar_h))
                pygame.draw.rect(surface, (0, 255, 0), (bar_x, bar_y, bar_w * health, bar_h))

    def draw_container_frame(self, surf, rect, padding=5, border_thickness=2):
        container_rect = rect.inflate(-padding * 2, -padding * 2)
        pygame.draw.rect(surf, COLOR_UI_DARK, container_rect, border_radius=5)

        pygame.draw.line(surf, COLOR_UI_HIGHLIGHT, (container_rect.left, container_rect.bottom), 
                         (container_rect.left, container_rect.top), border_thickness)
        pygame.draw.line(surf, COLOR_UI_HIGHLIGHT, (container_rect.left, container_rect.top), 
                         (container_rect.right, container_rect.top), border_thickness)
        
        pygame.draw.line(surf, COLOR_UI_BORDER, (container_rect.right, container_rect.top), 
                         (container_rect.right, container_rect.bottom), border_thickness)
        pygame.draw.line(surf, COLOR_UI_BORDER, (container_rect.right, container_rect.bottom), 
                         (container_rect.left, container_rect.bottom), border_thickness)
        
        return container_rect.left + padding, container_rect.top + padding, container_rect.width - 2 * padding
        

    def draw_info_panel(self, surface):
        """Menggambar panel informasi dengan struktur container yang halus."""
        
        # --- A. FRAME LUAR UTAMA ---
        info_rect = pygame.Rect(SIM_SIZE, 0, INFO_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(surface, COLOR_DARK_BLUE, info_rect)
        pygame.draw.rect(surface, COLOR_UI_BORDER, info_rect, 3) 
        
        panel_area = info_rect.inflate(-10, -10)
        
        x_offset = panel_area.left
        y_cursor = panel_area.top + 5 
        width_max = panel_area.width
        line_spacing = 25 
        
        # 1. Judul
        title_text = FONT_LARGE.render("Simulasi Deforestasi", True, COLOR_WHITE)
        surface.blit(title_text, (x_offset + 5, y_cursor))
        y_cursor += line_spacing * 2
        
        # --- 2. CONTAINER STATUS & BENCANA ---
        status_container_height = 80 
        status_rect = pygame.Rect(x_offset, y_cursor, width_max, status_container_height)
        start_x, start_y, cont_width = self.draw_container_frame(surface, status_rect, padding=5) 
        
        if self.is_raining:
            status_name = "HUJAN LEBAT!"
            status_color = COLOR_WATER
            detail_text = f"RISIKO {self.disaster_type.upper()} TINGGI ({self.rain_duration - self.rain_timer:.1f}s)"
        elif self.disaster_active:
            disaster_names = {'landslide': 'TANAH LONGSOR!','flood': 'BANJIR BESAR!','earthquake': 'GEMPA BUMI!','drought': 'KEKERINGAN!'}
            status_name = disaster_names.get(self.disaster_type, 'BAHAYA!')
            status_color = COLOR_DANGER
            detail_text = f"AKTIF ({self.disaster_timer:.1f}s tersisa)"
        else:
            warning_map = {0: ("AMAN", COLOR_SAFE, "Keseimbangan Ekosistem"), 
                           1: ("WASPADA", COLOR_WARNING, "Tingkat Erosi Meningkat"), 
                           2: ("BAHAYA!", COLOR_DANGER, "Risiko Bencana Signifikan"), 
                           3: ("KRITIS!!!", COLOR_DANGER, "Bencana Sudah Dekat")}
            status_name, status_color, detail_text = warning_map[self.warning_level]

        main_status_text = FONT_MEDIUM.render(status_name, True, status_color)
        surface.blit(main_status_text, (start_x, start_y))
        
        detail_status_text = FONT_SMALL.render(detail_text, True, COLOR_WHITE)
        surface.blit(detail_status_text, (start_x, start_y + line_spacing))

        if self.warning_level >= 1 or self.disaster_active:
            flash_opacity = abs(math.sin(self.warning_flash)) 
            if flash_opacity > 0.5:
                warning_icon = FONT_MEDIUM.render("!", True, status_color)
                surface.blit(warning_icon, (start_x + main_status_text.get_width() + 5, start_y))
            
        y_cursor += status_container_height + 5 


        # --- 3. CONTAINER STATISTIK (DITINGGIKAN) ---
        stats_container_height = 180 # Ditingkatkan dari ~140 ke 180
        stats_rect = pygame.Rect(x_offset, y_cursor, width_max, stats_container_height)
        start_x, start_y, cont_width = self.draw_container_frame(surface, stats_rect, padding=5)

        # Bar Risiko Erosi
        bar_y = start_y 
        bar_h = 12 
        
        risk_label = FONT_SMALL.render("RISIKO EROSI", True, COLOR_WHITE)
        surface.blit(risk_label, (start_x, bar_y))
        bar_y += 18 
        
        bar_color = lerp_color(COLOR_SAFE, COLOR_DANGER, self.erosion_risk)
        pygame.draw.rect(surface, (50, 50, 50), (start_x, bar_y, cont_width, bar_h), border_radius=3)
        pygame.draw.rect(surface, bar_color, (start_x, bar_y, int(cont_width * self.erosion_risk), bar_h), border_radius=3)
        risk_value = FONT_TINY.render(f"{self.erosion_risk*100:.1f}%", True, COLOR_WHITE)
        surface.blit(risk_value, (start_x + cont_width - risk_value.get_width() - 5, bar_y + 1))
        
        current_y = bar_y + line_spacing 
        info_lines = [
            (f"Pohon Aktif: {len(self.trees)}", COLOR_WHITE),
            (f"Tunggul: {len(self.stumps)}", COLOR_STUMP_TOP),
            (f"Total Bencana: {self.total_disasters}", COLOR_WARNING),
            (f"Pohon Hilang: {self.trees_lost_to_disaster}", COLOR_DANGER),
        ]

        for line, color in info_lines:
            text = FONT_SMALL.render(line, True, color)
            surface.blit(text, (start_x, current_y))
            current_y += line_spacing
            
        y_cursor += stats_container_height + 5 
        
        # Tentukan posisi tombol baru secara dinamis
        button_y_end = self._reposition_buttons(y_cursor) 

        # Gambar Tombol yang sudah diinisialisasi
        for button in self.buttons:
            button.draw(surface)

        # --- 4. CONTAINER KONTROL & TUJUAN (DIKECILKAN) ---
        
        # Posisi awal Active Mode container (tepat setelah tombol terakhir)
        control_rect_y = button_y_end 
        
        # Mengurangi tinggi container mode aktif dengan membatasi ketinggian (max 70px)
        MAX_CONTROL_HEIGHT = 70 
        control_container_height = min(MAX_CONTROL_HEIGHT, SCREEN_HEIGHT - control_rect_y - 10)
        
        control_rect = pygame.Rect(x_offset, control_rect_y, width_max, control_container_height)
        start_x, start_y, cont_width = self.draw_container_frame(surface, control_rect, padding=5)
        
        current_y = start_y
        
        # Informasi Mode Aktif
        mode_text = FONT_MEDIUM.render(f"MODE AKTIF:", True, COLOR_UI_HIGHLIGHT)
        surface.blit(mode_text, (start_x, current_y))
        
        mode_name = self.current_mode.replace('_', ' ').upper()
        mode_detail_color = COLOR_BUTTON_SAFE if 'plant' in self.current_mode else COLOR_BUTTON_NORMAL
        mode_detail = FONT_MEDIUM.render(mode_name, True, mode_detail_color)
        surface.blit(mode_detail, (start_x + mode_text.get_width() + 5, current_y))

    def draw_clouds(self, surface):
        """Menggambar awan tipis yang bergerak."""
        for cloud in self.clouds:
            # Ganti warna awan saat hujan menjadi gelap
            if self.is_raining:
                cloud.color = COLOR_STORM_CLOUD
            else:
                cloud.color = (200, 200, 200, 150)
            cloud.draw(surface)

    def draw_rain_background(self, surface):
        """Menggambar lapisan latar belakang hujan/badai."""
        if self.is_raining:
            # Lapisan gelap untuk menunjukkan badai
            storm_surface = pygame.Surface((SIM_SIZE, SIM_SIZE), pygame.SRCALPHA)
            alpha_dark = int(100 * (self.rain_timer / self.rain_duration)) 
            storm_surface.fill((0, 0, 0, alpha_dark))
            surface.blit(storm_surface, (0, 0))

        # Partikel hujan dan awan digambar setelah ini
            
    def run(self):
        running = True
        
        while running:
            dt = clock.tick(FPS) 
            
            # Reset guncangan dari kilat jika tidak ada kilat
            if self.lightning_active == 0.0:
                self.quake_offset_x = 0
                self.quake_offset_y = 0
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                # Cek interaksi tombol
                for button in self.buttons:
                    action = button.handle_event(event)
                    if action:
                        if action == 'cut_mass':
                            self.remove_20_percent_trees()
                        elif action == 'reset':
                            self.reset_simulation()
                        else:
                            # Ubah mode kontrol klik di peta
                            self.current_mode = action
                            print(f"Mode Kontrol Diubah: {self.current_mode.upper()}")
                        
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    
                    # Hanya merespons klik di area simulasi
                    if x < SIM_SIZE and y < SIM_SIZE:
                        gx = x // self.cell_size
                        gy = y // self.cell_size
                        
                        if event.button == 1: # Klik Kiri (Ikuti Mode Aktif)
                            if self.current_mode == 'plant_single': 
                                if 0 <= gx < self.terrain_grid and 0 <= gy < self.terrain_grid:
                                    self.add_tree_by_grid(gx, gy)
                            
                            elif self.current_mode == 'cut_single': 
                                self.remove_tree_by_pixel(x, y)
                        
                        elif event.button == 3: # Klik Kanan: Default untuk Tebang pohon
                             self.remove_tree_by_pixel(x, y)

                        
            # === UPDATE SIMULASI ===
            self.update(dt)
            
            # === DRAWING ===
            screen.fill(COLOR_DARK_BLUE)
            
            offset_x = getattr(self, 'quake_offset_x', 0)
            offset_y = getattr(self, 'quake_offset_y', 0)

            # Gambar di sim_surface dengan offset goyang
            sim_surface = pygame.Surface((SIM_SIZE, SIM_SIZE))
            
            # Z-Order Baru: Clouds di atas Trees/Stumps
            self.draw_terrain_smooth(sim_surface) # 1. Base terrain, river, and lightning flash
            self.draw_stumps_2d(sim_surface)      # 2. Stumps
            self.draw_trees_2d(sim_surface)       # 3. Trees (Canopy)
            self.draw_clouds(sim_surface)         # 4. Clouds (Di atas pohon, sesuai permintaan)
            
            # 5. Hujan/Badai (Overlay, di atas semuanya kecuali partikel)
            self.draw_rain_background(sim_surface)

            for particle in self.particles:
                particle.draw(sim_surface)
                
            for rain_drop in self.rain_particles:
                rain_drop.draw(sim_surface)
                
            screen.blit(sim_surface, (offset_x, offset_y))
            
            # Gambar Panel Info dan Tombol
            self.draw_info_panel(screen) 
            
            pygame.display.flip()

        pygame.quit()


# ============ Main Execution ============
if __name__ == "__main__":
    simulation = DeforestationSimulation()
    simulation.run()