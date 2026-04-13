param([string]$ImagePath)

# This script must be run with pwsh (PowerShell 7+)
# It uses the WinRT LockScreen API to set the lock screen image

Add-Type -AssemblyName System.Runtime.WindowsRuntime

# Load WinRT type projections
$null = [Windows.System.UserProfile.LockScreen, Windows.System.UserProfile, ContentType = WindowsRuntime]
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]

# Helper to await WinRT async operations
Add-Type -Language CSharp @"
using System;
using System.Threading.Tasks;
using System.Runtime.CompilerServices;

public static class WinRTHelper
{
    public static void Await(Windows.Foundation.IAsyncAction action)
    {
        System.WindowsRuntimeSystemExtensions.AsTask(action).GetAwaiter().GetResult();
    }
    public static T Await<T>(Windows.Foundation.IAsyncOperation<T> op)
    {
        return System.WindowsRuntimeSystemExtensions.AsTask(op).GetAwaiter().GetResult();
    }
}
"@ -ReferencedAssemblies @(
    "System.Runtime.WindowsRuntime",
    [Windows.System.UserProfile.LockScreen].Assembly.Location,
    [Windows.Storage.StorageFile].Assembly.Location
)

$file = [WinRTHelper]::Await([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath))
[WinRTHelper]::Await([Windows.System.UserProfile.LockScreen]::SetImageFileAsync($file))
Write-Output "OK"

Function Await($WinRtTask, $ResultType) {
    $method = $asTaskGeneric.MakeGenericMethod($ResultType)
    $task = $method.Invoke($null, @($WinRtTask))
    $task.Wait()
    $task.Result
}

Function AwaitAction($WinRtTask) {
    $asAction = [System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object { $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncAction' }
    $task = $asAction.Invoke($null, @($WinRtTask))
    $task.Wait()
}

$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync($ImagePath)) ([Windows.Storage.StorageFile])
AwaitAction ([Windows.System.UserProfile.LockScreen]::SetImageFileAsync($file))
Write-Output "OK"
