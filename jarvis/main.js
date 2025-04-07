import * as THREE from 'three';
import './style.css';
import {EffectComposer} from 'three/examples/jsm/postprocessing/EffectComposer.js';
import {RenderPass} from 'three/examples/jsm/postprocessing/RenderPass.js';
import {UnrealBloomPass} from 'three/examples/jsm/postprocessing/UnrealBloomPass.js';
import { io } from 'socket.io-client';
import { isFinished, setFinished } from './shared_var.js';

// Socket setup
export const socket = io('http://localhost:8000');

socket.on('prompt_response', (data) => {
    if (data['role'] === 'user') {
        setFinished(false)
        switchState(states.THINKING);
    }
    if (data['role'] === 'assistant') {
        setFinished(false);
        switchState(states.ANSWERING);
    }
});

// Scene setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
const renderer = new THREE.WebGLRenderer({
    canvas: document.querySelector('#bg'),
});
renderer.setPixelRatio(window.devicePixelRatio);
renderer.setSize(window.innerWidth, window.innerHeight);
camera.position.setZ(30);

// Background gradient
const canvas = document.createElement('canvas');
canvas.width = window.innerWidth;
canvas.height = window.innerHeight;
const context = canvas.getContext('2d');
const gradient = context.createRadialGradient(
    window.innerWidth / 2, window.innerHeight / 2, 0,
    window.innerWidth / 2, window.innerHeight / 2, Math.max(window.innerWidth, window.innerHeight)
);
gradient.addColorStop(0, '#000000');
gradient.addColorStop(0.5, 'rgb(0,69,115)');
gradient.addColorStop(1, '#003278');
context.fillStyle = gradient;
context.fillRect(0, 0, window.innerWidth, window.innerHeight);

const texture = new THREE.CanvasTexture(canvas);
const planeGeometry = new THREE.PlaneGeometry(window.innerWidth, window.innerHeight);
const planeMaterial = new THREE.MeshBasicMaterial({ map: texture });
const plane = new THREE.Mesh(planeGeometry, planeMaterial);
scene.background = texture;
plane.position.z = -50;
scene.add(plane);

// Torus rings
const torusGeometry = new THREE.TorusGeometry(12.36, 0.7, 16, 100);
const torusGeometry2 = new THREE.TorusGeometry(10, 1.5, 32, 100);
const torusGeometry3 = new THREE.TorusGeometry(8, 0.6, 16, 100);

const torusMaterial = new THREE.MeshStandardMaterial({ color: 0x00b3ff, emissive: 0x00b3ff, emissiveIntensity: 0.7, roughness: 0.5, metalness: 1.2, opacity: 0.5, transparent: true, wireframe: true });
const torusMaterial2 = new THREE.MeshStandardMaterial({ color: 0x00b3ff, emissive: 0x00b3ff, emissiveIntensity: 0.2, roughness: 0.5, metalness: 1.2, opacity: 0.5, transparent: true, wireframe: true });
const torusMaterial3 = new THREE.MeshStandardMaterial({ color: 0x00b3ff, emissive: 0x00b3ff, emissiveIntensity: 1, roughness: 0.5, metalness: 1.2, opacity: 0.05, transparent: true, wireframe: true });

const torus = new THREE.Mesh(torusGeometry, torusMaterial);
const torus2 = new THREE.Mesh(torusGeometry2, torusMaterial2);
const torus3 = new THREE.Mesh(torusGeometry3, torusMaterial3);
scene.add(torus, torus2, torus3);

// Lighting
const pointLight1 = new THREE.PointLight(0xffffff, 1, 100);
pointLight1.position.set(10, 10, 10);
const pointLight2 = new THREE.PointLight(0x0000ff, 1, 100);
pointLight2.position.set(-10, -10, -10);
const ambientLight = new THREE.AmbientLight(0xffffff, 1);
scene.add(pointLight1, pointLight2, ambientLight);

