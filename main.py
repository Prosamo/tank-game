import asyncio
import pygame, sys, time, random, math, copy
import js

random.seed(time.time())

pygame.init()    # Pygameを初期化
WIDTH, HEIGHT = 256, 256
screen = pygame.display.set_mode((WIDTH, HEIGHT))    # 画面を作成
pygame.display.set_caption("戦車ゲーム")    # タイトルを作成
clock = pygame.time.Clock()
font = pygame.font.SysFont('', 16)

game_window = pygame.Surface((WIDTH, HEIGHT))
gw_pos = (0, 0)

tank_image = pygame.image.load("tank.png").convert_alpha()
ball_image = pygame.image.load("ball.png").convert_alpha()
e_tank_image = pygame.image.load("e-tank.png").convert_alpha()
e_ball_image = pygame.image.load("e-ball.png").convert_alpha()

class Stick:
    def __init__(self, x, y, r, border_width = 2):
        self.x, self.y = x, y
        self.r = r
        self.inner_r= int(self.r * 0.6)
        self.border_width = border_width
        self.inner_x = self.x + self.r - self.inner_r # 初期位置を調整
        self.inner_y = self.y + self.r - self.inner_r # 初期位置を調整

        self.angle = 0
        
    def draw(self):
        # 透明な土台を設定
        alpha_surface = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
        alpha_surface.fill((0, 0, 0, 0))
        #白い枠線
        pygame.draw.circle(alpha_surface, (255, 255, 255, 128), (self.r, self.r), self.r, self.border_width)
        #灰色の丸
        pygame.draw.circle(alpha_surface, (128, 128, 128, 128), (self.inner_x, self.inner_y), self.inner_r)
        #描画
        game_window.blit(alpha_surface, (self.x, self.y))
    def update(self, mouse_pos = None):
        if mouse_pos is None:
            self.inner_x = self.r
            self.inner_y = self.r
            return
        mouse_x, mouse_y = mouse_pos
        if mouse_x <= WIDTH//2:
            dx = mouse_x - (self.x + self.r)
            dy = mouse_y - (self.y + self.r)
            self.angle = math.atan2(dy, dx)
            self.inner_x = self.r + self.r * 0.4 * math.cos(self.angle)# 中心からの距離を計算
            self.inner_y = self.r + self.r * 0.4 * math.sin(self.angle)# 中心からの距離を計算
            self.inner_x = int(self.inner_x)
            self.inner_y = int(self.inner_y)

class Button:
    def __init__(self, x, y, r, color = (128, 182, 255)):
        self.x = x
        self.y = y
        self.r = r
        self.width = self.r*2
        self.height = self.r*2
        self.color = color
    def draw(self):
        # 透明な土台を設定
        alpha_surface = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
        alpha_surface.fill((0, 0, 0, 0))
        #円
        pygame.draw.circle(alpha_surface, (*self.color, 128), (self.r, self.r), self.r)
        #白い枠線
        pygame.draw.circle(alpha_surface, (255, 255, 255, 128), (self.r, self.r), self.r, 2)
        #描画
        game_window.blit(alpha_surface, (self.x,self.y))
    def pressed(self, mouse_x, mouse_y):
        if self.x <= mouse_x <= self.x+self.width and self.y <= mouse_y <= self.y+self.height:
            return True
        else:
            return False


class Gauge:
    def __init__(self, x, y, width, height):
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.rate = 1
    def draw(self):
        # 透明な土台を設定
        alpha_surface = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        alpha_surface.fill((0, 0, 0, 64))
        #緑の四角
        pygame.draw.rect(alpha_surface, (128, 255, 128, 128), (0, self.height*(1-self.rate), self.width, self.height))
        #枠線
        pygame.draw.rect(alpha_surface, (255, 255, 255, 128), (0, 0, self.width, self.height), 2)
        #描画
        game_window.blit(alpha_surface, (self.x, self.y))
    def update(self, rate):
        self.rate = rate


