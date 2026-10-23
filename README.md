<div align="center">

# 🎬 MP4 Downloader (Tüm Platformlar Video & Kesit İndirici)

<img src="assets/obito.jpg" width="200" style="border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.3);" />

**YouTube • Twitch • TikTok • Twitter (X) • Instagram • Anime/Film Siteleri & M3U8**  
*Sıfır CPU Yükü • Ultra Hızlı Kesit Alma • En Yüksek Kalite MP4 Otomatik Birleştirme*

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows&logoColor=white)](https://microsoft.com/windows)
[![Quality](https://img.shields.io/badge/Kalite-4K%20%2F%202K%20%2F%201080p60-orange)]()
[![CPU Usage](https://img.shields.io/badge/CPU%20Y%C3%BCk%C3%BC-%250%20(Stream%20Copy)-brightgreen)]()
[![License](https://img.shields.io/badge/Lisans-MIT-green)]()

---

</div>

## 🟢 GitHub'ı İlk Defa Kullananlar İçin 4 Adımda Kurulum

Hiç kodlama veya GitHub bilmeseniz bile 1 dakikada kurup çalıştırabilirsiniz:

### 1. Adım: Dosyaları İndirin
1. Bu sayfanın sağ üst tarafındaki yeşil **`<> Code`** butonuna tıklayın.
2. Açılan menüden en alttaki **`Download ZIP`** seçeneğine basın ve indirin.
3. İnen ZIP (veya RAR) dosyasına sağ tıklayıp **"Buraya Ayıkla"** / **"Tümünü Ayıkla"** diyerek klasöre çıkartın.

---

### ⚡ EN KOLAY YOL (Tek Tıkla Başlat):
Klasörü ayıkladıktan sonra içindeki **`baslat.bat`** dosyasına çift tıklayın!  
Gereksinimleri otomatik olarak kontrol eder, eksikleri yükler ve programı hemen açar.

---

### Veya Manuel Kurulum (Terminal / PowerShell İle):

#### 2. Adım: Klasörün İçinde Terminal Açın
İki yöntemden birini kullanabilirsiniz:
- **Yöntem 1 (Adres Çubuğu):** Çıkardığınız proje klasörünün içine girin (`downloader.py` dosyasını gördüğünüz yer). Üstteki adres çubuğuna sol tıklayıp **`cmd`** yazın ve **Enter**'a basın.
- **Yöntem 2 (CD Komutu):** Terminal veya PowerShell açıp klasörün yoluna gidin:
  ```powershell
  cd "C:\Users\KullaniciAdiniz\Desktop\mp4-downloader"
  ```

> 💡 **Python Gereksinimi:**  
> Bilgisayarınızda Python yüklü değilse [python.org](https://www.python.org/downloads/) adresinden 1 dakikada kurabilirsiniz. Kurulum ekranında en alttaki **`Add python.exe to PATH`** kutucuğunu işaretlemeyi unutmayın!

---

### 3. Adım: Gereksinimleri Yükleyin
Terminalde `pip` bulunamadı hatası yaşamamak için en garanti komut:
```bash
python -m pip install -r requirements.txt
```
*(Gerekli kütüphaneler birkaç saniye içinde otomatik kurulacaktır).*

---

### 4. Adım: Programı Başlatın
Aynı pencereye şunu yazıp **Enter**'a basın:
```bash
python downloader.py
```
Programınız şık ve Türkçe arayüzüyle anında açılacaktır! 🎉

---

### 💡 (İsteğe Bağlı) Bilgisayarın Her Yerinden Tek Komutla Çalıştırma
Klasörün içindeyken bir defaya mahsus şu komutu çalıştırırsanız:
```bash
pip install .
```
Artık bilgisayarınızda nerede olursanız olun (Masaüstü, Belgeler vb. fark etmeksizin) terminale sadece:
```bash
orkunfb
```
*(veya alternatif olarak `indir` ya da `mp4`)* yazarak programı doğrudan başlatabilirsiniz!

---

## ⚡ Kullanım Rehberi

Program açıldığında indirmek istediğiniz videonun linkini yapıştırıp **Enter**'a basın.

### 1. Standart İndirme (Tüm Video)
- Linki yapıştırdıktan sonra seçeneklerden `[2] Videonun Tamamını İndir` seçebilir veya doğrudan `Enter`'a basabilirsiniz.
- Video sunulan **en yüksek kalitede (4K, 2K, 1080p60fps vb.)** ses ve görüntüsü birleştirilmiş tek bir `.mp4` olarak doğrudan **Masaüstünüze** iner.

### 2. ✂️ Zaman Aralığı (Kesit) İndirme
4-5 saatlik uzun bir yayın veya filmden sadece istediğiniz dakikaları indirmek için seçeneklerden `[1]` seçin ve aralığı yazın:
- Dakika bazlı: `25dk 48dk` veya `10:00-25:00`
- Saat bazlı: `2-3` veya `01:00:00-02:00:00`
- Tek satırda linkle birlikte: `https://site.com/video.mp4 25dk 48dk`

> ⚡ **Sıfır CPU Yükü:** Video kare kare tekrar işlenmez (renderlanmaz). **Stream Copy** teknolojisi sayesinde işlemcinizi kasmadan (%0 CPU), fan açtırmadan orijinal stüdyo kalitesinde saniyeler içinde kesilip indirilir.

### 3. 🚀 Eşzamanlı Çoklu Video İndirme (Toplu İndirme)
Birden fazla video linkini aralarında boşluk bırakarak tek seferde yapıştırabilirsiniz:
```text
https://youtu.be/video1 https://tiktok.com/@kisi/video2 https://x.com/user/status/video3
```
Program **5 videoyu aynı anda** paralel iş parçacıklarıyla (ThreadPool) canlı ilerleme çubukları eşliğinde süper hızlı indirir.

### 4. ⌨️ Komut Satırından Tek Satırda Doğrudan İndirme (CLI)
Arayüze girmeden tek satırda doğrudan indirme yapabilirsiniz:
```bash
python downloader.py "https://youtube.com/watch?v=..."
python downloader.py "https://youtube.com/watch?v=..." 10dk 15dk
orkunfb "https://site.com/yayin.m3u8" 01:00:00-02:00:00
```

### 5. 🎬 Anime, Dizi ve Film Sitelerinden İndirme (F12 Taktiği)
1. Tarayıcıda videoyu açın, klavyeden **F12** tuşuna basıp açılan pencerede **Ağ (Network)** sekmesine gelin.
2. Filtre kutusuna **`m3u8`** yazın ve videoyu 1-2 saniye oynatın.
3. Listede beliren `master.m3u8` linkine sağ tıklayıp bağlantıyı kopyalayın.
4. Programa yapıştırın; video otomatik olarak en yüksek kalitede MP4 olarak inecektir!

### 6. ⛔ İndirmeyi İptal Etme
- İndirme veya kesme esnasında vazgeçerseniz istediğiniz an **`Ctrl + C`** tuşlarına basabilirsiniz.
- Program anında durur ve diskte yarım kalan geçici dosyaları (`.part`, `.ytdl`, `.temp`) arkasında hiç çöp bırakmadan temizler.

---

## 📋 Desteklenen Popüler Platformlar

| Platform | Maksimum Çözünürlük | Filigransız | Kesit (Aralık) Alma | Çoklu İndirme |
| :--- | :---: | :---: | :---: | :---: |
| **YouTube** | **4K / 2K / 1080p60** | ✓ | ✓ | ✓ |
| **TikTok** | **HD (Logosuz)** | ✓ | ✓ | ✓ |
| **Twitter / X** | **Orijinal En Yüksek** | ✓ | ✓ | ✓ |
| **Instagram** | **Reels & Gönderi HD** | ✓ | ✓ | ✓ |
| **Twitch** | **1080p60 VOD & Klipler** | ✓ | ✓ | ✓ |
| **Reddit & Pinterest** | **En Yüksek Kalite** | ✓ | ✓ | ✓ |
| **Anime & Dizi Siteleri** | **Orijinal M3U8 Akışı** | ✓ | ✓ | ✓ |

---

## 🌟 Öne Çıkan Özellikler

- **0 CPU & Düşük Sistem Dostu:** Özel Windows öncelik motoru ve 64 KB bellek tamponu sayesinde 10 yıllık eski bilgisayarlarda dahi tarayıcıyı, fareyi veya sistemi asla dondurmaz.
- **🛡️ Bot Koruması & Oturum Aşma:** `curl-cffi` TLS parmak izi taklidi (Chrome Impersonation) ve YouTube n-sig / anti-bot challenge çözücüleri içerir. Yaş kısıtlamalı veya üyelik gerektiren videolarda tarayıcınızın (Chrome, Edge, Brave, Firefox) oturum çerezlerini otomatik algılayıp indirir.
- **Canlı İlerleme & Hız Monitörü:** Kesit alırken veya indirirken `✂️ Kesit İndiriliyor • 45.2 MB • 8.4 MB/s` şeklinde anlık durumu canlı gösterir.
- **Tek Tıkla Masaüstü:** Tüm indirilen MP4 dosyaları doğrudan Masaüstünüze tertemiz kaydedilir.
- **🔒 Tamamen Güvenli & Gizli:** İndirdiğiniz hiçbir video, bağlantı veya kişisel bilginiz internete veya dış sunuculara iletilmez, her şey tamamen yerel ve cihazınızda çalışır.

---

## 📌 Program İçi Kısayollar

Program açıkken komut satırına yazabileceğiniz pratik komutlar:
- **`klasor` / `open`:** İndirilenlerin kaydedildiği Masaüstü klasörünü Windows Gezgini'nde açar.
- **`cls` / `temizle`:** Konsol ekranını temizler ve ana paneli yeniler.
- **`yardim`:** Dizi, film ve canlı yayın indirme rehberini açar.
- **`q` / `cikis`:** Programdan güvenle çıkar.

---

## ❓ Sıkça Sorulan Sorular (SSS)

**S: FFmpeg kurmam gerekiyor mu?**  
**C:** Hayır! Proje `imageio-ffmpeg` motoru sayesinde FFmpeg'i sıfır yapılandırmayla arka planda otomatik temin eder. Ek bir kurulum yapmanıza gerek yoktur.

**S: İndirilen videolar nerede?**  
**C:** Tüm videolar doğrudan Masaüstünüze (`Desktop`) kaydedilir. Program açıkken `klasor` yazarak da doğrudan klasöre gidebilirsiniz.

**S: 4K videolarda ses neden ayrılmıyor?**  
**C:** YouTube 1080p ve üzeri çözünürlüklerde ses ile görüntüyü ayrı akışlarda sunar. MP4 Downloader en yüksek video akışı ile stüdyo kalitesindeki ses akışını tespit eder ve kayıpsız tek bir MP4 dosyası haline getirir.

**S: Kesit alırken bilgisayarım neden hiç kasmıyor?**  
**C:** Geleneksel programlar videoyu CPU ile tekrar render eder. Bu araç ise **Stream Copy (`-c copy`)** kullandığı için videoyu yeniden işlemez; ham dijital veriyi kayıpsız kopyalar. Bu sayede işlemci yükü %0 olur ve saniyeler içinde tamamlanır.

---

## 🔨 Kendi Bağımsız (.EXE) Dosyanızı Üretme

Python'a ihtiyaç duymadan çift tıklayıp açılacak tek parça bir EXE dosyası üretmek isterseniz terminalde:
```bash
python build_exe.py
```
komutunu çalıştırmanız yeterlidir. `orkunfb.exe` hazır olarak klasörünüzde oluşacaktır.
