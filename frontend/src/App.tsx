import { Routes, Route, Navigate } from 'react-router-dom';
import { Classes } from '@blueprintjs/core';

function Home() {
  return (
    <div className={`${Classes.DARK}`} style={{ padding: '2rem' }}>
      <h1 style={{ fontFamily: 'var(--font-mono)', color: 'var(--text-secondary)' }}>
        Ba Reng? v0.1.0
      </h1>
      <p style={{ color: 'var(--text-tertiary)' }}>
        Botswana Parliament MP Monitor
      </p>
    </div>
  );
}

export default function App() {
  return (
    <div className={Classes.DARK}>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </div>
  );
}
