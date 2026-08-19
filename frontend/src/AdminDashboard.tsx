import { useState, useEffect } from 'react';

export function AdminDashboard() {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    fetch(`${import.meta.env.PROD ? '' : 'http://localhost:8000'}/api/admin/accuracy`)
      .then(res => res.json())
      .then(d => {
        if (d.error) setError(d.error);
        else setData(d);
        setLoading(false);
      })
      .catch(e => {
        setError(e.message);
        setLoading(false);
      });
  }, []);

  if (loading) return <div style={{ padding: '32px', color: 'var(--text-secondary)', textAlign: 'center' }}>Loading AI metrics...</div>;
  if (error) return <div style={{ padding: '32px', color: '#ff4444', textAlign: 'center' }}>Error: {error}</div>;

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '32px' }}>
      <h2 style={{ marginBottom: '24px' }}>AI Evaluation Layer</h2>
      
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '32px' }}>
        <div style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', padding: '24px', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>Total Predictions</div>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold' }}>{data?.total_predictions || 0}</div>
        </div>
        <div style={{ background: 'var(--bg-primary)', border: '1px solid #ff4444', padding: '24px', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>Avg Predicted Risk</div>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#ff4444' }}>{Math.round(data?.average_risk_score || 0)}%</div>
        </div>
        <div style={{ background: 'var(--bg-primary)', border: '1px solid #00C851', padding: '24px', borderRadius: '8px' }}>
          <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '1px', marginBottom: '8px' }}>Completion Rate</div>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#00C851' }}>
            {data?.total_predictions > 0 
              ? Math.round((data?.outcomes.completed / data?.total_predictions) * 100) 
              : 0}%
          </div>
        </div>
      </div>

      <div style={{ background: 'var(--bg-primary)', border: '1px solid var(--border-color)', padding: '24px', borderRadius: '8px' }}>
        <h3 style={{ fontSize: '1.2rem', marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>Outcome Breakdown</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
            <span style={{ color: '#00C851' }}>Tasks Completed</span>
            <span style={{ fontFamily: 'monospace', fontSize: '1.1rem' }}>{data?.outcomes.completed || 0}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
            <span style={{ color: '#ff4444' }}>Tasks Failed</span>
            <span style={{ fontFamily: 'monospace', fontSize: '1.1rem' }}>{data?.outcomes.failed || 0}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
            <span style={{ color: '#ffbb33' }}>Tasks Pending</span>
            <span style={{ fontFamily: 'monospace', fontSize: '1.1rem' }}>{data?.outcomes.pending || 0}</span>
          </div>
        </div>
      </div>
      
      <div style={{ marginTop: '32px', fontSize: '0.9rem', color: 'var(--text-secondary)', fontStyle: 'italic' }}>
        <p>This dashboard pulls strictly from the <code style={{ background: 'var(--bg-primary)', padding: '2px 4px', borderRadius: '4px' }}>risk_predictions</code> Firestore collection to evaluate the accuracy of the Gemini Risk Analyzer models over time.</p>
      </div>
    </div>
  );
}
