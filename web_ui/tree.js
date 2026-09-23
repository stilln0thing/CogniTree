/* tree.js — Decision tree canvas: SVG pan/zoom nodes with Bezier paths */

'use strict';

class DecisionTreeCanvas {
  constructor(svgId, containerId) {
    this.svg       = document.getElementById(svgId);
    this.root      = document.getElementById('tree-svg-root');
    this.container = document.getElementById(containerId);

    this.nodes      = [];   // { id, label, parentId, x, y }
    this.activeId   = null;

    // Pan state
    this.panX = 40;
    this.panY = 40;

    this._bindPan();
    this._updateTransform();
  }

  // ── Public API ────────────────────────────────────────────────────────────

  addNode(id, label, parentId = null) {
    const pos = this._calcPosition(parentId);

    const node = { id, label, parentId, x: pos.x, y: pos.y };
    this.nodes.push(node);
    this.activeId = id;

    this._render();
  }

  reset() {
    this.nodes    = [];
    this.activeId = null;
    if (this.root) this.root.innerHTML = '';
    this.panX = 40;
    this.panY = 40;
    this._updateTransform();
  }

  // ── Positioning ──────────────────────────────────────────────────────────

  _calcPosition(parentId) {
    const NODE_W  = 100;
    const NODE_H  = 60;
    const PAD_X   = 20;

    if (!parentId && this.nodes.length === 0) {
      return { x: 110, y: 30 };
    }

    if (!parentId) {
      // Chain vertically from last root node
      const last = this.nodes[this.nodes.length - 1];
      return { x: last.x, y: last.y + NODE_H + PAD_X };
    }

    const parent   = this.nodes.find(n => n.id === parentId);
    const siblings = this.nodes.filter(n => n.parentId === parentId);
    const idx      = siblings.length;

    const totalW    = (siblings.length + 1) * (NODE_W + PAD_X) - PAD_X;
    const startX    = parent.x - totalW / 2 + (NODE_W + PAD_X) * idx;

    return { x: startX + NODE_W / 2, y: parent.y + NODE_H + PAD_X };
  }

  // ── Rendering ────────────────────────────────────────────────────────────

  _render() {
    if (!this.root) return;
    this.root.innerHTML = '';

    // 1. Draw bezier paths first (behind nodes)
    this.nodes.forEach(node => {
      if (!node.parentId) return;
      const parent = this.nodes.find(n => n.id === node.parentId);
      if (!parent) return;

      const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
      const midY = (parent.y + node.y) / 2;
      path.setAttribute('d', `M${parent.x},${parent.y} C${parent.x},${midY} ${node.x},${midY} ${node.x},${node.y}`);
      path.setAttribute('class', node.id === this.activeId ? 'c-path active' : 'c-path');
      this.root.appendChild(path);
    });

    // 2. Draw nodes
    this.nodes.forEach(node => {
      const isActive = node.id === this.activeId;
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('transform', `translate(${node.x},${node.y})`);

      // Node dot (circle)
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('r', '8');
      circle.setAttribute('class', isActive ? 'c-node-dot active' : 'c-node-dot');

      // Label
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', '14');
      text.setAttribute('y', '4');
      text.setAttribute('class', isActive ? 'c-node-text active' : 'c-node-text');
      const maxLen = 18;
      text.textContent = node.label.length > maxLen
        ? node.label.slice(0, maxLen) + '…'
        : node.label;

      g.appendChild(circle);
      g.appendChild(text);

      // Click → time travel
      g.style.cursor = 'pointer';
      g.addEventListener('click', (e) => {
        e.stopPropagation();
        this.activeId = node.id;
        this._render();
        if (typeof window.onNodeSelect === 'function') {
          window.onNodeSelect(node);
        }
      });

      this.root.appendChild(g);
    });

    this._updateTransform();
  }

  // ── Pan & Zoom ────────────────────────────────────────────────────────────

  _bindPan() {
    if (!this.container) return;

    let dragging = false;
    let startX = 0, startY = 0;

    this.container.addEventListener('mousedown', (e) => {
      if (e.target.tagName === 'circle' || e.target.tagName === 'text') return;
      dragging = true;
      startX = e.clientX - this.panX;
      startY = e.clientY - this.panY;
      this.container.style.cursor = 'grabbing';
    });

    window.addEventListener('mousemove', (e) => {
      if (!dragging) return;
      this.panX = e.clientX - startX;
      this.panY = e.clientY - startY;
      this._updateTransform();
    });

    window.addEventListener('mouseup', () => {
      if (dragging) {
        dragging = false;
        if (this.container) this.container.style.cursor = '';
      }
    });
  }

  _updateTransform() {
    if (this.root) {
      this.root.setAttribute('transform', `translate(${this.panX},${this.panY})`);
    }
  }
}

// ── Init ───────────────────────────────────────────────────────────────────
window.treeCanvas = new DecisionTreeCanvas('tree-canvas-svg', 'tree-viewport-container');
