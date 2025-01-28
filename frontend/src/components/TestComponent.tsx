// frontend/src/components/TestComponent.tsx

import React, { useState } from 'react';
import api from '../services/api';

const TestComponent: React.FC = () => {
  const [message, setMessage] = useState<string>('');

  const fetchTest = async () => {
    try {
      const response = await api.get('/test');
      setMessage(response.data.message);
    } catch (error) {
      console.error("Ошибка при запросе:", error);
      setMessage('Ошибка при запросе');
    }
  };

  return (
    <div>
      <h2>Test Component</h2>
      <button onClick={fetchTest}>Fetch Test Message</button>
      {message && <p>Response: {message}</p>}
    </div>
  );
};

export default TestComponent;
