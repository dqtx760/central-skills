---
name: install-to-central
description: 浠?GitHub 瀹夎鎶€鑳藉埌涓ぎ浠撳簱锛岃嚜鍔ㄥ悓姝ュ埌鎵€鏈夋櫤鑳戒綋銆傜敤娉曪細/install-to-central <github-url>
---

# install-to-central

浠?GitHub 瀹夎鎶€鑳藉埌涓ぎ浠撳簱 `C:\Users\Administrator\.agents\skills\`锛屽苟鑷姩鍚屾鍒版墍鏈夋櫤鑳戒綋鐩綍銆?
## 鐢ㄦ硶

褰撶敤鎴疯"瀹夎鎶€鑳?銆?瑁呬釜鎶€鑳?銆?install skill"銆?浠?GitHub 瀹夎"鎴栨彁渚?GitHub URL 瑕佹眰瀹夎鍒颁腑澶粨搴撴椂锛屼娇鐢ㄦ鎶€鑳姐€?
## 鍙傛暟

鎻愪緵涓€涓?GitHub URL锛屾敮鎸佷袱绉嶆牸寮忥細

- **鏁翠釜浠撳簱灏辨槸鎶€鑳?*: `https://github.com/user/repo`
- **浠撳簱鍐呯殑瀛愮洰褰?*: `https://github.com/user/repo/path/to/skill`

鎶€鑳藉悕绉颁細鑷姩浠?URL 鏈€鍚庝竴娈垫彁鍙栥€?
## 鎵ц姝ラ

### 1. 瑙ｆ瀽 URL

浠?URL 鎻愬彇 owner銆乺epo 鍜屽瓙鐩綍璺緞锛?
```
$url = '<鐢ㄦ埛鎻愪緵鐨刄RL>'
$cleanUrl = $url -replace '\.git$',''
$parts = ($cleanUrl -replace 'https://github.com/','') -split '/'
$owner = $parts[0]
$repo = $parts[1]
```

- 濡傛灉 `$parts.Count -eq 2` 鈫?鏁翠釜浠撳簱妯″紡锛屾妧鑳藉悕 = `$repo`
- 濡傛灉 `$parts.Count -gt 2` 鈫?瀛愮洰褰曟ā寮忥紝瀛愮洰褰曡矾寰?= 绗?娈靛埌鏈€鍚庯紝鎶€鑳藉悕 = 鏈€鍚庝竴娈?
### 2. 鍏嬮殕鍒颁复鏃剁洰褰?
```powershell
$tmpDir = Join-Path $env:TEMP "skill-install-$(Get-Random)"
git clone --depth 1 "https://github.com/${owner}/${repo}.git" $tmpDir
```

### 3. 瀹氫綅鎶€鑳芥簮鐩綍

- **浠撳簱妯″紡**锛氭簮鐩綍 = `$tmpDir`
- **瀛愮洰褰曟ā寮?*锛氭簮鐩綍 = `Join-Path $tmpDir <瀛愮洰褰曡矾寰?`

楠岃瘉婧愮洰褰曞瓨鍦紝鍚﹀垯鎶ラ敊缁堟銆?
### 4. 澶嶅埗鍒颁腑澶粨搴?
```powershell
$target = "C:\Users\Administrator\.agents\skills\<鎶€鑳藉悕>"
if (Test-Path $target) { throw "涓ぎ浠撳簱宸插瓨鍦ㄥ悓鍚嶆妧鑳斤細<鎶€鑳藉悕>" }
Copy-Item -Recurse $sourceDir $target
```

### 5. 杩愯鍚屾鑴氭湰

```powershell
$syncScript = "C:\Users\Administrator\.agents\sync-skills.ps1"
if (Test-Path $syncScript) { & $syncScript }
```

### 6. 娓呯悊

```powershell
Remove-Item -Recurse -Force $tmpDir
```

### 7. 鎶ュ憡缁撴灉

杈撳嚭瀹夎鎽樿锛氭妧鑳藉悕銆佹簮 URL銆佸凡瀹夎鍒颁腑澶粨搴撱€佸凡鍚屾鐨勬櫤鑳戒綋鍒楄〃銆?