class Tank:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.image = tank_image
        self.speed = 1.5
        self.angle = 0
        self.ball = 5
        self.last_charge_time = time.time()
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
    def draw(self):
        game_window.blit(self.image, self.rect.topleft)
    def update(self, angle):
        self.charge()
        self.angle = angle
        self.image = pygame.transform.rotate(tank_image, -math.degrees(self.angle))
        self.rect = self.image.get_rect(center=(int(self.x), int(self.y)))
    def charge(self):
        current_time = time.time()
        if current_time - self.last_charge_time >= 0.8:
            self.ball = min(5, self.ball+1)
            self.last_charge_time = current_time
    def move(self): # 戦車の位置を角度に基づいて更新
        self.x += self.speed * math.cos(self.angle)
        self.x = min(max(self.x, 8), 248)
        self.y += self.speed * math.sin(self.angle)
        self.y = min(max(self.y, 8), 248)
    def shoot(self):
        if self.ball >= 1:
            self.ball -= 1
            Ball(self.x, self.y, self.angle)
    def fire(self):
        if self.ball >= 5:
            self.ball -=5
            Laser(game_window, self.x, self.y, self.angle)


class ETank:
    tanks = []
    @classmethod
    def reset(cls):
        cls.tanks = []
    
    @classmethod
    def update_all(cls):
        for tank in cls.tanks:
            tank.update()
    @classmethod
    def draw_all(cls):
        for tank in cls.tanks:
            tank.draw()

    def __init__(self, x, y, target_x, target_y):
        self.x, self.y = x, y
        self.image = e_tank_image

        dx = target_x - self.x
        dy = target_y - self.y
        self.angle = math.atan2(dy, dx) # 自分の戦車に向けてアングルを計算
        
        ETank.tanks.append(self)
        self.last_time = time.time()
        self.rect = self.image.get_rect(center=(self.x, self.y))
    def draw(self):
        game_window.blit(self.image, self.rect.topleft)
    def update(self):
        self.image = pygame.transform.rotate(e_tank_image, -math.degrees(self.angle))
        self.rect = self.image.get_rect(center=(self.x, self.y))
        current_time = time.time()
        if current_time-self.last_time >= 3:
            self.shoot()
            self.last_time = time.time()
    def shoot(self):
        EBall(self.x, self.y, self.angle)  
        

class Ball:
    balls = []
    @classmethod
    def reset(cls):
        cls.balls = []
    
    @classmethod
    def update_all(cls):
        for ball in copy.copy(cls.balls):
            ball.update()
            ball.check_collision()
    @classmethod
    def draw_all(cls):
        for ball in cls.balls:
            ball.draw()

    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 3
        self.image = ball_image
        self.rect = self.image.get_rect(center=(self.x, self.y))
        Ball.balls.append(self)

    def update(self):
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def draw(self):
        if 0 <= self.x <= 256 and 0 <= self.y <= 256:
            game_window.blit(self.image, (self.x, self.y))
            return
        Ball.balls.remove(self)

    def check_collision(self):
        for enemy in copy.copy(ETank.tanks):
            if self.rect.colliderect(enemy.rect):
                ETank.tanks.remove(enemy)
                #画面外に行くと同時に敵に当たると、二回removeされるのを防ぐため
                try:
                    Ball.balls.remove(self)
                except ValueError:
                    pass
                game.score+=300
                break


class EBall(Ball):
    balls = []
    @classmethod
    def reset(cls):
        cls.balls = []

    @classmethod
    def update_all(cls, enemy):
        for ball in copy.copy(cls.balls):
            ball.update()
            ball.check_collision(enemy)
    @classmethod
    def draw_all(cls):
        for ball in cls.balls:
            ball.draw()

    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 3
        self.image = e_ball_image
        self.rect = self.image.get_rect(center=(self.x, self.y))
        EBall.balls.append(self)
    def update(self):
        super().update()
    def draw(self):
        if 0 <= self.x <= 256 and 0 <= self.y <= 256:
            game_window.blit(self.image, (self.x, self.y))
            return
        EBall.balls.remove(self)
    def check_collision(self, enemy):
        if self.rect.colliderect(enemy.rect):
            game.mode = False
            result.update(game.score)
            result.mode = True


