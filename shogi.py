#!/usr/bin/env python3
"""
kensyo-shogi v1.0.1 — Python Shogi (将棋) by kensyo-lab
https://github.com/kensyo-lab/kensyo-shogi
© 腱鞘炎 2026 / MIT License
"""

__version__ = "1.0.1"

import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageTk
import os, sys, threading, time, random, json, datetime

# ── アセットパス ───────────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
SPRITE_PATH = os.path.join(BASE_DIR, "assets", "images", "pieces.png")
BOARD_PATH  = os.path.join(BASE_DIR, "assets", "images", "board.png")
TITLE_PATH  = os.path.join(BASE_DIR, "assets", "images", "kensyo-shogi-title.png")
SOUND_PATH  = os.path.join(BASE_DIR, "assets", "sounds", "koma.mp3")
KIFU_DIR    = os.path.join(BASE_DIR, "kifu")
os.makedirs(KIFU_DIR, exist_ok=True)

# ── サウンド ──────────────────────────────────────────────────────────────
_sound_enabled = True
_sound_func    = None

def _init_sound():
    global _sound_func
    try:
        import pygame
        pygame.mixer.init()
        sound = pygame.mixer.Sound(SOUND_PATH)
        _sound_func = lambda: threading.Thread(target=sound.play, daemon=True).start()
        return
    except Exception: pass
    try:
        from playsound import playsound
        _sound_func = lambda: threading.Thread(
            target=playsound, args=(SOUND_PATH, False), daemon=True).start()
        return
    except Exception: pass
    if sys.platform == "darwin":
        _sound_func = lambda: os.popen(f'afplay "{SOUND_PATH}" &')
        return
    for cmd in ("mpg123", "aplay"):
        if os.system(f"which {cmd} > /dev/null 2>&1") == 0:
            _sound_func = lambda c=cmd: os.popen(f'{c} "{SOUND_PATH}" &')
            return
    _sound_func = lambda: None

_init_sound()

def play_sound():
    if _sound_enabled and _sound_func:
        _sound_func()

# ── スプライトシート ──────────────────────────────────────────────────────
CELL_W, CELL_H = 140, 148

SPRITE_SENTE = {
    '王':(0,0),'飛':(0,1),'角':(0,2),'金':(0,3),
    '銀':(0,4),'桂':(0,5),'香':(0,6),'歩':(0,7),
    '龍':(1,1),'馬':(1,2),
    '全':(1,4),'圭':(1,5),'杏':(1,6),'と':(1,7),
}
SPRITE_GOTE = {
    '王':(2,0),'飛':(2,1),'角':(2,2),'金':(2,3),
    '銀':(2,4),'桂':(2,5),'香':(2,6),'歩':(2,7),
    '龍':(3,1),'馬':(3,2),
    '全':(3,4),'圭':(3,5),'杏':(3,6),'と':(3,7),
}

PROMOTE_MAP = {'飛':'龍','角':'馬','銀':'全','桂':'圭','香':'杏','歩':'と'}
DEMOTE_MAP  = {v:k for k,v in PROMOTE_MAP.items()}
PROMOTABLE  = set(PROMOTE_MAP.keys())

# ── 合法手テーブル ────────────────────────────────────────────────────────
MOVES = {
    '王': [(-1,-1,False),(-1,0,False),(-1,1,False),(0,-1,False),
           (0,1,False),(1,-1,False),(1,0,False),(1,1,False)],
    '金': [(-1,-1,False),(-1,0,False),(-1,1,False),(0,-1,False),(0,1,False),(1,0,False)],
    '銀': [(-1,-1,False),(-1,0,False),(-1,1,False),(1,-1,False),(1,1,False)],
    '桂': [(-2,-1,False),(-2,1,False)],
    '香': [(-1,0,True)],
    '歩': [(-1,0,False)],
    '飛': [(0,-1,True),(0,1,True),(-1,0,True),(1,0,True)],
    '角': [(-1,-1,True),(-1,1,True),(1,-1,True),(1,1,True)],
    '龍': [(0,-1,True),(0,1,True),(-1,0,True),(1,0,True),
           (-1,-1,False),(-1,1,False),(1,-1,False),(1,1,False)],
    '馬': [(-1,-1,True),(-1,1,True),(1,-1,True),(1,1,True),
           (-1,0,False),(1,0,False),(0,-1,False),(0,1,False)],
    '全': [(-1,-1,False),(-1,0,False),(-1,1,False),(0,-1,False),(0,1,False),(1,0,False)],
    '圭': [(-1,-1,False),(-1,0,False),(-1,1,False),(0,-1,False),(0,1,False),(1,0,False)],
    '杏': [(-1,-1,False),(-1,0,False),(-1,1,False),(0,-1,False),(0,1,False),(1,0,False)],
    'と': [(-1,-1,False),(-1,0,False),(-1,1,False),(0,-1,False),(0,1,False),(1,0,False)],
}

# 持将棋：入玉駒点数（大駒5点、小駒1点）
NYUUGYOKU_PT = {
    '飛':5,'角':5,'龍':5,'馬':5,
    '歩':1,'香':1,'桂':1,'銀':1,'金':1,'と':1,'杏':1,'圭':1,'全':1,
}

# ── 評価関数 ─────────────────────────────────────────────────────────────
PIECE_VALUE = {
    '歩':100,'香':430,'桂':450,'銀':640,'金':690,
    '角':890,'飛':1040,'王':20000,
    'と':600,'杏':540,'圭':540,'全':640,'馬':1150,'龍':1300,
}
_POS_FU=[[ 0,0,0,0,0,0,0,0,0],[20,20,20,20,20,20,20,20,20],
         [ 5,5,5,5,5,5,5,5,5],[ 2,2,2,2,2,2,2,2,2],
         [ 0,0,0,0,0,0,0,0,0],[-5,-5,-5,-5,-5,-5,-5,-5,-5],
         [-10,-10,-10,-10,-10,-10,-10,-10,-10],
         [-15,-15,-15,-15,-15,-15,-15,-15,-15],
         [-20,-20,-20,-20,-20,-20,-20,-20,-20]]
_POS_KYO=[[ 0,0,0,0,0,0,0,0,0],[15,15,15,15,15,15,15,15,15],
          [10,10,10,10,10,10,10,10,10],[ 5,5,5,5,5,5,5,5,5],
          [ 0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],
          [0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0]]
