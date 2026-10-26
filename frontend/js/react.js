
const form = document.getElementById("react-chat-form");
const input = document.getElementById("react-query-input");
const button = document.getElementById("react-send-button");
const messages = document.getElementById("react-messages");
const logs = document.getElementById("react-tool-logs");
const badge = document.getElementById("react-api-status");
const chatStatus = document.getElementById("react-chat-status");
const clearButton = document.getElementById("react-clear-logs");

let isRunning = false;
let isSendingEmail = false;

const toolNames = {
  react_web_search: "Tavily Web Search",
  react_generate_pdf: "PDF Generator",
  react_pdf_generator: "PDF Generator",
  react_datetime: "Date & Time",
  react_send_email: "Email Preview",
};

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
  return item;
}

function addToolLog(title, detail, status = "") {
  logs.querySelector(".placeholder")?.remove();

  const item = document.createElement("div");
  item.className = "react-tool-entry";

  const heading = document.createElement("strong");
  heading.textContent = title;

  const description = document.createElement("div");
  description.textContent = detail;

  const time = document.createElement("small");
  time.textContent =
    `${new Date().toLocaleTimeString()}${status ? ` · ${status}` : ""}`;

  item.append(heading, description, time);
  logs.appendChild(item);
  logs.scrollTop = logs.scrollHeight;
}

