const state = {};
let history = [];
let selected = null;

export function resetInspector() {
    for (const key of Object.keys(state)) delete state[key];
    history = [];
    selected = null;
    document.querySelectorAll(".clickable").forEach(n => n.classList.remove("selected"));
    document.getElementById("inspector-content").textContent = "Click a node to inspect it.";
}

export function recordNodeEvent(event) {
    if (event.type === "supervisor_completed") {
        state.supervisor = {
            selected_agent: event.selected_agent,
            routing_reason: event.routing_reason,
            supervisor_usage: event.supervisor_usage || {},
            execution_path: event.execution_path
        };
    }
    if (event.type === "worker_draft") {
        state[event.node] = {
            attempts: event.attempt,
            latest_draft: event.draft_answer,
            worker_usage: event.worker_usage || {},
            execution_path: event.execution_path
        };
        history.push({
            attempt: event.attempt,
            worker: event.node,
            draft: event.draft_answer,
            approved: null,
            score: null,
            feedback: "Pending review"
        });
    }
    if (event.type === "supervisor_review_completed") {
        state.supervisor = {
            ...state.supervisor,
            latest_action: "Review",
            approved: event.approved,
            review_score: event.score,
            review_feedback: event.feedback,
            review_attempt: event.attempt,
            supervisor_usage: event.supervisor_usage || {},
            execution_path: event.execution_path
        };
        const item = history.find(entry => entry.attempt === event.attempt);
        if (item) {
            item.approved = event.approved;
            item.score = event.score;
            item.feedback = event.feedback;
        }
    }
    if (event.type === "final_answer" || event.type === "worker_completed") {
        const target = event.node || "supervisor";
        state[target] = {
            ...state[target],
            final_answer: event.answer,
            final_status: event.approved ? "Approved" : "Not approved"
        };
    }
    if (event.type === "tool_event") {
        const agent = event.node;
        if (agent) {
            const existing = state[agent] || {};
            state[agent] = {...existing, tool_history: [...(existing.tool_history || []), event]};
        }
    }
    if (selected) showInspector(selected);
}

function addField(container, title, value) {
    const row = document.createElement("div"); row.className = "inspector-row";
    const label = document.createElement("strong"); label.textContent = title.replaceAll("_", " ");
    const pre = document.createElement("pre"); pre.className = "inspector-json";
    pre.textContent = typeof value === "object" ? JSON.stringify(value, null, 2) : String(value);
    row.append(label, pre); container.appendChild(row);
}

export function showInspector(agent) {
    selected = agent;
    document.querySelectorAll(".clickable").forEach(el => {
        el.classList.toggle("selected", el.dataset.agent === agent);
    });
    const box = document.getElementById("inspector-content"); box.replaceChildren();
    const heading = document.createElement("h3"); heading.textContent = `${agent.toUpperCase()} — Inspector`;
    box.appendChild(heading);
    const data = state[agent] || { status: "No execution data yet" };
    Object.entries(data).forEach(([key, value]) => addField(box, key, value));
    if (agent === "supervisor" && history.length) {
        const heading2 = document.createElement("h3"); heading2.textContent = "Review History";
        box.appendChild(heading2);
        const wrapper = document.createElement("div"); wrapper.className = "review-history";
        for (const entry of history) {
            const card = document.createElement("div"); card.className = "review-entry";
            const title = document.createElement("strong");
            title.textContent = `Attempt ${entry.attempt} — ${entry.approved === null ? "Pending" : entry.approved ? "Approved" : "Rejected"}`;
            const feedback = document.createElement("p");
            feedback.textContent = `Score: ${entry.score ?? "Pending"} | Feedback: ${entry.feedback}`;
            const draft = document.createElement("pre"); draft.textContent = entry.draft;
            card.append(title, feedback, draft); wrapper.appendChild(card);
        }
        box.appendChild(wrapper);
    }
}

export function initializeInspector() {
    document.querySelectorAll(".clickable").forEach(el => {
        const show = () => showInspector(el.dataset.agent);
        el.addEventListener("click", show);
        el.addEventListener("keydown", event => {
            if (event.key === "Enter" || event.key === " ") {
                event.preventDefault(); show();
            }
        });
    });
}
