# Claude로부터 데이터 받기
$inputData = $input | ConvertFrom-Json
$filePath = $inputData.tool_input.file_path

if ([string]::IsNullOrWhiteSpace($filePath) -or !(Test-Path $filePath)) { exit 0 }

# 검사할 파일 확장자
$validExtensions = @(".js", ".ts", ".jsx", ".tsx", ".json", ".css", ".jsonc")
$extension = [System.IO.Path]::GetExtension($filePath)

if ($validExtensions -contains $extension) {
    Write-Host "✨ [Biome] 정리 중: $filePath"
    cmd /c "npx @biomejs/biome check --write `"$filePath`" 2>&1"
}
