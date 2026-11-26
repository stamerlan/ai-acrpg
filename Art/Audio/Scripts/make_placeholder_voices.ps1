# Writes Art/Audio/Source/vo_dj_news.wav and vo_dj_exit.wav: placeholder
# radio DJ lines in a Windows voice (System.Speech), until they are made
# with the trailer's DJ voice (Art/Trailer/Scripts/gen.js, voice Fenrir).
# Run: powershell -File Art/Audio/Scripts/make_placeholder_voices.ps1
Add-Type -AssemblyName System.Speech
$out = Join-Path (Split-Path $PSScriptRoot) "Source"
New-Item -ItemType Directory -Force $out | Out-Null
$lines = @{
  "vo_dj_news" = "<prosody rate='+15%' pitch='+2st'>Breaking news!</prosody>" +
    "<break time='200ms'/><prosody rate='+5%'>Why did the chicken cross " +
    "the border?</prosody><break time='350ms'/><prosody rate='+5%' " +
    "pitch='-1st'>Polish customs are investigating.</prosody>";
  "vo_dj_exit" = "<prosody rate='+20%' pitch='+3st' volume='loud'>" +
    "Kudakhstan!</prosody><break time='150ms'/><prosody rate='+15%' " +
    "pitch='+2st'>Now with more cosmos!</prosody><break time='300ms'/>" +
    "<prosody rate='+5%'>Chickens, do not bring luggage.</prosody>" +
    "<break time='250ms'/><prosody rate='-5%' pitch='-2st'>You will not " +
    "need it.</prosody>"
}
foreach ($name in $lines.Keys) {
  $voice = New-Object System.Speech.Synthesis.SpeechSynthesizer
  $voice.SelectVoice("Microsoft David Desktop")
  $format = New-Object System.Speech.AudioFormat.SpeechAudioFormatInfo(
    24000, [System.Speech.AudioFormat.AudioBitsPerSample]::Sixteen,
    [System.Speech.AudioFormat.AudioChannel]::Mono)
  $voice.SetOutputToWaveFile((Join-Path $out "$name.wav"), $format)
  $voice.SpeakSsml("<speak version='1.0' " +
    "xmlns='http://www.w3.org/2001/10/synthesis' xml:lang='en-US'>" +
    $lines[$name] + "</speak>")
  $voice.Dispose()
}
