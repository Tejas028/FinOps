import React, { useEffect, useState } from 'react';
import { getAnomalyDetails } from '../../api/anomalies';
import type { AnomalyListItem } from '../../types';
import { SeverityBadge } from '../shared/SeverityBadge';
import { Skeleton } from '../shared/Skeleton';
import { X } from 'lucide-react';

interface AnomalyDrawerProps {
  anomalyId: string | null;
  onClose: () => void;
}

export const AnomalyDrawer: React.FC<AnomalyDrawerProps> = ({ anomalyId, onClose }) => {
  const [detail, setDetail] = useState<AnomalyListItem | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!anomalyId) {
      setDetail(null);
      return;
    }
    const fetchDetail = async () => {
      setLoading(true);
      try {
        const data = await getAnomalyDetails(anomalyId);
        setDetail(data);
      } catch (e) {
        console.error("Failed to load anomaly detail", e);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [anomalyId]);

  if (!anomalyId) return null;

  return (
    <>
      <div 
        style={{
          position: 'fixed',
          top: 0,
          left: 0,
          width: '100vw',
          height: '100vh',
          background: 'rgba(0,0,0,0.5)',
          zIndex: 40,
          opacity: anomalyId ? 1 : 0,
          transition: 'opacity 0.2s',
        }} 
        onClick={onClose}
      />
      <div style={{
        position: 'fixed',
        top: 0,
        right: 0,
        width: '420px',
        height: '100vh',
        background: 'var(--bg-surface)',
        borderLeft: '1px solid var(--border)',
        zIndex: 50,
        transform: anomalyId ? 'translateX(0)' : 'translateX(100%)',
        transition: 'transform 0.3s ease',
        display: 'flex',
        flexDirection: 'column',
      }}>
        <div style={{
          padding: '24px',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 600 }}>Anomaly Detail</h2>
          <button 
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: 'var(--text-secondary)',
              cursor: 'pointer'
            }}
          >
            <X size={20} />
          </button>
        </div>

        <div style={{ padding: '24px', flex: 1, overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '24px' }}>
          {loading || !detail ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              <Skeleton height="60px" />
              <Skeleton height="100px" />
              <Skeleton height="100px" />
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <SeverityBadge severity={detail.severity} />
                <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>
                  Detected via {detail.detection_method}
                </span>
              </div>

              <div style={{ background: 'var(--bg-elevated)', border: '1px solid var(--border)', borderRadius: '8px', padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <div>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Actual Cost</div>
                    <div style={{ fontSize: '20px', color: 'var(--text-primary)', fontWeight: 600 }}>${detail.actual_cost.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '4px' }}>Expected</div>
                    <div style={{ fontSize: '20px', color: 'var(--text-secondary)' }}>${detail.expected_cost.toLocaleString(undefined, { maximumFractionDigits: 2 })}</div>
                  </div>
                </div>

                <div style={{ borderTop: '1px dashed var(--border)', paddingTop: '16px', display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Deviation</span>
                  <span style={{ fontSize: '14px', color: 'var(--red)', fontWeight: 500 }}>+{detail.deviation_pct.toFixed(1)}%</span>
                </div>
                {detail.z_score !== null && (
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ fontSize: '13px', color: 'var(--text-secondary)' }}>Z-Score</span>
                    <span style={{ fontSize: '14px', color: 'var(--text-primary)' }}>{detail.z_score.toFixed(2)}</span>
                  </div>
                )}
              </div>

              <div>
                <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: 600, color: 'var(--text-primary)' }}>Context</h3>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '13px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Service</span>
                    <span style={{ color: 'var(--text-primary)' }}>{detail.service}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Cloud Provider</span>
                    <span style={{ color: 'var(--text-primary)', textTransform: 'uppercase' }}>{detail.cloud_provider}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--text-secondary)' }}>Usage Date</span>
                    <span style={{ color: 'var(--text-primary)' }}>{detail.usage_date}</span>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </>
  );
};
