"""Embedded VRM viewer powered by Qt WebEngine and three-vrm."""

from __future__ import annotations

import base64
import json
from pathlib import Path

from PySide6.QtCore import QObject, QUrl, Signal, Slot
from PySide6.QtWebChannel import QWebChannel
from PySide6.QtWebEngineWidgets import QWebEngineView


_VIEWER_HTML = r"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<style>
:root { color-scheme: light; font-family: Georgia, serif; }
html, body { width: 100%; height: 100%; margin: 0; overflow: hidden; background: #f5f1e8; }
#stage { width: 100%; height: 100%; position: relative; }
#hint { position: absolute; left: 22px; top: 18px; color: #52656f; font-size: 14px; z-index: 2; }
#empty { position: absolute; inset: 0; display: grid; place-items: center; color: #52656f; text-align: center; pointer-events: none; }
#empty strong { display: block; color: #1f2933; font-size: 24px; margin-bottom: 8px; }
canvas { display: block; }
</style>
<script type="importmap">
{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.170.0/examples/jsm/","@pixiv/three-vrm":"https://cdn.jsdelivr.net/npm/@pixiv/three-vrm@3.4.2/lib/three-vrm.module.js"}}
</script>
<script src="qrc:///qtwebchannel/qwebchannel.js"></script>
</head>
<body>
<div id="stage"><div id="hint">VRM avatar preview</div><div id="empty"><div><strong>VRoidのガワを読み込んでください</strong><span>.vrm ファイルを選択すると、ここに表示されます</span></div></div></div>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin } from '@pixiv/three-vrm';

const stage = document.getElementById('stage');
const empty = document.getElementById('empty');
const scene = new THREE.Scene();
scene.background = new THREE.Color('#f5f1e8');
const camera = new THREE.PerspectiveCamera(28, 1, 0.1, 100);
camera.position.set(0, 1.15, 4.8);
camera.lookAt(0, 1.15, 0);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.outputColorSpace = THREE.SRGBColorSpace;
stage.appendChild(renderer.domElement);
new QWebChannel(qt.webChannelTransport, (channel) => {
    renderer.domElement.addEventListener('click', (event) => {
        const rect = renderer.domElement.getBoundingClientRect();
        const location = locationFromPoint(
            (event.clientX - rect.left) / rect.width,
            (event.clientY - rect.top) / rect.height,
        );
        if (location) channel.objects.avatarBridge.touch(location);
    });
});
scene.add(new THREE.HemisphereLight(0xffffff, 0x8797a0, 2.2));
const key = new THREE.DirectionalLight(0xffe0c2, 2.5);
key.position.set(1, 2, 3); scene.add(key);
const loader = new GLTFLoader();
loader.register((parser) => new VRMLoaderPlugin(parser));
let current = null;

function locationFromPoint(x, y) {
    if (x > 0.34 && x < 0.66 && y > 0.04 && y < 0.12) return 'head';
    if (x > 0.38 && x < 0.62 && y > 0.10 && y < 0.17) return 'forehead';
    if (x > 0.34 && x < 0.50 && y > 0.14 && y < 0.23) return 'left_eye';
    if (x >= 0.50 && x < 0.66 && y > 0.14 && y < 0.23) return 'right_eye';
    if (x > 0.27 && x < 0.45 && y > 0.20 && y < 0.29) return 'left_cheek';
    if (x >= 0.55 && x < 0.73 && y > 0.20 && y < 0.29) return 'right_cheek';
    if (x > 0.42 && x < 0.58 && y > 0.22 && y < 0.31) return 'mouth';
    if (x > 0.40 && x < 0.60 && y > 0.28 && y < 0.36) return 'neck';
    if (x > 0.16 && x < 0.36 && y > 0.28 && y < 0.42) return 'left_shoulder';
    if (x >= 0.64 && x < 0.84 && y > 0.28 && y < 0.42) return 'right_shoulder';
    if (x > 0.28 && x < 0.72 && y > 0.32 && y < 0.53) return 'chest';
    if (x > 0.30 && x < 0.70 && y >= 0.53 && y < 0.66) return 'stomach';
    if (x < 0.16 && y > 0.40 && y < 0.78) return 'left_hand';
    if (x > 0.84 && y > 0.40 && y < 0.78) return 'right_hand';
    if (x >= 0.16 && x < 0.32 && y > 0.36 && y < 0.70) return 'left_upper_arm';
    if (x >= 0.68 && x < 0.84 && y > 0.36 && y < 0.70) return 'right_upper_arm';
    if (x > 0.30 && x < 0.48 && y > 0.64 && y < 0.79) return 'left_thigh';
    if (x >= 0.52 && x < 0.70 && y > 0.64 && y < 0.79) return 'right_thigh';
    if (x > 0.30 && x < 0.48 && y >= 0.79) return 'left_foot';
    if (x >= 0.52 && x < 0.70 && y >= 0.79) return 'right_foot';
    return null;
}

function resize() {
  const width = stage.clientWidth, height = stage.clientHeight;
  camera.aspect = width / Math.max(height, 1); camera.updateProjectionMatrix(); renderer.setSize(width, height, false);
}
window.addEventListener('resize', resize); resize();

window.loadVrmBase64 = async (encoded) => {
  const raw = atob(encoded); const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  const gltf = await loader.parseAsync(bytes.buffer, '');
  if (current) scene.remove(current.scene);
  current = gltf.userData.vrm;
  scene.add(current.scene);
  current.scene.rotation.y = 0;
  const bounds = new THREE.Box3().setFromObject(current.scene);
  const size = bounds.getSize(new THREE.Vector3());
  const targetHeight = 2.35;
  current.scene.scale.setScalar(targetHeight / Math.max(size.y, 0.01));
  const fittedBounds = new THREE.Box3().setFromObject(current.scene);
  const fittedCenter = fittedBounds.getCenter(new THREE.Vector3());
  current.scene.position.y += 1.15 - fittedCenter.y;
  empty.style.display = 'none';
  camera.lookAt(0, 1.15, 0);
  resize();
};
window.setVrmEmotion = (emotion) => {
  if (!current || !current.expressionManager) return;
  const aliases = { happy: 'happy', sad: 'sad', surprised: 'surprised', uncomfortable: 'angry', neutral: 'neutral' };
  const expression = aliases[emotion] || 'neutral';
  for (const name of ['happy', 'sad', 'angry', 'surprised']) current.expressionManager.setValue(name, name === expression ? 1 : 0);
  current.expressionManager.setValue('neutral', expression === 'neutral' ? 1 : 0);
};
function animate() { requestAnimationFrame(animate); if (current) current.update(1 / 60); renderer.render(scene, camera); }
animate();
</script>
</body>
</html>"""


class _AvatarBridge(QObject):
    def __init__(self, viewer: "VrmViewer") -> None:
        super().__init__(viewer)
        self.viewer = viewer

    @Slot(str)
    def touch(self, location: str) -> None:
        if location in {
            "head", "forehead", "left_eye", "right_eye", "left_cheek", "right_cheek", "mouth", "neck",
            "left_shoulder", "right_shoulder", "chest", "stomach", "left_upper_arm", "right_upper_arm",
            "left_hand", "right_hand", "left_thigh", "right_thigh", "left_foot", "right_foot",
        }:
            self.viewer.touched.emit(location, 0.3)


class VrmViewer(QWebEngineView):
    touched = Signal(str, float)

    def __init__(self, default_path: str | None = None) -> None:
        super().__init__()
        self.setMinimumSize(460, 560)
        self.default_path = default_path
        self.channel = QWebChannel(self.page())
        self.bridge = _AvatarBridge(self)
        self.channel.registerObject("avatarBridge", self.bridge)
        self.page().setWebChannel(self.channel)
        self.loadFinished.connect(self._load_default)
        self.setHtml(_VIEWER_HTML, QUrl("https://rippu.local/"))

    def _load_default(self, success: bool) -> None:
        if success and self.default_path and Path(self.default_path).exists():
            self.load_vrm(self.default_path)

    def load_vrm(self, path: str) -> None:
        data = base64.b64encode(Path(path).read_bytes()).decode("ascii")
        script = f"window.loadVrmBase64({json.dumps(data)});"
        self.page().runJavaScript(script)

    def set_emotion(self, emotion: str) -> None:
        self.page().runJavaScript(f"window.setVrmEmotion({json.dumps(emotion)});")

    def mousePressEvent(self, event) -> None:
        """Map the fitted avatar's screen regions to interaction locations."""
        point = event.position()
        width = max(self.width(), 1)
        height = max(self.height(), 1)
        x = point.x() / width
        y = point.y() / height
        location = None
        if 0.08 < y < 0.29 and 0.32 < x < 0.68:
            location = "face" if y > 0.14 else "head"
        elif 0.27 < y < 0.66 and 0.27 < x < 0.73:
            location = "chest"
        elif 0.22 < y < 0.70 and (0.02 < x < 0.27 or 0.73 < x < 0.98):
            location = "hand"
        if location:
            self.touched.emit(location, 0.3)
        super().mousePressEvent(event)


__all__ = ["VrmViewer"]
