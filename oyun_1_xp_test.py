from ursina import *
import math, random
from ursina.shaders import basic_lighting_shader

Entity.default_shader = basic_lighting_shader

# ----------------------------- XP KÜRESİ SINIFI (YENİ) -----------------------------
class XPOrb(Entity):
    def __init__(self, position, amount=5):
        super().__init__(
            model='cube',
            color=color.yellow, # XP genelde sarı/altın rengi olur
            scale=0.3,
            position=position + Vec3(0, 0.5, 0), # Yerden biraz yukarıda doğsun
            collider='box',
            shader=basic_lighting_shader
        )
        self.amount = amount
        # Doğduğunda hafifçe zıplama efekti
        self.animate_y(self.y + 0.5, duration=0.5, curve=curve.out_bounce)

    def update(self):
        # Kendi etrafında dönsün
        self.rotation_y += 100 * time.dt
        
        # Oyuncuya yakınsa (Toplama mantığı)
        if distance(self, player) < 1.5:
            player.add_xp(self.amount)
            print(f"XP Toplandı: {self.amount}")
            destroy(self)

# ----------------------------- PLAYER SINIFI -----------------------------
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
        self.weapon = "sword"

        # Kılıç modeli
        self.sword = Entity(parent=self, model='sword', color=color.gray, scale=0.1,
                            position=(0,0.3,1), rotation_y = 180)

        # Yay modeli (başta gizli)
        self.bow = Entity(parent=self, model='cube', color=color.yellow, scale=(0.05,0.3,0.1),
                          position=(0.3,0.3,1), visible=False)

        # Saldırı alanı
        self.attack_area = Entity(parent=self, model=Mesh(vertices=[], mode='triangle', thickness=2),
                                  color=color.rgba(255,0,0,0.5), visible=False, shader=None)
        
        # Health bar
        self.health_bg = Entity(parent=self, model='quad', color=color.rgb(100,0,0),
                                scale=(1, 0.1, 1), position=(0, 0.6, 0), billboard=True, shader=None)
        self.health_fg = Entity(parent=self.health_bg, model='quad', color=color.green,
                                scale=(1, 1, 1), position=(0,0,-0.5), shader=None)

    def update_health_bar(self):
        ratio = max(self.hp / self.max_hp, 0)
        self.health_fg.scale_x = ratio
        self.health_fg.x = -(1 - ratio) / 2
        self.health_fg.color = color.rgb(255*(1-ratio), 255*ratio, 0)

    def take_damage_p(self, dmg):
        global mod
        self.hp -= dmg
        if self.hp <= 0:
            mod = "game over"
        else:
            self.update_health_bar()

    def update(self):
        if mod in ["menu", "game over"]: return

        # Hareket
        move = (held_keys['d'] - held_keys['a'], 0, held_keys['w'] - held_keys['s'])
        if move != (0,0,0):
            self.rotation_y = math.degrees(math.atan2(move[0], move[2]))
        self.position += Vec3(*move) * time.dt * self.speed
        camera.position = self.position + Vec3(0, 15, -15)
        camera.look_at(self.position)

        # Silah değiştirme
        if held_keys['q']:
            self.switch_weapon()

        # Saldırı
        if self.attack_cooldown > 0:
            self.attack_cooldown -= time.dt
        if mouse.left and self.attack_cooldown <= 0:
            if self.weapon == "sword":
                self.sword_attack()
            elif self.weapon == "bow":
                self.bow_attack()
            self.attack_cooldown = 0.5

    def switch_weapon(self):
        if self.weapon == "sword":
            self.weapon = "bow"
            self.sword.visible = False
            self.bow.visible = True
        else:
            self.weapon = "sword"
            self.sword.visible = True
            self.bow.visible = False

    def sword_attack(self):
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

    def bow_attack(self):
        arrow = Entity(model='cube', color=color.orange, scale=(0.1,0.1,0.5),
                       position=self.position + self.forward, rotation_y=self.rotation_y)
        arrow.direction = self.forward
        arrow.speed = 10
        arrow.life_time = 2
        arrow.is_arrow = True
        invoke(destroy, arrow, delay=arrow.life_time)

    def show_attack_area(self):
        radius = 2
        segments = 20
        vertices = [(0,0,0)]
        for i in range(segments+1):
            angle_rad = math.radians(90 - (i * 180/segments))
            x = math.sin(angle_rad) * radius
            z = math.cos(angle_rad) * radius
            vertices.append((x, 0.5, z))
        self.attack_area.model = Mesh(vertices=vertices, triangles=[(0,i,i+1) for i in range(1, len(vertices)-1)], mode='triangle')
        self.attack_area.visible = True
        invoke(self.hide_attack_area, delay=0.2)

    def hide_attack_area(self):
        self.attack_area.visible = False

    def add_xp(self, amount):
        self.xp += amount
        # XP barı veya görseli varsa burada güncellenebilir
        if self.xp >= self.xp_needed:
            self.level_up()

    def level_up(self):
        self.level += 1
        self.xp = 0
        self.xp_needed += 5
        show_levelup_menu()


