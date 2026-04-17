import React from 'react';

interface SeverityBadgeProps {
  severity: "low" | "medium" | "high" | "critical" | string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity }) => {
  const s = (severity || "LOW").toUpperCase();
  
  const styles: Record<string, React.CSSProperties> = {
    LOW: {
      background: 'rgba(123, 123, 150, 0.15)',
      color: '#7B7B96',
      border: '1px solid rgba(123, 123, 150, 0.3)',
    },
    MEDIUM: {
      background: 'rgba(217, 119, 6, 0.15)',
      color: '#D97706',
      border: '1px solid rgba(217, 119, 6, 0.3)',
    },
    HIGH: {
      background: 'rgba(245, 158, 11, 0.2)',
      color: '#F59E0B',
      border: '1px solid rgba(245, 158, 11, 0.4)',
    },
    CRITICAL: {
      background: '#F59E0B',
      color: '#0A0A0F',
      border: 'none',
      fontWeight: 600,
    }
  };

  const currentStyle = styles[s] || styles.LOW;

  return (
    <span style={{
      ...currentStyle,
      padding: "2px 8px",
      borderRadius: "4px",
      fontSize: "11px",
      fontWeight: currentStyle.fontWeight || 500,
      letterSpacing: "0.05em",
      textTransform: "uppercase",
      display: "inline-block",
      fontFamily: "monospace",
    }}>
      {s}
    </span>
  );
};
