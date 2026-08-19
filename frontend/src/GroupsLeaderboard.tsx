import { useState, useEffect } from 'react';
import type { User } from 'firebase/auth';

interface Group {
  id: string;
  name: string;
  members: string[];
}

interface LeaderboardEntry {
  user_id: string;
  displayName: string;
  score: number;
}

export function GroupsLeaderboard({ user }: { user: User }) {
  const [groups, setGroups] = useState<Group[]>([]);
  const [selectedGroup, setSelectedGroup] = useState<Group | null>(null);
  const [leaderboard, setLeaderboard] = useState<LeaderboardEntry[]>([]);
  const [newGroupName, setNewGroupName] = useState('');
  const [joinGroupId, setJoinGroupId] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchGroups = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${import.meta.env.PROD ? '' : 'http://localhost:8000'}/api/groups`, {
        headers: { 'x-user-id': user.uid }
      });
      const data = await res.json();
      setGroups(data);
      if (data.length > 0 && !selectedGroup) {
        setSelectedGroup(data[0]);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  const fetchLeaderboard = async (groupId: string) => {
    try {
      const res = await fetch(`${import.meta.env.PROD ? '' : 'http://localhost:8000'}/api/groups/${groupId}/leaderboard`);
      const data = await res.json();
      setLeaderboard(data);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchGroups();
  }, []);

  useEffect(() => {
    if (selectedGroup) {
      fetchLeaderboard(selectedGroup.id);
    }
  }, [selectedGroup]);

  const createGroup = async () => {
    if (!newGroupName.trim()) return;
    try {
      const res = await fetch(`${import.meta.env.PROD ? '' : 'http://localhost:8000'}/api/groups`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'x-user-id': user.uid },
        body: JSON.stringify({ name: newGroupName })
      });
      const data = await res.json();
      setGroups([...groups, data]);
      setSelectedGroup(data);
      setNewGroupName('');
    } catch (e) {
      console.error(e);
    }
  };

  const joinGroup = async () => {
    if (!joinGroupId.trim()) return;
    try {
      await fetch(`${import.meta.env.PROD ? '' : 'http://localhost:8000'}/api/groups/${joinGroupId}/join`, {
        method: 'POST',
        headers: { 'x-user-id': user.uid }
      });
      setJoinGroupId('');
      fetchGroups();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading && groups.length === 0) return <div style={{ padding: '32px', color: 'var(--text-secondary)' }}>Loading groups...</div>;

  return (
    <div className="glass-panel animate-fade-in" style={{ padding: '32px' }}>
      <h2 style={{ marginBottom: '24px', fontFamily: 'var(--font-display)', fontSize: '2rem' }}>Accountability Groups</h2>
      
      <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap', marginBottom: '32px' }}>
        <div style={{ flex: '1 1 300px', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', padding: '24px', borderRadius: '8px' }}>
          <h3 style={{ marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>Create a Group</h3>
          <input 
            className="glass-input" 
            placeholder="Squad Name" 
            value={newGroupName} 
            onChange={e => setNewGroupName(e.target.value)}
            style={{ width: '100%', marginBottom: '12px' }}
          />
          <button onClick={createGroup} className="cyber-button" style={{ width: '100%' }}>Create</button>
        </div>
        
        <div style={{ flex: '1 1 300px', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', padding: '24px', borderRadius: '8px' }}>
          <h3 style={{ marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>Join a Group</h3>
          <input 
            className="glass-input" 
            placeholder="Group ID (e.g. 1a2b3c4d)" 
            value={joinGroupId} 
            onChange={e => setJoinGroupId(e.target.value)}
            style={{ width: '100%', marginBottom: '12px' }}
          />
          <button onClick={joinGroup} className="cyber-button" style={{ width: '100%' }}>Join</button>
        </div>
      </div>

      {groups.length > 0 ? (
        <div style={{ display: 'flex', gap: '24px', flexWrap: 'wrap' }}>
          {/* Group Selector */}
          <div style={{ flex: '0 0 250px' }}>
            <h3 style={{ marginBottom: '16px', color: 'var(--text-secondary)' }}>Your Groups</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {groups.map(g => (
                <button 
                  key={g.id} 
                  onClick={() => setSelectedGroup(g)}
                  style={{
                    padding: '12px',
                    textAlign: 'left',
                    borderRadius: '8px',
                    border: '1px solid var(--border-color)',
                    background: selectedGroup?.id === g.id ? 'var(--accent-primary)' : 'var(--bg-primary)',
                    color: selectedGroup?.id === g.id ? '#000' : 'var(--text-primary)',
                    cursor: 'pointer',
                    fontWeight: selectedGroup?.id === g.id ? 'bold' : 'normal'
                  }}
                  className="hover-lift"
                >
                  <div style={{ fontSize: '1.1rem' }}>{g.name}</div>
                  <div style={{ fontSize: '0.8rem', opacity: 0.7, fontFamily: 'monospace' }}>ID: {g.id}</div>
                </button>
              ))}
            </div>
          </div>
          
          {/* Leaderboard */}
          <div style={{ flex: '1 1 400px', background: 'var(--bg-primary)', border: '1px solid var(--border-color)', padding: '24px', borderRadius: '8px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', borderBottom: '1px solid var(--border-color)', paddingBottom: '8px' }}>
              <h3 style={{ fontSize: '1.5rem', fontFamily: 'var(--font-display)' }}>{selectedGroup?.name} Leaderboard</h3>
              <span style={{ color: 'var(--accent-primary)', fontFamily: 'monospace' }}>Invite: {selectedGroup?.id}</span>
            </div>
            
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {leaderboard.length === 0 ? (
                <p style={{ color: 'var(--text-secondary)' }}>No data yet.</p>
              ) : (
                leaderboard.map((entry, idx) => (
                  <div key={entry.user_id} style={{ display: 'flex', alignItems: 'center', padding: '16px', border: '1px solid var(--border-color)', borderRadius: '8px', background: entry.user_id === user.uid ? 'rgba(255,255,255,0.05)' : 'transparent' }}>
                    <div style={{ fontSize: '1.5rem', fontWeight: 'bold', width: '40px', color: idx === 0 ? '#ffbb33' : idx === 1 ? '#c0c0c0' : idx === 2 ? '#cd7f32' : 'var(--text-secondary)' }}>
                      #{idx + 1}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 'bold', fontSize: '1.1rem' }}>{entry.displayName}</div>
                      {entry.user_id === user.uid && <div style={{ fontSize: '0.8rem', color: 'var(--accent-primary)' }}>You</div>}
                    </div>
                    <div style={{ fontSize: '1.8rem', fontWeight: 'bold', fontFamily: 'monospace' }}>
                      {entry.score} <span style={{ fontSize: '1rem', color: 'var(--text-secondary)' }}>pts</span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      ) : (
        <div style={{ textAlign: 'center', padding: '48px', color: 'var(--text-secondary)', border: '1px dashed var(--border-color)', borderRadius: '8px' }}>
          You aren't in any accountability groups yet. Create or join one to compete on the leaderboard!
        </div>
      )}
    </div>
  );
}
