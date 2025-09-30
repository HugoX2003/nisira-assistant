import React, { useState, useEffect } from 'react';
import { testRagSimple, testRagMultiple, getRagSystemStatus, testCustomQuestion } from '../services/api';

const TestingPanel = ({ onBackToChat }) => {
  const [systemStatus, setSystemStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [testResults, setTestResults] = useState(null);
  const [customQuestion, setCustomQuestion] = useState('');
  const [activeTest, setActiveTest] = useState(null);

  // Obtener estado del sistema al cargar el componente
  useEffect(() => {
    loadSystemStatus();
  }, []);

  const loadSystemStatus = async () => {
    try {
      const status = await getRagSystemStatus();
      setSystemStatus(status);
    } catch (error) {
      console.error('Error loading system status:', error);
    }
  };

  const runSimpleTest = async () => {
    setLoading(true);
    setActiveTest('simple');
    try {
      const result = await testRagSimple();
      setTestResults(result);
    } catch (error) {
      setTestResults({ success: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const runMultipleTest = async () => {
    setLoading(true);
    setActiveTest('multiple');
    try {
      const result = await testRagMultiple();
      setTestResults(result);
    } catch (error) {
      setTestResults({ success: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const runCustomTest = async () => {
    if (!customQuestion.trim()) {
      alert('Por favor ingresa una pregunta');
      return;
    }
    
    setLoading(true);
    setActiveTest('custom');
    try {
      const result = await testCustomQuestion(customQuestion);
      setTestResults(result);
    } catch (error) {
      setTestResults({ success: false, error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (seconds) => {
    return `${seconds}s`;
  };

  const SystemStatusCard = () => (
    <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 mb-6">
      <h3 className="text-lg font-semibold text-gray-800 mb-3 flex items-center">
        🔍 Estado del Sistema RAG
        <button 
          onClick={loadSystemStatus}
          className="ml-2 text-sm bg-blue-500 text-white px-2 py-1 rounded hover:bg-blue-600"
        >
          Actualizar
        </button>
      </h3>
      {systemStatus ? (
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-600">Estado:</p>
            <p className={`font-medium ${systemStatus.system_initialized ? 'text-green-600' : 'text-red-600'}`}>
              {systemStatus.system_initialized ? '✅ Inicializado' : '❌ Error'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Documentos:</p>
            <p className="font-medium">{systemStatus.system_stats?.total_documents || 0}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Sistema LLM:</p>
            <p className={`font-medium ${systemStatus.system_stats?.llm_available ? 'text-green-600' : 'text-yellow-600'}`}>
              {systemStatus.system_stats?.llm_available ? '✅ Activo' : '⚠️ Limitado'}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Conectividad:</p>
            <p className={`font-medium ${systemStatus.connectivity_test === 'success' ? 'text-green-600' : 'text-red-600'}`}>
              {systemStatus.connectivity_test === 'success' ? '✅ OK' : '❌ Error'}
            </p>
          </div>
        </div>
      ) : (
        <p className="text-gray-600">Cargando estado del sistema...</p>
      )}
    </div>
  );

  const TestButtons = () => (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
      <button
        onClick={runSimpleTest}
        disabled={loading}
        className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        🧪 Test Simple
      </button>
      <button
        onClick={runMultipleTest}
        disabled={loading}
        className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed"
      >
        📊 Test Múltiple
      </button>
      <div className="flex flex-col space-y-2">
        <input
          type="text"
          value={customQuestion}
          onChange={(e) => setCustomQuestion(e.target.value)}
          placeholder="Tu pregunta personalizada..."
          className="border border-gray-300 rounded px-3 py-2 focus:outline-none focus:ring-2 focus:ring-purple-500"
        />
        <button
          onClick={runCustomTest}
          disabled={loading}
          className="bg-purple-500 text-white px-6 py-2 rounded-lg hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          🎯 Test Personalizado
        </button>
      </div>
    </div>
  );

  const TestResults = () => {
    if (!testResults) return null;

    if (!testResults.success) {
      return (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-lg font-semibold text-red-800 mb-2">❌ Error en Test</h3>
          <p className="text-red-600">{testResults.error}</p>
        </div>
      );
    }

    return (
      <div className="bg-white border border-gray-200 rounded-lg p-6">
        <h3 className="text-xl font-bold text-gray-800 mb-4">
          📋 Resultados del Test {activeTest === 'simple' ? 'Simple' : activeTest === 'multiple' ? 'Múltiple' : 'Personalizado'}
        </h3>

        {/* Test Simple */}
        {activeTest === 'simple' && (
          <div>
            <div className="mb-4">
              <p className="text-sm text-gray-600">Pregunta:</p>
              <p className="font-medium text-gray-800">{testResults.question}</p>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600">Respuesta:</p>
              <div className="bg-gray-50 p-4 rounded border max-h-96 overflow-y-auto">
                <pre className="whitespace-pre-wrap text-sm">{testResults.answer}</pre>
              </div>
            </div>

            <div className="grid grid-cols-3 gap-4 mb-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">{testResults.sources?.length || 0}</p>
                <p className="text-sm text-gray-600">Fuentes</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{formatTime(testResults.test_duration)}</p>
                <p className="text-sm text-gray-600">Tiempo</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-600">{testResults.system_stats?.total_documents || 0}</p>
                <p className="text-sm text-gray-600">Documentos</p>
              </div>
            </div>

            {testResults.sources && testResults.sources.length > 0 && (
              <div>
                <p className="text-sm text-gray-600 font-semibold mb-2">📚 Fuentes utilizadas:</p>
                {testResults.sources.map((source, index) => (
                  <div key={index} className="bg-gray-50 p-3 rounded border mb-2">
                    <p className="font-medium text-sm">{source.filename}</p>
                    <p className="text-xs text-gray-600 mt-1">{source.content}</p>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Test Múltiple */}
        {activeTest === 'multiple' && (
          <div>
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">{testResults.total_questions}</p>
                <p className="text-sm text-gray-600">Preguntas</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{formatTime(testResults.total_duration)}</p>
                <p className="text-sm text-gray-600">Tiempo Total</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-600">{formatTime(testResults.average_time_per_query)}</p>
                <p className="text-sm text-gray-600">Promedio</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-orange-600">{testResults.system_stats?.total_documents || 0}</p>
                <p className="text-sm text-gray-600">Documentos</p>
              </div>
            </div>

            <div className="space-y-4">
              {testResults.results?.map((result, index) => (
                <div key={index} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex justify-between items-start mb-2">
                    <h4 className="font-semibold text-gray-800">
                      {result.question_number}. {result.question}
                    </h4>
                    <span className="text-sm text-gray-500">{formatTime(result.query_time)}</span>
                  </div>
                  
                  {result.error ? (
                    <p className="text-red-600 text-sm">❌ Error: {result.error}</p>
                  ) : (
                    <>
                      <p className="text-gray-700 text-sm mb-2">{result.answer_preview}</p>
                      <p className="text-xs text-gray-500">📚 {result.sources_count} fuentes encontradas</p>
                    </>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Test Personalizado */}
        {activeTest === 'custom' && (
          <div>
            <div className="mb-4">
              <p className="text-sm text-gray-600">Tu Pregunta:</p>
              <p className="font-medium text-gray-800">{testResults.question}</p>
            </div>
            
            <div className="mb-4">
              <p className="text-sm text-gray-600">Respuesta:</p>
              <div className="bg-gray-50 p-4 rounded border max-h-96 overflow-y-auto">
                <pre className="whitespace-pre-wrap text-sm">{testResults.answer}</pre>
              </div>
            </div>

            <div className="grid grid-cols-4 gap-4 mb-4">
              <div className="text-center">
                <p className="text-2xl font-bold text-blue-600">{testResults.sources?.length || 0}</p>
                <p className="text-sm text-gray-600">Fuentes</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-green-600">{formatTime(testResults.query_time)}</p>
                <p className="text-sm text-gray-600">Tiempo</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-purple-600">{testResults.quality_indicators?.answer_length || 0}</p>
                <p className="text-sm text-gray-600">Caracteres</p>
              </div>
              <div className="text-center">
                <p className={`text-2xl font-bold ${testResults.quality_indicators?.response_quality === 'good' ? 'text-green-600' : 'text-yellow-600'}`}>
                  {testResults.quality_indicators?.response_quality === 'good' ? '👍' : '⚠️'}
                </p>
                <p className="text-sm text-gray-600">Calidad</p>
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">🧪 Panel de Testing - Sistema RAG</h1>
      
      <SystemStatusCard />
      
      {loading && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-blue-800 flex items-center">
            <span className="animate-spin mr-2">⟳</span>
            Ejecutando test... Por favor espera.
          </p>
        </div>
      )}
      
      <TestButtons />
      <TestResults />
    </div>
  );
};

export default TestingPanel;