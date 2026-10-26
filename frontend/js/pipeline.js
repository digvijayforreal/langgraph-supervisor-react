const nodes = ["start", "supervisor", "router", "research", "data_analyst", "document", "end"];

function setNode(name, status) {
    const el = document.getElementById(`node-${name}`);
    if (!el) return;
    el.classList.remove("active", "completed", "skipped", "failed");
    if (status !== "idle") el.classList.add(status);
    const label = el.querySelector(".node-status");
    if (label) label.textContent = status.charAt(0).toUpperCase() + status.slice(1);
}
function status(value) { document.getElementById("pipeline-status").textContent = value; }
function review(value, statusClass = "") {
    const el = document.getElementById("review-summary");
    el.className = "supervisor-review-status";
    if (statusClass) el.classList.add(statusClass);
    el.textContent = value;
}
export function resetPipeline() {
    nodes.forEach(node => setNode(node, "idle"));
    status("Waiting"); review("Waiting for task");
}
export function updatePipeline(event) {
    switch (event.type) {
        case "query_received":
            setNode("start", "completed"); status("Query received"); break;
        case "supervisor_started":
            setNode("supervisor", "active");
            if (event.phase === "review") {
                review(`Reviewing attempt ${event.attempt}`, "reviewing");
                status("Supervisor reviewing draft");
            } else {
                review("Routing or answering directly...");
                status("Supervisor analyzing query");
            }
            break;
        case "supervisor_completed":
            setNode("supervisor", "completed");
            if (event.selected_agent === "supervisor") {
                ["research", "data_analyst", "document"].forEach(n => setNode(n, "skipped"));
                setNode("router", "skipped");
                review("Answered directly", "approved");
                status("General answer by Supervisor");
            } else {
                setNode("router", "completed");
                ["research", "data_analyst", "document"].filter(n => n !== event.selected_agent)
                    .forEach(n => setNode(n, "skipped"));
                review(`Assigned to ${event.selected_agent}`);
                status(`Selected: ${event.selected_agent}`);
            }
            break;
        case "worker_scheduled":
            setNode(event.node, "active");
            status(`${event.node} — attempt ${event.attempt}`); break;
        case "worker_draft":
            setNode(event.node, "completed");
            status(`Draft ${event.attempt} ready`); break;
        case "supervisor_review_completed":
            setNode("supervisor", event.approved ? "completed" : "failed");
            review(`${event.approved ? "Approved" : "Rejected"} · ${event.score}/10 · Attempt ${event.attempt}`,
                event.approved ? "approved" : "rejected");
            status(event.approved ? "Supervisor approved" : "Supervisor rejected draft");
            break;
        case "revision_requested":
            setNode(event.node, "active"); status(`Revision ${event.attempt} requested`); break;
        case "worker_completed":
        case "final_answer":
            status(event.approved ? "Final answer ready" : "Review limit reached"); break;
        case "completed":
            setNode("end", "completed"); status("Completed"); break;
        case "error": status("Execution failed"); break;
    }
}
