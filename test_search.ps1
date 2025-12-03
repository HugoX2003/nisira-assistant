# Test RAG Hybrid Search
$headers = @{ "Content-Type" = "application/json" }
$body = '{"question": "Que menciona el documento Guia de despliegue de Castillo Anhuaman y Lopez Benites"}'
$uri = "https://nisira-assistant-backend-f53bfb28dc45.herokuapp.com/api/rag/chat/"

Write-Host "Enviando peticion a: $uri" -ForegroundColor Cyan
Write-Host "Pregunta: $body" -ForegroundColor Cyan
Write-Host ""

try {
    $response = Invoke-RestMethod -Uri $uri -Method POST -Headers $headers -Body $body -TimeoutSec 180
    
    Write-Host "=== RESPUESTA ===" -ForegroundColor Green
    Write-Host $response.answer
    Write-Host ""
    Write-Host "=== DOCUMENTOS RELEVANTES ===" -ForegroundColor Yellow
    
    foreach ($doc in $response.relevant_documents) {
        Write-Host "----------------------------------------"
        Write-Host "Fuente: $($doc.source)" -ForegroundColor Cyan
        Write-Host "Score: $($doc.similarity_score)"
        Write-Host "Tipo: $($doc.search_type)"
        Write-Host "Contenido (preview): $($doc.content.Substring(0, [Math]::Min(200, $doc.content.Length)))..."
    }
} catch {
    Write-Host "Error: $_" -ForegroundColor Red
}
