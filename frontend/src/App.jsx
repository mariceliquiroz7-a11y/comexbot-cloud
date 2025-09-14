import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [message, setMessage] = useState(''); // Mensaje actual en el input
  const [chatHistory, setChatHistory] = useState([]); // Historial de mensajes del chat
  const [backendResponse, setBackendResponse] = useState(''); // Respuesta del backend

  // Hook para cargar mensajes iniciales o hacer una petición inicial si fuera necesario
  useEffect(() => {
    // Puedes hacer una llamada inicial al backend aquí si quieres cargar algo al inicio
    // Por ahora, solo configuramos para que el backend responda "Hello World" al inicio si se consulta "/"
    // Pero para el chat, enviaremos un mensaje al endpoint "/chat"
  }, []);

  const handleSendMessage = async () => {
    if (message.trim() === '') return; // No enviar mensajes vacíos

    // Añadir mensaje del usuario al historial
    setChatHistory([...chatHistory, { sender: 'user', text: message }]);

    try {
      // Enviar el mensaje al backend
      const response = await axios.post('http://127.0.0.1:8000/chat', {
        message: message,
      });
      
      // Guardar la respuesta del backend
      setBackendResponse(response.data.response);
      
      // Añadir respuesta del bot al historial
      setChatHistory((prevHistory) => [
        ...prevHistory,
        { sender: 'bot', text: response.data.response },
      ]);

      // Limpiar el input después de enviar
      setMessage('');
    } catch (error) {
      console.error('Error al enviar mensaje al backend:', error);
      // Mostrar un mensaje de error en el chat
      setChatHistory((prevHistory) => [
        ...prevHistory,
        { sender: 'bot', text: 'Error: No se pudo conectar con el servidor.' },
      ]);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="App">
      <header className="App-header">
        <h1>Mi Chatbot</h1>
        <div className="chat-container">
          <div className="chat-history">
            {chatHistory.map((msg, index) => (
              <div key={index} className={`message ${msg.sender}`}>
                <strong>{msg.sender === 'user' ? 'Tú: ' : 'Bot: '}</strong>
                {msg.text}
              </div>
            ))}
          </div>
          <div className="input-area">
            <input
              type="text"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Escribe tu mensaje..."
            />
            <button onClick={handleSendMessage}>Enviar</button>
          </div>
        </div>
      </header>
    </div>
  );
}

export default App;