# ----------------------------- DÜŞMAN SINIFI -----------------------------
class Enemy(Entity):
    def __init__(self, player):
        super().__init__(model='cube', color=color.red, scale=0.8, collider='box')
        self.player = player
        self.speed = 2
        self.max_hp = 3
        self.hp = self.max_hp
        self.attack_power = 0.1
        self.health_bg = Entity(parent=self, model='quad', color=color.rgb(100,0,0),
                                scale=(1,0.1,1), position=(0,0.6,0), billboard=True)
        self.health_fg = Entity(parent=self.health_bg, model='quad', color=color.green,
                                scale=(1,1,1), position=(0,0,-0.5))

    def update(self):
        if mod in ["menu", "game over"]: return
        direction = (self.player.position - self.position).normalized()
        self.position += direction * self.speed * time.dt
        if distance(self, player) < 1:
            self.sword_attack()

    def take_damage(self, dmg):
        self.hp -= dmg
        if self.hp <= 0:
            # 🔥 YENİ: Öldüğünde XP küresi düşür
            XPOrb(position=self.position, amount=5) 
            destroy(self)
        else:
            self.update_health_bar()

    def update_health_bar(self):
        ratio = max(self.hp / self.max_hp, 0)
        self.health_fg.scale_x = ratio
        self.health_fg.x = -(1 - ratio) / 2
        self.health_fg.color = color.rgb(255*(1-ratio), 255*ratio, 0)

    def sword_attack(self):
        if player.hp > 0:
            dir_to_enemy = self.position - player.position
            distance = dir_to_enemy.length()
            if distance <= 2:
                forward = self.forward
                angle = math.degrees(math.acos(forward.normalized().dot(dir_to_enemy.normalized())))
                if angle <= 90 and player:
                    player.take_damage_p(self.attack_power)


# ----------------------------- GÖREV SİSTEMİ -----------------------------
class Quest:
    number = 0
    def __init__(self, title, desc, pos, marker = None, reward_weapon=False):
        self.title = title
        self.desc = desc
        self.pos = Vec3(*pos)
        self.active = False
        self.done = False
        self.reward_weapon = reward_weapon
        self.marker = marker
        if self.marker == None:
            self.marker = Entity(model='cube', color=color.azure, scale=0.5, position=self.pos, shader=None)
        elif self.marker == 1:
            self.marker = Entity(model= "Campfire", scale = 1, shader =None, position= self.pos)


    def update(self):
        if self.done: return
        if distance(player, self.marker) < 2 and not self.active and self.title == quests[Quest.number].title:
            Quest.number += 1% len(quests)
            self.active = True
        quest_text.text = f"GÖREV AKTİF: {quests[Quest.number].title}"
        if self.active and distance(player, self.marker) < 1:
            self.complete()

    def complete(self):
        self.done = True
        self.active = False
        destroy(self.marker)
        quest_text.text = f"✔ GÖREV TAMAMLANDI: {self.title}"
        if self.reward_weapon:
            print("Yeni silah (yay) açıldı!")
            player.weapon = "bow"
            player.sword.visible = False
            player.bow.visible = True


def spawn_enemy():
    e = Enemy(player)
    e.position = Vec3(random.uniform(-10,10), 0, random.uniform(-10,10))


# ----------------------------- LEVEL UP MENÜSÜ -----------------------------
def show_levelup_menu():
    global menu_entities, mod
    mod = "menu"
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
    global mod
    if stat == "attack": player.attack_power += 1
    elif stat == "speed": player.speed += 1
    elif stat == "hp":
        player.max_hp += 5
        player.hp += 5
    for e in menu_entities: destroy(e)
    mod = "oyun"


# ----------------------------- ANA AYARLAR -----------------------------
app = Ursina()
ground = Entity(model='plane', scale=100, texture='grass', collider='box', shader=None)
player = Player()
camera.rotation_x = 45

enemy_spawn_timer = 0
menu_entities = []
mod = "oyun"
game_over_text = Text("GAME OVER", scale=2, visible=False, color=color.red)

# 🔥 Görevler
quests = [
    Quest("Kamp Alanına Git", "Kamp alanını bul.", (15,0.5,0), marker= 1),
    Quest("Ormanı Keşfet", "Ormanın girişine ulaş.", (-15,0,20)),
    Quest("Gizli Tapınağı Bul", "Tapınağın kapısına git.", (0,0,-18)),
    Quest("Efsanevi Silahı Al", "Yeni yayı elde et.", (0,0,-25), reward_weapon=True)
]

quest_text = Text(text="Görev Yok", origin=(-.5,.5), scale=1.2, position=(-0.85,0.45), color=color.yellow)


# ----------------------------- UPDATE FONKSİYONU -----------------------------
def update():
    global enemy_spawn_timer
    if mod == "menu": return
    if mod == "game over":
        game_over_text.visible = True
        return

    # Görev kontrolü
    for q in quests:
        q.update()

    # Ok (arrow) hareketi ve çarpışma
    for e in scene.entities:
        if hasattr(e, 'is_arrow') and e.is_arrow:
            e.position += e.direction * e.speed * time.dt
            for en in scene.entities:
                if isinstance(en, Enemy) and distance(e, en) < 1:
                    en.take_damage(player.attack_power * 3)
                    destroy(e)
                    break

    # Düşman doğurma
    enemy_spawn_timer += time.dt
    if enemy_spawn_timer > 2:
        spawn_enemy()
        enemy_spawn_timer = 0


app.run()