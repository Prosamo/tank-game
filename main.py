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
        game_window.blit(alpha_surface, (self.x, self.y))
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
            Laser(self.x, self.y, self.angle)
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
        for enemy in ETank.tanks:
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
    def __init__(self, x, y, angle):
        self.x, self.y = x, y
        self.angle = angle
        self.max_length = 384
        self.s_pos = (self.x, self.y)
        self.e_pos = (self.x + self.max_length * math.cos(self.angle),
                      self.y + self.max_length * math.sin(self.angle))
        self.rect = pygame.Rect(self.x, self.y-32, WIDTH, 64)
        self.width = 8
        Laser.lasers.append(self)
        self.count = 0
        self.mode = 'charge'

        self.a = (self.e_pos[1]-self.s_pos[1])/(self.e_pos[0]-self.s_pos[0])
        self.a = max(min(self.a, 2147483637), -2147483637)
        self.b = self.s_pos[1] - self.a * self.s_pos[0]
    
    def charge(self):
        if self.width:
            pygame.draw.line(game_window, (255, 255, 255), self.s_pos, self.e_pos, self.width)
            x, y = self.s_pos
            ex, ey = self.e_pos
            for _ in range(2):
                diff = random.randint(-self.width//2, self.width//2)
                pygame.draw.line(game_window, Laser.COLOR, 
                                 (x-int(diff*math.sin(self.angle)), y+int(diff*math.cos(self.angle))), 
                                 (ex-int(diff*math.sin(self.angle)), ey+int(diff*math.cos(self.angle))), 
                                 1)
            #ランダムにパーティクルを描画
            diff = self.width * 4
            for _ in range(50):
                game_window.set_at((random.randint(int(x-diff), int(x+diff)), random.randint(int(y-diff), int(y+diff))), random.choice([(255, 255, 255), Laser.COLOR]))
            for _ in range(300):
                if int(x) <= int(ex):
                    rx = random.randint(int(x), int(ex))
                else:
                    rx = random.randint(int(ex), int(x))
                ry = int(rx * self.a + self.b)
                diff = random.randint(-self.width, self.width)
                game_window.set_at((rx-int(diff*math.sin(self.angle)), ry+int(diff*math.cos(self.angle))), random.choice([(255, 255, 255), Laser.COLOR]))
            self.width -= 1
            return  

        self.width = 16
        self.count = 0
        self.mode = 'beam'
    
    def beam(self):
        if self.count <= 10:
            return
        s_pos = self.s_pos
        e_pos = self.e_pos
        
        global gw_pos
        gw_pos = (random.randint(-3, 3), random.randint(-3, 3))
        x, y = s_pos
        ex, ey = e_pos

        pygame.draw.line(game_window, (255, 255, 255), (x, y), (ex, ey), self.width)
        # yの方がsin、x方がcosでずらす
        diff = self.width//2
        pygame.draw.line(game_window, Laser.COLOR, 
                         (x-int((-diff+1)*math.sin(self.angle)), y+int((-diff+1)*math.cos(self.angle))), 
                         (ex-int((-diff+1)*math.sin(self.angle)), ey+int((-diff+1)*math.cos(self.angle))), 
                         2)
        pygame.draw.line(game_window, Laser.COLOR, 
                         (x-int((diff-1)*math.sin(self.angle)), y+int((diff-1)*math.cos(self.angle))), 
                         (ex-int((diff-1)*math.sin(self.angle)), ey+int((diff-1)*math.cos(self.angle))), 
                         2)
        for _ in range(5):
            r = random.randint(-self.width//2, self.width//2)
            pygame.draw.line(game_window, Laser.COLOR, 
                (x-int(r*math.sin(self.angle)), y+int(r*math.cos(self.angle))), 
                (ex-int(r*math.sin(self.angle)), ey+int(r*math.cos(self.angle))), 
                 1)
        self.check_collision()
        if self.count == 40:
            gw_pos = (0, 0)
            self.width = 8
            self.mode = 'finish'
    def finish(self):
        if self.width:
            pygame.draw.line(game_window, (255, 255, 255), self.s_pos, self.e_pos, self.width)
            x, y = self.s_pos
            ex, ey = self.e_pos
            for _ in range(2):
                r = random.randint(-self.width//2, self.width//2)
                pygame.draw.line(game_window, Laser.COLOR, (x+r, y+r), (ex+r, ey+r), 1)
            #ランダムにパーティクルを描画
            x, y = self.s_pos
            ex, ey = self.e_pos
            r = self.width * 4
            for _ in range(300):
                if int(x) <= int(ex):
                    rx = random.randint(int(x), int(ex))
                else:
                    rx = random.randint(int(ex), int(x))
                ry = rx * self.a + self.b
                diff = random.randint(-self.width, self.width)
                game_window.set_at((int(rx-diff*math.sin(self.angle)), int(ry+diff*math.cos(self.angle))), random.choice([(255, 255, 255), Laser.COLOR]))
            self.width -= 2
            return

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
        for p in point:
            if point_to_segment_distance(p[0], p[1], self.s_pos[0], self.s_pos[1], self.e_pos[0], self.e_pos[1]) <= self.width//2:
                return True

        return False

    def draw(self):
        self.count += 1
        if self.mode == 'charge':
            self.charge()
        elif self.mode == 'beam':
            self.beam()
        elif self.mode == 'finish':
            self.finish()

class Game:
    def __init__(self):
        self.last_time = time.time()
        self.interval = 3
        self.mode = True
        stick.holding = False
        self.tank = Tank(128, 128)
        self.score = 0
        ETank.tanks = []
        EBall.balls = []
        Ball.balls = []
        Laser.lasers = []

        self.shake_duration = 0
        self.shake_offset = (0, 0)
            
    def process(self):
        game_window.fill((255, 224, 160))
        game.score += 0.5
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
        for l in copy.copy(Laser.lasers):
            l.draw()
        screen.fill((0, 0, 0))
        screen.blit(game_window, gw_pos)
        screen.blit(text, (184, 8))
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
                    """
                    button_html = '''
                                  <div id="tmp_div" style="display:none;">
                                    <a id="tempLink" href="{url}" target="_blank">Open Link</a>
                                    <script>
                                      document.getElementById("tempLink").addEventListener("click", function(event) {
                                        event.preventDefault();
                                        window.open("{url}", '_blank');
                                      });

                                      document.getElementById("tempLink").addEventListener("touchstart", function(event) {
                                        event.preventDefault();
                                        window.open("{url}", '_blank');
                                      });
                                      document.body.insertAdjacentHTML('beforeend', document.getElementById('tmp_div').outerHTML);
                                      var temp_link = document.getElementById('tempLink');
                                      temp_link.click();
                                      var touchEvent = new Event('touchstart');
                                      temp_link.dispatchEvent(touchEvent);
                                      document.getElementById('tmp_div').remove();
                                    </script>
                                  </div>
                                  '''
                    button_html = f'{button_html}'
                    """
                    """
                    button_html = f'''
                                  <div id = tmp_div style="display:none">
                                  <a id="tempLink" href="{url}" target="_blank" id="openLinkButton">Open Link</a>
                                  <script>
                                  document.getElementById("openLinkButton").addEventListener("click", function(event) {{
                                      event.preventDefault();
                                      window.open("{url}", '_blank');
                                  }});
                                  
                                  document.getElementById("openLinkButton").addEventListener("touchstart", function(event) {{
                                      event.preventDefault();
                                      window.open("{url}", '_blank');
                                  }});
                                  var touchEvent = new Event('touchstart');
                                  temp_link.dispatchEvent(touchEvent);
                                  </script>
                                  </div>
                                  '''
                    document.body.insertAdjacentHTML('beforeend', button_html)
                    temp_link = document.getElementById('tempLink')
                    tmp_div = document.getElementById('tmp_div')
                    temp_link.click()
                    tmp_div.remove()
                    """
                    
                else:
                    try:
                        link = document.getElementById('link')
                        link.remove()
                    except:
                        pass
                    game = Game()
                    self.mode = False
        text = self.font.render(f'Score:{self.score:.0f}', True, (0, 0, 0))
        text2 = self.font.render(f'HighScore:{self.high_score:.0f}', True, (0, 0, 0))
        text3 = self.font.render('Touch To Restart', True, (0, 0, 0))
        text_post = self.font_jp.render('XでPost(左上にリンクが出ます)', True, (0, 0, 0))
        game_window.blit(text, (32, 32))
        game_window.blit(text2, (32, 64))
        game_window.blit(text_post, (32, 96))
        game_window.blit(text_post, (33, 96))
        game_window.blit(text_post, (32, 97))
        game_window.blit(text_post, (33, 97))
        game_window.blit(text3, (32, 216))
        screen.blit(game_window, (0, 0))
async def main():
    while True:
        if game.mode:
            game.process()
        if result.mode:
            result.show()
        pygame.display.update()
        clock.tick(30)
        await asyncio.sleep(0)
def vocalize(a):
    pygame.mixer.init(frequency=44100)
    pygame.mixer.set_num_channels(32)
    sound_key = pygame.mixer.Sound(a)
    sound_key.play()
stick = Stick(40, 184, 20)
shoot_button = Button(184, 184, 20)
shoot_dummy = Button(184, 184, 20, color = (128, 128, 128))
fire_button = Button(184, 128, 20, color = (255, 128, 128))
fire_dummy = Button(184, 128, 20, color = (128, 128, 128))
gauge = Gauge(232, 88, 16, 80)
game = Game()
result = Result(0)

asyncio.run(main())


