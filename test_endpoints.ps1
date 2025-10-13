# Script de prueba de endpoints para Nisira Assistant en Heroku
# ============================================================

$BASE_URL = "https://nisira-assistant-51691aa80938.herokuapp.com"
$TOKEN = $null
$USER_ID = $null
$CONVERSATION_ID = $null

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "PRUEBA DE ENDPOINTS - NISIRA ASSISTANT" -ForegroundColor Cyan
Write-Host "URL: $BASE_URL" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Funcion para hacer requests y mostrar resultados
function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Endpoint,
        [string]$Description,
        [hashtable]$Body = $null,
        [string]$Token = $null
    )
    
    Write-Host "[TEST] $Description" -ForegroundColor Yellow
    Write-Host "   $Method $Endpoint" -ForegroundColor Gray
    
    try {
        $headers = @{
            "Content-Type" = "application/json"
        }
        
        if ($Token) {
            $headers["Authorization"] = "Bearer $Token"
        }
        
        $params = @{
            Uri = "$BASE_URL$Endpoint"
            Method = $Method
            Headers = $headers
            ErrorAction = "Stop"
        }
        
        if ($Body) {
            $params["Body"] = ($Body | ConvertTo-Json)
        }
        
        $response = Invoke-RestMethod @params
        Write-Host "   [OK] SUCCESS" -ForegroundColor Green
        
        # Mostrar respuesta de forma legible
        if ($response) {
            $jsonOutput = $response | ConvertTo-Json -Depth 5
            Write-Host "   Response:" -ForegroundColor Gray
            $jsonOutput -split "`n" | ForEach-Object { Write-Host "   $_" -ForegroundColor Gray }
        }
        
        return $response
    }
    catch {
        Write-Host "   [ERROR]: $($_.Exception.Message)" -ForegroundColor Red
        if ($_.ErrorDetails.Message) {
            Write-Host "   Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
        }
        return $null
    }
    finally {
        Write-Host ""
    }
}

# ============================================================
# 1. PRUEBAS DE SALUD E INFO
# ============================================================
Write-Host "`n=== 1. ENDPOINTS DE SALUD E INFO ===" -ForegroundColor Cyan

Test-Endpoint -Method "GET" -Endpoint "/api/health/" -Description "Health Check"
Test-Endpoint -Method "GET" -Endpoint "/api/info/" -Description "API Info"

# ============================================================
# 2. PRUEBAS DE AUTENTICACION
# ============================================================
Write-Host "`n=== 2. ENDPOINTS DE AUTENTICACION ===" -ForegroundColor Cyan

# Registrar usuario de prueba
$timestamp = Get-Date -Format "yyyyMMddHHmmss"
$testUser = "test_user_$timestamp"
$testPassword = "Test123456"

$registerBody = @{
    username = $testUser
    password = $testPassword
    email = "$testUser@test.com"
}

$registerResponse = Test-Endpoint -Method "POST" -Endpoint "/api/auth/register/" `
    -Description "Registrar Usuario de Prueba" -Body $registerBody

if ($registerResponse) {
    Write-Host "   [OK] Usuario registrado: $testUser" -ForegroundColor Green
}

# Login y obtener token
$loginBody = @{
    username = $testUser
    password = $testPassword
}

$loginResponse = Test-Endpoint -Method "POST" -Endpoint "/api/auth/login/" `
    -Description "Login y Obtener Token JWT" -Body $loginBody

if ($loginResponse -and $loginResponse.access) {
    $TOKEN = $loginResponse.access
    $USER_ID = $loginResponse.user_id
    Write-Host "   [OK] Token obtenido correctamente" -ForegroundColor Green
    Write-Host "   User ID: $USER_ID" -ForegroundColor Gray
}
else {
    Write-Host "   [ERROR] No se pudo obtener el token. Las siguientes pruebas pueden fallar." -ForegroundColor Red
}

# ============================================================
# 3. PRUEBAS DE SISTEMA RAG
# ============================================================
Write-Host "`n=== 3. ENDPOINTS DEL SISTEMA RAG ===" -ForegroundColor Cyan

