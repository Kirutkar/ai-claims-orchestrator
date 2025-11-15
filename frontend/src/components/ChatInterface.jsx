import React, { useState, useRef, useEffect } from 'react';
import claimsAPI from '../services/api';

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'bot',
      text: "👋 Hello! I'm your AI Claims Assistant. I'll help you submit your insurance claim. Let's start with your policy number.",
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [claimData, setClaimData] = useState({});
  const [currentStep, setCurrentStep] = useState('policy_number');
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const addMessage = (text, type = 'user', options = {}) => {
    const newMessage = {
      id: messages.length + 1,
      type,
      text,
      timestamp: new Date(),
      ...options
    };
    setMessages(prev => [...prev, newMessage]);
  };

  const addBotMessage = async (text, delay = 800) => {
    setIsTyping(true);
    await new Promise(resolve => setTimeout(resolve, delay));
    setIsTyping(false);
    addMessage(text, 'bot');
  };

  const handleFileUpload = (event) => {
    const files = Array.from(event.target.files);
    const fileNames = files.map(f => f.name);
    setUploadedFiles(prev => [...prev, ...fileNames]);
    
    addMessage(`📎 Uploaded: ${fileNames.join(', ')}`, 'user');
    addBotMessage(
      "Great! I've received your documents. 📄\n\nWould you like to:\n• Upload more documents\n• Review your claim\n• Submit the claim\n\nType 'submit' to proceed or upload more files."
    );
  };

  const validateClaimData = () => {
    const required = ['policy_number', 'claim_type', 'claim_amount', 'incident_date', 'claimant_name', 'claimant_email', 'description'];
    return required.every(field => claimData[field]);
  };

  const submitClaim = async () => {
    try {
      const claimPayload = {
        ...claimData,
        documents: uploadedFiles
      };

      addMessage('Submitting your claim...', 'user');
      await addBotMessage('🔄 Processing your claim with AI agents...');

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
      setCurrentStep('completed');

    } catch (error) {
      await addBotMessage(
        `❌ Sorry, there was an error submitting your claim: ${error.message}\n\n` +
        `Please try again or contact support.`
      );
    }
  };

  const handleUserInput = async (input) => {
    const lowerInput = input.toLowerCase().trim();

    // Handle special commands
    if (lowerInput === 'submit' && validateClaimData()) {
      await submitClaim();
      return;
    }

    if (lowerInput === 'review') {
      const review = `
📋 **Claim Summary:**
━━━━━━━━━━━━━━━━━━━
🆔 Policy: ${claimData.policy_number || 'N/A'}
📝 Type: ${claimData.claim_type || 'N/A'}
💰 Amount: $${claimData.claim_amount || '0'}
📅 Date: ${claimData.incident_date || 'N/A'}
👤 Name: ${claimData.claimant_name || 'N/A'}
📧 Email: ${claimData.claimant_email || 'N/A'}
📄 Description: ${claimData.description || 'N/A'}
📎 Documents: ${uploadedFiles.length} file(s)

Type 'submit' to proceed or continue editing.
      `;
      await addBotMessage(review);
      return;
    }

    // Process based on current step
    switch (currentStep) {
      case 'policy_number':
        setClaimData(prev => ({ ...prev, policy_number: input }));
        await addBotMessage(
          `Perfect! Policy ${input} recorded. ✓\n\n` +
          `Now, what type of claim is this?\n\n` +
          `1️⃣ Health\n2️⃣ Auto\n3️⃣ Home\n4️⃣ Life\n5️⃣ Travel\n\n` +
          `Type the number or name.`
        );
        setCurrentStep('claim_type');
        break;

      case 'claim_type':
        const typeMap = {
          '1': 'health', 'health': 'health',
          '2': 'auto', 'auto': 'auto', 'car': 'auto', 'vehicle': 'auto',
          '3': 'home', 'home': 'home', 'house': 'home', 'property': 'home',
          '4': 'life', 'life': 'life',
          '5': 'travel', 'travel': 'travel'
        };
        const claimType = typeMap[lowerInput];
        
        if (claimType) {
          setClaimData(prev => ({ ...prev, claim_type: claimType }));
          await addBotMessage(
            `Got it! ${claimType.charAt(0).toUpperCase() + claimType.slice(1)} claim. ✓\n\n` +
            `What is the claim amount in USD? (Numbers only)`
          );
          setCurrentStep('claim_amount');
        } else {
          await addBotMessage(`❌ Please enter a valid claim type (1-5 or type name).`);
        }
        break;

      case 'claim_amount':
        const amount = parseFloat(input.replace(/[^0-9.]/g, ''));
        if (amount && amount > 0) {
          setClaimData(prev => ({ ...prev, claim_amount: amount }));
          await addBotMessage(
            `Amount recorded: $${amount.toLocaleString()} ✓\n\n` +
            `When did the incident occur? (YYYY-MM-DD format)\n` +
            `Example: 2025-11-15`
          );
          setCurrentStep('incident_date');
        } else {
          await addBotMessage(`❌ Please enter a valid amount (numbers only).`);
        }
        break;

      case 'incident_date':
        // Basic date validation
        if (/^\d{4}-\d{2}-\d{2}$/.test(input)) {
          setClaimData(prev => ({ ...prev, incident_date: input }));
          await addBotMessage(
            `Date recorded: ${input} ✓\n\n` +
            `What is your full name?`
          );
          setCurrentStep('claimant_name');
        } else {
          await addBotMessage(`❌ Please enter date in YYYY-MM-DD format (e.g., 2025-11-15)`);
        }
        break;

      case 'claimant_name':
        setClaimData(prev => ({ ...prev, claimant_name: input }));
        await addBotMessage(
          `Thank you, ${input}! ✓\n\n` +
          `What is your email address?`
        );
        setCurrentStep('claimant_email');
        break;

      case 'claimant_email':
        if (input.includes('@')) {
          setClaimData(prev => ({ ...prev, claimant_email: input }));
          await addBotMessage(
            `Email recorded: ${input} ✓\n\n` +
            `Please describe the incident in detail.\n` +
            `Include what happened, where, and any relevant circumstances.`
          );
          setCurrentStep('description');
        } else {
          await addBotMessage(`❌ Please enter a valid email address.`);
        }
        break;

      case 'description':
        setClaimData(prev => ({ ...prev, description: input }));
        await addBotMessage(
          `Description recorded! ✓\n\n` +
          `Now, please upload supporting documents:\n\n` +
          `📄 For ${claimData.claim_type} claims, we typically need:\n` +
          (claimData.claim_type === 'health' ? 
            `• Medical receipts\n• Hospital bills\n• Prescription forms\n• Lab reports` :
          claimData.claim_type === 'auto' ?
            `• Police report\n• Photos of damage\n• Repair estimates\n• Accident report` :
          claimData.claim_type === 'home' ?
            `• Photos of damage\n• Repair invoices\n• Police report (if applicable)\n• Appraisal documents` :
            `• Supporting documentation\n• Receipts\n• Official reports`) +
          `\n\nClick the 📎 button below to upload files.`
        );
        setCurrentStep('documents');
        break;

      case 'documents':
        if (lowerInput === 'skip') {
          await addBotMessage(
            `⚠️ Proceeding without documents. This may affect claim processing.\n\n` +
            `Type 'review' to see your claim summary or 'submit' to proceed.`
          );
        }
        break;

      case 'completed':
        if (lowerInput.includes('status')) {
          await addBotMessage(`Please go to the Dashboard tab to view claim status.`);
        } else if (lowerInput.includes('another') || lowerInput.includes('new')) {
          setClaimData({});
          setUploadedFiles([]);
          setCurrentStep('policy_number');
          await addBotMessage(`Great! Let's start a new claim. What's your policy number?`);
        } else if (lowerInput.includes('all') || lowerInput.includes('list')) {
          await addBotMessage(`Please switch to the Dashboard tab to view all claims.`);
        }
        break;

      default:
        await addBotMessage(`I didn't understand that. Type 'help' for assistance.`);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    const userInput = inputValue.trim();
    addMessage(userInput, 'user');
    setInputValue('');

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
              <span className="status-dot"></span> Online
            </p>
          </div>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map(message => (
          <div key={message.id} className={`message ${message.type}`}>
            <div className="message-content">
              <div className="message-avatar">
                {message.type === 'bot' ? '🤖' : '👤'}
              </div>
              <div className="message-bubble">
                <div className="message-text">{message.text}</div>
                <div className="message-time">
                  {message.timestamp.toLocaleTimeString([], { 
                    hour: '2-digit', 
                    minute: '2-digit' 
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

      <div className="chat-input-container">
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileUpload}
          multiple
          accept="image/*,.pdf"
          style={{ display: 'none' }}
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
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your message..."
            className="chat-input"
            autoFocus
          />
          <button type="submit" className="send-button">
            ➤
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