// Center sphere
const sphereGeometry = new THREE.SphereGeometry(5, 32, 20);
const sphereMaterial = new THREE.MeshStandardMaterial({ color: 0x00b3ff, emissive: 0x00b3ff, emissiveIntensity: 0.7, roughness: 0.5, metalness: 1.2, opacity: 0.5, transparent: true, wireframe: true });
const sphere = new THREE.Mesh(sphereGeometry, sphereMaterial);
scene.add(sphere);

// Background lines
const lines = [];
const lineMaterial = new THREE.LineBasicMaterial({ color: 0x00b3ff });

for (let i = 0; i < 100; i++) {
    const lineGeometry = new THREE.BufferGeometry();
    const points = [];
    const size = Math.random() * 5 + 1;
    points.push(new THREE.Vector3(0, 0, 0));
    points.push(new THREE.Vector3(0, 0, -size));
    lineGeometry.setFromPoints(points);

    const line = new THREE.Line(lineGeometry, lineMaterial);
    line.position.set(
        (Math.random() - 0.5) * 50,
        (Math.random() - 0.5) * 50,
        (Math.random() - 0.5) * 50
    );
    lines.push(line);
    scene.add(line);
}

// Post-processing
const composer = new EffectComposer(renderer);
composer.addPass(new RenderPass(scene, camera));
const bloomPass = new UnrealBloomPass(
    new THREE.Vector2(window.innerWidth, window.innerHeight),
    1.5, 0.4, 0.85
);
composer.addPass(bloomPass);

// States
const states = {
    THINKING: 'thinking',
    WAITING: 'waiting',
    ANSWERING: 'answering'
};

let currentState = states.WAITING;
let isThinkingAnimated = false;

function animateThinking() {
    const text = document.getElementById('jarvis');
    if (!isThinkingAnimated) {
        text.style.animation = 'pulse 2s infinite';
        isThinkingAnimated = true;
    }
}

function animateWaiting() {
    const text = document.getElementById('jarvis');
    if (isThinkingAnimated) {
        text.style.animation = 'none';
        isThinkingAnimated = false;
    }
    text.style.textShadow = '0 0 10px #00b3ff, 0 0 20px #00b3ff, 0 0 30px';
}

function animateAnswering() {
    const text = document.getElementById('jarvis');
    if (isThinkingAnimated) {
        text.style.animation = 'none';
        isThinkingAnimated = false;
    }
    text.style.transition = 'text-shadow 0.5s ease-in-out';
    text.style.textShadow = '0 0 10px #00b3ff, 0 0 20px #00b3ff, 0 0 30px #00b3ff, 0 0 40px #00b3ff, 0 0 50px #00b3ff, 0 0 60px #00b3ff, 0 0 70px #00b3ff, 0 0 80px #00b3ff';
    sphere.rotation.y += 0.06;
    torus3.rotation.z -= 1;
    torus.rotation.z -= 1;
}

function switchState(newState) {
    currentState = newState;
    const text = document.getElementById('jarvis');
    text.style.textShadow = '0 0 10px #00e5ff, 0 0 20px #00e5ff, 0 0 30px #00e5ff;';
    text.style.transition = 'text-shadow 0.5s ease-in-out';
    sphere.material.color.setHex(0x00b3ff);
    torus.material.color.setHex(0x00b3ff);
}

// Main animation loop
function animate() {
    requestAnimationFrame(animate);
    sphere.rotation.y += 0.003;
    torus3.rotation.z -= 0.003;

    lines.forEach(line => {
        line.position.z += 0.1;
        if (line.position.z > 30) {
            line.position.z = -50;
        }
    });

    if (isFinished()) {
        switchState(states.WAITING);
    }

    if (currentState === states.THINKING) {
        animateThinking();
    } else if (currentState === states.WAITING) {
        animateWaiting();
    } else if (currentState === states.ANSWERING) {
        animateAnswering();
    }

    composer.render();
}

animate();