Test-Endpoint -Method "GET" -Endpoint "/api/rag/status/" `
    -Description "Estado del Sistema RAG" -Token $TOKEN

Test-Endpoint -Method "GET" -Endpoint "/api/rag/system-status/" `
    -Description "Estado Detallado del Sistema RAG"

# Prueba de consulta RAG
$ragQueryBody = @{
    question = "Cual es la vision de Carlos Franco sobre la democracia en el Peru?"
    top_k = 3
    include_generation = $true
}

Test-Endpoint -Method "POST" -Endpoint "/api/rag/query/" `
    -Description "Consulta RAG" -Body $ragQueryBody

# ============================================================
# 4. PRUEBAS DE CONVERSACIONES
# ============================================================
Write-Host "`n=== 4. ENDPOINTS DE CONVERSACIONES ===" -ForegroundColor Cyan

# Listar conversaciones
Test-Endpoint -Method "GET" -Endpoint "/api/conversations/" `
    -Description "Listar Conversaciones" -Token $TOKEN

# Crear conversacion
$createConvBody = @{
    title = "Conversacion de Prueba - $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
}

$convResponse = Test-Endpoint -Method "POST" -Endpoint "/api/conversations/create/" `
    -Description "Crear Nueva Conversacion" -Body $createConvBody -Token $TOKEN

if ($convResponse -and $convResponse.conversation.id) {
    $CONVERSATION_ID = $convResponse.conversation.id
    Write-Host "   [OK] Conversacion creada con ID: $CONVERSATION_ID" -ForegroundColor Green
}

# ============================================================
# 5. PRUEBAS DE CHAT
# ============================================================
Write-Host "`n=== 5. ENDPOINTS DE CHAT ===" -ForegroundColor Cyan

if ($CONVERSATION_ID) {
    # Enviar mensaje basico
    $chatBody = @{
        conversation_id = $CONVERSATION_ID
        message = "Hola, esta es una prueba del sistema de chat"
    }
    
    Test-Endpoint -Method "POST" -Endpoint "/api/chat/" `
        -Description "Enviar Mensaje (Chat Basico)" -Body $chatBody -Token $TOKEN
    
    # Chat con RAG
    $ragChatBody = @{
        conversation_id = $CONVERSATION_ID
        message = "Que opina Carlos Franco sobre la participacion ciudadana?"
        use_rag = $true
        top_k = 3
    }
    
    Test-Endpoint -Method "POST" -Endpoint "/api/rag/chat/" `
        -Description "Chat Mejorado con RAG" -Body $ragChatBody -Token $TOKEN
    
    # Obtener mensajes de la conversacion
    Test-Endpoint -Method "GET" -Endpoint "/api/conversations/$CONVERSATION_ID/messages/" `
        -Description "Obtener Mensajes de la Conversacion" -Token $TOKEN
}
else {
    Write-Host "   [WARNING] No se pudo crear conversacion, saltando pruebas de chat" -ForegroundColor Yellow
}

# ============================================================
# 6. LIMPIEZA
# ============================================================
Write-Host "`n=== 6. LIMPIEZA ===" -ForegroundColor Cyan

if ($CONVERSATION_ID) {
    Test-Endpoint -Method "DELETE" -Endpoint "/api/conversations/$CONVERSATION_ID/delete/" `
        -Description "Eliminar Conversacion de Prueba" -Token $TOKEN
}

# ============================================================
# RESUMEN
# ============================================================
Write-Host "`n=====================================" -ForegroundColor Cyan
Write-Host "PRUEBAS COMPLETADAS" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Revisa los resultados arriba para verificar que todos los endpoints funcionen correctamente." -ForegroundColor White
Write-Host ""
Write-Host "Datos de prueba creados:" -ForegroundColor White
Write-Host "   Usuario: $testUser" -ForegroundColor Gray
if ($TOKEN) {
    $tokenPreview = $TOKEN.Substring(0, [Math]::Min(50, $TOKEN.Length))
    Write-Host "   Token: $tokenPreview..." -ForegroundColor Gray
}
Write-Host ""
