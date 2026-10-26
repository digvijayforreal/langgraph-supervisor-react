import { streamChat } from "./api.js";
import { resetPipeline, updatePipeline } from "./pipeline.js";
import { initializeInspector, recordNodeEvent, resetInspector } from "./inspector.js";

const form = document.getElementById("chat-form");
const input = document.getElementById("query-input");
const button = document.getElementById("send-button");
const messages = document.getElementById("chat-messages");
const logs = document.getElementById("execution-logs");
const badge = document.getElementById("api-status");
const uploadInput = document.getElementById("upload-file");
const uploadStatus = document.getElementById("upload-status");
const chatStatus = document.getElementById("chat-status");
const executionTime = document.getElementById("execution-time");

let isRunning = false;
let delivered = false;
let currentUpload = null;
let chartsForRequest = new Set();

function addMessage(sender, body, kind = "assistant") {
    messages.querySelector(".placeholder")?.remove();
    const item = document.createElement("div");
    item.className = `message ${kind}`;
    const title = document.createElement("span");
    title.className = "sender";
    title.textContent = sender;
    const text = document.createElement("pre");
    text.className = "message-body";
    text.textContent = String(body ?? "");
    item.append(title, text);
    messages.appendChild(item);
    messages.scrollTop = messages.scrollHeight;
}

function addLog(event) {
    logs.querySelector(".placeholder")?.remove();
    const item = document.createElement("div");
    item.className = event.type === "error" ? "log-entry error" : "log-entry";
    const time = document.createElement("span");
    time.className = "log-time";
    time.textContent = new Date().toLocaleTimeString();
    const details = document.createElement("span");
    details.textContent = [
        event.type, event.node, event.phase,
        event.attempt != null ? `#${event.attempt}` : null,
        event.approved === false ? "rejected" : null,
        event.message
    ].filter(Boolean).join(" | ");
    item.append(time, details);
    logs.appendChild(item);
    logs.scrollTop = logs.scrollHeight;
}

function renderChart(fileName) {
    if (chartsForRequest.has(fileName)) return;
    chartsForRequest.add(fileName);
    const img = document.createElement("img");
    img.src = `/charts/${encodeURIComponent(fileName)}`;
    img.alt = "Generated data analysis chart";
    img.className = "chart-preview";
    img.loading = "lazy";
    messages.appendChild(img);
    messages.scrollTop = messages.scrollHeight;
}

function onEvent(event) {
    updatePipeline(event);
    recordNodeEvent(event);
    addLog(event);

    if ((event.type === "final_answer" || event.type === "worker_completed") && !delivered) {
        delivered = true;
        const node = event.node || "supervisor";
        addMessage(
            node === "supervisor" ? "SUPERVISOR" : `${node.toUpperCase()} AGENT`,
            event.answer,
            event.approved === false ? "system" : "assistant"
        );
    }

    // A chart may be emitted during an attempt that is later rejected.
    // Only show it once the Supervisor approves the final answer.
    if (event.type === "tool_event" && event.stage === "result") {
        try {
            const result = typeof event.result === "string" ? JSON.parse(event.result) : event.result;
            if (result?.success && result.tool === "generate_chart" && result.chart_file) {
                pendingCharts.push({ file: result.chart_file, attempt: event.attempt });
            }
        } catch (_) { /* Not every tool returns JSON. */ }
    }
    if (event.type === "worker_completed" && event.approved !== false && event.node === "data_analyst") {
        const finalAttempt = event.attempts;
        for (const chart of pendingCharts) {
            if (chart.attempt === finalAttempt) renderChart(chart.file);
        }
    }
    if (event.type === "completed") {
        executionTime.textContent = event.execution_time_ms != null
            ? `${event.execution_time_ms} ms` : "Completed";
    }
}

let pendingCharts = [];

function shouldAttachFile(question) {
    if (!currentUpload) return false;
    const q = question.trim();
    // Greetings should never be interpreted as dataset requests.
    if (/^(hi|hello|hey|good morn(?:ing|ing ai|ing there)|good moring|good afternoon|good evening|thanks|thank you)[!?.\s]*$/i.test(q)) {
        return false;
    }
    // Weather/current information requests should route to Research or Supervisor.
    if (/\b(weather|forecast|temperature|web\s*search|search\s*(?:the\s*)?web|online|latest\s+(?:news|release))\b/i.test(q)) {
        return false;
    }
    const fileContext = /\b(uploaded|attached|file|dataset|csv|xlsx|excel|pdf|document|spreadsheet|column|columns|rows|table|chart|plot|graph|revenue|sales|life expectancy|minimum|maximum|average|mean|analy[sz]e|inspect|extract|summari[sz]e)\b/i;
    return fileContext.test(q);
}

function buildQueryWithFile(question) {
    if (!shouldAttachFile(question)) return question;
    return [
        `Uploaded file: ${currentUpload.file_name}`,
        `Relevant specialist: ${currentUpload.agent}`,
        `Exact server filename: ${currentUpload.file_name}`,
        "The file is already stored on the server. Use file-processing tools.",
        `User question: ${question}`
    ].join("\n");
}

async function uploadSelectedFile() {
    if (!uploadInput?.files?.length) return;
    const selectedFile = uploadInput.files[0];
    uploadStatus.textContent = `Uploading ${selectedFile.name}...`;
    const body = new FormData();
    body.append("file", selectedFile);
    const response = await fetch("/upload", { method: "POST", body });
    let payload;
    try {
        payload = await response.json();
    } catch {
        throw new Error(`Upload returned HTTP ${response.status}`);
    }
    if (!response.ok) {
        throw new Error(typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail || payload));
    }
    if (!payload.file_name || !payload.agent) {
        throw new Error("Upload response missing filename or agent");
    }
    currentUpload = payload;
    uploadStatus.textContent = `Uploaded ${payload.original_name || selectedFile.name}`;
    uploadInput.value = "";
}

form.addEventListener("submit", async event => {
    event.preventDefault();
    const question = input.value.trim();
    if (!question || isRunning) return;

    isRunning = true;
    delivered = false;
    pendingCharts = [];
    chartsForRequest = new Set();
    input.disabled = true;
    button.disabled = true;
    if (uploadInput) uploadInput.disabled = true;
    badge.className = "status-badge busy";
    badge.textContent = "Running";
    chatStatus.textContent = "Processing";
    executionTime.textContent = "Running...";
    resetPipeline();
    resetInspector();
    logs.replaceChildren();
    addMessage("YOU", question, "user");
    input.value = "";

    try {
        await uploadSelectedFile();
        const effectiveQuery = buildQueryWithFile(question);
        await streamChat(effectiveQuery, onEvent);
        badge.className = "status-badge";
        badge.textContent = "Ready";
    } catch (error) {
        console.error("LangGraph error:", error);
        if (!delivered) addMessage("SYSTEM", `Execution failed: ${error.message}`, "system");
        updatePipeline({ type: "error" });
        badge.className = "status-badge error";
        badge.textContent = "Error";
        executionTime.textContent = "Failed";
        addLog({ type: "error", message: error.message });
    } finally {
        isRunning = false;
        input.disabled = false;
        button.disabled = false;
        if (uploadInput) uploadInput.disabled = false;
        chatStatus.textContent = "Idle";
        input.focus();
    }
});

uploadInput?.addEventListener("change", () => {
    const selected = uploadInput.files?.[0];
    uploadStatus.textContent = selected
        ? `Selected: ${selected.name}`
        : currentUpload ? `Uploaded ${currentUpload.original_name}` : "";
});

input.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        if (!isRunning && input.value.trim()) form.requestSubmit();
    }
});

initializeInspector();
