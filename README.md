# kensyo-shogi 🎴

## Screenshot
![title](<img width="632" height="663" alt="image" src="https://github.com/user-attachments/assets/50d80ceb-6440-4bd1-a4d9-fc0336ad8130" />
)



**Python + tkinter で動く、本格将棋ゲームです。**

![Version](https://img.shields.io/badge/Version-1.0.1-brightgreen)
![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![License](https://img.shields.io/badge/License-MIT-green)
![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)

---

## 特徴

- **タイトル画面** — 起動時にメニューを表示。←→キーまたはマウスで選択
- **CPU対局** — 先手／後手を選んでCPUと対戦
- **難易度5段階** — 入門・初級・中級・上級・最強（αβ法＋詰み探索）
- **完全な将棋ルール実装**
  - 王手放置の禁止（合法手から完全除外）
  - 詰み判定（合法手0で自動終了）
  - 千日手検出（同一局面4回で引き分け）
  - 持将棋判定（両王入玉＋双方24点以上）
  - 二歩・行き場なし禁止
- **棋譜記録・保存** — 対局終了・投了・中断時に保存確認。`kifu/` フォルダへKIF風形式で保存
- **棋譜参照** — 過去の対局棋譜をタイトル画面から一覧閲覧
- **設定** — 難易度・効果音のON/OFFを変更可能
- **CPU思考アニメーション** — `CPU思考中…` ＋ 経過時間をリアルタイム表示
- **直前の手表示** — 盤面下に `▲７六歩` 形式で直前の手を常時表示
- **駒音** — 駒を置くたびに木の駒音が鳴る

---

## 動作環境

- Python 3.8 以上
- Windows / macOS / Linux

---

## インストールと起動

```bash
# 1. リポジトリをクローン
git clone https://github.com/kensyo-lab/kensyo-shogi.git
cd kensyo-shogi

# 2. 依存ライブラリをインストール
pip install -r requirements.txt

# 3. 起動
python shogi.py
```

> **tkinter** は Python 標準ライブラリに含まれます。  
> Linux で `tkinter` が見つからない場合: `sudo apt install python3-tk`

### 効果音の再生バックエンド（優先順）

| 優先度 | ライブラリ | インストール |
|:---:|---|---|
| 1 | `pygame` | `pip install pygame`（推奨） |
| 2 | `playsound` | `pip install playsound` |
| 3 | OS付属コマンド | macOS: `afplay` / Linux: `mpg123` or `aplay` |

いずれも使えない場合は無音で動作します。

---

## ファイル構成

```
kensyo-shogi/
├── shogi.py                        # メインスクリプト（全機能1ファイル完結）
├── requirements.txt                # 依存ライブラリ
├── assets/
│   ├── images/
│   │   ├── kensyo-shogi-title.png  # タイトル画面
│   │   ├── pieces.png              # 駒スプライトシート
│   │   └── board.png               # 将棋盤
│   └── sounds/
│       └── koma.mp3                # 駒音
├── kifu/                           # 棋譜保存先（自動生成）
├── README.md
└── LICENSE
```

---

## 操作方法

| 操作 | 内容 |
|---|---|
| 駒をクリック | 選択（緑ドット＝移動可能マス、赤ドット＝取れる駒） |
| 移動先をクリック | 移動 |
| 持ち駒をクリック | 選択して打てるマスを表示 |
| ←→キー / マウス | タイトルメニューの選択 |
| Enter | タイトルメニューの決定 |
| 「タイトルへ」 | タイトル画面に戻る（棋譜保存確認あり） |
| 「投了」 | 現在の手番が投了 |

---

## 難易度について

| 難易度 | 探索深さ | 特徴 |
|:---:|:---:|---|
| 入門 | 1手 | ランダム要素多め。将棋を覚えたての方向け |
| 初級 | 2手 | 駒の損得のみ評価 |
| 中級 | 3手 | αβ枝刈り探索 |
| 上級 | 4手 | 位置評価テーブル追加 |
| 最強 | 5手 | 詰み探索延長あり。思考時間が長くなる場合があります |

---

## 使用素材・クレジット

### 駒・将棋盤画像
- **提供元**: [Sunfish Shogi Images](https://sunfish-shogi.github.io/shogi-images/)

### 効果音
- **素材名**: 「【将棋】駒音1」
- **制作者**: れがしろ さん
- **提供元**: [ニコニコモンズ nc316163](https://commons.nicovideo.jp/works/agreement/nc316163)

---

## ライセンス

本ソフトウェアは **MIT License** のもとで公開されています。詳細は [LICENSE](LICENSE) を参照してください。

---

## 作者

**kensyo-lab** （腱鞘炎）  
© 腱鞘炎 2026

- GitHub: [kensyo-lab](https://github.com/kensyo-lab)

---

## 更新履歴

### v1.0.1 (2026-04-27)
- タイトル画面を追加
- 王手・詰み判定を完全実装
- 千日手・持将棋判定を追加
- 棋譜の記録・保存・参照機能を追加
- 設定画面（難易度・効果音）を追加
- CPU思考中アニメーション・経過時間表示を追加
- 直前の手を盤面下に表示
- 持ち駒の枚数表示位置を改善
- 後手持ち駒エリアの表示崩れを修正

### v1.0.0 (2026-04-27)
- 初回リリース
- 基本的な将棋ルール・CPU対戦機能
