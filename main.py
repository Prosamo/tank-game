import asyncio
import pygame, sys, time, random, math, webbrowser

pygame.init()    # Pygameを初期化
screen = pygame.display.set_mode((256, 256))    # 画面を作成
pygame.display.set_caption("戦車ゲーム")    # タイトルを作成
clock = pygame.time.Clock()
font = pygame.font.SysFont('', 16)

tank_image = pygame.image.load("tank.png")
ball_image = pygame.image.load("ball.png")
e_tank_image = pygame.image.load("e-tank.png")
e_ball_image = pygame.image.load("e-ball.png")

class Stick:
    def __init__(self, x, y, r, border_width = 2):
        self.x, self.y = x, y
        self.r = r
        self.inner_r= int(self.r * 0.6)
        self.border_width = border_width
        self.inner_x = self.x + self.r - self.inner_r # 初期位置を調整
        self.inner_y = self.y + self.r - self.inner_r # 初期位置を調整

        self.angle = 0
        
        self.holding = False
    def draw(self):
        # 透明な土台を設定
        alpha_surface = pygame.Surface((self.r*2, self.r*2), pygame.SRCALPHA)
        alpha_surface.fill((0, 0, 0, 0))
        #白い枠線
        pygame.draw.circle(alpha_surface, (255, 255, 255, 128), (self.r, self.r), self.r, self.border_width)
        #灰色の丸
        pygame.draw.circle(alpha_surface, (128, 128, 128, 128), (self.inner_x, self.inner_y), self.inner_r)
        #描画
        screen.blit(alpha_surface, (self.x, self.y))
    def update(self, mouse_x, mouse_y):
        if self.holding and mouse_x <= 128:
            dx = mouse_x - (self.x + self.r)
            dy = mouse_y - (self.y + self.r)
            self.angle = math.atan2(dy, dx)
            self.inner_x = self.r + self.r * 0.4 * math.cos(self.angle)# 中心からの距離を計算
            self.inner_y = self.r + self.r * 0.4 * math.sin(self.angle)# 中心からの距離を計算
            self.inner_x = int(self.inner_x)
            self.inner_y = int(self.inner_y)
        else:
            self.inner_x = self.r
            self.inner_y = self.r

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
        #青い円
        pygame.draw.circle(alpha_surface, (*self.color, 128), (self.r, self.r), self.r)
        #白い枠線
        pygame.draw.circle(alpha_surface, (255, 255, 255, 128), (self.r, self.r), self.r, 2)
        #描画
        screen.blit(alpha_surface, (self.x,self.y))
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
        screen.blit(alpha_surface, (self.x, self.y))
    def update(self, rate):
        self.rate = rate

class Tank:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.image = tank_image
        self.speed = 1
        self.angle = 0
        self.ball = 5
        self.last_charge_time = time.time()
        self.rect = self.image.get_rect(center=(self.x, self.y))
    def draw(self):
        screen.blit(self.image, self.rect.topleft)
    def update(self, angle):
        self.charge()
        self.angle = angle
        self.image = pygame.transform.rotate(tank_image, -math.degrees(self.angle))
        self.rect = self.image.get_rect(center=(self.x, self.y))
    def charge(self):
        current_time = time.time()
        if current_time - self.last_charge_time >= 1.1:
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
            Beam(self.x, self.y, self.angle)
            game.start_shake(10)
class ETank:
    tanks = []
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
        screen.blit(self.image, self.rect.topleft)
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
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 2
        self.image = ball_image
        self.rect = self.image.get_rect(center=(self.x, self.y))
        Ball.balls.append(self)

    def update(self):
        self.x += self.speed * math.cos(self.angle)
        self.y += self.speed * math.sin(self.angle)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def draw(self):
        if 0 <= self.x <= 256 and 0 <= self.y <= 256:
            screen.blit(self.image, (self.x, self.y))
            return
        Ball.balls.remove(self)

    def check_collision(self):
        for enemy in ETank.tanks:
            if self.rect.colliderect(enemy.rect):
                ETank.tanks.remove(enemy)
                Ball.balls.remove(self)
                game.score+=300
                break
