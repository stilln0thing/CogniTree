/* tree.js — Smooth SVG Decision Tree Canvas with Bezier Connectors & Auto-Layout */

class DecisionTreeCanvas {
  constructor(svgId, containerId) {
    this.svg = document.getElementById(svgId);
    this.group = document.getElementById('tree-root-group');
    this.container = document.getElementById(containerId);
    this.nodes = [];
    this.activeNodeId = null;

    this.panX = 40;
    this.panY = 40;
    this.zoom = 1.0;

    this.initPanZoom();
  }

  initPanZoom() {
    if (!this.container) return;
    let isDragging = false;
    let startX = 0, startY = 0;

    this.container.addEventListener('mousedown', (e) => {
      if (e.target.tagName === 'circle' || e.target.tagName === 'text') return;
      isDragging = true;
      startX = e.clientX - this.panX;
      startY = e.clientY - this.panY;
    });

    window.addEventListener('mousemove', (e) => {
      if (!isDragging) return;
      this.panX = e.clientX - startX;
      this.panY = e.clientY - startY;
      this.updateTransform();
    });

    window.addEventListener('mouseup', () => {
      isDragging = false;
    });
  }

  updateTransform() {
    if (this.group) {
      this.group.setAttribute('transform', `translate(${this.panX}, ${this.panY}) scale(${this.zoom})`);
    }
  }

  addNode(id, label, parentId = null) {
    // If first node, root at top center
    let x = 180;
    let y = 60;

    if (parentId) {
      const parent = this.nodes.find(n => n.id === parentId);
      if (parent) {
        const siblings = this.nodes.filter(n => n.parentId === parentId);
        x = parent.x + (siblings.length * 140) - (siblings.length > 0 ? 70 : 0);
        y = parent.y + 90;
      }
    } else if (this.nodes.length > 0) {
      const last = this.nodes[this.nodes.length - 1];
      x = last.x;
      y = last.y + 90;
      parentId = last.id;
    }

    const node = { id, label, parentId, x, y };
    this.nodes.push(node);
    this.activeNodeId = id;
    this.render();
  }

  render() {
    if (!this.group) return;
    this.group.innerHTML = '';

    // Step 1: Render smooth Bezier connecting paths
    this.nodes.forEach(node => {
      if (node.parentId) {
        const parent = this.nodes.find(n => n.id === node.parentId);
        if (parent) {
          const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
          const midY = (parent.y + node.y) / 2;
          const d = `M ${parent.x} ${parent.y} C ${parent.x} ${midY}, ${node.x} ${midY}, ${node.x} ${node.y}`;
          
          path.setAttribute('d', d);
          path.setAttribute('class', node.id === this.activeNodeId ? 'tree-edge active' : 'tree-edge');
          this.group.appendChild(path);
        }
      }
    });

    // Step 2: Render Nodes & Labels
    this.nodes.forEach(node => {
      const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
      g.setAttribute('class', 'tree-node-group');
      g.setAttribute('transform', `translate(${node.x}, ${node.y})`);

      // Node Circle
      const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      circle.setAttribute('r', '16');
      circle.setAttribute('class', node.id === this.activeNodeId ? 'tree-node-circle active' : 'tree-node-circle');

      // Node Label
      const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      text.setAttribute('x', '22');
      text.setAttribute('y', '5');
      text.setAttribute('class', 'tree-node-text');
      text.textContent = node.label.length > 18 ? node.label.substring(0, 18) + '...' : node.label;

      g.appendChild(circle);
      g.appendChild(text);

      g.addEventListener('click', (e) => {
        e.stopPropagation();
        this.activeNodeId = node.id;
        this.render();
        if (window.onNodeSelect) {
          window.onNodeSelect(node);
        }
      });

      this.group.appendChild(g);
    });

    this.updateTransform();
  }
}

window.treeCanvas = new DecisionTreeCanvas('tree-svg', 'tree-viewport');
