
$ErrorActionPreference = "Stop"

$baseUrl = "http://localhost:8000"
$resultados = [System.Collections.Generic.List[object]]::new()
$script:falhaCritica = $false

function Testar-Etapa {
    param(
        [string]$Nome,
        [scriptblock]$Acao
    )

    Write-Host "`n[$Nome]" -ForegroundColor Cyan

    try {
        & $Acao
        $resultados.Add([PSCustomObject]@{
            Etapa = $Nome
            Status = "APROVADO"
            Detalhe = "Execução concluída"
        })

        Write-Host "APROVADO" -ForegroundColor Green
        return $true
    }
    catch {
        $resultados.Add([PSCustomObject]@{
            Etapa = $Nome
            Status = "REPROVADO"
            Detalhe = $_.Exception.Message
        })

        Write-Host "REPROVADO: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Verificar-ComandoDocker {
    param([string[]]$Argumentos)

    & docker @Argumentos

    if ($LASTEXITCODE -ne 0) {
        throw "Comando Docker falhou: docker $($Argumentos -join ' ')"
    }
}

function Verificar-HTTP {
    param(
        [string]$Url,
        [int]$StatusEsperado = 200
    )

    try {
        $resposta = Invoke-WebRequest -Uri $Url -Method Get
        $status = [int]$resposta.StatusCode
    }
    catch {
        if ($null -eq $_.Exception.Response) {
            throw
        }
        $status = [int]$_.Exception.Response.StatusCode
    }

    if ($status -ne $StatusEsperado) {
        throw "Esperado HTTP $StatusEsperado, recebido HTTP $status."
    }
}

function Esperar-ErroHttp {
    param(
        [string]$Url,
        [string]$Metodo,
        [object]$Body,
        [int]$StatusEsperado = 400
    )

    $parametros = @{
        Uri = $Url
        Method = $Metodo
    }

    if ($null -ne $Body) {
        $parametros.ContentType = "application/json"
        $parametros.Body = $Body | ConvertTo-Json -Depth 5
    }

    try {
        Invoke-RestMethod @parametros | Out-Null
    }
    catch {
        if ($null -eq $_.Exception.Response) {
            throw
        }

        $status = [int]$_.Exception.Response.StatusCode

        if ($status -ne $StatusEsperado) {
            throw "Esperado HTTP $StatusEsperado, recebido HTTP $status."
        }

        return
    }

    throw "A operação deveria ter sido bloqueada, mas foi aceita."
}

Write-Host "`n====================================" -ForegroundColor Magenta
Write-Host " LIBRATECH - VALIDACAO AUTOMATIZADA" -ForegroundColor Magenta
Write-Host "====================================" -ForegroundColor Magenta

# 1. Docker
$dockerOK = Testar-Etapa "Docker Engine" {
    Verificar-ComandoDocker @("version")
}

if (-not $dockerOK) {
    $script:falhaCritica = $true
}

# 2. Containers
$containersOK = Testar-Etapa "Containers do projeto" {
    Verificar-ComandoDocker @("compose", "ps")
}

if (-not $containersOK) {
    $script:falhaCritica = $true
}

# 3. API
$apiOK = Testar-Etapa "Healthcheck da API" {
    Verificar-HTTP "$baseUrl/health"
}

if (-not $apiOK) {
    $script:falhaCritica = $true
}

# 4. PostgreSQL
$dbOK = Testar-Etapa "Healthcheck PostgreSQL" {
    Verificar-HTTP "$baseUrl/health/db"
}

if (-not $dbOK) {
    $script:falhaCritica = $true
}

# Sem infraestrutura, não adianta executar os testes seguintes.
if (-not ($dockerOK -and $containersOK -and $apiOK -and $dbOK)) {
    Write-Host "`nInfraestrutura indisponível. Testes dependentes foram ignorados." -ForegroundColor Yellow
}
else {

    # 5. Pytest
    Testar-Etapa "Testes automatizados Pytest" {
        Verificar-ComandoDocker @(
            "compose", "exec", "-T", "api",
            "python", "-m", "pytest", "-q", "-p", "no:cacheprovider"
        )
    }

    # 6. Ruff
    Testar-Etapa "Análise estática Ruff" {
        Verificar-ComandoDocker @(
            "compose", "exec", "-T", "api", "sh", "-c",
            'ruff check --no-cache --cache-dir /tmp/ruff-cache $(find app tests migrations -type f -name "*.py")'
        )
    }

    # 7. Alembic
    Testar-Etapa "Estado das migrations" {
        Verificar-ComandoDocker @(
            "compose", "exec", "-T", "api", "alembic", "current"
        )
    }

    # 8. Alembic check
    Testar-Etapa "Consistência das migrations" {
        Verificar-ComandoDocker @(
            "compose", "exec", "-T", "api", "alembic", "check"
        )
    }

    # Identificadores exclusivos
    $sufixo = [guid]::NewGuid().ToString("N").Substring(0, 12)
    $isbn = "978" + (Get-Random -Minimum 1000000000 -Maximum 2000000000).ToString()
    $email = "teste_$sufixo@libratech.com"

    $livroId = $null
    $leitorId = $null
    $emprestimoId = $null

    # 9. Cadastro de livro
    $livroOK = Testar-Etapa "Cadastro de livro" {
        $body = @{
            titulo = "TESTE AUTOMATIZADO $sufixo"
            autor = "Autor de Teste"
            isbn = $isbn
            categoria = "Teste"
            quantidade_total = 1
        } | ConvertTo-Json

        $script:livro = Invoke-RestMethod `
            -Uri "$baseUrl/livros" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body

        $script:livroId = $script:livro.id

        if (-not $script:livroId) {
            throw "ID do livro não retornado."
        }
    }

    # 10. ISBN duplicado
    if ($livroOK) {
        Testar-Etapa "Bloqueio de ISBN duplicado" {
            $body = @{
                titulo = "Livro duplicado"
                autor = "Autor"
                isbn = $isbn
                categoria = "Teste"
                quantidade_total = 1
            }

            Esperar-ErroHttp "$baseUrl/livros" "Post" $body 400
        }
    }

    # 11. Cadastro de leitor
    $leitorOK = Testar-Etapa "Cadastro de leitor" {
        $body = @{
            nome = "LEITOR TESTE $sufixo"
            email = $email
            telefone = "85999999999"
        } | ConvertTo-Json

        $script:leitor = Invoke-RestMethod `
            -Uri "$baseUrl/leitores" `
            -Method Post `
            -ContentType "application/json" `
            -Body $body

        $script:leitorId = $script:leitor.id

        if (-not $script:leitorId) {
            throw "ID do leitor não retornado."
        }
    }

    # 12. E-mail duplicado
    if ($leitorOK) {
        Testar-Etapa "Bloqueio de e-mail duplicado" {
            $body = @{
                nome = "Leitor duplicado"
                email = $email
                telefone = "85999999999"
            }

            Esperar-ErroHttp "$baseUrl/leitores" "Post" $body 400
        }
    }

    # 13. Empréstimo
    $emprestimoOK = $false

    if ($livroOK -and $leitorOK) {
        $emprestimoOK = Testar-Etapa "Realização de empréstimo" {
            $body = @{
                livro_id = $livroId
                leitor_id = $leitorId
            } | ConvertTo-Json

            $script:emprestimo = Invoke-RestMethod `
                -Uri "$baseUrl/emprestimos" `
                -Method Post `
                -ContentType "application/json" `
                -Body $body

            $script:emprestimoId = $script:emprestimo.id

            if (-not $script:emprestimoId) {
                throw "ID do empréstimo não retornado."
            }
        }
    }

    # 14. Bloqueio por estoque
    if ($emprestimoOK) {
        Testar-Etapa "Bloqueio por falta de estoque" {
            $body = @{
                livro_id = $livroId
                leitor_id = $leitorId
            }

            Esperar-ErroHttp "$baseUrl/emprestimos" "Post" $body 400
        }
    }

    # 15. Cinco renovações
    if ($emprestimoOK) {
        Testar-Etapa "Cinco renovações permitidas" {
            for ($i = 1; $i -le 5; $i++) {
                Invoke-RestMethod `
                    -Uri "$baseUrl/emprestimos/$emprestimoId/renovacao" `
                    -Method Post | Out-Null
            }
        }

        # 16. Sexta renovação
        Testar-Etapa "Bloqueio da sexta renovação" {
            Esperar-ErroHttp `
                "$baseUrl/emprestimos/$emprestimoId/renovacao" `
                "Post" $null 400
        }

        # 17. Devolução
        Testar-Etapa "Devolução do empréstimo" {
            Invoke-RestMethod `
                -Uri "$baseUrl/emprestimos/$emprestimoId/devolucao" `
                -Method Post | Out-Null
        }

        # 18. Devolução duplicada
        Testar-Etapa "Bloqueio de devolução duplicada" {
            Esperar-ErroHttp `
                "$baseUrl/emprestimos/$emprestimoId/devolucao" `
                "Post" $null 400
        }
    }

    # 19. Consulta
    if ($livroOK -and $leitorOK -and $emprestimoOK) {
        Testar-Etapa "Consulta dos registros" {
            Invoke-RestMethod "$baseUrl/livros/$livroId" | Out-Null
            Invoke-RestMethod "$baseUrl/leitores/$leitorId" | Out-Null
            Invoke-RestMethod "$baseUrl/emprestimos/$emprestimoId" | Out-Null
        }
    }
}

# Relatório
Write-Host "`n====================================" -ForegroundColor Magenta
Write-Host " RELATORIO FINAL" -ForegroundColor Magenta
Write-Host "====================================" -ForegroundColor Magenta

$resultados | Format-Table -AutoSize

$aprovados = @($resultados | Where-Object Status -eq "APROVADO").Count
$reprovados = @($resultados | Where-Object Status -eq "REPROVADO").Count

Write-Host "Aprovados: $aprovados" -ForegroundColor Green
Write-Host "Reprovados: $reprovados" -ForegroundColor Red

$relatorio = Join-Path $PSScriptRoot "relatorio_validacao.txt"

$resultados |
    Format-Table -AutoSize |
    Out-String |
    Set-Content -Path $relatorio -Encoding UTF8

Write-Host "Relatório salvo em: $relatorio" -ForegroundColor Cyan

if ($script:falhaCritica -or $reprovados -gt 0) {
    Write-Host "VALIDACAO COM FALHAS" -ForegroundColor Red
    exit 1
}

Write-Host "VALIDACAO CONCLUIDA" -ForegroundColor Green
exit 0
