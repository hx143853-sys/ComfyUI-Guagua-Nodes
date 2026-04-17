param(
    [string]$Message = ""
)

$ErrorActionPreference = "Stop"

function Invoke-Git {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    & git @Args
    if ($LASTEXITCODE -ne 0) {
        throw "git $($Args -join ' ') failed."
    }
}

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    throw "git is not installed or not in PATH."
}

$repoRoot = $PSScriptRoot
Push-Location $repoRoot

try {
    if (-not (Test-Path (Join-Path $repoRoot ".git"))) {
        Invoke-Git init -b main
    }

    $remoteUrl = (& git config --get remote.origin.url 2>$null | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($remoteUrl)) {
        throw "No GitHub remote is configured yet. Run: git remote add origin <your-github-repo-url>"
    }

    Invoke-Git add .

    $status = & git status --porcelain
    if ([string]::IsNullOrWhiteSpace(($status | Out-String))) {
        Write-Host "No changes to commit."
        exit 0
    }

    if ([string]::IsNullOrWhiteSpace($Message)) {
        $Message = "Update Guagua🐸 nodes $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    }

    Invoke-Git commit -m $Message

    $currentBranch = (& git branch --show-current).Trim()
    if ([string]::IsNullOrWhiteSpace($currentBranch)) {
        $currentBranch = "main"
    }

    $upstreamRemote = (& git config --get "branch.$currentBranch.remote" 2>$null | Out-String).Trim()
    if ([string]::IsNullOrWhiteSpace($upstreamRemote)) {
        Invoke-Git push -u origin $currentBranch
    } else {
        Invoke-Git push
    }
}
finally {
    Pop-Location
}
