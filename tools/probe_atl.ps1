# Builds one tiny project per PlatformToolset with the same MSBuild the
# breakpad stage uses, and reports which toolsets can find ATL.
param(
    [string[]]$Toolsets = @('v143', 'v144', 'v145')
)

$ErrorActionPreference = 'Continue'
New-Item -ItemType Directory -Force probe | Out-Null
Set-Location probe

"int main() { return 0; }" | Out-File -Encoding ascii main.cpp

# ATL needs atls.lib; UseOfAtl=Static is what makes MSBuild link it.
$template = @'
<?xml version="1.0" encoding="utf-8"?>
<Project DefaultTargets="Build" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">
  <ItemGroup>
    <ClCompile Include="main.cpp" />
  </ItemGroup>
  <PropertyGroup>
    <Configuration>Release</Configuration>
    <Platform>x64</Platform>
    <PlatformToolset>__TOOLSET__</PlatformToolset>
    <UseOfAtl>Static</UseOfAtl>
  </PropertyGroup>
  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.Default.props" />
  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.props" />
  <Import Project="$(VCTargetsPath)\Microsoft.Cpp.targets" />
</Project>
'@

foreach ($ts in $Toolsets) {
    "== toolset $ts =="
    $proj = "probe_$ts.vcxproj"
    $template.Replace('__TOOLSET__', $ts) | Set-Content -Encoding utf8 $proj
    $out = & msbuild $proj /p:Configuration=Release /p:Platform=x64 /v:minimal 2>&1
    $errs = $out | Select-String -Pattern 'error |warning MSB' | Select-Object -First 3
    if ($errs) { $errs | ForEach-Object { "  $_" } } else { "  OK" }
}

Set-Location ..