class Laser:
    lasers = []
    COLOR = (0, 192, 255)
    LENGTH = 384
    WIDTH = 16
    RANDOM_LINES = 6

    @classmethod
    def draw_all(cls):
        for laser in copy.copy(cls.lasers):
            laser.draw()
        
    @classmethod
    def reset(cls):
        cls.lasers = []

    def __init__(self, master, x, y, angle):
        self.master = master    # 描画する先
        self.x, self.y = x, y
        self.angle = angle
        self.length = Laser.LENGTH
        self.width = Laser.WIDTH//2
        self.count = 0
        self.mode = 'charge'

        Laser.lasers.append(self)
    
    # self.x, self.yを中心にself.angleだけ回転した点を返す
    def __rotated(self, xy):
        x, y = xy
        # 原点まで平行移動
        dx = x - self.x
        dy = y - self.y
        # 回転行列
        rotated_x = dx * math.cos(self.angle) - dy * math.sin(self.angle)
        rotated_y = dx * math.sin(self.angle) + dy * math.cos(self.angle)
        # 元の位置に戻す
        return int(rotated_x + self.x), int(rotated_y + self.y)
    
    def __draw_laser_particle(self):
        for _ in range(300):
            rx = random.randint(int(self.x), int(self.x + self.length))
            ry = self.y + random.randint(-self.width, self.width)
            self.master.set_at(self.__rotated((rx, ry)), random.choice([(255, 255, 255), Laser.COLOR]))
    
    def __draw_laser(self, random_lines, width):
        # 斜めの線がきれいに書けるので、lineではなくpolygonで描画
        pygame.draw.polygon(
            self.master, (255, 255, 255),
            [self.__rotated((self.x, self.y-width//2)),
             self.__rotated((self.x + self.length, self.y-width//2)),
             self.__rotated((self.x + self.length, self.y + width//2)),
             self.__rotated((self.x, self.y + width//2))],
            0)
        # ランダムに線を引く
        for _ in range(random_lines):
            r = random.randint(-width//2, width//2)
            pygame.draw.line(
                self.master, Laser.COLOR,
                self.__rotated((self.x, self.y+r)),
                self.__rotated((self.x + self.length, self.y+r)),
                1)
    
    def __charge(self):
        if self.width:
            self.__draw_laser(Laser.RANDOM_LINES//2, self.width)
            #ランダムにパーティクルを描画
            diff = self.width * 4
            for _ in range(50):
                rx = random.randint(int(self.x-diff), int(self.x+diff))
                ry = random.randint(int(self.y-diff), int(self.y+diff))
                self.master.set_at((rx, ry), random.choice([(255, 255, 255), Laser.COLOR]))
            self.__draw_laser_particle()
            self.width -= 1
            return  

        self.width = Laser.WIDTH
        self.count = 0
        self.mode = 'beam'
    
    def __beam(self):
        # 少しディレイをかける
        if self.count <= 10:
            return

        global gw_pos
        gw_pos = (random.randint(-3, 3), random.randint(-3, 3))
        
        r_width = random.randint(self.width-2, self.width+2)
        self.__draw_laser(Laser.RANDOM_LINES, r_width)
        # 両端に線を引く
        diff = r_width//2
        pygame.draw.line(self.master, Laser.COLOR, self.__rotated((self.x, self.y-diff)), self.__rotated((self.x + self.length, self.y-diff)), 2),
        pygame.draw.line(self.master, Laser.COLOR, self.__rotated((self.x, self.y+diff)), self.__rotated((self.x + self.length, self.y+diff)), 2)
        
        self.check_collision()

        if self.count == 40:
            self.width = Laser.WIDTH//2
            self.mode = 'finish'

    def __finish(self):
        if self.width:
            self.__draw_laser(Laser.RANDOM_LINES//2, self.width)
            self.__draw_laser_particle()
            self.width -= 2
            return
        global gw_pos
        gw_pos = (0, 0)
        Laser.lasers.remove(self)

    def check_collision(self):
        for enemy in ETank.tanks:
            if self.colliderect(enemy.rect):
                ETank.tanks.remove(enemy)
                game.score+=300
        for e_ball in EBall.balls:
            if self.colliderect(e_ball.rect):
                EBall.balls.remove(e_ball)
    
    def colliderect(self, rect):
        def point_to_segment_distance(px, py, x1, y1, x2, y2):
            # 線分ABのベクトル
            dx = x2 - x1
            dy = y2 - y1

            if dx == dy == 0:
                # AとBが同じ点
                return math.hypot(px - x1, py - y1)

            # 線分上の最近点を求めるためのt（0 <= t <= 1）
            t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
            t = max(0, min(1, t))

            # 最近点の座標
            nearest_x = x1 + t * dx
            nearest_y = y1 + t * dy

            # 点と最近点の距離
            return math.hypot(px - nearest_x, py - nearest_y)

        point = ([rect.x, rect.y],
                 [rect.x+rect.width, rect.y],
                 [rect.x+rect.width, rect.y+rect.height],
                 [rect.x, rect.y+rect.height]
                 )
        sx, sy = self.x, self.y
        ex, ey = self.__rotated((self.x+self.length, self.y))
        for p in point:
            if point_to_segment_distance(p[0], p[1], sx, sy, ex, ey) <= self.width//2:
                return True

        return False

    def draw(self):
        self.count += 1
        if self.mode == 'charge':
            self.__charge()
        elif self.mode == 'beam':
            self.__beam()
        elif self.mode == 'finish':
            self.__finish()

class Finger:
    fingers = []

    # 一番近い座標の指を返す
    @classmethod
    def search(cls, id):
        for f in cls.fingers:
            if f.id == id:
                return f
        return None
    
    @classmethod
    def reset(cls):
        Finger.fingers = []

    def __init__(self, id, x, y):
        self.id = id
        self.x, self.y = x, y
        Finger.fingers.append(self)

    def update(self, x, y):
        self.x, self.y = x, y
    
    def remove(self):
        Finger.fingers.remove(self)
        
class Game:
    def __init__(self):
        self.last_time = time.time()
        self.interval = 3
        self.mode = True
        stick.holding = False
        self.tank = Tank(128, 128)
        self.score = 0
        ETank.reset()
        EBall.reset()
        Ball.reset()
        Laser.reset()
        Finger.reset()
            
    def process(self):
        # ゲームの状態更新
        game.score += 0.5
        # 一定時間ごとにスコアに応じて敵を出現させる
        if time.time() - self.last_time >= self.interval:
            ETank(random.randint(8, 248), random.randint(8, 248), self.tank.x, self.tank.y)
            if self.score >= 10000:
                ETank(random.randint(8, 248), random.randint(8, 248), self.tank.x, self.tank.y)
            if self.score >= 2000:
                ETank(random.randint(8, 248), random.randint(8, 248), self.tank.x, self.tank.y)
            self.last_time = time.time()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:  # キーを押したとき
                self.tank.shoot()
            
            # マルチタッチ対応
            if event.type == pygame.FINGERDOWN:
                finger_id, finger_x, finger_y = event.finger_id, event.x*WIDTH, event.y*HEIGHT
                Finger(finger_id, finger_x, finger_y)
                if shoot_button.pressed(finger_x, finger_y):
                    self.tank.shoot()
                if fire_button.pressed(finger_x, finger_y):
                    self.tank.fire()
            elif event.type == pygame.FINGERMOTION:
                finger_id, finger_x, finger_y = event.finger_id, event.x*WIDTH, event.y*HEIGHT
                finger = Finger.search(finger_id)
                if finger is not None:
                    finger.update(finger_x, finger_y)
            elif event.type == pygame.FINGERUP:
                finger_id = event.finger_id
                finger = Finger.search(finger_id)
                if finger is not None:
                    finger.remove()
        
        # スティック操での移動処理
        for f in Finger.fingers:
            if f.x <= WIDTH//2:
                stick.update([f.x, f.y])
                self.tank.update(stick.angle)
                self.tank.move()
                break
        else:
            stick.update()
            self.tank.update(stick.angle)
                    
        gauge.update(self.tank.ball/5)
        ETank.update_all()
        Ball.update_all()
        EBall.update_all(self.tank)

        # 描画処理
        game_window.fill((255, 224, 160))
        self.tank.draw()
        ETank.draw_all()
        Ball.draw_all()
        EBall.draw_all()
        Laser.draw_all()
        stick.draw()
        if self.tank.ball:
            shoot_button.draw()
        else:
            shoot_dummy.draw()
        if self.tank.ball >= 5:
            fire_button.draw()
        else:
            fire_dummy.draw()
        gauge.draw()
        text = font.render(f'Score:{int(self.score)}', True, (0, 0, 0))
        screen.fill((0, 0, 0))
        screen.blit(game_window, gw_pos)
        screen.blit(text, (184, 8))

class Result:
    def __init__(self):
        self.font = pygame.font.SysFont('', 32)
        self.font_jp = pygame.font.Font('NotoSansJP-VariableFont_wght.ttf', 16)
        self.score = 0
        self.high_score = 0
        self.mode = False
        self.prepare_img()

    # リザルト画面の準備
    def prepare_img(self):
        self.text = self.font.render(f'Score:{self.score:.0f}', True, (0, 0, 0))
        self.text2 = self.font.render(f'HighScore:{self.high_score:.0f}', True, (0, 0, 0))
        self.text3 = self.font.render('Touch To Restart', True, (0, 0, 0))
        text_post = self.font_jp.render('XでPost(左上にリンクが出ます)', True, (0, 0, 0))
        self.text_post = text_post.copy()
        self.text_post.blits((
            (text_post, (0, 1)),
            (text_post, (1, 0)),
            (text_post, (1, 1)))
            )
        self.surface = pygame.Surface((WIDTH, HEIGHT))
        self.surface.fill((255, 224, 160))
        self.surface.blits((
            (self.text, (32, 32)),
            (self.text2, (32, 64)),
            (self.text_post, (32, 96)),
            (self.text3, (32, 216)))
        )
    def update(self, score):
        self.score = score
        if self.high_score < score:
            self.high_score = score
        self.prepare_img()
    def show(self):
        global game
        game_window.fill((255, 224, 160))
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:  # キーを押したとき
                game = Game()
                self.mode = False
            if event.type == pygame.MOUSEBUTTONDOWN:  # 画面を押したとき
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if 80 <= mouse_y <= 136:
                    url = f'https://x.com/intent/post?text=%E3%82%B9%E3%82%B3%E3%82%A2%E3%81%AF{self.score:.0f}%E3%81%A7%E3%81%97%E3%81%9F%EF%BC%81%0A%E3%83%8F%E3%82%A4%E3%82%B9%E3%82%B3%E3%82%A2%E3%81%AF{self.high_score:.0f}%E3%81%A7%E3%81%97%E3%81%9F%EF%BC%81%0A%0A%E3%81%93%E3%81%A1%E3%82%89%E3%81%8B%E3%82%89%E9%81%8A%E3%81%B9%E3%81%BE%E3%81%99%0Ahttps%3A%2F%2Fprosamo.github.io%2Ftank-game%2F'
                    #js.window.open(url, '_blank')
                    #js.window.location.href = url
                    try:
                        link = document.getElementById('link')
                        link.remove()
                    except:
                        pass
                    button_html = f''' <a id = link href="{url}" target="_blank" id="openLinkButton">Open Link</a> '''
                    document.body.insertAdjacentHTML('beforeend', button_html)
                else:
                    try:
                        link = document.getElementById('link')
                        link.remove()
                    except:
                        pass
                    game = Game()
                    self.mode = False

        screen.blit(self.surface, (0, 0))

async def main():
    while True:
        if game.mode:
            game.process()
        if result.mode:
            result.show()
        pygame.display.update()
        clock.tick(30)
        await asyncio.sleep(0)

if __name__ == '__main__':
    stick = Stick(40, 184, 20)
    shoot_button = Button(184, 184, 20)
    shoot_dummy = Button(184, 184, 20, color = (128, 128, 128))
    fire_button = Button(184, 128, 20, color = (255, 128, 128))
    fire_dummy = Button(184, 128, 20, color = (128, 128, 128))
    gauge = Gauge(232, 88, 16, 80)
    game = Game()
    result = Result()
    asyncio.run(main())


