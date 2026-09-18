"""Launch the interactive avatar GUI."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from PySide6.QtCore import QObject, QPointF, QRunnable, Qt, QThreadPool, Signal, Slot
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import QApplication, QComboBox, QFileDialog, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QPushButton, QPlainTextEdit, QSlider, QVBoxLayout, QWidget

from .domain import ActionCommand, InteractionEngine, InteractionEvent, Reaction, proposal_to_reaction
from engine import ChatEngine, ChatError
from .llm import OllamaClient
from .vrm_viewer import VrmViewer


class AvatarWidget(QWidget):
    touched = Signal(str, float)

    def __init__(self) -> None:
        super().__init__()
        self.setMinimumSize(460, 560)
        self.emotion = "neutral"
        self.active_location = ""
        self.setMouseTracking(True)

    def mousePressEvent(self, event) -> None:
        point = event.position()
        location = self.location_at(point.x(), point.y())
        if location:
            self.active_location = location
            self.touched.emit(location, 0.3)
            self.update()

    def location_at(self, x: float, y: float) -> str | None:
        if 175 < x < 285 and 85 < y < 205:
            return "head"
        if 190 < x < 270 and 185 < y < 255:
            return "face"
        if 135 < x < 325 and 255 < y < 430:
            return "chest"
        if 75 < x < 145 and 260 < y < 450:
            return "hand"
        if 315 < x < 385 and 260 < y < 450:
            return "hand"
        return None

    def set_emotion(self, emotion: str) -> None:
        self.emotion = emotion
        self.update()

    def paintEvent(self, _event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor("#f5f1e8"))
        center = self.width() / 2
        painter.setPen(QPen(QColor("#1f2933"), 3))
        painter.setBrush(QColor("#d9e9e5"))
        painter.drawEllipse(QPointF(center, 145), 72, 82)
        painter.setBrush(QColor("#bcd8d2"))
        painter.drawRoundedRect(center - 95, 235, 190, 205, 45, 45)
        painter.drawLine(center - 95, 275, center - 165, 390)
        painter.drawLine(center + 95, 275, center + 165, 390)
        painter.setBrush(QColor("#1f2933"))
        painter.drawEllipse(QPointF(center - 27, 130), 7, 11)
        painter.drawEllipse(QPointF(center + 27, 130), 7, 11)
        painter.setPen(QPen(QColor("#bf5b4b"), 4))
        if self.emotion == "sad":
            painter.drawArc(center - 25, 160, 50, 25, 0, 180 * 16)
        elif self.emotion in {"happy", "surprised"}:
            painter.drawArc(center - 25, 150, 50, 35, 180 * 16, 180 * 16)
        else:
            painter.drawLine(center - 20, 172, center + 20, 172)
        painter.setPen(QPen(QColor("#52656f"), 1))
        painter.drawText(20, 30, "触れたい場所をクリック")
        painter.drawText(20, self.height() - 20, f"emotion: {self.emotion} / location: {self.active_location or '-'}")


class WorkerSignals(QObject):
    result = Signal(object)
    error = Signal(str)


class LlmWorker(QRunnable):
    def __init__(self, client: OllamaClient, state, event: InteractionEvent) -> None:
        super().__init__()
        self.client, self.state, self.event = client, state, event
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.result.emit(self.client.propose(self.state, self.event))
        except Exception as exc:
            self.signals.error.emit(str(exc))


class ChatWorker(QRunnable):
    def __init__(self, messages: list[dict[str, str]]) -> None:
        super().__init__()
        self.messages = messages
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            engine = ChatEngine.from_project()
            self.signals.result.emit(engine.chat(self.messages))
        except ChatError as exc:
            self.signals.error.emit(str(exc))
        except Exception:
            self.signals.error.emit("会話中に予期しない障害が起きました。")


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Rippu Avatar Lab")
        self.engine = InteractionEngine()
        self.ollama_enabled = os.getenv("OLLAMA_ENABLED", "0") == "1"
        self.client = OllamaClient(os.getenv("OLLAMA_HOST", "http://localhost:11434"), os.getenv("OLLAMA_MODEL", "gemma3"))
        self.thread_pool = QThreadPool.globalInstance()
        default_vrm = Path(__file__).resolve().parent.parent / "assets" / "Seed-san.vrm"
        self.avatar = VrmViewer(str(default_vrm) if default_vrm.exists() else None)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.chat_messages: list[dict[str, str]] = []
        self.chat_log = QPlainTextEdit()
        self.chat_log.setReadOnly(True)
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("めあに話しかける")
        self.chat_input.returnPressed.connect(self.send_chat)
        self.chat_send = QPushButton("送信")
        self.chat_send.clicked.connect(self.send_chat)
        self.status = QLabel("ルールベース反応: 利用可能")
        self.expression = QComboBox()
        self.expression.addItems(["happy", "sad", "surprised", "angry", "neutral"])
        self.intensity = QSlider(Qt.Orientation.Horizontal)
        self.intensity.setRange(10, 100)
        self.intensity.setValue(30)
        send_expression = QPushButton("表情を送る")
        send_expression.clicked.connect(self.send_expression)
        reset = QPushButton("状態をリセット")
        reset.clicked.connect(self.reset)
        load_vrm = QPushButton("VRMを読み込む")
        load_vrm.clicked.connect(self.open_vrm)
        touch_controls = QGridLayout()
        touch_locations = (
            "head", "forehead", "left_eye", "right_eye", "left_cheek", "right_cheek", "mouth", "neck",
            "left_shoulder", "right_shoulder", "chest", "stomach", "left_upper_arm", "right_upper_arm",
            "left_hand", "right_hand", "left_thigh", "right_thigh", "left_foot", "right_foot",
        )
        for index, location in enumerate(touch_locations):
            button = QPushButton(location)
            button.clicked.connect(lambda _checked=False, value=location: self.send_touch(value, 0.3))
            touch_controls.addWidget(button, index // 4, index % 4)
        layout = QVBoxLayout()
        layout.addWidget(self.avatar)
        layout.addWidget(load_vrm)
        layout.addWidget(QLabel("タッチ部位の検証"))
        layout.addLayout(touch_controls)
        layout.addWidget(QLabel("カメラ表情の代替入力"))
        layout.addWidget(self.expression)
        layout.addWidget(send_expression)
        layout.addWidget(QLabel("タッチ強度"))
        layout.addWidget(self.intensity)
        layout.addWidget(reset)
        layout.addWidget(self.status)
        layout.addWidget(QLabel("めあとの会話"))
        layout.addWidget(self.chat_log)
        chat_controls = QHBoxLayout()
        chat_controls.addWidget(self.chat_input)
        chat_controls.addWidget(self.chat_send)
        layout.addLayout(chat_controls)
        layout.addWidget(QLabel("イベントログ"))
        layout.addWidget(self.log)
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)
        self.avatar.touched.connect(self.send_touch)

    def send_touch(self, location: str, _intensity: float) -> None:
        event = InteractionEvent("touch", "gui", "touch", location, self.intensity.value() / 100)
        self.handle_event(event)

    def send_expression(self) -> None:
        value = self.expression.currentText()
        self.handle_event(InteractionEvent("expression", "gui", value, confidence=1.0))

    def open_vrm(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "VRMアバターを選択", "", "VRM files (*.vrm)")
        if path:
            self.avatar.load_vrm(path)
            self.status.setText(f"VRMを読み込みました: {os.path.basename(path)}")

    def handle_event(self, event: InteractionEvent) -> None:
        reaction = self.engine.handle(event)
        self.apply_reaction(event, reaction, "ルール")
        if event.type == "touch" and event.location:
            self.chat_messages.append({
                "role": "user",
                "content": (
                    f"[対話コンテキスト] ユーザーがアバターの{event.location}に触れました。"
                    f"強さは{event.intensity:.0%}です。これを踏まえて次の会話に自然に反映してください。"
                ),
            })
        if not self.ollama_enabled:
            return
        worker = LlmWorker(self.client, self.engine.state, event)
        worker.signals.result.connect(lambda proposal: self.apply_reaction(event, proposal_to_reaction(proposal), "Ollama"))
        worker.signals.error.connect(lambda error: self.status.setText(f"Ollama: フォールバック中 ({error})"))
        self.status.setText("Ollama: 応答待ち。GUIは操作可能")
        self.thread_pool.start(worker)

    def send_chat(self) -> None:
        message = self.chat_input.text().strip()
        if not message or not self.chat_send.isEnabled():
            return
        self.chat_input.clear()
        self.chat_messages.append({"role": "user", "content": message})
        self.chat_log.appendPlainText(f"あなた: {message}")
        self.chat_log.appendPlainText("めあ: 返事を考えています…")
        self.chat_send.setEnabled(False)
        self.status.setText("会話AI: 応答待ち。GUIは操作可能")
        worker = ChatWorker(list(self.chat_messages))
        worker.signals.result.connect(self._finish_chat)
        worker.signals.error.connect(self._fail_chat)
        self.thread_pool.start(worker)

    def _finish_chat(self, result) -> None:
        self.chat_messages.append({"role": "assistant", "content": result.content})
        self.avatar.set_emotion(result.emotion)
        text = self.chat_log.toPlainText()
        marker = "めあ: 返事を考えています…"
        if text.endswith(marker):
            text = text[: -len(marker)].rstrip()
        self.chat_log.setPlainText(f"{text}\nめあ: {result.content}")
        self.chat_log.verticalScrollBar().setValue(self.chat_log.verticalScrollBar().maximum())
        self.chat_send.setEnabled(True)
        self.status.setText("会話AI: 応答しました")

    def _fail_chat(self, error: str) -> None:
        text = self.chat_log.toPlainText()
        marker = "めあ: 返事を考えています…"
        if text.endswith(marker):
            text = text[: -len(marker)].rstrip()
        self.chat_log.setPlainText(f"{text}\nめあ: エラー: {error}")
        self.chat_log.verticalScrollBar().setValue(self.chat_log.verticalScrollBar().maximum())
        self.chat_send.setEnabled(True)
        self.status.setText(f"会話AI: {error}")

    def apply_reaction(self, event: InteractionEvent, reaction: Reaction, source: str) -> None:
        self.avatar.set_emotion(reaction.emotion)
        self.log.appendPlainText(f"[{source}] {event.type}/{event.location or event.value} -> {reaction.emotion}: {reaction.message}")
        self.status.setText(f"{source}: {reaction.message}")

    def reset(self) -> None:
        self.engine = InteractionEngine()
        self.avatar.set_emotion("neutral")
        self.chat_messages.clear()
        self.chat_log.clear()
        self.log.clear()
        self.status.setText("状態をリセットしました")


def main() -> int:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(600, 900)
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
