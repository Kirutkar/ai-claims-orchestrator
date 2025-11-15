import React, { useState } from 'react';
import { Bot } from 'lucide-react';
import ClaimForm from './components/ClaimForm';
import Dashboard from './components/Dashboard';

function App() {
  const [activeTab, setActiveTab] = useState('submit');

  return (
    <div className="app">
      <header className="header">
        <div className="container">
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <Bot size={48} />
            <div>
              <h1>AI Claims Orchestrator</h1>
              <p>Intelligent Insurance Claims Processing with Multi-Agent AI</p>
            </div>
          </div>
        </div>
      </header>

      <div className="container">
        <div className="tabs">
          <button
            className={`tab-button ${activeTab === 'submit' ? 'active' : ''}`}
            onClick={() => setActiveTab('submit')}
          >
            Submit Claim
          </button>
          <button
            className={`tab-button ${activeTab === 'dashboard' ? 'active' : ''}`}
            onClick={() => setActiveTab('dashboard')}
          >
            Claims Dashboard
          </button>
        </div>

        {activeTab === 'submit' && (
          <ClaimForm 
            onClaimSubmitted={(response) => {
              // Optionally switch to dashboard after submission
              setTimeout(() => setActiveTab('dashboard'), 3000);
            }}
          />
        )}

        {activeTab === 'dashboard' && <Dashboard />}
      </div>
    </div>
  );
}

export default App;
