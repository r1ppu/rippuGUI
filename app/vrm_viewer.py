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
#hit-status { position: absolute; right: 18px; top: 16px; padding: 8px 11px; border: 1px solid #52656f; border-radius: 6px; background: rgba(255,255,255,.88); color: #1f2933; font-size: 13px; z-index: 3; }
#hit-area { position: absolute; display: none; border: 3px solid #d95d50; border-radius: 10px; background: rgba(217,93,80,.25); box-shadow: 0 0 0 2px rgba(255,255,255,.7), 0 0 18px rgba(217,93,80,.6); pointer-events: none; z-index: 2; }
#hit-marker { position: absolute; display: none; width: 16px; height: 16px; margin: -8px 0 0 -8px; border: 3px solid #fff; border-radius: 50%; background: #d95d50; box-shadow: 0 0 0 2px #d95d50, 0 0 14px rgba(217,93,80,.8); pointer-events: none; z-index: 4; }
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
<div id="stage"><div id="hint">VRM avatar preview</div><div id="hit-status">判定: まだ選択されていません</div><div id="hit-area"></div><div id="hit-marker"></div><div id="empty"><div><strong>VRoidのガワを読み込んでください</strong><span>.vrm ファイルを選択すると、ここに表示されます</span></div></div></div>
<script type="module">
import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { VRMLoaderPlugin } from '@pixiv/three-vrm';

const stage = document.getElementById('stage');
const empty = document.getElementById('empty');
const hitStatus = document.getElementById('hit-status');
const hitArea = document.getElementById('hit-area');
const hitMarker = document.getElementById('hit-marker');
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
        const x = (event.clientX - rect.left) / rect.width;
        const y = (event.clientY - rect.top) / rect.height;
        const location = locationFromPoint(x, y);
        showHitResult(location, x, y);
        if (location) channel.objects.avatarBridge.touch(location);
    });
});
scene.add(new THREE.HemisphereLight(0xffffff, 0x8797a0, 2.2));
const key = new THREE.DirectionalLight(0xffe0c2, 2.5);
key.position.set(1, 2, 3); scene.add(key);
const loader = new GLTFLoader();
loader.register((parser) => new VRMLoaderPlugin(parser));
let current = null;
const boneLocations = new Map();

const locationLabels = {
    head: '頭', forehead: '額', left_eye: '左目', right_eye: '右目',
    left_cheek: '左頬', right_cheek: '右頬', mouth: '口', neck: '首',
    left_shoulder: '左肩', right_shoulder: '右肩', chest: '胸', stomach: '腹',
    left_upper_arm: '左上腕', right_upper_arm: '右上腕', left_hand: '左手',
    right_hand: '右手', left_thigh: '左太もも', right_thigh: '右太もも',
    left_foot: '左足', right_foot: '右足',
};
const locationColors = {
    head: '#e76f51', forehead: '#f4a261', left_eye: '#e9c46a', right_eye: '#e9c46a',
    left_cheek: '#f4a261', right_cheek: '#f4a261', mouth: '#e76f51', neck: '#2a9d8f',
    left_shoulder: '#457b9d', right_shoulder: '#457b9d', chest: '#2a9d8f', stomach: '#52b788',
    left_upper_arm: '#4d908e', right_upper_arm: '#4d908e', left_hand: '#277da1', right_hand: '#277da1',
    left_thigh: '#90be6d', right_thigh: '#90be6d', left_foot: '#43aa8b', right_foot: '#43aa8b',
};

function showHitResult(location, x, y) {
    hitMarker.style.display = 'block';
    hitMarker.style.left = `${x * 100}%`;
    hitMarker.style.top = `${y * 100}%`;
    if (!location) {
        hitArea.style.display = 'none';
        hitStatus.textContent = '判定: なし';
        hitStatus.style.borderColor = '#52656f';
        hitStatus.style.color = '#52656f';
        return;
    }
    const bounds = hitBounds(x, y);
    hitArea.style.display = 'block';
    hitArea.style.left = `${bounds.left * 100}%`;
    hitArea.style.top = `${bounds.top * 100}%`;
    hitArea.style.width = `${(bounds.right - bounds.left) * 100}%`;
    hitArea.style.height = `${(bounds.bottom - bounds.top) * 100}%`;
    const color = locationColors[location] || '#d95d50';
    hitArea.style.borderColor = color;
    hitArea.style.backgroundColor = `${color}55`;
    hitArea.style.boxShadow = `0 0 0 2px rgba(255,255,255,.7), 0 0 18px ${color}99`;
    hitMarker.style.backgroundColor = color;
    hitMarker.style.boxShadow = `0 0 0 2px ${color}, 0 0 14px ${color}cc`;
    hitStatus.textContent = `判定: ${locationLabels[location] || location}`;
    hitStatus.style.borderColor = color;
    hitStatus.style.color = color;
}

function hitBounds(x, y) {
    const size = 0.045;
    return {
        left: Math.max(0, x - size), top: Math.max(0, y - size),
        right: Math.min(1, x + size), bottom: Math.min(1, y + size),
    };
}

