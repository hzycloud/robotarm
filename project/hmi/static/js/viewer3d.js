// 文件作用：Edge-Sort 上位机 3D 机械臂视图。
//
// 主要内容：
//   1. 用 three.js + URDFLoader 加载 /urdf/so101_new_calib.urdf（官方 SO-101 模型）。
//   2. 提供 window.updateArmJoints(joints, gripper)，按 robot_state.json 的 6 值约定
//      依次驱动 shoulder_pan/shoulder_lift/elbow_flex/wrist_flex/wrist_roll/gripper。
//   3. 鼠标拖拽旋转、滚轮缩放（OrbitControls），模型加载失败时显示提示。
import * as THREE from "three";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { URDFLoader } from "../vendor/urdf-loader.js";

const JOINT_ORDER = ["shoulder_pan", "shoulder_lift", "elbow_flex", "wrist_flex", "wrist_roll", "gripper"];

const container = document.getElementById("viewer3d");
let robot = null;
let statusEl = null;

function showStatus(text) {
  if (!statusEl) {
    statusEl = document.createElement("div");
    statusEl.style.cssText =
      "position:absolute;inset:0;display:flex;align-items:center;justify-content:center;color:#9aa4b0;pointer-events:none;";
    container.appendChild(statusEl);
  }
  statusEl.textContent = text;
}

function init() {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x12151a);

  const camera = new THREE.PerspectiveCamera(45, container.clientWidth / container.clientHeight, 0.01, 10);
  camera.position.set(0.6, 0.5, 0.8);

  const renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(container.clientWidth, container.clientHeight);
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.target.set(0, 0.15, 0);
  controls.update();

  scene.add(new THREE.AmbientLight(0xffffff, 0.7));
  const dir = new THREE.DirectionalLight(0xffffff, 1.1);
  dir.position.set(0.5, 1, 0.5);
  scene.add(dir);

  const loader = new URDFLoader();
  loader.load(
    "/urdf/so101_new_calib.urdf",
    (model) => {
      robot = model;
      scene.add(robot);
      if (statusEl) statusEl.remove();
      showStatus("");
    },
    undefined,
    (err) => {
      showStatus("3D 模型加载失败：" + (err && err.message ? err.message : "未知错误"));
    },
  );

  function resize() {
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }

  window.addEventListener("resize", resize);
  const observer = new ResizeObserver(resize);
  observer.observe(container);

  function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  }
  animate();

  showStatus("3D 模型加载中…");
}

window.updateArmJoints = function (joints, gripper) {
  if (!robot || !Array.isArray(joints)) return;
  JOINT_ORDER.forEach((name, i) => {
    const joint = robot.joints[name];
    const value = joints[i];
    if (joint && typeof value === "number") {
      try {
        joint.setAngle(value);
      } catch {
        // 超出关节限位时 URDFJoint 可能抛错，忽略并保持当前姿态
      }
    }
  });
};

init();