class EBall(Ball):
    balls = []
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = 2
        self.image = e_ball_image
        self.rect = self.image.get_rect(center=(self.x, self.y))
        EBall.balls.append(self)
    def update(self):
        super().update()
    def draw(self):
        if 0 <= self.x <= 256 and 0 <= self.y <= 256:
            screen.blit(self.image, (self.x, self.y))
            return
        EBall.balls.remove(self)
    def check_collision(self, enemy):
        if self.rect.colliderect(enemy.rect):
            game.mode = False
            result.update(game.score)
            result.mode = True

# ビームクラスの定義
class Beam:
    beams = []
    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        self.angle = angle
        self.length = 0
        self.max_length = 384
        self.life = 60  # ビームの寿命（フレーム数）
        self.alpha = 255  # 初期の透明度
        self.get_rect()
        Beam.beams.append(self)
    
    def update(self):
        self.get_rect()
        if self.length < self.max_length:
            self.length += 20
        self.life -= 1
        if self.life < 50:  # 寿命の半分を過ぎたら徐々に透明にする
            self.alpha = int(255 * (self.life / 50))
    
    def draw(self, ):
        if self.life <= 0:
            Beam.beams.remove(self)
        end_pos = (self.x + self.length * math.cos(self.angle),
                   self.y + self.length * math.sin(self.angle))
        beam_surface = pygame.Surface((256, 256), pygame.SRCALPHA)
        # 青白い発光を描画
        pygame.draw.line(beam_surface, (0, 192, 255, self.alpha // 1.5), (self.x, self.y), end_pos, 15)
        # 白いビームを描画
        pygame.draw.line(beam_surface, (255, 255, 255, self.alpha), (self.x, self.y), end_pos, 5)
        screen.blit(beam_surface, (0, 0))

    def get_rect(self):
        self.rect = pygame.Rect(self.x-8 + self.length * math.cos(self.angle),
                     self.y-8 + self.length * math.sin(self.angle),
                     16, 16)
    
    def check_collision(self):
        for enemy in ETank.tanks:
            if self.rect.colliderect(enemy.rect):
                ETank.tanks.remove(enemy)
                game.score+=300
        for e_ball in EBall.balls:
            if self.rect.colliderect(e_ball.rect):
                EBall.balls.remove(e_ball)

class Shake:
    def __init__(self):
        self.score = 0
        self.shake_duration = 0
        self.shake_offset = (0, 0)
    
    def start_shake(self, duration):
        self.shake_duration = duration
    
    def update_shake(self):
        if self.shake_duration > 0:
            self.shake_duration -= 1
            self.shake_offset = (random.randint(-5, 5), random.randint(-5, 5))
        else:
            self.shake_offset = (0, 0)

class Game:
    def __init__(self):
        self.last_time = time.time()
        self.interval = 3
        self.mode = True
        self.tank = Tank(128, 128)
        self.score = 0
        ETank.tanks = []
        EBall.balls = []
        Ball.balls = []
        Beam.beams = []

        self.shake_duration = 0
        self.shake_offset = (0, 0)
        
    def start_shake(self, duration):
        self.shake_duration = duration
    
    def update_shake(self):
        if self.shake_duration > 0:
            self.shake_duration -= 1
            self.shake_offset = (random.randint(-2, 2), random.randint(-2, 2))
        else:
            self.shake_offset = (0, 0)
            
    def process(self):
        screen.fill((255, 224, 160))
        game.score += 0.3
        if time.time() - self.last_time >= self.interval:
            ETank(random.randint(8, 248), random.randint(8, 248), self.tank.x, self.tank.y)
            ETank(random.randint(8, 248), random.randint(8, 248), self.tank.x, self.tank.y)
            self.last_time = time.time()
     
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:  # キーを押したとき
                self.tank.shoot() 

            # マウスボタンの状態をチェック
            mouse_pressed = pygame.mouse.get_pressed()
            if mouse_pressed[0]:
                # 左クリックが押されている場合
                stick.holding = True
            else:
                stick.holding = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if shoot_button.pressed(mouse_x, mouse_y):
                    self.tank.shoot()
                if fire_button.pressed(mouse_x, mouse_y):
                    self.tank.fire()
                    
        self.update_shake()
        mouse_x, mouse_y = pygame.mouse.get_pos()
        stick.update(mouse_x, mouse_y)
        gauge.update(self.tank.ball/5)
        self.tank.update(stick.angle)
        if stick.holding and mouse_x <= 128:
            self.tank.move()
        self.tank.draw()
        for i in ETank.tanks:
            i.update()
            i.draw()
        for i in Ball.balls:
            i.update()
            i.draw()
            i.check_collision()
        for i in EBall.balls:
            i.update()
            i.draw()
            i.check_collision(self.tank)
        # ビームの更新と描画
        for i in Beam.beams:
            i.update()
            i.draw()
            i.check_collision()
        stick.draw()
        shoot_button.draw()
        fire_button.draw()
        gauge.draw()
        text = font.render(f'Score:{int(self.score)}', True, (0, 0, 0))
        screen.blit(text, (184, 8))
        screen.blit(screen, self.shake_offset)
class Result:
    def __init__(self, score):
        self.font = pygame.font.SysFont('', 32)
        self.font_jp = pygame.font.Font('NotoSansJP-VariableFont_wght.ttf', 16)
        self.score = 0
        self.high_score = 0
        self.mode = False
    def update(self, score):
        self.score = score
        if self.high_score < score:
            self.high_score = score
    def show(self):
        global game
        screen.fill((255, 224, 160))
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
                    webbrowser.open(f'https://x.com/intent/post?text=%E3%82%B9%E3%82%B3%E3%82%A2%E3%81%AF{self.score:.0f}%E3%81%A7%E3%81%97%E3%81%9F%EF%BC%81%0A%E3%83%8F%E3%82%A4%E3%82%B9%E3%82%B3%E3%82%A2%E3%81%AF{self.high_score:.0f}%E3%81%A7%E3%81%97%E3%81%9F%EF%BC%81%0A%0A%E3%81%93%E3%81%A1%E3%82%89%E3%81%8B%E3%82%89%E9%81%8A%E3%81%B9%E3%81%BE%E3%81%99%0Ahttps%3A%2F%2Fprosamo.github.io%2Ftank-game%2F')
                else:
                    game = Game()
                    self.mode = False
        text = self.font.render(f'Score:{int(self.score)}', True, (0, 0, 0))
        text2 = self.font.render(f'HighScore:{int(self.high_score)}', True, (0, 0, 0))
        text3 = self.font.render('Touch To Restart', True, (0, 0, 0))
        text_post = self.font_jp.render('X で Post', True, (0, 0, 0))
        screen.blit(text, (32, 32))
        screen.blit(text2, (32, 64))
        screen.blit(text_post, (32, 96))
        screen.blit(text_post, (33, 96))
        screen.blit(text_post, (32, 97))
        screen.blit(text_post, (33, 97))
        screen.blit(text3, (32, 216))
async def main():
    while True:
        if game.mode:
            game.process()
        if result.mode:
            result.show()
        pygame.display.update()
        clock.tick(50)
        await asyncio.sleep(0)
def vocalize(a):
    pygame.mixer.init(frequency=44100)
    pygame.mixer.set_num_channels(32)
    sound_key = pygame.mixer.Sound(a)
    sound_key.play()
stick = Stick(40, 184, 20)
shoot_button = Button(184, 184, 20)
fire_button = Button(184, 128, 20, color = (255, 128, 128))
gauge = Gauge(232, 88, 16, 80)
game = Game()
result = Result(0)

asyncio.run(main())


