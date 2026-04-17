import React, { useState, useEffect } from 'react';
import { Sparkles } from 'lucide-react';
import axios from 'axios';

interface AIInsightPanelProps {
  endpoint: string;
  payload: any;
  trigger: string;
  className?: string;
}

export const AIInsightPanel: React.FC<AIInsightPanelProps> = ({ 
  endpoint, 
  payload, 
  trigger,
  className = ""
}) => {
  const [insight, setInsight] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(false);

  useEffect(() => {
    const fetchInsight = async () => {
      if (!payload) {
        setInsight(null);
        setError(false);
        return;
      }
      
      setLoading(true);
      setError(false);
      setInsight(null); // Clear previous insight while loading new one
      
      try {
        const baseUrl = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
        const response = await axios.post(`${baseUrl}${endpoint}`, payload);
        setInsight(response.data.insight);
      } catch (err) {
        console.error('AI Insight fetch failed:', err);
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchInsight();
  }, [trigger, endpoint, payload]);

  if (!payload && !loading) return null;

  return (
    <div className={className} style={{
      background: '#13131A',
      border: '1px solid #2A2A3D',
      borderLeft: '3px solid #F59E0B',
      borderRadius: '8px',
      padding: '14px 16px',
      marginTop: '12px'
    }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '12px'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Sparkles size={14} color="#F59E0B" />
          <span style={{
            color: '#7B7B96',
            fontSize: '11px',
            letterSpacing: '0.08em',
            textTransform: 'uppercase'
          }}>
            AI Insight
          </span>
        </div>
        <span style={{ color: '#7B7B96', fontSize: '10px' }}>Powered by Groq</span>
      </div>

      <div style={{ minHeight: '40px' }}>
        {loading ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <div className="shimmer-line" style={{ width: '100%' }} />
            <div className="shimmer-line" style={{ width: '85%' }} />
            <div className="shimmer-line" style={{ width: '60%' }} />
          </div>
        ) : error ? (
          <div style={{ color: '#7B7B96', fontSize: '12px', fontStyle: 'italic' }}>
            AI insights not available
          </div>
        ) : (
          <div style={{ color: '#C8C8D8', fontSize: '13px', lineHeight: '1.6' }}>
            {insight}
          </div>
        )}
      </div>

      <style>{`
        .shimmer-line {
          height: 12px;
          border-radius: 4px;
          background: linear-gradient(90deg, #1C1C27 25%, #2A2A3D 50%, #1C1C27 75%);
          background-size: 200% 100%;
          animation: shimmer 1.5s infinite;
        }
        @keyframes shimmer {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  );
};
