import React, { useState, useRef, useEffect } from "react";
import { claimsAPI } from "../services/api";
import { v4 as uuidv4 } from "uuid";
import { FormattedText } from "../utils/formatText";

function generateUniqueId() {
  const uniquePart = uuidv4().replace(/-/g, "").substring(0, 8).toUpperCase();
  return `CLM-${uniquePart}`;
}

const ChatInterface = () => {
  const [useBackendAgent, setUseBackendAgent] = useState(true); // Toggle for backend agent
  const [useGuidedFlow, setUseGuidedFlow] = useState(true); // Use guided question flow
  const [conversationId, setConversationId] = useState(null);
  const [collectedClaimData, setCollectedClaimData] = useState({}); // Data collected through guided flow
  const [readyToSubmit, setReadyToSubmit] = useState(false); // Whether claim is ready to submit
  const [tempClaimId, setTempClaimId] = useState(null); // Temporary claim ID for file uploads before submission
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: "bot",
      text: "👋 Hello! I'm your AI Claims Assistant powered by Gemini AI. I'll guide you through submitting your claim step by step.\n\n**Ready to start?** Type 'new claim' or 'start' to begin!",
      timestamp: new Date(),
    },
  ]);
  const [inputValue, setInputValue] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [claimData, setClaimData] = useState({});
  const [currentStep, setCurrentStep] = useState("policy_number");
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);
  const chatInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (text, type = "user", options = {}) => {
    const newMessage = {
      id: messages.length + 1,
      type,
      text,
      timestamp: new Date(),
      ...options,
    };
    setMessages((prev) => [...prev, newMessage]);
  };

  const addBotMessage = async (text, delay = 800) => {
    setIsTyping(true);
    await new Promise((resolve) => setTimeout(resolve, delay));
    setIsTyping(false);
    addMessage(text, "bot");
    // Focus input field after bot message is displayed
    setTimeout(() => {
      chatInputRef.current?.focus();
    }, 100);
  };

  // New function to get AI response from backend
  const getAIResponse = async (userMessage) => {
    try {
      setIsTyping(true);

      // Build context
      const context = {};
      if (Object.keys(claimData).length > 0) {
        context.claim_data = claimData;
      }

      // Call backend chat API
      const response = await claimsAPI.sendChatMessage(
        userMessage,
        conversationId,
        context
      );

      setIsTyping(false);

      // Add AI response
      addMessage(response.response, "bot", {
        suggestions: response.suggestions,
        intent: response.intent,
      });

      // Focus input field after bot message is displayed
      setTimeout(() => {
        chatInputRef.current?.focus();
      }, 100);

      // Update conversation ID if provided
      if (response.conversation_id && !conversationId) {
        setConversationId(response.conversation_id);
      }

      return response;
    } catch (error) {
      setIsTyping(false);
      console.error("Chat API error:", error);
      await addBotMessage(
        `❌ Sorry, I'm having trouble connecting to the AI assistant. ${error.message}\n\nPlease try again or use the form to submit your claim.`
      );
      return null;
    }
  };

  // Guided submission flow - asks questions one by one
  const handleGuidedSubmission = async (userMessage) => {
    try {
      setIsTyping(true);

      // Call guided submission API
      const response = await claimsAPI.sendGuidedMessage(
        userMessage,
        conversationId,
        collectedClaimData
      );

      setIsTyping(false);

      // Update collected data
      setCollectedClaimData(response.collected_data || {});

      // Update ready to submit status
      setReadyToSubmit(response.ready_to_submit || false);

      // Add AI response
      addMessage(response.response, "bot", {
        next_field: response.next_field,
        is_complete: response.is_complete,
      });

      // Focus input field after bot message is displayed
      setTimeout(() => {
        chatInputRef.current?.focus();
      }, 100);

      // Update conversation ID if provided
      if (response.conversation_id && !conversationId) {
        setConversationId(response.conversation_id);
      }

      return response;
    } catch (error) {
      setIsTyping(false);
      console.error("Guided chat API error:", error);
      await addBotMessage(
        `❌ Sorry, I'm having trouble processing your response. ${error.message}\n\nPlease try again.`
      );
      return null;
    }
  };

  const handleFileUpload = async (event) => {
    const files = Array.from(event.target.files);

    if (files.length === 0) return;

    const tempClaimId = generateUniqueId();
    setTempClaimId(tempClaimId);
    // If we have a temp claim ID (from guided flow), upload files to backend
    if (tempClaimId && useGuidedFlow) {
      try {
        setIsTyping(true);
        const uploadPromises = files.map((file) =>
          claimsAPI.uploadClaimDocument(tempClaimId, file)
        );
        const results = await Promise.all(uploadPromises);

        // Update collected data with uploaded documents
        const uploadedPaths = results.map((r) => r.saved_path);
        setCollectedClaimData((prev) => ({
          ...prev,
          documents: [...(prev.documents || []), ...uploadedPaths],
        }));

        await addBotMessage(
          `✓ Uploaded ${files.length} file(s) successfully!\n\n` +
            `Files: ${files.map((f) => f.name).join(", ")}\n\n` +
            `You can upload more files or proceed to submit your claim.`
        );
        setIsTyping(false);
      } catch (error) {
        setIsTyping(false);
        console.error("File upload error:", error);
        await addBotMessage(
          `❌ Error uploading files: ${
            error.response?.data?.detail || error.message
          }\n\n` + `Please try again.`
        );
      }
    } else {
      // Fallback: just track file names locally
      const fileNames = files.map((f) => f.name);
      setUploadedFiles((prev) => [...prev, ...fileNames]);
    }

    addMessage(`📎 Uploaded: ${fileNames.join(", ")}`, "user");
    addBotMessage(
      "Great! I've received your documents. 📄\n\nWould you like to:\n• Upload more documents\n• Review your claim\n• Submit the claim\n\nType 'submit' to proceed or upload more files."
    );
  };

  const validateClaimData = () => {
    const required = [
      "policy_number",
      "claim_type",
      "claim_amount",
      "incident_date",
      "claimant_name",
      "claimant_email",
      "description",
    ];
    return required.every((field) => claimData[field]);
  };

  const submitClaim = async () => {
    try {
      const claimPayload = {
        ...claimData,
        documents: uploadedFiles,
      };

      addMessage("Submitting your claim...", "user");
      await addBotMessage("🔄 Processing your claim with AI agents...");

      const response = await claimsAPI.submitClaim(claimPayload);

      await addBotMessage(
        `✅ Claim submitted successfully!\n\n` +
          `📋 Claim ID: ${response.claim_id}\n` +
          `📊 Status: ${response.status}\n\n` +
          `Our AI agents are analyzing your claim. This typically takes 10-15 seconds.\n\n` +
          `Would you like to:\n` +
          `• View claim status\n` +
          `• Submit another claim\n` +
          `• View all claims`
      );

      // Reset for new claim
      setClaimData({});
      setUploadedFiles([]);
      setCurrentStep("completed");
    } catch (error) {
      console.log({ error });
      await addBotMessage(
        `❌ Sorry, there was an error submitting your claim: ${error.message}\n\n` +
          `Please try again or contact support.`
      );
    }
  };

  // Submit claim from collected data (guided flow)
  const submitCollectedClaim = async () => {
    try {
      // Convert collected data to claim payload format
      // Documents are already uploaded to backend, so we just need the paths
      const claimPayload = {
        policy_number: collectedClaimData.policy_number,
        claim_type: collectedClaimData.claim_type,
        claim_amount: collectedClaimData.claim_amount,
        incident_date: collectedClaimData.incident_date,
        description: collectedClaimData.description,
        claimant_name: collectedClaimData.claimant_name,
        claimant_email: collectedClaimData.claimant_email,
        documents: collectedClaimData.documents || [], // Use uploaded document paths
        temp_claim_id: tempClaimId, // Pass temp claim ID for file migration
      };

      addMessage("Submitting your claim...", "user");
      setIsTyping(true);
      await addBotMessage("🔄 Submitting your claim...");

      // Submit claim with temp_claim_id to migrate files
      const response = await claimsAPI.submitClaim(claimPayload);

      setIsTyping(false);
      await addBotMessage(
        `✅ **Claim Submitted Successfully!**\n\n` +
          `📋 **Claim ID:** ${response.claim_id}\n` +
          `📊 **Status:** ${response.status}\n\n` +
          `Your claim has been submitted and is being processed by our AI agents.\n\n` +
          `Would you like to:\n` +
          `• View claim status (go to Dashboard)\n` +
          `• Submit another claim (type 'new claim')\n` +
          `• View all claims (go to Dashboard)`
      );

      // Reset for new claim
      setCollectedClaimData({});
      setClaimData({});
      setUploadedFiles([]);
      setReadyToSubmit(false);
      setTempClaimId(null);
      setCurrentStep("policy_number");
    } catch (error) {
      setIsTyping(false);
      console.error("Submit claim error:", error);
      await addBotMessage(
        `❌ Sorry, there was an error submitting your claim: ${
          error.response?.data?.detail || error.message
        }\n\n` + `Please try again or contact support.`
      );
    }
  };

  const handleUserInput = async (input) => {
    const lowerInput = input.toLowerCase().trim();

    // If guided flow is enabled, use step-by-step question flow
    if (useGuidedFlow && useBackendAgent) {
      const guidedResponse = await handleGuidedSubmission(input);

      // If ready to submit and user confirms, submit the claim
      if (
        readyToSubmit &&
        (lowerInput === "yes" ||
          lowerInput === "submit" ||
          lowerInput === "confirm")
      ) {
        await submitCollectedClaim();
        return;
      }

      return;
    }

    // If backend agent is enabled (but not guided flow), use intelligent responses
    if (useBackendAgent) {
      // Handle special commands that still need local processing
      if (lowerInput === "submit" && validateClaimData()) {
        await submitClaim();
        return;
      }

      if (lowerInput === "review") {
        const review = `
📋 **Claim Summary:**
━━━━━━━━━━━━━━━━━━━
🆔 Policy: ${claimData.policy_number || "N/A"}
📝 Type: ${claimData.claim_type || "N/A"}
💰 Amount: $${claimData.claim_amount || "0"}
📅 Date: ${claimData.incident_date || "N/A"}
👤 Name: ${claimData.claimant_name || "N/A"}
📧 Email: ${claimData.claimant_email || "N/A"}
📄 Description: ${claimData.description || "N/A"}
📎 Documents: ${uploadedFiles.length} file(s)

Type 'submit' to proceed or continue editing.
        `;
        await addBotMessage(review);
        return;
      }

      // For all other inputs, use backend AI agent
      const aiResponse = await getAIResponse(input);

      // If AI detected intent to submit claim and we have data, offer to submit
      if (aiResponse?.intent === "submit_claim" && validateClaimData()) {
        await addBotMessage(
          "I see you're ready to submit! Would you like me to submit your claim now? Type 'yes' to confirm or 'review' to check your information first."
        );
      }

      return;
    }

    // Fallback to original local logic if backend agent is disabled
    // Process based on current step
    switch (currentStep) {
      case "policy_number":
        setClaimData((prev) => ({ ...prev, policy_number: input }));
        await addBotMessage(
          `Perfect! Policy ${input} recorded. ✓\n\n` +
            `Now, what type of claim is this?\n\n` +
            `1️⃣ Health\n2️⃣ Auto\n3️⃣ Home\n4️⃣ Life\n5️⃣ Travel\n\n` +
            `Type the number or name.`
        );
        setCurrentStep("claim_type");
        break;

      case "claim_type":
        const typeMap = {
          1: "health",
          health: "health",
          2: "auto",
          auto: "auto",
          car: "auto",
          vehicle: "auto",
          3: "home",
          home: "home",
          house: "home",
          property: "home",
          4: "life",
          life: "life",
          5: "travel",
          travel: "travel",
        };
        const claimType = typeMap[lowerInput];

        if (claimType) {
          setClaimData((prev) => ({ ...prev, claim_type: claimType }));
          await addBotMessage(
            `Got it! ${
              claimType.charAt(0).toUpperCase() + claimType.slice(1)
            } claim. ✓\n\n` + `What is the claim amount in USD? (Numbers only)`
          );
          setCurrentStep("claim_amount");
        } else {
          await addBotMessage(
            `❌ Please enter a valid claim type (1-5 or type name).`
          );
        }
        break;

      case "claim_amount":
        const amount = parseFloat(input.replace(/[^0-9.]/g, ""));
        if (amount && amount > 0) {
          setClaimData((prev) => ({ ...prev, claim_amount: amount }));
          await addBotMessage(
            `Amount recorded: $${amount.toLocaleString()} ✓\n\n` +
              `When did the incident occur? (YYYY-MM-DD format)\n` +
              `Example: 2025-11-15`
          );
          setCurrentStep("incident_date");
        } else {
          await addBotMessage(`❌ Please enter a valid amount (numbers only).`);
        }
        break;

      case "incident_date":
        // Basic date validation
        if (/^\d{4}-\d{2}-\d{2}$/.test(input)) {
          setClaimData((prev) => ({ ...prev, incident_date: input }));
          await addBotMessage(
            `Date recorded: ${input} ✓\n\n` + `What is your full name?`
          );
          setCurrentStep("claimant_name");
        } else {
          await addBotMessage(
            `❌ Please enter date in YYYY-MM-DD format (e.g., 2025-11-15)`
          );
        }
        break;

      case "claimant_name":
        setClaimData((prev) => ({ ...prev, claimant_name: input }));
        await addBotMessage(
          `Thank you, ${input}! ✓\n\n` + `What is your email address?`
        );
        setCurrentStep("claimant_email");
        break;

      case "claimant_email":
        if (input.includes("@")) {
          setClaimData((prev) => ({ ...prev, claimant_email: input }));
          await addBotMessage(
            `Email recorded: ${input} ✓\n\n` +
              `Please describe the incident in detail.\n` +
              `Include what happened, where, and any relevant circumstances.`
          );
          setCurrentStep("description");
        } else {
          await addBotMessage(`❌ Please enter a valid email address.`);
        }
        break;

      case "description":
        setClaimData((prev) => ({ ...prev, description: input }));
        await addBotMessage(
          `Description recorded! ✓\n\n` +
            `Now, please upload supporting documents:\n\n` +
            `📄 For ${claimData.claim_type} claims, we typically need:\n` +
            (claimData.claim_type === "health"
              ? `• Medical receipts\n• Hospital bills\n• Prescription forms\n• Lab reports`
              : claimData.claim_type === "auto"
              ? `• Police report\n• Photos of damage\n• Repair estimates\n• Accident report`
              : claimData.claim_type === "home"
              ? `• Photos of damage\n• Repair invoices\n• Police report (if applicable)\n• Appraisal documents`
              : `• Supporting documentation\n• Receipts\n• Official reports`) +
            `\n\nClick the 📎 button below to upload files.`
        );
        setCurrentStep("documents");
        break;

      case "documents":
        if (lowerInput === "skip") {
          await addBotMessage(
            `⚠️ Proceeding without documents. This may affect claim processing.\n\n` +
              `Type 'review' to see your claim summary or 'submit' to proceed.`
          );
        }
        break;

      case "completed":
        if (lowerInput.includes("status")) {
          await addBotMessage(
            `Please go to the Dashboard tab to view claim status.`
          );
        } else if (
          lowerInput.includes("another") ||
          lowerInput.includes("new")
        ) {
          setClaimData({});
          setUploadedFiles([]);
          setCurrentStep("policy_number");
          await addBotMessage(
            `Great! Let's start a new claim. What's your policy number?`
          );
        } else if (lowerInput.includes("all") || lowerInput.includes("list")) {
          await addBotMessage(
            `Please switch to the Dashboard tab to view all claims.`
          );
        }
        break;

      default:
        await addBotMessage(
          `I didn't understand that. Type 'help' for assistance.`
        );
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userInput = inputValue.trim();
    addMessage(userInput, "user");
    setInputValue("");

    // Keep focus on input field after submitting
    setTimeout(() => {
      chatInputRef.current?.focus();
    }, 50);

    await handleUserInput(userInput);
  };

  return (
    <div className="chat-container">
      <div className="chat-header">
        <div className="chat-header-content">
          <div className="bot-avatar">🤖</div>
          <div>
            <h3>AI Claims Assistant</h3>
            <p className="status-indicator">
              <span className="status-dot"></span>{" "}
              {useBackendAgent ? "AI Agent Active" : "Online"}
            </p>
          </div>
        </div>
        {useBackendAgent && (
          <div
            style={{
              marginLeft: "auto",
              fontSize: "0.75rem",
              color: "#666",
              paddingTop: "0.5rem",
            }}
          >
            ✨ Powered by Gemini AI
          </div>
        )}
      </div>

      <div className="chat-messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.type}`}>
            <div className="message-content">
              <div className="message-avatar">
                {message.type === "bot" ? "🤖" : "👤"}
              </div>
              <div className="message-bubble">
                <div className="message-text">
                  <FormattedText text={message.text} />
                </div>
                <div className="message-time">
                  {message.timestamp.toLocaleTimeString([], {
                    hour: "2-digit",
                    minute: "2-digit",
                  })}
                </div>
              </div>
            </div>
          </div>
        ))}

        {isTyping && (
          <div className="message bot">
            <div className="message-content">
              <div className="message-avatar">🤖</div>
              <div className="message-bubble typing">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Submit Button - Show when ready */}
      {readyToSubmit && (
        <div
          style={{
            padding: "1rem",
            backgroundColor: "#f0f9ff",
            borderTop: "2px solid #3b82f6",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            marginTop: "auto",
          }}
        >
          <div>
            <strong style={{ color: "#1e40af", display: "block" }}>
              ✓ All information collected!
            </strong>
            <p
              style={{
                margin: "0.25rem 0 0 0",
                fontSize: "0.875rem",
                color: "#64748b",
              }}
            >
              Ready to submit your claim
            </p>
          </div>
          <button
            onClick={submitCollectedClaim}
            disabled={isTyping}
            style={{
              padding: "0.75rem 1.5rem",
              fontSize: "1rem",
              fontWeight: "600",
              borderRadius: "8px",
              border: "none",
              cursor: isTyping ? "not-allowed" : "pointer",
              backgroundColor: isTyping ? "#9ca3af" : "#3b82f6",
              color: "white",
              transition: "all 0.2s",
            }}
            onMouseOver={(e) => {
              if (!isTyping) e.target.style.backgroundColor = "#2563eb";
            }}
            onMouseOut={(e) => {
              if (!isTyping) e.target.style.backgroundColor = "#3b82f6";
            }}
          >
            {isTyping ? "⏳ Submitting..." : "📤 Submit Claim"}
          </button>
        </div>
      )}

      <div className="chat-input-container">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          multiple
          accept="image/*,.pdf"
          style={{ display: "none" }}
        />

        <button
          className="attach-button"
          onClick={() => fileInputRef.current?.click()}
          title="Upload documents"
        >
          📎
        </button>

        <form onSubmit={handleSubmit} className="chat-input-form">
          <input
            ref={chatInputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder={
              readyToSubmit
                ? "Type 'yes' to confirm or click Submit button..."
                : "Type your answer..."
            }
            className="chat-input"
            autoFocus
            disabled={isTyping}
          />
          <button type="submit" className="send-button" disabled={isTyping}>
            {isTyping ? "..." : "➤"}
          </button>
        </form>
      </div>

      {uploadedFiles.length > 0 && (
        <div className="uploaded-files-preview">
          {uploadedFiles.map((file, index) => (
            <div key={index} className="file-chip">
              📄 {file}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default ChatInterface;
