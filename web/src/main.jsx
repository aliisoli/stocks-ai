
import React, { useState, useRef, useEffect } from "react";
import { createRoot } from "react-dom/client";
import { marked } from "marked";

function App() {
  const [ticker, setTicker] = useState("NVDA");
  const [status, setStatus] = useState("");
  const [news, setNews] = useState([]);
  const [summary, setSummary] = useState(null);
  const [report, setReport] = useState("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [isCompleted, setIsCompleted] = useState(false);
  const esRef = useRef(null);

  // Popular tech stocks for dropdown
  const techStocks = [
    { value: "NVDA", label: "NVIDIA Corp (NVDA)" },
    { value: "AAPL", label: "Apple Inc (AAPL)" },
    { value: "MSFT", label: "Microsoft Corp (MSFT)" },
    { value: "GOOGL", label: "Alphabet Inc (GOOGL)" },
    { value: "AMZN", label: "Amazon.com Inc (AMZN)" },
    { value: "TSLA", label: "Tesla Inc (TSLA)" },
    { value: "META", label: "Meta Platforms Inc (META)" },
    { value: "NFLX", label: "Netflix Inc (NFLX)" },
    { value: "AMD", label: "Advanced Micro Devices (AMD)" },
    { value: "CRM", label: "Salesforce Inc (CRM)" },
    { value: "ADBE", label: "Adobe Inc (ADBE)" },
    { value: "INTC", label: "Intel Corp (INTC)" }
  ];

  // Cleanup EventSource on component unmount
  useEffect(() => {
    return () => {
      if (esRef.current) {
        esRef.current.close();
        esRef.current = null;
      }
    };
  }, []);

  const start = () => {
    // Close existing connection
    if (esRef.current) {
      esRef.current.close();
      esRef.current = null;
    }

    setIsConnecting(true);
    setIsCompleted(false);
    setStatus("Connecting...");
    setNews([]);
    setSummary(null);
    setReport("");

    // Get server URL from environment or use default
    const serverUrl = import.meta.env.VITE_SERVER_URL || "http://localhost:8000";
    // Remove sites parameter since it's not needed anymore
    const qs = new URLSearchParams({ ticker }).toString();
    const es = new EventSource(`${serverUrl}/api/stream?${qs}`);
    esRef.current = es;

    es.onopen = () => {
      setStatus("Connected, analyzing...");
      setIsConnecting(false);
    };

    es.onmessage = (evt) => {
      try {
        const { event, data } = JSON.parse(evt.data);
        if (event === "status") setStatus(data.message);
        if (event === "news") {
          setNews(prev => [...prev, data]);
        }
        if (event === "data_summary") setSummary(data);
        if (event === "report") setReport(data.markdown);
        if (event === "error") {
          setStatus("Error: " + data.message);
          setIsConnecting(false);
          es.close();
          esRef.current = null;
        }
        if (event === "done") {
          setStatus("Analysis Complete");
          setIsConnecting(false);
          setIsCompleted(true);
          es.close();
          esRef.current = null;
        }
      } catch (e) {
        console.error("Parse error", e);
        setStatus("Error parsing response");
        setIsConnecting(false);
        es.close();
        esRef.current = null;
      }
    };

    es.onerror = (error) => {
      console.error("EventSource error:", error);
      // Only show connection lost if we haven't completed successfully
      if (!isCompleted) {
        setStatus("Connection lost");
      }
      setIsConnecting(false);
      es.close();
      esRef.current = null;
    };
  };

  // Get news summary from the first item with content
  const getNewsSummary = () => {
    if (!news || news.length === 0) {
      return null;
    }
    
    // Look for a news item with substantial content
    const summaryItem = news.find(item => 
      item.snippet && item.snippet.length > 100
    ) || news[0];
    
    return summaryItem;
  };

  const newsSummary = getNewsSummary();

  return (
    <div className="wrap">
      <h1>AutoGen Stock Analyzer</h1>
      <div style={{marginTop: 6, color: '#aab2bf', fontSize: 14, lineHeight: 1.6}}>
        <div>
          This app orchestrates three lightweight agents to analyze a stock when you click <strong>Analyze</strong>:
        </div>
        <ul style={{margin: '8px 0 0 18px', padding: 0}}>
          <li><strong>Research Agent</strong>: Retrieves and summarizes recent News & Market Intelligence.</li>
          <li><strong>Market Data Agent</strong>: Fetches OHLC and a quick fundamentals snapshot.</li>
          <li><strong>Analyst Agent</strong>: Synthesizes a concise memo from news and data.</li>
        </ul>
        <div style={{
          marginTop: 10,
          fontSize: 12,
          color: '#aab2bf',
          background: '#1b2330',
          border: '1px solid #222834',
          borderRadius: 8,
          padding: '8px 12px'
        }}>
          Disclaimer: This is not financial advice. The application is for skill demonstration purposes only and was built by Aliakbar.
        </div>
      </div>
      <div className="card" style={{marginTop:12}}>
        <div className="row">
          <select 
            value={ticker} 
            onChange={e=>setTicker(e.target.value)} 
            className="mono"
            disabled={isConnecting}
            style={{minWidth: 250, padding: 8}}
          >
            {techStocks.map(stock => (
              <option key={stock.value} value={stock.value}>
                {stock.label}
              </option>
            ))}
          </select>
          <button 
            onClick={start} 
            disabled={isConnecting}
            style={{marginLeft: 12}}
          >
            {isConnecting ? "Analyzing..." : "Analyze"}
          </button>
          <span className="pill" style={{marginLeft: 12}}>{status}</span>
        </div>
      </div>

      <div className="card" style={{marginTop:16}}>
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'12px'}}>
          <h3 style={{margin: 0}}>News & Market Intelligence</h3>
          <span style={{fontSize: 12, color: '#aab2bf', background:'#1b2330', border:'1px solid #222834', padding:'4px 8px', borderRadius: 999}}>
            Retrieved via Research Agent
          </span>
        </div>
        
        {!newsSummary ? (
          <div style={{
            opacity: 0.7,
            padding: '20px',
            textAlign: 'center',
            fontStyle: 'italic'
          }}>
            Awaiting results…
          </div>
        ) : (
          <div style={{
            backgroundColor: '#151922',
            border: '1px solid #222834',
            borderRadius: '12px'
          }}>
            {/* Header */}
            <div style={{
              backgroundColor: '#1b2330',
              padding: '14px 18px',
              borderBottom: '1px solid #222834'
            }}>
              <h4 style={{
                margin: 0,
                fontSize: '16px',
                fontWeight: 600
              }}>
                {newsSummary.title}
              </h4>
            </div>
            
            {/* Content */}
            <div style={{
              padding: '18px',
              lineHeight: 1.7,
              fontSize: '14px'
            }}>
              <div style={{
                whiteSpace: 'pre-wrap',
                wordWrap: 'break-word'
              }}>
                {newsSummary.snippet}
              </div>
              
              {newsSummary.url && (
                <div style={{
                  marginTop: '14px',
                  paddingTop: '14px',
                  borderTop: '1px solid #222834'
                }}>
                  <a 
                    href={newsSummary.url} 
                    target="_blank" 
                    rel="noreferrer"
                    style={{
                      fontSize: '13px',
                      fontWeight: 500
                    }}
                  >
                    🔗 View Source
                  </a>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      <div className="card" style={{marginTop:16}}>
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'12px'}}>
          <h3 style={{margin: 0}}>Market Data Snapshot</h3>
          <span style={{fontSize: 12, color: '#aab2bf', background:'#1b2330', border:'1px solid #222834', padding:'4px 8px', borderRadius: 999}}>
            Retrieved via Market Data Agent
          </span>
        </div>
        {summary ? (
          <div style={{
            backgroundColor: '#151922',
            padding: '16px',
            borderRadius: '8px',
            border: '1px solid #222834',
            overflow: 'auto'
          }}>
            <pre className="mono stream" style={{
              margin: 0,
              fontSize: '12px',
              lineHeight: '1.4'
            }}>
              {JSON.stringify(summary, null, 2)}
            </pre>
          </div>
        ) : (
          <div style={{
            opacity: 0.7,
            padding: '20px',
            textAlign: 'center',
            fontStyle: 'italic'
          }}>
            Awaiting results…
          </div>
        )}
      </div>

      <div className="card" style={{marginTop:16}}>
        <div style={{display:'flex', justifyContent:'space-between', alignItems:'center', marginBottom:'12px'}}>
          <h3 style={{margin: 0}}>Analyst Memo</h3>
          <span style={{fontSize: 12, color: '#aab2bf', background:'#1b2330', border:'1px solid #222834', padding:'4px 8px', borderRadius: 999}}>
            Drafted by Analyst Agent
          </span>
        </div>
        <div style={{
          backgroundColor: '#151922',
          border: '1px solid #222834',
          borderRadius: '8px',
          padding: report ? '20px' : '0',
          minHeight: report ? 'auto' : '60px',
          display: 'flex',
          alignItems: report ? 'flex-start' : 'center',
          justifyContent: report ? 'flex-start' : 'center'
        }}>
          {report ? (
            <div 
              className="stream" 
              style={{
                lineHeight: '1.6'
              }}
              dangerouslySetInnerHTML={{__html: marked.parse(report)}} 
            />
          ) : (
            <div style={{
              opacity: 0.7,
              fontStyle: 'italic',
              textAlign: 'center'
            }}>
              Awaiting results…
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
