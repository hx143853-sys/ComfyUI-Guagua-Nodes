param(
    [Parameter(Mandatory = $true)]
    [string]$NodeSlug,

    [string]$NodeTitle = "",

    [switch]$Publish,

    [string]$CommitMessage = ""
)

$ErrorActionPreference = "Stop"

function Convert-ToPascalCase {
    param([string]$Value)

    $parts = ($Value -replace "[^a-zA-Z0-9]+", " ").Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
    if ($parts.Count -eq 0) {
        throw "NodeSlug must contain letters or numbers so a Python class name can be generated."
    }

    return ($parts | ForEach-Object {
        if ($_.Length -eq 1) {
            $_.ToUpperInvariant()
        } else {
            $_.Substring(0, 1).ToUpperInvariant() + $_.Substring(1)
        }
    }) -join ""
}

function Convert-ToTitle {
    param([string]$Value)

    $parts = ($Value -replace "[^a-zA-Z0-9]+", " ").Split(" ", [System.StringSplitOptions]::RemoveEmptyEntries)
    if ($parts.Count -eq 0) {
        throw "NodeSlug must contain letters or numbers so a default node title can be generated."
    }

    return ($parts | ForEach-Object {
        if ($_.Length -eq 1) {
            $_.ToUpperInvariant()
        } else {
            $_.Substring(0, 1).ToUpperInvariant() + $_.Substring(1).ToLowerInvariant()
        }
    }) -join " "
}

$normalizedSlug = ($NodeSlug.ToLowerInvariant() -replace "[^a-z0-9]+", "_").Trim("_")
if ([string]::IsNullOrWhiteSpace($normalizedSlug)) {
    throw "NodeSlug must include at least one English letter or number, for example: prompt_cleaner"
}

$repoRoot = Split-Path -Parent $PSScriptRoot
$targetDirectory = Join-Path $repoRoot "nodes\custom"
$targetPath = Join-Path $targetDirectory "$normalizedSlug.py"

if (Test-Path $targetPath) {
    throw "Node file already exists: $targetPath"
}

$classStem = Convert-ToPascalCase -Value $normalizedSlug
$className = "Guagua${classStem}Node"
$resolvedTitle = if ([string]::IsNullOrWhiteSpace($NodeTitle)) {
    Convert-ToTitle -Value $normalizedSlug
} else {
    $NodeTitle.Trim()
}

$moduleContent = @"
from __future__ import annotations


class $className:
    CATEGORY = "Guagua🐸/Custom"
    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("text",)
    FUNCTION = "run"

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "text": ("STRING", {"multiline": True, "default": ""}),
            }
        }

    def run(self, text: str):
        return (text,)


NODE_CLASS_MAPPINGS = {
    "$resolvedTitle": $className,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "$resolvedTitle": "$resolvedTitle",
}
"@

New-Item -ItemType Directory -Force -Path $targetDirectory | Out-Null
Set-Content -Path $targetPath -Value $moduleContent -Encoding UTF8

Write-Host "Created node file: $targetPath"

if ($Publish) {
    $publishScript = Join-Path $repoRoot "publish_to_github.ps1"
    $resolvedCommitMessage = if ([string]::IsNullOrWhiteSpace($CommitMessage)) {
        "Add Guagua🐸 node: $resolvedTitle"
    } else {
        $CommitMessage
    }

    & $publishScript -Message $resolvedCommitMessage
}
