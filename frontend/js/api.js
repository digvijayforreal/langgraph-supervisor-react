// fetch() is used instead of EventSource because /chat/stream is a POST route.
export async function streamChat(message, onEvent) {
    const response = await fetch("/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message })
    });
    if (!response.ok) {
        const body = await response.text();
        throw new Error(`HTTP ${response.status}: ${body.slice(0, 200)}`);
    }
    if (!response.body) throw new Error("Streaming is unavailable");

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    let completed = false;
    let failed = false;

    function processBlock(block) {
        const payload = block.split("\n")
            .filter(line => line.startsWith("data:"))
            .map(line => line.slice(5).trimStart()).join("\n");
        if (!payload) return;
        const event = JSON.parse(payload);
        onEvent(event);
        if (event.type === "completed") completed = true;
        if (event.type === "error") {
            failed = true;
            throw new Error(event.message || "Unknown graph error");
        }
    }

    while (true) {
        const { value, done } = await reader.read();
        if (done) {
            buffer += decoder.decode();
        } else {
            buffer += decoder.decode(value, { stream: true });
        }
        buffer = buffer.replace(/\r\n/g, "\n");
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";
        for (const part of parts) processBlock(part);
        if (done) break;
    }
    if (buffer.trim()) processBlock(buffer);
    if (!completed && !failed) throw new Error("Stream closed before completion");
}
