import { useEffect, useState, useRef } from 'react';

export type CursorStyle = 'none' | 'trailing' | 'invert' | 'magnetic' | 'glitch' | 'spotlight' | 'liquid';

export const CustomCursor = ({ type }: { type: CursorStyle }) => {
  const [position, setPosition] = useState({ x: -100, y: -100 });
  const [isHovering, setIsHovering] = useState(false);
  
  // For Magnetic
  const [magneticPos, setMagneticPos] = useState<{ x: number, y: number, w: number, h: number } | null>(null);
  
  // For Glitch & Liquid
  const [velocity, setVelocity] = useState({ x: 0, y: 0 });
  const lastPos = useRef({ x: -100, y: -100, time: 0 });

  useEffect(() => {
    const updatePosition = (e: MouseEvent) => {
      const currentPos = { x: e.clientX, y: e.clientY };
      setPosition(currentPos);
      
      const now = Date.now();
      const dt = now - lastPos.current.time;
      if (dt > 0) {
        setVelocity({
          x: (currentPos.x - lastPos.current.x) / dt * 10,
          y: (currentPos.y - lastPos.current.y) / dt * 10
        });
      }
      lastPos.current = { x: currentPos.x, y: currentPos.y, time: now };
      
      const target = e.target as HTMLElement;
      const clickable = target.closest('button') || target.closest('a') || target.closest('input') || target.closest('select');
      setIsHovering(!!clickable);

      if (clickable && type === 'magnetic') {
        const rect = (clickable as HTMLElement).getBoundingClientRect();
        setMagneticPos({ x: rect.left + rect.width / 2, y: rect.top + rect.height / 2, w: rect.width, h: rect.height });
      } else {
        setMagneticPos(null);
      }
    };

    if (type !== 'none') {
      window.addEventListener('mousemove', updatePosition);
    }
    
    return () => {
      window.removeEventListener('mousemove', updatePosition);
    };
  }, [type]);

  if (type === 'none') return null;

  if (type === 'trailing') {
    return (
      <>
        <div style={{
          position: 'fixed', top: 0, left: 0, width: '8px', height: '8px',
          backgroundColor: 'var(--accent-primary)', borderRadius: '50%',
          transform: `translate(${position.x - 4}px, ${position.y - 4}px)`,
          pointerEvents: 'none', zIndex: 9999, transition: 'width 0.2s, height 0.2s'
        }} />
        <div style={{
          position: 'fixed', top: 0, left: 0, width: isHovering ? '48px' : '32px', height: isHovering ? '48px' : '32px',
          border: '2px solid var(--accent-primary)', borderRadius: '50%',
          transform: `translate(${position.x - (isHovering ? 24 : 16)}px, ${position.y - (isHovering ? 24 : 16)}px)`,
          pointerEvents: 'none', zIndex: 9998, transition: 'transform 0.15s ease-out, width 0.2s, height 0.2s',
          backgroundColor: isHovering ? 'var(--accent-primary)' : 'transparent', opacity: isHovering ? 0.2 : 1
        }} />
      </>
    );
  }

  if (type === 'invert') {
    return (
      <div style={{
        position: 'fixed', top: 0, left: 0, width: isHovering ? '64px' : '24px', height: isHovering ? '64px' : '24px',
        backgroundColor: 'white', borderRadius: '50%',
        transform: `translate(${position.x - (isHovering ? 32 : 12)}px, ${position.y - (isHovering ? 32 : 12)}px)`,
        pointerEvents: 'none', zIndex: 9999, transition: 'transform 0.05s linear, width 0.2s, height 0.2s', mixBlendMode: 'difference'
      }} />
    );
  }

  if (type === 'magnetic') {
    const posX = isHovering && magneticPos ? magneticPos.x : position.x;
    const posY = isHovering && magneticPos ? magneticPos.y : position.y;
    const width = isHovering && magneticPos ? magneticPos.w + 12 : 12;
    const height = isHovering && magneticPos ? magneticPos.h + 12 : 12;
    const borderRadius = isHovering ? '12px' : '50%';
    
    return (
      <div style={{
        position: 'fixed', top: 0, left: 0, width: `${width}px`, height: `${height}px`,
        backgroundColor: isHovering ? 'transparent' : 'var(--accent-primary)',
        border: isHovering ? '2px solid var(--accent-primary)' : 'none',
        borderRadius,
        transform: `translate(${posX - width / 2}px, ${posY - height / 2}px)`,
        pointerEvents: 'none', zIndex: 9999, transition: 'all 0.15s ease-out'
      }} />
    );
  }

  if (type === 'glitch') {
    const speed = Math.sqrt(velocity.x * velocity.x + velocity.y * velocity.y);
    const glitchOffset = speed > 5 ? speed : 0;
    
    return (
      <div style={{ position: 'fixed', top: 0, left: 0, pointerEvents: 'none', zIndex: 9999 }}>
        <div style={{
          position: 'absolute', width: '12px', height: '12px', backgroundColor: '#0ff', mixBlendMode: 'screen',
          transform: `translate(${position.x - 6 - glitchOffset}px, ${position.y - 6}px)`, transition: 'transform 0.05s'
        }} />
        <div style={{
          position: 'absolute', width: '12px', height: '12px', backgroundColor: '#f00', mixBlendMode: 'screen',
          transform: `translate(${position.x - 6 + glitchOffset}px, ${position.y - 6}px)`, transition: 'transform 0.05s'
        }} />
        <div style={{
          position: 'absolute', width: '12px', height: '12px', backgroundColor: 'white',
          transform: `translate(${position.x - 6}px, ${position.y - 6}px)`,
          opacity: isHovering ? 0 : 1
        }} />
      </div>
    );
  }

  if (type === 'spotlight') {
    return (
      <div style={{
        position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', pointerEvents: 'none', zIndex: 9998,
        background: `radial-gradient(circle 200px at ${position.x}px ${position.y}px, transparent 0%, rgba(0,0,0,0.85) 100%)`,
        transition: 'background 0.1s ease-out'
      }} />
    );
  }

  if (type === 'liquid') {
    const speed = Math.sqrt(velocity.x * velocity.x + velocity.y * velocity.y);
    const angle = Math.atan2(velocity.y, velocity.x);
    const scaleX = 1 + Math.min(speed / 10, 2);
    const scaleY = 1 - Math.min(speed / 30, 0.5);
    
    return (
      <div style={{
        position: 'fixed', top: 0, left: 0, width: '20px', height: '20px', backgroundColor: 'var(--accent-primary)', borderRadius: '50%',
        transform: `translate(${position.x - 10}px, ${position.y - 10}px) rotate(${angle}rad) scale(${scaleX}, ${scaleY})`,
        pointerEvents: 'none', zIndex: 9999, transition: 'transform 0.05s linear',
        filter: 'blur(1px)' // Note: intensive blur may affect performance
      }} />
    );
  }

  return null;
};
