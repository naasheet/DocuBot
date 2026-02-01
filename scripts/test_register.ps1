# Test the DocuBot register API endpoint
# Use this if Invoke-RestMethod gives "connection closed unexpectedly"

param(
    [string]$ApiUrl = "http://localhost:8000",
    [string]$Email = "test@example.com",
    [string]$Password = "Test123!",
    [string]$FullName = "Test User"
)

# Ensure UTF-8 encoding for JSON body (fixes PowerShell encoding issues)
$body = @{
    email     = $Email
    password  = $Password
    full_name = $FullName
} | ConvertTo-Json

$uri = "$ApiUrl/api/v1/auth/register"

try {
    # Method 1: Use Invoke-WebRequest with explicit encoding (more reliable than Invoke-RestMethod)
    $response = Invoke-WebRequest -Method Post -Uri $uri `
        -ContentType "application/json; charset=utf-8" `
        -Body ([System.Text.Encoding]::UTF8.GetBytes($body)) `
        -UseBasicParsing
    $response.Content | ConvertFrom-Json | ConvertTo-Json -Depth 5
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    if ($_.Exception.Response) {
        $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        $reader.BaseStream.Position = 0
        Write-Host $reader.ReadToEnd()
    }
}
