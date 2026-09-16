# 06 論文・システム事例

## 必読寄りのシステム論文
1. **Nadine: An LLM-driven Intelligent Social Robot with Affective Capabilities and Human-like Memory** (2024)  
   - LLM + RAG記憶 + 感情内部状態の具体例  
   - https://arxiv.org/abs/2405.20189  
   - HTML: https://arxiv.org/html/2405.20189v1

2. **LLM-based robot personality simulation and cognitive system** (Scientific Reports, 2025)  
   - 人格・感情・短期/長期記憶・意図の分離  
   - https://www.nature.com/articles/s41598-025-01528-8

3. **Human-Inspired Context-Selective Multimodal Memory for Social Robots (SUMMER)**  
   - 社会的・感情的に重要な記憶の選択  
   - https://arxiv.org/pdf/2604.12081

4. **Ludi 0.1: An Agentic System for Socially Intelligent Robots**  
   - 実ヒューマノイド上のエージェントハーネス  
   - https://arxiv.org/html/2608.22035

5. **EgoMem / lifelong memory for embodied dialogue**（OpenReview等）  
   - リアルタイム・生涯記憶の非同期設計の参考  
   - https://openreview.net/attachment?id=nrP6ozdmHt&name=pdf

## HRI・コンパニオンの背景（概念）
- Socially Assistive Robotics / Companion robots のレビューを都度検索して追加すること
- 「依存・境界線・セーフワード」はプロダクト倫理として別メモを推奨（実装前にルール化）

## このプロジェクトへの写像
| 論文の要素 | 瞳プロトタイプでの対応 |
|---|---|
| Episodic RAG | ユーザー別SQLite + 要約チャンク |
| Affective state | trust/affection/... の数値 |
| Personality prompt | 瞳のsystem prompt |
| Tools / ReAct | memory_search, update_state |
| Embodiment | 当面はGUIイベントボタン |