function renderPdfLink(answer) {
  const matches = answer.match(/[^\\/\n`"'<>]+\.pdf/ig);
  if (!matches?.length) return;

  const filename = matches[matches.length - 1].trim();
  const link = document.createElement("a");
  link.className = "react-file-link";
  link.textContent = `Open PDF report: ${filename}`;
  link.href = `/api/react/reports/${encodeURIComponent(filename)}`;
  link.target = "_blank";
  link.rel = "noopener noreferrer";

  const wrapper = document.createElement("div");
  wrapper.className = "react-widget";
  wrapper.appendChild(link);
  messages.appendChild(wrapper);
}

function parseEmailPreview(answer) {
  if (!answer.includes("EMAIL PREVIEW")) return null;

  const getField = (label) => {
    const match = answer.match(new RegExp(`^${label}:\\s*(.*)$`, "im"));
    return match ? match[1].trim() : "";
  };

  const bodyMatch = answer.match(
    /^Body:\s*\n([\s\S]*?)(?:\n\n(?:This tool cannot send emails|Use the application's separate)[\s\S]*)?$/im
  );

  let attachment = getField("Attachment");

  // Convert a local report path into a filename, never submit the path.
  if (attachment && attachment !== "No attachment") {
    attachment = attachment.split(/[\\/]/).pop().trim();
  } else {
    attachment = "";
  }

  return {
    recipient: getField("To"),
    subject: getField("Subject"),
    attachment,
    body: bodyMatch ? bodyMatch[1].trim() : "",
  };
}

function makeField(labelText, value, multiline = false, required = false) {
  const wrapper = document.createElement("label");
  wrapper.className = "react-email-edit-field";
  wrapper.textContent = labelText;

  const control = document.createElement(multiline ? "textarea" : "input");
  control.value = value || "";
  control.required = required;
  control.className = "react-email-input";

  if (multiline) {
    control.rows = 7;
  }

  wrapper.appendChild(control);
  return { wrapper, control };
}

function renderEmailPreview(email) {
  const card = document.createElement("section");
  card.className = "react-email-widget";

  const heading = document.createElement("div");
  heading.className = "react-email-heading";
  heading.textContent = "Email Draft — Not Sent";
  card.appendChild(heading);

  const notice = document.createElement("p");
  notice.className = "react-email-note";
  notice.textContent =
    "Review and edit every field. Nothing is sent until you confirm below.";
  card.appendChild(notice);

  const recipient = makeField("Recipient email", email.recipient, false, true);
  recipient.control.type = "email";
  recipient.control.autocomplete = "email";

  const subject = makeField("Subject", email.subject, false, true);
  subject.control.maxLength = 200;

  const body = makeField("Message body", email.body, true, true);
  body.control.maxLength = 20000;

  const attachment = makeField(
    "PDF attachment filename (optional)",
    email.attachment || ""
  );
  attachment.control.placeholder = "Example: report_123.pdf";
  attachment.control.maxLength = 255;

  card.append(
    recipient.wrapper,
    subject.wrapper,
    body.wrapper,
    attachment.wrapper
  );

  const confirmLabel = document.createElement("label");
  confirmLabel.className = "react-email-confirm";

  const confirm = document.createElement("input");
  confirm.type = "checkbox";
  confirm.required = true;

  const confirmText = document.createElement("span");
  confirmText.textContent =
    "I reviewed the recipient, subject, body and attachment, and approve sending this email.";

  confirmLabel.append(confirm, confirmText);

  const send = document.createElement("button");
  send.type = "button";
  send.className = "react-email-send-button";
  send.textContent = "Approve & Send Email";

  const status = document.createElement("p");
  status.className = "react-email-note";
  status.setAttribute("role", "status");

  send.addEventListener("click", async () => {
    if (isSendingEmail) return;

    if (!recipient.control.reportValidity()) return;
    if (!subject.control.reportValidity()) return;
    if (!body.control.reportValidity()) return;

    if (!confirm.checked) {
      status.textContent = "Please check the approval box before sending.";
      return;
    }

    const filename = attachment.control.value.trim();

    if (
      filename &&
      (filename !== filename.split(/[\\/]/).pop() ||
        !filename.toLowerCase().endsWith(".pdf") ||
        filename.includes(".."))
    ) {
      status.textContent =
        "Enter only the filename of a PDF inside the reports folder.";
      return;
    }

    const approved = window.confirm(
      `Send this email now?\n\nTo: ${recipient.control.value}\nSubject: ${subject.control.value}\n\nOnly continue if these details are correct.`
    );

    if (!approved) return;

    isSendingEmail = true;
    send.disabled = true;
    status.textContent = "Sending email…";

    addToolLog(
      "Email delivery requested",
      `User approved email to ${recipient.control.value}.`,
      "Sending"
    );

    try {
      const response = await fetch("/api/react/email/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          recipient: recipient.control.value.trim(),
          subject: subject.control.value.trim(),
          body: body.control.value,
          attachment_filename: filename || null,
        }),
      });

      const result = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(result.detail || `HTTP ${response.status}`);
      }

      status.textContent = "Email sent successfully.";
      send.textContent = "Email Sent";
      confirm.disabled = true;
      recipient.control.disabled = true;
      subject.control.disabled = true;
      body.control.disabled = true;
      attachment.control.disabled = true;

      addToolLog(
        "Email sent",
        `The server reported delivery to ${result.recipient}.`,
        "Success"
      );
    } catch (error) {
      status.textContent = `Could not send email: ${error.message}`;
      send.disabled = false;
      addToolLog("Email delivery failed", error.message, "Error");
    } finally {
      isSendingEmail = false;
    }
  });

  card.append(confirmLabel, send, status);
  messages.appendChild(card);
  messages.scrollTop = messages.scrollHeight;
}

function renderAnswer(answer) {
  const email = parseEmailPreview(answer);

  if (email) {
    addMessage("GEMINI REACT", "I've prepared an email draft for your review.");
    renderEmailPreview(email);
  } else {
    addMessage("GEMINI REACT", answer);
  }

  renderPdfLink(answer);
}

async function readSseStream(response) {
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`HTTP ${response.status}: ${body.slice(0, 300)}`);
  }

  if (!response.body) {
    throw new Error("Streaming is unavailable in this response.");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let finalAnswer = "";
  let gotCompleted = false;

  function processBlock(block) {
    const data = block
      .split("\n")
      .filter((line) => line.startsWith("data:"))
      .map((line) => line.slice(5).trimStart())
      .join("\n");

    if (!data) return;

    const event = JSON.parse(data);

    if (event.type === "started") {
      addToolLog("Workflow started", event.message || "Gemini ReAct is running.");
    }

    if (event.type === "tool_started") {
      const label = toolNames[event.tool] || event.tool || "Unknown tool";
      addToolLog(`${label} — Started`, "Gemini requested this tool.", "Running");
    }

    if (event.type === "tool_completed") {
      const label = toolNames[event.tool] || event.tool || "Unknown tool";
      addToolLog(
        `${label} — Completed`,
        event.result_preview || "Tool returned a result.",
        "Completed"
      );
    }

    if (event.type === "completed") {
      finalAnswer = event.response || "";
      gotCompleted = true;
    }

    if (event.type === "error") {
      throw new Error(event.message || "ReAct workflow failed.");
    }
  }

  while (true) {
    const { value, done } = await reader.read();

    buffer += done
      ? decoder.decode()
      : decoder.decode(value, { stream: true });

    buffer = buffer.replace(/\r\n/g, "\n");
    const blocks = buffer.split("\n\n");
    buffer = blocks.pop() || "";

    for (const block of blocks) processBlock(block);
    if (done) break;
  }

  if (buffer.trim()) processBlock(buffer);

  if (!gotCompleted) {
    throw new Error("The stream ended before the workflow completed.");
  }

  return finalAnswer;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();

  const message = input.value.trim();
  if (!message || isRunning) return;

  isRunning = true;
  input.disabled = true;
  button.disabled = true;
  badge.className = "status-badge busy";
  badge.textContent = "Running";
  chatStatus.textContent = "Processing";

  addMessage("YOU", message, "user");
  addToolLog("Request received", "Sending the query to Gemini ReAct.");
  input.value = "";

  try {
    const response = await fetch("/api/react/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message }),
    });

    const answer = await readSseStream(response);
    renderAnswer(answer);

    badge.className = "status-badge";
    badge.textContent = "Ready";
    addToolLog("Workflow finished", "Final response received.", "Completed");
  } catch (error) {
    console.error("ReAct request failed:", error);
    addMessage("SYSTEM", `Execution failed: ${error.message}`, "system");
    addToolLog("Workflow failed", error.message, "Error");
    badge.className = "status-badge error";
    badge.textContent = "Error";
  } finally {
    isRunning = false;
    input.disabled = false;
    button.disabled = false;
    chatStatus.textContent = "Idle";
    input.focus();
  }
});

input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if (!isRunning && input.value.trim()) form.requestSubmit();
  }
});

clearButton.addEventListener("click", () => {
  logs.replaceChildren();
  const placeholder = document.createElement("p");
  placeholder.className = "placeholder";
  placeholder.textContent = "Tool activity will appear here.";
  logs.appendChild(placeholder);
});
