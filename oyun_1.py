from ursina import *
import math, random
from ursina.shaders import basic_lighting_shader
Entity.default_shader = basic_lighting_shader

class Player(Entity):
    def __init__(self):
        super().__init__(model='cube', color=color.azure, scale=(1,1,1), collider='box')
        self.speed = 5
        self.attack_power = 1
        self.max_hp = 10
        self.hp = 10
        self.xp = 0
        self.level = 1
        self.xp_needed = 10
        self.attack_cooldown = 0

        # Kılıç modeli
        self.sword = Entity(parent=self, model='cube', color=color.gray, scale=(0.1, 0.4, 1),
                            position=(0,0.3,0.8))

        # Saldırı alanı (yarım daire)
        self.attack_area = Entity(parent=self, model=Mesh(vertices=[], mode='triangle', thickness=2),
                                  color=color.rgba(255,0,0,100), visible=False)

    def update(self):
        move = (held_keys['d'] - held_keys['a'], 0, held_keys['w'] - held_keys['s'])
        if move != (0,0,0):
            self.rotation_y = math.degrees(math.atan2(move[0], move[2]))
        self.position += Vec3(*move) * time.dt * self.speed
        camera.position = self.position + Vec3(0, 15, -15)
        camera.look_at(self.position)

        if self.attack_cooldown > 0:
            self.attack_cooldown -= time.dt

        if mouse.left and self.attack_cooldown <= 0:
            self.sword_attack()
            self.attack_cooldown = 0.5

    def sword_attack(self):
        print("Kılıç saldırısı!")
        self.show_attack_area()

        for e in scene.entities:
            if isinstance(e, Enemy):
                dir_to_enemy = e.position - self.position
                distance = dir_to_enemy.length()
                if distance <= 2:
                    forward = self.forward
                    angle = math.degrees(math.acos(forward.normalized().dot(dir_to_enemy.normalized())))
                    if angle <= 90:
                        e.take_damage(self.attack_power)

    def show_attack_area(self):
        # Yarım daire mesh oluştur
        radius = 2
        segments = 20
        vertices = [(0,0,0)]
        for i in range(segments+1):
            angle_rad = math.radians(90 - (i * 180/segments))
            x = math.sin(angle_rad) * radius
            z = math.cos(angle_rad) * radius
            vertices.append((x, 0, z))
        self.attack_area.model = Mesh(vertices=vertices, triangles=[(0,i,i+1) for i in range(1, len(vertices)-1)], mode='triangle')
        self.attack_area.visible = True
        invoke(self.hide_attack_area, delay=0.2)

    def hide_attack_area(self):
        self.attack_area.visible = False
    
    def add_xp(self, amount):
        self.xp += amount
        if self.xp >= self.xp_needed:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.xp = 0
        self.xp_needed += 5
        show_levelup_menu()


class Enemy(Entity):
    def __init__(self, player):
        super().__init__(model='cube', color=color.red, scale=0.8, collider='box')
        self.player = player
        self.speed = 2
        self.max_hp = 3
        self.hp = self.max_hp

        # Health bar arka plan (kırmızı)
        self.health_bg = Entity(parent=self, model='quad', color=color.rgb(100,0,0),
                                scale=(1, 0.1, 1), position=(0, 0.6, 0), billboard=True)

        # Health bar ön (yeşil)
        self.health_fg = Entity(parent=self.health_bg, model='quad', color=color.green,
                                scale=(1, 1, 1), position=(0,0,0))

    def update(self):
        direction = (self.player.position - self.position).normalized()
        self.position += direction * self.speed * time.dt

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            destroy(self)
            self.player.add_xp(5)
        else:
            self.update_health_bar()

    def update_health_bar(self):
        ratio = max(self.hp / self.max_hp, 0)
        self.health_fg.scale_x = ratio
        self.health_fg.x = -(1 - ratio) / 2  # sola kayma olmaması için
        # Renk yeşilden kırmızıya geçiş
        self.health_fg.color = color.rgb(255*(1-ratio), 255*ratio, 0)


def spawn_enemy():
    e = Enemy(player)
    e.position = Vec3(random.uniform(-10, 10), 0, random.uniform(-10, 10))

def show_levelup_menu():
    global menu_entities
    menu_entities = []
    options = [
        ("Saldırı Gücü +1", lambda: upgrade_stat("attack")),
        ("Hız +1", lambda: upgrade_stat("speed")),
        ("Can +5", lambda: upgrade_stat("hp"))
    ]
    y = 0
    for text_label, func in options:
        btn = Button(text=text_label, scale=(0.3, 0.1), position=(0, y))
        btn.on_click = func
        menu_entities.append(btn)
        y -= 0.15

def upgrade_stat(stat):
    if stat == "attack":
        player.attack_power += 1
    elif stat == "speed":
        player.speed += 1
    elif stat == "hp":
        player.max_hp += 5
        player.hp += 5
    for e in menu_entities:
        destroy(e)

app = Ursina()

# Zemin
ground = Entity(model='plane', scale=50, texture='grass', texture_scale=(50,50),
                color=color.rgb(50, 200, 50), collider='box')

player = Player()
camera.rotation_x = 45

enemy_spawn_timer = 0
menu_entities = []

def update():
    global enemy_spawn_timer
    enemy_spawn_timer += time.dt
    if enemy_spawn_timer > 2:
        spawn_enemy()
        enemy_spawn_timer = 0

app.run()