_POS_GIN=[[ 0,0,5,0,0,0,5,0,0],[ 0,5,10,5,5,5,10,5,0],
          [ 0,5,10,5,5,5,10,5,0],[ 0,5,10,5,5,5,10,5,0],
          [ 0,5,5,5,5,5,5,5,0],[0,0,0,0,0,0,0,0,0],
          [0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0]]
_POS_HI=[[ 5,5,5,5,5,5,5,5,5],[10,10,10,10,10,10,10,10,10],
         [ 5,5,5,5,5,5,5,5,5],[0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],
         [0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[ 5,5,5,5,5,5,5,5,5]]
_POS_KAKU=[[ 0,0,0,0,0,0,0,0,0],[ 0,5,0,5,0,5,0,5,0],
           [ 0,0,5,0,5,0,5,0,0],[ 0,5,0,10,0,10,0,5,0],
           [ 0,0,5,0,10,0,5,0,0],[0,0,0,0,0,0,0,0,0],
           [0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0]]
_POS_OU=[[-30,-30,-30,-30,-30,-30,-30,-30,-30],
         [-20,-20,-20,-20,-20,-20,-20,-20,-20],
         [-10,-10,-10,-10,-10,-10,-10,-10,-10],
         [0,0,0,0,0,0,0,0,0],[0,0,0,0,0,0,0,0,0],
         [5,5,5,5,5,5,5,5,5],[5,5,5,5,5,5,5,5,5],
         [5,10,10,10,10,10,10,10,5],[5,15,15,10,10,10,15,15,5]]
POS_TABLE={'歩':_POS_FU,'と':_POS_FU,'香':_POS_KYO,'杏':_POS_KYO,
           '銀':_POS_GIN,'全':_POS_GIN,'飛':_POS_HI,'龍':_POS_HI,
           '角':_POS_KAKU,'馬':_POS_KAKU,'王':_POS_OU}

DIFFICULTY = {
    '入門':{'depth':1,'random':0.8,'pos_eval':False,'tsumi':False},
    '初級':{'depth':2,'random':0.3,'pos_eval':False,'tsumi':False},
    '中級':{'depth':3,'random':0.0,'pos_eval':True, 'tsumi':False},
    '上級':{'depth':4,'random':0.0,'pos_eval':True, 'tsumi':False},
    '最強':{'depth':5,'random':0.0,'pos_eval':True, 'tsumi':True },
}

# ── 棋譜表記ヘルパー ─────────────────────────────────────────────────────
_COL_KANJI = '９８７６５４３２１'
_ROW_KANJI = '一二三四五六七八九'

def move_to_kifu(move, player, board_before):
    """手をKIF風文字列に変換"""
    prefix = '▲' if player == 'S' else '△'
    if move[0] == 'drop':
        _, name, tr, tc = move
        return f"{prefix}{_COL_KANJI[tc]}{_ROW_KANJI[tr]}{name}打"
    else:
        _, fr, fc, tr, tc, promote = move
        piece = board_before[fr][fc][0] if board_before[fr][fc] else '?'
        promo_str = '成' if promote and piece in PROMOTABLE else ''
        return f"{prefix}{_COL_KANJI[tc]}{_ROW_KANJI[tr]}{piece}{promo_str}({fc+1}{fr+1})"

# ── ゲームロジック ────────────────────────────────────────────────────────
def initial_board():
    board = [[None]*9 for _ in range(9)]
    back = ['香','桂','銀','金','王','金','銀','桂','香']
    for c,p in enumerate(back): board[0][c]=(p,'G')
    board[1][1]=('飛','G'); board[1][7]=('角','G')
    for c in range(9): board[2][c]=('歩','G')
    for c in range(9): board[6][c]=('歩','S')
    board[7][1]=('角','S'); board[7][7]=('飛','S')
    for c,p in enumerate(back): board[8][c]=(p,'S')
    return board

def legal_moves_for(board, fr, fc):
    cell = board[fr][fc]
    if cell is None: return []
    piece, player = cell
    sign = -1 if player=='G' else 1
    result = []
    for dr,dc,slide in MOVES.get(piece,[]):
        rdr,rdc = dr*sign, dc*sign
        r,c = fr+rdr, fc+rdc
        while 0<=r<9 and 0<=c<9:
            t = board[r][c]
            if t is None: result.append((r,c))
            elif t[1]!=player: result.append((r,c)); break
            else: break
            if not slide: break
            r+=rdr; c+=rdc
    return result

def drop_moves_for(board, player, name):
    result = []
    for r in range(9):
        for c in range(9):
            if board[r][c]: continue
            if player=='S':
                if name=='歩' and r==0: continue
                if name=='香' and r==0: continue
                if name=='桂' and r<=1: continue
            else:
                if name=='歩' and r==8: continue
                if name=='香' and r==8: continue
                if name=='桂' and r>=7: continue
            if name=='歩':
                if any(board[rr][c]==('歩',player) for rr in range(9)): continue
            result.append((r,c))
    return result

def king_pos(board, player):
    for r in range(9):
        for c in range(9):
            if board[r][c]==('王',player): return (r,c)
    return None

def is_attacked(board, r, c, by_player):
    """(r,c)がby_playerに攻撃されているか"""
    for fr in range(9):
        for fc in range(9):
            cell = board[fr][fc]
            if cell and cell[1]==by_player:
                if (r,c) in legal_moves_for(board,fr,fc):
                    return True
    return False

def is_in_check(board, player):
    kp = king_pos(board, player)
    if kp is None: return True
    opp = 'G' if player=='S' else 'S'
    return is_attacked(board, kp[0], kp[1], opp)

def apply_move_inplace(board, hands, move, player):
    """手を適用して新しい(board, hands)コピーを返す"""
    b = [row[:] for row in board]
    h = {'S':dict(hands['S']),'G':dict(hands['G'])}
    if move[0]=='drop':
        _,name,tr,tc = move
        b[tr][tc]=(name,player)
        h[player][name]-=1
        if h[player][name]==0: del h[player][name]
    else:
        _,fr,fc,tr,tc,promote = move
        piece = b[fr][fc][0]
        captured = b[tr][tc]
        if captured:
            base = DEMOTE_MAP.get(captured[0],captured[0])
            h[player][base]=h[player].get(base,0)+1
        new_piece = PROMOTE_MAP[piece] if promote and piece in PROMOTE_MAP else piece
        b[tr][tc]=(new_piece,player)
        b[fr][fc]=None
    return b,h

def legal_moves_no_check(board, hands, player):
    """王手放置を除いた完全合法手リスト → [(move, board_after, hands_after)]"""
    candidates = []
    # 盤上の駒
    for fr in range(9):
        for fc in range(9):
            cell = board[fr][fc]
            if cell is None or cell[1]!=player: continue
            piece = cell[0]
            for tr,tc in legal_moves_for(board,fr,fc):
                in_zone  = (player=='S' and tr<=2) or (player=='G' and tr>=6)
                from_zone= (player=='S' and fr<=2) or (player=='G' and fr>=6)
                can_promo = piece in PROMOTABLE and (in_zone or from_zone)
                must = False
                if can_promo:
                    if player=='S':
                        if piece=='歩' and tr==0: must=True
                        if piece=='香' and tr==0: must=True
                        if piece=='桂' and tr<=1: must=True
                    else:
                        if piece=='歩' and tr==8: must=True
                        if piece=='香' and tr==8: must=True
                        if piece=='桂' and tr>=7: must=True
                if must:
                    candidates.append(('board',fr,fc,tr,tc,True))
                elif can_promo:
                    candidates.append(('board',fr,fc,tr,tc,True))
                    candidates.append(('board',fr,fc,tr,tc,False))
                else:
                    candidates.append(('board',fr,fc,tr,tc,False))
    # 持ち駒打ち
    for name,cnt in hands[player].items():
        if cnt<=0: continue
        for tr,tc in drop_moves_for(board,player,name):
            candidates.append(('drop',name,tr,tc))

    # 王手放置フィルタ
    result = []
    for move in candidates:
        nb,nh = apply_move_inplace(board,hands,move,player)
        if not is_in_check(nb,player):
            result.append((move,nb,nh))
    return result

def board_hash(board, hands, turn):
    """局面ハッシュ（千日手用）"""
    return (tuple(tuple(r) for r in board),
            tuple(sorted(hands['S'].items())),
            tuple(sorted(hands['G'].items())),
            turn)

def check_nyuugyoku(board, hands, player):
    """持将棋判定: 両王が入玉 & 点数チェック"""
    # 先手の王が敵陣（row<=2）、後手の王が敵陣（row>=6）にいるか
    sp = king_pos(board,'S'); gp = king_pos(board,'G')
    if sp is None or gp is None: return False
    if not (sp[0]<=2 and gp[0]>=6): return False
    # 点数計算
    def pts(pl):
        score = 0
        for r in range(9):
            for c in range(9):
                cell = board[r][c]
                if cell and cell[1]==pl:
                    score += NYUUGYOKU_PT.get(cell[0],0)
        for name,cnt in hands[pl].items():
            score += NYUUGYOKU_PT.get(name,0)*cnt
        return score
    s_pt = pts('S'); g_pt = pts('G')
    # 両者24点以上で持将棋
    return s_pt>=24 and g_pt>=24

# ── αβ探索 ───────────────────────────────────────────────────────────────
INF = 10**9

def evaluate(board, hands, player, use_pos):
    opp = 'G' if player=='S' else 'S'
    score = 0
    for r in range(9):
        for c in range(9):
            cell = board[r][c]
            if cell is None: continue
            name,pl = cell
            val = PIECE_VALUE.get(name,0)
            if use_pos and name in POS_TABLE:
                tbl = POS_TABLE[name]
                pos_bonus = tbl[r][c] if pl=='S' else tbl[8-r][8-c]
                val += pos_bonus
            score += val if pl==player else -val
    for name,cnt in hands[player].items():
        score += PIECE_VALUE.get(name,0)*cnt*0.85
    for name,cnt in hands[opp].items():
        score -= PIECE_VALUE.get(name,0)*cnt*0.85
    return score

def alphabeta(board, hands, player, depth, alpha, beta,
              maximizing, root_player, use_pos, use_tsumi):
    opp = 'G' if player=='S' else 'S'
    if king_pos(board,root_player) is None: return -INF
    if king_pos(board,opp) is None: return INF
    if depth==0: return evaluate(board,hands,root_player,use_pos)
    legal = legal_moves_no_check(board,hands,player)
    if not legal:
        # 詰み
        return -INF if player==root_player else INF
    if maximizing:
        val = -INF
        for move,nb,nh in legal:
            val = max(val, alphabeta(nb,nh,opp,depth-1,alpha,beta,
                                     False,root_player,use_pos,use_tsumi))
            alpha = max(alpha,val)
            if alpha>=beta: break
        return val
    else:
        val = INF
        for move,nb,nh in legal:
            val = min(val, alphabeta(nb,nh,opp,depth-1,alpha,beta,
                                     True,root_player,use_pos,use_tsumi))
            beta = min(beta,val)
            if alpha>=beta: break
        return val

def best_move_search(board, hands, player, difficulty):
    cfg = DIFFICULTY[difficulty]
    depth=cfg['depth']; rand_p=cfg['random']
    use_pos=cfg['pos_eval']; use_tsumi=cfg['tsumi']
    legal = legal_moves_no_check(board,hands,player)
    if not legal: return None
    if random.random()<rand_p:
        m,_,_ = random.choice(legal); return m
    opp = 'G' if player=='S' else 'S'
    random.shuffle(legal)
    best,best_val = None,-INF
    for move,nb,nh in legal:
        val = alphabeta(nb,nh,opp,depth-1,-INF,INF,
                        False,player,use_pos,use_tsumi)
        if val>best_val: best_val,best = val,move
    return best

# ════════════════════════════════════════════════════════════
#  タイトル画面
# ════════════════════════════════════════════════════════════
TITLE_W = 640
TITLE_H = 640
# 下段4枠の中心座標（640px縮小後）
MENU_ITEMS = ['対局開始', '棋譜参照', '設定', '終了']
MENU_CX = [103, 247, 392, 537]
MENU_CY = 517
MENU_W, MENU_H = 120, 91

class TitleScreen(tk.Frame):
    def __init__(self, master, on_select):
        super().__init__(master, bg='black')
        self.on_select = on_select
        self.selected  = 0

        raw = Image.open(TITLE_PATH).convert('RGBA')
        self.img_tk = ImageTk.PhotoImage(
            raw.resize((TITLE_W, TITLE_H), Image.LANCZOS))

        self.canvas = tk.Canvas(self, width=TITLE_W, height=TITLE_H,
                                bg='black', highlightthickness=0)
        self.canvas.pack()
        self.canvas.bind('<Button-1>', self._on_click)
        self.canvas.bind('<Motion>',   self._on_motion)
        master.bind('<Left>',  self._left)
        master.bind('<Right>', self._right)
        master.bind('<Return>',self._enter)
        master.bind('<KP_Enter>',self._enter)
        self._draw()

    def _draw(self):
        self.canvas.delete('all')
        self.canvas.create_image(0, 0, anchor='nw', image=self.img_tk)
        for i, (label, cx) in enumerate(zip(MENU_ITEMS, MENU_CX)):
            x1 = cx - MENU_W//2; y1 = MENU_CY - MENU_H//2
            x2 = cx + MENU_W//2; y2 = MENU_CY + MENU_H//2
            if i == self.selected:
                # 選択中: 明るいオーバーレイ
                self.canvas.create_rectangle(x1, y1, x2, y2,
                    fill='#ffe87a', outline='#c8820a', width=3, stipple='gray50')
            # ラベル
            font_size = 14 if i == self.selected else 12
            weight = 'bold' if i == self.selected else 'normal'
            color  = '#2a0a00' if i == self.selected else '#3a1a00'
            self.canvas.create_text(cx, MENU_CY, text=label,
                font=('Hiragino Sans', font_size, weight), fill=color)

    def _hit_index(self, x, y):
        for i, cx in enumerate(MENU_CX):
            x1 = cx-MENU_W//2; y1 = MENU_CY-MENU_H//2
            x2 = cx+MENU_W//2; y2 = MENU_CY+MENU_H//2
            if x1<=x<=x2 and y1<=y<=y2:
                return i
        return -1

    def _on_click(self, event):
        i = self._hit_index(event.x, event.y)
        if i >= 0:
            self.selected = i; self._draw()
            self.after(80, lambda: self.on_select(i))

    def _on_motion(self, event):
        i = self._hit_index(event.x, event.y)
        if i >= 0 and i != self.selected:
            self.selected = i; self._draw()

    def _left(self, _):
        self.selected = (self.selected-1)%4; self._draw()

    def _right(self, _):
        self.selected = (self.selected+1)%4; self._draw()

    def _enter(self, _):
        self.on_select(self.selected)

    def destroy(self):
        try:
            self.master.unbind('<Left>')
            self.master.unbind('<Right>')
            self.master.unbind('<Return>')
            self.master.unbind('<KP_Enter>')
        except Exception: pass
        super().destroy()

# ════════════════════════════════════════════════════════════
#  設定ダイアログ
# ════════════════════════════════════════════════════════════
class SettingsDialog(tk.Toplevel):
    def __init__(self, parent, current_diff, sound_on):
        super().__init__(parent)
        self.title("設定 / Settings")
        self.configure(bg='#1e1208')
        self.resizable(False,False)
        self.grab_set()
        self.result = None

        tk.Label(self,text="CPU難易度 / Difficulty",
                 font=('Hiragino Sans',13,'bold'),
                 bg='#1e1208',fg='#f5d77a').pack(pady=(16,4))
        self.diff_var = tk.StringVar(value=current_diff)
        descs={'入門':'ランダム手多め','初級':'駒得を考える',
               '中級':'αβ 3手読み','上級':'位置評価 4手読み','最強':'詰み探索 5手読み'}
        df=tk.Frame(self,bg='#1e1208'); df.pack(pady=(0,4))
        for name in DIFFICULTY:
            tk.Radiobutton(df,text=f"  {name}  — {descs[name]}",
                           variable=self.diff_var,value=name,
                           font=('Hiragino Sans',11),bg='#1e1208',fg='#d4c090',
                           selectcolor='#3a2010',anchor='w',
                           activebackground='#1e1208').pack(anchor='w',padx=24)

        tk.Label(self,text="効果音 / Sound",
                 font=('Hiragino Sans',13,'bold'),
                 bg='#1e1208',fg='#f5d77a').pack(pady=(10,4))
        self.sound_var = tk.BooleanVar(value=sound_on)
        sf=tk.Frame(self,bg='#1e1208'); sf.pack()
        for text,val in [("ON"  ,True),("OFF",False)]:
            tk.Radiobutton(sf,text=text,variable=self.sound_var,value=val,
                           font=('Hiragino Sans',12),bg='#1e1208',fg='#f5d77a',
                           selectcolor='#3a2010',
                           activebackground='#1e1208').pack(side='left',padx=12)

        tk.Button(self,text="保存して閉じる / Save",command=self._ok,
                  font=('Hiragino Sans',12,'bold'),
                  bg='#7a4010',fg='white',relief='flat',
                  padx=16,pady=5,cursor='hand2').pack(pady=14)
        self.protocol("WM_DELETE_WINDOW",self._ok)
        self.update_idletasks()
        px=parent.winfo_x()+parent.winfo_width()//2-self.winfo_width()//2
        py=parent.winfo_y()+parent.winfo_height()//2-self.winfo_height()//2
        self.geometry(f"+{max(0,px)}+{max(0,py)}")

    def _ok(self):
        self.result={'difficulty':self.diff_var.get(),'sound':self.sound_var.get()}
        self.destroy()

# ════════════════════════════════════════════════════════════
#  対局設定ダイアログ
# ════════════════════════════════════════════════════════════
class GameSetupDialog(tk.Toplevel):
    def __init__(self, parent, current_diff):
        super().__init__(parent)
        self.title("対局設定 / Game Setup")
        self.configure(bg='#1e1208')
        self.resizable(False,False)
        self.grab_set()
        self.result = None

        tk.Label(self,text="あなたの手番 / Your Color",
                 font=('Hiragino Sans',13,'bold'),
                 bg='#1e1208',fg='#f5d77a').pack(pady=(18,6))
        self.player_var=tk.StringVar(value='S')
        frm=tk.Frame(self,bg='#1e1208'); frm.pack()
        for text,val in [("先手（下）▶",'S'),("後手（上）◀",'G')]:
            tk.Radiobutton(frm,text=text,variable=self.player_var,value=val,
                           font=('Hiragino Sans',12),bg='#1e1208',fg='#f5d77a',
                           selectcolor='#3a2010',
                           activebackground='#1e1208').pack(side='left',padx=12)

        tk.Label(self,text="CPU難易度 / Difficulty",
                 font=('Hiragino Sans',13,'bold'),
                 bg='#1e1208',fg='#f5d77a').pack(pady=(14,4))
        self.diff_var=tk.StringVar(value=current_diff)
        descs={'入門':'ランダム手多め','初級':'駒得を考える',
               '中級':'αβ 3手読み','上級':'位置評価 4手読み','最強':'詰み探索 5手読み'}
        df=tk.Frame(self,bg='#1e1208'); df.pack(pady=(0,4))
        for name in DIFFICULTY:
            tk.Radiobutton(df,text=f"  {name}  — {descs[name]}",
                           variable=self.diff_var,value=name,
                           font=('Hiragino Sans',11),bg='#1e1208',fg='#d4c090',
                           selectcolor='#3a2010',anchor='w',
                           activebackground='#1e1208').pack(anchor='w',padx=24)

        tk.Button(self,text="対局開始 / Start",command=self._ok,
                  font=('Hiragino Sans',13,'bold'),
                  bg='#7a4010',fg='white',relief='flat',
                  padx=20,pady=6,cursor='hand2').pack(pady=14)
        self.protocol("WM_DELETE_WINDOW",self._cancel)
        self.update_idletasks()
        px=parent.winfo_x()+parent.winfo_width()//2-self.winfo_width()//2
        py=parent.winfo_y()+parent.winfo_height()//2-self.winfo_height()//2
        self.geometry(f"+{max(0,px)}+{max(0,py)}")

    def _ok(self):
        self.result={'player':self.player_var.get(),'difficulty':self.diff_var.get()}
        self.destroy()
    def _cancel(self):
        self.destroy()

# ════════════════════════════════════════════════════════════
#  棋譜参照ダイアログ
# ════════════════════════════════════════════════════════════
class KifuViewDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("棋譜参照 / Kifu Viewer")
        self.configure(bg='#1e1208')
        self.resizable(True,True)
        self.grab_set()

        files = sorted([f for f in os.listdir(KIFU_DIR) if f.endswith('.txt')], reverse=True)
        if not files:
            tk.Label(self,text="棋譜ファイルがありません。",
                     font=('Hiragino Sans',12),bg='#1e1208',fg='#f5d77a').pack(pady=20)
            tk.Button(self,text="閉じる",command=self.destroy,
                      bg='#5a3010',fg='white',relief='flat',padx=10).pack(pady=8)
            return

        top=tk.Frame(self,bg='#1e1208'); top.pack(fill='both',expand=True,padx=8,pady=8)

        # ファイルリスト
        lf=tk.Frame(top,bg='#1e1208'); lf.pack(side='left',fill='y')
        tk.Label(lf,text="棋譜一覧",font=('Hiragino Sans',11,'bold'),
                 bg='#1e1208',fg='#c8a060').pack()
        lb=tk.Listbox(lf,width=28,bg='#2a1a08',fg='#f0d890',
                      selectbackground='#7a4010',font=('Courier New',10))
        lb.pack(fill='y',expand=True)
        for f in files: lb.insert('end',f.replace('.txt',''))

        # 内容表示
        rf=tk.Frame(top,bg='#1e1208'); rf.pack(side='left',fill='both',expand=True,padx=(8,0))
        tk.Label(rf,text="内容",font=('Hiragino Sans',11,'bold'),
                 bg='#1e1208',fg='#c8a060').pack()
        txt=tk.Text(rf,width=40,bg='#2a1a08',fg='#f0d890',
                    font=('Courier New',11),wrap='word',state='disabled')
        sb=tk.Scrollbar(rf,command=txt.yview); txt.config(yscrollcommand=sb.set)
        sb.pack(side='right',fill='y'); txt.pack(fill='both',expand=True)

        def on_select(evt):
            idx=lb.curselection()
            if not idx: return
            fname=files[idx[0]]
            path=os.path.join(KIFU_DIR,fname)
            with open(path,encoding='utf-8') as f: content=f.read()
            txt.config(state='normal'); txt.delete('1.0','end')
            txt.insert('end',content); txt.config(state='disabled')

        lb.bind('<<ListboxSelect>>',on_select)
        if files: lb.selection_set(0); lb.event_generate('<<ListboxSelect>>')

        tk.Button(self,text="閉じる / Close",command=self.destroy,
                  font=('Hiragino Sans',11),bg='#5a3010',fg='white',
                  relief='flat',padx=10,pady=4).pack(pady=6)
        self.geometry("560x480")
        self.update_idletasks()
        px=parent.winfo_x()+parent.winfo_width()//2-280
        py=parent.winfo_y()+parent.winfo_height()//2-240
        self.geometry(f"+{max(0,px)}+{max(0,py)}")

# ════════════════════════════════════════════════════════════
#  将棋盤画面
# ════════════════════════════════════════════════════════════
class ShogiApp(tk.Frame):
    SQ=62; MARGIN=38; HAND_W=136; HAND_SQ=50

    def __init__(self, master, difficulty, on_back):
        super().__init__(master, bg='#1e1208')
        self.master     = master
        self.difficulty = difficulty
        self.on_back    = on_back

        self._load_sprites()
        bw=self.SQ*9+2; bh=self.SQ*9+2
        self.board_img_tk=ImageTk.PhotoImage(
            Image.open(BOARD_PATH).convert('RGBA').resize((bw,bh),Image.LANCZOS))

        cw=self.HAND_W+self.MARGIN*2+self.SQ*9+4+self.HAND_W
        ch=self.MARGIN*2+self.SQ*9+4+28
        self.canvas=tk.Canvas(self,width=cw,height=ch,
                              bg='#1e1208',highlightthickness=0)
        self.canvas.pack(padx=6,pady=6)

        sf=tk.Frame(self,bg='#1e1208'); sf.pack()
        self.last_move_var=tk.StringVar()
        tk.Label(sf,textvariable=self.last_move_var,
                 font=('Hiragino Sans',12),
                 bg='#1e1208',fg='#c8c8ff',width=36).pack()
        self.status_var=tk.StringVar()
        tk.Label(sf,textvariable=self.status_var,
                 font=('Hiragino Sans',14,'bold'),
                 bg='#1e1208',fg='#f5d77a',width=36).pack()
        self.think_var=tk.StringVar()
        tk.Label(sf,textvariable=self.think_var,
                 font=('Courier New',13),
                 bg='#1e1208',fg='#80c8ff',width=36).pack()

        bf=tk.Frame(self,bg='#1e1208'); bf.pack(pady=(4,8))
        for text,cmd in [("タイトルへ / Title",self._go_title),
                         ("投了 / Resign",      self.resign)]:
            tk.Button(bf,text=text,command=cmd,
                      font=('Hiragino Sans',12),bg='#5a3010',fg='#f5d77a',
                      relief='flat',padx=10,pady=3,cursor='hand2',
                      activebackground='#7a4820',
                      activeforeground='white').pack(side='left',padx=6)

        self.canvas.bind('<Button-1>',self.on_click)

        # ゲーム状態
        self.human_player='S'; self.cpu_player='G'
        self._thinking=False; self._dot_job=None
        self._think_start=0.0; self._dot_count=1
        self.board=None; self.hands=None; self.turn='S'
        self.selected=None; self.valid_mvs=[]; self.game_over=False
        self.last_move=None
        # 棋譜・千日手用
        self.kifu_moves=[]        # [(move_str, player)]
        self.board_history=[]     # board_hash のリスト
        self.game_start_time=None
        self.game_result=''

    def start_game(self, human_player, difficulty):
        self._thinking=False
        if self._dot_job: self.master.after_cancel(self._dot_job); self._dot_job=None
        self.human_player = human_player
        self.cpu_player   = 'G' if human_player=='S' else 'S'
        self.difficulty   = difficulty
        self.board        = initial_board()
        self.hands        = {'S':{},'G':{}}
        self.turn='S'; self.selected=None; self.valid_mvs=[]
        self.game_over=False; self.last_move=None
        self.think_var.set('')
        self.kifu_moves=[]
        self.last_move_var.set('')
        self.board_history=[board_hash(self.board,self.hands,'S')]
        self.game_start_time=datetime.datetime.now()
        self.game_result=''
        self.draw(); self._update_status()
        if self.turn==self.cpu_player:
            self.master.after(300,self._cpu_think)

    def _go_title(self):
        if not self.game_over and self.board is not None and self.kifu_moves:
            if messagebox.askyesno("棋譜を保存しますか？",
                                   "対局を中断します。棋譜を保存しますか？\nSave kifu before quitting?"):
                self._save_kifu('中断')
        self._thinking=False
        if self._dot_job: self.master.after_cancel(self._dot_job); self._dot_job=None
        self.on_back()

    def _load_sprites(self):
        raw=Image.open(SPRITE_PATH).convert('RGBA')
        self.sprites={}; self.sprites_sm={}
        full=(self.SQ-4,self.SQ-4); small=(self.HAND_SQ,self.HAND_SQ)
        def crop(r,c,size):
            x,y=c*CELL_W,r*CELL_H
            return raw.crop((x,y,x+CELL_W,y+CELL_H)).resize(size,Image.LANCZOS)
        for name,(r,c) in SPRITE_SENTE.items():
            self.sprites[('S',name)]=ImageTk.PhotoImage(crop(r,c,full))
            self.sprites_sm[('S',name)]=ImageTk.PhotoImage(crop(r,c,small))
        for name,(r,c) in SPRITE_GOTE.items():
            self.sprites[('G',name)]=ImageTk.PhotoImage(crop(r,c,full))
            self.sprites_sm[('G',name)]=ImageTk.PhotoImage(crop(r,c,small))

    @property
    def _board_origin(self):
        return self.HAND_W+self.MARGIN+2, self.MARGIN+2

    def sq_to_xy(self,row,col):
        ox,oy=self._board_origin; return ox+col*self.SQ, oy+row*self.SQ

    def xy_to_sq(self,x,y):
        ox,oy=self._board_origin
        c,r=(x-ox)//self.SQ,(y-oy)//self.SQ
        return (int(r),int(c)) if 0<=r<9 and 0<=c<9 else None

    def _update_status(self):
        if self.game_over: return
        hp="先手（下）" if self.human_player=='S' else "後手（上）"
        diff=self.difficulty
        in_check = is_in_check(self.board, self.turn)
        check_str = " 【王手！】" if in_check else ""
        if self.turn==self.human_player:
            self.status_var.set(f"あなたの番（{hp}）  {diff}{check_str}")
        else:
            cp="後手（上）" if self.cpu_player=='G' else "先手（下）"
            self.status_var.set(f"CPU思考中  （{cp}）  {diff}{check_str}")

    def _start_think_anim(self):
        self._think_start=time.time(); self._dot_count=1; self._tick_think()

    def _tick_think(self):
        if not self._thinking: return
        elapsed=time.time()-self._think_start
        mm=int(elapsed)//60; ss=int(elapsed)%60
        dots="…"*self._dot_count
        self.think_var.set(f"CPU思考中{dots}    {mm:02d}:{ss:02d}")
        self._dot_count=self._dot_count%3+1
        self._dot_job=self.master.after(500,self._tick_think)

    def _stop_think_anim(self):
        if self._dot_job: self.master.after_cancel(self._dot_job); self._dot_job=None
        self.think_var.set('')

    def _cpu_think(self):
        if self.game_over or self.turn!=self.cpu_player: return
        self._thinking=True; self._update_status(); self._start_think_anim()
        b=[row[:] for row in self.board]
        h={'S':dict(self.hands['S']),'G':dict(self.hands['G'])}
        pl=self.cpu_player; diff=self.difficulty
        def think():
            move=best_move_search(b,h,pl,diff)
            self.master.after(0,lambda:self._cpu_apply(move))
        threading.Thread(target=think,daemon=True).start()

    def _cpu_apply(self,move):
        self._thinking=False; self._stop_think_anim()
        if self.game_over or move is None: return
        player=self.cpu_player; opp=self.human_player
        board_before=[row[:] for row in self.board]
        move_str=move_to_kifu(move,player,board_before)
        if move[0]=='drop':
            _,name,tr,tc=move
            self.board[tr][tc]=(name,player)
            self.hands[player][name]-=1
            if self.hands[player][name]==0: del self.hands[player][name]
            self.last_move=(None,(tr,tc))
        else:
            _,fr,fc,tr,tc,promote=move
            piece=self.board[fr][fc][0]
            captured=self.board[tr][tc]
            if captured:
                base=DEMOTE_MAP.get(captured[0],captured[0])
                self.hands[player][base]=self.hands[player].get(base,0)+1
            new_piece=PROMOTE_MAP[piece] if promote and piece in PROMOTE_MAP else piece
            self.board[tr][tc]=(new_piece,player)
            self.board[fr][fc]=None
            self.last_move=((fr,fc),(tr,tc))
        self.kifu_moves.append(move_str)
        play_sound()
        self.last_move_var.set(f"直前の手：{move_str}")
        self.turn=opp
        self._post_move_check(player,opp)

    def _post_move_check(self, mover, next_player):
        """手を指した後の各種判定"""
        # 持将棋
        if check_nyuugyoku(self.board,self.hands,next_player):
            self._end_game('draw','持将棋（引き分け）'); return
        # 千日手
        bh=board_hash(self.board,self.hands,next_player)
        self.board_history.append(bh)
        if self.board_history.count(bh)>=4:
            self._end_game('draw','千日手（引き分け）'); return
        # 詰み判定
        legal=legal_moves_no_check(self.board,self.hands,next_player)
        if not legal:
            self._end_game(mover); return
        self.selected=None; self.valid_mvs=[]
        self.draw(); self._update_status()
        if next_player==self.cpu_player:
            self.master.after(200,self._cpu_think)

    def draw(self):
        self.canvas.delete('all')
        ox,oy=self._board_origin
        self.canvas.create_image(ox-2,oy-2,anchor='nw',image=self.board_img_tk)
        lf=('Hiragino Sans',11)
        for i,ch in enumerate('９８７６５４３２１'):
            self.canvas.create_text(ox+i*self.SQ+self.SQ//2,oy-18,
                                    text=ch,font=lf,fill='#c8a060')
        for i,ch in enumerate('一二三四五六七八九'):
            self.canvas.create_text(ox+9*self.SQ+16,oy+i*self.SQ+self.SQ//2,
                                    text=ch,font=lf,fill='#c8a060')
        if self.last_move:
            for sq in self.last_move:
                if sq and len(sq)==2:
                    x,y=self.sq_to_xy(*sq)
                    self.canvas.create_rectangle(x+1,y+1,x+self.SQ-1,y+self.SQ-1,
                                                 fill='#b8920a',outline='',stipple='gray25')
        if self.selected and isinstance(self.selected,tuple) and len(self.selected)==2:
            x,y=self.sq_to_xy(*self.selected)
            self.canvas.create_rectangle(x+1,y+1,x+self.SQ-1,y+self.SQ-1,
                                         fill='#ffe855',outline='',stipple='gray50')
        for (r,c) in self.valid_mvs:
            x,y=self.sq_to_xy(r,c)
            color='#ff5050' if self.board[r][c] else '#50d050'
            cx2,cy2=x+self.SQ//2,y+self.SQ//2
            self.canvas.create_oval(cx2-9,cy2-9,cx2+9,cy2+9,
                                    fill=color,outline='',stipple='gray50')
        # 王手ハイライト
        if self.board and not self.game_over:
            if is_in_check(self.board,self.turn):
                kp=king_pos(self.board,self.turn)
                if kp:
                    x,y=self.sq_to_xy(*kp)
                    self.canvas.create_rectangle(x+1,y+1,x+self.SQ-1,y+self.SQ-1,
                                                 outline='#ff2020',width=3)
        for r in range(9):
            for c in range(9):
                p=self.board[r][c] if self.board else None
                if p:
                    key=(p[1],p[0])
                    if key in self.sprites:
                        x,y=self.sq_to_xy(r,c)
                        self.canvas.create_image(x+2,y+2,anchor='nw',
                                                 image=self.sprites[key])
        self._draw_hand('G',ox,oy); self._draw_hand('S',ox,oy)

    def _draw_hand(self,player,ox,oy):
        hand={k:v for k,v in self.hands[player].items() if v>0}
        sq,pad=self.HAND_SQ,4
        if player=='S':
            hx=ox+9*self.SQ+self.MARGIN+6; hy_start=oy+9*self.SQ-sq
            step=-(sq+pad)
            # タイトルは最下部（先手エリアの下）
            title_y=oy+9*self.SQ+4; title="先手 持ち駒"
            self.canvas.create_text(hx,title_y,text=title,
                                    font=('Hiragino Sans',10),fill='#c8a060',anchor='nw')
        else:
            hx=6; hy_start=oy+18; step=sq+pad
            title_y=oy+4; title="後手 持ち駒"
            self.canvas.create_text(4,title_y,text=title,
                                    font=('Hiragino Sans',10),fill='#c8a060',anchor='nw')
        for i,(name,cnt) in enumerate(hand.items()):
            yy=hy_start+i*step; key=(player,name)
            if (self.selected and isinstance(self.selected,tuple) and
                    len(self.selected)==3 and self.selected[1]==player and
                    self.selected[2]==name):
                self.canvas.create_rectangle(hx-2,yy-2,hx+sq+2,yy+sq+2,
                                             outline='#ffe855',width=3)
            if key in self.sprites_sm:
                self.canvas.create_image(hx,yy,anchor='nw',image=self.sprites_sm[key])
            # 枚数を駒の右外（駒と重ならない位置）に表示
            if cnt>1:
                self.canvas.create_text(hx+sq+2,yy+sq//2,text=f"×{cnt}",
                                        font=('Hiragino Sans',10,'bold'),
                                        fill='#f5d77a',anchor='w')

    def on_click(self,event):
        if self.game_over or self.board is None: return
        if self.turn!=self.human_player: return
        x,y=event.x,event.y
        hand_hit=self._hand_hit(x,y)
        if hand_hit:
            pl,name=hand_hit
            if pl==self.turn and self.hands[pl].get(name,0)>0:
                # 王手放置チェック込みの打てるマス
                valid=[]
                for move,_,_ in legal_moves_no_check(self.board,self.hands,pl):
                    if move[0]=='drop' and move[1]==name:
                        valid.append((move[2],move[3]))
                self.selected=('hand',pl,name)
                self.valid_mvs=valid
                self.draw()
            return
        sq=self.xy_to_sq(x,y)
        if sq is None: self._deselect(); return
        r,c=sq
        if self.selected and (r,c) in self.valid_mvs:
            self._do_human_move(r,c); return
        piece=self.board[r][c]
        if piece and piece[1]==self.turn:
            # 王手放置を除いた合法手
            legal=legal_moves_no_check(self.board,self.hands,self.turn)
            valid=[(m[3],m[4]) for m,_,_ in legal
                   if m[0]=='board' and m[1]==r and m[2]==c]
            self.selected=(r,c); self.valid_mvs=valid; self.draw()
        else:
            self._deselect()

    def _deselect(self):
        self.selected=None; self.valid_mvs=[]; self.draw()

    def _hand_hit(self,x,y):
        ox,oy=self._board_origin; sq=self.HAND_SQ
        for player in ['S','G']:
            hand={k:v for k,v in self.hands[player].items() if v>0}
            if player=='S':
                hx=ox+9*self.SQ+self.MARGIN+6; hy_start=oy+9*self.SQ-sq; step=-(sq+4)
            else:
                hx=6; hy_start=oy; step=sq+4
            for i,(name,cnt) in enumerate(hand.items()):
                yy=hy_start+i*step
                if hx<=x<=hx+sq and yy<=y<=yy+sq: return (player,name)
        return None

    def _do_human_move(self,tr,tc):
        player=self.human_player; sel=self.selected
        board_before=[row[:] for row in self.board]

        # 指した手を特定
        legal=legal_moves_no_check(self.board,self.hands,player)
        chosen_move=None
        if isinstance(sel,tuple) and len(sel)==3:
            _,pl,name=sel
            for move,_,_ in legal:
                if move[0]=='drop' and move[1]==name and move[2]==tr and move[3]==tc:
                    chosen_move=move; break
        else:
            fr,fc=sel
            # 成り選択
            promo_candidates=[m for m,_,_ in legal
                if m[0]=='board' and m[1]==fr and m[2]==fc and m[3]==tr and m[4]==tc]
            if len(promo_candidates)==2:
                # 成り/不成りを選ばせる
                piece=self.board[fr][fc][0]
                ans=messagebox.askyesno("成り確認",
                    f"【{piece}】を成りますか？\nPromote {piece}?")
                chosen_move=next((m for m in promo_candidates if m[5]==ans), promo_candidates[0])
            elif promo_candidates:
                chosen_move=promo_candidates[0]

        if chosen_move is None: self._deselect(); return

        # 適用
        move_str=move_to_kifu(chosen_move,player,board_before)
        nb,nh=apply_move_inplace(self.board,self.hands,chosen_move,player)
        self.board=[row[:] for row in nb]
        self.hands={'S':dict(nh['S']),'G':dict(nh['G'])}

        # last_move
        if chosen_move[0]=='drop':
            self.last_move=(None,(tr,tc))
        else:
            self.last_move=((chosen_move[1],chosen_move[2]),(tr,tc))

        self.kifu_moves.append(move_str)
        play_sound()
        self.last_move_var.set(f"直前の手：{move_str}")
        self.turn=self.cpu_player
        self._post_move_check(player,self.cpu_player)

    def _end_game(self, winner, reason=''):
        self.game_over=True; self.selected=None; self.valid_mvs=[]
        self._stop_think_anim(); self.draw()
        if winner=='draw':
            self.status_var.set(f"引き分け — {reason}")
            self.think_var.set('')
            self.game_result=reason
            messagebox.showinfo("対局終了",f"{reason}\nDraw!")
        else:
            w="先手" if winner=='S' else "後手"
            you="あなた" if winner==self.human_player else "CPU"
            self.status_var.set(f"🏆 {w}（{you}）の勝ち！")
            self.think_var.set('')
            self.game_result=f"{w}（{you}）の勝ち"
            reason_str=reason if reason else ''
            messagebox.showinfo("対局終了 / Game Over",
                f"{w}（{you}）の勝ちです！{reason_str}\n{w} ({you}) wins!")
        # 棋譜保存確認
        if self.kifu_moves:
            if messagebox.askyesno("棋譜を保存しますか？","Save kifu?"):
                self._save_kifu(self.game_result)

    def _save_kifu(self, result):
        now=datetime.datetime.now()
        fname=now.strftime(f"%Y%m%d_%H%M%S")+"_"+self.difficulty+".txt"
        path=os.path.join(KIFU_DIR,fname)
        hp="先手" if self.human_player=='S' else "後手"
        lines=[
            f"対局日時: {now.strftime('%Y/%m/%d %H:%M:%S')}",
            f"難易度:   {self.difficulty}",
            f"あなた:   {hp}",
            f"結果:     {result}",
            f"手数:     {len(self.kifu_moves)}手",
            "─"*30,
        ]
        for i,m in enumerate(self.kifu_moves):
            lines.append(f"{i+1:3d}手目  {m}")
        with open(path,'w',encoding='utf-8') as f:
            f.write('\n'.join(lines))
        messagebox.showinfo("棋譜保存",f"保存しました:\n{fname}")

    def resign(self):
        if self.game_over or self.board is None: return
        loser="先手" if self.turn=='S' else "後手"
        if messagebox.askyesno("投了確認",f"{loser}が投了しますか？\nResign?"):
            winner='G' if self.human_player=='S' else 'S'
            self.kifu_moves.append(f"{'▲' if self.turn=='S' else '△'}投了")
            self._end_game(winner,'投了')

# ════════════════════════════════════════════════════════════
#  アプリケーションルート
# ════════════════════════════════════════════════════════════
class App:
    def __init__(self, root):
        self.root       = root
        self.difficulty = '中級'
        root.title("kensyo-shogi")
        root.configure(bg='black')
        root.resizable(False,False)
        self._show_title()

    def _show_title(self):
        self._clear()
        self.root.geometry(f"{TITLE_W}x{TITLE_H}")
        self.title_screen=TitleScreen(self.root, self._on_menu)
        self.title_screen.pack()

    def _on_menu(self, idx):
        if idx==0: self._start_game()
        elif idx==1: self._view_kifu()
        elif idx==2: self._settings()
        elif idx==3:
            if messagebox.askyesno("終了","kensyo-shogiを終了しますか？\nQuit?"): 
                self.root.quit()

    def _start_game(self):
        dlg=GameSetupDialog(self.root, self.difficulty)
        self.root.wait_window(dlg)
        if dlg.result is None: return
        self.difficulty=dlg.result['difficulty']
        self._clear()
        self.shogi=ShogiApp(self.root, self.difficulty, self._show_title)
        self.shogi.pack()
        self.root.update_idletasks()
        self.root.geometry('')   # サイズ自動調整
        self.shogi.start_game(dlg.result['player'], self.difficulty)

    def _view_kifu(self):
        KifuViewDialog(self.root)

    def _settings(self):
        global _sound_enabled
        dlg=SettingsDialog(self.root, self.difficulty, _sound_enabled)
        self.root.wait_window(dlg)
        if dlg.result:
            self.difficulty=dlg.result['difficulty']
            _sound_enabled=dlg.result['sound']

    def _clear(self):
        for w in self.root.winfo_children(): w.destroy()

if __name__=='__main__':
    root=tk.Tk()
    App(root)
    root.mainloop()
