import React from 'react';

interface SeverityBadgeProps {
  severity: "low" | "medium" | "high" | "critical" | string;
}

export const SeverityBadge: React.FC<SeverityBadgeProps> = ({ severity }) => {
  let background = 'transparent';
  let color = 'var(--text-primary)';
  let opacity = 1;
  let fontWeight = 400;

  switch (severity.toLowerCase()) {
    case 'low':
      background = 'var(--accent-dim)';
      color = 'var(--accent)';
      break;
    case 'medium':
      background = 'var(--accent-med)';
      color = 'var(--bg-base)';
      opacity = 0.8;
      break;
    case 'high':
      /* Use full accent at 60% approx via rgb breakdown, or rely on CSS classes if we had them. 
         Wait, let's use a solid color but we only have --accent-full. 
         We'll emulate 60% opacity of full accent on --bg-surface: */
      background = 'color-mix(in srgb, var(--accent-full) 60%, transparent)';
      color = 'var(--bg-base)';
      break;
    case 'critical':
      background = 'var(--accent-full)';
      color = 'var(--bg-base)';
      fontWeight = 600;
      break;
    default:
      background = 'var(--bg-elevated)';
      color = 'var(--text-secondary)';
  }

  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2px 8px',
      borderRadius: '12px',
      fontSize: '11px',
      textTransform: 'uppercase',
      letterSpacing: '0.5px',
      background,
      color,
      opacity,
      fontWeight
    }}>
      {severity}
    </span>
  );
};
