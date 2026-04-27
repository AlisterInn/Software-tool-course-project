const statusBadge = document.getElementById("statusBadge");
const messageBox = document.getElementById("messageBox");
const treeViewport = document.getElementById("treeViewport");
const treeMeta = document.getElementById("treeMeta");

const singleValueInput = document.getElementById("singleValue");
const batchValuesInput = document.getElementById("batchValues");
const randomCountInput = document.getElementById("randomCount");

const inorderOutput = document.getElementById("inorderOutput");
const preorderOutput = document.getElementById("preorderOutput");
const postorderOutput = document.getElementById("postorderOutput");
const searchPathOutput = document.getElementById("searchPathOutput");

let highlightedPath = [];

function setMessage(text, type = "info") {
    messageBox.textContent = text;
    messageBox.dataset.type = type;
}

async function apiPost(url, payload = {}) {
    const res = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (!res.ok) {
        throw new Error(data.error || "Request failed");
    }
    return data;
}

function parseSingleValue() {
    const value = singleValueInput.value.trim();
    if (!value) {
        throw new Error("Enter a value first.");
    }

    const number = Number.parseInt(value, 10);
    if (Number.isNaN(number)) {
        throw new Error("Value must be an integer.");
    }
    return number;
}

function parseBatchValues() {
    const raw = batchValuesInput.value.trim();
    if (!raw) {
        throw new Error("Enter comma-separated values for batch insert.");
    }

    const values = raw
        .split(",")
        .map((item) => Number.parseInt(item.trim(), 10))
        .filter((item) => !Number.isNaN(item));

    if (!values.length) {
        throw new Error("No valid integers found in batch input.");
    }
    return values;
}

function collectLayout(root) {
    const positions = [];
    const edges = [];
    let xIndex = 0;

    function walk(node, depth, parentKey = null) {
        if (!node) {
            return;
        }

        walk(node.left, depth + 1, node.key);

        const x = xIndex;
        xIndex += 1;
        positions.push({ key: node.key, height: node.height, balance: node.balance, depth, x });
        if (parentKey !== null) {
            edges.push({ parent: parentKey, child: node.key });
        }

        walk(node.right, depth + 1, node.key);
    }

    walk(root, 0, null);
    return { positions, edges };
}

function renderTree(root) {
    treeViewport.innerHTML = "";
    if (!root) {
        treeMeta.textContent = "Nodes: 0";
        treeViewport.innerHTML = '<p class="empty">Tree is empty. Insert values to start.</p>';
        return;
    }

    const { positions, edges } = collectLayout(root);
    const maxDepth = Math.max(...positions.map((node) => node.depth));
    const width = Math.max(900, positions.length * 110);
    const height = Math.max(360, (maxDepth + 1) * 120 + 40);
    const xSpacing = width / (positions.length + 1);
    const ySpacing = (height - 60) / (maxDepth + 1);

    const keyed = new Map();
    positions.forEach((node) => {
        keyed.set(node.key, {
            ...node,
            px: (node.x + 1) * xSpacing,
            py: 40 + node.depth * ySpacing,
        });
    });

    const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    svg.setAttribute("viewBox", `0 0 ${width} ${height}`);
    svg.classList.add("tree-svg");

    edges.forEach((edge) => {
        const parent = keyed.get(edge.parent);
        const child = keyed.get(edge.child);
        if (!parent || !child) {
            return;
        }

        const line = document.createElementNS("http://www.w3.org/2000/svg", "line");
        line.setAttribute("x1", parent.px);
        line.setAttribute("y1", parent.py + 22);
        line.setAttribute("x2", child.px);
        line.setAttribute("y2", child.py - 22);
        line.setAttribute("class", "tree-edge");
        svg.appendChild(line);
    });

    const highlightedSet = new Set(highlightedPath);
    positions.forEach((node) => {
        const group = document.createElementNS("http://www.w3.org/2000/svg", "g");
        group.setAttribute("transform", `translate(${keyed.get(node.key).px}, ${keyed.get(node.key).py})`);

        const circle = document.createElementNS("http://www.w3.org/2000/svg", "circle");
        circle.setAttribute("r", "24");
        circle.setAttribute("class", highlightedSet.has(node.key) ? "tree-node highlighted" : "tree-node");
        group.appendChild(circle);

        const valueLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
        valueLabel.setAttribute("class", "node-value");
        valueLabel.textContent = String(node.key);
        group.appendChild(valueLabel);

        const metaLabel = document.createElementNS("http://www.w3.org/2000/svg", "text");
        metaLabel.setAttribute("class", "node-meta");
        metaLabel.setAttribute("y", "38");
        metaLabel.textContent = `h:${node.height} bf:${node.balance}`;
        group.appendChild(metaLabel);

        svg.appendChild(group);
    });

    treeViewport.appendChild(svg);
    treeMeta.textContent = `Nodes: ${positions.length} | Height: ${root.height}`;
}

function renderTraversals(data) {
    const format = (items) => (items && items.length ? items.join(" -> ") : "-");
    inorderOutput.textContent = format(data.inorder);
    preorderOutput.textContent = format(data.preorder);
    postorderOutput.textContent = format(data.postorder);
    searchPathOutput.textContent = format(data.searchPath || []);
}

function renderState(data) {
    renderTree(data.root);
    renderTraversals(data);
}

async function withAction(action, onSuccessMessage) {
    try {
        const data = await action();
        renderState(data);
        setMessage(data.message || onSuccessMessage, "success");
    } catch (error) {
        setMessage(error.message || "Something went wrong.", "error");
    }
}

async function checkHealth() {
    try {
        const res = await fetch("/health");
        if (res.ok) {
            statusBadge.textContent = "Server Online";
            statusBadge.classList.add("ok");
        }
    } catch {
        statusBadge.textContent = "Offline";
        statusBadge.classList.remove("ok");
    }
}

document.getElementById("insertBtn").addEventListener("click", () => {
    withAction(async () => {
        const value = parseSingleValue();
        highlightedPath = [];
        return apiPost("/api/avl/insert", { value });
    }, "Inserted value");
});

document.getElementById("deleteBtn").addEventListener("click", () => {
    withAction(async () => {
        const value = parseSingleValue();
        highlightedPath = [];
        return apiPost("/api/avl/delete", { value });
    }, "Deleted value");
});

document.getElementById("searchBtn").addEventListener("click", () => {
    withAction(async () => {
        const value = parseSingleValue();
        const data = await apiPost("/api/avl/search", { value });
        highlightedPath = data.searchPath || [];
        return data;
    }, "Search complete");
});

document.getElementById("clearBtn").addEventListener("click", () => {
    withAction(async () => {
        highlightedPath = [];
        return apiPost("/api/avl/reset");
    }, "Tree cleared");
});

document.getElementById("randomBtn").addEventListener("click", () => {
    withAction(async () => {
        const count = Number.parseInt(randomCountInput.value, 10) || 9;
        highlightedPath = [];
        return apiPost("/api/avl/random", { count });
    }, "Random tree generated");
});

document.getElementById("batchInsertBtn").addEventListener("click", () => {
    withAction(async () => {
        const values = parseBatchValues();
        highlightedPath = [];

        let latest = null;
        for (const value of values) {
            latest = await apiPost("/api/avl/insert", { value });
        }
        if (latest) {
            latest.message = `Inserted ${values.length} values`;
        }
        return latest;
    }, "Batch insert complete");
});

async function bootstrap() {
    await checkHealth();
    try {
        const res = await fetch("/api/avl/state");
        const data = await res.json();
        renderState(data);
    } catch {
        setMessage("Unable to load initial tree state.", "error");
    }
}

bootstrap();