function registerBoneLocation(humanBone, location) {
    try {
        const node = current?.humanoid?.getNormalizedBoneNode(humanBone);
        if (node) {
            boneLocations.set(node.uuid, location);
            boneLocations.set(`name:${node.name}`, location);
        }
    } catch (_error) {
    }
}

function buildBoneLocationMap() {
    boneLocations.clear();
    [
        ['head', 'head'], ['neck', 'neck'], ['chest', 'chest'], ['spine', 'chest'],
        ['hips', 'stomach'], ['leftShoulder', 'left_shoulder'], ['rightShoulder', 'right_shoulder'],
        ['leftUpperArm', 'left_upper_arm'], ['rightUpperArm', 'right_upper_arm'],
        ['leftHand', 'left_hand'], ['rightHand', 'right_hand'],
        ['leftUpperLeg', 'left_thigh'], ['rightUpperLeg', 'right_thigh'],
        ['leftFoot', 'left_foot'], ['rightFoot', 'right_foot'],
    ].forEach(([bone, location]) => registerBoneLocation(bone, location));
    current?.scene?.traverse((object) => {
        if (!object.isSkinnedMesh) return;
        object.skeleton.bones.forEach((bone) => {
            const location = locationForBoneName(bone.name);
            if (location) boneLocations.set(`name:${bone.name}`, location);
        });
    });
}

function locationForBoneName(name = '') {
    const token = name.toLowerCase();
    const compact = token.replace(/[^a-z0-9]/g, '');
    const side = /(^|[._-])l($|[._-])/.test(token) || compact.endsWith('l')
        ? 'left'
        : /(^|[._-])r($|[._-])/.test(token) || compact.endsWith('r') ? 'right' : '';
    if (compact.includes('head')) return 'head';
    if (compact.includes('neck')) return 'neck';
    if (compact.includes('chest') || compact.includes('spine')) return 'chest';
    if (compact.includes('hip') || compact.includes('pelvis')) return 'stomach';
    if (side && compact.includes('shoulder')) return `${side}_shoulder`;
    if (side && (compact.includes('upperarm') || compact.includes('forearm') || compact === 'arm')) return `${side}_upper_arm`;
    if (side && (compact.includes('hand') || compact.includes('palm') || compact.includes('finger') || compact.includes('thumb'))) return `${side}_hand`;
    if (side && (compact.includes('upperleg') || compact.includes('thigh') || compact.includes('shin'))) return `${side}_thigh`;
    if (side && (compact.includes('foot') || compact.includes('toe') || compact.includes('heel'))) return `${side}_foot`;
    return null;
}

function namedMeshLocation(object) {
    const name = `${object.name || ''} ${object.material?.name || ''}`.toLowerCase();
    const namedParts = [
        ['left_eye', /left.?eye|eye.?l|l.?eye/], ['right_eye', /right.?eye|eye.?r|r.?eye/],
        ['mouth', /mouth|lip/], ['left_cheek', /left.?cheek|cheek.?l/],
        ['right_cheek', /right.?cheek|cheek.?r/],
    ];
    return namedParts.find(([, pattern]) => pattern.test(name))?.[0] || null;
}

function boneLocationFromHit(hit) {
    const mesh = hit.object;
    if (!mesh.isSkinnedMesh || !mesh.geometry.index || !mesh.geometry.attributes.skinIndex || !mesh.geometry.attributes.skinWeight || !Number.isInteger(hit.faceIndex)) {
        return locationForBoneName(mesh.name) || 'head';
    }
    const indices = mesh.geometry.index;
    const start = hit.faceIndex * 3;
    const weightsByBone = new Map();
    for (let offset = 0; offset < 3; offset += 1) {
        const vertexIndex = indices.getX(start + offset);
        const skinIndices = mesh.geometry.attributes.skinIndex;
        const skinWeights = mesh.geometry.attributes.skinWeight;
        for (let influence = 0; influence < 4; influence += 1) {
            const boneIndex = skinIndices.getComponent(vertexIndex, influence);
            const weight = skinWeights.getComponent(vertexIndex, influence);
            weightsByBone.set(boneIndex, (weightsByBone.get(boneIndex) || 0) + weight);
        }
    }
    const bestBone = [...weightsByBone.entries()].sort((a, b) => b[1] - a[1])[0];
    if (!bestBone) return locationForBoneName(mesh.name) || 'head';
    const bone = mesh.skeleton.bones[bestBone[0]];
    return boneLocations.get(bone?.uuid) || boneLocations.get(`name:${bone?.name}`) || locationForBoneName(bone?.name) || 'head';
}

function locationFromPoint(x, y) {
    if (!current) return null;
    const pointer = new THREE.Vector2(x * 2 - 1, -(y * 2 - 1));
    const raycaster = new THREE.Raycaster();
    raycaster.setFromCamera(pointer, camera);
    current.scene.updateMatrixWorld(true);
    const hits = raycaster.intersectObject(current.scene, true);
    if (!hits.length) return null;

    const hit = hits[0];
    return namedMeshLocation(hit.object) || boneLocationFromHit(hit) || 'head';
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
    buildBoneLocationMap();
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

__all__ = ["VrmViewer"]
